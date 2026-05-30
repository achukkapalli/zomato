"""Groq LLM ranking and explanation service (Phase 3)."""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Protocol

from pydantic import BaseModel, Field, ValidationError

from config.settings import Settings, get_settings
from src.models.preferences import UserPreferences
from src.models.restaurant import Restaurant
from src.services.filter_service import _sort_key
from src.services.prompt_builder import build_messages

logger = logging.getLogger(__name__)


class LLMRecommendationEntry(BaseModel):
    restaurant_id: str
    rank: int = Field(..., ge=1)
    explanation: str = ""


class LLMResponsePayload(BaseModel):
    summary: str | None = None
    recommendations: list[LLMRecommendationEntry] = Field(default_factory=list)


class RankAndExplainResult(BaseModel):
    """Parsed, validated LLM output ready for orchestrator merge (Phase 4)."""

    summary: str | None = None
    recommendations: list[LLMRecommendationEntry] = Field(default_factory=list)
    used_fallback: bool = False


class GroqClientProtocol(Protocol):
    """Subset of Groq client used for testing."""

    class chat:
        class completions:
            @staticmethod
            def create(**kwargs: Any) -> Any: ...


class LLMServiceError(Exception):
    """Base error for LLM failures."""


class LLMNotConfiguredError(LLMServiceError):
    """Raised when Groq API key is missing."""


class LLMService:
    """Rank and explain filtered candidates via Groq Chat Completions."""

    def __init__(
        self,
        settings: Settings | None = None,
        client: GroqClientProtocol | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._client = client

    def _get_client(self) -> GroqClientProtocol:
        if self._client is not None:
            return self._client
        api_key = self._settings.resolved_groq_api_key()
        if not api_key:
            raise LLMNotConfiguredError(
                "Groq API key not set. Add GROQ_API_KEY or LLM_API_KEY to your .env file."
            )
        from groq import Groq

        self._client = Groq(api_key=api_key)
        return self._client

    def rank_and_explain(
        self,
        preferences: UserPreferences,
        candidates: list[Restaurant],
    ) -> RankAndExplainResult:
        if not candidates:
            raise ValueError("Cannot call LLM with an empty candidate list")

        cfg = self._settings
        try:
            raw_content = self._call_groq_with_retry(preferences, candidates)
            parsed = parse_llm_response(
                raw_content,
                candidates,
                top_k=cfg.top_k,
                preferences=preferences,
            )
            if parsed.recommendations:
                return parsed
            logger.warning("Groq returned no valid recommendations; using fallback")
        except LLMNotConfiguredError:
            raise
        except Exception as exc:  # noqa: BLE001
            logger.warning("Groq call failed (%s); using fallback", exc)

        return fallback_ranking(preferences, candidates, top_k=cfg.top_k)

    def _call_groq_with_retry(
        self,
        preferences: UserPreferences,
        candidates: list[Restaurant],
    ) -> str:
        last_error: Exception | None = None
        for attempt in range(2):
            try:
                return self._call_groq(preferences, candidates)
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                if attempt == 0 and _is_retryable(exc):
                    logger.info("Retrying Groq request after %s", type(exc).__name__)
                    time.sleep(1.0)
                    continue
                raise
        raise last_error or LLMServiceError("Groq request failed")

    def _call_groq(
        self,
        preferences: UserPreferences,
        candidates: list[Restaurant],
    ) -> str:
        cfg = self._settings
        client = self._get_client()
        messages = build_messages(preferences, candidates, top_k=cfg.top_k)

        completion = client.chat.completions.create(
            model=cfg.llm_model,
            messages=messages,
            temperature=cfg.llm_temperature,
            max_tokens=cfg.llm_max_tokens,
            response_format={"type": "json_object"},
            timeout=cfg.llm_request_timeout,
        )
        content = completion.choices[0].message.content
        if not content or not str(content).strip():
            raise LLMServiceError("Groq returned empty content")
        return str(content).strip()


def _is_retryable(exc: Exception) -> bool:
    name = type(exc).__name__.lower()
    module = type(exc).__module__.lower()
    if "ratelimit" in name or "timeout" in name or "connection" in name:
        return True
    if "groq" in module and ("429" in str(exc) or "503" in str(exc)):
        return True
    return False


def _extract_json_text(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


def parse_llm_response(
    raw_content: str,
    candidates: list[Restaurant],
    *,
    top_k: int,
    preferences: UserPreferences | None = None,
) -> RankAndExplainResult:
    """Validate JSON and keep only IDs present in the candidate list."""
    valid_ids = {r.id for r in candidates}
    by_id = {r.id: r for r in candidates}

    text = _extract_json_text(raw_content)
    data = json.loads(text)
    payload = LLMResponsePayload.model_validate(data)

    seen: set[str] = set()
    cleaned: list[LLMRecommendationEntry] = []

    for entry in sorted(payload.recommendations, key=lambda e: e.rank):
        rid = str(entry.restaurant_id).strip()
        if rid not in valid_ids or rid in seen:
            continue
        seen.add(rid)
        cleaned.append(
            LLMRecommendationEntry(
                restaurant_id=rid,
                rank=len(cleaned) + 1,
                explanation=entry.explanation.strip()
                or _template_explanation(by_id[rid], preferences),
            )
        )
        if len(cleaned) >= top_k:
            break

    return RankAndExplainResult(
        summary=(payload.summary or "").strip() or None,
        recommendations=cleaned,
        used_fallback=False,
    )


def _template_explanation(
    restaurant: Restaurant,
    preferences: UserPreferences | None,
) -> str:
    if preferences is None:
        return (
            f"{restaurant.name} in {restaurant.location} matches your filters "
            f"({restaurant.budget_band} budget)."
        )
    parts = [
        f"{restaurant.name} in {preferences.location} fits your {preferences.budget} budget."
    ]
    if preferences.cuisine:
        parts.append(f"Cuisine includes {preferences.cuisine}.")
    if restaurant.rating is not None:
        parts.append(f"Rated {restaurant.rating}/5.")
    if preferences.additional_preferences:
        parts.append(f"Notes: {preferences.additional_preferences}.")
    return " ".join(parts)


def fallback_ranking(
    preferences: UserPreferences,
    candidates: list[Restaurant],
    *,
    top_k: int,
) -> RankAndExplainResult:
    """Deterministic top-K by rating when Groq fails or returns invalid JSON."""
    # Ensure uniqueness by restaurant_id in case upstream data contains duplicates.
    seen: set[str] = set()
    unique_candidates: list[Restaurant] = []
    for r in sorted(candidates, key=_sort_key):
        if r.id in seen:
            continue
        seen.add(r.id)
        unique_candidates.append(r)
        if len(unique_candidates) >= top_k:
            break
    sorted_rows = unique_candidates
    recommendations = [
        LLMRecommendationEntry(
            restaurant_id=r.id,
            rank=index + 1,
            explanation=_template_explanation(r, preferences),
        )
        for index, r in enumerate(sorted_rows)
    ]
    summary = (
        f"Top {len(recommendations)} picks in {preferences.location} "
        f"for {preferences.budget} budget"
        + (f" and {preferences.cuisine} cuisine" if preferences.cuisine else "")
        + ", ranked by rating."
    )
    return RankAndExplainResult(
        summary=summary,
        recommendations=recommendations,
        used_fallback=True,
    )


def try_parse_llm_response(
    raw_content: str,
    candidates: list[Restaurant],
    *,
    top_k: int,
) -> RankAndExplainResult | None:
    """Parse without raising; returns None on failure."""
    try:
        return parse_llm_response(raw_content, candidates, top_k=top_k)
    except (json.JSONDecodeError, ValidationError, TypeError, ValueError) as exc:
        logger.debug("LLM parse failed: %s", exc)
        return None


def rank_and_explain(
    preferences: UserPreferences,
    candidates: list[Restaurant],
    settings: Settings | None = None,
    client: GroqClientProtocol | None = None,
) -> RankAndExplainResult:
    """Module-level helper used by orchestrator (Phase 4)."""
    return LLMService(settings=settings, client=client).rank_and_explain(
        preferences, candidates
    )
