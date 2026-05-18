"""TaskCard widget — one Task rendered as a kanban card.

Created in aa-ma-tui-tracker M3 Step 3.2 (2026-05-18).

Renders three lines:
    [bold]task_name[/bold]
    [status]
    X/Y steps · M/N ms

Counting logic delegates to Task.step_progress() / Task.milestone_progress()
so the snapshot renderer and the Textual widget share a single source of
truth (per L-005 mechanism-duplication rule).
"""

from __future__ import annotations

from textual.widgets import Static

from aa_ma.tui.model import Task


class TaskCard(Static):
    """A single Task displayed as a card inside a KanbanColumn."""

    def __init__(self, task: Task, **kwargs) -> None:
        # NOTE: stored as `task_data` not `task` — Textual's Widget reserves
        # the `task` attribute name for its Worker/@work integration.
        self.task_data = task
        super().__init__(self.format(), **kwargs)

    def format(self) -> str:
        """Return the card's text content (Rich markup).

        Pure — testable without mounting in an App. Three lines:
            bold name
            aggregate status
            X/Y steps · M/N ms
        """
        s_done, s_total = self.task_data.step_progress()
        m_done, m_total = self.task_data.milestone_progress()
        return (
            f"[bold]{self.task_data.name}[/bold]\n"
            f"[{self.task_data.aggregate_status.value}]\n"
            f"{s_done}/{s_total} steps · {m_done}/{m_total} ms"
        )
