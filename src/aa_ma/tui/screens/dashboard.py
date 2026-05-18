"""DashboardScreen — 4-column kanban (the landing screen).

Created in aa-ma-tui-tracker M3 Step 3.4 (2026-05-18).

Composes one KanbanColumn per non-ERROR AggregateStatus, in canonical
order (PENDING → IN_PROGRESS → BLOCKED → COMPLETE). Source of canonical
order: `aa_ma.tui.snapshot.BOARD_COLUMNS` (shared with snapshot.render_board
per L-005 mechanism-duplication rule).

ERROR-status tasks are NOT shown as kanban cards (per M2 board convention);
they will surface as PARSE_ERROR badges in M3 Step 3.6+ (TaskDetailScreen)
or as a separate footer indicator (M5 polish).
"""

from __future__ import annotations

from collections.abc import Iterable

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.screen import Screen

from aa_ma.tui.model import Task
from aa_ma.tui.snapshot import BOARD_COLUMNS
from aa_ma.tui.widgets.kanban_column import KanbanColumn


class DashboardScreen(Screen):
    """Top-level kanban screen. Reactive `dashboard_tasks` drives column refresh.

    Key bindings:
        enter → drill in to TaskDetailScreen for `current_task`
    """

    BINDINGS = [
        Binding("enter", "drill_in", "Open task", priority=True),
    ]

    def __init__(self, tasks: Iterable[Task], **kwargs) -> None:
        super().__init__(**kwargs)
        # Materialise once at construction; M3 Step 3.5+ wires reactive refresh.
        self.dashboard_tasks: list[Task] = list(tasks)
        # `current_task` is the selection target for the Enter binding. M3
        # Step 3.7 will replace this default with arrow-key navigation that
        # updates `current_task` as the user moves through cards.
        self.current_task: Task | None = (
            self.dashboard_tasks[0] if self.dashboard_tasks else None
        )

    def compose(self) -> ComposeResult:
        yield Horizontal(
            *(KanbanColumn(status, self.dashboard_tasks) for status in BOARD_COLUMNS)
        )

    def action_drill_in(self) -> None:
        """Push TaskDetailScreen for the currently-selected task (noop if empty)."""
        if self.current_task is None:
            return
        # Local import avoids dashboard ↔ task_detail circular at module load.
        from aa_ma.tui.screens.task_detail import TaskDetailScreen

        self.app.push_screen(TaskDetailScreen(self.current_task))
