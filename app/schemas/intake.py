from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator

class SexEnum(str, Enum):
    MN = "M/N" # male neutered
    FS = "F/S" # female spayed
    M = "M"
    F = "F"
    
class SpeciesEnum(str, Enum):
    DOG = "Dog"
    CAT = "Cat"
    OTHER = "Other"
    
class HumanFamilyMember(BaseModel):
    name: str
    age: Optional[int] = Field(None, description="Only specify age if under 18")
    
class NonHumanFamilyMember(BaseModel):
    species: SpeciesEnum = Field(..., description="The species of the non-human family member")
    other_species_description: Optional[str] = Field(
        None,
        description="Required if species type is 'Other'"
    )
    sex: SexEnum = Field(..., description="The biologic sex and alteration status")
    age_years: float = Field(..., gt=0.0, description="Age in years.")
    allowed_to_interact: bool = Field(..., description="Flag indicating if this anmial is allowed to interact with the consulting animal")
    
    @model_validator(mode="after")
    def validate_other_species(self) -> "NonHumanFamilyMember":
        """
        Ensures that other_species_description is provided when 'Other' is selected for species
        Returns:
            NonHumanFamilyMember: _description_
        """
        if self.species == SpeciesEnum.OTHER:
            if not self.other_species_description or not self.other_species_description.strip():
                raise ValueError("When species is set to 'Other', the description cannot be empty")
        else:
            self.other_species_description = None
            
        return self

class BehaviorIssueSection(BaseModel):
    """
    Represents an isolated behavioral issue subsection (e.g., Behavior 1, Behavior 2)
    mirroring the exact Karen Pryor Academy discovery prompts.
    """
    issue_title: str = Field(..., description="E.g., Car rides or Vet care phobia")
    target_behavior: str = Field(..., description="What is the behavior you're requesting help with?")
    reason_for_help_now: str = Field(..., description="What made you decide to seek help now?")
    duration: str = Field(..., description="How long has this behavior(s) been occurring?")
    onset: str = Field(..., description="Did it start suddenly, or has it gradually been getting worse?")
    context: str = Field(..., description="When and where does it occur?")
    antecedents: str = Field(..., description="What happens before the behavior occurs?")
    body_language: str = Field(..., description="Describe the behavior in terms of clear, observable body language.")
    
class MedicalHistorySection(BaseModel):
    sees_vet_regularly: bool
    current_vet_info: Optional[str] = None
    known_conditions: Optional[str] = None
    management_and_medications: Optional[str] = Field(None, description="List active medications like amitriptyline")
    allergies: Optional[str] = None
    concerning_unaddressed_symptoms: Optional[str] = Field(None, description="E.g., recent diarrhea or finicky appetite changes")
    
class EnvironmentalSection(BaseModel):
    diet_types: str = Field(..., description="What kind of food does your pet eat?")
    daily_amount_offered: str
    appetite_description: str = Field(..., description="How predictably does your dog eat? Appetite level?")
    delivery_method: str = Field(..., description="Bowl, puzzles, training sessions, non-contingent enrichment?")
    favorite_treats: str
    equipment_used: str = Field(..., description="Y-harness, step-in harness, martingale collar, etc.")
    exercise_routine: str = Field(..., description="Type and hours of daily exercise details.")
    sleep_patterns: str = Field(..., description="Where do they sleep and for how long?")
    average_daily_routine: str = Field(..., description="Chronological timeline of an average day.")
    
class ComprehensiveIntakeSchema(BaseModel):
    # Core Metadata
    owner_name: str = Field(..., min_length=1)
    pet_name: str = Field(..., min_length=1)
    species: SpeciesEnum = Field(default=SpeciesEnum.DOG)
    breed: str = Field(..., examples=["Greyhound"])
    sex: SexEnum
    age_years: float = Field(..., gt=0.0, examples=[1.25])
    weight_lbs: float = Field(..., gt=0.0)

    # History Background
    human_household: List[HumanFamilyMember] = Field(default_factory=list)
    non_human_household: List[NonHumanFamilyMember] = Field(default_factory=list)
    ownership_duration: str
    acquisition_source: str = Field(..., description="Where did you get him/her from?")
    known_history_details: str
    previous_homes_count: int = Field(default=0)
    historical_issues_prior_home: Optional[str] = None
    
    # Global Behavior Query
    bite_or_nip_history: str = Field(..., description="Has your pet bitten or nipped a person or animal? Was law enforcement involved?")
    
    # Dynamic Behavioral Subsections (Crucial Matrix Element)
    behavior_issues: List[BehaviorIssueSection] = Field(
        ..., 
        min_length=1, 
        description="Array containing multiple individual behavioral issues requiring custom training plans."
    )
    
    # Training History Context
    existing_trained_behaviors: str
    training_methodologies: str = Field(..., description="How did you train these behaviors?")
    available_training_time_weekly: str
    completed_on_demand_courses: str

    # Health & Environment
    medical_history: MedicalHistorySection
    environment: EnvironmentalSection
    additional_notes: Optional[str] = Field(None, description="Other things not covered by this intake form but you think it's important to mention")

    # --- Data Integrity Check ---
    @field_validator("behavior_issues")
    @classmethod
    def ensure_distinct_issues(cls, v: List[BehaviorIssueSection]) -> List[BehaviorIssueSection]:
        if not v:
            raise ValueError("You must supply at least 1 behavioral subsection layout for evaluation.")
        return v