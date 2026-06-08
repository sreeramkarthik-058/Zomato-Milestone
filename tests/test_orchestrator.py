import json
import pytest
from unittest.mock import MagicMock

from restaurant_recommender.orchestrator import RecommendationOrchestrator
from restaurant_recommender.models import (
    UserPreferences,
    Budget,
    RecommendationStatus,
    Restaurant,
)
from restaurant_recommender.llm.provider import MockLLMProvider
from restaurant_recommender.config import clear_settings_cache


@pytest.fixture(autouse=True)
def _clear_settings():
    clear_settings_cache()
    yield
    clear_settings_cache()


@pytest.fixture
def store_with_data(tmp_path):
    from restaurant_recommender.store.restaurant_store import RestaurantStore
    
    r1 = Restaurant(
        id="id1",
        name="Alpha",
        location="Indiranagar, Bangalore",
        city="Bangalore",
        cuisines=["North Indian"],
        rating=4.5,
        approx_cost=800.0,
        cost_band="medium",
    )
    r2 = Restaurant(
        id="id2",
        name="Beta",
        location="Koramangala, Bangalore",
        city="Bangalore",
        cuisines=["Chinese"],
        rating=4.2,
        approx_cost=1200.0,
        cost_band="medium",
    )
    
    path = tmp_path / "test_store.parquet"
    store = RestaurantStore()
    store.save_parquet(path, [r1, r2])
    store.load_parquet(path)
    return store


@pytest.fixture
def mock_ingestion():
    service = MagicMock()
    # run_if_needed just needs to be called
    service.run_if_needed.return_value = None
    return service


def test_orchestrator_success(store_with_data, mock_ingestion):
    # Setup mock provider to return a valid JSON response
    llm_payload = {
        "summary": "Enjoy these top picks.",
        "recommendations": [
            {"restaurant_id": "id1", "rank": 1, "explanation": "Top rated."}
        ]
    }
    provider = MockLLMProvider(json.dumps(llm_payload))
    
    orchestrator = RecommendationOrchestrator(
        store=store_with_data,
        ingestion_service=mock_ingestion,
        engine=None # It will create one with default provider, but we can't easily inject mock provider here without more complex DI or mocking create_llm_provider
    )
    
    # Actually, it's better to inject the engine with the mock provider
    from restaurant_recommender.llm.engine import RecommendationEngine
    engine = RecommendationEngine(provider=provider)
    orchestrator = RecommendationOrchestrator(
        store=store_with_data,
        ingestion_service=mock_ingestion,
        engine=engine
    )
    
    prefs = UserPreferences(
        location="Bangalore",
        budget=Budget.MEDIUM,
        cuisine="North Indian",
        min_rating=4.0
    )
    
    response = orchestrator.recommend(prefs)
    
    assert response.status == RecommendationStatus.SUCCESS
    assert len(response.recommendations) == 1
    assert response.recommendations[0].restaurant_name == "Alpha"
    assert response.summary == "Enjoy these top picks."
    mock_ingestion.run_if_needed.assert_called_once()


def test_orchestrator_no_matches(store_with_data, mock_ingestion):
    orchestrator = RecommendationOrchestrator(
        store=store_with_data,
        ingestion_service=mock_ingestion
    )
    
    prefs = UserPreferences(
        location="Bangalore",
        budget=Budget.MEDIUM,
        cuisine="Italian", # No Italian in store
        min_rating=4.0
    )
    
    response = orchestrator.recommend(prefs)
    
    assert response.status == RecommendationStatus.NO_MATCHES
    assert "No restaurants match" in response.message
    mock_ingestion.run_if_needed.assert_called_once()
