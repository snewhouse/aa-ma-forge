#!/usr/bin/env bash
# codemem + graphify post-commit step (M15.4, report 03 T4; M2 Task 2.5 origin).
#
# Wired in by `scripts/install.sh --wire-git-hook` (appends a guarded line to
# the repo's .git/hooks/post-commit). graphify's own post-commit hook is NOT
# used: it returns as soon as it spawns its rebuild, so a sidecar written
# beside it could claim fresh before (or without) the rebuild finishing.
#
# Contract:
# - Exit 0 always; never slows a commit. The hook captures HEAD, spawns a
#   detached worker (`--worker <sha> <repo>`) and returns.
# - Workers are serialised by flock on <git-dir>/codemem-post-commit.lock
#   (the git dir is never committed content). Each runs, in order:
#     1. `codemem refresh` + `codemem refresh-commits` (own writer lock;
#        errors in refresh.log);
#     2. `graphify update .` (code-only, no LLM);
#     3. on graphify exit 0 only, the SHA captured at commit time →
#        graphify-out/.built_sha (R03-D12). A failed or killed run leaves the
#        previous .built_sha, so the sidecar never claims a graph it lacks.
# - No-op during rebase / cherry-pick / revert / merge.
# - Every log line goes to refresh.log in the codemem index dir (aa_ma_codemem_dir:
#   the XDG cache, or $CODEMEM_DB's dir; M16); graphify absent = one notice.
# - Repo-controlled inputs stay inert: PATH keeps absolute entries only (a
#   relative entry would run a repo's ./graphify), codemem comes from this
#   forge's venv before PATH, and refresh.log / .built_sha are never written
#   through a symlink. A graphify-out that is or holds a symlink skips
#   graphify (it could write through the link); codemem refuses an index dir
#   that is or holds one itself. A stray
#   refresh.pid is no longer read: killing a PID from a repo-writable file
#   could kill any process of the user.
# - Bounded: each step runs under `timeout` (when present) and a worker waits
#   at most LOCK_WAIT_S for the queue, so a wedged step cannot hold it forever.

set -u

case "${GIT_REFLOG_ACTION:-}" in
    rebase*|cherry-pick*|revert*|merge*) exit 0 ;;
esac

PATH="$(printf '%s' "${PATH:-}" | tr ':' '\n' | grep '^/' | paste -sd: -)"
export PATH

SELF="$(readlink -f "${BASH_SOURCE[0]}" 2>/dev/null || printf '%s' "${BASH_SOURCE[0]}")"  # why: readlink -f is absent on old macOS; the invoked path still works
FORGE_ROOT="$(cd "$(dirname "${SELF}")/../../.." && pwd)"
SHA_RE='^([0-9a-f]{40}|[0-9a-f]{64})$'
# The slowest measured step is a cold `graphify update` (11.5 s on aa-ma-forge,
# M15.4); 300 s is ~25x that. A worker waits for one predecessor's three
# capped steps (codemem refresh, refresh-commits, graphify update) plus a
# minute of slack before giving up its turn.
STEP_TIMEOUT_S=300
CAPPED_STEPS=3
LOCK_WAIT_S=$((CAPPED_STEPS * STEP_TIMEOUT_S + 60))

log_line() {
    # One line to <index dir>/refresh.log, never through a symlink ($CODEMEM_DB may name a repo dir).
    local dir="${CM:-}" log
    if [[ -z "${dir}" ]]; then
        # No index dir (no realpath/sha256 tool): stderr is the only place left (§6.0 shows it).
        printf 'codemem post-commit: %s (no index dir to log to)\n' "$1" >&2
        return 0
    fi
    log="${dir}/refresh.log"
    [[ -L "${dir}" || -L "${log}" ]] && return 0
    mkdir -p "${dir}" 2>/dev/null || return 0  # why: an unwritable repo is not a reason to fail a commit
    printf '[%s] post-commit: %s\n' "$(date +%Y-%m-%dT%H:%M:%S%z)" "$1" >> "${log}" 2>/dev/null || true  # why: logging must never fail the worker
}

write_built_sha() {
    # Replace graphify-out/.built_sha with $1: temp file + mv, so a planted
    # symlink is replaced, never followed.
    local out="${REPO_ROOT}/graphify-out" tmp
    if [[ -L "${out}" || ! -d "${out}" ]]; then
        log_line "graphify-out is missing or a symlink: .built_sha not written"
        return 0
    fi
    if [[ -d "${out}/.built_sha" && ! -L "${out}/.built_sha" ]]; then
        log_line "graphify-out/.built_sha is a directory: not written"
        return 0
    fi
    if ! tmp="$(mktemp "${out}/.built_sha.XXXXXX" 2>/dev/null)"; then  # why: the failure is logged on the next line
        log_line "cannot create a temp file in graphify-out: .built_sha not written"
        return 0
    fi
    if ! { printf '%s\n' "$1" > "${tmp}" && rm -f -- "${out}/.built_sha" && mv -f -- "${tmp}" "${out}/.built_sha"; }; then
        log_line "cannot replace graphify-out/.built_sha: not written"
    fi
    rm -f -- "${tmp}"
}

capped() {
    # "$@" under timeout when present (absent on stock macOS); rc 124 = timed out.
    if command -v timeout > /dev/null 2>&1; then  # why: a presence probe
        timeout "${STEP_TIMEOUT_S}" "$@"
    else
        "$@"
    fi
}

refresh_codemem() {
    # CODEMEM_BIN (user env, like RUFF_BIN) pins the binary with no fallback.
    local codemem
    if ! codemem="$(aa_ma_codemem_bin "${FORGE_ROOT}")"; then
        log_line "codemem not found: index not refreshed"
        return 0
    fi
    # why: codemem refresh logs its own errors to refresh.log; its stdout is a summary nobody reads
    capped "${codemem}" refresh > /dev/null 2>&1 || log_line "codemem refresh exited $? (75 = another refresh held the lock; 124 = timed out after ${STEP_TIMEOUT_S}s)"
    # why: as above; the git-mining cache (co_changes, hot_spots) follows the commit too
    capped "${codemem}" refresh-commits > /dev/null 2>&1 || log_line "codemem refresh-commits exited $? (124 = timed out after ${STEP_TIMEOUT_S}s)"
}

run_worker() {
    local sha="$1" lock graphify rc
    [[ "${sha}" =~ ${SHA_RE} ]] || exit 0
    cd "${REPO_ROOT}" || exit 0
    lock="$(git rev-parse --absolute-git-dir 2>/dev/null)/codemem-post-commit.lock" || exit 0  # why: not a repo any more → nothing to refresh
    # Inherited from the git hook, these would point git (and codemem's git
    # calls) at the commit-time index; the worker outlives that.
    unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_PREFIX

    # Without flock (stock macOS) codemem still refreshes — its own db.lock
    # serialises it — and only the graph step, which needs the queue, is skipped.
    if ! command -v flock > /dev/null 2>&1; then  # why: a presence probe; the branch logs the outcome
        refresh_codemem
        log_line "flock not found: graph refresh skipped (cannot serialise; .built_sha unchanged)"
        exit 0
    fi
    if ! { exec 9>> "${lock}"; } 2>/dev/null; then  # why: the failure is logged on the next line
        log_line "cannot open ${lock##*/}: refresh skipped"
        exit 0
    fi
    if ! flock -w "${LOCK_WAIT_S}" 9; then
        log_line "flock on ${lock##*/} failed or waited ${LOCK_WAIT_S}s: refresh skipped"
        exit 0
    fi
    refresh_codemem

    graphify="$(command -v graphify || true)"  # why: absent is handled (and logged) below
    if [[ -z "${graphify}" ]]; then
        log_line "graphify not found: code graph not refreshed (.built_sha unchanged)"
        exit 0
    fi
    if [[ -L graphify-out ]]; then
        log_line "graphify-out is a symlink: code graph not refreshed (.built_sha unchanged)"
        exit 0
    fi
    # why: find's own errors (an unreadable subdir) are not a reason to fail the worker; any output refuses
    if [[ -d graphify-out && -n "$(find graphify-out -type l -print -quit 2>/dev/null)" ]]; then
        log_line "graphify-out holds a symlink: code graph not refreshed (.built_sha unchanged)"
        exit 0
    fi
    # why: graphify output carries repo text; only its exit code is logged
    capped "${graphify}" update . > /dev/null 2>&1
    rc=$?
    if [[ "${rc}" -eq 124 ]]; then
        log_line "graphify update timed out after ${STEP_TIMEOUT_S}s: .built_sha kept"
        exit 0
    elif [[ "${rc}" -ne 0 ]]; then
        log_line "graphify update failed (rc ${rc}): .built_sha kept"
        exit 0
    fi
    write_built_sha "${sha}"
    exit 0
}

if [[ "${1:-}" == "--worker" ]]; then
    REPO_ROOT="${3:-}"
    [[ -n "${REPO_ROOT}" && -d "${REPO_ROOT}" ]] || exit 0
    # This forge's helpers, never the target repo's copy (it would run inside the hook).
    # Loaded here, not at the top: the committing user never waits for them.
    # shellcheck source=/dev/null
    if ! . "${FORGE_ROOT}/claude-code/hooks/lib/aa-ma-parse.sh"; then
        printf 'codemem post-commit: %s missing — index not refreshed\n' "${FORGE_ROOT}/claude-code/hooks/lib/aa-ma-parse.sh" >&2
        exit 0
    fi
    CM="$(aa_ma_codemem_dir "${REPO_ROOT}")" || CM=""
    run_worker "${2:-}"
fi

# why: outside a repo or before the first commit there is nothing to refresh, and a hook must stay silent
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
HEAD_SHA="$(git rev-parse HEAD 2>/dev/null)" || exit 0  # why: no commit yet → nothing to refresh
[[ "${HEAD_SHA}" =~ ${SHA_RE} ]] || exit 0

# why: the worker is detached; its output must not reach the committing terminal (it logs to refresh.log)
if command -v setsid > /dev/null 2>&1; then
    setsid bash "${SELF}" --worker "${HEAD_SHA}" "${REPO_ROOT}" < /dev/null > /dev/null 2>&1 &  # why: detached worker; it logs to refresh.log
else
    bash "${SELF}" --worker "${HEAD_SHA}" "${REPO_ROOT}" < /dev/null > /dev/null 2>&1 &  # why: detached worker; it logs to refresh.log
fi
exit 0
