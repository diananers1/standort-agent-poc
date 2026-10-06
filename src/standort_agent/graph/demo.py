from pathlib import Path

from standort_agent.graph.workflow import location_graph
from standort_agent.loader import (
    load_business_profile,
    load_municipalities,
)


def main():
    data_dir = Path(__file__).resolve().parents[3] / "data"
    dataset = load_municipalities(
        data_dir / "municipalities.json"
    )

    profile = load_business_profile(
        data_dir / "examples" / "profil_1.json"
    )

    result = location_graph.invoke(
        {
            "raw_profile": profile,
            "municipalities": dataset.municipalities,
        }
    )

    for index, evaluation in enumerate(
        result["top_results"],
        start=1,
    ):
        print(
            f"{index}. "
            f"{evaluation.municipality.gemeinde} "
            f"{evaluation.total_score:.1f}/100"
        )


if __name__ == "__main__":
    main()
