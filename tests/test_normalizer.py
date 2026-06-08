from restaurant_recommender.ingestion.normalizer import (
    normalize_row,
    normalize_rows,
    parse_cost,
    parse_cuisines,
    parse_rating,
)
from restaurant_recommender.models import Restaurant


def test_parse_rating_from_fraction():
    assert parse_rating("4.1/5") == 4.1


def test_parse_rating_missing():
    assert parse_rating("NEW") is None
    assert parse_rating("-") is None


def test_parse_cost_single_value():
    assert parse_cost("800") == 800.0


def test_parse_cost_range():
    assert parse_cost("300-600") == 450.0


def test_parse_cuisines():
    assert parse_cuisines("North Indian, Chinese") == ["North Indian", "Chinese"]


def test_normalize_row_valid():
    row = {
        "name": "Jalsa",
        "address": "942, 21st Main Road, Banashankari, Bangalore",
        "location": "Banashankari",
        "cuisines": "North Indian, Mughlai, Chinese",
        "rate": "4.1/5",
        "approx_cost(for two people)": "800",
    }
    restaurant = normalize_row(row)
    assert restaurant is not None
    assert restaurant.name == "Jalsa"
    assert restaurant.city == "Bangalore"
    assert restaurant.rating == 4.1
    assert restaurant.approx_cost == 800.0
    assert restaurant.cost_band == "medium"
    assert len(restaurant.id) == 16


def test_normalize_row_drops_missing_rating():
    row = {
        "name": "Test",
        "address": "1 Road, Delhi",
        "rate": "NEW",
        "cuisines": "Indian",
        "approx_cost(for two people)": "500",
    }
    assert normalize_row(row) is None


def test_normalize_row_drops_missing_name():
    assert normalize_row({"address": "Somewhere, Mumbai", "rate": "4.0/5"}) is None


def test_normalize_rows_deduplicates_keeps_higher_rating():
    rows = [
        {
            "name": "Dup",
            "address": "Same Place, Bangalore",
            "rate": "3.0/5",
            "cuisines": "Indian",
            "approx_cost(for two people)": "400",
        },
        {
            "name": "Dup",
            "address": "Same Place, Bangalore",
            "rate": "4.5/5",
            "cuisines": "Indian",
            "approx_cost(for two people)": "400",
        },
    ]
    result = normalize_rows(rows)
    assert len(result) == 1
    assert result[0].rating == 4.5
    assert result[0].id == Restaurant.generate_id("Dup", "Same Place, Bangalore")
