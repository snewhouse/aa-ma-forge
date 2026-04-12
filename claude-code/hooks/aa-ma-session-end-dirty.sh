#!/usr/bin/env bash
# SessionEnd hook — warn when AA-MA artifacts are git-dirty at session end.
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
