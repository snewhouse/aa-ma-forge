#!/usr/bin/env bats
# test_stage_a_preflight.bats — verifies Stage A (pre-flight checks).
#
# Plan §4.1.2 acceptance: given `git branch --show-current` returns `main`,
# the command exits with non-zero AND stdout contains exactly:
#   `ABORT: Cannot run /sole-dev-merge from main branch`
#
# This file covers all 4 abort branches plus the happy path. Each abort
# message has a unique anchor phrase grep-tested for distinctness.

setup() {
  REPO_ROOT="$(cd "$BATS_TEST_DIRNAME/../../.." && pwd)"

  TMPDIR="$(mktemp -d)"
  cd "$TMPDIR" || return 1
  git init -b main -q
  git config user.email "test@test.com"
  git config user.name "test"
  git config commit.gpgsign false
  echo "a" > a
  git add a
  git commit -q -m "baseline"
  git checkout -b feat -q

  # shellcheck source=fixtures/load_stages.bash
  source "$REPO_ROOT/tests/commands/sole-dev-merge/fixtures/load_stages.bash"
  eval "$(SOLE_DEV_MERGE_MD=$REPO_ROOT/claude-code/commands/sole-dev-merge.md load_stages)"
}

teardown() {
  cd /
  rm -rf "$TMPDIR"
}

@test "Stage A abort 1: on main branch (plan §4.1.2 exact string)" {
  git checkout main -q
  run stage_a_preflight
  [ "$status" -eq 1 ]
  [[ "$output" == *"ABORT: Cannot run /sole-dev-merge from main branch"* ]]
}

@test "Stage A abort 2: working tree is dirty" {
  # Untracked file in working tree → git status --porcelain non-empty
  touch dirty_file
  run stage_a_preflight
  [ "$status" -eq 2 ]
  [[ "$output" == *"ABORT: Working tree is dirty"* ]]
  rm -f dirty_file
}

@test "Stage A abort 3: no remote configured" {
  # feat branch, clean tree, no remote → abort 3
  run stage_a_preflight
  [ "$status" -eq 3 ]
  [[ "$output" == *"ABORT: No remote configured"* ]]
}

@test "Stage A abort 4: branch has no commits ahead of main" {
  # Add a remote AND reset feat to main → branch is at same SHA as main
  git remote add origin https://example.com/test.git
  git reset --hard main -q
  run stage_a_preflight
  [ "$status" -eq 4 ]
  [[ "$output" == *"ABORT: Branch has no commits ahead of main"* ]]
}

@test "Stage A happy path: feat branch, clean, remote, ahead of main" {
  git remote add origin https://example.com/test.git
  echo "b" > b
  git add b
  git commit -q -m "feat"
  run stage_a_preflight
  [ "$status" -eq 0 ]
  [[ "$output" == *"Pre-flight OK"* ]]
}

@test "Stage A: each abort message is distinct (no duplicates)" {
  # Run all 4 abort scenarios in isolation; the four output lines must be
  # mutually distinct so a user/test can disambiguate the failure cause.
  msgs=()

  git checkout main -q
  run stage_a_preflight
  msgs+=("$output")

  git checkout feat -q
  touch dirty
  run stage_a_preflight
  msgs+=("$output")
  rm -f dirty

  run stage_a_preflight
  msgs+=("$output")

  git remote add origin https://example.com/test.git
  git reset --hard main -q
  run stage_a_preflight
  msgs+=("$output")

  # Verify all 4 are distinct
  unique_count=$(printf '%s\n' "${msgs[@]}" | sort -u | wc -l)
  [ "$unique_count" -eq 4 ]
}
