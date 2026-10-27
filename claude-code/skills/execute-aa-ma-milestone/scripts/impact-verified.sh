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

# Slug check, symlink guards, aa-ma-parse.sh, and the milestone this run certifies.
# shellcheck source=/dev/null
. "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/fence-common.sh"
fence_init "${1:-}" "its impact"
PLAN="${TASK_DIR}/${TASK_NAME}-plan.md"
TASKS="${TASK_DIR}/${TASK_NAME}-tasks.md"

BASE_ARGS=()
if BASE=$(aa_ma_milestone_base); then
    BASE_ARGS=(--base "${BASE}")
else
    BASE_ERROR="${BASE}"  # aa_ma_milestone_base printed the reason
fi

IMPACT_KV=$(aa_ma_impact "${PLAN}" "${TASKS}" --milestone "${MILESTONE_NUMBER}" "${BASE_ARGS[@]}")
IMPACT_RC=$?
# Values carry repo-controlled text (file names, a heading); every printed or logged one passes
# aa_ma_sanitize_lines, so bidi, zero-width and ESC characters arrive as `?` (§6.8 security A03).
field() { printf '%s\n' "${IMPACT_KV}" | aa_ma_gate_field "$1" | aa_ma_sanitize_lines; }

case "${IMPACT_RC}" in
    0)
        COUNTS="changed=$(field changed) predicted=$(field predicted) cochange=$(field cochange) unexplained=$(field unexplained)"
        # api_diff is recorded too: a skipped API diff must not read as a clean pass (§6.8 A04).
        echo "[$(date -Iseconds)] IMPACT_VERIFIED — ${MILESTONE_TITLE} — ${COUNTS} api_diff=$(field api_diff)" >> "${PROV}"
        echo "IMPACT-GATE: PASS — ${COUNTS} api_diff=$(field api_diff)"
        ;;
    5)  # = aa_ma.impact.EXIT_NOT_APPLICABLE
        echo "IMPACT-GATE: not applicable (grandfathered) — $(field reason)"
        ;;
    127)
        blocked "aa-ma-impact could not run (see the line above)."
        ;;
    *)
        [[ -n "${BASE_ERROR:-}" ]] && blocked "$(printf '%s\n' "${BASE_ERROR}" | aa_ma_sanitize_lines)"
        printf '%s\n' "${IMPACT_KV}" | grep -E '^(unexplained_file|api_break|unreviewed_cp)=' \
            | aa_ma_sanitize_lines | sed 's/^/  - /'
        blocked "aa-ma-impact rc ${IMPACT_RC}: $(field reason). See references/impact-gate.md."
        ;;
esac
