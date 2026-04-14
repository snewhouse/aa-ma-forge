#!/usr/bin/env bash
# codemem post-commit hook (M2 Task 2.5 — upgraded from M1 Task 1.11).
#
# Wired in by `scripts/install.sh --wire-git-hook` (option (a): appends a
# guarded line to the repo's .git/hooks/post-commit).
#
# Contract (per codemem-reference.md):
# - Exit 0 always. Never fail a commit.
# - Log errors to .codemem/refresh.log — never print to stderr of the
#   calling git process.
# - No-op during rebase / cherry-pick / revert / merge
#   (GIT_REFLOG_ACTION prefix check).
# - Single active refresh at a time: storm of rapid commits
#   (e.g. `git commit --amend` x5 in <1s) must leave only one process
#   actively indexing. Achieved via `.codemem/refresh.pid` + `setsid`:
#     1. If a PID exists and is still alive, kill its entire process
#        group (via `kill -- -<pgid>`) before starting a new one.
#     2. Spawn the new refresh via `setsid` so it has its own process
#        group (clean boundary for future kill).
#     3. Record the new PID.

set -u

# Skip non-user commits.
case "${GIT_REFLOG_ACTION:-}" in
    rebase*|cherry-pick*|revert*|merge*) exit 0 ;;
esac

# Locate the codemem CLI. Prefer a venv-installed entry point; fall
# back to `python3 -m codemem.cli` if `codemem` isn't on PATH so the
# hook works even outside an activated venv.
if command -v codemem >/dev/null 2>&1; then
    CODEMEM_CMD=(codemem)
elif command -v python3 >/dev/null 2>&1; then
    CODEMEM_CMD=(python3 -m codemem.cli)
else
    exit 0
fi

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
DB_DIR="${REPO_ROOT}/.codemem"
mkdir -p "${DB_DIR}"
LOG="${DB_DIR}/refresh.log"
PID_FILE="${DB_DIR}/refresh.pid"

# --- Kill previous refresh if still running --------------------------
# A storm of `git commit --amend` calls would otherwise pile up N
# concurrent refreshes competing for the DB lock; we want exactly one
# active at a time.
if [ -f "${PID_FILE}" ]; then
    OLD_PID="$(cat "${PID_FILE}" 2>/dev/null || true)"
    if [ -n "${OLD_PID}" ] && kill -0 "${OLD_PID}" 2>/dev/null; then
        # Kill the ENTIRE process group (refresh may have spawned
        # subprocesses: sg scan, python, etc.). The leading `-`
        # targets the group, not just the leader.
        kill -- -"${OLD_PID}" 2>/dev/null || kill "${OLD_PID}" 2>/dev/null || true
        # Give it a moment to exit cleanly before we write the new PID.
        sleep 0.05
    fi
fi

# --- Spawn the new refresh in its own process group ------------------
# `setsid` creates a new session (and hence a new process group with
# PGID == child PID). `&` backgrounds the child so git commit returns
# immediately. Redirect everything to the log so stdout/stderr can't
# leak to the parent shell.
if command -v setsid >/dev/null 2>&1; then
    setsid "${CODEMEM_CMD[@]}" refresh >>"${LOG}" 2>&1 < /dev/null &
else
    # macOS default shell lacks setsid; fall back to plain background
    # spawn. The process-group kill above still mostly works via the
    # child's own PID as PGID when it's the session leader.
    "${CODEMEM_CMD[@]}" refresh >>"${LOG}" 2>&1 < /dev/null &
fi

CHILD_PID=$!
printf '%s\n' "${CHILD_PID}" > "${PID_FILE}"

exit 0
