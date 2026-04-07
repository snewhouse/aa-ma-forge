# Shutdown Protocol

Procedures for gracefully and safely shutting down agent teams.

---

## Graceful Shutdown (Default)

A 4-phase process that ensures all work is preserved and teammates exit cleanly.

### Phase 1: Drain

**Purpose:** Allow busy teammates to finish current work without starting new tasks.

**Steps:**
1. Check TaskList for in_progress tasks
2. For each teammate with in_progress work:
   ```
   SendMessage to {teammate}:
   "Team is shutting down. Please finish your current task,
   commit your work, and mark the task complete. Do not start
   new tasks."
   ```
3. Wait for teammates to finish (timeout: 5 minutes)
4. After timeout, check TaskList again:
   - All in_progress → completed? Proceed to Phase 2
   - Still in_progress? Send one more reminder (2 min timeout)
   - Still not done? Proceed anyway, log as partial completion

**Drain timeout:** 5 minutes initial + 2 minutes grace = 7 minutes max

### Phase 2: Verify

**Purpose:** Ensure work quality and completeness before shutdown.

**Steps:**
1. **TaskList check** — verify task completion status:
   - All tasks completed → proceed
   - Some tasks pending → log as deferred, note in report
   - Some tasks in_progress → handled in Phase 1

2. **Quality gates** (if applicable):
   - Run consistency check: `git status`, `git diff`, check for conflicts
   - Run test suite if implementation team: `{test_command}`
   - Verify no uncommitted changes

3. **AA-MA finalization** (if active):
   - Run AA-MA Finalization Protocol (see AA_MA_INTEGRATION.md)
   - Verify acceptance criteria
   - Update all 5 AA-MA files
   - Get user authorization

4. **Git status** — ensure all work is committed:
   - If uncommitted changes exist, commit them
   - Use appropriate commit message (with AA-MA signature if active)

### Phase 3: Shutdown Teammates

**Purpose:** Gracefully terminate all teammate processes.

**Steps:**
1. Determine shutdown order: **reverse of spawn order** (last spawned = first shutdown)
   - This ensures dependent teammates shut down before their dependencies
2. For each teammate (in reverse spawn order):
   ```
   SendMessage type: "shutdown_request" to {teammate}:
   "All tasks complete. Please shut down."
   ```
3. Wait for shutdown_response from each (timeout: 30 seconds per teammate)
4. Handle responses:
   - **Approved**: Teammate exits, proceed to next
   - **Rejected**: Teammate has reason to continue
     - Read the rejection reason
     - If valid (still has work): allow to finish, retry shutdown
     - If invalid: send another shutdown_request with "Please wrap up now"
     - After 2 rejections: proceed anyway (teammate will time out)

### Phase 4: Cleanup

**Purpose:** Remove team infrastructure and report results.

**Steps:**
1. **TeamDelete** — remove team and task directories
2. **Final git status** — verify clean working state
3. **Completion report** — present to user (see Report Format below)

---

## Emergency Shutdown

For situations requiring immediate termination: critical errors, token limit, user request to "stop everything."

### Trigger Conditions
- User explicitly says "stop", "abort", "cancel the team"
- Token/context limit approaching critical threshold
- Critical unrecoverable error
- Multiple teammates failing simultaneously

### Protocol
1. **Skip Drain** — do not wait for in_progress tasks
2. **Send shutdown_request to ALL teammates simultaneously** (not sequentially):
   ```
   For each teammate (in parallel):
     SendMessage type: "shutdown_request":
     "Emergency shutdown. Stop immediately."
   ```
3. **Do NOT wait for responses** — proceed after 15 seconds regardless
4. **TeamDelete** — force cleanup
5. **Git status** — check for uncommitted work
   - If uncommitted changes: commit with message "emergency: team shutdown — partial work"
   - If conflicts: flag to user for manual resolution
6. **Emergency report** — present to user with:
   - What was completed
   - What was in progress (may be incomplete)
   - What was not started
   - Any uncommitted or conflicted state

---

## Report Format

### Graceful Shutdown Report
```markdown
## Team Report: {team_name}

### Summary
- Type: {RESEARCH|IMPLEMENTATION|HYBRID|REVIEW}
- Duration: {start_time} → {end_time}
- Tasks: {completed}/{total} completed

### Completed Tasks
{for each completed task:}
- {task_name}: {brief_result_summary}

### Deferred Tasks
{for each incomplete task:}
- {task_name}: {reason_deferred}

### Key Results
{for RESEARCH: consolidated findings}
{for IMPLEMENTATION: files changed, tests passing}
{for REVIEW: consolidated findings summary}

### Files Modified
{list of files changed by team}

### Follow-Up Actions
{any remaining work or recommendations}
```

### Emergency Shutdown Report
```markdown
## Emergency Shutdown: {team_name}

### Reason: {why shutdown was triggered}

### State at Shutdown
- Completed: {list}
- In Progress (incomplete): {list}
- Not Started: {list}

### Git State
- Uncommitted changes: {yes/no — details}
- Conflicts: {yes/no — details}

### Recovery Options
- Resume: Create new team for remaining tasks
- Manual: Complete remaining work without team
- Discard: Revert team changes with `git revert`
```

---

## Shutdown Decision Tree

```
Time to shut down?
├── Normal completion (all tasks done)
│   └── Graceful Shutdown (full 4-phase)
├── Partial completion (some tasks remain)
│   └── Graceful Shutdown + partial completion report
├── User requests stop
│   ├── "Stop when convenient" → Graceful Shutdown
│   └── "Stop now" → Emergency Shutdown
├── Critical error
│   └── Emergency Shutdown
└── Token limit approaching
    └── Emergency Shutdown
```

---

## Post-Shutdown Verification

After any shutdown, verify:
1. `git status` — clean working tree (no uncommitted changes)
2. No orphaned team files in `~/.claude/teams/`
3. No orphaned task files in `~/.claude/tasks/`
4. AA-MA files updated (if active)
5. User has clear understanding of what was completed and what remains
