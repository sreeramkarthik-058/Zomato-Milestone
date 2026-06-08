"""Map Hugging Face rows to normalized Restaurant models."""

from __future__ import annotations

import re
from typing import Any

from restaurant_recommender.ingestion.budget import cost_band_from_amount
from restaurant_recommender.models import Restaurant

# Hugging Face column names → internal fields
#   name                          → name
#   address                       → location (full address for search/display)
#   address (last segment)        → city
#   location                      → area (fallback if address missing)
#   cuisines                      → cuisines (comma-separated list)
#   rate                          → rating (e.g. "4.1/5")
#   approx_cost(for two people)   → approx_cost, cost_band

_COST_COLUMN = "approx_cost(for two people)"
_MISSING_RATE_VALUES = frozenset({"", "-", "nan", "new", "none", "null"})


def parse_rating(raw: Any) -> float | None:
    """Parse Zomato rate field (e.g. '4.1/5') to float."""
    if raw is None:
        return None
    text = str(raw).strip()
    if not text or text.lower() in _MISSING_RATE_VALUES:
        return None
    if "/" in text:
        text = text.split("/", 1)[0].strip()
    try:
        value = float(text)
    except ValueError:
        return None
    if value < 0:
        return None
    return value


def parse_cost(raw: Any) -> float | None:
    """Parse approx cost for two; supports '800', '300-600', etc."""
    if raw is None:
        return None
    text = str(raw).strip().replace(",", "")
    if not text or text.lower() in _MISSING_RATE_VALUES:
        return None

    numbers = [float(n) for n in re.findall(r"\d+(?:\.\d+)?", text)]
    if not numbers:
        return None
    if len(numbers) >= 2 and ("-" in text or "to" in text.lower()):
        return (numbers[0] + numbers[1]) / 2
    return numbers[0]


def parse_cuisines(raw: Any) -> list[str]:
    """Split comma-separated cuisine string into a list."""
    if raw is None:
        return []
    text = str(raw).strip()
    if not text or text.lower() in _MISSING_RATE_VALUES:
        return []
    return [part.strip() for part in text.split(",") if part.strip()]


def extract_city_from_address(address: str) -> str | None:
    """Use the last comma-separated segment as city (e.g. Bangalore)."""
    parts = [part.strip() for part in address.split(",") if part.strip()]
    if not parts:
        return None
    return parts[-1]


def build_location(row: dict[str, Any], city: str | None) -> str | None:
    """Prefer full address; fall back to area + city."""
    address = str(row.get("address") or "").strip()
    if address:
        return address
    area = str(row.get("location") or "").strip()
    if area and city:
        return f"{area}, {city}"
    return area or city or None


def normalize_row(row: dict[str, Any]) -> Restaurant | None:
    """Convert one HF row to Restaurant; return None if required fields missing."""
    name = str(row.get("name") or "").strip()
    if not name:
        return None

    address = str(row.get("address") or "").strip()
    city = extract_city_from_address(address) if address else None
    if not city:
        listed_city = str(row.get("listed_in(city)") or "").strip()
        city = listed_city or None

    location = build_location(row, city)
    if not location:
        return None

    rating = parse_rating(row.get("rate"))
    if rating is None:
        return None

    approx_cost = parse_cost(row.get(_COST_COLUMN))
    cuisines = parse_cuisines(row.get("cuisines"))

    restaurant_id = Restaurant.generate_id(name, location)
    return Restaurant(
        id=restaurant_id,
        name=name,
        location=location,
        city=city,
        cuisines=cuisines,
        rating=rating,
        approx_cost=approx_cost,
        cost_band=cost_band_from_amount(approx_cost),
    )


def normalize_rows(rows: list[dict[str, Any]]) -> list[Restaurant]:
    """
    Normalize and deduplicate rows.

    Duplicate ids (same name + location) keep the row with the highest rating.
    """
    by_id: dict[str, Restaurant] = {}
    for row in rows:
        restaurant = normalize_row(row)
        if restaurant is None:
            continue
        existing = by_id.get(restaurant.id)
        if existing is None or restaurant.rating > existing.rating:
            by_id[restaurant.id] = restaurant
    return list(by_id.values())
