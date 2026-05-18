"""Shared pytest fixtures for tests/tui/.

Created in aa-ma-tui-tracker M1 (2026-05-17), extended in M2 + M3.

Static-task body factored to `_static_tasks.py::make_static_tasks()` in M3
Step 3.10 so snapshot fixture apps (which can't take pytest fixtures) can
import the same builder directly.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.tui._static_tasks import make_static_tasks


@pytest.fixture
def fixtures_dir() -> Path:
    """Absolute path to the tests/tui/fixtures/tasks/ directory.

    Use via:
        def test_x(fixtures_dir: Path) -> None:
            playwright = fixtures_dir / "playwright-skill"
            ...
    """
    return Path(__file__).parent / "fixtures" / "tasks"


@pytest.fixture
def snapshots_dir() -> Path:
    """Absolute path to tests/tui/snapshots/ (golden text + JSON files)."""
    return Path(__file__).parent / "snapshots"


@pytest.fixture
def static_tasks() -> list:
    """Three deterministic Task objects for golden-file rendering tests.

    Layout:
        alpha-task   — COMPLETE (all 2 milestones done; 4 steps total)
        beta-task    — IN_PROGRESS (M1 done, M2 mid-flight; 5 steps total)
        gamma-task   — BLOCKED (M1 done, M2 blocked; 3 steps total)

    Body factored to `_static_tasks.py::make_static_tasks()` so snapshot
    fixture apps (which can't take pytest fixtures) share the same builder.
    """
    return make_static_tasks()
