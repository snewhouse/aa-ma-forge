#!/usr/bin/env bash
# Event: PostToolUse(Bash)
# Mode: Advisory — warns, never blocks
# Exit: 0 always
# Fail-open: every skip path (kill switch, no active plan, not a commit) exits 0 silently; each skip of the co-change advisory leaves one hooks.log line (DEBUG: no index / no codemem; WARN: codemem failed or timed out)
#
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
# Ad-hoc commits — no active AA-MA plan, or `[ad-hoc]` on its own line in the message —
# instead get ONE co-change line (code-conventions-impact 10.7): the codemem co_changes
# partners of the committed files (aa_ma_cochange_partners: the T7 constants, >= 5 shared
# commits and >= 50% of the file's commits) that the commit left out, under a 2 s timeout.
# No codemem or no index → a DEBUG hooks.log line; a failed or slow query → a WARN line;
# nothing is printed either way.
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

aa_ma_debug_cmd "commit-drift: examining last commit after" "$cmd"

# -----------------------------------------------------------------------------
# Ad-hoc co-change advisory (10.7). Prints at most one line; never fails the hook.
# -----------------------------------------------------------------------------
COCHANGE_TIMEOUT_S=2      # the advisory must never slow a commit noticeably
COCHANGE_MAX_NAMES=10     # the line stays one readable line
DRIFT_HOOK="aa-ma-commit-drift"

# cochange_advisory <committed-file>... — at most one stderr line; every skip logs one line.
cochange_advisory() {
    local real forge top partners rc=0 skip="co-change advisory skipped"
    local -a missed=()
    # why: no `readlink -f` (old macOS) → the path as invoked, then the lib lookups decide
    real="$(readlink -f "${BASH_SOURCE[0]}" 2>/dev/null)" || real="${BASH_SOURCE[0]}"
    forge="${real%/*}"; forge="${forge%/*/*}"   # <forge>/claude-code/hooks/<this>
    # why: git's own message is replaced by the debug line
    top=$(git rev-parse --show-toplevel 2>/dev/null) || { log_debug "$DRIFT_HOOK" "${skip}: not in a git work tree"; return 0; }
    partners=$(aa_ma_cochange_partners "$top" "$forge" "$COCHANGE_TIMEOUT_S" -- "$@") || rc=$?
    case "$rc" in
        0) ;;
        3) log_debug "$DRIFT_HOOK" "${skip}: no codemem index for this repo"; return 0 ;;
        4) log_debug "$DRIFT_HOOK" "${skip}: no codemem binary (or no timeout(1))"; return 0 ;;
        6) log_warn "$DRIFT_HOOK" "${skip}: codemem co_changes timed out after ${COCHANGE_TIMEOUT_S} s"; return 0 ;;
        *) log_warn "$DRIFT_HOOK" "${skip}: codemem co_changes failed or printed no JSON (rc ${rc})"; return 0 ;;
    esac
    [ -n "$partners" ] || return 0
    mapfile -t missed < <(grep -Fvx -f <(printf '%s\n' "$@") <<< "$partners")
    [ "${#missed[@]}" -gt 0 ] || return 0
    local shown more=""
    # Partner paths are repo-controlled: aa_ma_sanitize_lines turns bidi/zero-width/tag characters into `?`.
    shown=$(printf '%s\n' "${missed[@]:0:COCHANGE_MAX_NAMES}" | aa_ma_sanitize_lines | paste -sd ',' - | sed 's/,/, /g')
    [ "${#missed[@]}" -gt "$COCHANGE_MAX_NAMES" ] && more=" (+$(( ${#missed[@]} - COCHANGE_MAX_NAMES )) more)"
    printf 'ℹ️  co-change advisory (codemem; shared>=%s, ratio>=%s): often changed with these files but not in this commit: %s%s\n' \
        "$AA_MA_COCHANGE_MIN_SHARED" "$AA_MA_COCHANGE_MIN_RATIO" "${shown//[[:cntrl:]]/?}" "$more" >&2
}

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

# -----------------------------------------------------------------------------
# Active plans? None, or an [ad-hoc] commit: the co-change advisory.
# -----------------------------------------------------------------------------
mapfile -t TASKS < <(aa_ma_list_active_tasks)
if [ "${#TASKS[@]}" -eq 0 ] \
    || printf '%s\n' "$commit_msg" | grep -Eq '^[[:space:]]*\[ad-hoc\][[:space:]]*$'; then
    if [ -n "$commit_files" ]; then
        mapfile -t _committed <<< "$commit_files"
        # shellcheck disable=SC2310  # why: set -e off inside it is the point — any failure there is "no advisory"
        cochange_advisory "${_committed[@]}" || true   # why: advisory only; a failure inside must never fail the hook
    fi
fi
if [ "${#TASKS[@]}" -eq 0 ]; then
    aa_ma_debug "commit-drift: no active AA-MA plans, skipping"
    exit 0
fi

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
