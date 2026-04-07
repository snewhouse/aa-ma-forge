# Error Recovery

Procedures for handling errors during agent-teams execution.

---

## File Conflicts

### Prevention (Primary Strategy)

File conflicts are prevented by design:

1. **Architect assigns non-overlapping scopes** before implementation begins
2. **Each implementer receives explicit file list** in their spawn prompt
3. **Spawn prompt includes warning**: "Only modify files within your assigned scope"
4. **If overlap unavoidable**: implementers work on shared files sequentially (use addBlockedBy)

### Detection

Signs of file conflict:
- Git merge conflict when lead runs `git status`
- Two implementers report modifying the same file
- Test failures after multiple implementers commit

### Resolution

1. **Identify conflicting files** — `git diff` to see conflicts
2. **Determine which change takes precedence** — based on task priority and correctness
3. **Ask implementers for context** — SendMessage to both about the conflict
4. **Lead resolves** — manually merge or pick the correct version
5. **Rerun tests** — verify resolution doesn't break anything
6. **Prevent recurrence** — reassign scopes if needed

---

## Stuck Teammates

### Detection Criteria

A teammate is considered stuck when ANY of these are true:
1. **Idle timeout**: Teammate has been idle for >5 minutes with in_progress tasks
2. **No progress**: Teammate has not updated TaskUpdate or sent a message after 2 check-ins
3. **Repeated errors**: Teammate reports the same error 3+ times without resolution

### Recovery Protocol

**Step 1: Check In**
```
SendMessage to stuck teammate:
"Status check — are you blocked on anything? What's your current progress?"
```
Wait for response (2 minute timeout).

**Step 2: Assist**
If teammate responds with a blocker:
- Provide the needed information or context
- Unblock by answering their question
- If blocker is outside their scope, resolve it yourself or reassign

**Step 3: Reassign**
If teammate remains unresponsive or cannot resolve:
- SendMessage shutdown_request to the stuck teammate
- Create a new task with the unfinished work description
- Spawn a replacement teammate (same role, fresh context)
- Assign the new task to the replacement

**Step 4: Escalate**
If replacement also gets stuck:
- Notify user via direct message (not teammate)
- Present the blocker and ask for guidance
- Offer options: manual intervention, skip task, or rethink approach

---

## Failed Tasks

### Severity Assessment

| Failure Type | Severity | Action |
|-------------|----------|--------|
| Test failure (specific) | Low | Retry with error context |
| Build/compile error | Medium | Retry with fix guidance |
| Scope violation | Medium | Reassign with corrected scope |
| Complete inability | High | Different teammate or escalate |
| Repeated same failure | High | Escalate to user |

### 3-Strike Retry Escalation

**Strike 1: Same Teammate**
- Send the error details back to the teammate
- Ask them to diagnose and retry
- Include relevant error logs in the message

**Strike 2: Different Teammate**
- Shut down the failing teammate
- Spawn a fresh teammate (same role, new context)
- Include the failure context: "Previous attempt failed because {reason}"
- New teammate may approach differently

**Strike 3: Escalate to User**
- Present the failure to the user:
  ```
  Task "{task_name}" has failed after 2 attempts.

  Attempt 1: {teammate_1} — failed because {reason}
  Attempt 2: {teammate_2} — failed because {reason}

  Options:
  - Manual intervention (you fix it)
  - Skip this task and continue
  - Rethink the approach
  - Abort the team
  ```
- Wait for user decision before proceeding

---

## Partial Completions

When a team must stop before all tasks are complete (token limit, user request, critical failure):

### State Preservation

1. **Record completed work**:
   - List all completed tasks and their results
   - List all in-progress tasks and their current state
   - List all pending tasks not yet started

2. **Save context** (if AA-MA active):
   - Update tasks.md with current state
   - Log partial completion to context-log.md
   - Log to provenance.log

3. **Git commit** partial work:
   - Commit all completed changes
   - Message: "partial: {description} (team stopped — {reason})"

### User Options

Present to user via AskUserQuestion:

```
Team "{team_name}" stopping with partial completion.

Completed: {X}/{total} tasks
In-progress: {Y} tasks (work will be lost)
Pending: {Z} tasks (not started)

Options:
- Resume later: State preserved in task list / AA-MA files
- Manual completion: I'll continue the remaining tasks without a team
- Archive: Accept partial results, defer remaining work
- Discard: Revert all team changes
```

### Resume Protocol

To resume a partially completed team:
1. Check TaskList or AA-MA tasks.md for incomplete tasks
2. Create a new team (previous team was deleted)
3. Create tasks only for remaining work
4. Include context from previous attempt in spawn prompts:
   "Previous team completed {X} tasks. Remaining work: {list}"

---

## Emergency Situations

### Token/Context Limit Approaching
- Immediately initiate shutdown (Phase 6)
- Prioritize completing in-progress tasks
- Do NOT spawn new teammates
- Present partial completion report

### Teammate Modifies Wrong Files
- SendMessage to teammate: "STOP — you modified files outside your scope"
- Review the changes (`git diff`)
- If safe: accept and adjust scopes
- If problematic: `git checkout -- {files}` to revert
- Reassign or retrain the teammate

### All Teammates Fail
- Shut down all teammates
- Present failure report to user
- Suggest: "This task may be too complex for agent teams. Consider breaking it into smaller pieces or executing manually."

---

## Error Logging

All errors should be logged for debugging:

```
# To user (concise):
"Teammate {name} encountered an error on task {id}: {brief_description}"

# To provenance.log (if AA-MA active):
[{timestamp}] ERROR — Teammate: {name}, Task: {id}, Type: {error_type}, Detail: {description}

# To context-log.md (if AA-MA active, for significant errors):
## [{date}] Team Error: {brief}
- Teammate: {name}
- Task: {task_description}
- Error: {full_description}
- Resolution: {what_was_done}
```
