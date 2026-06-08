import json

import pytest

from restaurant_recommender.config import Settings, clear_settings_cache
from restaurant_recommender.llm.engine import RecommendationEngine
from restaurant_recommender.llm.prompt_builder import PromptBuilder
from restaurant_recommender.llm.provider import GroqProvider, LLMProviderError, MockLLMProvider
from restaurant_recommender.models import (
    Budget,
    Candidate,
    CandidateList,
    RecommendationStatus,
    Restaurant,
    UserPreferences,
)
from restaurant_recommender.store.restaurant_store import RestaurantStore

FIXTURE_PATH = __import__("pathlib").Path(__file__).parent / "fixtures" / "restaurants_sample.parquet"


def _restaurant(
    name: str,
    rid: str,
    *,
    city: str = "Bangalore",
    cuisines: list[str] | None = None,
    rating: float = 4.5,
    cost: float = 800.0,
) -> Restaurant:
    location = f"1 Main, {city}"
    return Restaurant(
        id=rid,
        name=name,
        location=location,
        city=city,
        cuisines=cuisines or ["North Indian"],
        rating=rating,
        approx_cost=cost,
        cost_band="medium",
    )


@pytest.fixture(autouse=True)
def _clear_settings():
    clear_settings_cache()
    yield
    clear_settings_cache()


@pytest.fixture
def store(tmp_path) -> RestaurantStore:
    r1 = _restaurant("Alpha", "id1")
    r2 = _restaurant("Beta", "id2", rating=4.2)
    path = tmp_path / "data.parquet"
    s = RestaurantStore()
    s.save_parquet(path, [r1, r2])
    s.load_parquet(path)
    return s


@pytest.fixture
def candidates() -> CandidateList:
    return CandidateList(
        items=[
            Candidate(
                id="id1",
                name="Alpha",
                location="1 Main, Bangalore",
                cuisines=["North Indian"],
                rating=4.5,
                approx_cost=800.0,
            ),
            Candidate(
                id="id2",
                name="Beta",
                location="1 Main, Bangalore",
                cuisines=["North Indian"],
                rating=4.2,
                approx_cost=800.0,
            ),
        ]
    )


@pytest.fixture
def preferences() -> UserPreferences:
    return UserPreferences(
        location="Bangalore",
        budget=Budget.MEDIUM,
        cuisine="North Indian",
        min_rating=4.0,
    )


def _mock_response(**overrides: object) -> str:
    payload = {
        "summary": "Two strong North Indian picks in Bangalore.",
        "recommendations": [
            {
                "restaurant_id": "id1",
                "rank": 1,
                "explanation": "Highest rating and fits your cuisine.",
            },
            {
                "restaurant_id": "id2",
                "rank": 2,
                "explanation": "Good alternative within budget.",
            },
        ],
    }
    payload.update(overrides)
    return json.dumps(payload)


def test_engine_success_with_mock_provider(
    store: RestaurantStore,
    candidates: CandidateList,
    preferences: UserPreferences,
):
    prompt = PromptBuilder(settings=Settings(prompt_version="v1", top_n=5)).build(
        preferences,
        candidates,
    )
    provider = MockLLMProvider(_mock_response())
    engine = RecommendationEngine(provider=provider)

    response = engine.recommend(prompt, candidates, store)

    assert response.status == RecommendationStatus.SUCCESS
    assert len(response.recommendations) == 2
    assert response.recommendations[0].restaurant_name == "Alpha"
    assert response.recommendations[0].rating == 4.5
    assert "North Indian" in response.recommendations[0].cuisine
    assert "₹800" in response.recommendations[0].estimated_cost
    assert response.recommendations[0].explanation
    assert response.summary is not None
    assert provider.call_count == 1


def test_engine_drops_unknown_id_from_mock(
    store: RestaurantStore,
    candidates: CandidateList,
    preferences: UserPreferences,
):
    body = {
        "recommendations": [
            {"restaurant_id": "id1", "rank": 1, "explanation": "ok"},
            {"restaurant_id": "unknown", "rank": 2, "explanation": "skip"},
        ]
    }
    prompt = PromptBuilder(settings=Settings()).build(preferences, candidates)
    engine = RecommendationEngine(provider=MockLLMProvider(json.dumps(body)))

    response = engine.recommend(prompt, candidates, store)

    assert response.status == RecommendationStatus.SUCCESS
    assert len(response.recommendations) == 1
    assert response.recommendations[0].restaurant_id == "id1"


def test_engine_repair_on_invalid_json(
    store: RestaurantStore,
    candidates: CandidateList,
    preferences: UserPreferences,
):
    valid = _mock_response()

    class RepairMock(MockLLMProvider):
        def __init__(self):
            super().__init__("not json")
            self._queue = ["not json", valid]

        def complete(self, messages: list[dict[str, str]]) -> str:
            self.call_count += 1
            self.last_messages = messages
            return self._queue.pop(0)

    prompt = PromptBuilder(settings=Settings()).build(preferences, candidates)
    provider = RepairMock()
    engine = RecommendationEngine(provider=provider)

    response = engine.recommend(prompt, candidates, store)

    assert response.status == RecommendationStatus.SUCCESS
    assert len(response.recommendations) == 2
    assert provider.call_count == 2


def test_engine_enrichment_uses_store_not_llm_values(
    store: RestaurantStore,
    candidates: CandidateList,
    preferences: UserPreferences,
):
    body = {
        "recommendations": [
            {
                "restaurant_id": "id1",
                "rank": 1,
                "explanation": "Pick",
            }
        ]
    }
    prompt = PromptBuilder(settings=Settings()).build(preferences, candidates)
    engine = RecommendationEngine(provider=MockLLMProvider(json.dumps(body)))
    response = engine.recommend(prompt, candidates, store)

    assert response.recommendations[0].restaurant_name == "Alpha"
    assert response.recommendations[0].rating == 4.5


def test_groq_provider_requires_api_key():
    with pytest.raises(LLMProviderError, match="LLM_API_KEY"):
        GroqProvider(settings=Settings(llm_api_key=""))


def test_create_provider_uses_groq():
    from restaurant_recommender.llm.provider import create_llm_provider

    with pytest.raises(LLMProviderError, match="LLM_API_KEY"):
        create_llm_provider(Settings(llm_provider="groq", llm_api_key=""))
