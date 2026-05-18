# aa-ma-tui-tracker Tasks (HTP)

> Hierarchical Task Plan. Update `Status:` and `Result Log:` immediately after each sub-step (L-080–082). HARD gates refuse milestone completion while any PENDING sub-step remains.

Created: 2026-05-17

---

## Milestone 0: Scaffolding
- Status: COMPLETE
- Mode: AFK
- Gate: SOFT
- Complexity: 15
- Audit-Profile: code-only
- TDD-Waiver: tooling-config
- Dependencies: None
- Result Log: All 6 sub-steps COMPLETE. 5/5 acceptance criteria verified empirically (--version exit 0, import succeeds, 4 deps resolved within constraints, [project] dependencies array present, lint-imports KEPT 2 contracts). No regressions (659 tests pass). TDD-Waiver applied at milestone level: scaffolding milestone, no behavior to test beyond smoke (no `tests/` commits expected for M0; tdd-sequence-auditor should honor this).
- Acceptance Criteria:
  - `uv run aa-ma-tui --version` exits 0 with non-empty version string
  - `python -c "import aa_ma.tui"` succeeds
  - `uv.lock` shows `textual`, `rich`, `watchfiles`, `pydantic` resolved
  - `pyproject.toml` contains a `[project] dependencies` array (which did not exist before M0)
  - `lint-imports` (import-linter) exits 0 (root_package is `codemem`, so `aa_ma.tui` is out of scope — trivially passes)

### Step 0.1: Create `[project] dependencies` array in pyproject.toml
- Status: COMPLETE
- Mode: AFK
- TDD-Waiver: tooling-config
- Result Log: Added `[project] dependencies = [...]` array at pyproject.toml:18-25 with 4 pinned runtime deps: `pydantic>=2,<3`, `textual>=0.80,<1.0`, `rich>=13,<14`, `watchfiles>=0.21,<1.0`. Each declared explicitly per L-055 (no implicit transitives for direct imports). Inline comments cite source lesson and target milestone. Verified via `sed -n '11,32p'`.

### Step 0.2: Add `[project.scripts] aa-ma-tui = "aa_ma.tui.__main__:main"` to pyproject.toml
- Status: COMPLETE
- Mode: AFK
- TDD-Waiver: tooling-config
- Result Log: Added `[project.scripts]` block at pyproject.toml:27-29 with `aa-ma-tui = "aa_ma.tui.__main__:main"`. Entry point will resolve once T0.4/T0.5 create the package files. Verified via `sed -n '11,32p'`.

### Step 0.3: Document deferred version-bump (M4 cz bump owns it)
- Status: COMPLETE
- Mode: AFK
- TDD-Waiver: tooling-config
- Result Log: Added 4-line `# NOTE:` comment above pyproject.toml `version` field. Explicit warning "Do NOT hand-edit", points to commitizen as owner, names M4 ship vehicle (`cz bump --increment MINOR`), and cross-references context-log Decision 6. Preserves Wave-1 CRITICAL fix (no dual cz+semantic-release conflict).

### Step 0.4: Create `src/aa_ma/tui/__init__.py` (re-export `__version__`)
- Status: COMPLETE
- Mode: AFK
- Result Log: Created `src/aa_ma/tui/__init__.py` (17 lines). Re-exports `__version__` from parent `aa_ma` (sourced via `importlib.metadata.version("aa-ma")`, so values cannot drift). Docstring lists M0 contract + which modules land in M1/M2/M3 per reference.md. `__all__` declared.

### Step 0.5: Create skeletal `src/aa_ma/tui/__main__.py` (argparse only; `main()` prints version, exits 0)
- Status: COMPLETE
- Mode: AFK
- Result Log: Created `src/aa_ma/tui/__main__.py` (52 lines). Provides `main(argv=None) -> int` with argparse `--version` action (prints `aa-ma-tui {version}`, exits 0). `_build_parser()` factored out as M2/M3 extension point (SOLID Open/Closed). `if __name__ == "__main__"` block uses `sys.exit(main())` so `python -m aa_ma.tui` also works. No pydantic/textual/rich/watchfiles imports — those land in M1+.

### Step 0.6: `uv sync` + `uv run aa-ma-tui --version` smoke + commit
- Status: COMPLETE
- Mode: AFK
- Result Log: `uv sync` ran clean — resolver picked pydantic 2.12.5, textual 0.89.1, rich 13.9.4, watchfiles 0.24.0 (all within plan constraints). Re-resolution downgraded transitives `rich 14.3.3→13.9.4`, `watchfiles 1.1.1→0.24.0`, `python-semantic-release 10.5.3→9.21.0`, `python-gitlab 6.5.0→4.13.0` — verified safe: no `from rich`/`from watchfiles`/`from gitlab` in src/packages/scripts; semantic-release pin `>=9.0` still satisfied. Smoke: `uv run aa-ma-tui --version` → `aa-ma-tui 0.9.0` exit 0 ✓; `python -c "import aa_ma.tui"` ✓; full pytest 659 passed / 1 skipped / 6 deselected ✓; `ruff check src/aa_ma/tui/` clean ✓; `lint-imports` 2 contracts kept, 0 broken ✓. Commit pending in this turn.

---

## Milestone 1: Parser foundation
- Status: COMPLETE
- Mode: AFK
- Gate: HARD
- Complexity: 60
- Critical-Path: data-xform
- Audit-Profile: code-only
- Dependencies: Milestone 0
- Acceptance Criteria:
  - `Task`, `Milestone`, `Step` Pydantic models with documented enums (`MilestoneStatus`, `StepStatus`, `Mode`, `Gate`, `AggregateStatus`) — every value justified per L-065
  - `parse_task_dir(path: Path) -> Task` raises `ParseError` on malformed input
  - `discover_tasks(roots) -> list[Task]` never raises; populates `parse_error` field on per-task failure
  - Parser tolerates `- Status:` and `**Status:**` variants
  - Parser tolerates absent `Mode:` and `Gate:` (uses defaults `AFK` / `SOFT`)
  - Coverage ≥ 90% on `parser.py` + `model.py`
  - hypothesis round-trip property test passes
- Result Log: All 7 acceptance criteria verified empirically. 30 tests added (29 unit + 1 hypothesis property, 50 examples). Coverage parser.py 91% / model.py 100%. Full suite 688+3 slow / 1 skipped — no regressions. HARD gate approved by user via AskUserQuestion. CRITICAL_PATH_REVIEW evidence in provenance.log. See context-log.md `[2026-05-17] Milestone Completion: M1 Parser foundation` for full summary.

### Step 1.1: TDD model.py — enum sets
- Status: COMPLETE
- Mode: AFK
- Result Log: RED→GREEN: wrote `tests/tui/test_model.py` (9 tests) covering all 5 enum sets + Pydantic model constructors + ParseError raisability. RED confirmed (ModuleNotFoundError × 9). Created `src/aa_ma/tui/model.py` (228 lines) with `MilestoneStatus` (5 values), `StepStatus` (4 values; ACTIVE coerced to IN_PROGRESS at parse time per spec), `Mode`, `Gate`, `AggregateStatus` (5 values, per-state docstring per L-065). Pydantic v2 models: `Step` frozen, `Milestone` frozen w/ defaults Gate.SOFT + Mode.AFK, `Task` mutable for derived field. GREEN: 9/9 PASS.

### Step 1.2: TDD parse_task_dir — happy path with playwright-skill fixture
- Status: COMPLETE
- Mode: AFK
- Result Log: RED→GREEN: wrote `test_parse_complete_task` asserting playwright-skill parses to ≥1 milestone, M1 = "Core Skill File (SKILL.md)" / status COMPLETE / complexity 45, S1.1 status COMPLETE / result_log contains "playwright-testing". RED confirmed (ModuleNotFoundError). Created `src/aa_ma/tui/parser.py` (347 lines) with regex-based grammar mirroring `plan_markers/parser.py` style, factored `_field_pattern()` helper for L-052 tolerance. GREEN: 1/1 PASS.

### Step 1.3: TDD parser tolerance — `**Status:**` variant
- Status: COMPLETE
- Mode: AFK
- Result Log: Added 3 tests: bold-pair `**Status:**`, absent-Status default→PENDING, blank-Result-Log→None. All PASSED on first run — `_field_pattern()` helper from T1.2 already covered the L-052 tolerance surface by design. Tests now serve as regression guards. Used fixtures: edge-bold-status, edge-no-status, edge-blank-result. GREEN: 3/3 PASS (4/4 total).

### Step 1.4: TDD discover_tasks — merges multiple roots
- Status: COMPLETE
- Mode: AFK
- Result Log: RED→GREEN: 3 tests — merges 2 roots, empty root returns [], nonexistent root silently skipped. RED confirmed (ImportError: discover_tasks). Added `discover_tasks(roots)` to parser.py with per-root sub-dir iteration + try/except for parse-error tolerance (T1.5 pre-built). Dedup via `seen: dict[Path, Task]` keyed on `child.resolve()`. GREEN: 3/3 PASS (7/7 total).

### Step 1.5: TDD discover_tasks — survives per-task parse errors (attaches `parse_error`)
- Status: COMPLETE
- Mode: AFK
- Result Log: Added 2 tests: malformed-tasks-md fixture + missing-tasks-file dir. Both PASSED first run — T1.4 GREEN included the try/except path that constructs `Task(aggregate_status=ERROR, parse_error=str(exc))`. Used edge-malformed fixture (intentionally no `## Milestone N:` headers → parser raises ParseError → discover_tasks wraps). GREEN: 2/2 PASS (9/9 total).

### Step 1.6: TDD aggregate_status derivation (5 tests, one per state)
- Status: COMPLETE
- Mode: AFK
- Result Log: RED→GREEN: 5 state-specific tests (PENDING/IN_PROGRESS/BLOCKED/COMPLETE/ERROR) + 1 end-to-end on playwright-skill fixture. RED confirmed (5/6 fail; only PENDING trivially passed since it's the default). Added `@model_validator(mode='after')` on Task to derive aggregate_status with precedence: parse_error→ERROR, any BLOCKED→BLOCKED, all COMPLETE→COMPLETE, any in-flight→IN_PROGRESS, else PENDING. Uses `object.__setattr__` to mutate (non-frozen Task model). GREEN: 6/6 PASS (15/15 total).

### Step 1.7: hypothesis round-trip property test
- Status: COMPLETE
- Mode: AFK
- Result Log: Created `tests/tui/test_parser_properties.py` (164 lines). Hypothesis strategy generates between 1-4 milestones, each with 0-3 steps, random plain/bold-pair `Status:` form (exercises L-052 surface). Marked `@pytest.mark.slow` per pyproject convention. `@settings(deadline=None, max_examples=50, suppress_health_check=[function_scoped_fixture])`. Round-trip assertions: parsed milestone count, status enum, gate, mode, complexity, step count, step status. 50 examples PASS in 0.26s. Run via `uv run pytest -m slow`.

### Step 1.8: TDD provenance_tail returns last N lines
- Status: COMPLETE
- Mode: AFK
- Result Log: RED→GREEN: 3 tests — playwright-skill real fixture has 11 non-blank prov-log lines, last 5 returned with "PLAN COMPLETE" terminal entry; missing log → []; short log (<5 lines) returns all. RED confirmed (`provenance_tail=[]` default fails for real fixture). Added `_provenance_tail(path, name, n=5)` helper + wired into `parse_task_dir` return. GREEN: 3/3 PASS.

### Step 1.9: TDD last_modified = max(file mtimes)
- Status: COMPLETE
- Mode: AFK
- Result Log: RED→GREEN: 2 tests — explicit `os.utime` on 5 files asserts max wins; solo-tasks.md only asserts solo mtime returned. RED confirmed (`last_modified=None`). Added `_max_mtime(path, name)` helper iterating `_AA_MA_FILE_SUFFIXES` constant (DRY for the 5 canonical file names) + wired into `parse_task_dir` return. Returns timezone-aware UTC datetime. GREEN: 2/2 PASS.

### Step 1.10: Coverage gate — assert ≥ 90% on parser.py + model.py
- Status: COMPLETE
- Mode: AFK
- Result Log: Added `pytest-cov>=5.0` to dev-deps (was missing — plan gap, not declared at T0). Ran `uv run pytest tests/tui/ --cov=aa_ma.tui --cov-report=term-missing`: **model.py 100% (77/77 stmts), parser.py 91% (125/138 stmts)**. Both exceed 90% gate. Missing lines in parser.py are defensive ValueError fallbacks inside the `_extract_*` helpers (lines 88-89, 102, 105-106, 117-118, 129-130, 141-142, 236, 328) — unreachable from current fixtures but kept for robustness. `__main__.py` shows 0% (M0 scaffolding; M2/M3 will exercise). Full suite: 688/689 pass / 1 skipped (no regressions). Ruff clean, lint-imports KEPT 2 contracts.

---

## Milestone 2: Snapshot mode (Rich + JSON)
- Status: COMPLETE
- Mode: AFK
- Gate: HARD
- Complexity: 55
- Critical-Path: data-xform
- Audit-Profile: code-only
- Dependencies: Milestone 1
- Note: Critical-Path:data-xform shared with M1 — output rendering is a continuation of the parse→model→render pipeline; same evidence requirement (CRITICAL_PATH_REVIEW entry in provenance.log on completion).
- Result Log: All 8 acceptance criteria verified. 27 new tests added (19 snapshot + 7 json + 8 dispatch — minus 1 overlap = 34 unique; +19 net to full suite: 715 pass vs 688 in M1). tui package coverage 94% (model.py 100%, snapshot.py 100%, json_output.py 100%, __main__.py 88%, parser.py 91%). HARD gate approved by user. CRITICAL_PATH_REVIEW evidence in provenance.log. Live smoke against `~/.claude/dev/completed/`: 8 tasks discovered, 6 render in board view (COMPLETE/IN_PROGRESS), 2 fall to ERROR aggregate status due to legacy `## Step N:` / `## M1:` milestone-header variants (caught gracefully by discover_tasks try/except; tracked as D-M2-1 parser-tolerance backlog). JSON envelope includes all 8 names + schema_version=1.
- Acceptance Criteria:
  - `aa-ma-tui --snapshot` renders 4-column Rich kanban
  - `aa-ma-tui --snapshot=tree --task NAME` renders Rich Tree
  - `aa-ma-tui --snapshot=summary` one line per task
  - `aa-ma-tui --json` validates against `Task.model_json_schema()`
  - All four modes call the SAME `discover_tasks` function object (per L-052)
  - Exit codes: 0 / 2 (task not found) / 3 (no tasks)
  - `--include-completed` flag works against `~/.claude/dev/completed/`
  - Golden snapshots match for board/tree/summary

### Step 2.1: TDD render_board (golden file)
- Status: COMPLETE
- Mode: AFK
- Result Log: RED→GREEN: 4 tests (golden equality, status grouping, empty-list, discover_tasks reuse). RED via ModuleNotFoundError. Implemented `render_board(tasks)` using Rich Columns of 4 Panels (PENDING/IN_PROGRESS/BLOCKED/COMPLETE). Each panel lists task cards with `X/Y steps · M/N ms`. ERROR-status tasks deliberately excluded from board (M3 surfaces them as PARSE_ERROR badges). Console pinned at width=120 + `file=io.StringIO()` to prevent double-print (bug caught in T2.6). Golden bootstrapped on first run, locked on second. GREEN: 4/4.

### Step 2.2: TDD render_tree (Rich Tree of milestones + steps)
- Status: COMPLETE
- Mode: AFK
- Result Log: RED→GREEN: 4 tests (golden, milestone titles present, step numbers present, result_log truncated at 60 chars). Implemented `render_tree(task)` using Rich Tree: top = name+aggregate, branches = milestones with `M{n}: {title} [{status}]`, leaves = steps with `{n.m} {title} [{status}] — {first_60_chars}…`. `_RESULT_LOG_PREVIEW_CHARS = 60` named constant. GREEN: 4/4.

### Step 2.3: TDD render_summary (one line per task)
- Status: COMPLETE
- Mode: AFK
- Result Log: RED→GREEN: 3 tests (golden, one-line-per-task count, metadata fields present). Implemented `render_summary(tasks)` emitting `NAME  [status]  X/Y steps  M/N ms  · YYYY-MM-DD` per line. Helpers `_step_progress()` + `_milestone_progress()` factored out (DRY — also used by `_task_card` in render_board). GREEN: 3/3.

### Step 2.4: TDD json_output.dump (schema-validated)
- Status: COMPLETE
- Mode: AFK
- Result Log: RED→GREEN: 7 tests (SCHEMA_VERSION constant, dump returns str, schema_version in envelope, all names present, jsonschema validates per task, golden semantic equality, discover_tasks reuse). Added `SCHEMA_VERSION: int = 1` to model.py with bumping-policy docstring (per M2 plan risk #2). Created `json_output.dump(tasks)` returning `{"schema_version": 1, "tasks": [task.model_dump(mode='json') for t in tasks]}` with `indent=2, sort_keys=True`. Each task validated against `Task.model_json_schema()` via `jsonschema.validate` (jsonschema 4.26.0 already installed transitively). GREEN: 7/7.

### Step 2.5: TDD __main__ dispatch + exit codes
- Status: COMPLETE
- Mode: AFK
- Result Log: RED→GREEN: 8 tests covering board/tree/summary/json dispatch + exit codes 0/2/3 + --include-completed + --root + no-flag fallthrough. Implemented argparse with `--snapshot[=board|tree|summary]` (const='board'), `--json`, `--task NAME`, `--include-completed`, `--root PATH`. Exit code constants `EXIT_OK=0, EXIT_TASK_NOT_FOUND=2, EXIT_NO_TASKS=3` as single source of truth. `_resolve_roots()` hybrid layout detection: if `<root>/dev/active` exists → `.claude`-style project root traversal; else → direct scan root (preserves test convenience). GREEN: 8/8.

### Step 2.6: Manual smoke against ~/.claude/dev/completed (8 tasks)
- Status: COMPLETE
- Mode: AFK
- Result Log: `uv run aa-ma-tui --snapshot=summary --include-completed --root ~/.claude` exit 0; 8 tasks displayed: aa-ma-team-guide [COMPLETE] · agent-token-optimization [ERROR] · galactic-skills-review [IN_PROGRESS] · playwright-skill [COMPLETE] · safety-app-production-settings [ERROR] · security-quality-remediation [COMPLETE] · ultraplan-agent-teams-hardening [COMPLETE] · ultraplan-enhancement [IN_PROGRESS]. The 2 ERROR tasks use legacy `## Step N:` (agent-token-optimization) and `## M1:` (safety-app-production-settings) milestone-header variants — discover_tasks correctly wraps them in Task(aggregate_status=ERROR, parse_error=...) so the pipeline doesn't collapse. Per scope discipline (L-007), parser-tolerance extension is out of M2 scope; tracked as D-M2-1 backlog for v0.11.0. **Critical bug discovered + fixed during smoke**: `Console(record=True).print()` was writing to stdout AND recording → `print(console.export_text())` doubled every snapshot. Fix: `file=io.StringIO()` on Console init to suppress stdout; export_text remains intact. Tests didn't catch this because they called `render_X()` directly and inspected the string return, not via CLI which `print()`s on top. Added defensive note in snapshot.py docstring.

### Step 2.7: JSON smoke + jq assertion (all 8 names)
- Status: COMPLETE
- Mode: AFK
- Result Log: `uv run aa-ma-tui --json --include-completed --root ~/.claude | jq -r '.tasks[] | .name' | sort` → all 8 expected names present (aa-ma-team-guide, agent-token-optimization, galactic-skills-review, playwright-skill, safety-app-production-settings, security-quality-remediation, ultraplan-agent-teams-hardening, ultraplan-enhancement). `jq '.tasks | length'` = 8. `jq '.schema_version'` = 1. JSON envelope includes ERROR-status tasks (unlike board view), proving discover_tasks' parse-error wrapping reaches the JSON consumer faithfully.

### Step 2.8: Re-run snapshot tests; regenerate goldens if needed
- Status: COMPLETE
- Mode: AFK
- Result Log: Full re-run after StringIO fix + ruff format: 715 default + 3 slow pass / 1 skipped (no regressions; +27 from M1 baseline of 688). tui package coverage 94% overall (model.py 100%, snapshot.py 100%, json_output.py 100%, parser.py 91%, __main__.py 88%). Goldens preserved (board.txt, tree.txt, summary.txt, data.json — all committed in this milestone). No regeneration needed (StringIO change is render-output-neutral; the export_text string is identical before/after). Ruff lint clean, ruff format applied to 4 files, lint-imports 2/2 KEPT.

---

## Milestone 3: Interactive Textual app
- Status: ACTIVE
- Mode: AFK
- Gate: HARD
- Complexity: 75
- Critical-Path: external-api
- Prototype-Required: YES
- Audit-Profile: code-only
- Dependencies: Milestone 2
- Acceptance Criteria:
  - `aa-ma-tui` launches Textual app
  - DashboardScreen shows 4-column kanban with task cards (name, progress bar, M/N ms, X/Y steps, badges)
  - Keybindings work (↑/↓/Enter/r/q/?//)
  - TaskDetailScreen drill-in with milestone Tree + Result Log preview + provenance tail
  - File-watch via `awatch(debounce=300)` refreshes affected task only
  - Bounded malformed-input tolerance: `run_test(size=(120,40))` completes within 2s + `PARSE_ERROR` literal in render
  - pytest-textual-snapshot smoke test of both screens

### Step 3.1: Prototype spike — Textual+watchfiles integration (LOGIC variant)
- Status: COMPLETE
- Mode: AFK
- Result Log: Invoked `Skill(prototype)` LOGIC variant per engineering-standards §1 (Prototype-Required: YES). Built `prototypes/m3_textual_watchfiles_spike.py` (~200 lines) — single file with portable reducer (`AAMAFilter(DefaultFilter)` + `reduce_watch_event(state, changes) -> (state, affected)`) and throwaway Textual shell. Auto-driver uses `app.run_test()` pilot mode (headless WSL terminal). Run cmd: `uv run python prototypes/m3_textual_watchfiles_spike.py`. **VERDICT: PASS** — all 4 integration concerns validated empirically: (1) awatch ran inside @work without blocking; (2) `mutate_reactive(SpikeApp.events)` triggered watch_events handler — confirms class-attribute reference pattern; (3) AAMAFilter suppressed `ignored.txt` + `.hidden.md` noise (whitelist by 5 canonical suffixes from reference.md); (4) debounce=300ms coalesced 5-write burst into single event. Portable patterns lift directly into M3 production: AAMAFilter → `watcher.py`, reduce_watch_event → `watcher.py`, @work+mutate_reactive pattern → `app.py`. Prototype deletion deferred to M3 close (Step 3.12) per the LOGIC.md "delete-or-absorb" rule.

### Step 3.2: TDD TaskCard widget (progress + badges)
- Status: COMPLETE
- Mode: AFK
- Result Log: RED→GREEN: wrote `tests/tui/test_widgets_task_card.py` (9 tests covering: construction, Static-subclass, format-includes-name/status/step-progress/milestone-progress, Task.step_progress() exists, Task.milestone_progress() exists, empty-milestones safe). RED confirmed: `ModuleNotFoundError: No module named 'aa_ma.tui.widgets'`. GREEN: (a) Added `Task.step_progress()` + `Task.milestone_progress()` methods to model.py (single source of truth, closes M2 §6.8 W1-CR consolidation). (b) Refactored snapshot.py — removed `_step_progress` + `_milestone_progress` module helpers; `_task_card` + `render_summary` now call `task.step_progress()` / `task.milestone_progress()`. (c) Created `src/aa_ma/tui/widgets/{__init__,task_card}.py` (~50 lines). **Design correction during GREEN**: Textual's Widget class reserves `task` as Worker/@work integration name; renamed our attribute to `task_data`. Inline comment documents WHY. All 9 RED tests now GREEN. Full suite 724 pass / 1 skipped (+9 from M2 baseline of 715). No regressions in M1+M2 (snapshot.py output is bytewise-identical since the refactor is a pure delegate).

### Step 3.3: TDD KanbanColumn widget (groups by aggregate_status)
- Status: COMPLETE
- Mode: AFK
- Result Log: RED→GREEN: wrote `tests/tui/test_widgets_kanban_column.py` (7 tests: construction stores status+filtered-tasks, filtering across all 4 statuses + PENDING-empty, header includes status+count, ERROR-status dropped silently, VerticalScroll subclass, compose yields TaskCards, compose-empty yields placeholder). RED confirmed ModuleNotFoundError. GREEN: `src/aa_ma/tui/widgets/kanban_column.py` (~45 lines, KanbanColumn(VerticalScroll) with column_status + column_tasks attrs, header_text() returning "STATUS (N)", compose() yielding Label header + TaskCards or "(no tasks)" placeholder). Updated widgets/__init__.py to re-export KanbanColumn. 72 pass / 1 deselected (+7 from Step 3.2).

### Step 3.4: TDD DashboardScreen.compose yields 4 columns
- Status: COMPLETE
- Mode: AFK
- Result Log: RED→GREEN: wrote `tests/tui/test_screens_dashboard.py` (6 tests: yields-4-columns, canonical-order, task-distribution, stores-tasks, Screen subclass, BOARD_COLUMNS public+canonical). RED confirmed (ModuleNotFoundError aa_ma.tui.screens). GREEN: (a) Promoted `snapshot._BOARD_COLUMNS` to public `BOARD_COLUMNS` (replace_all rename; assertion at module level still fires; M2 reference.md docstring references are advisory only — no functional break). (b) Created `src/aa_ma/tui/screens/__init__.py` re-exporting DashboardScreen. (c) Created `src/aa_ma/tui/screens/dashboard.py` (~35 lines, DashboardScreen(Screen) with `dashboard_tasks` attr + compose() yielding Horizontal of 4 KanbanColumns from BOARD_COLUMNS). **Design discovery during GREEN**: Textual stores wrapper-ctor children in `_pending_children` pre-mount (NOT `_nodes` or `children` — those are NodeList([])). Test helper `_columns_from_compose` walks `_pending_children`. Documented via inline comment. 78 pass / 1 deselected (+6 from Step 3.3).

### Step 3.5: TDD DashboardScreen Enter → TaskDetailScreen (Pilot)
- Status: PENDING
- Mode: AFK
- Result Log:

### Step 3.6: TDD TaskDetailScreen.compose (tree + preview pane)
- Status: PENDING
- Mode: AFK
- Result Log:

### Step 3.7: TDD TaskDetailScreen arrow nav selects step
- Status: PENDING
- Mode: AFK
- Result Log:

### Step 3.8: TDD watcher.watch_roots — callback on file change
- Status: PENDING
- Mode: AFK
- Result Log:

### Step 3.9: TDD AAMAFilter — ignores unrelated files
- Status: PENDING
- Mode: AFK
- Result Log:

### Step 3.10: TDD app_smoke (pytest-textual-snapshot SVG)
- Status: PENDING
- Mode: AFK
- Result Log:

### Step 3.11: Manual smoke — interactive TUI + cross-terminal file-touch
- Status: PENDING
- Mode: HITL
- Result Log:

### Step 3.12: Coverage gate — assert tui package ≥ 80%
- Status: PENDING
- Mode: AFK
- Result Log:

---

## Milestone 4: ADR, docs, integration test, release
- Status: PENDING
- Mode: HITL
- Gate: HARD
- Complexity: 40
- Critical-Path: version-pipeline
- Audit-Profile: full
- Dependencies: Milestone 3
- Acceptance Criteria:
  - `docs/adr/0007-aa-ma-tui-tracker.md` exists with full sections
  - `docs/adr/INDEX.md` contains ADR-0007 row
  - `README.md` has `## Visualizing Active Tasks` section
  - `CLAUDE.md` has one-line under `## Build & Development Commands`
  - `CHANGELOG.md` `[0.10.0]` `### Feat` entry mentions `aa-ma-tui`
  - Integration test green
  - `/doc-sync` reports 0 CRITICAL findings
  - `git tag -l v0.10.0` returns `v0.10.0`

### Step 4.1: Draft ADR-0007
- Status: PENDING
- Mode: HITL
- Result Log:

### Step 4.2: Update INDEX.md + README.md + CLAUDE.md
- Status: PENDING
- Mode: AFK
- Result Log:

### Step 4.3: Write integration test (subprocess against temp active dir)
- Status: PENDING
- Mode: AFK
- Result Log:

### Step 4.4: /doc-sync (or Skill(doc-drift-detection)) + fix drift
- Status: PENDING
- Mode: AFK
- Result Log:

### Step 4.5: Full test suite + coverage no-regression
- Status: PENDING
- Mode: AFK
- Result Log:

### Step 4.6: HITL gate → `uv run cz bump --increment MINOR` → push --follow-tags
- Status: PENDING
- Mode: HITL
- Result Log:

---

## Milestone 5: Optional polish (DEFERRED — backlog for v0.11.0)
- Status: PENDING
- Mode: AFK
- Gate: SOFT
- Complexity: 30
- Audit-Profile: code-only
- Dependencies: Milestone 4
- Acceptance Criteria:
  - Help modal on `?`
  - Fuzzy filter on `/`
  - `--theme dark|light|auto`
  - Cleaner PARSE_ERROR rendering

(No sub-steps yet. Capture with `/gsd-add-backlog` after v0.10.0 ships, do not silent-drop.)
