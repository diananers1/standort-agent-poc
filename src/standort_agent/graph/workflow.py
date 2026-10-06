from typing import Literal

from langgraph.graph import END, START, StateGraph

from standort_agent.agents.demographics import (
    DemographicAgent,
)
from standort_agent.agents.poi import POIAgent
from standort_agent.agents.rent import RentAgent
from standort_agent.agents.transit import TransitAgent

from standort_agent.graph.state import LocationState

from standort_agent.interpretation.rules import (
    interpret_profile,
    profile_input_errors,
)

from standort_agent.scoring.aggregator import (
    rank_municipalities,
)

from standort_agent.scoring.regions import (
    filter_by_region,
)


def validate_scope_node(
    state: LocationState,
) -> LocationState:
    """
    Reject requests outside the geographic scope of the
    Austrian dataset.
    """
    profile = state["raw_profile"]

    errors = profile_input_errors(profile)
    if errors:
        return {"error": "\n\n".join(errors)}

    return {}


def route_after_validation(
    state: LocationState,
) -> Literal[
    "interpret_profile",
    "end",
]:
    """
    Decide whether the workflow should continue.
    """
    if state.get("error"):
        return "end"

    return "interpret_profile"


def interpret_profile_node(
    state: LocationState,
) -> LocationState:
    """
    Convert free-text business input into a structured
    representation used by the scoring system.
    """
    raw_profile = state["raw_profile"]

    interpreted = interpret_profile(
        raw_profile
    )

    return {
        "interpreted_profile": interpreted
    }


def filter_region_node(
    state: LocationState,
) -> LocationState:
    """
    Filter the Austrian dataset according to the requested
    city or federal state.
    """
    profile = state["interpreted_profile"]

    candidates = filter_by_region(
        municipalities=state["municipalities"],
        preferred_locations=profile.preferred_locations,
    )

    if not candidates:
        return {
            "candidate_municipalities": [],
            "error": (
                "No municipalities in the current dataset "
                "match the requested regional preference."
            ),
        }

    return {
        "candidate_municipalities": candidates
    }


def route_after_region_filter(
    state: LocationState,
) -> Literal[
    "evaluate_locations",
    "end",
]:
    if state.get("error"):
        return "end"

    return "evaluate_locations"


def evaluate_locations_node(
    state: LocationState,
) -> LocationState:
    """
    Run the four specialist agents and aggregate their
    normalized scores.
    """
    candidates = state[
        "candidate_municipalities"
    ]

    all_municipalities = state[
        "municipalities"
    ]

    profile = state[
        "interpreted_profile"
    ]

    agents = [
        DemographicAgent(),
        POIAgent(),
        RentAgent(),
        TransitAgent(),
    ]

    rankings = rank_municipalities(
        municipalities=candidates,
        profile=profile,
        agents=agents,
        normalization_population=all_municipalities,
    )

    return {
        "rankings": rankings,
        "top_results": rankings[:5],
    }


def build_location_graph():
    """
    Build and compile the LangGraph workflow.
    """
    builder = StateGraph(
        LocationState
    )

    builder.add_node(
        "validate_scope",
        validate_scope_node,
    )

    builder.add_node(
        "interpret_profile",
        interpret_profile_node,
    )

    builder.add_node(
        "filter_region",
        filter_region_node,
    )

    builder.add_node(
        "evaluate_locations",
        evaluate_locations_node,
    )

    # START
    builder.add_edge(
        START,
        "validate_scope",
    )

    # Scope validation can either continue or stop.
    builder.add_conditional_edges(
        "validate_scope",
        route_after_validation,
        {
            "interpret_profile": "interpret_profile",
            "end": END,
        },
    )

    builder.add_edge(
        "interpret_profile",
        "filter_region",
    )

    # Region filtering can also stop if there are no candidates.
    builder.add_conditional_edges(
        "filter_region",
        route_after_region_filter,
        {
            "evaluate_locations": "evaluate_locations",
            "end": END,
        },
    )

    builder.add_edge(
        "evaluate_locations",
        END,
    )

    return builder.compile()


location_graph = build_location_graph()