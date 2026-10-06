from pathlib import Path

import pytest

from standort_agent.agents.demographics import DemographicAgent
from standort_agent.agents.poi import POIAgent
from standort_agent.agents.rent import RentAgent, affordability_score
from standort_agent.agents.transit import TransitAgent
from standort_agent.interpretation.rules import interpret_profile
from standort_agent.loader import load_business_profile, load_municipalities

DATA_DIR = Path(__file__).resolve().parents[1] / "data"


@pytest.fixture
def municipalities():
    return load_municipalities(DATA_DIR / "municipalities.json").municipalities


@pytest.fixture(params=[1, 2, 3])
def profile(request):
    return interpret_profile(load_business_profile(
        DATA_DIR / "examples" / f"profil_{request.param}.json"
    ))


@pytest.mark.parametrize("ratio,expected", [
    (0.70, 100), (0.80, 100), (0.90, 90), (1.00, 80),
    (1.125, 55), (1.25, 30), (1.375, 15), (1.50, 0), (2.00, 0),
])
def test_affordability_score(ratio, expected):
    assert affordability_score(ratio) == pytest.approx(expected)


def test_affordability_never_increases_with_rent_ratio():
    ratios = sorted({i / 1000 for i in range(2001)} | {
        0.799999, 0.800001, 0.999999, 1.000001,
        1.249999, 1.250001, 1.499999, 1.500001,
    })
    scores = [affordability_score(ratio) for ratio in ratios]
    assert all(0 <= score <= 100 for score in scores)
    assert all(cheaper >= expensive for cheaper, expensive in zip(scores, scores[1:]))


@pytest.mark.parametrize("transit,expected", [(0, 0), (2.5, 25), (5, 50), (9.8, 98), (10, 100)])
def test_transit_scale(transit, expected, municipalities, profile):
    municipality = municipalities[0].model_copy(update={"oev_score": transit})
    result = TransitAgent().evaluate(municipality, profile, municipalities)
    assert result.signal == "transit"
    assert result.score == pytest.approx(expected)
    assert result.raw_value == transit


@pytest.mark.parametrize("agent,signal", [
    (POIAgent(), "poi"), (DemographicAgent(), "demographics"),
    (RentAgent(), "rent"), (TransitAgent(), "transit"),
])
def test_agent_scores_are_bounded(agent, signal, municipalities, profile):
    for municipality in municipalities:
        result = agent.evaluate(municipality, profile, municipalities)
        assert result.signal == signal
        assert 0 <= result.score <= 100
        assert result.reason.strip()


def test_poi_ranks_density_extremes_correctly(municipalities, profile):
    agent = POIAgent()
    lowest = min(municipalities, key=lambda item: item.poi_dichte)
    highest = max(municipalities, key=lambda item: item.poi_dichte)
    assert agent.evaluate(lowest, profile, municipalities).score == pytest.approx(0)
    assert agent.evaluate(highest, profile, municipalities).score == pytest.approx(100)


def test_demographics_reports_weighted_age_match(municipalities, profile):
    municipality = municipalities[0]
    age = municipality.altersverteilung
    weights = profile.target_age_weights
    expected = (age.age_18_34 * weights.age_18_34
                + age.age_35_54 * weights.age_35_54
                + age.age_55_plus * weights.age_55_plus)
    result = DemographicAgent().evaluate(municipality, profile, municipalities)
    assert result.raw_value == pytest.approx(expected)


def test_rent_estimates_monthly_cost_and_affordability(municipalities, profile):
    for municipality in municipalities:
        result = RentAgent().evaluate(municipality, profile, municipalities)
        estimated = municipality.mietindex_eur_m2 * profile.flaeche_m2
        assert result.raw_value == pytest.approx(estimated)
        assert result.score == pytest.approx(affordability_score(
            estimated / profile.budget_miete_eur
        ))


@pytest.mark.parametrize("monthly_rent,budget_relation", [(1000, "below"), (6000, "above")])
def test_rent_reason_identifies_budget_relation(monthly_rent, budget_relation, municipalities, profile):
    municipality = municipalities[0].model_copy(update={"mietindex_eur_m2": 10})
    adjusted = profile.model_copy(update={"flaeche_m2": monthly_rent / 10, "budget_miete_eur": 4000})
    result = RentAgent().evaluate(municipality, adjusted, municipalities)
    assert result.raw_value == pytest.approx(monthly_rent)
    assert f"{budget_relation} the budget" in result.reason
