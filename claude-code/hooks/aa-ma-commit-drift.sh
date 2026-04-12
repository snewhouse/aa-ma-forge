#!/usr/bin/env bash
# PostToolUse(Bash) hook — warn when a commit lands without touching any
# AA-MA task's tasks.md or provenance.log.
#
# Fires after ANY successful Bash tool call. We first check whether the
# Bash command looked like `git commit` (word-boundary). If yes, we inspect
# the last commit via `git log -1 --name-only HEAD` (NOT the PostToolUse
# tool_response, whose shape is undocumented for Bash). We warn only when:
#   - AA_MA_HOOKS_DISABLE is not set
#   - At least one active AA-MA plan exists
#   - The command is actually a git commit (not commit-tree, not unrelated)
#   - The commit exists (not the initial-commit edge case)
#   - More than AA_MA_DRIFT_THRESHOLD files were touched (default 1)
#   - None of the committed files is a tasks.md or provenance.log under an
#     active task directory
#   - The commit message does NOT contain `[no-sync-check]` on its own line
#
# Always exits 0 (advisory).

set -euo pipefail

# Resolve helper across two layouts.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "${SCRIPT_DIR}/lib/aa-ma-parse.sh" ]; then
    HELPER="${SCRIPT_DIR}/lib/aa-ma-parse.sh"
elif [ -f "${SCRIPT_DIR}/aa-ma-parse.sh" ]; then
    HELPER="${SCRIPT_DIR}/aa-ma-parse.sh"
else
    printf 'aa-ma-commit-drift: cannot find aa-ma-parse.sh helper\n' >&2
    exit 0
fi
# shellcheck source=lib/aa-ma-parse.sh
# shellcheck disable=SC1090,SC1091
. "$HELPER"

# -----------------------------------------------------------------------------
# Guard rails — each exits 0.
# -----------------------------------------------------------------------------
if aa_ma_is_disabled; then
    aa_ma_debug "commit-drift: AA_MA_HOOKS_DISABLE=1, skipping"
    exit 0
fi

if ! command -v jq >/dev/null 2>&1; then
    aa_ma_debug "commit-drift: jq missing, skipping"
    exit 0
fi

stdin_json=$(cat)
cmd=$(printf '%s' "$stdin_json" | jq -er '.tool_input.command // empty' 2>/dev/null) || exit 0
[ -z "$cmd" ] && exit 0

# Word-boundary match on `git commit`. Distinguishes commit-tree, commit-graph.
if ! printf '%s' "$cmd" | grep -Eq 'git commit([[:space:]]|$)'; then
    exit 0
fi

aa_ma_debug "commit-drift: examining last commit after: $cmd"

# -----------------------------------------------------------------------------
# Active plans?
# -----------------------------------------------------------------------------
mapfile -t TASKS < <(aa_ma_list_active_tasks)
if [ "${#TASKS[@]}" -eq 0 ]; then
    aa_ma_debug "commit-drift: no active AA-MA plans, skipping"
    exit 0
fi

# -----------------------------------------------------------------------------
# Inspect the last commit in the current working directory's repo.
# -----------------------------------------------------------------------------
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    aa_ma_debug "commit-drift: not inside a git repo, skipping"
    exit 0
fi

# Initial-commit guard: `git log -1` fails on a pre-first-commit repo.
if ! git log -1 --format=%H HEAD >/dev/null 2>&1; then
    aa_ma_debug "commit-drift: no commits yet (initial-commit case), skipping"
    exit 0
fi

commit_files=$(git log -1 --name-only --format= HEAD 2>/dev/null | awk 'NF')
commit_msg=$(git log -1 --format=%B HEAD 2>/dev/null)

# Below-threshold skip.
file_count=$(printf '%s\n' "$commit_files" | awk 'NF' | wc -l)
threshold="${AA_MA_DRIFT_THRESHOLD:-1}"
if [ "$file_count" -le "$threshold" ]; then
    aa_ma_debug "commit-drift: ${file_count} files <= threshold ${threshold}, skipping"
    exit 0
fi

# [no-sync-check] bypass marker (on its own line, trailing delimiters OK).
if printf '%s\n' "$commit_msg" \
    | grep -Eq '^[[:space:]]*\[no-sync-check\][[:space:]"'"'"'\`]*$'; then
    aa_ma_debug "commit-drift: [no-sync-check] marker found, skipping"
    exit 0
fi

# -----------------------------------------------------------------------------
# Determine which active tasks had their tasks.md OR provenance.log touched.
# A task counts as "synced" if ANY artifact bearing its name is in the diff.
# -----------------------------------------------------------------------------
project_root=$(git rev-parse --show-toplevel 2>/dev/null)

unsync_tasks=()
for td in "${TASKS[@]}"; do
    name=$(basename "$td")
    # Compute rel path from project root to the task dir. Skip if the task dir
    # isn't inside this repo (e.g. $HOME task dir while in a project repo).
    rel=$(realpath --relative-to="$project_root" "$td" 2>/dev/null || true)
    case "$rel" in
        ''|..*|/*) continue ;;  # outside this repo
    esac
    tasks_path="${rel}/${name}-tasks.md"
    prov_path="${rel}/${name}-provenance.log"
    if printf '%s\n' "$commit_files" | grep -Fxq -e "$tasks_path"; then
        aa_ma_debug "commit-drift: task ${name} sync via tasks.md"
        continue
    fi
    if printf '%s\n' "$commit_files" | grep -Fxq -e "$prov_path"; then
        aa_ma_debug "commit-drift: task ${name} sync via provenance.log"
        continue
    fi
    unsync_tasks+=("$name")
done

if [ "${#unsync_tasks[@]}" -eq 0 ]; then
    aa_ma_debug "commit-drift: all active tasks synced by this commit"
    exit 0
fi

# -----------------------------------------------------------------------------
# Emit warning.
# -----------------------------------------------------------------------------
{
    printf '\n'
    printf '⚠️  Possible AA-MA drift: commit touched %d files but no active plan\n' "$file_count"
    printf '    had its tasks.md or provenance.log updated.\n\n'
    printf 'Active plans without sync in this commit:\n'
    for t in "${unsync_tasks[@]}"; do
        printf '  - %s\n' "$t"
    done
    printf '\nIf the commit genuinely doesn'"'"'t relate to any active plan,\n'
    printf 'add on its own line to the commit message:\n\n'
    printf '  [no-sync-check]\n\n'
    printf 'Kill switch: export AA_MA_HOOKS_DISABLE=1\n'
} >&2

exit 0
