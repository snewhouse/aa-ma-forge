# /aa-ma-plan Skip-Detection — Tier-4 Findings

**Date:** 2026-05-11
**Harness commit:** `d24c80a` (plus M4.1 doc + install.sh helper-symlink patch)
**Executor:** Claude Code, autonomous run (Stephen in a meeting)
**Verification:** independent Explore subagent confirmed all 8 audit claims

## Methodology

The scenarios as documented in `tests/smoke/aa-ma-plan-skip-detection.md`
prescribe **live `/aa-ma-plan` invocations**. From inside a running Claude
session, that means recursing the command body against my own behavior —
which is exactly what we're trying to test. Two constraints applied:

1. Scenarios 1, 2, 3, 4 were **synthesized** by directly invoking the
   marker helper (`bash ~/.claude/hooks/lib/aa-ma-plan-marker.sh ...`) for
   every phase the live command would produce, then firing the advisory
   hook with the appropriate Claude Code stdin payload. This exercises the
   **complete production-shape integration**: real installed hooks, real
   helper script, real settings.json registration, real `~/.claude/runtime/`
   storage, real grammar — only the upstream marker producer is human-
   driven rather than the live command body.
2. **Scenario 5 (compaction survival) is DEFERRED.** Compaction is a Claude
   Code harness event (triggered by `/compact` or context-pressure
   thresholds). It is not reproducible from a Bash session and cannot be
   meaningfully synthesized — the failure mode of interest is "does the
   slug remain stable across compaction and does the same log keep being
   appended to". Pass criterion when Stephen runs this live: only ONE
   `~/.claude/runtime/aa-ma-plan-<slug>.log` exists after a /aa-ma-plan
   run that crossed a compaction event, and all 10 markers are in it.

## Per-Scenario Results

### Scenario 1 — Happy Path: **PASS**

- Recording: `tests/smoke/recordings/scenario-1-20260511.log`
- All 10 markers present in correct order: PHASE_0 INIT + PHASE_{1, 1.3, 1.5, 2, 3, 4, 4.2, 4.5, 5} DONE.
- Hook (PreToolUse, simulated stdin): silent, exit 0.
- Python parser cross-format: 10 markers parse, phases match.

### Scenario 2 — Legitimate `--skip-lessons`: **PASS**

- Recording: `tests/smoke/recordings/scenario-2-20260511.log`
- `[<ts>] PHASE_1.5 SKIPPED — reason=flag_--skip-lessons` present verbatim.
- Other 9 phases DONE.
- Hook: silent (skip-with-reason is its own evidence).

### Scenario 3 — User-Choice Skip of Phase 4.5: **PASS**

- Recording: `tests/smoke/recordings/scenario-3-20260511.log`
- `PHASE_4.2 SKIPPED — reason=user_passed` + `PHASE_4.5 SKIPPED — reason=user_choice`.
- Both reasons non-empty and shell-token format.
- Hook: silent (both skips carry reason).

### Scenario 4 — Forced-Skip Negative (delete PHASE_1.3): **PASS**

- Recording: `tests/smoke/recordings/scenario-4-20260511.log` (9 lines, no PHASE_1.3).
- Stderr capture: `tests/smoke/recordings/scenario-4-stderr-20260511.txt`.
- Hook stderr verbatim:
  ```
  aa-ma-plan: 1 phase marker issue(s) detected in /home/sjnewhouse/.claude/runtime/aa-ma-plan-scenario4-20260511132409.log
    - PHASE_1.3: marker missing from runtime log
    (advisory only — bypass with AA_MA_HOOKS_DISABLE=1)
  ```
- Hook exit code: 0 (advisory, as required).
- **This is the critical positive proof** that the hook detects the bug
  class it was designed for.

### Scenario 5 — Compaction Survival: **DEFERRED**

- Rationale: compaction is harness-driven; not reproducible from a Bash
  session.
- Manual reproduction note for Stephen: in a future live session, run
  `/aa-ma-plan refactor src/aa_ma/plan_markers/parser.py for clarity`,
  manually invoke `/compact` between Phase 3 and Phase 4. Verify after
  completion that only one `~/.claude/runtime/aa-ma-plan-*.log` exists
  for that run and that all 10 markers are present.

## Cross-Cutting Verifications

| Check | Result | Evidence |
|-------|--------|----------|
| `PreToolUse(ExitPlanMode)` fires the hook | PASS | Scenario 1 + 4 stdin payloads |
| `SessionEnd` fires the hook with same logic | PASS | Cross-check, same warning produced |
| `AA_MA_HOOKS_DISABLE=1` silences output | PASS | Cross-check, no stderr emitted |
| Empty `~/.claude/runtime/` → graceful bail | PASS | Subagent audit point 8 |
| Marker helper symlinked at `~/.claude/hooks/lib/aa-ma-plan-marker.sh` | PASS | After `install.sh` re-run post helper-symlink patch |
| settings.json has both new hook registrations | PASS | `jq` queries confirm |

## Issues Found & Resolved Mid-Run

1. **install.sh did not symlink `aa-ma-plan-marker.sh`** (the marker helper
   used by the /aa-ma-plan command body). Found at first install attempt.
   **Fix applied** in this run: added an explicit symlink block in
   `scripts/install.sh` mirroring the `aa-ma-parse.sh` pattern (helpers
   need to live under `~/.claude/hooks/lib/` so they're invocable from
   slash-command bodies regardless of where the user's project lives).
   Re-running install confirmed the symlink. This patch will be committed
   alongside the findings.

No other anomalies detected. Spec at `docs/spec/plan-marker-grammar.md` is
fully consistent with observed behavior.

## Recommendations for M5

1. **Ship as-is for v1**. The 4 testable scenarios pass; the deferred
   Scenario 5 is documented with reproducible pass criteria for the next
   live session.
2. **Document the install.sh helper-symlink rule** in `CLAUDE.md` /
   `docs/spec/aa-ma-specification.md` so future contributors don't have
   to discover this gap when adding new helpers.
3. **CHANGELOG entry** should call out: (a) new advisory hook, (b)
   marker grammar canonical contract, (c) bypass via existing
   `AA_MA_HOOKS_DISABLE=1` kill switch.
4. **No version-bump blockers identified.** Minor version bump
   (`feat:` not `BREAKING CHANGE`) is appropriate.

## Independent Verification

A separate Explore subagent independently audited the recordings, parser
behavior, hook deployment, and settings.json registration. All 8 audit
claims returned **PASS**. Audit included verification that the Python
parser cleanly reads bash-helper-written markers (the cross-format
invariant from M2 round-trip testing — re-confirmed here).
