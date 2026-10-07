import json
from pathlib import Path

# Loads JSON and validates it through the models.

from standort_agent.models import (
    BusinessProfile,
    MunicipalityDataset,
)


def load_municipalities(
    path: str | Path,
) -> MunicipalityDataset:
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"Municipality dataset does not exist: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        raw_data = json.load(file)

    return MunicipalityDataset.model_validate(raw_data)


def load_business_profile(
    path: str | Path,
) -> BusinessProfile:
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"Business profile does not exist: {path}"
        )

    with path.open("r", encoding="utf-8") as file:
        raw_data = json.load(file)

    return BusinessProfile.model_validate(raw_data)