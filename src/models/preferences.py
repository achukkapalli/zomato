"""User preference input model (Phase 2)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

UserBudget = Literal["low", "medium", "high"]


class UserPreferences(BaseModel):
    """Validated user inputs for the recommendation pipeline."""

    location: str = Field(..., min_length=1, description="City name, e.g. Bangalore or Delhi")
    budget: UserBudget
    cuisine: str | None = None
    min_rating: float | None = Field(default=None, ge=0.0, le=5.0)
    additional_preferences: str | None = Field(default=None, max_length=500)

    model_config = {"str_strip_whitespace": True}

    @field_validator("location")
    @classmethod
    def normalize_location(cls, value: str) -> str:
        from src.data.preprocessor import normalize_city

        normalized = normalize_city(value)
        if not normalized:
            raise ValueError("location must not be empty")
        return normalized

    @field_validator("cuisine")
    @classmethod
    def normalize_cuisine(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned if cleaned else None

    @field_validator("additional_preferences")
    @classmethod
    def normalize_additional(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned if cleaned else None

    def effective_min_rating(self, default: float = 3.0) -> float:
        """Minimum rating threshold, using application default when omitted."""
        return self.min_rating if self.min_rating is not None else default
