---
name: archive-aa-ma
description: Archive a completed AA-MA plan to .claude/dev/completed/
---

# Archive AA-MA Plan

Archive a completed AA-MA plan from `.claude/dev/active/` to `.claude/dev/completed/`.

## Usage

```
/archive-aa-ma {task-name}
```

**Example**: `/archive-aa-ma user-authentication`

---

## Workflow

### Step 1: Validate Task Exists

```bash
ls .claude/dev/active/{task-name}/
```

**If not found**:
```
ERROR: Task '{task-name}' not found in .claude/dev/active/
```

### Step 2: Verify Completion

Read `{task-name}-tasks.md` and verify ALL milestones have `Status: COMPLETE`.

**Parse tasks.md for milestone status**:
- Find all `## ` headers (milestones)
- Check each milestone's `Status:` field
- ALL must be `COMPLETE`

**If any milestone is not COMPLETE**:
```
ERROR: Cannot archive incomplete plan

Milestones still pending:
- [Milestone 1]: Status: ACTIVE
- [Milestone 3]: Status: PENDING

Complete all milestones first, then retry /archive-aa-ma {task-name}
```

### Step 3: Add Completion Headers

For each file in the task directory, prepend a completion header:

```markdown
<!-- ARCHIVED: [YYYY-MM-DD HH:MM] -->
<!-- Plan: {task-name} - COMPLETE -->
<!-- Total Milestones: X | Duration: [first provenance entry] to [last] -->

```

**Files to update**:
- `{task-name}-plan.md`
- `{task-name}-reference.md`
- `{task-name}-context-log.md`
- `{task-name}-tasks.md`
- `{task-name}-provenance.log`

### Step 4: Move to Completed

```bash
mkdir -p .claude/dev/completed/
mv .claude/dev/active/{task-name}/ .claude/dev/completed/{task-name}/
```

### Step 5: Confirmation

Display minimal confirmation:

```
✅ Archived: {task-name}
📁 Location: .claude/dev/completed/{task-name}/
📊 Milestones: X complete
⏱️  Duration: [calculated from provenance log]

Archive will be committed to git in Step 7.
```

### Step 6: Optional Retrospective

After archive is confirmed and committed, offer an engineering retrospective scoped to the plan's duration.

**Detection:** Extract date range from the provenance log:
```bash
# First entry date
PLAN_START=$(head -5 .claude/dev/completed/{task-name}/*-provenance.log | grep -oP '\d{4}-\d{2}-\d{2}' | head -1)
# Last entry date
PLAN_END=$(tail -5 .claude/dev/completed/{task-name}/*-provenance.log | grep -oP '\d{4}-\d{2}-\d{2}' | tail -1)
```

**Prompt user:**
```
📊 Run engineering retrospective for this plan?
   Period: {PLAN_START} to {PLAN_END}
   [Y] Run /retro scoped to plan dates
   [N] Skip
```

**If accepted:**
1. Invoke `Skill(retro)` with `--since {PLAN_START}` flag
2. Store retro output alongside archived plan at `.claude/dev/completed/{task-name}/retro-{date}.md`
3. This step is entirely optional and post-workflow — archive is already complete

**If declined or retro fails:** Continue without error. Archive is already confirmed.

### Step 7: Commit Archive to Git

Archive and any retrospective output must be committed per git-conventions.md ("MUST add, commit, AND push all changes").

```bash
# Stage archived files
git add .claude/dev/completed/{task-name}/

# Stage removal of active directory
git add .claude/dev/active/{task-name}/

# Commit
git commit -m "$(cat <<'EOF'
chore: archive AA-MA plan {task-name}

Archived completed plan from .claude/dev/active/ to .claude/dev/completed/
[includes retrospective if generated]
EOF
)"

# Push
git push
```

**Success Message:**
```
✅ Archive committed and pushed
📦 Commit: [first 8 chars of SHA]
```

---

## Error Handling

| Error | Message |
|-------|---------|
| Task not found | `ERROR: Task '{task-name}' not found in .claude/dev/active/` |
| Incomplete plan | `ERROR: Cannot archive incomplete plan. Pending: [milestone list]` |
| Move failed | `ERROR: Failed to move directory. Check permissions.` |
| No task name provided | `ERROR: Please provide task name: /archive-aa-ma {task-name}` |

---

## Implementation Details

### Parsing Milestone Status

```bash
# Extract all milestone headers and their status
grep -A 2 "^## " .claude/dev/active/{task-name}/{task-name}-tasks.md | grep "Status:"
```

### Calculating Duration

Parse `{task-name}-provenance.log`:
- First entry timestamp = start
- Last entry timestamp = end
- Duration = end - start

### Header Template

```markdown
<!-- ARCHIVED: 2025-12-01 14:30 -->
<!-- Plan: user-authentication - COMPLETE -->
<!-- Total Milestones: 5 | Duration: 2025-11-28 to 2025-12-01 -->

```

---

## Notes

- **Local only**: Archives are NOT committed to git by default
- **Preserved for reference**: Archived plans remain readable in `.claude/dev/completed/`
- **Restore**: To restore, manually move back to `active/`:
  ```bash
  mv .claude/dev/completed/{task-name}/ .claude/dev/active/{task-name}/
  ```

---

## When to Archive

Use `/archive-aa-ma` when:
- ✅ ALL milestones have `Status: COMPLETE`
- ✅ Final git commit and push completed
- ✅ Plan is no longer being actively worked on
- ✅ You want to clean up the active directory

**Don't use** when:
- ❌ Any milestone is still PENDING, ACTIVE, or BLOCKED
- ❌ You might need to add more milestones
- ❌ Work is still in progress

---

**End of archive-aa-ma.md**
