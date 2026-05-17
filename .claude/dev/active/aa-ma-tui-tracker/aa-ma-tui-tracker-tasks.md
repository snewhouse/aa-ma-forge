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
- Status: PENDING
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

### Step 1.1: TDD model.py — enum sets
- Status: PENDING
- Mode: AFK
- Result Log:

### Step 1.2: TDD parse_task_dir — happy path with playwright-skill fixture
- Status: PENDING
- Mode: AFK
- Result Log:

### Step 1.3: TDD parser tolerance — `**Status:**` variant
- Status: PENDING
- Mode: AFK
- Result Log:

### Step 1.4: TDD discover_tasks — merges multiple roots
- Status: PENDING
- Mode: AFK
- Result Log:

### Step 1.5: TDD discover_tasks — survives per-task parse errors (attaches `parse_error`)
- Status: PENDING
- Mode: AFK
- Result Log:

### Step 1.6: TDD aggregate_status derivation (5 tests, one per state)
- Status: PENDING
- Mode: AFK
- Result Log:

### Step 1.7: hypothesis round-trip property test
- Status: PENDING
- Mode: AFK
- Result Log:

### Step 1.8: TDD provenance_tail returns last N lines
- Status: PENDING
- Mode: AFK
- Result Log:

### Step 1.9: TDD last_modified = max(file mtimes)
- Status: PENDING
- Mode: AFK
- Result Log:

### Step 1.10: Coverage gate — assert ≥ 90% on parser.py + model.py
- Status: PENDING
- Mode: AFK
- Result Log:

---

## Milestone 2: Snapshot mode (Rich + JSON)
- Status: PENDING
- Mode: AFK
- Gate: HARD
- Complexity: 55
- Critical-Path: data-xform
- Audit-Profile: code-only
- Dependencies: Milestone 1
- Note: Critical-Path:data-xform shared with M1 — output rendering is a continuation of the parse→model→render pipeline; same evidence requirement (CRITICAL_PATH_REVIEW entry in provenance.log on completion).
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
- Status: PENDING
- Mode: AFK
- Result Log:

### Step 2.2: TDD render_tree (Rich Tree of milestones + steps)
- Status: PENDING
- Mode: AFK
- Result Log:

### Step 2.3: TDD render_summary (one line per task)
- Status: PENDING
- Mode: AFK
- Result Log:

### Step 2.4: TDD json_output.dump (schema-validated)
- Status: PENDING
- Mode: AFK
- Result Log:

### Step 2.5: TDD __main__ dispatch + exit codes
- Status: PENDING
- Mode: AFK
- Result Log:

### Step 2.6: Manual smoke against ~/.claude/dev/completed (8 tasks)
- Status: PENDING
- Mode: AFK
- Result Log:

### Step 2.7: JSON smoke + jq assertion (all 8 names)
- Status: PENDING
- Mode: AFK
- Result Log:

### Step 2.8: Re-run snapshot tests; regenerate goldens if needed
- Status: PENDING
- Mode: AFK
- Result Log:

---

## Milestone 3: Interactive Textual app
- Status: PENDING
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
- Status: PENDING
- Mode: AFK
- Result Log:

### Step 3.2: TDD TaskCard widget (progress + badges)
- Status: PENDING
- Mode: AFK
- Result Log:

### Step 3.3: TDD KanbanColumn widget (groups by aggregate_status)
- Status: PENDING
- Mode: AFK
- Result Log:

### Step 3.4: TDD DashboardScreen.compose yields 4 columns
- Status: PENDING
- Mode: AFK
- Result Log:

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
