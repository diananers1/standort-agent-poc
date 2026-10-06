import math


def min_max_normalize(
    value: float,
    minimum: float,
    maximum: float,
) -> float:
    if maximum == minimum:
        return 100.0

    normalized = (
        (value - minimum)
        / (maximum - minimum)
    ) * 100.0

    return max(
        0.0,
        min(100.0, normalized),
    )


def log_min_max_normalize(
    value: float,
    minimum: float,
    maximum: float,
) -> float:
    return min_max_normalize(
        value=math.log1p(value),
        minimum=math.log1p(minimum),
        maximum=math.log1p(maximum),
    )