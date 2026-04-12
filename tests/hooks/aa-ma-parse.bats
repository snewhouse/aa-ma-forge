#!/usr/bin/env bats
# aa-ma-parse.bats — tests for claude-code/hooks/lib/aa-ma-parse.sh

setup() {
    REPO_ROOT="$(cd "${BATS_TEST_DIRNAME}/.." && pwd)"
    HELPER="$REPO_ROOT/../claude-code/hooks/lib/aa-ma-parse.sh"
    if [ ! -f "$HELPER" ]; then
        # Fallback when tests/ is inside repo root (expected layout)
        HELPER="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)/claude-code/hooks/lib/aa-ma-parse.sh"
    fi
    FIXTURE="${BATS_TEST_DIRNAME}/fixtures/build_active_dir.sh"
    BATS_TMP="$(mktemp -d)"
    BATS_TMP_HOME="$(mktemp -d)"
    export BATS_TMP BATS_TMP_HOME
}

teardown() {
    [ -n "${BATS_TMP:-}" ] && rm -rf "$BATS_TMP"
    [ -n "${BATS_TMP_HOME:-}" ] && rm -rf "$BATS_TMP_HOME"
    unset AA_MA_HOOKS_DISABLE HOOK_DEBUG AA_MA_PARSE_SH_LOADED 2>/dev/null || true
}

load_helper() {
    # shellcheck disable=SC1090
    . "$HELPER"
}

@test "aa_ma_is_disabled returns non-zero when env unset" {
    load_helper
    unset AA_MA_HOOKS_DISABLE
    run aa_ma_is_disabled
    [ "$status" -ne 0 ]
}

@test "aa_ma_is_disabled returns 0 when AA_MA_HOOKS_DISABLE=1" {
    load_helper
    AA_MA_HOOKS_DISABLE=1
    run aa_ma_is_disabled
    [ "$status" -eq 0 ]
}

@test "aa_ma_is_disabled treats AA_MA_HOOKS_DISABLE=0 as not-disabled" {
    load_helper
    AA_MA_HOOKS_DISABLE=0
    run aa_ma_is_disabled
    [ "$status" -ne 0 ]
}

@test "aa_ma_debug silent when HOOK_DEBUG unset" {
    load_helper
    unset HOOK_DEBUG
    run aa_ma_debug "should not appear"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "aa_ma_debug emits [aa-ma-debug] prefix when HOOK_DEBUG=1" {
    load_helper
    HOOK_DEBUG=1
    run aa_ma_debug "hello"
    [ "$status" -eq 0 ]
    [[ "$output" == *"[aa-ma-debug] hello"* ]]
}

@test "aa_ma_extract_active_milestone finds bold-format Status: ACTIVE" {
    "$FIXTURE" "$BATS_TMP" 1 bold
    load_helper
    result=$(aa_ma_extract_active_milestone "$BATS_TMP/task-1/task-1-tasks.md")
    [ "$result" = "Milestone 1: Foundation" ]
}

@test "aa_ma_extract_active_milestone finds plain-format Status: ACTIVE" {
    "$FIXTURE" "$BATS_TMP" 1 plain
    load_helper
    result=$(aa_ma_extract_active_milestone "$BATS_TMP/task-1/task-1-tasks.md")
    [ "$result" = "Milestone 1: Foundation" ]
}

@test "aa_ma_extract_active_milestone handles mixed format in multi-task fixture" {
    "$FIXTURE" "$BATS_TMP" 2 mixed
    load_helper
    bold_result=$(aa_ma_extract_active_milestone "$BATS_TMP/task-1/task-1-tasks.md")
    plain_result=$(aa_ma_extract_active_milestone "$BATS_TMP/task-2/task-2-tasks.md")
    [ "$bold_result" = "Milestone 1: Foundation" ]
    [ "$plain_result" = "Milestone 1: Foundation" ]
}

@test "aa_ma_extract_active_milestone returns empty for empty file" {
    empty_file="$BATS_TMP/empty.md"
    : > "$empty_file"
    load_helper
    result=$(aa_ma_extract_active_milestone "$empty_file")
    [ -z "$result" ]
}

@test "aa_ma_extract_active_step finds first PENDING step via fallback" {
    "$FIXTURE" "$BATS_TMP" 1 plain
    load_helper
    # Fixture has milestone ACTIVE but step PENDING → PENDING fallback
    result=$(aa_ma_extract_active_step "$BATS_TMP/task-1/task-1-tasks.md")
    [ "$result" = "Step 1.1: Initial step" ]
}

@test "HTML-comment false-positive guard: commented Status: ACTIVE ignored" {
    cat > "$BATS_TMP/html.md" <<'EOF'
## Milestone 1: Guard Test
<!-- Status: ACTIVE -->
- Status: PENDING
EOF
    load_helper
    # Should detect PENDING (fallback), NOT ACTIVE from the HTML comment
    result=$(aa_ma_extract_active_milestone "$BATS_TMP/html.md")
    [ "$result" = "Milestone 1: Guard Test" ]
}

@test "aa_ma_list_active_tasks sorts by mtime (newest first)" {
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 3 plain "-200,-100,0"
    load_helper
    cd "$BATS_TMP"
    mapfile -t tasks < <(aa_ma_list_active_tasks)
    [ "${#tasks[@]}" -eq 3 ]
    # task-3 has offset 0 (newest), task-1 has offset -200 (oldest)
    [[ "${tasks[0]}" == *"/task-3" ]]
    [[ "${tasks[1]}" == *"/task-2" ]]
    [[ "${tasks[2]}" == *"/task-1" ]]
}

@test "aa_ma_list_active_tasks applies project-first collision rule" {
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 1 plain
    "$FIXTURE" "$BATS_TMP_HOME/.claude/dev/active" 1 plain
    load_helper
    cd "$BATS_TMP"
    HOME="$BATS_TMP_HOME"
    export HOME
    mapfile -t tasks < <(aa_ma_list_active_tasks)
    [ "${#tasks[@]}" -eq 1 ]
    [[ "${tasks[0]}" == "$BATS_TMP"* ]]
    ! [[ "${tasks[0]}" == "$BATS_TMP_HOME"* ]]
}

@test "aa_ma_list_active_tasks merges non-colliding tasks from both paths" {
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 1 plain
    # Create a differently-named task in fake HOME
    fake_home_active="$BATS_TMP_HOME/.claude/dev/active/home-only-task"
    mkdir -p "$fake_home_active"
    touch "$fake_home_active/home-only-task-tasks.md"

    load_helper
    cd "$BATS_TMP"
    HOME="$BATS_TMP_HOME"
    export HOME
    mapfile -t tasks < <(aa_ma_list_active_tasks)
    [ "${#tasks[@]}" -eq 2 ]
}

@test "aa_ma_list_active_tasks emits nothing when no task dirs exist" {
    load_helper
    cd "$BATS_TMP"
    HOME="$BATS_TMP_HOME"
    export HOME
    run aa_ma_list_active_tasks
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "aa_ma_list_active_tasks uses alphabetical tiebreak when mtimes equal" {
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 3 plain "0,0,0"
    load_helper
    cd "$BATS_TMP"
    mapfile -t tasks < <(aa_ma_list_active_tasks)
    [ "${#tasks[@]}" -eq 3 ]
    # All mtimes equal → alphabetical ascending (task-1, task-2, task-3)
    [[ "${tasks[0]}" == *"/task-1" ]]
    [[ "${tasks[1]}" == *"/task-2" ]]
    [[ "${tasks[2]}" == *"/task-3" ]]
}
