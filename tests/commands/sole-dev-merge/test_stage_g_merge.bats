#!/usr/bin/env bats
# test_stage_g_merge.bats — Stage G1 (branch protection) + G3 (auto-merge
# dispatch incl. timeout/failure error paths) + G4 (post-merge cleanup).
#
# Plan §4.4.1 falsifiable AC: mocked `gh api repos/.../allow_rebase_merge`
# returning `false` → script's merge dispatch uses `--merge` not `--rebase`.
# Plan §4.4.3 falsifiable AC: green CI → exactly one call to
# `pr merge <n> --rebase`, never with --delete-branch (L-1332: gh's local
# step fails in a worktree and skips the remote delete). G3 then decides from
# `gh pr view --json state`, deletes refs/heads/<branch> itself and asserts
# with ls-remote (sole-dev-merge-fixes M1).
# Plan §4.5 G4 cleanup: post-merge → on main, main fast-forwarded from origin,
# `git fetch --prune` cleans deleted-branch ref.
#
# Stub controls (see fixtures/bin/gh):
#   GH_ALLOW_REBASE=true|false   — `gh api ... .allow_rebase_merge` echoes.

load fixtures/helpers

setup() {
    REPO_ROOT="$(cd "${BATS_TEST_DIRNAME}/../../.." && pwd)"
    COMMAND_MD="${REPO_ROOT}/claude-code/skills/sole-dev-merge/SKILL.md"
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
    # G3/G4 require ORIGINAL_BRANCH (Stage A sets it); no default any more.
    export ORIGINAL_BRANCH=feature
    # G4 runs only after G3 recorded a merge (sole-dev-merge-fixes M2 §6.8); G3 sets its own.
    export MERGE_DISPATCHED=1
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

@test "G3: green CI + rebase → exactly 1 'pr merge <n> --rebase', no --delete-branch (AC §4.4.3, L-1332)" {
    _sandbox_with_pushed_feature
    export CI_STATE=green MERGE_STRATEGY=rebase

    run bash "$G3_SCRIPT"
    [ "$status" -eq 0 ]
    # AC §4.4.3 falsifiable — the gh CLI takes PR_NUM as a positional FIRST arg.
    [ "$(grep -cE 'pr merge [0-9]+ --rebase$' "$CLI_LOG")" -eq 1 ]
    [ "$(grep -c -- '--delete-branch' "$CLI_LOG")" -eq 0 ]
}

@test "G3: green CI + merge fallback → 'pr merge <n> --merge' (NOT --rebase), no --delete-branch — AC §4.4.1" {
    _sandbox_with_pushed_feature
    export CI_STATE=green MERGE_STRATEGY=merge

    run bash "$G3_SCRIPT"
    [ "$status" -eq 0 ]
    [ "$(grep -cE 'pr merge [0-9]+ --merge$' "$CLI_LOG")" -eq 1 ]
    [ "$(grep -c -- '--delete-branch' "$CLI_LOG")" -eq 0 ]
    # Negative assertion: no --rebase call landed
    [ "$(grep -c -- '--rebase' "$CLI_LOG")" -eq 0 ]
}

@test "G3: green + rebase → merge without --delete-branch, then push --delete, ls-remote empty" {
    _sandbox_with_pushed_feature
    export CI_STATE=green MERGE_STRATEGY=rebase

    run bash "$G3_SCRIPT"
    [ "$status" -eq 0 ]
    [ "$(grep -cE '^gh pr merge 42 --rebase$' "$CLI_LOG")" -eq 1 ]
    [ "$(grep -c -- '--delete-branch' "$CLI_LOG")" -eq 0 ]
    [ -z "$(git ls-remote origin refs/heads/feature)" ]
    [[ "$output" == *"MERGE_DISPATCHED=1"* ]]
}

@test "G3: state != MERGED → STATUS: MERGE_FAILED, no push --delete" {
    _sandbox_with_pushed_feature
    export CI_STATE=green GH_PR_STATE=OPEN

    run bash "$G3_SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"STATUS: MERGE_FAILED"* ]]
    [[ "$output" == *"MERGE_DISPATCHED=0"* ]]
    [ -n "$(git ls-remote origin refs/heads/feature)" ]
}

@test "G3: gh pr merge rc=1 but state MERGED → treated as merged (E6 either way)" {
    _sandbox_with_pushed_feature
    export CI_STATE=green GH_MERGE_RC=1

    run bash "$G3_SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"MERGE_DISPATCHED=1"* ]]
    [ -z "$(git ls-remote origin refs/heads/feature)" ]
}

@test "G3: branch already deleted server-side → no abort, ls-remote assert passes" {
    _sandbox_with_pushed_feature
    git --git-dir="$BARE_REMOTE" update-ref -d refs/heads/feature
    export CI_STATE=green

    run bash "$G3_SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"MERGE_DISPATCHED=1"* ]]
    [[ "$output" != *"BRANCH_NOT_DELETED"* ]]
}

@test "G3: remote refuses delete → STATUS: BRANCH_NOT_DELETED (warning), rc 0" {
    _sandbox_with_pushed_feature
    printf '#!/bin/sh\nwhile read o n r; do [ "$n" = 0000000000000000000000000000000000000000 ] && exit 1; done; exit 0\n' \
        > "$BARE_REMOTE/hooks/pre-receive"
    chmod +x "$BARE_REMOTE/hooks/pre-receive"
    export CI_STATE=green

    run bash "$G3_SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"STATUS: BRANCH_NOT_DELETED — feature"* ]]
    [ -n "$(git ls-remote origin refs/heads/feature)" ]
}

@test "G3: unknown REMOTE_CHOICE → STATUS: REMOTE_UNKNOWN, MERGE_DISPATCHED=0" {
    _sandbox_with_pushed_feature
    export CI_STATE=green REMOTE_CHOICE=bitbucket

    run bash "$G3_SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"STATUS: REMOTE_UNKNOWN"* ]]
    [[ "$output" == *"MERGE_DISPATCHED=0"* ]]
    [[ "$output" != *"merged"* ]]
}

@test "G3: ORIGINAL_BRANCH unset → fails loud before any merge" {
    _sandbox_with_pushed_feature
    unset ORIGINAL_BRANCH
    export CI_STATE=green

    run bash "$G3_SCRIPT"
    [ "$status" -ne 0 ]
    [ "$(grep -c 'pr merge' "$CLI_LOG")" -eq 0 ]
    [ -n "$(git ls-remote origin refs/heads/feature)" ]
}

# --- security-audit cases: refuse before any state change -----------------

@test "G3: PR head ref differs from ORIGINAL_BRANCH → ABORT rc 1, no merge" {
    _sandbox_with_pushed_feature
    export CI_STATE=green GH_HEAD_REF=other

    run bash "$G3_SCRIPT"
    [ "$status" -eq 1 ]
    [[ "$output" == *"ABORT"*"head is 'other'"* ]]
    [ "$(grep -c 'pr merge' "$CLI_LOG")" -eq 0 ]
    [ -n "$(git ls-remote origin refs/heads/feature)" ]
}

@test "G3: ORIGINAL_BRANCH is the default branch → ABORT rc 1, no merge" {
    _sandbox_with_pushed_feature
    export CI_STATE=green ORIGINAL_BRANCH=main GH_HEAD_REF=main

    run bash "$G3_SCRIPT"
    [ "$status" -eq 1 ]
    [[ "$output" == *"ABORT"* ]]
    [ "$(grep -c 'pr merge' "$CLI_LOG")" -eq 0 ]
    [ -n "$(git ls-remote origin refs/heads/main)" ]
}

@test "G3: option-shaped ORIGINAL_BRANCH '--output=x' → ABORT rc 1, no file x, no merge" {
    _sandbox_with_pushed_feature
    export CI_STATE=green ORIGINAL_BRANCH='--output=x' GH_HEAD_REF='--output=x'

    run bash "$G3_SCRIPT"
    [ "$status" -eq 1 ]
    [[ "$output" == *"ABORT"* ]]
    [ ! -e x ]
    [ "$(grep -c 'pr merge' "$CLI_LOG")" -eq 0 ]
}

@test "G3: a same-named tag on the remote survives the branch delete" {
    _sandbox_with_pushed_feature
    git tag feature-tag-src && git push -q origin "feature-tag-src:refs/tags/feature"
    export CI_STATE=green

    run bash "$G3_SCRIPT"
    [ "$status" -eq 0 ]
    [ -z "$(git ls-remote origin refs/heads/feature)" ]
    [ -n "$(git ls-remote origin refs/tags/feature)" ]
}

@test "G3: remote branch other/feature → not deleted, no false BRANCH_NOT_DELETED" {
    _sandbox_with_pushed_feature
    git push -q origin "feature:refs/heads/other/feature"
    export CI_STATE=green

    run bash "$G3_SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"MERGE_DISPATCHED=1"* ]]
    [[ "$output" != *"BRANCH_NOT_DELETED"* ]]
    [ -z "$(git ls-remote origin refs/heads/feature)" ]
    [ -n "$(git ls-remote origin refs/heads/other/feature)" ]
}

# --- §6.8 review fixes (code-reviewer W3, security-auditor INFO) -----------

@test "G3: ls-remote fails after the delete → BRANCH_NOT_DELETED with its rc, never read as deleted" {
    _sandbox_with_pushed_feature
    local real_git; real_git=$(command -v git)
    mkdir -p "$BATS_TMP/gitbin"
    printf '#!/bin/sh\n[ "$1" = ls-remote ] && exit 128\nexec %s "$@"\n' "$real_git" > "$BATS_TMP/gitbin/git"
    chmod +x "$BATS_TMP/gitbin/git"
    export CI_STATE=green

    PATH="$BATS_TMP/gitbin:$PATH" run bash "$G3_SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"STATUS: BRANCH_NOT_DELETED — feature"*"rc=128"* ]]
}

@test "G3: MERGE_STRATEGY outside rebase|merge|squash → ABORT rc 1, no merge" {
    _sandbox_with_pushed_feature
    export CI_STATE=green MERGE_STRATEGY=admin

    run bash "$G3_SCRIPT"
    [ "$status" -eq 1 ]
    [[ "$output" == *"ABORT"* ]]
    [ "$(grep -c 'pr merge' "$CLI_LOG")" -eq 0 ]
}

@test "G3: option-shaped DEFAULT_BRANCH → ABORT rc 1, no merge" {
    _sandbox_with_pushed_feature
    export CI_STATE=green DEFAULT_BRANCH='-xmain'

    run bash "$G3_SCRIPT"
    [ "$status" -eq 1 ]
    [[ "$output" == *"ABORT"* ]]
    [ "$(grep -c 'pr merge' "$CLI_LOG")" -eq 0 ]
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

# Helper: main checkout at $1 (default $BATS_TMP) with a linked worktree for
# branch $2 (default feature) at $1/.worktrees/$2, a bare remote, and the
# post-merge server state: remote main = the branch tip, remote branch gone.
# Leaves cwd in the worktree. Exports MAIN, WT, ORIGINAL_BRANCH.
_sandbox_worktree() {
    MAIN="${1:-$BATS_TMP}"
    local branch="${2:-feature}"
    mkdir -p "$MAIN"
    cd "$MAIN"
    sandbox_init
    echo init > a.txt && git add a.txt
    mkcommit "init"
    git init --bare -q "$BARE_REMOTE"
    git remote add origin "$BARE_REMOTE"
    git push -q origin main
    git fetch -q origin
    WT="$MAIN/.worktrees/$branch"
    git worktree add -q -b "$branch" "$WT"
    cd "$WT"
    echo feat > b.txt && git add b.txt
    mkcommit "feat: new feature"
    git push -q -u origin "$branch"
    git --git-dir="$BARE_REMOTE" update-ref refs/heads/main "$(git rev-parse HEAD)"
    git --git-dir="$BARE_REMOTE" update-ref -d "refs/heads/$branch"
    export MAIN WT ORIGINAL_BRANCH="$branch"
}

# Fingerprint of a checkout's tracked state: HEAD, index/worktree diff, status.
_fingerprint() {
    { git -C "$1" rev-parse HEAD; git -C "$1" diff HEAD; git -C "$1" status --porcelain --untracked-files=no; } | sha256sum
}

@test "G4: AC2.2 from a worktree, clean main checkout → main fast-forwarded, worktree untouched, cleanup printed" {
    _sandbox_worktree
    local wt_head; wt_head=$(git rev-parse HEAD)

    run bash "$G4_SCRIPT"
    [ "$status" -eq 0 ]
    [ "$(git -C "$MAIN" rev-parse HEAD)" = "$(git --git-dir="$BARE_REMOTE" rev-parse main)" ]
    [ "$(git -C "$MAIN" branch --show-current)" = "main" ]
    [ "$(git -C "$WT" branch --show-current)" = "feature" ]
    [ "$(git -C "$WT" rev-parse HEAD)" = "$wt_head" ]
    [[ "$output" == *"worktree remove"* ]]
    [[ "$output" == *"branch -D feature"* ]]
    [[ "$output" == *"STATUS: OK"* ]]
}

@test "G4: AC2.2b main checkout path with a space → printed cleanup commands are quoted" {
    _sandbox_worktree "$BATS_TMP/my main"

    run bash "$G4_SCRIPT"
    [ "$status" -eq 0 ]
    local rm_line del_line
    rm_line=$(grep -E '^ +git -C .* worktree remove ' <<<"$output")
    del_line=$(grep -E '^ +git -C .* branch -D ' <<<"$output")
    [ -n "$rm_line" ] && [ -n "$del_line" ]
    # Dry run: a git function records argv instead of acting.
    git() { printf '%s\n' "$@" > "$BATS_TMP/argv"; }
    eval "$rm_line"
    [ "$(sed -n 2p "$BATS_TMP/argv")" = "$MAIN" ]
    [ "$(sed -n 5p "$BATS_TMP/argv")" = "$WT" ]
    eval "$del_line"
    [ "$(sed -n 2p "$BATS_TMP/argv")" = "$MAIN" ]
    [ "$(sed -n 5p "$BATS_TMP/argv")" = "feature" ]
    unset -f git
}

@test "G4: AC2.3 dirty tracked file in the main checkout → STATUS: MAIN_CHECKOUT_DIRTY, main byte-identical" {
    _sandbox_worktree
    echo dirty >> "$MAIN/a.txt"
    local before; before=$(_fingerprint "$MAIN")

    run bash "$G4_SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"STATUS: MAIN_CHECKOUT_DIRTY"* ]]
    [ "$(_fingerprint "$MAIN")" = "$before" ]
    [ "$(git -C "$WT" branch --show-current)" = "feature" ]
}

@test "G4: AC2.3b untracked file in the main checkout → not dirty, fast-forwarded (branch feature/x)" {
    _sandbox_worktree "$BATS_TMP" "feature/x"
    echo u > "$MAIN/untracked.txt"

    run bash "$G4_SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" != *"MAIN_CHECKOUT_DIRTY"* ]]
    [ "$(git -C "$MAIN" rev-parse HEAD)" = "$(git --git-dir="$BARE_REMOTE" rev-parse main)" ]
    [ -f "$MAIN/untracked.txt" ]
    [ "$(git -C "$WT" branch --show-current)" = "feature/x" ]
    [[ "$output" == *"branch -D feature/x"* ]]
}

@test "G4: AC2.4 run from a subdirectory of a plain checkout → non-worktree path" {
    _sandbox_with_pushed_feature
    git --git-dir="$BARE_REMOTE" update-ref -d refs/heads/feature
    git --git-dir="$BARE_REMOTE" update-ref refs/heads/main "$(git rev-parse feature)"
    mkdir -p sub && cd sub

    run bash "$G4_SCRIPT"
    [ "$status" -eq 0 ]
    [ "$(git -C "$BATS_TMP" branch --show-current)" = "main" ]
    [ "$(git -C "$BATS_TMP" rev-parse main)" = "$(git --git-dir="$BARE_REMOTE" rev-parse main)" ]
    [[ "$output" != *"worktree remove"* ]]
}

@test "G4: AC2.5 main checkout on branch 'other' → 'other' untouched, local main updated or MAIN_NOT_UPDATED" {
    _sandbox_worktree
    git -C "$MAIN" checkout -q -b other
    local other_sha; other_sha=$(git -C "$MAIN" rev-parse other)

    run bash "$G4_SCRIPT"
    [ "$status" -eq 0 ]
    [ "$(git -C "$MAIN" branch --show-current)" = "other" ]
    [ "$(git -C "$MAIN" rev-parse other)" = "$other_sha" ]
    [ "$(git -C "$WT" branch --show-current)" = "feature" ]
    [[ "$(git -C "$MAIN" rev-parse refs/heads/main)" == "$(git --git-dir="$BARE_REMOTE" rev-parse main)" \
       || "$output" == *"STATUS: MAIN_NOT_UPDATED"* ]]
}

@test "G4: AC2.5b default branch in use by a third worktree → STATUS: MAIN_NOT_UPDATED, never STATUS: OK" {
    _sandbox_worktree
    git -C "$MAIN" checkout -q -b other
    git -C "$MAIN" worktree add -q "$BATS_TMP/wt-main" main

    run bash "$G4_SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"STATUS: MAIN_NOT_UPDATED"* ]]
    [[ "$output" != *"STATUS: OK"* ]]
}

@test "G4: option-shaped DEFAULT_BRANCH → ABORT rc 1 before any fetch or checkout" {
    _sandbox_worktree
    export DEFAULT_BRANCH='-xmain'

    run bash "$G4_SCRIPT"
    [ "$status" -eq 1 ]
    [[ "$output" == *"ABORT"* ]]
    [ "$(git -C "$WT" branch --show-current)" = "feature" ]
}

@test "G4: AC2.6 ORIGINAL_BRANCH unset → fails loud, no branch deleted, no checkout" {
    _sandbox_with_pushed_feature
    git --git-dir="$BARE_REMOTE" update-ref refs/heads/main "$(git rev-parse feature)"
    unset ORIGINAL_BRANCH

    run bash "$G4_SCRIPT"
    [ "$status" -ne 0 ]
    git rev-parse -q --verify refs/heads/feature
    [ "$(git branch --show-current)" = "feature" ]
}

# ---------------------------------------------------------------------------
# §6.8 M4 GitLab-branch coverage (MED-3 fix) — G1 + G3 GitLab paths
# previously had 0% test coverage despite full stub support.
# ---------------------------------------------------------------------------

@test "G1 gitlab: merge_method=ff → MERGE_STRATEGY=merge (MED-3 coverage)" {
    _sandbox_with_pushed_feature
    export REMOTE_CHOICE=gitlab
    export GLAB_API_MODE=merge_method GLAB_MERGE_METHOD=ff

    run bash "$G1_SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"MERGE_STRATEGY=merge"* ]]
    [[ "$output" == *"merge_method=ff"* ]]
}

@test "G3 gitlab: green+rebase → glab mr merge --rebase --remove-source-branch --yes (MED-3 coverage)" {
    _sandbox_with_pushed_feature
    export REMOTE_CHOICE=gitlab CI_STATE=green MERGE_STRATEGY=rebase
    export MR_IID=42

    run bash "$G3_SCRIPT"
    [ "$status" -eq 0 ]
    # Canonical GitLab rebase-merge invocation per reference.md
    [ "$(grep -cE 'mr merge 42 --rebase --remove-source-branch --yes' "$CLI_LOG")" -eq 1 ]
    [ "$(grep -c 'pr merge' "$CLI_LOG")" -eq 0 ]  # never touches gh
}

@test "G3 gitlab: CI_STATE=timeout → STATUS:CI_TIMEOUT + glab recovery (HIGH-1 fix regression)" {
    _sandbox_with_pushed_feature
    export REMOTE_CHOICE=gitlab CI_STATE=timeout MR_IID=42
    export PR_URL="https://gitlab.com/test/repo/-/merge_requests/42"

    run bash "$G3_SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"STATUS: CI_TIMEOUT"* ]]
    # HIGH-1 fix: recovery hint is glab (NOT hardcoded gh)
    [[ "$output" == *"glab mr merge 42 --when-pipeline-succeeds"* ]]
    [[ "$output" != *"gh pr merge"* ]]
}

@test "G3: CI_STATE=unknown → STATUS:CI_UNKNOWN catchall (MED-1 fix regression)" {
    _sandbox_with_pushed_feature
    export REMOTE_CHOICE=github CI_STATE=mystery_value
    # MED-1: previously the catchall said "skipping merge" but emitted NO
    # STATUS line — downstream tooling parsing STATUS missed the terminal state.
    run bash "$G3_SCRIPT"
    [ "$status" -eq 0 ]
    [[ "$output" == *"STATUS: CI_UNKNOWN"* ]]
    [[ "$output" == *"CI_STATE='mystery_value'"* ]]
    [ "$(grep -c 'pr merge' "$CLI_LOG")" -eq 0 ]
}
