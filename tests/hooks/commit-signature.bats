#!/usr/bin/env bats
# commit-signature.bats — tests for claude-code/hooks/aa-ma-commit-signature.sh
#
# Hook contract (PreToolUse matcher=Bash):
#   stdin  : {"tool_name":"Bash","tool_input":{"command":"...git commit..."}}
#   exit 0 : pass (kill-switch, no active plan, sig present, [ad-hoc] marker, editor-open)
#   exit 2 : block with stderr naming the active task + signature template
#   exit 1 : hook infra error (jq parse failure)
#
# Against an absent hook these MUST be RED. Against the patched hook they MUST be GREEN.

setup() {
    HOOK="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)/claude-code/hooks/aa-ma-commit-signature.sh"
    FIXTURE="${BATS_TEST_DIRNAME}/fixtures/build_active_dir.sh"
    BATS_TMP="$(mktemp -d)"
    BATS_TMP_HOME="$(mktemp -d)"
    export BATS_TMP BATS_TMP_HOME
}

teardown() {
    [ -n "${BATS_TMP:-}" ] && rm -rf "$BATS_TMP"
    [ -n "${BATS_TMP_HOME:-}" ] && rm -rf "$BATS_TMP_HOME"
}

# Build a PreToolUse stdin JSON for a given bash command string.
# Uses jq to handle quoting correctly.
make_input() {
    jq -cn --arg cmd "$1" '{tool_name:"Bash",tool_input:{command:$cmd}}'
}

@test "no active plan → exit 0 (pass-through)" {
    cd "$BATS_TMP"
    input=$(make_input 'git commit -m "feat: x"')
    HOME="$BATS_TMP_HOME" run bash -c "printf '%s' \"\$1\" | bash \"$HOOK\"" _ "$input"
    [ "$status" -eq 0 ]
}

@test "signature present for active task → exit 0" {
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 1 plain
    cd "$BATS_TMP"
    input=$(make_input 'git commit -m "feat: x\n\n[AA-MA Plan] task-1 .claude/dev/active/task-1"')
    HOME="$BATS_TMP_HOME" run bash -c "printf '%s' \"\$1\" | bash \"$HOOK\"" _ "$input"
    [ "$status" -eq 0 ]
}

@test "[ad-hoc] marker on own line → exit 0" {
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 1 plain
    cd "$BATS_TMP"
    input=$(make_input "git commit -m \"feat: fix typo

[ad-hoc]\"")
    HOME="$BATS_TMP_HOME" run bash -c "printf '%s' \"\$1\" | bash \"$HOOK\"" _ "$input"
    [ "$status" -eq 0 ]
}

@test "missing signature AND missing [ad-hoc] → exit 2 with helpful stderr" {
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 1 plain
    cd "$BATS_TMP"
    input=$(make_input 'git commit -m "feat: unrelated"')
    HOME="$BATS_TMP_HOME" run bash -c "printf '%s' \"\$1\" | bash \"$HOOK\"" _ "$input"
    [ "$status" -eq 2 ]
    [[ "$output" == *"task-1"* ]]
    [[ "$output" == *"[AA-MA Plan]"* ]]
    [[ "$output" == *"AA_MA_HOOKS_DISABLE=1"* ]]
}

@test "kill switch (AA_MA_HOOKS_DISABLE=1) → exit 0 regardless" {
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 1 plain
    cd "$BATS_TMP"
    input=$(make_input 'git commit -m "unsigned"')
    HOME="$BATS_TMP_HOME" AA_MA_HOOKS_DISABLE=1 run bash -c "printf '%s' \"\$1\" | bash \"$HOOK\"" _ "$input"
    [ "$status" -eq 0 ]
}

@test "HEREDOC form with signature in body → exit 0 (substring match)" {
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 1 plain
    cd "$BATS_TMP"
    # HEREDOC body is visible in tool_input.command since Claude Code passes the literal invocation.
    cmd='git commit -m "$(cat <<'"'"'EOF'"'"'
feat: x

[AA-MA Plan] task-1 .claude/dev/active/task-1
EOF
)"'
    input=$(make_input "$cmd")
    HOME="$BATS_TMP_HOME" run bash -c "printf '%s' \"\$1\" | bash \"$HOOK\"" _ "$input"
    [ "$status" -eq 0 ]
}

@test "editor-open form (bare 'git commit' or --amend) → exit 0 (pass-through)" {
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 1 plain
    cd "$BATS_TMP"
    input=$(make_input 'git commit')
    HOME="$BATS_TMP_HOME" run bash -c "printf '%s' \"\$1\" | bash \"$HOOK\"" _ "$input"
    [ "$status" -eq 0 ]
    input=$(make_input 'git commit --amend')
    HOME="$BATS_TMP_HOME" run bash -c "printf '%s' \"\$1\" | bash \"$HOOK\"" _ "$input"
    [ "$status" -eq 0 ]
}

@test "unknown task name in signature → exit 2 (reject)" {
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 1 plain
    cd "$BATS_TMP"
    input=$(make_input 'git commit -m "feat: x

[AA-MA Plan] bogus-task .claude/dev/active/bogus-task"')
    HOME="$BATS_TMP_HOME" run bash -c "printf '%s' \"\$1\" | bash \"$HOOK\"" _ "$input"
    [ "$status" -eq 2 ]
}

@test "non-commit bash command → exit 0 (not our concern)" {
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 1 plain
    cd "$BATS_TMP"
    input=$(make_input 'ls -la')
    HOME="$BATS_TMP_HOME" run bash -c "printf '%s' \"\$1\" | bash \"$HOOK\"" _ "$input"
    [ "$status" -eq 0 ]
}

@test "word-boundary: 'git commit-tree' does not trigger the hook" {
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 1 plain
    cd "$BATS_TMP"
    # git commit-tree is a plumbing command, distinct from 'git commit'.
    input=$(make_input 'git commit-tree HEAD^{tree} -m "x"')
    HOME="$BATS_TMP_HOME" run bash -c "printf '%s' \"\$1\" | bash \"$HOOK\"" _ "$input"
    [ "$status" -eq 0 ]
}
