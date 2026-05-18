# 0007. `aa-ma-tui` — Read-Only Textual TUI + Rich Snapshot for AA-MA Task Tracking

**Status:** Implemented
**Date:** 2026-05-18
**Deciders:** Stephen Newhouse + AI
**Tags:** `tui`, `read-only`, `release`, `textual`, `watchfiles`

## Context and Problem Statement

`/aa-ma-plan` + `/execute-aa-ma-milestone` accumulate active tasks under
`.claude/dev/active/`. Each task is a 5-file directory (plan / reference /
context-log / tasks / provenance). When the portfolio grows past 2–3 active
tasks the only way to scan *what is blocked, what is in progress, what
milestone is next* is to open every `*-tasks.md` by hand. The
session-start briefing inspects only the current working directory, so the
global picture stays invisible — exactly the operational gap AA-MA's
"sub-step sync rule" (L-080–L-082) is meant to expose.

**Question:** How do we surface AA-MA portfolio state — kanban + drill-in
+ live refresh — without races against the executor that writes
`*-tasks.md`, and without forcing the user to install a separate tool?

## Decision Drivers

- **No race with executors.** L-080–L-082 says only the executor commands
  may write `*-tasks.md`. A tracker that mutates files would corrupt
  Result Logs mid-step.
- **Reuse existing parser surface.** `src/aa_ma/plan_parsers.py` and
  `src/aa_ma/plan_markers/parser.py` already parse parts of the AA-MA
  grammar; a sibling TUI module in `aa-ma-forge` benefits from those
  shared regex / enum / em-dash conventions.
- **KISS — one install, one binary.** The user installs the plugin once
  via `scripts/install.sh`; a tracker that demands a second package or a
  global CLI would be friction without value.
- **Two render targets, one model.** Snapshot output for commits / CI /
  prompts; interactive TUI for live use. A second render shouldn't double
  the parser surface.
- **Bounded malformed-input tolerance.** Real-world legacy `## Step N:` /
  `## M1:` headers (observed in the v1 demo corpus) must NOT crash the
  pipeline.
- **Release vehicle.** A v0.10.0 minor bump cleanly delineates "before
  the tracker" from "with the tracker" for downstream consumers.

## Considered Options

1. **Standalone `aa-ma-tui` entrypoint inside aa-ma-forge** — one new
   sub-package (`src/aa_ma/tui/`), one new `[project.scripts]` entry,
   two render modes sharing one parser. Leaves the door open to a future
   `aa-ma view` subcommand.
2. **Scaffold an `aa-ma` top-level CLI first, ship `aa-ma view`** —
   design a cohesive multi-command CLI surface; the tracker becomes one
   subcommand.
3. **Two binaries (`aa-ma-snap` + `aa-ma-tui`)** — separate the snapshot
   mode from the interactive mode so each can be invoked independently
   without paying for the other.

## Decision Outcome

**Chosen:** Option 1 — Standalone `aa-ma-tui` entrypoint inside
aa-ma-forge.

**Rationale:** KISS wins for v0.10. Option 2 doubles the scope (we'd be
designing a top-level CLI surface under feature pressure); Option 3
duplicates entrypoint, argument parsing, parser invocation, and packaging
ceremony — Rich is a transitive dependency of Textual anyway, so the
second render target is essentially free inside one binary. Option 1
preserves a clean upgrade path to Option 2 later: `aa-ma view` can be
added as an alias once the top-level CLI exists.

## Pros and Cons of the Options

### Option 1 — Standalone `aa-ma-tui` (CHOSEN)

- ✅ One install vector via existing `scripts/install.sh` + uv workspace.
- ✅ Reuses `src/aa_ma/plan_*` parser conventions (em-dash, enum
  tolerance, regex grammar).
- ✅ Two render targets (Textual + Rich snapshot) sharing the same
  `discover_tasks()` symbol — L-052 dual-formatter rule satisfied by
  construction (test-enforced via `sys.modules` identity check).
- ❌ A future top-level CLI would need to migrate `[project.scripts]`
  — small surface (entry-point rename + deprecation alias + docs sweep),
  not literally one line.
- ❌ Tightens coupling between aa-ma-forge release cadence and tracker
  features — accepted because the tracker IS about tracking AA-MA work.

### Option 2 — Top-level `aa-ma` CLI first

- ✅ Cohesive UX from day one (`aa-ma plan`, `aa-ma execute`,
  `aa-ma view`).
- ❌ Designs the CLI surface under feature pressure — KISS violation.
- ❌ Doubles the v0.10 scope; pushes tracker release past v1.0.

### Option 3 — Two binaries

- ✅ Strict separation of concerns (snapshot binary has no Textual
  import; interactive binary has no `argparse --json`).
- ❌ Duplicates entrypoint, argparse, parser invocation, and packaging
  ceremony — DRY violation.
- ❌ Rich is already a transitive dep of Textual; the second render is
  free inside one binary.

## Consequences

**Positive:**

- The tracker ships in `v0.10.0` with **zero new install steps** —
  existing `scripts/install.sh` consumers get `aa-ma-tui` automatically
  once they upgrade the plugin.
- The 5-file AA-MA grammar gains a documented, typed parser surface
  (`src/aa_ma/tui/{model,parser}.py`) usable by future tooling: any
  future agent or skill that needs to introspect AA-MA task state can
  `from aa_ma.tui.parser import discover_tasks`.
- Live refresh via `watchfiles.awatch()` makes the tracker
  immediately-useful in a "leave it running in a second pane" mode
  while the executor writes Result Logs in the main pane.
- File-level decoupling: the tracker can read directories the executor
  is actively writing to without locking, since it never opens those
  files for write.

**Negative:**

- Adds 4 runtime deps to `pyproject.toml` ([project] dependencies):
  `pydantic>=2,<3`, `textual>=0.80,<1.0`, `rich>=13,<14`,
  `watchfiles>=0.21,<1.0`. Two were already transitive (Rich via
  Textual; watchfiles via fastmcp), but the explicit declaration per
  L-055 is the policy-correct shape.
- Adds 1 dev dep: `pytest-textual-snapshot>=1.0` for SVG regression
  testing of Textual screens.
- The KISS pop+push dashboard refresh pattern (vs. true reactive
  in-place mutation) leaks a `DashboardScreen` `isinstance` guard into
  `AAMAApp._reload_tasks`. This is M5 polish (`D-M3-1` backlog).

**Neutral:**

- Adopts Textual's `mutate_reactive(ClassName.attr)` convention
  (reference class attribute, not instance attribute) for mutable
  reactive updates — validated by the M3 Step 3.1 prototype and
  documented in
  `.claude/dev/active/aa-ma-tui-tracker/aa-ma-tui-tracker-reference.md`.
- `BOARD_COLUMNS` constant promoted to public in
  `src/aa_ma/tui/snapshot.py` so the dashboard and the snapshot
  renderer share the canonical 4-status order — single source of
  truth, drift-detected by a module-level `assert` (caught originally
  by M2 §6.8 future-proofing-auditor W6).
- WSL2 inotify subdir-registration timing constraint (≥ 1 s) surfaced
  during M3 Step 3.8 watcher tests; documented as test-module constant
  `_WSL_INOTIFY_SETTLE_S = 1.5`.

## Implementation Notes

Implementation landed across 5 milestones in plan
`.claude/dev/active/aa-ma-tui-tracker/`:

- **M0 (scaffolding)** — declared 4 runtime deps explicitly per L-055;
  added `[project.scripts] aa-ma-tui = "aa_ma.tui.__main__:main"`.
- **M1 (parser foundation)** — `model.py` (5 enums, Pydantic v2 Task /
  Milestone / Step) + `parser.py` (regex grammar + `parse_task_dir` +
  `discover_tasks`); 30 tests including a hypothesis round-trip property
  test; coverage 91%/100%.
- **M2 (snapshot mode)** — `snapshot.py` (Rich kanban / tree / summary)
  + `json_output.py` (`schema_version=1` envelope); 27 tests; goldens
  locked.
- **M3 (interactive Textual app)** — `app.py` + `watcher.py` + 2 screens
  + 2 widgets; live file-watch via `awatch(debounce=300)` +
  `AAMAFilter`; pytest-textual-snapshot regression. Prototype spike
  preceded TDD per `Prototype-Required: YES`.
- **M4 (this milestone)** — ADR-0007, README / CLAUDE.md updates,
  integration test, `/doc-sync`, release via
  `uv run cz bump --increment MINOR` → `v0.10.0`.

CLI contract (frozen at v0.10.0):

```
aa-ma-tui                                  # launch interactive TUI
aa-ma-tui --snapshot[=board|tree|summary]  # render once to stdout
aa-ma-tui --json                           # emit JSON envelope
aa-ma-tui --task NAME                      # filter to one task (required with --snapshot=tree)
aa-ma-tui --include-completed              # extend discovery to dev/completed/
aa-ma-tui --root PATH                      # explicit root (default scans ./ and ~/)
```

Exit codes: `0` normal · `2` `--task` not found · `3` no tasks
discovered. JSON envelope shape:
`{"schema_version": 1, "tasks": [Task.model_dump(mode="json"), ...]}`.

Open polish items (deferred to v0.11.0 — `M5` backlog):

- D-M2-1 — parser tolerance for legacy `## Step N:` / `## M(\d+):`
  milestone-header variants
- D-M2-2 — machine-enforce SCHEMA_VERSION bump policy
- D-M3-1 — SOC split of `AAMAApp._reload_tasks` (paired with reactive
  in-place mutation, lifting the `isinstance(self.screen,
  DashboardScreen)` guard out of the data path)
- D-M3-2 — `asyncio.shield` + worker-group cancel from
  `action_quit` for clean shutdown under heavy filesystem load
- D-M3-3 — TYPE_CHECKING + top-level import replacing the local-import
  circular-avoidance in `DashboardScreen.action_drill_in`
- D-M3-4 — Move `KanbanColumn { width: 1fr; ... }` rule from
  `AAMAApp.CSS` to `KanbanColumn.DEFAULT_CSS` (Textual-native
  per-widget styling)

## References

- Plan: [.claude/dev/active/aa-ma-tui-tracker/aa-ma-tui-tracker-plan.md](../../.claude/dev/active/aa-ma-tui-tracker/aa-ma-tui-tracker-plan.md)
- Engineering Standards: [claude-code/rules/engineering-standards.md](../../claude-code/rules/engineering-standards.md)
- L-052 dual-formatter rule (referenced in `snapshot.py` + `json_output.py` re-export of `discover_tasks`)
- L-055 explicit dependency classification (drove M0 T0.1 `[project] dependencies` array creation)
- L-065 state machine completeness (drove `AggregateStatus` per-state docstring + terminal-state justification)
- L-080–L-082 sub-step sync rule (drove the read-only design)
- Precedent: [JiraTUI](https://github.com/whyisdifficult/jiratui) — real-world Textual + Rich TUI of work items
- Context7 sources consulted at plan time and during execution:
  `/textualize/textual`, `/samuelcolvin/watchfiles`,
  `/websites/rich_readthedocs_io_en_stable`
