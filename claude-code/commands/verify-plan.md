---
name: verify-plan
description: Run adversarial verification on an existing AA-MA plan using 6 structured angles to catch errors before execution
---

# /verify-plan - Plan Verification Command

Run structured adversarial verification against an AA-MA plan to catch factual errors, unverified assumptions, impact gaps, vague criteria, implementation barriers, and domain-specific risks.

## Usage

```
/verify-plan [task-name]
```

If `task-name` is omitted, list active tasks and prompt for selection.

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
