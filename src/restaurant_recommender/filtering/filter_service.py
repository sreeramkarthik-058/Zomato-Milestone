"""Apply deterministic filters to produce a candidate shortlist for the LLM."""

from __future__ import annotations

import logging

from restaurant_recommender.config import Settings, get_settings
from restaurant_recommender.filtering.budget import matches_budget
from restaurant_recommender.filtering.location import LOCATION_ALIASES, matches_location
from restaurant_recommender.models import Budget, Candidate, CandidateList, Restaurant, UserPreferences
from restaurant_recommender.store.restaurant_store import RestaurantStore

logger = logging.getLogger(__name__)


def matches_cuisine(restaurant: Restaurant, cuisine_preference: str) -> bool:
    """Case-insensitive substring match against any cuisine tag."""
    needle = cuisine_preference.strip().lower()
    if not needle:
        return False
    return any(needle in cuisine.lower() for cuisine in restaurant.cuisines)


def matches_rating(restaurant: Restaurant, min_rating: float) -> bool:
    """Include restaurants at or above the minimum rating (EC-FLT-05)."""
    return restaurant.rating >= min_rating


class FilterService:
    """Integration-layer hard filters before LLM ranking."""

    def __init__(
        self,
        settings: Settings | None = None,
        location_aliases: dict[str, str] | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._location_aliases = location_aliases or LOCATION_ALIASES

    def filter(
        self,
        preferences: UserPreferences,
        store: RestaurantStore,
    ) -> CandidateList:
        """
        Filter catalog by preferences, sort by rating desc, cap to max_candidates.

        Order: location → cuisine → rating → budget → sort → cap.
        additional_preferences does not affect filtering (LLM-only).
        """
        if not store.is_loaded():
            raise RuntimeError("Restaurant store is not loaded; run ingestion first")

        restaurants = store.get_all()
        filtered = self._apply_filters(restaurants, preferences)
        filtered.sort(key=lambda r: r.rating, reverse=True)

        cap = self._settings.max_candidates
        capped = filtered[:cap]
        candidates = [Candidate.from_restaurant(r) for r in capped]

        logger.info(
            "Filter: %s -> %s candidates (cap=%s) for location=%r cuisine=%r",
            len(restaurants),
            len(candidates),
            cap,
            preferences.location,
            preferences.cuisine,
        )
        return CandidateList(items=candidates)

    def _apply_filters(
        self,
        restaurants: list[Restaurant],
        preferences: UserPreferences,
    ) -> list[Restaurant]:
        result = restaurants
        result = [
            r
            for r in result
            if matches_location(
                city=r.city,
                location=r.location,
                preference=preferences.location,
                aliases=self._location_aliases,
            )
        ]
        result = [r for r in result if matches_cuisine(r, preferences.cuisine)]
        result = [r for r in result if matches_rating(r, preferences.min_rating)]
        result = [r for r in result if matches_budget(r, preferences.budget)]
        return result
