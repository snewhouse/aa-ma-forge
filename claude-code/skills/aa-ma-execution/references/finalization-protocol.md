# AA-MA finalization protocol — the integrity check, doc update, HARD gate and approval steps before a milestone is COMPLETE.

## Contents

- [VI. Finalization Protocol — MANDATORY](#vi-finalization-protocol--mandatory)
  - [Step 1: Integrity Check (Checklist Verification + Sub-Step Audit)](#step-1-integrity-check-checklist-verification--sub-step-audit)
  - [Step 2: Documentation Auto-Update](#step-2-documentation-auto-update)
  - [Step 2.5: Post-Milestone Simplification Review](#step-25-post-milestone-simplification-review)
  - [Step 2.6: HARD Gate Check](#step-26-hard-gate-check)
  - [Step 2.7: Executable Test Stubs](#step-27-executable-test-stubs)
  - [Step 3: User Authorization (Approval Gate)](#step-3-user-authorization-approval-gate)
  - [Step 4: Transparent Status Change](#step-4-transparent-status-change)
  - [Finalization Protocol Applies To](#finalization-protocol-applies-to)

## VI. Finalization Protocol — MANDATORY

Before marking ANY milestone COMPLETE, you **MUST** execute this 4-step protocol. No exceptions.

### Step 1: Integrity Check (Checklist Verification + Sub-Step Audit)

**Part A — Sub-Step Status Audit (L-081, L-083 — MECHANICAL CHECK):**

Before checking acceptance criteria, run this mechanical audit:
```
Sub-Step Status Audit for Milestone [N]:
  Total sub-steps: [X]
  COMPLETE: [Y]
  SKIPPED:  [Z] (with reasons)
  PENDING:  [W]

  If W > 0:
    🚫 FINALIZATION BLOCKED — [W] sub-steps still PENDING
    [List each PENDING sub-step]
    ACTION: Populate Result Logs before finalizing.
    HALT — do not proceed to Part B.

  If W = 0:
    ✅ All sub-steps accounted for (Y complete + Z skipped)
    Proceed to Part B.
```

**Part B — Acceptance Criteria Verification:**

Display acceptance criteria verification to the user:

```
Acceptance Criteria Verification:
- ✓ [Criterion 1]: Confirmed - [brief evidence]
- ✓ [Criterion 2]: Confirmed - [brief evidence]
- ✓ [Criterion 3]: Confirmed - [brief evidence]

All [X] criteria verified. Ready for finalization.
```

**Rules:**
- Every acceptance criterion must be explicitly listed
- Each must have `✓` confirmation with brief evidence
- If ANY criterion cannot be confirmed → HALT, do not proceed

### Step 2: Documentation Auto-Update

Automatically update all 5 AA-MA files:

| File | Auto-Update Action |
|------|-------------------|
| `tasks.md` | Mark milestone `Status: COMPLETE`, fill `Result Log:` |
| `reference.md` | Add any new immutable facts discovered |
| `context-log.md` | Append completion summary (see template below) |
| `provenance.log` | Append completion entry with timestamp + commit hash |
| `plan.md` | No change (historical record) |

**Template for context-log.md:**
```markdown
## [YYYY-MM-DD] Milestone Completion: [Title]
- Status: COMPLETE
- Key outcome: [1-2 sentence summary]
- Artifacts: [list of files created/modified]
- Tests: [pass/fail summary]
```

**Template for provenance.log:**
```
[TIMESTAMP] MILESTONE COMPLETE — [Milestone ID] — Commit: [hash] — Criteria: [X/X] verified
```

### Step 2.5: Post-Milestone Simplification Review

**Skip if:** Only docs/config changed (no `.py`/`.ts`/`.js`/`.go`/`.rs`), diff < 20 lines code, or `--skip-simplify` flag.

**Execution:** Launch 3 parallel review agents against the milestone diff (`git diff [last-checkpoint]..HEAD`):

| Agent | Focus | Catches |
|-------|-------|---------|
| **Code Reuse** | Search codebase for existing utilities | Agents reinventing what already exists |
| **Code Quality** | Redundant state, copy-paste, leaky abstractions | Inconsistent patterns across parallel tasks |
| **Efficiency** | N+1, missed concurrency, hot-path bloat | Performance issues surviving past task-level review |

**Findings** reported with severity (CRITICAL / WARNING / INFO). CRITICAL findings require explicit acknowledgment at the approval gate (Step 3). User can fix, acknowledge, or review details.

**Log to provenance:** `[TIMESTAMP] Post-milestone review: N findings (C/W/I) [fixed|acknowledged|skipped]`

**On failure:** Skip review, log `Post-milestone review: SKIPPED — agent failure`. Do NOT block finalization.

### Step 2.6: HARD Gate Check

If the milestone has `Gate: HARD` in tasks.md, verify a signed approval artifact exists in context-log.md before proceeding:

```
Required artifact format:
## [date] GATE APPROVAL: [Milestone Title]
- Gate: HARD
- Approved by: [user]
- Criteria verified: [X/X]
- Decision: APPROVED
```

**If HARD gate and no approval artifact:** HALT. Use AskUserQuestion to request approval. If approved, write the artifact to context-log.md, then continue. If `Gate: SOFT` (default), proceed normally.

### Step 2.7: Executable Test Stubs

If `[task]-tests.yaml` exists in the task directory, auto-detect and run tests for the current milestone. Each test has `name`, `command`, and `expected`/`expected_pattern`. All tests must pass. Falls back to existing test behavior if file is absent.

### Step 3: User Authorization (Approval Gate)

Use AskUserQuestion to get explicit user approval:

```
Finalization Review

Milestone: [Title]
Acceptance Criteria: [X/X] verified
Gate: [HARD|SOFT] — [Approval artifact found / Convention-based]

Ready to mark this milestone COMPLETE?
```

**Options:**
- **Approve** → "Proceed with status change and commit"
- **Review First** → "Show me the detailed verification before approving"
- **Reject** → "Do not mark complete, keep as ACTIVE"

**Behavior by choice:**
- **Approve**: Proceed to Step 4
- **Review First**: Display full integrity checklist from Step 1, then re-prompt
- **Reject**: HALT, keep `Status: ACTIVE`, ask user what needs fixing

### Step 4: Transparent Status Change

After approval, execute status change with minimal confirmation:

```
✅ Milestone marked COMPLETE: [Title]
```

If this was the FINAL milestone (all milestones now COMPLETE), add:

```
💡 All milestones complete! Run: /archive-aa-ma [task-name]
```

### Finalization Protocol Applies To

- `/execute-aa-ma-milestone` — at milestone boundary
- `/execute-aa-ma-full` — at each milestone boundary in the loop

**Note:** `/execute-aa-ma-step` does NOT trigger finalization (steps accumulate until milestone).
