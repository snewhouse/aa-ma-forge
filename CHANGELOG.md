# Changelog

All notable changes to this project will be documented in this file.

This project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Feat

- **`aa-ma-tui` — Read-only Textual TUI + Rich snapshot for AA-MA task tracking** (ADR-0007). New `src/aa_ma/tui/` sub-package + `aa-ma-tui` CLI entry. Five sub-modules (`model`, `parser`, `snapshot`, `json_output`, `app`), 2 screens (`DashboardScreen` 4-column kanban + `TaskDetailScreen` milestone Tree + Result Log preview + provenance tail), 2 widgets (`TaskCard`, `KanbanColumn`), `watcher.py` driving `watchfiles.awatch(debounce=300)` + `AAMAFilter` via Textual `@work(exclusive=True)`. Strict read-only — never writes to `*-tasks.md`, cannot race with `/execute-aa-ma-*` writers. CLI: `aa-ma-tui` (interactive) · `--snapshot[=board|tree|summary]` · `--json` · `--task NAME` · `--include-completed` · `--root PATH`. Exit codes 0/2/3. JSON envelope `{"schema_version":1, "tasks":[...]}`.
- **New runtime deps declared explicitly** (per L-055): `pydantic>=2,<3`, `textual>=0.80,<1.0`, `rich>=13,<14`, `watchfiles>=0.21,<1.0`. Two were already transitive (Rich via Textual; watchfiles via fastmcp), promoted to direct deps per policy.
- **Pydantic v2 `Task` model** gains `step_progress()` and `milestone_progress()` methods — single source of truth for counting, consumed by both snapshot renderers and TUI widgets.
- **`AAMA_FILE_SUFFIXES` and `TASKS_FILE_SUFFIX`** public constants in `aa_ma.tui.parser` — shared by `parser`, `watcher`, and `app` (L-005 mechanism-duplication consolidation).
- **`BOARD_COLUMNS`** promoted from `snapshot._BOARD_COLUMNS` to public — shared by `snapshot.render_board` and `screens/dashboard.py`. Module-level assertion forces explicit decision when `AggregateStatus` enum grows.

### Docs

- **`docs/adr/0007-aa-ma-tui-tracker.md`** — MADR-format ADR documenting the read-only Textual+Rich tracker decision (3 considered options, decision drivers, consequences, implementation notes, 6 deferred polish items).
- **`README.md`** — new `## Visualizing active tasks` section with 7-line CLI cheatsheet and link to ADR-0007.
- **`CLAUDE.md`** — `uv run aa-ma-tui` added to Build & Development Commands; Architecture block updated with full `src/aa_ma/` tree (replaces obsolete "skeleton, no logic yet" line).
- **`docs/adr/INDEX.md`** — appended ADR-0007 row.

### Dev deps

- `pytest-textual-snapshot>=1.0` (also pulled `syrupy 5.2.0` transitively) — used for SVG snapshot regression on DashboardScreen + TaskDetailScreen via `snap_compare`.

### Tests

- +60 new tests across 6 new files: `test_widgets_task_card.py` (9), `test_widgets_kanban_column.py` (7), `test_screens_dashboard.py` (10), `test_screens_task_detail.py` (9), `test_watcher.py` (13), `test_app_smoke.py` (8), `test_integration.py` (9 subprocess end-to-end). Plus 27 from M2 (snapshot/json/dispatch) + 30 from M1 (model/parser/hypothesis).
- 2 SVG golden snapshots (`tests/tui/__snapshots__/test_app_smoke/`).
- Full suite: **780 pass / 1 skipped / 7 deselected** (was 715 at v0.9.0).

### Design notes

- **KISS pop+push dashboard refresh** chosen over true reactive in-place mutation for v0.10. M5 polish target (`D-M3-1`) is the reactive replacement; current pattern is debuggable + deterministic.
- **`mutate_reactive(ClassName.attr)`** Textual convention — must reference the CLASS attribute (not `self.attr`) for `watch_*` handler to fire on in-place mutation. Validated by Step 3.1 prototype.
- **WSL2 inotify subdir-registration timing** ≥ 1 s — documented as test-module constant.
- **L-052 dual-formatter rule** satisfied by construction — all 4 render modes (board/tree/summary + JSON) call the same `discover_tasks` function object, verified by `sys.modules` identity test.

- **`/goal` integration (Claude Code)** — opt-in cross-turn drive-to-completion across two surfaces:
  - **`/execute-aa-ma-full` §2.5 Goal Synthesis & Bind** — synthesises a Haiku-evaluable condition from `plan.md` Acceptance Criteria (referencing observable artefacts: `provenance.log`, `tasks.md` Status, git tags, test exit codes) with a turn-cap derived from milestone count (`max(4, ceil(min(pending * 1.5, 30)))`). Surfaces condition + cap via `AskUserQuestion` [Bind / Edit / Skip] before binding `/goal`. Logs `GOAL_BOUND`, `GOAL_BIND_DECLINED`, or `GOAL_SYNTHESIS_SKIPPED` to provenance. Final `GOAL_FINAL` line at task completion.
  - **`/verify-plan --iterate` Step 4.5 Iterate Mode** — bounded iteration loop (cap 3) that re-runs adversarial 6-angle verification, appends new Verdict blocks (audit trail preserved), revises plan files between iterations, terminates on GREEN-with-0-Criticals or cap exhaustion. Logs `VERIFY_ITERATE` to provenance.
- **New skill `goal-condition-synthesis`** — produces falsifiable `/goal` conditions from AA-MA plan artefacts. Enforces observable-artefact rule (≥ 2 references), rejects vague conditions at construction time, validates turn-cap ≤ 30 and condition length ≤ 4 000 chars, owns the canonical verdict-token enum. Consumed by `/execute-aa-ma-full` §2.5 and `/verify-plan --iterate`.
- **Python helper `aa_ma.goal_synthesis`** — testable reference implementation of the synthesis algorithm (`turn_cap`, `validate_condition`, `count_observable_artifacts`, `condition_hash`). Unit-tested in `tests/test_goal_synthesis.py`.
- **Optional `PHASE_4.7` plan-marker** — records goal-condition synthesis when performed during a plan run. Forward-compatible (older parsers warn-and-ignore).

### Docs

- **`docs/spec/aa-ma-team-guide.md` §2.7 AFK Mode + `/goal` Cookbook** — integration walkthrough with worked example (`add-jwt-auth` autonomous run), anti-patterns, when-NOT-to-use, audit one-liner, protocol-toggle table.
- **`docs/spec/aa-ma-quick-reference.md`** — new "`/goal` Integration" table summarising the two surfaces; canonical references point to `Skill(goal-condition-synthesis)`.
- **`claude-code/skills/aa-ma-execution/SKILL.md` §IX.5 Goal-Condition Synthesis Patterns** — operator reference; cites synthesis SKILL as the canonical source for templates, vocabulary, and observable artefacts.
- **`docs/spec/claude-code-foundations.md`** — Skills 18 → 19, new `goal-condition-synthesis` row.
- **`SECURITY.md`** — Skills 18 → 19, list updated.
- **`README.md`** — capabilities bullet for goal-driven autonomous execution; Skills table appends `goal-condition-synthesis`.

### Design notes

- `/goal` integration is **opt-in everywhere**. Existing AA-MA workflows that pre-date `/goal` are unaffected.
- Goals live at the **task** level (one per session). aa-ma-forge does not attempt to make `/goal` milestone-scoped — that would conflict with Claude Code's one-goal-per-session model.
- A per-milestone Haiku adversary surface was prototyped and **deferred** — Claude Code does not document a synchronous Haiku evaluation API, and `/goal` is per-turn cross-turn only. Re-evaluate once either Claude Code ships such an API or aa-ma-forge defines its own `Skill(haiku-eval)` wrapper.
- Synthesis is the canonical source of the verdict-token enum, the observable-artefact list, and the turn-cap formula. The execution SKILL and team-guide link back rather than restating, to avoid drift.
- All goal-related state lands in `provenance.log`. Audit: `grep -E '^\[.*\] (GOAL_|VERIFY_ITERATE)' <task>-provenance.log`.

### Protocol toggles (agent-honoured, not hook-enforced)

- `--no-goal` flag on `/execute-aa-ma-full` — skip §2.5 for one run
- Omitting `--iterate` on `/verify-plan` — single-pass behaviour unchanged
- `/goal clear` — user-owned detach at any time
- `AA_MA_HOOKS_DISABLE=1` — disables aa-ma-forge **hooks** only (commit-signature, drift, etc.); it does **not** intercept `/goal` itself. Claude Code's `/goal` is gated separately by managed-settings keys (`disableAllHooks`, `allowManagedHooksOnly`).

## v0.9.0 (2026-05-13)

### Feat

- **skills**: vendor the `understand-codebase` onboarding skill (`SKILL.md` + 9
  `references/` companions + `templates/onboarding-team.md`), its 4
  `codebase-onboarding-*` worker agents (`conventions`, `health`, `runbook`,
  `synthesizer`), and the `/understand-codebase` command into the AA-MA Forge
  ecosystem — maintained here going forward (versioned, tested, CI-checked,
  `install.sh`-deployed). Tiered (Quick / Standard / Deep); Deep tier runs a
  `TeamCreate` agent-team; reuses (when present) `/index`, `gsd-map-codebase`,
  `/codebase-deep-dive`, `system-mapping`, `impact-analysis` rather than
  re-implementing them, degrading gracefully when those aren't installed. Full
  rationale and dependency posture in
  [ADR-0006](docs/adr/0006-understand-codebase-adoption.md).

### Docs

- **spec**: reconcile `docs/spec/claude-code-foundations.md` asset tables to
  current reality — Commands 9→10, Skills 16→18 (also picks up the v0.8.0
  `verify-impl` omission), Agents 2→11 (also picks up the five v0.8.0 audit
  agents), Hooks 2→8 (also picks up the v0.7.0/v0.8.0 hooks). Bump asset counts
  in `CLAUDE.md`, `SECURITY.md` (incl. the incidental "4→5 spec docs" fix),
  `README.md`, and `docs/spec/aa-ma-quick-reference.md`.
- **readme**: reconcile pre-existing drift inherited from v0.8.0 —
  `README.md:37` "templates for all 7 AA-MA file types" → "8 (5 standard + 3
  optional)"; `README.md:307` "ships five hooks" → "ships eight hooks"; Skills
  table append 5 missing rows (`grill-with-docs`, `prototype`,
  `understand-codebase`, `verify-impl`, `write-a-skill` — 13 → 18 entries).

## v0.8.0 (2026-05-11)

Post-impl adversarial review symmetric to `/verify-plan` — closes the asymmetry
between pre-execution rigor (6-angle plan-verification + 9 HARD gates) and
post-execution rigor (previously only one SOFT, skippable simplification
review). Adds Phase 6.8 to `/execute-aa-ma-milestone` + new `/verify-impl`
skill dispatching up to 5 parallel audit agents per plan-declared
`Audit-Profile`: `code-reviewer`, `security-auditor`, `tdd-sequence-auditor`,
`context7-evidence-auditor`, `future-proofing-auditor`. CRITICAL findings
surface via `AskUserQuestion` accept/dispute/defer panel before §7.3 user
authorization. Mechanical security checks split into a new
`security-static-check.sh` PreToolUse hook (commit-time, zero tokens),
mirroring the existing `aa-ma-commit-drift.sh` / `aa-ma-validator` split.
Grandfathered by `Created:` date — does not break in-flight plans (mirrors
v0.5.0 cutover precedent). Full architectural rationale in
[ADR-0005](docs/adr/0005-post-impl-adversarial-review.md). Project's own
lesson history (L-005 install.sh KISS violation, L-006 cz bump CHANGELOG
schema strip, L-007 sole-dev-merge format pass scope drift) maps directly to
mandatory pattern checks in the new code-reviewer agent.

### Feat

- **execute**: wire Phase 6.8 Post-Impl Adversarial Review into
  `/execute-aa-ma-milestone` (between §6.7 and §7.1, ~110 lines) and
  `/execute-aa-ma-full` (§B.6 delegation, ~21 lines) — invokes
  `Skill(verify-impl)` per the milestone's `Audit-Profile`, aggregates
  findings, surfaces CRITICAL via accept/dispute/defer panel, halts on
  BLOCKED verdict (M5)
- **verify-impl**: add `/verify-impl` skill orchestrator (~210 lines, 8-step
  execution flow, parallel/sequential dispatch per `AA_MA_AUDIT_BUDGET`) +
  5 audit-agent prompts in `claude-code/agents/` (~620 lines total) +
  `docs/templates/impl-review-template.md` (~110 lines, mirrors
  `verification-template.md` structure) (M4)
- **plan-verification**: add `Audit-Profile` + `TDD-Waiver` parsers in
  `src/aa_ma/plan_parsers.py` — `Skill(plan-verification)` Angle 6 gains
  structural checks #4 (Audit-Profile presence for v0.8.0+ plans) and #5
  (TDD-Waiver canonical values: refactor | docs-only | prototype |
  hotfix-emergency | tooling-config); novel values rejected per ADR-0005
  (mirrors `Critical-Path:` enum pattern from ADR-0001) (M3)
- **hooks**: add `security-static-check.sh` PreToolUse hook — 5 mechanical
  pattern classes (hardcoded secrets / shell injection / path traversal /
  SQL string concatenation / unsafe binary deserialisation CWE-502);
  bypassable via `AA_MA_HOOKS_DISABLE=1` master switch or
  `[security-bypass: <reason>]` marker (reason required, auditable in git
  log); registered in `scripts/install.sh` AA_MA_HOOKS array (M2)

### Test

- **plan_parsers**: 39 pytest unit cases —
  `tests/codemem/test_audit_profile_parser.py` (20 cases) + `test_tdd_waiver_parser.py`
  (19 cases) — canonical-enum validation, absence handling, bold/plain
  field-name tolerance, HTML-comment stripping, edge cases (M3)
- **plan_parsers**: 19 corpus-grandfathering cases —
  `tests/codemem/test_corpus_grandfathering.py` — runs both parsers
  against every completed plan's `tasks.md`; verifies zero false-positives
  on the 9-plan pre-v0.8.0 corpus; regex generalised to 4 milestone-heading
  variants found in real corpus (M3)
- **security-static-check**: 21 bats cases —
  `tests/hooks/security-static-check.bats` — each of 5 pattern classes
  has positive (caught) and negative (clean) case; bypass mechanisms;
  word-boundary on `git commit-tree`; non-Python file out-of-scope;
  deletion-only diff; placeholder strings; env-var reads; non-git CWD;
  shellcheck pass (M2)
- **verify-impl-agents**: 39 structural-validation pytest cases —
  `tests/skills/test_verify_impl_agents.py` — frontmatter format, SUMMARY
  trailer, severity vocabulary, grandfathering, budget modes, L-005/L-006/
  L-007 lesson references, agent-specific invariants (M4)
- **phase-6.8-integration**: 16 bats integration cases —
  `tests/hooks/execute_aa_ma_milestone_phase_6_8.bats` — section
  existence + line ordering, ADR-0005 reference, verify-impl invocation,
  grandfathering, all 5 agents named inline, 3 verdicts, override panel,
  6 bypass mechanisms, defer-creates-sub-task, bash snippet syntax,
  full-command delegation (M5)
- **Posture**: 586 pytest passed (1 skipped, 6 deselected) + 112 bats GREEN
  (96 existing + 16 new); ruff + shellcheck clean across all new files

### Docs

- **adr**: [ADR-0005](docs/adr/0005-post-impl-adversarial-review.md)
  (~260 lines) — Post-Impl Adversarial Review architectural decision;
  8 sub-decisions (D1–D7b) mapping to grilling Q1–Q7b; 4 considered
  options with pros/cons; Sub-Decisions table; Critical Files Affected;
  References (lessons L-001/L-005/L-006/L-007, ADR-0001, ADR-0003); status
  Accepted (M1)
- **spec**: `docs/spec/aa-ma-specification.md` gains
  "Optional: Post-Impl Adversarial Review Report" subsection in §II File
  Taxonomy (~90 lines) — full `[task]-impl-review.md` structure mirroring
  `verification.md`; Phase 6.8 anatomy table with file:line references
  (§6.7 L-481-541, §7.1 L-559, §7.3 L-647); 6 bypass mechanisms documented
  (M1)
- **plan-verification**: Angle 6 SKILL.md gains checks #4 (Audit-Profile)
  and #5 (TDD-Waiver) with grandfathering for 3 cutover dates (M3)
- **agents**: 5 new agent files in `claude-code/agents/` — each documents
  trigger conditions, mandatory checks, severity classification, output
  format, grandfathering, budget modes (M4)
- **template**: `docs/templates/impl-review-template.md` — 5 agent
  sections + User Override Decisions table + Revision History (M4)
- **adr-index**: ADR-0005 added to `docs/adr/INDEX.md` (M1)

### Chore

- **security**: refresh `SECURITY.md` hardcoded counts — skills 16→17,
  agents 2→7, hooks 2→8 (8 named), rules 1→2 (M6 step 6.1)
- **scripts/install.sh**: register
  `"PreToolUse|Bash|security-static-check.sh|10|"` in AA_MA_HOOKS array;
  auto-discovers new skill + 5 agents via existing `for d in
  claude-code/skills/*/` and `for f in claude-code/agents/*.md` loops (M2/M4)

### Plan close

- post-impl-adversarial-review v1: 6 milestones (M1 ADR + spec, M2 hook,
  M3 parsers, M4 skill + 5 agents, M5 §6.8 integration, M6 release) —
  full feature ship in single 0.7.0 → 0.8.0 minor bump
- 7 commits authored under `[AA-MA Plan] post-impl-adversarial-review`
  footer
- Critical-Path evidence: hook-modification (M2), doc-count-drift (M1,
  M5, M6), version-pipeline (M6) — all logged to provenance.log
- Prototype-Required: YES on M4 → 6 PROTOTYPE entries in provenance.log
- HARD gates: M2, M3, M4, M5, M6 all enforced; SOFT M1 docs-only
- Grandfathering verified by construction: this plan's
  `Created: 2026-05-11` is pre-v0.8.0 cutover → §6.8 does NOT fire on
  its own milestones (self-bootstrap safety)

## v0.7.0 (2026-05-11)

Harden `/aa-ma-plan` against silent phase-skipping. Adds a structured runtime
marker log (`~/.claude/runtime/aa-ma-plan-<slug>.log`) recording every phase as
INIT, DONE, or SKIPPED-with-reason. New advisory hook `aa-ma-plan-skip-warn.sh`
fires on `PreToolUse(ExitPlanMode)` and `SessionEnd` to warn about missing
markers — never blocking. Fully additive: bypass via existing
`AA_MA_HOOKS_DISABLE=1` master kill switch. Shipped TDD-first with 73 new
automated tests (50 pytest + 17 bats + 6 integration) plus 4 live empirical
scenarios PASS (Scenario 5 compaction survival DEFERRED for next live session).
The full plan lives at `.claude/dev/active/harden-aa-ma-plan/`.

### Feat

- **aa-ma-plan**: wire marker discipline into /aa-ma-plan command body — new
  Phase 0 Runtime Log Initialization section with slug derivation algorithm +
  10-row marker discipline reference table covering every phase boundary
- **hooks**: add `aa-ma-plan-skip-warn.sh` advisory hook (90 lines, bash + jq,
  shellcheck clean) — reads newest runtime log, validates 9 required phase
  markers, warns to stderr, always exits 0 (advisory)
- **hooks**: add `aa-ma-plan-marker.sh` marker-writer helper (79 lines) —
  appends canonical em-dash-separated marker lines via
  `aa-ma-plan-marker.sh <slug> <phase> <status> [k=v ...]`
- **plan_markers**: new `src/aa_ma/plan_markers/` Python package (parser +
  fingerprint matcher, stdlib-only, frozen dataclasses, regex-driven). Public
  API: `parse_log()`, `correlate()`, `load_tool_calls()`
- **aa-ma-scribe**: Phase 5 close-out writes `PHASE_5 DONE` marker and moves
  the runtime log into the active task directory as `<task>-plan-run.log`
- **install.sh**: registers `PreToolUse|ExitPlanMode` + `SessionEnd` for the
  new advisory hook in `settings.json`; symlinks `aa-ma-plan-marker.sh` so
  command bodies can invoke it from any project directory
- **skill-ecosystem-integration**: COMPLETE M3 + PLAN CLOSE — v0.5.0 → v0.6.0
  (carried over from pre-v0.6.0-tag commits)

### Fix

- **aa-ma**: correct M3 milestone Status — ACTIVE → COMPLETE (drift fix,
  carried over from pre-v0.6.0-tag commits)
- **install.sh**: helper-symlink rule generalised — non-event scripts under
  `claude-code/hooks/` invoked from slash-command bodies must be explicitly
  symlinked, mirroring the `aa-ma-parse.sh` pattern. Gap discovered + fixed
  during M4 live testing

### Test

- **plan_markers**: 50 pytest cases — 18 parser (well-formed, multi-line,
  malformed, dataclass contract) + 32 fingerprint (transcript-derived
  correlation across all 9 phase predicates, SKIPPED override, MISSING
  detection, JSONL nested-content handling)
- **hooks**: 17 bats cases — 7 advisory-hook (happy, missing, skipped+reason,
  skipped-no-reason, kill-switch, no-log, malformed-json) + 10 marker-helper
  (grammar, validation, multi-write accumulation)
- **integration**: 6 lifecycle bats — stub creation, 10-line accumulation in
  stable order, Phase 5 move to task dir, hook silent on healthy log, hook
  warns on missing marker, legitimate SKIPPED silences hook
- **smoke**: 4 live Tier-4 scenarios PASS (happy path, --skip-lessons,
  user-choice skip of Phase 4.5, forced-skip negative); Scenario 5
  (compaction survival) DEFERRED with reproduction note

### Docs

- **spec**: `docs/spec/plan-marker-grammar.md` (192 lines) — canonical
  contract covering grammar, 9 required markers, storage lifecycle,
  fingerprint correlation, slug derivation, parser/hook contracts
- **spec**: `docs/spec/aa-ma-specification.md` adds "Phase Markers (v0.7.0+)"
  section
- **spec**: `docs/spec/aa-ma-quick-reference.md` adds 9-line marker cheat
  sheet
- **smoke**: `tests/smoke/aa-ma-plan-skip-detection.md` (276 lines) documents
  the 5 empirical scenarios for future regression cycles
- **smoke**: `tests/smoke/aa-ma-plan-skip-detection-findings.md` captures
  the 2026-05-11 autonomous run (4 PASS, 1 DEFERRED, full audit trail,
  independent verification by Explore subagent)

### Plan close

- harden-aa-ma-plan v1: 5 milestones (M1 parser+fingerprint, M2 hook, M3
  command body, M4 live scenarios, M5 docs+release) — full plan ship in
  single 0.6.0 → 0.7.0 minor bump
- 12 commits authored under `[AA-MA Plan] harden-aa-ma-plan` footer
- Test posture: 489 pytest passed + 81 bats passed (73 new); ruff + format
  clean; existing test suites unaffected; advisory hook is non-blocking by
  design and bypassable via existing `AA_MA_HOOKS_DISABLE=1` kill switch

## v0.6.0 (2026-05-10)

Skill ecosystem integration — adopt 3 mattpocock/skills (grill-with-docs, prototype,
write-a-skill) via fork+ADR+test pattern. Operationalises engineering-standards Theme 1
`Prototype-Required: YES` flag (ADR-0003). Ships canonical skill-authoring procedure
(ADR-0004). Adds `/aa-ma-plan` Phase 1.3 mode-aware grill protocol with `--grill-mode`
flag + `AA_MA_GRILL_MODE` env var (ADR-0002). Skill count 13 → 16. Backward-compat
preserved: greenfield projects (no `CONTEXT.md`, no `docs/adr/`) resolve auto → simple
→ unchanged v0.5.0 `/grill-me` protocol.

### Feat

- **skill-ecosystem-integration**: COMPLETE milestone M2 — prototype + write-a-skill adopted
- **skills**: fork prototype + write-a-skill from mattpocock/skills upstream
- **skill-ecosystem-integration**: COMPLETE milestone M1 — grill-with-docs adopted
- **aa-ma-plan**: wire grill-with-docs into Phase 1.3 (mode-aware) — new `--grill-mode={auto,with-docs,simple,skip}` flag, `AA_MA_GRILL_MODE` env var, and 105-line `scripts/grill-mode-resolver.sh` (8 branches, 13 unit tests covering 100% of declared paths)
- **skills**: fork grill-with-docs from mattpocock/skills upstream — auto-discovered by `scripts/install.sh`, all 3 forked files (SKILL.md, CONTEXT-FORMAT.md, ADR-FORMAT.md) MD5-clean against canonical with provenance comments

### Docs

- **adr**: ADR-0002 (grill-with-docs adoption — fork + Phase 1.3 wire), ADR-0003 (prototype adoption — operationalises Theme 1, LOGIC + UI branches), ADR-0004 (write-a-skill adoption — canonical authoring procedure)
- **research**: `docs/research/skill-ecosystem-audit.md` (258 lines, 6 sections + lineage map + cross-reference audit) synthesising 3 canonical inventories (mattpocock + gstack + gsd) fetched via `gh api`; "valid through 2026-Q3" decay markers per recommendation
- **research**: `docs/research/_inventories/{mattpocock,gstack,gsd}-inventory.json` — ground-truth canonical inventories with `_meta.{source_url, fetched_at, verifier_method}`
- **context**: `CONTEXT.md` (83 lines) at repo root — canonical plan-authoring vocabulary (Repo / Catalog / Ecosystem; Fork / Adoption / Upstream; Candidate / Proposal / Status enum); aa-ma-forge now satisfies grill-with-docs auto-detection going forward
- **rules**: `claude-code/rules/engineering-standards.md` Theme 1 cross-reference to `Skill(prototype)` (SOFT — no HARD gate behavior change; absent-field semantic preserved)
- **spec**: `docs/spec/aa-ma-quick-reference.md` updated with `--grill-mode` flag documentation; `docs/spec/claude-code-foundations.md` skill table extended with prototype + write-a-skill rows + count 13 → 16
- **lessons**: L-001 (External URL First Principle) + L-002 (per-milestone doc-count-drift) + L-003 (cz bump owns CHANGELOG headings — never manually edit `## vX.Y.Z`)

### Chore

- **security**: `SECURITY.md` skill count 13 → 16 with grill-with-docs + prototype + write-a-skill alphabetically inserted (positions 8, 12, 16 respectively)
- **doc-count-drift**: 4 Tier-6 sweeps run (M1.5, M1.6, M2.6, M2.7) — each milestone's count transition independently discharged per L-002 ("doc-count-drift fires per milestone, not per plan")
- **gitignore-aware**: discovered project's `CLAUDE.md` is gitignored (line 2) — local-only edits documented; tracked equivalent prose lives in `docs/spec/claude-code-foundations.md`

### Test

- **skills**: `tests/skills/{_helpers.py, test_grill_with_docs_frontmatter.py, test_prototype_frontmatter.py, test_write_a_skill_frontmatter.py}` — 6 frontmatter test cases sharing the DRY `_helpers.split_frontmatter` + `assert_skill_frontmatter` helper
- **commands**: `tests/commands/test_grill_mode_resolver.py` — 13 test cases, 100% coverage of all 8 grill-mode-resolver branches (raised plan-eng-review's "29% paths tested" baseline to 100%)
- **hooks**: `tests/hooks/install_dry_run.bats` — 4 cases verifying `install.sh --dry-run` symlink announcements; skill-count assertion made dynamic (compares against `ls -d claude-code/skills/*/ | wc -l`) — future-proof against all skill additions

### Plan close

- skill-ecosystem-integration v1.2: 3 milestones (M1: grill-with-docs; M2: prototype + write-a-skill; M3: audit + version bump) — full plan ship in single 0.5.0 → 0.6.0 minor bump
- 11 commits in M1 + 9 commits in M2 + (this) commits in M3 — each task atomic with `[AA-MA Plan]` footer
- Test posture: 439 pytest passed + 58 bats passed; ruff src/ + tests/ clean; /grill-me command unchanged on branch (regression preserved); engineering-standards Theme 1 SOFT cross-ref preserves HARD gate behavior

## v0.5.0 (2026-05-09)

Engineering-standards doctrine + Planning Standard 11→12. Wires a 6-theme
engineering doctrine into AA-MA workflow surfaces, introduces an ADR convention,
and adds element #12 ("Engineering Standards Declaration") to the AA-MA Planning
Standard. Pre-v0.5.0 plans are grandfathered automatically.

### Feat

- **rules**: ship `claude-code/rules/engineering-standards.md` (118 lines, 6 themes,
  auto-loaded). Defines the canonical `Critical-Path:` enum (`auth-flow`, `data-xform`,
  `external-api`, `version-pipeline`, `doc-count-drift`, `hook-modification`).
- **commands**: `/aa-ma-plan` Phase 1 adds inline lessons scan
  (`docs/lessons.md` + `git log --grep="revert\|fix\|hotfix"` + top-3 completed
  context-logs; hard `timeout 30s`; `--skip-lessons` opt-out flag); Phase 2 adds
  Engineering Standards Declaration prompt + `ENG_STANDARDS_DECLARED` provenance
  entry; Phase 4 emits element #12 in plan output.
- **commands**: `/execute-aa-ma-step` adds Section 6.2.5 — 7-item advisory
  checklist (4 HARD defer to milestone gate, 3 SOFT request context-log declaration).
- **commands**: `/execute-aa-ma-milestone` adds Section 6.7 Engineering Standards
  HARD Gate with 5 conditions (clean git for AA-MA files, zero PENDING in milestone,
  tests-pass evidence, impact-analysis evidence, Critical-Path/Prototype-Required
  provenance evidence). Bypassable via `AA_MA_HOOKS_DISABLE=1`.
- **skills**: `plan-verification` Angle 6 extended with Engineering Standards
  Auditor (always-evaluated; structural check for element #12 + Critical-Path
  canonical enum + theme/test consistency). Pre-v0.5.0 plans grandfathered.
- **skills**: `operational-constraints` references engineering-standards rule
  and element #12 emit (+3 net lines).
- **agents**: `aa-ma-validator` Dimension 2 bumped 11→12 with grandfathering
  SKIP semantic.
- **templates**: new `docs/templates/engineering-standards-template.md` (optional
  per-task artifact, one section per theme); `tasks-template.md` adds optional
  `Critical-Path:` and `Prototype-Required:` fields at milestone + sub-step levels.
- **docs**: introduce ADR convention at `docs/adr/`. Ships `INDEX.md`, `TEMPLATE.md`
  (MADR format), and `0001-engineering-standards-architecture.md` capturing decisions
  D1–D8.
- **scripts**: `scripts/check_adr_index.sh` advisory ADR INDEX validator.
- **spec**: Planning Standard bumps from 11 to 12 elements across `aa-ma.md`,
  `aa-ma-specification.md`, `aa-ma-quick-reference.md` (no edits — already shape-based),
  `claude-code-foundations.md` (Rules count 1→2), `aa-ma-plan-workflow/SKILL.md`,
  `references/PHASE_4_PLAN_GENERATION.md`, `references/PHASE_5_ARTIFACT_CREATION.md`,
  `aa-ma-validator.md`, `plan-template.md`, `README.md`.

### Behavior change (soft-breaking)

This release is **soft-breaking** for downstream consumers: re-running
`scripts/install.sh` after upgrading creates a new auto-loaded rule symlink at
`~/.claude/rules/engineering-standards.md` that affects every Claude Code
session in projects using aa-ma-forge. The change is additive (no existing
behavior is removed) but observable.

**Opt-out paths:**

- `export AA_MA_HOOKS_DISABLE=1` — master kill switch for all AA-MA hooks and
  the Section 6.7 Engineering Standards HARD gate.
- `rm ~/.claude/rules/engineering-standards.md` — remove the auto-loaded rule
  while leaving other AA-MA mechanisms intact.
- Project-local `claude-code/rules/engineering-standards.md` — overrides the
  plugin-shipped copy when both are present.

**Pre-v0.5.0 plans are grandfathered:** plans authored before v0.5.0 (without a
`Created: YYYY-MM-DD` front-matter on-or-after the v0.5.0 release date) remain
conformant under the prior standard. `Skill(plan-verification)` Angle 6 only
flags missing element #12 for plans `Created:` on-or-after v0.5.0.

### Rollback

Three options documented in `docs/runbooks/rollback-v0.5.0.md`:

1. **Soft revert:** `export AA_MA_HOOKS_DISABLE=1` (+ optional `rm` of the
   symlink). Persists for the current shell.
2. **Full revert from git:** `git checkout v0.4.0 -- claude-code/rules/
   docs/spec/ docs/adr/ docs/templates/` then `scripts/install.sh`.
3. **Clean uninstall + reinstall:** `scripts/uninstall.sh` then `git checkout
   v0.4.0` then `scripts/install.sh`.

Pre-v0.5.0 plans remain valid throughout — no plan migration needed.

### Post-install smoke (manual)

After `scripts/install.sh`, open a fresh Claude Code session and query "what
engineering principles do you apply when developing?" — expect all 6 themes
from `engineering-standards.md` to appear in the response. Programmatic check
documented in `tests/smoke/aa-ma-engineering-standards-smoke.md`.

### AA-MA plan provenance

This release is the deliverable of AA-MA plan
`aa-ma-engineering-standards` (M0–M4 across `feature/aa-ma-engineering-standards_001`
branch). Five milestones; HARD gates on M0, M3, M4; full audit trail in
`.claude/dev/active/aa-ma-engineering-standards/` (will move to
`.claude/dev/completed/` post-archival).

## v0.4.0 (2026-05-08)

### Feat

- **codemem**: yek adapter + 5-tool harness (M2c)
- **codemem**: Repomix adapter (M2b)
- **codemem**: live 3-tool fairness harness (M2a)
- **aa-ma-plan-workflow**: add Mode/Gate/Baseline fields to plan template
- **codemem-token-benchmarks**: M3 Task 3.1 COMPLETE — fastapi pinned + sweep orchestrator
- **codemem-token-benchmarks**: M2 Task 2.6 GREEN — integration test
- **codemem-token-benchmarks**: M2 Task 2.5 GREEN — full CLI benchmark harness
- **codemem-token-benchmarks**: M2 Task 2.4 RED — tiktoken normalization tests
- **codemem-token-benchmarks**: M2 Task 2.3 GREEN — inline Aider prose parser
- **codemem-token-benchmarks**: M2 Task 2.2 RED — parser tests + golden Aider fixture
- **execute-aa-ma-milestone**: add Section 7.2.5 Post-Completion Validator Dispatch
- **codemem-token-benchmarks**: M2 Task 2.1 COMPLETE — add tiktoken dev dep
- **codemem-token-benchmarks**: M1 COMPLETE — Task 1.3 scope decision + milestone finalization
- **codemem-token-benchmarks**: M1 Task 1.2 COMPLETE — smoke tests + 1 AC reframe
- **codemem-token-benchmarks**: M1 Task 1.1 COMPLETE — pinned tool installs verified
- **aa-ma**: new plan — codemem-token-benchmarks (executes DEFERRED Task 4.2)
- **codemem**: M4 COMPLETE — review-response patch (5 fixes) + milestone finalization
- **codemem**: M4 Task 4.6 — codemem-scoped doc-drift hook + test gate
- **codemem**: M4 Task 4.8 — zero-config install + co_changes demo (L-254 fix)
- **codemem**: M3.5 COMPLETE — fix L-253 apply_schema-without-migrate defect
- **codemem**: M3.5 Task 3.5.3 — auto-build-on-first-query
- **codemem**: M3.5 Task 3.5.2 — integration tests prove 14 tools reachable via FastMCP
- **codemem**: M3.5 Task 3.5.1 — wire 6 M3 tools into FastMCP server
- **codemem**: M4 Task 4.7 — CI smoke test + ast-grep drift check
- **codemem**: M4 Task 4.1 — perf bench script + aa-ma-forge measurements
- **codemem**: M3 Task 3.7 — aa_ma_context() moat tool (326/326)
- **codemem**: M3 Task 3.6 — layers() MCP tool (318/318)
- **codemem**: M3 Task 3.5 — symbol_history() MCP tool (308/308)
- **codemem**: M3 Task 3.4 — owners() MCP tool (301/301)
- **codemem**: M3 Task 3.3 — co_changes() MCP tool (291/291)
- **codemem**: M3 Task 3.2 — hot_spots() MCP tool (279/279)
- **codemem**: M3 Task 3.1 — git mining base layer (269/269)
- **codemem**: M3 Task 3.8 — schema v2 migration (254/254)
- **codemem**: M2 Task 2.8 + M2 COMPLETE — WAL rotation (227/227)
- **codemem**: M2 Tasks 2.6 + 2.7 — WAL checkpoint + writer lock (217/217)
- **codemem**: M2 Task 2.5 — post-commit storm control + 4 tests (208/208)
- **codemem**: M2 Task 2.4 — WAL replay + round-trip property test
- **codemem**: M2 Task 2.3 — WAL JSONL journal + 14 tests (201/201)
- **codemem**: M2 Task 2.2 — incremental refresh driver + 10 tests (187/187)
- **codemem**: M2 Task 2.1 — symbol-set diff + 14 tests (177/177)
- **codemem**: M1 Tasks 1.12 + 1.13 — ARCHITECTURE.md + perf SLOs (M1 COMPLETE)
- **codemem**: M1 Task 1.11 — install wiring + import-linter + CLI + 11 tests
- **codemem**: M1 Task 1.10 — FastMCP server + aliases + 8 tests (152/152)
- **codemem**: M1 Task 1.8 — pure-Python PageRank + PROJECT_INTEL.json (144/144)
- **codemem**: M1 Task 1.7 — 6 MCP tools + sanitizers + canonical CTE (131/131)
- **codemem**: M1 Task 1.6 — 4-strategy cross-file resolver + 11 tests (98/98)
- **codemem**: M1 Task 1.5 — indexer driver + 15 tests (87/87 suite green)
- **codemem**: M1 Task 1.4 — ast-grep wrapper + 8 YAML rule files + 36 tests
- **codemem**: M1 Task 1.3 — Python stdlib `ast` parser + 20 tests passing
- **codemem**: M1 Task 1.2 — SQLite schema v1 + db.py + 16 tests passing
- **codemem**: M1 Task 1.1 — scaffold + dual-distribution packaging verified
- **codemem**: M1 Task 1.0 complete — packaging=uv_workspace, plan v3→v4
- **codemem**: AA-MA plan v3 — 41 tasks across 4 milestones, 12 MCP tools
- **hooks**: M5 post-commit drift detector — plan complete
- **hooks**: M4 SessionEnd dirty AA-MA detector
- **hooks**: M3 commit-signature + install.sh + docs + canonicalization
- **hooks**: M2 fix shipped hooks (mtime + path + both-paths)
- **hooks**: M1 foundations — bats harness + shared parser + CI

### Fix

- **codemem**: honest tiktoken budget enforcement (M1)
- **codemem-token-benchmarks**: resolve OBS-001 — add codemem-mcp to dev-deps
- **codemem**: M3.5 Task 3.5.5 — ship project-scope .mcp.json (Option B); L-244 files defect
- **hooks**: resolve helper across symlinked + project layouts

### Refactor

- **codemem**: M3.5 Task 3.5.4 — remove wheel MCP-server channel (AD-Q15)

## v0.3.0 (2026-04-10)

### Feat

- **spec**: add temporal validity markers for reference.md facts
- **commands**: add /aa-ma-search cross-task keyword search command
- **hooks**: add SessionStart hook with auto-detection and settings.json registration
- **skills**: add token-compression skill with HITL/AFK intensity mapping
- **execution**: implement HITL/AFK mode dispatch in execution skill and commands

### Fix

- **hooks**: write compaction entries to task provenance.log and context-log.md
- **docs**: correct two factual inaccuracies in README

## v0.2.0 (2026-04-07)

### Added

- `/grill-me` command: relentless plan/design interview (adapted from Matt Pocock's concept)
- `aa-ma-plan-workflow` skill: 5-phase planning workflow with references and templates (planning counterpart to aa-ma-execution)
- `operational-constraints` skill: disciplined execution mode for complex tasks (mandatory for complexity >= 60%)
- `/ops-mode` command: activate operational constraints
- 4 supporting skills: `plan-verification`, `impact-analysis`, `system-mapping`, `retro`
- 5 additional skills: `complexity-router`, `agent-teams` (with references and templates), `defense-in-depth`, `dispatching-parallel-agents`, `debugging-strategies`
- verification.md documentation: anatomy in spec, template (`docs/templates/`), example (`examples/verification-example/`)
- `docs/ATTRIBUTION.md`: formal provenance mapping of all external influences (Diet-Coder, Matt Pocock, Helix.ml, gstack, superpowers, claude-mem, double-check, Context7) with "What's Original" section
- Standalone templates for all 7 AA-MA files in `docs/templates/` (plan, reference, context-log, tasks, provenance, tests, verification) with HTML comment instructions and placeholder syntax
- Attribution note in `retro/SKILL.md` crediting gstack integration
- Dependency note in `aa-ma-plan-workflow/SKILL.md` documenting superpowers as optional dependency
- Origin notes in 3 session-derived skills (dispatching-parallel-agents, defense-in-depth, debugging-strategies)
- Templates index (`docs/templates/README.md`) explaining how to use each template
- Dedicated anatomy sections in spec for reference.md, context-log.md, and provenance.log (previously underdocumented)
- tests.yaml example (`examples/aa-ma-team-guide/aa-ma-team-guide-tests.yaml`) completing the example set
- Skills table in README (13 skills documented)
- README banner image and five-files visual (green/orange, dark background)
- Mermaid workflow lifecycle diagram in README
- "What else helped" section documenting claude-mem and double-check plugins
- "Optional extras" section documenting superpowers, gstack, and Context7 MCP dependencies
- Post-install bridge in Quick Start ("open Claude Code and type /aa-ma-plan")
- Full command reference table in README (8 commands)

### Changed

- Renamed `/ultraplan` command to `/aa-ma-plan` to avoid collision with Anthropic's built-in Ultraplan feature (shipped 2026-04-04)
- Renamed `ultraplan-workflow` skill to `aa-ma-plan-workflow`
- Updated all cross-references across commands, skills, agents, specs, and documentation
- See `docs/ultraplan-rename-rationale.md` for full context and comparison
- install.sh now auto-discovers all skills via loop (was hardcoded to aa-ma-execution only)
- Expanded HITL/AFK acronyms inline in README
- Marked Python package as skeleton-only in README (honest labelling)
- Restructured charity section for clarity (MS leads, other causes get own paragraph)
- Updated claude-code-foundations.md: 6→8 commands, 1→13 skills
- Updated aa-ma-quick-reference.md: added /grill-me, /verify-plan, /archive-aa-ma, /ops-mode to cheat sheet
- Full command table in README updated to 8 commands (added /ops-mode)
- Replaced broken `senior-architect` references with "deep architectural review" in complexity-router and aa-ma-plan-workflow (senior-architect excluded as empty scaffold)

### Fixed

- Broken doc reference in verify-plan.md (pointed to non-existent design doc)

## v0.1.0 (2026-04-05)

Initial release of AA-MA Forge.

### Added

- AA-MA specification v2.1 (canonical spec, quick reference, team guide)
- Claude Code foundations reference (built-in vs AA-MA layer mapping)
- 6 AA-MA commands: execute-full, execute-milestone, execute-step, archive, aa-ma-plan, verify-plan
- AA-MA execution skill (1,187 lines)
- 2 specialised agents: aa-ma-scribe (plan to artifacts), aa-ma-validator (read-only validation)
- Operational rules (aa-ma.md) and compaction hook (pre-compact-aa-ma.sh)
- Origin story narrative: how-we-got-here.md
- Python package skeleton (aa_ma) with validators, schemas, and CLI placeholders
- Install/uninstall scripts with symlink deployment and backup-first strategy
- Example completed task artifacts (aa-ma-team-guide)
- Semantic versioning with commitizen and python-semantic-release
- Apache-2.0 licence
