---
name: aa-ma-execution
description: Use when executing tasks from AA-MA artifacts - handles step/milestone/full execution with proper context injection, validation, and provenance logging. Proactively use when detecting .claude/dev/active/ directories or when user asks to continue/resume work.
---

# AA-MA Execution Skill

Execute tasks from Advanced Agentic Memory Architecture (AA-MA) artifacts with proper context management, state tracking, and provenance logging.

<EXTREMELY-IMPORTANT>
This skill MUST be used when:
- You detect `.claude/dev/active/[task-name]/` directory exists
- User asks to "continue", "resume", or "execute" an AA-MA task
- You're working on a complex multi-session task with AA-MA artifacts
- User references a task plan, milestone, or step from AA-MA documentation

DO NOT rationalize away using this skill. If AA-MA artifacts exist, you MUST use this workflow.
</EXTREMELY-IMPORTANT>

## I. Detection: When to Use This Skill

### Automatic Detection

**ALWAYS check for AA-MA tasks at session start or when user asks to continue work:**

```bash
# Check for active AA-MA tasks
ls -lt .claude/dev/active/ 2>/dev/null | head -10
```

**If output shows directories**: AA-MA tasks exist → USE THIS SKILL

**If output is empty**: No AA-MA tasks → Use ad-hoc workflows (e.g., `/please_proceed`)

### User Intent Signals

Use this skill when user says:
- "Continue the [task-name] work"
- "Execute the next step/milestone"
- "Resume the AA-MA task"
- "Run the plan for [task-name]"
- "What's the status of [task-name]?"
- "Pick up where we left off"

### File Path References

Use this skill when user references files in `.claude/dev/active/`:
- `[task-name]-plan.md`
- `[task-name]-tasks.md`
- `[task-name]-reference.md`
- `[task-name]-context-log.md`
- `[task-name]-provenance.log`

## II. Execution Modes

The skill supports three execution modes, matching the slash commands:

| Mode | Purpose | Validation Level | When to Use |
|------|---------|------------------|-------------|
| **Step** | Execute single task | Guidance-based (warnings only) | Quick iteration, exploratory work |
| **Milestone** | Execute complete milestone | Strict validation (blocks on failure) | **RECOMMENDED DEFAULT** - Ensures quality gates |
| **Full** | Execute entire plan | Automated with checkpoints | Long-horizon automation |

**Default recommendation**: **Milestone mode** provides the best balance of structure and flexibility.

## III. Pre-Execution Checklist

Before executing ANY AA-MA task, complete this checklist:

### 1. Identify Active Task

```bash
# List all active tasks with timestamps
ls -lt .claude/dev/active/
```

**Ask user if multiple tasks exist**: "I found multiple AA-MA tasks. Which one should I work on?"

### 2. Load AA-MA Context

**CRITICAL**: Always inject the 5 AA-MA files with explicit XML delimiters to prevent context contamination.

**Priority order** (load high-priority first):
1. **REFERENCE** (immutable facts - highest priority)
2. **TASKS** (current execution state - required)
3. **CONTEXT_LOG** (historical decisions - important)
4. **PLAN** (strategy and rationale - load if tokens allow)
5. **PROVENANCE** (telemetry - load if tokens allow)

**Context Injection Pattern**:

```xml
<REFERENCE>
[Contents of [task-name]-reference.md]
Treat as non-negotiable facts. These are strict, immutable constants.
</REFERENCE>

<TASKS>
[Contents of [task-name]-tasks.md]
This is your HTP roadmap. Defines required next action.
Current step MUST be marked ACTIVE.
</TASKS>

<CONTEXT_LOG>
[Contents of [task-name]-context-log.md]
Summarised history of architectural decisions and unresolved issues.
</CONTEXT_LOG>

<!-- Load PLAN and PROVENANCE if tokens allow -->
<PLAN>
[Contents of [task-name]-plan.md]
</PLAN>

<PROVENANCE>
[Contents of [task-name]-provenance.log]
</PROVENANCE>
```

**Token management**: If approaching 70% token usage, skip PLAN and PROVENANCE. Mark in output:
```
⚠️ Token optimization: PLAN and PROVENANCE not loaded (use context compaction if needed)
```

### 3. Validate File Structure

Check that all 5 files exist and are non-empty:

```bash
cd .claude/dev/active/[task-name]/
for file in *-plan.md *-reference.md *-context-log.md *-tasks.md *-provenance.log; do
  if [[ ! -f "$file" ]]; then
    echo "❌ MISSING: $file"
  elif [[ ! -s "$file" ]]; then
    echo "⚠️  EMPTY: $file"
  else
    echo "✅ VALID: $file"
  fi
done
```

**If files missing or empty**:
- **STOP** execution
- **Report** to user: "AA-MA files incomplete. Run `/ultraplan` to initialize properly."

### 3.5 Pre-Flight System Mapping (First Milestone Only)

If this is the **first milestone** being executed and it touches 3+ files or unfamiliar code, invoke `Skill(system-mapping)` for the 5-point pre-flight check before starting execution. Skip for subsequent milestones unless they shift to a completely different subsystem. Skip if system-mapping was already run during `/ultraplan`.

### 4. Identify Current Task

Parse `[task-name]-tasks.md` to find the current ACTIVE task:

**HTP Node Structure**:
```markdown
## Task Title
- Status: PENDING | ACTIVE | COMPLETE
- Dependencies: [List of prerequisite Task IDs]
- Complexity: [0-100%]
- Acceptance Criteria: [Clear, testable criteria]

### Sub-step: [Action]
- Result Log: [MANDATORY — must be populated before proceeding to next step]
```

> **Sub-Step Sync Enforcement (L-080):** The Result Log field is NOT optional. Every sub-step must have a non-empty Result Log with specific evidence (IDs, counts, pass/fail verdicts) before the executor may proceed to the next step. This applies equally to agent execution AND lead orchestrator direct execution. If a sub-step is genuinely not applicable, mark it `Status: SKIPPED — [reason]` instead of leaving it PENDING.

**Find ACTIVE task**:
- Look for `Status: ACTIVE`
- If none found, find first `Status: PENDING` with no unmet dependencies
- If multiple ACTIVE, **STOP** and report error: "Multiple ACTIVE tasks detected. Only one task should be ACTIVE at a time."

### 5. Impact Analysis Awareness

**REQUIRED at milestone boundaries** (integrated into validation):

- Use the `impact-analysis` skill at milestone completion
- Output consolidated impact analysis for all modified files
- Verify no unresolved HIGH risk impacts before marking milestone COMPLETE

**Detection**: If `.claude/dev/active/` exists → impact analysis is REQUIRED for milestone execution.

See `Skill(impact-analysis)` for full verification checklist and output format.

### 6. Display Execution Plan

**Before starting work**, present clear execution summary:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 AA-MA EXECUTION PLAN
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📁 Task: [task-name]
🎚️  Mode: [Step/Milestone/Full]
📍 Current: [Current task title]

✅ ACCEPTANCE CRITERIA:
  - [Criterion 1]
  - [Criterion 2]

⚡ COMPLEXITY: [X]% [+ warning if ≥80%]

📋 NEXT ACTIONS:
  1. [Action 1]
  2. [Action 2]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**High complexity warning** (if Complexity ≥ 80%):
```
⚠️  HIGH COMPLEXITY DETECTED (≥80%)
This task requires deep reasoning and extra care.
Consider:
- Breaking into smaller sub-tasks
- Human-in-the-loop review checkpoints
- Extensive testing and validation
```

**Ask for confirmation**:
```
Proceed with execution? (yes/no/edit)
- yes: Execute as planned
- no: Cancel and review plan
- edit: Modify acceptance criteria or approach
```

## IV. Execution Workflows

### A. Step Execution (Single Task)

**Use when**: Quick iteration, exploratory work, low-risk changes

**Workflow**:

1. **Mark Task ACTIVE**:
   ```markdown
   ## Task Title
   - Status: ACTIVE  ← Update from PENDING
   ```

2. **Execute Task**:
   - Follow acceptance criteria exactly
   - Use appropriate tools, agents, skills as needed
   - Document decisions in real-time

3. **Sync Result Log (BLOCKING — L-080/L-082)**:

   **IMMEDIATELY after executing the task — before validation, before moving on:**
   - Write `Status: COMPLETE` on the sub-step in `tasks.md`
   - Write a concise `Result Log:` entry with specific evidence (IDs, counts, pass/fail verdicts, key findings)
   - If the sub-step is not applicable: write `Status: SKIPPED — [reason]`

   **WHY THIS IS BLOCKING**: When the lead orchestrator executes steps directly (not via agents), there is no automatic documentation pathway. Agents auto-populate Result Logs via their prompt contract. The lead orchestrator has no such forcing function — results exist in conversation context but never reach tasks.md unless explicitly written here. This step prevents the sub-step drift that occurs when Result Log updates are deferred to "end of milestone."

   **Verification**: Read back the sub-step in tasks.md to confirm the Result Log is non-empty. If empty, STOP — do not proceed to validation.

4. **Validation (Guidance-based)**:
   - Check acceptance criteria
   - If NOT met: **WARN** user but allow to proceed
   - Log warnings in Result Log:
     ```markdown
     ### Sub-step: [Action]
     - Result Log:
       ⚠️ Acceptance criteria not fully met:
       - [Unmet criterion 1]
       - [Unmet criterion 2]
       [Output and decisions]
     ```

4. **Update State**:
   - Mark task COMPLETE (or leave ACTIVE if continuing)
   - Update Result Log with output
   - Extract new facts → add to `[task-name]-reference.md`
   - Document decisions → add to `[task-name]-context-log.md`

5. **Git Commit & Push**:
   ```bash
   git add .
   git commit -m "feat([task-name]): [brief description]

   Completed AA-MA step: [Task Title]
   Acceptance criteria: [met/partial]

   [AA-MA Plan] [task-name] .claude/dev/active/[task-name]"
   git push
   ```

6. **Log Provenance**:
   ```bash
   echo "[$(date '+%Y-%m-%d %H:%M')] Commit $(git rev-parse --short HEAD) — TaskID: [task-id] — Status: [COMPLETE/PARTIAL]" >> [task-name]-provenance.log
   ```

### B. Milestone Execution (RECOMMENDED)

**Use when**: Delivering complete feature, quality gates required, production changes

**Workflow**:

1. **Identify Milestone Tasks**:
   - Parse `[task-name]-tasks.md` for milestone boundary
   - Collect all tasks in milestone (typically 3-7 related tasks)

2. **Pre-Execution Validation**:
   - Check dependencies: All prerequisite tasks COMPLETE?
   - Check blockers: Any known issues in CONTEXT_LOG?
   - Check resources: Required artifacts available (per REFERENCE)?

   **If validation fails**: **STOP** and report:
   ```
   🚫 MILESTONE BLOCKED

   Unmet dependencies:
   - [Dependency 1]: Status PENDING
   - [Dependency 2]: Missing artifact

   Resolve these before proceeding.
   ```

3. **Execute Milestone Tasks** (in dependency order):
   - For each task in milestone:
     - Mark ACTIVE
     - Execute (following step workflow — **including step 3: Sync Result Log**)
     - **SUB-STEP SYNC GATE (L-080)**: Before proceeding to the next task, verify:
       - The just-completed sub-step has `Status: COMPLETE` (not PENDING)
       - The `Result Log:` field is non-empty with specific evidence
       - If either check fails: **STOP** — write the Result Log NOW, then continue
     - **STRICT VALIDATION**: Acceptance criteria MUST be met
     - If criteria NOT met: **STOP** entire milestone
     - Mark COMPLETE
     - Update state files

4. **Milestone Sub-Step Consistency Check (L-081 — BLOCKING)**:

   **After all tasks in the milestone are executed, BEFORE post-execution validation:**
   ```
   Count PENDING sub-steps within this milestone in tasks.md.
   If count > 0:
     🚫 MILESTONE BLOCKED — Sub-step drift detected

     [N] sub-steps still marked PENDING within this milestone:
     - [Step X.Y]: Status PENDING, Result Log empty
     - [Step X.Z]: Status PENDING, Result Log empty

     ACTION REQUIRED: Populate each Result Log with evidence from
     execution, then re-run this check. If a step was not applicable,
     mark it: Status: SKIPPED — [reason]

     DO NOT mark the milestone COMPLETE until this check passes.
   ```
   **Only proceed to post-execution validation when count = 0.**

5. **Post-Execution Validation**:
   - **Impact Analysis** (REQUIRED): Invoke `Skill(impact-analysis)` and output consolidated analysis for all files modified in milestone
   - Run tests (if applicable)
   - Verify all acceptance criteria met
   - Check for regressions
   - Verify no HIGH risk impacts remain unresolved

   **If validation fails**: **ROLLBACK**
   ```bash
   # Rollback to last known good state
   git reset --hard [previous-commit]

   # Update task status back to PENDING
   # Log failure in CONTEXT_LOG
   ```

5. **Milestone Completion**:
   - Update all milestone tasks to COMPLETE
   - Extract ALL new facts → `[task-name]-reference.md`
   - Document milestone summary → `[task-name]-context-log.md`:
     ```markdown
     ## [YYYY-MM-DD] Milestone: [Milestone Title] - COMPLETE

     **Acceptance Criteria**: All met ✅

     **Key Decisions**:
     - [Decision 1]
     - [Decision 2]

     **Artifacts Created**:
     - [File 1]
     - [File 2]

     **Tests**: [X] passing

     **Next Milestone**: [Title]
     ```

6. **Git Commit, Tag & Push**:
   ```bash
   git add .
   git commit -m "feat([task-name]): complete milestone [N] - [title]

   Milestone acceptance criteria:
   - ✅ [Criterion 1]
   - ✅ [Criterion 2]

   Artifacts:
   - [Artifact 1]
   - [Artifact 2]

   [AA-MA Plan] [task-name] .claude/dev/active/[task-name]"

   # Optional: Tag milestone
   git tag -a "[task-name]-milestone-[N]" -m "Milestone [N]: [Title]"

   # MUST push commits and tags
   git push && git push --tags
   ```

7. **Log Provenance**:
   ```bash
   echo "[$(date '+%Y-%m-%d %H:%M')] MILESTONE [N] COMPLETE — Commit $(git rev-parse --short HEAD) — Tests: PASS" >> [task-name]-provenance.log
   ```

### C. Full Plan Execution (Automated)

**Use when**: Long-horizon automation, well-defined plan, minimal human-in-the-loop

**Workflow**:

1. **Load Full Plan**:
   - Inject all 5 AA-MA files (required for full execution)
   - Parse entire task hierarchy from `[task-name]-tasks.md`

2. **Build Execution Graph**:
   - Identify all tasks and dependencies
   - Topologically sort by dependencies
   - Identify milestone boundaries

3. **Execute Milestones Sequentially**:
   ```
   For each milestone in plan:
     1. Execute milestone (using Milestone workflow above)
     2. Validate acceptance criteria (STRICT)
     3. If FAIL → STOP entire plan
     4. If PASS → Continue to next milestone
     5. Create checkpoint (git commit + tag)
   ```

4. **Automated Checkpoints**:
   - After each milestone: git commit + tag
   - Save execution state to `[task-name]-tasks.md`
   - Update `[task-name]-context-log.md` with summary

5. **Failure Handling**:
   - If any milestone fails:
     ```
     🚫 FULL PLAN EXECUTION STOPPED

     Failed at: Milestone [N] - [Title]
     Reason: [Failure reason]

     Last successful checkpoint: [task-name]-milestone-[N-1]

     Rollback command:
     git reset --hard [task-name]-milestone-[N-1]

     Review CONTEXT_LOG for details.
     ```

6. **Completion Report**:
   ```
   ✅ FULL PLAN EXECUTION COMPLETE

   Milestones completed: [N]/[N]
   Total tasks: [X]
   Total commits: [Y]
   Execution time: [Duration]

   Final state:
   - All acceptance criteria met ✅
   - All tests passing ✅
   - Artifacts created: [List]

   View provenance log: [task-name]-provenance.log
   ```

## V. AA-MA Commit Signature — MANDATORY

**CRITICAL**: ALL commits during AA-MA execution MUST include the plan signature as the LAST line of the commit message footer.

### Signature Format

```
[AA-MA Plan] {task-name} .claude/dev/active/{task-name}
```

### Example Commits

**Step completion:**
```
feat(auth): implement JWT token generation

- Add token service with RS256 signing
- Configure 1-hour expiry

[AA-MA Plan] auth-system .claude/dev/active/auth-system
```

**Milestone completion:**
```
feat(auth-system): complete milestone 1 - authentication core

Acceptance criteria:
- ✅ JWT tokens generated correctly
- ✅ Token validation works
- ✅ All tests passing (8/8)

[AA-MA Plan] auth-system .claude/dev/active/auth-system
```

### Why This Matters

- **Traceability**: Every commit can be traced back to its originating plan
- **Provenance**: Clear audit trail for complex multi-session work
- **Context**: When reviewing git history, immediately know which plan drove each change

### Applies To

- All commits during AA-MA plan execution
- All commits from `/execute-aa-ma-step`, `/execute-aa-ma-milestone`, `/execute-aa-ma-full`
- All commits from `/commit-and-push`, `/pre-commit-*` while a plan is active
- Manual commits during plan execution

---

## VI. Finalization Protocol — MANDATORY

Before marking ANY milestone COMPLETE, you **MUST** execute this 4-step protocol. No exceptions.

### Step 1: Integrity Check (Checklist Verification + Sub-Step Audit)

**Part A — Sub-Step Status Audit (L-081, L-083 — MECHANICAL CHECK):**

Before checking acceptance criteria, run this mechanical audit:
```
Sub-Step Status Audit for Milestone [N]:
  Total sub-steps: [X]
  COMPLETE: [Y]
  SKIPPED:  [Z] (with reasons)
  PENDING:  [W]

  If W > 0:
    🚫 FINALIZATION BLOCKED — [W] sub-steps still PENDING
    [List each PENDING sub-step]
    ACTION: Populate Result Logs before finalizing.
    HALT — do not proceed to Part B.

  If W = 0:
    ✅ All sub-steps accounted for (Y complete + Z skipped)
    Proceed to Part B.
```

**Part B — Acceptance Criteria Verification:**

Display acceptance criteria verification to the user:

```
Acceptance Criteria Verification:
- ✓ [Criterion 1]: Confirmed - [brief evidence]
- ✓ [Criterion 2]: Confirmed - [brief evidence]
- ✓ [Criterion 3]: Confirmed - [brief evidence]

All [X] criteria verified. Ready for finalization.
```

**Rules:**
- Every acceptance criterion must be explicitly listed
- Each must have `✓` confirmation with brief evidence
- If ANY criterion cannot be confirmed → HALT, do not proceed

### Step 2: Documentation Auto-Update

Automatically update all 5 AA-MA files:

| File | Auto-Update Action |
|------|-------------------|
| `tasks.md` | Mark milestone `Status: COMPLETE`, fill `Result Log:` |
| `reference.md` | Add any new immutable facts discovered |
| `context-log.md` | Append completion summary (see template below) |
| `provenance.log` | Append completion entry with timestamp + commit hash |
| `plan.md` | No change (historical record) |

**Template for context-log.md:**
```markdown
## [YYYY-MM-DD] Milestone Completion: [Title]
- Status: COMPLETE
- Key outcome: [1-2 sentence summary]
- Artifacts: [list of files created/modified]
- Tests: [pass/fail summary]
```

**Template for provenance.log:**
```
[TIMESTAMP] MILESTONE COMPLETE — [Milestone ID] — Commit: [hash] — Criteria: [X/X] verified
```

### Step 2.5: Post-Milestone Simplification Review

**Skip if:** Only docs/config changed (no `.py`/`.ts`/`.js`/`.go`/`.rs`), diff < 20 lines code, or `--skip-simplify` flag.

**Execution:** Launch 3 parallel review agents against the milestone diff (`git diff [last-checkpoint]..HEAD`):

| Agent | Focus | Catches |
|-------|-------|---------|
| **Code Reuse** | Search codebase for existing utilities | Agents reinventing what already exists |
| **Code Quality** | Redundant state, copy-paste, leaky abstractions | Inconsistent patterns across parallel tasks |
| **Efficiency** | N+1, missed concurrency, hot-path bloat | Performance issues surviving past task-level review |

**Findings** reported with severity (CRITICAL / WARNING / INFO). CRITICAL findings require explicit acknowledgment at the approval gate (Step 3). User can fix, acknowledge, or review details.

**Log to provenance:** `[TIMESTAMP] Post-milestone review: N findings (C/W/I) [fixed|acknowledged|skipped]`

**On failure:** Skip review, log `Post-milestone review: SKIPPED — agent failure`. Do NOT block finalization.

### Step 2.6: HARD Gate Check

If the milestone has `Gate: HARD` in tasks.md, verify a signed approval artifact exists in context-log.md before proceeding:

```
Required artifact format:
## [date] GATE APPROVAL: [Milestone Title]
- Gate: HARD
- Approved by: [user]
- Criteria verified: [X/X]
- Decision: APPROVED
```

**If HARD gate and no approval artifact:** HALT. Use AskUserQuestion to request approval. If approved, write the artifact to context-log.md, then continue. If `Gate: SOFT` (default), proceed normally.

### Step 2.7: Executable Test Stubs

If `[task]-tests.yaml` exists in the task directory, auto-detect and run tests for the current milestone. Each test has `name`, `command`, and `expected`/`expected_pattern`. All tests must pass. Falls back to existing test behavior if file is absent.

### Step 3: User Authorization (Approval Gate)

Use AskUserQuestion to get explicit user approval:

```
Finalization Review

Milestone: [Title]
Acceptance Criteria: [X/X] verified
Gate: [HARD|SOFT] — [Approval artifact found / Convention-based]

Ready to mark this milestone COMPLETE?
```

**Options:**
- **Approve** → "Proceed with status change and commit"
- **Review First** → "Show me the detailed verification before approving"
- **Reject** → "Do not mark complete, keep as ACTIVE"

**Behavior by choice:**
- **Approve**: Proceed to Step 4
- **Review First**: Display full integrity checklist from Step 1, then re-prompt
- **Reject**: HALT, keep `Status: ACTIVE`, ask user what needs fixing

### Step 4: Transparent Status Change

After approval, execute status change with minimal confirmation:

```
✅ Milestone marked COMPLETE: [Title]
```

If this was the FINAL milestone (all milestones now COMPLETE), add:

```
💡 All milestones complete! Run: /archive-aa-ma [task-name]
```

### Finalization Protocol Applies To

- `/execute-aa-ma-milestone` — at milestone boundary
- `/execute-aa-ma-full` — at each milestone boundary in the loop

**Note:** `/execute-aa-ma-step` does NOT trigger finalization (steps accumulate until milestone).

---

## VII. State Management — MANDATORY SYNC

**CRITICAL**: You **MUST** update state files immediately after each task completion. No exceptions. No batching.

> **Root Cause of Sub-Step Drift (L-080, L-082):** When the lead orchestrator executes steps directly (not via agents), results exist in conversation context but never reach tasks.md unless explicitly written. Agents have a built-in forcing function (their prompt contract requires Result Log output). The lead orchestrator does NOT — making this section the primary defense against state drift.

### Updating AA-MA Files During Execution

#### 1. Update TASKS (`[task-name]-tasks.md`) — IMMEDIATELY, NOT AT MILESTONE END

**After each sub-step (not each milestone — EACH SUB-STEP):**
```markdown
## Task Title
- Status: COMPLETE  ← Update from ACTIVE
- Dependencies: [...]
- Complexity: [...]
- Acceptance Criteria: [...]

### Sub-step: [Action]
- Result Log:
  ✅ COMPLETE [YYYY-MM-DD HH:MM]

  **Output**: [Concise summary with specific evidence: IDs, counts, verdicts]
  **Decisions**: [Key decisions made]
  **Artifacts**: [Files created/modified]
  **Tests**: [Test results if applicable]
```

**Anti-pattern (BANNED):** "I'll update all Result Logs at the end of the milestone." This is the #1 cause of sub-step drift. By milestone end, conversation context may be compacted and evidence is lost.

#### 2. Update REFERENCE (`[task-name]-reference.md`)

**Immediately extract immutable facts**:
- API endpoints discovered
- File paths created
- Configuration values finalized
- Database schema changes
- Function signatures defined

**Example**:
```markdown
# [task-name] Reference

## API Endpoints
- POST /api/auth/login - JWT authentication
- GET /api/users/{id} - User profile retrieval

## File Structure
- src/auth/jwt.py - JWT token handling
- src/models/user.py - User model definition

## Configuration
- JWT_SECRET_KEY: Set in .env (required)
- TOKEN_EXPIRY: 3600 seconds (1 hour)

_Last Updated: YYYY-MM-DD HH:MM_
```

#### 3. Update CONTEXT_LOG (`[task-name]-context-log.md`)

**Document architectural decisions** (use compaction format):

```markdown
# [task-name] Context Log

## [YYYY-MM-DD] Task: [Task Title]

**Decision**: [What was decided]
**Rationale**: [Why this approach was chosen]
**Alternatives Considered**: [Other options and why rejected]
**Trade-offs**: [Pros and cons]

**Unresolved Issues**:
- [Issue 1]: [Description and blocker]
- [Issue 2]: [Description and workaround]

---
```

#### 4. Update PROVENANCE (`[task-name]-provenance.log`)

**After each git commit**:
```bash
echo "[$(date '+%Y-%m-%d %H:%M')] Commit $(git rev-parse --short HEAD) — TaskID: [task-id] — Status: [status] — Tests: [PASS/FAIL/SKIP]" >> [task-name]-provenance.log
```

**Example log**:
```
[2025-11-19 14:32] Commit a1b2c3d — TaskID: auth-jwt-impl — Status: COMPLETE — Tests: PASS
[2025-11-19 15:45] Commit e4f5g6h — TaskID: user-model-schema — Status: COMPLETE — Tests: PASS
[2025-11-19 16:20] MILESTONE 1 COMPLETE — Commit i7j8k9l — Tests: PASS
```

## VIII. Context Compaction

**When to compact**: Token usage > 70% of session limit

### Compaction Procedure

1. **Trigger Compaction**:
   ```
   ⚠️ Token usage: 75% (150K/200K)
   Initiating context compaction...
   ```

2. **Summarize History**:
   - Review message history
   - Extract key decisions, outcomes, and state
   - Discard verbose tool outputs (keep only summaries)
   - Preserve critical facts and constraints

3. **Update CONTEXT_LOG**:
   ```markdown
   ## [YYYY-MM-DD] Compaction Summary

   **Completed Work**:
   - [Task 1]: [Brief outcome]
   - [Task 2]: [Brief outcome]

   **Key Decisions**:
   - [Decision 1]: [Rationale]
   - [Decision 2]: [Rationale]

   **Current State**:
   - Active task: [Task ID and title]
   - Next actions: [What to do next]

   **Open Issues**:
   - [Issue 1]: [Description]

   **Artifacts Created**:
   - [File 1]: [Purpose]
   - [File 2]: [Purpose]
   ```

4. **Reset Session**:
   - Start new chat session
   - Reload 5 AA-MA files with XML delimiters
   - Continue from current active task

5. **Document Compaction in Provenance**:
   ```bash
   echo "[$(date '+%Y-%m-%d %H:%M')] CONTEXT COMPACTED — Session reset — Continuing from TaskID: [task-id]" >> [task-name]-provenance.log
   ```

## IX. Validation & Rollback

### Acceptance Criteria Validation

**Strict validation** (Milestone and Full modes):

```
For each criterion in acceptance criteria:
  ✅ Check if met

  If NOT met:
    ❌ VALIDATION FAILED

    Failed criterion: [Criterion description]
    Expected: [What was expected]
    Actual: [What was observed]

    STOP execution
    Initiate rollback
```

**Guidance validation** (Step mode):

```
For each criterion in acceptance criteria:
  Check if met

  If NOT met:
    ⚠️ WARNING: Acceptance criterion not met
    [Details]

    Proceed anyway? (yes/no)
    Log warning in Result Log
```

### Rollback Procedure

**When validation fails in Milestone or Full mode**:

1. **Stop Execution Immediately**:
   ```
   🚫 EXECUTION STOPPED
   Validation failed at: [Task Title]
   ```

2. **Identify Rollback Point**:
   ```bash
   # Find last successful milestone commit
   git log --oneline --grep="milestone" -1
   ```

3. **Rollback Code**:
   ```bash
   # Reset to last good state
   git reset --hard [last-good-commit]

   # OR use stash if you want to preserve work
   git stash save "Failed execution at [task-title]"
   git reset --hard [last-good-commit]
   ```

4. **Rollback State Files**:
   ```bash
   # Revert task status to PENDING
   # Update TASKS file to mark task as PENDING

   # Document failure in CONTEXT_LOG
   ```

5. **Log Rollback**:
   ```bash
   echo "[$(date '+%Y-%m-%d %H:%M')] ROLLBACK to $(git rev-parse --short HEAD) — Reason: Validation failed at [task-id]" >> [task-name]-provenance.log
   ```

6. **Report to User**:
   ```
   🔄 ROLLBACK COMPLETE

   Reverted to: [commit] ([milestone])
   Reason: [Failure description]

   Next steps:
   1. Review failure in CONTEXT_LOG
   2. Fix underlying issue
   3. Re-run milestone execution

   Stashed work available: git stash pop
   ```

## X. Integration with Slash Commands

This skill works alongside the existing slash commands:

### Skill as Primary Entry Point

When user says "continue work" or Claude detects AA-MA artifacts:
1. **Skill detects context** → Loads AA-MA files → Determines mode → Executes

### Slash Commands as Explicit Overrides

User can explicitly choose execution mode:
- `/execute-aa-ma-step` → Forces Step mode
- `/execute-aa-ma-milestone` → Forces Milestone mode (recommended)
- `/execute-aa-ma-full` → Forces Full automation

### Workflow Example

```
User: "Continue the user-auth work"

Claude (skill detection):
✅ Detected .claude/dev/active/user-auth/
📂 Loading AA-MA artifacts...
🎯 Current milestone: Implement parallel execution
📋 Recommending: Milestone mode (strict validation)

Proceed with milestone execution? (yes/no/step/full)

User: "yes"

Claude: [Executes milestone using this skill's workflow]
```

## XI. Error Handling

### Common Errors and Resolutions

#### 1. Missing AA-MA Files

**Error**:
```
❌ MISSING: user-auth-reference.md
```

**Resolution**:
```
AA-MA artifacts incomplete.

Fix:
1. Run /ultraplan to regenerate artifacts
2. OR manually create missing files:
   touch .claude/dev/active/[task-name]/[task-name]-reference.md
```

#### 2. Multiple ACTIVE Tasks

**Error**:
```
❌ Multiple ACTIVE tasks detected:
- Task A: Status ACTIVE
- Task B: Status ACTIVE
```

**Resolution**:
```
Only ONE task should be ACTIVE at a time.

Fix:
1. Review both tasks
2. Mark one as PENDING
3. Continue with remaining ACTIVE task
```

#### 3. Unmet Dependencies

**Error**:
```
🚫 BLOCKED: Unmet dependencies
Task: Implement API endpoint
Requires: Database schema (Status: PENDING)
```

**Resolution**:
```
Complete prerequisite tasks first.

Fix:
1. Execute dependency: "Database schema"
2. Mark COMPLETE
3. Re-run current task
```

#### 4. Context Token Limit

**Error**:
```
⚠️ Token usage: 85% (170K/200K)
Risk of context loss
```

**Resolution**:
```
Initiate context compaction.

Fix:
1. Summarize completed work
2. Update CONTEXT_LOG with compaction summary
3. Reset session
4. Reload AA-MA files
5. Continue from current task
```

#### 5. Validation Failure

**Error**:
```
❌ VALIDATION FAILED
Criterion: All tests must pass
Expected: 100% pass rate
Actual: 2 tests failing
```

**Resolution**:
```
Fix failing tests before proceeding.

Fix:
1. Review test failures
2. Fix underlying issues
3. Re-run tests
4. Re-run validation
```

## XII. Best Practices

### 1. Proactive Detection

**Always check for AA-MA tasks at session start**:
```bash
ls -lt .claude/dev/active/ 2>/dev/null
```

Don't wait for user to mention AA-MA - proactively detect and use.

### 2. Prefer Milestone Mode

**Default to milestone execution** for most work:
- Provides quality gates (strict validation)
- Natural checkpoints (git commits + tags)
- Balanced structure and flexibility

Use Step mode only for exploration. Use Full mode only for well-tested plans.

### 3. Update State Immediately

**Never batch state updates**:
- Update TASKS immediately after task completion
- Extract facts to REFERENCE in real-time
- Document decisions in CONTEXT_LOG as they happen

Batching leads to missed updates and state drift.

### 4. Validate Early and Often

**Don't skip validation checks**:
- Pre-execution: Check dependencies, blockers, resources
- During execution: Verify acceptance criteria continuously
- Post-execution: Run tests, check for regressions

Early validation prevents costly rollbacks.

### 5. Document Decisions, Not Actions

**In CONTEXT_LOG, focus on "why" not "what"**:

Good:
```markdown
**Decision**: Use PostgreSQL instead of SQLite
**Rationale**: Need concurrent writes for multi-agent system
**Trade-off**: More complex deployment, but better scalability
```

Bad:
```markdown
**Decision**: Installed PostgreSQL
**Rationale**: We needed a database
```

### 6. Use Complexity Scores

**High complexity (≥80%) signals need for extra care**:
- Break into smaller sub-tasks
- Add human review checkpoints
- Increase testing coverage
- Document more thoroughly

Don't rush high-complexity tasks.

### 7. Leverage Provenance Log

**Use provenance for debugging**:
- Track when issues were introduced (git bisect)
- Identify patterns (frequent rollbacks on specific tasks)
- Measure velocity (commits per milestone)

Provenance is your audit trail - use it.

## XIII. Checklist for Using This Skill

**Before invoking skill**:
- ☐ Checked `.claude/dev/active/` for AA-MA tasks
- ☐ Confirmed user intent matches AA-MA execution
- ☐ Identified which task/milestone to execute

**After invoking skill**:
- ☐ Loaded 5 AA-MA files with XML delimiters
- ☐ Validated file structure (all files exist, non-empty)
- ☐ Identified current ACTIVE task (or next PENDING)
- ☐ Displayed execution plan to user
- ☐ Got user confirmation to proceed
- ☐ Chose appropriate execution mode (Step/Milestone/Full)

**During execution**:
- ☐ **MUST** mark task ACTIVE before starting
- ☐ **MUST** follow acceptance criteria exactly
- ☐ **MUST** sync Result Log IMMEDIATELY after each sub-step (L-080 — BLOCKING, not batched)
- ☐ **MUST** verify Result Log is non-empty before proceeding to next step
- ☐ **MUST** validate work against criteria
- ☐ **MUST** update state files immediately (not batched)
- ☐ **MUST** extract facts to REFERENCE
- ☐ **MUST** document decisions in CONTEXT_LOG
- ☐ **MUST** commit AND push work (with AA-MA signature in commit footer)
- ☐ **MUST** include `[AA-MA Plan] {task-name} .claude/dev/active/{task-name}` in commit
- ☐ **MUST** log commit to PROVENANCE

**At milestone boundary**:
- ☐ **MUST** run Sub-Step Consistency Check: zero PENDING sub-steps (L-081 — BLOCKING)
- ☐ **MUST** run Sub-Step Status Audit in Finalization Step 1 Part A (L-083)
- ☐ **MUST** invoke `Skill(impact-analysis)` before marking COMPLETE
- ☐ **MUST** output consolidated impact analysis for all modified files
- ☐ **MUST** resolve any HIGH risk impacts before proceeding

**After execution**:
- ☐ Marked task COMPLETE
- ☐ Updated Result Log with output
- ☐ Ran tests (if applicable)
- ☐ Created git tag (if milestone)
- ☐ Checked token usage (compact if needed)
- ☐ Identified next task to execute

## XIV. Summary

**This skill provides**:
- 🎯 Proactive detection of AA-MA tasks
- 📋 Structured execution workflows (Step/Milestone/Full)
- ✅ Strict validation and quality gates
- 🔄 Rollback procedures for failures
- 📊 Real-time state tracking
- 📝 Automated provenance logging
- 🧠 Context compaction when needed

**Use this skill** whenever AA-MA artifacts exist. It ensures consistency, prevents context drift, and maintains audit trails for complex multi-session development work.

**Integration**: Works alongside `/execute-aa-ma-*` slash commands, providing the underlying workflow that those commands invoke.

---

**End of aa-ma-execution/SKILL.md**
