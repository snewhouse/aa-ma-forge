#!/usr/bin/env bash
# aa-ma-parse.sh — Shared helper library for AA-MA hooks.
#
# Source this file (don't execute it):
#     . "$(dirname "$0")/lib/aa-ma-parse.sh"
#
# Exports:
#     aa_ma_is_disabled                       -> 0 if AA_MA_HOOKS_DISABLE=1 set, else 1
#     aa_ma_extract_active_milestone <file>   -> stdout: active milestone heading text
#     aa_ma_extract_active_step <file>        -> stdout: active step heading text
#     aa_ma_list_active_tasks                 -> stdout: mtime-sorted task-dir paths, one per line
#     aa_ma_debug <msg...>                    -> stderr line iff HOOK_DEBUG=1
#
# Implementation notes:
#   - Format-agnostic Status regex: (\*\*)?Status:(\*\*)? +<WORD>
#     Accepts bold "**Status:** X" and plain "Status: X".
#   - HTML comments (<!-- ... -->) stripped before pattern-matching so block
#     examples in task files don't produce false positives.
#   - Milestone/step extraction uses an awk state machine instead of `grep -B2`
#     to avoid fragile line-context lookups across blank lines.
#   - Task listing iterates project-local `.claude/dev/active/` first, then
#     `$HOME/.claude/dev/active/`. Collisions resolve to project-local.
#     mtime order comes from `ls -t` on each task's `*-tasks.md` file.

# Guard against double-sourcing: functions are idempotent but re-definition
# is noisy under `set -u`/strict mode in consumers.
# shellcheck disable=SC2317  # `return` / `exit` fallback both unreachable by design
if [ "${AA_MA_PARSE_SH_LOADED:-0}" = "1" ]; then
    # Prefer `return` when sourced; fall back to `exit 0` if someone executes
    # the file directly (which would be a usage bug, but cleanly handled).
    return 0 2>/dev/null || exit 0
fi
AA_MA_PARSE_SH_LOADED=1

# -----------------------------------------------------------------------------
# aa_ma_is_disabled — returns 0 (true) if the master kill switch is set.
# -----------------------------------------------------------------------------
aa_ma_is_disabled() {
    [ "${AA_MA_HOOKS_DISABLE:-0}" = "1" ]
}

# -----------------------------------------------------------------------------
# aa_ma_debug <msg...> — emits a `[aa-ma-debug]` prefixed stderr line when
# HOOK_DEBUG=1 is set. Silent otherwise.
# -----------------------------------------------------------------------------
aa_ma_debug() {
    [ "${HOOK_DEBUG:-0}" = "1" ] || return 0
    printf '[aa-ma-debug] %s\n' "$*" >&2
}

# -----------------------------------------------------------------------------
# _aa_ma_strip_html_comments <file> — cat <file> with <!-- ... --> blocks
# removed. Used before Status-pattern matching so commented-out examples don't
# trigger false positives. Handles single-line comments only (block comments
# spanning lines are extremely rare in AA-MA tasks.md).
# -----------------------------------------------------------------------------
_aa_ma_strip_html_comments() {
    # Portable sed: remove <!-- ... --> on a single line.
    sed 's/<!--[^>]*-->//g' "$1"
}

# -----------------------------------------------------------------------------
# aa_ma_extract_active_milestone <tasks-file>
#   Emits the active milestone heading (stripped of leading "## ").
#   Preference order:
#     1. Milestone whose body contains a line matching Status: ACTIVE
#     2. First milestone whose body contains Status: PENDING
#   Emits empty string if neither found.
# -----------------------------------------------------------------------------
aa_ma_extract_active_milestone() {
    local file="$1"
    [ -f "$file" ] || return 0
    _aa_ma_strip_html_comments "$file" | awk '
        # ^## Milestone heading starts a new milestone block
        /^## / {
            current = $0
            sub(/^## /, "", current)
            found_pending = 0
            # keep track of first-pending fallback
            if (first_pending == "") first_pending_candidate = current
            next
        }
        # Status line: detect ACTIVE or PENDING within current milestone
        /(\*\*)?Status:(\*\*)? +ACTIVE/ {
            if (current != "") { active = current; exit }
        }
        /(\*\*)?Status:(\*\*)? +PENDING/ {
            if (current != "" && first_pending == "") {
                first_pending = current
            }
        }
        END {
            if (active != "") print active
            else if (first_pending != "") print first_pending
        }
    '
}

# -----------------------------------------------------------------------------
# aa_ma_extract_active_step <tasks-file>
#   Emits the active step heading (stripped of leading "### ").
#   Preference order:
#     1. Step whose body contains Status: ACTIVE
#     2. First step whose body contains Status: PENDING
#   Empty string if neither found.
# -----------------------------------------------------------------------------
aa_ma_extract_active_step() {
    local file="$1"
    [ -f "$file" ] || return 0
    _aa_ma_strip_html_comments "$file" | awk '
        /^### / {
            current = $0
            sub(/^### /, "", current)
            next
        }
        /(\*\*)?Status:(\*\*)? +ACTIVE/ {
            if (current != "") { active = current; exit }
        }
        /(\*\*)?Status:(\*\*)? +PENDING/ {
            if (current != "" && first_pending == "") {
                first_pending = current
            }
        }
        END {
            if (active != "") print active
            else if (first_pending != "") print first_pending
        }
    '
}

# -----------------------------------------------------------------------------
# aa_ma_list_active_tasks
#   Emits absolute paths to active task directories, one per line,
#   sorted newest-first by their tasks.md mtime.
#
#   Sources (checked in this order):
#     1. <cwd>/.claude/dev/active/
#     2. $HOME/.claude/dev/active/
#
#   Collision rule: if the same task name appears in both sources, the
#   project-local version wins (home version is suppressed).
# -----------------------------------------------------------------------------
aa_ma_list_active_tasks() {
    local project_dir="${PWD}/.claude/dev/active"
    local home_dir="${HOME}/.claude/dev/active"
    local -A seen_names=()
    local -a rows=()
    local task_name tasks_file mtime dir source_dir

    for source_dir in "$project_dir" "$home_dir"; do
        [ -d "$source_dir" ] || continue
        for dir in "$source_dir"/*/; do
            [ -d "$dir" ] || continue
            task_name=$(basename "$dir")
            # Collision: project-local wins (project is first in the outer loop).
            if [ -n "${seen_names[$task_name]:-}" ]; then
                continue
            fi
            seen_names[$task_name]=1
            tasks_file="${dir}${task_name}-tasks.md"
            if [ -f "$tasks_file" ]; then
                mtime=$(stat -c %Y "$tasks_file")
            else
                mtime=0
            fi
            rows+=("${mtime}"$'\t'"${dir%/}")
        done
    done

    # Sort numerically by mtime descending (newest first); on tie, sort by path
    # ascending for a stable deterministic fallback. Emit just the path column.
    if [ "${#rows[@]}" -gt 0 ]; then
        printf '%s\n' "${rows[@]}" \
            | sort -t$'\t' -k1,1rn -k2,2 \
            | awk -F'\t' 'NF==2 { print $2 }'
    fi
}

# -----------------------------------------------------------------------------
# End of aa-ma-parse.sh
# -----------------------------------------------------------------------------
