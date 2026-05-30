"""In-memory restaurant repository (Phase 1)."""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Callable

import pandas as pd

from config.settings import Settings, get_settings
from src.data.loader import DatasetLoadError, load_raw_rows_with_snapshot
from src.data.preprocessor import preprocess_rows
from src.models.restaurant import Restaurant

logger = logging.getLogger(__name__)


def save_processed_snapshot(restaurants: list[Restaurant], path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    records = [r.model_dump() for r in restaurants]
    pd.DataFrame(records).to_parquet(target, index=False)
    logger.info("Saved processed snapshot (%s restaurants) to %s", len(restaurants), target)


def load_processed_snapshot(path: str | Path) -> list[Restaurant]:
    import math
    target = Path(path)
    if not target.is_file():
        raise DatasetLoadError(f"Processed snapshot not found: {target}")
    frame = pd.read_parquet(target)
    if frame.empty:
        raise DatasetLoadError(f"Processed snapshot is empty: {target}")
    
    restaurants = []
    for row in frame.to_dict(orient="records"):
        cleaned = {}
        for k, v in row.items():
            if isinstance(v, (list, dict, tuple)):
                cleaned[k] = v
            else:
                try:
                    cleaned[k] = None if pd.isna(v) else v
                except (TypeError, ValueError):
                    cleaned[k] = v
        restaurants.append(Restaurant.model_validate(cleaned))
    return restaurants


class RestaurantRepository:
    """
    Thread-safe, in-memory store of normalized restaurants.

    Load once via ensure_loaded(); all reads use preprocessed Restaurant models only.
    """

    def __init__(
        self,
        settings: Settings | None = None,
        raw_loader: Callable[[Settings], list[dict]] | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._raw_loader = raw_loader or load_raw_rows_with_snapshot
        self._restaurants: list[Restaurant] = []
        self._locations: list[str] = []
        self._cuisines: list[str] = []
        self._loaded = False
        self._lock = threading.Lock()
        self._skipped_rows = 0

    @property
    def loaded(self) -> bool:
        return self._loaded

    @property
    def skipped_rows(self) -> int:
        return self._skipped_rows

    def ensure_loaded(self) -> None:
        """Load and preprocess the dataset exactly once per repository instance."""
        if self._loaded:
            return
        with self._lock:
            if self._loaded:
                return
            self._restaurants = self._load_and_preprocess()
            self._locations = self._build_location_index()
            self._cuisines = self._build_cuisine_index()
            self._loaded = True
            logger.info(
                "Repository ready: %s restaurants, %s cities, %s cuisine tags",
                len(self._restaurants),
                len(self._locations),
                len(self._cuisines),
            )

    def _load_and_preprocess(self) -> list[Restaurant]:
        snapshot_path = self._settings.data_snapshot_path
        if snapshot_path:
            path = Path(snapshot_path)
            if path.is_file():
                restaurants = load_processed_snapshot(path)
                self._skipped_rows = 0
                return restaurants

        raw_rows = self._raw_loader(self._settings)
        if not raw_rows:
            raise DatasetLoadError("No raw rows available after load.")

        restaurants = preprocess_rows(raw_rows, self._settings)
        self._skipped_rows = len(raw_rows) - len(restaurants)

        if not restaurants:
            raise DatasetLoadError("All rows were skipped during preprocessing.")

        if snapshot_path:
            try:
                save_processed_snapshot(restaurants, snapshot_path)
            except Exception as exc:  # noqa: BLE001
                logger.warning("Could not write snapshot to %s: %s", snapshot_path, exc)

        return restaurants

    def get_all(self) -> list[Restaurant]:
        self.ensure_loaded()
        return list(self._restaurants)

    def count(self) -> int:
        self.ensure_loaded()
        return len(self._restaurants)

    def get_by_id(self, restaurant_id: str) -> Restaurant | None:
        self.ensure_loaded()
        for restaurant in self._restaurants:
            if restaurant.id == restaurant_id:
                return restaurant
        return None

    def get_locations(self) -> list[str]:
        """Sorted unique cities for UI dropdowns (Phase 5)."""
        self.ensure_loaded()
        return list(self._locations)

    def get_cuisines(self) -> list[str]:
        """Sorted unique cuisine tags across all restaurants."""
        self.ensure_loaded()
        return list(self._cuisines)

    def filter_by_location(self, location: str, *, case_insensitive: bool = True) -> list[Restaurant]:
        self.ensure_loaded()
        if not location.strip():
            return []
        needle = location.strip()
        if case_insensitive:
            needle_fold = needle.casefold()
            return [r for r in self._restaurants if r.location.casefold() == needle_fold]
        return [r for r in self._restaurants if r.location == needle]

    def _build_location_index(self) -> list[str]:
        cities = {r.location for r in self._restaurants if r.location}
        return sorted(cities, key=str.casefold)

    def _build_cuisine_index(self) -> list[str]:
        tags: set[str] = set()
        for restaurant in self._restaurants:
            tags.update(restaurant.cuisines)
        return sorted(tags, key=str.casefold)

    def reload(self) -> None:
        """Force reload on next ensure_loaded (useful in tests)."""
        with self._lock:
            self._restaurants = []
            self._locations = []
            self._cuisines = []
            self._loaded = False
            self._skipped_rows = 0


_default_repository: RestaurantRepository | None = None
_repo_lock = threading.Lock()


def get_repository(settings: Settings | None = None) -> RestaurantRepository:
    """Process-wide singleton repository.

    Note:
    - Passing ``settings`` will initialize the singleton (if not yet created) with
      those settings.
    - Subsequent calls return the same singleton to avoid re-downloading and
      re-processing the dataset on every request (important for the API).
    """
    global _default_repository
    with _repo_lock:
        if _default_repository is None:
            _default_repository = RestaurantRepository(settings=settings)
        return _default_repository
