"""Shared pytest fixtures for tests/tui/.

Created in aa-ma-tui-tracker M1 (2026-05-17).
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def fixtures_dir() -> Path:
    """Absolute path to the tests/tui/fixtures/tasks/ directory.

    Use via:
        def test_x(fixtures_dir: Path) -> None:
            playwright = fixtures_dir / "playwright-skill"
            ...
    """
    return Path(__file__).parent / "fixtures" / "tasks"
