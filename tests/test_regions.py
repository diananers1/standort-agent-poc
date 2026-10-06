from pathlib import Path

import pytest

from standort_agent.loader import load_municipalities
from standort_agent.scoring.regions import filter_by_region

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


@pytest.mark.parametrize("locations,expected_cities,expected_state", [
    ([], None, None),
    ([" Wien "], None, "Wien"),
    (["Graz", "Linz"], {"Graz", "Linz"}, None),
    (["steiermark"], None, "Steiermark"),
    (["Berlin"], set(), None),
])
def test_region_filter(locations, expected_cities, expected_state):
    municipalities = load_municipalities(DATA_DIR / "municipalities.json").municipalities
    if expected_state:
        expected = [item for item in municipalities if item.bundesland == expected_state]
    elif expected_cities is not None:
        expected = [item for item in municipalities if item.gemeinde.split("(", 1)[0].strip() in expected_cities]
    else:
        expected = municipalities
    assert filter_by_region(municipalities, locations) == expected
    assert len(municipalities) == 20
