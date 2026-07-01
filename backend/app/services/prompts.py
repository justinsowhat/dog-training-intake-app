"""Prompt templates for the behavioral consulting agent.

All prompt text lives here so it can be managed/tuned independently of the
LLM orchestration logic in ``app.services.llm``. Functions here are pure string
builders — no LLM or DB access.
"""
from app.schemas.intake import ComprehensiveIntakeSchema
from app.schemas.plans import ComprehensiveTrainingPlanSchema

SYSTEM_BASE = (
    "You are a professional animal behavioral consultant certified.\n"
    "You work with all kinds of companion animals and tailor your guidance to the\n"
    "species in the dossier. You operate strictly under force-free, "
    "positive-reinforcement methodologies.\n"
)

INSTRUCTIONS = (
    "Instructions:\n"
    "1. Interact warmly as a professional behaviorist.\n"
    "2. Ask only ONE question per message. Never bundle multiple questions together or send a numbered\n"
    "   list of questions. Ask a single focused question, wait for the client's answer, then ask the next.\n"
    "   Keep each message short and conversational.\n"
    "3. ALWAYS use positive reinforcement. Never suggest physical corrections, dominance, or aversive setups.\n"
    "4. Address the context and subtle body language details provided in the dossier.\n"
    "5. Always treat the clients with respect.\n"
    "6. Some things might not be obvious; do not make assumptions, and always clarify with the clients.\n"
    "7. Keep gathering the details you need through conversation, one question at a time. Once you have enough\n"
    "   information to build a responsible, individualized plan for every reported behavior issue, call the\n"
    "   `submit_training_plan` tool to propose it. Do not call the tool prematurely while critical information\n"
    "   is still missing.\n"
)

# Rendered when a plan already exists, so the agent revises instead of regenerating.
CURRENT_PLAN_SECTION_HEADER = (
    "=== CURRENT PROPOSED PLAN (revise, do not regenerate from scratch) ===\n"
)
CURRENT_PLAN_SECTION_FOOTER = (
    "\nWhen the user asks to change, soften, add, remove, reorder, or re-pace ANYTHING in the plan,\n"
    "you MUST call `submit_training_plan` again with the COMPLETE revised plan, preserving the\n"
    "unchanged sections verbatim. The submission replaces the entire stored plan. If the user is\n"
    "only asking a question or chatting (not requesting a change), just answer conversationally and\n"
    "do NOT call the tool.\n"
    "=====================================================================\n"
)


# User-turn instruction injected by the manual /finalize endpoint to force a submission.
FINALIZE_INSTRUCTION = (
    "The basic intake flow is over. Execute the tool to officially submit the initial "
    "training plan details based on our conversation."
)

# Canned confirmation emitted after the agent proposes a plan for the first time (no extra LLM round-trip).
PLAN_PROPOSED_CONFIRMATION = (
    "I've put together a proposed training plan for {pet_name} based on everything we've covered. "
    "Take a look — tell me if you'd like to adjust any phase, soften the management steps, or add a protocol."
)

# Canned confirmation emitted after the agent REVISES an existing plan in follow-up chat.
PLAN_REVISED_CONFIRMATION = (
    "I've updated {pet_name}'s plan with that change — open the plan to see the revised version."
)


def _species_label(intake: ComprehensiveIntakeSchema) -> str:
    """Human-readable species, resolving the free-text value for 'Other'."""
    other = getattr(intake, "other_species_description", None)
    if other:
        return other
    return intake.species.value


def render_opening_suggestions_prompt(intake: ComprehensiveIntakeSchema) -> str:
    """Prompt for generating tailored opening chips from the owner's main concern."""
    first = intake.behavior_issues[0]
    concern = first.target_behavior.strip() or first.issue_title.strip()
    return (
        f"The owner of {intake.pet_name} (a {_species_label(intake)}) described their main concern as:\n"
        f'"{concern}"\n\n'
        "Generate 3 short tap-to-send replies (each 2-6 words) the owner could pick to START the "
        "conversation — concrete angles or sub-problems of this concern worth exploring first. "
        "Make them specific to what they wrote, not generic. Then add a final option exactly: "
        '"Something else". Return them via the suggest_openers tool.'
    )


def render_followup_suggestions_prompt(
    intake: ComprehensiveIntakeSchema,
    current_plan: ComprehensiveTrainingPlanSchema | None = None,
) -> str:
    """Prompt for short follow-up chips, tailored to the plan and the conversation so far.

    Unlike the opening chips (derived once from the intake), these are meant to be
    regenerated each turn so they track where the follow-up conversation has gone.
    """
    plan_context = (
        f"\n\nThe current plan covers:\n{render_plan_summary(current_plan)}"
        if current_plan is not None
        else ""
    )
    return (
        f"The owner of {intake.pet_name} (a {_species_label(intake)}) already has a training plan "
        f"and is now in the follow-up chat.{plan_context}\n\n"
        "Based on this plan and the conversation so far, generate 3-4 short tap-to-send messages "
        "(each 2-6 words) the owner is most likely to want NEXT — e.g. starting a specific protocol, "
        "handling a tricky situation, or adjusting the plan's pace. Make them specific to THIS plan "
        "and the latest exchange, not generic. Return them via the suggest_openers tool."
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
        f"Name: {intake.pet_name} | Species: {_species_label(intake)} | Breed: {intake.breed} | Age: {intake.age_years} yrs\n"
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
