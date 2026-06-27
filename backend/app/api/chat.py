import json
from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.schemas.intake import ComprehensiveIntakeSchema
from app.schemas.plans import ComprehensiveTrainingPlanSchema
from app.core.database import get_db_session
from app.core.deps import get_llm_client
from app.core.models import ConsultationORM, ChatMessageORM, TrainingPlanORM
from app.services import llm

router = APIRouter(prefix="/consultation", tags=["Chat"])


@router.post("/start", status_code=status.HTTP_201_CREATED)
async def start_consultation(
    intake_data: ComprehensiveIntakeSchema,
    db: AsyncSession = Depends(get_db_session)
) -> dict[str, str]:
    new_consultation = ConsultationORM(intake_snapshot=intake_data.model_dump())
    db.add(new_consultation)
    await db.commit()
    return {"consultation_id": new_consultation.id, "message": "New consultation created."}


async def _load_consultation(db: AsyncSession, consultation_id: str) -> ConsultationORM:
    result = await db.execute(select(ConsultationORM).where(ConsultationORM.id == consultation_id))
    consult = result.scalar_one_or_none()
    if not consult:
        raise HTTPException(status_code=404, detail="Consultation not found.")
    return consult


async def _load_current_plan(
    db: AsyncSession, consultation_id: str
) -> tuple[TrainingPlanORM | None, ComprehensiveTrainingPlanSchema | None]:
    result = await db.execute(
        select(TrainingPlanORM).where(TrainingPlanORM.consultation_id == consultation_id)
    )
    existing = result.scalar_one_or_none()
    schema = ComprehensiveTrainingPlanSchema(**existing.plan_payload) if existing else None
    return existing, schema


def _upsert_plan(
    db: AsyncSession,
    existing_plan: TrainingPlanORM | None,
    consultation_id: str,
    plan: ComprehensiveTrainingPlanSchema,
    plan_status: str,
) -> None:
    if existing_plan:
        existing_plan.plan_payload = plan.model_dump()
        existing_plan.plan_status = plan_status
    else:
        db.add(TrainingPlanORM(
            consultation_id=consultation_id,
            plan_payload=plan.model_dump(),
            plan_status=plan_status,
        ))


@router.post("/{consultation_id}/suggestions")
async def opening_suggestions(
    consultation_id: str,
    db: AsyncSession = Depends(get_db_session),
    client: AsyncOpenAI = Depends(get_llm_client)
) -> dict[str, list[str]]:
    consult = await _load_consultation(db, consultation_id)
    intake = ComprehensiveIntakeSchema(**consult.intake_snapshot)
    suggestions = await llm.generate_opening_suggestions(client, intake)
    return {"suggestions": suggestions}


@router.post("/{consultation_id}/chat")
async def consultation_chat(
    consultation_id: str,
    user_message: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db_session),
    client: AsyncOpenAI = Depends(get_llm_client)
) -> StreamingResponse:
    consult = await _load_consultation(db, consultation_id)

    fresh_user_message = ChatMessageORM(consultation_id=consultation_id, role="user", content=user_message)
    db.add(fresh_user_message)
    await db.commit()

    intake = ComprehensiveIntakeSchema(**consult.intake_snapshot)
    # consult.messages was loaded (via selectin) before the row above was added, so
    # append the current user turn explicitly rather than relying on a refresh.
    history = [llm.ChatTurn(role=m.role, content=m.content) for m in consult.messages]
    history.append(llm.ChatTurn(role="user", content=user_message))
    existing_plan, current_plan = await _load_current_plan(db, consultation_id)

    result_sink = llm.AgentTurnResult()

    async def ndjson_stream() -> AsyncGenerator[str, None]:
        async for event in llm.stream_agent_turn(
            client, intake, history, current_plan, result_sink
        ):
            yield json.dumps(event.to_wire()) + "\n"

        # Persist side effects once the stream is exhausted.
        if result_sink.assistant_text:
            db.add(ChatMessageORM(
                consultation_id=consultation_id, role="assistant", content=result_sink.assistant_text
            ))
        if result_sink.proposed_plan is not None:
            db.add(ChatMessageORM(
                consultation_id=consultation_id,
                role="assistant_plan",
                content=json.dumps(result_sink.proposed_plan.model_dump()),
            ))
            _upsert_plan(db, existing_plan, consultation_id, result_sink.proposed_plan, "proposed")
        await db.commit()

    return StreamingResponse(ndjson_stream(), media_type="application/x-ndjson")


@router.post("/{consultation_id}/finalize",
             response_model=ComprehensiveTrainingPlanSchema,
             status_code=status.HTTP_200_OK)
async def generate_final_training_plan(
    consultation_id: str,
    db: AsyncSession = Depends(get_db_session),
    client: AsyncOpenAI = Depends(get_llm_client)
) -> ComprehensiveTrainingPlanSchema:
    consult = await _load_consultation(db, consultation_id)

    intake = ComprehensiveIntakeSchema(**consult.intake_snapshot)
    history = [llm.ChatTurn(role=m.role, content=m.content) for m in consult.messages]
    existing_plan, current_plan = await _load_current_plan(db, consultation_id)

    try:
        plan = await llm.generate_forced_plan(client, intake, history, current_plan)
    except llm.PlanGenerationError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc))

    _upsert_plan(db, existing_plan, consultation_id, plan, "finalized")
    await db.commit()
    return plan
