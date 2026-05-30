"""Phase 0 smoke tests: project layout and tooling."""

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

EXPECTED_PATHS = [
    "config/settings.py",
    "src/data/loader.py",
    "src/models/restaurant.py",
    "src/services/filter_service.py",
    "src/orchestration/recommender.py",
    "src/app/main.py",
    "requirements.txt",
    "pyproject.toml",
    ".env.example",
    "docs/context.md",
]


@pytest.mark.parametrize("relative_path", EXPECTED_PATHS)
def test_project_skeleton_exists(relative_path: str) -> None:
    assert (ROOT / relative_path).is_file(), f"missing {relative_path}"


def test_docs_directory_exists() -> None:
    assert (ROOT / "docs").is_dir()
