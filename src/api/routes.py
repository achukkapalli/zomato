"""API routes (Phase 5 option B)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from config.settings import get_settings
from src.app.pipeline import run_recommendation
from src.data.repository import get_repository
from src.models.preferences import UserPreferences

router = APIRouter()


@router.get("/health")
def health() -> dict[str, Any]:
    settings = get_settings()
    repo = get_repository(settings=settings)
    dataset_loaded = False
    restaurant_count = 0
    city_count = 0

    try:
        repo.ensure_loaded()
        dataset_loaded = True
        restaurant_count = repo.count()
        city_count = len(repo.get_locations())
    except Exception:  # noqa: BLE001
        dataset_loaded = False

    return {
        "status": "ok" if dataset_loaded else "degraded",
        "dataset_loaded": dataset_loaded,
        "restaurant_count": restaurant_count,
        "city_count": city_count,
        "llm_configured": settings.llm_configured(),
        "llm_model": settings.llm_model,
    }


@router.post("/recommendations")
def recommend(preferences: UserPreferences) -> dict[str, Any]:
    """
    Returns either RecommendationResult or EmptyFilterResult (both are Pydantic models).
    """
    settings = get_settings()
    repo = get_repository(settings=settings)
    result = run_recommendation(preferences, settings=settings, repository=repo)
    payload = result.model_dump()

    # Phase 6: user-friendly hint when fallback was used.
    if payload.get("used_fallback") is True:
        payload["note"] = (
            "Used deterministic fallback ranking (Groq unavailable, not configured, "
            "timed out, or returned invalid JSON)."
        )
    return payload

