from typing import TypedDict

from standort_agent.models import (
    BusinessProfile,
    InterpretedProfile,
    Municipality,
    MunicipalityEvaluation,
)


class LocationState(TypedDict, total=False):
    # Original user input
    raw_profile: BusinessProfile

    # Structured interpretation of user input
    interpreted_profile: InterpretedProfile

    # Complete Austrian dataset
    municipalities: list[Municipality]

    # Municipalities remaining after region filtering
    candidate_municipalities: list[Municipality]

    # Complete ranked candidate list
    rankings: list[MunicipalityEvaluation]

    # First five recommendations
    top_results: list[MunicipalityEvaluation]

    # Used when the workflow cannot continue
    error: str
    llm_status: str
    customer_explanation: str