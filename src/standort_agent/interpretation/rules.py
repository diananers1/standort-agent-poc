from standort_agent.models import (
    BusinessProfile,
    InterpretedProfile,
    TargetAgeWeights,
)


def detect_business_category(text: str) -> str:
    value = text.lower()

    if "retail" in value or "einzelhandel" in value:
        return "retail"

    if (
        "gastronomie" in value
        or "café" in value
        or "cafe" in value
        or "restaurant" in value
    ):
        return "cafe"

    if (
        "fitness" in value
        or "wellness" in value
        or "studio" in value
    ):
        return "fitness"

    if "logistik" in value or "logistics" in value:
        return "logistics"

    return "general"


def interpret_target_group(
    text: str,
) -> TargetAgeWeights:
    value = text.lower()

    if (
        "junge" in value
        or "25" in value
        or "student" in value
        or "studierende" in value
    ):
        if "famil" in value:
            return TargetAgeWeights(
                age_18_34=0.55,
                age_35_54=0.40,
                age_55_plus=0.05,
            )

        return TargetAgeWeights(
            age_18_34=0.75,
            age_35_54=0.25,
            age_55_plus=0.0,
        )

    if "ab 30" in value:
        return TargetAgeWeights(
            age_18_34=0.20,
            age_35_54=0.60,
            age_55_plus=0.20,
        )

    return TargetAgeWeights(
        age_18_34=0.34,
        age_35_54=0.33,
        age_55_plus=0.33,
    )


def interpret_region(
    text: str,
) -> list[str]:
    value = text.strip().lower()

    if value in {
        "österreich",
        "austria",
        "",
    }:
        return []

    locations = []

    candidates = {
        "wien": "Wien",
        "graz": "Graz",
        "linz": "Linz",
        "salzburg": "Salzburg",
        "innsbruck": "Innsbruck",
        "klagenfurt": "Klagenfurt",
        "villach": "Villach",
    }

    for keyword, normalized in candidates.items():
        if keyword in value:
            locations.append(normalized)

    return locations


def interpret_profile(
    profile: BusinessProfile,
) -> InterpretedProfile:
    return InterpretedProfile(
        business_category=detect_business_category(
            profile.branche
        ),
        target_age_weights=interpret_target_group(
            profile.zielgruppe
        ),
        preferred_locations=interpret_region(
            profile.region_praeferenz
        ),
        flaeche_m2=profile.flaeche_m2,
        budget_miete_eur=profile.budget_miete_eur,
    )