# Engineering Standards E2E Smoke Test (Manual Checklist)

**Status:** Manual checklist (per AA-MA plan `aa-ma-engineering-standards` M4.7
locked decision: full E2E harness deferred to v0.6.0 if effort exceeds 1 hour).

**Purpose:** Verify the 6-theme engineering-standards doctrine + workflow wiring
is functioning end-to-end after install. Run on a fresh `claude-code` session
in a temp project directory after `scripts/install.sh` completes.

**TODO (v0.6.0):** Promote this manual checklist to an automated bash/pytest
harness at `tests/smoke/test_aa_ma_plan_workflow.sh` (or equivalent). Tracked as
"Eng-review-test (deferred if M4.7 ships manual checklist)" in the
aa-ma-engineering-standards plan deferred-items section. The 7 assertions below
are the harness's required pass/fail probes.

---

## Setup

```bash
# Fresh shell, fresh project dir
TMPDIR=$(mktemp -d)
cd "$TMPDIR"
git init -q
echo "smoke" > README.md
git add . && git commit -q -m "init"
```

## Assertions (7)

### 1. Phase 1 emits "Lessons Scan" subsection

```bash
# In a claude-code session at $TMPDIR:
/aa-ma-plan "trivial test feature"
# Expect: Phase 1 output contains the substring "Lessons Scan"
# Verify: grep -q "Lessons Scan" <captured_phase_1_output>
```

### 2. Phase 1 honors `--skip-lessons` flag

```bash
/aa-ma-plan "trivial test feature" --skip-lessons
# Expect: output contains "LESSONS-SCAN: SKIPPED"
```

### 3. Phase 2 prompts for "Engineering Standards Declaration"

```bash
/aa-ma-plan "trivial test feature"
# Expect: Phase 2 step 2.4 prompts for theme selection from the 6-theme list
# Expect: provenance.log contains a line matching "ENG_STANDARDS_DECLARED: themes=\["
```

### 4. Phase 4 emits element #12

```bash
# After Phase 4 completes, inspect the generated plan.md:
grep -q "12\..*Engineering Standards Declaration" .claude/dev/active/*/plan.md
# Expect: exit 0
```

### 5. `/execute-aa-ma-milestone` HARD gate refuses on dirty git

```bash
# With $TMPDIR/.claude/dev/active/<task>/ in dirty state:
echo "stray" > .claude/dev/active/<task>/<task>-tasks.md.tmp
/execute-aa-ma-milestone <task>
# Expect: exits non-zero with "BLOCKED: AA-MA artifacts have uncommitted changes"
```

### 6. `Critical-Path: auth-flow` task produces CRITICAL_PATH_REVIEW provenance entry

```bash
# Mark a sub-task with `Critical-Path: auth-flow` in tasks.md.
# Complete the milestone via /execute-aa-ma-milestone.
grep -q "CRITICAL_PATH_REVIEW" .claude/dev/active/<task>/<task>-provenance.log
# Expect: exit 0
```

### 7. `Prototype-Required: YES` task produces PROTOTYPE provenance entry

```bash
# Mark a sub-task with `Prototype-Required: YES` in tasks.md.
# Complete the milestone via /execute-aa-ma-milestone.
grep -qE "PROTOTYPE — " .claude/dev/active/<task>/<task>-provenance.log
# Expect: exit 0
```

---

## Post-install verification (CEO-8 manual smoke)

After `scripts/install.sh` completes:

```bash
# Fresh claude-code session
# Query: "what engineering principles do you apply when developing?"
# Expect: Response references all 6 themes from engineering-standards.md
#         (Verification & Truth, Development Principles, Reasoning & Planning,
#          Safety & Continuity, Execution Checklist, Sync & Commit Discipline)

# Programmatic check (against saved transcript):
TRANSCRIPT=/path/to/transcript.txt
for THEME in "Verification" "Development Principles" "Reasoning" "Safety" "Execution" "Sync"; do
    grep -q "$THEME" "$TRANSCRIPT" || { echo "FAIL: theme '$THEME' not in response"; exit 1; }
done
echo "All 6 themes present in response — POST-INSTALL SMOKE PASS"
```

---

## Verdict checklist

| Assertion | Expected | Actual | PASS/FAIL |
|-----------|----------|--------|-----------|
| 1. Phase 1 Lessons Scan emits | Substring present | | |
| 2. --skip-lessons honored | "LESSONS-SCAN: SKIPPED" | | |
| 3. Phase 2 declaration prompt | ENG_STANDARDS_DECLARED entry | | |
| 4. Phase 4 element #12 in plan.md | grep exit 0 | | |
| 5. Dirty-git HARD gate refusal | exit non-zero with "BLOCKED" | | |
| 6. CRITICAL_PATH_REVIEW entry | grep exit 0 | | |
| 7. PROTOTYPE entry | grep exit 0 | | |
| Post-install: 6 themes in response | All 6 present | | |

**Run by:** [name]
**Date:** [YYYY-MM-DD]
**Result:** [PASS | FAIL]
