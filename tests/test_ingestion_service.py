from pathlib import Path
from unittest.mock import patch

import pytest

from restaurant_recommender.config import Settings, clear_settings_cache
from restaurant_recommender.ingestion.service import DataIngestionService
from restaurant_recommender.models import Restaurant
from restaurant_recommender.store.restaurant_store import RestaurantStore

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "restaurants_sample.parquet"


@pytest.fixture
def sample_restaurants() -> list[Restaurant]:
    return [
        Restaurant(
            id=Restaurant.generate_id("Spice", "2nd Floor, Bangalore"),
            name="Spice",
            location="2nd Floor, 80 Feet Road, Bangalore",
            city="Bangalore",
            cuisines=["Chinese"],
            rating=4.1,
            approx_cost=800.0,
            cost_band="medium",
        ),
    ]


@pytest.fixture(autouse=True)
def _clear_settings():
    clear_settings_cache()
    yield
    clear_settings_cache()


def test_run_if_needed_uses_cache(tmp_path: Path, sample_restaurants: list[Restaurant]):
    cache = tmp_path / "restaurants.parquet"
    RestaurantStore().save_parquet(cache, sample_restaurants)

    settings = Settings(cache_path=cache, force_refresh=False)
    service = DataIngestionService(settings=settings)

    with patch(
        "restaurant_recommender.ingestion.service.load_raw_dataset",
    ) as mock_load:
        report = service.run_if_needed()

    mock_load.assert_not_called()
    assert report.from_cache is True
    assert report.refreshed is False
    assert report.rows_saved == 1
    assert service.store.count() == 1


def test_run_if_needed_refreshes_when_forced(
    tmp_path: Path,
    sample_restaurants: list[Restaurant],
):
    cache = tmp_path / "restaurants.parquet"
    RestaurantStore().save_parquet(cache, sample_restaurants)

    raw_row = {
        "name": "New Place",
        "address": "99 Street, Mumbai",
        "rate": "4.5/5",
        "cuisines": "Italian",
        "approx_cost(for two people)": "1200",
    }

    settings = Settings(cache_path=cache, force_refresh=True)
    service = DataIngestionService(settings=settings)

    with patch(
        "restaurant_recommender.ingestion.service.load_raw_dataset",
        return_value=[raw_row],
    ):
        report = service.run_if_needed()

    assert report.refreshed is True
    assert report.from_cache is False
    assert report.rows_raw == 1
    assert service.store.count() == 1
    assert service.store.get_all()[0].name == "New Place"


def test_run_if_needed_downloads_when_no_cache(tmp_path: Path):
    cache = tmp_path / "data" / "restaurants.parquet"
    settings = Settings(cache_path=cache, force_refresh=False)
    service = DataIngestionService(settings=settings)

    raw_row = {
        "name": "Cafe",
        "address": "1 Lane, Delhi",
        "rate": "4.0/5",
        "cuisines": "Cafe",
        "approx_cost(for two people)": "400",
    }

    with patch(
        "restaurant_recommender.ingestion.service.load_raw_dataset",
        return_value=[raw_row],
    ):
        report = service.run_if_needed()

    assert cache.exists()
    assert report.rows_saved == 1
    assert service.store.is_loaded()


def test_run_if_needed_raises_when_normalization_empty(tmp_path: Path):
    cache = tmp_path / "restaurants.parquet"
    settings = Settings(cache_path=cache, force_refresh=True)
    service = DataIngestionService(settings=settings)

    with patch(
        "restaurant_recommender.ingestion.service.load_raw_dataset",
        return_value=[{"name": "", "rate": "4/5"}],
    ):
        with pytest.raises(ValueError, match="No valid restaurants"):
            service.run_if_needed()
