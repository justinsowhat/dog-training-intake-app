"""Prompt templates for the behavioral consulting agent.

All prompt text lives here so it can be managed/tuned independently of the
LLM orchestration logic in ``backend.services.llm``. Functions here are pure string
builders — no LLM or DB access.
"""
from backend.schemas.intake import ComprehensiveIntakeSchema
from backend.schemas.plans import ComprehensiveTrainingPlanSchema

SYSTEM_BASE = (
    "You are a professional canine behavioral consultant certified.\n"
    "You operate strictly under force-free, positive-reinforcement methodologies.\n"
)

INSTRUCTIONS = (
    "Instructions:\n"
    "1. Interact warmly as a professional behaviorist.\n"
    "2. ALWAYS use positive reinforcement. Never suggest physical corrections, dominance, or aversive setups.\n"
    "3. Address the context and subtle body language details provided in the dossier.\n"
    "4. Always treat the clients with respect.\n"
    "5. Some things might not be obvious; do not make assumptions, and always clarify with the clients.\n"
    "6. Keep gathering the details you need through conversation. Once you have enough information to build a\n"
    "   responsible, individualized plan for every reported behavior issue, call the `submit_training_plan`\n"
    "   tool to propose it. Do not call the tool prematurely while critical information is still missing.\n"
)

# Rendered when a plan already exists, so the agent revises instead of regenerating.
CURRENT_PLAN_SECTION_HEADER = (
    "=== CURRENT PROPOSED PLAN (revise, do not regenerate from scratch) ===\n"
)
CURRENT_PLAN_SECTION_FOOTER = (
    "\nWhen the user requests changes, call `submit_training_plan` again with the FULL revised plan,\n"
    "preserving unchanged sections verbatim. The submission replaces the entire stored plan.\n"
    "=====================================================================\n"
)

# User-turn instruction injected by the manual /finalize endpoint to force a submission.
FINALIZE_INSTRUCTION = (
    "The basic intake flow is over. Execute the tool to officially submit the initial "
    "training plan details based on our conversation."
)

# Canned confirmation emitted after the agent proposes/revises a plan (no extra LLM round-trip).
PLAN_PROPOSED_CONFIRMATION = (
    "I've put together a proposed training plan for {dog_name} based on everything we've covered. "
    "Take a look — tell me if you'd like to adjust any phase, soften the management steps, or add a protocol."
)


def _render_behavior_summary(intake: ComprehensiveIntakeSchema) -> str:
    summary = ""
    for idx, b in enumerate(intake.behavior_issues, 1):
        summary += (
            f"[Issue #{idx}: {b.issue_title}]\n"
            f"- Target behavior: {b.target_behavior}\n"
            f"- Triggering context: {b.context}\n"
            f"- Observable body language: {b.body_language}\n"
        )
    return summary


def _render_dossier(intake: ComprehensiveIntakeSchema) -> str:
    return (
        "=== COMPREHENSIVE PATIENT DOSSIER ===\n"
        f"Dog Name: {intake.pet_name} | Breed: {intake.breed} | Age: {intake.age_years} yrs\n"
        f"Bite/Nip History: {intake.bite_or_nip_history}\n"
        f"Current Medications/Management: {intake.medical_history.management_and_medications or 'None'}\n"
        f"Reported Core Behaviors needing help:\n{_render_behavior_summary(intake)}"
        "====================================\n"
    )


def render_plan_summary(plan: ComprehensiveTrainingPlanSchema) -> str:
    """Compact, human-readable rendering of a plan (used in context, not raw JSON)."""
    lines = [f"Triage summary: {plan.triage_summary}"]
    for ip in plan.individualized_plans:
        lines.append(f"\nIssue: {ip.issue_title}")
        lines.append(f"  Immediate management: {ip.immediate_management.setup}")
        lines.append(f"  Tools: {', '.join(ip.immediate_management.tools_needed)}")
        for proto in ip.training_protocols:
            lines.append(f"  Protocol '{proto.skill_name}': {proto.success_criteria}")
    lines.append(f"\nEmergency protocol: {plan.emergency_protocol}")
    return "\n".join(lines)


def render_system_context(
    intake: ComprehensiveIntakeSchema,
    current_plan: ComprehensiveTrainingPlanSchema | None = None,
) -> str:
    parts = [
        SYSTEM_BASE,
        "\n",
        _render_dossier(intake),
        "\n",
        INSTRUCTIONS,
    ]
    if current_plan is not None:
        parts += [
            "\n",
            CURRENT_PLAN_SECTION_HEADER,
            render_plan_summary(current_plan),
            CURRENT_PLAN_SECTION_FOOTER,
        ]
    return "".join(parts)
