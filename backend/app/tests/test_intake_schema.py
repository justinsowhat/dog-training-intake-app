import pytest
from pydantic import ValidationError

from app.schemas.intake import ComprehensiveIntakeSchema, SpeciesEnum
from app.tests.factories import intake_payload


def test_defaults_to_dog_with_no_other_description():
    intake = ComprehensiveIntakeSchema(**intake_payload())
    assert intake.species == SpeciesEnum.DOG
    assert intake.other_species_description is None


def test_other_species_requires_description():
    payload = intake_payload()
    payload["species"] = "Other"
    with pytest.raises(ValidationError):
        ComprehensiveIntakeSchema(**payload)


def test_other_species_accepts_description():
    payload = intake_payload()
    payload["species"] = "Other"
    payload["other_species_description"] = "Ferret"
    intake = ComprehensiveIntakeSchema(**payload)
    assert intake.other_species_description == "Ferret"


def test_non_other_species_clears_stray_description():
    payload = intake_payload()
    payload["species"] = "Cat"
    payload["other_species_description"] = "ignored"
    intake = ComprehensiveIntakeSchema(**payload)
    assert intake.other_species_description is None
