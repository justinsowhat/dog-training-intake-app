from backend.schemas.intake import ComprehensiveIntakeSchema
from backend.schemas.plans import ComprehensiveTrainingPlanSchema
from backend.services import prompts
from backend.tests.factories import intake_payload, plan_payload


def _intake() -> ComprehensiveIntakeSchema:
    return ComprehensiveIntakeSchema(**intake_payload())


def _plan() -> ComprehensiveTrainingPlanSchema:
    return ComprehensiveTrainingPlanSchema(**plan_payload())


def test_behavior_summary_renders_each_issue_without_crashing():
    # Regression: a trailing comma here previously made this a tuple -> TypeError.
    summary = prompts._render_behavior_summary(_intake())
    assert "Issue #1: Car phobia" in summary
    assert "panting, trembling" in summary
    assert "during car rides" in summary


def test_render_system_context_includes_dossier_and_instructions():
    ctx = prompts.render_system_context(_intake())
    assert "COMPREHENSIVE PATIENT DOSSIER" in ctx
    assert "Rex" in ctx and "Greyhound" in ctx
    assert "submit_training_plan" in ctx  # instruction telling the model when to call the tool
    assert "CURRENT PROPOSED PLAN" not in ctx  # no plan yet


def test_render_system_context_appends_current_plan_section():
    ctx = prompts.render_system_context(_intake(), _plan())
    assert "CURRENT PROPOSED PLAN" in ctx
    assert "stays on mat 10s" in ctx
    assert "revise" in ctx.lower()


def test_render_plan_summary_is_compact_text_not_json():
    summary = prompts.render_plan_summary(_plan())
    assert "Triage summary: anxious in cars" in summary
    assert "Mat Stationing" in summary
    assert "{" not in summary  # human-readable, not raw JSON


def test_finalize_instruction_has_no_typo():
    assert "initial" in prompts.FINALIZE_INSTRUCTION
    assert "initila" not in prompts.FINALIZE_INSTRUCTION


def test_confirmation_message_interpolates_dog_name():
    assert "Rex" in prompts.PLAN_PROPOSED_CONFIRMATION.format(dog_name="Rex")
