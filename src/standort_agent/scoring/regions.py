from standort_agent.models import Municipality


def matches_preference(
    municipality: Municipality,
    preferred_locations: list[str],
) -> bool:
    """
    Return True when the municipality matches at least one
    preferred city or federal state.

    An empty preference list means Austria-wide search.
    """
    if not preferred_locations:
        return True

    municipality_name = municipality.gemeinde.split("(", 1)[0].strip().casefold()
    federal_state = municipality.bundesland.strip().casefold()

    for preference in preferred_locations:
        value = preference.strip().casefold()

        if value == municipality_name:
            return True

        if value == federal_state:
            return True

    return False


def filter_by_region(
    municipalities: list[Municipality],
    preferred_locations: list[str],
) -> list[Municipality]:
    """
    Restrict the candidate set according to the interpreted
    regional preference.
    """
    return [
        municipality
        for municipality in municipalities
        if matches_preference(
            municipality,
            preferred_locations,
        )
    ]