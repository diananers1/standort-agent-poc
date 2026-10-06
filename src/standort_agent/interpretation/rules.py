import re

from standort_agent.models import (
    BusinessProfile,
    InterpretedProfile,
    TargetAgeWeights,
)


AUSTRIAN_LOCATIONS = {
    # Country
    "österreich",
    "austria",

    # Federal states
    "wien",
    "niederösterreich",
    "oberösterreich",
    "steiermark",
    "kärnten",
    "salzburg",
    "tirol",
    "vorarlberg",
    "burgenland",

    # Cities represented in the dataset
    "graz",
    "linz",
    "wels",
    "leoben",
    "innsbruck",
    "klagenfurt",
    "villach",
    "st. pölten",
    "st pölten",
    "wiener neustadt",
    "eisenstadt",
    "bregenz",
    "dornbirn",
}


def is_supported_region(text: str | list[str]) -> bool:
    try:
        interpret_region(text)
    except ValueError:
        return False
    return True


def detect_business_category(text: str) -> str:
    value = text.casefold()
    patterns = {
        "retail": r"\b(?:retail|einzelhandel)\b",
        "cafe": r"\b(?:gastronomie|café|cafe|restaurant)\b",
        "fitness": r"\b(?:fitness|wellness|wellnessstudio|fitnessstudio)\b",
        "logistics": r"\b(?:logistik|logistics)\b",
    }
    for category, pattern in patterns.items():
        if re.search(pattern, value):
            return category
    return "general"


def interpret_target_group(
    text: str,
) -> TargetAgeWeights:
    value = text.lower()

    if (
        re.search(r"\b(?:junge|student\w*|studierende\w*)\b|\b25\b", value)
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

    if re.search(r"\bab\s+30\b", value):
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


def interpret_region(text: str | list[str]) -> list[str]:
    if isinstance(text, list):
        if not text:
            raise ValueError("Preferred region: select at least one location or All Austria.")
        parts = [part.strip().lower() for part in text]
        if any(part in {"österreich", "austria"} for part in parts):
            if len(parts) != 1:
                raise ValueError("Preferred region: select All Austria on its own, or choose individual locations.")
            return []
    else:
        value = text.strip().lower()

        # An empty interpreted list means nationwide search.
        if value in {"", "österreich", "austria"}:
            return []

        # Legacy text callers can separate complete location names.
        parts = re.split(r"\s+(?:oder|und|or|and)\s+|[,;/]", value)

    candidates = {
        # Cities
        "wien": "Wien",
        "graz": "Graz",
        "linz": "Linz",
        "wels": "Wels",
        "leoben": "Leoben",
        "innsbruck": "Innsbruck",
        "salzburg": "Salzburg",
        "klagenfurt": "Klagenfurt",
        "villach": "Villach",
        "st. pölten": "St. Pölten",
        "st pölten": "St. Pölten",
        "wiener neustadt": "Wiener Neustadt",
        "eisenstadt": "Eisenstadt",
        "bregenz": "Bregenz",
        "dornbirn": "Dornbirn",

        # Federal states
        "steiermark": "Steiermark",
        "oberösterreich": "Oberösterreich",
        "niederösterreich": "Niederösterreich",
        "kärnten": "Kärnten",
        "tirol": "Tirol",
        "vorarlberg": "Vorarlberg",
        "burgenland": "Burgenland",
    }

    locations = []
    for part in parts:
        normalized = candidates.get(part.strip())
        if normalized is None:
            raise ValueError(
                "Preferred region: enter an Austrian city or federal state "
                "represented in the dataset, or Österreich for all Austria. "
                "Separate multiple locations with 'oder' or commas."
            )
        if normalized not in locations:
            locations.append(normalized)
    return locations


def profile_input_errors(profile: BusinessProfile) -> list[str]:
    """Identify text the supported rules cannot interpret reliably."""
    errors = []
    if detect_business_category(profile.branche) == "general":
        errors.append(
            "Business / Industry: enter Retail / Einzelhandel, Gastronomie / Café, "
            "Fitness / Wellness, or Logistik."
        )
    target = profile.zielgruppe.strip().casefold()
    if not re.search(r"\b(?:junge|student\w*|studierende\w*)\b|\b25\b|\bab\s+30\b", target):
        errors.append(
            "Target group: use a supported description such as Junge Berufstätige "
            "(25–40), Studierende und Familien, or Erwachsene ab 30."
        )
    try:
        interpret_region(profile.region_praeferenz)
    except ValueError as exc:
        errors.append(str(exc))
    return errors


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
