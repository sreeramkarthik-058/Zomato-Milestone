"""Format recommendation results for user presentation (architecture §4.6)."""

from __future__ import annotations

from restaurant_recommender.models import (
    LLMRecommendationItem,
    RecommendationResult,
    Restaurant,
)

def format_estimated_cost(restaurant: Restaurant) -> str:
    """Human-readable cost with optional budget band (EC-OUT-08)."""
    if restaurant.approx_cost is None:
        return "Cost not available"
    
    band = f" ({restaurant.cost_band} budget)" if restaurant.cost_band else ""
    return f"₹{restaurant.approx_cost:.0f} for two{band}"

def to_recommendation_result(
    item: LLMRecommendationItem,
    restaurant: Restaurant,
) -> RecommendationResult:
    """Map LLM item and dataset record to end-user result (EC-OUT-07)."""
    cuisine = ", ".join(restaurant.cuisines) if restaurant.cuisines else "Not specified"
    
    return RecommendationResult(
        rank=item.rank,
        restaurant_name=restaurant.name,
        cuisine=cuisine,
        rating=restaurant.rating,
        estimated_cost=format_estimated_cost(restaurant),
        explanation=item.explanation,
        restaurant_id=restaurant.id,
    )
