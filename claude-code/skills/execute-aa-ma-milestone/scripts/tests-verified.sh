#!/usr/bin/env bash
# tests-verified.sh — §6.7 fence 3 of /execute-aa-ma-milestone: TESTS_VERIFIED.
#
# Usage: tests-verified.sh <task-name>    (cwd: the repository top level)
# Exit:  0 PASS, or an approved opt-out (one provenance line appended)
#        1 BLOCKED (no provenance line)
#
# Inputs come from the MERGE-BASE copy of <task>-reference.md, so a branch cannot change the
# command or the pass rule that prove it (it still controls the code and test config under
# test): `Test-Command:` (default `uv run pytest`) and the optional `Test-Command-Pass-Regex:`.
# A reference.md new on the branch has no merge-base copy; its HEAD copy is used, with a notice. The command runs as a shlex argv, never `bash -c`, under
# ${AA_MA_TEST_TIMEOUT:-540}s. PASS needs rc 0 AND a summary that names the pass count:
#   default         the final non-empty line, `=` banner stripped, matches `(^|, )([0-9]+) passed`
#   Pass-Regex set  the LAST output line matching it (bash ERE) gives an all-digit group 1
# No auto-rerun: a failing run is BLOCKED (Ste, 2026-10-13). Contract and rationale:
# references/gate-fences.md.
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
REF="${TASK_DIR}/${TASK_NAME}-reference.md"
PROV="${TASK_DIR}/${TASK_NAME}-provenance.log"

# The append target must be a regular file reached through no symlink. A committed link
# would redirect the line — which carries the repo's own heading text — into, say, ~/.bashrc.
for _p in .claude .claude/dev .claude/dev/active "${TASK_DIR}" "${PROV}"; do
    [[ -L "${_p}" ]] && blocked "${_p} is a symlink; refusing to write provenance through it."
done
[[ ! -e "${PROV}" || -f "${PROV}" ]] || blocked "${PROV} is not a regular file."

# -- The milestone being certified (Python SSoT, like the other §6.7 fences) ------------
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
    blocked "cannot read the milestone to verify its tests (gate rc ${_rc})."
}
MILESTONE_TITLE=$(printf '%s\n' "${GATE_KV}" | aa_ma_gate_field heading)
[[ -n "${MILESTONE_TITLE}" ]] || blocked "empty milestone heading."

# -- Inputs from the merge-base copy -------------------------------------------------------
# why: stderr dropped — a missing origin/HEAD falls through to the local candidates
BASE_REF=$(git symbolic-ref -q --short refs/remotes/origin/HEAD 2>/dev/null) || BASE_REF=""
if [[ -z "${BASE_REF}" ]]; then
    for _c in main master; do
        git rev-parse --verify -q "${_c}" >/dev/null && BASE_REF="${_c}" && break
    done
fi
[[ -n "${BASE_REF}" ]] || blocked "no default branch (origin/HEAD, main, master) to take the merge-base from."
BASE=$(git merge-base "${BASE_REF}" HEAD) || blocked "no merge-base between ${BASE_REF} and HEAD."

REF_TEXT=""
REF_FROM="merge-base ${BASE:0:7}"
# why: stderr dropped — a reference.md new on this branch is absent at the merge-base
if git cat-file -e "${BASE}:${REF}" 2>/dev/null; then
    REF_TEXT=$(git show "${BASE}:${REF}") || blocked "cannot read ${REF} at the merge-base ${BASE}."
# A plan created on this branch has nothing at the merge-base; its own copy is all there is (a
# brand-new plan is self-authored either way). Every existing plan keeps the merge-base guard.
# why: stderr dropped — not yet committed falls back to the working-tree file
elif git cat-file -e "HEAD:${REF}" 2>/dev/null; then
    REF_TEXT=$(git show "HEAD:${REF}") || blocked "cannot read ${REF} at HEAD."
    REF_FROM="HEAD"
    echo "NOTE: ${REF} is new on this branch (absent at the merge-base); using its HEAD copy."
elif [[ -f "${REF}" ]]; then
    REF_TEXT=$(cat -- "${REF}") || blocked "cannot read ${REF}."
    REF_FROM="working tree"
    echo "NOTE: ${REF} is new on this branch and uncommitted; using the working-tree copy."
fi

# count <name> / field <name>: how many `<name>:` lines, and the (trimmed) value of one.
count() { printf '%s\n' "${REF_TEXT}" | grep -c "^$1:"; }
field() { printf '%s\n' "${REF_TEXT}" | sed -n "s/^$1:[[:space:]]*//p" | sed 's/[[:space:]]*$//'; }
TEST_CMD_COUNT=$(count "Test-Command")
PASS_RE_COUNT=$(count "Test-Command-Pass-Regex")
[[ "${TEST_CMD_COUNT}" -le 1 ]] || blocked "more than one 'Test-Command:' line in ${REF} (${REF_FROM})."
[[ "${PASS_RE_COUNT}" -le 1 ]] || blocked "more than one 'Test-Command-Pass-Regex:' line in ${REF} (${REF_FROM})."
TEST_CMD=$(field "Test-Command")
PASS_RE=$(field "Test-Command-Pass-Regex")
if [[ "${TEST_CMD_COUNT}" -eq 0 ]]; then
    TEST_CMD="uv run pytest"
elif [[ -z "${TEST_CMD}" ]]; then
    blocked "'Test-Command:' is empty in ${REF} (${REF_FROM})."
fi

# append <line>: re-check the path just before writing (it may change during a long run) and
# refuse to report success when the line did not land.
append() {
    [[ ! -L "${PROV}" && ( ! -e "${PROV}" || -f "${PROV}" ) ]] \
        || blocked "${PROV} became a symlink or a non-file during the run; nothing written."
    printf '%s\n' "$1" >> "${PROV}" || blocked "cannot write ${PROV}; no TESTS_VERIFIED line was recorded."
}

# -- Opt-out (D10): `Test-Command: none — <reason>` + a context-log GATE APPROVAL ----------
if [[ "${TEST_CMD}" == none || "${TEST_CMD}" == none[[:space:]]* ]]; then
    [[ "${TEST_CMD}" =~ ^none[[:space:]]+—[[:space:]]+(.+)$ ]] \
        || blocked "the opt-out needs a reason: 'Test-Command: none — <reason>'."
    REASON="${BASH_REMATCH[1]}"
    # Block-scoped, exact-title check shared with §7.1 (aa-ma-parse.sh).
    if ! aa_ma_has_gate_approval "${TASK_DIR}/${TASK_NAME}-context-log.md" "Test-Command none — ${MILESTONE_TITLE}"; then
        echo "The opt-out needs, in ${TASK_NAME}-context-log.md:"
        echo "  ## [date] GATE APPROVAL: Test-Command none — ${MILESTONE_TITLE}"
        echo "  - Decision: APPROVED"
        blocked "'Test-Command: none' without a GATE APPROVAL."
    fi
    append "[$(date -Iseconds)] TESTS_VERIFIED — ${MILESTONE_TITLE} — skipped: ${REASON}"
    echo "TESTS-GATE: SKIPPED (approved opt-out) — ${REASON}"
    exit 0
fi

# -- Validate everything before running anything -------------------------------------------
if [[ "${TEST_CMD}" == *[\;\|\&\$\`\<\>]* ]]; then
    blocked "rejected character in Test-Command (; | & \$ \` < > are not allowed): ${TEST_CMD}"
fi
if [[ "${PASS_RE_COUNT}" -gt 0 ]]; then
    [[ -n "${PASS_RE}" ]] || blocked "'Test-Command-Pass-Regex:' is empty."
    # rc 2 is an invalid ERE (1 a plain mismatch). Probed in a child bash, so its error
    # message is contained and the rc is a command's.
    _rc=0
    bash -c '[[ "" =~ $1 ]]' _ "${PASS_RE}" 2>/dev/null || _rc=$?  # why: the rc is the verdict
    [[ "${_rc}" -ne 2 ]] || blocked "invalid Test-Command-Pass-Regex: ${PASS_RE}"
fi
TIMEOUT="${AA_MA_TEST_TIMEOUT:-540}"
[[ "${TIMEOUT}" =~ ^[1-9][0-9]*$ ]] || blocked "AA_MA_TEST_TIMEOUT must be a positive integer (got '${TIMEOUT}')."
# A test that ignores SIGTERM gets SIGKILL this many seconds after the timeout.
KILL_AFTER="${AA_MA_TEST_KILL_AFTER:-30}"
[[ "${KILL_AFTER}" =~ ^[1-9][0-9]*$ ]] || blocked "AA_MA_TEST_KILL_AFTER must be a positive integer (got '${KILL_AFTER}')."

ARGS=$(python3 -c 'import shlex, sys; print("\n".join(shlex.split(sys.argv[1])))' "${TEST_CMD}" 2>&1) \
    || blocked "cannot split Test-Command into arguments (python3 shlex): ${ARGS}"
ARGV=()
while IFS= read -r _a; do ARGV+=("${_a}"); done <<< "${ARGS}"

# why: `|| true` — no timeout(1) at all is handled on the next lines (warned, never silent)
TIMEOUT_BIN=$(command -v timeout || command -v gtimeout || true)
[[ -n "${TIMEOUT_BIN}" ]] || echo "WARN: no timeout(1)/gtimeout(1) found; running without a time limit."

# -- Run --------------------------------------------------------------------------------------
OUT=$(mktemp) || blocked "mktemp failed."
trap 'rm -f "${OUT}"' EXIT
echo "Running Test-Command (${REF_FROM}): ${TEST_CMD}"
if [[ -n "${TIMEOUT_BIN}" ]]; then
    "${TIMEOUT_BIN}" -k "${KILL_AFTER}" "${TIMEOUT}" "${ARGV[@]}" > "${OUT}" 2>&1
else
    "${ARGV[@]}" > "${OUT}" 2>&1
fi
RC=$?

# 124: timed out and stopped on SIGTERM; 137: needed the SIGKILL (or was killed otherwise).
if [[ -n "${TIMEOUT_BIN}" && ( "${RC}" -eq 124 || "${RC}" -eq 137 ) ]]; then
    tail -n 5 "${OUT}"
    blocked "tests timed out after ${TIMEOUT}s (rc ${RC}). Raise AA_MA_TEST_TIMEOUT and run this fence with run_in_background."
fi
# A command that cannot start is a configuration error, not a failing suite.
if [[ "${RC}" -eq 126 || "${RC}" -eq 127 ]]; then
    tail -n 5 "${OUT}"
    blocked "Test-Command could not run (rc ${RC}: not executable / not found): ${TEST_CMD}"
fi
if [[ "${RC}" -ne 0 ]]; then
    tail -n 20 "${OUT}"
    if [[ "${RC}" -eq 5 ]]; then
        echo "rc 5 is pytest's 'no tests collected'. A milestone with no tests declares, in reference.md,"
        echo "'Test-Command: none — <reason>' plus a context-log GATE APPROVAL."
    fi
    blocked "tests failed (rc ${RC}) — fix them, then re-run this fence. Never auto-pass."
fi

# -- rc 0: the summary must name the pass count -------------------------------------------
N=""
if [[ "${PASS_RE_COUNT}" -gt 0 ]]; then
    # grep narrows the output to candidate lines (1M lines: 0.01 s, vs 14 s for a bash loop over
    # every line) and keeps a last line that has no trailing newline; bash =~ still decides.
    MATCHED=0
    CANDIDATES=$(grep -aE -e "${PASS_RE}" "${OUT}")
    _grc=$?
    [[ "${_grc}" -le 1 ]] || blocked "grep could not scan the test output (rc ${_grc})."
    while IFS= read -r _line; do
        if [[ -n "${_line}" && "${_line}" =~ ${PASS_RE} ]]; then
            MATCHED=1
            N="${BASH_REMATCH[1]-}"
        fi
    done <<< "${CANDIDATES}"
    if [[ "${MATCHED}" -eq 0 ]]; then
        tail -n 5 "${OUT}"
        blocked "tests exited 0 but no output line matches Test-Command-Pass-Regex: ${PASS_RE}"
    fi
    [[ "${N}" =~ ^[0-9]+$ ]] \
        || blocked "Test-Command-Pass-Regex group 1 must capture the pass count (got '${N}')."
else
    LAST=$(grep -v '^[[:space:]]*$' "${OUT}" | tail -n 1)
    STRIPPED=$(printf '%s\n' "${LAST}" | sed -E 's/^=+ //; s/ =+$//')
    if [[ "${STRIPPED}" =~ (^|, )([0-9]+)\ passed ]]; then
        N="${BASH_REMATCH[2]}"
    else
        tail -n 5 "${OUT}"
        blocked "tests exited 0 but the final line is not a pytest summary: '${LAST}' (another runner: set Test-Command-Pass-Regex)."
    fi
fi

append "[$(date -Iseconds)] TESTS_VERIFIED — ${MILESTONE_TITLE} — passed=${N} cmd=${TEST_CMD}"
echo "TESTS-GATE: PASS — passed=${N} cmd=${TEST_CMD}"
