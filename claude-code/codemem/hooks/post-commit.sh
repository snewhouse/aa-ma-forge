#!/usr/bin/env bash
# codemem post-commit hook (M1 Task 1.11).
#
# Wired in by `scripts/install.sh --wire-git-hook` (option (a): appends a
# guarded line to the repo's .git/hooks/post-commit). M2 Task 2.5 replaces
# the body with the setsid + PID-file + log-rotation dance; M1 ships the
# visible skeleton so we can verify wiring in the AC test.
#
# Contract (per codemem-reference.md):
# - Exit 0 always. Never fail a commit.
# - Log errors to .codemem/refresh.log — never print to stderr of the
#   calling git process.
# - No-op during rebase / cherry-pick / bisect (GIT_DIR variable set
#   differently; skip).
# - Idempotent: re-running against the same commit state does nothing
#   meaningful.

set -u

# Skip during non-interactive git operations that we don't want to
# trigger a refresh on. M2 will expand this list.
case "${GIT_REFLOG_ACTION:-}" in
    rebase*|cherry-pick*|revert*|merge*) exit 0 ;;
esac

# Locate the codemem CLI. Prefer a venv-installed entry point; fall
# back to `python -m codemem.cli` if `codemem` isn't on PATH. This
# keeps the hook useful even when the user hasn't activated the venv.
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

# Fire refresh in the background so git commit returns immediately.
# Redirect both streams to the log; never leak to stdout/stderr of
# the parent shell (would pollute `git commit -qm ...`).
{
    "${CODEMEM_CMD[@]}" refresh
} >>"${LOG}" 2>&1 &

exit 0
