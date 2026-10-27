#!/usr/bin/env bash
# impact-verified.sh — §6.7 fence 4 of /execute-aa-ma-milestone: IMPACT_VERIFIED (T7, ADR-0009 scope).
#
# Usage: impact-verified.sh <task-name>    (cwd: the repository top level)
# Exit:  0 PASS (one provenance line appended), or not applicable (grandfathered plan; printed)
#        1 BLOCKED (no provenance line)
#
# The base is aa_ma_milestone_base (merge-base with origin's default branch). aa-ma-impact
# compares what the milestone changed (that window plus the working tree: §8.1 commits after
# the gate) with its Contract rows and codemem co-change partners, diffs the public API
# (griffe), and checks derived Critical-Path reviews; every difference needs an
# `Impact-Explained:` line or an `API-Break:` declaration. The grandfather check runs first,
# so a plan created before IMPACT_CUTOVER is "not applicable" even with no milestone window.
# How to read a BLOCKED report: references/impact-gate.md.
set -uo pipefail

blocked() {
    printf 'BLOCKED: %s\n' "$*"
    exit 1
}

TASK_NAME="${1:-}"
if ! [[ "${TASK_NAME}" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ && "${TASK_NAME}" != *..* ]]; then
    blocked "TASK_NAME must be a plain task slug (got '${TASK_NAME}')."
fi
TASK_DIR=".claude/dev/active/${TASK_NAME}"
PLAN="${TASK_DIR}/${TASK_NAME}-plan.md"
TASKS="${TASK_DIR}/${TASK_NAME}-tasks.md"
PROV="${TASK_DIR}/${TASK_NAME}-provenance.log"

# The append target must be a regular file reached through no symlink (as fence 3).
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
GATE_KV=$(aa_ma_gate "${TASKS}") || {
    _rc=$?
    printf '%s\n' "${GATE_KV:-}" | sed -n 's/^error=/  - /p'
    blocked "cannot read the milestone to verify its impact (gate rc ${_rc})."
}
MILESTONE_TITLE=$(printf '%s\n' "${GATE_KV}" | aa_ma_gate_field heading)
MILESTONE_NUMBER=$(printf '%s\n' "${GATE_KV}" | aa_ma_gate_field number)
[[ -n "${MILESTONE_TITLE}" && -n "${MILESTONE_NUMBER}" ]] || blocked "empty milestone heading or number."

BASE_ARGS=()
if BASE=$(aa_ma_milestone_base); then
    BASE_ARGS=(--base "${BASE}")
else
    BASE_ERROR="${BASE}"  # aa_ma_milestone_base printed the reason
fi

IMPACT_KV=$(aa_ma_impact "${PLAN}" "${TASKS}" --milestone "${MILESTONE_NUMBER}" "${BASE_ARGS[@]}")
IMPACT_RC=$?
field() { printf '%s\n' "${IMPACT_KV}" | aa_ma_gate_field "$1"; }

case "${IMPACT_RC}" in
    0)
        COUNTS="changed=$(field changed) predicted=$(field predicted) cochange=$(field cochange) unexplained=$(field unexplained)"
        echo "[$(date -Iseconds)] IMPACT_VERIFIED — ${MILESTONE_TITLE} — ${COUNTS}" >> "${PROV}"
        echo "IMPACT-GATE: PASS — ${COUNTS} api_diff=$(field api_diff)"
        ;;
    5)
        echo "IMPACT-GATE: not applicable (grandfathered) — $(field reason)"
        ;;
    127)
        blocked "aa-ma-impact could not run (see the line above)."
        ;;
    *)
        [[ -n "${BASE_ERROR:-}" ]] && blocked "${BASE_ERROR}"
        printf '%s\n' "${IMPACT_KV}" | grep -E '^(unexplained_file|api_break|unreviewed_cp)=' | sed 's/^/  - /'
        blocked "aa-ma-impact rc ${IMPACT_RC}: $(field reason). See references/impact-gate.md."
        ;;
esac
