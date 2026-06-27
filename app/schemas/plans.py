from pydantic import BaseModel, Field

class ManagementStep(BaseModel):
    setup: str = Field(..., description="Environmental change to prevent the behavior from occurring (e.g., plastic on walls, parking facing away).")
    tools_needed: list[str] = Field(..., description="Specific positive-reinforcement equipment required.")

class SkillProtocol(BaseModel):
    skill_name: str = Field(..., description="Name of the behavior (e.g., '1-2-3 Game', 'Voluntary Mat Stationing').")
    step_by_step: list[str] = Field(..., description="Granular, errorless training phases for the owner to execute.")
    success_criteria: str = Field(..., description="Clear criteria dictating when to advance to the next micro-stage.")

class BehaviorPlanMatrix(BaseModel):
    issue_title: str = Field(..., description="The matching title from the behavior section profile (e.g., 'Car Rides Panic')[cite: 1].")
    immediate_management: ManagementStep = Field(..., description="Steps to completely lower environmental stress right now.")
    training_protocols: list[SkillProtocol] = Field(..., description="Force-free skill-building loops targeting this specific issue.")

class ComprehensiveTrainingPlanSchema(BaseModel):
    """
    The final production-grade payload delivered cleanly to the data layer.
    """
    dog_name: str
    triage_summary: str = Field(..., description="Overall behavioral analysis synthesizing trigger tracking and history markers.")
    individualized_plans: list[BehaviorPlanMatrix] = Field(..., description="Breakdown per requested behavior section.")
    emergency_protocol: str = Field(..., description="What the owner must do if a threshold freeze or overstimulation nip occurs.")