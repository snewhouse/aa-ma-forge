"""Textual screens for the aa-ma-tui interactive app (M3).

Public surface:
    DashboardScreen     — 4-column kanban (default landing screen)
    TaskDetailScreen    — single-task drill-in view
"""

from __future__ import annotations

from aa_ma.tui.screens.dashboard import DashboardScreen
from aa_ma.tui.screens.task_detail import TaskDetailScreen

__all__ = ["DashboardScreen", "TaskDetailScreen"]
