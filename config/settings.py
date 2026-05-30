"""Environment-backed application settings (Phase 0+)."""

from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Any, Literal

from pydantic import AliasChoices, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

LLMProvider = Literal["groq"]

DEFAULT_BUDGET_BANDS: dict[str, dict[str, float]] = {
    "low": {"max": 500},
    "medium": {"min": 500, "max": 1500},
    "high": {"min": 1500},
}

DEFAULT_LLM_MODEL = "llama-3.3-70b-versatile"


class Settings(BaseSettings):
    """Typed configuration loaded from environment variables and optional `.env` file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    # Dataset
    hf_dataset_name: str = Field(
        default="ManikaSaini/zomato-restaurant-recommendation",
        validation_alias="HF_DATASET_NAME",
    )
    data_snapshot_path: str | None = Field(default="data/cache/restaurants.parquet", validation_alias="DATA_SNAPSHOT_PATH")

    # LLM (Groq — Phase 3)
    llm_provider: LLMProvider = Field(default="groq", validation_alias="LLM_PROVIDER")
    llm_model: str = Field(default=DEFAULT_LLM_MODEL, validation_alias="LLM_MODEL")
    llm_api_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("LLM_API_KEY", "GROQ_API_KEY"),
    )
    llm_temperature: float = Field(default=0.2, validation_alias="LLM_TEMPERATURE")
    llm_max_tokens: int = Field(default=2048, validation_alias="LLM_MAX_TOKENS")
    llm_request_timeout: float = Field(default=60.0, validation_alias="LLM_REQUEST_TIMEOUT")

    # Recommendation pipeline
    max_candidates: int = Field(default=30, validation_alias="MAX_CANDIDATES")
    top_k: int = Field(default=5, validation_alias="TOP_K")
    default_min_rating: float = Field(default=3.0, validation_alias="DEFAULT_MIN_RATING")
    max_additional_preferences_length: int = Field(
        default=500,
        validation_alias="MAX_ADDITIONAL_PREFERENCES_LENGTH",
    )
    budget_bands_json: str = Field(
        default=json.dumps(DEFAULT_BUDGET_BANDS),
        validation_alias="BUDGET_BANDS",
    )

    # Runtime
    app_env: Literal["development", "staging", "production"] = Field(
        default="development",
        validation_alias="APP_ENV",
    )
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    @field_validator("llm_provider")
    @classmethod
    def groq_only(cls, value: str) -> str:
        if value != "groq":
            raise ValueError("LLM_PROVIDER must be 'groq' for v1")
        return value

    @field_validator("max_candidates", "top_k", "llm_max_tokens")
    @classmethod
    def positive_int(cls, value: int) -> int:
        if value < 1:
            raise ValueError("must be >= 1")
        return value

    @field_validator("default_min_rating")
    @classmethod
    def rating_in_range(cls, value: float) -> float:
        if not 0.0 <= value <= 5.0:
            raise ValueError("default_min_rating must be between 0 and 5")
        return value

    @field_validator("llm_temperature")
    @classmethod
    def temperature_in_range(cls, value: float) -> float:
        if not 0.0 <= value <= 2.0:
            raise ValueError("llm_temperature must be between 0 and 2")
        return value

    @model_validator(mode="after")
    def clamp_top_k_to_max_candidates(self) -> Settings:
        if self.top_k > self.max_candidates:
            object.__setattr__(self, "top_k", self.max_candidates)
        return self

    @property
    def budget_bands(self) -> dict[str, dict[str, float]]:
        """Parsed budget band thresholds for cost-for-two (INR)."""
        parsed: Any = json.loads(self.budget_bands_json)
        if not isinstance(parsed, dict):
            raise ValueError("BUDGET_BANDS must be a JSON object")
        return parsed

    def resolved_groq_api_key(self) -> str | None:
        """API key from settings or ``GROQ_API_KEY`` / ``LLM_API_KEY`` env."""
        if self.llm_api_key and self.llm_api_key.strip():
            return self.llm_api_key.strip()
        for env_name in ("GROQ_API_KEY", "LLM_API_KEY"):
            value = os.environ.get(env_name, "").strip()
            if value:
                return value
        return None

    def llm_configured(self) -> bool:
        """True when a Groq API key is available."""
        return bool(self.resolved_groq_api_key())


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton for the process."""
    return Settings()
