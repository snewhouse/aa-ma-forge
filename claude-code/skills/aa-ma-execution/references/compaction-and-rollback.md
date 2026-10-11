# Context compaction, validation and rollback — how to compact context mid-task, validate acceptance criteria and roll back a step.

## Contents

- [VIII. Context Compaction](#viii-context-compaction)
  - [Compaction Procedure](#compaction-procedure)
- [IX. Validation & Rollback](#ix-validation--rollback)
  - [Acceptance Criteria Validation](#acceptance-criteria-validation)
  - [Rollback Procedure](#rollback-procedure)

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
