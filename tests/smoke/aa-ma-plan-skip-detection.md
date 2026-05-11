# /aa-ma-plan Skip-Detection — Live Empirical Test Scenarios

**Status:** Tier-4 manual smoke tests for the phase-marker discipline shipped
in `harden-aa-ma-plan` (M1-M3 complete). These scenarios complement the
automated tiers:

- **Tier 1 (pytest):** `tests/plan_markers/` — parser + fingerprint logic.
- **Tier 2 (bats):** `tests/hooks/aa-ma-plan-{skip-warn,marker}.bats` — hook + helper.
- **Tier 3 (bats):** `tests/integration/test_marker_lifecycle.bats` — lifecycle glue.
- **Tier 4 (this file):** real `/aa-ma-plan` invocations by Stephen.

## Prerequisites

Before running any scenario:

```bash
# 1. Install the new hooks into ~/.claude.
scripts/install.sh

# 2. Confirm the new entries are registered.
grep -E "aa-ma-plan-skip-warn|aa-ma-plan-marker" ~/.claude/settings.json

# 3. Make sure ~/.claude/runtime/ does NOT contain stale logs.
ls ~/.claude/runtime/ 2>/dev/null
# If anything is there, archive or remove before running scenarios.

# 4. Confirm AA_MA_HOOKS_DISABLE is unset.
unset AA_MA_HOOKS_DISABLE
echo "AA_MA_HOOKS_DISABLE=${AA_MA_HOOKS_DISABLE:-<unset>}"
```

Recordings of each run are archived under `tests/smoke/recordings/` as
`scenario-N-<YYYYMMDD>.log` (the runtime log itself, plus a brief
markdown note for any anomalies).

---

## Scenario 1 — Happy Path

**Goal:** Verify a complete, non-skipping `/aa-ma-plan` run produces all 9
required phase markers and the hook stays silent at `ExitPlanMode`.

**Prompt:**
```
/aa-ma-plan add a one-line docstring to src/aa_ma/__init__.py
```

**Expected behaviour during the run:**
- Phase 0 init creates `~/.claude/runtime/aa-ma-plan-<slug>.log` with
  a `PHASE_0 INIT — slug=<slug>` line.
- Each phase (1, 1.3, 1.5, 2, 3, 4, 4.2, 4.5, 5) appends a DONE marker
  via `aa-ma-plan-marker.sh`.

**Verification after the run:**

```bash
# Find the most recent runtime log (or the moved version in the task dir).
LATEST_LOG=$(ls -t ~/.claude/runtime/aa-ma-plan-*.log 2>/dev/null | head -1)
[ -z "$LATEST_LOG" ] && LATEST_LOG=$(ls -t .claude/dev/active/*/*-plan-run.log | head -1)

# Count DONE markers across the 9 required phases.
grep -cE 'PHASE_(1|1\.3|1\.5|2|3|4|4\.2|4\.5|5) DONE' "$LATEST_LOG"
# Expected: 9
```

**Pass criteria:**
- ✅ 9 DONE markers present (one per required phase).
- ✅ The `aa-ma-plan-skip-warn.sh` hook produced no stderr output during
      `ExitPlanMode` or session end.
- ✅ At Phase 5, the runtime log was moved into the task directory.

**Fail criteria:**
- ❌ Any DONE marker is missing → fix the command body or marker helper.
- ❌ Hook emitted warnings → investigate which phase the hook flagged.

**Recording:** copy the final log to
`tests/smoke/recordings/scenario-1-$(date +%Y%m%d).log`.

---

## Scenario 2 — Legitimate Skip via `--skip-lessons`

**Goal:** Verify the `--skip-lessons` flag produces a `SKIPPED — reason=...`
marker (not a missing one) and the hook stays silent.

**Prompt:**
```
/aa-ma-plan --skip-lessons add a one-line docstring to src/aa_ma/__init__.py
```

**Expected marker for Phase 1.5:**
```
[<ts>] PHASE_1.5 SKIPPED — reason=flag_--skip-lessons
```

**Verification after the run:**
```bash
LATEST_LOG=$(ls -t ~/.claude/runtime/aa-ma-plan-*.log 2>/dev/null | head -1 \
             || ls -t .claude/dev/active/*/*-plan-run.log | head -1)
grep 'PHASE_1.5' "$LATEST_LOG"
# Expected: a SKIPPED line with reason=
```

**Pass criteria:**
- ✅ `PHASE_1.5 SKIPPED` marker present with non-empty `reason=`.
- ✅ Hook silent (skip with reason is its own evidence).
- ✅ Other 8 phases all DONE.

**Recording:** `tests/smoke/recordings/scenario-2-$(date +%Y%m%d).log`.

---

## Scenario 3 — Unverified Plan (Phase 4.5 skipped by user)

**Goal:** Verify that selecting "skip" at Phase 4.5 produces a SKIPPED marker
with `reason=user_choice`, and the hook stays silent (legitimate skip).

**Prompt:**
```
/aa-ma-plan refactor the marker grammar regex in src/aa_ma/plan_markers/parser.py
```

**During the run:**
When Phase 4.5 prompts via AskUserQuestion to choose verification mode, pick
the option that bypasses verification (e.g., "skip").

**Expected marker:**
```
[<ts>] PHASE_4.5 SKIPPED — reason=user_choice
```

**Pass criteria:**
- ✅ `PHASE_4.5 SKIPPED reason=user_choice` present.
- ✅ Hook silent because the skip carries a reason.
- ✅ Other 8 phases DONE.

**Note:** if the hook DOES warn here despite the reason, that's a bug
worth investigating — the SKIPPED-with-reason silencing is a core
guarantee of the design.

**Recording:** `tests/smoke/recordings/scenario-3-$(date +%Y%m%d).log`.

---

## Scenario 4 — Forced-Skip Negative Test

**Goal:** Verify the hook detects an artificially-tampered missing marker.

**Setup:**
1. Run Scenario 1 (happy path) to completion. Don't archive the log yet.
2. Open the runtime log and manually delete the `PHASE_1.3 DONE` line:
   ```bash
   LATEST_LOG=$(ls -t ~/.claude/runtime/aa-ma-plan-*.log 2>/dev/null | head -1)
   # Edit $LATEST_LOG and remove the PHASE_1.3 DONE line.
   sed -i '/PHASE_1.3 DONE/d' "$LATEST_LOG"
   ```
3. Trigger the hook manually by simulating a session-end stdin payload:
   ```bash
   echo '{"hook_event_name":"SessionEnd","transcript_path":"","session_id":"test"}' \
       | bash ~/.claude/hooks/lib/aa-ma-plan-skip-warn.sh
   ```

**Expected hook output (to stderr):**
```
aa-ma-plan: 1 phase marker issue(s) detected in ~/.claude/runtime/aa-ma-plan-<slug>.log
  - PHASE_1.3: marker missing from runtime log
  (advisory only — bypass with AA_MA_HOOKS_DISABLE=1)
```

**Pass criteria:**
- ✅ Hook stderr contains "PHASE_1.3" and "missing".
- ✅ Hook exit code is 0 (advisory).

**Recording:** `tests/smoke/recordings/scenario-4-$(date +%Y%m%d).log` plus
the literal stderr captured to `scenario-4-stderr-$(date +%Y%m%d).txt`.

---

## Scenario 5 — Compaction Survival

**Goal:** Verify the runtime log survives a context compaction event
mid-run, and that Phase 4+ markers still append cleanly after resume.

**Setup:**
1. Start `/aa-ma-plan` on a moderately complex prompt that will go past
   Phase 3 before compaction would naturally trigger.
2. After Phase 3 completes (PHASE_3 DONE marker visible in the log),
   manually trigger `/compact`.
3. After compaction, resume; Phase 4+ markers should append to the
   SAME log file (slug shouldn't change).

**Verification:**
```bash
LATEST_LOG=$(ls -t ~/.claude/runtime/aa-ma-plan-*.log 2>/dev/null | head -1)
# All 10 markers (PHASE_0 + 9 required) should be present in one file.
awk '{print $2}' "$LATEST_LOG" | sort -u
```

**Pass criteria:**
- ✅ Only ONE `aa-ma-plan-*.log` file exists in `~/.claude/runtime/`
      after the run (no second file created post-compaction).
- ✅ Markers 0, 1, 1.3, 1.5, 2, 3 are present (pre-compaction).
- ✅ Markers 4, 4.2, 4.5, 5 are present (post-compaction).
- ✅ All written by the same slug.

**Anomalies acceptable for v1:**
- Compaction is non-deterministic from the user's side. If compaction does
  not actually trigger during the run, mark this scenario as "deferred"
  with a manual reproduction note.

**Recording:** `tests/smoke/recordings/scenario-5-$(date +%Y%m%d).log` plus
a note about whether compaction actually fired.

---

## Synthesis Template

After running 3+ of the 5 scenarios, file findings as:

`tests/smoke/aa-ma-plan-skip-detection-findings.md`

Required structure:
1. Date + git commit hash of the harness under test.
2. One subsection per scenario actually executed: pass/fail, observations,
   anomalies.
3. Cross-cutting observations (does the hook fire reliably at both
   `PreToolUse(ExitPlanMode)` and `SessionEnd`? Any false positives?
   Performance impact noticeable?).
4. Recommended refinements (if any) before M5 release.

The advisory hook is **explicitly advisory** — failure of any scenario
should not block M5 release, but should be documented for v2 hardening.
