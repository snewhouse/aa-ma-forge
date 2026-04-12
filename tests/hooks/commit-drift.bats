#!/usr/bin/env bats
# commit-drift.bats — tests for claude-code/hooks/aa-ma-commit-drift.sh
#
# Hook contract (PostToolUse matcher=Bash):
#   - Inspects last commit via `git log -1 --name-only HEAD`
#   - Warns (stderr) when committed-file count > AA_MA_DRIFT_THRESHOLD (default 1)
#     AND no active task's tasks.md/provenance.log is among those files
#   - [no-sync-check] on its own line in commit message suppresses the warning
#   - Kill switch respected
#   - Always exits 0 (advisory)
#   - Silent when no active plans, initial-commit case, below-threshold commits

setup() {
    HOOK="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)/claude-code/hooks/aa-ma-commit-drift.sh"
    FIXTURE="${BATS_TEST_DIRNAME}/fixtures/build_active_dir.sh"
    BATS_TMP="$(mktemp -d)"
    BATS_TMP_HOME="$(mktemp -d)"
    export BATS_TMP BATS_TMP_HOME
}

teardown() {
    [ -n "${BATS_TMP:-}" ] && rm -rf "$BATS_TMP"
    [ -n "${BATS_TMP_HOME:-}" ] && rm -rf "$BATS_TMP_HOME"
}

# Builds: .claude/dev/active/task-N/ layouts + initial git commit of everything.
# After return, caller should modify files to create drift scenarios and commit.
setup_repo_with_tasks() {
    local count="$1"
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" "$count" plain
    (
        cd "$BATS_TMP"
        git init -q
        git -c user.email=t@e.i -c user.name=t -c commit.gpgsign=false add -A
        git -c user.email=t@e.i -c user.name=t -c commit.gpgsign=false \
            commit -q -m "fixture: initial"
    )
}

# Helper: make a commit touching N random files outside .claude/ with a message.
commit_files() {
    local count="$1" msg="$2"
    (
        cd "$BATS_TMP"
        for i in $(seq 1 "$count"); do
            printf 'line\n' >> "src-$i.txt"
        done
        git -c user.email=t@e.i -c user.name=t -c commit.gpgsign=false add -A
        git -c user.email=t@e.i -c user.name=t -c commit.gpgsign=false \
            commit -q -m "$msg"
    )
}

# Helper: build a PostToolUse-shape stdin JSON.
make_input() {
    jq -cn --arg cmd "$1" '{tool_name:"Bash",tool_input:{command:$cmd},tool_response:{}}'
}

run_hook() {
    local cmd="$1"
    local input
    input=$(make_input "$cmd")
    HOME="$BATS_TMP_HOME" run bash -c "printf '%s' \"\$1\" | bash \"$HOOK\"" _ "$input"
}

@test "tasks.md touched in commit → silent" {
    setup_repo_with_tasks 1
    (
        cd "$BATS_TMP"
        printf '\nnew\n' >> .claude/dev/active/task-1/task-1-tasks.md
        printf 'code\n' >> src.txt
        git -c user.email=t@e.i -c user.name=t -c commit.gpgsign=false add -A
        git -c user.email=t@e.i -c user.name=t -c commit.gpgsign=false \
            commit -q -m "feat: update tasks + code"
    )
    cd "$BATS_TMP"
    run_hook 'git commit -m "feat: update tasks + code"'
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "tasks.md not touched (above threshold) → warn naming top active task" {
    setup_repo_with_tasks 1
    commit_files 2 "feat: code only"
    cd "$BATS_TMP"
    run_hook 'git commit -m "feat: code only"'
    [ "$status" -eq 0 ]
    [[ "$output" == *"task-1"* ]]
    [[ "$output" == *"drift"* || "$output" == *"tasks.md"* ]]
}

@test "[no-sync-check] marker on own line → silent" {
    setup_repo_with_tasks 1
    (
        cd "$BATS_TMP"
        printf 'code\n' > src.txt
        printf 'code\n' > src2.txt
        git -c user.email=t@e.i -c user.name=t -c commit.gpgsign=false add -A
        git -c user.email=t@e.i -c user.name=t -c commit.gpgsign=false \
            commit -q -m "chore: unrelated

[no-sync-check]"
    )
    cd "$BATS_TMP"
    run_hook 'git commit -m "chore: unrelated

[no-sync-check]"'
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "no active tasks → silent" {
    # Git repo exists but no .claude/dev/active/ content
    (
        cd "$BATS_TMP"
        git init -q
        printf 'code\n' > src.txt
        git -c user.email=t@e.i -c user.name=t -c commit.gpgsign=false add -A
        git -c user.email=t@e.i -c user.name=t -c commit.gpgsign=false \
            commit -q -m "initial"
        printf 'more\n' >> src.txt
        git -c user.email=t@e.i -c user.name=t -c commit.gpgsign=false add -A
        git -c user.email=t@e.i -c user.name=t -c commit.gpgsign=false \
            commit -q -m "feat: code"
    )
    cd "$BATS_TMP"
    run_hook 'git commit -m "feat: code"'
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "kill switch (AA_MA_HOOKS_DISABLE=1) → silent even when drift would trigger" {
    setup_repo_with_tasks 1
    commit_files 2 "feat: code"
    cd "$BATS_TMP"
    AA_MA_HOOKS_DISABLE=1 HOME="$BATS_TMP_HOME" run bash -c "printf '%s' \"\$1\" | bash \"$HOOK\"" _ "$(make_input 'git commit -m "feat: code"')"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "below-threshold commit (AA_MA_DRIFT_THRESHOLD high) → silent" {
    setup_repo_with_tasks 1
    commit_files 2 "feat: only 2 files"
    cd "$BATS_TMP"
    AA_MA_DRIFT_THRESHOLD=10 HOME="$BATS_TMP_HOME" run bash -c "printf '%s' \"\$1\" | bash \"$HOOK\"" _ "$(make_input 'git commit -m "feat: only 2 files"')"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "multiple active tasks, none touched → warn naming each" {
    setup_repo_with_tasks 2
    commit_files 2 "feat: unrelated"
    cd "$BATS_TMP"
    run_hook 'git commit -m "feat: unrelated"'
    [ "$status" -eq 0 ]
    [[ "$output" == *"task-1"* ]]
    [[ "$output" == *"task-2"* ]]
}

@test "provenance.log touched (instead of tasks.md) → silent (either satisfies)" {
    setup_repo_with_tasks 1
    (
        cd "$BATS_TMP"
        printf 'log\n' >> .claude/dev/active/task-1/task-1-provenance.log
        printf 'code\n' >> src.txt
        git -c user.email=t@e.i -c user.name=t -c commit.gpgsign=false add -A
        git -c user.email=t@e.i -c user.name=t -c commit.gpgsign=false \
            commit -q -m "feat: code + provenance"
    )
    cd "$BATS_TMP"
    run_hook 'git commit -m "feat: code + provenance"'
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}
