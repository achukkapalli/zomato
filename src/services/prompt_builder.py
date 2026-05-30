"""LLM prompt assembly for Groq (Phase 3)."""

from __future__ import annotations

import json

from src.models.preferences import UserPreferences
from src.models.restaurant import Restaurant

SYSTEM_PROMPT = """You are a restaurant recommendation assistant for a Zomato-style app.

You receive user preferences and a fixed list of candidate restaurants from a real database.

STRICT RULES:
1. Only recommend restaurants whose restaurant_id appears in the candidate list.
2. Do not invent restaurants, IDs, ratings, or prices.
3. Rank by best overall fit for location, budget, cuisine, minimum rating, and additional_preferences.
4. Return at most {top_k} recommendations.
5. Respond with valid JSON only — no markdown, no prose outside JSON.

OUTPUT JSON SCHEMA:
{{
  "summary": "optional one-paragraph overview of the shortlist",
  "recommendations": [
    {{
      "restaurant_id": "id from candidate list",
      "rank": 1,
      "explanation": "why this fits the user preferences"
    }}
  ]
}}

In each explanation, mention relevant preference dimensions (city, budget, cuisine, rating, extras)."""


def compact_candidate(restaurant: Restaurant) -> dict:
    """Minimal fields for the LLM prompt (token budget)."""
    return {
        "restaurant_id": restaurant.id,
        "name": restaurant.name,
        "cuisines": restaurant.cuisines,
        "rating": restaurant.rating,
        "estimated_cost": restaurant.estimated_cost,
        "budget_band": restaurant.budget_band,
        "location": restaurant.location,
    }


def build_user_message(preferences: UserPreferences, candidates: list[Restaurant]) -> str:
    payload = {
        "user_preferences": {
            "location": preferences.location,
            "budget": preferences.budget,
            "cuisine": preferences.cuisine,
            "min_rating": preferences.effective_min_rating(),
            "additional_preferences": preferences.additional_preferences,
        },
        "candidates": [compact_candidate(r) for r in candidates],
    }
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False)


def build_messages(
    preferences: UserPreferences,
    candidates: list[Restaurant],
    *,
    top_k: int,
) -> list[dict[str, str]]:
    """OpenAI-style message list for Groq chat completions."""
    system = SYSTEM_PROMPT.format(top_k=top_k)
    user = build_user_message(preferences, candidates)
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
