from __future__ import annotations

import re

from pydantic import BaseModel, Field, field_validator, model_validator


class AgeDistribution(BaseModel):
    age_18_34: float = Field(alias="18_34", ge=0.0, le=1.0)
    age_35_54: float = Field(alias="35_54", ge=0.0, le=1.0)
    age_55_plus: float = Field(alias="55_plus", ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_total(self) -> "AgeDistribution":
        total = (
            self.age_18_34
            + self.age_35_54
            + self.age_55_plus
        )

        if abs(total - 1.0) > 0.02:
            raise ValueError(
                f"Age distribution must sum approximately to 1.0; got {total:.3f}"
            )

        return self


class Municipality(BaseModel):
    gemeinde: str
    bundesland: str
    einwohner: int = Field(gt=0)

    altersverteilung: AgeDistribution

    poi_dichte: float = Field(ge=0.0, le=10.0)
    mietindex_eur_m2: float = Field(gt=0.0)
    oev_score: float = Field(ge=0.0, le=10.0)


class MunicipalityDataset(BaseModel):
    municipalities: list[Municipality]


class BusinessProfile(BaseModel):
    branche: str = Field(min_length=1)
    flaeche_m2: float = Field(gt=0, le=100_000, allow_inf_nan=False)
    zielgruppe: str = Field(min_length=1)
    budget_miete_eur: float = Field(ge=200, le=10_000_000, allow_inf_nan=False)
    region_praeferenz: str

    @field_validator("flaeche_m2", "budget_miete_eur", mode="before")
    @classmethod
    def validate_number_format(cls, value):
        if isinstance(value, str):
            value = value.strip()
            if not re.fullmatch(r"[+-]?(?:[0-9]+(?:\.[0-9]+)?|\.[0-9]+)", value):
                raise ValueError(
                    "Enter a plain number such as 200 or 200.5; "
                    "letters, scientific notation and thousands separators are not accepted"
                )
        return value

    @field_validator("branche", "zielgruppe", "region_praeferenz", mode="before")
    @classmethod
    def strip_text(cls, value):
        return value.strip() if isinstance(value, str) else value


class TargetAgeWeights(BaseModel):
    age_18_34: float = Field(default=0.0, ge=0.0, le=1.0)
    age_35_54: float = Field(default=0.0, ge=0.0, le=1.0)
    age_55_plus: float = Field(default=0.0, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_weights(self) -> "TargetAgeWeights":
        total = (
            self.age_18_34
            + self.age_35_54
            + self.age_55_plus
        )

        if abs(total - 1.0) > 0.001:
            raise ValueError(
                f"Target age weights must sum to 1.0; got {total:.3f}"
            )

        return self


class InterpretedProfile(BaseModel):
    business_category: str
    target_age_weights: TargetAgeWeights
    preferred_locations: list[str]

    flaeche_m2: float
    budget_miete_eur: float


class SignalResult(BaseModel):
    signal: str
    score: float = Field(ge=0.0, le=100.0)
    raw_value: float | str | None = None
    reason: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)


class MunicipalityEvaluation(BaseModel):
    municipality: Municipality
    signals: dict[str, SignalResult]
    total_score: float = Field(ge=0.0, le=100.0)
