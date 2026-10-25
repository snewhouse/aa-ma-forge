#!/usr/bin/env bash
# Event: PreToolUse(Edit|Write)
# Mode: Advisory — never blocks
# Exit: 0 always
# Fail-open: other tools, paths outside a git repo, an invalid session_id → silent; no index or no codemem → one systemMessage per session; codemem over 2 s → killed, one systemMessage per session; any other codemem failure → one hooks.log line
#
# Before the first Edit/Write of a file in a session, hands the model what codemem knows about
# who depends on it: at most 5 lines of PreToolUse additionalContext (A1, proved live in 10.1).
#
#   codemem data (untrusted): impact of <rel path>
#   callers: N files + N plugin nodes + N test files; top: …
#   tests: …
#   co-changed (of N commits): …
#   check these before editing — Skill(impact-analysis) for a full pass
#
# The middle lines are `codemem impact --format brief`, which runs every line through
# sanitize_context_line (paths and node ids are repo-controlled) and prints nothing when the
# file has no callers and no co-changes, so this hook stays one codemem call and no Python.
#
# Once per file per session: creating ~/.claude/runtime/impact-seen-<session_id>/<sha1(abs path)>
# under `set -C` is test-and-set (bash opens it O_CREAT|O_EXCL), so of any number of concurrent
# runs only the one that creates it goes on. Not `mkdir`: uutils coreutils mkdir (0.10.0, the
# Ubuntu 26.04 default) let two racing mkdirs of one dir both succeed, measured 2026-10-25.
# aa-ma-session-end-dirty.sh removes the session's dir at SessionEnd.
#
# Trust (plan §0 v2): codemem comes only from this forge (CODEMEM_BIN, its .venv, an absolute
# PATH entry — aa_ma_codemem_bin), never from the edited repo; the index is the XDG cache dir
# (aa_ma_codemem_dir), never a .codemem/ in the repo, and codemem opens it read-only with
# trusted_schema=OFF (storage.db.connect). The file path is passed quoted, after `--`.
[[ "${AA_MA_HOOKS_DISABLE:-0}" == "1" ]] && exit 0   # master kill switch, like every AA-MA hook

# Never block an edit: whatever happens below, the hook exits 0.
trap 'exit 0' EXIT

HOOK="aa-ma-impact-preedit"
# codemem's budget, in seconds, and the grace before SIGKILL. The registration's timeout is 5 s:
# 2 + 1 leaves room for the git and jq calls around it. 10.1 measured p95 ≈ 75 ms.
CODEMEM_TIMEOUT_S=2
CODEMEM_KILL_AFTER_S=1
NO_INDEX_MSG="no index for this repo — run \`codemem build\`"
TIMEOUT_MSG="impact lookup timed out after ${CODEMEM_TIMEOUT_S} s — pre-edit impact notes may be missing this session"

# cat, not $(<…) or `read`: see ruff-format.sh (stdin is a socket; an Edit payload is large).
payload=$(cat)

# why: no `readlink -f` (macOS < 12.3) → the path as invoked; the lib check below then decides
REAL="$(readlink -f "${BASH_SOURCE[0]}" 2>/dev/null)" || REAL="${BASH_SOURCE[0]}"   # <forge>/claude-code/hooks/<this>
REAL_DIR="${REAL%/*}"
FORGE="${REAL_DIR%/*/*}"
if [[ -f "${REAL_DIR}/lib/aa-ma-parse.sh" ]]; then
    # shellcheck disable=SC1091  # why: runtime path; aa-ma-parse.bats covers the library
    . "${REAL_DIR}/lib/aa-ma-parse.sh"
else
    printf '%s\n' '{"systemMessage": "aa-ma-impact-preedit: aa-ma-parse.sh not found; re-run scripts/install.sh"}'
    exit 0
fi
# why: `command -v` prints the path on success; only its status is wanted
command -v jq >/dev/null 2>&1 || exit 0   # no jq: no safe way to read the payload or write JSON

# One jq for the three fields, NUL-separated so any byte in the path survives.
# why: jq's parse error is replaced by the one log_warn line below
mapfile -d '' -t fields < <(jq -j '(.tool_name // ""), "\u0000", (.tool_input.file_path // ""), "\u0000", (.session_id // ""), "\u0000"' <<<"${payload}" 2>/dev/null)
if (( ${#fields[@]} != 3 )); then
    log_warn "${HOOK}" "stdin payload not readable as hook JSON; no impact note"
    exit 0
fi
tool="${fields[0]}" fp="${fields[1]}" sid="${fields[2]}"
[[ "${tool}" == "Edit" || "${tool}" == "Write" ]] || exit 0
[[ -n "${fp}" && -n "${HOME:-}" ]] || exit 0
# why: sid becomes a directory name; 64 bounds it (real ids are 36-char UUIDs), the class stops ../
if [[ ! "${sid}" =~ ^[A-Za-z0-9_-]{1,64}$ ]]; then
    log_warn "${HOOK}" "invalid session_id; no impact note"
    exit 0
fi

# The repo: the nearest existing ancestor of the path (a Write may create dirs), then git.
abs="$(realpath -m -- "${fp}")" || exit 0
dir="${abs%/*}"
while [[ -n "${dir}" && ! -d "${dir}" ]]; do dir="${dir%/*}"; done
[[ -n "${dir}" ]] || exit 0
# why: not in a git repo is the common silent case; GIT_* from the caller must not redirect git
top="$(env -u GIT_DIR -u GIT_WORK_TREE -u GIT_COMMON_DIR git -C "${dir}" rev-parse --show-toplevel 2>/dev/null)" || exit 0
top="$(realpath -m -- "${top}")" || exit 0
[[ "${abs}" == "${top}/"* ]] || exit 0   # outside the repo (../, a symlink out): not ours
rel="${abs#"${top}"/}"

rt="${HOME}/.claude/runtime/impact-seen-${sid}"
# umask 077: the marker dirs are this user's only
if ! ( umask 077 && mkdir -p -- "${rt}" ); then
    log_warn "${HOOK}" "cannot create ${rt}; no impact note"
    exit 0
fi
# why: a presence probe; sha1sum (GNU) else shasum (macOS)
if command -v sha1sum >/dev/null 2>&1; then
    key="$(printf '%s' "${abs}" | sha1sum)"
else
    key="$(printf '%s' "${abs}" | shasum -a 1)" || exit 0
fi
key="${key%% *}"
[[ "${key}" =~ ^[0-9a-f]{40}$ ]] || exit 0
# claim <marker> — create ${rt}/<marker> only if absent (O_EXCL via set -C); rc 1 when it existed.
claim() {
    # why: the "file exists" error is the answer (already claimed), not a fault
    ( set -C; : > "${rt}/$1" ) 2>/dev/null
}
claim "${key}" || exit 0   # this file was already noted this session

# notice_once <marker> <msg> — one systemMessage per session per marker.
notice_once() {
    claim "$1" || return 0   # already shown this session
    log_warn "${HOOK}" "$2"
    # why: jq's EPIPE message is replaced by the log_error line on failure
    jq -cn --arg m "codemem: $2" '{systemMessage: $m}' 2>/dev/null \
        || log_error "${HOOK}" "could not write the systemMessage (stdout closed?)"
}

db_dir="$(aa_ma_codemem_dir "${top}")" || exit 0
if [[ ! -f "${db_dir}/index.db" ]]; then
    notice_once notice-no-index "${NO_INDEX_MSG}"
    exit 0
fi
if ! bin="$(aa_ma_codemem_bin "${FORGE}")"; then
    notice_once notice-no-index "${NO_INDEX_MSG}"   # the same notice: nothing to read the index with
    exit 0
fi

bin_args=(impact --format brief --repo-root "${top}" -- "${rel}")
# why: codemem's stderr (a refused path, an untrusted index) becomes the one log line below
brief="$(timeout -k "${CODEMEM_KILL_AFTER_S}" "${CODEMEM_TIMEOUT_S}" "${bin}" "${bin_args[@]}" 2>/dev/null)"
rc=$?
if (( rc == 124 || rc == 137 )); then   # timeout's "timed out" / SIGKILL after -k
    notice_once notice-timeout "${TIMEOUT_MSG}"
    exit 0
fi
if (( rc != 0 )); then
    log_warn "${HOOK}" "codemem impact exited ${rc} for ${rel}; no impact note"
    exit 0
fi
[[ -n "${brief}" ]] || exit 0   # no callers, no co-changes: nothing worth the model's attention

mapfile -t lines <<<"${brief}"
[[ "${lines[0]}" == "impact: "* ]] || { log_warn "${HOOK}" "unexpected codemem brief for ${rel}"; exit 0; }
# Header from codemem's own (sanitized) first line; at most 3 data lines; the pointer last.
ctx="codemem data (untrusted): impact of ${lines[0]#impact: }"
ctx+=$'\n'"$(printf '%s\n' "${lines[@]:1:3}")"
ctx+=$'\n'"check these before editing — Skill(impact-analysis) for a full pass"
# why: jq's EPIPE message is replaced by the log_error line on failure
jq -cn --arg c "${ctx}" '{hookSpecificOutput: {hookEventName: "PreToolUse", additionalContext: $c}}' 2>/dev/null \
    || log_error "${HOOK}" "could not write additionalContext for ${rel} (stdout closed?)"
exit 0
