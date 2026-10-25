#!/usr/bin/env bats
# aa-ma-impact-preedit.bats — claude-code/hooks/aa-ma-impact-preedit.sh (code-conventions-impact 10.6)
# against the real captured PreToolUse(Edit|Write) payloads (tests/fixtures/hook-payloads) and the
# forge's real codemem (.venv, from `uv sync`), over throwaway repos indexed once per file.
#
# repo:  b.py defines helper(); a.py calls it; lonely.py is called by nothing and changes alone.
# evil:  the same, but the index row for a.py is renamed to an injection string.
# bare:  a git repo with no codemem index.

bats_require_minimum_version 1.5.0

load ../lib/hook_payloads

setup_file() {
    FORGE="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)"
    CODEMEM="${FORGE}/.venv/bin/codemem"
    [ -x "$CODEMEM" ] || { echo "no ${CODEMEM} — run uv sync" >&2; return 1; }
    FILE_TMP="$(mktemp -d "${BATS_FILE_TMPDIR}/impact.XXXXXX")"
    FILE_TMP="$(cd "$FILE_TMP" && pwd -P)"
    export FILE_TMP
    export XDG_CACHE_HOME="${FILE_TMP}/cache" XDG_STATE_HOME="${FILE_TMP}/state"
    unset CODEMEM_DB CODEMEM_BIN
    local r
    for r in repo evil bare; do
        mkdir -p "${FILE_TMP}/${r}"
        git -C "${FILE_TMP}/${r}" init -q -b main
        printf 'def helper():\n    return 1\n' > "${FILE_TMP}/${r}/b.py"
        printf 'from b import helper\n\ndef main():\n    return helper()\n' > "${FILE_TMP}/${r}/a.py"
        git -C "${FILE_TMP}/${r}" add -A
        git -C "${FILE_TMP}/${r}" -c user.name=t -c user.email=t@t -c commit.gpgsign=false commit -q -m one
        printf 'def alone():\n    return 0\n' > "${FILE_TMP}/${r}/lonely.py"
        git -C "${FILE_TMP}/${r}" add -A
        git -C "${FILE_TMP}/${r}" -c user.name=t -c user.email=t@t -c commit.gpgsign=false commit -q -m two
    done
    for r in repo evil; do
        "$CODEMEM" build --repo-root "${FILE_TMP}/${r}" >/dev/null 2>&1   # why: setup noise; the asserts below fail if it did not build
        "$CODEMEM" refresh-commits --repo-root "${FILE_TMP}/${r}" >/dev/null 2>&1   # why: as above
    done
    local db
    db="$(bash -c '. "$1"; aa_ma_codemem_dir "$2"' _ "${FORGE}/claude-code/hooks/lib/aa-ma-parse.sh" "${FILE_TMP}/evil")/index.db"
    "${FORGE}/.venv/bin/python" -I - "$db" <<'PY'
import sqlite3, sys
c = sqlite3.connect(sys.argv[1])
n = c.execute("UPDATE files SET path = ? WHERE path = 'a.py'",
              ("x\n\x1b[2J$(touch pwned)‮y.py",)).rowcount
c.commit()
assert n == 1, n
PY
}

teardown_file() { [ -n "${FILE_TMP:-}" ] && rm -rf "$FILE_TMP"; }

setup() {
    FORGE="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)"
    HOOK="${FORGE}/claude-code/hooks/aa-ma-impact-preedit.sh"
    WORK="$(mktemp -d "${BATS_TMPDIR}/impact-t.XXXXXX")"
    WORK="$(cd "$WORK" && pwd -P)"
    export HOME="${WORK}/home"
    mkdir -p "$HOME"
    export CLAUDE_HOOK_LOG="${WORK}/hooks.log"
    unset CODEMEM_DB CODEMEM_BIN AA_MA_HOOKS_DISABLE
    SID="00000000-0000-4000-8000-000000000001"
    RT="${HOME}/.claude/runtime/impact-seen-${SID}"
}

teardown() { rm -rf "$WORK"; }

# hook <Edit|Write> <file_path> [session_id] — run the hook on that captured payload, edited.
hook() {
    payload "PreToolUse-$1" --arg f "$2" --arg s "${3:-$SID}" \
        '.tool_input.file_path = $f | .session_id = $s' > "${WORK}/p.json"
    run bash -c '"$1" < "$2"' _ "$HOOK" "${WORK}/p.json"
}

ctx() { jq -r '.hookSpecificOutput.additionalContext' <<<"$output"; }

NO_INDEX='codemem: no index for this repo — run `codemem build`'

@test "fixtures are real PreToolUse(Edit) and PreToolUse(Write) payloads" {
    run jq -r '[.hook_event_name, .tool_name, (.tool_input | keys | join(","))] | @tsv' "${HOOK_PAYLOADS}/PreToolUse-Edit.json"
    [ "$output" = $'PreToolUse\tEdit\tfile_path,new_string,old_string,replace_all' ]
    run jq -r '[.hook_event_name, .tool_name, (.tool_input | keys | join(","))] | @tsv' "${HOOK_PAYLOADS}/PreToolUse-Write.json"
    [ "$output" = $'PreToolUse\tWrite\tcontent,file_path' ]
}

@test "Edit of a file with callers → ≤5 lines of additionalContext, untrusted header, Skill pointer last" {
    hook Edit "${FILE_TMP}/repo/b.py"
    [ "$status" -eq 0 ]
    [ "$(jq -r '.hookSpecificOutput.hookEventName' <<<"$output")" = "PreToolUse" ]
    mapfile -t lines < <(ctx)
    (( ${#lines[@]} >= 3 && ${#lines[@]} <= 5 ))
    [ "${lines[0]}" = "codemem data (untrusted): impact of b.py" ]
    [[ "${lines[1]}" == "callers: 1 file + 0 plugin nodes + 0 test files; top: a.py" ]]
    [[ "${lines[-1]}" == *"Skill(impact-analysis)"* ]]
}

@test "Write payload works the same way" {
    hook Write "${FILE_TMP}/repo/b.py"
    [ "$status" -eq 0 ]
    [ "$(ctx | head -1)" = "codemem data (untrusted): impact of b.py" ]
}

@test "once per file per session: the second Edit of the same file is silent" {
    hook Edit "${FILE_TMP}/repo/b.py"
    [ -n "$output" ]
    hook Write "${FILE_TMP}/repo/b.py"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
    # a new session sees it again
    hook Edit "${FILE_TMP}/repo/b.py" "00000000-0000-4000-8000-000000000009"
    [ -n "$output" ]
}

@test "NotebookEdit (any other tool) → exit 0, empty stdout, no marker" {
    payload PreToolUse-Edit --arg f "${FILE_TMP}/repo/b.py" \
        '.tool_name = "NotebookEdit" | .tool_input.file_path = $f' > "${WORK}/p.json"
    run bash -c '"$1" < "$2"' _ "$HOOK" "${WORK}/p.json"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
    [ ! -e "${HOME}/.claude/runtime" ]
}

@test "a path outside the repo, or escaping it with ../, is ignored" {
    mkdir -p "${WORK}/outside"
    printf 'x = 1\n' > "${WORK}/outside/o.py"
    hook Edit "${WORK}/outside/o.py"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
    hook Edit "${FILE_TMP}/repo/../outside.py"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
    [ ! -e "$RT" ]
}

@test "0 callers and 0 co-changes → silent" {
    hook Edit "${FILE_TMP}/repo/lonely.py"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "no index → one systemMessage per session, never an in-repo .codemem/" {
    hook Edit "${FILE_TMP}/bare/b.py"
    [ "$status" -eq 0 ]
    [ "$(jq -r .systemMessage <<<"$output")" = "$NO_INDEX" ]
    hook Edit "${FILE_TMP}/bare/a.py"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
    [ ! -e "${FILE_TMP}/bare/.codemem" ]
}

@test "codemem absent (CODEMEM_BIN=/nonexistent) → the same one notice per session" {
    CODEMEM_BIN=/nonexistent hook Edit "${FILE_TMP}/repo/b.py"
    [ "$status" -eq 0 ]
    [ "$(jq -r .systemMessage <<<"$output")" = "$NO_INDEX" ]
    CODEMEM_BIN=/nonexistent hook Edit "${FILE_TMP}/repo/a.py"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "codemem that hangs → killed at 2 s, one timeout notice per session, never blocks" {
    printf '#!/usr/bin/env bash\nsleep 5\n' > "${WORK}/slow-codemem"
    chmod +x "${WORK}/slow-codemem"
    SECONDS=0
    CODEMEM_BIN="${WORK}/slow-codemem" hook Edit "${FILE_TMP}/repo/b.py"
    (( SECONDS < 5 ))
    [ "$status" -eq 0 ]
    [[ "$(jq -r .systemMessage <<<"$output")" == "codemem: impact lookup timed out"* ]]
    CODEMEM_BIN="${WORK}/slow-codemem" hook Edit "${FILE_TMP}/repo/a.py"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "an injected path in the index (newline, ESC, \$(…), bidi) reaches the model as one inert line" {
    hook Edit "${FILE_TMP}/evil/b.py"
    [ "$status" -eq 0 ]
    c="$(ctx)"
    [ "$(printf '%s\n' "$c" | wc -l)" -le 5 ]
    [[ "$c" == *'$(touch pwned)'* ]]
    [[ "$c" != *$'\e'* ]]
    [[ "$c" != *$'‮'* ]]
    run ! grep -q '^y.py' <<<"$c"   # the embedded newline did not start a line of its own
    [ ! -e "${FILE_TMP}/evil/pwned" ]
    [ ! -e "${WORK}/pwned" ]
}

@test "a file_path with spaces and \$(touch x) executes nothing" {
    hook Write "${FILE_TMP}/repo/new dir/\$(touch ${WORK}/x).py"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
    [ ! -e "${WORK}/x" ]
    [ ! -e "${FILE_TMP}/repo/x" ]
}

@test "concurrent invocations for one file print once" {
    # Four racers, not two: a non-atomic marker (uutils mkdir 0.10.0) lost 2-way races ~1 in 3.
    payload PreToolUse-Edit --arg f "${FILE_TMP}/repo/b.py" '.tool_input.file_path = $f' > "${WORK}/p.json"
    for i in 1 2 3 4; do "$HOOK" < "${WORK}/p.json" > "${WORK}/o${i}" & done
    wait
    [ "$(cat "${WORK}"/o[1-4] | grep -c hookSpecificOutput)" -eq 1 ]
}

@test "an invalid session_id → silent, no marker, one log line" {
    hook Edit "${FILE_TMP}/repo/b.py" "../../etc"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
    [ ! -e "${HOME}/.claude/runtime" ]
    [ "$(grep -c 'aa-ma-impact-preedit' "$CLAUDE_HOOK_LOG")" -eq 1 ]
}

@test "AA_MA_HOOKS_DISABLE=1 → silent, nothing written" {
    AA_MA_HOOKS_DISABLE=1 hook Edit "${FILE_TMP}/repo/b.py"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
    [ ! -e "${HOME}/.claude/runtime" ]
}

@test "garbage on stdin → exit 0, empty stdout" {
    run bash -c 'printf "not json" | "$1"' _ "$HOOK"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}
