#!/usr/bin/env bats
# ruff-format.bats — claude-code/hooks/ruff-format.sh against a real PostToolUse(Edit)
# payload. The fixture was captured 2026-10-09 from a headless `claude -p` Edit run
# (code-conventions-impact M2.4); only cwd/transcript_path/file paths were rewritten
# to /tmp/capture/…, and each test points tool_input.file_path at its own file.

setup() {
    REPO_ROOT="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)"
    HOOK="${REPO_ROOT}/claude-code/hooks/ruff-format.sh"
    PAYLOAD="${BATS_TEST_DIRNAME}/fixtures/ruff-format/posttooluse-edit.json"
    WORK="$(mktemp -d "${BATS_TMPDIR}/ruff-format.XXXXXX")"
    export HOME="${WORK}/home"   # the hook logs to $HOME/.claude/logs/hooks.log
    LOG="${HOME}/.claude/logs/hooks.log"
    # why: the locked ruff from `uv sync` (CI's bats job runs it), never whatever is on PATH.
    export PATH="${REPO_ROOT}/.venv/bin:${PATH}"
    [ "$(command -v ruff)" = "${REPO_ROOT}/.venv/bin/ruff" ] || {
        echo "ruff not found in ${REPO_ROOT}/.venv/bin — run uv sync" >&2; return 1; }
}

teardown() { rm -rf "$WORK"; }

# $1 = path the payload's tool_input.file_path should name
run_hook() {
    jq --arg f "$1" '.tool_input.file_path = $f' "$PAYLOAD" > "$WORK/payload.json"
    run bash "$HOOK" < "$WORK/payload.json"
}

@test "fixture is a real PostToolUse(Edit) payload" {
    run jq -r '[.hook_event_name, .tool_name, (.tool_input | has("file_path"))] | @tsv' "$PAYLOAD"
    [ "$output" = $'PostToolUse\tEdit\ttrue' ]
}

@test ".py is formatted in place and the hook exits 0" {
    printf 'x=1\nif x :\n  y=[1,2 ,3]\n' > "$WORK/sample.py"
    run_hook "$WORK/sample.py"
    [ "$status" -eq 0 ]
    [ "$(cat "$WORK/sample.py")" = $'x = 1\nif x:\n    y = [1, 2, 3]' ]
    [ ! -e "$LOG" ]
}

@test "non-.py file is a no-op" {
    printf 'x=1\n' > "$WORK/notes.txt"
    run_hook "$WORK/notes.txt"
    [ "$status" -eq 0 ]
    [ "$(cat "$WORK/notes.txt")" = "x=1" ]
    [ ! -e "$LOG" ]
}

@test "ruff failure writes exactly one hooks.log line and still exits 0" {
    printf 'def broken(:\n' > "$WORK/bad.py"
    run_hook "$WORK/bad.py"
    [ "$status" -eq 0 ]
    [ "$(wc -l < "$LOG")" -eq 1 ]
    grep -q "ERROR ruff-format: ${WORK}/bad.py:" "$LOG"
}

@test "AA_MA_HOOKS_DISABLE=1 → the hook touches nothing" {
    printf 'x=1\n' > "$WORK/sample.py"
    jq --arg f "$WORK/sample.py" '.tool_input.file_path = $f' "$PAYLOAD" > "$WORK/payload.json"
    run env AA_MA_HOOKS_DISABLE=1 bash "$HOOK" < "$WORK/payload.json"
    [ "$status" -eq 0 ]
    [ "$(cat "$WORK/sample.py")" = "x=1" ]
}

@test "CLAUDE_HOOK_LOG overrides the log path" {
    printf 'def broken(:\n' > "$WORK/bad.py"
    jq --arg f "$WORK/bad.py" '.tool_input.file_path = $f' "$PAYLOAD" > "$WORK/payload.json"
    run env CLAUDE_HOOK_LOG="$WORK/custom.log" bash "$HOOK" < "$WORK/payload.json"
    [ "$status" -eq 0 ]
    [ "$(wc -l < "$WORK/custom.log")" -eq 1 ]
    [ ! -e "$LOG" ]
}
