# Quality Gates

Quality enforcement points during agent-teams execution. Gates prevent low-quality work from progressing through the team workflow.

---

## Gate Types

| # | Gate | When Triggered | Enforced By | Required For |
|---|------|---------------|-------------|--------------|
| 1 | Design Review | Before implementation begins | Architect teammate | IMPLEMENTATION teams |
| 2 | Code Review | After each implementation task | Reviewer teammate | All code changes |
| 3 | Test Verification | After implementation + review | Tester or Lead | Before marking task complete |
| 4 | Consistency Check | After all team tasks complete | Lead (your session) | Always |
| 5 | AA-MA Validation | At milestone boundary | Lead (your session) | When AA-MA is active |

---

## Gate 1: Design Review

**When:** Before any implementer starts coding
**Enforced by:** Architect teammate
**Purpose:** Ensure scope partitioning is correct, patterns are appropriate, dependencies are identified

### What the Architect Reviews
- File scope assignments (non-overlapping)
- Proposed patterns and approaches
- Task dependencies (correct ordering)
- Potential conflicts or risks

### Enforcement via Tasks
```
Task: "Design review for {feature}" → assign to Architect
  No dependencies (runs first)

Task: "Implement module A" → assign to Implementer 1
  addBlockedBy: [Design review task]

Task: "Implement module B" → assign to Implementer 2
  addBlockedBy: [Design review task]
```

Implementation tasks are **blocked** until the design review task is completed.

### Pass Criteria
- Architect approves the design
- Scopes are non-overlapping
- Dependencies are clearly defined
- No unresolved risks

### Failure Handling
- If Architect identifies issues: lead adjusts scope/approach before unblocking implementers
- If Architect cannot design: escalate to user for architectural decision

---

## Gate 2: Code Review

**When:** After each implementer completes their task
**Enforced by:** Reviewer teammate
**Purpose:** Catch bugs, security issues, pattern violations, and quality problems early

### What the Reviewer Checks
- Code correctness and logic
- Security vulnerabilities
- Adherence to project patterns
- Error handling
- Test coverage
- Documentation (if required)

### Enforcement via Tasks
```
Task: "Implement module A" → assign to Implementer 1
Task: "Review module A" → assign to Reviewer
  addBlockedBy: [Implement module A]

Task: "Implement module B" → assign to Implementer 2
Task: "Review module B" → assign to Reviewer
  addBlockedBy: [Implement module B]
```

### Review Outcomes

| Outcome | Action |
|---------|--------|
| APPROVE | Proceed to next task |
| REQUEST_CHANGES (Critical) | Implementer must fix before proceeding |
| REQUEST_CHANGES (Important) | Fix before next major gate |
| REQUEST_CHANGES (Minor) | Note for later, proceed |

### Failure Handling
- Critical issues: send review findings to implementer, they fix and re-submit
- If implementer cannot fix: lead assists or reassigns
- If reviewer and implementer disagree: lead mediates

---

## Gate 3: Test Verification

**When:** After implementation and code review pass
**Enforced by:** Tester teammate (if present) or Lead
**Purpose:** Verify functionality works correctly and acceptance criteria are met

### What Gets Verified
- All existing tests still pass
- New tests cover the implemented functionality
- Acceptance criteria from task description are met
- Edge cases are handled

### Verification Steps
1. Run test suite: `{test_command}`
2. Check test output: all pass?
3. Review acceptance criteria: each met?
4. If AA-MA active: check criteria from tasks.md

### Pass Criteria
- All tests pass (zero failures)
- Each acceptance criterion verified with evidence
- No regressions in existing functionality

### Failure Handling
- Test failures: send details to implementer for fix
- Missing tests: tester writes them or implementer adds them
- Acceptance criteria not met: determine if implementation or criteria needs adjustment

---

## Gate 4: Consistency Check

**When:** After ALL team tasks are complete (before shutdown)
**Enforced by:** Lead (your session)
**Purpose:** Ensure all changes work together and the codebase is in a clean state

### 4-Step Protocol

**Step 1: Git Status**
```bash
git status
```
- No uncommitted changes (all work committed)
- No untracked files that should be tracked
- Clean working tree

**Step 2: Git Diff**
```bash
git diff main...HEAD  # or appropriate base branch
```
- Review all changes holistically
- Verify changes are coherent (not contradictory between implementers)
- Check for accidental reverts or overwrites

**Step 3: Conflict Check**
```bash
git diff --name-only --diff-filter=U
```
- No merge conflicts
- No partially merged files

**Step 4: Test Suite**
```bash
{full_test_command}
```
- All tests pass
- No regressions from team's changes

### Pass Criteria
- All 4 steps pass
- Codebase is in a deployable state

### Failure Handling
- Uncommitted changes: commit them
- Conflicts: resolve manually
- Test failures: identify which teammate's changes caused the failure, dispatch fix
- Incoherent changes: lead reconciles or asks user

---

## Gate 5: AA-MA Validation

**When:** At milestone boundary (only when AA-MA is active)
**Enforced by:** Lead (your session)
**Purpose:** Ensure AA-MA milestone acceptance criteria are met and all files are synchronized

### Validation Steps

1. **Read acceptance criteria** from `[task]-tasks.md` active milestone
2. **Verify each criterion** with evidence:
   ```
   Acceptance Criteria Verification:
   - ✓ [Criterion 1]: Confirmed — [evidence]
   - ✓ [Criterion 2]: Confirmed — [evidence]
   All [X] criteria verified.
   ```
3. **Verify AA-MA file sync**:
   - tasks.md: All sub-steps marked COMPLETE with Result Logs
   - reference.md: New facts added
   - context-log.md: Decisions documented
   - provenance.log: All commits logged
4. **Run AA-MA Finalization Protocol** (see AA_MA_INTEGRATION.md)

### Pass Criteria
- All acceptance criteria verified
- All 5 AA-MA files synchronized
- User authorization received
- Git commit with AA-MA signature

### Failure Handling
- Criteria not met: identify gap, create remediation task
- Files not synced: lead updates them immediately
- User rejects: address feedback, re-verify

---

## Gate Summary by Team Type

| Gate | RESEARCH | IMPLEMENTATION | HYBRID | REVIEW |
|------|----------|---------------|--------|--------|
| Design Review | - | Required | Phase 2 only | - |
| Code Review | - | Required | Phase 2 only | N/A (they ARE reviewers) |
| Test Verification | - | Required | Phase 2 only | - |
| Consistency Check | Always | Always | Always | Always |
| AA-MA Validation | If active | If active | If active | If active |

---

## Enforcement Principles

1. **Gates are non-negotiable** — do not skip gates to save time
2. **Blocked tasks stay blocked** — task dependencies enforce gate ordering
3. **Critical issues block progress** — no proceeding with unresolved Critical findings
4. **Lead is final arbiter** — when teammates disagree, lead decides
5. **User is ultimate authority** — escalate to user when lead cannot resolve
