---
name: execute-aa-ma-step
description: Execute single task from AA-MA plan with lightweight validation guardrails
---

# AA-MA Step Execution

You are executing a **single task** from an AA-MA (Advanced Agentic Memory Architecture) tracked plan.

**Scope**: One HTP task node (maximum granular control)
**Validation**: Lightweight guardrails (Result Log enforcement, acceptance criteria check, milestone boundary detection)
**Git**: No auto-commit (changes accumulate)

---

## 1. Locate Active Task & Pre-Execution Validation

Check `.claude/dev/active/` for the most recent task directory:

```bash
ls -lt .claude/dev/active/ | head -5
```

**Expected structure**: `.claude/dev/active/[task-name]/`

### Tier 1: Existence Check (Fast)

Verify all 5 required AA-MA files exist and are non-empty:

```bash
TASK_DIR=".claude/dev/active/[task-name]"
TASK_NAME="[task-name]"
MISSING=0
for file in "${TASK_NAME}-plan.md" "${TASK_NAME}-reference.md" "${TASK_NAME}-context-log.md" "${TASK_NAME}-tasks.md" "${TASK_NAME}-provenance.log"; do
  if [[ ! -s "${TASK_DIR}/${file}" ]]; then
    echo "❌ MISSING or EMPTY: ${file}"
    MISSING=$((MISSING + 1))
  fi
done
echo "Tier 1 result: ${MISSING} files missing"
```

**If Tier 1 fails (any files missing or empty):**

```
⚠️ AA-MA ARTIFACTS INCOMPLETE — AUTO-RECOVERY TRIGGERED

Missing/empty files detected: [list]

Auto-recovery: Triggering Phase 5 artifact creation with scribe+validator agents...
```

1. Notify user that auto-recovery is starting
2. Spawn `aa-ma-scribe` agent to create missing files from available plan context
3. Spawn `aa-ma-validator` agent to verify created files (5-dimension check)
4. If validator reports PASS/WARN → continue execution
5. If validator reports FAIL → retry once (re-scribe → re-validate)
6. If still FAIL after retry → HALT and alert user: "Auto-recovery failed. Run `/aa-ma-plan` to recreate artifacts."
7. If agent spawning unavailable → fallback: create files directly inline, then continue

**Note:** Step execution uses Tier 1 only (existence check). Full content validation (Tier 2) runs at milestone boundaries via `/execute-aa-ma-milestone`.

---

## 2. Priority Context Injection

**REQUIRED - Auto-inject with XML delimiters:**

Load and inject these two files immediately:

```xml
<REFERENCE>
{Read contents of [task-name]-reference.md}
# Immutable facts and constants. Treat as non-negotiable.
# Examples: API endpoints, file paths, configuration values, core function signatures
</REFERENCE>

<TASKS>
{Read contents of [task-name]-tasks.md}
# HTP (Hierarchical Task Planning) roadmap. Defines your required next action.
# Current execution scope: SINGLE STEP
# Status values: PENDING | ACTIVE | COMPLETE | BLOCKED
</TASKS>
```

**CONDITIONAL - Load if tokens allow**:
3. `[task-name]-context-log.md` (summarized architectural decisions)
4. `[task-name]-plan.md` (original strategy and rationale)

---

## 3. Validate Loaded Context

**Required checks**:
- ✅ REFERENCE contains key constants (APIs, paths, configs)
- ✅ TASKS has clear HTP structure with Status fields
- ✅ At least one task has `Status: PENDING` or `Status: ACTIVE`

**If validation fails**:
```
ERROR: [Specific issue]
- Missing AA-MA files → "AA-MA files not found. Run /aa-ma-plan first."
- Malformed HTP → "tasks.md lacks proper HTP format. Review AA-MA Planning Standard."
- No pending tasks → "All tasks complete. Check tasks.md status."
```

---

## 4. Parse HTP & Create TodoWrite Todos

**Parse tasks.md for HTP structure**:
- `## headers` = Milestones (e.g., "## Step 1: Setup Infrastructure")
- `### headers` = Sub-tasks (e.g., "### Sub-step: Install dependencies")
- Extract `Status:` field (PENDING | ACTIVE | COMPLETE | BLOCKED)
- Extract `Complexity:` percentage

**Identify next PENDING task**:
- Find first task node with `Status: PENDING`
- This is your target task for this execution

**Create TodoWrite todos for**:
- The target task (## level)
- All its sub-tasks (### level)

**Todo format**:
```json
{
  "content": "[Task title from HTP]",
  "status": "pending|in_progress|completed",
  "activeForm": "[Present continuous form]"
}
```

**Status mapping**:
- HTP `PENDING` → TodoWrite `pending`
- HTP `ACTIVE` → TodoWrite `in_progress`
- HTP `COMPLETE` → TodoWrite `completed`
- HTP `BLOCKED` → TodoWrite `pending` (prefix content with "BLOCKED: ")

**Complexity flagging**:
- If `Complexity: ≥ 80%` → Prefix content with "[High Complexity] "
- High complexity signals need for deep reasoning / Chain-of-Thought

---

## 4.5 Quality Standards (Actionable Triggers)

These principles apply DURING execution. Each has a trigger and skip condition.

- **KISS:** If implementation exceeds 200 lines for a single function, decompose. Skip for generated code.
- **DRY:** Before writing a new utility, grep the codebase for existing implementations.
- **SOLID:** If a class has >5 public methods, evaluate single-responsibility. If a module mixes data access + business logic + presentation, separate.
- **SOC:** If a file grows beyond one clear responsibility, split.
- **TDD:** If this step produces code, invoke `superpowers:test-driven-development`. Skip for docs/config.
- **12-Factor:** If task involves services/deployment, reference 12-Factor. For tasks with `.env` files, verify env-var-drift (see `rules/env-var-drift.md`).
- **Context7 MCP:** Use for library docs. Retry once on failure, fall back to WebSearch + official docs.
- **WebSearch:** Fallback when Context7 fails. Use proactively for unfamiliar APIs or recent library changes.

---

## 5. Execute Target Task

**Set task status to ACTIVE**:
1. Update tasks.md: Change target task `Status: PENDING` → `Status: ACTIVE`
2. Update TodoWrite: Mark corresponding todo as `in_progress`

**Mode Dispatch (HITL / AFK)**:
- Parse `Mode:` field from the target task in tasks.md
- If not present, inherit from parent milestone; default to `HITL`
- **HITL**: Display task summary and acceptance criteria, use `AskUserQuestion` [Proceed / Skip / Abort]. Only continue if Proceed.
- **AFK**: Proceed directly to execution without pause

**Execute the task**:
- Follow task instructions and acceptance criteria
- Use agents, skills, Context7 MCP as appropriate for efficiency
- For high complexity tasks (≥80%), use deep reasoning / Chain-of-Thought
- Execute all sub-tasks (### nodes) within the target task

**Impact awareness** (lightweight, no blocking):
- Consider upstream callers before modifying existing code
- Be aware of contract changes (function signatures, return types)
- Full impact analysis verification runs at **milestone boundary** (not step level)
- If editing shared/core modules, note potential impacts in Result Log

**For each sub-task**:
1. Mark TodoWrite sub-task as `in_progress`
2. Execute sub-task
3. Verify result meets expectations (guidance-based, trust your assessment)
4. **IMMEDIATELY** update `Result Log:` field in tasks.md with specific evidence — do not batch to end of task
5. If sub-task has acceptance criteria, verify them now (quick pass/fail)
6. Mark TodoWrite sub-task as `completed`

---

## 6. Complete Task

**When all sub-tasks done**:

### 6.1 Result Log Enforcement (REQUIRED)

**Before marking any sub-step or task COMPLETE, you MUST write its Result Log entry in tasks.md.**

This is not optional. Per L-080/L-081/L-082, Result Log drift is the #1 cause of sub-step state loss.

For each sub-step and the parent task:
- Write `Status: COMPLETE` and a concise `Result Log:` with **specific evidence** (file paths created, test counts, pass/fail verdicts, IDs generated)
- Vague Result Logs are rejected. Bad: "Done." Good: "Created `src/auth/middleware.py` with JWT validation; 3/3 unit tests pass."
- **Do not proceed to the next step until the current step's Result Log is written and saved to tasks.md.**

### 6.2 Step Acceptance Criteria Check (if defined)

If the step has `Acceptance Criteria:` defined in tasks.md, verify each criterion before marking COMPLETE:

1. Read the acceptance criteria for this step
2. For each criterion, confirm it is met (run the test, check the file exists, verify the output)
3. If any criterion FAILS: set `Status: BLOCKED` with the failing criterion in the Result Log, do not mark COMPLETE
4. If no explicit acceptance criteria exist: proceed with guidance-based assessment (trust your judgment)

This is lightweight — no formal verification matrix, just a quick pass/fail check per criterion.

### 6.3 Last-Step-of-Milestone Detection

**After completing this step, check: are there any remaining PENDING steps in the current milestone?**

```bash
# Quick check — count PENDING steps in the current milestone section
grep -c "Status: PENDING" [relevant milestone section of tasks.md]
```

- **If PENDING steps remain**: Report completion normally (Section 7)
- **If this was the LAST step of the milestone**: Display prominently:

```
=== MILESTONE BOUNDARY REACHED ===

All steps in [Milestone Name] are COMPLETE.
Run /execute-aa-ma-milestone for full validation, impact analysis, and auto-commit.

Do NOT proceed to the next milestone without running milestone validation.
```

### 6.4 Update State

1. **Update tasks.md**:
   - Change target task `Status: ACTIVE` → `Status: COMPLETE`
   - Confirm task-level `Result Log:` is filled (Section 6.1 should have done this already)

2. **Update TodoWrite**:
   - Mark task todo as `completed`

3. **Sync changes**:
   - Save tasks.md with updated Status and Result Log
   - Ensure TodoWrite reflects all status changes

4. **NO AUTO-COMMIT**:
   - Changes accumulate in working directory
   - Allows related tasks to be committed together
   - User will commit manually or use execute-aa-ma-milestone for auto-commit
   - **IMPORTANT**: When commits are made (manually or via milestone), include the AA-MA signature:
     ```
     [AA-MA Plan] [task-name] .claude/dev/active/[task-name]
     ```

5. **FINALIZATION NOTE**:
   - The **Finalization Protocol** (integrity check, doc auto-update, user approval) does NOT run at step level
   - Finalization runs at **milestone completion** only (via `/execute-aa-ma-milestone` or `/execute-aa-ma-full`)
   - Steps accumulate until milestone boundary is reached

---

## 7. Next Actions

**Report completion to user**:
```
✅ Task completed: [task title]

Summary: [brief outcome summary]

Result Log updated in tasks.md.

Next steps:
- Run /execute-aa-ma-step again to continue with next task
- OR run /execute-aa-ma-milestone to execute remaining tasks in this milestone
- OR commit changes manually when ready: git add . && git commit -m "..."
```

**If blocked**:
```
🚫 Task blocked: [task title]

Issue: [specific blocker]

Actions taken:
- Set Status: BLOCKED in tasks.md
- Created new sub-task: "### Sub-step: Resolve [blocker]"

Suggested resolution:
[remediation steps]

Please resolve blocker, then re-run /execute-aa-ma-step.
```

---

## Token & Context Optimization

- **Monitor token usage**: Check current session context usage
- **If approaching limits**: Consider context compaction:
  1. Summarize completed work
  2. Preserve essential state and open issues
  3. Discard redundant tool outputs
  4. Reset session with compacted context

---

## Error Handling

**Missing dependencies**:
```
ERROR: Task has unmet dependencies
- Task: [task-id]
- Dependencies: [list]
- Status of dependencies: [check Status: fields]

Resolution: Complete dependency tasks first, then retry.
```

**Malformed acceptance criteria**:
```
WARNING: Acceptance criteria unclear or missing
- Task: [task-id]
- Issue: [description]

Proceeding with best-effort execution. Consider updating tasks.md with clearer criteria.
```

---

**End of execute-aa-ma-step.md**
