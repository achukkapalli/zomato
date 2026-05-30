"""Phase 5: pipeline runner unit tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from config.settings import Settings
from src.app.pipeline import run_recommendation
from src.models.preferences import UserPreferences
from src.models.recommendation import RecommendationResult


@pytest.fixture
def preferences() -> UserPreferences:
    return UserPreferences(
        location="Bangalore",
        budget="medium",
        cuisine="Italian",
    )


@patch("src.app.pipeline.RecommendationOrchestrator", autospec=True)
def test_run_recommendation_calls_orchestrator(
    mock_orchestrator_class: MagicMock,
    preferences: UserPreferences,
) -> None:
    # Setup mock instance
    mock_orchestrator = mock_orchestrator_class.return_value
    mock_result = MagicMock(spec=RecommendationResult)
    mock_orchestrator.recommend.return_value = mock_result

    # Setup repository and settings mocks
    mock_repo = MagicMock()
    mock_llm = MagicMock()
    settings = Settings()

    # Call target
    result = run_recommendation(
        preferences,
        settings=settings,
        repository=mock_repo,
        llm_service=mock_llm,
    )

    # Asserts
    assert result is mock_result
    mock_orchestrator_class.assert_called_once_with(
        settings=settings,
        repository=mock_repo,
        llm_service=mock_llm,
    )
    mock_orchestrator.recommend.assert_called_once_with(preferences)
