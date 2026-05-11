#!/usr/bin/env bats
# aa-ma-plan-marker.bats — tests for claude-code/hooks/aa-ma-plan-marker.sh

setup() {
    REPO_ROOT="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)"
    HELPER="${REPO_ROOT}/claude-code/hooks/aa-ma-plan-marker.sh"
    BATS_TMP_HOME="$(mktemp -d)"
    export BATS_TMP_HOME
}

teardown() {
    [ -n "${BATS_TMP_HOME:-}" ] && rm -rf "$BATS_TMP_HOME"
}

@test "writes INIT marker with slug to runtime log" {
    HOME="$BATS_TMP_HOME" run bash "$HELPER" myslug-20260511 0 INIT slug=myslug-20260511
    [ "$status" -eq 0 ]
    logfile="${BATS_TMP_HOME}/.claude/runtime/aa-ma-plan-myslug-20260511.log"
    [ -f "$logfile" ]
    grep -qE '^\[[^]]+\] PHASE_0 INIT — slug=myslug-20260511$' "$logfile"
}

@test "writes DONE marker with multiple key=value payloads" {
    HOME="$BATS_TMP_HOME" run bash "$HELPER" t 1.3 DONE grill_mode=with-docs branches_resolved=7 questions_asked=12
    [ "$status" -eq 0 ]
    grep -qE 'PHASE_1.3 DONE — grill_mode=with-docs branches_resolved=7 questions_asked=12' \
        "${BATS_TMP_HOME}/.claude/runtime/aa-ma-plan-t.log"
}

@test "writes SKIPPED with reason → silent (no warning)" {
    HOME="$BATS_TMP_HOME" run bash "$HELPER" t 4.5 SKIPPED reason=user_choice
    [ "$status" -eq 0 ]
    [ -z "${output:-}" ] || ! [[ "$output" == *"WARNING"* ]]
    grep -qE 'PHASE_4.5 SKIPPED — reason=user_choice' \
        "${BATS_TMP_HOME}/.claude/runtime/aa-ma-plan-t.log"
}

@test "SKIPPED without reason → warns to stderr but still appends" {
    HOME="$BATS_TMP_HOME" run bash "$HELPER" t 4.5 SKIPPED note=oops
    [ "$status" -eq 0 ]
    [[ "$output" == *"WARNING"* ]]
    [[ "$output" == *"reason"* ]]
    grep -qE 'PHASE_4.5 SKIPPED — note=oops' \
        "${BATS_TMP_HOME}/.claude/runtime/aa-ma-plan-t.log"
}

@test "INIT on non-PHASE_0 → warns but still appends" {
    HOME="$BATS_TMP_HOME" run bash "$HELPER" t 1 INIT slug=t
    [ "$status" -eq 0 ]
    [[ "$output" == *"WARNING"* ]]
}

@test "invalid status → exit 2" {
    HOME="$BATS_TMP_HOME" run bash "$HELPER" t 1 MAYBE
    [ "$status" -eq 2 ]
    [[ "$output" == *"invalid status"* ]]
}

@test "invalid slug (uppercase) → exit 2" {
    HOME="$BATS_TMP_HOME" run bash "$HELPER" BadSlug 1 DONE
    [ "$status" -eq 2 ]
    [[ "$output" == *"invalid slug"* ]]
}

@test "missing args → exit 2 with usage" {
    HOME="$BATS_TMP_HOME" run bash "$HELPER" only-slug
    [ "$status" -eq 2 ]
    [[ "$output" == *"usage"* ]]
}

@test "key=value with space in value → exit 2" {
    HOME="$BATS_TMP_HOME" run bash "$HELPER" t 1 DONE 'bad_key=value with space'
    [ "$status" -eq 2 ]
    [[ "$output" == *"invalid key=value"* ]]
}

@test "multiple marker writes accumulate in same log" {
    HOME="$BATS_TMP_HOME" bash "$HELPER" t 0 INIT slug=t
    HOME="$BATS_TMP_HOME" bash "$HELPER" t 1 DONE context_gathering=complete
    HOME="$BATS_TMP_HOME" bash "$HELPER" t 5 DONE artifacts=5
    logfile="${BATS_TMP_HOME}/.claude/runtime/aa-ma-plan-t.log"
    [ "$(wc -l < "$logfile")" -eq 3 ]
}
