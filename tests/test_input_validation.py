from pathlib import Path

import pytest
from pydantic import ValidationError

from standort_agent.graph.workflow import location_graph
from standort_agent.interpretation.rules import interpret_region, is_supported_region
from standort_agent.loader import load_business_profile, load_municipalities
from standort_agent.models import BusinessProfile
from standort_agent.ui import app

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


@pytest.fixture
def values():
    return load_business_profile(DATA_DIR / "examples" / "profil_1.json").model_dump()


@pytest.mark.parametrize("field,label", [
    ("flaeche_m2", "Required area"),
    ("budget_miete_eur", "Monthly rent budget"),
])
@pytest.mark.parametrize("value", [None, 0, -1, "abc", float("nan"), float("inf"), float("-inf"), 1e100])
def test_invalid_numbers_clear_outputs(values, field, label, value):
    values[field] = value
    rows, message, report = app.analyze_location(**values)
    assert rows == []
    assert report is None
    assert label in message
    assert "Please check your input" in message
    with pytest.raises(ValidationError):
        BusinessProfile(**values)


@pytest.mark.parametrize("field,label", [
    ("branche", "Business / Industry"), ("zielgruppe", "Target group"),
])
@pytest.mark.parametrize("value", [None, "", "   ", "xyz", "notretail", "studio", "1250"])
def test_invalid_text_clear_outputs(values, field, label, value):
    values[field] = value
    rows, message, report = app.analyze_location(**values)
    assert rows == []
    assert report is None
    assert label in message


@pytest.mark.parametrize("region", ["Atlantis", "Not Wien", "nicht Wien", "Wien oder Berlin", "Wienxyz", "Wien,", "Österreich oder Berlin"])
def test_invalid_region_is_rejected_everywhere(values, region):
    assert not is_supported_region(region)
    with pytest.raises(ValueError):
        interpret_region(region)
    values["region_praeferenz"] = region
    rows, message, report = app.analyze_location(**values)
    assert rows == [] and report is None
    assert "Preferred region" in message
    result = location_graph.invoke({
        "raw_profile": BusinessProfile(**values),
        "municipalities": app.DATASET.municipalities,
    })
    assert result.get("error")
    assert not result.get("rankings")


@pytest.mark.parametrize("region,expected", [
    ("", []), (" Österreich ", []), ("Graz oder Linz", ["Graz", "Linz"]),
    ("Wiener Neustadt", ["Wiener Neustadt"]),
    ("St Pölten", ["St. Pölten"]), ("Graz, Linz", ["Graz", "Linz"]),
])
def test_complete_region_names(region, expected):
    assert is_supported_region(region)
    assert interpret_region(region) == expected


@pytest.mark.parametrize("field", ["branche", "zielgruppe"])
def test_graph_rejects_unknown_text(values, field):
    values[field] = "xyz"
    result = location_graph.invoke({
        "raw_profile": BusinessProfile(**values),
        "municipalities": app.DATASET.municipalities,
    })
    assert result.get("error")
    assert not result.get("rankings")


def test_all_invalid_fields_are_reported_together():
    rows, message, report = app.analyze_location("xyz", -1, "xyz", 0, "Atlantis")
    assert rows == [] and report is None
    for label in ["Business / Industry", "Required area", "Target group", "Monthly rent budget", "Preferred region"]:
        assert label in message


@pytest.mark.parametrize("number", [1, 2, 3])
def test_supported_profiles_generate_reports(number, tmp_path, monkeypatch):
    monkeypatch.setattr(app, "OUTPUT_PATH", tmp_path / "report.html")
    profile = load_business_profile(DATA_DIR / "examples" / f"profil_{number}.json")
    rows, summary, report = app.analyze_location(**profile.model_dump())
    assert rows
    assert "Best match" in summary
    assert Path(report).is_file()


def test_empty_dataset_returns_message(values, monkeypatch):
    monkeypatch.setattr(app, "DATASET", load_municipalities(DATA_DIR / "municipalities.json").model_copy(update={"municipalities": []}))
    rows, message, report = app.analyze_location(**values)
    assert rows == [] and report is None
    assert "No municipalities" in message


@pytest.mark.parametrize("field", ["flaeche_m2", "budget_miete_eur"])
@pytest.mark.parametrize("value", ["34e4", "1E3", "200m2", "4,000", "", "   "])
def test_numeric_text_format_is_rejected(values, field, value):
    values[field] = value
    rows, message, report = app.analyze_location(**values)
    assert rows == [] and report is None
    assert "plain number" in message


@pytest.mark.parametrize("field,value,label", [
    ("branche", "34e4", "Business / Industry"),
    ("zielgruppe", "34e4", "Target group"),
    ("region_praeferenz", "34e4", "Preferred region"),
    ("flaeche_m2", "34e4", "Required area"),
    ("budget_miete_eur", "34e4", "Monthly rent budget"),
    ("flaeche_m2", "0", "Required area"),
    ("budget_miete_eur", "-1", "Monthly rent budget"),
    ("branche", "", "Business / Industry"),
    ("zielgruppe", "", "Target group"),
    ("region_praeferenz", "Not Wien", "Preferred region"),
])
def test_invalid_input_shows_error_popup_after_clearing(values, field, value, label):
    values[field] = value
    callback = app.analyze_with_error_popup(*values.values())
    rows, message, report = next(callback)
    assert rows == [] and report is None
    assert label in message
    with pytest.raises(app.gr.Error, match=label):
        next(callback)


def test_plain_decimal_input_succeeds_without_popup(values, tmp_path, monkeypatch):
    monkeypatch.setattr(app, "OUTPUT_PATH", tmp_path / "report.html")
    values.update(flaeche_m2="200.5", budget_miete_eur="4000")
    callback = app.analyze_with_error_popup(*values.values())
    rows, _, report = next(callback)
    assert rows and Path(report).is_file()
    with pytest.raises(StopIteration):
        next(callback)


@pytest.mark.parametrize("budget", [1, 199, 199.99, "1", "199.99"])
def test_monthly_budget_below_minimum_shows_popup(values, budget):
    values["budget_miete_eur"] = budget
    callback = app.analyze_with_error_popup(*values.values())
    rows, message, report = next(callback)
    assert rows == [] and report is None
    assert "Monthly rent budget" in message
    assert "200" in message
    with pytest.raises(app.gr.Error, match="200"):
        next(callback)


@pytest.mark.parametrize("budget", [200, "200", 200.01, 10_000_000])
def test_monthly_budget_range_accepts_boundaries(values, budget):
    values["budget_miete_eur"] = budget
    assert BusinessProfile(**values).budget_miete_eur == float(budget)


@pytest.mark.parametrize("regions", [["Graz", "Wien"], ["Graz", "Linz"], ["Österreich"]])
def test_multiple_regions_compare_selected_locations(values, regions, tmp_path, monkeypatch):
    monkeypatch.setattr(app, "OUTPUT_PATH", tmp_path / "report.html")
    values["region_praeferenz"] = regions
    rows, summary, report = app.analyze_location(**values)
    assert rows and Path(report).is_file()
    if regions != ["Österreich"]:
        assert all(row[0].split("(", 1)[0].strip() in regions for row in rows)
        assert set(row[0].split("(", 1)[0].strip() for row in rows) == set(regions)
    assert "Best match" in summary


@pytest.mark.parametrize("regions,expected", [
    ([], "select at least one"),
    (["Österreich", "Wien"], "All Austria on its own"),
])
def test_invalid_location_selection_shows_popup(values, regions, expected):
    values["region_praeferenz"] = regions
    callback = app.analyze_with_error_popup(*values.values())
    rows, message, report = next(callback)
    assert rows == [] and report is None
    assert expected in message
    with pytest.raises(app.gr.Error, match=expected):
        next(callback)
