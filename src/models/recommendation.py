"""Recommendation result models (Phase 2+)."""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.models.restaurant import Restaurant


class RecommendationItem(BaseModel):
    """One ranked recommendation with LLM explanation (Phase 4+)."""

    rank: int = Field(..., ge=1)
    restaurant: Restaurant
    explanation: str = ""


class RecommendationResult(BaseModel):
    """Successful recommendation response."""

    summary: str | None = None
    items: list[RecommendationItem] = Field(default_factory=list)
    used_fallback: bool = False


class EmptyFilterResult(BaseModel):
    """Returned when the filter pipeline yields no candidates."""

    reason_code: str
    message: str
    suggestions: list[str] = Field(default_factory=list)
