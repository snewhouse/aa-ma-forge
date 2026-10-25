#!/usr/bin/env bash
# predicted-vs-actual.sh — §6.3 of /execute-aa-ma-milestone: which changed files did the plan
# not predict? (code-conventions-impact 10.7, R6). ADVISORY in M10: M11's gate-computed
# IMPACT_VERIFIED (aa-ma-impact) is the enforcing successor.
#
# Usage: predicted-vs-actual.sh <task-name>    (cwd: the repository top level)
# Exit:  0 — the lines below were printed (an empty UNPREDICTED list included)
#        2 — cannot run: bad task name, plan/tasks file missing, no ACTIVE milestone, not a
#            git repo, or no default branch (origin/HEAD, main, master) for the merge-base
#
# changed   = git diff merge-base(<default>, HEAD)..HEAD ∪ staged ∪ unstaged
#             ∪ untracked-not-ignored, minus EXCLUDE (AA-MA artefacts and generated files)
# predicted = the ACTIVE milestone's Contract paths (every row verb, nothing exempt;
#             aa_ma.render.coverage.milestone_contract_paths — a directory row covers what
#             is under it) ∪ their codemem co_changes partners at the T7 constants
# Output: `NOTE: …` lines, then one `UNPREDICTED <path>` per changed, unpredicted file
# (sorted; control characters shown as `?`), then the summary
#   predicted-vs-actual — <milestone heading> — changed=N predicted=P cochange=C unpredicted=U
# No codemem binary or index, or a failed query: a NOTE, and the Contract alone predicts.
# §6.0 refreshed the index to HEAD just before, so this script does not refresh it.
set -uo pipefail

usage_error() {
    printf 'predicted-vs-actual: %s\n' "$*" >&2
    exit 2
}

# T7 (plan Milestone 11 Contract): COCHANGE_MIN_SHARED / COCHANGE_MIN_RATIO. A partner counts
# when it shared >= 5 of the file's commits and >= 50% of them.
COCHANGE_MIN_SHARED=5
COCHANGE_MIN_RATIO=0.5
# why: 30 s bounds a hung codemem; a query over ~50 paths takes well under 1 s (measured 0.06 s)
CODEMEM_TIMEOUT_S=30
# Never "unpredicted": AA-MA artefacts and regenerated output (M11's IMPACT_EXCLUDE).
EXCLUDE=('.claude/dev/*' 'docs/architecture/*' 'tests/golden/*' 'uv.lock' 'CHANGELOG.md')

TASK_NAME="${1:-}"
if ! [[ "${TASK_NAME}" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ && "${TASK_NAME}" != *..* ]]; then
    usage_error "TASK_NAME must be a plain task slug (got '${TASK_NAME}'). Usage: predicted-vs-actual.sh <task-name>"
fi
TASK_DIR=".claude/dev/active/${TASK_NAME}"
PLAN="${TASK_DIR}/${TASK_NAME}-plan.md"
TASKS="${TASK_DIR}/${TASK_NAME}-tasks.md"
[[ -f "${PLAN}" ]] || usage_error "${PLAN} not found (run from the repository top level)."
[[ -f "${TASKS}" ]] || usage_error "${TASKS} not found."

# why: git's own message is replaced by this one
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || usage_error "not inside a git work tree."

# This script's own forge, never the target repo's tree (code-intel-refresh.sh precedent).
SELF="$(readlink -f "${BASH_SOURCE[0]}" 2>/dev/null || printf '%s' "${BASH_SOURCE[0]}")"  # why: readlink -f is absent on old macOS; the invoked path still works
FORGE="$(cd "$(dirname "${SELF}")/../../../.." && pwd)"
AA_MA_LIB="${FORGE}/claude-code/hooks/lib/aa-ma-parse.sh"
[[ -f "${AA_MA_LIB}" ]] || usage_error "aa-ma-parse.sh not found at ${AA_MA_LIB} — run scripts/install.sh."
# shellcheck source=/dev/null
. "${AA_MA_LIB}"

GATE_KV=$(aa_ma_gate "${TASKS}") || {
    printf '%s\n' "${GATE_KV:-}" | sed -n 's/^error=/  - /p' >&2
    usage_error "cannot read the ACTIVE milestone of ${TASKS}."
}
NUMBER=$(printf '%s\n' "${GATE_KV}" | aa_ma_gate_field number)
HEADING=$(printf '%s\n' "${GATE_KV}" | aa_ma_gate_field heading)
[[ -n "${NUMBER}" ]] || usage_error "the gate named no milestone number."

# -- changed ---------------------------------------------------------------------------------
# why: stderr dropped — a missing origin/HEAD falls through to the local candidates
BASE_REF=$(git symbolic-ref -q --short refs/remotes/origin/HEAD 2>/dev/null) || BASE_REF=""
if [[ -z "${BASE_REF}" ]]; then
    for _c in main master; do
        git rev-parse --verify -q "${_c}" >/dev/null && BASE_REF="${_c}" && break
    done
fi
[[ -n "${BASE_REF}" ]] || usage_error "no default branch (origin/HEAD, main, master) to take the merge-base from."
BASE=$(git merge-base "${BASE_REF}" HEAD) || usage_error "no merge-base between ${BASE_REF} and HEAD."
[[ "${BASE}" == "$(git rev-parse HEAD)" ]] \
    && echo "NOTE: the merge-base with ${BASE_REF} is HEAD; only working-tree changes count."

declare -A CHANGED=()
while IFS= read -r -d '' _p; do
    CHANGED["${_p}"]=1
done < <(git diff --name-only -z --no-renames "${BASE}" HEAD -- ;
         git diff --name-only -z --no-renames HEAD -- ;
         git ls-files --others --exclude-standard -z)
for _p in "${!CHANGED[@]}"; do
    for _x in "${EXCLUDE[@]}"; do
        # shellcheck disable=SC2053  # why: the right side is a glob on purpose
        [[ "${_p}" == ${_x} ]] && unset 'CHANGED[$_p]' && break
    done
done

# -- predicted -------------------------------------------------------------------------------
# -I: isolated mode — the target repo's cwd is not on sys.path.
CONTRACT=$(uv run --quiet --project "${FORGE}" python -I - "${PLAN}" "${NUMBER}" <<'PY'
import sys
from pathlib import Path

from aa_ma.render.coverage import milestone_contract_paths

for path in milestone_contract_paths(Path(sys.argv[1]).read_text(encoding="utf-8"), sys.argv[2]):
    print(path)
PY
) || usage_error "cannot parse the Contract of Milestone ${NUMBER} in ${PLAN} (uv/python failed)."
mapfile -t PREDICTED <<< "${CONTRACT}"
[[ -n "${CONTRACT}" ]] || PREDICTED=()
if (( ${#PREDICTED[@]} == 0 )); then
    echo "NOTE: no Contract rows for Milestone ${NUMBER} in ${PLAN}; nothing to predict against — skipped."
    echo "predicted-vs-actual — ${HEADING} — changed=${#CHANGED[@]} predicted=0 cochange=0 unpredicted=0"
    exit 0
fi

COCHANGE=()
TOP=$(git rev-parse --show-toplevel)
if ! CM_DIR=$(aa_ma_codemem_dir "${TOP}") || [[ ! -f "${CM_DIR}/index.db" ]]; then
    echo "NOTE: co_changes skipped (no codemem index for this repo — run \`codemem build\`); the Contract alone predicts."
elif ! CM_BIN=$(aa_ma_codemem_bin "${FORGE}"); then
    echo "NOTE: co_changes skipped (no codemem binary); the Contract alone predicts."
else
    # Several paths print one object keyed by path; one path prints its result object.
    CM_OUT="" PARTNERS=""
    # why: codemem's stderr is replaced by the NOTE below
    CM_OUT=$(timeout -k 1 "${CODEMEM_TIMEOUT_S}" "${CM_BIN}" query co_changes --repo-root "${TOP}" --threshold "${COCHANGE_MIN_SHARED}" --min-ratio "${COCHANGE_MIN_RATIO}" -- "${PREDICTED[@]}" 2>/dev/null)
    CM_RC=$?
    JQ_RC=1
    if (( CM_RC == 0 )); then
        # why: jq's parse error on a non-JSON answer becomes the NOTE below
        PARTNERS=$(jq -r 'if has("files") then [.] else [.[]] end | .[] | .files[]?.path' <<< "${CM_OUT}" 2>/dev/null)
        JQ_RC=$?
    fi
    if (( JQ_RC == 0 )); then
        [[ -n "${PARTNERS}" ]] && mapfile -t COCHANGE < <(sort -u <<< "${PARTNERS}")
    else
        echo "NOTE: co_changes skipped (codemem query failed or printed no JSON); the Contract alone predicts."
    fi
fi

# predicted_by <path>: rc 0 when a Contract path is it or a directory above it, or it is a partner.
predicted_by() {
    local q
    for q in "${PREDICTED[@]}" "${COCHANGE[@]}"; do
        q="${q%/}"
        [[ "$1" == "${q}" || "$1" == "${q}/"* ]] && return 0
    done
    return 1
}

UNPREDICTED=()
for _p in "${!CHANGED[@]}"; do
    predicted_by "${_p}" || UNPREDICTED+=("${_p//[[:cntrl:]]/?}")
done
if (( ${#UNPREDICTED[@]} > 0 )); then
    printf 'UNPREDICTED %s\n' "${UNPREDICTED[@]}" | LC_ALL=C sort
fi
echo "predicted-vs-actual — ${HEADING} — changed=${#CHANGED[@]} predicted=${#PREDICTED[@]} cochange=${#COCHANGE[@]} unpredicted=${#UNPREDICTED[@]}"
exit 0
