"""Phase 4: Orchestrator integration tests."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from config.settings import Settings
from src.models.preferences import UserPreferences
from src.models.recommendation import EmptyFilterResult, RecommendationResult
from src.orchestration.recommender import RecommendationOrchestrator
from src.services.llm_service import (
    LLMRecommendationEntry,
    LLMService,
    RankAndExplainResult,
)


@pytest.fixture
def preferences() -> UserPreferences:
    return UserPreferences(
        location="Bangalore",
        budget="medium",
        cuisine="Italian",
        min_rating=4.0,
        additional_preferences="family-friendly",
    )


@pytest.fixture
def mock_llm_service() -> MagicMock:
    service = MagicMock(spec=LLMService)
    # Default mock return
    service.rank_and_explain.return_value = RankAndExplainResult(
        summary="Top Italian picks.",
        recommendations=[
            LLMRecommendationEntry(
                restaurant_id="r_blr_italian_medium",
                rank=1,
                explanation="Authentic pasta.",
            )
        ],
        used_fallback=False,
    )
    return service


def test_orchestrator_successful_merge(
    preferences: UserPreferences,
    filter_repository,
    mock_llm_service: MagicMock,
) -> None:
    settings = Settings(max_candidates=5)
    orchestrator = RecommendationOrchestrator(
        settings=settings,
        repository=filter_repository,
        llm_service=mock_llm_service,
    )

    result = orchestrator.recommend(preferences)

    assert isinstance(result, RecommendationResult)
    assert not result.used_fallback
    assert result.summary == "Top Italian picks."
    assert len(result.items) == 1

    item = result.items[0]
    assert item.rank == 1
    assert item.restaurant.id == "r_blr_italian_medium"
    assert item.restaurant.name == "Trattoria Roma"
    assert item.explanation == "Authentic pasta."

    mock_llm_service.rank_and_explain.assert_called_once()


def test_orchestrator_empty_filter_results(
    mock_llm_service: MagicMock,
) -> None:
    # Query location Tokyo which does not exist in mock filter repository
    prefs = UserPreferences(location="Tokyo", budget="medium")
    from tests.conftest import _StaticRestaurantRepository
    empty_repo = _StaticRestaurantRepository([])

    orchestrator = RecommendationOrchestrator(
        repository=empty_repo,
        llm_service=mock_llm_service,
    )

    result = orchestrator.recommend(prefs)

    assert isinstance(result, EmptyFilterResult)
    assert result.reason_code == "REPOSITORY_EMPTY"
    assert "not available" in result.message.lower()
    mock_llm_service.rank_and_explain.assert_not_called()


def test_orchestrator_grounding_strips_unknown_ids(
    preferences: UserPreferences,
    filter_repository,
    mock_llm_service: MagicMock,
) -> None:
    # LLM returns one valid ID and one hallucinated ID
    mock_llm_service.rank_and_explain.return_value = RankAndExplainResult(
        summary="Mixed picks.",
        recommendations=[
            LLMRecommendationEntry(
                restaurant_id="r_blr_italian_medium",
                rank=1,
                explanation="Valid.",
            ),
            LLMRecommendationEntry(
                restaurant_id="r_hallucinated",
                rank=2,
                explanation="Hallucinated.",
            ),
        ],
        used_fallback=False,
    )

    orchestrator = RecommendationOrchestrator(
        repository=filter_repository,
        llm_service=mock_llm_service,
    )

    result = orchestrator.recommend(preferences)

    assert isinstance(result, RecommendationResult)
    assert len(result.items) == 1
    assert result.items[0].restaurant.id == "r_blr_italian_medium"


def test_orchestrator_llm_fallback_used(
    preferences: UserPreferences,
    filter_repository,
    mock_llm_service: MagicMock,
) -> None:
    # Mock LLM service using fallback
    mock_llm_service.rank_and_explain.return_value = RankAndExplainResult(
        summary="Fallback ranking.",
        recommendations=[
            LLMRecommendationEntry(
                restaurant_id="r_blr_italian_medium",
                rank=1,
                explanation="Fallback description.",
            )
        ],
        used_fallback=True,
    )

    orchestrator = RecommendationOrchestrator(
        repository=filter_repository,
        llm_service=mock_llm_service,
    )

    result = orchestrator.recommend(preferences)

    assert isinstance(result, RecommendationResult)
    assert result.used_fallback
    assert len(result.items) == 1
    assert result.items[0].restaurant.id == "r_blr_italian_medium"


def test_orchestrator_falls_back_when_llm_not_configured(
    preferences: UserPreferences,
    filter_repository,
) -> None:
    """
    Phase 5 UX requirement: app should be runnable even without GROQ_API_KEY set.
    The orchestrator must not raise; it should return deterministic fallback picks.
    """
    settings = Settings(llm_api_key=None, top_k=3, max_candidates=5)
    orchestrator = RecommendationOrchestrator(
        settings=settings,
        repository=filter_repository,
    )

    result = orchestrator.recommend(preferences)

    assert isinstance(result, RecommendationResult)
    assert result.used_fallback
    assert result.items
