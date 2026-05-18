"""Filesystem watcher — async refresh driver for the aa-ma-tui Textual app.

Created in aa-ma-tui-tracker M3 Steps 3.8 + 3.9 (2026-05-18).

Three public exports:
    AAMAFilter          — DefaultFilter subclass whitelisting 5 AA-MA suffixes
    reduce_watch_event  — pure reducer (state, changes) → (state', affected)
    watch_roots         — async driver wrapping watchfiles.awatch

Architecture validated in Step 3.1 prototype (PROTOTYPE PASS, see
provenance.log entry 2026-05-18T07:30:00). The driver is consumed by
`aa_ma.tui.app.AAMAApp` inside a @work(exclusive=True) task; the callback
mutates the App's reactive `tasks` list and calls `mutate_reactive(...)`.
"""

from __future__ import annotations

import asyncio
import inspect
import time
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from watchfiles import Change, DefaultFilter, awatch

from aa_ma.tui.parser import AAMA_FILE_SUFFIXES


# -----------------------------------------------------------------------------
# AAMAFilter — only AA-MA artifact files trigger the watcher
# -----------------------------------------------------------------------------


class AAMAFilter(DefaultFilter):
    """Whitelist filter — accepts only the canonical AA-MA artifact suffixes (see AAMA_FILE_SUFFIXES).

    Inherits DefaultFilter's noise suppression (.git, __pycache__, etc.) and
    adds a tail-suffix whitelist matching the AA-MA file-naming grammar
    (`{task}-{role}.{md|log}`). A bare `tasks.md` (no `-` prefix) is NOT
    accepted — it doesn't belong to a task. Suffix tuple is the canonical
    `aa_ma.tui.parser.AAMA_FILE_SUFFIXES` (single source of truth per L-005).
    """

    def __call__(self, change: Change, path: str) -> bool:
        if not super().__call__(change, path):
            return False
        return any(path.endswith(suf) for suf in AAMA_FILE_SUFFIXES)


# -----------------------------------------------------------------------------
# reduce_watch_event — pure reducer
# -----------------------------------------------------------------------------


def reduce_watch_event(
    state: dict[str, float],
    changes: set[tuple[Change, str]],
) -> tuple[dict[str, float], set[str]]:
    """Pure reducer: (state, batch) → (new_state, affected_task_names).

    state maps task-name → last-seen-mtime float; the affected set tells
    the caller which tasks to re-parse. Task-name extraction follows the
    AA-MA layout convention:
        .../dev/active/<task-name>/<task-name>-tasks.md
        ↓
        task_name = Path(path).parent.name

    Pure (no I/O); safe to call from anywhere.
    """
    affected: set[str] = set()
    now = time.time()
    for _change, path in changes:
        affected.add(Path(path).parent.name)
    new_state = {**state, **{name: now for name in affected}}
    return new_state, affected


# -----------------------------------------------------------------------------
# watch_roots — async driver wrapping awatch
# -----------------------------------------------------------------------------


_CallbackResult = None | Awaitable[None]
_Callback = Callable[[set[str]], _CallbackResult]


async def watch_roots(
    roots: list[Path],
    callback: _Callback,
    *,
    debounce: int = 300,
    stop_event: asyncio.Event | None = None,
) -> None:
    """Watch `roots` and invoke `callback(affected_task_names)` per batch.

    Wraps `watchfiles.awatch` with the AAMAFilter applied. Callback may be
    sync (returns None) or async (returns Awaitable). When `stop_event` is
    set, the loop exits cleanly on the next iteration.

    Designed to be consumed from a Textual @work(exclusive=True) task:

        @work(exclusive=True)
        async def watch_filesystem(self) -> None:
            async def cb(affected):
                for name in affected:
                    self._reload_task(name)
                self.mutate_reactive(AAMAApp.tasks)
            await watch_roots([self.root], cb, stop_event=self._stop_event)
    """
    state: dict[str, float] = {}
    kwargs: dict[str, Any] = {
        "debounce": debounce,
        "watch_filter": AAMAFilter(),
    }
    if stop_event is not None:
        kwargs["stop_event"] = stop_event

    async for changes in awatch(*roots, **kwargs):
        state, affected = reduce_watch_event(state, changes)
        if not affected:
            continue
        result = callback(affected)
        if inspect.isawaitable(result):
            await result
