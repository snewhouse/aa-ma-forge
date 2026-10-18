#!/usr/bin/env bash
# aa-ma-log.sh — logging library for AA-MA hooks: one masked line per call to hooks.log.
#
# Source this file (don't execute it). aa-ma-parse.sh sources it, so every AA-MA hook has it.
#
# Exports:
#     log_info|log_warn|log_error <hook-name> <msg> -> append "<date -Is> LEVEL <hook-name>: <msg>"
#     log_debug <hook-name> <msg>                   -> the same at DEBUG, only when HOOK_DEBUG=1; also to stderr
#     fail_open_notice <hook-name> <msg>            -> stdout {"systemMessage": "<hook-name>: <msg>"} + a WARN line
#     mask_secrets <text>                           -> stdout: <text> capped, control characters → space, secrets → [REDACTED:<rule id>]
#     AA_MA_LOG_SH_LOADED                           -> set to 1 once sourced (re-source guard)
#
# Log file: ${CLAUDE_HOOK_LOG:-$HOME/.claude/logs/hooks.log} (the logging-and-comments contract);
# with neither set, lines go to stderr — never to a shared directory.
# Patterns: src/aa_ma/secret_patterns.tsv in the forge checkout — the same file aa_ma.logsetup
# reads — found through this file's real path, since install.sh symlinks it into ~/.claude.
# They load on the first mask, not at source time: most hook runs never log, and the path
# resolve costs a fork on every tool call. If the patterns cannot be read, or a line is not
# exactly <id><TAB><regex>, every message becomes "[redaction failed]": fail closed.
#
# Why fail_open_notice is the only thing on stdout: hook stdout is parsed as JSON, and stderr on
# exit 0 is never shown to the user (L-1319), so a notice the user must see is a systemMessage.
# Nothing here may fail its caller: hooks run under `set -e`, often with stdout or stderr closed
# (EPIPE), so every write has a fallback and every function returns 0.

# shellcheck disable=SC2317  # why: `return` / `exit` fallback both unreachable by design
if [ "${AA_MA_LOG_SH_LOADED:-0}" = "1" ]; then
    return 0 2>/dev/null || exit 0   # why: `return` when sourced, `exit` if run directly
fi
AA_MA_LOG_SH_LOADED=1

# Redaction input cap, in characters (≈8 KB): bounds regex work on hostile input (plan §0 v2).
_AA_MA_LOG_MAX_CHARS=8192
# Extra characters masked past the cap before truncating, so a secret that straddles the
# cut is masked whole instead of leaving an unmatched fragment (same as aa_ma.logsetup).
_AA_MA_LOG_CAP_OVERLAP=256
_AA_MA_SECRET_IDS=()
_AA_MA_SECRET_RES=()
_AA_MA_SECRET_PATTERNS_OK=0
_AA_MA_SECRET_PATTERNS_TRIED=0

# Loads the pattern file into the two arrays, once; sets _AA_MA_SECRET_PATTERNS_OK=1 only on success.
_aa_ma_log_load_patterns() {
    [ "${_AA_MA_SECRET_PATTERNS_TRIED}" = "1" ] && return 0
    _AA_MA_SECRET_PATTERNS_TRIED=1
    local real file id re ids=() res=()
    # why: no `readlink -f` on macOS < 12.3; the fallback below takes over
    real="$(readlink -f "${BASH_SOURCE[0]}" 2>/dev/null)" || real=""
    # why: one-level readlink (install.sh links straight to the forge file), else the path as sourced
    [ -n "${real}" ] || real="$(readlink "${BASH_SOURCE[0]}" 2>/dev/null)" || real="${BASH_SOURCE[0]}"
    file="${real%/*/*/*/*}/src/aa_ma/secret_patterns.tsv"   # <forge>/claude-code/hooks/lib/<this>
    [ -r "${file}" ] || return 0
    while IFS=$'\t' read -r id re; do
        case "${id}" in '' | '#'*) continue ;; esac
        # a rule with no regex, or a second tab: treat the whole file as unreadable
        [[ -n "${re}" && "${re}" != *$'\t'* ]] || return 0
        ids+=("${id}")
        res+=("${re}")
    done < "${file}"
    [ "${#ids[@]}" -gt 0 ] || return 0
    _AA_MA_SECRET_IDS=("${ids[@]}")
    _AA_MA_SECRET_RES=("${res[@]}")
    _AA_MA_SECRET_PATTERNS_OK=1
}

# _aa_ma_log_oneline <text> — <text> cut to the masking window, every control character
# (CR, LF, ESC, BEL, …, and the C1 range such as U+009B CSI) turned into a space. Hook
# messages quote repo-controlled names; an escape sequence in one would otherwise reach
# the terminal from the log or a systemMessage.
_aa_ma_log_oneline() {
    local text="${1-}"
    text="${text:0:$((_AA_MA_LOG_MAX_CHARS + _AA_MA_LOG_CAP_OVERLAP))}"   # chars, in the caller's locale
    # why: bytes from here on — [[:cntrl:]] matches U+009B in some UTF-8 locales only;
    # C1 in UTF-8 is 0xC2 0x80-0x9F, and a lone 0x80-0x9F byte may be part of a valid character
    local LC_ALL=C
    text="${text//[[:cntrl:]]/ }"
    printf '%s\n' "${text//$'\xc2'[$'\x80'-$'\x9f']/ }"
}

mask_secrets() {
    local text i re
    text="$(_aa_ma_log_oneline "${1-}")"
    _aa_ma_log_load_patterns
    if [ "${_AA_MA_SECRET_PATTERNS_OK}" != "1" ]; then
        printf '%s\n' "[redaction failed]"
        return 0
    fi
    for i in "${!_AA_MA_SECRET_RES[@]}"; do
        re="${_AA_MA_SECRET_RES[${i}]}"
        while [[ "${text}" =~ ${re} ]] && [ -n "${BASH_REMATCH[0]}" ]; do
            text="${text/"${BASH_REMATCH[0]}"/"[REDACTED:${_AA_MA_SECRET_IDS[${i}]}]"}"
        done
    done
    printf '%s\n' "${text:0:${_AA_MA_LOG_MAX_CHARS}}"
}

# _aa_ma_log <LEVEL> <hook-name> <msg> — the one writer behind every log_* function.
_aa_ma_log() {
    local level="$1" hook msg log dir line ts
    hook="$(_aa_ma_log_oneline "${2-}")"
    hook="${hook:0:${_AA_MA_LOG_MAX_CHARS}}"
    msg="$(mask_secrets "${3-}")"
    log="${CLAUDE_HOOK_LOG:-}"
    [ -n "${log}" ] || [ -z "${HOME:-}" ] || log="${HOME}/.claude/logs/hooks.log"
    # why: `date -Is` is GNU; BSD/macOS may reject it. A failed stamp must never abort a set -e hook.
    ts="$(date -Is 2>/dev/null)" || ts="$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null)" || ts="unknown-time"
    line="${ts} ${level} ${hook}: ${msg}"
    if [ -z "${log}" ]; then
        # HOME unset (cron, env -i) and no CLAUDE_HOOK_LOG: there is no private place to write. Never
        # fall back to a shared dir such as /tmp, where a planted symlink would redirect the append.
        printf '%s\n' "${line}" >&2 2>/dev/null || :   # why: stderr may be closed; must not trip set -e
        return 0
    fi
    dir="${log%/*}"
    [ "${dir}" = "${log}" ] && dir=.
    # why: the shell's own redirection error is replaced by the one-line notice that follows
    # umask 077 in a subshell: a new hooks.log is 600 in a 700 dir; an existing file keeps its mode
    ( umask 077; { [ -d "${dir}" ] || mkdir -p "${dir}"; } && printf '%s\n' "${line}" >> "${log}" ) 2>/dev/null \
        || printf 'aa-ma-log: cannot append to %s\n' "${log}" >&2 2>/dev/null || :   # why: stderr may be closed; must not trip set -e
    if [ "${level}" = "DEBUG" ]; then
        printf '%s\n' "${line}" >&2 2>/dev/null || :   # why: debug echo is best-effort; the log line is the record
    fi
    return 0
}

log_info()  { _aa_ma_log INFO "${1-}" "${2-}"; }
log_warn()  { _aa_ma_log WARN "${1-}" "${2-}"; }
log_error() { _aa_ma_log ERROR "${1-}" "${2-}"; }
log_debug() {
    [ "${HOOK_DEBUG:-0}" = "1" ] || return 0
    _aa_ma_log DEBUG "${1-}" "${2-}"
}

fail_open_notice() {
    local hook msg
    log_warn "${1-}" "${2-}"   # masks and caps on its own; the masked copy below is for stdout
    hook="$(_aa_ma_log_oneline "${1-}")"
    hook="${hook:0:${_AA_MA_LOG_MAX_CHARS}}"
    msg="$(mask_secrets "${2-}")"
    # why: `command -v` prints the path on success; only its status is wanted
    if command -v jq >/dev/null 2>&1; then
        # why: jq's own EPIPE message is replaced by the log_error line on failure
        jq -cn --arg m "${hook}: ${msg}" '{systemMessage: $m}' 2>/dev/null \
            || log_error aa-ma-log "could not write the systemMessage for ${hook} (stdout closed?)"
    else
        log_error aa-ma-log "jq not on PATH; ${hook} notice replaced by a fixed systemMessage"
        # why: a closed stdout is reported by the log_error line that follows, not by the shell
        printf '%s\n' '{"systemMessage": "AA-MA hook notice: jq is missing; see ~/.claude/logs/hooks.log"}' 2>/dev/null \
            || log_error aa-ma-log "could not write the systemMessage for ${hook} (stdout closed?)"
    fi
    return 0
}
