import json

import pytest

from app.schemas.intake import ComprehensiveIntakeSchema
from app.schemas.plans import ComprehensiveTrainingPlanSchema
from app.services import llm, prompts
from app.tests.factories import (
    FakeLLMClient,
    completion_with_tool,
    completion_without_tool,
    empty_chunk,
    intake_payload,
    plan_payload,
    text_chunk,
    tool_chunk,
)


def _intake() -> ComprehensiveIntakeSchema:
    return ComprehensiveIntakeSchema(**intake_payload())


async def _collect(agen):
    return [e async for e in agen]


def test_build_plan_tool_shape():
    tool = llm.build_plan_tool()
    assert tool["type"] == "function"
    assert tool["function"]["name"] == "submit_training_plan"
    assert "properties" in tool["function"]["parameters"]


def test_build_messages_orders_system_then_history():
    history = [llm.ChatTurn(role="user", content="hi"), llm.ChatTurn(role="assistant", content="hello")]
    messages = llm.build_messages(_intake(), history, None)
    assert messages[0]["role"] == "system"
    assert messages[1] == {"role": "user", "content": "hi"}
    assert messages[2] == {"role": "assistant", "content": "hello"}


def test_build_messages_maps_assistant_plan_row_to_readable_text():
    plan = ComprehensiveTrainingPlanSchema(**plan_payload())
    history = [llm.ChatTurn(role="assistant_plan", content=json.dumps(plan.model_dump()))]
    messages = llm.build_messages(_intake(), history, None)
    assert messages[1]["role"] == "assistant"
    assert "Proposed training plan" in messages[1]["content"]
    assert "Mat Stationing" in messages[1]["content"]


def test_render_history_turn_falls_back_on_bad_plan_json():
    turn = llm.ChatTurn(role="assistant_plan", content="not-json")
    msg = llm._render_history_turn(turn)
    assert msg["role"] == "assistant"
    assert "not-json" in msg["content"]


# --- streaming agent turn --------------------------------------------------

async def test_stream_text_only_yields_tokens_then_done():
    fake = FakeLLMClient()
    fake.stream_chunks = [text_chunk("Hello "), text_chunk("there"), empty_chunk()]
    sink = llm.AgentTurnResult()

    events = await _collect(llm.stream_agent_turn(fake, _intake(), [], None, sink))

    assert [e.type for e in events] == ["token", "token", "done"]
    assert sink.assistant_text == "Hello there"
    assert sink.proposed_plan is None
    # auto tool choice + streaming were requested
    assert fake.calls[0]["tool_choice"] == "auto"
    assert fake.calls[0]["stream"] is True


async def test_stream_proposes_plan_from_fragmented_tool_call():
    args = json.dumps(plan_payload())
    fake = FakeLLMClient()
    fake.stream_chunks = [
        text_chunk("Let me draft that. "),
        tool_chunk(0, name="submit_training_plan", args=args[:30]),
        tool_chunk(0, args=args[30:]),  # name only on first fragment, args split
    ]
    sink = llm.AgentTurnResult()

    events = await _collect(llm.stream_agent_turn(fake, _intake(), [], None, sink))

    assert [e.type for e in events] == ["token", "plan", "message", "done"]
    plan_event = next(e for e in events if e.type == "plan")
    assert plan_event.plan.pet_name == "Rex"
    assert sink.proposed_plan is not None
    assert sink.assistant_text == "Let me draft that. "


async def test_stream_proposed_confirmation_when_no_existing_plan():
    fake = FakeLLMClient()
    fake.stream_chunks = [tool_chunk(0, name="submit_training_plan", args=json.dumps(plan_payload()))]
    sink = llm.AgentTurnResult()

    events = await _collect(llm.stream_agent_turn(fake, _intake(), [], None, sink))

    msg = next(e for e in events if e.type == "message")
    assert msg.text == prompts.PLAN_PROPOSED_CONFIRMATION.format(pet_name="Rex")


async def test_stream_revised_confirmation_when_plan_already_exists():
    existing = ComprehensiveTrainingPlanSchema(**plan_payload())
    fake = FakeLLMClient()
    fake.stream_chunks = [
        tool_chunk(0, name="submit_training_plan", args=json.dumps(plan_payload(triage="revised"))),
    ]
    sink = llm.AgentTurnResult()

    events = await _collect(llm.stream_agent_turn(fake, _intake(), [], existing, sink))

    msg = next(e for e in events if e.type == "message")
    assert msg.text == prompts.PLAN_REVISED_CONFIRMATION.format(pet_name="Rex")


async def test_stream_malformed_tool_args_yields_error_not_crash():
    fake = FakeLLMClient()
    fake.stream_chunks = [tool_chunk(0, name="submit_training_plan", args="{not valid json")]
    sink = llm.AgentTurnResult()

    events = await _collect(llm.stream_agent_turn(fake, _intake(), [], None, sink))

    assert [e.type for e in events] == ["error", "done"]
    assert sink.proposed_plan is None


async def test_stream_schema_invalid_tool_args_yields_error():
    # Valid JSON but missing required fields -> ValidationError, surfaced as error event.
    fake = FakeLLMClient()
    fake.stream_chunks = [tool_chunk(0, name="submit_training_plan", args=json.dumps({"pet_name": "Rex"}))]
    sink = llm.AgentTurnResult()

    events = await _collect(llm.stream_agent_turn(fake, _intake(), [], None, sink))

    assert [e.type for e in events] == ["error", "done"]


async def test_stream_ignores_non_plan_tool():
    fake = FakeLLMClient()
    fake.stream_chunks = [tool_chunk(0, name="some_other_tool", args="{}")]
    sink = llm.AgentTurnResult()

    events = await _collect(llm.stream_agent_turn(fake, _intake(), [], None, sink))

    assert [e.type for e in events] == ["done"]
    assert sink.proposed_plan is None


def test_stream_event_to_wire_serializes_plan():
    plan = ComprehensiveTrainingPlanSchema(**plan_payload())
    wire = llm.StreamEvent(type="plan", plan=plan).to_wire()
    assert wire["type"] == "plan"
    assert wire["plan"]["pet_name"] == "Rex"
    assert "text" not in wire
    # round-trips through JSON
    assert json.loads(json.dumps(wire))["plan"]["pet_name"] == "Rex"


# --- forced plan generation ------------------------------------------------

async def test_generate_forced_plan_success_appends_finalize_instruction():
    fake = FakeLLMClient()
    fake.completion = completion_with_tool(json.dumps(plan_payload()))

    plan = await llm.generate_forced_plan(fake, _intake(), [], None)

    assert plan.pet_name == "Rex"
    # forced tool choice, not auto
    assert fake.calls[0]["tool_choice"]["function"]["name"] == "submit_training_plan"
    assert fake.calls[0]["messages"][-1]["content"] == prompts.FINALIZE_INSTRUCTION


async def test_generate_forced_plan_no_tool_call_raises():
    fake = FakeLLMClient()
    fake.completion = completion_without_tool()
    with pytest.raises(llm.PlanGenerationError):
        await llm.generate_forced_plan(fake, _intake(), [], None)


async def test_generate_forced_plan_bad_json_raises():
    fake = FakeLLMClient()
    fake.completion = completion_with_tool("{broken")
    with pytest.raises(llm.PlanGenerationError):
        await llm.generate_forced_plan(fake, _intake(), [], None)


# --- opening suggestions ---------------------------------------------------

async def test_opening_suggestions_returns_cleaned_list():
    fake = FakeLLMClient()
    fake.completion = completion_with_tool(
        json.dumps({"suggestions": ["Reactivity on walks", "  ", "At home too", "Something else"]}),
        name="suggest_openers",
    )
    out = await llm.generate_opening_suggestions(fake, _intake(), limit=4)
    assert out == ["Reactivity on walks", "At home too", "Something else"]


async def test_opening_suggestions_respects_limit():
    fake = FakeLLMClient()
    fake.completion = completion_with_tool(
        json.dumps({"suggestions": ["a", "b", "c", "d", "e"]}), name="suggest_openers"
    )
    out = await llm.generate_opening_suggestions(fake, _intake(), limit=3)
    assert out == ["a", "b", "c"]


async def test_opening_suggestions_falls_back_when_no_tool_call():
    fake = FakeLLMClient()
    fake.completion = completion_without_tool()
    assert await llm.generate_opening_suggestions(fake, _intake()) == llm.FALLBACK_SUGGESTIONS


async def test_opening_suggestions_falls_back_on_bad_json():
    fake = FakeLLMClient()
    fake.completion = completion_with_tool("{bad", name="suggest_openers")
    assert await llm.generate_opening_suggestions(fake, _intake()) == llm.FALLBACK_SUGGESTIONS


# --- follow-up suggestions -------------------------------------------------

async def test_followup_suggestions_uses_plan_and_history_context():
    plan = ComprehensiveTrainingPlanSchema(**plan_payload())
    history = [llm.ChatTurn(role="user", content="how do I start?")]
    fake = FakeLLMClient()
    fake.completion = completion_with_tool(
        json.dumps({"suggestions": ["Start mat work", "Soften week 1"]}), name="suggest_openers"
    )

    out = await llm.generate_followup_suggestions(fake, _intake(), history, plan)
    assert out == ["Start mat work", "Soften week 1"]
    # System prompt carries the current plan; the user turn is the follow-up ask.
    sent = fake.calls[0]["messages"]
    assert "CURRENT PROPOSED PLAN" in sent[0]["content"]
    assert sent[-1]["role"] == "user"


async def test_followup_suggestions_falls_back_when_no_tool_call():
    fake = FakeLLMClient()
    fake.completion = completion_without_tool()
    out = await llm.generate_followup_suggestions(fake, _intake(), [], None)
    assert out == llm.FALLBACK_FOLLOWUP_SUGGESTIONS
