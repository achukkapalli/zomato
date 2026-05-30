"""CLI developer tool for Zomoto recommendation pipeline (Phase 4)."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from typing import Any

from config.settings import get_settings
from src.models.preferences import UserPreferences
from src.orchestration.recommender import RecommendationOrchestrator

# Log details to stderr so stdout has clean JSON only
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)


def serialize_result(result: Any) -> str:
    """Pretty-print RecommendationResult or EmptyFilterResult as JSON."""
    return json.dumps(result.model_dump(), indent=2, ensure_ascii=False)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run end-to-end Zomato restaurant recommendation pipeline."
    )
    # Required preferences
    parser.add_argument(
        "--location",
        required=True,
        help="City name (e.g. Bangalore, Delhi)",
    )
    parser.add_argument(
        "--budget",
        required=True,
        choices=["low", "medium", "high"],
        help="Budget band",
    )
    # Optional preferences
    parser.add_argument(
        "--cuisine",
        default=None,
        help="Cuisine tag (e.g. Italian, North Indian)",
    )
    parser.add_argument(
        "--min-rating",
        type=float,
        default=None,
        help="Minimum rating threshold (0.0 to 5.0)",
    )
    parser.add_argument(
        "--additional",
        default=None,
        help="Free text notes (e.g. family-friendly, roof seating)",
    )

    args = parser.parse_args()

    try:
        preferences = UserPreferences(
            location=args.location,
            budget=args.budget,
            cuisine=args.cuisine,
            min_rating=args.min_rating,
            additional_preferences=args.additional,
        )
    except Exception as exc:
        print(f"Validation Error: {exc}", file=sys.stderr)
        return 1

    settings = get_settings()
    # Inform user if Groq API key is present
    if not settings.llm_configured():
        print(
            "Warning: GROQ_API_KEY / LLM_API_KEY not configured. "
            "The pipeline will use fallback rating-based ranking.",
            file=sys.stderr,
        )

    orchestrator = RecommendationOrchestrator(settings=settings)

    print("Running recommendation pipeline...", file=sys.stderr)
    result = orchestrator.recommend(preferences)

    # Output JSON representation to stdout
    print(serialize_result(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
