#!/usr/bin/env bats
# aa-ma-deps.bats — the `Dependencies:` advisory (diagram-generation M7, map Ticket 16).
#
# The advisory must NEVER block. These tests execute the §5.1 fence as shipped in
# execute-aa-ma-milestone.md (running the text, not grepping it) and the
# `aa_ma_deps` launcher, including with uv missing from PATH.

bats_require_minimum_version 1.5.0

setup() {
    REPO_ROOT="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)"
    HELPER="${REPO_ROOT}/claude-code/hooks/lib/aa-ma-parse.sh"
    MILESTONE_CMD="${REPO_ROOT}/claude-code/commands/execute-aa-ma-milestone.md"
    FIXTURE="${REPO_ROOT}/tests/fixtures/deps-hazards.md"
    WORK="$(mktemp -d "${BATS_TMPDIR}/deps.XXXXXX")"
    CLAUDE_HOME="$WORK/claude-home"
    mkdir -p "$CLAUDE_HOME/hooks/lib" && ln -s "$HELPER" "$CLAUDE_HOME/hooks/lib/aa-ma-parse.sh"
    mkdir -p "$WORK/t/.claude/dev/active/t"
    cp "$FIXTURE" "$WORK/t/.claude/dev/active/t/t-tasks.md"
    export REPO_ROOT HELPER MILESTONE_CMD WORK CLAUDE_HOME
}

teardown() {
    rm -rf "$WORK"
}

_advisory_fence() {
    awk '/^### 5\.1 /{f=1} f && /^```bash$/{g=1; next} g && /^```$/{exit} g' "$MILESTONE_CMD"
}

@test "aa_ma_deps runs python -m aa_ma.deps from the plugin checkout" {
    # shellcheck disable=SC1090
    . "$HELPER"
    cd "$WORK"
    run aa_ma_deps advisory "$WORK/t/.claude/dev/active/t/t-tasks.md"
    [ "$status" -eq 0 ]
    [ "$output" = "Milestone 3 is ACTIVE but Milestone 2 (Dependencies) is PENDING" ]
    run aa_ma_deps check "$WORK/t/.claude/dev/active/t/t-tasks.md"
    [ "$status" -eq 0 ]
}

@test "the shipped §5.1 advisory fence prints the warning and exits 0" {
    _advisory_fence > "$WORK/fence.sh"
    [ -s "$WORK/fence.sh" ]
    run bash -c "cd '$WORK/t' && TASK_NAME=t bash '$WORK/fence.sh'"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Milestone 3 is ACTIVE but Milestone 2 (Dependencies) is PENDING"* ]]
}

@test "the advisory fence never blocks, even with uv missing" {
    _advisory_fence > "$WORK/fence.sh"
    run bash -c "cd '$WORK/t' && PATH=/usr/bin:/bin TASK_NAME=t bash '$WORK/fence.sh'"
    [ "$status" -eq 0 ]
    [[ "$output" == *"advisory unavailable"* ]]
}

@test "the shipped /aa-ma-plan Step 5.5 fence prints the Milestone graph and checks it" {
    PLAN_CMD="${REPO_ROOT}/claude-code/commands/aa-ma-plan.md"
    awk '/^Write `Dependencies:` in the canonical form only/{f=1} f && /^```bash$/{g=1; next} g && /^```$/{exit} g' \
        "$PLAN_CMD" > "$WORK/plan-fence.sh"
    [ -s "$WORK/plan-fence.sh" ]
    run bash -c "cd '$WORK/t' && TASK_DIR=.claude/dev/active/t TASK_NAME=t bash '$WORK/plan-fence.sh'"
    [ "$status" -eq 0 ]
    [[ "$output" == *"### Milestone graph"* ]]
    [[ "$output" == *"  M2a --> M3"* ]]
    sed -i 's/Dependencies: Step M2a.1/Dependencies: Milestone 9/' "$WORK/t/.claude/dev/active/t/t-tasks.md"
    run bash -c "cd '$WORK/t' && TASK_DIR=.claude/dev/active/t TASK_NAME=t bash '$WORK/plan-fence.sh'"
    [ "$status" -eq 1 ]
    [[ "$output" == *"UNRESOLVED_DEPENDENCY Sub-step M3.1: Milestone 9"* ]]
}
