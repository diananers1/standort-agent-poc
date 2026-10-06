from standort_agent.agents.base import SignalAgent
from standort_agent.models import (
    InterpretedProfile,
    Municipality,
    SignalResult,
)
from standort_agent.scoring.normalization import (
    log_min_max_normalize,
    min_max_normalize,
)


class DemographicAgent(SignalAgent):

    def evaluate(
        self,
        municipality: Municipality,
        profile: InterpretedProfile,
        municipalities: list[Municipality],
    ) -> SignalResult:

        weights = profile.target_age_weights

        def age_match(item: Municipality) -> float:
            age = item.altersverteilung

            return (
                age.age_18_34 * weights.age_18_34
                + age.age_35_54 * weights.age_35_54
                + age.age_55_plus * weights.age_55_plus
            )

        all_matches = [
            age_match(item)
            for item in municipalities
        ]

        raw_age_match = age_match(municipality)

        age_fit_score = min_max_normalize(
            raw_age_match,
            min(all_matches),
            max(all_matches),
        )

        populations = [
            item.einwohner
            for item in municipalities
        ]

        population_score = log_min_max_normalize(
            municipality.einwohner,
            min(populations),
            max(populations),
        )

        demographic_score = (
            0.70 * age_fit_score
            + 0.30 * population_score
        )

        estimated_target_population = int(
            municipality.einwohner
            * raw_age_match
        )

        return SignalResult(
            signal="demographics",
            score=demographic_score,
            raw_value=raw_age_match,
            reason=(
                f"Target-group compatibility is "
                f"{raw_age_match:.1%}; estimated target-market "
                f"size is about {estimated_target_population:,} residents."
            ),
        )