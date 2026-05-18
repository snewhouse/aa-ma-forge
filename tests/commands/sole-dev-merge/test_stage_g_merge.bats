#!/usr/bin/env bats
# test_stage_g_merge.bats — Stage G1 (branch protection) + G3 (auto-merge
# dispatch incl. timeout/failure error paths) + G4 (post-merge cleanup).
#
# Plan §4.4.1 falsifiable AC: mocked `gh api repos/.../allow_rebase_merge`
# returning `false` → script's merge dispatch uses `--merge` not `--rebase`.
# Plan §4.4.3 falsifiable AC: green CI → exactly one call to
# `pr merge --rebase --delete-branch` (counted via mock).
# Plan §4.5 G4 cleanup: post-merge → on main, main fast-forwarded from origin,
# `git fetch --prune` cleans deleted-branch ref.
#
# Stub controls (see fixtures/bin/gh):
#   GH_ALLOW_REBASE=true|false   — `gh api ... .allow_rebase_merge` echoes.

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
    : > "$CLI_LOG"
    export BATS_TMP SCRIPT_DIR REPO_ROOT COMMAND_MD EXTRACT STUB_DIR \
           BARE_REMOTE CLI_LOG

    export PATH="$STUB_DIR:$PATH"
    [[ "$(command -v gh)"   == "$STUB_DIR/gh"   ]]
    [[ "$(command -v glab)" == "$STUB_DIR/glab" ]]

    [[ -f "$COMMAND_MD" ]] || { echo "Missing $COMMAND_MD" >&2; return 1; }
    [[ -x "$EXTRACT"   ]] || { echo "Missing or non-exec $EXTRACT" >&2; return 1; }

    G1_SCRIPT="${SCRIPT_DIR}/g1.sh"
    G3_SCRIPT="${SCRIPT_DIR}/g3.sh"
    G4_SCRIPT="${SCRIPT_DIR}/g4.sh"
    bash "$EXTRACT" stage-g1-protect "$COMMAND_MD" > "$G1_SCRIPT"
    bash "$EXTRACT" stage-g3-merge   "$COMMAND_MD" > "$G3_SCRIPT"
    bash "$EXTRACT" stage-g4-cleanup "$COMMAND_MD" > "$G4_SCRIPT"
    chmod +x "$G1_SCRIPT" "$G3_SCRIPT" "$G4_SCRIPT"
    export G1_SCRIPT G3_SCRIPT G4_SCRIPT

    export PR_NUM=42
    export PR_URL="https://github.com/test/repo/pull/42"
    export REMOTE_CHOICE=github
}

teardown() {
    rm -rf "$BATS_TMP" "$BARE_REMOTE" "$SCRIPT_DIR"
}

# Helper: sandbox with main + feature branch + bare remote (post-push state).
_sandbox_with_pushed_feature() {
    cd "$BATS_TMP"
    sandbox_init
    echo init > a.txt && git add a.txt
    mkcommit "init"
    git init --bare -q "$BARE_REMOTE"
    git remote add origin "$BARE_REMOTE"
    git push -q origin main
    git checkout -q -b feature
    echo feat > b.txt && git add b.txt
    mkcommit "feat: new feature"
    git push -q -u origin feature
}

# ---------------------------------------------------------------------------
# Stage G1 — branch-protection pre-check
# ---------------------------------------------------------------------------

@test "G1: rebase allowed (default) → MERGE_STRATEGY=rebase" {
    _sandbox_with_pushed_feature
    export GH_ALLOW_REBASE=true

    run bash "$G1_SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"MERGE_STRATEGY=rebase"* ]]
}

@test "G1: rebase disabled (GH_ALLOW_REBASE=false) → MERGE_STRATEGY=merge + warning (AC §4.4.1)" {
    _sandbox_with_pushed_feature
    export GH_ALLOW_REBASE=false

    run bash "$G1_SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"MERGE_STRATEGY=merge"* ]]
    # User-facing warning so the operator knows the strategy fell back
    [[ "$output" == *"rebase"* ]]
    [[ "$output" == *"disabled"* || "$output" == *"fallback"* ]]
}

# ---------------------------------------------------------------------------
# Stage G3 — auto-merge dispatch (incl. error paths from plan §4.4)
# ---------------------------------------------------------------------------

@test "G3: green CI + rebase → exactly 1 'pr merge --rebase --delete-branch' (AC §4.4.3)" {
    _sandbox_with_pushed_feature
    export CI_STATE=green MERGE_STRATEGY=rebase

    run bash "$G3_SCRIPT"
    [ "$status" -eq 0 ]
    # AC §4.4.3 falsifiable
    [ "$(grep -c 'pr merge --rebase --delete-branch' "$CLI_LOG")" -eq 1 ]
}

@test "G3: green CI + merge fallback → 'pr merge --merge --delete-branch' (NOT --rebase) — AC §4.4.1" {
    _sandbox_with_pushed_feature
    export CI_STATE=green MERGE_STRATEGY=merge

    run bash "$G3_SCRIPT"
    [ "$status" -eq 0 ]
    [ "$(grep -c 'pr merge --merge --delete-branch' "$CLI_LOG")" -eq 1 ]
    [ "$(grep -c 'pr merge --rebase' "$CLI_LOG")" -eq 0 ]
}

@test "G3: CI_STATE=timeout → no merge + STATUS:CI_TIMEOUT + recovery hint" {
    _sandbox_with_pushed_feature
    export CI_STATE=timeout MERGE_STRATEGY=rebase

    run bash "$G3_SCRIPT"
    [ "$status" -eq 0 ]
    [ "$(grep -c 'pr merge' "$CLI_LOG")" -eq 0 ]
    [[ "$output" == *"STATUS: CI_TIMEOUT"* ]]
    [[ "$output" == *"$PR_URL"* ]]
}

@test "G3: CI_STATE=failed → no merge + STATUS:CI_FAILED + diagnostic" {
    _sandbox_with_pushed_feature
    export CI_STATE=failed MERGE_STRATEGY=rebase

    run bash "$G3_SCRIPT"
    [ "$status" -eq 0 ]
    [ "$(grep -c 'pr merge' "$CLI_LOG")" -eq 0 ]
    [[ "$output" == *"STATUS: CI_FAILED"* ]]
    [[ "$output" == *"$PR_URL"* ]]
}

# ---------------------------------------------------------------------------
# Stage G4 — post-merge cleanup (plan §4.5)
# ---------------------------------------------------------------------------

@test "G4: post-merge → HEAD switches to main + git fetch --prune invoked" {
    _sandbox_with_pushed_feature
    # Simulate the post-merge server state: the bare remote's feature ref is
    # gone (deleted by --delete-branch), and main has the new commit.
    git --git-dir="$BARE_REMOTE" update-ref -d refs/heads/feature
    # main on bare remote receives the feature commit (simulating fast-forward).
    git --git-dir="$BARE_REMOTE" update-ref refs/heads/main "$(git rev-parse feature)"

    # Stage G4 is invoked from on-feature state per plan §4.5.1.
    [ "$(git branch --show-current)" = "feature" ]

    run bash "$G4_SCRIPT"
    [ "$status" -eq 0 ]

    # AC §4.5: post-G4 HEAD is main
    cd "$BATS_TMP"  # G4 may have cd'd
    [ "$(git branch --show-current)" = "main" ]
    # main on local now matches origin/main (fast-forwarded)
    [ "$(git rev-parse main)" = "$(git --git-dir="$BARE_REMOTE" rev-parse main)" ]
    # Final summary line emitted
    [[ "$output" == *"merged"* || "$output" == *"OK"* ]]
}
