# Bidirectional Sync Protocol

How the TaskList (agent-teams task tracking) and AA-MA files (`.claude/dev/active/[task]/`) stay synchronized during team-based execution.

**Key principle:** Semantic merge with ambiguity escalation. Each domain has a single owner, eliminating routine conflicts. Genuinely ambiguous cases are escalated to the user.

---

## 1. Domain Ownership

Each piece of data has exactly one authoritative owner. This eliminates conflicts for ~95% of updates.

| Domain | Owner | What It Includes | Examples |
|--------|-------|-----------------|----------|
| **Status** | TaskList | Task/milestone status, task owner, blockedBy, task creation/deletion | `PENDING → ACTIVE → COMPLETE`, assigning tasks to teammates |
| **Content** | AA-MA | Acceptance criteria, result logs, immutable facts, architectural decisions, plan text | Milestone acceptance criteria in tasks.md, facts in reference.md, decisions in context-log.md |
| **Metadata** | Both (append-only) | Provenance entries, context-log timestamps, execution telemetry | Both systems can append entries; neither overwrites the other's entries |

### Decision Table

When an update occurs, determine the domain and apply the rule:

| Update Type | Domain | Owner | Action |
|------------|--------|-------|--------|
| Mark task COMPLETE | Status | TaskList | Lead updates TaskList via TaskUpdate, then syncs Status to tasks.md |
| Assign task to teammate | Status | TaskList | Lead uses TaskUpdate with owner, no AA-MA update needed |
| Add blockedBy dependency | Status | TaskList | Lead uses TaskUpdate, then syncs dependency to tasks.md if relevant |
| Fill Result Log after step | Content | AA-MA | Lead writes to tasks.md Result Log, TaskList description unchanged |
| Extract new fact | Content | AA-MA | Lead writes to reference.md, no TaskList update |
| Record architectural decision | Content | AA-MA | Lead writes to context-log.md, no TaskList update |
| Modify acceptance criteria | **Ambiguous** | **Escalate** | See Section 3 — could be either domain |
| Log commit hash | Metadata | Both | Append to provenance.log AND optionally note in TaskList |
| Log team spawn/shutdown | Metadata | Both | Append to provenance.log |

---

## 2. Sync Events

### When Syncs Happen

| Trigger | Direction | What Syncs |
|---------|-----------|------------|
| **Task completion** (teammate reports done) | TaskList → AA-MA | Lead marks task complete in TaskList, then updates tasks.md Status + Result Log |
| **New fact discovered** (teammate reports finding) | Content → AA-MA only | Lead writes fact to reference.md (TaskList not affected) |
| **Design decision made** (architect recommends) | Content → AA-MA only | Lead writes decision to context-log.md |
| **Milestone boundary** (all tasks done) | Bidirectional | Full sync: TaskList statuses → tasks.md, AA-MA content verified, provenance updated |
| **Team shutdown** (Phase 7) | AA-MA ← final state | Lead performs final sync of all TaskList statuses to tasks.md before TeamDelete |

### Who Performs Sync

- **The team lead (your session)** performs ALL syncs
- Teammates do NOT write to AA-MA files directly
- Teammates report results via `SendMessage` — lead interprets and writes to AA-MA
- This single-writer pattern prevents concurrent write conflicts

### Sync Timing

- **Immediate** after each task completion (no batching — per AA-MA no-batching rule)
- **Before** AA-MA Finalization Protocol at milestone boundaries
- **During** Phase 7 cleanup before TeamDelete

---

## 3. Ambiguity Detection

Some updates don't clearly belong to one domain. These are **ambiguous** and require user input.

### What Counts as Ambiguous

| Scenario | Why It's Ambiguous | Resolution Path |
|----------|--------------------|----------------|
| Teammate wants to change acceptance criteria | Content domain (AA-MA owns criteria), but request came from TaskList context (teammate) | Escalate: show original criteria + proposed change |
| Teammate discovers a fact that contradicts reference.md | Content domain, but the contradiction means either reference.md or teammate is wrong | Escalate: show both values, user decides which is correct |
| Status update implies content change (e.g., BLOCKED) | Status is TaskList domain, but BLOCKED requires a blocker description in context-log.md (content) | Auto-handle: update TaskList status AND append blocker to context-log.md (both domains, no conflict) |
| Teammate suggests modifying the plan scope | Content domain (AA-MA owns plan), but could affect TaskList task structure | Escalate: present scope change proposal to user |
| Result Log content changes task dependencies | Content + Status overlap | Escalate: user decides if dependencies need updating |

### Detection Rules

An update is ambiguous when:
1. It touches data in a domain the updater doesn't own, OR
2. It contradicts existing data in any domain, OR
3. It would change the structure (not just values) of AA-MA files (e.g., adding/removing milestones)

---

## 4. Escalation Protocol

When an ambiguous case is detected:

### Step 1: Identify the Conflict

```
⚠️ Sync Conflict Detected

Domain: [Status | Content | Cross-domain]
Source: [Teammate name] via [SendMessage | TaskUpdate]
Target: [AA-MA file name]

Current value (AA-MA):
  [current content]

Proposed value (TaskList/Teammate):
  [proposed content]

Reason for ambiguity: [which detection rule triggered]
```

### Step 2: Present to User

Use `AskUserQuestion`:

```
Sync conflict in [domain]:

Current (AA-MA): [value]
Proposed (teammate): [value]

Which should we keep?
- Keep current (AA-MA value)
- Accept proposed (teammate value)
- Merge both (I'll explain how)
```

### Step 3: Resolve and Log

After user decides:
1. Apply the chosen value to the appropriate file(s)
2. Log the resolution to context-log.md:

```markdown
## [YYYY-MM-DD] Sync Conflict Resolved

**Conflict:** [description]
**Source:** [teammate name]
**Resolution:** [Keep current | Accept proposed | Merged]
**Rationale:** [user's reasoning if provided]
**Entry type:** CONFLICT_RESOLVED
```

### Step 4: Notify Teammate (if applicable)

If the teammate's proposed change was rejected, message them:
```
SendMessage to [teammate]:
"Your proposed change to [item] was reviewed. Decision: [kept current value].
Reason: [brief]. Please proceed with current state."
```

---

## 5. Examples

### Example 1: Routine Status Sync (No Conflict)

**Scenario:** Implementer-1 completes "Implement JWT token generation" and messages the lead.

**Sync flow:**
1. Lead receives message: "JWT implementation complete, tests pass"
2. Lead updates TaskList: `TaskUpdate(taskId: "3", status: "completed")`
3. Lead syncs to AA-MA tasks.md:
   - Step 2.2 Status: `PENDING` → `COMPLETE`
   - Step 2.2 Result Log: "JWT token generation with RS256 signing. Tests: 5/5 pass."
4. Lead updates reference.md: adds `JWT_ALGORITHM: RS256` as new fact
5. No conflict — clean sync.

---

### Example 2: Ambiguous Case — Teammate Modifies Acceptance Criteria

**Scenario:** Architect teammate messages: "After reviewing the codebase, I think the acceptance criterion 'All token edge cases handled' is too vague. It should be 'Token expiry, refresh, and revocation handled with specific error codes'."

**Detection:** Acceptance criteria is Content domain (AA-MA owns). The change request came from a teammate. Criteria modification = ambiguous.

**Escalation:**
```
⚠️ Sync Conflict Detected

Domain: Content (acceptance criteria)
Source: Architect via SendMessage
Target: tasks.md Step 2.3 Acceptance Criteria

Current (AA-MA):
  "All token edge cases handled"

Proposed (Architect):
  "Token expiry, refresh, and revocation handled with specific error codes"

Reason: Teammate proposing content-domain change
```

**User decides:** "Accept proposed — it's more specific and testable."

**Resolution:**
1. Update tasks.md Step 2.3 Acceptance Criteria
2. Log to context-log.md as CONFLICT_RESOLVED
3. Message Architect: "Your criteria update was accepted."

---

### Example 3: Append-Only Metadata (No Conflict Possible)

**Scenario:** During execution, two events happen close together:
- Lead appends to provenance.log: `[timestamp] Team impl-auth spawned — 4 teammates`
- Implementer completes task, lead appends: `[timestamp] Commit abc123 — TaskID: step-2.2`

**Sync flow:** Both are append-only metadata. Each entry is a new line. No conflict is possible — entries accumulate in chronological order.

---

### Example 4: Status Update with Content Implication

**Scenario:** Implementer-2 hits a blocker and messages: "Can't proceed — the database schema in reference.md is wrong. Column `user_id` should be `UUID` not `INT`."

**Sync flow:**
1. Status update (TaskList): Mark task as BLOCKED → `TaskUpdate(taskId: "4", status: "pending")`
2. Content update (AA-MA): The blocker description goes to context-log.md
3. Fact correction (AA-MA): The schema error in reference.md is **ambiguous** — it contradicts existing content

**Escalation for the fact correction:**
```
Teammate reports reference.md fact is incorrect:
Current: user_id column type = INT
Proposed: user_id column type = UUID
```

**User decides:** "Accept proposed — teammate is right, the schema design changed."

**Resolution:**
1. Update reference.md: `user_id: UUID`
2. Log to context-log.md: CONFLICT_RESOLVED with rationale
3. Unblock the task

---

## Quick Reference Card

```
DOMAIN OWNERSHIP
├── Status → TaskList (PENDING/ACTIVE/COMPLETE, owner, blockedBy)
├── Content → AA-MA (criteria, facts, decisions, result logs)
├── Metadata → Both (append-only, no conflicts)
└── Ambiguous → Escalate to user

SYNC TIMING
├── After task completion → immediate (no batching)
├── At milestone boundary → full bidirectional sync
└── At team shutdown → final state sync

WHO SYNCS
├── Lead performs ALL syncs
├── Teammates report via SendMessage
└── Single-writer pattern prevents conflicts

ESCALATION
├── Detect: domain ownership violated or data contradicted
├── Present: show both values to user
├── Resolve: apply user decision
└── Log: CONFLICT_RESOLVED in context-log.md
```

---

## Cross-References

- **AA-MA Integration**: `~/.claude/skills/agent-teams/references/AA_MA_INTEGRATION.md`
- **Phase 5 Artifact Creation**: `~/.claude/skills/aa-ma-plan-workflow/references/PHASE_5_ARTIFACT_CREATION.md`
- **Agent-Teams SKILL.md**: `~/.claude/skills/agent-teams/SKILL.md` (Phase 5 Coordinate, Phase 7 Cleanup)
- **AA-MA Execution Skill**: `~/.claude/skills/aa-ma-execution/SKILL.md` (no-batching rule, state update cycle)
