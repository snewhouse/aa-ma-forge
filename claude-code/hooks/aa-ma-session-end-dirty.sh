#!/usr/bin/env bash
# Event: SessionEnd
# Mode: Advisory — warns on stderr, never blocks
# Exit: 0 always
# Fail-open: kill switch, no active task, CLAUDE_CODE unset, not a git repo → exit 0 silently; an unreadable payload or invalid session_id → no marker cleanup
#
# SessionEnd hook — warn when AA-MA artifacts are git-dirty at session end, and remove this
# session's aa-ma-impact-preedit.sh markers (~/.claude/runtime/impact-seen-<session_id>).
#
# Enforces the CLAUDE.md rule: "never leave uncommitted work at session end".
# Scans every active task directory (project-local + $HOME); for each, runs
# `git status --porcelain` in that task's project root, and emits a single
# stderr warning naming any dirty AA-MA artifact file.
#
# Always advisory — exits 0 regardless of what it finds.
#
# Silent cases:
#   - AA_MA_HOOKS_DISABLE=1          (master kill switch)
#   - No active task directories
#   - CLAUDE_CODE env var unset      (CI / non-session contexts)
#   - No dirty AA-MA artifacts
#
# Verbose cases:
#   - HOOK_DEBUG=1                   per-task trace lines to stderr

set -euo pipefail

# Resolve helper across two layouts (project subdir OR installed sibling).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "${SCRIPT_DIR}/lib/aa-ma-parse.sh" ]; then
    HELPER="${SCRIPT_DIR}/lib/aa-ma-parse.sh"
elif [ -f "${SCRIPT_DIR}/aa-ma-parse.sh" ]; then
    HELPER="${SCRIPT_DIR}/aa-ma-parse.sh"
else
    printf 'aa-ma-session-end-dirty: cannot find aa-ma-parse.sh helper\n' >&2
    exit 0  # advisory only — never fail a session
fi
# shellcheck source=lib/aa-ma-parse.sh
# shellcheck disable=SC1090,SC1091
. "$HELPER"

# -----------------------------------------------------------------------------
# Guard rails (each exits 0 — the hook is advisory).
# -----------------------------------------------------------------------------
if aa_ma_is_disabled; then
    aa_ma_debug "session-end-dirty: AA_MA_HOOKS_DISABLE=1, skipping"
    exit 0
fi

# -----------------------------------------------------------------------------
# Remove this session's impact-preedit markers. Before the CLAUDE_CODE guard: the
# markers exist whenever the PreToolUse hook ran, whatever the environment says.
# Only a session_id matching the marker hook's own regex reaches rm, so the path
# is always exactly ~/.claude/runtime/impact-seen-<id> — never anything else.
# -----------------------------------------------------------------------------
if [ ! -t 0 ] && [ -n "${HOME:-}" ] && command -v jq > /dev/null 2>&1; then  # why: a presence probe
    # why: 2 s bounds a stdin that never closes; a jq parse error just means no session_id
    sid="$(timeout 2 cat | jq -r '.session_id // empty' 2>/dev/null || true)"
    if [[ "${sid}" =~ ^[A-Za-z0-9_-]{1,64}$ ]]; then
        rm -rf -- "${HOME}/.claude/runtime/impact-seen-${sid}" \
            || log_warn session-end-dirty "could not remove impact-seen-${sid}"
    elif [ -n "${sid}" ]; then
        log_warn session-end-dirty "invalid session_id; impact-preedit markers not removed"
    fi
fi

# CI / non-Claude-Code context: CLAUDE_CODE env var absent → exit silently.
# This avoids spamming warnings during bats runs, GitHub Actions, local tests.
if [ -z "${CLAUDE_CODE:-}" ]; then
    aa_ma_debug "session-end-dirty: CLAUDE_CODE unset (CI / non-session context), skipping"
    exit 0
fi

# -----------------------------------------------------------------------------
# Collect active task directories.
# -----------------------------------------------------------------------------
mapfile -t TASKS < <(aa_ma_list_active_tasks)
if [ "${#TASKS[@]}" -eq 0 ]; then
    aa_ma_debug "session-end-dirty: no active tasks"
    exit 0
fi

# -----------------------------------------------------------------------------
# For each task dir, find its project root and check git status.
# -----------------------------------------------------------------------------
warnings_emitted=0

for task_dir in "${TASKS[@]}"; do
    task_name=$(basename "$task_dir")
    aa_ma_debug "session-end-dirty: inspecting ${task_name} at ${task_dir}"

    # Find the enclosing git repo root. If the task dir isn't inside a repo,
    # skip it (e.g. $HOME/.claude/dev/active/ lives in $HOME, which may or
    # may not be a repo — don't assume).
    project_root=$(git -C "$task_dir" rev-parse --show-toplevel 2>/dev/null || true)
    if [ -z "$project_root" ]; then
        aa_ma_debug "session-end-dirty: ${task_name} not in a git repo, skipping"
        continue
    fi

    # Get relative path from project root to the task directory so we can
    # filter porcelain output to just files under this task's artifact tree.
    rel_task_dir=$(realpath --relative-to="$project_root" "$task_dir" 2>/dev/null || echo "")
    if [ -z "$rel_task_dir" ]; then
        aa_ma_debug "session-end-dirty: could not compute rel path for ${task_name}"
        continue
    fi

    # git status --porcelain emits lines like " M path/to/file" or "?? path".
    # We want any line whose path starts with our task dir's relative path.
    dirty_artifacts=$(git -C "$project_root" status --porcelain 2>/dev/null \
        | awk -v prefix="$rel_task_dir/" '{
            # porcelain format: first 2 chars = status, then space, then path
            path = substr($0, 4)
            if (index(path, prefix) == 1) print path
        }')

    if [ -n "$dirty_artifacts" ]; then
        warnings_emitted=$((warnings_emitted + 1))
        {
            printf '⚠️  AA-MA artifacts dirty in task [%s]:\n' "$task_name"
            printf '%s\n' "$dirty_artifacts" | sed 's/^/    /'
            printf '    Commit or stash before ending the session (CLAUDE.md convention).\n'
        } >&2
    else
        aa_ma_debug "session-end-dirty: ${task_name} clean"
    fi
done

aa_ma_debug "session-end-dirty: done; ${warnings_emitted} warning(s) emitted"
exit 0
