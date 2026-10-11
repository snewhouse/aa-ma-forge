# AA-MA execution errors — common errors during execution and how to resolve each.

## Contents

- [XI. Error Handling](#xi-error-handling)
  - [Common Errors and Resolutions](#common-errors-and-resolutions)

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
1. Run /aa-ma-plan to regenerate artifacts
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
