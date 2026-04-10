#!/usr/bin/env bash
# SessionStart hook: Auto-detect active AA-MA tasks and emit hidden context
#
# When wired into ~/.claude/settings.json as a SessionStart hook:
#   - Scans ~/.claude/dev/active/ for active task directories
#   - Extracts current step and milestone from tasks.md
#   - Emits hidden system context so Claude knows what task is active
#
# If no active tasks exist, emits nothing (zero overhead).
# Always exits 0 — never blocks session start.
#
# Pattern inspired by caveman's caveman-activate.js (SessionStart stdout
# becomes hidden system context that Claude sees but users don't).

set -euo pipefail

# Check project-level .claude/dev/active/ first (most common), then HOME
# Claude Code sets CWD to the project root when hooks run
ACTIVE_DIR=""
if [ -d ".claude/dev/active" ] && [ -n "$(ls -A ".claude/dev/active" 2>/dev/null)" ]; then
    ACTIVE_DIR=".claude/dev/active"
elif [ -d "$HOME/.claude/dev/active" ] && [ -n "$(ls -A "$HOME/.claude/dev/active" 2>/dev/null)" ]; then
    ACTIVE_DIR="$HOME/.claude/dev/active"
fi

# Exit silently if no active tasks found at either location
if [ -z "$ACTIVE_DIR" ]; then
    exit 0
fi

# Find the most recently modified active task
task_dir=""
task_name=""
for d in "$ACTIVE_DIR"/*/; do
    [ -d "$d" ] || continue
    task_dir="$d"
    task_name=$(basename "$d")
done

# No task found (shouldn't happen after the ls -A check, but be safe)
if [ -z "$task_name" ]; then
    exit 0
fi

tasks_file="${task_dir}${task_name}-tasks.md"

# Extract current state from tasks.md
active_milestone="unknown"
active_step="unknown"

if [ -f "$tasks_file" ]; then
    # Find the ACTIVE milestone
    # Format: "## Milestone N: Title" followed by "- **Status:** ACTIVE" on next line
    active_milestone=$(grep -B2 '\*\*Status:\*\* ACTIVE' "$tasks_file" 2>/dev/null \
        | grep -E '^## ' | head -1 | sed 's/^## //' || true)

    # Find the first PENDING step (### header)
    active_step=$(grep -B2 '\*\*Status:\*\* PENDING' "$tasks_file" 2>/dev/null \
        | grep -E '^### ' | head -1 | sed 's/^### //' || true)

    # Fallback: if no ACTIVE milestone, find first PENDING milestone
    if [ -z "$active_milestone" ]; then
        active_milestone=$(grep -B2 '\*\*Status:\*\* PENDING' "$tasks_file" 2>/dev/null \
            | grep -E '^## ' | head -1 | sed 's/^## //' || true)
    fi

    [ -z "$active_milestone" ] && active_milestone="unknown"
    [ -z "$active_step" ] && active_step="unknown"
fi

# Emit hidden context (stdout from SessionStart hooks becomes system context)
printf 'AA-MA ACTIVE: task=[%s] milestone=[%s] step=[%s]. Load context: Read .claude/dev/active/%s/%s-reference.md and %s-tasks.md before proceeding.' \
    "$task_name" "$active_milestone" "$active_step" "$task_name" "$task_name" "$task_name"

exit 0
