# shellcheck shell=bash
# aa-ma-install-lib.sh — what scripts/install.sh and scripts/uninstall.sh share.
# Sourced, never run. Callers set REPO_ROOT before using points_into_repo.
#
# AA_MA_HOOKS is the one hook table: install.sh registers each row, uninstall.sh
# deregisters each row, and codemem's plugin-surface extractor reads this file
# (surface_allowlist.HOOK_TABLE, `_HOOK_BLOCK` / `_HOOK_ROW` in plugin_surface.py).
#
# Row: event|matcher|source_basename|timeout|statusMessage. A matcher is a regex and may
# itself hold `|` (`Edit|Write`), so a row is split by anchoring on the
# `<name>.sh|<timeout>|` field. Empty matcher = no tool-name restriction (SessionStart, …).

AA_MA_HOOKS=(
    "SessionStart||aa-ma-session-start.sh|5|Loading AA-MA context..."
    "PreCompact||pre-compact-aa-ma.sh|5|"
    "PreToolUse|Bash|aa-ma-commit-signature.sh|10|"
    "PreToolUse|Bash|security-static-check.sh|10|"
    "SessionEnd||aa-ma-session-end-dirty.sh|5|"
    "PostToolUse|Bash|aa-ma-commit-drift.sh|5|"
    "PreToolUse|ExitPlanMode|aa-ma-plan-skip-warn.sh|5|"
    "SessionEnd||aa-ma-plan-skip-warn.sh|5|"
    "PostToolUse|Edit|Write|ruff-format.sh|10|"
)

# aa_ma_hook_parse ROW — set HOOK_EVENT HOOK_MATCHER HOOK_SRC HOOK_TIMEOUT HOOK_STATUS;
# return 1 when ROW does not parse.
# why: SC2034 — the HOOK_* variables are this function's output, read by the sourcing script.
# shellcheck disable=SC2034
aa_ma_hook_parse() {
    [[ "$1" =~ ^([A-Za-z]+)\|(.*)\|([A-Za-z0-9_.-]+\.sh)\|([0-9]+)\|(.*)$ ]] || return 1
    HOOK_EVENT="${BASH_REMATCH[1]}" HOOK_MATCHER="${BASH_REMATCH[2]}" HOOK_SRC="${BASH_REMATCH[3]}"
    HOOK_TIMEOUT="${BASH_REMATCH[4]}" HOOK_STATUS="${BASH_REMATCH[5]}"
}

# aa_ma_hooks_validate — name every row that does not parse on stderr; return 1 if any.
# Run it before changing anything, so a bad table never leaves a half-done (un)install.
aa_ma_hooks_validate() {
    local row bad=0
    for row in "${AA_MA_HOOKS[@]}"; do
        aa_ma_hook_parse "${row}" || { printf 'Unparseable AA_MA_HOOKS row: %s\n' "${row}" >&2; bad=1; }
    done
    return "${bad}"
}

# points_into_repo LINK — true when LINK resolves into this checkout. A relative link
# resolves against its own directory; one whose source directory is gone falls back to
# its raw destination. Another checkout under .worktrees/ is not this one.
points_into_repo() {
    local dest
    # why: 2>/dev/null — readlink -f fails when the source directory is gone; the raw
    # destination below is the answer then, not an error.
    dest="$(readlink -f "$1" 2>/dev/null || readlink "$1")"
    [[ "${dest}" == "${REPO_ROOT}/"* && "${dest}" != "${REPO_ROOT}/.worktrees/"* ]]
}
