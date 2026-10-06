from standort_agent.agents.base import SignalAgent
from standort_agent.models import (
    InterpretedProfile,
    Municipality,
    SignalResult,
)


class TransitAgent(SignalAgent):

    def evaluate(
        self,
        municipality: Municipality,
        profile: InterpretedProfile,
        municipalities: list[Municipality],
    ) -> SignalResult:

        score = municipality.oev_score * 10.0

        return SignalResult(
            signal="transit",
            score=score,
            raw_value=municipality.oev_score,
            reason=(
                f"Public transport connectivity is "
                f"{municipality.oev_score:.1f}/10."
            ),
        )