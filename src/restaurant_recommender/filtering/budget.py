"""Filter restaurants by user budget tier."""

from __future__ import annotations

from restaurant_recommender.ingestion.budget import cost_band_from_amount
from restaurant_recommender.models import Budget, Restaurant


def restaurant_cost_band(restaurant: Restaurant) -> str | None:
    """Resolve cost band from stored band or approx_cost."""
    if restaurant.cost_band:
        return restaurant.cost_band
    return cost_band_from_amount(restaurant.approx_cost)


def matches_budget(restaurant: Restaurant, budget: Budget) -> bool:
    """
    Return True if the restaurant fits the user's budget tier.

    Restaurants without cost data are excluded (EC-FLT-07).
    """
    band = restaurant_cost_band(restaurant)
    if band is None:
        return False
    return band == budget.value
