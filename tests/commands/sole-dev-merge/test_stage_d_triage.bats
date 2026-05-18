#!/usr/bin/env bats
# test_stage_d_triage.bats — Stage D findings triage with planted B602.
#
# Plan §2.5 / AC §4.2.5: given a fixture with `subprocess.run(cmd, shell=True)`
# in a changed Python file, after Stage D runs:
#   - `bandit -t B602 fixture.py 2>&1 | grep -c "Issue:"` returns 0 (auto-fix
#     applied), AND
#   - `git log -1 --format=%s` matches regex `^fix\(review\): apply CRITICAL bandit`
#
# Stage D behaviour:
#   - For CRITICAL findings from Bandit/ShellCheck with deterministic patterns:
#     attempt auto-fix (B602 → s/shell=True/shell=False/) and commit
#   - For agent-emitted CRITICALs: tag for user-review (no auto-fix)
#   - For HIGH/MEDIUM: AskUserQuestion panel (not testable in bats; skipped here)
#   - For LOW: append to Reviewer notes section (advisory)

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
    bash "$EXTRACT" stage-c-aggregate "$COMMAND_MD" > "$SC_SCRIPT"
    chmod +x "$SC_SCRIPT"

    SD_SCRIPT="${SCRIPT_DIR}/sd.sh"
    bash "$EXTRACT" stage-d-triage "$COMMAND_MD" > "$SD_SCRIPT" || \
        { echo "stage-d-triage not yet implemented in $COMMAND_MD" >&2; return 1; }
    chmod +x "$SD_SCRIPT"

    export SC_SCRIPT SD_SCRIPT
}

teardown() {
    rm -rf "$BATS_TMP" "$SCRIPT_DIR"
    rm -f "/tmp/sole-dev-merge-review-${SLUG}.md" \
          "/tmp/sole-dev-merge-security-${SLUG}.md" \
          "/tmp/sole-dev-merge-bandit-${SLUG}.json" \
          "/tmp/sole-dev-merge-shellcheck-${SLUG}.json" \
          "/tmp/sole-dev-merge-findings-${SLUG}.md"
}

@test "Stage D auto-fixes planted Bandit B602 (AC §4.2.5)" {
    cd "$BATS_TMP"
    sandbox_init
    echo init > a.txt && git add a.txt
    mkcommit "init"
    git checkout -q -b feature

    # Plant a Python file with B602 (subprocess shell=True)
    cat > vulnerable.py <<'PY'
import subprocess
def run_cmd(cmd):
    return subprocess.run(cmd, shell=True)
PY
    git add vulnerable.py
    mkcommit "feat: vulnerable"

    # Mocked agent outputs (empty — focus on Bandit-driven auto-fix)
    : > "/tmp/sole-dev-merge-review-${SLUG}.md"
    : > "/tmp/sole-dev-merge-security-${SLUG}.md"

    # Run Stage C aggregator to produce findings.md including the B602 entry
    export BASE_REF=main DEFAULT_BRANCH=main \
           CHANGED_PY="vulnerable.py" CHANGED_SH=""
    bash "$SC_SCRIPT" >/dev/null

    # Verify pre-Stage-D state: findings.md HAS a B602 CRITICAL
    grep -q "B602" "/tmp/sole-dev-merge-findings-${SLUG}.md"
    grep -q "shell=True" vulnerable.py

    # Run Stage D
    run bash "$SD_SCRIPT"
    [ "$status" -eq 0 ]

    # AC §4.2.5 #1: post-fix, Bandit B602 finds 0 issues on the fixed file
    BANDIT_ISSUES=$(bandit -t B602 vulnerable.py 2>&1 | grep -c "Issue:" || true)
    [ "$BANDIT_ISSUES" -eq 0 ]

    # AC §4.2.5 #2: commit subject matches `^fix\(review\): apply CRITICAL bandit`
    SUBJECT=$(git log -1 --format=%s)
    [[ "$SUBJECT" =~ ^fix\(review\):\ apply\ CRITICAL\ bandit ]]

    # The file no longer contains shell=True
    ! grep -q "shell=True" vulnerable.py
}

@test "Stage D is a no-op when findings.md has no auto-fixable CRITICALs" {
    cd "$BATS_TMP"
    sandbox_init
    echo init > a.txt && git add a.txt
    mkcommit "init"
    git checkout -q -b feature
    echo "## d" > NOTES.md && git add NOTES.md
    mkcommit "docs"

    # Empty findings.md (or only LOW entries)
    cat > "/tmp/sole-dev-merge-findings-${SLUG}.md" <<'EOF'
[LOW]      cosmetic: trailing whitespace — NOTES.md:1
EOF

    PRE_SHA=$(git rev-parse HEAD)
    run bash "$SD_SCRIPT"
    [ "$status" -eq 0 ]
    POST_SHA=$(git rev-parse HEAD)

    # No commit created
    [ "$PRE_SHA" = "$POST_SHA" ]
}

@test "Stage D B602 auto-fix is line-scoped — docstring with 'shell=True' survives" {
    # Regression test addressing §6.8 audit HIGH findings 1-3:
    # "Stage D's sed -i 's/shell=True/shell=False/g' rewrites EVERY occurrence
    #  including docstrings, comments, # nosec, and test fixtures."
    # Fix: drive auto-fix from $BANDIT_OUT JSON (exact line + test_id equality),
    # apply line-scoped sed (only the EXACT line Bandit reports).

    cd "$BATS_TMP"
    sandbox_init
    echo init > a.txt && git add a.txt
    mkcommit "init"
    git checkout -q -b feature

    # File has TWO occurrences of `shell=True`:
    #   line 1: docstring (must SURVIVE — Bandit doesn't flag it)
    #   line 4: actual B602 call (must be FIXED — Bandit flags it on line 4)
    cat > mixed.py <<'PY'
"""Demo module: never use shell=True for untrusted input."""
import subprocess
def run_cmd(cmd):
    return subprocess.run(cmd, shell=True)
PY
    git add mixed.py
    mkcommit "feat: mixed"

    : > "/tmp/sole-dev-merge-review-${SLUG}.md"
    : > "/tmp/sole-dev-merge-security-${SLUG}.md"

    export BASE_REF=main DEFAULT_BRANCH=main \
           CHANGED_PY="mixed.py" CHANGED_SH=""
    bash "$SC_SCRIPT" >/dev/null

    # Sanity-check pre-Stage-D: both occurrences present
    [ "$(grep -c 'shell=True' mixed.py)" -eq 2 ]

    run bash "$SD_SCRIPT"
    [ "$status" -eq 0 ]

    # Post-Stage-D:
    # - Docstring on line 1 SURVIVES (still contains "shell=True")
    head -1 mixed.py | grep -q "shell=True"

    # - Line 4 was rewritten (no longer contains "shell=True")
    ! sed -n '4p' mixed.py | grep -q "shell=True"

    # - Bandit re-scan finds 0 B602 issues
    BANDIT_ISSUES=$(bandit -t B602 mixed.py 2>&1 | grep -c "Issue:" || true)
    [ "$BANDIT_ISSUES" -eq 0 ]
}

@test "Stage D tags agent-emitted CRITICALs for user review (no auto-fix)" {
    cd "$BATS_TMP"
    sandbox_init
    echo init > a.txt && git add a.txt
    mkcommit "init"
    git checkout -q -b feature
    cat > src.py <<'PY'
def x(): return 1
PY
    git add src.py
    mkcommit "feat: src"

    # An agent-emitted CRITICAL — NOT a Bandit/ShellCheck pattern
    # Stage D should NOT auto-fix this; just tag for user review.
    cat > "/tmp/sole-dev-merge-findings-${SLUG}.md" <<'EOF'
[CRITICAL] Logic error: function returns wrong value — src.py:1
EOF

    PRE_SHA=$(git rev-parse HEAD)
    run bash "$SD_SCRIPT"
    [ "$status" -eq 0 ]
    POST_SHA=$(git rev-parse HEAD)

    # No auto-fix commit (agent CRITICALs are tagged, not fixed)
    [ "$PRE_SHA" = "$POST_SHA" ]

    # Output should indicate the agent CRITICAL was tagged for user review
    [[ "$output" == *"user"* ]] || [[ "$output" == *"review"* ]] || [[ "$output" == *"tag"* ]]
}
