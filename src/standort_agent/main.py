from pathlib import Path

from standort_agent.agents.demographics import (
    DemographicAgent,
)
from standort_agent.agents.poi import POIAgent
from standort_agent.agents.rent import RentAgent
from standort_agent.agents.transit import TransitAgent
from standort_agent.interpretation.rules import (
    interpret_profile,
)
from standort_agent.loader import (
    load_business_profile,
    load_municipalities,
)
from standort_agent.scoring.aggregator import (
    rank_municipalities,
)
from standort_agent.scoring.weighting import (
    get_weights,
)


def main() -> None:
    data_dir = Path(__file__).resolve().parents[2] / "data"
    dataset = load_municipalities(
        data_dir / "municipalities.json"
    )

    raw_profile = load_business_profile(
        data_dir / "examples" / "profil_1.json"
    )

    profile = interpret_profile(raw_profile)

    agents = [
        DemographicAgent(),
        POIAgent(),
        RentAgent(),
        TransitAgent(),
    ]

    rankings = rank_municipalities(
        municipalities=dataset.municipalities,
        profile=profile,
        agents=agents,
    )

    print()
    print("Business profile")
    print("----------------")
    print(raw_profile.model_dump())
    print()

    print("Interpreted profile")
    print("-------------------")
    print(profile.model_dump())
    print()

    print("Weights")
    print("-------")
    print(get_weights(profile))
    print()

    print("Location ranking")
    print("----------------")

    for index, evaluation in enumerate(
        rankings[:5],
        start=1,
    ):
        print(
            f"{index}. "
            f"{evaluation.municipality.gemeinde} "
            f"- {evaluation.total_score:.1f}/100"
        )

        for signal in evaluation.signals.values():
            print(
                f"   {signal.signal:15} "
                f"{signal.score:5.1f} "
                f"| {signal.reason}"
            )

        print()


if __name__ == "__main__":
    main()
