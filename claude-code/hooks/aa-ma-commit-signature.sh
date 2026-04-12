#!/usr/bin/env bash
# PreToolUse(Bash) hook — enforce AA-MA commit signature on git commits.
#
# Fires via Claude Code's PreToolUse event with matcher="Bash". Reads a JSON
# object from stdin of shape {tool_name: "Bash", tool_input: {command: "..."}}.
#
# Decision tree:
#   1. AA_MA_HOOKS_DISABLE=1              → exit 0 (kill switch)
#   2. stdin JSON malformed                → exit 1 (hook infra error, NOT block)
#   3. command is not `git commit ...`     → exit 0 (not our concern)
#   4. command is `git commit` without -m/-F/--message/--file (editor form)
#                                          → exit 0 (can't see message yet)
#   5. no active AA-MA plan directories    → exit 0 (nothing to enforce)
#   6. command contains `[ad-hoc]` line    → exit 0 (auditable bypass)
#   7. command contains `[AA-MA Plan] <name>` where <name> is an active task
#                                          → exit 0 (valid signature)
#   8. otherwise                           → exit 2 with pretty stderr
#
# Known scope limits (documented, not bugs):
#   - Bare `git commit` / `--amend` opens the editor; PreToolUse can't see
#     the future message. We pass through.
#   - `git commit -F /path/to/msg.txt` — marker in the file, not in the
#     command string. We pass through (accept false negatives).
#   - Message via variable expansion (`git commit -m "$MSG"`) — we see the
#     literal `$MSG`, not its expansion. We pass through.

set -euo pipefail

# Resolve helper across two layouts:
#   - Project layout:  <repo>/claude-code/hooks/aa-ma-commit-signature.sh
#                      helper at ../hooks/lib/aa-ma-parse.sh (subdir)
#   - Installed layout: ~/.claude/hooks/lib/aa-ma-commit-signature.sh
#                      helper at same dir (sibling)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "${SCRIPT_DIR}/lib/aa-ma-parse.sh" ]; then
    HELPER="${SCRIPT_DIR}/lib/aa-ma-parse.sh"
elif [ -f "${SCRIPT_DIR}/aa-ma-parse.sh" ]; then
    HELPER="${SCRIPT_DIR}/aa-ma-parse.sh"
else
    printf 'aa-ma-commit-signature: cannot find aa-ma-parse.sh helper (looked in %s/lib and %s)\n' \
        "$SCRIPT_DIR" "$SCRIPT_DIR" >&2
    exit 1
fi
# shellcheck source=lib/aa-ma-parse.sh
# shellcheck disable=SC1090,SC1091
. "$HELPER"

# -----------------------------------------------------------------------------
# 1. Kill switch.
# -----------------------------------------------------------------------------
if aa_ma_is_disabled; then
    aa_ma_debug "commit-signature: AA_MA_HOOKS_DISABLE=1, passing through"
    exit 0
fi

# -----------------------------------------------------------------------------
# 2. Parse stdin JSON.
# -----------------------------------------------------------------------------
if ! command -v jq >/dev/null 2>&1; then
    printf 'aa-ma-commit-signature: jq not found in PATH — install jq to enforce AA-MA commit signatures\n' >&2
    exit 1
fi

stdin_json=$(cat)
cmd=$(printf '%s' "$stdin_json" | jq -er '.tool_input.command // empty' 2>/dev/null) || {
    printf 'aa-ma-commit-signature: failed to parse stdin JSON (expected {tool_name, tool_input: {command}})\n' >&2
    exit 1
}

[ -z "$cmd" ] && exit 0  # empty command — nothing to do

aa_ma_debug "commit-signature: examining command: $cmd"

# -----------------------------------------------------------------------------
# 3. Word-boundary match on `git commit`. NOT `git commit-tree`, `commit-graph`.
#    Pattern: `git commit` followed by whitespace OR end-of-string.
# -----------------------------------------------------------------------------
if ! printf '%s' "$cmd" | grep -Eq 'git commit([[:space:]]|$)'; then
    exit 0
fi

# -----------------------------------------------------------------------------
# 4. Editor form detection. If no message-providing flag is present, the
#    editor will open and we can't inspect the message at PreToolUse time.
# -----------------------------------------------------------------------------
if ! printf '%s' "$cmd" | grep -Eq '([[:space:]]|^)(-m|-F|-c|-C|--message|--file|--reedit-message|--reuse-message)([[:space:]]|=|$)'; then
    aa_ma_debug "commit-signature: editor-form commit (no -m/-F), passing through"
    exit 0
fi

# -----------------------------------------------------------------------------
# 5. Active plan detection.
# -----------------------------------------------------------------------------
mapfile -t TASKS < <(aa_ma_list_active_tasks)
if [ "${#TASKS[@]}" -eq 0 ]; then
    exit 0
fi

# -----------------------------------------------------------------------------
# 6. [ad-hoc] bypass marker on its own line.
#    The marker must appear on a line by itself (trimmed) in the command text.
#    We grep for a pattern matching whitespace-flanked `[ad-hoc]` inside a
#    HEREDOC/string literal. Since the literal command string may contain
#    \n escapes OR real newlines, we test both.
# -----------------------------------------------------------------------------
# Normalize \n escape sequences to real newlines for marker scanning.
normalized_cmd=$(printf '%s' "$cmd" | sed 's/\\n/\n/g')
# Pattern allows trailing delimiters (", ', `) that arise from shell quoting when the
# marker is the last line of a -m "..." message literal.
if printf '%s\n' "$normalized_cmd" | grep -Eq '^[[:space:]]*\[ad-hoc\][[:space:]"'"'"'\`]*$'; then
    aa_ma_debug "commit-signature: [ad-hoc] marker found, passing through"
    exit 0
fi

# -----------------------------------------------------------------------------
# 7. Extract candidate [AA-MA Plan] signatures from the command.
#    Accept the signature only if the task name matches an active task.
# -----------------------------------------------------------------------------
active_names=()
for td in "${TASKS[@]}"; do
    active_names+=("$(basename "$td")")
done

# Find all [AA-MA Plan] NAME occurrences (NAME = one word, not spaces).
sig_names=$(printf '%s' "$normalized_cmd" | grep -Eo '\[AA-MA Plan\] [^ ]+' | awk '{print $NF}' || true)

if [ -n "$sig_names" ]; then
    while IFS= read -r found_name; do
        for active_name in "${active_names[@]}"; do
            if [ "$found_name" = "$active_name" ]; then
                aa_ma_debug "commit-signature: valid signature [$found_name]"
                exit 0
            fi
        done
    done <<< "$sig_names"
fi

# -----------------------------------------------------------------------------
# 8. Block. Build pretty stderr message naming the top active task.
# -----------------------------------------------------------------------------
top_name="${active_names[0]}"
{
    printf '\n'
    printf '❌ AA-MA signature missing or invalid\n\n'
    printf 'Active AA-MA plan: %s\n' "$top_name"
    if [ "${#active_names[@]}" -gt 1 ]; then
        others=$(IFS=, ; printf '%s' "${active_names[*]:1}")
        printf '(Other active plans: %s)\n' "${others//,/, }"
    fi
    printf '\n'
    printf 'Append to commit message footer:\n\n'
    printf '  [AA-MA Plan] %s .claude/dev/active/%s\n\n' "$top_name" "$top_name"
    printf 'Or if this commit is genuinely unrelated to the active plan,\n'
    printf 'add on its own line:\n\n'
    printf '  [ad-hoc]\n\n'
    printf 'Emergency bypass (auditable via commit history, not git log):\n\n'
    printf '  export AA_MA_HOOKS_DISABLE=1\n\n'
} >&2

exit 2
