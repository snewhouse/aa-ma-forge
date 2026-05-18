"""AAMAApp — top-level Textual orchestration for aa-ma-tui.

Created in aa-ma-tui-tracker M3 Step 3.10 (2026-05-18).

Composes:
    DashboardScreen   — landing screen pushed on_mount
    watch_filesystem  — @work background task driving live refresh
                        (only when watch_roots are provided)

Architecture validated in Step 3.1 prototype (PROTOTYPE PASS, see
provenance.log 2026-05-18T07:30:00).
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from textual import work
from textual.app import App

from aa_ma.tui.model import ParseError, Task
from aa_ma.tui.parser import parse_task_dir
from aa_ma.tui.screens.dashboard import DashboardScreen
from aa_ma.tui.watcher import watch_roots

logger = logging.getLogger(__name__)


class AAMAApp(App):
    """Top-level aa-ma-tui App.

    Constructor parameters:
        initial_tasks  — list of Task to seed the dashboard with
        watch_roots    — list of Path; if non-empty, a @work watcher refreshes
                         affected tasks via watcher.watch_roots(). If empty,
                         the app runs in static mode (suitable for tests).

    `tracker_tasks` is the live task list (plain attribute, not reactive).
    Reactive list-mutation patterns are deferred to M5 polish; M3 uses
    pop+push for screen refresh which is sufficient for v0.10.
    """

    CSS = """
    DashboardScreen { layout: vertical; }
    KanbanColumn { width: 1fr; border: solid $primary; padding: 1; }
    """

    def __init__(
        self,
        *,
        initial_tasks: list[Task] | None = None,
        watch_roots: list[Path] | None = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.tracker_tasks: list[Task] = list(initial_tasks or [])
        self.watch_roots_value: list[Path] = list(watch_roots or [])
        self._stop_event = asyncio.Event()

    def on_mount(self) -> None:
        self.push_screen(DashboardScreen(self.tracker_tasks))
        if self.watch_roots_value:
            self.watch_filesystem()  # @work — fire and forget

    @work(exclusive=True)
    async def watch_filesystem(self) -> None:
        """Background watcher — refreshes tracker_tasks on AA-MA file changes."""

        async def cb(affected: set[str]) -> None:
            await self._reload_tasks(affected)

        try:
            await watch_roots(
                self.watch_roots_value,
                cb,
                stop_event=self._stop_event,
                debounce=300,
            )
        except Exception:  # pragma: no cover  (defensive — surface via log only)
            logger.exception("watch_filesystem crashed")

    async def _reload_tasks(self, affected: set[str]) -> None:
        """Re-parse `affected` tasks from disk and refresh the dashboard."""
        new_state: list[Task] = list(self.tracker_tasks)
        by_name = {t.name: i for i, t in enumerate(new_state)}
        for name in affected:
            task = self._find_and_parse_task(name)
            if task is None:
                continue
            if name in by_name:
                new_state[by_name[name]] = task
            else:
                new_state.append(task)
        self.tracker_tasks = new_state
        # Refresh the dashboard screen (M5 polish will swap this for reactive)
        if isinstance(self.screen, DashboardScreen):
            self.pop_screen()
            self.push_screen(DashboardScreen(self.tracker_tasks))

    def _find_and_parse_task(self, name: str) -> Task | None:
        """Locate <name>/ under any watch_root and parse it; ERROR-wrap on fail."""
        for root in self.watch_roots_value:
            candidate = root / name
            if not (candidate / f"{name}-tasks.md").exists():
                continue
            try:
                return parse_task_dir(candidate)
            except ParseError as exc:
                return Task(name=name, root=candidate, parse_error=str(exc))
        return None

    async def action_quit(self) -> None:
        self._stop_event.set()
        self.exit()
