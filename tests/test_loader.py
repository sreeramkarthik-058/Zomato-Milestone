import pytest

from restaurant_recommender.ingestion.loader import parse_dataset_id


def test_parse_dataset_id_from_url():
    url = "https://huggingface.co/datasets/ManikaSaini/zomato-restaurant-recommendation"
    assert parse_dataset_id(url) == "ManikaSaini/zomato-restaurant-recommendation"


def test_parse_dataset_id_from_repo_id():
    assert parse_dataset_id("ManikaSaini/zomato-restaurant-recommendation") == (
        "ManikaSaini/zomato-restaurant-recommendation"
    )


def test_parse_dataset_id_invalid():
    with pytest.raises(ValueError):
        parse_dataset_id("not-a-valid-id")
