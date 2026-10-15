#!/usr/bin/env bats
# aa-ma-footer.bats — tests for claude-code/hooks/lib/aa-ma-footer.sh and the
# skill's `footer-resolve` snippet (sole-dev-merge-fixes M1, forge L-054).
#
# Rule under test: one active plan → that plan; several → the one plan the
# branch changed since its merge-base with origin/HEAD (origin/main when
# origin/HEAD is unset); anything else → [ad-hoc] plus a stderr WARN.
#
# Cross-directory dependency: the helper-path cases extract the skill's
# stage-b-commit and stage-d-triage blocks with
# tests/commands/sole-dev-merge/fixtures/extract_stage.sh.

bats_require_minimum_version 1.5.0

setup() {
    REPO_ROOT="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)"
    HELPER="$REPO_ROOT/claude-code/hooks/lib/aa-ma-footer.sh"
    SKILL_MD="$REPO_ROOT/claude-code/skills/sole-dev-merge/SKILL.md"
    D_MD="$REPO_ROOT/claude-code/skills/sole-dev-merge/references/stage-d-triage.md"
    EXTRACT="$REPO_ROOT/tests/commands/sole-dev-merge/fixtures/extract_stage.sh"
    BATS_TMP="$(mktemp -d)"
    # why: never let a real ~/.claude link leak into the helper-path cases
    export CLAUDE_HOME="$BATS_TMP/claude-home"
    mkdir -p "$CLAUDE_HOME"
    unset AA_MA_FOOTER_HELPER
    # The helper must work without the caller's pipefail.
    set +o pipefail
    # shellcheck disable=SC1090
    . "$HELPER"
}

teardown() {
    [ -n "${BATS_TMP:-}" ] && rm -rf "$BATS_TMP"
}

# _repo PLAN... — repo with the given plans committed on main, a bare origin,
# origin/HEAD set, and branch `feat` checked out. cwd = the repo.
# REPO_DIR (default repo) names it, so one test can build two.
_repo() {
    local dir="$BATS_TMP/${REPO_DIR:-repo}"
    mkdir -p "$dir" && cd "$dir"
    git init -q -b main
    git config user.email t@t.com
    git config user.name T
    echo x > f.txt
    local p
    for p in "$@"; do
        mkdir -p ".claude/dev/active/$p"
        echo t > ".claude/dev/active/$p/$p-tasks.md"
    done
    git add -A
    git commit -q -m init
    git init --bare -q "$dir.git"
    git remote add origin "$dir.git"
    git push -q origin main
    git remote set-head origin main
    git checkout -q -b feat
}

# Every "picks X" case also checks the mirror case, so a helper that ignores
# what the branch touched (e.g. first directory found) cannot pass both.

# _touch PLAN — commit a change to PLAN's files on the current branch.
_touch() {
    echo more >> ".claude/dev/active/$1/$1-tasks.md"
    git commit -q -am "touch $1"
}

@test "footer: 0 plans → [ad-hoc]" {
    _repo
    run --separate-stderr emit_aa_ma_footer
    [ "$status" -eq 0 ]
    [ "$output" = $'\n\n[ad-hoc]' ]
}

@test "footer: 1 plan → that plan, even untouched" {
    _repo solo
    run --separate-stderr emit_aa_ma_footer
    [ "$status" -eq 0 ]
    [ "$output" = $'\n\n[AA-MA Plan] solo .claude/dev/active/solo' ]
    [ -z "$stderr" ]
}

@test "footer: 2 plans, branch touched b → [AA-MA Plan] b, no WARN (and a → a)" {
    _repo a b
    _touch b
    run --separate-stderr emit_aa_ma_footer
    [ "$status" -eq 0 ]
    [ "$output" = $'\n\n[AA-MA Plan] b .claude/dev/active/b' ]
    [ -z "$stderr" ]
    git checkout -q -b feat2 main
    _touch a
    run --separate-stderr emit_aa_ma_footer
    [ "$output" = $'\n\n[AA-MA Plan] a .claude/dev/active/a' ]
    [ -z "$stderr" ]
}

@test "footer: 2 plans, both touched → [ad-hoc] + WARN" {
    _repo a b
    _touch a
    _touch b
    run --separate-stderr emit_aa_ma_footer
    [ "$status" -eq 0 ]
    [ "$output" = $'\n\n[ad-hoc]' ]
    [[ "$stderr" == *"WARN: aa-ma-footer"* ]]
}

@test "footer: 2 plans, neither touched → [ad-hoc] + WARN" {
    _repo a b
    echo y >> f.txt && git commit -q -am "unrelated"
    run --separate-stderr emit_aa_ma_footer
    [ "$status" -eq 0 ]
    [ "$output" = $'\n\n[ad-hoc]' ]
    [[ "$stderr" == *"WARN: aa-ma-footer"* ]]
}

@test "footer: an uncommitted edit to b's files counts as touched" {
    _repo a b
    echo dirty >> .claude/dev/active/b/b-tasks.md
    run --separate-stderr emit_aa_ma_footer
    [ "$status" -eq 0 ]
    [ "$output" = $'\n\n[AA-MA Plan] b .claude/dev/active/b' ]
    git checkout -q -- .claude/dev/active/b
    echo dirty >> .claude/dev/active/a/a-tasks.md
    run --separate-stderr emit_aa_ma_footer
    [ "$output" = $'\n\n[AA-MA Plan] a .claude/dev/active/a' ]
}

@test "footer: detached HEAD → no crash, a footer is printed" {
    _repo a b
    git checkout -q --detach main
    run --separate-stderr emit_aa_ma_footer
    [ "$status" -eq 0 ]
    [[ "$output" == $'\n\n[ad-hoc]' || "$output" == $'\n\n[AA-MA Plan] '* ]]
}

@test "footer: no origin/HEAD → falls back to origin/main" {
    _repo a b
    git remote set-head origin -d
    ! git rev-parse -q --verify refs/remotes/origin/HEAD
    _touch b
    run --separate-stderr emit_aa_ma_footer
    [ "$status" -eq 0 ]
    [ "$output" = $'\n\n[AA-MA Plan] b .claude/dev/active/b' ]
    git checkout -q -b feat2 main
    _touch a
    run --separate-stderr emit_aa_ma_footer
    [ "$output" = $'\n\n[AA-MA Plan] a .claude/dev/active/a' ]
}

@test "footer: an untracked plan dir counts as touched" {
    REPO_DIR=r1 _repo a b
    mkdir -p .claude/dev/active/c
    echo t > .claude/dev/active/c/c-tasks.md
    run --separate-stderr emit_aa_ma_footer
    [ "$status" -eq 0 ]
    [ "$output" = $'\n\n[AA-MA Plan] c .claude/dev/active/c' ]
    REPO_DIR=r2 _repo b c
    mkdir -p .claude/dev/active/a
    echo t > .claude/dev/active/a/a-tasks.md
    run --separate-stderr emit_aa_ma_footer
    [ "$output" = $'\n\n[AA-MA Plan] a .claude/dev/active/a' ]
}

# --- the skill's footer-resolve snippet (B-commit, D) ----------------------

@test "footer-resolve: B-commit outside forge, helper under CLAUDE_HOME → commits with the plan footer" {
    _repo solo
    mkdir -p "$CLAUDE_HOME/hooks/lib"
    ln -s "$HELPER" "$CLAUDE_HOME/hooks/lib/aa-ma-footer.sh"
    [ ! -e claude-code/hooks/lib/aa-ma-footer.sh ]
    bash "$EXTRACT" stage-b-commit "$SKILL_MD" > "$BATS_TMP/b-commit.sh"
    echo z >> f.txt

    run bash "$BATS_TMP/b-commit.sh"
    [ "$status" -eq 0 ]
    [ "$(git log -1 --format=%B | sed '/^$/d' | tail -1)" = "[AA-MA Plan] solo .claude/dev/active/solo" ]
}

@test "footer-resolve: B-commit outside forge, no helper anywhere → [ad-hoc] footer and a notice" {
    _repo solo
    bash "$EXTRACT" stage-b-commit "$SKILL_MD" > "$BATS_TMP/b-commit.sh"
    echo z >> f.txt

    run bash "$BATS_TMP/b-commit.sh"
    [ "$status" -eq 0 ]
    [[ "$output" == *"aa-ma-footer.sh not found"* ]]
    [ "$(git log -1 --format=%B | sed '/^$/d' | tail -1)" = "[ad-hoc]" ]
}

@test "footer-resolve: D outside forge, no helper anywhere → runs (no findings), rc 0" {
    _repo
    bash "$EXTRACT" stage-d-triage "$D_MD" > "$BATS_TMP/d.sh"

    SLUG="bats-footer-$$" run bash "$BATS_TMP/d.sh"
    [ "$status" -eq 0 ]
    [[ "$output" == *"nothing to triage"* ]]
}

@test "footer-resolve: the B-commit and D snippets are byte-identical" {
    local b d
    b=$(sed -n '/# footer-resolve:begin/,/# footer-resolve:end/p' "$SKILL_MD")
    d=$(sed -n '/# footer-resolve:begin/,/# footer-resolve:end/p' "$D_MD")
    [ -n "$b" ]
    [ "$b" = "$d" ]
}
