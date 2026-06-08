"""Orchestrate dataset download, normalization, and cache persistence."""

from __future__ import annotations

import logging
from pathlib import Path

from pydantic import BaseModel, Field

from restaurant_recommender.config import Settings, get_settings
from restaurant_recommender.ingestion.loader import load_raw_dataset
from restaurant_recommender.ingestion.normalizer import normalize_rows
from restaurant_recommender.store.restaurant_store import RestaurantStore

logger = logging.getLogger(__name__)


class IngestionReport(BaseModel):
    """Summary of an ingestion or cache load operation."""

    source: str
    cache_path: Path
    rows_raw: int = 0
    rows_normalized: int = 0
    rows_saved: int = 0
    from_cache: bool = False
    refreshed: bool = False


class DataIngestionService:
    """Load HF data when needed and maintain the local Parquet cache."""

    def __init__(
        self,
        settings: Settings | None = None,
        store: RestaurantStore | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._store = store or RestaurantStore()

    @property
    def store(self) -> RestaurantStore:
        return self._store

    def cache_exists(self) -> bool:
        return self._settings.cache_path.exists()

    def should_refresh(self) -> bool:
        return self._settings.force_refresh or not self.cache_exists()

    def run_if_needed(self) -> IngestionReport:
        """
        Load cache if present and not forcing refresh; otherwise ingest from HF.

        Returns an IngestionReport describing what happened.
        """
        cache_path = self._settings.cache_path

        if not self.should_refresh():
            count = self._store.load_parquet(cache_path)
            return IngestionReport(
                source=str(self._settings.dataset_url),
                cache_path=cache_path,
                rows_saved=count,
                rows_normalized=count,
                from_cache=True,
                refreshed=False,
            )

        logger.info("Downloading dataset from %s", self._settings.dataset_url)
        raw_rows = load_raw_dataset(self._settings.dataset_url)
        if not raw_rows:
            raise ValueError("Dataset returned zero rows")

        restaurants = normalize_rows(raw_rows)
        if not restaurants:
            raise ValueError("No valid restaurants after normalization")

        self._store.save_parquet(cache_path, restaurants)

        return IngestionReport(
            source=str(self._settings.dataset_url),
            cache_path=cache_path,
            rows_raw=len(raw_rows),
            rows_normalized=len(restaurants),
            rows_saved=len(restaurants),
            from_cache=False,
            refreshed=True,
        )
