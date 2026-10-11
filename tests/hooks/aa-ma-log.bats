#!/usr/bin/env bats
# aa-ma-log.bats — tests for claude-code/hooks/lib/aa-ma-log.sh (M7.1).
# Contract: one line per call, `<date -Is> LEVEL <hook-name>: <msg>`, appended to
# ${CLAUDE_HOOK_LOG:-~/.claude/logs/hooks.log}; secrets masked; CR/LF stripped;
# fail_open_notice puts a jq-built {"systemMessage"} on stdout (L-1319).

bats_require_minimum_version 1.5.0

setup() {
    ROOT="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)"
    LIB="$ROOT/claude-code/hooks/lib/aa-ma-log.sh"
    WORK="$(mktemp -d)"
    export CLAUDE_HOOK_LOG="$WORK/logs/hooks.log"
    unset HOOK_DEBUG
    # why: token-shaped strings are assembled at runtime so no literal secret is committed
    AWS="AKIA""ABCDEFGHIJKLMNOP"
    GHP="ghp_""$(printf 'a%.0s' {1..36})"
    ANT="sk-ant-api03-""$(printf 'B%.0s' {1..40})"
}

teardown() {
    rm -rf "$WORK"
}

ts_re='^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}[+-][0-9]{2}:[0-9]{2}'

@test "log_info appends one formatted line and prints nothing" {
    . "$LIB"
    run --separate-stderr log_info my-hook "hello world"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
    [ -z "$stderr" ]
    [ "$(wc -l < "$CLAUDE_HOOK_LOG")" -eq 1 ]
    line=$(cat "$CLAUDE_HOOK_LOG")
    [[ "$line" =~ $ts_re' INFO my-hook: hello world$' ]]
}

@test "log_warn and log_error use WARN and ERROR" {
    . "$LIB"
    log_warn h "w"
    log_error h "e"
    [[ "$(sed -n 1p "$CLAUDE_HOOK_LOG")" =~ ' WARN h: w'$ ]]
    [[ "$(sed -n 2p "$CLAUDE_HOOK_LOG")" =~ ' ERROR h: e'$ ]]
}

@test "log_debug is silent without HOOK_DEBUG=1" {
    . "$LIB"
    run --separate-stderr log_debug h "quiet"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
    [ -z "$stderr" ]
    [ ! -s "$CLAUDE_HOOK_LOG" ]
}

@test "log_debug with HOOK_DEBUG=1 writes the log line and the same line to stderr, not stdout" {
    . "$LIB"
    export HOOK_DEBUG=1
    run --separate-stderr log_debug h "loud"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
    [[ "$stderr" =~ $ts_re' DEBUG h: loud$' ]]
    [[ "$(cat "$CLAUDE_HOOK_LOG")" =~ ' DEBUG h: loud'$ ]]
}

@test "CR and LF in the message and hook name never split the log line" {
    . "$LIB"
    log_info $'ho\nok' $'a\nb\rc'
    [ "$(wc -l < "$CLAUDE_HOOK_LOG")" -eq 1 ]
    grep -q ' INFO ho ok: a b c$' "$CLAUDE_HOOK_LOG"
}

@test "log_* masks secrets with the gitleaks rule id" {
    . "$LIB"
    log_warn h "aws=$AWS gh=$GHP key=$ANT"
    ! grep -qF "$AWS" "$CLAUDE_HOOK_LOG"
    ! grep -qF "$GHP" "$CLAUDE_HOOK_LOG"
    ! grep -qF "$ANT" "$CLAUDE_HOOK_LOG"
    grep -qF 'aws=[REDACTED:aws-access-token]' "$CLAUDE_HOOK_LOG"
    grep -qF 'gh=[REDACTED:github-pat]' "$CLAUDE_HOOK_LOG"
    grep -qF 'key=[REDACTED:anthropic-api-key]' "$CLAUDE_HOOK_LOG"
}

@test "near-miss strings are left alone" {
    . "$LIB"
    run mask_secrets "AKIA1234 ghp_short sk-ant-tiny xoxb- eyJhbGci"
    [ "$status" -eq 0 ]
    [ "$output" = "AKIA1234 ghp_short sk-ant-tiny xoxb- eyJhbGci" ]
}

@test "mask_secrets prints the masked text on stdout" {
    . "$LIB"
    run mask_secrets "token $GHP end"
    [ "$status" -eq 0 ]
    [ "$output" = "token [REDACTED:github-pat] end" ]
}

@test "messages are capped at 8 KB before matching" {
    . "$LIB"
    big=$(head -c 20000 /dev/zero | tr '\0' 'x')
    log_info h "$big"
    msg=$(sed 's/^[^ ]* INFO h: //' "$CLAUDE_HOOK_LOG")
    [ "${#msg}" -le 8192 ]
}

@test "missing pattern file fails closed: the message is replaced, never logged unmasked" {
    mkdir -p "$WORK/forge/claude-code/hooks/lib"
    cp "$LIB" "$WORK/forge/claude-code/hooks/lib/"
    . "$WORK/forge/claude-code/hooks/lib/aa-ma-log.sh"
    log_warn h "secret $GHP"
    ! grep -qF "$GHP" "$CLAUDE_HOOK_LOG"
    grep -qF ' WARN h: [redaction failed]' "$CLAUDE_HOOK_LOG"
}

@test "an unwritable log path returns 0 and says so on stderr" {
    . "$LIB"
    export CLAUDE_HOOK_LOG=/proc/aa-ma-no-such/hooks.log
    run --separate-stderr log_error h "lost"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
    [[ "$stderr" == *"aa-ma-log: cannot append to /proc/aa-ma-no-such/hooks.log"* ]]
}

@test "fail_open_notice prints a systemMessage JSON object and logs a WARN line" {
    . "$LIB"
    run --separate-stderr fail_open_notice ruff-format "ruff not on PATH"
    [ "$status" -eq 0 ]
    printf '%s' "$output" | jq empty
    [ "$(printf '%s' "$output" | jq -r '.systemMessage')" = "ruff-format: ruff not on PATH" ]
    grep -q ' WARN ruff-format: ruff not on PATH$' "$CLAUDE_HOOK_LOG"
}

@test "fail_open_notice: injected quotes cannot add JSON keys" {
    . "$LIB"
    run fail_open_notice h 'x", "decision": "block", "y": "'
    [ "$status" -eq 0 ]
    printf '%s' "$output" | jq empty
    [ "$(printf '%s' "$output" | jq -c '[paths]')" = '[["systemMessage"]]' ]
}

@test "fail_open_notice masks secrets in the systemMessage" {
    . "$LIB"
    run fail_open_notice h "leaked $AWS"
    [ "$(printf '%s' "$output" | jq -r '.systemMessage')" = "h: leaked [REDACTED:aws-access-token]" ]
}

@test "aa-ma-parse.sh sources aa-ma-log.sh; aa_ma_debug routes through log_debug" {
    . "$ROOT/claude-code/hooks/lib/aa-ma-parse.sh"
    type log_info >/dev/null
    export HOOK_DEBUG=1
    run --separate-stderr aa_ma_debug "via parse"
    [ "$status" -eq 0 ]
    [[ "$stderr" =~ ' DEBUG '.+': via parse'$ ]]
    grep -q ': via parse$' "$CLAUDE_HOOK_LOG"
}

@test "aa-ma-parse.sh finds aa-ma-log.sh through a symlink (installed layout)" {
    mkdir -p "$WORK/home/hooks/lib"
    ln -s "$ROOT/claude-code/hooks/lib/aa-ma-parse.sh" "$WORK/home/hooks/lib/aa-ma-parse.sh"
    run bash -c '. "$1"; type log_warn >/dev/null && echo ok' _ "$WORK/home/hooks/lib/aa-ma-parse.sh"
    [ "$status" -eq 0 ]
    [ "$output" = "ok" ]
}
