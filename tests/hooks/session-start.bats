#!/usr/bin/env bats
# session-start.bats — tests for claude-code/hooks/aa-ma-session-start.sh
#
# Validates the post-M2 behavior:
#   - mtime-top selection (not alphabetical)
#   - Resolved path emission (not hardcoded relative)
#   - Trailing-slash $HOME normalization
#   - Multi-task footer "(N other active tasks: a, b, c and M more)"
#   - Empty state (no active tasks)
#   - Single-task emission
#
# Against the pre-M2 hook these MUST be RED. Against the patched hook they MUST be GREEN.

setup() {
    HOOK="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)/claude-code/hooks/aa-ma-session-start.sh"
    FIXTURE="${BATS_TEST_DIRNAME}/fixtures/build_active_dir.sh"
    BATS_TMP="$(mktemp -d)"
    BATS_TMP_HOME="$(mktemp -d)"
    export BATS_TMP BATS_TMP_HOME
}

teardown() {
    [ -n "${BATS_TMP:-}" ] && rm -rf "$BATS_TMP"
    [ -n "${BATS_TMP_HOME:-}" ] && rm -rf "$BATS_TMP_HOME"
}

@test "empty state: no active tasks → hook emits nothing and exits 0" {
    cd "$BATS_TMP"
    HOME="$BATS_TMP_HOME" run bash "$HOOK"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "single-task: emits task name and resolved path" {
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 1 plain
    cd "$BATS_TMP"
    HOME="$BATS_TMP_HOME" run bash "$HOOK"
    [ "$status" -eq 0 ]
    [[ "$output" == *"task=[task-1]"* ]]
    # Path emitted must be the actual resolved project-local path (absolute), not the hardcoded bare `.claude/dev/active/`.
    [[ "$output" == *"$BATS_TMP/.claude/dev/active/task-1"* ]]
}

@test "mtime-top: newest task surfaced first (discriminates vs alphabetical)" {
    # INVERTED offsets so alphabetical-last != mtime-newest:
    # task-1 is NEWEST (offset 0), task-3 is OLDEST (offset -200).
    # Buggy hook picks task-3 (alphabetical last); correct hook picks task-1.
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 3 plain "0,-100,-200"
    cd "$BATS_TMP"
    HOME="$BATS_TMP_HOME" run bash "$HOOK"
    [ "$status" -eq 0 ]
    [[ "$output" == *"task=[task-1]"* ]]
    ! [[ "$output" == *"task=[task-3]"* ]]
}

@test "multi-task footer: 4 active tasks → top + (3 other active tasks: ...)" {
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 4 plain "-300,-200,-100,0"
    cd "$BATS_TMP"
    HOME="$BATS_TMP_HOME" run bash "$HOOK"
    [ "$status" -eq 0 ]
    # Top should be task-4 (newest). Footer must mention 3 other tasks and include each name.
    [[ "$output" == *"task=[task-4]"* ]]
    [[ "$output" == *"(3 other active tasks:"* ]]
    [[ "$output" == *"task-3"* ]]
    [[ "$output" == *"task-2"* ]]
    [[ "$output" == *"task-1"* ]]
}

@test "multi-task footer truncation: 6 tasks → top + 3 names + 'and 2 more'" {
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 6 plain "-500,-400,-300,-200,-100,0"
    cd "$BATS_TMP"
    HOME="$BATS_TMP_HOME" run bash "$HOOK"
    [ "$status" -eq 0 ]
    # Top task-6 (newest); footer lists next 3 names then "and 2 more"
    [[ "$output" == *"task=[task-6]"* ]]
    [[ "$output" == *"(5 other active tasks:"* ]]
    [[ "$output" == *"and 2 more"* ]]
}

@test "trailing-slash \$HOME normalization: no double-slash in emitted path" {
    "$FIXTURE" "$BATS_TMP_HOME/.claude/dev/active" 1 plain
    cd "$BATS_TMP"
    HOME="${BATS_TMP_HOME}/" run bash "$HOOK"
    [ "$status" -eq 0 ]
    # No "//" should appear in the emitted path.
    ! [[ "$output" == *"//"* ]]
}

@test "home-fallback: task lives only in \$HOME, hook emits its HOME path" {
    "$FIXTURE" "$BATS_TMP_HOME/.claude/dev/active" 1 plain
    cd "$BATS_TMP"
    HOME="$BATS_TMP_HOME" run bash "$HOOK"
    [ "$status" -eq 0 ]
    [[ "$output" == *"$BATS_TMP_HOME/.claude/dev/active/task-1"* ]]
}
