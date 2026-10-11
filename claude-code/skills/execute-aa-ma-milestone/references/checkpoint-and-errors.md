# Git checkpoint, completion report and errors — the milestone commit and provenance entries (§8), status update (§9), completion report (§10), BLOCKED handling (§11), token use and rollback.

## Contents

- [8. Git Checkpoint Creation (Auto-commit)](#8-git-checkpoint-creation-auto-commit)
  - [8.1 Stage Changes](#81-stage-changes)
  - [8.2 Create Structured Commit](#82-create-structured-commit)
  - [8.3 Update Provenance Log](#83-update-provenance-log)
  - [8.4 Commit Provenance Update](#84-commit-provenance-update)
  - [8.5 Push to Remote](#85-push-to-remote)
- [9. Update Milestone Status](#9-update-milestone-status)
- [10. Report Completion](#10-report-completion)
- [11. Error Handling at Checkpoint](#11-error-handling-at-checkpoint)
  - [11.1 Set Status to BLOCKED](#111-set-status-to-blocked)
  - [11.2 Create Remediation Sub-Task](#112-create-remediation-sub-task)
  - [11.3 Alert User](#113-alert-user)
  - [11.4 Update TodoWrite](#114-update-todowrite)
  - [11.5 HALT Execution](#115-halt-execution)
- [Token & Context Optimization](#token--context-optimization)
- [Rollback Support](#rollback-support)

## 8. Git Checkpoint Creation (Auto-commit)

**If validation passes, create git checkpoint automatically:**

### 8.1 Stage Changes
```bash
git add .
```

### 8.2 Create Structured Commit

```bash
# Extract milestone info from tasks.md
TASK_NAME="[task-name]"
MILESTONE_TITLE="[milestone title from ## header]"
MILESTONE_ID="[milestone-id, e.g., step-1-setup]"
COMPLEXITY="[complexity percentage]"

# Build acceptance criteria list
ACCEPTANCE_VERIFIED="$(cat <<'EOF'
- [criterion 1]: ✓ [verification method]
- [criterion 2]: ✓ [verification method]
EOF
)"

# Build completed tasks list
TASKS_COMPLETED="$(cat <<'EOF'
- [sub-task 1]
- [sub-task 2]
EOF
)"

# Build test status
TEST_STATUS="ALL PASS"  # or specific test summary

# Create commit
git commit -m "feat($TASK_NAME): Complete $MILESTONE_TITLE

Milestone: $MILESTONE_ID
Complexity: $COMPLEXITY%

Acceptance criteria verified:
$ACCEPTANCE_VERIFIED

Tasks completed:
$TASKS_COMPLETED

Tests: $TEST_STATUS

[AA-MA Plan] $TASK_NAME .claude/dev/active/$TASK_NAME"
```

### 8.3 Update Provenance Log

The milestone commit above is the hash the record must name, so it is
**final before this step runs** — never amended afterwards (L-018: `--amend`
rewrites the hash, and M1/M2 of `mattpocock-trio-adoption` each recorded a
pre-amend hash that no longer existed).

```bash
# Get commit info — HEAD is the milestone commit and stays that commit.
COMMIT_HASH=$(git rev-parse --short HEAD)
TIMESTAMP=$(date -Iseconds)
MILESTONE_ID="[milestone-id]"

# Append milestone completion to provenance log
echo "[$TIMESTAMP] MILESTONE COMPLETE — $MILESTONE_ID — Commit: $COMMIT_HASH — Criteria: [X/X] verified" >> .claude/dev/active/$TASK_NAME/${TASK_NAME}-provenance.log
```

**Session Checkpoint (on compaction or session end):** If context compaction is triggered during milestone execution, also write a CHECKPOINT entry for reliable session resume:

```bash
# Write checkpoint for session resume
ACTIVE_STEP="[current-step-id]"
NEXT_ACTION="[description of next action]"
TOKEN_USAGE="[estimated %]"
echo "[$TIMESTAMP] CHECKPOINT — ActiveStep: $ACTIVE_STEP — NextAction: \"$NEXT_ACTION\" — ContextLoaded: REFERENCE,TASKS — TokenUsage: $TOKEN_USAGE%" >> .claude/dev/active/$TASK_NAME/${TASK_NAME}-provenance.log
```

### 8.4 Commit Provenance Update

```bash
# A separate, small docs commit — NOT `--amend` (L-018). The milestone commit
# keeps the hash that provenance.log now names.
git add .claude/dev/active/$TASK_NAME/${TASK_NAME}-provenance.log
git commit -m "docs(aa-ma): provenance — MILESTONE COMPLETE $MILESTONE_ID ($COMMIT_HASH)

[AA-MA Plan] $TASK_NAME .claude/dev/active/$TASK_NAME"
```

### 8.5 Push to Remote

```bash
git push
```

---

## 9. Update Milestone Status

**After successful git checkpoint**:

1. Update tasks.md: Change milestone `Status: ACTIVE` → `Status: COMPLETE`
2. Fill in milestone-level `Result Log:` with summary
3. Update TodoWrite: Mark milestone todo as `completed`
4. Save all changes

---

## 10. Report Completion

**Success message**:
```
✅ Milestone completed: [milestone title]

Acceptance Criteria: All verified ✓
Tests: [status]
Commit: [commit-hash]
Provenance: Updated

Summary:
[Brief outcome summary]

Next steps:
- Run /execute-aa-ma-milestone again to continue with next milestone
- OR run /execute-aa-ma-full to execute all remaining milestones
- OR review changes and plan next phase manually
```

---

## 11. Error Handling at Checkpoint

**If validation fails at milestone boundary:**

### 11.1 Set Status to BLOCKED

Update tasks.md: Change milestone `Status: ACTIVE` → `Status: BLOCKED`

### 11.2 Create Remediation Sub-Task

Add new sub-task under milestone:
```markdown
### Sub-step N.M: Resolve [validation failure]
- Status: PENDING
- Dependencies: None
- Complexity: [estimate]%
- Acceptance Criteria: [specific fix required]
- Result Log: (to be filled)
```

### 11.3 Alert User

```
🚫 Milestone blocked: [milestone title]

Validation Failure:
- Check: [which validation check failed]
- Details: [specific criterion/test that didn't pass]

Remediation:
Created new sub-task: "Resolve [validation failure]"

Suggested steps:
[remediation guidance]

Resolution:
1. Fix the blocking issue
2. Re-run /execute-aa-ma-milestone to retry validation
```

### 11.4 Update TodoWrite

- Mark milestone todo as `pending` (not completed)
- Add new todo for remediation sub-task
- Prefix milestone content with "BLOCKED: "

### 11.5 HALT Execution

- Do NOT proceed to next milestone
- Do NOT create git commit
- Wait for user intervention

---

## Token & Context Optimization

- **Monitor token usage**: Check current session context usage
- **If approaching limits**: Consider context compaction:
  1. Summarize completed milestones
  2. Preserve essential state, open issues, acceptance criteria
  3. Discard redundant tool outputs
  4. Update context-log.md with summary
  5. Reset session with compacted context

---

## Rollback Support

**Each milestone commit is a rollback point:**

- **View milestone history**: `git log --oneline --grep="feat([task-name])"`
- **Rollback specific milestone**: `git revert [milestone-commit-hash]`
- **Rollback to milestone**: `git reset --hard [milestone-commit-hash]` (destructive, use with caution)
- **Audit trail**: Provenance log provides complete execution history

**Provenance log format**:
```
[2025-11-17T10:30:00+00:00] Commit a1b2c3d — MilestoneID: step-1-setup — Status: COMPLETE
[2025-11-17T11:45:00+00:00] Commit e4f5g6h — MilestoneID: step-2-implement — Status: COMPLETE
```
