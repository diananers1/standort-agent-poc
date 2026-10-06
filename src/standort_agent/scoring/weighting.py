from standort_agent.models import InterpretedProfile


DEFAULT_WEIGHTS = {
    "demographics": 0.25,
    "poi": 0.25,
    "rent": 0.30,
    "transit": 0.20,
}


BUSINESS_WEIGHTS = {
    "retail": {
        "demographics": 0.30,
        "poi": 0.30,
        "rent": 0.20,
        "transit": 0.20,
    },
    "cafe": {
        "demographics": 0.25,
        "poi": 0.30,
        "rent": 0.25,
        "transit": 0.20,
    },
    "fitness": {
        "demographics": 0.30,
        "poi": 0.15,
        "rent": 0.35,
        "transit": 0.20,
    },
    "logistics": {
        "demographics": 0.10,
        "poi": 0.10,
        "rent": 0.50,
        "transit": 0.30,
    },
}


def get_weights(
    profile: InterpretedProfile,
) -> dict[str, float]:
    return BUSINESS_WEIGHTS.get(
        profile.business_category,
        DEFAULT_WEIGHTS,
    )