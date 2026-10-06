from pathlib import Path

import pytest

from standort_agent.agents.demographics import DemographicAgent
from standort_agent.agents.poi import POIAgent
from standort_agent.agents.rent import RentAgent
from standort_agent.agents.transit import TransitAgent
from standort_agent.interpretation.rules import interpret_profile
from standort_agent.loader import load_business_profile, load_municipalities
from standort_agent.scoring.aggregator import rank_municipalities
from standort_agent.scoring.weighting import get_weights

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
EXPECTED_SIGNALS = {"demographics", "poi", "rent", "transit"}


@pytest.fixture(params=[1, 2, 3])
def profile(request):
    return interpret_profile(load_business_profile(
        DATA_DIR / "examples" / f"profil_{request.param}.json"
    ))


@pytest.fixture
def municipalities():
    return load_municipalities(DATA_DIR / "municipalities.json").municipalities


@pytest.fixture
def agents():
    return [DemographicAgent(), POIAgent(), RentAgent(), TransitAgent()]


@pytest.mark.parametrize("category", ["retail", "cafe", "fitness", "logistics", "general", "unknown"])
def test_business_weights_are_normalized(category):
    profile = interpret_profile(load_business_profile(DATA_DIR / "examples" / "profil_1.json"))
    profile = profile.model_copy(update={"business_category": category})
    weights = get_weights(profile)
    assert set(weights) == EXPECTED_SIGNALS
    assert sum(weights.values()) == pytest.approx(1.0)
    assert all(0 <= weight <= 1 for weight in weights.values())


def test_ranking_contains_every_municipality(municipalities, profile, agents):
    rankings = rank_municipalities(municipalities, profile, agents)
    assert len(rankings) == 20
    assert sorted(item.municipality.gemeinde for item in rankings) == sorted(
        item.gemeinde for item in municipalities
    )


def test_ranking_signals_and_weighted_scores(municipalities, profile, agents):
    weights = get_weights(profile)
    for evaluation in rank_municipalities(municipalities, profile, agents):
        assert set(evaluation.signals) == EXPECTED_SIGNALS
        assert all(result.signal == key for key, result in evaluation.signals.items())
        assert all(0 <= result.score <= 100 for result in evaluation.signals.values())
        assert 0 <= evaluation.total_score <= 100
        expected = sum(evaluation.signals[key].score * weight for key, weight in weights.items())
        assert evaluation.total_score == pytest.approx(expected)


def test_ranking_is_sorted_descending(municipalities, profile, agents):
    scores = [item.total_score for item in rank_municipalities(municipalities, profile, agents)]
    assert scores == sorted(scores, reverse=True)


def test_ranking_is_deterministic(municipalities, profile, agents):
    first = rank_municipalities(municipalities, profile, agents)
    second = rank_municipalities(municipalities, profile, agents)
    assert [item.model_dump() for item in first] == [item.model_dump() for item in second]


def test_empty_dataset_has_empty_ranking(profile, agents):
    assert rank_municipalities([], profile, agents) == []
