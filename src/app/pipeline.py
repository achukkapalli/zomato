"""Phase 5 helper: run the recommendation pipeline without Streamlit dependencies.

This module exists to keep Phase 5 deliverables testable (unit tests can import this
without initializing Streamlit).
"""

from __future__ import annotations

from config.settings import Settings, get_settings
from src.data.repository import RestaurantRepository, get_repository
from src.models.preferences import UserPreferences
from src.models.recommendation import EmptyFilterResult, RecommendationResult
from src.orchestration.recommender import RecommendationOrchestrator
from src.services.llm_service import LLMService


def run_recommendation(
    preferences: UserPreferences,
    *,
    settings: Settings | None = None,
    repository: RestaurantRepository | None = None,
    llm_service: LLMService | None = None,
) -> RecommendationResult | EmptyFilterResult:
    """Run the end-to-end pipeline and return a typed result."""
    cfg = settings or get_settings()
    repo = repository or get_repository(settings=cfg)
    orchestrator = RecommendationOrchestrator(
        settings=cfg,
        repository=repo,
        llm_service=llm_service,
    )
    return orchestrator.recommend(preferences)

