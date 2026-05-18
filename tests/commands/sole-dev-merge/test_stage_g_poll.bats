#!/usr/bin/env bats
# test_stage_g_poll.bats — Stage G2 (CI poll with timeout).
#
# Plan §4.4.2 falsifiable AC: given mocked `gh pr checks --watch` that never
# returns, with `timeout 5s` wrapper for test speed → the script exits 0 AND
# stdout contains `STATUS: CI_TIMEOUT`.
#
# Stage G2 internally wraps the watch call in `timeout 900s` in production;
# tests override via CI_POLL_TIMEOUT env var to a shorter value (2s) so the
# never-return path resolves quickly.
#
# Stub controls (see fixtures/bin/gh):
#   GH_WATCH_HANG=1   — `gh pr checks --watch` sleeps 999s (timeout trigger)
#   GH_CHECKS_RC=N    — exit code for normal `gh pr checks` (0=green, 1=failed)

load fixtures/helpers

setup() {
    REPO_ROOT="$(cd "${BATS_TEST_DIRNAME}/../../.." && pwd)"
    COMMAND_MD="${REPO_ROOT}/claude-code/commands/sole-dev-merge.md"
    EXTRACT="${REPO_ROOT}/tests/commands/sole-dev-merge/fixtures/extract_stage.sh"
    STUB_DIR="${REPO_ROOT}/tests/commands/sole-dev-merge/fixtures/bin"

    SCRIPT_DIR="$(tmp_script_dir)"
    BATS_TMP="$(mktemp -d)"
    CLI_LOG="${BATS_TMP}/cli.log"
    : > "$CLI_LOG"
    export BATS_TMP SCRIPT_DIR REPO_ROOT COMMAND_MD EXTRACT STUB_DIR CLI_LOG

    export PATH="$STUB_DIR:$PATH"
    [[ "$(command -v gh)" == "$STUB_DIR/gh" ]]

    [[ -f "$COMMAND_MD" ]] || { echo "Missing $COMMAND_MD" >&2; return 1; }
    [[ -x "$EXTRACT"   ]] || { echo "Missing or non-exec $EXTRACT" >&2; return 1; }

    G2_SCRIPT="${SCRIPT_DIR}/g2.sh"
    bash "$EXTRACT" stage-g2-poll "$COMMAND_MD" > "$G2_SCRIPT"
    chmod +x "$G2_SCRIPT"
    export G2_SCRIPT

    # Sandbox: minimal repo so any `git` calls inside G2 don't error.
    cd "$BATS_TMP"
    sandbox_init
    echo init > a.txt && git add a.txt
    mkcommit "init"

    # Stage F's outputs that G2 inherits in production.
    export PR_NUM=42
    export PR_URL="https://github.com/test/repo/pull/42"
    export REMOTE_CHOICE=github
    # Override inner timeout for test speed (overrides Stage G2's 900s default).
    export CI_POLL_TIMEOUT=2s
}

teardown() {
    rm -rf "$BATS_TMP" "$SCRIPT_DIR"
}

@test "G2: CI green (RC=0) → CI_STATE=green, no STATUS line" {
    export GH_WATCH_HANG=0 GH_CHECKS_RC=0

    run bash "$G2_SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"CI_STATE=green"* ]]
    [[ "$output" != *"STATUS: CI_TIMEOUT"* ]]
    [[ "$output" != *"STATUS: CI_FAILED"* ]]
}

@test "G2: never-returning watch + 2s inner timeout → CI_STATE=timeout + STATUS:CI_TIMEOUT (AC §4.4.2)" {
    export GH_WATCH_HANG=1

    # Outer test-side timeout of 5s guards against runaway; inner Stage-G2
    # timeout (CI_POLL_TIMEOUT=2s) is what actually fires.
    run timeout 5s bash "$G2_SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"STATUS: CI_TIMEOUT"* ]]
    [[ "$output" == *"CI_STATE=timeout"* ]]
    # Recovery hint for the operator (per plan §4.4)
    [[ "$output" == *"gh pr merge"* ]]
    [[ "$output" == *"--auto"* ]]
}

@test "G2: CI failed (RC=1) → CI_STATE=failed + STATUS:CI_FAILED + PR URL" {
    export GH_WATCH_HANG=0 GH_CHECKS_RC=1

    run bash "$G2_SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"STATUS: CI_FAILED"* ]]
    [[ "$output" == *"CI_STATE=failed"* ]]
    # PR URL in failure path so operator can click through
    [[ "$output" == *"$PR_URL"* ]]
}

@test "G2: gh pr checks invoked with --watch + --interval 30 + --fail-fast" {
    export GH_WATCH_HANG=0 GH_CHECKS_RC=0

    run bash "$G2_SCRIPT"
    [ "$status" -eq 0 ]
    # Verify the canonical flag combination per reference.md
    grep -q 'pr checks .*--watch' "$CLI_LOG"
    grep -q -- '--interval 30' "$CLI_LOG"
    grep -q -- '--fail-fast' "$CLI_LOG"
}
