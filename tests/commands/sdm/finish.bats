#!/usr/bin/env bats
# finish.bats — `sdm.sh finish <PR_NUM>` (sole-dev-merge-simplify 1.1). GitHub only.
#
# Covers the one PR lookup, the strategy re-read, the check-runs gate, the merge with
# --match-head-commit, the remote branch delete with a lease, and the G4 cleanup (plain
# checkout and linked worktree). Ported tests name their source:
#   g_merge:<line>  tests/commands/sole-dev-merge/test_stage_g_merge.bats
#   state:<line>    tests/commands/sole-dev-merge/test_stage_state.bats
# New tests are prefixed `new <n>:`.
#
# Sandbox (fixtures/helpers.bash): $WORK on `feature`, 1 commit ahead of main; origin is
# https://github.com/test/repo.git, rewritten to the bare forge $FORGE, so the branch delete
# and ls-remote hit the forge and nothing reaches GitHub. gh is fixtures/bin/gh (logs to $CLI_LOG).
# The stub's `pr merge` does not move the forge's main: tests that check the fast-forward move
# it themselves (post-merge server state).

bats_require_minimum_version 1.5.0

load fixtures/helpers

setup() {
    sdm_setup
    FORGE="$BATS_TEST_TMPDIR/forge/test/repo.git"
    PR_URL="https://github.com/test/repo/pull/$STUB_PR_NUM"
}

# Full ref name → its sha on the forge, or empty when the ref does not exist.
forge_sha() { git --git-dir="$FORGE" rev-parse -q --verify "$1" || true; }   # why: absent ref is a normal answer
local_sha() { git -C "${2:-$WORK}" rev-parse -q --verify "$1" || true; }     # why: absent ref is a normal answer

# The branch is on the forge (ship pushed it) and the forge's main holds the branch tip (the merge).
pushed_and_merged() {
    git push -q origin "${1:-feature}"
    git --git-dir="$FORGE" update-ref refs/heads/main "$(git rev-parse "${1:-feature}")"
}

# Main checkout $WORK on main (optionally moved to $1 first) with a linked worktree for branch $2
# (default feature) at $WORK/.worktrees/$2, in the post-merge server state. Leaves cwd in the
# worktree. Sets WT (the worktree's toplevel) and MAIN (the main checkout's toplevel).
wt_setup() {
    local branch="${2:-feature}"
    if [[ -n "${1:-}" ]]; then mv "$WORK" "$1"; WORK=$1; cd "$WORK"; fi
    [[ "$branch" == feature ]] || git branch -q -m feature "$branch"
    pushed_and_merged "$branch"
    git checkout -q main
    git worktree add -q "$WORK/.worktrees/$branch" "$branch"
    cd "$WORK/.worktrees/$branch"
    WT=$(git rev-parse --show-toplevel)
    MAIN=$(git -C "$WORK" rev-parse --show-toplevel)
}

# Fingerprint of a checkout's tracked state: HEAD, index/worktree diff, status.
fingerprint() {
    { git -C "$1" rev-parse HEAD; git -C "$1" diff HEAD; git -C "$1" status --porcelain --untracked-files=no; } | sha256sum
}

merge_line() { grep '^gh pr merge ' "$CLI_LOG" || true; }   # why: no merge call is a normal answer

# ---------------------------------------------------------------------------
# Merge dispatch
# ---------------------------------------------------------------------------

@test "g_merge:107 green CI + rebase allowed → exactly one 'pr merge 42 … --rebase', no --delete-branch" {
    pushed_and_merged
    export GH_ALLOW_REBASE=true

    run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    [ "$status" -eq 0 ]
    [ "$(grep -cE "^gh pr merge $STUB_PR_NUM .*--rebase( |\$)" "$CLI_LOG")" -eq 1 ]
    [ "$(gh_calls 'pr merge')" -eq 1 ]
    [ "$(grep -c -- '--delete-branch' "$CLI_LOG")" -eq 0 ]
}

@test "g_merge:118 merge fallback: GH_ALLOW_REBASE=false → 'pr merge 42 … --merge', never --rebase, no --delete-branch" {
    pushed_and_merged
    export GH_ALLOW_REBASE=false

    run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    [ "$status" -eq 0 ]
    [ "$(grep -cE "^gh pr merge $STUB_PR_NUM .*--merge( |\$)" "$CLI_LOG")" -eq 1 ]
    [ "$(grep -c -- '--rebase' "$CLI_LOG")" -eq 0 ]
    [ "$(grep -c -- '--delete-branch' "$CLI_LOG")" -eq 0 ]
}

@test "g_merge:130 green → merge without --delete-branch, then the remote branch is gone, STATUS: OK" {
    pushed_and_merged

    run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    [ "$status" -eq 0 ]
    [ "$(gh_calls 'pr merge')" -eq 1 ]
    [ "$(grep -c -- '--delete-branch' "$CLI_LOG")" -eq 0 ]
    [ -z "$(forge_sha refs/heads/feature)" ]
    [ "${lines[-1]}" = "STATUS: OK" ]
}

@test "g_merge:142 state after the merge call != MERGED → STATUS: MERGE_FAILED, remote branch kept" {
    pushed_and_merged
    export GH_PR_STATE=OPEN

    run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    [ "$status" -eq 0 ]
    [[ "$output" == *"STATUS: MERGE_FAILED"* ]]
    [[ "$output" != *"STATUS: OK"* ]]
    [ -n "$(forge_sha refs/heads/feature)" ]
}

@test "g_merge:153 gh pr merge rc=1 but state MERGED → treated as merged, branch deleted" {
    pushed_and_merged
    export GH_MERGE_RC=1

    run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    [ "$status" -eq 0 ]
    [[ "$stderr" == *"finish: gh pr merge rc=1 — checking PR state"* ]]
    [ -z "$(forge_sha refs/heads/feature)" ]
    [ "${lines[-1]}" = "STATUS: OK" ]
}

@test "g_merge:163 branch already deleted server-side → no abort, no BRANCH_NOT_DELETED" {
    pushed_and_merged
    git --git-dir="$FORGE" update-ref -d refs/heads/feature

    run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    [ "$status" -eq 0 ]
    [[ "$output" != *"BRANCH_NOT_DELETED"* ]]
    [ "${lines[-1]}" = "STATUS: OK" ]
}

@test "g_merge:174 remote refuses the delete → STATUS: BRANCH_NOT_DELETED — feature, rc 0" {
    pushed_and_merged
    printf '#!/bin/sh\nwhile read o n r; do [ "$n" = 0000000000000000000000000000000000000000 ] && exit 1; done; exit 0\n' \
        > "$FORGE/hooks/pre-receive"
    chmod +x "$FORGE/hooks/pre-receive"

    run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    [ "$status" -eq 0 ]
    [[ $'\n'"$output"$'\n' == *$'\n'"STATUS: BRANCH_NOT_DELETED — feature"$'\n'* ]]
    [ -n "$(forge_sha refs/heads/feature)" ]
}

# ---------------------------------------------------------------------------
# Refuse before any state change
# ---------------------------------------------------------------------------

@test "g_merge:211 PR head ref differs from the branch → ABORT rc 1, no merge" {
    git push -q origin feature
    export GH_PR_HEAD_REF=other

    run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    [ "$status" -eq 1 ]
    [ "$output" = "ABORT: finish: PR $STUB_PR_NUM head is 'other', not 'feature'" ]
    [ "$(gh_calls 'pr merge')" -eq 0 ]
    [ -n "$(forge_sha refs/heads/feature)" ]
}

@test "g_merge:222 run on the default branch → preflight ABORT rc 1, no gh call" {
    git push -q origin feature
    git checkout -q main
    local main_before; main_before=$(forge_sha refs/heads/main)

    run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    [ "$status" -eq 1 ]
    [ "$output" = "ABORT: Cannot run /sole-dev-merge from main branch" ]
    [ ! -s "$CLI_LOG" ]
    [ "$(forge_sha refs/heads/main)" = "$main_before" ]
    [ -n "$(forge_sha refs/heads/feature)" ]
}

@test "g_merge:244 a same-named tag on the remote survives the branch delete" {
    pushed_and_merged
    git tag feature-tag-src
    git push -q origin "feature-tag-src:refs/tags/feature"

    run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    [ "$status" -eq 0 ]
    [ -z "$(forge_sha refs/heads/feature)" ]
    [ -n "$(forge_sha refs/tags/feature)" ]
}

@test "g_merge:255 remote branch other/feature → not deleted, no false BRANCH_NOT_DELETED" {
    pushed_and_merged
    git push -q origin "feature:refs/heads/other/feature"

    run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    [ "$status" -eq 0 ]
    [[ "$output" != *"BRANCH_NOT_DELETED"* ]]
    [ -z "$(forge_sha refs/heads/feature)" ]
    [ -n "$(forge_sha refs/heads/other/feature)" ]
}

@test "g_merge:270 ls-remote fails after the delete → BRANCH_NOT_DELETED with its rc, never read as deleted" {
    pushed_and_merged
    local real_git; real_git=$(command -v git)
    mkdir -p "$BATS_TEST_TMPDIR/gitbin"
    printf '#!/bin/sh\n[ "$1" = ls-remote ] && exit 128\nexec %s "$@"\n' "$real_git" > "$BATS_TEST_TMPDIR/gitbin/git"
    chmod +x "$BATS_TEST_TMPDIR/gitbin/git"

    PATH="$BATS_TEST_TMPDIR/gitbin:$PATH" run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    [ "$status" -eq 0 ]
    [[ $'\n'"$output"$'\n' == *$'\n'"STATUS: BRANCH_NOT_DELETED — feature (ls-remote rc=128, could not verify)"$'\n'* ]]
}

# ---------------------------------------------------------------------------
# Check-runs gate (CI_STATE is no longer an input: finish reads the check-runs itself)
# ---------------------------------------------------------------------------

@test "g_merge:303 a check-run still in progress → STATUS: CI_NOT_DONE, no merge" {
    pushed_and_merged
    export GH_CHECK_RUNS=$'completed success\nqueued null'

    run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    [ "$status" -eq 0 ]
    [ "$output" = "STATUS: CI_NOT_DONE — 1 check-run(s) not completed; re-run sdm.sh finish $STUB_PR_NUM" ]
    [ "$(gh_calls 'pr merge')" -eq 0 ]
    [ -n "$(forge_sha refs/heads/feature)" ]
}

@test "g_merge:314 a failed check-run → STATUS: CI_FAILED — see <url>, no merge" {
    pushed_and_merged
    export GH_CHECK_RUNS=$'completed success\ncompleted failure'

    run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    [ "$status" -eq 0 ]
    [ "$output" = "STATUS: CI_FAILED — see $PR_URL" ]
    [ "$(gh_calls 'pr merge')" -eq 0 ]
    [ -n "$(forge_sha refs/heads/feature)" ]
}

# ---------------------------------------------------------------------------
# G4 cleanup
# ---------------------------------------------------------------------------

@test "g_merge:329 plain checkout → on main, fast-forwarded, fetch --prune, local branch deleted, summary lines" {
    pushed_and_merged
    git push -q origin main:refs/heads/gone
    git fetch -q origin
    git --git-dir="$FORGE" update-ref -d refs/heads/gone
    [ "$(git branch --show-current)" = feature ]

    run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    [ "$status" -eq 0 ]
    [ "$(git -C "$WORK" branch --show-current)" = main ]
    [ "$(local_sha refs/heads/main)" = "$(forge_sha refs/heads/main)" ]
    [ -z "$(local_sha refs/remotes/origin/gone)" ]
    [ -z "$(local_sha refs/heads/feature)" ]
    local short; short=$(git -C "$WORK" rev-parse --short main)
    [ "${#lines[@]}" -eq 3 ]
    [ "${lines[0]}" = "finish: cleanup done — main at $short" ]
    [ "${lines[1]}" = "Final: branch=feature merged into main (sha=$short) — $PR_URL" ]
    [ "${lines[2]}" = "STATUS: OK" ]
}

@test "g_merge:384 from a worktree, clean main checkout → main fast-forwarded, worktree untouched, cleanup printed" {
    wt_setup
    local wt_head; wt_head=$(git rev-parse HEAD)

    run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    [ "$status" -eq 0 ]
    [ "$(git -C "$MAIN" rev-parse HEAD)" = "$(forge_sha refs/heads/main)" ]
    [ "$(git -C "$MAIN" branch --show-current)" = main ]
    [ "$(git -C "$WT" branch --show-current)" = feature ]
    [ "$(git -C "$WT" rev-parse HEAD)" = "$wt_head" ]
    [ -n "$(local_sha refs/heads/feature "$MAIN")" ]
    [ -z "$(forge_sha refs/heads/feature)" ]
    [[ "$output" == *"Operator cleanup:"* ]]
    [[ "$output" == *"worktree remove"* ]]
    [[ "$output" == *"branch -D feature"* ]]
    [ "${lines[-1]}" = "STATUS: OK worktree=$WT" ]
}

@test "g_merge:399 main checkout path with a space → printed cleanup commands are quoted" {
    wt_setup "$BATS_TEST_TMPDIR/my main"

    run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    [ "$status" -eq 0 ]
    local rm_line del_line
    rm_line=$(grep -E '^ +git -C .* worktree remove ' <<<"$output")
    del_line=$(grep -E '^ +git -C .* branch -D ' <<<"$output")
    [ -n "$rm_line" ]
    [ -n "$del_line" ]
    # Dry run: a git function records argv instead of acting.
    git() { printf '%s\n' "$@" > "$BATS_TEST_TMPDIR/argv"; }
    eval "$rm_line"
    [ "$(sed -n 2p "$BATS_TEST_TMPDIR/argv")" = "$MAIN" ]
    [ "$(sed -n 5p "$BATS_TEST_TMPDIR/argv")" = "$WT" ]
    eval "$del_line"
    [ "$(sed -n 2p "$BATS_TEST_TMPDIR/argv")" = "$MAIN" ]
    [ "$(sed -n 5p "$BATS_TEST_TMPDIR/argv")" = feature ]
    unset -f git
}

@test "g_merge:419 dirty tracked file in the main checkout → STATUS: MAIN_CHECKOUT_DIRTY, main byte-identical" {
    wt_setup
    echo dirty >> "$MAIN/a.txt"
    local before; before=$(fingerprint "$MAIN")

    run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    [ "$status" -eq 0 ]
    [[ "$output" == *"STATUS: MAIN_CHECKOUT_DIRTY — "*"a.txt"* ]]
    [[ "$output" != *"STATUS: OK"* ]]
    [ "$(fingerprint "$MAIN")" = "$before" ]
    [ "$(git -C "$WT" branch --show-current)" = feature ]
}

@test "g_merge:431 untracked file in the main checkout → not dirty, fast-forwarded (branch feature/x)" {
    wt_setup "" feature/x
    echo u > "$MAIN/untracked.txt"

    run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    [ "$status" -eq 0 ]
    [[ "$output" != *"MAIN_CHECKOUT_DIRTY"* ]]
    [ "$(git -C "$MAIN" rev-parse HEAD)" = "$(forge_sha refs/heads/main)" ]
    [ -f "$MAIN/untracked.txt" ]
    [ "$(git -C "$WT" branch --show-current)" = feature/x ]
    [[ "$output" == *"branch -D feature/x"* ]]
    [ -z "$(forge_sha refs/heads/feature/x)" ]
}

@test "g_merge:444 run from a subdirectory of a plain checkout → plain-checkout path" {
    pushed_and_merged
    mkdir -p sub
    cd sub

    run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    [ "$status" -eq 0 ]
    [ "$(git -C "$WORK" branch --show-current)" = main ]
    [ "$(local_sha refs/heads/main)" = "$(forge_sha refs/heads/main)" ]
    [[ "$output" != *"worktree remove"* ]]
}

@test "g_merge:457 main checkout on branch 'other' → 'other' untouched, local main updated or MAIN_NOT_UPDATED" {
    wt_setup
    git -C "$MAIN" checkout -q -b other
    local other_sha; other_sha=$(git -C "$MAIN" rev-parse other)

    run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    [ "$status" -eq 0 ]
    [ "$(git -C "$MAIN" branch --show-current)" = other ]
    [ "$(git -C "$MAIN" rev-parse other)" = "$other_sha" ]
    [ "$(git -C "$WT" branch --show-current)" = feature ]
    [[ "$(local_sha refs/heads/main "$MAIN")" == "$(forge_sha refs/heads/main)" \
       || "$output" == *"STATUS: MAIN_NOT_UPDATED"* ]]
}

@test "g_merge:471 default branch in use by a third worktree → STATUS: MAIN_NOT_UPDATED, never STATUS: OK" {
    wt_setup
    git -C "$MAIN" checkout -q -b other
    git -C "$MAIN" worktree add -q "$BATS_TEST_TMPDIR/wt-main" main

    run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    [ "$status" -eq 0 ]
    [ "${lines[-1]}" = "STATUS: MAIN_NOT_UPDATED — main is in use by another worktree" ]
    [[ "$output" != *"STATUS: OK"* ]]
}

# ---------------------------------------------------------------------------
# The one PR lookup
# ---------------------------------------------------------------------------

@test "g_merge:556 PR from another repository (isCrossRepository) → ABORT rc 1, no merge" {
    git push -q origin feature
    export GH_PR_CROSS_REPO=true

    run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    [ "$status" -eq 1 ]
    [ "$output" = "ABORT: finish: PR $STUB_PR_NUM is from another repository (isCrossRepository=true)" ]
    [ "$(gh_calls 'pr merge')" -eq 0 ]
    [ -n "$(forge_sha refs/heads/feature)" ]
}

@test "g_merge:568 reads the PR's head, owner, state and head oid in one lookup" {
    pushed_and_merged

    run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    [ "$status" -eq 0 ]
    [ "$(grep -cE "^gh pr view $STUB_PR_NUM -R test/repo .*--json headRefName,isCrossRepository,state,headRefOid,url( |\$)" "$CLI_LOG")" -eq 1 ]
    # the lookup and the post-merge state read, nothing else
    [ "$(gh_calls 'pr view')" -eq 2 ]
    [ "$(grep -cE -- '--json (headRefName|isCrossRepository)( |$)' "$CLI_LOG")" -eq 0 ]
}

@test "g_merge:578 an unreadable PR (lookup fails) → ABORT rc 1, no merge" {
    git push -q origin feature
    export GH_PR_LOOKUP_RC=1

    run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    [ "$status" -eq 1 ]
    [ "$output" = "ABORT: finish: cannot read PR $STUB_PR_NUM (head/owner lookup failed)" ]
    [ "$(gh_calls 'pr merge')" -eq 0 ]
}

@test "g_merge:620 a PR MERGED at another commit (stale PR_NUM) → ABORT rc 1, no merge, remote branch kept" {
    git push -q origin feature
    local other; other=$(git rev-parse main)
    export GH_PR_LOOKUP_STATE=MERGED GH_PR_HEAD_OID="$other"

    run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    [ "$status" -eq 1 ]
    [ "$output" = "ABORT: finish: PR $STUB_PR_NUM is MERGED at $other, not this branch's HEAD" ]
    [ "$(gh_calls 'pr merge')" -eq 0 ]
    [ -n "$(forge_sha refs/heads/feature)" ]
}

@test "g_merge:632 this branch's PR already merged at HEAD → no merge call, branch deleted, cleanup proceeds" {
    pushed_and_merged
    export GH_PR_LOOKUP_STATE=MERGED

    run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    [ "$status" -eq 0 ]
    [ "$(gh_calls 'pr merge')" -eq 0 ]
    [[ "$stderr" == *"finish: PR $STUB_PR_NUM already merged at HEAD — no merge call"* ]]
    [ -z "$(forge_sha refs/heads/feature)" ]
    [ "$(git -C "$WORK" branch --show-current)" = main ]
}

@test "state:390 no cleanup unless the merge is confirmed: state OPEN after the merge call → MERGE_FAILED, nothing deleted" {
    pushed_and_merged
    export GH_PR_STATE=OPEN

    run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    [ "$status" -eq 0 ]
    [ "$output" = "STATUS: MERGE_FAILED — state=OPEN — see $PR_URL" ]
    [ -n "$(forge_sha refs/heads/feature)" ]
    [ "$(git branch --show-current)" = feature ]
    [ -n "$(local_sha refs/heads/feature)" ]
}

# ---------------------------------------------------------------------------
# New tests
# ---------------------------------------------------------------------------

@test "new 2: all check-runs skipped → STATUS: CI_FAILED, no merge call" {
    pushed_and_merged
    export GH_CHECK_RUNS=$'completed skipped\ncompleted skipped'

    run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    [ "$status" -eq 0 ]
    [ "$output" = "STATUS: CI_FAILED — see $PR_URL" ]
    [ "$(gh_calls 'pr merge')" -eq 0 ]
}

@test "new 2: zero check-runs → STATUS: CI_FAILED, no merge call" {
    pushed_and_merged
    export GH_CHECK_RUNS=''

    run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    [ "$status" -eq 0 ]
    [ "$output" = "STATUS: CI_FAILED — see $PR_URL" ]
    [ "$(gh_calls 'pr merge')" -eq 0 ]
}

@test "new 3: an in-progress run → exact STATUS: CI_NOT_DONE line, no merge" {
    pushed_and_merged
    export GH_CHECK_RUNS='in_progress null'

    run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    [ "$status" -eq 0 ]
    [ "$output" = "STATUS: CI_NOT_DONE — 1 check-run(s) not completed; re-run sdm.sh finish $STUB_PR_NUM" ]
    [ "$(gh_calls 'pr merge')" -eq 0 ]
}

@test "new 3: a cancelled run beside a success → STATUS: CI_FAILED, no merge" {
    pushed_and_merged
    export GH_CHECK_RUNS=$'completed success\ncompleted cancelled'

    run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    [ "$status" -eq 0 ]
    [ "$output" = "STATUS: CI_FAILED — see $PR_URL" ]
    [ "$(gh_calls 'pr merge')" -eq 0 ]
}

@test "new 3: neutral + success → merges" {
    pushed_and_merged
    export GH_CHECK_RUNS=$'completed neutral\ncompleted success'

    run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    [ "$status" -eq 0 ]
    [ "$(gh_calls 'pr merge')" -eq 1 ]
    [ "${lines[-1]}" = "STATUS: OK" ]
}

@test "check-runs unreadable → ABORT: finish: cannot read check-runs, no merge" {
    pushed_and_merged
    export GH_CHECK_RUNS_RC=1

    run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    [ "$status" -eq 1 ]
    [ "$output" = "ABORT: finish: cannot read check-runs" ]
    [ "$(gh_calls 'pr merge')" -eq 0 ]
}

@test "more check-runs than one page → ABORT: finish: <total> check-runs, not all read, no merge" {
    pushed_and_merged
    export GH_CHECK_RUNS='completed success' GH_CHECK_RUNS_TOTAL=101

    run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    [ "$status" -eq 1 ]
    [ "$output" = "ABORT: finish: 101 check-runs, not all read" ]
    [ "$(gh_calls 'pr merge')" -eq 0 ]
}

@test "a CLOSED PR → ABORT: finish: PR <n> is CLOSED, not OPEN, no merge, branch kept" {
    pushed_and_merged
    export GH_PR_LOOKUP_STATE=CLOSED

    run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    [ "$status" -eq 1 ]
    [ "$output" = "ABORT: finish: PR $STUB_PR_NUM is CLOSED, not OPEN" ]
    [ "$(gh_calls 'pr merge')" -eq 0 ]
    [ -n "$(forge_sha refs/heads/feature)" ]
}

@test "new 5: strategy re-read fails → ABORT: finish: cannot read allow_rebase_merge, no merge" {
    pushed_and_merged
    export GH_API_REPO_RC=1

    run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    [ "$status" -eq 1 ]
    [ "$output" = "ABORT: finish: cannot read allow_rebase_merge" ]
    [ "$(gh_calls 'pr merge')" -eq 0 ]
    [ -n "$(forge_sha refs/heads/feature)" ]
}

@test "new 6: plain checkout, 'git checkout main' blocked → STATUS: MAIN_NOT_UPDATED, rc 0, no set -e death" {
    # feature drops a.txt and an untracked a.txt with other content sits in the work tree:
    # checking out main (which tracks a.txt) would overwrite it, so git refuses.
    git rm -q a.txt
    mkcommit "chore: drop a.txt"
    echo different > a.txt
    pushed_and_merged

    run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    [ "$status" -eq 0 ]
    [ "${lines[-1]}" = "STATUS: MAIN_NOT_UPDATED — could not switch to and fast-forward main" ]
    [[ "$output" != *"STATUS: OK"* ]]
    [ "$(git branch --show-current)" = feature ]
    [ "$(cat a.txt)" = different ]
    [ -z "$(forge_sha refs/heads/feature)" ]
}

@test "new 6: plain checkout, local main diverged (ff-only fails) → STATUS: MAIN_NOT_UPDATED, rc 0" {
    git checkout -q main
    echo local > local.txt
    git add local.txt
    mkcommit "local-only commit on main"
    git checkout -q feature
    pushed_and_merged

    run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    [ "$status" -eq 0 ]
    [ "${lines[-1]}" = "STATUS: MAIN_NOT_UPDATED — could not switch to and fast-forward main" ]
    [[ "$output" != *"STATUS: OK"* ]]
}

@test "new 7: --match-head-commit mismatch → STATUS: MERGE_FAILED, remote branch kept, no delete" {
    pushed_and_merged
    local pushed; pushed=$(forge_sha refs/heads/feature)
    export GH_MERGE_HEAD_MISMATCH=1 GH_PR_STATE=OPEN

    run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    [ "$status" -eq 0 ]
    [ "$output" = "STATUS: MERGE_FAILED — state=OPEN — see $PR_URL" ]
    [ "$(forge_sha refs/heads/feature)" = "$pushed" ]
    [ "$(git branch --show-current)" = feature ]
}

@test "new 8: finish from a tracked subdirectory of a plain checkout → toplevel used, STATUS: OK" {
    mkdir -p src/pkg
    echo x > src/pkg/x.txt
    git add src/pkg/x.txt
    mkcommit "feat: add src/pkg"
    pushed_and_merged
    cd src/pkg

    run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    cd "$WORK"
    [ "$status" -eq 0 ]
    [ "${lines[-1]}" = "STATUS: OK" ]
    [ -z "$(forge_sha refs/heads/feature)" ]
    [ "$(git branch --show-current)" = main ]
}

@test "new 10: a PR_NUM that is not a PR number → ABORT rc 1 before any git or gh call" {
    local x
    for x in abc 0 -1 '' 07 '--repo=evil/x'; do
        : > "$CLI_LOG"
        run --separate-stderr "$SDM" finish "$x"
        echo "PR_NUM='$x' rc=$status out=$output"
        [ "$status" -eq 1 ]
        [ "$output" = "ABORT: finish: PR_NUM '$x' is not a PR number" ]
        [ ! -s "$CLI_LOG" ]
    done
    # checked before the preflight: outside a repository the PR_NUM line still wins
    cd "$BATS_TEST_TMPDIR"
    run --separate-stderr "$SDM" finish abc
    [ "$status" -eq 1 ]
    [ "$output" = "ABORT: finish: PR_NUM 'abc' is not a PR number" ]
    [ ! -s "$CLI_LOG" ]
}

@test "new 11: allow_rebase_merge is null → ABORT, no merge" {
    pushed_and_merged
    export GH_ALLOW_REBASE=null

    run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    [ "$status" -eq 1 ]
    [ "$output" = "ABORT: finish: allow_rebase_merge is 'null', not true or false" ]
    [ "$(gh_calls 'pr merge')" -eq 0 ]
}

@test "new 12: OPEN PR whose head is not local HEAD → ABORT, no merge, no check-runs read" {
    pushed_and_merged
    local sha; sha=$(git rev-parse HEAD)
    export GH_PR_HEAD_OID=1111111111111111111111111111111111111111

    run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    [ "$status" -eq 1 ]
    [ "$output" = "ABORT: finish: PR $STUB_PR_NUM head is at $GH_PR_HEAD_OID, not this branch's HEAD $sha — push, then re-run ship" ]
    [ "$(gh_calls 'pr merge')" -eq 0 ]
    [ "$(grep -c 'check-runs' "$CLI_LOG")" -eq 0 ]
    [ -n "$(forge_sha refs/heads/feature)" ]
}

@test "new 13: merge call fails and the PR stays OPEN → MERGE_FAILED, no branch delete" {
    pushed_and_merged
    export GH_MERGE_RC=1 GH_PR_STATE=OPEN

    run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    [ "$status" -eq 0 ]
    [ "$output" = "STATUS: MERGE_FAILED — state=OPEN — see $PR_URL" ]
    [ -n "$(forge_sha refs/heads/feature)" ]
    [ -n "$(local_sha refs/heads/feature)" ]
}

@test "new 13: merge rc 0 but state CLOSED → MERGE_FAILED, no branch delete" {
    pushed_and_merged
    export GH_PR_STATE=CLOSED

    run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    [ "$status" -eq 0 ]
    [ "$output" = "STATUS: MERGE_FAILED — state=CLOSED — see $PR_URL" ]
    [ -n "$(forge_sha refs/heads/feature)" ]
    [ "$(git branch --show-current)" = feature ]
}

@test "new 14: already MERGED at HEAD → no merge, no strategy read, no check-runs, branch deleted, STATUS: OK" {
    pushed_and_merged
    export GH_PR_LOOKUP_STATE=MERGED

    run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    [ "$status" -eq 0 ]
    [ "$(gh_calls 'pr merge')" -eq 0 ]
    [ "$(grep -c 'allow_rebase_merge' "$CLI_LOG")" -eq 0 ]
    [ "$(grep -c 'check-runs' "$CLI_LOG")" -eq 0 ]
    [ -z "$(forge_sha refs/heads/feature)" ]
    [ "${lines[-1]}" = "STATUS: OK" ]
}

@test "new 15: remote branch moved after the merge → lease keeps it, STATUS: BRANCH_NOT_DELETED — feature" {
    pushed_and_merged
    local head moved
    head=$(git rev-parse HEAD)
    echo moved > moved.txt
    git add moved.txt
    mkcommit "feat: pushed after the merge"
    moved=$(git rev-parse HEAD)
    git reset -q --hard "$head"
    git push -q --force origin "$moved:refs/heads/feature"
    [ "$(git rev-parse HEAD)" = "$head" ]

    run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    [ "$status" -eq 0 ]
    [ "$(forge_sha refs/heads/feature)" = "$moved" ]
    [[ $'\n'"$output"$'\n' == *$'\n'"STATUS: BRANCH_NOT_DELETED — feature"$'\n'* ]]
}

@test "new: merge argv → --match-head-commit <local HEAD> and -R test/repo, never --delete-branch or --auto" {
    pushed_and_merged
    local sha line; sha=$(git rev-parse HEAD)

    run --separate-stderr "$SDM" finish "$STUB_PR_NUM"
    [ "$status" -eq 0 ]
    line=$(merge_line)
    [ "$(grep -c . <<<"$line")" -eq 1 ]
    [[ "$line " == "gh pr merge $STUB_PR_NUM "* ]]
    [[ " $line " == *" -R test/repo "* ]]
    [[ " $line " == *" --match-head-commit $sha "* ]]
    [[ " $line " == *" --rebase "* ]]
    [[ "$line" != *"--delete-branch"* ]]
    [[ "$line" != *"--auto"* ]]
}
