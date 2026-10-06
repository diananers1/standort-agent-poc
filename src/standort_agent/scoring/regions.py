from standort_agent.models import Municipality


def filter_by_region(
    municipalities: list[Municipality],
    preferred_locations: list[str],
) -> list[Municipality]:
    """Return municipalities matching any requested city or federal state.

    An empty preference list means a nationwide search. Match city names
    exactly so that Wien does not also select Wiener Neustadt.
    """
    if not preferred_locations:
        return list(municipalities)

    locations = {location.strip().casefold() for location in preferred_locations}
    return [
        municipality
        for municipality in municipalities
        if municipality.bundesland.strip().casefold() in locations
        or municipality.gemeinde.split("(", 1)[0].strip().casefold() in locations
    ]
