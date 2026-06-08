#!/usr/bin/env python3
"""Build tests/fixtures/restaurants_sample.parquet from sample HF rows."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from restaurant_recommender.ingestion.loader import load_raw_dataset
from restaurant_recommender.ingestion.normalizer import normalize_rows
from restaurant_recommender.store.restaurant_store import RestaurantStore

FIXTURE_PATH = ROOT / "tests" / "fixtures" / "restaurants_sample.parquet"
SAMPLE_SIZE = 15


def main() -> None:
    rows = load_raw_dataset(
        "ManikaSaini/zomato-restaurant-recommendation",
    )[:SAMPLE_SIZE]
    restaurants = normalize_rows(rows)
    FIXTURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    RestaurantStore().save_parquet(FIXTURE_PATH, restaurants)
    print(f"Wrote {len(restaurants)} restaurants to {FIXTURE_PATH}")


if __name__ == "__main__":
    main()
