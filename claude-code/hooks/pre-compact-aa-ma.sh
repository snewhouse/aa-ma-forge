#!/usr/bin/env bash
# PreCompact hook: Snapshot AA-MA state before auto-compaction
# Always exits 0 — never blocks compaction
set -euo pipefail

ACTIVE_DIR="$HOME/.claude/dev/active"
SNAPSHOT_DIR="$HOME/.claude/hooks/cache/compaction-snapshots"
LOG_FILE="$HOME/.claude/hooks/cache/compaction.log"

# Ensure directories exist
mkdir -p "$SNAPSHOT_DIR" "$(dirname "$LOG_FILE")"

# Check for active AA-MA tasks
if [ ! -d "$ACTIVE_DIR" ] || [ -z "$(ls -A "$ACTIVE_DIR" 2>/dev/null)" ]; then
    echo "$(date -Iseconds) | PreCompact | No active AA-MA tasks" >> "$LOG_FILE"
    exit 0
fi

for task_dir in "$ACTIVE_DIR"/*/; do
    [ -d "$task_dir" ] || continue
    task_name=$(basename "$task_dir")
    snapshot_file="$SNAPSHOT_DIR/${task_name}-snapshot.md"

    {
        echo "# AA-MA Compaction Snapshot: ${task_name}"
        echo "**Captured:** $(date -Iseconds)"
        echo ""

        # Task status from tasks.md
        if [ -f "${task_dir}${task_name}-tasks.md" ]; then
            echo "## Task Status"
            grep -E '(Milestone|Status|COMPLETE|IN.PROGRESS|PENDING|\[x\]|\[ \])' \
                "${task_dir}${task_name}-tasks.md" 2>/dev/null | head -30 || true
            echo ""
        fi

        # Full reference.md (immutable facts — always preserved)
        if [ -f "${task_dir}${task_name}-reference.md" ]; then
            echo "## Reference (Full)"
            cat "${task_dir}${task_name}-reference.md"
            echo ""
        fi

        # Last 20 lines of context-log
        if [ -f "${task_dir}${task_name}-context-log.md" ]; then
            echo "## Context Log (Last 20 Lines)"
            tail -20 "${task_dir}${task_name}-context-log.md"
            echo ""
        fi

        # Last 10 lines of provenance
        if [ -f "${task_dir}${task_name}-provenance.log" ]; then
            echo "## Provenance (Last 10 Lines)"
            tail -10 "${task_dir}${task_name}-provenance.log"
            echo ""
        fi
    } > "$snapshot_file"

    echo "$(date -Iseconds) | PreCompact | Snapshot saved: ${task_name}" >> "$LOG_FILE"
done

exit 0
