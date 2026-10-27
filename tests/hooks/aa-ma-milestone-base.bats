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
