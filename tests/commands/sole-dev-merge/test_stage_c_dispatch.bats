#!/usr/bin/env bats
# test_stage_c_dispatch.bats — Stage C (review + 3-source security) dispatch
# and aggregation.
#
# Plan §2.1-§2.4 contract:
#   - C1 (code-reviewer agent) writes findings to /tmp/sole-dev-merge-review-<slug>.md
#   - C2 (security-auditor agent) writes to /tmp/sole-dev-merge-security-<slug>.md
#   - C3 (Bandit) writes JSON to /tmp/sole-dev-merge-bandit-<slug>.json
#   - C4 (ShellCheck) writes JSON to /tmp/sole-dev-merge-shellcheck-<slug>.json
#   - Aggregator consolidates all 4 sources into /tmp/sole-dev-merge-findings-<slug>.md
#
# Severity contract (reference.md):
#   Agent emits: [CRITICAL]|[HIGH]|[MEDIUM]|[LOW] <one-line> — <path>:<line>
#   Bandit JSON:  HIGH→[CRITICAL], MEDIUM→[HIGH], LOW→[MEDIUM]
#   ShellCheck:   error→[CRITICAL], warning→[HIGH], info→[MEDIUM], style→[LOW]
#   Parse failure → safe-default: classify ALL findings as [HIGH]
#
# Test pattern: MOCK_AGENT_DISPATCH=1 means agent outputs are pre-populated by
# the test (bypassing real Agent tool). C3/C4 run real bandit/shellcheck.

load fixtures/helpers

setup() {
    REPO_ROOT="$(cd "${BATS_TEST_DIRNAME}/../../.." && pwd)"
    COMMAND_MD="${REPO_ROOT}/claude-code/commands/sole-dev-merge.md"
    EXTRACT="${REPO_ROOT}/tests/commands/sole-dev-merge/fixtures/extract_stage.sh"

    SCRIPT_DIR="$(tmp_script_dir)"
    BATS_TMP="$(mktemp -d)"
    SLUG="bats-$$-$(date +%s%N | tail -c 6)"
    export BATS_TMP SCRIPT_DIR SLUG REPO_ROOT COMMAND_MD EXTRACT

    [[ -f "$COMMAND_MD" ]] || { echo "Missing $COMMAND_MD" >&2; return 1; }
    [[ -x "$EXTRACT"   ]] || { echo "Missing $EXTRACT" >&2; return 1; }

    SC_SCRIPT="${SCRIPT_DIR}/sc.sh"
    bash "$EXTRACT" stage-c-aggregate "$COMMAND_MD" > "$SC_SCRIPT" || \
        { echo "stage-c-aggregate not yet implemented in $COMMAND_MD" >&2; return 1; }
    chmod +x "$SC_SCRIPT"
    export SC_SCRIPT
}

teardown() {
    rm -rf "$BATS_TMP" "$SCRIPT_DIR"
    sweep_slug_tmp
}

@test "aggregator parses agent severity contract and consolidates" {
    # Pre-populate C1 + C2 mocked agent outputs
    cat > "/tmp/sole-dev-merge-review-${SLUG}.md" <<'EOF'
[CRITICAL] Hardcoded SQL — src/db.py:42
[HIGH]     Unsafe regex backtracking risk — src/util.py:17
[LOW]      Missing type hint on public function — src/api.py:9
EOF
    cat > "/tmp/sole-dev-merge-security-${SLUG}.md" <<'EOF'
[MEDIUM]   Open redirect via user-supplied URL — src/route.py:55
EOF

    # Empty Bandit + ShellCheck (no Python or shell changes)
    cd "$BATS_TMP"
    sandbox_init
    echo init > a.txt && git add a.txt
    mkcommit "init"
    git checkout -q -b feature
    echo "## doc" > NOTES.md && git add NOTES.md
    mkcommit "docs"
    export BASE_REF=main DEFAULT_BRANCH=main CHANGED_PY="" CHANGED_SH=""

    run bash "$SC_SCRIPT"
    [ "$status" -eq 0 ]

    [ -f "/tmp/sole-dev-merge-findings-${SLUG}.md" ]
    FINDINGS=$(cat "/tmp/sole-dev-merge-findings-${SLUG}.md")

    # 1 CRITICAL + 1 HIGH + 1 MEDIUM + 1 LOW from agents
    [[ "$FINDINGS" == *"[CRITICAL]"* ]]
    [[ "$FINDINGS" == *"src/db.py:42"* ]]
    [[ "$FINDINGS" == *"src/route.py:55"* ]]
    [[ "$FINDINGS" == *"src/api.py:9"* ]]
}

@test "C3 maps Bandit HIGH severity to [CRITICAL]" {
    # Plant a Python file with Bandit B602 (subprocess shell=True)
    cd "$BATS_TMP"
    sandbox_init
    echo init > a.txt && git add a.txt
    mkcommit "init"
    git checkout -q -b feature

    cat > vulnerable.py <<'PY'
import subprocess
def run(cmd):
    return subprocess.run(cmd, shell=True)
PY
    git add vulnerable.py
    mkcommit "feat: vulnerable"

    # Mocked agent outputs (empty)
    : > "/tmp/sole-dev-merge-review-${SLUG}.md"
    : > "/tmp/sole-dev-merge-security-${SLUG}.md"

    export BASE_REF=main DEFAULT_BRANCH=main \
           CHANGED_PY="vulnerable.py" CHANGED_SH=""

    run bash "$SC_SCRIPT"
    [ "$status" -eq 0 ]

    FINDINGS=$(cat "/tmp/sole-dev-merge-findings-${SLUG}.md")
    # Bandit B602 is HIGH severity → maps to [CRITICAL]
    [[ "$FINDINGS" == *"[CRITICAL]"* ]]
    [[ "$FINDINGS" == *"B602"* ]] || [[ "$FINDINGS" == *"shell=True"* ]] || [[ "$FINDINGS" == *"subprocess"* ]]
}

@test "C3/C4 record UNKNOWN in findings when a scanner does not run" {
    # The regression this milestone exists to prevent, and the only test in this
    # file that needs no external binary — so it can never skip.
    #
    # A scanner that did not run must not be reported as one that found nothing.
    # Three degraded modes are covered because `command -v` alone caught only
    # the first: an absent binary, a resolvable binary that emits nothing
    # (`true` — a broken install looks like this), and one that emits non-JSON.
    #
    # Asserting on $FINDINGS is the point. An earlier version of the fix warned
    # on stdout only, which left the machine-readable artefact Stage D consumes
    # byte-identical to a clean scan.
    cd "$BATS_TMP"
    sandbox_init
    echo init > a.txt && git add a.txt
    mkcommit "init"
    git checkout -q -b feature
    printf '#!/bin/bash\nif [ "$1" = "x"\necho "broken"\n' > buggy.sh
    git add buggy.sh
    mkcommit "feat: buggy"

    printf 'import subprocess\nsubprocess.call("ls", shell=True)\n' > vuln.py
    git add vuln.py
    mkcommit "feat: vulnerable"

    local findings="/tmp/sole-dev-merge-findings-${SLUG}.md"

    # Both scanners, all three modes. C3/bandit matters at least as much as C4:
    # bandit is not a declared dependency of this repo, and $BANDIT_OUT drives
    # Stage D's B602 auto-remediation, so a silent miss disabled fixing too.
    for scanner in SHELLCHECK BANDIT; do
        for bin in /nonexistent/scanner true echo; do
            : > "/tmp/sole-dev-merge-review-${SLUG}.md"
            : > "/tmp/sole-dev-merge-security-${SLUG}.md"

            if [[ "$scanner" == SHELLCHECK ]]; then
                SHELLCHECK_BIN="$bin" BASE_REF=main DEFAULT_BRANCH=main \
                    CHANGED_PY="" CHANGED_SH="buggy.sh" run bash "$SC_SCRIPT"
            else
                BANDIT_BIN="$bin" BASE_REF=main DEFAULT_BRANCH=main \
                    CHANGED_PY="vuln.py" CHANGED_SH="" run bash "$SC_SCRIPT"
            fi
            [ "$status" -eq 0 ]

            # The degraded state must reach $FINDINGS, not just stdout, and must
            # carry a severity Stage D will actually triage.
            grep -q '^\[HIGH\]' "$findings" \
                || { echo "no [HIGH] sentinel for ${scanner}_BIN=$bin" >&2; false; }
            grep -qi 'UNKNOWN' "$findings" \
                || { echo "findings do not record UNKNOWN for ${scanner}_BIN=$bin" >&2; false; }

            # And "0 findings" must be unrepresentable in this state — that count
            # is what makes Stage D skip triage entirely.
            [[ "$output" != *"aggregate: 0 findings"* ]] \
                || { echo "reported 0 findings for ${scanner}_BIN=$bin" >&2; false; }
        done
    done
}

@test "C4 maps ShellCheck error to [CRITICAL]" {
    # Guard the external dependency so its absence names itself instead of
    # dying on an opaque string match 20 lines below. Same shape as the guard in
    # tests/hooks/security-static-check.bats, but resolvability is not enough:
    # `true` and `:` both satisfy `command -v` and neither can scan anything, so
    # require the binary to identify itself. The degraded paths this guard skips
    # are covered unconditionally by the test above.
    if ! "${SHELLCHECK_BIN:-shellcheck}" --version 2>/dev/null | grep -qi 'shellcheck'; then
        skip "shellcheck unusable (SHELLCHECK_BIN=${SHELLCHECK_BIN:-shellcheck})"
    fi

    cd "$BATS_TMP"
    sandbox_init
    echo init > a.txt && git add a.txt
    mkcommit "init"
    git checkout -q -b feature

    # ShellCheck SC2086 (unquoted variable) — emits 'info'/'warning' level
    # but SC2046 (unquoted command substitution) is also warning
    # We'll use SC1009 (parse error — actual `error` level)
    cat > buggy.sh <<'SH'
#!/bin/bash
if [ "$1" = "x"
echo "broken"
SH
    git add buggy.sh
    mkcommit "feat: buggy"

    : > "/tmp/sole-dev-merge-review-${SLUG}.md"
    : > "/tmp/sole-dev-merge-security-${SLUG}.md"

    export BASE_REF=main DEFAULT_BRANCH=main \
           CHANGED_PY="" CHANGED_SH="buggy.sh"

    run bash "$SC_SCRIPT"
    [ "$status" -eq 0 ]

    FINDINGS=$(cat "/tmp/sole-dev-merge-findings-${SLUG}.md")
    # Expect a CRITICAL or HIGH from the parse error
    [[ "$FINDINGS" == *"[CRITICAL]"* ]] || [[ "$FINDINGS" == *"[HIGH]"* ]]
    [[ "$FINDINGS" == *"buggy.sh"* ]]
}

@test "parse failure triggers safe-default all-HIGH classification" {
    # Agent emits free-form text NOT matching the severity contract
    cat > "/tmp/sole-dev-merge-review-${SLUG}.md" <<'EOF'
This is a random review without proper severity tagging.
Reviewer thinks the code has issues.
EOF
    : > "/tmp/sole-dev-merge-security-${SLUG}.md"

    cd "$BATS_TMP"
    sandbox_init
    echo init > a.txt && git add a.txt
    mkcommit "init"
    git checkout -q -b feature
    echo "## x" > NOTES.md && git add NOTES.md
    mkcommit "docs"
    export BASE_REF=main DEFAULT_BRANCH=main CHANGED_PY="" CHANGED_SH=""

    run bash "$SC_SCRIPT"
    [ "$status" -eq 0 ]

    # The aggregator should detect parse failure and either mention it
    # in stdout or classify the malformed input as [HIGH] in findings.
    # Safe-default contract: classify all findings as [HIGH] on parse failure.
    [[ "$output" == *"parse"* ]] || [[ "$output" == *"safe-default"* ]] || \
      { FINDINGS=$(cat "/tmp/sole-dev-merge-findings-${SLUG}.md"); [[ "$FINDINGS" == *"[HIGH]"* ]]; }
}

@test "all 4 sources empty → empty findings file (clean run)" {
    : > "/tmp/sole-dev-merge-review-${SLUG}.md"
    : > "/tmp/sole-dev-merge-security-${SLUG}.md"

    cd "$BATS_TMP"
    sandbox_init
    echo init > a.txt && git add a.txt
    mkcommit "init"
    git checkout -q -b feature
    echo "## x" > NOTES.md && git add NOTES.md
    mkcommit "docs"
    export BASE_REF=main DEFAULT_BRANCH=main CHANGED_PY="" CHANGED_SH=""

    run bash "$SC_SCRIPT"
    [ "$status" -eq 0 ]

    [ -f "/tmp/sole-dev-merge-findings-${SLUG}.md" ]
    # No findings → no [SEVERITY] lines
    ! grep -qE '^\[(CRITICAL|HIGH|MEDIUM|LOW)\]' "/tmp/sole-dev-merge-findings-${SLUG}.md"
}
