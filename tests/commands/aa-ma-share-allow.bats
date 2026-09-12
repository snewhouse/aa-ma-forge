#!/usr/bin/env bats
# Allowlist for /aa-ma-share: only plan.md, docs/adr/*.md and docs/spec/*.md may be
# published. The command calls this script; prose in the command is not the check.

setup() {
  REPO_ROOT="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)"
  ALLOW="${REPO_ROOT}/scripts/aa-ma-share-allow.sh"
}

@test "allows docs/adr/*.md (relative)" {
  run "$ALLOW" "docs/adr/0010-x.md"; [ "$status" -eq 0 ]
}

@test "allows ./-prefixed docs/adr path" {
  run "$ALLOW" "./docs/adr/0010-x.md"; [ "$status" -eq 0 ]
}

@test "allows absolute docs/spec path" {
  run "$ALLOW" "/abs/repo/docs/spec/aa-ma-specification.md"; [ "$status" -eq 0 ]
}

@test "allows a task plan.md" {
  run "$ALLOW" ".claude/dev/active/t/t-plan.md"; [ "$status" -eq 0 ]
}

@test "refuses context-log.md" {
  run "$ALLOW" ".claude/dev/active/t/t-context-log.md"; [ "$status" -eq 1 ]; [[ "$output" == *refused* ]]
}

@test "refuses provenance.log" {
  run "$ALLOW" ".claude/dev/active/t/t-provenance.log"; [ "$status" -eq 1 ]
}

@test "refuses reference.md" {
  run "$ALLOW" ".claude/dev/active/t/t-reference.md"; [ "$status" -eq 1 ]
}

@test "refuses tasks.md" {
  run "$ALLOW" ".claude/dev/active/t/t-tasks.md"; [ "$status" -eq 1 ]
}

@test "refuses README.md" {
  run "$ALLOW" "README.md"; [ "$status" -eq 1 ]
}

@test "refuses an empty argument" {
  run "$ALLOW" ""; [ "$status" -eq 1 ]
}

@test "refuses a parent-escape that textually matches an allowed prefix" {
  run "$ALLOW" "docs/adr/../../.claude/dev/active/t/t-context-log.md"; [ "$status" -eq 1 ]
}
