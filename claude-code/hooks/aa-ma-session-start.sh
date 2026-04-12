#!/usr/bin/env bash
# SessionStart hook: surface the most-recently-touched active AA-MA task.
#
# Behaviour:
#   - Scans project-local `.claude/dev/active/` first, then $HOME/.claude/dev/active/
#   - Picks the task whose `*-tasks.md` has the newest mtime (ties → alphabetical)
#   - Emits a single hidden-context line describing the top task + its absolute path
#   - Appends "(N other active tasks: a, b, c [and M more])" when there are 2+ active tasks
#
# Honours AA_MA_HOOKS_DISABLE=1 (master kill switch).
# Always exits 0 — never blocks session start.

set -euo pipefail

# shellcheck source=lib/aa-ma-parse.sh
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
. "${SCRIPT_DIR}/lib/aa-ma-parse.sh"

# Master kill switch honoured.
if aa_ma_is_disabled; then
    exit 0
fi

# Collect active task dirs (mtime-sorted, project-first collision).
mapfile -t TASKS < <(aa_ma_list_active_tasks)

if [ "${#TASKS[@]}" -eq 0 ]; then
    exit 0
fi

# Normalise each path to remove any accidental "//" introduced by trailing-slash $HOME.
normalise_path() {
    # shellcheck disable=SC2001  # sed more portable than bash ${var//} here
    printf '%s' "$1" | sed 's|//*|/|g'
}

TOP_DIR="$(normalise_path "${TASKS[0]}")"
TOP_NAME="$(basename "$TOP_DIR")"
TOP_TASKS_FILE="${TOP_DIR}/${TOP_NAME}-tasks.md"

# Extract milestone + step from the top task's tasks.md (format-agnostic via helper).
active_milestone="unknown"
active_step="unknown"
if [ -f "$TOP_TASKS_FILE" ]; then
    m=$(aa_ma_extract_active_milestone "$TOP_TASKS_FILE")
    s=$(aa_ma_extract_active_step "$TOP_TASKS_FILE")
    [ -n "$m" ] && active_milestone="$m"
    [ -n "$s" ] && active_step="$s"
fi

# Build footer listing other active tasks (cap at 3 names, then "and M more").
FOOTER=""
OTHER_COUNT=$(( ${#TASKS[@]} - 1 ))
if [ "$OTHER_COUNT" -gt 0 ]; then
    declare -a OTHER_NAMES=()
    for ((i = 1; i < ${#TASKS[@]}; i++)); do
        OTHER_NAMES+=("$(basename "${TASKS[i]}")")
    done

    shown_count=${#OTHER_NAMES[@]}
    if [ "$shown_count" -gt 3 ]; then
        shown_count=3
    fi

    # Comma-join the shown names.
    joined=""
    for ((j = 0; j < shown_count; j++)); do
        if [ $j -eq 0 ]; then
            joined="${OTHER_NAMES[j]}"
        else
            joined="${joined}, ${OTHER_NAMES[j]}"
        fi
    done

    remaining=$(( ${#OTHER_NAMES[@]} - shown_count ))
    if [ "$remaining" -gt 0 ]; then
        FOOTER=" (${OTHER_COUNT} other active tasks: ${joined} and ${remaining} more)"
    else
        FOOTER=" (${OTHER_COUNT} other active tasks: ${joined})"
    fi
fi

# Emit the hidden system-context line. Path is the ACTUAL resolved path, not a hardcoded fragment.
printf 'AA-MA ACTIVE: task=[%s] milestone=[%s] step=[%s]. Load context: Read %s/%s-reference.md and %s-tasks.md before proceeding.%s' \
    "$TOP_NAME" "$active_milestone" "$active_step" "$TOP_DIR" "$TOP_NAME" "$TOP_NAME" "$FOOTER"

exit 0
