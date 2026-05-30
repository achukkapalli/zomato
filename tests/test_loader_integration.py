"""Optional integration test: downloads from Hugging Face (slow, needs network)."""

from __future__ import annotations

import os

import pytest

from config.settings import Settings
from src.data.loader import load_raw_rows
from src.data.repository import RestaurantRepository

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_HF_INTEGRATION") != "1",
    reason="Set RUN_HF_INTEGRATION=1 to run Hugging Face download tests",
)


def test_load_raw_rows_from_hf() -> None:
    rows = load_raw_rows("ManikaSaini/zomato-restaurant-recommendation")
    assert len(rows) > 1000
    assert "name" in rows[0] or "listed_in(city)" in rows[0]


def test_repository_loads_hf_dataset() -> None:
    repo = RestaurantRepository(settings=Settings())
    repo.ensure_loaded()
    assert repo.count() > 1000
    assert len(repo.get_locations()) >= 5
