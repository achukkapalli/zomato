"""Recommendation orchestrator (Phase 4)."""

from __future__ import annotations

import logging
import time

from config.settings import Settings, get_settings
from src.data.repository import RestaurantRepository, get_repository
from src.models.preferences import UserPreferences
from src.models.recommendation import (
    EmptyFilterResult,
    RecommendationItem,
    RecommendationResult,
)
from src.services import filter_service
from src.services.llm_service import LLMNotConfiguredError, LLMService, fallback_ranking

logger = logging.getLogger(__name__)


class RecommendationOrchestrator:
    """
    Coordinates data loading, deterministic filtering, and LLM ranking.
    """

    def __init__(
        self,
        settings: Settings | None = None,
        repository: RestaurantRepository | None = None,
        llm_service: LLMService | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.repository = repository or get_repository(settings=self.settings)
        self.llm_service = llm_service or LLMService(settings=self.settings)

    def recommend(
        self,
        preferences: UserPreferences,
    ) -> RecommendationResult | EmptyFilterResult:
        """
        Executes end-to-end recommendation flow:
        1. Ensure dataset is loaded.
        2. Apply deterministic filters.
        3. If no matches, return EmptyFilterResult.
        4. If matches exist, call LLM to rank and explain.
        5. Merge LLM output with canonical repository data.
        """
        # Ensure data is loaded
        self.repository.ensure_loaded()

        # Apply deterministic filters
        filter_start = time.perf_counter()
        filter_res = filter_service.apply(
            preferences, self.repository, settings=self.settings
        )
        filter_duration = time.perf_counter() - filter_start

        logger.info(
            "Filter completed in %.3f seconds. Candidates remaining: %d/%d",
            filter_duration,
            len(filter_res.restaurants),
            filter_res.matched_count_before_cap,
        )

        # Handle empty filter state
        if filter_res.is_empty:
            return EmptyFilterResult(
                reason_code=filter_res.reason_code.value,
                message=filter_res.message,
                suggestions=filter_res.suggestions,
            )

        # LLM ranking and explanation
        llm_start = time.perf_counter()
        try:
            llm_res = self.llm_service.rank_and_explain(preferences, filter_res.restaurants)
        except LLMNotConfiguredError:
            # Phase 5 UX requirement: app should still work without secrets configured.
            logger.info("LLM not configured; using deterministic fallback ranking")
            llm_res = fallback_ranking(
                preferences,
                filter_res.restaurants,
                top_k=self.settings.top_k,
            )
        llm_duration = time.perf_counter() - llm_start

        logger.info(
            "LLM rank_and_explain completed in %.3f seconds. Fallback used: %s",
            llm_duration,
            llm_res.used_fallback,
        )

        # Merge ranked list with canonical restaurant data from filter_res
        items = []
        for entry in llm_res.recommendations:
            # Match LLM-ranked IDs with canonical records from candidate list
            restaurant = next((r for r in filter_res.restaurants if r.id == entry.restaurant_id), None)
            if restaurant is None:
                # Grounding check: skip hallucinated/out-of-shortlist IDs
                logger.warning(
                    "LLM returned restaurant_id '%s' which is not in candidate shortlist. Skipping.",
                    entry.restaurant_id,
                )
                continue
            items.append(
                RecommendationItem(
                    rank=entry.rank,
                    restaurant=restaurant,
                    explanation=entry.explanation,
                )
            )

        return RecommendationResult(
            summary=llm_res.summary,
            items=items,
            used_fallback=llm_res.used_fallback,
        )
