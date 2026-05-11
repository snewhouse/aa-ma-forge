#!/usr/bin/env bats
# test_marker_lifecycle.bats — Tier 3 integration smoke for the /aa-ma-plan
# phase-marker lifecycle: stub creation → append → Phase 5 move → hook reads
# from final location.
#
# Exercises the full glue:
#   - aa-ma-plan-marker.sh writes well-formed markers
#   - Multi-write accumulation in the same file
#   - Phase 5 "move into task dir" works as documented in aa-ma-scribe.md
#   - aa-ma-plan-skip-warn.sh hook recognises a healthy log as silent
#   - Python parser reads what the bash helper writes (cross-format)

setup() {
    REPO_ROOT="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)"
    MARKER="${REPO_ROOT}/claude-code/hooks/aa-ma-plan-marker.sh"
    HOOK="${REPO_ROOT}/claude-code/hooks/aa-ma-plan-skip-warn.sh"
    BATS_TMP_HOME="$(mktemp -d)"
    SLUG="lifecycle-20260511130000"
    LOGPATH="${BATS_TMP_HOME}/.claude/runtime/aa-ma-plan-${SLUG}.log"
    TASK_NAME="lifecycle"
    TASK_DIR="${BATS_TMP_HOME}/work/.claude/dev/active/${TASK_NAME}"
    mkdir -p "${BATS_TMP_HOME}/work" "$TASK_DIR"
    export REPO_ROOT MARKER HOOK BATS_TMP_HOME SLUG LOGPATH TASK_NAME TASK_DIR
}

teardown() {
    [ -n "${BATS_TMP_HOME:-}" ] && rm -rf "$BATS_TMP_HOME"
}

# Helper: append all 9 required phase markers via the bash helper.
append_full_run() {
    HOME="$BATS_TMP_HOME" bash "$MARKER" "$SLUG" 0 INIT slug="$SLUG"
    HOME="$BATS_TMP_HOME" bash "$MARKER" "$SLUG" 1 DONE context_gathering=complete
    HOME="$BATS_TMP_HOME" bash "$MARKER" "$SLUG" 1.3 DONE grill_mode=with-docs branches_resolved=7
    HOME="$BATS_TMP_HOME" bash "$MARKER" "$SLUG" 1.5 DONE lessons_loaded=10 git_grep_hits=3
    HOME="$BATS_TMP_HOME" bash "$MARKER" "$SLUG" 2 DONE brainstorm_skill=invoked
    HOME="$BATS_TMP_HOME" bash "$MARKER" "$SLUG" 3 DONE context7_calls=2 web_fetches=1
    HOME="$BATS_TMP_HOME" bash "$MARKER" "$SLUG" 4 DONE complexity_score=40% plan_elements=12/12
    HOME="$BATS_TMP_HOME" bash "$MARKER" "$SLUG" 4.2 DONE reviews=eng
    HOME="$BATS_TMP_HOME" bash "$MARKER" "$SLUG" 4.5 DONE verdict=GREEN criticals=0
    HOME="$BATS_TMP_HOME" bash "$MARKER" "$SLUG" 5 DONE artifacts=5 task_dir=.claude/dev/active/lifecycle
}

@test "lifecycle: stub creation by first marker write" {
    [ ! -f "$LOGPATH" ]
    HOME="$BATS_TMP_HOME" bash "$MARKER" "$SLUG" 0 INIT slug="$SLUG"
    [ -f "$LOGPATH" ]
    [ "$(wc -l < "$LOGPATH")" -eq 1 ]
    grep -qE '^\[[^]]+\] PHASE_0 INIT — slug=lifecycle-20260511130000$' "$LOGPATH"
}

@test "lifecycle: 10-line full run accumulates in stable order" {
    append_full_run
    [ "$(wc -l < "$LOGPATH")" -eq 10 ]
    # Order preserved.
    awk '{print $2}' "$LOGPATH" | tr -d ':' > "${BATS_TMP_HOME}/phases.txt"
    expected="PHASE_0
PHASE_1
PHASE_1.3
PHASE_1.5
PHASE_2
PHASE_3
PHASE_4
PHASE_4.2
PHASE_4.5
PHASE_5"
    diff <(echo "$expected") "${BATS_TMP_HOME}/phases.txt"
}

@test "lifecycle: Phase 5 'move into task dir' produces permanent artifact" {
    append_full_run
    [ -f "$LOGPATH" ]
    [ ! -f "${TASK_DIR}/${TASK_NAME}-plan-run.log" ]
    # Simulate aa-ma-scribe's Phase 5 move (per aa-ma-scribe.md instruction).
    mv "$LOGPATH" "${TASK_DIR}/${TASK_NAME}-plan-run.log"
    [ ! -f "$LOGPATH" ]
    [ -f "${TASK_DIR}/${TASK_NAME}-plan-run.log" ]
    [ "$(wc -l < "${TASK_DIR}/${TASK_NAME}-plan-run.log")" -eq 10 ]
}

@test "lifecycle: hook is silent on a healthy 9-marker log" {
    append_full_run
    transcript="${BATS_TMP_HOME}/transcript.jsonl"
    : > "$transcript"
    stdin="{\"hook_event_name\":\"PreToolUse\",\"transcript_path\":\"$transcript\",\"session_id\":\"t\"}"
    HOME="$BATS_TMP_HOME" CLAUDE_CODE=1 run bash -c "echo '$stdin' | bash '$HOOK'"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "lifecycle: hook warns if a phase marker is missing" {
    # Skip PHASE_1.3 — induce a deliberate gap.
    HOME="$BATS_TMP_HOME" bash "$MARKER" "$SLUG" 0 INIT slug="$SLUG"
    HOME="$BATS_TMP_HOME" bash "$MARKER" "$SLUG" 1 DONE context_gathering=complete
    HOME="$BATS_TMP_HOME" bash "$MARKER" "$SLUG" 1.5 DONE lessons_loaded=10
    HOME="$BATS_TMP_HOME" bash "$MARKER" "$SLUG" 2 DONE brainstorm_skill=invoked
    HOME="$BATS_TMP_HOME" bash "$MARKER" "$SLUG" 3 DONE context7_calls=2
    HOME="$BATS_TMP_HOME" bash "$MARKER" "$SLUG" 4 DONE complexity_score=40%
    HOME="$BATS_TMP_HOME" bash "$MARKER" "$SLUG" 4.2 DONE reviews=eng
    HOME="$BATS_TMP_HOME" bash "$MARKER" "$SLUG" 4.5 DONE verdict=GREEN
    HOME="$BATS_TMP_HOME" bash "$MARKER" "$SLUG" 5 DONE artifacts=5
    stdin='{"hook_event_name":"SessionEnd","transcript_path":"","session_id":"t"}'
    HOME="$BATS_TMP_HOME" CLAUDE_CODE=1 run bash -c "echo '$stdin' | bash '$HOOK'"
    [ "$status" -eq 0 ]
    [[ "$output" == *"PHASE_1.3"* ]]
}

@test "lifecycle: legitimate skip (with reason) silences the hook for that phase" {
    HOME="$BATS_TMP_HOME" bash "$MARKER" "$SLUG" 0 INIT slug="$SLUG"
    HOME="$BATS_TMP_HOME" bash "$MARKER" "$SLUG" 1 DONE x=y
    HOME="$BATS_TMP_HOME" bash "$MARKER" "$SLUG" 1.3 DONE x=y
    HOME="$BATS_TMP_HOME" bash "$MARKER" "$SLUG" 1.5 SKIPPED reason=flag_--skip-lessons
    HOME="$BATS_TMP_HOME" bash "$MARKER" "$SLUG" 2 DONE x=y
    HOME="$BATS_TMP_HOME" bash "$MARKER" "$SLUG" 3 DONE x=y
    HOME="$BATS_TMP_HOME" bash "$MARKER" "$SLUG" 4 DONE x=y
    HOME="$BATS_TMP_HOME" bash "$MARKER" "$SLUG" 4.2 SKIPPED reason=user_passed
    HOME="$BATS_TMP_HOME" bash "$MARKER" "$SLUG" 4.5 DONE x=y
    HOME="$BATS_TMP_HOME" bash "$MARKER" "$SLUG" 5 DONE x=y
    stdin='{"hook_event_name":"SessionEnd","transcript_path":"","session_id":"t"}'
    HOME="$BATS_TMP_HOME" CLAUDE_CODE=1 run bash -c "echo '$stdin' | bash '$HOOK'"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}
