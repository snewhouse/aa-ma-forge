# aa-ma-tui-tracker Implementation Plan

Created: 2026-05-17
Owner: Stephen Newhouse + AI
Status: APPROVED (Phase 4.5 verified, revisions applied)
Repo: aa-ma-forge

> **For Claude:** REQUIRED SUB-SKILL: Use `/execute-aa-ma-milestone` (or `superpowers:executing-plans` in a fresh session) to implement this plan task-by-task. AA-MA task name: `aa-ma-tui-tracker`. AA-MA task directory: `.claude/dev/active/aa-ma-tui-tracker/` inside the `aa-ma-forge` repo.

**Goal:** Ship `aa-ma-tui` — a clean, KISS terminal UI inside `aa-ma-forge` that visualises every active AA-MA workflow (kanban + per-task milestone/step tree, with progress markers) and a one-shot `--snapshot` mode usable in commits, CI, and prompts.

**Architecture:** Read-only Pydantic-typed parser that consumes the existing AA-MA artifact format (5 files per task) and feeds two render targets sharing one in-memory model: a Textual interactive app (dashboard → drill-in) and a Rich one-shot stdout renderer. File-watch via `watchfiles.awatch()` with a debounced AA-MA-aware filter. Zero mutation of task files — strict separation from `/execute-aa-ma-*` writers.

**Tech Stack:** Python 3.11+ · Textual ≥ 0.80 · Rich ≥ 13 · watchfiles ≥ 0.21 · Pydantic v2 · hatchling · uv · pytest + pytest-textual-snapshot · hypothesis (round-trip parser fixtures). Repo: `~/biorelate/projects/gitlab/github_private/aa-ma-forge`.

---

## Context

**Why this exists.** `~/.claude/dev/active/` is currently empty, while `~/.claude/dev/completed/` holds 8 prior tasks (`aa-ma-team-guide`, `agent-token-optimization`, `galactic-skills-review`, `playwright-skill`, `safety-app-production-settings`, `security-quality-remediation`, `ultraplan-agent-teams-hardening`, `ultraplan-enhancement`). The trigger is recurring: every time you start a multi-task workflow under `/aa-ma-plan` + `/execute-aa-ma-milestone`, active tasks accumulate and the only way to scan "what's blocked, what's in progress, what milestone is next" across the portfolio is to open each `*-tasks.md` by hand. The session-start briefing only checks the current working directory, so the global picture stays invisible. Today's empty-active state is the *quiet* moment to ship the tool — before the next sprint creates the same overload.

**Intended outcome.** One command — `aa-ma-tui` — gives a live kanban of all active tasks; `Enter` drills into one task's milestone tree with per-step status, progress bar, Mode/Gate badges, and the tail of `provenance.log`. A `--snapshot` mode renders the same information once to stdout (no Textual init) so it can be piped into commits, CI logs, AI prompts, or scripts. A `--include-completed` flag opens the same view onto historical tasks for retros, reuse, and pattern review (the historical view is also the v1 smoke-demo target while `active/` is empty).

**Why now, why this shape.** The 8-completed-task corpus gives a rich, immediately-available test/demo dataset; the empty-active state means no race risk with `/execute-aa-ma-*` writers during initial development. The shape (read-only, in-aa-ma-forge, two-modes-one-model) was selected through Phase 1.3 grilling and Phase 1.4 user decisions: ship inside aa-ma-forge to reuse the existing `src/aa_ma/plan_parsers.py` enums and `src/aa_ma/plan_markers/parser.py`; stay read-only to avoid racing with `/execute-aa-ma-*` writers and to respect the L-080–L-082 sub-step sync rule (only executor commands write to `*-tasks.md`); ship `--snapshot` together with the TUI because Rich is a transitive dep of Textual anyway, so a second render target is essentially free.

---

## Executive Summary

A read-only Python TUI inside `aa-ma-forge` that parses every `.claude/dev/active/*/` AA-MA task directory (both project-local and global) into a typed Pydantic model, then renders that model two ways: a live Textual dashboard with drill-in, and a one-shot Rich stdout snapshot. One parser, one model, two render targets, zero mutation.

---

## Architecture Overview

```
                    ┌──────────────────────────┐
   filesystem ─────►│  aa_ma.tui.parser        │  (pure functions)
   .claude/dev/     │  parse_task_dir()        │
   active/*/        │  discover_tasks()        │
                    └──────────┬───────────────┘
                               │ List[Task]   (Pydantic v2)
                               ▼
                    ┌──────────────────────────┐
                    │  aa_ma.tui.model         │
                    │  Task / Milestone / Step │
                    │  Status/Mode/Gate enums  │
                    └──────────┬───────────────┘
                               │
                  ┌────────────┴────────────┐
                  ▼                         ▼
        ┌──────────────────┐     ┌──────────────────────┐
        │ aa_ma.tui.app    │     │ aa_ma.tui.snapshot   │
        │ Textual app      │     │ Rich one-shot render │
        │ • DashboardScr   │     │ • board / tree /     │
        │ • TaskDetailScr  │     │   summary / json     │
        │ watchfiles.awatch│     │ stdout only          │
        └──────────────────┘     └──────────────────────┘
                  ▲                         ▲
                  │                         │
                  └────────┬────────────────┘
                           │
                  aa-ma-tui [--snapshot=MODE] [--task NAME] [--root PATH] [--json]
```

**Entry point.** `[project.scripts] aa-ma-tui = "aa_ma.tui.__main__:main"` (added in pyproject.toml, version-bump in M0).

**Roots resolved.** Default scans `./.claude/dev/active/` AND `~/.claude/dev/active/`. Each is independent; both are merged into the displayed task list with a `root_label` field so the UI can distinguish "this repo" from "global".

**Aggregate state.** A task's `aggregate_status` is derived once at parse time, not stored: `COMPLETE` if all milestones COMPLETE; `BLOCKED` if any milestone marked BLOCKED; `IN_PROGRESS` (active) if any milestone has a non-PENDING step; else `PENDING`. This is the column the dashboard kanban groups by.

**File-watch.** `watchfiles.awatch()` worker runs in a Textual `@work` async task. A custom `AAMAFilter(DefaultFilter)` whitelists only `*-tasks.md`, `*-plan.md`, `*-context-log.md`, `*-reference.md`, `*-provenance.log`. Debounce = 300 ms. On a batch of changes: only reparse touched task dirs, post a Textual `TasksRefreshed` message; the app handles re-render via reactive update.

---

## Implementation Milestones

Five milestones. Each has TDD-bite-sized steps. Vertical slicing where possible — M2 ships a usable `--snapshot` command end-to-end before M3 starts on the interactive Textual app.

### Milestone 0: Scaffolding (≈ 30 min, Complexity 15%)

**Goal:** Add the `tui` package, declare the `aa-ma-tui` script, install dependencies. No behaviour yet — just the runtime shell.

**Gate:** SOFT · **Mode:** AFK

**Acceptance Criteria** (all falsifiable):
- Running `uv run aa-ma-tui --version` from the `aa-ma-forge` repo root exits 0 and prints a non-empty version string. (Exact version `aa-ma-tui 0.10.0` is asserted in M4 after `uv run cz bump`.)
- `python -c "import aa_ma.tui"` succeeds with no import error.
- `uv lock` shows new deps `textual`, `rich`, `watchfiles`, `pydantic` resolved (grep `uv.lock` for the four names).
- `pyproject.toml` contains a `[project] dependencies = [...]` array (which did NOT exist before M0 — confirmed by Wave-1 ground-truth audit).
- `import-linter` (already in dev-deps; root_package = `codemem` so `aa_ma.tui` is out of its scope) reports zero new boundary violations.

**Tasks:**
- **T0.1** **CREATE** the missing `[project] dependencies = [...]` array in `pyproject.toml` (currently absent — aa-ma-forge ships zero runtime deps today). Populate with `pydantic>=2,<3`, `textual>=0.80,<1.0`, `rich>=13,<14`, `watchfiles>=0.21,<1.0`. (TDD-Waiver: `tooling-config`)
- **T0.2** Add `[project.scripts] aa-ma-tui = "aa_ma.tui.__main__:main"` to `pyproject.toml` (the `[project.scripts]` table is currently absent — create it).
- **T0.3** **Do NOT hand-edit version strings.** The repo runs **both** `[tool.commitizen]` and `[tool.semantic_release]` (dual pipeline confirmed by Wave-1 verification, lines 30–50 of pyproject.toml). Both tools list `version_files = ["pyproject.toml:version", "VERSION:__version__"]` (or equivalent). The correct version-bump path is `uv run cz bump --increment MINOR` after the M0 commit — this updates `pyproject.toml`, `VERSION`, and `CHANGELOG.md` atomically. For M0 we defer the version bump to M4 release; M0 only adds deps + script + package skeleton without bumping. (TDD-Waiver: `tooling-config`.)
- **T0.4** `mkdir -p src/aa_ma/tui` ; create `__init__.py` with `__version__` re-export from `aa_ma`.
- **T0.5** Create skeletal `src/aa_ma/tui/__main__.py` with argparse parsing `--version`, `--snapshot[=MODE]`, `--task`, `--root`, `--include-completed`, `--json`; `main()` prints version and exits 0 for now.
- **T0.6** `uv sync` to install. Run `uv run aa-ma-tui --version` → assert it prints SOMETHING (exact version string only validated after M4 cz-bump). Commit with conventional message `feat(tui): scaffold aa-ma-tui package and CLI entrypoint`.

**Rollback:** `git revert` the M0 commit; deps are additive only. The `[project] dependencies` array is new so the revert removes it cleanly.

---

### Milestone 1: Parser foundation (≈ 4 h, Complexity 60%)

**Goal:** A pure, typed parser that turns a task directory into a `Task` model. No UI, no I/O coupling beyond reading files.

**Gate:** HARD (parser correctness is the foundation everything else relies on)
**Mode:** AFK
**Critical-Path:** `data-xform`

**Acceptance Criteria:**
- `aa_ma.tui.model.Task` has fields `name: str`, `root: Path`, `milestones: list[Milestone]`, `aggregate_status: AggregateStatus`, `last_modified: datetime | None`, `provenance_tail: list[str]` (last 5 lines).
- `aa_ma.tui.model.Milestone` has `number: int`, `title: str`, `status: MilestoneStatus`, `gate: Gate = Gate.SOFT`, `mode: Mode = Mode.AFK`, `complexity: int | None`, `dependencies: str | None`, `acceptance_criteria: str | None`, `steps: list[Step]`.
- `aa_ma.tui.model.Step` has `number: str` (e.g. "1.2"), `title: str`, `status: StepStatus`, `result_log: str | None`.
- Enums: `MilestoneStatus = {PENDING, ACTIVE, IN_PROGRESS, COMPLETE, BLOCKED}` · `StepStatus = {PENDING, IN_PROGRESS, COMPLETE, BLOCKED}` · `Mode = {HITL, AFK}` · `Gate = {SOFT, HARD}` · `AggregateStatus = {PENDING, IN_PROGRESS, BLOCKED, COMPLETE, ERROR}`. Every enum value is justified in a docstring (per **L-065**).
- `parse_task_dir(path: Path) -> Task` parses a single dir; raises `ParseError` with a precise message on malformed input.
- `discover_tasks(roots: list[Path]) -> list[Task]` scans roots, returns parsed tasks; **never raises** on per-task parse failure — returns a `Task` with `aggregate_status=ERROR` and `parse_error: str` field so the UI can render "PARSE_ERROR" badges.
- Parser tolerates both `- Status: PENDING` and `**Status:** PENDING` (per **L-052** variant-tolerance).
- Test fixtures: copies of three real completed tasks-files (`playwright-skill`, `agent-token-optimization`, `security-quality-remediation`) plus three synthetic edge-case fixtures (missing-status, blank-result-log, mixed-bold).
- `pytest tests/tui/test_parser.py -v` → all green; coverage of `parser.py` ≥ 90%.
- `hypothesis`-based round-trip test: render(parse(file)) ≈ original status fields (round-trip property, per **L-058**).

**Files:**
- Create: `src/aa_ma/tui/model.py` (Pydantic v2 models + enums)
- Create: `src/aa_ma/tui/parser.py` (pure parsing functions)
- Create: `tests/tui/__init__.py`
- Create: `tests/tui/conftest.py` (fixture loader)
- Create: `tests/tui/fixtures/tasks/{playwright-skill,agent-token-optimization,security-quality-remediation,edge-no-status,edge-bold-status,edge-blank-result}/...` (copy real samples + synthesize edges)
- Create: `tests/tui/test_parser.py`
- Create: `tests/tui/test_parser_properties.py` (hypothesis)
- Modify: `pyproject.toml` (add `hypothesis` if missing — already in dev-deps)

**Tasks (TDD discipline):**
- **T1.1** Write `tests/tui/test_model.py` asserting all 5 enum sets and their values. Run → FAIL (model not created). Create `model.py`. Re-run → PASS. Commit.
- **T1.2** Write `tests/tui/test_parser.py::test_parse_complete_task` using `playwright-skill` fixture, asserting milestones count, first milestone status, first step status. Run → FAIL. Implement minimal `parse_task_dir`. Run → PASS. Commit.
- **T1.3** Add `test_parse_tolerates_bold_status` fixture + test. RED. Implement regex tolerating both forms. GREEN. Commit.
- **T1.4** Add `test_discover_tasks_merges_roots` — two synthetic root dirs each containing one task. RED. Implement `discover_tasks`. GREEN. Commit.
- **T1.5** Add `test_discover_tasks_survives_parse_error` — synthesize a malformed task dir. RED. Wrap per-task parse in try/except, attach `parse_error` field. GREEN. Commit.
- **T1.6** Add `test_aggregate_status_*` (5 tests, one per AggregateStatus value). RED. Implement `aggregate_status` derivation in `Task.model_validator`. GREEN. Commit.
- **T1.7** Add `tests/tui/test_parser_properties.py` with one hypothesis strategy generating valid tasks.md content. RED on first violation. Tighten parser. GREEN. Commit.
- **T1.8** Add `test_provenance_tail_returns_last_n_lines`. RED → implement → GREEN → commit.
- **T1.9** Add `test_last_modified_max_of_files`. RED → implement → GREEN → commit.
- **T1.10** Run `uv run pytest tests/tui/ --cov=aa_ma.tui --cov-report=term-missing`. Assert ≥ 90% on `parser.py` + `model.py`. If gaps, add targeted tests. Commit.

**Reuses:** `aa_ma.plan_parsers` enum-validation helpers (don't re-implement `parse_audit_profile` / `parse_tdd_waiver` style — those are for plan markers, not tasks.md, but mirror the *tolerance pattern*).

**Rollback:** `git revert` M1 commits; no API contract published yet so safe.

**Risks (top 3):**
1. **Status-line grammar drift** — Real samples mostly conform but the L-052 lesson is that variants do appear. *Mitigation:* hypothesis strategy + fixture diversity (3 real + 3 edge); CI runs on every PR.
2. **Aggregate status semantics under-specified** — What if a milestone has BOTH COMPLETE and BLOCKED steps? *Mitigation:* enumerate every state per **L-065**; document terminal-state rules in `model.py` docstring; cover with tests.
3. **`hypothesis` flake** — Property tests can produce non-deterministic CI failures. *Mitigation:* `@settings(deadline=None, max_examples=100)`, derandomized seeds, `--hypothesis-show-statistics` in CI for visibility.

---

### Milestone 2: Snapshot mode (`--snapshot` Rich renderer + `--json`) (≈ 4 h, Complexity 55%)

**Goal:** Ship a usable end-to-end CLI. Bypasses Textual entirely; pure stdout. Validates the parser against real data in your shell.

**Gate:** HARD · **Mode:** AFK · **Critical-Path:** `data-xform`

**Acceptance Criteria:**
- `aa-ma-tui --snapshot` (default `--snapshot=board`) renders a Rich `Columns` of 4 panels (PENDING / IN_PROGRESS / BLOCKED / COMPLETE) listing all discovered tasks with their progress (`X/Y steps · M/N milestones`), Mode/Gate badges, and root label.
- `aa-ma-tui --snapshot=tree --task NAME` renders one task as a Rich `Tree` (milestones → steps), with status icons and the first 60 chars of each Result Log.
- `aa-ma-tui --snapshot=summary` prints one line per task: `NAME  [status]  X/Y steps  M/N ms  · last update`.
- `aa-ma-tui --json` emits a JSON dump of `discover_tasks(...)` — schema validated against `aa_ma.tui.model.Task.model_json_schema()`.
- **All four output modes call the same `discover_tasks` function object** (per **L-052** dual-formatter rule). Falsifiable test: `assert sys.modules['aa_ma.tui.snapshot'].discover_tasks is sys.modules['aa_ma.tui.json_output'].discover_tasks is sys.modules['aa_ma.tui.app'].discover_tasks` — fails if any module imports a divergent copy.
- Exit codes: 0 normal · 2 `--task NAME` not found · 3 no tasks discovered.
- `aa-ma-tui --include-completed` extends discovery to `<root>/.claude/dev/completed/` (default: active only). Useful while `~/.claude/dev/active/` is empty.
- Golden-file tests: `tests/tui/snapshots/board.txt`, `tree.txt`, `summary.txt`, `data.json` compared via Rich's `Console(record=True).export_text()`.

**Files:**
- Create: `src/aa_ma/tui/snapshot.py` (Rich rendering functions; `render_board`, `render_tree`, `render_summary`)
- Create: `src/aa_ma/tui/json_output.py` (JSON serialiser using `model_dump_json`)
- Modify: `src/aa_ma/tui/__main__.py` (wire argparse → snapshot / json dispatch)
- Create: `tests/tui/test_snapshot.py`
- Create: `tests/tui/test_json_output.py`
- Create: `tests/tui/snapshots/` (golden text files committed)

**Tasks (TDD):**
- **T2.1** Write `test_snapshot_board_matches_golden` against a static 3-task fixture set. RED → implement `render_board`. GREEN. Commit.
- **T2.2** Write `test_snapshot_tree_renders_milestones_and_steps`. RED → implement `render_tree`. GREEN. Commit.
- **T2.3** Write `test_snapshot_summary_one_line_per_task`. RED → implement. GREEN. Commit.
- **T2.4** Write `test_json_output_validates_against_schema`. RED → implement `json_output.dump`. GREEN. Commit.
- **T2.5** Write `test_main_dispatch_board_default`, `test_main_dispatch_tree_requires_task`, `test_main_exit_code_no_tasks`, `test_main_exit_code_task_not_found`. RED → wire dispatch in `__main__.py`. GREEN. Commit.
- **T2.6** Manual smoke against the live `completed/` corpus (active/ is empty at v1 launch): `uv run aa-ma-tui --snapshot=board --include-completed --root ~/.claude` — eyeball output. Capture as `provenance.log` entry: `[ts] PROTOTYPE — board snapshot rendered against 8 completed tasks (active=0): OK`.
- **T2.7** `uv run aa-ma-tui --json --include-completed --root ~/.claude | jq '.[] | .name'` — assert all 8 completed task names appear (`aa-ma-team-guide`, `agent-token-optimization`, `galactic-skills-review`, `playwright-skill`, `safety-app-production-settings`, `security-quality-remediation`, `ultraplan-agent-teams-hardening`, `ultraplan-enhancement`). Commit fixture if any anomaly found.
- **T2.8** Regenerate golden files only if anomalies found; otherwise re-run all snapshot tests. Commit.

**Tests-to-validate-milestone:**
- `uv run pytest tests/tui/ -v` — all 18+ tests green.
- `uv run aa-ma-tui --snapshot=board --include-completed --root ~/.claude` exits 0 with a visible kanban listing the 8 completed tasks.
- `uv run aa-ma-tui --json --include-completed --root ~/.claude | python -c "import json,sys; json.load(sys.stdin)"` exits 0.

**Rollback:** Revert M2 commits. M1 parser stays usable from the API.

**Risks (top 3):**
1. **Golden-file brittleness** under terminal width changes. *Mitigation:* tests construct `Console(width=120, record=True)` explicitly; pin width.
2. **JSON schema drift** breaks downstream consumers (later). *Mitigation:* `Task.model_json_schema()` is exported as `aa_ma.tui.model.SCHEMA_VERSION = 1`; CHANGELOG breaking-change required to bump.
3. **`--task NAME` ambiguity** if same name in both roots. *Mitigation:* require `--root` if name collision; exit code 4 with clear message.

---

### Milestone 3: Interactive Textual app (≈ 8 h, Complexity 75%)

**Goal:** The live TUI. Dashboard screen aggregates all active tasks; task-detail screen drills into one task; file-watch refreshes on change.

**Gate:** HARD · **Mode:** AFK · **Critical-Path:** `external-api` (filesystem-watch contract)
**Prototype-Required:** YES (Textual reactive + watchfiles integration warrants a spike — see T3.1)

**Acceptance Criteria:**
- `aa-ma-tui` (no args) launches a Textual app.
- DashboardScreen shows a 4-column kanban (PENDING / IN_PROGRESS / BLOCKED / COMPLETE) with one card per task; each card shows: name · `█▒▒▒▒` progress bar · `M/N ms · X/Y steps` · `[HITL]` / `[HARD]` badges · root label.
- Keybindings (visible in Footer): `↑/k`, `↓/j` task nav · `Enter` drill-in · `r` manual refresh · `q` quit · `?` help · `/` filter.
- Pressing `Enter` opens TaskDetailScreen for the focused task: left pane = milestone Tree; right pane = Result Log preview for the selected step; bottom = last 5 provenance lines.
- TaskDetailScreen keybindings: `↑/↓` step nav · `←/h` collapse milestone · `→/l` expand milestone · `Esc` back to dashboard · `q` quit.
- File-watch via `watchfiles.awatch()` running in a Textual `@work` async task; on any change to a watched file under `<root>/.claude/dev/active/`, only the affected task is reparsed and the relevant Card / Tree updated.
- Debounce = 300 ms (`debounce=300` in `awatch` call).
- **Malformed-input tolerance (bounded).** Given a fixture dir containing one malformed task, `async with AAMATuiApp(roots=[tmp]).run_test(size=(120,40)) as pilot:` completes without raising within 2 seconds, AND the literal string `PARSE_ERROR` appears in `pilot.app.screen.render_str()` for that task's card.
- `pytest-textual-snapshot` smoke test of both screens with a 3-task fixture.

**Files:**
- Create: `src/aa_ma/tui/app.py` (`AAMATuiApp(App)`, BINDINGS, run loop)
- Create: `src/aa_ma/tui/screens/__init__.py`
- Create: `src/aa_ma/tui/screens/dashboard.py` (`DashboardScreen(Screen)`)
- Create: `src/aa_ma/tui/screens/task_detail.py` (`TaskDetailScreen(Screen)`)
- Create: `src/aa_ma/tui/widgets/__init__.py`
- Create: `src/aa_ma/tui/widgets/task_card.py` (`TaskCard(Static)` — reactive `task` attr)
- Create: `src/aa_ma/tui/widgets/kanban_column.py` (`KanbanColumn(VerticalScroll)`)
- Create: `src/aa_ma/tui/watcher.py` (`async def watch_roots(roots, on_change) -> None`)
- Create: `src/aa_ma/tui/app.tcss` (Textual CSS — color tokens, spacing)
- Modify: `src/aa_ma/tui/__main__.py` (default no-args → launch app)
- Create: `tests/tui/test_app_smoke.py` (pytest-textual-snapshot)
- Create: `tests/tui/test_watcher.py` (real tmp_path + watchfiles)

**Tasks (TDD-first where possible, prototype-first where not):**
- **T3.1** **Prototype spike** (`Skill(prototype)` LOGIC variant). Throwaway script `prototype_textual_watcher.py` — launches a Textual app with one Static, an `@work` async watcher on a tmp dir, and asserts the Static updates when a file is touched. Run live; observe correct debounce behaviour. Record verdict in `provenance.log` per Theme-1 rule: `[ts] PROTOTYPE — Textual+watchfiles integration: VERIFIED`. Delete prototype. Commit nothing.
- **T3.2** Write `tests/tui/test_widgets_task_card.py::test_renders_progress_and_badges`. RED → implement `TaskCard`. GREEN. Commit.
- **T3.3** Write `tests/tui/test_widgets_kanban_column.py::test_groups_tasks_by_aggregate_status`. RED → implement. GREEN. Commit.
- **T3.4** Write `tests/tui/test_screens_dashboard.py::test_compose_yields_4_columns`. RED → implement `DashboardScreen.compose`. GREEN. Commit.
- **T3.5** Write `tests/tui/test_screens_dashboard.py::test_enter_pushes_task_detail` using `Pilot` from Textual's test framework. RED → wire BINDINGS + action. GREEN. Commit.
- **T3.6** Write `tests/tui/test_screens_task_detail.py::test_compose_yields_tree_and_preview`. RED → implement. GREEN. Commit.
- **T3.7** Write `tests/tui/test_screens_task_detail.py::test_arrow_nav_selects_step`. RED → wire. GREEN. Commit.
- **T3.8** Write `tests/tui/test_watcher.py::test_on_file_change_triggers_callback` — uses `tmp_path`, real filesystem, `asyncio.wait_for(..., timeout=2.0)`. RED → implement `watch_roots`. GREEN. Commit.
- **T3.9** Write `tests/tui/test_watcher.py::test_ignores_unrelated_files` (verifies AAMAFilter). RED → implement filter subclass. GREEN. Commit.
- **T3.10** Write `tests/tui/test_app_smoke.py` (snapshot via `pytest-textual-snapshot`). RED → wire `__main__` to launch app. GREEN. Commit.
- **T3.11** Manual smoke: `uv run aa-ma-tui` in interactive terminal; navigate, drill in, edit a fixture task file in another terminal, confirm refresh. Log to `provenance.log`. Commit any CSS tweaks.
- **T3.12** Run full test suite + coverage. Assert tui package ≥ 80%. Commit.

**Tests-to-validate-milestone:**
- `uv run pytest tests/tui/ -v` — all green (now ~30+ tests).
- `uv run aa-ma-tui` launches without traceback; kanban renders; `Enter` drills in; `r` refreshes; `q` quits.
- Touch a task's `*-tasks.md` in another shell — dashboard reflects within 1s.

**Rollback:** Disable script entry point (`aa-ma-tui` stub returns "disabled") and revert M3 commits in one shot. M2 snapshot CLI keeps working.

**Risks (top 3):**
1. **Premature reactive watcher invocation** (Textual `__init__` pitfall surfaced in Context7 docs). *Mitigation:* use `set_reactive(Cls.attr, value)` in constructors, document in code comment.
2. **Watchfiles CPU on macOS/WSL** with many file events. *Mitigation:* debounce 300ms + `AAMAFilter` whitelist; default `force_polling=False`; `--poll-interval N` escape hatch.
3. **Snapshot-test flakes** under different terminal sizes. *Mitigation:* `pytest-textual-snapshot` defaults to 80×24; pin via `App.run_test(size=(120, 40))`; commit golden SVGs.

---

### Milestone 4: ADR, docs, integration test, release (≈ 2 h, Complexity 40%)

**Goal:** Document the decision; surface usage in README; one end-to-end integration test; cut release.

**Gate:** HARD · **Mode:** HITL (release versioning) · **Critical-Path:** `version-pipeline` · **Critical-Path:** `doc-count-drift`

**Acceptance Criteria:**
- `docs/adr/0007-aa-ma-tui-tracker.md` exists with sections: Context · Decision · Consequences · Alternatives Considered · References (cites JiraTUI, kanban-tui, rust_kanban, L-052, L-065, L-080–082).
- `docs/adr/INDEX.md` contains a row for ADR-0007 (Wave-1 confirmed `INDEX.md` exists; Tier 5 ADR-Index detector enforces this in `/release-prep`).
- `README.md` has a `## Visualizing Active Tasks` section showing `uv run aa-ma-tui` + `--snapshot` + `--include-completed` examples.
- `CLAUDE.md` gets a one-line addition under the `## Build & Development Commands` section (confirmed by Wave-1 audit; there is NO "Tools" section in aa-ma-forge's CLAUDE.md — original plan wording was incorrect) pointing at `uv run aa-ma-tui` with a one-sentence description.
- `CHANGELOG.md` `[0.10.0]` section contains a `### Feat` entry mentioning `aa-ma-tui` (NOT `### Added` — house style is conventional-commit-based per `[tool.commitizen]` config; `update_changelog_on_bump = true` so `cz bump` writes this automatically).
- Integration test `tests/tui/test_integration.py::test_end_to_end_against_temp_active_dir` spawns a temp `.claude/dev/active/` with two fake tasks, runs `aa-ma-tui --snapshot=summary --root <tmp>` via subprocess, asserts both names + correct status counts in stdout.
- `/doc-sync` reports zero CRITICAL findings; Tier 6 count-drift detector reports no stale counts (per **L-052 recurring-issues** + the SECURITY.md anti-pattern).
- Tag `v0.10.0` exists in `git tag -l` (created by `uv run cz bump`).

**Files:**
- Create: `docs/adr/0007-aa-ma-tui-tracker.md`
- Modify: `docs/adr/INDEX.md` (confirmed exists per Wave-1)
- Modify: `README.md`
- Modify: `CLAUDE.md` (one-line under "Build & Development Commands")
- Touch (managed by cz bump): `pyproject.toml`, `VERSION`, `CHANGELOG.md` — DO NOT hand-edit; `cz bump` updates all three atomically because both are registered as `version_files` targets.
- Create: `tests/tui/test_integration.py`

**Tasks:**
- **T4.1** Draft ADR-0007 from this plan's "Architecture Overview" + "Alternatives Considered" sections (Approaches A/B/C from Phase 2). HITL: user reviews wording. Commit `docs(adr): add ADR-0007 aa-ma-tui-tracker`.
- **T4.2** Update `docs/adr/INDEX.md` (add ADR-0007 row), `README.md` (add `## Visualizing Active Tasks` section), `CLAUDE.md` (add one-line under `## Build & Development Commands` mentioning `uv run aa-ma-tui`). Commit `docs: README/CLAUDE/ADR-INDEX for aa-ma-tui`.
- **T4.3** Write integration test (`test_end_to_end_against_temp_active_dir`). RED → ensure parser/snapshot work via subprocess. GREEN. Commit `test(tui): end-to-end integration test`.
- **T4.4** Run `Skill(doc-drift-detection)` (or `/doc-sync`). Fix any flagged drift. Commit `docs: fix drift surfaced by doc-sync` (only if any).
- **T4.5** Run full test suite + coverage. Assert overall coverage doesn't regress. Commit any fixture or test additions.
- **T4.6** HITL gate: user approves release. Run `uv run cz bump --increment MINOR` — this atomically updates `pyproject.toml`, `VERSION`, `CHANGELOG.md`, commits with `bump:`, and creates tag `v0.10.0`. Push commit + tag: `git push --follow-tags`. Confirm with `git tag -l v0.10.0`.

**Rollback:** `git revert v0.10.0` tag deletion + revert release commit. M0-M3 functionality stays in place; only the version tag is undone.

**Risks (top 3):**
1. **Doc drift after release** (the SECURITY.md anti-pattern). *Mitigation:* Tier 6 hardcoded-count guard if any prose mentions "N tasks" / "N keybindings" — wire a `count_*` function into `.claude/doc-counts.sh` if used.
2. **ADR cross-reference rot** if INDEX.md is forgotten. *Mitigation:* Tier 5 ADR-Index detector catches; gated in `/release-prep`.
3. **Integration test depends on subprocess + tmp_path race** on Windows. *Mitigation:* mark `@pytest.mark.skipif(sys.platform == "win32")` if proven flaky; not a launch blocker.

---

### Milestone 5 (Optional polish, deferred — flag `--milestone-5` in plan only): Help screen, filter, theming, graceful parse-error display (≈ 4 h, Complexity 30%)

**Goal:** v0.11.0 follow-up. Help modal on `?`. Fuzzy task-name filter on `/`. `--theme dark|light|auto`. Cleaner error rendering.

**Gate:** SOFT · **Mode:** AFK

Not part of v0.10.0 launch. Listed so that backlog items captured during M1-M4 land somewhere durable rather than in TODO comments. If you defer this milestone, do so explicitly via `/gsd-add-backlog` so it isn't silently dropped.

---

## Required Artefacts (cross-milestone summary)

| Artefact | M | Purpose |
|---|---|---|
| `src/aa_ma/tui/{model,parser,snapshot,json_output,app,watcher}.py` | 1-3 | Core implementation |
| `src/aa_ma/tui/screens/{dashboard,task_detail}.py` | 3 | Textual screens |
| `src/aa_ma/tui/widgets/{task_card,kanban_column}.py` | 3 | Reusable widgets |
| `src/aa_ma/tui/app.tcss` | 3 | Textual CSS |
| `tests/tui/{test_model,test_parser,test_parser_properties,test_snapshot,test_json_output,test_widgets_*,test_screens_*,test_watcher,test_app_smoke,test_integration}.py` | 1-4 | Test suite |
| `tests/tui/fixtures/tasks/{playwright-skill,...}/...` | 1 | Real + synthetic parser fixtures |
| `tests/tui/snapshots/*.{txt,json}` | 2 | Golden snapshots |
| `docs/adr/0007-aa-ma-tui-tracker.md` | 4 | Architecture Decision Record |
| `README.md`, `CLAUDE.md`, `docs/adr/INDEX.md` updates | 4 | Documentation |
| `pyproject.toml` (new `[project.scripts]`, new `[project] dependencies` array) | 0 | Packaging (M0) |
| `pyproject.toml`, `VERSION`, `CHANGELOG.md` (managed by `uv run cz bump`) | 4 | Versioning + changelog (M4 — atomic via commitizen) |

---

## Tests-to-Validate-Milestone (consolidated)

- **M0:** `uv run aa-ma-tui --version` returns 0 with non-empty version string.
- **M1:** `uv run pytest tests/tui/test_model.py tests/tui/test_parser.py tests/tui/test_parser_properties.py -v` all green; coverage ≥ 90% on parser+model.
- **M2:** `uv run pytest tests/tui/test_snapshot.py tests/tui/test_json_output.py -v` all green; `uv run aa-ma-tui --snapshot=board --include-completed --root ~/.claude` exits 0 with kanban visible.
- **M3:** `uv run pytest tests/tui/ -v` all green; `uv run aa-ma-tui --include-completed` launches and refreshes on file change within 1s.
- **M4:** `uv run pytest tests/tui/test_integration.py -v` green; `/doc-sync` zero CRITICAL findings; `git tag -l v0.10.0` returns `v0.10.0`.

---

## Rollback Strategy (overall)

The work is purely additive within `aa-ma-forge`:
- All new code is in `src/aa_ma/tui/` (new package; deleting the dir is sufficient).
- The only non-additive edits are to `pyproject.toml` (new `[project.scripts]` and new `[project] dependencies` arrays — neither existed before M0).
- M4 release is reversible via `git tag -d v0.10.0 && git push --delete origin v0.10.0` AND `git revert <bump-commit>`. `uv run cz` does not auto-publish to a registry.
- `uv pip install aa-ma==0.9.0` downgrades cleanly because no shared modules are modified.
- Per-milestone rollback is `git revert` of the milestone's commit range (kept linear by TDD-style frequent commits).

---

## Dependencies & Assumptions

**Dependencies (new — all added in M0 T0.1; Wave-1 confirmed NONE currently exist in `[project] dependencies`):**
- `textual>=0.80,<1.0` (pinned-loose; major-bump requires re-test)
- `rich>=13,<14`
- `watchfiles>=0.21,<1.0`
- `pydantic>=2,<3` (currently only a transitive dep; M0 promotes to direct per L-055)
- Dev (M3 only): `pytest-textual-snapshot>=1.0`

**Assumptions (status updated after Wave-1 verification):**
1. **`hypothesis` already in dev-deps** — **VERIFIED** at `pyproject.toml:31`.
2. ~~`pydantic` already a dep~~ — **DISPROVEN** by Wave-1. Pydantic appears only as a *transitive* dep of `mcp` / `openapi-pydantic` / `fastmcp`. The plan now adds it explicitly as a runtime dep in T0.1.
3. **The 5 file-name pattern is stable** — **VERIFIED** by Phase 1 research against 8 completed tasks; identical structure.
4. **Status/Mode/Gate enum values** — **PARTIALLY DISPROVEN** by Wave-1: real samples only show `ACTIVE` and `COMPLETE` in Status; `Mode:` and `Gate:` fields are *absent* in most tasks. The plan's enum is a superset of what's been seen; `Mode = Mode.AFK` and `Gate = Gate.SOFT` defaults handle absence. The parser MUST tolerate missing `Mode:` / `Gate:` fields (added explicit M1 acceptance criterion via the existing defaults in the dataclass spec).
5. **No project uses `--root` paths containing spaces** — covered by parametrized test in M1.
6. **`watchfiles` works on WSL2 + Ubuntu 24.04** — **VERIFIED** by Wave-1 (`watchfiles` already resolved as transitive of `fastmcp` in `uv.lock`, proving install works in this env). T3.1 prototype spike still recommended for the live-refresh contract.
7. **No CI workflow currently runs `pytest`** — Wave-1 finding: only `.github/workflows/security.yml` exists. **Plan accepts this** for v0.10.0 (local-pytest is the gate); a follow-up backlog item should add a `tests.yml` workflow but is OUT of scope here (KISS).
8. **`[project.scripts]` table doesn't exist in pyproject** — **VERIFIED** by Wave-1; T0.2 creates it.

**State-machine completeness (per L-065):**
- `AggregateStatus`: PENDING (initial; reachable from new tasks) · IN_PROGRESS (reachable from PENDING via any non-COMPLETE step start) · BLOCKED (reachable from any state on milestone-level BLOCKED) · COMPLETE (terminal — all milestones COMPLETE) · ERROR (terminal — parse failure; only entered via try/except in `discover_tasks`).
- Every state has at least one incoming transition; only COMPLETE and ERROR are terminal; both terminal states are documented in `model.py` docstring with the justification: "COMPLETE: nothing left to do. ERROR: artifact is malformed; resolution requires human edit, then re-parse will exit ERROR back into one of the other 4 states."

---

## Effort Estimate + Complexity per Milestone

| M | Effort | Complexity | Why |
|---|---|---|---|
| M0 | 30 min | 15% | Scaffolding; mechanical |
| M1 | 4 h | 60% | Parser correctness is the foundation; hypothesis + 90% cov bar |
| M2 | 4 h | 55% | Rich rendering is well-trodden; golden-file discipline is the work |
| M3 | 8 h | 75% | First Textual app in this repo; reactive + async + watchfiles integration; prototype-first warranted |
| M4 | 2 h | 40% | Docs + integration test + release pipeline |
| **Total v0.10.0** | **~18.5 h** | — | Comfortable 3-day sprint at focused pace |
| M5 (optional) | 4 h | 30% | Polish; defer or backlog |

Steps with Complexity ≥ 80%: **none individually**; M3 as a whole is the highest at 75%. No mandatory CoT-deep-reasoning gate, but T3.1 prototype spike serves the same purpose.

---

## Top Risks & Mitigations (cross-cutting; per-milestone risks above)

1. **Parser correctness drift over time** — AA-MA artifact format may evolve (e.g., new Status values like `IN_PROGRESS` is already a deviation from earlier convention). *Mitigation:* hypothesis property tests in M1; an `aa-ma-forge` CI job runs the parser against all `.claude/dev/completed/*` directories monthly; any new Status value surfaces as a parser failure (FAIL FAST).
2. **Concurrent write race** with `/execute-aa-ma-milestone` or `/execute-aa-ma-step` mid-render. *Mitigation:* read-only design + `discover_tasks` survives `ParseError`; if a file is mid-write, parser returns `parse_error=...` for that task only; next watchfiles event triggers a re-read once write completes. No file lock needed (we never write).
3. **User installs aa-ma-forge globally and `aa-ma-tui` collides with another tool** in $PATH. *Mitigation:* script name `aa-ma-tui` is unique enough (verified `which aa-ma-tui` returns nothing pre-install); document in CHANGELOG; alias support deferred until reported.

---

## Next Action

After plan approval (ExitPlanMode):
1. `/aa-ma-plan` Phase 5 creates `.claude/dev/active/aa-ma-tui-tracker/` **in the `aa-ma-forge` repo** (`cd ~/biorelate/projects/gitlab/github_private/aa-ma-forge` first; this `clauding` directory is not a git repo). The 5 AA-MA files are populated from this revised plan.
2. Then start execution at **M0 Task T0.1** (create `[project] dependencies = [...]` array with the 4 runtime deps).
3. AA-MA file to update first: `aa-ma-tui-tracker-tasks.md` (mark T0.1 IN_PROGRESS, write Result Log on completion per L-080–082 sub-step sync rule).

---

## Engineering Standards Declaration (element #12)

All six themes from `claude-code/rules/engineering-standards.md` materially apply to this plan:

1. **Verification & Truth** — Parser must be tested against real AA-MA artifact fixtures (3 real + 3 synthetic edges), not assumed behavior; T3.1 prototype spike for Textual+watchfiles integration before committing to the design (`Skill(prototype)` LOGIC variant); `CRITICAL_PATH_REVIEW` provenance entries on T1 (`data-xform`), T3 (`external-api` for filesystem-watch contract), T4 (`version-pipeline` + `doc-count-drift`).
2. **Development Principles** — KISS is explicit user constraint; TDD discipline per task (RED→GREEN→COMMIT); DRY (one parser, one model, two render targets); SOLID (parser/render/app strictly separated); SOC (Pydantic models own validation, parser owns I/O, render is pure formatting).
3. **Reasoning & Planning** — Socratic alternatives presented in Phase 2 (A/B/C); first-principles applied to "is mutation needed?" → answered "no, AA-MA write discipline reserves writes for executor commands"; skill assessment (brainstorming → writing-plans → plan-verification → executing-plans is the chain) declared up-front.
4. **Safety & Continuity** — Non-breaking constraint trivially satisfied (additive package); lessons applied (L-052 dual-formatter rule, L-058 schema documentation, L-065 state-machine completeness, L-080–082 sub-step sync rule by *not* mutating, L-214 closed code fences); incremental validation via per-task TDD commits.
5. **Execution Checklist** — Every task in M1-M4 has HARD-gated acceptance criteria. T1.10, T2.8, T3.12, T4.5 are explicit coverage / re-run / sync gates per the Engineering Standards Checklist.
6. **Sync & Commit Discipline** — Per-task `Status: COMPLETE` + `Result Log:` writes immediately after each step (the very discipline this tool is designed to *visualize* and *enforce by visibility*); Conventional Commits with `[AA-MA Plan] aa-ma-tui-tracker .claude/dev/active/aa-ma-tui-tracker` footer on every commit; milestone HARD-gate refusal if PENDING sub-steps remain.

---

## Verification (how to test end-to-end after implementation)

```bash
# from ~/biorelate/projects/gitlab/github_private/aa-ma-forge

# 1. Install
uv sync
uv pip install -e .

# 2. Smoke version
uv run aa-ma-tui --version
# expect: aa-ma-tui 0.10.0 (after M4 cz bump; M0 prints whatever __version__ was inherited)

# 3. Snapshot all available AA-MA tasks (board view, including completed since active/ is empty)
uv run aa-ma-tui --snapshot=board --include-completed --root ~/.claude
# expect: 4-column Rich kanban listing the 8 completed tasks (most in COMPLETE column)

# 4. Snapshot one specific task as a tree
uv run aa-ma-tui --snapshot=tree --task playwright-skill --include-completed --root ~/.claude
# expect: Rich Tree showing 3 milestones with step counts

# 5. JSON output (machine-readable)
uv run aa-ma-tui --json --include-completed --root ~/.claude | jq '.[] | .name'
# expect: 8 task name strings

# 6. Interactive TUI
uv run aa-ma-tui --include-completed --root ~/.claude
# expect: Textual app launches; ↑/↓/Enter navigation works

# 7. File-watch refresh (in two terminals — pre-stage an active task to demo)
#   Terminal X: mkdir -p ~/.claude/dev/active/demo-task && \
#               cp ~/.claude/dev/completed/playwright-skill/*.{md,log} \
#                  ~/.claude/dev/active/demo-task/ && \
#               rename 's/playwright-skill/demo-task/' ~/.claude/dev/active/demo-task/*
#   Terminal A: uv run aa-ma-tui --root ~/.claude   # no --include-completed; only demo-task shown
#   Terminal B: touch ~/.claude/dev/active/demo-task/demo-task-tasks.md
#   expect: dashboard updates within ~1s. Cleanup: rm -rf ~/.claude/dev/active/demo-task

# 8. Full test suite
uv run pytest tests/tui/ -v --cov=aa_ma.tui --cov-report=term-missing
# expect: all green; tui package coverage ≥ 80%; parser+model ≥ 90%

# 9. Doc-drift gate
/doc-sync   # (or: Skill(doc-drift-detection))
# expect: zero CRITICAL findings

# 10. End-to-end integration test (already run by pytest in step 8;
#     this just confirms the subprocess approach works manually)
uv run pytest tests/tui/test_integration.py -v
```

---

## Critical Files Reference Map

| Existing file to reuse | Purpose |
|---|---|
| `src/aa_ma/plan_parsers.py` | Enum-validation idiom for `Audit-Profile` / `TDD-Waiver`; mirror its tolerance pattern in new tasks.md parser |
| `src/aa_ma/plan_markers/parser.py` | Em-dash separator + `INIT/DONE/SKIPPED` enum (reference for parser conventions; not a direct dep unless M5 adds plan-marker view) |
| `pyproject.toml` | Add `[project.scripts]`, runtime deps, version bump |
| `~/.claude/dev/completed/playwright-skill/playwright-skill-tasks.md` | Fixture source (canonical structure) |
| `~/.claude/dev/completed/agent-token-optimization/*` | Fixture source (diverse Mode/Gate values) |
| `~/.claude/dev/completed/security-quality-remediation/*` | Fixture source (longest milestone count seen) |

| New file (created) | Layer |
|---|---|
| `src/aa_ma/tui/model.py` | Domain |
| `src/aa_ma/tui/parser.py` | I/O → Domain |
| `src/aa_ma/tui/snapshot.py` | Domain → Rich |
| `src/aa_ma/tui/json_output.py` | Domain → JSON |
| `src/aa_ma/tui/app.py` | Textual orchestration |
| `src/aa_ma/tui/screens/*.py` | Textual screens |
| `src/aa_ma/tui/widgets/*.py` | Textual widgets |
| `src/aa_ma/tui/watcher.py` | Async filesystem watch |
| `src/aa_ma/tui/app.tcss` | Styling |
| `src/aa_ma/tui/__main__.py` | argparse + dispatch |
| `docs/adr/0007-aa-ma-tui-tracker.md` | Architecture Decision Record |

---

## Plan Review History

- **CEO Review:** Skipped (focused dev-tool addition; not a product pivot).
- **Eng Review:** Embedded in the user-approved high-level design table (Phase 2 brainstorm).
- **Design Review:** Auto-skipped (no frontend files).
- **Plan Verification (Phase 4.5):** **EXECUTED 2026-05-17** in interactive mode. 4 of 6 angles run (Wave 1 only — Wave 2 skipped after Wave 1 surfaced sufficient signal).
  - Angle 1 (Ground-truth): 17/20 OK, 3 WARNING (library versions deferred to M0 sync), 0 CRITICAL.
  - Angle 2 (Assumptions): 3 CRITICAL, 3 WARNING, 4 VERIFIED — all addressed in revised plan above.
  - Angle 3 (Impact): 4 CRITICAL, 4 WARNING, 6 OK — all addressed in revised plan above.
  - Angle 4 (Falsifiability): 45/47 criteria falsifiable (95.7%), 2 rewritten in revised plan, 0 banned phrases in acceptance criteria.
  - Angle 5 (Fresh-agent) + Angle 6 (Specialist domains incl. Engineering Standards): **deferred** — Wave 1 captured the substantive issues; deferring saves ~60k tokens.

---

## Plan Revisions Applied (from Phase 4.5 findings)

| Wave-1 Finding | Resolution |
|---|---|
| `pydantic` claimed-as-dep but actually transitive only | M0 T0.1 now CREATES `[project] dependencies` array with explicit `pydantic>=2,<3` |
| "8 active tasks" motivation false (all 8 in `completed/`) | Context rewritten; smoke commands use `--include-completed`; new `--include-completed` flag added |
| Hand-edit `pyproject.toml` + `CHANGELOG.md` conflicts with dual commitizen + semantic-release | M0 defers version bump; M4 uses `uv run cz bump --increment MINOR` (atomic update of `pyproject.toml` + `VERSION` + `CHANGELOG.md`) |
| `VERSION` file omitted | Added to M4 file list (managed by `cz bump`) |
| `CLAUDE.md` has no "Tools" section | Section name corrected to `## Build & Development Commands` |
| ADR INDEX.md "if exists" — actually exists | M4 explicit task and acceptance criterion |
| CHANGELOG `### Added` vs `### Feat` | Confirmed `### Feat` (conventional-commit style; `cz bump` writes it) |
| `[project] dependencies` does not currently exist | Acceptance criterion: M0 must CREATE it, not add to it |
| Status enum: only `ACTIVE`/`COMPLETE` seen; Mode/Gate absent | Defaults in dataclass handle absence; parser tolerance is explicit M1 criterion |
| M2 "share parser" unfalsifiable | Rewritten to `is`-identity assertion across modules |
| M3 "never crashes" unfalsifiable | Rewritten as bounded `run_test(size=...)` + `PARSE_ERROR` literal check |

**Outstanding open items** (NOT fixed; intentionally accepted in v0.10.0):
- No CI workflow runs `pytest tests/tui/` (only `security.yml` exists). Local-pytest is the gate; CI workflow is backlog. KISS.
- Textual as a runtime dep (rather than an `aa-ma[tui]` extras pattern). v1 keeps single install path; extras refactor is future work if dep weight becomes a complaint.

---

## Time Estimates

- M0: 30 min
- M1: 4 h
- M2: 4 h
- M3: 8 h
- M4: 2 h
- **Total v0.10.0:** ~18.5 h (one focused engineering week, ~3 days at concentrated pace)
- M5 (optional): 4 h, deferred to v0.11.0 backlog

---

**Plan complete.** Next: Phase 4.5 verification (interactive mode — read-only) before ExitPlanMode.
