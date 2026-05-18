#!/usr/bin/env bats
# test_stage_a_preflight.bats — Stage A 4-branch abort coverage + happy path.
#
# Plan §1.6 acceptance: 4 cases exercise each abort branch.
# Plan §4.1.2 falsifiable AC: on-main abort produces stdout containing exactly
# `ABORT: Cannot run /sole-dev-merge from main branch` AND non-zero exit.
#
# Test pattern: see test_stage_b_scope.bats header note (plumbing-only commits
# to avoid the aa-ma-commit-signature.sh PreToolUse hook).

setup() {
    REPO_ROOT="$(cd "${BATS_TEST_DIRNAME}/../../.." && pwd)"
    COMMAND_MD="${REPO_ROOT}/claude-code/commands/sole-dev-merge.md"
    EXTRACT="${REPO_ROOT}/tests/commands/sole-dev-merge/fixtures/extract_stage.sh"

    # Keep the script OUTSIDE the sandbox to avoid an untracked file dirtying
    # the porcelain output when Stage A runs.
    SCRIPT_DIR="$(mktemp -d)"
    BATS_TMP="$(mktemp -d)"
    export BATS_TMP SCRIPT_DIR REPO_ROOT COMMAND_MD EXTRACT

    [[ -f "$COMMAND_MD" ]] || { echo "Missing $COMMAND_MD" >&2; return 1; }
    [[ -x "$EXTRACT"   ]] || { echo "Missing or non-exec $EXTRACT" >&2; return 1; }

    SA_SCRIPT="${SCRIPT_DIR}/sa.sh"
    bash "$EXTRACT" stage-a-preflight "$COMMAND_MD" > "$SA_SCRIPT"
    chmod +x "$SA_SCRIPT"
    export SA_SCRIPT
}

teardown() {
    rm -rf "$BATS_TMP" "$SCRIPT_DIR"
}

# Helper: plumbing commit (bypasses commit-signature hook)
mkcommit() {
    local msg="$1"
    local parent
    parent=$(git rev-parse --verify -q HEAD 2>/dev/null || true)
    local tree
    tree=$(git write-tree)
    local sha
    if [[ -n "$parent" ]]; then
        sha=$(echo "$msg" | git commit-tree "$tree" -p "$parent")
    else
        sha=$(echo "$msg" | git commit-tree "$tree")
    fi
    git update-ref HEAD "$sha"
}
export -f mkcommit

@test "ABORT on main branch (AC §4.1.2 verbatim)" {
    cd "$BATS_TMP"
    git init -q -b main
    git config user.email t@t.com
    git config user.name T
    echo init > a.txt && git add a.txt
    mkcommit "init"

    run bash "$SA_SCRIPT"
    [ "$status" -ne 0 ]
    # AC §4.1.2: stdout contains exactly this string
    [[ "$output" == "ABORT: Cannot run /sole-dev-merge from main branch" ]]
}

@test "ABORT on master branch (symmetric handling)" {
    cd "$BATS_TMP"
    git init -q -b master
    git config user.email t@t.com
    git config user.name T
    echo init > a.txt && git add a.txt
    mkcommit "init"

    run bash "$SA_SCRIPT"
    [ "$status" -ne 0 ]
    [[ "$output" == "ABORT: Cannot run /sole-dev-merge from master branch" ]]
}

@test "ABORT on dirty working tree" {
    cd "$BATS_TMP"
    git init -q -b main
    git config user.email t@t.com
    git config user.name T
    echo init > a.txt && git add a.txt
    mkcommit "init"

    git checkout -q -b feature
    echo "uncommitted" > b.txt

    run bash "$SA_SCRIPT"
    [ "$status" -ne 0 ]
    [[ "$output" == "ABORT: Uncommitted changes detected (commit or stash first)" ]]
}

@test "ABORT when no git remote configured" {
    cd "$BATS_TMP"
    git init -q -b main
    git config user.email t@t.com
    git config user.name T
    echo init > a.txt && git add a.txt
    mkcommit "init"

    git checkout -q -b feature
    mkcommit "feat: empty"

    # No remote configured — should abort
    run bash "$SA_SCRIPT"
    [ "$status" -ne 0 ]
    [[ "$output" == "ABORT: No git remote configured (need github.com or gitlab.com remote)" ]]
}

@test "ABORT when feature branch has no commits ahead of main" {
    cd "$BATS_TMP"
    git init -q -b main
    git config user.email t@t.com
    git config user.name T
    echo init > a.txt && git add a.txt
    mkcommit "init"

    # Branch off main but make no new commits
    git checkout -q -b feature
    git remote add origin https://example.com/r.git

    run bash "$SA_SCRIPT"
    [ "$status" -ne 0 ]
    [[ "$output" == "ABORT: No commits ahead of main (nothing to merge)" ]]
}

@test "Happy path: Pre-flight OK + exports set" {
    cd "$BATS_TMP"
    git init -q -b main
    git config user.email t@t.com
    git config user.name T
    echo init > a.txt && git add a.txt
    mkcommit "init"

    git checkout -q -b feature
    echo feat > b.txt && git add b.txt
    mkcommit "feat: real change"
    git remote add origin https://example.com/r.git

    run bash "$SA_SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == "Pre-flight OK"* ]]
    [[ "$output" == *"branch=feature"* ]]
    [[ "$output" == *"ahead=1"* ]]
}
