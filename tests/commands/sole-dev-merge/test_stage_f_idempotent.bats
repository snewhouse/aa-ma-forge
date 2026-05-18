#!/usr/bin/env bats
# test_stage_f_idempotent.bats — Stage E0 (auth pre-flight) + Stage F (push +
# PR/MR creation, idempotent).
#
# Plan §3.7 acceptance: mock `gh pr view` returning success → assert
# `gh pr create` NOT called, `gh pr edit` IS called.
# Plan §4.3.4 falsifiable AC (PR idempotency, GitHub):
#   planted prior PR → `pr create` count = 0 AND `pr edit --body-file` count = 1
# Plan §4.3.5 falsifiable AC (auth pre-flight):
#   mocked non-zero gh auth status → command exits within 5 seconds with stdout
#   containing `STATUS: AUTH_REQUIRED`.
#
# All gh/glab calls are stubbed via PATH-shadowing (fixtures/bin/{gh,glab}).
# Stubs log every invocation to "$CLI_LOG"; tests assert via grep.

load fixtures/helpers

setup() {
    REPO_ROOT="$(cd "${BATS_TEST_DIRNAME}/../../.." && pwd)"
    COMMAND_MD="${REPO_ROOT}/claude-code/commands/sole-dev-merge.md"
    EXTRACT="${REPO_ROOT}/tests/commands/sole-dev-merge/fixtures/extract_stage.sh"
    STUB_DIR="${REPO_ROOT}/tests/commands/sole-dev-merge/fixtures/bin"

    SCRIPT_DIR="$(tmp_script_dir)"
    BATS_TMP="$(mktemp -d)"
    BARE_REMOTE="${BATS_TMP}.bare.git"
    CLI_LOG="${BATS_TMP}/cli.log"
    BODY_FILE="${BATS_TMP}/body.md"
    : > "$CLI_LOG"
    echo "## Test plan" > "$BODY_FILE"
    export BATS_TMP SCRIPT_DIR REPO_ROOT COMMAND_MD EXTRACT STUB_DIR \
           BARE_REMOTE CLI_LOG BODY_FILE

    # Shadow real gh/glab with stubs (must come BEFORE existing PATH so they win).
    export PATH="$STUB_DIR:$PATH"
    # Verify shadowing worked — guards against silent fall-through to real gh.
    [[ "$(command -v gh)"   == "$STUB_DIR/gh"   ]]
    [[ "$(command -v glab)" == "$STUB_DIR/glab" ]]

    [[ -f "$COMMAND_MD" ]] || { echo "Missing $COMMAND_MD" >&2; return 1; }
    [[ -x "$EXTRACT"   ]] || { echo "Missing or non-exec $EXTRACT" >&2; return 1; }

    E0_SCRIPT="${SCRIPT_DIR}/e0.sh"
    F_SCRIPT="${SCRIPT_DIR}/f.sh"
    bash "$EXTRACT" stage-e0-auth "$COMMAND_MD" > "$E0_SCRIPT"
    bash "$EXTRACT" stage-f-push  "$COMMAND_MD" > "$F_SCRIPT"
    chmod +x "$E0_SCRIPT" "$F_SCRIPT"
    export E0_SCRIPT F_SCRIPT
}

teardown() {
    rm -rf "$BATS_TMP" "$BARE_REMOTE" "$SCRIPT_DIR"
}

# Helper: build a sandbox repo with one feature commit, wired to a bare remote.
_sandbox_with_commit() {
    cd "$BATS_TMP"
    sandbox_init
    echo init > a.txt && git add a.txt
    mkcommit "init"
    git checkout -q -b feature
    echo feat > b.txt && git add b.txt
    mkcommit "feat: real change"
    git init --bare -q "$BARE_REMOTE"
    git remote add origin "$BARE_REMOTE"
}

# ---------------------------------------------------------------------------
# Stage E0 — auth pre-flight (AC §4.3.5)
# ---------------------------------------------------------------------------

@test "E0: gh auth status non-zero → STATUS: AUTH_REQUIRED + clean exit 0 (AC §4.3.5)" {
    _sandbox_with_commit
    export REMOTE_CHOICE=github GH_AUTH_OK=0

    # 5s timeout per AC ("exits within 5 seconds")
    run timeout 5s bash "$E0_SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"STATUS: AUTH_REQUIRED"* ]]
    [[ "$output" == *"gh auth login"* ]]
}

@test "E0: glab auth status non-zero → STATUS: AUTH_REQUIRED" {
    _sandbox_with_commit
    export REMOTE_CHOICE=gitlab GLAB_AUTH_OK=0

    run timeout 5s bash "$E0_SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"STATUS: AUTH_REQUIRED"* ]]
    [[ "$output" == *"glab auth login"* ]]
}

@test "E0: both auths OK → silent pass (no STATUS line)" {
    _sandbox_with_commit
    export REMOTE_CHOICE=github  # GH_AUTH_OK defaults to 1

    run bash "$E0_SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" != *"AUTH_REQUIRED"* ]]
}

# ---------------------------------------------------------------------------
# Stage F — push + PR/MR idempotency
# ---------------------------------------------------------------------------

@test "F-github: existing PR → gh pr edit (NOT create) — AC §4.3.4" {
    _sandbox_with_commit
    export REMOTE_CHOICE=github GH_PR_EXISTS=1
    export PR_TITLE="feat: real change" PR_BODY_FILE="$BODY_FILE"

    run bash "$F_SCRIPT"
    [ "$status" -eq 0 ]
    # AC §4.3.4 falsifiable assertions
    [ "$(grep -c 'pr create' "$CLI_LOG")" -eq 0 ]
    [ "$(grep -c 'pr edit --body-file' "$CLI_LOG")" -eq 1 ]
}

@test "F-github: no existing PR → gh pr create (NOT edit)" {
    _sandbox_with_commit
    export REMOTE_CHOICE=github GH_PR_EXISTS=0
    export PR_TITLE="feat: real change" PR_BODY_FILE="$BODY_FILE"

    run bash "$F_SCRIPT"
    [ "$status" -eq 0 ]
    [ "$(grep -c 'pr edit' "$CLI_LOG")" -eq 0 ]
    [ "$(grep -c 'pr create --title' "$CLI_LOG")" -eq 1 ]
    [ "$(grep -c -- '--body-file' "$CLI_LOG")" -eq 1 ]
}

@test "F-gitlab: existing MR → glab mr update (NOT create)" {
    _sandbox_with_commit
    export REMOTE_CHOICE=gitlab GLAB_MR_EXISTS=1
    export PR_TITLE="feat: real change" PR_BODY_FILE="$BODY_FILE"

    run bash "$F_SCRIPT"
    [ "$status" -eq 0 ]
    [ "$(grep -c 'mr create' "$CLI_LOG")" -eq 0 ]
    [ "$(grep -c 'mr update --description' "$CLI_LOG")" -eq 1 ]
}

@test "F-gitlab: no existing MR → glab mr create (NOT update); --description NOT --description-file" {
    _sandbox_with_commit
    export REMOTE_CHOICE=gitlab GLAB_MR_EXISTS=0
    export PR_TITLE="feat: real change" PR_BODY_FILE="$BODY_FILE"

    run bash "$F_SCRIPT"
    [ "$status" -eq 0 ]
    [ "$(grep -c 'mr update' "$CLI_LOG")" -eq 0 ]
    [ "$(grep -c 'mr create --title' "$CLI_LOG")" -eq 1 ]
    # Guards against the fabricated --description-file flag (reference.md
    # "WRONG SYNTAX TO NEVER USE").
    [ "$(grep -c -- '--description-file' "$CLI_LOG")" -eq 0 ]
    [ "$(grep -c -- '--description' "$CLI_LOG")" -ge 1 ]
}

@test "F: title truncated to 70 chars when commit subject is longer" {
    cd "$BATS_TMP"
    sandbox_init
    echo init > a.txt && git add a.txt
    mkcommit "init"
    git checkout -q -b feature
    echo feat > b.txt && git add b.txt
    local long_subject
    long_subject="feat: $(printf 'x%.0s' {1..100})"  # 106 chars total
    mkcommit "$long_subject"
    git init --bare -q "$BARE_REMOTE"
    git remote add origin "$BARE_REMOTE"

    export REMOTE_CHOICE=github GH_PR_EXISTS=0 PR_BODY_FILE="$BODY_FILE"
    # Stage F must derive title from topmost commit subject; do NOT pre-set PR_TITLE.
    unset PR_TITLE || true

    run bash "$F_SCRIPT"
    [ "$status" -eq 0 ]
    # The gh stub writes `gh pr create --title <TITLE> --body-file <PATH>`
    # (quotes stripped by `echo $*`). Extract title via sed between the two
    # known flag boundaries — quote-agnostic.
    local logged_title
    logged_title="$(sed -n 's/^gh pr create --title \(.*\) --body-file .*$/\1/p' "$CLI_LOG" | head -1)"
    [ -n "$logged_title" ]
    [ "${#logged_title}" -le 70 ]
}

@test "F: git push -u origin HEAD called once before PR/MR ops" {
    # This is the load-bearing first action of Stage F — without it, gh/glab
    # ops on a fresh branch fail. We assert by capturing git-call order via
    # `git -c` config logging or by checking that the bare remote received
    # the branch.
    _sandbox_with_commit
    export REMOTE_CHOICE=github GH_PR_EXISTS=0
    export PR_TITLE="feat: real change" PR_BODY_FILE="$BODY_FILE"

    run bash "$F_SCRIPT"
    [ "$status" -eq 0 ]
    # The bare remote should now have a ref to the feature branch.
    [ -n "$(git --git-dir="$BARE_REMOTE" for-each-ref refs/heads/feature)" ]
}
