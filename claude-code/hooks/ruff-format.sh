#!/usr/bin/env bash
# Event: PostToolUse(Edit|Write)
# Mode: Advisory — never blocks
# Exit: 0 always
# Fail-open: non-.py or missing file → exit 0; unreadable stdin → one hooks.log line; jq not found → a systemMessage; ruff not found → one systemMessage per session; a ruff format failure is logged to hooks.log
#
# Formats and autofixes an edited .py file with ruff, then hands the model what `ruff check`
# still finds, as PostToolUse additionalContext (at most 10 lines).
#
# ruff comes ONLY from this forge's .venv or an absolute PATH entry — never from the edited
# repo, which may be hostile and commit its own .venv/bin/ruff (plan §0 v2, Security CRITICAL).
# A relative PATH entry such as `.venv/bin` would resolve against that repo, so it is refused.
[[ "${AA_MA_HOOKS_DISABLE:-0}" == "1" ]] && exit 0   # master kill switch, like every AA-MA hook

HOOK="ruff-format"
# Context lines handed to the model per edit: enough to act on, small enough not to drown it.
MAX_CONTEXT_LINES=10

payload=$(</dev/stdin)
# Fork-free pre-gate: this runs on every Edit/Write, and a .py file_path always appears in the
# JSON as `….py"`. A miss is exact; a hit (e.g. ".py" in the edited text) gets the real check below.
[[ "${payload}" == *'.py"'* ]] || exit 0

REAL="$(readlink -f "${BASH_SOURCE[0]}")"   # <forge>/claude-code/hooks/ruff-format.sh
REAL_DIR="${REAL%/*}"
FORGE="${REAL_DIR%/*/*}"
if [[ -f "${REAL_DIR}/lib/aa-ma-log.sh" ]]; then
    # shellcheck disable=SC1091  # why: runtime path; aa-ma-log.bats covers the library
    . "${REAL_DIR}/lib/aa-ma-log.sh"
else
    printf '%s\n' '{"systemMessage": "ruff-format: aa-ma-log.sh not found; re-run scripts/install.sh"}'
    exit 0
fi
# why: `command -v` prints the path on success; only its status is wanted
if ! command -v jq >/dev/null 2>&1; then
    fail_open_notice "${HOOK}" "jq not on PATH; .py edits are not formatted"
    exit 0
fi

# One jq for both fields, NUL-separated so any byte in the path survives.
# why: jq's parse error is replaced by the one log_warn line below
mapfile -d '' -t fields < <(jq -j '(.tool_input.file_path // ""), "\u0000", (.session_id // ""), "\u0000"' <<<"${payload}" 2>/dev/null)
if (( ${#fields[@]} != 2 )); then   # jq printed nothing: the payload is not the JSON we expect
    log_warn "${HOOK}" "stdin payload not readable as hook JSON; .py edit not formatted"
    exit 0
fi
f="${fields[0]}" sid="${fields[1]}"
[[ "${f}" == *.py && -f "${f}" ]] || exit 0

# notify_no_ruff — one fail_open_notice per session; the marker file remembers the session.
notify_no_ruff() {
    local marker
    # why: sid becomes a filename; 64 bounds it (real ids are 36-char UUIDs), the class stops ../
    if [[ "${sid}" =~ ^[A-Za-z0-9_-]{1,64}$ ]]; then
        marker="${HOME}/.claude/hooks/cache/ruff-format-no-ruff-${sid}"
        [[ -e "${marker}" ]] && return 0
        { mkdir -p "${marker%/*}" && : > "${marker}"; } \
            || log_warn "${HOOK}" "could not write ${marker}; the notice may repeat this session"
    fi
    fail_open_notice "${HOOK}" "ruff not found (forge .venv or an absolute PATH entry); .py edits are not formatted this session"
}

ruff=""
if [[ -x "${FORGE}/.venv/bin/ruff" ]]; then
    ruff="${FORGE}/.venv/bin/ruff"
else
    ruff=$(command -v ruff) || ruff=""
    [[ "${ruff}" == /* ]] || ruff=""
fi
if [[ -z "${ruff}" ]]; then
    notify_no_ruff
    exit 0
fi

# Fix first, then format: ruff's documented order, so autofix output is formatted too.
# why: `ruff check` exiting 1 only means lint remains, which the report below shows
"${ruff}" check --fix --unfixable F401,F841 --quiet -- "${f}" >/dev/null 2>&1
# Format exits non-zero only on syntax errors or bad config: that is a failure worth logging.
if ! out=$("${ruff}" format -- "${f}" 2>&1); then
    log_error "${HOOK}" "${f}: ${out//$'\n'/ | }"
fi

# why: exit 1 means findings, which is the point; ruff's own errors were logged by format above
findings=$("${ruff}" check --output-format concise --quiet -- "${f}" 2>/dev/null)
[[ -n "${findings}" ]] || exit 0
mapfile -t lines <<<"${findings}"
if (( ${#lines[@]} > MAX_CONTEXT_LINES )); then
    more=$(( ${#lines[@]} - MAX_CONTEXT_LINES + 1 ))
    lines=("${lines[@]:0:MAX_CONTEXT_LINES-1}" "… and ${more} more — run: ruff check ${f}")
fi
# why: jq's EPIPE message is replaced by the log_error line on failure
jq -cn 2>/dev/null --arg c "$(printf '%s\n' "${lines[@]}")" \
    '{hookSpecificOutput: {hookEventName: "PostToolUse", additionalContext: $c}}' \
    || log_error "${HOOK}" "could not write additionalContext for ${f} (stdout closed?)"
exit 0
