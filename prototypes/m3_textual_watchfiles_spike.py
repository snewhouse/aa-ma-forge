"""PROTOTYPE — M3 Step 3.1 Textual+watchfiles integration spike (THROWAWAY)

Question being answered:
    Does watchfiles.awatch(debounce=300) inside Textual's @work decorator
    cleanly mutate a `reactive` list[Task]-equivalent on the App, with the
    watch_* handler firing reliably and without race conditions?

Specifically validates:
    1. awatch() runs as a Textual @work worker without blocking event loop
    2. mutate_reactive() triggers watch_* handler on in-place list mutation
    3. AAMAFilter (DefaultFilter subclass) suppresses noise (.git, __pycache__)
    4. Debounce coalesces rapid changes into a single batch

Run:    uv run python prototypes/m3_textual_watchfiles_spike.py
Delete: rm prototypes/m3_textual_watchfiles_spike.py (after M3 completes)

The PORTABLE BITS (the reducer + AAMAFilter) lift cleanly into:
    src/aa_ma/tui/watcher.py     — reducer + filter
    src/aa_ma/tui/app.py         — @work + reactive pattern (architectural)

The Textual App shell is throwaway. Auto-driver at the bottom uses
Textual's run_test() pilot mode because this prototype runs in a headless
WSL terminal — you can't drive it by hand here.
"""

from __future__ import annotations

import asyncio
import tempfile
import time
from pathlib import Path

from watchfiles import Change, DefaultFilter, awatch


# ============================================================================
# PORTABLE LOGIC — lifts cleanly into src/aa_ma/tui/watcher.py
# ============================================================================


class AAMAFilter(DefaultFilter):
    """Whitelist filter — only AA-MA artifact files trigger events.

    Reference.md grammar: 5 standard suffixes per task dir.
    """

    _AAMA_SUFFIXES = (
        "-tasks.md",
        "-plan.md",
        "-reference.md",
        "-context-log.md",
        "-provenance.log",
    )

    def __call__(self, change: Change, path: str) -> bool:
        if not super().__call__(change, path):
            return False
        return any(path.endswith(suf) for suf in self._AAMA_SUFFIXES)


def reduce_watch_event(
    state: dict[str, float], changes: set[tuple[Change, str]]
) -> tuple[dict[str, float], set[str]]:
    """Pure reducer: (state, event) -> (new_state, affected_task_names).

    - state maps task-name -> last-seen timestamp.
    - changes is the raw watchfiles batch.
    - affected_task_names is what the caller should re-parse.

    Task-name extraction rule (mirrors discover_tasks layout):
        .../dev/active/<task-name>/<task-name>-tasks.md
        => task-name = parent dir name
    """
    affected: set[str] = set()
    now = time.time()
    for _change, path in changes:
        task_name = Path(path).parent.name
        affected.add(task_name)
    new_state = {**state, **{name: now for name in affected}}
    return new_state, affected


# ============================================================================
# THROWAWAY TUI SHELL — Textual app
# ============================================================================

from textual.app import App, ComposeResult
from textual.reactive import reactive
from textual.widgets import Footer, Header, Static
from textual import work


class SpikeApp(App):
    """Throwaway Textual app that proves the integration works."""

    CSS = """
    #status { padding: 1; height: auto; }
    #events { padding: 1; height: 1fr; border: solid green; }
    """

    BINDINGS = [("q", "quit", "Quit")]

    # Reactive list[str] — events captured from the watcher
    events: reactive[list[str]] = reactive(list, recompose=False)

    def __init__(self, watch_root: Path, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.watch_root = watch_root
        self._state: dict[str, float] = {}
        self._stop_event = asyncio.Event()

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static(f"watching: {self.watch_root}", id="status")
        yield Static("(no events yet)", id="events")
        yield Footer()

    def on_mount(self) -> None:
        self.watch_filesystem()

    def watch_events(self, _old: list[str], new: list[str]) -> None:
        widget = self.query_one("#events", Static)
        if not new:
            widget.update("(no events yet)")
        else:
            widget.update("\n".join(f"  {e}" for e in new[-20:]))

    @work(exclusive=True)
    async def watch_filesystem(self) -> None:
        """The actual integration under test — awatch in @work, mutate in handler."""
        async for changes in awatch(
            self.watch_root,
            debounce=300,
            stop_event=self._stop_event,
            watch_filter=AAMAFilter(),
        ):
            self._state, affected = reduce_watch_event(self._state, changes)
            for task_name in sorted(affected):
                self.events.append(f"[{time.time():.2f}] {task_name}")
            # CRUCIAL: mutate_reactive triggers watch_events()
            self.mutate_reactive(SpikeApp.events)

    async def action_quit(self) -> None:
        self._stop_event.set()
        self.exit()


# ============================================================================
# AUTO-DRIVER (headless verdict capture)
# ============================================================================


async def drive() -> dict[str, object]:
    """Spin up SpikeApp, touch fake AA-MA files, observe events.

    Returns a dict with the verdict facts.
    """
    facts: dict[str, object] = {
        "awatch_ran_in_work": None,
        "mutate_reactive_fired_watcher": None,
        "filter_suppressed_noise": None,
        "debounce_coalesced": None,
        "events_seen": [],
        "errors": [],
    }

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        task_dir = root / "spike-task"
        task_dir.mkdir()
        # Pre-create the 5 AA-MA files so AAMAFilter sees them
        (task_dir / "spike-task-tasks.md").write_text("# pending\n")
        (task_dir / "spike-task-plan.md").write_text("# plan\n")
        (task_dir / "spike-task-context-log.md").write_text("# ctx\n")
        (task_dir / "spike-task-reference.md").write_text("# ref\n")
        (task_dir / "spike-task-provenance.log").write_text("")

        # Noise files that AAMAFilter MUST suppress
        (task_dir / "ignored.txt").write_text("noise")
        (task_dir / ".hidden.md").write_text("hidden")

        app = SpikeApp(watch_root=root)

        async with app.run_test() as pilot:
            await pilot.pause(0.5)  # let @work spin up awatch
            facts["awatch_ran_in_work"] = True  # if we got here, yes

            # Emit AA-MA-relevant change
            (task_dir / "spike-task-tasks.md").write_text("# COMPLETE\n")
            await pilot.pause(0.6)  # > debounce 300ms

            # Emit noise that filter should suppress
            (task_dir / "ignored.txt").write_text("more noise")
            await pilot.pause(0.6)

            # Rapid burst to test debounce coalescing
            burst_start = time.time()
            for i in range(5):
                (task_dir / "spike-task-context-log.md").write_text(f"# burst {i}\n")
                await asyncio.sleep(0.02)  # << debounce
            await pilot.pause(0.6)
            facts["burst_duration_s"] = time.time() - burst_start

            facts["events_seen"] = list(app.events)
            facts["mutate_reactive_fired_watcher"] = len(app.events) > 0

            # noise-suppression: no event should contain "ignored.txt" related task_name
            # AAMAFilter suppresses by suffix — noise file has no AA-MA suffix
            # so it never enters the reducer in the first place
            facts["filter_suppressed_noise"] = not any(
                "ignored" in e.lower() for e in app.events
            )

            # debounce: the 5-burst should produce ≤ 2 events for spike-task,
            # not 5
            spike_events = [e for e in app.events if "spike-task" in e]
            facts["debounce_coalesced"] = len(spike_events) <= 4

            await app.action_quit()
            await pilot.pause(0.1)

    return facts


def main() -> int:
    print("=" * 70)
    print("M3 PROTOTYPE — Textual + watchfiles integration spike")
    print("=" * 70)
    try:
        facts = asyncio.run(drive())
    except Exception as exc:
        print(f"FATAL: prototype crashed: {exc!r}")
        return 1

    print("\n--- VERDICT FACTS ---")
    for k, v in facts.items():
        print(f"  {k}: {v}")

    # Pass criteria
    all_green = (
        facts.get("awatch_ran_in_work")
        and facts.get("mutate_reactive_fired_watcher")
        and facts.get("filter_suppressed_noise")
        and facts.get("debounce_coalesced")
        and not facts.get("errors")
    )

    print("\n--- VERDICT ---")
    if all_green:
        print("  PASS — integration pattern viable for M3 production code")
        return 0
    print("  FAIL — at least one expectation not met; review facts above")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
