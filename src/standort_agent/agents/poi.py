from standort_agent.agents.base import SignalAgent
from standort_agent.models import (
    InterpretedProfile,
    Municipality,
    SignalResult,
)
from standort_agent.scoring.normalization import (
    min_max_normalize,
)


class POIAgent(SignalAgent):

    def evaluate(
        self,
        municipality: Municipality,
        profile: InterpretedProfile,
        municipalities: list[Municipality],
    ) -> SignalResult:

        values = [
            item.poi_dichte
            for item in municipalities
        ]

        score = min_max_normalize(
            municipality.poi_dichte,
            min(values),
            max(values),
        )

        return SignalResult(
            signal="poi",
            score=score,
            raw_value=municipality.poi_dichte,
            reason=(
                f"POI density is "
                f"{municipality.poi_dichte:.1f}/10. "
                "This is used as a proxy for surrounding "
                "commercial activity, not direct competition."
            ),
        )