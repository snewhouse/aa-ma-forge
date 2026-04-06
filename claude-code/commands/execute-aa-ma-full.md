---
name: execute-aa-ma-full
description: Execute complete AA-MA plan from current position to completion with automated checkpoints
---

# AA-MA Full Plan Execution

You are executing the **complete AA-MA plan** from current position to final completion.

**Scope**: All remaining milestones in tasks.md
**Validation**: Strict at every milestone boundary
**Git**: Auto-commit + provenance at each milestone, final tag on completion

⚠️ **Use this command only for well-understood plans that don't need frequent human checkpoints.**

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

### Tier 2: Content Validation (Thorough)

After Tier 1 passes, spawn the `aa-ma-validator` agent for deep content checks:

```
Spawn aa-ma-validator with:
  subagent_type: "aa-ma-validator"
  prompt: Validate artifacts at [task-dir] in pre-execution context
  Tools: Read, Glob, Grep (NO Write, NO Bash)
```

**Validator checks 5 dimensions:**
1. **Existence** — all 5 files present and non-empty
2. **Plan completeness** — plan.md has the 11 AA-MA required elements
3. **Reference completeness** — reference.md has facts extracted from plan
4. **HTP structure** — tasks.md has proper milestone/step hierarchy with Status fields
5. **Cross-file consistency** — no contradictions between files

**Validator verdict handling:**
- **PASS**: All checks passed → continue to step 2
- **WARN**: Minor issues (non-blocking) → log warnings, continue to step 2
- **FAIL**: Critical issues → attempt remediation:
  1. Spawn `aa-ma-scribe` to fix identified issues
  2. Re-run validator
  3. If still FAIL → HALT and alert user

**If Tier 2 agent spawning unavailable:** Skip Tier 2 (Tier 1 existence check is sufficient to proceed). Log: "Tier 2 validation skipped — agent spawning unavailable."

**Why full plan execution requires both tiers:** Full execution will run through all remaining milestones unattended. Catching content issues upfront (missing acceptance criteria, inconsistent references, malformed HTP) prevents failures deep into the execution that are costly to recover from.

---

## 2. Full Context Injection

**REQUIRED - Auto-inject ALL 5 AA-MA files with XML delimiters:**

```xml
<REFERENCE>
{Read contents of [task-name]-reference.md}
# Immutable facts and constants. Treat as non-negotiable.
</REFERENCE>

<TASKS>
{Read contents of [task-name]-tasks.md}
# HTP roadmap. Current execution scope: FULL PLAN
# Status values: PENDING | ACTIVE | COMPLETE | BLOCKED
</TASKS>

<CONTEXT_LOG>
{Read contents of [task-name]-context-log.md}
# Summarized architectural decisions and unresolved bugs
</CONTEXT_LOG>

<PLAN>
{Read contents of [task-name]-plan.md}
# Original strategy, rationale, and high-level constraints
</PLAN>

<PROVENANCE>
{Read contents of [task-name]-provenance.log}
# Execution telemetry and git history
</PROVENANCE>
```

**Why load all 5**: Full plan execution requires complete context to make informed decisions across multiple milestones.

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
- **TDD:** If this milestone produces code, invoke `superpowers:test-driven-development`. Let the skill decide test strategy. Skip for docs-only, config-only, or infrastructure-only milestones.
- **12-Factor:** If the task involves service deployment, API servers, or containerized applications, reference 12-Factor principles for config (env vars not files), statelessness, and port binding. For ALL tasks with `.env` files, verify env-var-drift compliance (see `rules/env-var-drift.md`).
- **Context7 MCP:** Use for library docs and code generation. Retry once on failure, then fall back to WebSearch + official docs.
- **WebSearch:** Fallback when Context7 fails. Also use proactively for unfamiliar APIs, recent library changes, or deployment patterns.

### Pre-Execution Check (First Milestone Only)

If this is the **first milestone** and it touches 3+ files or unfamiliar code, invoke `Skill(system-mapping)` for the 5-point pre-flight check. Skip for subsequent milestones.

---

## 5. Execute Plan Sequentially

**For each PENDING milestone (in order)**:

### 5.1 Pre-Flight Checks

1. **Verify dependencies met**:
   - Check `Dependencies:` field
   - All dependency milestones must have `Status: COMPLETE`
   - If unmet → HALT and alert user

2. **Update status**:
   - Set milestone `Status: PENDING` → `Status: ACTIVE`
   - Update TodoWrite milestone todo to `in_progress`

### 5.2 Execute All Sub-Tasks

**For each sub-task in milestone**:
1. Mark TodoWrite sub-task as `in_progress`
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
- Check next milestone's `Dependencies:` field
- Verify all dependencies have `Status: COMPLETE`

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

### 8.1 Validation Failure at Milestone Boundary

**If ANY validation check fails:**

1. **Set Status to BLOCKED**:
   - Update milestone `Status: ACTIVE` → `Status: BLOCKED` in tasks.md

2. **Create Remediation Sub-Task**:
   ```markdown
   ### Sub-step: Resolve [validation failure]
   - Status: PENDING
   - Dependencies: None
   - Complexity: [estimate]%
   - Acceptance Criteria: [specific fix required]
   - Result Log: (to be filled)
   ```

3. **Alert User and HALT**:
   ```
   🚫 Plan execution halted at milestone: [milestone title]

   Validation Failure:
   - Check: [which check failed]
   - Details: [specific issue]

   Remediation:
   Created sub-task: "Resolve [validation failure]"

   Resolution:
   1. Fix the blocking issue
   2. Re-run /execute-aa-ma-full to resume execution

   Note: Execution will resume from this milestone, not restart from beginning.
   ```

4. **Update TodoWrite**:
   - Mark milestone as `pending` (not completed)
   - Prefix content with "BLOCKED: "
   - Add remediation sub-task todo

5. **Do NOT proceed**: Wait for user intervention

### 8.2 Dependency Chain Broken

**If next milestone has unmet dependencies:**

```
🚫 Cannot proceed: Dependency chain broken

Milestone: [current milestone]
Next Milestone: [next milestone title]
Unmet Dependencies: [list dependency IDs with Status fields]

Resolution:
- Review tasks.md dependency graph
- Ensure dependencies are correctly specified
- Complete missing dependency milestones first
- OR adjust dependency specifications if incorrect

Execution halted. Fix dependencies, then re-run /execute-aa-ma-full.
```

### 8.3 Context Limit Approaching

**If token usage approaching limits during execution:**

1. **Trigger context compaction**:
   - Summarize completed milestones
   - Update context-log.md with summary
   - Preserve REFERENCE, current position in TASKS
   - Discard redundant tool outputs

2. **Save state**:
   - Commit current progress
   - Update provenance log with compaction note

3. **Alert user**:
   ```
   ⚠️ Context limit approaching - Compaction recommended

   Current usage: [X]% of limit
   Milestones completed: [count]
   Milestones remaining: [count]

   Recommended action:
   1. Current progress saved (commit: [hash])
   2. Perform context compaction (summarize completed work)
   3. Re-run /execute-aa-ma-full to continue with fresh context

   OR

   Continue with /execute-aa-ma-milestone to execute remaining milestones one at a time.
   ```

---

## 9. Token & Context Optimization

**During execution**:
- Monitor token usage after each milestone
- If usage > 70%: Consider proactive compaction
- If usage > 85%: Trigger mandatory compaction

**Compaction procedure**:
1. Summarize completed milestones (key decisions, outcomes)
2. Update context-log.md with summary
3. Commit: `git commit -m "docs([task-name]): update context log with milestone summaries"`
4. Alert user to reset session and reload context

---

## 10. Rollback Support

**Each milestone commit is a rollback point:**

### View Full History
```bash
git log --oneline --grep="feat([task-name])"
```

### Rollback to Specific Milestone
```bash
# Non-destructive (creates revert commit)
git revert [milestone-commit-hash]

# Destructive (use with caution)
git reset --hard [milestone-commit-hash]
```

### Audit Trail
Provenance log provides complete execution history:
```bash
cat .claude/dev/active/[task-name]/[task-name]-provenance.log
```

---

## 11. Best Practices

**When to use execute-aa-ma-full**:
- ✅ Plan is well-understood with clear milestones
- ✅ Acceptance criteria are specific and testable
- ✅ Dependencies are correctly specified
- ✅ You don't need frequent human review checkpoints
- ✅ Plan has been validated (e.g., after successful first milestone execution)

**When NOT to use**:
- ❌ First time executing a new plan (use execute-aa-ma-milestone first)
- ❌ Plan has ambiguous acceptance criteria
- ❌ High uncertainty or exploratory work
- ❌ Frequent design decisions needed
- ❌ Learning/experimentation phase

**Recommendation**:
Start with `/execute-aa-ma-milestone` for first 1-2 milestones to validate the plan, then switch to `/execute-aa-ma-full` once confident in plan quality.

---

**End of execute-aa-ma-full.md**
