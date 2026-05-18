"""Rich-rendered snapshot modes for aa-ma-tui.

Created in aa-ma-tui-tracker M2 (2026-05-18).

Three render functions:
    - render_board(tasks)   — 4-column kanban grouped by AggregateStatus
    - render_tree(task)     — single-task milestones-and-steps tree
    - render_summary(tasks) — one line per task

All return a `str` (terminal text). All pin `Console(width=120, record=True)`
so output is reproducible across hosts (per M2 plan risk #1 mitigation).

L-052 dual-formatter rule: this module imports `discover_tasks` from
`aa_ma.tui.parser` (rather than wrapping it). The matching CLI entrypoint
in __main__ and the JSON formatter MUST use the same symbol so any future
parser change propagates to all 4 modes uniformly. Verified by
`test_render_board_reuses_parser_discover_tasks`.
"""

from __future__ import annotations

import io

from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree

from aa_ma.tui.model import AggregateStatus, Task

# Re-export so consumers can import the canonical discovery function from any
# rendering module (per L-052 dual-formatter rule).
from aa_ma.tui.parser import discover_tasks  # noqa: F401

_RENDER_WIDTH = 120

# Fixed column order — matches plan acceptance criterion #1.
_BOARD_COLUMNS: tuple[AggregateStatus, ...] = (
    AggregateStatus.PENDING,
    AggregateStatus.IN_PROGRESS,
    AggregateStatus.BLOCKED,
    AggregateStatus.COMPLETE,
)


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


def _task_card(task: Task) -> str:
    """One-line task summary used inside board columns."""
    n_milestones = len(task.milestones)
    complete_milestones = sum(
        1 for m in task.milestones if m.status.value == "COMPLETE"
    )
    total_steps = sum(len(m.steps) for m in task.milestones)
    complete_steps = sum(
        1 for m in task.milestones for s in m.steps if s.status.value == "COMPLETE"
    )
    return (
        f"[bold]{task.name}[/bold]\n"
        f"{complete_steps}/{total_steps} steps · "
        f"{complete_milestones}/{n_milestones} ms"
    )


def _group_by_aggregate(tasks: list[Task]) -> dict[AggregateStatus, list[Task]]:
    """Bucket tasks by aggregate_status (preserves input order within bucket)."""
    buckets: dict[AggregateStatus, list[Task]] = {
        status: [] for status in _BOARD_COLUMNS
    }
    for task in tasks:
        if task.aggregate_status in buckets:
            buckets[task.aggregate_status].append(task)
        # ERROR-status tasks are dropped from board view; surfaced separately
        # in the TUI as PARSE_ERROR badges (M3 territory).
    return buckets


# -----------------------------------------------------------------------------
# Render functions
# -----------------------------------------------------------------------------


_RESULT_LOG_PREVIEW_CHARS = 60


def _step_progress(task: Task) -> tuple[int, int]:
    """Return (completed_steps, total_steps) across all milestones."""
    total = sum(len(m.steps) for m in task.milestones)
    complete = sum(
        1 for m in task.milestones for s in m.steps if s.status.value == "COMPLETE"
    )
    return complete, total


def _milestone_progress(task: Task) -> tuple[int, int]:
    """Return (completed_milestones, total_milestones)."""
    total = len(task.milestones)
    complete = sum(1 for m in task.milestones if m.status.value == "COMPLETE")
    return complete, total


def render_summary(tasks: list[Task]) -> str:
    """One line per task: `NAME  [status]  X/Y steps  M/N ms  · last update`."""
    console = Console(width=_RENDER_WIDTH, record=True, file=io.StringIO())
    for task in tasks:
        s_done, s_total = _step_progress(task)
        m_done, m_total = _milestone_progress(task)
        last = task.last_modified.date().isoformat() if task.last_modified else "—"
        console.print(
            f"{task.name}  [{task.aggregate_status.value}]  "
            f"{s_done}/{s_total} steps  {m_done}/{m_total} ms  · {last}"
        )
    return console.export_text()


def render_tree(task: Task) -> str:
    """Render a single task as a Rich Tree of milestones → steps.

    Each milestone shows title + status. Each step shows number, title,
    status, and the first _RESULT_LOG_PREVIEW_CHARS chars of its Result
    Log (if any).
    """
    tree = Tree(f"[bold]{task.name}[/bold] ({task.aggregate_status.value})")
    for milestone in task.milestones:
        m_branch = tree.add(
            f"M{milestone.number}: {milestone.title} [{milestone.status.value}]"
        )
        for step in milestone.steps:
            preview = ""
            if step.result_log:
                preview = step.result_log[:_RESULT_LOG_PREVIEW_CHARS]
                if len(step.result_log) > _RESULT_LOG_PREVIEW_CHARS:
                    preview += "…"
            label = f"{step.number} {step.title} [{step.status.value}]"
            if preview:
                label = f"{label} — {preview}"
            m_branch.add(label)

    console = Console(width=_RENDER_WIDTH, record=True, file=io.StringIO())
    console.print(tree)
    return console.export_text()


def render_board(tasks: list[Task]) -> str:
    """Render a 4-column Rich kanban grouped by AggregateStatus.

    Empty buckets render the column header with no body lines, matching the
    "no tasks" UX in the plan.
    """
    buckets = _group_by_aggregate(tasks)
    panels = []
    for status in _BOARD_COLUMNS:
        body_tasks = buckets[status]
        if body_tasks:
            body = "\n\n".join(_task_card(t) for t in body_tasks)
        else:
            body = "[dim](no tasks)[/dim]"
        panels.append(
            Panel(body, title=status.value, expand=True, width=_RENDER_WIDTH // 4)
        )

    console = Console(width=_RENDER_WIDTH, record=True, file=io.StringIO())
    console.print(Columns(panels, equal=True, expand=True))
    return console.export_text()
