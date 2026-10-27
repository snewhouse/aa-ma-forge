# shellcheck shell=bash
# fence-common.sh — the shared start of the §6.7 fence scripts (sourced, never run).
#
# tests-verified.sh (fence 3) and impact-verified.sh (fence 4) both: refuse a task name that is
# not a plain slug, refuse to append provenance through a symlink, load aa-ma-parse.sh
# (repo-local first, then the installed copy) and read the milestone they certify from the
# Python SSoT gate. One copy here so the two fences cannot drift (M11 §6.6).
#
# Usage (cwd: the repository top level):
#   . "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/fence-common.sh"
#   fence_init <task-name> <what this fence verifies>
# Sets TASK_NAME TASK_DIR PROV GATE_KV MILESTONE_TITLE MILESTONE_NUMBER, or BLOCKs (exit 1).

blocked() {
    printf 'BLOCKED: %s\n' "$*"
    exit 1
}

fence_init() {
    TASK_NAME="${1:-}"
    local what="${2:-the milestone}" _p _cand _rc _top
    if ! [[ "${TASK_NAME}" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ && "${TASK_NAME}" != *..* ]]; then
        blocked "TASK_NAME must be a plain task slug (got '${TASK_NAME}')."
    fi
    TASK_DIR=".claude/dev/active/${TASK_NAME}"
    PROV="${TASK_DIR}/${TASK_NAME}-provenance.log"

    # The append target must be a regular file reached through no symlink. A committed link
    # would redirect the line — which carries the repo's own heading text — into, say, ~/.bashrc.
    for _p in .claude .claude/dev .claude/dev/active "${TASK_DIR}" "${PROV}"; do
        [[ -L "${_p}" ]] && blocked "${_p} is a symlink; refusing to write provenance through it."
    done
    [[ ! -e "${PROV}" || -f "${PROV}" ]] || blocked "${PROV} is not a regular file."

    _top=$(git rev-parse --show-toplevel 2>/dev/null)  # why: outside a repo the first candidate is simply absent
    for _cand in \
        "${_top}/claude-code/hooks/lib/aa-ma-parse.sh" \
        "${CLAUDE_HOME:-${HOME}/.claude}/hooks/lib/aa-ma-parse.sh"; do
        [[ -f "${_cand}" ]] && AA_MA_LIB="${_cand}" && break
    done
    [[ -n "${AA_MA_LIB:-}" ]] || blocked "aa-ma-parse.sh not found — run scripts/install.sh."
    # shellcheck source=/dev/null
    . "${AA_MA_LIB}"
    GATE_KV=$(aa_ma_gate "${TASK_DIR}/${TASK_NAME}-tasks.md") || {
        _rc=$?
        printf '%s\n' "${GATE_KV:-}" | sed -n 's/^error=/  - /p'
        blocked "cannot read the milestone to verify ${what} (gate rc ${_rc})."
    }
    MILESTONE_TITLE=$(printf '%s\n' "${GATE_KV}" | aa_ma_gate_field heading)
    MILESTONE_NUMBER=$(printf '%s\n' "${GATE_KV}" | aa_ma_gate_field number)
    [[ -n "${MILESTONE_TITLE}" ]] || blocked "empty milestone heading."
    [[ -n "${MILESTONE_NUMBER}" ]] || blocked "empty milestone number."
}
