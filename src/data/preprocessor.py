"""Restaurant record preprocessing (Phase 1)."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from config.settings import Settings
from src.data.schema import LOCATION_ALIASES, resolve_column
from src.models.restaurant import BudgetBand, Restaurant

_RATING_PATTERN = re.compile(r"(\d+(?:\.\d+)?)\s*/\s*5", re.IGNORECASE)
_RATING_PLAIN = re.compile(r"^\d+(?:\.\d+)?$")
_COST_RANGE = re.compile(r"(\d[\d,]*)\s*-\s*(\d[\d,]*)")
_COST_NUMBER = re.compile(r"(\d[\d,]*)")


def _is_nan(value: object) -> bool:
    if value is None:
        return True
    if isinstance(value, float):
        import math
        if math.isnan(value):
            return True
    try:
        import numpy as np
        if isinstance(value, (np.float64, np.float32, np.float16)) and np.isnan(value):
            return True
    except ImportError:
        pass
    try:
        import pandas as pd
        if pd.isna(value):
            return True
    except (TypeError, ValueError, ImportError):
        pass
    return False


def normalize_city(city: str | None) -> str:
    if _is_nan(city):
        return ""
    cleaned = " ".join(str(city).strip().split())
    key = cleaned.casefold()
    if key in LOCATION_ALIASES:
        return LOCATION_ALIASES[key]
    return cleaned.title() if cleaned.islower() else cleaned


def parse_rating(value: object | None) -> float | None:
    """Parse Zomato rate strings such as '4.1/5', 'NEW', or '-'."""
    if _is_nan(value):
        return None
    text = str(value).strip()
    if not text or text.upper() in {"NEW", "-", "NA", "N/A"}:
        return None
    match = _RATING_PATTERN.search(text)
    if match:
        rating = float(match.group(1))
        return rating if 0.0 <= rating <= 5.0 else None
    if _RATING_PLAIN.match(text):
        rating = float(text)
        return rating if 0.0 <= rating <= 5.0 else None
    try:
        rating = float(text)
        return rating if 0.0 <= rating <= 5.0 else None
    except ValueError:
        return None


def parse_cost(value: object | None) -> float | None:
    """Parse cost-for-two: '300', '1,200', '300-400', or currency-prefixed strings."""
    if _is_nan(value):
        return None
    text = str(value).strip()
    if not text or text.upper() in {"-", "NA", "N/A"}:
        return None

    range_match = _COST_RANGE.search(text.replace("₹", "").replace("Rs.", ""))
    if range_match:
        low = float(range_match.group(1).replace(",", ""))
        high = float(range_match.group(2).replace(",", ""))
        return (low + high) / 2.0

    numbers = _COST_NUMBER.findall(text.replace("₹", "").replace("Rs.", ""))
    if not numbers:
        return None
    return float(numbers[0].replace(",", ""))


def parse_cuisines(value: object | None) -> list[str]:
    if _is_nan(value):
        return []
    text = str(value).strip()
    if not text:
        return []
    return [part.strip() for part in text.split(",") if part.strip()]



def assign_budget_band(
    cost: float | None,
    bands: dict[str, dict[str, float]],
) -> BudgetBand:
    if cost is None:
        return "unknown"
    low = bands.get("low", {})
    medium = bands.get("medium", {})
    high = bands.get("high", {})

    low_max = low.get("max")
    medium_max = medium.get("max", low_max)
    high_min = high.get("min", medium_max)

    if low_max is not None and cost <= low_max:
        return "low"
    if medium_max is not None and cost <= medium_max:
        return "medium"
    if high_min is not None and cost >= high_min:
        return "high"
    medium_min = medium.get("min", low_max)
    if (
        medium_min is not None
        and medium_max is not None
        and medium_min <= cost <= medium_max
    ):
        return "medium"
    if low_max is not None and cost > low_max:
        if medium_max is not None and cost <= medium_max:
            return "medium"
        return "high"
    return "unknown"


def _stable_id(url: str | None, name: str, city: str, row_index: int) -> str:
    if url and str(url).strip():
        digest = hashlib.sha256(str(url).strip().encode()).hexdigest()[:12]
        return f"r_{digest}"
    base = f"{name}|{city}|{row_index}"
    digest = hashlib.sha256(base.encode()).hexdigest()[:12]
    return f"r_{digest}"


def preprocess_row(
    raw_row: dict[str, Any],
    row_index: int,
    settings: Settings,
) -> Restaurant | None:
    """
    Map one raw HF row to a Restaurant, or None if the row should be skipped.
    Skips rows without a usable name (edge case D-06).
    """
    name_val = resolve_column(raw_row, "name")
    if name_val is None or not str(name_val).strip():
        return None

    name = str(name_val).strip()
    city = normalize_city(
        str(resolve_column(raw_row, "city") or "")
        or str(resolve_column(raw_row, "locality") or "")
    )
    locality_val = resolve_column(raw_row, "locality")
    locality = None
    if not _is_nan(locality_val):
        s = str(locality_val).strip()
        if s and s.lower() not in {"nan", "none", "null", "na", "n/a"}:
            locality = s

    cuisines = parse_cuisines(resolve_column(raw_row, "cuisines"))
    rating = parse_rating(resolve_column(raw_row, "rate"))
    estimated_cost = parse_cost(resolve_column(raw_row, "approx_cost"))
    budget_band = assign_budget_band(estimated_cost, settings.budget_bands)

    url = resolve_column(raw_row, "url")
    rest_id = _stable_id(
        str(url) if url is not None else None,
        name,
        city,
        row_index,
    )

    metadata: dict[str, Any] = {}
    optional_fields = (
        ("address", "address"),
        ("votes", "votes"),
        ("rest_type", "rest_type"),
        ("online_order", "online_order"),
        ("book_table", "book_table"),
        ("listed_in_type", "listed_in_type"),
    )
    for meta_key, schema_key in optional_fields:
        val = resolve_column(raw_row, schema_key)
        if val is not None and str(val).strip():
            metadata[meta_key] = val

    return Restaurant(
        id=rest_id,
        name=name,
        location=city,
        cuisines=cuisines,
        rating=rating,
        estimated_cost=estimated_cost,
        budget_band=budget_band,
        locality=locality,
        metadata=metadata,
    )


def preprocess_rows(
    raw_rows: list[dict[str, Any]],
    settings: Settings,
) -> list[Restaurant]:
    """
    Convert raw dataset rows to normalized restaurants, skipping invalid rows.

    Also de-duplicate records that resolve to the same stable ID (usually same URL).
    When duplicates exist, keep the "best" record (highest rating, then highest votes),
    while preserving as much metadata as possible.
    """

    def _votes(meta: dict[str, Any]) -> int:
        raw = meta.get("votes")
        try:
            return int(raw) if raw is not None else 0
        except (TypeError, ValueError):
            return 0

    def _quality_key(r: Restaurant) -> tuple[float, int, int, int]:
        # Higher is better (so we can use max()).
        rating = r.rating if r.rating is not None else -1.0
        votes = _votes(r.metadata)
        has_cost = 1 if r.estimated_cost is not None else 0
        cuisine_count = len(r.cuisines)
        return (rating, votes, has_cost, cuisine_count)

    by_id: dict[str, Restaurant] = {}
    for index, row in enumerate(raw_rows):
        record = preprocess_row(row, index, settings)
        if record is None:
            continue

        existing = by_id.get(record.id)
        if existing is None:
            by_id[record.id] = record
            continue

        # Prefer higher-quality record.
        better, worse = (record, existing) if _quality_key(record) > _quality_key(existing) else (existing, record)

        # Merge cuisines/metadata so we don't lose information.
        merged_cuisines = sorted({*better.cuisines, *worse.cuisines}, key=str.casefold)
        merged_meta = {**worse.metadata, **better.metadata}
        # Keep the higher votes value if both present.
        merged_votes = max(_votes(existing.metadata), _votes(record.metadata))
        if merged_votes:
            merged_meta["votes"] = merged_votes

        by_id[record.id] = better.model_copy(
            update={
                "cuisines": merged_cuisines,
                "metadata": merged_meta,
            }
        )

    return list(by_id.values())
