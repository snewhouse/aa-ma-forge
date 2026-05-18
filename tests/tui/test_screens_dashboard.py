"""Tests for src/aa_ma/tui/screens/dashboard.py — M3 Step 3.4.

DashboardScreen composes 4 KanbanColumns in canonical order:
    PENDING → IN_PROGRESS → BLOCKED → COMPLETE.
"""

from __future__ import annotations

from aa_ma.tui.model import AggregateStatus
from aa_ma.tui.screens.dashboard import DashboardScreen
from aa_ma.tui.widgets.kanban_column import KanbanColumn


def _columns_from_compose(screen: DashboardScreen) -> list[KanbanColumn]:
    """Walk compose() output, returning the KanbanColumns in yield order.

    Handles two compose shapes: direct yield of KanbanColumns, or yield of
    a wrapper container whose constructor children are KanbanColumns.
    Pre-mount, Textual stores ctor children in `_pending_children`
    (`._nodes` / `.children` are empty until on_mount).
    """
    columns: list[KanbanColumn] = []
    for widget in screen.compose():
        if isinstance(widget, KanbanColumn):
            columns.append(widget)
        else:
            for child in getattr(widget, "_pending_children", None) or []:
                if isinstance(child, KanbanColumn):
                    columns.append(child)
    return columns


def test_dashboard_screen_compose_yields_4_columns(static_tasks) -> None:
    screen = DashboardScreen(static_tasks)
    columns = _columns_from_compose(screen)
    assert len(columns) == 4


def test_dashboard_screen_columns_in_canonical_order(static_tasks) -> None:
    screen = DashboardScreen(static_tasks)
    columns = _columns_from_compose(screen)
    statuses = [c.column_status for c in columns]
    assert statuses == [
        AggregateStatus.PENDING,
        AggregateStatus.IN_PROGRESS,
        AggregateStatus.BLOCKED,
        AggregateStatus.COMPLETE,
    ]


def test_dashboard_screen_distributes_tasks_by_status(static_tasks) -> None:
    """alpha → COMPLETE, beta → IN_PROGRESS, gamma → BLOCKED, PENDING empty."""
    screen = DashboardScreen(static_tasks)
    by_status = {c.column_status: c for c in _columns_from_compose(screen)}
    assert [t.name for t in by_status[AggregateStatus.COMPLETE].column_tasks] == ["alpha-task"]
    assert [t.name for t in by_status[AggregateStatus.IN_PROGRESS].column_tasks] == ["beta-task"]
    assert [t.name for t in by_status[AggregateStatus.BLOCKED].column_tasks] == ["gamma-task"]
    assert by_status[AggregateStatus.PENDING].column_tasks == []


def test_dashboard_screen_stores_input_tasks(static_tasks) -> None:
    screen = DashboardScreen(static_tasks)
    assert screen.dashboard_tasks == static_tasks


def test_dashboard_screen_is_screen_subclass() -> None:
    from textual.screen import Screen

    assert issubclass(DashboardScreen, Screen)


def test_dashboard_current_task_defaults_to_first_task(static_tasks) -> None:
    """`current_task` is set at construction — needed by Enter binding."""
    screen = DashboardScreen(static_tasks)
    assert screen.current_task is static_tasks[0]


def test_dashboard_current_task_is_none_when_empty() -> None:
    """No tasks → current_task is None (action_drill_in must noop)."""
    screen = DashboardScreen([])
    assert screen.current_task is None


def test_dashboard_has_enter_binding() -> None:
    """Enter key bound to drill_in action."""
    keys = [b.key for b in DashboardScreen.BINDINGS]
    assert "enter" in keys


def test_dashboard_enter_pushes_task_detail(static_tasks) -> None:
    """Pilot test — pressing Enter from DashboardScreen pushes TaskDetailScreen."""
    import asyncio

    from textual.app import App

    from aa_ma.tui.screens.task_detail import TaskDetailScreen

    async def _run() -> None:
        class _MinApp(App):
            def on_mount(self) -> None:
                self.push_screen(DashboardScreen(static_tasks))

        app = _MinApp()
        async with app.run_test() as pilot:
            await pilot.pause()
            assert isinstance(app.screen, DashboardScreen)
            await pilot.press("enter")
            await pilot.pause()
            assert isinstance(app.screen, TaskDetailScreen)
            assert app.screen.detail_task is static_tasks[0]

    asyncio.run(_run())


def test_board_columns_is_public_and_canonical() -> None:
    """BOARD_COLUMNS is a public constant promoted from M2 _BOARD_COLUMNS.

    DashboardScreen and snapshot.py share this canonical 4-tuple — single
    source of truth for the board's column order.
    """
    from aa_ma.tui.snapshot import BOARD_COLUMNS

    assert BOARD_COLUMNS == (
        AggregateStatus.PENDING,
        AggregateStatus.IN_PROGRESS,
        AggregateStatus.BLOCKED,
        AggregateStatus.COMPLETE,
    )
