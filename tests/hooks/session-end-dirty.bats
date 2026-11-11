#!/usr/bin/env bats
# session-end-dirty.bats — tests for claude-code/hooks/aa-ma-session-end-dirty.sh

load ../lib/hook_payloads

setup() {
    HOOK="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)/claude-code/hooks/aa-ma-session-end-dirty.sh"
    FIXTURE="${BATS_TEST_DIRNAME}/fixtures/build_active_dir.sh"
    BATS_TMP="$(mktemp -d)"
    BATS_TMP_HOME="$(mktemp -d)"
    export BATS_TMP BATS_TMP_HOME
}

teardown() {
    [ -n "${BATS_TMP:-}" ] && rm -rf "$BATS_TMP"
    [ -n "${BATS_TMP_HOME:-}" ] && rm -rf "$BATS_TMP_HOME"
}

# Helper: create an active-task layout INSIDE a git repo rooted at $BATS_TMP,
# with the task dirs committed. Subsequent modifications show as `M` in
# git status --porcelain under the real path .claude/dev/active/<task>/.
setup_committed_tasks() {
    local count="$1"
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" "$count" plain
    (
        cd "$BATS_TMP"
        git init -q
        git -c user.email=test@example.invalid \
            -c user.name=test \
            -c commit.gpgsign=false \
            add -A
        git -c user.email=test@example.invalid \
            -c user.name=test \
            -c commit.gpgsign=false \
            commit -q -m "fixture: initial"
    )
}

@test "no active tasks → silent exit 0" {
    cd "$BATS_TMP"
    HOME="$BATS_TMP_HOME" CLAUDE_CODE=1 run bash "$HOOK"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "clean working tree → silent exit 0" {
    setup_committed_tasks 1
    cd "$BATS_TMP"
    HOME="$BATS_TMP_HOME" CLAUDE_CODE=1 run bash "$HOOK"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "dirty AA-MA artifact → one stderr warning naming the file" {
    setup_committed_tasks 1
    printf '\ndirty change\n' >> "$BATS_TMP/.claude/dev/active/task-1/task-1-tasks.md"
    cd "$BATS_TMP"
    HOME="$BATS_TMP_HOME" CLAUDE_CODE=1 run bash "$HOOK"
    [ "$status" -eq 0 ]
    [[ "$output" == *"task-1-tasks.md"* ]]
    [[ "$output" == *"task-1"* ]]
    [[ "$output" == *"dirty"* || "$output" == *"Commit or stash"* ]]
}

@test "kill switch (AA_MA_HOOKS_DISABLE=1) → silent exit 0 even when dirty" {
    setup_committed_tasks 1
    printf '\ndirty\n' >> "$BATS_TMP/.claude/dev/active/task-1/task-1-tasks.md"
    cd "$BATS_TMP"
    HOME="$BATS_TMP_HOME" CLAUDE_CODE=1 AA_MA_HOOKS_DISABLE=1 run bash "$HOOK"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "CI context (CLAUDE_CODE unset) → silent exit 0 even when dirty" {
    setup_committed_tasks 1
    printf '\ndirty\n' >> "$BATS_TMP/.claude/dev/active/task-1/task-1-tasks.md"
    cd "$BATS_TMP"
    HOME="$BATS_TMP_HOME" run env -u CLAUDE_CODE bash "$HOOK"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "HOOK_DEBUG=1 → verbose trace lines per task (even when clean)" {
    setup_committed_tasks 2
    cd "$BATS_TMP"
    HOME="$BATS_TMP_HOME" CLAUDE_CODE=1 HOOK_DEBUG=1 run bash "$HOOK"
    [ "$status" -eq 0 ]
    [[ "$output" == *" DEBUG aa-ma-session-end-dirty.sh: "* ]]
}

@test "task dir not in a git repo → skipped silently (no crash)" {
    # Create task dir without git init
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 1 plain
    cd "$BATS_TMP"
    HOME="$BATS_TMP_HOME" CLAUDE_CODE=1 run bash "$HOOK"
    [ "$status" -eq 0 ]
    # No "dirty" warning; may or may not have debug output.
    [[ "$output" != *"⚠️"* ]]
}

@test "a real captured SessionEnd payload on stdin: dirty artifact still warned (M7.5)" {
    setup_committed_tasks 1
    printf '\ndirty change\n' >> "$BATS_TMP/.claude/dev/active/task-1/task-1-tasks.md"
    cd "$BATS_TMP"
    HOME="$BATS_TMP_HOME" CLAUDE_CODE=1 run bash -c 'bash "$1" < "$2"' _ "$HOOK" "$HOOK_PAYLOADS/SessionEnd.json"
    [ "$status" -eq 0 ]
    [[ "$output" == *"task-1-tasks.md"* ]]
}

@test "impact-preedit markers (10.6): this session's dir removed, others and an invalid sid untouched" {
    cd "$BATS_TMP"
    rt="$BATS_TMP_HOME/.claude/runtime"
    sid="$(jq -r .session_id "$HOOK_PAYLOADS/SessionEnd.json")"
    mkdir -p "$rt/impact-seen-${sid}/abc" "$rt/impact-seen-other-session" "$rt/keep"
    HOME="$BATS_TMP_HOME" run bash -c 'bash "$1" < "$2"' _ "$HOOK" "$HOOK_PAYLOADS/SessionEnd.json"
    [ "$status" -eq 0 ]
    [ ! -e "$rt/impact-seen-${sid}" ]
    [ -d "$rt/impact-seen-other-session" ]
    [ -d "$rt/keep" ]
    # an invalid session_id never reaches rm
    # "impact-seen-../../victim" would resolve to $rt/victim
    mkdir -p "$rt/impact-seen-.." "$rt/victim"
    jq '.session_id = "../../victim"' "$HOOK_PAYLOADS/SessionEnd.json" > "$BATS_TMP/p.json"
    HOME="$BATS_TMP_HOME" run bash -c 'bash "$1" < "$2"' _ "$HOOK" "$BATS_TMP/p.json"
    [ "$status" -eq 0 ]
    [ -d "$rt/victim" ]
    [ -d "$rt/keep" ]
}
