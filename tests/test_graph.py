from pathlib import Path

from standort_agent.graph.workflow import (
    location_graph,
)
from standort_agent.loader import (
    load_business_profile,
    load_municipalities,
)


DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def test_location_graph_runs_end_to_end():
    dataset = load_municipalities(
        DATA_DIR / "municipalities.json"
    )

    profile = load_business_profile(
        DATA_DIR / "examples" / "profil_2.json"
    )

    result = location_graph.invoke(
        {
            "raw_profile": profile,
            "municipalities": dataset.municipalities,
        }
    )

    assert "interpreted_profile" in result
    assert "rankings" in result
    assert len(result["rankings"]) == 20
    assert len(result["top_results"]) == 5


def test_location_graph_filters_vienna():
    dataset = load_municipalities(DATA_DIR / "municipalities.json")
    profile = load_business_profile(DATA_DIR / "examples" / "profil_1.json")
    result = location_graph.invoke({
        "raw_profile": profile,
        "municipalities": dataset.municipalities,
    })
    expected = {item.gemeinde for item in dataset.municipalities if item.bundesland == "Wien"}
    assert {item.municipality.gemeinde for item in result["rankings"]} == expected
