"""Phase 0: configuration and environment loading."""

from __future__ import annotations

import json
import os

import pytest

from config.settings import Settings, get_settings


def test_default_hf_dataset_name() -> None:
    settings = Settings()
    assert settings.hf_dataset_name == "ManikaSaini/zomato-restaurant-recommendation"


def test_hf_dataset_name_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HF_DATASET_NAME", "custom/dataset")
    settings = Settings()
    assert settings.hf_dataset_name == "custom/dataset"


def test_llm_api_key_optional_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    settings = Settings(_env_file=None)
    assert settings.llm_api_key is None
    assert settings.llm_configured() is False


def test_llm_api_key_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_API_KEY", "gsk-test-key")
    settings = Settings()
    assert settings.llm_api_key == "gsk-test-key"
    assert settings.llm_configured() is True


def test_groq_defaults() -> None:
    settings = Settings()
    assert settings.llm_provider == "groq"
    assert settings.llm_model == "llama-3.3-70b-versatile"


def test_max_candidates_and_top_k_defaults() -> None:
    settings = Settings()
    assert settings.max_candidates == 30
    assert settings.top_k == 5


def test_top_k_clamped_when_greater_than_max_candidates() -> None:
    settings = Settings(max_candidates=3, top_k=10)
    assert settings.top_k == 3


def test_invalid_max_candidates_raises() -> None:
    with pytest.raises(ValueError):
        Settings(max_candidates=0)


def test_budget_bands_parsed() -> None:
    settings = Settings()
    bands = settings.budget_bands
    assert "low" in bands
    assert "medium" in bands
    assert "high" in bands


def test_budget_bands_from_json_env(monkeypatch: pytest.MonkeyPatch) -> None:
    custom = {"low": {"max": 400}, "medium": {"min": 400, "max": 1200}, "high": {"min": 1200}}
    monkeypatch.setenv("BUDGET_BANDS", json.dumps(custom))
    settings = Settings()
    assert settings.budget_bands["low"]["max"] == 400


def test_get_settings_cached() -> None:
    a = get_settings()
    b = get_settings()
    assert a is b


def test_package_imports() -> None:
    import src
    import src.app
    import src.data
    import src.models
    import src.orchestration
    import src.services

    assert src.__version__ == "0.1.0"
