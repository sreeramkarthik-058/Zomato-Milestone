from pathlib import Path

import pytest

from restaurant_recommender.config import Settings, clear_settings_cache
from restaurant_recommender.filtering.budget import matches_budget, restaurant_cost_band
from restaurant_recommender.filtering.filter_service import (
    FilterService,
    matches_cuisine,
    matches_location,
    matches_rating,
)
from restaurant_recommender.filtering.location import expand_location_terms
from restaurant_recommender.models import Budget, Restaurant, UserPreferences
from restaurant_recommender.store.restaurant_store import RestaurantStore

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "restaurants_sample.parquet"


def _restaurant(
    name: str,
    *,
    city: str,
    location: str | None = None,
    cuisines: list[str] | None = None,
    rating: float = 4.0,
    approx_cost: float | None = 800.0,
    cost_band: str | None = None,
) -> Restaurant:
    loc = location or f"1 Main St, {city}"
    band = cost_band
    if band is None and approx_cost is not None:
        from restaurant_recommender.ingestion.budget import cost_band_from_amount

        band = cost_band_from_amount(approx_cost)
    return Restaurant(
        id=Restaurant.generate_id(name, loc),
        name=name,
        location=loc,
        city=city,
        cuisines=cuisines or ["North Indian"],
        rating=rating,
        approx_cost=approx_cost,
        cost_band=band,
    )


@pytest.fixture
def catalog() -> list[Restaurant]:
    return [
        _restaurant("Bangalore Medium", city="Bangalore", approx_cost=800.0, rating=4.5),
        _restaurant("Bangalore Low", city="Bangalore", approx_cost=300.0, rating=4.0),
        _restaurant("Delhi Chinese", city="Delhi", cuisines=["Chinese"], approx_cost=600.0),
        _restaurant(
            "Delhi Strict",
            city="Delhi",
            cuisines=["Chinese"],
            rating=3.5,
            approx_cost=600.0,
        ),
        _restaurant(
            "Mumbai High",
            city="Mumbai",
            cuisines=["Italian"],
            approx_cost=2000.0,
            rating=4.8,
        ),
        _restaurant(
            "No Cost",
            city="Bangalore",
            approx_cost=None,
            cost_band=None,
            rating=4.9,
        ),
    ]


@pytest.fixture
def loaded_store(catalog: list[Restaurant], tmp_path: Path) -> RestaurantStore:
    path = tmp_path / "test.parquet"
    store = RestaurantStore()
    store.save_parquet(path, catalog)
    store.load_parquet(path)
    return store


@pytest.fixture(autouse=True)
def _clear_settings():
    clear_settings_cache()
    yield
    clear_settings_cache()


# --- location ---


def test_expand_location_terms_bengaluru():
    terms = expand_location_terms("Bengaluru")
    assert "bengaluru" in terms
    assert "bangalore" in terms


def test_matches_location_city():
    r = _restaurant("X", city="Bangalore", location="Area, Bangalore")
    assert matches_location(city=r.city, location=r.location, preference="bangalore")


def test_matches_location_alias():
    r = _restaurant("X", city="Bangalore", location="Banashankari, Bangalore")
    assert matches_location(city=r.city, location=r.location, preference="Bengaluru")


def test_matches_location_no_match():
    r = _restaurant("X", city="Delhi", location="Connaught Place, Delhi")
    assert not matches_location(city=r.city, location=r.location, preference="Mumbai")


# --- cuisine ---


def test_matches_cuisine_substring():
    r = _restaurant("X", city="Delhi", cuisines=["North Indian", "Chinese"])
    assert matches_cuisine(r, "north indian")
    assert matches_cuisine(r, "Chinese")
    assert not matches_cuisine(r, "Italian")


# --- rating ---


def test_matches_rating_boundary():
    r = _restaurant("X", city="Delhi", rating=4.0)
    assert matches_rating(r, 4.0)
    assert matches_rating(r, 3.5)
    assert not matches_rating(r, 4.1)


# --- budget ---


def test_matches_budget_tiers():
    low = _restaurant("L", city="Delhi", approx_cost=400.0)
    high = _restaurant("H", city="Delhi", approx_cost=2000.0)
    assert matches_budget(low, Budget.LOW)
    assert not matches_budget(low, Budget.HIGH)
    assert matches_budget(high, Budget.HIGH)


def test_matches_budget_excludes_missing_cost():
    r = _restaurant("N", city="Bangalore", approx_cost=None, cost_band=None)
    assert restaurant_cost_band(r) is None
    assert not matches_budget(r, Budget.LOW)


# --- FilterService ---


def test_filter_combined_prefs(loaded_store: RestaurantStore):
    prefs = UserPreferences(
        location="Bangalore",
        budget=Budget.MEDIUM,
        cuisine="North Indian",
        min_rating=4.0,
    )
    service = FilterService(settings=Settings(max_candidates=20))
    result = service.filter(prefs, loaded_store)

    names = {c.name for c in result.items}
    assert "Bangalore Medium" in names
    assert "Bangalore Low" not in names  # low budget band
    assert "Delhi Chinese" not in names
    assert "No Cost" not in names  # missing cost


def test_filter_respects_max_candidates(loaded_store: RestaurantStore):
    prefs = UserPreferences(
        location="Delhi",
        budget=Budget.MEDIUM,
        cuisine="Chinese",
        min_rating=3.0,
    )
    service = FilterService(settings=Settings(max_candidates=1))
    result = service.filter(prefs, loaded_store)
    assert len(result) == 1
    assert result.items[0].name == "Delhi Chinese"  # higher rating than Delhi Strict


def test_filter_empty_when_no_match(loaded_store: RestaurantStore):
    prefs = UserPreferences(
        location="Chennai",
        budget=Budget.LOW,
        cuisine="Italian",
        min_rating=4.0,
    )
    result = FilterService().filter(prefs, loaded_store)
    assert len(result) == 0


def test_additional_preferences_do_not_affect_filter_count(loaded_store: RestaurantStore):
    base = UserPreferences(
        location="Delhi",
        budget=Budget.MEDIUM,
        cuisine="Chinese",
        min_rating=4.0,
    )
    with_extra = UserPreferences(
        location="Delhi",
        budget=Budget.MEDIUM,
        cuisine="Chinese",
        min_rating=4.0,
        additional_preferences="family-friendly rooftop",
    )
    service = FilterService()
    assert len(service.filter(base, loaded_store)) == len(
        service.filter(with_extra, loaded_store)
    )


def test_filter_unloaded_store_raises():
    prefs = UserPreferences(
        location="Delhi",
        budget=Budget.LOW,
        cuisine="Indian",
        min_rating=4.0,
    )
    with pytest.raises(RuntimeError, match="not loaded"):
        FilterService().filter(prefs, RestaurantStore())


def test_filter_fixture_parquet_integration():
    if not FIXTURE_PATH.exists():
        pytest.skip("fixture missing")

    store = RestaurantStore()
    store.load_parquet(FIXTURE_PATH)

    prefs = UserPreferences(
        location="Bangalore",
        budget=Budget.MEDIUM,
        cuisine="North Indian",
        min_rating=3.5,
    )
    result = FilterService(settings=Settings(max_candidates=20)).filter(prefs, store)
    assert len(result) <= 20
    for candidate in result.items:
        assert candidate.id
        assert candidate.rating >= 3.5
