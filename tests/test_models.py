import pytest
from pydantic import ValidationError

from restaurant_recommender.models import (
    Budget,
    Candidate,
    CandidateList,
    LLMRecommendationItem,
    LLMResponse,
    PromptPayload,
    RecommendationResponse,
    RecommendationResult,
    RecommendationStatus,
    Restaurant,
    UserPreferences,
)


def test_user_preferences_valid():
    prefs = UserPreferences(
        location="Bangalore",
        budget=Budget.MEDIUM,
        cuisine="North Indian",
        min_rating=4.0,
        additional_preferences="family-friendly",
    )
    assert prefs.location == "Bangalore"
    assert prefs.budget == Budget.MEDIUM


def test_user_preferences_strips_whitespace():
    prefs = UserPreferences(
        location="  Delhi  ",
        budget=Budget.LOW,
        cuisine=" Chinese ",
        min_rating=3.5,
    )
    assert prefs.location == "Delhi"
    assert prefs.cuisine == "Chinese"


@pytest.mark.parametrize(
    "location",
    ["", "   "],
)
def test_user_preferences_rejects_empty_location(location: str):
    with pytest.raises(ValidationError):
        UserPreferences(
            location=location,
            budget=Budget.HIGH,
            cuisine="Italian",
            min_rating=4.0,
        )


def test_user_preferences_rejects_empty_cuisine():
    with pytest.raises(ValidationError):
        UserPreferences(
            location="Mumbai",
            budget=Budget.LOW,
            cuisine="   ",
            min_rating=4.0,
        )


@pytest.mark.parametrize("min_rating", [-0.1, 5.1])
def test_user_preferences_rejects_invalid_min_rating(min_rating: float):
    with pytest.raises(ValidationError):
        UserPreferences(
            location="Mumbai",
            budget=Budget.LOW,
            cuisine="Italian",
            min_rating=min_rating,
        )


def test_user_preferences_allows_boundary_ratings():
    low = UserPreferences(
        location="Mumbai",
        budget=Budget.LOW,
        cuisine="Italian",
        min_rating=0.0,
    )
    high = UserPreferences(
        location="Mumbai",
        budget=Budget.LOW,
        cuisine="Italian",
        min_rating=5.0,
    )
    assert low.min_rating == 0.0
    assert high.min_rating == 5.0


def test_user_preferences_additional_preferences_optional():
    prefs = UserPreferences(
        location="Mumbai",
        budget=Budget.LOW,
        cuisine="Italian",
        min_rating=4.0,
        additional_preferences=None,
    )
    assert prefs.additional_preferences is None


def test_user_preferences_rejects_long_additional_preferences():
    with pytest.raises(ValidationError):
        UserPreferences(
            location="Mumbai",
            budget=Budget.LOW,
            cuisine="Italian",
            min_rating=4.0,
            additional_preferences="x" * 2001,
        )


def test_restaurant_generate_id_stable():
    id1 = Restaurant.generate_id("Truffles", "St. Marks Road, Bangalore")
    id2 = Restaurant.generate_id("Truffles", "St. Marks Road, Bangalore")
    id3 = Restaurant.generate_id("truffles", "  st. marks road, bangalore  ")
    assert id1 == id2 == id3
    assert len(id1) == 16


def test_candidate_from_restaurant():
    restaurant = Restaurant(
        id=Restaurant.generate_id("A", "B"),
        name="A",
        location="B",
        cuisines=["Chinese", "Thai"],
        rating=4.2,
        approx_cost=800.0,
    )
    candidate = Candidate.from_restaurant(restaurant)
    assert candidate.id == restaurant.id
    assert candidate.cuisines == ["Chinese", "Thai"]


def test_candidate_list_ids():
    candidates = CandidateList(
        items=[
            Candidate(
                id="abc",
                name="R1",
                location="L1",
                cuisines=["Indian"],
                rating=4.0,
            )
        ]
    )
    assert len(candidates) == 1
    assert candidates.ids() == {"abc"}


def test_llm_response_schema():
    response = LLMResponse(
        summary="Great picks for families.",
        recommendations=[
            LLMRecommendationItem(
                restaurant_id="id1",
                rank=1,
                explanation="Matches your cuisine and rating.",
            )
        ],
    )
    assert response.recommendations[0].rank == 1


def test_recommendation_response_no_matches():
    response = RecommendationResponse(
        status=RecommendationStatus.NO_MATCHES,
        message="No restaurants matched your filters.",
    )
    assert response.recommendations == []
    assert response.status == RecommendationStatus.NO_MATCHES


def test_prompt_payload():
    payload = PromptPayload(
        system_prompt="You are a helpful assistant.",
        user_prompt='{"preferences": {}}',
        prompt_version="v1",
    )
    assert payload.prompt_version == "v1"


def test_recommendation_result_fields():
    result = RecommendationResult(
        rank=1,
        restaurant_name="Test Rest",
        cuisine="Italian",
        rating=4.5,
        estimated_cost="₹800 for two",
        explanation="Fits your budget.",
        restaurant_id="abc123",
    )
    assert result.restaurant_name == "Test Rest"
