import json

from sqlalchemy import select

from app.core.models import ChatMessageORM, ConsultationORM, TrainingPlanORM
from app.tests.factories import (
    completion_with_tool,
    completion_without_tool,
    intake_payload,
    plan_payload,
    text_chunk,
    tool_chunk,
)


def _parse_ndjson(body: str) -> list[dict]:
    return [json.loads(line) for line in body.splitlines() if line.strip()]


# --- /start ----------------------------------------------------------------

async def test_start_creates_consultation(client, session_maker):
    resp = await client.post("/consultation/start", json=intake_payload())
    assert resp.status_code == 201
    cid = resp.json()["consultation_id"]
    assert cid

    async with session_maker() as db:
        row = (await db.execute(select(ConsultationORM).where(ConsultationORM.id == cid))).scalar_one()
        assert row.intake_snapshot["pet_name"] == "Rex"


async def test_start_rejects_invalid_intake(client):
    bad = intake_payload()
    bad["behavior_issues"] = []  # min_length=1 violated
    resp = await client.post("/consultation/start", json=bad)
    assert resp.status_code == 422


# --- /chat -----------------------------------------------------------------

async def test_chat_streams_ndjson_and_persists_messages(client, fake_llm, consultation_id, session_maker):
    fake_llm.stream_chunks = [text_chunk("Hi! "), text_chunk("Tell me more.")]

    resp = await client.post(f"/consultation/{consultation_id}/chat", json={"user_message": "my dog panics"})
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("application/x-ndjson")

    events = _parse_ndjson(resp.text)
    assert [e["type"] for e in events] == ["token", "token", "done"]

    async with session_maker() as db:
        msgs = (await db.execute(
            select(ChatMessageORM).where(ChatMessageORM.consultation_id == consultation_id)
        )).scalars().all()
        roles = sorted(m.role for m in msgs)
        assert roles == ["assistant", "user"]
        assert any(m.role == "assistant" and m.content == "Hi! Tell me more." for m in msgs)


async def test_chat_includes_current_user_message_in_llm_context(client, fake_llm, consultation_id):
    fake_llm.stream_chunks = [text_chunk("ok")]
    await client.post(f"/consultation/{consultation_id}/chat", json={"user_message": "REMEMBER_ME"})

    sent_messages = fake_llm.calls[0]["messages"]
    assert sent_messages[-1] == {"role": "user", "content": "REMEMBER_ME"}


async def test_chat_autonomously_proposes_and_persists_plan(client, fake_llm, consultation_id, session_maker):
    args = json.dumps(plan_payload())
    fake_llm.stream_chunks = [
        text_chunk("Based on what we discussed. "),
        tool_chunk(0, name="submit_training_plan", args=args),
    ]

    resp = await client.post(f"/consultation/{consultation_id}/chat", json={"user_message": "make a plan"})
    events = _parse_ndjson(resp.text)
    assert [e["type"] for e in events] == ["token", "plan", "message", "done"]
    assert events[1]["plan"]["dog_name"] == "Rex"

    async with session_maker() as db:
        plan_row = (await db.execute(
            select(TrainingPlanORM).where(TrainingPlanORM.consultation_id == consultation_id)
        )).scalar_one()
        assert plan_row.plan_status == "proposed"
        assert plan_row.plan_payload["dog_name"] == "Rex"

        plan_msgs = (await db.execute(
            select(ChatMessageORM).where(
                ChatMessageORM.consultation_id == consultation_id,
                ChatMessageORM.role == "assistant_plan",
            )
        )).scalars().all()
        assert len(plan_msgs) == 1


async def test_chat_iterates_existing_plan_in_context_and_upserts(client, fake_llm, consultation_id, session_maker):
    # Seed an existing proposed plan.
    async with session_maker() as db:
        db.add(TrainingPlanORM(
            consultation_id=consultation_id, plan_payload=plan_payload(), plan_status="proposed"
        ))
        await db.commit()

    revised = plan_payload(triage="revised: less intensive management")
    fake_llm.stream_chunks = [tool_chunk(0, name="submit_training_plan", args=json.dumps(revised))]

    resp = await client.post(
        f"/consultation/{consultation_id}/chat",
        json={"user_message": "make issue 1 less intensive"},
    )
    assert resp.status_code == 200

    # The existing plan was injected into the system prompt for revision.
    system_prompt = fake_llm.calls[0]["messages"][0]["content"]
    assert "CURRENT PROPOSED PLAN" in system_prompt

    async with session_maker() as db:
        plans = (await db.execute(
            select(TrainingPlanORM).where(TrainingPlanORM.consultation_id == consultation_id)
        )).scalars().all()
        assert len(plans) == 1  # upserted, not duplicated
        assert plans[0].plan_payload["triage_summary"] == "revised: less intensive management"


async def test_chat_404_for_unknown_consultation(client, fake_llm):
    resp = await client.post("/consultation/does-not-exist/chat", json={"user_message": "hi"})
    assert resp.status_code == 404


# --- /finalize -------------------------------------------------------------

async def test_finalize_returns_plan_and_marks_finalized(client, fake_llm, consultation_id, session_maker):
    fake_llm.completion = completion_with_tool(json.dumps(plan_payload()))

    resp = await client.post(f"/consultation/{consultation_id}/finalize")
    assert resp.status_code == 200
    assert resp.json()["dog_name"] == "Rex"

    async with session_maker() as db:
        plan_row = (await db.execute(
            select(TrainingPlanORM).where(TrainingPlanORM.consultation_id == consultation_id)
        )).scalar_one()
        assert plan_row.plan_status == "finalized"


async def test_finalize_upserts_over_existing_proposed_plan(client, fake_llm, consultation_id, session_maker):
    async with session_maker() as db:
        db.add(TrainingPlanORM(
            consultation_id=consultation_id, plan_payload=plan_payload(), plan_status="proposed"
        ))
        await db.commit()

    fake_llm.completion = completion_with_tool(json.dumps(plan_payload(triage="final version")))
    resp = await client.post(f"/consultation/{consultation_id}/finalize")
    assert resp.status_code == 200

    async with session_maker() as db:
        plans = (await db.execute(
            select(TrainingPlanORM).where(TrainingPlanORM.consultation_id == consultation_id)
        )).scalars().all()
        assert len(plans) == 1
        assert plans[0].plan_status == "finalized"
        assert plans[0].plan_payload["triage_summary"] == "final version"


async def test_finalize_502_when_model_skips_tool_call(client, fake_llm, consultation_id):
    fake_llm.completion = completion_without_tool()
    resp = await client.post(f"/consultation/{consultation_id}/finalize")
    assert resp.status_code == 502


async def test_finalize_404_for_unknown_consultation(client, fake_llm):
    resp = await client.post("/consultation/nope/finalize")
    assert resp.status_code == 404
