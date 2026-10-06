from standort_agent.agents.base import SignalAgent
from standort_agent.models import (
    InterpretedProfile,
    Municipality,
    MunicipalityEvaluation,
)
from standort_agent.scoring.weighting import (
    get_weights,
)


def evaluate_municipality(
    municipality: Municipality,
    profile: InterpretedProfile,
    municipalities: list[Municipality],
    agents: list[SignalAgent],
) -> MunicipalityEvaluation:

    results = {
        result.signal: result
        for result in (
            agent.evaluate(
                municipality=municipality,
                profile=profile,
                municipalities=municipalities,
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
) -> list[MunicipalityEvaluation]:

    evaluations = [
        evaluate_municipality(
            municipality=municipality,
            profile=profile,
            municipalities=municipalities,
            agents=agents,
        )
        for municipality in municipalities
    ]

    return sorted(
        evaluations,
        key=lambda item: item.total_score,
        reverse=True,
    )