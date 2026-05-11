#!/usr/bin/env bats
# aa-ma-plan-skip-warn.bats — tests for claude-code/hooks/aa-ma-plan-skip-warn.sh
#
# Hook is advisory: always exit 0. Warnings go to stderr. Operates by:
#   1. Reading stdin JSON from Claude Code (transcript_path, hook_event_name).
#   2. Finding newest ~/.claude/runtime/aa-ma-plan-*.log under $HOME.
#   3. Parsing markers and correlating against transcript tool_use entries.
#   4. Emitting warnings to stderr for missing/unbacked phase markers.

setup() {
    REPO_ROOT="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)"
    HOOK="${REPO_ROOT}/claude-code/hooks/aa-ma-plan-skip-warn.sh"
    BATS_TMP_HOME="$(mktemp -d)"
    RUNTIME_DIR="${BATS_TMP_HOME}/.claude/runtime"
    mkdir -p "$RUNTIME_DIR"
    export BATS_TMP_HOME RUNTIME_DIR REPO_ROOT
}

teardown() {
    [ -n "${BATS_TMP_HOME:-}" ] && rm -rf "$BATS_TMP_HOME"
}

# Write a runtime log containing all 9 required markers (happy-path content).
write_full_log() {
    local logfile="${RUNTIME_DIR}/aa-ma-plan-happy-20260511130000.log"
    cat > "$logfile" <<'EOF'
[2026-05-11T13:00:00+01:00] PHASE_0 INIT — slug=happy
[2026-05-11T13:01:00+01:00] PHASE_1 DONE — context_gathering=complete
[2026-05-11T13:02:00+01:00] PHASE_1.3 DONE — grill_mode=with-docs branches_resolved=5 questions_asked=7
[2026-05-11T13:03:00+01:00] PHASE_1.5 DONE — lessons_loaded=10 git_grep_hits=3
[2026-05-11T13:04:00+01:00] PHASE_2 DONE — brainstorm_skill=invoked alternatives_considered=2
[2026-05-11T13:05:00+01:00] PHASE_3 DONE — context7_calls=2 web_fetches=1
[2026-05-11T13:06:00+01:00] PHASE_4 DONE — complexity_score=40% plan_elements=12/12
[2026-05-11T13:07:00+01:00] PHASE_4.2 DONE — reviews=eng
[2026-05-11T13:08:00+01:00] PHASE_4.5 DONE — verdict=GREEN criticals=0 warnings=0
[2026-05-11T13:09:00+01:00] PHASE_5 DONE — artifacts=5 task_dir=/tmp/x
EOF
    echo "$logfile"
}

# Write a transcript JSONL that backs all 9 fingerprints.
write_full_transcript() {
    local tpath="${BATS_TMP_HOME}/transcript.jsonl"
    {
        echo '{"type":"tool_use","name":"Agent","input":{"subagent_type":"Explore","prompt":"x"}}'
        echo '{"type":"tool_use","name":"AskUserQuestion","input":{}}'
        echo '{"type":"tool_use","name":"AskUserQuestion","input":{}}'
        echo '{"type":"tool_use","name":"AskUserQuestion","input":{}}'
        echo '{"type":"tool_use","name":"Read","input":{"file_path":"docs/lessons.md"}}'
        echo '{"type":"tool_use","name":"Skill","input":{"skill":"superpowers:brainstorming"}}'
        echo '{"type":"tool_use","name":"WebFetch","input":{"url":"https://example.com"}}'
        echo '{"type":"tool_use","name":"Skill","input":{"skill":"complexity-router"}}'
        echo '{"type":"tool_use","name":"Skill","input":{"skill":"plan-eng-review"}}'
        echo '{"type":"tool_use","name":"Skill","input":{"skill":"plan-verification"}}'
        echo '{"type":"tool_use","name":"Agent","input":{"subagent_type":"aa-ma-scribe","prompt":"x"}}'
        echo '{"type":"tool_use","name":"Agent","input":{"subagent_type":"aa-ma-validator","prompt":"x"}}'
    } > "$tpath"
    echo "$tpath"
}

# Synthesize the stdin JSON the hook expects from Claude Code.
build_stdin() {
    local transcript_path="$1"
    local event="${2:-PreToolUse}"
    printf '{"hook_event_name":"%s","transcript_path":"%s","session_id":"test"}' \
        "$event" "$transcript_path"
}

@test "happy path: all 9 markers present + full transcript → silent exit 0" {
    write_full_log >/dev/null
    tpath="$(write_full_transcript)"
    stdin="$(build_stdin "$tpath")"
    HOME="$BATS_TMP_HOME" CLAUDE_CODE=1 run bash -c "echo '$stdin' | bash '$HOOK'"
    [ "$status" -eq 0 ]
    # Hook is advisory and silent when fingerprints match.
    [ -z "$output" ]
}

@test "missing PHASE_1.3 marker → stderr warning, exit 0" {
    # Build log WITHOUT PHASE_1.3
    logfile="${RUNTIME_DIR}/aa-ma-plan-missing-20260511130000.log"
    cat > "$logfile" <<'EOF'
[2026-05-11T13:00:00+01:00] PHASE_0 INIT — slug=missing
[2026-05-11T13:01:00+01:00] PHASE_1 DONE — context_gathering=complete
[2026-05-11T13:03:00+01:00] PHASE_1.5 DONE — lessons_loaded=10
[2026-05-11T13:04:00+01:00] PHASE_2 DONE — brainstorm_skill=invoked
[2026-05-11T13:05:00+01:00] PHASE_3 DONE — context7_calls=2
[2026-05-11T13:06:00+01:00] PHASE_4 DONE — complexity_score=40%
[2026-05-11T13:07:00+01:00] PHASE_4.2 DONE — reviews=eng
[2026-05-11T13:08:00+01:00] PHASE_4.5 DONE — verdict=GREEN criticals=0
[2026-05-11T13:09:00+01:00] PHASE_5 DONE — artifacts=5 task_dir=/tmp/x
EOF
    tpath="$(write_full_transcript)"
    stdin="$(build_stdin "$tpath")"
    HOME="$BATS_TMP_HOME" CLAUDE_CODE=1 run bash -c "echo '$stdin' | bash '$HOOK'"
    [ "$status" -eq 0 ]
    [[ "$output" == *"PHASE_1.3"* ]]
}

@test "SKIPPED with reason → silent (skip is its own evidence)" {
    logfile="${RUNTIME_DIR}/aa-ma-plan-skipped-20260511130000.log"
    cat > "$logfile" <<'EOF'
[2026-05-11T13:00:00+01:00] PHASE_0 INIT — slug=skipped
[2026-05-11T13:01:00+01:00] PHASE_1 DONE — context_gathering=complete
[2026-05-11T13:02:00+01:00] PHASE_1.3 DONE — grill_mode=skip
[2026-05-11T13:03:00+01:00] PHASE_1.5 SKIPPED — reason=flag_--skip-lessons
[2026-05-11T13:04:00+01:00] PHASE_2 DONE — brainstorm_skill=invoked
[2026-05-11T13:05:00+01:00] PHASE_3 DONE — context7_calls=0
[2026-05-11T13:06:00+01:00] PHASE_4 DONE — complexity_score=40%
[2026-05-11T13:07:00+01:00] PHASE_4.2 SKIPPED — reason=user_passed
[2026-05-11T13:08:00+01:00] PHASE_4.5 DONE — verdict=GREEN
[2026-05-11T13:09:00+01:00] PHASE_5 DONE — artifacts=5 task_dir=/tmp/x
EOF
    tpath="$(write_full_transcript)"
    stdin="$(build_stdin "$tpath")"
    HOME="$BATS_TMP_HOME" CLAUDE_CODE=1 run bash -c "echo '$stdin' | bash '$HOOK'"
    [ "$status" -eq 0 ]
    # Skips with reasons must not warn.
    ! [[ "$output" == *"PHASE_1.5"* ]]
    ! [[ "$output" == *"PHASE_4.2"* ]]
}

@test "SKIPPED without reason → stderr warning, exit 0" {
    logfile="${RUNTIME_DIR}/aa-ma-plan-badskip-20260511130000.log"
    cat > "$logfile" <<'EOF'
[2026-05-11T13:00:00+01:00] PHASE_0 INIT — slug=badskip
[2026-05-11T13:01:00+01:00] PHASE_1 DONE — context_gathering=complete
[2026-05-11T13:02:00+01:00] PHASE_1.3 DONE — grill_mode=skip
[2026-05-11T13:03:00+01:00] PHASE_1.5 DONE — lessons_loaded=0
[2026-05-11T13:04:00+01:00] PHASE_2 DONE — brainstorm_skill=invoked
[2026-05-11T13:05:00+01:00] PHASE_3 DONE — context7_calls=0
[2026-05-11T13:06:00+01:00] PHASE_4 DONE — complexity_score=40%
[2026-05-11T13:07:00+01:00] PHASE_4.2 DONE — reviews=
[2026-05-11T13:08:00+01:00] PHASE_4.5 SKIPPED — note=oops
[2026-05-11T13:09:00+01:00] PHASE_5 DONE — artifacts=5 task_dir=/tmp/x
EOF
    tpath="$(write_full_transcript)"
    stdin="$(build_stdin "$tpath")"
    HOME="$BATS_TMP_HOME" CLAUDE_CODE=1 run bash -c "echo '$stdin' | bash '$HOOK'"
    [ "$status" -eq 0 ]
    [[ "$output" == *"PHASE_4.5"* ]]
    [[ "$output" == *"reason"* ]]
}

@test "kill switch AA_MA_HOOKS_DISABLE=1 → silent exit 0 even when markers missing" {
    logfile="${RUNTIME_DIR}/aa-ma-plan-killed-20260511130000.log"
    echo "[2026-05-11T13:00:00+01:00] PHASE_0 INIT — slug=killed" > "$logfile"
    tpath="${BATS_TMP_HOME}/empty.jsonl"
    : > "$tpath"
    stdin="$(build_stdin "$tpath")"
    HOME="$BATS_TMP_HOME" CLAUDE_CODE=1 AA_MA_HOOKS_DISABLE=1 \
        run bash -c "echo '$stdin' | bash '$HOOK'"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "no runtime log present → silent exit 0 (not in a plan)" {
    # Empty runtime dir; no aa-ma-plan-*.log files.
    tpath="${BATS_TMP_HOME}/empty.jsonl"
    : > "$tpath"
    stdin="$(build_stdin "$tpath")"
    HOME="$BATS_TMP_HOME" CLAUDE_CODE=1 \
        run bash -c "echo '$stdin' | bash '$HOOK'"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "malformed stdin JSON → silent exit 0 (defensive, never block)" {
    write_full_log >/dev/null
    HOME="$BATS_TMP_HOME" CLAUDE_CODE=1 \
        run bash -c "echo 'not json' | bash '$HOOK'"
    [ "$status" -eq 0 ]
    # Hook may emit debug to stderr but must not crash.
}
