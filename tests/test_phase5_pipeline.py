"""Phase 5: testable pipeline helper (no Streamlit required)."""

from __future__ import annotations

from unittest.mock import MagicMock

from config.settings import Settings
from src.app.pipeline import run_recommendation
from src.models.preferences import UserPreferences
from src.models.recommendation import EmptyFilterResult, RecommendationResult
from src.services.llm_service import LLMRecommendationEntry, RankAndExplainResult


def test_pipeline_helper_runs_with_mock_llm(filter_repository) -> None:
    prefs = UserPreferences(
        location="Bangalore",
        budget="medium",
        cuisine="Italian",
        min_rating=4.0,
        additional_preferences="family-friendly",
    )

    mock_llm = MagicMock()
    mock_llm.rank_and_explain.return_value = RankAndExplainResult(
        summary="Top picks.",
        recommendations=[
            LLMRecommendationEntry(
                restaurant_id="r_blr_italian_medium",
                rank=1,
                explanation="Great for families.",
            )
        ],
        used_fallback=False,
    )

    result = run_recommendation(
        prefs,
        settings=Settings(max_candidates=5, top_k=3),
        repository=filter_repository,  # in-memory fixture
        llm_service=mock_llm,
    )

    assert isinstance(result, RecommendationResult)
    assert result.items[0].restaurant.name == "Trattoria Roma"


def test_pipeline_helper_returns_empty_result(filter_repository) -> None:
    prefs = UserPreferences(location="Tokyo", budget="medium")
    result = run_recommendation(prefs, repository=filter_repository)
    assert isinstance(result, EmptyFilterResult)

