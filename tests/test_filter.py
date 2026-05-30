"""Phase 2: filter service unit tests."""

from __future__ import annotations

import time

import pytest

from config.settings import Settings
from src.data.repository import RestaurantRepository
from src.models.preferences import UserPreferences
from src.models.restaurant import Restaurant
from src.services.filter_service import (
    FilterReasonCode,
    apply,
    cap_candidates,
    filter_by_budget,
    filter_by_cuisine,
    filter_by_location,
    filter_by_rating,
)


def test_filter_by_location_case_insensitive(filter_restaurants: list[Restaurant]) -> None:
    matches = filter_by_location(filter_restaurants, "bangalore")
    assert len(matches) == 6
    assert all(r.location == "Bangalore" for r in matches)


def test_filter_by_cuisine_partial_and_multi_tag(filter_restaurants: list[Restaurant]) -> None:
    bangalore = filter_by_location(filter_restaurants, "Bangalore")
    italian = filter_by_cuisine(bangalore, "ital")
    names = {r.name for r in italian}
    assert "Trattoria Roma" in names
    assert "Pizza Corner" in names
    assert "Golden Dragon" not in names


def test_filter_by_cuisine_skipped_when_none(filter_repository) -> None:
    prefs = UserPreferences(location="Bangalore", budget="medium")
    result = apply(prefs, filter_repository)
    assert result.ok
    assert len(result.restaurants) >= 2


def test_filter_by_rating_excludes_null_rating(filter_restaurants: list[Restaurant]) -> None:
    bangalore = filter_by_location(filter_restaurants, "Bangalore")
    rated = filter_by_rating(bangalore, 3.5)
    assert all(r.rating is not None and r.rating >= 3.5 for r in rated)
    assert not any(r.name == "No Stars Diner" for r in rated)


def test_filter_by_budget_excludes_unknown_band(filter_restaurants: list[Restaurant]) -> None:
    bangalore = filter_by_location(filter_restaurants, "Bangalore")
    low = filter_by_budget(bangalore, "low")
    assert all(r.budget_band == "low" for r in low)
    assert not any(r.budget_band == "unknown" for r in low)


def test_cap_candidates_limits_and_sorts_by_rating(
    filter_repository_with_many,
    settings: Settings,
) -> None:
    prefs = UserPreferences(location="Bangalore", budget="medium", cuisine="Italian")
    result = apply(prefs, filter_repository_with_many, settings=Settings(max_candidates=5))
    assert result.ok
    assert len(result.restaurants) == 5
    ratings = [r.rating for r in result.restaurants]
    assert ratings == sorted(ratings, reverse=True)


def test_cap_tie_break_by_votes() -> None:
    rows = [
        Restaurant(
            id="a",
            name="A",
            location="X",
            cuisines=[],
            rating=4.5,
            budget_band="medium",
            metadata={"votes": 10},
        ),
        Restaurant(
            id="b",
            name="B",
            location="X",
            cuisines=[],
            rating=4.5,
            budget_band="medium",
            metadata={"votes": 100},
        ),
    ]
    capped = cap_candidates(rows, 1)
    assert capped[0].id == "b"


def test_apply_acceptance_bangalore_medium_italian_min_4(
    filter_repository,
) -> None:
    """Implementation plan acceptance: Bangalore + medium + Italian + min 4.0."""
    prefs = UserPreferences(
        location="Bangalore",
        budget="medium",
        cuisine="Italian",
        min_rating=4.0,
    )
    result = apply(prefs, filter_repository)
    assert result.ok
    assert len(result.restaurants) == 1
    assert result.restaurants[0].name == "Trattoria Roma"
    assert result.restaurants[0].budget_band == "medium"
    assert "Italian" in result.restaurants[0].cuisines


def test_no_location_match(filter_repository) -> None:
    prefs = UserPreferences(location="Tokyo", budget="medium")
    result = apply(prefs, filter_repository)
    assert result.is_empty
    assert result.reason_code == FilterReasonCode.NO_LOCATION_MATCH
    assert result.suggestions


def test_no_cuisine_match(filter_repository) -> None:
    prefs = UserPreferences(location="Bangalore", budget="medium", cuisine="Mexican")
    result = apply(prefs, filter_repository)
    assert result.reason_code == FilterReasonCode.NO_CUISINE_MATCH


def test_no_rating_match(filter_repository) -> None:
    prefs = UserPreferences(
        location="Bangalore",
        budget="medium",
        cuisine="Italian",
        min_rating=5.0,
    )
    result = apply(prefs, filter_repository)
    assert result.reason_code == FilterReasonCode.NO_RATING_MATCH


def test_no_budget_match(filter_repository) -> None:
    prefs = UserPreferences(
        location="Bangalore",
        budget="low",
        cuisine="Chinese",
        min_rating=4.0,
    )
    result = apply(prefs, filter_repository)
    assert result.reason_code == FilterReasonCode.NO_BUDGET_MATCH


def test_apply_with_mock_repository_integration(
    mock_raw_loader,
    settings: Settings,
) -> None:
    repo = RestaurantRepository(settings=settings, raw_loader=mock_raw_loader)
    prefs = UserPreferences(location="Delhi", budget="low", cuisine="Italian")
    result = apply(prefs, repo, settings=settings)
    assert result.ok
    assert len(result.restaurants) == 1
    assert result.restaurants[0].name == "Spice Route"


def test_filter_performance_under_50ms(
    filter_repository_with_many,
    settings: Settings,
) -> None:
    prefs = UserPreferences(location="Bangalore", budget="medium", cuisine="Italian")
    start = time.perf_counter()
    for _ in range(100):
        apply(prefs, filter_repository_with_many, settings=settings)
    elapsed_ms = (time.perf_counter() - start) * 1000 / 100
    assert elapsed_ms < 50, f"avg filter took {elapsed_ms:.2f}ms"
