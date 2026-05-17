# aa-ma-tui-tracker Context Log

> Decision history. Trade-offs. Compaction summaries. Gate approvals.

## [2026-05-17] Initial Context (Phase 1-4.5 of /aa-ma-plan)

### Feature Request
> "I'd like a way to visually keep track of work, plans, progress relating to aa-ma workflows; UI in the terminal, clean and clear, consider kanban and task lists with progress markers; KISS; research known published solutions and apply Socratic Thinking; DO NOT SKIP STEPS in aa-ma-plan"

Subsequent user inputs:
- "we can create adr" — ADR creation in scope (ADR-0007 in M4)
- "feel free to use web search, context 7 and spawn subagents" — used Context7 for Textual/watchfiles/Rich + 2 parallel Explore subagents
- After exiting plan mode: "work without stopping for clarifying questions" — autonomous mode for remainder

### Phase 1.3 Grill Protocol
Mode resolved: **simple** (no `CONTEXT.md`, no `docs/adr/` in `clauding` working dir). Note: aa-ma-forge itself HAS `docs/adr/` — but the grill resolver runs in the cwd of the plan invocation. ADR-creation path remains open via user consent.

### Phase 1.5 Lessons Scan (5 lessons surfaced)
- **L-052** — Dual-formatter rule: when N output modes share data, test ALL of them; one working doesn't prove the others work. Applied to M2 acceptance criterion (all 4 modes share `discover_tasks`).
- **L-058** — Schema completeness: count fields in actual source vs documented; applied to M1 hypothesis round-trip test.
- **L-065** — State-machine completeness: every state needs incoming + outgoing transitions; terminal states justified. Applied to `AggregateStatus` enum documentation.
- **L-080–082** — Sub-step sync rule: Result Log mandatory, never batched. This is the very rule the TUI exists to make *visible*. Applied to read-only design (don't race with executor writes).
- **L-214** — Closed code fences: opening ```` ``` ```` must have matching closing. Apply during M4 README writing.

### Phase 2 Brainstorm — Alternatives Considered

| Approach | Decision | Why |
|---|---|---|
| A. Standalone `aa-ma-tui` entrypoint in aa-ma-forge | **CHOSEN** | KISS: 1 new package, 1 script, 2 render modes share 1 parser. Leaves door open to future `aa-ma view` subcommand. |
| B. Scaffold `aa-ma` top-level CLI first, ship `aa-ma view` | Rejected | Doubles scope (top-level CLI design under feature pressure). Violates KISS. |
| C. Two binaries (`aa-ma-snap` + `aa-ma-tui`) | Rejected | Duplicates entrypoint, arg parsing, parser invocation. DRY violation; Rich is transitive of Textual anyway. |

### Phase 2.4 Engineering Standards Declaration
**All 6 themes apply.** Theme #1 (Verification): parser tested against real fixtures + prototype spike for Textual+watchfiles. Theme #2 (Dev Principles): KISS explicit user constraint + TDD discipline. Theme #3 (Reasoning): Socratic A/B/C alternatives. Theme #4 (Safety): non-breaking (additive package) + L-052/L-058/L-065/L-080–082/L-214 applied. Theme #5 (Execution Checklist): per-task HARD gates. Theme #6 (Sync & Commit): per-task Result Log + Conventional Commits with `[AA-MA Plan]` footer.

### Phase 3 Research — Context7 Library Choices

- **Textual** (`/textualize/textual`, v4.0.0–v6.6.0 in Context7; `/websites/textual_textualize_io` 3144 snippets) — `reactive()` + `watch_*` watchers, `data_bind()`, `mutate_reactive()`, `set_reactive()`, BINDINGS, DataTable, `@work` async. Pitfall: don't assign reactive in `__init__` (use `set_reactive`).
- **watchfiles** (`/samuelcolvin/watchfiles`, 92 snippets) — `awatch(path, debounce=N, stop_event=...)` async generator. `DefaultFilter` subclassable; `BaseFilter.__call__` overridable. Plan uses `AAMAFilter(DefaultFilter)` whitelisting only `*-tasks.md`, `*-plan.md`, `*-context-log.md`, `*-reference.md`, `*-provenance.log`.
- **Rich** (`/websites/rich_readthedocs_io_en_stable`, 1543 snippets) — `Progress` + `BarColumn`/`MofNCompleteColumn`/`TaskProgressColumn`, `Layout`/`Tree`/`Panel`, `Console(record=True).export_text()` for golden tests.
- **Precedent**: JiraTUI (`/whyisdifficult/jiratui`, 135 snippets) — real-world Textual+Rich TUI of work items; pattern reference for ADR-0007.

### Phase 4 Plan Generation
Generated via `superpowers:writing-plans` skill. 12-element AA-MA Planning Standard satisfied. Initial plan ~526 lines; vertical-sliced into 5 milestones (M0 scaffolding through M4 release) with M5 explicitly deferred.

### Phase 4.5 Adversarial Verification

Executed in **interactive mode** (read-only). 4 of 6 angles run (Wave 1 only).

**Wave 1 findings:**

| Angle | OK | WARNING | CRITICAL |
|---|---|---|---|
| 1. Ground-truth | 17 | 3 | 0 |
| 2. Assumption | 4 | 3 | 3 |
| 3. Impact | 6 | 4 | 4 |
| 4. Falsifiability | 45/47 | 2 | 0 |

**5 CRITICALs all addressed in plan revision:**
1. `pydantic` was claimed-as-dep but is transitive only → M0 T0.1 creates `[project] dependencies` array with explicit `pydantic>=2,<3`
2. "8 active tasks" motivation was FALSE (all 8 in `completed/`) → context rewritten + `--include-completed` flag added
3. Dual commitizen+semantic-release pipeline → M4 uses `uv run cz bump --increment MINOR` (no hand-edits)
4. `VERSION` file omitted → added to M4 file list (managed by cz)
5. `CLAUDE.md` has no "Tools" section → corrected to `## Build & Development Commands`

**Wave 2 (Angles 5–6) deferred.** Wave 1 surfaced sufficient signal; deferring saved ~60k tokens. If user wants Wave 2 before M1 starts, run `/verify-plan aa-ma-tui-tracker` from aa-ma-forge cwd.

**Open items explicitly accepted (not blockers):**
- No CI workflow runs pytest on tui — backlog item
- Textual as runtime dep (not extras) — v1 keeps single install path

### Decisions Locked

1. **Read-only**, never mutates `*-tasks.md` (respects L-080–082; avoids race with `/execute-aa-ma-*`).
2. **Ship in aa-ma-forge** (reuses `plan_parsers.py` + `plan_markers/parser.py`).
3. **Two modes, one model** (`--snapshot` Rich + Textual app share `discover_tasks`).
4. **All-tasks dashboard + drill-in** (KanbanColumn × 4, then TaskDetailScreen).
5. **`--include-completed` flag** added (default scans active/ only, but v1 demo corpus is in completed/).
6. **Version bump deferred to M4 cz** (no hand-edits in M0 to avoid commitizen/semantic_release conflict).
7. **Wave-2 verification deferred** to save tokens; run only if user requests.

### Next Action

Start execution at **M0 T0.1**: CREATE the `[project] dependencies = [...]` array in `pyproject.toml` with the 4 runtime deps. Mark Status: IN_PROGRESS in tasks.md when starting.

---

## [2026-05-17] Milestone Completion: M0 Scaffolding

- Status: COMPLETE
- Gate: SOFT — convention-based approval, no signed artifact required
- Key outcome: TUI sub-package scaffolded; runtime deps declared explicitly per L-055; CLI entry point `aa-ma-tui` registered and verified.
- Artifacts: `src/aa_ma/tui/__init__.py` (new), `src/aa_ma/tui/__main__.py` (new), `pyproject.toml` (modified — added `[project] dependencies`, `[project.scripts]`, version-pin comment), `uv.lock` (re-resolved).
- Tests: 659 passed / 1 skipped / 6 deselected. No regressions.
- Smoke: `uv run aa-ma-tui --version` → `aa-ma-tui 0.9.0` exit 0 ✓.
- TDD-Waiver applied: `tooling-config` — scaffolding milestone, no behavior to test (acceptance is the smoke result).
- Notable resolver behaviour: adding `[project] dependencies` triggered transitive re-resolution. rich 14.3.3→13.9.4 + watchfiles 1.1.1→0.24.0 (driven by our explicit `<14` / `<1.0` upper pins) + cascade downgrade python-semantic-release 10.5.3→9.21.0 (pin `>=9.0` still satisfied) + python-gitlab 6.5.0→4.13.0 (no direct usage in src/). Verified safe via grep — no `from rich`/`from watchfiles`/`from gitlab` anywhere in src/packages/scripts.
- Observation (pre-existing, out of scope for M0): `commitizen` is NOT installed in `.venv` despite `[tool.commitizen]` block in pyproject.toml. M4 T4.6 (`uv run cz bump`) will need to install or use a globally-available commitizen — flag for M4 prep.
- Next: M1 Parser foundation. HARD gate, Critical-Path: data-xform. Will require pytest+hypothesis TDD discipline.

---

_This log will be updated via context compaction as the task progresses._
