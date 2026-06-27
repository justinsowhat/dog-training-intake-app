import json
from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
from openai import AsyncOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.schemas.intake import ComprehensiveIntakeSchema
from app.schemas.plans import ComprehensiveTrainingPlanSchema
from app.core.config import settings
from app.core.database import get_db_session, async_session_pool
from app.core.deps import get_llm_client
from app.core.models import ConsultationORM, ChatMessageORM, TrainingPlanORM

router = APIRouter(prefix="/consultation", tags=["Chat"])

@router.post("/start", status_code=status.HTTP_201_CREATED)
async def start_consultation(
    intake_data: ComprehensiveIntakeSchema,
    db: AsyncSession = Depends(get_db_session)
)-> dict[str, str]:
    new_consultation = ConsultationORM(intake_snapshot=intake_data.model_dump())
    db.add(new_consultation)
    await db.commit()
    return {"consultation_id": new_consultation.id, "message":"New consultation created."}

@router.post("/{consultation_id}/{chat}")
async def consultation_chat(
    consultation_id: str,
    user_message: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db_session),
    client: AsyncOpenAI = Depends(get_llm_client)
)-> StreamingResponse:
    result = await db.execute(select(ConsultationORM).where(ConsultationORM.id == consultation_id))
    consult = result.scalar_one_or_none()
    if not consult:
        raise HTTPException(status_code=404, detail="Consultation not found.")

    fresh_user_message = ChatMessageORM(consultation_id=consultation_id, role="user", content=user_message)
    db.add(fresh_user_message)
    await db.commit()
    
    mock_schema = ComprehensiveIntakeSchema(**consult.intake_snapshot)
    
    llm_messages = [{"role": "system", "content": _compile_system_context(mock_schema)}]
    for msg in consult.messages:
        llm_messages.append({"role": msg.role, "content": msg.content})

    async def database_aware_stream() -> AsyncGenerator[str, None]:
        response_stream = await client.chat.completions.create(
            model=settings.MODEL_SLUG,
            messages=llm_messages,
            stream=True
        )
        
        full_assistant_reply = ""
        async for chunk in response_stream:
            if chunk.choices and chunk.choices[0].delta.content:
                token = chunk.choices[0].delta.content
                full_assistant_reply += token
                yield token
                
        async with async_session_pool() as background_db:
            llm_response = ChatMessageORM(consultation_id=consultation_id, role="assistant", content=full_assistant_reply)
            background_db.add(llm_response)
            await background_db.commit()
        
    return StreamingResponse(database_aware_stream(), media_type="text/plain")

def _compile_system_context(intake: ComprehensiveIntakeSchema) -> str:
    behaviors_summary = ""
    for idx, b in enumerate(intake.behavior_issues, 1):
        behaviors_summary += (
            f"\[Issue #{idx}: {b.issue_title}]\n"
            f"- Target behavior: {b.target_behavior}\n"
            f"- Triggering context: {b.context}\n",
            f"- Observable body language: {b.body_language}\n"
        )
        
    return (
        f"You are a professional canine behavioral consultant certified by the Karen Pryor Academy.\n"
        f"You operate strictly under force-free, positive-reinforcement methodologies.\n\n"
        f"=== COMPREHENSIVE PATIENT DOSSIER ===\n"
        f"Dog Name: {intake.pet_name} | Breed: {intake.breed} | Age: {intake.age_years} yrs\n"
        f"Bite/Nip History: {intake.bite_or_nip_history}\n"
        f"Current Medications/Management: {intake.medical_history.management_and_medications or 'None'}\n"
        f"Reported Core Behaviors needing help:{behaviors_summary}\n"
        f"====================================\n\n"
        f"Instructions:\n"
        f"1. Interact warmly as a professional behaviorist.\n"
        f"2. ALWAYS use positive reinforcement. Never suggest physical corrections, dominance, or aversive setups.\n"
        f"3. Address the context and subtle body language details provided in the dossier.\n"
        f"4. Always treat the clients with respect.\n"
        f"5. Some things might not be obvious; do not make assumptions, and always clarify with the clients."
    )
    

@router.post("/{consultation_id}/finalize",
             response_model=ComprehensiveTrainingPlanSchema,
             status_code=status.HTTP_200_OK)
async def generate_final_training_plan(
    consultation_id: str,
    db: AsyncSession = Depends(get_db_session),
    client: AsyncOpenAI = Depends(get_llm_client)) -> ComprehensiveTrainingPlanSchema:
    
    result = await db.execute(select(ConsultationORM).where(ConsultationORM.id == consultation_id))
    consult = result.scalar_one_or_none
    if not consult:
        raise HTTPException(status_code=404, detail="Consultation is not found.")
    
    mock_intake_schema = ComprehensiveIntakeSchema(**consult.intake_snapshot)
    
    llm_messages = [{"role": "system", "content": _compile_system_context(mock_schema=mock_intake_schema)}]
    
    for msg in consult.messages:
        llm_messages.append({"role": msg.role, "content": msg.content})
        
    llm_messages.append({
        "role": "user", 
        "content": "The basic intake flow is over. Execute the tool to officially submit the initila training plan details based on our conversation."
    })
    
    tools = [
        {
            "type": "fucntion",
            "function": {
                "name": "submit_training_plan",
                "description": "Submits the finalized structured behavioral training plan to the database layout.",
                "parameters": ComprehensiveTrainingPlanSchema.model_json_schema()
            }
        }
    ]
    
    try: 
        response = await client.chat.completions.create(
            model=settings.MODEL_SLUG,
            messages=llm_messages,
            tools=tools,
            tool_choice={"type": "function", "function": {"name": "submit_training_plan"}}
        )
        
        message = response.choices[0].message
        if not message.tool_calls:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="LLM failed to invoke the mandatory data submission tool call."
            )
        
        tool_call = message.tool_calls[0]
        raw_arguments = tool_call.function.arguments
        
        parsed_json = json.loads(raw_arguments)
        plan_object = ComprehensiveTrainingPlanSchema(**parsed_json)
        
        plan_query = await db.execute(select(TrainingPlanORM).where(TrainingPlanORM.consultation_id == consultation_id))
        existing_plan = plan_query.scalar_one_or_none()
        
        if existing_plan:
            existing_plan.plan_payload = plan_object.model_dump()
        else:
            new_plan = TrainingPlanORM(
                consultation_id=consultation_id,
                plan_payload=plan_object.model_dump()
            )
            db.add(new_plan)
        
        await db.commit()
        return plan_object
    
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The model returned malformed structural JSON that could not be decoded."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Asynchronous tool call pipeline failure: {str(e)}"
        )
    