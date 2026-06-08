"""End-to-end recommendation pipeline (architecture §4.7)."""

from __future__ import annotations

import logging

from restaurant_recommender.config import Settings, get_settings
from restaurant_recommender.filtering.filter_service import FilterService
from restaurant_recommender.ingestion.service import DataIngestionService
from restaurant_recommender.llm.engine import RecommendationEngine
from restaurant_recommender.llm.prompt_builder import PromptBuilder
from restaurant_recommender.models import (
    RecommendationResponse,
    RecommendationStatus,
    UserPreferences,
)
from restaurant_recommender.store.restaurant_store import RestaurantStore

logger = logging.getLogger(__name__)


class RecommendationOrchestrator:
    """Coordinates ingestion, filtering, and LLM ranking into one call."""

    def __init__(
        self,
        settings: Settings | None = None,
        store: RestaurantStore | None = None,
        ingestion_service: DataIngestionService | None = None,
        filter_service: FilterService | None = None,
        prompt_builder: PromptBuilder | None = None,
        engine: RecommendationEngine | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._store = store or RestaurantStore()
        
        # Dependency injection for services
        self._ingestion = ingestion_service or DataIngestionService(
            self._settings, self._store
        )
        self._filter = filter_service or FilterService(self._settings)
        self._prompt_builder = prompt_builder or PromptBuilder(self._settings)
        self._engine = engine or RecommendationEngine(self._settings)

    def recommend(self, preferences: UserPreferences) -> RecommendationResponse:
        """
        Execute the full pipeline for a set of user preferences.
        
        1. Ingest/Load data
        2. Filter to shortlist
        3. Rank with LLM
        """
        try:
            # 1. Ingestion / Cache Load
            # This ensures the store is populated before filtering
            self._ingestion.run_if_needed()
            
            # 2. Filtering
            candidates = self._filter.filter(preferences, self._store)
            
            if not candidates.items:
                return RecommendationResponse(
                    status=RecommendationStatus.NO_MATCHES,
                    message="No restaurants match your filters (location, cuisine, rating, budget).",
                )
            
            # 3. Prompt Building
            prompt = self._prompt_builder.build(preferences, candidates)
            
            # 4. LLM Ranking and Enrichment
            # Note: Engine already handles enrichment and formatting via OutputFormatter
            return self._engine.recommend(prompt, candidates, self._store)
            
        except Exception as exc:
            logger.exception("Orchestration pipeline failed")
            return RecommendationResponse(
                status=RecommendationStatus.ERROR,
                message=f"An unexpected error occurred: {exc}",
            )
