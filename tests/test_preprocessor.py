"""Phase 1: preprocessor unit tests."""

from __future__ import annotations

import pytest

from config.settings import Settings
from src.data.preprocessor import (
    assign_budget_band,
    normalize_city,
    parse_cost,
    parse_cuisines,
    parse_rating,
    preprocess_row,
    preprocess_rows,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("4.1/5", 4.1),
        ("4.5/5", 4.5),
        ("NEW", None),
        ("-", None),
        (None, None),
        ("", None),
    ],
)
def test_parse_rating(raw: str | None, expected: float | None) -> None:
    assert parse_rating(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("800", 800.0),
        ("1,200", 1200.0),
        ("300-400", 350.0),
        ("-", None),
        (None, None),
    ],
)
def test_parse_cost(raw: str | None, expected: float | None) -> None:
    assert parse_cost(raw) == expected


def test_parse_cuisines_comma_separated() -> None:
    assert parse_cuisines("Italian, Chinese, Cafe") == ["Italian", "Chinese", "Cafe"]


def test_parse_cuisines_empty() -> None:
    assert parse_cuisines("") == []
    assert parse_cuisines(None) == []


def test_normalize_city_aliases() -> None:
    assert normalize_city("bengaluru") == "Bangalore"
    assert normalize_city("  delhi ncr  ") == "Delhi"


@pytest.mark.parametrize(
    ("cost", "expected"),
    [
        (400.0, "low"),
        (800.0, "medium"),
        (2000.0, "high"),
        (None, "unknown"),
    ],
)
def test_assign_budget_band(cost: float | None, expected: str) -> None:
    bands = Settings().budget_bands
    assert assign_budget_band(cost, bands) == expected


def test_preprocess_row_builds_restaurant(sample_raw_row: dict, settings: Settings) -> None:
    restaurant = preprocess_row(sample_raw_row, 0, settings)
    assert restaurant is not None
    assert restaurant.name == "Jalsa"
    assert restaurant.location == "Bangalore"
    assert restaurant.rating == 4.1
    assert restaurant.estimated_cost == 800.0
    assert restaurant.budget_band == "medium"
    assert "North Indian" in restaurant.cuisines
    assert restaurant.id.startswith("r_")


def test_preprocess_row_skips_missing_name(sample_raw_row: dict, settings: Settings) -> None:
    row = {**sample_raw_row, "name": "  "}
    assert preprocess_row(row, 0, settings) is None


def test_preprocess_row_null_rating_and_cost(settings: Settings) -> None:
    row = {
        "name": "Test Cafe",
        "listed_in(city)": "Bangalore",
        "rate": "NEW",
        "approx_cost(for two people)": "-",
        "cuisines": "Cafe",
        "url": "https://example.com/test",
    }
    restaurant = preprocess_row(row, 0, settings)
    assert restaurant is not None
    assert restaurant.rating is None
    assert restaurant.estimated_cost is None
    assert restaurant.budget_band == "unknown"


def test_preprocess_rows_count(sample_raw_rows: list[dict], settings: Settings) -> None:
    restaurants = preprocess_rows(sample_raw_rows, settings)
    assert len(restaurants) == 3


def test_preprocess_rows_dedupes_same_url(settings: Settings) -> None:
    rows = [
        {
            "url": "https://www.zomato.com/bangalore/dup",
            "name": "Dup Place",
            "listed_in(city)": "Bangalore",
            "location": "Indiranagar",
            "rate": "3.9/5",
            "votes": 10,
            "cuisines": "Cafe",
            "approx_cost(for two people)": "500",
        },
        {
            # Same URL -> same stable ID -> should be merged/deduped
            "url": "https://www.zomato.com/bangalore/dup",
            "name": "Dup Place",
            "listed_in(city)": "Bangalore",
            "location": "Indiranagar",
            "rate": "4.4/5",
            "votes": 250,
            "cuisines": "Cafe, Desserts",
            "approx_cost(for two people)": "600",
        },
    ]

    restaurants = preprocess_rows(rows, settings)
    assert len(restaurants) == 1
    assert restaurants[0].rating == 4.4
    assert "Desserts" in restaurants[0].cuisines
