"""Location matching helpers and city aliases."""

from __future__ import annotations

# Optional aliases (implementation-plan Phase 3); extend via config later.
LOCATION_ALIASES: dict[str, str] = {
    "bengaluru": "bangalore",
    "bangalore": "bengaluru",
    "bombay": "mumbai",
    "mumbai": "bombay",
    "new delhi": "delhi",
    "delhi": "new delhi",
}


def expand_location_terms(location: str) -> set[str]:
    """Return lowercase terms to match against city/location fields."""
    key = location.strip().lower()
    terms = {key}
    if key in LOCATION_ALIASES:
        terms.add(LOCATION_ALIASES[key])
    return terms


def matches_location(
    *,
    city: str | None,
    location: str,
    preference: str,
    aliases: dict[str, str] | None = None,
) -> bool:
    """Case-insensitive substring match on city or full location (EC-INP-05/06)."""
    alias_map = aliases if aliases is not None else LOCATION_ALIASES
    key = preference.strip().lower()
    terms = {key}
    if key in alias_map:
        terms.add(alias_map[key])

    haystacks: list[str] = []
    if city:
        haystacks.append(city.lower())
    haystacks.append(location.lower())

    return any(term in haystack for haystack in haystacks for term in terms)
