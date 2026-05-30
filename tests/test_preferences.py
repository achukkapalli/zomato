"""Phase 2: UserPreferences validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.models.preferences import UserPreferences


def test_required_location_and_budget() -> None:
    prefs = UserPreferences(location="Bangalore", budget="medium")
    assert prefs.location == "Bangalore"
    assert prefs.budget == "medium"
    assert prefs.cuisine is None
    assert prefs.effective_min_rating() == 3.0


def test_location_normalized_bengaluru() -> None:
    prefs = UserPreferences(location="bengaluru", budget="low")
    assert prefs.location == "Bangalore"


def test_empty_location_rejected() -> None:
    with pytest.raises(ValidationError):
        UserPreferences(location="   ", budget="medium")


def test_invalid_budget_rejected() -> None:
    with pytest.raises(ValidationError):
        UserPreferences(location="Delhi", budget="cheap")  # type: ignore[arg-type]


def test_min_rating_bounds() -> None:
    with pytest.raises(ValidationError):
        UserPreferences(location="Delhi", budget="low", min_rating=6.0)


def test_whitespace_cuisine_becomes_none() -> None:
    prefs = UserPreferences(location="Delhi", budget="low", cuisine="   ")
    assert prefs.cuisine is None


def test_additional_preferences_max_length() -> None:
    with pytest.raises(ValidationError):
        UserPreferences(
            location="Delhi",
            budget="low",
            additional_preferences="x" * 501,
        )
