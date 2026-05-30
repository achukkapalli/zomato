"""Optional live Groq integration test."""

from __future__ import annotations

import os

import pytest

from config.settings import Settings
from src.models.preferences import UserPreferences
from src.services.llm_service import LLMService

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_GROQ_INTEGRATION") != "1",
    reason="Set RUN_GROQ_INTEGRATION=1 and GROQ_API_KEY to run live Groq tests",
)


@pytest.fixture
def live_settings() -> Settings:
    settings = Settings()
    if not settings.llm_configured():
        pytest.skip("GROQ_API_KEY / LLM_API_KEY not set")
    return settings


def test_live_groq_rank_and_explain(live_settings: Settings, filter_repository) -> None:
    from src.services.filter_service import apply as apply_filter

    prefs = UserPreferences(
        location="Bangalore",
        budget="medium",
        cuisine="Italian",
        min_rating=4.0,
    )
    filtered = apply_filter(prefs, filter_repository)
    assert filtered.ok

    service = LLMService(settings=live_settings)
    result = service.rank_and_explain(prefs, filtered.restaurants)
    assert result.recommendations
    assert all(entry.explanation for entry in result.recommendations)
