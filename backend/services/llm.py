"""LLM orchestration for the behavioral consulting agent.

Owns all LLM I/O and tool-call parsing. Deliberately free of SQLAlchemy: callers
load the data the service needs (intake, history, current plan) and persist any
side effects themselves. The AsyncOpenAI client is passed in (preserving the
existing ``Depends(get_llm_client)`` dependency injection).
"""
import json
from collections.abc import AsyncGenerator
from dataclasses import dataclass

from openai import AsyncOpenAI
from pydantic import ValidationError

from backend.core.config import settings
from backend.schemas.intake import ComprehensiveIntakeSchema
from backend.schemas.plans import ComprehensiveTrainingPlanSchema
from backend.services import prompts

PLAN_TOOL_NAME = "submit_training_plan"


class PlanGenerationError(Exception):
    """Raised when the model fails to produce a valid training plan."""


@dataclass
class ChatTurn:
    """Neutral representation of one stored conversation row."""
    role: str  # "user" | "assistant" | "assistant_plan"
    content: str


@dataclass
class StreamEvent:
    """A single event yielded by an agentic turn."""
    type: str  # "token" | "plan" | "message" | "error" | "done"
    text: str | None = None
    plan: ComprehensiveTrainingPlanSchema | None = None

    def to_wire(self) -> dict:
        out: dict = {"type": self.type}
        if self.text is not None:
            out["text"] = self.text
        if self.plan is not None:
            out["plan"] = self.plan.model_dump()
        return out


@dataclass
class AgentTurnResult:
    """Accumulated side effects for the route to persist after streaming."""
    assistant_text: str = ""
    proposed_plan: ComprehensiveTrainingPlanSchema | None = None


def build_plan_tool() -> dict:
    return {
        "type": "function",
        "function": {
            "name": PLAN_TOOL_NAME,
            "description": "Submits the finalized structured behavioral training plan to the database layer.",
            "parameters": ComprehensiveTrainingPlanSchema.model_json_schema(),
        },
    }


def _render_history_turn(turn: ChatTurn) -> dict:
    """Map a stored turn into an OpenAI chat message.

    ``assistant_plan`` rows store the proposed plan as JSON; render them back into
    a compact assistant text line so the model knows it already proposed a plan.
    """
    if turn.role == "assistant_plan":
        try:
            plan = ComprehensiveTrainingPlanSchema(**json.loads(turn.content))
            rendered = prompts.render_plan_summary(plan)
        except (json.JSONDecodeError, ValidationError, TypeError):
            rendered = turn.content
        return {"role": "assistant", "content": f"[Proposed training plan]\n{rendered}"}
    return {"role": turn.role, "content": turn.content}


def build_messages(
    intake: ComprehensiveIntakeSchema,
    history: list[ChatTurn],
    current_plan: ComprehensiveTrainingPlanSchema | None,
) -> list[dict]:
    messages = [{"role": "system", "content": prompts.render_system_context(intake, current_plan)}]
    messages.extend(_render_history_turn(t) for t in history)
    return messages


def _parse_plan_arguments(raw_arguments: str) -> ComprehensiveTrainingPlanSchema:
    parsed = json.loads(raw_arguments)
    return ComprehensiveTrainingPlanSchema(**parsed)


async def stream_agent_turn(
    client: AsyncOpenAI,
    intake: ComprehensiveIntakeSchema,
    history: list[ChatTurn],
    current_plan: ComprehensiveTrainingPlanSchema | None,
    result_sink: AgentTurnResult,
) -> AsyncGenerator[StreamEvent, None]:
    """Stream one autonomous, tool-aware turn.

    Yields ``token`` events for conversational text and, if the model decides to
    propose a plan, a ``plan`` event followed by a canned ``message`` event. The
    accumulated text/plan are written to ``result_sink`` for the caller to persist.
    """
    messages = build_messages(intake, history, current_plan)

    response_stream = await client.chat.completions.create(
        model=settings.MODEL_SLUG,
        messages=messages,
        tools=[build_plan_tool()],
        tool_choice="auto",
        stream=True,
    )

    assistant_text = ""
    tool_args_by_index: dict[int, str] = {}
    tool_name_by_index: dict[int, str] = {}

    async for chunk in response_stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        if delta.content:
            assistant_text += delta.content
            yield StreamEvent(type="token", text=delta.content)
        if delta.tool_calls:
            for tc in delta.tool_calls:
                i = tc.index
                if tc.function and tc.function.name:
                    tool_name_by_index[i] = tc.function.name
                if tc.function and tc.function.arguments:
                    tool_args_by_index[i] = tool_args_by_index.get(i, "") + tc.function.arguments

    result_sink.assistant_text = assistant_text

    # Resolve a plan submission, if any.
    for i, raw_arguments in tool_args_by_index.items():
        if tool_name_by_index.get(i) != PLAN_TOOL_NAME:
            continue
        try:
            plan = _parse_plan_arguments(raw_arguments)
        except (json.JSONDecodeError, ValidationError) as exc:
            yield StreamEvent(type="error", text=f"The model returned an invalid training plan: {exc}")
            break
        result_sink.proposed_plan = plan
        yield StreamEvent(type="plan", plan=plan)
        yield StreamEvent(
            type="message",
            text=prompts.PLAN_PROPOSED_CONFIRMATION.format(dog_name=plan.dog_name),
        )
        break

    yield StreamEvent(type="done")


async def generate_forced_plan(
    client: AsyncOpenAI,
    intake: ComprehensiveIntakeSchema,
    history: list[ChatTurn],
    current_plan: ComprehensiveTrainingPlanSchema | None = None,
) -> ComprehensiveTrainingPlanSchema:
    """Force a plan submission (used by the manual /finalize endpoint)."""
    messages = build_messages(intake, history, current_plan)
    messages.append({"role": "user", "content": prompts.FINALIZE_INSTRUCTION})

    response = await client.chat.completions.create(
        model=settings.MODEL_SLUG,
        messages=messages,
        tools=[build_plan_tool()],
        tool_choice={"type": "function", "function": {"name": PLAN_TOOL_NAME}},
    )

    message = response.choices[0].message
    if not message.tool_calls:
        raise PlanGenerationError("LLM failed to invoke the mandatory data submission tool call.")

    try:
        return _parse_plan_arguments(message.tool_calls[0].function.arguments)
    except json.JSONDecodeError as exc:
        raise PlanGenerationError("The model returned malformed structural JSON that could not be decoded.") from exc
    except ValidationError as exc:
        raise PlanGenerationError(f"The model returned a structurally invalid plan: {exc}") from exc
