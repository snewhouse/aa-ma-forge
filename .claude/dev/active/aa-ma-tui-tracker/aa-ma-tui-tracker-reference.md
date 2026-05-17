# aa-ma-tui-tracker Reference

> Immutable facts. High-priority context. Never re-derive — always reach here first.

Created: 2026-05-17

## Repo & Versions

| Fact | Value |
|---|---|
| Repo | `~/biorelate/projects/gitlab/github_private/aa-ma-forge` |
| Branch (planning) | `main` (commit `0168d40`) |
| Package name | `aa-ma` |
| Current version | `0.9.0` (target: `0.10.0` after M4 cz-bump) |
| Python requirement | `>=3.11` |
| Build backend | `hatchling.build` |
| Package manager | `uv` (workspace with `packages/codemem-mcp`) |
| License | Apache-2.0 |

## New runtime deps (declared in M0 T0.1 — CREATES `[project] dependencies` array which does NOT exist today)

| Package | Constraint | Why |
|---|---|---|
| `pydantic` | `>=2,<3` | Typed model (Task/Milestone/Step). **Currently transitive only** — promoted to direct per L-055. |
| `textual` | `>=0.80,<1.0` | Interactive TUI framework. |
| `rich` | `>=13,<14` | Snapshot mode + Textual's renderer (transitive of textual; declared explicitly per L-055). |
| `watchfiles` | `>=0.21,<1.0` | Async file-watch for live refresh. Already in `uv.lock` as transitive of `fastmcp` — install verified. |

## New dev deps (M3 only)

| Package | Why |
|---|---|
| `pytest-textual-snapshot>=1.0` | SVG-snapshot smoke testing of Textual screens. |

## Files to reuse (do NOT re-implement)

| Path | What to use |
|---|---|
| `src/aa_ma/plan_parsers.py:139-170` | `parse_audit_profile`, `parse_tdd_waiver` — enum-tolerance pattern to mirror in `tui/parser.py` |
| `src/aa_ma/plan_parsers.py:32-58` | `CANONICAL_AUDIT_PROFILES`, `CANONICAL_TDD_WAIVERS` — reference for enum-canonical lists |
| `src/aa_ma/plan_markers/parser.py:142-161` | `parse_log(text) -> list[Marker]` — reference for line-grammar parser style |
| `src/aa_ma/plan_markers/parser.py:35` | `_EM_DASH = "—"` (U+2014) — separator convention |

## Files to create (M0–M4)

### New package

| Path | Layer | Created in |
|---|---|---|
| `src/aa_ma/tui/__init__.py` | Public API | M0 |
| `src/aa_ma/tui/__main__.py` | argparse + dispatch | M0 (skeleton), M2 (wire snapshot), M3 (default → launch app) |
| `src/aa_ma/tui/model.py` | Pydantic v2 models + enums | M1 |
| `src/aa_ma/tui/parser.py` | I/O → Domain | M1 |
| `src/aa_ma/tui/snapshot.py` | Domain → Rich | M2 |
| `src/aa_ma/tui/json_output.py` | Domain → JSON | M2 |
| `src/aa_ma/tui/app.py` | Textual orchestration | M3 |
| `src/aa_ma/tui/screens/__init__.py` | Screen package | M3 |
| `src/aa_ma/tui/screens/dashboard.py` | `DashboardScreen(Screen)` | M3 |
| `src/aa_ma/tui/screens/task_detail.py` | `TaskDetailScreen(Screen)` | M3 |
| `src/aa_ma/tui/widgets/__init__.py` | Widget package | M3 |
| `src/aa_ma/tui/widgets/task_card.py` | `TaskCard(Static)` | M3 |
| `src/aa_ma/tui/widgets/kanban_column.py` | `KanbanColumn(VerticalScroll)` | M3 |
| `src/aa_ma/tui/watcher.py` | `async def watch_roots(...)` | M3 |
| `src/aa_ma/tui/app.tcss` | Textual CSS | M3 |

### Test files

| Path | Created in |
|---|---|
| `tests/tui/__init__.py` | M1 |
| `tests/tui/conftest.py` | M1 |
| `tests/tui/fixtures/tasks/{playwright-skill,agent-token-optimization,security-quality-remediation,edge-no-status,edge-bold-status,edge-blank-result}/` | M1 |
| `tests/tui/test_model.py` | M1 |
| `tests/tui/test_parser.py` | M1 |
| `tests/tui/test_parser_properties.py` | M1 |
| `tests/tui/test_snapshot.py` | M2 |
| `tests/tui/test_json_output.py` | M2 |
| `tests/tui/snapshots/{board,tree,summary}.txt`, `data.json` | M2 |
| `tests/tui/test_widgets_task_card.py` | M3 |
| `tests/tui/test_widgets_kanban_column.py` | M3 |
| `tests/tui/test_screens_dashboard.py` | M3 |
| `tests/tui/test_screens_task_detail.py` | M3 |
| `tests/tui/test_watcher.py` | M3 |
| `tests/tui/test_app_smoke.py` | M3 |
| `tests/tui/test_integration.py` | M4 |

### Docs

| Path | Created in |
|---|---|
| `docs/adr/0007-aa-ma-tui-tracker.md` | M4 |
| `docs/adr/INDEX.md` (modify — add ADR-0007 row) | M4 |
| `README.md` (modify — add `## Visualizing Active Tasks` section) | M4 |
| `CLAUDE.md` (modify — add line under `## Build & Development Commands`) | M4 |
| `CHANGELOG.md` (touched by `cz bump`) | M4 |
| `VERSION` (touched by `cz bump`) | M4 |
| `pyproject.toml` (modify version + script + deps + auto-bump) | M0 + M4 |

## AA-MA artifact grammar (input to the tool we are building)

5 files per task, naming `{task}-{file}.{md|log}`:
- `*-plan.md` — Strategy
- `*-reference.md` — Immutable facts
- `*-context-log.md` — Decision history
- `*-tasks.md` — HTP execution roadmap (PARSER TARGET)
- `*-provenance.log` — Telemetry

Optional: `*-verification.md`, `*-tests.yaml`.

### tasks.md grammar (regex/pattern summary)

| Element | Pattern |
|---|---|
| Milestone | `^## Milestone (\d+): (.+)$` |
| Step | `^### Step (\d+\.\d+): (.+)$` |
| Status (milestone or step) | `^- (\*\*)?Status:(\*\*)?\s*(PENDING\|ACTIVE\|IN_PROGRESS\|COMPLETE\|BLOCKED)$` |
| Mode (milestone, optional) | `^- (\*\*)?Mode:(\*\*)?\s*(HITL\|AFK)$` (default AFK) |
| Gate (milestone, optional) | `^- (\*\*)?Gate:(\*\*)?\s*(SOFT\|HARD)$` (default SOFT) |
| Complexity (milestone, optional) | `^- (\*\*)?Complexity:(\*\*)?\s*(\d+)%?$` |
| Audit-Profile | `^- (\*\*)?Audit-Profile:(\*\*)?\s*(full\|code-only\|docs-only\|infra\|custom)$` |
| Result Log (step) | `^- Result Log:\s*(.+)$` |

### Status enums observed in completed/

- `Status:` actually seen: `ACTIVE`, `COMPLETE` (others in the plan's enum are aspirational / per-spec)
- `Mode:` actually seen: usually absent (default AFK)
- `Gate:` actually seen: usually absent (default SOFT)
- The parser MUST tolerate missing Mode/Gate (use Pydantic field defaults)

## Roots resolution

- Default: `<root>/.claude/dev/active/`
- With `--include-completed`: `<root>/.claude/dev/active/` + `<root>/.claude/dev/completed/`
- Default `<root>` when none given: scan BOTH `./` AND `~/`
- Currently: `~/.claude/dev/active/` is EMPTY; `~/.claude/dev/completed/` holds 8 tasks (the v1 demo corpus)

## State machine (per L-065)

```
AggregateStatus = {
  PENDING:     no milestone has any non-PENDING step    (initial; reachable)
  IN_PROGRESS: at least one milestone has non-PENDING + non-COMPLETE step
  BLOCKED:     any milestone or step Status: BLOCKED
  COMPLETE:    all milestones COMPLETE                   (terminal)
  ERROR:       parse failure                             (terminal; entered via try/except in discover_tasks)
}
```

Every state has incoming + outgoing transitions; COMPLETE and ERROR are terminal with documented justification (see `model.py` docstring).

## Engineering Standards (which themes apply)

All 6 themes from `claude-code/rules/engineering-standards.md` apply. Element #12 of the plan documents the rationale per theme.

## Critical-Path values used in this plan

| Milestone | Critical-Path | Reason |
|---|---|---|
| M1 | `data-xform` | Parser correctness foundational |
| M3 | `external-api` | Filesystem-watch contract |
| M4 | `version-pipeline` | cz bump release |
| M4 | `doc-count-drift` | Tier 6 detector domain |

All values are canonical (per ADR-0005-style enum list in `plan_parsers.py`).

## TDD-Waiver values used

| Task | Waiver | Reason |
|---|---|---|
| T0.1, T0.3 | `tooling-config` | pyproject deps + scripts; no behavior to test |

## Wave-1 Verification Findings (resolved)

Phase 4.5 ran on 2026-05-17. See `aa-ma-tui-tracker-verification.md` for full audit trail. All 5 CRITICALs addressed in plan revision; 4 of 7 WARNINGs addressed; 3 explicitly accepted (CI workflow, runtime-vs-extras dep, banned-term-prose).

## M1 immutable facts (added 2026-05-17 at M1 completion)

### Public API surface

- `aa_ma.tui.model.MilestoneStatus`: 5 values (PENDING, ACTIVE, IN_PROGRESS, COMPLETE, BLOCKED)
- `aa_ma.tui.model.StepStatus`: 4 values (PENDING, IN_PROGRESS, COMPLETE, BLOCKED) — no ACTIVE; coerced from real-world `Status: ACTIVE` on steps to IN_PROGRESS at parse time
- `aa_ma.tui.model.Mode`: 2 values (HITL, AFK)
- `aa_ma.tui.model.Gate`: 2 values (SOFT, HARD)
- `aa_ma.tui.model.AggregateStatus`: 5 values (PENDING, IN_PROGRESS, BLOCKED, COMPLETE, ERROR) — last two terminal
- `aa_ma.tui.model.ParseError`: Exception subclass
- `aa_ma.tui.model.Step(number: str, title: str, status: StepStatus, result_log: str | None = None)` — frozen
- `aa_ma.tui.model.Milestone(number: int, title: str, status: MilestoneStatus, gate: Gate = SOFT, mode: Mode = AFK, complexity: int | None = None, dependencies: str | None = None, acceptance_criteria: str | None = None, steps: list[Step] = [])` — frozen
- `aa_ma.tui.model.Task(name: str, root: Path, milestones: list[Milestone] = [], aggregate_status: AggregateStatus = PENDING, last_modified: datetime | None = None, provenance_tail: list[str] = [], parse_error: str | None = None)` — mutable (model_validator mutates aggregate_status); aggregate_status DERIVED via @model_validator(mode='after')
- `aa_ma.tui.parser.parse_task_dir(path: Path) -> Task` — raises ParseError on malformed input
- `aa_ma.tui.parser.discover_tasks(roots: list[Path]) -> list[Task]` — never raises; wraps per-task failures

### Module-private constants (M2/M3 may reuse)

- `aa_ma.tui.parser._AA_MA_FILE_SUFFIXES` — canonical 5-file suffix tuple
- `aa_ma.tui.parser._PROVENANCE_TAIL_DEFAULT = 5`
- `aa_ma.tui.parser._field_pattern(field_name) -> re.Pattern` — L-052 tolerance helper

### Test fixtures (committed at M1)

`tests/tui/fixtures/tasks/`:
- 3 real-world copies from `~/.claude/dev/completed/`: `playwright-skill`, `agent-token-optimization`, `security-quality-remediation`
- 4 synthetic edges: `edge-no-status`, `edge-bold-status`, `edge-blank-result`, `edge-malformed`

### Dev dep added in M1 (was missing from plan)

- `pytest-cov>=5.0` (required for M1 AC #6 coverage gate)

_Last Updated: 2026-05-17_
