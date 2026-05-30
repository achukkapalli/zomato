"""Pytest fixtures for Zomoto."""

from __future__ import annotations

import pytest

from config.settings import Settings, get_settings
from src.data.repository import RestaurantRepository
from src.models.restaurant import Restaurant


@pytest.fixture
def settings() -> Settings:
    """Fresh settings instance (bypasses cache) with snapshot path disabled for unit tests."""
    return Settings(data_snapshot_path=None)


@pytest.fixture(autouse=True)
def clear_settings_cache() -> None:
    """Isolate tests that mutate cached settings."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def sample_raw_row() -> dict:
    """Single raw row matching the Zomato HF schema."""
    return {
        "url": "https://www.zomato.com/bangalore/jalsa-banashankari",
        "address": "942, 21st Main Road, Bangalore",
        "name": "Jalsa",
        "online_order": "Yes",
        "book_table": "Yes",
        "rate": "4.1/5",
        "votes": 812,
        "phone": "08012345678",
        "location": "Banashankari",
        "rest_type": "Casual Dining",
        "dish_liked": "Paneer, Biryani",
        "cuisines": "North Indian, Mughlai",
        "approx_cost(for two people)": "800",
        "reviews_list": "[]",
        "menu_item": "[]",
        "listed_in(type)": "Buffet",
        "listed_in(city)": "Bangalore",
    }


@pytest.fixture
def sample_raw_rows(sample_raw_row: dict) -> list[dict]:
    """Multiple raw rows for repository tests."""
    row_delhi = {
        **sample_raw_row,
        "url": "https://www.zomato.com/delhi/spice-delhi",
        "name": "Spice Route",
        "rate": "4.5/5",
        "cuisines": "Italian, Continental",
        "approx_cost(for two people)": "400",
        "listed_in(city)": "Delhi",
        "location": "Connaught Place",
    }
    row_new = {
        **sample_raw_row,
        "url": "https://www.zomato.com/bangalore/new-place",
        "name": "New Place",
        "rate": "NEW",
        "approx_cost(for two people)": "-",
        "cuisines": "",
    }
    row_no_name = {**sample_raw_row, "name": "", "url": "https://example.com/noname"}
    return [sample_raw_row, row_delhi, row_new, row_no_name]


@pytest.fixture
def mock_raw_loader(sample_raw_rows: list[dict]):
    """Return a loader callable that avoids Hugging Face downloads."""

    def _load(_settings: Settings) -> list[dict]:
        return sample_raw_rows

    return _load


@pytest.fixture
def filter_restaurants() -> list[Restaurant]:
    """Curated restaurants for Phase 2 filter tests."""
    return [
        Restaurant(
            id="r_blr_italian_medium",
            name="Trattoria Roma",
            location="Bangalore",
            cuisines=["Italian", "Continental"],
            rating=4.5,
            estimated_cost=800.0,
            budget_band="medium",
            metadata={"votes": 500},
        ),
        Restaurant(
            id="r_blr_italian_low",
            name="Pizza Corner",
            location="Bangalore",
            cuisines=["Italian"],
            rating=4.2,
            estimated_cost=400.0,
            budget_band="low",
            metadata={"votes": 200},
        ),
        Restaurant(
            id="r_blr_chinese_medium",
            name="Golden Dragon",
            location="Bangalore",
            cuisines=["Chinese"],
            rating=4.6,
            estimated_cost=900.0,
            budget_band="medium",
            metadata={"votes": 800},
        ),
        Restaurant(
            id="r_blr_italian_high",
            name="Fine Dine Italia",
            location="Bangalore",
            cuisines=["Italian"],
            rating=3.8,
            estimated_cost=2000.0,
            budget_band="high",
            metadata={"votes": 100},
        ),
        Restaurant(
            id="r_delhi_italian_medium",
            name="Delhi Italian",
            location="Delhi",
            cuisines=["Italian"],
            rating=4.8,
            estimated_cost=700.0,
            budget_band="medium",
            metadata={"votes": 600},
        ),
        Restaurant(
            id="r_blr_unknown",
            name="Mystery Cafe",
            location="Bangalore",
            cuisines=["Cafe"],
            rating=4.0,
            estimated_cost=None,
            budget_band="unknown",
            metadata={"votes": 50},
        ),
        Restaurant(
            id="r_blr_unrated",
            name="No Stars Diner",
            location="Bangalore",
            cuisines=["Cafe"],
            rating=None,
            estimated_cost=600.0,
            budget_band="medium",
            metadata={"votes": 10},
        ),
    ]


class _StaticRestaurantRepository:
    """In-memory repository backed by a fixed restaurant list (tests only)."""

    def __init__(self, restaurants: list[Restaurant]) -> None:
        self._restaurants = restaurants
        self._loaded = True

    def ensure_loaded(self) -> None:
        return None

    def get_all(self) -> list[Restaurant]:
        return list(self._restaurants)

    def get_locations(self) -> list[str]:
        cities = {r.location for r in self._restaurants if r.location}
        return sorted(cities, key=str.casefold)

    def get_cuisines(self) -> list[str]:
        tags: set[str] = set()
        for r in self._restaurants:
            tags.update(r.cuisines)
        return sorted(tags, key=str.casefold)


@pytest.fixture
def filter_repository(filter_restaurants: list[Restaurant]) -> _StaticRestaurantRepository:
    return _StaticRestaurantRepository(filter_restaurants)


@pytest.fixture
def filter_repository_with_many(filter_restaurants: list[Restaurant]) -> _StaticRestaurantRepository:
    """Repository with duplicates for cap / tie-break tests."""
    extras = [
        Restaurant(
            id=f"r_extra_{i}",
            name=f"Extra Italian {i}",
            location="Bangalore",
            cuisines=["Italian"],
            rating=4.5,
            estimated_cost=800.0,
            budget_band="medium",
            metadata={"votes": 1000 - i},
        )
        for i in range(40)
    ]
    return _StaticRestaurantRepository(filter_restaurants + extras)
