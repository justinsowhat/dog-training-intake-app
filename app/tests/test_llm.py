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
    assert tool["type"] == "function"  # regression: was "fucntion"
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
    assert plan_event.plan.dog_name == "Rex"
    assert sink.proposed_plan is not None
    assert sink.assistant_text == "Let me draft that. "


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
    fake.stream_chunks = [tool_chunk(0, name="submit_training_plan", args=json.dumps({"dog_name": "Rex"}))]
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
    assert wire["plan"]["dog_name"] == "Rex"
    assert "text" not in wire
    # round-trips through JSON
    assert json.loads(json.dumps(wire))["plan"]["dog_name"] == "Rex"


# --- forced plan generation ------------------------------------------------

async def test_generate_forced_plan_success_appends_finalize_instruction():
    fake = FakeLLMClient()
    fake.completion = completion_with_tool(json.dumps(plan_payload()))

    plan = await llm.generate_forced_plan(fake, _intake(), [], None)

    assert plan.dog_name == "Rex"
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
