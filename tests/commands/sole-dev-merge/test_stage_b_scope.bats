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
    COMMAND_MD="${REPO_ROOT}/claude-code/skills/sole-dev-merge/SKILL.md"
    EXTRACT="${REPO_ROOT}/tests/commands/sole-dev-merge/fixtures/extract_stage.sh"

    STUB_DIR="${REPO_ROOT}/tests/commands/sole-dev-merge/fixtures/bin"

    SCRIPT_DIR="$(tmp_script_dir)"
    BATS_TMP="$(mktemp -d)"
    CLI_LOG="${SCRIPT_DIR}/cli.log"; : > "$CLI_LOG"     # why: outside the repo, so Stage A sees a clean tree
    export BATS_TMP SCRIPT_DIR REPO_ROOT COMMAND_MD EXTRACT STUB_DIR CLI_LOG

    # why: the pre-commit stub logs argv + env; real ruff and git stay on PATH
    export PATH="$STUB_DIR:$PATH"
    [[ "$(command -v pre-commit)" == "$STUB_DIR/pre-commit" ]] || { echo "pre-commit stub not first on PATH" >&2; return 1; }

    [[ -f "$COMMAND_MD" ]] || { echo "Missing $COMMAND_MD" >&2; return 1; }
    [[ -x "$EXTRACT"   ]] || { echo "Missing or non-exec $EXTRACT" >&2; return 1; }
}

teardown() {
    rm -rf "$BATS_TMP" "${BATS_TMP}.bare.git" "$SCRIPT_DIR"
}

# --- Helpers for the M3 cases (sole-dev-merge-fixes M3, spec F4/F5) ----------

# A fresh shell with an empty env, like a new Bash tool call (as in test_stage_state.bats).
fresh() { env -i PATH="$PATH" HOME="$HOME" CLI_LOG="$CLI_LOG" "$@"; }
# blk NAME — extract a stage block once, print its path.
blk() {
    local f="${SCRIPT_DIR}/$1.sh"
    [[ -f "$f" ]] || bash "$EXTRACT" "$1" "$COMMAND_MD" > "$f"
    printf '%s' "$f"
}
# b_sandbox — main (a.txt, tracked out-of-scope out.txt, .pre-commit-config.yaml) and
# feature (+ app.py, which ruff reformats), with a bare origin so Stage A passes.
# NOCFG=1: no pre-commit config. EMPTY=1: feature's commit changes nothing.
# TESTSDIR=1: main has a tests/ dir, so Stage B's pytest step runs.
b_sandbox() {
    cd "$BATS_TMP"
    sandbox_init
    echo init > a.txt
    echo keep > out.txt
    [[ "${NOCFG:-0}" == 1 ]] || printf 'repos: []\n' > .pre-commit-config.yaml
    if [[ "${TESTSDIR:-0}" == 1 ]]; then mkdir tests && echo keep > tests/keep.txt; fi
    git add -A && mkcommit "init"
    git init -q --bare "${BATS_TMP}.bare.git"
    git remote add origin "${BATS_TMP}.bare.git"
    git switch -q -c feature
    if [[ "${EMPTY:-0}" != 1 ]]; then
        printf 'import os\ndef hello( ):\n    return 1\n' > app.py
        git add app.py
    fi
    mkcommit "feat: app"
}
# pc_calls — the pre-commit stub's log lines.
pc_calls() { grep '^pre-commit ' "$CLI_LOG" || true; }

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

# --- Step 5: pre-commit gets a diff range (spec F5, plan §4 M3) ---------------

@test "AC5.1: pre-commit is called once with --files and the base..HEAD refs in env" {
    b_sandbox
    fresh bash "$(blk stage-a-preflight)" >/dev/null
    run fresh bash "$(blk stage-b-scope)"
    [ "$status" -eq 0 ]
    run pc_calls
    [ "$output" = "pre-commit run --files app.py FROM=main TO=HEAD" ]
}

@test "AC5.2: pre-commit never gets --from-ref (it would stash unstaged fixes)" {
    b_sandbox
    fresh bash "$(blk stage-a-preflight)" >/dev/null
    run fresh bash "$(blk stage-b-scope)"
    [ "$status" -eq 0 ]
    [ "$(pc_calls | grep -c .)" -eq 1 ]    # why: non-vacuous — the stub did run
    [ "$(pc_calls | grep -c -- '--from-ref')" -eq 0 ]
    run grep -c -- '--from-ref' "$(blk stage-b-scope)"
    [ "$output" = 0 ]
}

@test "AC5.3: a failing pre-commit prints its rc and Stage B still passes" {
    b_sandbox
    fresh bash "$(blk stage-a-preflight)" >/dev/null
    run fresh PRE_COMMIT_RC=1 bash "$(blk stage-b-scope)"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Stage B: pre-commit rc=1 (best-effort)"* ]]
    [[ "$output" == *"Stage B OK"* ]]
}

@test "AC5.4: no .pre-commit-config.yaml → pre-commit is not called" {
    NOCFG=1 b_sandbox
    fresh bash "$(blk stage-a-preflight)" >/dev/null
    run fresh bash "$(blk stage-b-scope)"
    [ "$status" -eq 0 ]
    [ -z "$(pc_calls)" ]
}

@test "AC5.4: no changed files → pre-commit is not called" {
    EMPTY=1 b_sandbox
    fresh bash "$(blk stage-a-preflight)" >/dev/null
    run fresh bash "$(blk stage-b-scope)"
    [ "$status" -eq 0 ]
    [[ "$output" == *"0 file(s)"* ]]
    [ -z "$(pc_calls)" ]
}

# --- Step 4: pytest's rc is printed (spec Q8) ---------------------------------

@test "Q8: Stage B prints pytest's rc and stays best-effort" {
    TESTSDIR=1 b_sandbox
    # why: a per-test uv stub, so a shared one never shadows real uv in other suites
    mkdir -p "${SCRIPT_DIR}/uvbin"
    printf '#!/usr/bin/env bash\necho "uv $*" >> "%s"\n[[ "$1 $2" == "run pytest" ]] && exit 3\nexit 0\n' \
        "$CLI_LOG" > "${SCRIPT_DIR}/uvbin/uv"
    chmod +x "${SCRIPT_DIR}/uvbin/uv"
    fresh bash "$(blk stage-a-preflight)" >/dev/null
    run fresh PATH="${SCRIPT_DIR}/uvbin:$PATH" bash "$(blk stage-b-scope)"
    [ "$status" -eq 0 ]
    grep -q '^uv run pytest' "$CLI_LOG"    # why: non-vacuous — the stub, not real uv, ran
    [[ "$output" == *"Stage B: pytest rc=3 (best-effort)"* ]]
    [[ "$output" == *"Stage B OK"* ]]
}

# --- L-007 guard: staged and untracked out-of-scope rows (spec F4.1) -----------

@test "L-007 guard restores a staged out-of-scope edit to HEAD" {
    b_sandbox
    fresh bash "$(blk stage-a-preflight)" >/dev/null
    echo drifted >> out.txt
    git add out.txt
    run fresh bash "$(blk stage-b-scope)"
    [ "$status" -eq 0 ]
    git diff --cached --quiet -- out.txt
    git diff --quiet -- out.txt
    [ "$(cat out.txt)" = keep ]
}

@test "L-007 guard leaves an untracked out-of-scope file in place and lists it" {
    b_sandbox
    fresh bash "$(blk stage-a-preflight)" >/dev/null
    echo operator > stray.txt
    run fresh bash "$(blk stage-b-scope)"
    [ "$status" -eq 0 ]
    [ "$(cat stray.txt)" = operator ]
    [[ "$output" == *"L-007 guard: untracked out-of-scope file(s) left unstaged: stray.txt"* ]]
}

@test "L-007 guard unstages a staged NEW out-of-scope file but never deletes it" {
    # why: restore --source=HEAD on a path HEAD lacks deletes the file with rc 0 (probed)
    b_sandbox
    fresh bash "$(blk stage-a-preflight)" >/dev/null
    echo operator > newstaged.txt
    git add newstaged.txt
    run fresh bash "$(blk stage-b-scope)"
    [ "$status" -eq 0 ]
    [ "$(cat newstaged.txt)" = operator ]
    [ "$(git status --porcelain -- newstaged.txt)" = "?? newstaged.txt" ]
    [[ "$output" == *"L-007 guard: untracked out-of-scope file(s) left unstaged: newstaged.txt"* ]]
}

# --- B-commit: only in-scope paths, staged-set assert (spec F4.2-F4.4) --------

@test "AC4.1: B-commit leaves an untracked out-of-scope file out of the commit and on disk" {
    b_sandbox
    fresh bash "$(blk stage-a-preflight)" >/dev/null
    fresh bash "$(blk stage-b-scope)" >/dev/null
    echo operator > stray.txt
    run fresh bash "$(blk stage-b-commit)"
    [ "$status" -eq 0 ]
    [[ "$output" == *"committed in-scope auto-fixes"* ]]
    run git show --name-only --format= HEAD
    [[ "$output" != *"stray.txt"* ]]
    [ "$(cat stray.txt)" = operator ]
    [ "$(git status --porcelain)" = "?? stray.txt" ]
}

@test "AC4.2: B-commit commits the in-scope ruff fix" {
    b_sandbox
    fresh bash "$(blk stage-a-preflight)" >/dev/null
    fresh bash "$(blk stage-b-scope)" >/dev/null
    BEFORE=$(git rev-parse HEAD)
    run fresh bash "$(blk stage-b-commit)"
    [ "$status" -eq 0 ]
    [ "$(git rev-parse HEAD)" != "$BEFORE" ]
    [ "$(git show --name-only --format= HEAD)" = app.py ]
    git show HEAD:app.py | grep -q 'def hello():'
    [ -z "$(git status --porcelain)" ]
}

@test "AC4.4: an out-of-scope file already staged makes B-commit ABORT with no commit" {
    b_sandbox
    fresh bash "$(blk stage-a-preflight)" >/dev/null
    fresh bash "$(blk stage-b-scope)" >/dev/null
    echo drifted >> out.txt
    git add out.txt
    BEFORE=$(git rev-parse HEAD)
    run fresh bash "$(blk stage-b-commit)"
    [ "$status" -eq 1 ]
    [[ "$output" == *"ABORT: Stage B-commit staged files outside the intended list"* ]]
    [ "$(git rev-parse HEAD)" = "$BEFORE" ]
    [ -z "$(git diff --cached --name-only)" ]
}
