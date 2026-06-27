"""Sample payloads and fake OpenAI-SDK objects for tests.

The fakes mimic the small slice of the OpenAI streaming/non-streaming response
shapes that ``app.services.llm`` actually touches (``choices[0].delta`` with
``content``/``tool_calls`` for streaming, ``choices[0].message.tool_calls`` for
the forced call).
"""
from types import SimpleNamespace


# --- Domain payloads -------------------------------------------------------

def intake_payload() -> dict:
    """A valid ComprehensiveIntakeSchema body."""
    return {
        "owner_name": "Sam",
        "pet_name": "Rex",
        "breed": "Greyhound",
        "sex": "M",
        "age_years": 2.0,
        "weight_lbs": 60.0,
        "ownership_duration": "1 year",
        "acquisition_source": "shelter",
        "known_history_details": "unknown",
        "bite_or_nip_history": "none",
        "behavior_issues": [
            {
                "issue_title": "Car phobia",
                "target_behavior": "panic in car",
                "reason_for_help_now": "upcoming vet trips",
                "duration": "6 months",
                "onset": "gradual",
                "context": "during car rides",
                "antecedents": "seeing the leash",
                "body_language": "panting, trembling",
            }
        ],
        "existing_trained_behaviors": "sit",
        "training_methodologies": "clicker",
        "available_training_time_weekly": "3h",
        "completed_on_demand_courses": "none",
        "medical_history": {"sees_vet_regularly": True},
        "environment": {
            "diet_types": "kibble",
            "daily_amount_offered": "2 cups",
            "appetite_description": "good",
            "delivery_method": "bowl",
            "favorite_treats": "cheese",
            "equipment_used": "harness",
            "exercise_routine": "daily walks",
            "sleep_patterns": "crate",
            "average_daily_routine": "walk, nap, play",
        },
    }


def plan_payload(pet_name: str = "Rex", triage: str = "anxious in cars") -> dict:
    """A valid ComprehensiveTrainingPlanSchema body."""
    return {
        "pet_name": pet_name,
        "triage_summary": triage,
        "individualized_plans": [
            {
                "issue_title": "Car phobia",
                "immediate_management": {"setup": "park facing away", "tools_needed": ["mat"]},
                "training_protocols": [
                    {
                        "skill_name": "Mat Stationing",
                        "step_by_step": ["intro mat", "reward contact"],
                        "success_criteria": "stays on mat 10s",
                    }
                ],
            }
        ],
        "emergency_protocol": "end the session and create distance",
    }


# --- Fake streaming chunks -------------------------------------------------

def text_chunk(text: str) -> SimpleNamespace:
    delta = SimpleNamespace(content=text, tool_calls=None)
    return SimpleNamespace(choices=[SimpleNamespace(delta=delta)])


def tool_chunk(index: int, name: str | None = None, args: str | None = None) -> SimpleNamespace:
    frag = SimpleNamespace(index=index, function=SimpleNamespace(name=name, arguments=args))
    delta = SimpleNamespace(content=None, tool_calls=[frag])
    return SimpleNamespace(choices=[SimpleNamespace(delta=delta)])


def empty_chunk() -> SimpleNamespace:
    """A keep-alive style chunk with no choices (must be tolerated)."""
    return SimpleNamespace(choices=[])


# --- Fake non-streaming completion -----------------------------------------

def completion_with_tool(args_json: str, name: str = "submit_training_plan") -> SimpleNamespace:
    tc = SimpleNamespace(function=SimpleNamespace(name=name, arguments=args_json))
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(tool_calls=[tc]))])


def completion_without_tool() -> SimpleNamespace:
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(tool_calls=None))])


# --- Fake client -----------------------------------------------------------

class FakeCompletions:
    def __init__(self, owner: "FakeLLMClient") -> None:
        self._owner = owner

    async def create(self, **kwargs):
        self._owner.calls.append(kwargs)
        if kwargs.get("stream"):
            chunks = list(self._owner.stream_chunks)

            async def _gen():
                for c in chunks:
                    yield c

            return _gen()
        return self._owner.completion


class FakeLLMClient:
    """Stand-in for AsyncOpenAI. Configure ``stream_chunks`` or ``completion`` per test."""

    def __init__(self) -> None:
        self.calls: list[dict] = []
        self.stream_chunks: list = []
        self.completion = None
        self.chat = SimpleNamespace(completions=FakeCompletions(self))
