"""Textual widgets for the aa-ma-tui interactive app (M3).

Public surface:
    TaskCard        — single-task card for kanban columns
    KanbanColumn    — VerticalScroll grouping TaskCards by aggregate_status
"""

from __future__ import annotations

from aa_ma.tui.widgets.task_card import TaskCard

__all__ = ["TaskCard"]
