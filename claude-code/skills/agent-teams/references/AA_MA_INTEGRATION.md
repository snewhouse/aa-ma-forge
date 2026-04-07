# AA-MA Integration

How agent-teams integrates with the Advanced Agentic Memory Architecture when an active task exists.

**Key principle:** AA-MA integration is additive. The agent-teams skill works identically with or without AA-MA — state synchronization is simply skipped when no active task exists.

---

## Detection

At Phase 1 (Task Analysis), check for active AA-MA tasks:

```bash
ls -lt .claude/dev/active/ 2>/dev/null | head -10
```

**If directories found:**
1. Read `[task]-tasks.md` to find milestone with `Status: ACTIVE`
2. Parse the active milestone's sub-steps, dependencies, and complexity scores
3. Use this to inform team composition and task creation
4. Enable state synchronization for all team operations

**If no directories found:**
- Proceed with standard team workflow
- Skip all AA-MA state sync steps

---

## Milestone-to-Team Mapping

Parse the ACTIVE milestone in `[task]-tasks.md` and map to team tasks:

### Mapping Rules

| AA-MA Element | Maps To |
|--------------|---------|
| Milestone title | Team name suffix |
| Sub-step | Team task (TaskCreate) |
| Sub-step dependencies | Task dependencies (addBlockedBy) |
| Complexity >= 80% | plan_mode_required for implementer |
| Acceptance criteria | Task description criteria |
| Status: ACTIVE | Current work |
| Status: PENDING | Future work (don't create tasks yet) |

### Example Mapping

**AA-MA tasks.md:**
```markdown
## Milestone 2: API Authentication Layer
- Status: ACTIVE
- Dependencies: Milestone 1
- Complexity: 75%

### Sub-step 2.1: Design auth middleware
- Status: PENDING
- Complexity: 40%
- Acceptance Criteria: Middleware design documented

### Sub-step 2.2: Implement JWT token generation
- Status: PENDING
- Complexity: 60%
- Acceptance Criteria: JWT tokens generated with proper claims

### Sub-step 2.3: Implement token validation
- Status: PENDING
- Complexity: 85%
- Acceptance Criteria: All token edge cases handled
```

**Mapped to team tasks:**
```
Team: impl-api-auth-layer
  Task 1: "Design auth middleware" → Architect (Complexity 40%, no plan mode)
  Task 2: "Implement JWT token generation" → Implementer 1 (Complexity 60%, no plan mode)
    addBlockedBy: [Task 1]
  Task 3: "Implement token validation" → Implementer 2 (Complexity 85%, plan mode REQUIRED)
    addBlockedBy: [Task 1]
  Task 4: "Review auth implementation" → Reviewer
    addBlockedBy: [Task 2, Task 3]
```

---

## State Synchronization

When AA-MA is active, team events trigger updates to the 5 AA-MA files:

### Sync Table

| Team Event | AA-MA File | Update |
|-----------|-----------|--------|
| Task marked complete | `tasks.md` | Mark sub-step COMPLETE, fill Result Log with summary |
| All tasks for milestone complete | `tasks.md` | Mark milestone COMPLETE |
| New facts discovered (research) | `reference.md` | Append immutable facts |
| Design decision made (architect) | `context-log.md` | Append decision with rationale |
| Code committed | `provenance.log` | Append `[timestamp] Commit {hash} — TaskID: {step}` |
| Error/blocker encountered | `context-log.md` | Append blocker description and resolution |
| Team spawned | `provenance.log` | Append `[timestamp] Team {name} spawned — {count} teammates` |
| Team shutdown | `provenance.log` | Append `[timestamp] Team {name} shutdown — {completed}/{total} tasks` |

### Sync Timing
- **Immediately** after each task completion (before moving to next task)
- **At milestone boundary** before running AA-MA Finalization Protocol
- **At team shutdown** during Phase 7 Cleanup

### Who Performs Sync
- **Lead session** (your session) performs all AA-MA updates
- Teammates do NOT write to AA-MA files directly
- Teammates report their results via SendMessage — lead updates AA-MA

---

## Workflow When AA-MA Is Active

### Phase 1: Task Analysis (enhanced)
1. Standard task classification
2. Read `.claude/dev/active/[task]/` — load REFERENCE and TASKS
3. Find ACTIVE milestone in tasks.md
4. Use milestone scope to inform team type and size

### Phase 2: Team Composition (enhanced)
1. Map milestone sub-steps to team tasks (see Mapping Rules)
2. Set plan_mode_required for complexity >= 80% sub-steps
3. Include AA-MA context in team proposal

### Phase 3: User Approval (enhanced)
- Show AA-MA task name and active milestone in proposal
- Show mapping from AA-MA sub-steps to team tasks

### Phase 4: Team Spawn (enhanced)
- Include relevant REFERENCE content in teammate spawn prompts
- Log team spawn to provenance.log

### Phase 5: Coordinate (enhanced)
- After each task completion, update tasks.md Result Log
- After research findings, update reference.md with new facts
- After design decisions, update context-log.md
- After commits, update provenance.log

### Phase 6-7: Shutdown & Cleanup (enhanced)
- Run AA-MA Finalization Protocol before TeamDelete:

**AA-MA Finalization Protocol:**
1. **Integrity Check** — verify each acceptance criterion from milestone
   ```
   Acceptance Criteria Verification:
   - [Criterion 1]: Confirmed — [evidence]
   - [Criterion 2]: Confirmed — [evidence]
   All [X] criteria verified.
   ```
2. **Documentation Auto-Update** — update all 5 AA-MA files
3. **User Authorization** — AskUserQuestion for explicit approval
4. **Confirmation** — display minimal confirmation
5. **Git commit** — with AA-MA commit signature:
   ```
   feat(task): description

   [AA-MA Plan] {task-name} .claude/dev/active/{task-name}
   ```

---

## Bidirectional Sync Protocol

When agent-teams executes with AA-MA active, the team lead must keep TaskList state and AA-MA file state synchronized. This follows the formal protocol documented in `~/.claude/skills/aa-ma-plan-workflow/references/SYNC_PROTOCOL.md`.

### Domain Ownership Summary

| Domain | Owner | Examples |
|--------|-------|---------|
| **Status** | TaskList | PENDING/ACTIVE/COMPLETE, task owner, blockedBy |
| **Content** | AA-MA | Acceptance criteria, result logs, facts, decisions |
| **Metadata** | Both (append-only) | Provenance entries, timestamps |
| **Ambiguous** | Escalate to user | Criteria changes, fact contradictions |

### Sync Rules for Team Lead

1. **After teammate completes task:** Update TaskList (TaskUpdate status:completed) AND AA-MA tasks.md (Status: COMPLETE + Result Log)
2. **After teammate discovers fact:** Write to AA-MA reference.md only (TaskList not affected)
3. **After design decision:** Write to AA-MA context-log.md only (TaskList not affected)
4. **After git commit:** Append to AA-MA provenance.log AND optionally note in TaskList
5. **If teammate proposes criteria change:** ESCALATE to user (ambiguous — see SYNC_PROTOCOL.md § 3)

### Conflict Resolution

When an update is ambiguous (touches data the updater doesn't own, contradicts existing data, or would change AA-MA file structure):

1. Identify the conflict domain and values
2. Present both values to user via AskUserQuestion
3. Apply user decision
4. Log as `CONFLICT_RESOLVED` in context-log.md
5. Notify teammate if their proposal was rejected

Full protocol: `~/.claude/skills/aa-ma-plan-workflow/references/SYNC_PROTOCOL.md`

---

## Non-AA-MA Mode

When no active AA-MA task exists, the skill operates identically but:
- Skips all AA-MA file reads at Phase 1
- Skips state synchronization at Phase 5
- Skips AA-MA Finalization Protocol at Phase 6-7
- Skips AA-MA commit signature
- All other phases (classification, composition, approval, spawn, coordinate, shutdown, cleanup) work exactly the same

---

## Context Injection for Teammates

When AA-MA is active, include relevant context in teammate spawn prompts:

```
{For implementers — include from reference.md:}
Key facts for your implementation:
- API_ENDPOINT: {value}
- DB_SCHEMA: {value}
- {other relevant constants}

{For researchers — include from tasks.md:}
Current milestone context:
- Milestone: {title}
- Acceptance criteria: {list}
- Known issues: {from context-log.md}
```

**Token budget:** Only inject facts relevant to the teammate's specific task. Do not dump entire AA-MA files into spawn prompts.
