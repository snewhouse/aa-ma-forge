#!/usr/bin/env bats
# test_stage_b_scope.bats — L-007 scope-filter behaviour of Stage B.
#
# Plan §1.5 acceptance: given a feature branch with an in-scope formatting
# error AND an out-of-scope dirty `tests/codemem/foo.py`, verify post-Stage-B:
# the in-scope file is fixed AND the out-of-scope file is reverted to HEAD.
#
# Plan §4.1.3 falsifiable AC: out-of-scope `tests/codemem/foo.py` shows zero
# `git diff` after Stage B; the in-scope file passes `ruff check`. L-007 guard
# active.
#
# Test pattern:
#   - Sandbox repo (BATS_TMP) bootstrapped with `git init -b main`
#   - Plumbing-only commits (commit-tree + update-ref) to avoid tripping the
#     aa-ma-commit-signature.sh PreToolUse hook
#   - Stage A is sourced first so BASE_REF is set, then Stage B runs

load fixtures/helpers

setup() {
    REPO_ROOT="$(cd "${BATS_TEST_DIRNAME}/../../.." && pwd)"
    COMMAND_MD="${REPO_ROOT}/claude-code/commands/sole-dev-merge.md"
    EXTRACT="${REPO_ROOT}/tests/commands/sole-dev-merge/fixtures/extract_stage.sh"

    SCRIPT_DIR="$(tmp_script_dir)"
    BATS_TMP="$(mktemp -d)"
    export BATS_TMP SCRIPT_DIR REPO_ROOT COMMAND_MD EXTRACT

    [[ -f "$COMMAND_MD" ]] || { echo "Missing $COMMAND_MD" >&2; return 1; }
    [[ -x "$EXTRACT"   ]] || { echo "Missing or non-exec $EXTRACT" >&2; return 1; }
}

teardown() {
    rm -rf "$BATS_TMP" "$SCRIPT_DIR"
}

@test "Stage B reformats in-scope Python file" {
    cd "$BATS_TMP"
    git init -q -b main
    git config user.email t@t.com
    git config user.name T

    # main: pre-existing files
    mkdir -p tests/codemem src
    echo "def existing(): return 1" > tests/codemem/foo.py
    echo "def already(): pass" > src/already_there.py
    git add -A
    mkcommit "init"

    # feature: adds src/new_file.py with lint-fixable issues
    git checkout -q -b feature
    cat > src/new_file.py <<'PY'
import os
def hello( ):
    return 1
PY
    git add src/new_file.py
    mkcommit "feat: add new_file"

    # Set BASE_REF as Stage A would
    export BASE_REF=main DEFAULT_BRANCH=main

    # Extract and run Stage B
    SB_SCRIPT="${SCRIPT_DIR}/sb.sh"
    bash "$EXTRACT" stage-b-scope "$COMMAND_MD" > "$SB_SCRIPT"
    chmod +x "$SB_SCRIPT"

    run bash "$SB_SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Stage B OK"* ]]

    # AC: in-scope file passes ruff check after Stage B
    run ruff check src/new_file.py
    [ "$status" -eq 0 ]

    # And was reformatted (def hello() not def hello( ))
    grep -q "def hello():" src/new_file.py
}

@test "L-007 guard reverts out-of-scope drift (canonical scenario)" {
    cd "$BATS_TMP"
    git init -q -b main
    git config user.email t@t.com
    git config user.name T

    # main: tests/codemem/foo.py (pre-existing, out-of-scope to feature)
    mkdir -p tests/codemem src
    cat > tests/codemem/foo.py <<'PY'
# Pre-existing on main; feature must not touch this
def existing():
    return 1
PY
    echo "" > src/keep.py
    git add -A
    mkcommit "init"

    # feature: in-scope src/new_file.py
    git checkout -q -b feature
    cat > src/new_file.py <<'PY'
import os
def hello( ):
    return 2
PY
    git add src/new_file.py
    mkcommit "feat: new_file"

    # Simulate drift introduced by some downstream tool during Stage B:
    # touch foo.py without committing
    echo "# drifted — L-007 guard must revert" >> tests/codemem/foo.py

    export BASE_REF=main DEFAULT_BRANCH=main

    SB_SCRIPT="${SCRIPT_DIR}/sb.sh"
    bash "$EXTRACT" stage-b-scope "$COMMAND_MD" > "$SB_SCRIPT"
    chmod +x "$SB_SCRIPT"

    run bash "$SB_SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"L-007 guard: reverted 1 out-of-scope file(s): tests/codemem/foo.py"* ]]

    # AC §4.1.3: out-of-scope file shows zero `git diff` after Stage B
    DIFF_BYTES=$(git diff tests/codemem/foo.py | wc -c)
    [ "$DIFF_BYTES" -eq 0 ]

    # AC §4.1.3: in-scope file passes ruff check
    run ruff check src/new_file.py
    [ "$status" -eq 0 ]
}

@test "L-007 guard reports clean when no drift" {
    cd "$BATS_TMP"
    git init -q -b main
    git config user.email t@t.com
    git config user.name T

    mkdir -p src
    echo "" > src/keep.py
    git add -A
    mkcommit "init"

    git checkout -q -b feature
    # Add a Python file that is already clean (no lint errors, well-formatted)
    cat > src/already_clean.py <<'PY'
def f():
    return 1
PY
    git add src/already_clean.py
    mkcommit "feat: already_clean"

    export BASE_REF=main DEFAULT_BRANCH=main

    SB_SCRIPT="${SCRIPT_DIR}/sb.sh"
    bash "$EXTRACT" stage-b-scope "$COMMAND_MD" > "$SB_SCRIPT"
    chmod +x "$SB_SCRIPT"

    run bash "$SB_SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"L-007 guard: clean (no out-of-scope drift)"* ]]
}

@test "Stage B handles branch with zero Python changes (only .md)" {
    cd "$BATS_TMP"
    git init -q -b main
    git config user.email t@t.com
    git config user.name T

    echo "init" > README.md
    git add -A
    mkcommit "init"

    git checkout -q -b feature
    echo "## new" >> README.md
    git add README.md
    mkcommit "docs: update README"

    export BASE_REF=main DEFAULT_BRANCH=main

    SB_SCRIPT="${SCRIPT_DIR}/sb.sh"
    bash "$EXTRACT" stage-b-scope "$COMMAND_MD" > "$SB_SCRIPT"
    chmod +x "$SB_SCRIPT"

    run bash "$SB_SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"0 Python"* ]]
    [[ "$output" == *"Stage B OK"* ]]
}
