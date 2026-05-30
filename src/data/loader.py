"""Hugging Face dataset loader and optional snapshot I/O (Phase 1)."""

from __future__ import annotations

import logging
from typing import Any

from datasets import load_dataset

from config.settings import Settings, get_settings

logger = logging.getLogger(__name__)


class DatasetLoadError(Exception):
    """Raised when the Hugging Face dataset cannot be loaded."""


def load_raw_rows(dataset_name: str) -> list[dict[str, Any]]:
    """
    Download and load the train split from Hugging Face.

    Returns a list of plain dict rows (no Hugging Face Dataset object leaves this module).
    """
    try:
        dataset = load_dataset(dataset_name, split="train")
    except Exception as exc:  # noqa: BLE001 — wrap HF/network errors
        raise DatasetLoadError(
            f"Failed to load dataset '{dataset_name}'. "
            "Check network access and HF_DATASET_NAME."
        ) from exc

    if len(dataset) == 0:
        raise DatasetLoadError(f"Dataset '{dataset_name}' train split is empty.")

    logger.info("Loaded %s rows from %s", len(dataset), dataset_name)
    return [dict(row) for row in dataset]


def load_raw_rows_with_snapshot(settings: Settings | None = None) -> list[dict[str, Any]]:
    """Load raw rows from Hugging Face (processed snapshots are handled by the repository)."""
    cfg = settings or get_settings()
    return load_raw_rows(cfg.hf_dataset_name)
