#!/usr/bin/env bats
# ruff-format.bats — claude-code/hooks/ruff-format.sh against the real captured
# PostToolUse(Edit) payload (tests/fixtures/hook-payloads, M7.5); each test points
# tool_input.file_path at its own file.

setup() {
    REPO_ROOT="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)"
    HOOK="${REPO_ROOT}/claude-code/hooks/ruff-format.sh"
    PAYLOAD="${BATS_TEST_DIRNAME}/../fixtures/hook-payloads/PostToolUse-Edit.json"
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

# fake_forge — a copy of the hook in a forge layout with NO .venv, so ruff must come from PATH
# (or a stub put in $WORK/forge/.venv/bin). Prints the copied hook's path.
fake_forge() {
    local d="$WORK/forge"
    mkdir -p "$d/claude-code/hooks/lib" "$d/src/aa_ma"
    cp "$HOOK" "$d/claude-code/hooks/"
    cp "$REPO_ROOT/claude-code/hooks/lib/aa-ma-log.sh" "$d/claude-code/hooks/lib/"
    cp "$REPO_ROOT/src/aa_ma/secret_patterns.tsv" "$d/src/aa_ma/"
    echo "$d/claude-code/hooks/ruff-format.sh"
}

# no_ruff_path — a PATH dir holding only the tools the hook needs; ruff is not among them.
no_ruff_path() {
    local b="$WORK/sysbin" t
    mkdir -p "$b"
    for t in jq readlink dirname date mkdir head grep wc; do ln -sf "$(command -v "$t")" "$b/$t"; done
    echo "$b"
}

# hostile_repo — a git repo that commits its own .venv/bin/ruff, which writes $WORK/PWNED.
hostile_repo() {
    local r="$WORK/hostile"
    mkdir -p "$r/.venv/bin"
    # why: /bin/sh + a builtin redirect, so the stub runs on any PATH (a stub that cannot start proves nothing)
    printf '#!/bin/sh\n: > "%s/PWNED"\n' "$WORK" > "$r/.venv/bin/ruff"
    chmod +x "$r/.venv/bin/ruff"
    printf 'x=1\n' > "$r/mod.py"
    git -C "$r" init -q && git -C "$r" add -A && git -C "$r" -c user.name=t -c user.email=t@t commit -qm init
    echo "$r"
}

@test "ruff check --fix, then format, then check for the report; the forge .venv ruff wins over PATH" {
    hook=$(fake_forge)
    mkdir -p "$WORK/forge/.venv/bin" "$WORK/bin"
    printf '#!/usr/bin/env bash\necho "$1" >> "%s/calls"\n' "$WORK" > "$WORK/forge/.venv/bin/ruff"
    printf '#!/usr/bin/env bash\necho PATH-ruff >> "%s/calls"\n' "$WORK" > "$WORK/bin/ruff"
    chmod +x "$WORK/forge/.venv/bin/ruff" "$WORK/bin/ruff"
    printf 'x=1\n' > "$WORK/sample.py"
    jq --arg f "$WORK/sample.py" '.tool_input.file_path = $f' "$PAYLOAD" > "$WORK/payload.json"
    run env PATH="$WORK/bin:$PATH" bash "$hook" < "$WORK/payload.json"
    [ "$status" -eq 0 ]
    [ "$(paste -sd, "$WORK/calls")" = "check,format,check" ]
}

@test "remaining findings reach the model as PostToolUse additionalContext JSON" {
    printf 'import os\n' > "$WORK/unused.py"
    run_hook "$WORK/unused.py"
    [ "$status" -eq 0 ]
    printf '%s' "$output" | jq empty
    [ "$(printf '%s' "$output" | jq -c '[paths | select(length <= 2)]')" = '[["hookSpecificOutput"],["hookSpecificOutput","hookEventName"],["hookSpecificOutput","additionalContext"]]' ]
    [ "$(printf '%s' "$output" | jq -r '.hookSpecificOutput.hookEventName')" = "PostToolUse" ]
    printf '%s' "$output" | jq -r '.hookSpecificOutput.additionalContext' | grep -q 'F401'
}

@test "a clean file prints nothing" {
    printf '"""Doc."""\n\nX = 1\n' > "$WORK/clean.py"
    run_hook "$WORK/clean.py"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "additionalContext is capped at 10 lines, the last naming how many more" {
    for i in $(seq 1 15); do printf 'import m%s\n' "$i"; done > "$WORK/many.py"
    run_hook "$WORK/many.py"
    [ "$status" -eq 0 ]
    ctx=$(printf '%s' "$output" | jq -r '.hookSpecificOutput.additionalContext')
    [ "$(printf '%s\n' "$ctx" | wc -l)" -eq 10 ]
    [[ "$(printf '%s\n' "$ctx" | tail -n 1)" =~ ^…\ and\ [0-9]+\ more ]]
}

@test "a hostile repo's committed .venv/bin/ruff is never run (forge ruff present)" {
    r=$(hostile_repo)
    jq --arg f "$r/mod.py" --arg c "$r" '.tool_input.file_path = $f | .cwd = $c' "$PAYLOAD" > "$WORK/payload.json"
    cd "$r"
    run bash "$HOOK" < "$WORK/payload.json"
    [ "$status" -eq 0 ]
    [ ! -e "$WORK/PWNED" ]
}

@test "a hostile repo's .venv/bin/ruff is never run, even with no forge ruff and .venv/bin on PATH" {
    r=$(hostile_repo)
    hook=$(fake_forge)
    sysbin=$(no_ruff_path)
    jq --arg f "$r/mod.py" --arg c "$r" '.tool_input.file_path = $f | .cwd = $c' "$PAYLOAD" > "$WORK/payload.json"
    cd "$r"
    run env PATH=".venv/bin:$sysbin" "$BASH" "$hook" < "$WORK/payload.json"
    [ "$status" -eq 0 ]
    [ ! -e "$WORK/PWNED" ]
    printf '%s' "$output" | jq -e '.systemMessage | test("ruff")' >/dev/null
}

@test "ruff missing → exactly one systemMessage per session_id" {
    hook=$(fake_forge)
    sysbin=$(no_ruff_path)
    printf 'x=1\n' > "$WORK/s.py"
    jq --arg f "$WORK/s.py" '.tool_input.file_path = $f | .session_id = "sess-A"' "$PAYLOAD" > "$WORK/a.json"
    jq --arg f "$WORK/s.py" '.tool_input.file_path = $f | .session_id = "sess-B"' "$PAYLOAD" > "$WORK/b.json"
    out1=$(env PATH="$sysbin" "$BASH" "$hook" < "$WORK/a.json")
    out2=$(env PATH="$sysbin" "$BASH" "$hook" < "$WORK/a.json")
    out3=$(env PATH="$sysbin" "$BASH" "$hook" < "$WORK/b.json")
    [ "$(printf '%s' "$out1" | jq -r '.systemMessage')" != "null" ]
    [ -z "$out2" ]
    [ "$(printf '%s' "$out3" | jq -r '.systemMessage')" != "null" ]
    [ "$(grep -c 'WARN ruff-format: ruff not found' "$LOG")" -eq 2 ]
}

@test "jq missing on a .py edit → a systemMessage and a hooks.log line, never silence (M7 §6.6)" {
    local b="$WORK/nojq" t
    mkdir -p "$b"
    for t in readlink date mkdir head grep wc; do ln -sf "$(command -v "$t")" "$b/$t"; done
    printf 'x=1\n' > "$WORK/s.py"
    jq --arg f "$WORK/s.py" '.tool_input.file_path = $f' "$PAYLOAD" > "$WORK/p.json"
    run env PATH="$b" "$BASH" "$HOOK" < "$WORK/p.json"
    [ "$status" -eq 0 ]
    [[ "$output" == *'"systemMessage"'* ]]
    grep -qF 'WARN ruff-format: jq not on PATH' "$LOG"
}

@test "a non-.py edit exits before any fork: no ruff, no jq, no library (M7 §6.6)" {
    local b="$WORK/empty"
    mkdir -p "$b"
    jq --arg f "$WORK/notes.txt" '.tool_input.file_path = $f' "$PAYLOAD" > "$WORK/p.json"
    run env PATH="$b" "$BASH" "$HOOK" < "$WORK/p.json"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
    [ ! -e "$LOG" ]
}
