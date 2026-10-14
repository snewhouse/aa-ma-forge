#!/usr/bin/env bash
# §6.0 code-intel refresh — CODE_INTEL_REFRESH (code-conventions-impact M15.6, report 03 T6).
#
# Usage: code-intel-refresh.sh <task-name> [--dry-run]     (run from the repo top)
# Exit:  0 refreshed; the line is appended (or, with --dry-run, printed)
#        1 BLOCKED: bad task name, unsafe provenance path, unreadable milestone,
#          a symlinked .codemem/, or a codemem index that exists but did not reach HEAD
#
# Runs the 15.4 post-commit worker synchronously (same flock as post-commit runs;
# codemem refresh + refresh-commits, `graphify update .` code-only, start-SHA
# .built_sha) for the PRE-commit HEAD, then records
#   [ts] CODE_INTEL_REFRESH — <milestone heading> — codemem=<sha|skipped(no index)> graphify=<sha|WARN reason>
# A file cannot name the commit that contains it, so the line names the HEAD the
# milestone commit will sit on. graphify is leads-only: it WARNs, never blocks (R03-D7).

set -uo pipefail

blocked() {
    printf 'BLOCKED: %s\n' "$*"
    exit 1
}

TASK_NAME="${1:-}"
DRY_RUN=0
[[ "${2:-}" == "--dry-run" ]] && DRY_RUN=1
if ! [[ "${TASK_NAME}" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ && "${TASK_NAME}" != *..* ]]; then
    blocked "TASK_NAME must be a plain task slug (got '${TASK_NAME}')."
fi
TASK_DIR=".claude/dev/active/${TASK_NAME}"
PROV="${TASK_DIR}/${TASK_NAME}-provenance.log"
# The line carries the repo's own heading text: never append it through a symlink.
for _p in .claude .claude/dev .claude/dev/active "${TASK_DIR}" "${PROV}"; do
    [[ -L "${_p}" ]] && blocked "${_p} is a symlink; refusing to write provenance through it."
done
[[ ! -e "${PROV}" || -f "${PROV}" ]] || blocked "${PROV} is not a regular file."

TOP="$(git rev-parse --show-toplevel 2>/dev/null)" || blocked "not inside a git repo."  # why: git's message is replaced by this one
HEAD_SHA="$(git rev-parse HEAD 2>/dev/null)" || blocked "no HEAD commit."  # why: as above
[[ "${HEAD_SHA}" =~ ^([0-9a-f]{40}|[0-9a-f]{64})$ ]] || blocked "HEAD is not a 40- or 64-hex SHA."

SELF="$(readlink -f "${BASH_SOURCE[0]}" 2>/dev/null || printf '%s' "${BASH_SOURCE[0]}")"  # why: readlink -f is absent on old macOS; the invoked path still works
FORGE="$(cd "$(dirname "${SELF}")/../../../.." && pwd)"
WORKER="${FORGE}/claude-code/codemem/hooks/post-commit.sh"
[[ -f "${WORKER}" ]] || blocked "post-commit.sh not found at ${WORKER} — run scripts/install.sh."

# This script's own forge, never the target repo's tree: a repo that commits
# claude-code/hooks/lib/aa-ma-parse.sh would otherwise run inside the gate.
AA_MA_LIB="${FORGE}/claude-code/hooks/lib/aa-ma-parse.sh"
[[ -f "${AA_MA_LIB}" ]] || blocked "aa-ma-parse.sh not found at ${AA_MA_LIB} — run scripts/install.sh."
# shellcheck source=/dev/null
. "${AA_MA_LIB}"
GATE_KV=$(aa_ma_gate "${TASK_DIR}/${TASK_NAME}-tasks.md") || {
    printf '%s\n' "${GATE_KV}" | sed -n 's/^error=/  - /p'
    blocked "cannot read the milestone being refreshed."
}
HEADING=$(printf '%s\n' "${GATE_KV}" | aa_ma_gate_field heading)
[[ -n "${HEADING}" ]] || blocked "empty milestone heading."

# Repo-controlled: codemem refuses a .codemem that is or holds a symlink, so its
# sidecar could only lie, and "run codemem build" would not help. A dangling
# index.db link is one too (it fails -e and would read as "no index").
if [[ -L "${TOP}/.codemem" ]] || { [[ -d "${TOP}/.codemem" ]] && [[ -n "$(find "${TOP}/.codemem" -maxdepth 1 -type l -print -quit 2>/dev/null)" ]]; }; then  # why: find errors on an unreadable dir; codemem then refuses it too, caught below
    blocked ".codemem is or holds a symlink; codemem refuses to index through one. Remove the link, run \`codemem build\`, then re-run."
fi

# The worker always exits 0; the sidecars say what it achieved.
bash "${WORKER}" --worker "${HEAD_SHA}" "${TOP}"

# Sidecars are read only through aa_ma_read_sidecar_sha: never through a link (§6.8 C2).
if [[ -e "${TOP}/.codemem/index.db" ]]; then
    [[ "$(aa_ma_read_sidecar_sha "${TOP}/.codemem/last_sha")" == "${HEAD_SHA}" ]] \
        || blocked "the codemem index did not reach HEAD ${HEAD_SHA:0:12}. If .codemem/refresh.log says another refresh held db.lock (exit 75), wait and re-run; if it names an error, run \`codemem build\`, then re-run."
    CODEMEM="${HEAD_SHA}"
else
    CODEMEM="skipped(no index)"
fi

if [[ "$(aa_ma_read_sidecar_sha "${TOP}/graphify-out/.built_sha")" == "${HEAD_SHA}" ]]; then
    GRAPHIFY="${HEAD_SHA}"
elif ! command -v graphify > /dev/null 2>&1; then  # why: a presence probe
    GRAPHIFY="WARN graphify not found"
else
    GRAPHIFY="WARN not refreshed (see .codemem/refresh.log)"
fi

LINE="[$(date -Iseconds)] CODE_INTEL_REFRESH — ${HEADING} — codemem=${CODEMEM} graphify=${GRAPHIFY}"
if [[ "${DRY_RUN}" -eq 1 ]]; then
    printf '%s\n' "${LINE}"
    exit 0
fi
[[ ! -L "${PROV}" && ( ! -e "${PROV}" || -f "${PROV}" ) ]] \
    || blocked "${PROV} became a symlink or a non-file during the run; nothing written."
printf '%s\n' "${LINE}" >> "${PROV}" || blocked "cannot write ${PROV}."
printf '%s\n' "${LINE}"
