#!/usr/bin/env python3
"""Print HF column names and cost distribution for budget band tuning."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from restaurant_recommender.config import get_settings
from restaurant_recommender.ingestion.loader import load_raw_dataset
from restaurant_recommender.ingestion.normalizer import normalize_rows, parse_cost

_COST_COLUMN = "approx_cost(for two people)"


def main() -> None:
    settings = get_settings()
    print(f"Dataset: {settings.dataset_url}\n")

    rows = load_raw_dataset(settings.dataset_url)
    print("Columns:", sorted(rows[0].keys()) if rows else [])
    print(f"Raw rows: {len(rows)}\n")

    costs_raw = [parse_cost(row.get(_COST_COLUMN)) for row in rows]
    costs_raw = [c for c in costs_raw if c is not None]
    if costs_raw:
        import statistics

        print("Raw approx_cost (parsed) distribution:")
        print(f"  count: {len(costs_raw)}")
        print(f"  min:   {min(costs_raw):.0f}")
        print(f"  max:   {max(costs_raw):.0f}")
        print(f"  mean:  {statistics.mean(costs_raw):.0f}")
        print(f"  median:{statistics.median(costs_raw):.0f}")
        for threshold in (500, 1500):
            below = sum(1 for c in costs_raw if c <= threshold)
            print(f"  <= {threshold}: {below} ({100 * below / len(costs_raw):.1f}%)")

    restaurants = normalize_rows(rows)
    print(f"\nNormalized restaurants: {len(restaurants)}")
    bands = {}
    for r in restaurants:
        bands[r.cost_band or "unknown"] = bands.get(r.cost_band or "unknown", 0) + 1
    print("Cost bands:", dict(sorted(bands.items())))


if __name__ == "__main__":
    main()
