#!/usr/bin/env python3
"""
Print dataset statistics for local validation (Phase 1.8).

Usage:
    python scripts/inspect_dataset.py
    python scripts/inspect_dataset.py --limit 5
"""

from __future__ import annotations

import argparse
import sys
sys.stdout.reconfigure(encoding="utf-8")
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.settings import get_settings
from src.data.repository import RestaurantRepository


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect loaded Zomato restaurant data.")
    parser.add_argument("--limit", type=int, default=3, help="Sample rows to print")
    args = parser.parse_args()

    settings = get_settings()
    repo = RestaurantRepository(settings=settings)
    repo.ensure_loaded()

    print(f"Dataset: {settings.hf_dataset_name}")
    print(f"Restaurants loaded: {repo.count()}")
    print(f"Rows skipped in preprocess: {repo.skipped_rows}")
    print(f"Unique cities: {len(repo.get_locations())}")
    print(f"Unique cuisine tags: {len(repo.get_cuisines())}")
    print("\nCities (first 20):")
    for city in repo.get_locations()[:20]:
        print(f"  - {city}")

    print("\nCuisines (first 20):")
    for cuisine in repo.get_cuisines()[:20]:
        print(f"  - {cuisine}")

    print(f"\nSample restaurants (top {args.limit} by list order):")
    for restaurant in repo.get_all()[: args.limit]:
        print(
            f"  [{restaurant.id}] {restaurant.name} | {restaurant.location} | "
            f"rating={restaurant.rating} | cost={restaurant.display_cost} | "
            f"band={restaurant.budget_band} | cuisines={', '.join(restaurant.cuisines[:3])}"
        )


if __name__ == "__main__":
    main()
