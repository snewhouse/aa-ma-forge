"""Tests for src/aa_ma/tui/widgets/kanban_column.py — M3 Step 3.3.

KanbanColumn(VerticalScroll) groups TaskCards by aggregate_status. One
column per non-ERROR AggregateStatus value (the M2 _BOARD_COLUMNS tuple).
"""

from __future__ import annotations

from pathlib import Path

from aa_ma.tui.model import AggregateStatus, Task
from aa_ma.tui.widgets.kanban_column import KanbanColumn


def test_kanban_column_stores_status_and_tasks(static_tasks) -> None:
    col = KanbanColumn(AggregateStatus.COMPLETE, static_tasks)
    assert col.column_status is AggregateStatus.COMPLETE
    # `column_tasks` exposes the FILTERED list, not the input list.
    assert all(t.aggregate_status is AggregateStatus.COMPLETE for t in col.column_tasks)


def test_kanban_column_filters_to_matching_status(static_tasks) -> None:
    # static_tasks: alpha COMPLETE, beta IN_PROGRESS, gamma BLOCKED
    complete = KanbanColumn(AggregateStatus.COMPLETE, static_tasks)
    assert [t.name for t in complete.column_tasks] == ["alpha-task"]

    in_progress = KanbanColumn(AggregateStatus.IN_PROGRESS, static_tasks)
    assert [t.name for t in in_progress.column_tasks] == ["beta-task"]

    blocked = KanbanColumn(AggregateStatus.BLOCKED, static_tasks)
    assert [t.name for t in blocked.column_tasks] == ["gamma-task"]

    pending = KanbanColumn(AggregateStatus.PENDING, static_tasks)
    assert pending.column_tasks == []


def test_kanban_column_header_includes_status_and_count(static_tasks) -> None:
    col_complete = KanbanColumn(AggregateStatus.COMPLETE, static_tasks)
    header = col_complete.header_text()
    assert "COMPLETE" in header
    assert "1" in header  # one task matches

    col_pending = KanbanColumn(AggregateStatus.PENDING, static_tasks)
    header = col_pending.header_text()
    assert "PENDING" in header
    assert "0" in header  # zero tasks match


def test_kanban_column_drops_error_status_silently() -> None:
    """ERROR tasks never appear in any board column (per M2 board convention)."""
    error_task = Task(
        name="broken", root=Path("/tmp/broken"), parse_error="syntax fail"
    )
    # Build a column for every non-ERROR status — none should contain the broken task.
    for status in (
        AggregateStatus.PENDING,
        AggregateStatus.IN_PROGRESS,
        AggregateStatus.BLOCKED,
        AggregateStatus.COMPLETE,
    ):
        col = KanbanColumn(status, [error_task])
        assert error_task not in col.column_tasks


def test_kanban_column_is_vertical_scroll_subclass() -> None:
    from textual.containers import VerticalScroll

    assert issubclass(KanbanColumn, VerticalScroll)


def test_kanban_column_compose_yields_taskcards(static_tasks) -> None:
    """compose() yields a TaskCard per filtered task. Verifies wiring without mounting."""
    from aa_ma.tui.widgets.task_card import TaskCard

    col = KanbanColumn(AggregateStatus.COMPLETE, static_tasks)
    yielded = list(col.compose())
    # 1 task matches COMPLETE → 1 TaskCard
    cards = [w for w in yielded if isinstance(w, TaskCard)]
    assert len(cards) == 1
    assert cards[0].task_data.name == "alpha-task"


def test_kanban_column_compose_empty_yields_placeholder(static_tasks) -> None:
    """Empty column compose() yields at least one widget (placeholder), no TaskCards."""
    from aa_ma.tui.widgets.task_card import TaskCard

    col = KanbanColumn(AggregateStatus.PENDING, static_tasks)
    yielded = list(col.compose())
    assert len(yielded) >= 1
    assert not any(isinstance(w, TaskCard) for w in yielded)
