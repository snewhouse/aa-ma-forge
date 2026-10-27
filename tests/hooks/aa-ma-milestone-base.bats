#!/usr/bin/env bats
# aa-ma-milestone-base.bats — `aa_ma_milestone_base` (code-conventions-impact 11.5, R1).
#
# The milestone window for §6.7 fence 4 and verify-impl: `git merge-base origin/<default> HEAD`.
# Fails closed with rc 2 and a named error when there is no window to certify.

bats_require_minimum_version 1.5.0

setup() {
    REPO_ROOT="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)"
    # shellcheck source=/dev/null
    . "${REPO_ROOT}/claude-code/hooks/lib/aa-ma-parse.sh"
    WORK="$(mktemp -d "${BATS_TMPDIR}/milestone-base.XXXXXX")"
    git init -q --bare -b main "$WORK/origin.git"
    git clone -q "$WORK/origin.git" "$WORK/r" 2>/dev/null
    cd "$WORK/r" || return 1
    _commit base
    git push -q origin main
    git remote set-head origin -a > /dev/null
}

teardown() {
    rm -rf "$WORK"
}

_commit() {
    echo "$1" > "f-$1"
    git add -A && git -c user.name=t -c user.email=t@t -c commit.gpgsign=false commit -qm "$1"
}

@test "a branched milestone → the merge-base SHA with origin's default branch" {
    want=$(git rev-parse HEAD)
    git checkout -q -b feat
    _commit one
    _commit two
    run aa_ma_milestone_base
    [ "$status" -eq 0 ]
    [ "$output" = "$want" ]
}

@test "on the default branch tip (branch == main) → rc 2, no milestone window" {
    run aa_ma_milestone_base
    [ "$status" -eq 2 ]
    [[ "$output" == *"no milestone window"* ]]
}

@test "a rebased branch → the new merge-base" {
    git checkout -q -b feat
    _commit one
    git checkout -q main
    _commit main2
    git push -q origin main
    new=$(git rev-parse HEAD)
    git checkout -q feat
    git -c user.name=t -c user.email=t@t rebase -q main
    run aa_ma_milestone_base
    [ "$status" -eq 0 ]
    [ "$output" = "$new" ]
}

@test "no origin → rc 2 with a named error" {
    git remote remove origin
    git checkout -q -b feat
    _commit one
    run aa_ma_milestone_base
    [ "$status" -eq 2 ]
    [[ "$output" == *"no origin default branch"* ]]
}

@test "origin without a HEAD symref falls back to origin/main" {
    git remote set-head origin -d
    want=$(git rev-parse HEAD)
    git checkout -q -b feat
    _commit one
    run aa_ma_milestone_base
    [ "$status" -eq 0 ]
    [ "$output" = "$want" ]
}

# verify-impl Step 1 (Phase 6.8): its milestone window, executed as shipped. From the
# `# Milestone window` comment to MILESTONE_HEAD_SHA, with N and the task paths stubbed.
_verify_impl_window() {
    awk '/^# Milestone window/{f=1} f; /^MILESTONE_HEAD_SHA=/{exit}' \
        "${REPO_ROOT}/claude-code/skills/verify-impl/SKILL.md" > "$WORK/window.sh"
    run bash -c '. "$1"; N=2 TASK_DIR=x TASK_NAME=x; . "$2"; echo "BASE=$MILESTONE_BASE_SHA"' \
        _ "${REPO_ROOT}/claude-code/hooks/lib/aa-ma-parse.sh" "$WORK/window.sh"
}

@test "verify-impl Step 1 takes the window from aa_ma_milestone_base" {
    want=$(git rev-parse HEAD)
    git checkout -q -b feat
    _commit one
    _verify_impl_window
    [ "$status" -eq 0 ]
    [[ "$output" == *"BASE=$want"* ]]
    [[ "$output" != *WARN* ]]
}

@test "verify-impl Step 1 without a window: one WARN, and HEAD~10 really applies" {
    for i in 1 2 3 4 5 6 7 8 9 10 11; do _commit "c$i"; done
    git push -q origin main
    want=$(git rev-parse HEAD~10)
    _verify_impl_window
    [ "$status" -eq 0 ]
    [ "$(grep -c WARN <<< "$output")" -eq 1 ]
    [[ "$output" == *"BASE=$want"* ]]
}
