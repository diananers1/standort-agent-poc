import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from standort_agent.loader import load_business_profile, load_municipalities

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def test_load_municipalities():
    dataset = load_municipalities(DATA_DIR / "municipalities.json")
    assert len(dataset.municipalities) == 20
    first = dataset.municipalities[0]
    assert first.gemeinde == "Wien (1., Innere Stadt)"
    assert first.bundesland == "Wien"
    assert first.einwohner == 16000
    assert first.poi_dichte == pytest.approx(9.2)
    assert first.mietindex_eur_m2 == pytest.approx(28.5)
    assert first.oev_score == pytest.approx(9.8)
    assert first.altersverteilung.age_18_34 == pytest.approx(0.28)
    assert first.altersverteilung.age_35_54 == pytest.approx(0.35)
    assert first.altersverteilung.age_55_plus == pytest.approx(0.37)


@pytest.mark.parametrize("filename,industry,area,budget,region", [
    ("profil_1.json", "Retail / Einzelhandel", 200, 4000, "Wien"),
    ("profil_2.json", "Gastronomie / Café", 120, 2500, "Österreich"),
    ("profil_3.json", "Fitness / Wellnessstudio", 400, 6000, "Graz oder Linz"),
])
def test_load_business_profile(filename, industry, area, budget, region):
    profile = load_business_profile(DATA_DIR / "examples" / filename)
    assert profile.branche == industry
    assert profile.flaeche_m2 == area
    assert profile.budget_miete_eur == budget
    assert profile.region_praeferenz == region
    assert profile.zielgruppe


@pytest.mark.parametrize("loader", [load_municipalities, load_business_profile])
def test_missing_file(loader, tmp_path):
    with pytest.raises(FileNotFoundError, match="does not exist"):
        loader(tmp_path / "missing.json")


@pytest.mark.parametrize("loader", [load_municipalities, load_business_profile])
def test_invalid_json(loader, tmp_path):
    path = tmp_path / "invalid.json"
    path.write_text("{broken", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        loader(path)


@pytest.mark.parametrize("loader", [load_municipalities, load_business_profile])
def test_missing_required_fields(loader, tmp_path):
    path = tmp_path / "invalid.json"
    path.write_text("{}", encoding="utf-8")
    with pytest.raises(ValidationError):
        loader(path)
