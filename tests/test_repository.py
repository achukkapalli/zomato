"""Phase 1: repository tests (no Hugging Face download)."""

from __future__ import annotations

import threading
from pathlib import Path

import pytest

from config.settings import Settings
from src.data.loader import DatasetLoadError
from src.data.repository import RestaurantRepository, load_processed_snapshot, save_processed_snapshot


def test_ensure_loaded_with_mock_loader(mock_raw_loader, settings: Settings) -> None:
    repo = RestaurantRepository(settings=settings, raw_loader=mock_raw_loader)
    repo.ensure_loaded()
    assert repo.loaded
    assert repo.count() == 3
    assert repo.skipped_rows == 1


def test_get_all_returns_copy(mock_raw_loader, settings: Settings) -> None:
    repo = RestaurantRepository(settings=settings, raw_loader=mock_raw_loader)
    first = repo.get_all()
    second = repo.get_all()
    assert first == second
    assert first is not second


def test_get_locations_and_cuisines(mock_raw_loader, settings: Settings) -> None:
    repo = RestaurantRepository(settings=settings, raw_loader=mock_raw_loader)
    locations = repo.get_locations()
    cuisines = repo.get_cuisines()
    assert "Bangalore" in locations
    assert "Delhi" in locations
    assert "Italian" in cuisines
    assert "North Indian" in cuisines


def test_filter_by_location_case_insensitive(mock_raw_loader, settings: Settings) -> None:
    repo = RestaurantRepository(settings=settings, raw_loader=mock_raw_loader)
    matches = repo.filter_by_location("bangalore")
    assert len(matches) == 2
    assert all(r.location == "Bangalore" for r in matches)


def test_get_by_id(mock_raw_loader, settings: Settings) -> None:
    repo = RestaurantRepository(settings=settings, raw_loader=mock_raw_loader)
    sample_id = repo.get_all()[0].id
    assert repo.get_by_id(sample_id) is not None
    assert repo.get_by_id("nonexistent") is None


def test_ensure_loaded_thread_safe(mock_raw_loader, settings: Settings) -> None:
    repo = RestaurantRepository(settings=settings, raw_loader=mock_raw_loader)
    errors: list[Exception] = []

    def load() -> None:
        try:
            repo.ensure_loaded()
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=load) for _ in range(5)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert not errors
    assert repo.count() == 3


def test_empty_raw_rows_raises(settings: Settings) -> None:
    def empty_loader(_: Settings) -> list[dict]:
        return []

    repo = RestaurantRepository(settings=settings, raw_loader=empty_loader)
    with pytest.raises(DatasetLoadError):
        repo.ensure_loaded()


def test_processed_snapshot_roundtrip(
    mock_raw_loader,
    settings: Settings,
    tmp_path: Path,
) -> None:
    snapshot = tmp_path / "restaurants.parquet"
    repo = RestaurantRepository(settings=settings, raw_loader=mock_raw_loader)
    repo.ensure_loaded()
    save_processed_snapshot(repo.get_all(), snapshot)

    loaded = load_processed_snapshot(snapshot)
    assert len(loaded) == 3
    assert loaded[0].name == repo.get_all()[0].name

    settings_snapshot = Settings(data_snapshot_path=str(snapshot))
    repo2 = RestaurantRepository(settings=settings_snapshot, raw_loader=mock_raw_loader)
    repo2.ensure_loaded()
    assert repo2.count() == 3
    assert repo2.skipped_rows == 0
