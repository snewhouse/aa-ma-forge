---
name: verify-plan
description: Run adversarial verification on an existing AA-MA plan using 6 structured angles to catch errors before execution
---

# /verify-plan - Plan Verification Command

Run structured adversarial verification against an AA-MA plan to catch factual errors, unverified assumptions, impact gaps, vague criteria, implementation barriers, and domain-specific risks.

## Usage

```
/verify-plan [task-name] [--iterate]
```

If `task-name` is omitted, list active tasks and prompt for selection.

**`--iterate` flag (opt-in, requires Claude Code's built-in `/goal`):** wraps
the verification protocol with a `/goal` cross-turn driver that re-runs
verification, ingests findings, edits plan files, and re-verifies until the
Verdict is GREEN with zero Criticals, or 3 iterations are exhausted. Without
the flag, behaviour is unchanged: single-pass verification, generate report,
exit. If `/goal` is unavailable (slash command errors, or managed-settings
hook restrictions apply — see `Skill(goal-condition-synthesis)`), the command
falls back to single-pass and logs `VERIFY_ITERATE_SKIPPED — reason=<token>`
to provenance.

See Step 4.5 (Iterate Mode) for the full protocol.

## Instructions for AI

### Step 1: Locate the Plan

If task-name argument was provided:
```bash
TASK_NAME="[argument]"
TASK_DIR=".claude/dev/active/${TASK_NAME}"
PLAN_FILE="${TASK_DIR}/${TASK_NAME}-plan.md"
```

If no argument, list active tasks and prompt:
```bash
ls .claude/dev/active/ 2>/dev/null
```

Then use `AskUserQuestion` to select a task.

Verify plan file exists:
```bash
test -f "${PLAN_FILE}" || echo "ERROR: No plan found"
```

If plan doesn't exist, display error and exit:
```
No plan found at ${PLAN_FILE}
Run /aa-ma-plan first to create a plan.
```

### Step 2: Load Plan Content

Read the plan file completely using the Read tool.
Also read these files if they exist (for additional context):
- `${TASK_DIR}/${TASK_NAME}-reference.md`
- `${TASK_DIR}/${TASK_NAME}-tasks.md`

### Step 3: Check for Existing Verification

```bash
VERIFY_FILE="${TASK_DIR}/${TASK_NAME}-verification.md"
```

If verification.md already exists, read it and display previous results:
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PREVIOUS VERIFICATION FOUND
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Revision: v[N] | Date: [date]
CRITICAL: [N] | WARNING: [N]
Result: [PASS/FAIL/PASS WITH WARNINGS]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Ask: "Re-run verification? [Y/n]"

If user says no, exit.

### Step 4: Invoke Plan Verification Skill

```
Skill: plan-verification
```

Pass to the skill:
- **Plan text:** Contents of plan.md
- **Project root:** Current working directory (pwd)
- **Mode:** From user selection (skill will prompt if not provided)
- **Previous findings:** From existing verification.md (if re-running)

### Step 4.5: Iterate Mode (opt-in, --iterate flag only)

**Skip this step entirely if `--iterate` was not passed.**

When `--iterate` is active:

1. **Synthesize the iteration goal** by invoking `Skill(goal-condition-synthesis)` with `mode: verify-iterate`. The skill returns a condition shaped like:

   ```
   <task>-verification.md latest "## Verdict" block shows GREEN with
   0 Criticals AND every Critical from the previous Verdict block has a
   "Resolution:" line in this block;
   or stop after 3 iterations.
   ```

2. **Bind the goal** via `/goal <condition>`. Surface the condition and the 3-iteration cap to the user before binding (`AskUserQuestion` with [Bind / Edit / Skip iterate]).

3. **On Bind:**
   - The first verification pass runs as normal (Step 4 above).
   - If the Verdict is GREEN with zero Criticals, `/goal` evaluates MET → run terminates cleanly. Proceed to Step 6.
   - If not, the goal driver re-invokes verification next turn. Each iteration must:
     - **Append** (not overwrite) a new `## Verdict — Revision N+1` block to `<task>-verification.md`. This preserves the audit trail.
     - Add `Resolution:` lines under every Critical from the previous Verdict block, citing the plan edit that addressed it.
     - Edit the plan files (`<task>-plan.md`, `<task>-reference.md`, etc.) to incorporate findings.
     - Re-run only the affected verification angles (not the full 6-angle wave).
   - After 3 iterations or first GREEN/0-Critical Verdict, the goal terminates.

4. **On termination, clear the goal:** `/goal clear`. Surface the final Verdict, the iteration count, and the evaluator's final reason. Append to `<task>-provenance.log`:

   ```
   [TIMESTAMP] VERIFY_ITERATE — verdict=<GREEN|YELLOW|RED> iterations=<N> criticals=<N> outcome=<MET|EXHAUSTED|USER_HALTED>
   ```

5. **If goal binding fails or `/goal` is unavailable:** fall back to single-pass behavior, log `VERIFY_ITERATE_SKIPPED — reason=<token>` to provenance.log, do NOT block.

**Why the cap of 3?** Empirically: more than 3 verification iterations on the
same plan typically indicates the plan needs a human re-think, not another
mechanical pass. The cap is heuristic, not load-bearing — adjust if your
project's experience disagrees, but document the rationale in the synthesis
SKILL alongside the formula.

**Concurrency note:** If a sibling session is editing the same plan files
(`<task>-plan.md`, `<task>-reference.md`), the iterate loop will race on
writes. Run `--iterate` in a worktree (`git worktree add .worktrees/iterate-N
<branch>`) when sibling sessions may be active. Per
`plan-authoring-standards.md` L-066, one `--iterate` session at a time per
plan.

**Why iterate at all?** Single-pass `/verify-plan` produces a report and
leaves the operator to act on it. For plans that need revisions to clear
Criticals, iterate-mode converts a manual loop into an autonomous one bounded
by a cost ceiling. The append-only Verdict log preserves what was found at
each pass — a richer audit trail than a single overwriting report.

### Step 5: Handle Results

The plan-verification skill will:
1. Run all 6 verification angles (Wave 1 parallel, Wave 2 sequential)
2. Consolidate findings with severity classification
3. Generate/update `${TASK_NAME}-verification.md`
4. Display results summary

**If automated mode and FAIL:**
- Present CRITICAL findings with suggested fixes
- Offer to revise the plan (max 2 revision loops)
- After each revision, re-run only affected angles

**If PASS or PASS WITH WARNINGS:**
- Display summary
- Recommend proceeding with `/execute-aa-ma-milestone`

### Step 6: Commit Verification Report

```bash
git add "${TASK_DIR}/${TASK_NAME}-verification.md"
git commit -m "docs: add/update verification report for ${TASK_NAME}

[AA-MA Plan] ${TASK_NAME} ${TASK_DIR}"
```

### Step 7: Display Final Summary

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VERIFICATION COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Task: [task-name]
Report: ${TASK_DIR}/${TASK_NAME}-verification.md

Next steps:
  /execute-aa-ma-milestone  → Begin implementation
  /verify-plan [task]       → Re-run verification after changes
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Error Handling

**Plan file not found:**
- Display helpful message pointing to `/aa-ma-plan`

**Skill invocation fails:**
- Fall back to manual verification prompt with the 6 angles listed
- Note in output: "Skill unavailable, using fallback verification"

**No active AA-MA tasks:**
- Display: "No active tasks found. Run /aa-ma-plan first."

---

## Integration

- **Invokes:** `plan-verification` skill (core verification engine)
- **Called by:** User directly, or recommended after plan revisions
- **Produces:** `[task]-verification.md` in the AA-MA task directory
- **Core skill:** `claude-code/skills/plan-verification/SKILL.md`
