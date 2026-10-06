from pathlib import Path

import pytest

from standort_agent.graph.workflow import location_graph
from standort_agent.loader import load_business_profile, load_municipalities
from standort_agent.reporting.explanation import explain_for_customer
from standort_agent.reporting.report import generate_html_report

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


@pytest.fixture
def recommendation():
    profile = load_business_profile(DATA_DIR / "examples" / "profil_1.json")
    dataset = load_municipalities(DATA_DIR / "municipalities.json")
    result = location_graph.invoke({"raw_profile": profile, "municipalities": dataset.municipalities})
    return profile, result["rankings"]


def test_explanation_discloses_actual_budget_overrun(recommendation):
    profile, rankings = recommendation
    text = explain_for_customer(profile, rankings[0])
    assert rankings[0].municipality.gemeinde in text
    assert "€4,400" in text
    assert "€400 above your budget" in text
    assert "synthetic data" in text
    assert "do not predict sales" in text


@pytest.mark.parametrize("budget,phrase", [(5000, "€600 within your rent budget"), (4400, "no rent headroom")])
def test_explanation_handles_budget_headroom(recommendation, budget, phrase):
    profile, rankings = recommendation
    profile = profile.model_copy(update={"budget_miete_eur": budget})
    assert phrase in explain_for_customer(profile, rankings[0])


def test_weak_scores_do_not_get_positive_claims(recommendation):
    profile, rankings = recommendation
    evaluation = rankings[0].model_copy(update={
        "total_score": 20,
        "signals": {key: value.model_copy(update={"score": 20}) for key, value in rankings[0].signals.items()},
    })
    text = explain_for_customer(profile, evaluation)
    assert "cautious approach" in text
    assert "weaker match" in text
    assert "relatively sparse" in text
    assert "Limited public transport" in text
    assert "Strong public transport" not in text


def test_report_includes_customer_explanation(recommendation, tmp_path):
    profile, rankings = recommendation
    report = generate_html_report(profile, rankings, tmp_path / "report.html")
    html = report.read_text(encoding="utf-8")
    assert "What this means for your business" in html
    assert "€400 above your budget" in html
