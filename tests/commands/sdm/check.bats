#!/usr/bin/env bats
# check.bats — `sdm.sh check`, the shared preflight, and `sdm.sh help` (sole-dev-merge-simplify 1.1).
#
# Ported from tests/commands/sole-dev-merge/ (test_stage_a_preflight, test_stage_b_scope,
# test_smoke_e2e, test_stage_state); the old suite's file:line is in each test's comment.
# Old Stage B restored out-of-scope files; `check` instead ABORTs naming them and leaves them
# exactly as they are. `check` also refuses a dirty tree at START, so every drift here is made
# DURING check, by the pre-commit stub's PRE_COMMIT_RUN (it runs after ruff, before the scope check).
#
# Texts are the spec's (sdm-spec.md); stdout is asserted exactly with --separate-stderr.
# Commits in a test are plumbing only (mkcommit): a PreToolUse hook blocks the porcelain command.

bats_require_minimum_version 1.5.0

load fixtures/helpers

setup() {
    local real_ruff s
    real_ruff=$(command -v ruff) || { echo "ruff not on PATH" >&2; return 1; }
    sdm_setup
    # why: a logging wrapper around the real ruff, so a test can see which names ruff got
    mkdir -p "$BATS_TEST_TMPDIR/bin"
    printf '#!/usr/bin/env bash\n{ printf ruff; printf " %%q" "$@"; echo; } >> "$CLI_LOG"\nexec %q "$@"\n' \
        "$real_ruff" > "$BATS_TEST_TMPDIR/bin/ruff"
    # why: check must never run these; stubs log any call so a test can assert there was none
    for s in pytest mypy shellcheck uv; do
        printf '#!/usr/bin/env bash\n{ printf %s; printf " %%q" "$@"; echo; } >> "$CLI_LOG"\nexit 0\n' "$s" \
            > "$BATS_TEST_TMPDIR/bin/$s"
    done
    chmod +x "$BATS_TEST_TMPDIR"/bin/*
    export PATH="$BATS_TEST_TMPDIR/bin:$PATH"
}

# --- helpers -----------------------------------------------------------------

# base_and_branch — commit the work tree on main, push it, and restart `feature` from it.
base_and_branch() {
    git add -A
    mkcommit "init: baseline"
    git push -q origin main
    git checkout -q -B feature
}

# b_sandbox — main (a.txt, tracked out-of-scope out.txt, .pre-commit-config.yaml) and
# feature (+ app.py, which ruff reformats). Knobs, as in the old suite:
#   NOCFG=1 no pre-commit config; EMPTY=1 feature's commit changes nothing;
#   CLEAN=1 app.py is already ruff-clean; MAIN_EXTRA / FEATURE_EXTRA newline-separated
#   file names (content "keep") added on main / feature.
b_sandbox() {
    local f
    git checkout -q main
    echo keep > out.txt
    [[ "${NOCFG:-0}" == 1 ]] || printf 'repos: []\n' > .pre-commit-config.yaml
    while IFS= read -r f; do [[ -z "$f" ]] || echo keep > "$f"; done <<< "${MAIN_EXTRA:-}"
    base_and_branch
    if [[ "${EMPTY:-0}" != 1 ]]; then
        if [[ "${CLEAN:-0}" == 1 ]]; then
            printf 'def hello():\n    return 1\n' > app.py
        else
            printf 'import os\ndef hello( ):\n    return 1\n' > app.py
        fi
        git add app.py
        while IFS= read -r f; do [[ -z "$f" ]] || { echo keep > "$f"; git add -- "$f"; }; done <<< "${FEATURE_EXTRA:-}"
    fi
    mkcommit "feat: app"
}

pc_calls() { grep '^pre-commit ' "$CLI_LOG" || true; }      # why: grep exits 1 on no match
ruff_calls() { grep '^ruff ' "$CLI_LOG" || true; }          # why: grep exits 1 on no match
outside() { printf 'ABORT: check: files outside the branch changed: %s(left as they are)' "$(printf '%q ' "$@")"; }
check_ok() { printf 'check OK (branch=feature, base=main, ahead=%s)' "$1"; }

# =============================================================================
# Shared preflight (old test_stage_a_preflight.bats, test_stage_state.bats)
# =============================================================================

@test "ABORT on main branch (a_preflight:35)" {
    git checkout -q main
    run --separate-stderr "$SDM" check
    [ "$status" -eq 1 ]
    [ "$output" = "ABORT: Cannot run /sole-dev-merge from main branch" ]
}

@test "ABORT on master branch (a_preflight:49)" {
    git checkout -q -b master main
    run --separate-stderr "$SDM" check
    [ "$status" -eq 1 ]
    [ "$output" = "ABORT: Cannot run /sole-dev-merge from master branch" ]
}

@test "ABORT on dirty working tree (a_preflight:62)" {
    echo uncommitted > c.txt
    run --separate-stderr "$SDM" check
    [ "$status" -eq 1 ]
    [ "$output" = "ABORT: Uncommitted changes detected (commit or stash first)" ]
    [ "$(cat c.txt)" = uncommitted ]
}

@test "ABORT when no git remote is configured (a_preflight:78, new text)" {
    git remote remove origin
    run --separate-stderr "$SDM" check
    [ "$status" -eq 1 ]
    [ "$output" = "ABORT: No git remote configured (need a github.com origin)" ]
}

@test "ABORT when the branch has no commits ahead of main (a_preflight:95)" {
    git checkout -q -B feature main
    run --separate-stderr "$SDM" check
    [ "$status" -eq 1 ]
    [ "$output" = "ABORT: No commits ahead of main (nothing to merge)" ]
}

@test "happy path prints only the check OK line (a_preflight:112)" {
    BEFORE=$(git rev-parse HEAD)
    run --separate-stderr "$SDM" check
    [ "$status" -eq 0 ]
    [ "$output" = "$(check_ok 1)" ]
    [ "$(git rev-parse HEAD)" = "$BEFORE" ]
}

# _default_branch NAME — origin/HEAD → origin/NAME at main's commit.
_default_branch() {
    git update-ref "refs/remotes/origin/$1" main
    git symbolic-ref refs/remotes/origin/HEAD "refs/remotes/origin/$1"
}

@test "ABORT on the remote's default branch when it is not main/master (a_preflight:148)" {
    _default_branch trunk
    git checkout -q -b trunk main
    echo more > c.txt && git add c.txt
    mkcommit "work on trunk"
    run --separate-stderr "$SDM" check
    [ "$status" -eq 1 ]
    [ "$output" = "ABORT: Cannot run /sole-dev-merge from trunk branch" ]
}

@test "ABORT when the remote's default branch is not a valid branch name (a_preflight:159)" {
    # why: refs/remotes/origin/-x is a legal ref and can be origin/HEAD (probed in the old suite)
    _default_branch -x
    run --separate-stderr "$SDM" check
    [ "$status" -eq 1 ]
    [ "$output" = "ABORT: DEFAULT_BRANCH '-x' is not a valid branch name" ]
}

@test "outside a git repository prints an ABORT line and exits 1 (state:297)" {
    mkdir "$BATS_TEST_TMPDIR/norepo"
    cd "$BATS_TEST_TMPDIR/norepo"
    # why: the ceiling stops git finding a repo above the test dir
    export GIT_CEILING_DIRECTORIES="$BATS_TEST_TMPDIR"
    run --separate-stderr "$SDM" check
    [ "$status" -eq 1 ]
    [ "$output" = "ABORT: Not inside a git repository" ]
}

@test "refuses a detached HEAD (state:306)" {
    git switch -q --detach
    run --separate-stderr "$SDM" check
    [ "$status" -eq 1 ]
    [ "$output" = "ABORT: Detached HEAD — check out the branch to merge" ]
}

# =============================================================================
# check: scope, fixers, out-of-scope ABORT (old test_stage_b_scope.bats)
# =============================================================================

@test "reformats and commits an in-scope Python file; ruff gets only in-scope .py (b_scope:87)" {
    git checkout -q main
    mkdir -p tests/codemem src
    echo "def existing(): return 1" > tests/codemem/foo.py
    echo "def already(): pass" > src/already_there.py
    base_and_branch
    printf 'import os\ndef hello( ):\n    return 1\n' > src/new_file.py
    git add src/new_file.py
    mkcommit "feat: add new_file"

    run --separate-stderr "$SDM" check
    [ "$status" -eq 0 ]
    [ "${lines[-1]}" = "$(check_ok 2)" ]
    run ruff check src/new_file.py
    [ "$status" -eq 0 ]
    grep -q '^def hello():' src/new_file.py
    [ -z "$(git status --porcelain)" ]
    [ -n "$(ruff_calls | grep -F 'src/new_file.py')" ]     # why: non-vacuous — ruff ran on it
    [ -z "$(ruff_calls | grep -e foo.py -e already_there)" ]
}

@test "new (§6.8 CRITICAL): a ruff-excluded .py the branch touches is left byte-identical, nothing committed" {
    # why: a named file bypasses extend-exclude unless --force-exclude; planted eval fixtures must survive (ADR-0021)
    git checkout -q main
    printf '[tool.ruff]\nextend-exclude = ["fixtures"]\n' > pyproject.toml
    base_and_branch
    mkdir -p fixtures
    printf 'import os\nimport subprocess\ndef run( cmd ):\n    return subprocess.run(cmd)\n' > fixtures/planted.py   # planted: F401 + format
    git add fixtures/planted.py
    mkcommit "test: planted fixture"
    BEFORE=$(git rev-parse HEAD)
    run ruff check --diff -- fixtures/planted.py
    [ "$status" -ne 0 ]                                          # why: non-vacuous — ruff would rewrite it if named
    run ruff format --check -- fixtures/planted.py
    [ "$status" -ne 0 ]

    run --separate-stderr "$SDM" check
    [ "$status" -eq 0 ]
    [ "$(git rev-parse HEAD)" = "$BEFORE" ]
    [ "$(git show HEAD:fixtures/planted.py)" = "$(cat fixtures/planted.py)" ]
    [ -z "$(git status --porcelain)" ]
}

@test "out-of-scope drift from a fixer ABORTs, left as it is, nothing committed (b_scope:130, changed)" {
    git checkout -q main
    mkdir -p tests/codemem src
    printf '# Pre-existing on main; feature must not touch this\ndef existing():\n    return 1\n' > tests/codemem/foo.py
    echo "" > src/keep.py
    printf 'repos: []\n' > .pre-commit-config.yaml
    base_and_branch
    printf 'import os\ndef hello( ):\n    return 2\n' > src/new_file.py
    git add src/new_file.py
    mkcommit "feat: new_file"
    BEFORE=$(git rev-parse HEAD)
    export PRE_COMMIT_RUN='echo "# drifted" >> tests/codemem/foo.py'

    run --separate-stderr "$SDM" check
    [ "$status" -eq 1 ]
    [ "${lines[-1]}" = "$(outside tests/codemem/foo.py)" ]
    [ "$(tail -n1 tests/codemem/foo.py)" = "# drifted" ]      # not restored
    [ "$(git rev-parse HEAD)" = "$BEFORE" ]
    git diff --cached --quiet                                  # nothing staged
    [ "$(git status --porcelain)" = $' M src/new_file.py\n M tests/codemem/foo.py' ]
}

@test "no drift → no ABORT and check OK (b_scope:180, changed)" {
    git checkout -q main
    mkdir -p src
    echo "" > src/keep.py
    base_and_branch
    printf 'def f():\n    return 1\n' > src/already_clean.py
    git add src/already_clean.py
    mkcommit "feat: already_clean"
    BEFORE=$(git rev-parse HEAD)

    run --separate-stderr "$SDM" check
    [ "$status" -eq 0 ]
    [[ "$output" != *ABORT* ]]
    [ "$output" = "$(check_ok 1)" ]
    [ "$(git rev-parse HEAD)" = "$BEFORE" ]
}

@test "a branch with zero Python changes (only .md) passes without calling ruff (b_scope:211)" {
    git checkout -q main
    echo init > README.md
    base_and_branch
    echo "## new" >> README.md
    git add README.md
    mkcommit "docs: update README"

    run --separate-stderr "$SDM" check
    [ "$status" -eq 0 ]
    [ "$output" = "$(check_ok 1)" ]
    [ -z "$(ruff_calls)" ]
}

# --- pre-commit gets a diff range (old spec F5) -------------------------------

@test "pre-commit is called once with --files and the base..HEAD refs in env (b_scope:240)" {
    b_sandbox
    run --separate-stderr "$SDM" check
    [ "$status" -eq 0 ]
    run pc_calls
    [ "$output" = "pre-commit run --files ./app.py FROM=main TO=HEAD" ]
}

@test "file names reach pre-commit as single ./-prefixed arguments, never as options (b_scope:249)" {
    # why: pre-commit's argparse reads a bare '--config=x' as a flag and rejects '--' (probed)
    FEATURE_EXTRA=$'--config=evil.yaml\nsp ace.txt' b_sandbox
    run --separate-stderr "$SDM" check
    [ "$status" -eq 0 ]
    run pc_calls
    [ "$output" = 'pre-commit run --files ./--config=evil.yaml ./app.py ./sp\ ace.txt FROM=main TO=HEAD' ]
}

@test "pre-commit never gets --from-ref or --to-ref (b_scope:259)" {
    b_sandbox
    run --separate-stderr "$SDM" check
    [ "$status" -eq 0 ]
    [ "$(pc_calls | grep -c .)" -eq 1 ]    # why: non-vacuous — the stub did run
    [ "$(pc_calls | grep -c -e '--from-ref' -e '--to-ref')" -eq 0 ]
    run grep -c -e '--from-ref' -e '--to-ref' <(grep -vE '^[[:space:]]*#' "$SDM")
    [ "$output" = 0 ]
}

@test "a failing pre-commit prints its rc and check still passes (b_scope:270)" {
    b_sandbox
    export PRE_COMMIT_RC=1
    run --separate-stderr "$SDM" check
    [ "$status" -eq 0 ]
    [ "${lines[0]}" = "check: pre-commit rc=1" ]
    [ "${lines[-1]}" = "$(check_ok 2)" ]
}

@test "no .pre-commit-config.yaml → pre-commit is not called (b_scope:279)" {
    NOCFG=1 b_sandbox
    run --separate-stderr "$SDM" check
    [ "$status" -eq 0 ]
    [ -z "$(pc_calls)" ]
    [ "$output" = "$(check_ok 2)" ]
}

@test "no changed files → pre-commit is not called (b_scope:287)" {
    EMPTY=1 b_sandbox
    run --separate-stderr "$SDM" check
    [ "$status" -eq 0 ]
    [ -z "$(pc_calls)" ]
    [ "$output" = "$(check_ok 1)" ]
}

# --- out-of-scope rows: staged, untracked, renamed (old spec F4.1; now ABORT) -----

@test "a staged out-of-scope edit ABORTs; index and file left as they are (b_scope:315, changed)" {
    b_sandbox
    BEFORE=$(git rev-parse HEAD)
    export PRE_COMMIT_RUN='echo drifted >> out.txt; git add out.txt'
    run --separate-stderr "$SDM" check
    [ "$status" -eq 1 ]
    [ "${lines[-1]}" = "$(outside out.txt)" ]
    [ "$(git rev-parse HEAD)" = "$BEFORE" ]
    [ "$(git diff --cached --name-only)" = out.txt ]
    [ "$(cat out.txt)" = $'keep\ndrifted' ]
}

@test "an untracked out-of-scope file ABORTs and stays in place (b_scope:327, changed)" {
    b_sandbox
    BEFORE=$(git rev-parse HEAD)
    export PRE_COMMIT_RUN='echo operator > stray.txt'
    run --separate-stderr "$SDM" check
    [ "$status" -eq 1 ]
    [ "${lines[-1]}" = "$(outside stray.txt)" ]
    [ "$(cat stray.txt)" = operator ]
    [ "$(git rev-parse HEAD)" = "$BEFORE" ]
    [ "$(git status --porcelain -- stray.txt)" = "?? stray.txt" ]
}

@test "an out-of-scope file whose name has a space is named %q-quoted and left dirty (b_scope:337, changed)" {
    # why: porcelain v1 C-quotes such a name; the old 3-char strip gave '"out file.txt"'
    MAIN_EXTRA='out file.txt' b_sandbox
    export PRE_COMMIT_RUN="echo drifted >> 'out file.txt'"
    run --separate-stderr "$SDM" check
    [ "$status" -eq 1 ]
    [ "${lines[-1]}" = 'ABORT: check: files outside the branch changed: out\ file.txt (left as they are)' ]
    [ "$(cat 'out file.txt')" = $'keep\ndrifted' ]
}

@test "an out-of-scope staged rename ABORTs naming both ends; neither file lost (b_scope:348, changed)" {
    b_sandbox
    BEFORE=$(git rev-parse HEAD)
    export PRE_COMMIT_RUN='git mv out.txt moved.txt'
    run --separate-stderr "$SDM" check
    [ "$status" -eq 1 ]
    [[ "${lines[-1]}" == "ABORT: check: files outside the branch changed: "*"(left as they are)" ]]
    [[ "${lines[-1]}" == *" out.txt "* || "${lines[-1]}" == *": out.txt "* ]]
    [[ "${lines[-1]}" == *"moved.txt "* ]]
    [ "$(cat moved.txt)" = keep ]
    [ "$(git status --porcelain -- out.txt moved.txt)" = "R  out.txt -> moved.txt" ]   # left as it was
    [ "$(git rev-parse HEAD)" = "$BEFORE" ]
}

@test "a staged NEW out-of-scope file ABORTs and stays staged and on disk (b_scope:360, changed)" {
    b_sandbox
    export PRE_COMMIT_RUN='echo operator > newstaged.txt; git add newstaged.txt'
    run --separate-stderr "$SDM" check
    [ "$status" -eq 1 ]
    [ "${lines[-1]}" = "$(outside newstaged.txt)" ]
    [ "$(cat newstaged.txt)" = operator ]
    [ "$(git status --porcelain -- newstaged.txt)" = "A  newstaged.txt" ]
}

@test "a worktree rename (Y=R, intent-to-add) is read as one record; both ends named, none lost (b_scope:373, changed)" {
    # why: `mv` + `git add -N` gives " R moved.txt\0out.txt\0" (probed, git 2.53)
    b_sandbox
    export PRE_COMMIT_RUN='mv out.txt moved.txt; git add -N moved.txt'
    run --separate-stderr "$SDM" check
    [ "$status" -eq 1 ]
    [ "$(git status --porcelain -- out.txt moved.txt)" = " R out.txt -> moved.txt" ]   # non-vacuous: Y=R, left as it was
    [[ "${lines[-1]}" == "ABORT: check: files outside the branch changed: "*"(left as they are)" ]]
    [[ "${lines[-1]}" == *" out.txt "* || "${lines[-1]}" == *": out.txt "* ]]
    [[ "${lines[-1]}" == *"moved.txt "* ]]
    [[ "${lines[-1]}" != *".txt .txt"* && "${lines[-1]}" != *": .txt"* ]]   # why: the old bug parsed a path ".txt"
    [ "$(cat moved.txt)" = keep ]
}

# --- the auto-fix commit (old spec F4.2-F4.4, B-commit) ------------------------

@test "an untracked out-of-scope file never enters a commit and stays on disk (b_scope:392, now ABORT)" {
    # why: the old B-commit committed the in-scope fix beside an untracked stray; under the
    # spec an untracked out-of-scope path (??) ABORTs before anything is committed
    b_sandbox
    BEFORE=$(git rev-parse HEAD)
    export PRE_COMMIT_RUN='echo operator > stray.txt'
    run --separate-stderr "$SDM" check
    [ "$status" -eq 1 ]
    [ "${lines[-1]}" = "$(outside stray.txt)" ]
    [ "$(git rev-parse HEAD)" = "$BEFORE" ]
    [ -z "$(git log --format= --name-only main..HEAD | grep stray.txt)" ]
    [ "$(cat stray.txt)" = operator ]
    [ "$(git status --porcelain)" = $' M app.py\n?? stray.txt' ]
}

@test "commits the in-scope ruff fix as one chore(scope) commit (b_scope:406)" {
    b_sandbox
    BEFORE=$(git rev-parse HEAD)
    run --separate-stderr "$SDM" check
    [ "$status" -eq 0 ]
    [ "${lines[-1]}" = "$(check_ok 2)" ]
    [ "$(git rev-parse HEAD~1)" = "$BEFORE" ]
    [ "$(git show --name-only --format= HEAD)" = app.py ]
    [ "$(git log -1 --format=%s)" = "chore(scope): pre-PR auto-fixes" ]
    git show HEAD:app.py | grep -q 'def hello():'
    [ -z "$(git status --porcelain)" ]
}

@test "an out-of-scope file staged by a fixer ABORTs with no commit and the index untouched (b_scope:419, changed)" {
    # why: in the old suite the operator pre-staged it; check now refuses a dirty start, so a fixer stages it
    b_sandbox
    BEFORE=$(git rev-parse HEAD)
    export PRE_COMMIT_RUN='echo drifted >> out.txt; git add out.txt'
    run --separate-stderr "$SDM" check
    [ "$status" -eq 1 ]
    [ "${lines[-1]}" = "$(outside out.txt)" ]
    [ "$(git rev-parse HEAD)" = "$BEFORE" ]
    [ "$(git diff --cached --name-only)" = out.txt ]     # app.py's ruff fix was not staged
    [ -n "$(git diff --name-only -- app.py)" ]
}

@test "an out-of-scope staged file ABORTs even when nothing in scope is dirty (b_scope:434, changed)" {
    # why: the old test used NOCFG=1 and pre-staged; the drift now needs the pre-commit stub, so CLEAN=1 only
    CLEAN=1 b_sandbox
    BEFORE=$(git rev-parse HEAD)
    export PRE_COMMIT_RUN='echo drifted >> out.txt; git add out.txt'
    run --separate-stderr "$SDM" check
    [ "$status" -eq 1 ]
    [ "${lines[-1]}" = "$(outside out.txt)" ]
    [ -z "$(git status --porcelain -- app.py)" ]        # non-vacuous: nothing in scope was dirty
    [ "$(git rev-parse HEAD)" = "$BEFORE" ]
    [ "$(git diff --cached --name-only)" = out.txt ]
}

@test "a staged out-of-scope deletion paired by rename detection still ABORTs (b_scope:464, changed)" {
    # why: with renames on, --name-only names only the destination, hiding the deleted source
    MAIN_EXTRA='gone.txt' b_sandbox
    git rm -q gone.txt && mkcommit "feat: drop gone"    # gone.txt is in scope (deleted by the branch)
    BEFORE=$(git rev-parse HEAD)
    export PRE_COMMIT_RUN='git rm -q out.txt; echo keep > gone.txt; git add gone.txt'
    run --separate-stderr "$SDM" check
    [ "$status" -eq 1 ]
    [[ "$(git status --porcelain)" == *"R  out.txt -> gone.txt"* ]]    # non-vacuous: git paired them; left as is
    [ "${lines[-1]}" = "$(outside out.txt)" ]
    [ "$(git rev-parse HEAD)" = "$BEFORE" ]
}

@test "an in-scope file whose staged change was undone is not an ABORT and makes no commit (b_scope:480)" {
    # why: CLEAN=1 so ruff changes nothing whatever its order; the stub stages a fix, then undoes it in the tree
    CLEAN=1 b_sandbox
    BEFORE=$(git rev-parse HEAD)
    export PRE_COMMIT_RUN='echo "# fix" >> app.py; git add app.py; git show HEAD:app.py > app.py'
    run --separate-stderr "$SDM" check
    [ "$status" -eq 0 ]
    [[ "$output" != *ABORT* ]]
    [ "${lines[-1]}" = "$(check_ok 1)" ]
    [ "$(git rev-parse HEAD)" = "$BEFORE" ]
}

@test "an in-scope name that looks like a glob matches only itself (b_scope:494, changed)" {
    # why: a glob '*.txt' in scope must not pull out.txt into scope; out.txt's drift is the ABORT
    FEATURE_EXTRA='*.txt' b_sandbox
    BEFORE=$(git rev-parse HEAD)
    export PRE_COMMIT_RUN='echo changed > "*.txt"; echo drifted >> out.txt'
    run --separate-stderr "$SDM" check
    [ "$status" -eq 1 ]
    [ "${lines[-1]}" = "$(outside out.txt)" ]
    [ "$(git rev-parse HEAD)" = "$BEFORE" ]
    [ "$(git status --porcelain -- out.txt)" = " M out.txt" ]
    [ "$(cat '*.txt')" = changed ]
}

@test "commits an in-scope file with a non-ASCII name (b_scope:508)" {
    FEATURE_EXTRA='café.txt' b_sandbox
    export PRE_COMMIT_RUN="echo changed > 'café.txt'"
    run --separate-stderr "$SDM" check
    [ "$status" -eq 0 ]
    [ "${lines[-1]}" = "$(check_ok 2)" ]
    run git -c core.quotePath=false show --name-only --format= HEAD
    [[ "$output" == *"café.txt"* ]]
    [ -z "$(git status --porcelain)" ]
}

# =============================================================================
# End to end (old test_smoke_e2e.bats:87)
# =============================================================================

@test "smoke: an in-scope ruff fix is committed with the footer and check OK (smoke_e2e:87, changed)" {
    git checkout -q main
    mkdir -p tests/codemem src
    echo "# pre-existing out-of-scope file" > tests/codemem/dummy.py
    echo "ok = 1" > src/existing.py
    printf 'repos: []\n' > .pre-commit-config.yaml
    base_and_branch
    printf "import os\ndef hello( ):\n    return os.path.join('a','b')\n" > src/new_feature.py
    git add src/new_feature.py
    mkcommit "feat: add new_feature"
    BASE=$(git rev-parse HEAD)

    run --separate-stderr "$SDM" check
    [ "$status" -eq 0 ]
    [ "$output" = $'check: pre-commit rc=0\n'"$(check_ok 2)" ]
    [ "$(git rev-parse HEAD~1)" = "$BASE" ]
    [ "$(git log -1 --format=%B)" = $'chore(scope): pre-PR auto-fixes\n\n[ad-hoc]' ]
    [ "$(git show --name-only --format= HEAD)" = src/new_feature.py ]
    grep -q '^def hello():' src/new_feature.py
    git diff --quiet main HEAD -- tests/codemem/dummy.py src/existing.py
    [ -z "$(git status --porcelain)" ]
}

# =============================================================================
# New tests
# =============================================================================

@test "new: check from a subdirectory uses the toplevel; ruff and pre-commit get repo-relative names" {
    git checkout -q main
    mkdir -p src
    echo "" > src/keep.py
    printf 'repos: []\n' > .pre-commit-config.yaml
    base_and_branch
    printf 'import os\ndef hello( ):\n    return 1\n' > src/app.py
    git add src/app.py
    mkcommit "feat: app"

    cd src
    run --separate-stderr "$SDM" check
    [ "$status" -eq 0 ]
    [ "${lines[-1]}" = "$(check_ok 2)" ]
    [ "$(pc_calls)" = "pre-commit run --files ./src/app.py FROM=main TO=HEAD" ]
    [ -n "$(ruff_calls)" ]
    [ -z "$(ruff_calls | grep -v ' src/app\.py$')" ]     # every ruff call names src/app.py, from the top
    [ "$(git show --name-only --format= HEAD)" = src/app.py ]
    [ -z "$(git status --porcelain)" ]
}

# frag_key TEXT PLACEHOLDER_RE — the literal prefix of TEXT before the first placeholder; when that is
# shorter than 12 chars (e.g. "$1: …", "finish: <n> …"), the longest literal fragment instead. Trimmed.
frag_key() {
    local text=$1 re=$2 pre best="" f
    pre=$(sed -E "s/${re}.*//" <<<"$text")
    pre=$(sed -E "s/^[[:space:]'\":]+//; s/[[:space:]'\"]+$//" <<<"$pre")
    if ((${#pre} >= 12)); then printf '%s' "$pre"; return; fi
    while IFS= read -r f; do
        f=$(sed -E "s/^[[:space:]'\":,(]+//; s/[[:space:]'\",(]+$//" <<<"$f")
        ((${#f} > ${#best})) && best=$f
    done < <(sed -E "s/${re}/\n/g" <<<"$text")
    printf '%s' "$best"
}

@test "new: sdm.sh help's exit table matches every STATUS and ABORT text the script prints" {
    local code help rows tok m key row n_abort=0 n_status=0
    run --separate-stderr "$SDM" help
    [ "$status" -eq 0 ]
    help=$output
    for alt in -h --help; do
        run --separate-stderr "$SDM" "$alt"
        [ "$status" -eq 0 ]
        [ "$output" = "$help" ]
    done
    run --separate-stderr "$SDM"
    [ "$status" -eq 0 ]
    [ "$output" = "$help" ]
    run --separate-stderr "$SDM" bogus
    [ "$status" -eq 1 ]
    [ "$output" = "ABORT: unknown subcommand 'bogus' (see sdm.sh help)" ]

    # the rows: "<STATUS-or-ABORT text> | <meaning>"
    rows=$(grep -E '^(STATUS|ABORT): .* \| ' <<<"$help" | sed 's/ | .*//')
    [ "$(grep -c '^STATUS: ' <<<"$rows")" -ge 5 ]
    [ "$(grep -c '^ABORT: ' <<<"$rows")" -ge 10 ]
    # the script's code: no comment lines, no exit table (else every row would match itself)
    code=$(sed '/^# exit-table:begin$/,/^# exit-table:end$/d' "$SDM" | grep -vE '^[[:space:]]*#')

    # script → table
    while IFS= read -r tok; do
        n_status=$((n_status + 1))
        grep -qE "^${tok}([^A-Z_]|$)" <<<"$rows" || { echo "no help row for '$tok'"; return 1; }
    done < <(grep -oE 'STATUS: [A-Z_]+' <<<"$code" | sort -u)
    while IFS= read -r m; do
        [[ -n "$m" ]] || continue
        n_abort=$((n_abort + 1))
        key=$(frag_key "$m" '\$(\{[^}]*\}|\([^)]*\)|\(.*|[A-Za-z_][A-Za-z0-9_]*|[0-9@*#?])')
        [[ -n "$key" ]] || { echo "no literal text in ABORT message '$m'"; return 1; }
        grep '^ABORT: ' <<<"$rows" | grep -qF -- "$key" || { echo "no help row for ABORT '$m' (key '$key')"; return 1; }
    done < <({ grep -oE "\bdie \"[^\"]*" <<<"$code" | sed 's/^die "//'
               grep -oE "\bdie '[^']*" <<<"$code" | sed "s/^die '//"
               grep -oE '"ABORT: [^"%]+' <<<"$code" | sed 's/^"ABORT: //'; } | sort -u)
    [ "$n_status" -ge 5 ]       # why: non-vacuous — the scan found the script's lines
    [ "$n_abort" -ge 10 ]

    # table → script
    while IFS= read -r row; do
        if [[ "$row" == STATUS:* ]]; then
            tok=$(grep -oE '^STATUS: [A-Z_]+' <<<"$row")
            grep -qE "${tok}([^A-Z_]|$)" <<<"$code" || { echo "help row '$row' not in the script"; return 1; }
        else
            m=${row#ABORT: }
            key=$(frag_key "$m" '<[^>]*>')
            grep -qF -- "$key" <<<"$code" \
                || grep -qF -- "$(sed -E 's/^(check|ship|finish): //' <<<"$key")" <<<"$code" \
                || { echo "help row '$row' (key '$key') not in the script"; return 1; }
        fi
    done <<<"$rows"
}

@test "new: out-of-scope names with a quote, a backslash or a tab are %q-quoted in the ABORT line" {
    # carried TODO: porcelain C-quotes such names; the ABORT line must name the real file, with no raw control chars
    Q_NAME='q"b\s.txt' T_NAME=$'t\tab.txt'
    export Q_NAME T_NAME
    git checkout -q main
    echo keep > "$Q_NAME"; echo keep > "$T_NAME"
    printf 'repos: []\n' > .pre-commit-config.yaml
    base_and_branch
    echo feat > app.txt && git add app.txt && mkcommit "feat: app"
    BEFORE=$(git rev-parse HEAD)
    export PRE_COMMIT_RUN='echo drifted >> "$Q_NAME"; echo drifted >> "$T_NAME"'

    run --separate-stderr "$SDM" check
    [ "$status" -eq 1 ]
    [ "${lines[-1]}" = "$(outside "$Q_NAME" "$T_NAME")" ]
    [[ "${lines[-1]}" != *[[:cntrl:]]* ]]
    [ "$(cat "$Q_NAME")" = $'keep\ndrifted' ]
    [ "$(cat "$T_NAME")" = $'keep\ndrifted' ]
    [ "$(git rev-parse HEAD)" = "$BEFORE" ]
}

@test "new: in-scope names with a double quote, fixed by ruff and by pre-commit, are committed" {
    local -a got
    PY_NAME='b"ad.py' TXT_NAME='in"scope.txt'
    export PY_NAME TXT_NAME
    b_sandbox
    printf 'import os\ndef hello( ):\n    return 1\n' > "$PY_NAME"
    echo keep > "$TXT_NAME"
    git add -- "$PY_NAME" "$TXT_NAME"
    mkcommit "feat: quoted names"
    export PRE_COMMIT_RUN='echo changed > "$TXT_NAME"'

    run --separate-stderr "$SDM" check
    [ "$status" -eq 0 ]
    [ "${lines[-1]}" = "$(check_ok 3)" ]
    mapfile -d '' -t got < <(git show -z --name-only --format= HEAD)
    [ "${#got[@]}" -eq 3 ]
    [[ " ${got[*]} " == *" $PY_NAME "* && " ${got[*]} " == *" $TXT_NAME "* && " ${got[*]} " == *" app.py "* ]]
    git show "HEAD:$PY_NAME" | grep -q '^def hello():'
    [ "$(git show "HEAD:$TXT_NAME")" = changed ]
    [ -z "$(git status --porcelain)" ]
}

@test "new: the auto-fix commit ends with the footer from AA_MA_FOOTER_HELPER" {
    printf '%s\n' "emit_aa_ma_footer() { printf '\\n\\n[AA-MA Plan] x .claude/dev/active/x'; }" \
        > "$BATS_TEST_TMPDIR/footer.sh"
    export AA_MA_FOOTER_HELPER="$BATS_TEST_TMPDIR/footer.sh"
    b_sandbox
    run --separate-stderr "$SDM" check
    [ "$status" -eq 0 ]
    [ "$(git log -1 --format=%B)" = $'chore(scope): pre-PR auto-fixes\n\n[AA-MA Plan] x .claude/dev/active/x' ]
    [[ "$stderr" != *"aa-ma-footer.sh not found"* ]]
}

@test "new: with no footer helper found the auto-fix commit ends [ad-hoc] and stderr says so" {
    # helpers.bash: AA_MA_FOOTER_HELPER=/nonexistent, CLAUDE_HOME an empty dir; the sandbox has no repo copy
    [ ! -e "$WORK/claude-code/hooks/lib/aa-ma-footer.sh" ]
    [ -z "$(ls -A "$CLAUDE_HOME")" ]
    b_sandbox
    run --separate-stderr "$SDM" check
    [ "$status" -eq 0 ]
    [ "$(git log -1 --format=%B)" = $'chore(scope): pre-PR auto-fixes\n\n[ad-hoc]' ]
    printf '%s\n' "${stderr_lines[@]}" | grep -qxF 'check: aa-ma-footer.sh not found — using the [ad-hoc] footer'
    [[ "$output" != *"not found"* ]]      # why: a progress line, so stderr only
}

@test "new: check never calls pytest, mypy, ruff S or shellcheck" {
    git checkout -q main
    mkdir -p tests
    echo "def test_x(): assert True" > tests/test_x.py
    printf '[project]\nname = "x"\n' > pyproject.toml
    printf 'repos: []\n' > .pre-commit-config.yaml
    base_and_branch
    printf 'import os\ndef hello( ):\n    return 1\n' > app.py
    printf '#!/bin/sh\necho $1\n' > run.sh
    echo "def test_y(): assert True" > tests/test_y.py
    git add -A && mkcommit "feat: py, sh, tests"

    run --separate-stderr "$SDM" check
    [ "$status" -eq 0 ]
    [ -n "$(ruff_calls)" ] && [ -n "$(pc_calls)" ]    # why: non-vacuous — the fixers ran
    run grep -E '^(pytest|mypy|shellcheck|uv)( |$)' "$CLI_LOG"
    [ "$status" -eq 1 ]
    [ -z "$(ruff_calls | grep -e '--select' -e '--extend-select')" ]
}
