# Errors, token use, rollback and best practices — validation failures, broken dependency chains, context limits, token use, rollback and best practices for a full run.

## Contents

- [8. Error Handling](#8-error-handling)
  - [8.1 Validation Failure at Milestone Boundary](#81-validation-failure-at-milestone-boundary)
  - [8.2 Dependency Chain Broken](#82-dependency-chain-broken)
  - [8.3 Context Limit Approaching](#83-context-limit-approaching)
- [9. Token & Context Optimization](#9-token--context-optimization)
- [10. Rollback Support](#10-rollback-support)
  - [View Full History](#view-full-history)
  - [Rollback to Specific Milestone](#rollback-to-specific-milestone)
  - [Audit Trail](#audit-trail)
- [11. Best Practices](#11-best-practices)

## 8. Error Handling

### 8.1 Validation Failure at Milestone Boundary

**If ANY validation check fails:**

1. **Set Status to BLOCKED**:
   - Update milestone `Status: ACTIVE` → `Status: BLOCKED` in tasks.md

2. **Create Remediation Sub-Task**:
   ```markdown
   ### Sub-step N.M: Resolve [validation failure]
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
