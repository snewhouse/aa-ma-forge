"""Tests for src/aa_ma/tui/screens/task_detail.py — M3 Step 3.6/3.7.

TaskDetailScreen compose layout:
    [detail-header]   bold task name + aggregate status
    [Horizontal]
        [milestone-tree]   Tree of milestones → steps
        [result-log-preview]   Static showing selected step's result_log
    [prov-tail]   joined provenance_tail
"""

from __future__ import annotations

import asyncio

from textual.app import App
from textual.containers import Horizontal
from textual.widgets import Static, Tree

from aa_ma.tui.screens.task_detail import TaskDetailScreen


# -----------------------------------------------------------------------------
# Construction & compose structure
# -----------------------------------------------------------------------------


def test_task_detail_stores_task(static_tasks) -> None:
    screen = TaskDetailScreen(static_tasks[1])  # beta-task
    assert screen.detail_task is static_tasks[1]


def test_task_detail_compose_yields_header_horizontal_provtail(static_tasks) -> None:
    """compose() yields detail-header, a Horizontal body, and prov-tail."""
    screen = TaskDetailScreen(static_tasks[0])
    widgets = list(screen.compose())
    # Find by id
    by_id = {getattr(w, "id", None): w for w in widgets}
    assert "detail-header" in by_id
    assert "prov-tail" in by_id
    # The horizontal body wraps tree + preview
    horizontals = [w for w in widgets if isinstance(w, Horizontal)]
    assert len(horizontals) == 1


def test_task_detail_header_includes_name_and_status(static_tasks) -> None:
    screen = TaskDetailScreen(static_tasks[1])  # beta IN_PROGRESS
    header = next(w for w in screen.compose() if getattr(w, "id", None) == "detail-header")
    rendered = str(header.renderable)
    assert "beta-task" in rendered
    assert "IN_PROGRESS" in rendered


def test_task_detail_tree_contains_milestones_and_steps(static_tasks) -> None:
    """Tree widget has one node per milestone, each with step leaves."""
    screen = TaskDetailScreen(static_tasks[0])  # alpha — 2 ms, 4 steps total
    horizontal = next(w for w in screen.compose() if isinstance(w, Horizontal))
    trees = [c for c in horizontal._pending_children if isinstance(c, Tree)]
    assert len(trees) == 1
    tree = trees[0]
    # Root has 2 milestone children
    assert len(tree.root.children) == 2
    # Total leaves = 4 steps
    total_leaves = sum(len(ms_node.children) for ms_node in tree.root.children)
    assert total_leaves == 4


def test_task_detail_result_log_preview_default_placeholder(static_tasks) -> None:
    screen = TaskDetailScreen(static_tasks[0])
    horizontal = next(w for w in screen.compose() if isinstance(w, Horizontal))
    preview = next(
        c for c in horizontal._pending_children if getattr(c, "id", None) == "result-log-preview"
    )
    assert "select a step" in str(preview.renderable).lower()


def test_task_detail_prov_tail_joins_lines(static_tasks) -> None:
    screen = TaskDetailScreen(static_tasks[0])  # alpha has 3 prov entries
    prov = next(w for w in screen.compose() if getattr(w, "id", None) == "prov-tail")
    rendered = str(prov.renderable)
    # All 3 alpha provenance lines present
    assert "alpha M1 COMPLETE" in rendered
    assert "alpha M2 COMPLETE" in rendered
    assert "alpha SHIPPED" in rendered


def test_task_detail_prov_tail_empty_shows_placeholder() -> None:
    """Tasks with no provenance entries show a (no entries) placeholder."""
    from pathlib import Path

    from aa_ma.tui.model import Task

    t = Task(name="x", root=Path("/tmp/x"))
    screen = TaskDetailScreen(t)
    prov = next(w for w in screen.compose() if getattr(w, "id", None) == "prov-tail")
    assert "no" in str(prov.renderable).lower()


# -----------------------------------------------------------------------------
# Pilot integration: mounts cleanly
# -----------------------------------------------------------------------------


def test_task_detail_mounts_via_pilot(static_tasks) -> None:
    """Sanity check that TaskDetailScreen mounts without errors in a real App."""

    async def _run() -> None:
        class _MinApp(App):
            def on_mount(self) -> None:
                self.push_screen(TaskDetailScreen(static_tasks[1]))

        app = _MinApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            assert isinstance(app.screen, TaskDetailScreen)
            # query_one finds widgets by id post-mount
            assert app.screen.query_one("#detail-header", Static) is not None
            assert app.screen.query_one("#result-log-preview", Static) is not None
            assert app.screen.query_one("#prov-tail", Static) is not None

    asyncio.run(_run())
