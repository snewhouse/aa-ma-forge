"""KanbanColumn widget — vertical column of TaskCards grouped by status.

Created in aa-ma-tui-tracker M3 Step 3.3 (2026-05-18).

One column per non-ERROR AggregateStatus (PENDING / IN_PROGRESS / BLOCKED /
COMPLETE). ERROR-status tasks are dropped silently — they are surfaced by
the DashboardScreen as separate PARSE_ERROR badges (M3 Step 3.4 territory).
"""

from __future__ import annotations

from collections.abc import Iterable

from textual.app import ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Label

from aa_ma.tui.model import AggregateStatus, Task
from aa_ma.tui.widgets.task_card import TaskCard


class KanbanColumn(VerticalScroll):
    """A scrollable column of TaskCards filtered by aggregate_status."""

    def __init__(
        self,
        column_status: AggregateStatus,
        tasks: Iterable[Task],
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.column_status = column_status
        self.column_tasks: list[Task] = [
            t for t in tasks if t.aggregate_status == column_status
        ]

    def header_text(self) -> str:
        """Return the column header text — `STATUS (N)`."""
        return f"{self.column_status.value} ({len(self.column_tasks)})"

    def compose(self) -> ComposeResult:
        yield Label(f"[bold]{self.header_text()}[/bold]")
        if not self.column_tasks:
            yield Label("[dim](no tasks)[/dim]")
            return
        for task in self.column_tasks:
            yield TaskCard(task)
