"""Tests for src/aa_ma/tui/watcher.py — M3 Steps 3.8 + 3.9.

watcher.py contains:
  - AAMAFilter(DefaultFilter)  — whitelists canonical AA-MA suffixes (see AAMA_FILE_SUFFIXES)
  - reduce_watch_event(state, changes) → (new_state, affected_task_names)
  - async watch_roots(roots, callback, *, debounce, stop_event) — driver

The reducer pattern + filter were validated empirically in M3 Step 3.1
prototype (PROTOTYPE PASS entry in provenance.log).
"""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from watchfiles import Change

from aa_ma.tui.watcher import AAMAFilter, reduce_watch_event, watch_roots

# Live awatch timing constants — single source of truth (§6.8 W3 fix).
# WSL2 inotify needs ≥1s to register subdir watches (empirically validated
# 2026-05-18; works at root immediately, fails at 0.3s for subdirs).
_WSL_INOTIFY_SETTLE_S = 1.5
# Pause after a file modification, long enough to clear `_TEST_DEBOUNCE_MS`
# and let the callback fire.
_DEBOUNCE_DRAIN_S = 0.8
# Debounce window for the tests (smaller than production 300ms for speed).
_TEST_DEBOUNCE_MS = 200


# =============================================================================
# Step 3.9 — AAMAFilter
# =============================================================================


def test_aama_filter_accepts_tasks_md() -> None:
    f = AAMAFilter()
    assert f(Change.modified, "/x/foo-tasks.md") is True


def test_aama_filter_accepts_all_5_canonical_suffixes() -> None:
    f = AAMAFilter()
    for suf in (
        "-tasks.md",
        "-plan.md",
        "-reference.md",
        "-context-log.md",
        "-provenance.log",
    ):
        assert f(Change.modified, f"/x/foo{suf}") is True, f"rejected {suf}"


def test_aama_filter_rejects_unrelated_extension() -> None:
    f = AAMAFilter()
    assert f(Change.modified, "/x/foo.txt") is False
    assert f(Change.modified, "/x/foo.json") is False


def test_aama_filter_rejects_aama_file_without_dash_prefix() -> None:
    """A file literally named `tasks.md` (no `-tasks.md` suffix) is NOT AA-MA."""
    f = AAMAFilter()
    assert f(Change.modified, "/x/tasks.md") is False


def test_aama_filter_inherits_default_noise_suppression() -> None:
    """DefaultFilter rejects __pycache__ / .git — AAMAFilter inherits that."""
    f = AAMAFilter()
    assert f(Change.modified, "/x/__pycache__/foo-tasks.md") is False
    assert f(Change.modified, "/x/.git/foo-tasks.md") is False


# =============================================================================
# Step 3.8 — reduce_watch_event
# =============================================================================


def test_reduce_watch_event_extracts_task_name_from_parent_dir() -> None:
    state: dict[str, float] = {}
    changes = {(Change.modified, "/dev/active/spike-task/spike-task-tasks.md")}
    new_state, affected = reduce_watch_event(state, changes)
    assert affected == {"spike-task"}
    assert "spike-task" in new_state


def test_reduce_watch_event_coalesces_multiple_files_per_task() -> None:
    """Two files in same task dir → one affected entry."""
    changes = {
        (Change.modified, "/x/foo-task/foo-task-tasks.md"),
        (Change.modified, "/x/foo-task/foo-task-context-log.md"),
    }
    _, affected = reduce_watch_event({}, changes)
    assert affected == {"foo-task"}


def test_reduce_watch_event_distinguishes_different_tasks() -> None:
    changes = {
        (Change.modified, "/x/a/a-tasks.md"),
        (Change.modified, "/x/b/b-tasks.md"),
    }
    _, affected = reduce_watch_event({}, changes)
    assert affected == {"a", "b"}


def test_reduce_watch_event_empty_batch_returns_empty() -> None:
    new_state, affected = reduce_watch_event({"foo": 1.0}, set())
    assert affected == set()
    assert new_state == {"foo": 1.0}  # state unchanged


def test_reduce_watch_event_preserves_existing_state_entries() -> None:
    state = {"old-task": 100.0}
    changes = {(Change.modified, "/x/new-task/new-task-tasks.md")}
    new_state, _ = reduce_watch_event(state, changes)
    assert "old-task" in new_state
    assert "new-task" in new_state


# =============================================================================
# Step 3.8 — watch_roots driver (live awatch)
# =============================================================================


def test_watch_roots_fires_callback_on_file_change() -> None:
    """End-to-end: touch a file inside watched root → callback fires with task name."""

    async def _run() -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            task_dir = root / "spike"
            task_dir.mkdir()
            (task_dir / "spike-tasks.md").write_text("# initial\n")

            received: list[set[str]] = []
            stop = asyncio.Event()

            async def cb(affected: set[str]) -> None:
                received.append(affected)
                # First non-empty batch is enough — stop the watcher.
                if affected:
                    stop.set()

            # Launch watcher
            watcher_task = asyncio.create_task(
                watch_roots([root], cb, debounce=_TEST_DEBOUNCE_MS, stop_event=stop)
            )
            await asyncio.sleep(_WSL_INOTIFY_SETTLE_S)

            # Modify the watched file
            (task_dir / "spike-tasks.md").write_text("# COMPLETE\n")

            # Wait for callback or timeout (5s safety net)
            await asyncio.wait_for(watcher_task, timeout=5.0)

            assert any("spike" in batch for batch in received), received

    asyncio.run(_run())


def test_watch_roots_ignores_non_aama_files() -> None:
    """Touching a non-AA-MA file does NOT fire the callback (AAMAFilter applied)."""

    async def _run() -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            task_dir = root / "spike"
            task_dir.mkdir()
            (task_dir / "spike-tasks.md").write_text("# init\n")
            (task_dir / "noise.txt").write_text("noise")

            received: list[set[str]] = []
            stop = asyncio.Event()

            async def cb(affected: set[str]) -> None:
                received.append(affected)

            watcher_task = asyncio.create_task(
                watch_roots([root], cb, debounce=_TEST_DEBOUNCE_MS, stop_event=stop)
            )
            await asyncio.sleep(_WSL_INOTIFY_SETTLE_S)

            # Touch only the noise file
            (task_dir / "noise.txt").write_text("more noise")
            await asyncio.sleep(_DEBOUNCE_DRAIN_S)  # well past debounce

            # Stop watcher
            stop.set()
            try:
                await asyncio.wait_for(watcher_task, timeout=2.0)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                watcher_task.cancel()

            # No callback should have fired since AAMAFilter dropped the noise
            assert received == [] or all(b == set() for b in received), received

    asyncio.run(_run())


def test_watch_roots_accepts_sync_callback() -> None:
    """Callback may be a plain function (no coroutine wrapping)."""

    async def _run() -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            task_dir = root / "alpha"
            task_dir.mkdir()
            (task_dir / "alpha-tasks.md").write_text("# init\n")

            received: list[set[str]] = []
            stop = asyncio.Event()

            def sync_cb(affected: set[str]) -> None:
                received.append(affected)
                if affected:
                    stop.set()

            watcher_task = asyncio.create_task(
                watch_roots([root], sync_cb, debounce=_TEST_DEBOUNCE_MS, stop_event=stop)
            )
            await asyncio.sleep(_WSL_INOTIFY_SETTLE_S)

            (task_dir / "alpha-tasks.md").write_text("# changed\n")
            await asyncio.wait_for(watcher_task, timeout=5.0)

            assert any("alpha" in b for b in received)

    asyncio.run(_run())
