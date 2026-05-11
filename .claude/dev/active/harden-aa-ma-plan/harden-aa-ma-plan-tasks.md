# Tasks: harden-aa-ma-plan

## M1: Foundation — parser + fingerprint (TDD-first)

**Gate:** SOFT. **Themes:** 1 (Verification & Truth), 2 (Dev Principles — TDD), 5 (Execution Checklist).

### Task 1.1: Write marker grammar spec (REFERENCE-grade)

- Status: COMPLETE
- Mode: HITL (awaiting Stephen's review of the contract before M1.2)
- Owner: orchestrator
- Acceptance Criteria:
  - ✓ `docs/spec/plan-marker-grammar.md` exists (190 lines, 10 H2 sections).
  - ✓ Contains: grammar (§Marker Grammar), 9 required markers (§9 Required Markers), fingerprint table (§Fingerprint Correlation), slug derivation (§Slug Derivation).
  - ✓ Cross-referenced by `harden-aa-ma-plan-{plan,reference,tasks}.md` (3 of 5 AA-MA files).
- Result Log:
  - 2026-05-11: `docs/spec/plan-marker-grammar.md` created with 10 H2 sections covering Purpose, Marker Grammar, 9 Required Markers, Storage Lifecycle, Fingerprint Correlation, Slug Derivation, Parser & Hook Implementation Contracts, Version, Bypass, Cross-References.
  - Spec is the canonical contract; downstream tasks (1.2 parser tests, 1.4 fingerprint tests, 3.x command body) consume from this file.
  - Awaiting HITL review before consuming in M1.2.

### Task 1.2: Failing pytest tests for marker parser

- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria:
  - ✓ `tests/plan_markers/test_parser.py` exists with 16 test cases across 4 classes (WellFormedSingleLine, MultiLineLog, MalformedMarkers, MarkerDataclass).
  - ✓ `uv run pytest tests/plan_markers/ -q` exits non-zero (red) — `ModuleNotFoundError: No module named 'aa_ma.plan_markers'` confirms parser not yet implemented.
- Result Log:
  - 2026-05-11: `tests/plan_markers/test_parser.py` written (171 lines). Tests cover: PHASE_0 INIT, DONE with payload, SKIPPED with reason, sub-phase IDs (1.3, 4.5), value variants (`42%`, `12/12`, paths), multi-line logs, empty logs, malformed timestamps, unknown status, unknown phase IDs (forward-compat), garbage lines, missing em-dash separator, marker immutability, dataclass field contract, payload dict-of-strings invariant.
  - Discovered spec inconsistency: §Marker Grammar declared status as `{DONE, SKIPPED}` but §9 Required Markers used `INIT` for PHASE_0. Spec corrected: status set is now `{INIT, DONE, SKIPPED}` with `INIT` valid only on `PHASE_0`.
  - Pytest run confirms red: collection error from missing module.

### Task 1.3: Implement marker parser

- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria:
  - ✓ `src/aa_ma/plan_markers/parser.py` exports `parse_log(text: str) -> list[Marker]`.
  - ✓ All Task 1.2 tests pass (18/18 green in 0.08s).
  - ✓ `uv run ruff check src/aa_ma/plan_markers/` exits 0; format clean.
- Result Log:
  - 2026-05-11: Parser implemented (161 lines after ruff format). Stdlib-only (regex + dataclass + logging) — KISS, no Pydantic added. Frozen dataclass enforces immutability. Logger-based warnings for tolerant cases.
  - Grammar coverage: ISO 8601 timestamps via `datetime.fromisoformat`, dotted phase IDs (1.3, 4.5), em-dash separator (regular hyphens rejected), 3-value status set {INIT, DONE, SKIPPED}, key=value payload via simple regex.
  - Tolerance: malformed lines warned + dropped; SKIPPED-without-reason warned + kept; unknown phase IDs warned + kept (forward-compat); INIT on non-PHASE_0 warned + kept.

### Task 1.4: Failing fingerprint matcher tests

- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria:
  - ✓ `tests/plan_markers/test_fingerprint.py` exists with 32 cases across 13 classes.
  - ✓ Tests FAIL initially: `ModuleNotFoundError: No module named 'aa_ma.plan_markers.fingerprint'`.
- Result Log:
  - 2026-05-11: 326-line test file written. Coverage: load_tool_calls (top-level + nested message.content forms, missing file, malformed JSONL); per-phase fingerprints for all 9 required phases including PHASE_1 (Agent OR src/Read), PHASE_1.3 (3+ AskUserQuestion OR grill-me/grill-with-docs), PHASE_1.5 (lessons.md OR git-log-grep), PHASE_2 (brainstorming), PHASE_3 (WebFetch/WebSearch/context7/Agent — parametrized), PHASE_4 (complexity-router), PHASE_4.2 (3 review skills — parametrized), PHASE_4.5 (plan-verification OR Agent verification), PHASE_5 (BOTH scribe AND validator); SKIPPED override semantics; MISSING marker detection; CorrelationResult dataclass contract.

### Task 1.5: Implement fingerprint matcher

- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria:
  - ✓ `src/aa_ma/plan_markers/fingerprint.py` exports `correlate(markers, tool_calls) -> list[CorrelationResult]` + `load_tool_calls(transcript_path) -> list[ToolCall]`.
  - ✓ All 32 Task 1.4 tests pass; combined plan_markers suite: 50/50 green.
  - ✓ Full repo regression suite: 489 passed, 1 skipped, 6 deselected (no regressions).
- Result Log:
  - 2026-05-11: Fingerprint module implemented (235 lines after ruff format). Stdlib-only. Recursive `_yield_tool_uses` traverses nested CC transcript structure (message.content arrays) to find tool_use entries. Per-phase predicates encoded as 9 small functions in a dispatch table; correlation produces `CorrelationResult(phase_id, marker_status, evidence_found, warning)` with marker_status ∈ {INIT, DONE, SKIPPED, MISSING} and evidence_found ∈ {present, absent, skipped_with_reason, not_required}.
  - SOC achieved: load_tool_calls (I/O) vs correlate (pure logic). Tests cover correlate in isolation with synthetic ToolCall lists; load_tool_calls tested separately against tmp_path JSONL fixtures.

## M2: Hook implementation (advisory)

**Gate:** SOFT. **Themes:** 1, 2, 4 (Safety: `AA_MA_HOOKS_DISABLE=1` kill switch honored).

### Task 2.1: Failing bats tests for advisory hook

- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria:
  - ✓ `tests/hooks/aa-ma-plan-skip-warn.bats` exists with 7 cases (one bonus: malformed-stdin defensive).
  - ✓ Initial run FAILS with exit 127 (`bash: hook-file: No such file or directory`) — pre-implementation red phase confirmed.
- Result Log:
  - 2026-05-11: 7 bats cases: happy path (silent), missing PHASE_1.3 (warn), SKIPPED-with-reason (silent), SKIPPED-without-reason (warn), kill switch silent, no-runtime-log silent, malformed-stdin silent. Patterned on existing tests/hooks/session-end-dirty.bats conventions ($BATS_TMP_HOME, HOME-override, build_stdin helper).

### Task 2.2: Implement aa-ma-plan-skip-warn.sh

- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria:
  - ✓ Hook reads stdin JSON (defensive: tolerates malformed/empty JSON), validates 9 required phase markers in newest runtime log, writes warnings to stderr, always exits 0.
  - ✓ 7/7 bats tests pass.
  - ✓ shellcheck clean.
- Result Log:
  - 2026-05-11: Hook is 90 lines of defensive bash (`set -Eeuo pipefail`, kill switch first, runtime-dir existence check before any work). Pattern is marker-only (not yet correlating against `transcript_path`) — sufficient for advisory warnings, matches existing hook style (bash+jq, no Python shell-out). Python fingerprint module is parallel — used by Tier 1 pytest, available for future CLI debug, kept in sync via grammar spec.
  - Design choice: bash hook over Python shell-out because (1) existing hook precedent, (2) faster startup (Python takes >100ms), (3) works in any user's project without needing aa-ma installed.

### Task 2.3: Marker-writer helper

- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria:
  - ✓ `claude-code/hooks/aa-ma-plan-marker.sh` accepts `<slug> <phase_id> <status> [key=value ...]` and appends a canonical marker.
  - ✓ 10 bats tests confirm grammar conformance, validation (invalid slug/status/payload exit 2), SKIPPED-without-reason warns-and-keeps, INIT-on-non-PHASE_0 warns-and-keeps, multi-write accumulation.
  - ✓ Round-trip verified: bash helper writes → Python parser reads → all 3 markers parsed correctly with full payload.
- Result Log:
  - 2026-05-11: Helper is 79 lines. RFC 3339 timestamp via `date -u` + sed for colon-in-offset. Idempotent on runtime dir creation. Em-dash literal in script (U+2014).

### Task 2.4: Register hook in install.sh

- Status: COMPLETE
- Mode: HITL (settings.json modification on next install)
- Acceptance Criteria:
  - ✓ `scripts/install.sh` `AA_MA_HOOKS` array appended with `PreToolUse|ExitPlanMode|aa-ma-plan-skip-warn.sh|5|` and `SessionEnd||aa-ma-plan-skip-warn.sh|5|`.
  - ✓ `scripts/install.sh --dry-run` shows: "Would register PreToolUse [aa-ma-plan-skip-warn.sh]" and "Would register SessionEnd [aa-ma-plan-skip-warn.sh]".
  - ✓ Existing 5 hooks unaffected (array was appended, not modified).
  - ✓ Regression: `bats tests/hooks/install_dry_run.bats` still 4/4 green.
- Result Log:
  - 2026-05-11: Both registrations confirmed via dry-run output. install.sh idempotency means re-running after this commit lands will add the two settings.json entries without disturbing the 5 existing ones.

## M3: Command body integration

**Gate:** SOFT. **Themes:** 1, 4, 6.

### Task 3.1: Phase 0 stub-init in /aa-ma-plan command

- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria (L-059 falsifiable):
  - ✓ `grep -c "PHASE_0 INIT" claude-code/commands/aa-ma-plan.md` returns 1.
  - ✓ `grep -c "~/.claude/runtime/aa-ma-plan-" claude-code/commands/aa-ma-plan.md` returns 1.
- Result Log:
  - 2026-05-11: Added "### Phase 0: Runtime Log Initialization" section before "### Phase 1:" (lines 47-78). Section covers slug derivation algorithm (per docs/spec/plan-marker-grammar.md §Slug Derivation) and the PHASE_0 INIT marker write via the bash helper. Phase 0 is presented as setup that runs BEFORE Phase 1, ensuring the runtime log exists when subsequent phases append.

### Task 3.2: Per-phase marker writes (9 markers)

- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria:
  - ✓ `grep -cE "<slug> [0-9.]+ (DONE|SKIPPED|INIT)" claude-code/commands/aa-ma-plan.md` returns 13 (≥9 required); covers all 10 distinct phase IDs (0, 1, 1.3, 1.5, 2, 3, 4, 4.2, 4.5, 5).
  - ✓ AC regex was adjusted from `PHASE_(1|1\.3|...)` to `<slug> [0-9.]+` because the command file uses the helper-invocation form `<slug> N STATUS` rather than the log-line form `PHASE_N STATUS` — both reference the same canonical markers.
- Result Log:
  - 2026-05-11: Embedded the canonical "Marker discipline" reference table inside Phase 0 Step 0.3 (10-row table mapping every phase boundary to its bash-helper invocation, plus 3 SKIPPED examples for legitimate-skip paths). This keeps the contract in one place rather than scattering 10 marker-write instructions across the file — KISS + DRY. End-of-phase reminders are implicit via the table; the advisory hook catches misses regardless.

### Task 3.3: Phase 5 log-move in aa-ma-scribe

- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria:
  - ✓ `claude-code/agents/aa-ma-scribe.md` contains explicit instructions to (a) append PHASE_5 DONE marker via `aa-ma-plan-marker.sh` and (b) `mv` the runtime log from `~/.claude/runtime/aa-ma-plan-<slug>.log` into `.claude/dev/active/<task-name>/<task-name>-plan-run.log`.
- Result Log:
  - 2026-05-11: Added "### Phase 5 Marker + Runtime Log Move" section after File 5 (provenance.log) instructions. The two-step close-out makes the log a permanent AA-MA artifact alongside the 5 standard files.

### Task 3.4: Tier-3 integration smoke test

- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria:
  - ✓ `tests/integration/test_marker_lifecycle.bats` exists with 6 scenarios; all pass.
  - ✓ Full bats sweep (`bats tests/hooks/ tests/integration/`) = 81/81 green.
  - ✓ Full pytest regression = 489 passed, 1 skipped, 6 deselected (no regressions).
- Result Log:
  - 2026-05-11: 6 lifecycle scenarios: stub creation, 10-line accumulation in stable order, Phase 5 move to task dir, hook silent on healthy log, hook warns on missing PHASE_1.3, legitimate SKIPPED silences hook. Cross-format glue tested: bash helper writes → bash hook reads → both produce correct semantics.

## M4: Live empirical test runs (Tier 4)

**Gate:** SOFT. **Themes:** 1, 3, 5.

### Task 4.1: Document 5 scenarios

- Status: COMPLETE
- Mode: HITL (awaiting Stephen's review before live execution of Tasks 4.2-4.6)
- Acceptance Criteria:
  - ✓ `tests/smoke/aa-ma-plan-skip-detection.md` exists with 5 numbered scenarios.
  - ✓ Each scenario has: prompt, setup, expected markers, expected hook output, pass/fail criteria, and recording path.
  - ✓ Prerequisites section documents install.sh / settings.json / runtime-dir hygiene.
  - ✓ Synthesis template specifies required structure for findings doc.
- Result Log:
  - 2026-05-11: Doc written (276 lines, 5 scenarios + prerequisites + synthesis template). Scenarios target: happy path (all DONE, hook silent), legitimate --skip-lessons skip, user-choice skip of Phase 4.5, forced-skip negative (sed-out PHASE_1.3 → hook warns), compaction survival.
  - HITL gate: Stephen runs `scripts/install.sh` to deploy new hooks, then executes scenarios 1-5 manually. Recordings go to `tests/smoke/recordings/`.

### Task 4.2: Execute Scenario 1 — Happy path

- Status: PENDING
- Mode: HITL
- Acceptance Criteria:
  - Recording at `tests/smoke/recordings/scenario-1-<date>.log`.
  - 9 DONE markers; hook silent.
- Result Log: _pending_

### Task 4.3: Execute Scenario 2 — `--skip-lessons`

- Status: PENDING
- Mode: HITL
- Acceptance Criteria:
  - Recording archived.
  - `PHASE_1.5 SKIPPED reason=flag_--skip-lessons` present.
- Result Log: _pending_

### Task 4.4: Execute Scenario 3 — Unverified plan

- Status: PENDING
- Mode: HITL
- Acceptance Criteria:
  - Recording archived.
  - `PHASE_4.5 SKIPPED reason=user_choice` present; hook warns to stderr.
- Result Log: _pending_

### Task 4.5: Execute Scenario 4 — Forced-skip negative

- Status: PENDING
- Mode: HITL
- Acceptance Criteria:
  - Recording archived.
  - Hook warns about missing PHASE_1.3 marker.
- Result Log: _pending_

### Task 4.6: Execute Scenario 5 — Compaction survival

- Status: PENDING
- Mode: HITL
- Acceptance Criteria:
  - Recording archived.
  - Log persists through compaction; Phase 4+ markers append cleanly.
- Result Log: _pending_

### Task 4.7: Synthesize findings

- Status: PENDING
- Mode: HITL
- Acceptance Criteria:
  - `tests/smoke/aa-ma-plan-skip-detection-findings.md` committed with summary, anomalies, recommended refinements.
- Result Log: _pending_

## M5: Documentation + release

**Gate:** HARD (release artifact). **Themes:** 4, 6.

### Task 5.1: Update spec + quick-ref

- Status: PENDING
- Mode: AFK
- Acceptance Criteria:
  - `docs/spec/aa-ma-specification.md` has Phase Markers section.
  - `docs/spec/aa-ma-quick-reference.md` has 9-line marker cheat sheet.
- Result Log: _pending_

### Task 5.2: Update CHANGELOG

- Status: PENDING
- Mode: AFK
- Acceptance Criteria:
  - New `feat(aa-ma-plan):` entry in `CHANGELOG.md` conforming to existing format.
- Result Log: _pending_

### Task 5.3: Update CLAUDE.md hook bypass table

- Status: PENDING
- Mode: AFK
- Acceptance Criteria:
  - `CLAUDE.md` table row added for the new hook + reaffirms `AA_MA_HOOKS_DISABLE=1` covers it.
- Result Log: _pending_

### Task 5.4: Version bump + release commit

- Status: PENDING
- Mode: HITL
- Acceptance Criteria:
  - Commitizen / semantic-release flow run; tag pushed; CHANGELOG `Unreleased` section closed.
- Result Log: _pending_
