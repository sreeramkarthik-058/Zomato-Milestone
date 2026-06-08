"""Parquet-backed in-memory restaurant catalog."""

from __future__ import annotations

import logging
import os
from pathlib import Path

import pandas as pd

from restaurant_recommender.models import Restaurant

logger = logging.getLogger(__name__)

_PARQUET_COLUMNS = [
    "id",
    "name",
    "location",
    "city",
    "cuisines",
    "rating",
    "approx_cost",
    "cost_band",
]


class RestaurantStore:
    """Read-only catalog loaded from a local Parquet cache."""

    def __init__(self) -> None:
        self._restaurants: list[Restaurant] = []
        self._by_id: dict[str, Restaurant] = {}
        self._cache_path: Path | None = None

    def load_parquet(self, path: Path) -> int:
        """Load restaurants from Parquet; returns row count."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Restaurant cache not found: {path}")

        try:
            frame = pd.read_parquet(path)
        except Exception as exc:
            raise ValueError(f"Corrupt or unreadable Parquet cache: {path}") from exc

        if frame.empty:
            raise ValueError(f"Restaurant cache is empty: {path}")

        missing = [col for col in _PARQUET_COLUMNS if col not in frame.columns]
        if missing:
            raise ValueError(f"Parquet cache missing columns {missing}: {path}")

        restaurants: list[Restaurant] = []
        for record in frame.to_dict(orient="records"):
            cuisines = record.get("cuisines")
            if cuisines is None or (isinstance(cuisines, float) and pd.isna(cuisines)):
                cuisines_list: list[str] = []
            elif isinstance(cuisines, list):
                cuisines_list = [str(c) for c in cuisines]
            else:
                cuisines_list = [str(cuisines)]

            approx = record.get("approx_cost")
            if approx is not None and isinstance(approx, float) and pd.isna(approx):
                approx = None

            city = record.get("city")
            if city is not None and isinstance(city, float) and pd.isna(city):
                city = None

            cost_band = record.get("cost_band")
            if cost_band is not None and isinstance(cost_band, float) and pd.isna(cost_band):
                cost_band = None

            restaurants.append(
                Restaurant(
                    id=str(record["id"]),
                    name=str(record["name"]),
                    location=str(record["location"]),
                    city=str(city) if city is not None else None,
                    cuisines=cuisines_list,
                    rating=float(record["rating"]),
                    approx_cost=float(approx) if approx is not None else None,
                    cost_band=str(cost_band) if cost_band is not None else None,
                )
            )

        self._restaurants = restaurants
        self._by_id = {r.id: r for r in restaurants}
        self._cache_path = path
        logger.info("Loaded %s restaurants from %s", len(restaurants), path)
        return len(restaurants)

    def save_parquet(self, path: Path, restaurants: list[Restaurant]) -> None:
        """Persist restaurants to Parquet using atomic replace (EC-ING-18)."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        records = [
            {
                "id": r.id,
                "name": r.name,
                "location": r.location,
                "city": r.city,
                "cuisines": r.cuisines,
                "rating": r.rating,
                "approx_cost": r.approx_cost,
                "cost_band": r.cost_band,
            }
            for r in restaurants
        ]
        frame = pd.DataFrame.from_records(records, columns=_PARQUET_COLUMNS)

        temp_path = path.with_suffix(path.suffix + ".tmp")
        frame.to_parquet(temp_path, index=False)
        os.replace(temp_path, path)

        self._restaurants = restaurants
        self._by_id = {r.id: r for r in restaurants}
        self._cache_path = path
        logger.info("Saved %s restaurants to %s", len(restaurants), path)

    def get_all(self) -> list[Restaurant]:
        return list(self._restaurants)

    def get_by_id(self, restaurant_id: str) -> Restaurant | None:
        return self._by_id.get(restaurant_id)

    def count(self) -> int:
        return len(self._restaurants)

    def is_loaded(self) -> bool:
        return bool(self._restaurants)
