from standort_agent.agents.base import SignalAgent
from standort_agent.models import (
    InterpretedProfile,
    Municipality,
    SignalResult,
)


def affordability_score(
    ratio: float,
) -> float:
    """
    ratio =
        estimated monthly rent
        /
        monthly rent budget
    """

    if ratio <= 0.80:
        return 100.0

    if ratio <= 1.00:
        # 80% -> 100
        # 100% -> 80
        progress = (ratio - 0.80) / 0.20
        return 100.0 - progress * 20.0

    if ratio <= 1.25:
        # 100% -> 80
        # 125% -> 30
        progress = (ratio - 1.00) / 0.25
        return 80.0 - progress * 50.0

    if ratio <= 1.50:
        # 125% -> 30
        # 150% -> 0
        progress = (ratio - 1.25) / 0.25
        return 30.0 - progress * 30.0

    return 0.0


class RentAgent(SignalAgent):

    def evaluate(
        self,
        municipality: Municipality,
        profile: InterpretedProfile,
        municipalities: list[Municipality],
    ) -> SignalResult:

        estimated_monthly_rent = (
            municipality.mietindex_eur_m2
            * profile.flaeche_m2
        )

        ratio = (
            estimated_monthly_rent
            / profile.budget_miete_eur
        )

        score = affordability_score(ratio)

        difference = (
            estimated_monthly_rent
            - profile.budget_miete_eur
        )

        if difference <= 0:
            reason = (
                f"Estimated rent is €{estimated_monthly_rent:,.0f}/month, "
                f"€{abs(difference):,.0f} below the budget."
            )
        else:
            reason = (
                f"Estimated rent is €{estimated_monthly_rent:,.0f}/month, "
                f"€{difference:,.0f} above the budget."
            )

        return SignalResult(
            signal="rent",
            score=score,
            raw_value=estimated_monthly_rent,
            reason=reason,
        )