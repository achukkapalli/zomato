"""Phase 3: Groq LLM service tests (mocked client)."""

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from config.settings import Settings
from src.models.preferences import UserPreferences
from src.models.restaurant import Restaurant
from src.services.llm_service import (
    LLMNotConfiguredError,
    LLMService,
    fallback_ranking,
    parse_llm_response,
    rank_and_explain,
    try_parse_llm_response,
)
from src.services.prompt_builder import build_messages


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
def candidates() -> list[Restaurant]:
    return [
        Restaurant(
            id="r_1",
            name="Trattoria",
            location="Bangalore",
            cuisines=["Italian"],
            rating=4.5,
            estimated_cost=800.0,
            budget_band="medium",
        ),
        Restaurant(
            id="r_2",
            name="Pizza Hub",
            location="Bangalore",
            cuisines=["Italian", "Pizza"],
            rating=4.0,
            estimated_cost=500.0,
            budget_band="medium",
        ),
        Restaurant(
            id="r_3",
            name="Dragon Wok",
            location="Bangalore",
            cuisines=["Chinese"],
            rating=4.8,
            estimated_cost=900.0,
            budget_band="medium",
        ),
    ]


def _groq_response(payload: dict) -> SimpleNamespace:
    content = json.dumps(payload)
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )


def _mock_groq_client(payload: dict) -> MagicMock:
    client = MagicMock()
    client.chat.completions.create.return_value = _groq_response(payload)
    return client


def test_build_messages_include_preferences_and_candidates(
    preferences: UserPreferences,
    candidates: list[Restaurant],
) -> None:
    messages = build_messages(preferences, candidates, top_k=5)
    assert len(messages) == 2
    assert messages[0]["role"] == "system"
    assert "restaurant_id" in messages[1]["content"]
    assert "Bangalore" in messages[1]["content"]
    assert "family-friendly" in messages[1]["content"]


def test_parse_valid_json(preferences: UserPreferences, candidates: list[Restaurant]) -> None:
    raw = json.dumps(
        {
            "summary": "Great Italian options.",
            "recommendations": [
                {"restaurant_id": "r_1", "rank": 1, "explanation": "Best Italian fit in Bangalore."},
                {"restaurant_id": "r_2", "rank": 2, "explanation": "Solid medium-budget Italian."},
            ],
        }
    )
    result = parse_llm_response(raw, candidates, top_k=5, preferences=preferences)
    assert not result.used_fallback
    assert result.summary == "Great Italian options."
    assert len(result.recommendations) == 2
    assert result.recommendations[0].restaurant_id == "r_1"


def test_parse_drops_unknown_ids(candidates: list[Restaurant]) -> None:
    raw = json.dumps(
        {
            "recommendations": [
                {"restaurant_id": "r_fake", "rank": 1, "explanation": "Hallucinated"},
                {"restaurant_id": "r_1", "rank": 2, "explanation": "Valid"},
            ]
        }
    )
    result = parse_llm_response(raw, candidates, top_k=5)
    assert len(result.recommendations) == 1
    assert result.recommendations[0].restaurant_id == "r_1"


def test_parse_dedupes_duplicate_ids(candidates: list[Restaurant]) -> None:
    raw = json.dumps(
        {
            "recommendations": [
                {"restaurant_id": "r_1", "rank": 1, "explanation": "A"},
                {"restaurant_id": "r_1", "rank": 2, "explanation": "B"},
            ]
        }
    )
    result = parse_llm_response(raw, candidates, top_k=5)
    assert len(result.recommendations) == 1


def test_parse_truncates_to_top_k(candidates: list[Restaurant]) -> None:
    raw = json.dumps(
        {
            "recommendations": [
                {"restaurant_id": "r_1", "rank": 1, "explanation": "A"},
                {"restaurant_id": "r_2", "rank": 2, "explanation": "B"},
                {"restaurant_id": "r_3", "rank": 3, "explanation": "C"},
            ]
        }
    )
    result = parse_llm_response(raw, candidates, top_k=2)
    assert len(result.recommendations) == 2


def test_parse_invalid_json_returns_none(candidates: list[Restaurant]) -> None:
    assert try_parse_llm_response("not json", candidates, top_k=5) is None


def test_fallback_ranking(preferences: UserPreferences, candidates: list[Restaurant]) -> None:
    result = fallback_ranking(preferences, candidates, top_k=2)
    assert result.used_fallback
    assert len(result.recommendations) == 2
    assert result.recommendations[0].restaurant_id == "r_3"
    assert "Bangalore" in result.recommendations[0].explanation


def test_rank_and_explain_with_mock_groq(
    preferences: UserPreferences,
    candidates: list[Restaurant],
) -> None:
    payload = {
        "summary": "Italian picks in Bangalore.",
        "recommendations": [
            {
                "restaurant_id": "r_1",
                "rank": 1,
                "explanation": "Top Italian, medium budget, family-friendly vibe.",
            },
        ],
    }
    settings = Settings(llm_api_key="test-key", llm_provider="groq")
    client = _mock_groq_client(payload)
    service = LLMService(settings=settings, client=client)
    result = service.rank_and_explain(preferences, candidates)

    assert not result.used_fallback
    assert result.recommendations[0].restaurant_id == "r_1"
    client.chat.completions.create.assert_called_once()
    call_kwargs = client.chat.completions.create.call_args.kwargs
    assert call_kwargs["model"] == settings.llm_model
    assert call_kwargs["response_format"] == {"type": "json_object"}


def test_rank_and_explain_fallback_on_invalid_json(
    preferences: UserPreferences,
    candidates: list[Restaurant],
) -> None:
    client = MagicMock()
    client.chat.completions.create.return_value = _groq_response({"wrong": "shape"})
    settings = Settings(llm_api_key="test-key")
    service = LLMService(settings=settings, client=client)
    result = service.rank_and_explain(preferences, candidates)
    assert result.used_fallback
    assert len(result.recommendations) == 3


def test_rank_and_explain_fallback_on_api_error(
    preferences: UserPreferences,
    candidates: list[Restaurant],
) -> None:
    client = MagicMock()
    client.chat.completions.create.side_effect = RuntimeError("connection failed")
    settings = Settings(llm_api_key="test-key")
    service = LLMService(settings=settings, client=client)
    result = service.rank_and_explain(preferences, candidates)
    assert result.used_fallback


def test_missing_api_key_raises(preferences: UserPreferences, candidates: list[Restaurant]) -> None:
    service = LLMService(settings=Settings(llm_api_key=None))
    with pytest.raises(LLMNotConfiguredError):
        service.rank_and_explain(preferences, candidates)


def test_empty_candidates_raises(preferences: UserPreferences) -> None:
    service = LLMService(settings=Settings(llm_api_key="key"))
    with pytest.raises(ValueError):
        service.rank_and_explain(preferences, [])


def test_groq_defaults_in_settings() -> None:
    settings = Settings()
    assert settings.llm_provider == "groq"
    assert settings.llm_model == "llama-3.3-70b-versatile"


def test_invalid_provider_rejected() -> None:
    with pytest.raises(ValidationError):
        Settings(llm_provider="openai")  # type: ignore[arg-type]


def test_resolved_groq_api_key_from_GROQ_API_KEY(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "gsk-test")
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    settings = Settings(llm_api_key=None)
    assert settings.resolved_groq_api_key() == "gsk-test"
    assert settings.llm_configured()
