---
name: aa-ma-execution
description: "Shared execution rules for AA-MA plans: context-injection order, validation, provenance logging and sync discipline. Use when resuming AA-MA work without a named scope, or when another execution skill needs these rules. A request for the next or a specific step goes to execute-aa-ma-step; a milestone goes to execute-aa-ma-milestone."
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
- **Report** to user: "AA-MA files incomplete. Run `/aa-ma-plan` to initialize properly."

### 3.5 Pre-Flight System Mapping (First Milestone Only)

If this is the **first milestone** being executed and it touches 3+ files or unfamiliar code, invoke `Skill(system-mapping)` for the 5-point pre-flight check before starting execution. Skip for subsequent milestones unless they shift to a completely different subsystem. Skip if system-mapping was already run during `/aa-ma-plan`.

### 4. Identify Current Task

Parse `[task-name]-tasks.md` to find the current ACTIVE task:

**HTP Node Structure**:
```markdown
## Milestone N: Title
- Status: PENDING | ACTIVE | COMPLETE
- Dependencies: [List of prerequisite Task IDs]
- Complexity: [0-100%]
- Acceptance Criteria: [Clear, testable criteria]

### Sub-step N.M: [Action]
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

### 7. Mode-Based Execution Control (HITL / AFK Dispatch)

Every task in `tasks.md` carries a `Mode:` field that controls execution behaviour.

**Parsing Mode (precedence order):**
1. Sub-step `Mode:` field (highest priority)
2. Parent milestone `Mode:` field
3. Default: `HITL` (safe default — pauses for human input)

**When Mode: HITL (Human In The Loop):**
- Display task summary and acceptance criteria
- Activate `Skill(token-compression)` at **lite** intensity (preserve clarity for human review)
- Use `AskUserQuestion` with three options:
  - **Proceed** — execute the task
  - **Skip** — mark `Status: SKIPPED — User skipped at HITL gate`, move to next task
  - **Abort** — halt execution, keep milestone `Status: ACTIVE`
- Wait for user response before executing any work

**When Mode: AFK (Away From Keyboard):**
- Activate `Skill(token-compression)` at **ultra** intensity (maximum compression for autonomous execution)
- Execute task directly without pause
- Log in Result Log: `Mode: AFK — auto-dispatched`
- No user interaction unless the task fails or hits a HARD gate

**Token Compression Override:**
Manual override: ask for "compress lite|full|ultra" at any point during execution.
See `Skill(token-compression)` for full intensity level details and auto-clarity exceptions.

**HARD Gate Override:**
HARD gates always pause for approval regardless of Mode. If a milestone has `Gate: HARD`, the finalization protocol (Section VI, Step 2.6) enforces user approval even for AFK tasks.

**Display format:**
```
🔄 Task Mode: [HITL — pauses for input / AFK — auto-dispatch]
```

## IV. Execution Workflows

See [execution-workflows.md](references/execution-workflows.md#iv-execution-workflows) — how a step, a milestone and a full plan are executed, sub-step by sub-step.

## V. AA-MA Commit Signature — MANDATORY

See [commit-signature.md](references/commit-signature.md#v-aa-ma-commit-signature--mandatory) — the footer every commit carries while a plan is active, with examples.

---

## VI. Finalization Protocol — MANDATORY

See [finalization-protocol.md](references/finalization-protocol.md#vi-finalization-protocol--mandatory) — the integrity check, doc update, HARD gate and approval steps before a milestone is COMPLETE.

---

## VII. State Management — MANDATORY SYNC

**CRITICAL**: You **MUST** update state files immediately after each task completion. No exceptions. No batching.

> **Root Cause of Sub-Step Drift (L-080, L-082):** When the lead orchestrator executes steps directly (not via agents), results exist in conversation context but never reach tasks.md unless explicitly written. Agents have a built-in forcing function (their prompt contract requires Result Log output). The lead orchestrator does NOT — making this section the primary defense against state drift.

### Updating AA-MA Files During Execution

#### 1. Update TASKS (`[task-name]-tasks.md`) — IMMEDIATELY, NOT AT MILESTONE END

**After each sub-step (not each milestone — EACH SUB-STEP):**
```markdown
## Milestone N: Title
- Status: COMPLETE  ← Update from ACTIVE
- Dependencies: [...]
- Complexity: [...]
- Acceptance Criteria: [...]

### Sub-step N.M: [Action]
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

See [compaction-and-rollback.md](references/compaction-and-rollback.md#viii-context-compaction) — how to compact context mid-task, validate acceptance criteria and roll back a step.

## IX. Validation & Rollback

See [compaction-and-rollback.md](references/compaction-and-rollback.md#ix-validation--rollback) — how to compact context mid-task, validate acceptance criteria and roll back a step.

## IX.5 Goal-Condition Synthesis Patterns (Optional, Claude Code `/goal`)

See [goal-conditions.md](references/goal-conditions.md#ix5-goal-condition-synthesis-patterns-optional-claude-code-goal) — optional `/goal` conditions built from AA-MA artefacts.

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

See [error-handling.md](references/error-handling.md#xi-error-handling) — common errors during execution and how to resolve each.

## XII. Best Practices

See [best-practices.md](references/best-practices.md#xii-best-practices) — habits that keep execution state accurate across sessions.

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
