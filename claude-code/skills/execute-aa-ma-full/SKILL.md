---
name: execute-aa-ma-full
description: Execute complete AA-MA plan from current position to completion with automated checkpoints. Run only when the user asks to run a whole AA-MA plan.
disable-model-invocation: true
---

# AA-MA Full Plan Execution

You are executing the **complete AA-MA plan** from current position to final completion.

**Scope**: All remaining milestones in tasks.md
**Validation**: Strict at every milestone boundary
**Git**: Auto-commit + provenance at each milestone, final tag on completion

⚠️ **Use this command only for well-understood plans that don't need frequent human checkpoints.**

---

## 1. Locate Active Task & Pre-Execution Validation

See [pre-execution-validation.md](references/pre-execution-validation.md#1-locate-active-task--pre-execution-validation) — the Tier 1 existence check and the Tier 2 validator dispatch, with auto-recovery.

---

## 2. Full Context Injection

See [context-and-goal.md](references/context-and-goal.md#2-full-context-injection) — which AA-MA files to load for a full run, and the optional /goal synthesis and bind for AFK runs.

---

## 2.5 Goal Synthesis & Bind (Optional, Recommended for AFK Runs)

See [context-and-goal.md](references/context-and-goal.md#25-goal-synthesis--bind-optional-recommended-for-afk-runs) — which AA-MA files to load for a full run, and the optional /goal synthesis and bind for AFK runs.

---

## 3. Validate Loaded Context

**Required checks**:
- ✅ All 5 AA-MA files exist and are readable
- ✅ REFERENCE contains key constants
- ✅ TASKS has clear HTP structure with Status fields
- ✅ At least one milestone has `Status: PENDING` or `Status: ACTIVE`
- ✅ All milestones have explicit Acceptance Criteria defined
- ✅ Dependencies between milestones are clearly specified

**If validation fails**:
```
ERROR: [Specific issue]
- Missing files → "AA-MA files incomplete. Run /aa-ma-plan or check directory."
- Malformed HTP → "tasks.md lacks proper HTP format."
- No pending milestones → "All milestones complete."
- Missing acceptance criteria → "One or more milestones lack acceptance criteria."
- Unclear dependencies → "Milestone dependencies not specified."
```

---

## 4. Parse HTP & Create TodoWrite Todos

**Parse tasks.md for complete HTP structure**:
- `## headers` = Milestones
- `### headers` = Sub-tasks
- Extract all metadata: `Status:`, `Dependencies:`, `Complexity:`, `Acceptance Criteria:`

**Identify execution plan**:
1. Count total milestones
2. Count PENDING/ACTIVE milestones
3. Count COMPLETE milestones
4. Identify first PENDING milestone (starting point)
5. Map dependency tree

**Create TodoWrite todos for ALL remaining work**:
- All PENDING/ACTIVE milestones
- All sub-tasks within those milestones

**Todo format**:
```json
{
  "content": "[Milestone/Task title]",
  "status": "pending|in_progress|completed",
  "activeForm": "[Present continuous form]"
}
```

**Hierarchical organization**:
```
- [ ] Milestone 1: [title]
  - [ ] Sub-task 1.1
  - [ ] Sub-task 1.2
- [ ] Milestone 2: [title]
  - [ ] Sub-task 2.1
  - [ ] Sub-task 2.2
```

---

## 4.5 Quality Standards (Actionable Triggers)

These principles apply DURING execution. Each has a trigger condition and skip condition.

- **KISS:** If implementation exceeds 200 lines for a single function or method, decompose before proceeding. Skip for generated code or data tables.
- **DRY:** Before writing a new utility function, grep the codebase for existing implementations. If a match exists, reuse it. Section B.5 (Post-Milestone Simplification Review) catches misses post-hoc.
- **SOLID:** If a class has >5 public methods, evaluate single-responsibility. If a module mixes data access + business logic + presentation, separate. Skip for scripts and one-off tools.
- **SOC:** If a file grows beyond one clear responsibility, split. If a function handles both data transformation and side effects, separate.
- **TDD:** If this milestone produces code, invoke `superpowers:test-driven-development`. Let the skill decide test strategy. Skip it only with a canonical `TDD-Waiver:` value (`engineering-standards.md` §2).
- **12-Factor:** If the task involves service deployment, API servers, or containerized applications, reference 12-Factor principles for config (env vars not files), statelessness, and port binding. For ALL tasks with `.env` files, verify env-var-drift compliance (see `rules/env-var-drift.md`).
- **Context7 MCP:** Use for library docs and code generation. Retry once on failure, then fall back to WebSearch + official docs.
- **WebSearch:** Fallback when Context7 fails. Also use proactively for unfamiliar APIs, recent library changes, or deployment patterns.

### Pre-Execution Check (First Milestone Only)

If this is the **first milestone** and it touches 3+ files or unfamiliar code, invoke `Skill(system-mapping)` for the 5-point pre-flight check. Skip for subsequent milestones.

---

## 5. Execute Plan Sequentially

**For each PENDING milestone (in order)**:

### 5.1 Pre-Flight Checks

1. **Update status**:
   - Set milestone `Status: PENDING` → `Status: ACTIVE`
   - Update TodoWrite milestone todo to `in_progress`

2. **Dependency advisory — never blocks** (map Ticket 16): run the fence from
   `/execute-aa-ma-milestone` §5.1 step 3 (`aa_ma_deps advisory "${TASKS_MD}"`), show the
   user any line it prints, log it to provenance.log, and continue.

### 5.2 Execute All Sub-Tasks

**For each sub-task in milestone**:
1. Mark TodoWrite sub-task as `in_progress`
1.5. **Mode Dispatch**: Parse `Mode:` from sub-task (inherit from milestone if absent, default HITL). HITL: display summary + criteria, `AskUserQuestion` [Proceed/Skip/Abort]. AFK: execute directly without pause.
2. Execute sub-task (use agents, skills, Context7 MCP as needed)
3. Verify result (guidance-based, trust your assessment)
4. Update `Result Log:` in tasks.md
5. Mark TodoWrite sub-task as `completed`

### 5.3 Milestone Boundary Validation (STRICT)

**REQUIRED validation before marking milestone COMPLETE:**

#### A. Acceptance Criteria Verification
- Explicitly verify EACH criterion met
- Document verification method/result for each
- If ANY fails → set `Status: BLOCKED`, HALT, alert user

#### B. Dependency Verification (for next milestone)
- Advisory only: the next milestone's `Dependencies:` are reported by its own §5.1 step 2
  when it becomes ACTIVE. Never halt on them.

#### C. Impact Analysis Verification (REQUIRED)

**Before completing milestone, verify no breaking changes introduced:**

1. **Invoke the impact-analysis skill** (`Skill(impact-analysis)`)
2. **Output consolidated impact analysis** for ALL files modified in this milestone
3. **Verify no unresolved cascade effects**

**Required output format** (consolidated for milestone):
```
📊 Impact Analysis: Milestone "[Milestone Title]"
┌─ Files Modified: [N]
│
├─ [file_path]
│  ├─ Upstream: [N] callers
│  ├─ Contract: [YES/NO]
│  └─ Risk: [LOW/MEDIUM/HIGH]
│
└─ Overall Risk: [LOW/MEDIUM/HIGH]
```

**Validation rules**:
- Overall Risk = LOW → Proceed to Test Execution
- Overall Risk = MEDIUM → Document cascade updates, then proceed
- Overall Risk = HIGH → HALT, present options (auto-fix, manual review, abort)

**Never complete milestone with unresolved HIGH risk impacts.**

#### D. Test Execution (if specified)
- Run ALL listed tests
- ALL must pass (zero failures)
- Document results in Result Log
- If failures → set `Status: BLOCKED`, HALT, alert user

### 5.4 Finalization Protocol — MANDATORY

Before marking the milestone COMPLETE and creating git checkpoint, execute this 4-step finalization protocol at EACH milestone boundary. **No exceptions.**

#### A. Integrity Check (Checklist Verification)

Display acceptance criteria verification to the user:

```
Acceptance Criteria Verification:
- ✓ [Criterion 1]: Confirmed - [brief evidence]
- ✓ [Criterion 2]: Confirmed - [brief evidence]

Gate: [HARD|SOFT] — [Approval artifact found / Convention-based]
All [X] criteria verified. Ready for finalization.
```

**Rules:**
- Every acceptance criterion must be explicitly listed with evidence
- If ANY criterion cannot be confirmed → HALT, do not proceed
- If `Gate: HARD` and no approval artifact in context-log.md → HALT, request approval (see `/execute-aa-ma-milestone` Section 7.1)
- If `[task]-tests.yaml` exists, auto-run tests for this milestone (see `/execute-aa-ma-milestone` Section 6.4)

#### B. Documentation Auto-Update

Automatically update all 5 AA-MA files:

| File | Auto-Update Action |
|------|-------------------|
| `tasks.md` | Mark milestone `Status: COMPLETE`, fill `Result Log:` |
| `reference.md` | Add any new immutable facts discovered |
| `context-log.md` | Append completion summary |
| `provenance.log` | Append completion entry (after commit) |
| `plan.md` | No change (historical record) |

#### B.5. Post-Milestone Simplification Review

**Skip if:** Only docs/config changed, diff < 20 lines code, or `--skip-simplify` flag passed to `/execute-aa-ma-full`.

Launch 3 parallel agents against milestone diff (reuse, quality, efficiency). CRITICAL findings require acknowledgment at approval gate. See `/execute-aa-ma-milestone` Section 6.6 for full protocol.

**Note:** For fully automated AFK runs, pass `--skip-simplify` to skip this review at every milestone and save tokens. The review is most valuable when running milestones interactively.

**On failure:** Skip review, log to provenance. Do NOT block finalization.

#### B.6. Post-Impl Adversarial Review (Phase 6.8 — NEW in v0.8.0)

Reference: ADR-0005 + `/execute-aa-ma-milestone` Section 6.8 (full anatomy).

**Skip if:** plan's `Created:` date is < v0.8.0 release tag commit date (grandfathered), OR `AA_MA_AUDIT_BUDGET=off`, OR `AA_MA_HOOKS_DISABLE=1`.

Delegate to `/execute-aa-ma-milestone` Section 6.8 — same logic, same agents:
the `verify-impl` skill orchestrator dispatches up to 5 audit agents
(code-reviewer, security-auditor, tdd-sequence-auditor,
context7-evidence-auditor, future-proofing-auditor) per the milestone's
plan-declared `Audit-Profile:` field. Aggregated verdict written to
`[task]-impl-review.md`.

**Verdicts:**
- `PASS` / `PASS_WITH_WARNINGS` → proceed to C (User Authorization)
- `BLOCKED` (any CRITICAL accepted via override panel) → HALT this milestone, surface remediation to user. Do NOT auto-advance to next milestone. The user must fix the accepted CRITICAL, re-run `/execute-aa-ma-milestone` (which re-runs §6.8), and only when §6.8 passes clean can `/execute-aa-ma-full` resume.

**Provenance:** §6.8 entry emitted by the milestone command itself. No duplicate entry from the full command — the delegation is logical, not physical.

#### C. User Authorization (Approval Gate)

Use AskUserQuestion to get explicit user approval:

```
📋 Finalization Review

Milestone: [Title]
Acceptance Criteria: [X/X] verified ✓

Ready to mark COMPLETE?
- Approve: Proceed with commit
- Review First: Show detailed verification
- Reject: Keep as ACTIVE
```

**Behavior:**
- **Approve**: Proceed to git commit
- **Review First**: Display full checklist, then re-prompt
- **Reject**: HALT execution, keep `Status: ACTIVE`, ask user what needs fixing

#### D. Transparent Status Change

After approval, display minimal confirmation:

```
✅ Milestone marked COMPLETE: [Title]
```

Then proceed to git commit.

### 5.5 Git Checkpoint Creation

**If validation passes:**

```bash
# Stage changes
git add .

# Get milestone info
TASK_NAME="[task-name]"
MILESTONE_TITLE="[milestone title]"
MILESTONE_ID="[milestone-id]"
COMPLEXITY="[complexity %]"

# Create structured commit
git commit -m "feat($TASK_NAME): Complete $MILESTONE_TITLE

Milestone: $MILESTONE_ID
Complexity: $COMPLEXITY%

Acceptance criteria verified:
- [criterion 1]: ✓ [method]
- [criterion 2]: ✓ [method]

Tasks completed:
- [sub-task 1]
- [sub-task 2]

Tests: [status]

[AA-MA Plan] $TASK_NAME .claude/dev/active/$TASK_NAME"

# Update provenance log
COMMIT_HASH=$(git rev-parse --short HEAD)
TIMESTAMP=$(date -Iseconds)
echo "[$TIMESTAMP] Commit $COMMIT_HASH — MilestoneID: $MILESTONE_ID — Status: COMPLETE" >> .claude/dev/active/$TASK_NAME/${TASK_NAME}-provenance.log

# Commit provenance update
git add .claude/dev/active/$TASK_NAME/${TASK_NAME}-provenance.log
git commit --amend --no-edit

# Push
git push
```

### 5.6 Update Milestone Status

1. Set milestone `Status: ACTIVE` → `Status: COMPLETE` in tasks.md
2. Update milestone `Result Log:` with summary
3. Update TodoWrite milestone todo to `completed`

### 5.7 Continue to Next Milestone

- Move to next PENDING milestone
- Repeat steps 5.1-5.6

---

## 6. Plan Completion

**When ALL milestones have Status: COMPLETE:**

### 6.1 Create Final Git Tag

```bash
TASK_NAME="[task-name]"
START_TIMESTAMP="[from first provenance log entry]"
END_TIMESTAMP=$(date -Iseconds)
TOTAL_MILESTONES="[count from tasks.md]"

git tag -a "${TASK_NAME}-complete" -m "Completed AA-MA plan: $TASK_NAME

Total milestones: $TOTAL_MILESTONES
Started: $START_TIMESTAMP
Completed: $END_TIMESTAMP

See ${TASK_NAME}-provenance.log for full execution history."
```

### 6.2 Push Tag

```bash
git push --tags
```

### 6.3 Final Provenance Entry

```bash
TIMESTAMP=$(date -Iseconds)
echo "[$TIMESTAMP] PLAN COMPLETE — Tag: ${TASK_NAME}-complete — All milestones COMPLETE" >> .claude/dev/active/$TASK_NAME/${TASK_NAME}-provenance.log

# If a /goal was bound at §2.5, capture the final verdict.
# Query /goal status (no args) and parse the evaluator's last reason.
# Format: GOAL_FINAL — verdict=<MET|UNMET|TURN_CAP_HIT|CLEARED> turns=<N> reason='<short>'
echo "[$TIMESTAMP] GOAL_FINAL — verdict=[MET|UNMET|TURN_CAP_HIT|CLEARED|NOT_BOUND] turns=[N] reason='[short]'" >> .claude/dev/active/$TASK_NAME/${TASK_NAME}-provenance.log

# Commit provenance log
git add .claude/dev/active/$TASK_NAME/${TASK_NAME}-provenance.log
git commit -m "docs($TASK_NAME): finalize provenance log"
git push
```

### 6.4 Mark Plan Complete

Update tasks.md:
- Add header comment at top: `# Status: COMPLETE`
- Add completion timestamp
- Preserve all milestone/task structure for reference

---

## 7. Report Completion

**Success message**:
```
🎉 AA-MA Plan Completed: [task-name]

Execution Summary:
- Total milestones: [count]
- Total sub-tasks: [count]
- Started: [start timestamp]
- Completed: [end timestamp]
- Duration: [calculated duration]

Git:
- Total commits: [count milestone commits]
- Tag created: [task-name]-complete
- All changes pushed to remote

Provenance:
- Full execution history: .claude/dev/active/[task-name]/[task-name]-provenance.log

Next Steps:
- Review implementation and verify all acceptance criteria met
- Run end-to-end tests if not already executed
- Archive completed plan: /archive-aa-ma [task-name]
- Update project documentation if needed
```

---

## 8. Error Handling

See [errors-and-operations.md](references/errors-and-operations.md#8-error-handling) — validation failures, broken dependency chains, context limits, token use, rollback and best practices for a full run.

**If a validation check fails at a milestone boundary, follow §8.1 in the reference first: set the milestone BLOCKED, add a remediation sub-task, alert the user and stop the run.**

---

**End of execute-aa-ma-full.md**
