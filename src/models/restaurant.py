"""Restaurant domain model (Phase 1)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

BudgetBand = Literal["low", "medium", "high", "unknown"]


class Restaurant(BaseModel):
    """Normalized restaurant record used across filter, LLM, and UI layers."""

    id: str
    name: str
    location: str
    cuisines: list[str] = Field(default_factory=list)
    rating: float | None = None
    estimated_cost: float | None = None
    budget_band: BudgetBand = "unknown"
    locality: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": True}

    @property
    def display_cost(self) -> str:
        if self.estimated_cost is None:
            return "Cost not available"
        return f"₹{int(self.estimated_cost)} for two"
