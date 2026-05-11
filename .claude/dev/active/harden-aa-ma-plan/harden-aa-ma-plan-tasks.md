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

- Status: PENDING
- Mode: AFK
- Acceptance Criteria:
  - `tests/plan_markers/test_fingerprint.py` exists with cases per fingerprint table.
  - Tests FAIL initially.
- Result Log: _pending_

### Task 1.5: Implement fingerprint matcher

- Status: PENDING
- Mode: AFK
- Acceptance Criteria:
  - `src/aa_ma/plan_markers/fingerprint.py` reads JSONL transcript, returns `list[CorrelationResult]`.
  - All Task 1.4 tests pass.
- Result Log: _pending_

## M2: Hook implementation (advisory)

**Gate:** SOFT. **Themes:** 1, 2, 4 (Safety: `AA_MA_HOOKS_DISABLE=1` kill switch honored).

### Task 2.1: Failing bats tests for advisory hook

- Status: PENDING
- Mode: AFK
- Acceptance Criteria:
  - `tests/hooks/aa_ma_plan_skip_warn.bats` exists with 6 cases.
  - `bats tests/hooks/aa_ma_plan_skip_warn.bats` FAILS initially.
- Result Log: _pending_

### Task 2.2: Implement aa-ma-plan-skip-warn.sh

- Status: PENDING
- Mode: AFK
- Acceptance Criteria:
  - Hook reads stdin JSON, extracts `transcript_path`, invokes Python fingerprint, writes warnings to stderr, exits 0.
  - All 2.1 bats tests pass.
  - `shellcheck` clean.
- Result Log: _pending_

### Task 2.3: Marker-writer helper

- Status: PENDING
- Mode: AFK
- Acceptance Criteria:
  - `claude-code/hooks/aa-ma-plan-marker.sh` provides `aa_ma_marker <phase> <status> [k=v ...]`.
  - Bats test confirms output matches grammar.
- Result Log: _pending_

### Task 2.4: Register hook in install.sh

- Status: PENDING
- Mode: HITL
- Acceptance Criteria:
  - `scripts/install.sh` `AA_MA_HOOKS` array contains entries for `PreToolUse|ExitPlanMode|aa-ma-plan-skip-warn.sh` and `SessionEnd||aa-ma-plan-skip-warn.sh`.
  - `scripts/install.sh --dry-run` shows the new entries.
  - Existing hooks unaffected.
- Result Log: _pending_

## M3: Command body integration

**Gate:** SOFT. **Themes:** 1, 4, 6.

### Task 3.1: Phase 0 stub-init in /aa-ma-plan command

- Status: PENDING
- Mode: AFK
- Acceptance Criteria (L-059 falsifiable):
  - `grep -c "PHASE_0 INIT" claude-code/commands/aa-ma-plan.md` returns ≥1.
  - `grep -c "~/.claude/runtime/aa-ma-plan-" claude-code/commands/aa-ma-plan.md` returns ≥1.
- Result Log: _pending_

### Task 3.2: Per-phase marker writes (9 markers)

- Status: PENDING
- Mode: AFK
- Acceptance Criteria:
  - `grep -cE "PHASE_(1|1\.3|1\.5|2|3|4|4\.2|4\.5|5) (DONE|SKIPPED)" claude-code/commands/aa-ma-plan.md` returns ≥9.
- Result Log: _pending_

### Task 3.3: Phase 5 log-move in aa-ma-scribe

- Status: PENDING
- Mode: AFK
- Acceptance Criteria:
  - `claude-code/agents/aa-ma-scribe.md` contains instruction to move `~/.claude/runtime/aa-ma-plan-<slug>.log` into `.claude/dev/active/<task>/<task>-plan-run.log`.
- Result Log: _pending_

### Task 3.4: Tier-3 integration smoke test

- Status: PENDING
- Mode: AFK
- Acceptance Criteria:
  - `tests/integration/test_marker_lifecycle.bats` simulates stub→append→move; passes locally.
- Result Log: _pending_

## M4: Live empirical test runs (Tier 4)

**Gate:** SOFT. **Themes:** 1, 3, 5.

### Task 4.1: Document 5 scenarios

- Status: PENDING
- Mode: HITL
- Acceptance Criteria:
  - `tests/smoke/aa-ma-plan-skip-detection.md` exists with 5 numbered scenarios (each has prompt, setup, expected markers, expected hook output, pass/fail criteria).
- Result Log: _pending_

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
