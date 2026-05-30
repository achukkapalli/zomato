"""Deterministic restaurant filter pipeline (Phase 2)."""

from __future__ import annotations

import logging
from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from config.settings import Settings, get_settings
from src.models.preferences import UserPreferences
from src.models.restaurant import BudgetBand, Restaurant

if TYPE_CHECKING:
    from src.data.repository import RestaurantRepository

logger = logging.getLogger(__name__)


class FilterReasonCode(str, Enum):
    """Why the filter pipeline returned no candidates."""

    SUCCESS = "SUCCESS"
    REPOSITORY_EMPTY = "REPOSITORY_EMPTY"
    NO_LOCATION_MATCH = "NO_LOCATION_MATCH"
    NO_CUISINE_MATCH = "NO_CUISINE_MATCH"
    NO_RATING_MATCH = "NO_RATING_MATCH"
    NO_BUDGET_MATCH = "NO_BUDGET_MATCH"
    NO_MATCH_AFTER_ALL_FILTERS = "NO_MATCH_AFTER_ALL_FILTERS"


REASON_MESSAGES: dict[FilterReasonCode, str] = {
    FilterReasonCode.REPOSITORY_EMPTY: "Restaurant data is not available.",
    FilterReasonCode.NO_LOCATION_MATCH: "No restaurants found in the selected city.",
    FilterReasonCode.NO_CUISINE_MATCH: "No restaurants match the selected cuisine in this city.",
    FilterReasonCode.NO_RATING_MATCH: "No restaurants meet the minimum rating in this city.",
    FilterReasonCode.NO_BUDGET_MATCH: "No restaurants match the selected budget in this city.",
    FilterReasonCode.NO_MATCH_AFTER_ALL_FILTERS: "No restaurants match all of your filters.",
}

SUGGESTIONS: dict[FilterReasonCode, list[str]] = {
    FilterReasonCode.NO_LOCATION_MATCH: [
        "Pick a city from the dropdown and check spelling (e.g. Bangalore vs Bengaluru).",
    ],
    FilterReasonCode.NO_CUISINE_MATCH: [
        "Clear the cuisine filter or try a broader type (e.g. North Indian).",
    ],
    FilterReasonCode.NO_RATING_MATCH: [
        "Lower the minimum rating (e.g. 3.5 instead of 4.5).",
    ],
    FilterReasonCode.NO_BUDGET_MATCH: [
        "Try medium or high budget if you selected low, or vice versa.",
    ],
    FilterReasonCode.NO_MATCH_AFTER_ALL_FILTERS: [
        "Relax two filters: lower the rating and remove or broaden cuisine.",
        "Try a different budget band for this city.",
    ],
}


class FilterResult(BaseModel):
    """Outcome of the filter pipeline."""

    restaurants: list[Restaurant] = Field(default_factory=list)
    reason_code: FilterReasonCode = FilterReasonCode.SUCCESS
    message: str = ""
    suggestions: list[str] = Field(default_factory=list)
    matched_count_before_cap: int = 0

    @property
    def is_empty(self) -> bool:
        return not self.restaurants

    @property
    def ok(self) -> bool:
        return self.reason_code == FilterReasonCode.SUCCESS and bool(self.restaurants)


def _votes_key(restaurant: Restaurant) -> int:
    raw = restaurant.metadata.get("votes")
    try:
        return int(raw) if raw is not None else 0
    except (TypeError, ValueError):
        return 0


def _sort_key(restaurant: Restaurant) -> tuple[float, int, str]:
    """Rating desc, then votes desc, then name (edge cases F-09, F-10, F-11)."""
    rating = restaurant.rating if restaurant.rating is not None else -1.0
    return (-rating, -_votes_key(restaurant), restaurant.name.casefold())


def filter_by_location(restaurants: list[Restaurant], location: str) -> list[Restaurant]:
    needle = location.casefold()
    return [r for r in restaurants if r.location.casefold() == needle]


def filter_by_cuisine(restaurants: list[Restaurant], cuisine: str) -> list[Restaurant]:
    needle = cuisine.casefold()
    matched: list[Restaurant] = []
    for restaurant in restaurants:
        if any(needle in tag.casefold() for tag in restaurant.cuisines):
            matched.append(restaurant)
            continue
        combined = ", ".join(restaurant.cuisines).casefold()
        if needle in combined:
            matched.append(restaurant)
    return matched


def filter_by_rating(restaurants: list[Restaurant], min_rating: float) -> list[Restaurant]:
    """Exclude rows without a rating or below threshold (edge case F-11)."""
    return [
        r
        for r in restaurants
        if r.rating is not None and r.rating >= min_rating
    ]


def filter_by_budget(restaurants: list[Restaurant], budget: BudgetBand) -> list[Restaurant]:
    """
    Match exact budget band. Rows with ``unknown`` band are excluded (edge case F-13).
    """
    return [r for r in restaurants if r.budget_band == budget]


def cap_candidates(restaurants: list[Restaurant], max_candidates: int) -> list[Restaurant]:
    sorted_rows = sorted(restaurants, key=_sort_key)
    return sorted_rows[:max_candidates]


def dedupe_candidates(restaurants: list[Restaurant]) -> list[Restaurant]:
    """
    Remove obvious duplicate entries that would lead to repeated UI/API results.

    We consider a "duplicate" as same (name, city, locality) after normalization.
    When duplicates exist, keep the best one by the same ranking criteria used for
    capping (rating desc, votes desc).
    """
    best_by_key: dict[tuple[str, str, str], Restaurant] = {}
    for r in restaurants:
        key = (
            r.name.strip().casefold(),
            r.location.strip().casefold(),
            (r.locality or "").strip().casefold(),
        )
        current_best = best_by_key.get(key)
        if current_best is None:
            best_by_key[key] = r
            continue
        # _sort_key is "best first" when sorted ascending.
        if _sort_key(r) < _sort_key(current_best):
            best_by_key[key] = r
    return list(best_by_key.values())


def build_filter_result(
    restaurants: list[Restaurant],
    reason: FilterReasonCode,
    *,
    matched_before_cap: int | None = None,
) -> FilterResult:
    if reason == FilterReasonCode.SUCCESS:
        return FilterResult(
            restaurants=restaurants,
            reason_code=reason,
            message="",
            suggestions=[],
            matched_count_before_cap=matched_before_cap or len(restaurants),
        )
    return FilterResult(
        restaurants=[],
        reason_code=reason,
        message=REASON_MESSAGES.get(reason, "No matches found."),
        suggestions=list(SUGGESTIONS.get(reason, [])),
        matched_count_before_cap=0,
    )


def apply(
    preferences: UserPreferences,
    repository: RestaurantRepository,
    settings: Settings | None = None,
) -> FilterResult:
    """
    Run the ordered filter pipeline: location → cuisine → rating → budget → cap.

    Returns restaurants ready for the LLM, or an empty result with reason codes.
    """
    cfg = settings or get_settings()
    repository.ensure_loaded()

    all_restaurants = repository.get_all()
    if not all_restaurants:
        return build_filter_result([], FilterReasonCode.REPOSITORY_EMPTY)

    known_locations = {city.casefold() for city in repository.get_locations()}
    if preferences.location.casefold() not in known_locations:
        return build_filter_result([], FilterReasonCode.NO_LOCATION_MATCH)

    current = filter_by_location(all_restaurants, preferences.location)
    if not current:
        return build_filter_result([], FilterReasonCode.NO_LOCATION_MATCH)

    if preferences.cuisine:
        after_cuisine = filter_by_cuisine(current, preferences.cuisine)
        if not after_cuisine:
            return build_filter_result([], FilterReasonCode.NO_CUISINE_MATCH)
        current = after_cuisine

    min_rating = preferences.effective_min_rating(cfg.default_min_rating)
    after_rating = filter_by_rating(current, min_rating)
    if not after_rating:
        return build_filter_result([], FilterReasonCode.NO_RATING_MATCH)
    current = after_rating

    after_budget = filter_by_budget(current, preferences.budget)
    if not after_budget:
        return build_filter_result([], FilterReasonCode.NO_BUDGET_MATCH)
    current = dedupe_candidates(after_budget)

    matched_before_cap = len(current)
    capped = cap_candidates(current, cfg.max_candidates)

    logger.debug(
        "Filter %s/%s/%s min_rating=%s -> %s candidates (capped from %s)",
        preferences.location,
        preferences.budget,
        preferences.cuisine,
        min_rating,
        len(capped),
        matched_before_cap,
    )

    return build_filter_result(
        capped,
        FilterReasonCode.SUCCESS,
        matched_before_cap=matched_before_cap,
    )
