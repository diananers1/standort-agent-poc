from pathlib import Path

import pytest

from standort_agent.interpretation.rules import (
    detect_business_category, interpret_profile, interpret_region,
    interpret_target_group,
)
from standort_agent.loader import load_business_profile

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


@pytest.mark.parametrize("text,expected", [
    ("Retail / Einzelhandel", "retail"), ("EINZELHANDEL", "retail"),
    ("Gastronomie / Café", "cafe"), ("Cafe", "cafe"),
    ("Fitness / Wellnessstudio", "fitness"), ("Wellness", "fitness"),
    ("Logistik", "logistics"), ("Unbekannte Branche", "general"),
])
def test_business_category(text, expected):
    assert detect_business_category(text) == expected


@pytest.mark.parametrize("text", [
    "Junge Berufstätige (25–40)", "Studierende und Familien",
    "Erwachsene ab 30, gesundheitsbewusst", "Unbekannte Zielgruppe",
])
def test_target_weights_are_normalized(text):
    weights = interpret_target_group(text).model_dump()
    assert sum(weights.values()) == pytest.approx(1.0)
    assert all(0 <= weight <= 1 for weight in weights.values())


def test_young_professionals_prioritize_younger_age_groups():
    weights = interpret_target_group("Junge Berufstätige (25–40)")
    assert weights.age_18_34 > weights.age_35_54 > weights.age_55_plus
    assert weights.age_18_34 + weights.age_35_54 >= 0.9


def test_students_and_families_include_working_age_adults():
    weights = interpret_target_group("Studierende und Familien")
    assert weights.age_18_34 > weights.age_55_plus
    assert weights.age_35_54 > weights.age_55_plus


def test_adults_over_thirty_prioritize_middle_age_group():
    weights = interpret_target_group("Erwachsene ab 30, gesundheitsbewusst")
    assert weights.age_35_54 > weights.age_18_34
    assert weights.age_35_54 > weights.age_55_plus


@pytest.mark.parametrize("text,expected", [
    ("Österreich", []), (" Austria ", []), ("", []),
    ("Wien", ["Wien"]), (" WIEN ", ["Wien"]),
    ("Graz oder Linz", ["Graz", "Linz"]),
])
def test_region(text, expected):
    assert interpret_region(text) == expected


@pytest.mark.parametrize("regions,expected", [
    (["Graz", "Linz"], ["Graz", "Linz"]),
    ([" WIEN ", "Wien"], ["Wien"]),
    (["Österreich"], []),
])
def test_region_selection_bypasses_text_splitting(regions, expected, monkeypatch):
    def unexpected_split(*args, **kwargs):
        raise AssertionError("Dropdown selections must not be parsed as text")

    monkeypatch.setattr("standort_agent.interpretation.rules.re.split", unexpected_split)
    assert interpret_region(regions) == expected


@pytest.mark.parametrize("regions", [[], ["Österreich", "Wien"], ["Wien", "Berlin"], ["Graz oder Linz"]])
def test_invalid_region_selections(regions):
    with pytest.raises(ValueError):
        interpret_region(regions)


@pytest.mark.parametrize("number,category,locations", [
    (1, "retail", ["Wien"]), (2, "cafe", []),
    (3, "fitness", ["Graz", "Linz"]),
])
def test_interpret_example_profile(number, category, locations):
    raw = load_business_profile(DATA_DIR / "examples" / f"profil_{number}.json")
    result = interpret_profile(raw)
    assert result.business_category == category
    assert result.preferred_locations == locations
    assert result.flaeche_m2 == raw.flaeche_m2
    assert result.budget_miete_eur == raw.budget_miete_eur
    assert sum(result.target_age_weights.model_dump().values()) == pytest.approx(1)


@pytest.mark.parametrize("industry,group", [
    ("retail", "young_professionals"),
    ("cafe", "students_families"),
    ("fitness", "adults_30_plus"),
    ("logistics", "young_professionals"),
])
def test_dropdown_profile_uses_direct_mappings(industry, group, monkeypatch):
    from standort_agent.models import BusinessProfile
    from standort_agent.interpretation.rules import profile_input_errors

    def unexpected_parse(*args, **kwargs):
        pytest.fail("Dropdown IDs and lists must not use text parsing")

    monkeypatch.setattr("standort_agent.interpretation.rules.re.search", unexpected_parse)
    monkeypatch.setattr("standort_agent.interpretation.rules.re.split", unexpected_parse)
    profile = BusinessProfile(
        branche=industry, zielgruppe=group,
        region_praeferenz=["Graz", "Wien"],
        flaeche_m2=200, budget_miete_eur=4000,
    )
    assert profile_input_errors(profile) == []
    interpreted = interpret_profile(profile)
    assert interpreted.business_category == industry
    assert interpreted.preferred_locations == ["Graz", "Wien"]
    assert sum(interpreted.target_age_weights.model_dump().values()) == pytest.approx(1)
