import math

import pytest

from standort_agent.scoring.normalization import (
    log_min_max_normalize, min_max_normalize,
)


@pytest.mark.parametrize("value,expected", [
    (10, 0), (20, 100), (15, 50), (5, 0), (25, 100),
])
def test_min_max_normalization(value, expected):
    assert min_max_normalize(value, 10, 20) == pytest.approx(expected)


@pytest.mark.parametrize("normalize", [min_max_normalize, log_min_max_normalize])
def test_identical_bounds_are_safe(normalize):
    score = normalize(10, 10, 10)
    assert math.isfinite(score)
    assert 0 <= score <= 100


@pytest.mark.parametrize("value,expected", [(100, 0), (10000, 100), (0, 0), (20000, 100)])
def test_log_normalization_endpoints_and_clamping(value, expected):
    assert log_min_max_normalize(value, 100, 10000) == pytest.approx(expected)


def test_log_population_normalization_is_strictly_increasing():
    populations = [100, 500, 1000, 5000, 10000, 100000]
    scores = [log_min_max_normalize(value, 100, 100000) for value in populations]
    assert all(a < b for a, b in zip(scores, scores[1:]))
    assert scores[0] == pytest.approx(0)
    assert scores[-1] == pytest.approx(100)


def test_log_normalization_uses_logarithmic_scale():
    # log1p(9), log1p(99), log1p(999) are equally spaced.
    assert log_min_max_normalize(99, 9, 999) == pytest.approx(50)
