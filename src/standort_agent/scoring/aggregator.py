from standort_agent.agents.base import SignalAgent
from standort_agent.models import (
    InterpretedProfile,
    Municipality,
    MunicipalityEvaluation,
)
from standort_agent.scoring.weighting import get_weights


def evaluate_municipality(
    municipality: Municipality,
    profile: InterpretedProfile,
    normalization_population: list[Municipality],
    agents: list[SignalAgent],
) -> MunicipalityEvaluation:
    """
    Evaluate one municipality.

    normalization_population is the complete reference dataset
    used by agents when relative normalization is required.
    """

    results = {
        result.signal: result
        for result in (
            agent.evaluate(
                municipality=municipality,
                profile=profile,
                municipalities=normalization_population,
            )
            for agent in agents
        )
    }

    weights = get_weights(profile)

    total_score = sum(
        results[signal].score * weight
        for signal, weight in weights.items()
    )

    return MunicipalityEvaluation(
        municipality=municipality,
        signals=results,
        total_score=total_score,
    )


def rank_municipalities(
    municipalities: list[Municipality],
    profile: InterpretedProfile,
    agents: list[SignalAgent],
    normalization_population: list[Municipality] | None = None,
) -> list[MunicipalityEvaluation]:
    """
    Rank candidate municipalities.

    Candidate municipalities may be filtered by region, while
    normalization_population can remain the complete Austrian
    dataset.

    If no separate normalization population is supplied, the
    candidate list itself is used for backwards compatibility.
    """

    reference_population = (
        normalization_population
        if normalization_population is not None
        else municipalities
    )

    evaluations = [
        evaluate_municipality(
            municipality=municipality,
            profile=profile,
            normalization_population=reference_population,
            agents=agents,
        )
        for municipality in municipalities
    ]

    return sorted(
        evaluations,
        key=lambda item: item.total_score,
        reverse=True,
    )