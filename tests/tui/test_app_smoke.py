"""Tests for src/aa_ma/tui/app.py — M3 Step 3.10.

AAMAApp orchestrates DashboardScreen + watcher + reactive task refresh.
This module covers:
    - construction with initial tasks
    - launches DashboardScreen on mount
    - bounded malformed-input tolerance (run_test(size=(120,40)) < 2s)
    - SVG snapshot regression of both screens (via pytest-textual-snapshot)
"""

from __future__ import annotations

import asyncio
import time
from pathlib import Path

from aa_ma.tui.app import AAMAApp
from aa_ma.tui.model import Task
from aa_ma.tui.screens.dashboard import DashboardScreen


# -----------------------------------------------------------------------------
# Construction
# -----------------------------------------------------------------------------


def test_aama_app_stores_initial_tasks(static_tasks) -> None:
    app = AAMAApp(initial_tasks=static_tasks)
    # Reactive attr stores the live task list (name chosen to avoid Worker.task collision)
    assert list(app.tracker_tasks) == list(static_tasks)


def test_aama_app_no_watch_roots_runs_without_watcher() -> None:
    """Constructing without watch_roots is valid — pure static mode for tests."""
    app = AAMAApp(initial_tasks=[])
    assert app.watch_roots_value == []


def test_aama_app_has_r_binding_for_reload() -> None:
    """`r` keybinding is named in M3 AC #3 — explicit reload action."""
    keys = [b.key for b in AAMAApp.BINDINGS]
    assert "r" in keys


def test_aama_app_r_binding_reloads_via_action(static_tasks, tmp_path) -> None:
    """Pilot test: pressing `r` calls action_reload → re-discover from watch_roots."""

    async def _run() -> None:
        # Set up a fake AA-MA active dir so discover_tasks finds something.
        task_dir = tmp_path / "foo"
        task_dir.mkdir()
        (task_dir / "foo-tasks.md").write_text(
            "## Milestone 1: M\n- Status: COMPLETE\n\n### Step 1.1: S\n- Status: COMPLETE\n- Result Log: x\n"
        )
        (task_dir / "foo-plan.md").write_text("")
        (task_dir / "foo-reference.md").write_text("")
        (task_dir / "foo-context-log.md").write_text("")
        (task_dir / "foo-provenance.log").write_text("")

        app = AAMAApp(initial_tasks=[], watch_roots=[tmp_path])
        async with app.run_test() as pilot:
            await pilot.pause()
            # Initially empty (we passed initial_tasks=[]).
            assert app.tracker_tasks == []
            await pilot.press("r")
            await pilot.pause(0.2)
            # After reload, the foo task should be discovered.
            names = [t.name for t in app.tracker_tasks]
            assert "foo" in names

    asyncio.run(_run())


# -----------------------------------------------------------------------------
# Launch — DashboardScreen pushed on mount
# -----------------------------------------------------------------------------


def test_aama_app_pushes_dashboard_on_mount(static_tasks) -> None:
    async def _run() -> None:
        app = AAMAApp(initial_tasks=static_tasks)
        async with app.run_test() as pilot:
            await pilot.pause()
            assert isinstance(app.screen, DashboardScreen)

    asyncio.run(_run())


# -----------------------------------------------------------------------------
# Bounded malformed-input tolerance (acceptance criterion #6 for M3)
# -----------------------------------------------------------------------------


def test_aama_app_tolerates_parse_error_tasks_within_2s(static_tasks) -> None:
    """An ERROR-status task does NOT block mount + first render."""

    async def _run() -> None:
        broken = Task(name="broken", root=Path("/tmp/broken"), parse_error="bad")
        all_tasks = list(static_tasks) + [broken]
        start = time.monotonic()
        app = AAMAApp(initial_tasks=all_tasks)
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            elapsed = time.monotonic() - start
            assert elapsed < 2.0, f"first render took {elapsed:.2f}s (>2s budget)"
            # Screen must be DashboardScreen, not a crashed app
            assert isinstance(app.screen, DashboardScreen)

    asyncio.run(_run())


# -----------------------------------------------------------------------------
# SVG snapshots — pytest-textual-snapshot
# -----------------------------------------------------------------------------


def test_dashboard_svg_matches_golden(snap_compare) -> None:
    """SVG regression test of the DashboardScreen via a fixture app file."""
    assert snap_compare("snapshot_apps/dashboard_static.py")


def test_task_detail_svg_matches_golden(snap_compare) -> None:
    """SVG regression test of the TaskDetailScreen via a fixture app file."""
    assert snap_compare(
        "snapshot_apps/dashboard_static.py", press=["enter"]
    )
