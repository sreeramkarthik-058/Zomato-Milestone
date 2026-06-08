from pathlib import Path

import pandas as pd
import pytest

from restaurant_recommender.models import Restaurant
from restaurant_recommender.store.restaurant_store import RestaurantStore

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "restaurants_sample.parquet"


@pytest.fixture
def sample_restaurants() -> list[Restaurant]:
    return [
        Restaurant(
            id=Restaurant.generate_id("A", "Addr A, Bangalore"),
            name="A",
            location="Addr A, Bangalore",
            city="Bangalore",
            cuisines=["Indian"],
            rating=4.2,
            approx_cost=600.0,
            cost_band="medium",
        ),
        Restaurant(
            id=Restaurant.generate_id("B", "Addr B, Delhi"),
            name="B",
            location="Addr B, Delhi",
            city="Delhi",
            cuisines=["Chinese"],
            rating=4.8,
            approx_cost=200.0,
            cost_band="low",
        ),
    ]


def test_save_and_load_parquet(tmp_path: Path, sample_restaurants: list[Restaurant]):
    path = tmp_path / "restaurants.parquet"
    store = RestaurantStore()
    store.save_parquet(path, sample_restaurants)

    assert path.exists()
    reloaded = RestaurantStore()
    count = reloaded.load_parquet(path)
    assert count == 2
    assert reloaded.get_by_id(sample_restaurants[0].id) is not None
    assert reloaded.get_all()[1].name == "B"


def test_get_by_id_missing():
    store = RestaurantStore()
    assert store.get_by_id("missing") is None


def test_load_missing_file():
    store = RestaurantStore()
    with pytest.raises(FileNotFoundError):
        store.load_parquet(Path("/nonexistent/restaurants.parquet"))


def test_load_corrupt_parquet(tmp_path: Path):
    path = tmp_path / "bad.parquet"
    path.write_text("not parquet", encoding="utf-8")
    store = RestaurantStore()
    with pytest.raises(ValueError, match="Corrupt"):
        store.load_parquet(path)


def test_fixture_parquet_has_required_fields():
    if not FIXTURE_PATH.exists():
        pytest.skip("Run scripts/build_fixture.py to create sample parquet")

    store = RestaurantStore()
    count = store.load_parquet(FIXTURE_PATH)
    assert 10 <= count <= 20
    for restaurant in store.get_all():
        assert restaurant.id
        assert restaurant.name
        assert restaurant.location
        assert restaurant.rating >= 0
