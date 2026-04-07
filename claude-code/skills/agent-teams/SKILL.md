---
name: agent-teams
description: >-
  Orchestrate Claude Code agent teams for collaborative multi-agent work.
  Use when tasks need 2+ coordinated agents that communicate with each other.
  Supports research teams (competing hypotheses, parallel investigation),
  implementation teams (architect + implementers + reviewer), hybrid teams,
  and code review teams. Integrates with AA-MA for structured execution.
  Handles team creation, task distribution, inter-agent debate, progress
  monitoring, error recovery, and graceful shutdown. Keywords: team, teammate,
  multi-agent, swarm, coordinate, collaborate, spawn agents, parallel agents
  communicate, competing hypotheses, research team, implementation team.
---

# Agent Teams Orchestration

Orchestrate persistent Claude Code agent teams with shared task lists, inter-agent messaging, and structured coordination for complex collaborative work.

## When to Use This Skill

**Use agent-teams when:**
- Task needs 2+ agents that **communicate** with each other
- Research needs **competing hypotheses** with adversarial debate
- Implementation needs **architect + implementers + reviewer** coordination
- Work benefits from persistent teammates over one-shot subagents

**Do NOT use — use these instead:**
- Tasks are independent, no communication needed → `dispatching-parallel-agents`
- Sequential tasks with review gates, same session → `subagent-driven-development`
- Single investigation or code change → direct execution

### Decision Flowchart

```
Complex task requiring multiple agents?
├── NO → Execute directly or use a single subagent
└── YES → Do agents need to communicate/coordinate?
    ├── NO → dispatching-parallel-agents (one-shot, parallel)
    └── YES → Are tasks sequential with review between each?
        ├── YES → subagent-driven-development (same session)
        └── NO → ★ agent-teams (persistent, communicating)
```

---

## Task Classification

Classify the user's request to select the right team type:

```
User Request → keyword + intent analysis:

  "research/investigate/explore/compare/analyze/evaluate"
    → RESEARCH team

  "implement/build/create/fix/refactor/deploy/migrate"
    → IMPLEMENTATION team

  "review/audit/check/validate/assess"
    → REVIEW team

  Both research + implementation signals present
    → HYBRID team (research phase → implementation phase)

  AA-MA active? → read milestone type for additional signal

  Ambiguous? → AskUserQuestion to clarify
```

| Type | When | Team Size | Debate Mode |
|------|------|-----------|-------------|
| RESEARCH | Investigation, comparison, analysis | 2-4 researchers + synthesizer | YES |
| IMPLEMENTATION | Building, fixing, deploying | architect + 1-3 impl + reviewer | No |
| HYBRID | Research then build | Phase 1: research → Phase 2: impl | Phase 1 only |
| REVIEW | Code audit, security review | 2-3 specialized reviewers | No |

---

## 7-Phase Lifecycle

```
┌─────────────────────────────────────────────────────┐
│ Phase 1: ANALYZE  → Classify task, detect AA-MA     │
│ Phase 2: COMPOSE  → Select roles, size team         │
│ Phase 3: APPROVE  → Present proposal to user        │
│ Phase 4: SPAWN    → TeamCreate, spawn teammates     │
│ Phase 5: COORDINATE → Messages, progress, debate    │
│ Phase 6: SHUTDOWN → Drain, verify, shutdown          │
│ Phase 7: CLEANUP  → TeamDelete, report, AA-MA sync  │
└─────────────────────────────────────────────────────┘
```

### Phase 1: Task Analysis

1. Parse user intent — extract keywords, scope, complexity
2. Check `.claude/dev/active/` for AA-MA tasks
3. Classify: RESEARCH / IMPLEMENTATION / HYBRID / REVIEW
4. Estimate team size (2-5 teammates; below 2 → recommend subagents instead)
5. If ambiguous, ask user via AskUserQuestion

### Phase 2: Team Composition

Select roles from **ROLE_TEMPLATES.md** based on task type:

| Type | Roles to Spawn |
|------|---------------|
| RESEARCH | 2-4 Researchers (Explore) + optional Synthesizer (Explore) |
| IMPLEMENTATION | 1 Architect (Plan) + 1-3 Implementers (general-purpose) + 1 Reviewer (code-reviewer) |
| HYBRID | Phase 1: Research roles → Phase 2: Implementation roles |
| REVIEW | 2-3 Reviewers (code-reviewer / security-auditor / test-automator) |

**Plan approval logic (adaptive, per-teammate):**
```
Teammate modifies core/shared modules (3+ importers)? → plan mode required
Modifies API contracts, DB schema, config?             → plan mode required
Creates new isolated files only?                       → NOT required
Writes tests only?                                     → NOT required
Research/review role?                                  → NEVER required
```

**Team naming convention:** `{task-type}-{short-descriptor}` (e.g., `research-auth-audit`, `impl-user-dashboard`)

### Phase 3: User Approval

Present the team proposal via AskUserQuestion:

```
Team Proposal: {team-name}
Type: {RESEARCH|IMPLEMENTATION|HYBRID|REVIEW}
Teammates ({count}):
  - {role}: {name} ({agent-type}) — {purpose}
  - ...
Tasks ({count}):
  - {task summary} → assigned to {name}
  - ...
AA-MA: {active task name | not active}
Estimated scope: {brief}

Approve this team configuration?
- Approve (Recommended)
- Modify (adjust roles/tasks)
- Cancel
```

### Phase 4: Team Spawn

Execute in this order:

1. **TeamCreate** — create team with descriptive name
2. **TaskCreate** — create all tasks with descriptions, activeForm
3. **TaskUpdate** — set dependencies (addBlockedBy) between tasks
4. **Task tool** — spawn each teammate with:
   - `team_name` parameter
   - `name` parameter (human-readable role name)
   - `subagent_type` from role template
   - `mode` set appropriately (plan for risky changes)
   - Prompt from role template with task-specific details
5. **TaskUpdate** — assign tasks to teammates (set owner)

**Spawn prompt structure:**
```
You are the {role} on team "{team-name}".

Your assignment: {task description}

Team context:
- Team type: {type}
- Your teammates: {list with roles}
- Your tasks: {assigned task IDs and descriptions}

Working directory: {path}

Instructions:
1. Read your assigned tasks via TaskGet
2. Mark tasks in_progress via TaskUpdate when starting
3. Communicate findings/blockers via SendMessage to team lead
4. Mark tasks completed via TaskUpdate when done
5. Check TaskList for next available work

{role-specific instructions from ROLE_TEMPLATES.md}
```

### Phase 5: Coordinate & Monitor

As team lead (your session), you:

1. **Receive messages** — teammates auto-deliver messages when they complete tasks or need help
2. **Track progress** — periodically check TaskList for status
3. **Unblock teammates** — answer questions, resolve conflicts, reassign work
4. **Sync state** — after each task completion, sync TaskList↔AA-MA per SYNC_PROTOCOL.md
5. **Trigger quality gates** — see QUALITY_GATES.md
6. **Handle errors** — see ERROR_RECOVERY.md

**AA-MA Sync (if active):** After each teammate task completion, immediately update AA-MA files (tasks.md Result Log, reference.md facts, context-log.md decisions, provenance.log). Follow domain ownership rules in `references/AA_MA_INTEGRATION.md` § Bidirectional Sync Protocol. Escalate ambiguous updates to user.

**For RESEARCH teams — Competing Hypotheses Protocol:**

After researchers complete initial investigation:
1. SendMessage to each researcher: "Share your findings and explicitly challenge the other researchers' conclusions"
2. Allow one debate round via peer SendMessage
3. Synthesizer (or lead) consolidates surviving conclusions
4. Only findings that survived adversarial challenge are reported

> Detail: See **references/TEAM_PATTERNS.md** § Competing Hypotheses

### Phase 6: Shutdown

Follow the graceful shutdown protocol:

1. **Drain** — message busy teammates to finish current task (don't start new)
2. **Verify** — TaskList check, all tasks complete or explicitly deferred
3. **Shutdown** — SendMessage type:shutdown_request to each (reverse spawn order)
4. **Handle rejections** — if teammate rejects, allow to finish, retry

> Detail: See **references/SHUTDOWN_PROTOCOL.md**

### Phase 7: Cleanup & Report

1. **Final AA-MA sync** — if active, perform final bidirectional sync:
   - Sync all remaining TaskList statuses → tasks.md
   - Verify all AA-MA content is current
   - Follow SYNC_PROTOCOL.md § Team Shutdown sync
2. **TeamDelete** — remove team and task directories
3. **Final report** — summarise to user:
   - Tasks completed vs deferred
   - Key findings (research) or changes made (implementation)
   - Files modified
   - Any follow-up actions needed

> Detail: See **references/AA_MA_INTEGRATION.md** § Bidirectional Sync Protocol

---

## AA-MA Integration

When `.claude/dev/active/` contains an active task:

- **Detection**: Check for active AA-MA task at Phase 1
- **Milestone mapping**: Parse tasks.md ACTIVE milestone → map to team tasks
- **State sync**: Teammate completions update tasks.md, reference.md, context-log.md, provenance.log
- **Finalization**: Run AA-MA Finalization Protocol at milestone boundaries
- **Commits**: Include AA-MA commit signature

The skill works identically without AA-MA — state sync is simply skipped.

> Detail: See **references/AA_MA_INTEGRATION.md**

---

## Error Handling

| Scenario | Response |
|----------|----------|
| File conflict between teammates | See ERROR_RECOVERY.md § File Conflicts |
| Teammate stuck/unresponsive | Message → wait → reassign → replace |
| Task fails | Retry same → different teammate → escalate to user |
| Partial completion | Preserve state, present options to user |

> Detail: See **references/ERROR_RECOVERY.md**

---

## Quality Gates

| Gate | When | Enforced By |
|------|------|-------------|
| Design Review | Before implementation | Architect teammate |
| Code Review | After each impl task | Reviewer teammate |
| Test Verification | After impl + review | Tester or lead |
| Consistency Check | After all tasks | Lead (git status, diff, tests) |
| AA-MA Validation | Milestone boundary | Lead |

> Detail: See **references/QUALITY_GATES.md**

---

## Reference Files

| File | Content |
|------|---------|
| `references/ROLE_TEMPLATES.md` | 6 role definitions with spawn prompts |
| `references/TEAM_PATTERNS.md` | Research/impl/hybrid/review patterns |
| `references/AA_MA_INTEGRATION.md` | Milestone mapping, state sync |
| `references/ERROR_RECOVERY.md` | Conflicts, stuck, failures, partials |
| `references/SHUTDOWN_PROTOCOL.md` | 4-phase graceful + emergency shutdown |
| `references/QUALITY_GATES.md` | 5 gate types + enforcement |

## Templates

| File | Content |
|------|---------|
| `templates/research-team.md` | Ready-to-use research team config |
| `templates/implementation-team.md` | Ready-to-use implementation team config |
| `templates/review-team.md` | Ready-to-use review team config |

---

## Quick Reference Checklist

### Before Team Creation
- [ ] Classified task type (RESEARCH/IMPLEMENTATION/HYBRID/REVIEW)
- [ ] Checked for AA-MA active tasks
- [ ] Selected roles from ROLE_TEMPLATES.md
- [ ] Sized team (2-5; <2 → use subagents instead)
- [ ] Determined plan approval needs per teammate
- [ ] Presented proposal and got user approval

### During Team Execution
- [ ] All teammates spawned and tasks assigned
- [ ] Monitoring TaskList for progress
- [ ] Responding to teammate messages
- [ ] Quality gates enforced at checkpoints
- [ ] Research teams: debate round triggered after initial findings
- [ ] Errors handled per ERROR_RECOVERY.md

### After Team Completion
- [ ] All tasks completed or explicitly deferred
- [ ] Graceful shutdown executed (SHUTDOWN_PROTOCOL.md)
- [ ] TeamDelete called
- [ ] Final report presented to user
- [ ] AA-MA files updated (if active)
- [ ] Git commit with changes (AA-MA signature if applicable)
