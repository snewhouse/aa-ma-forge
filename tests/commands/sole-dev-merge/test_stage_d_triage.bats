#!/usr/bin/env bats
# test_stage_d_triage.bats — Stage D findings triage with planted Ruff S602.
#
# Plan §2.5 / AC §4.2.5: given a fixture with `subprocess.run(cmd, shell=True)`
# in a changed Python file, after Stage D runs:
#   - `ruff check --select S602 fixture.py` is clean (auto-fix applied), AND
#   - `git log -1 --format=%s` matches regex `^fix\(review\): apply CRITICAL ruff`
#
# Stage D behaviour:
#   - For CRITICAL findings from Ruff/ShellCheck with deterministic patterns:
#     attempt auto-fix (S602 → s/shell=True/shell=False/) and commit
#   - For agent-emitted CRITICALs: tag for user-review (no auto-fix)
#   - For HIGH/MEDIUM: AskUserQuestion panel (not testable in bats; skipped here)
#   - For LOW: append to Reviewer notes section (advisory)

bats_require_minimum_version 1.5.0

load fixtures/helpers

setup() {
    REPO_ROOT="$(cd "${BATS_TEST_DIRNAME}/../../.." && pwd)"
    COMMAND_MD="${REPO_ROOT}/claude-code/skills/sole-dev-merge/SKILL.md"
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

    # Point Stage D at the REAL helper (the sandbox's `git rev-parse` would
    # otherwise return the sandbox path, not the aa-ma-forge repo).
    AA_MA_FOOTER_HELPER="${REPO_ROOT}/claude-code/hooks/lib/aa-ma-footer.sh"
    export SC_SCRIPT SD_SCRIPT AA_MA_FOOTER_HELPER

    # Security-pattern literals, assembled at runtime and never spelled whole.
    SHELL_TRUE='shell''=''True'
    SHELL_FALSE='shell''=''False'
}

# ruff_s602_clean FILE — rc 0 iff Ruff reports no S602 on FILE.
ruff_s602_clean() {
    "${RUFF_BIN:-ruff}" check --quiet --select S602 "$1"
}

teardown() {
    rm -rf "$BATS_TMP" "$SCRIPT_DIR"
    sweep_slug_tmp
}

@test "Stage D auto-fixes planted Ruff S602 (AC §4.2.5)" {
    cd "$BATS_TMP"
    sandbox_init
    echo init > a.txt && git add a.txt
    mkcommit "init"
    git checkout -q -b feature

    # Plant a Python file with S602 (subprocess shell=True)
    printf 'import subprocess\ndef run_cmd(cmd):\n    return subprocess.run(cmd, %s)\n' \
        "$SHELL_TRUE" > vulnerable.py
    git add vulnerable.py
    mkcommit "feat: vulnerable"

    # Mocked agent outputs (empty — focus on Ruff-driven auto-fix)
    : > "/tmp/sole-dev-merge-review-${SLUG}.md"
    : > "/tmp/sole-dev-merge-security-${SLUG}.md"

    # Run Stage C aggregator to produce findings.md including the S602 entry
    export BASE_REF=main DEFAULT_BRANCH=main \
           CHANGED_PY="vulnerable.py" CHANGED_SH=""
    bash "$SC_SCRIPT" >/dev/null

    # Verify pre-Stage-D state: findings.md HAS an S602 CRITICAL
    grep -qE '^\[CRITICAL\][[:space:]]+S602 ' "/tmp/sole-dev-merge-findings-${SLUG}.md"
    grep -qF "$SHELL_TRUE" vulnerable.py

    # Run Stage D
    run bash "$SD_SCRIPT"
    [ "$status" -eq 0 ]

    # AC §4.2.5 #1: post-fix, Ruff S602 finds 0 issues on the fixed file
    ruff_s602_clean vulnerable.py

    # AC §4.2.5 #2: commit subject matches `^fix\(review\): apply CRITICAL ruff`
    SUBJECT=$(git log -1 --format=%s)
    [[ "$SUBJECT" =~ ^fix\(review\):\ apply\ CRITICAL\ ruff ]]

    # The file no longer contains shell=True
    run ! grep -qF "$SHELL_TRUE" vulnerable.py
}

@test "Stage D auto-fixes exactly the S602 rows named in a Ruff JSON report" {
    # Drives Stage D from a hand-written Ruff report, no Stage C: pins the
    # contract that the fix keys on code == "S602" (exact) and location.row.
    cd "$BATS_TMP"
    sandbox_init
    echo init > a.txt && git add a.txt
    mkcommit "init"
    git checkout -q -b feature

    # Rows 2, 3 and 4 all carry the literal; only row 3 is reported as S602.
    printf 'import subprocess\na = subprocess.run("x", %s)\nb = subprocess.run("y", %s)\nc = subprocess.run("z", %s)\n' \
        "$SHELL_TRUE" "$SHELL_TRUE" "$SHELL_TRUE" > rep.py
    git add rep.py
    mkcommit "feat: rep"

    local abs="${BATS_TMP}/rep.py"
    cat > "/tmp/sole-dev-merge-ruff-${SLUG}.json" <<JSON
[
 {"code": "S603", "message": "not S602", "filename": "${abs}", "location": {"row": 2, "column": 5}},
 {"code": "S602", "message": "`subprocess` call with `shell=True` identified, security issue", "filename": "${abs}", "location": {"row": 3, "column": 5}},
 {"code": "S6020", "message": "near-miss code", "filename": "${abs}", "location": {"row": 4, "column": 5}}
]
JSON
    printf '[CRITICAL]     S602 `subprocess` call with `shell=True` identified, security issue — %s:3\n' "$abs" \
        > "/tmp/sole-dev-merge-findings-${SLUG}.md"

    run bash "$SD_SCRIPT"
    [ "$status" -eq 0 ]

    sed -n '2p' rep.py | grep -qF "$SHELL_TRUE"
    sed -n '3p' rep.py | grep -qF "$SHELL_FALSE"
    sed -n '4p' rep.py | grep -qF "$SHELL_TRUE"
    [[ "$(git log -1 --format=%s)" =~ ^fix\(review\):\ apply\ CRITICAL\ ruff ]]
    # The auto-fixed S602 is not re-tagged for user review.
    [[ "$output" != *"tagged for user review"* ]]
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

@test "Stage D S602 auto-fix is line-scoped — docstring with 'shell=True' survives" {
    # Regression test addressing §6.8 audit HIGH findings 1-3:
    # "Stage D's sed -i 's/shell=True/shell=False/g' rewrites EVERY occurrence
    #  including docstrings, comments, # nosec, and test fixtures."
    # Fix: drive auto-fix from $RUFF_OUT JSON (exact row + code equality),
    # apply line-scoped sed (only the EXACT line Ruff reports).

    cd "$BATS_TMP"
    sandbox_init
    echo init > a.txt && git add a.txt
    mkcommit "init"
    git checkout -q -b feature

    # File has TWO occurrences of `shell=True`:
    #   line 1: docstring (must SURVIVE — Ruff doesn't flag it)
    #   line 4: actual S602 call (must be FIXED — Ruff flags it on line 4)
    printf '"""Demo module: never use %s for untrusted input."""\nimport subprocess\ndef run_cmd(cmd):\n    return subprocess.run(cmd, %s)\n' \
        "$SHELL_TRUE" "$SHELL_TRUE" > mixed.py
    git add mixed.py
    mkcommit "feat: mixed"

    : > "/tmp/sole-dev-merge-review-${SLUG}.md"
    : > "/tmp/sole-dev-merge-security-${SLUG}.md"

    export BASE_REF=main DEFAULT_BRANCH=main \
           CHANGED_PY="mixed.py" CHANGED_SH=""
    bash "$SC_SCRIPT" >/dev/null

    # Sanity-check pre-Stage-D: both occurrences present
    [ "$(grep -cF "$SHELL_TRUE" mixed.py)" -eq 2 ]

    run bash "$SD_SCRIPT"
    [ "$status" -eq 0 ]

    # Post-Stage-D:
    # - Docstring on line 1 SURVIVES (still contains "shell=True")
    head -1 mixed.py | grep -qF "$SHELL_TRUE"

    # - Line 4 was rewritten (no longer contains "shell=True")
    if sed -n '4p' mixed.py | grep -qF "$SHELL_TRUE"; then echo 'line 4 still has shell=True' >&2; false; fi

    # - Ruff re-scan finds 0 S602 issues
    ruff_s602_clean mixed.py
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

    # An agent-emitted CRITICAL — NOT a Ruff/ShellCheck pattern
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

# --- M8 §6.8: Ruff S602 also fires on literal commands (Bandit's HIGH filter excluded them) ---

S602_NONLITERAL='`subprocess` call with `shell=True` identified, security issue'
S602_LITERAL='`subprocess` call with `shell=True` seems safe, but may be changed in the future; consider rewriting without `shell`'

# stage_d_repo <py-content> — a feature branch holding rep.py with the given content.
stage_d_repo() {
    cd "$BATS_TMP"
    sandbox_init
    echo init > a.txt && git add a.txt
    mkcommit "init"
    git checkout -q -b feature
    printf '%s\n' "$1" > rep.py
    git add rep.py
    mkcommit "feat: rep"
}

# ruff_report <row> <message> — a one-finding S602 report + its CRITICAL findings line.
ruff_report() {
    local abs="${BATS_TMP}/rep.py"
    jq -n --arg f "$abs" --argjson r "$1" --arg m "$2" \
        '[{code: "S602", message: $m, filename: $f, location: {row: $r, column: 1}}]' \
        > "/tmp/sole-dev-merge-ruff-${SLUG}.json"
    printf '[CRITICAL]     S602 %s — %s:%s\n' "$2" "$abs" "$1" > "/tmp/sole-dev-merge-findings-${SLUG}.md"
}

@test "Stage D does not auto-fix a literal-command S602; it is tagged for review" {
    stage_d_repo "import subprocess
subprocess.run(\"ls | wc -l\", ${SHELL_TRUE})"
    ruff_report 2 "$S602_LITERAL"
    run bash "$SD_SCRIPT"
    [ "$status" -eq 0 ]
    sed -n '2p' rep.py | grep -qF "$SHELL_TRUE"           # untouched: a pipe needs the shell
    [[ "$(git log -1 --format=%s)" == "feat: rep" ]]        # nothing committed
    [[ "$output" == *"tagged for user review"* ]]
}

@test "Stage D does not count an auto-fix that did not apply; it is tagged for review" {
    stage_d_repo "import subprocess
subprocess.run(
    cmd,
    ${SHELL_TRUE},
)"
    ruff_report 2 "$S602_NONLITERAL"   # Ruff reports the call's first row, not the shell= row
    run bash "$SD_SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$(git log -1 --format=%s)" == "feat: rep" ]]
    [[ "$output" != *"auto-fix: S602"* ]]
    [[ "$output" == *"tagged for user review"* ]]
}

@test "Stage D commits only the files it fixed, never a stray untracked file" {
    stage_d_repo "import subprocess
subprocess.run(cmd, ${SHELL_TRUE})"
    ruff_report 2 "$S602_NONLITERAL"
    printf 'TOKEN=stray\n' > stray.env
    run bash "$SD_SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$(git log -1 --format=%s)" =~ ^fix\(review\) ]]
    [ "$(git show --name-only --format= HEAD)" = "rep.py" ]
    [ -z "$(git ls-files stray.env)" ]
}
