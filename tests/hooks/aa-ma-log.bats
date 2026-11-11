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
    [[ "$line" =~ $ts_re' INFO my-hook: hello world'$ ]]
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
    [[ "$stderr" =~ $ts_re' DEBUG h: loud'$ ]]
    [[ "$(cat "$CLAUDE_HOOK_LOG")" =~ ' DEBUG h: loud'$ ]]
}

@test "CR and LF in the message and hook name never split the log line" {
    . "$LIB"
    log_info $'ho\nok' $'a\nb\rc'
    [ "$(wc -l < "$CLAUDE_HOOK_LOG")" -eq 1 ]
    grep -q ' INFO ho ok: a b c$' "$CLAUDE_HOOK_LOG"
}

@test "terminal control characters (ESC, BEL) reach neither the log nor the systemMessage (§6.8 M5 W7)" {
    # A repo-controlled name such as $'t\e]0;OWNED\a' would otherwise retitle the
    # terminal, or write the clipboard (OSC 52), when the notice is shown.
    . "$LIB"
    run --separate-stderr fail_open_notice $'h\e[31m' $'t\e]0;OWNED\a is active'
    [ "$status" -eq 0 ]
    msg=$(printf '%s' "$output" | jq -r '.systemMessage')
    # why: `if`, not a bare `!` — bats ignores a negated command's status (test_bats_assertions)
    if printf '%s' "$msg" | LC_ALL=C grep -q '[[:cntrl:]]'; then echo "control char in: $msg"; return 1; fi
    if LC_ALL=C grep -q $'[\x01-\x08\x0b-\x1f\x7f]' "$CLAUDE_HOOK_LOG"; then echo "control char in log"; return 1; fi
    [[ "$msg" == *"OWNED"*"is active"* ]]
}

@test "C1 control characters (U+009B CSI) reach neither the log nor the systemMessage in any locale; é is kept" {
    # [[:cntrl:]] matches U+009B in some UTF-8 locales but not in C or C.UTF-8 (live run 1, Stage D).
    local loc
    for loc in C C.UTF-8; do
        rm -f "$CLAUDE_HOOK_LOG"
        run --separate-stderr env LC_ALL="$loc" bash -c '. "$1"; fail_open_notice h "$2"' _ "$LIB" $'a\xc2\x9b31mb é'
        [ "$status" -eq 0 ]
        msg=$(printf '%s' "$output" | jq -r '.systemMessage')
        # why: `if`, not a bare `!` — bats ignores a negated command's status (test_bats_assertions)
        if printf '%s' "$msg" | LC_ALL=C grep -qF $'\xc2\x9b'; then echo "CSI in ($loc): $msg"; return 1; fi
        if LC_ALL=C grep -qF $'\xc2\x9b' "$CLAUDE_HOOK_LOG"; then echo "CSI in log ($loc)"; return 1; fi
        [[ "$msg" == *"é"* ]]
    done
}

@test "log_* masks secrets with their rule id" {
    . "$LIB"
    log_warn h "aws=$AWS gh=$GHP key=$ANT"
    run ! grep -qF "$AWS" "$CLAUDE_HOOK_LOG"
    run ! grep -qF "$GHP" "$CLAUDE_HOOK_LOG"
    run ! grep -qF "$ANT" "$CLAUDE_HOOK_LOG"
    grep -qF 'aws=[REDACTED:aws-access-key]' "$CLAUDE_HOOK_LOG"
    grep -qF 'gh=[REDACTED:github-token]' "$CLAUDE_HOOK_LOG"
    grep -qF 'key=[REDACTED:sk-key]' "$CLAUDE_HOOK_LOG"
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
    [ "$output" = "token [REDACTED:github-token] end" ]
}

@test "messages are capped at 8 KB before matching" {
    . "$LIB"
    big=$(head -c 20000 /dev/zero | tr '\0' 'x')
    log_info h "$big"
    msg=$(sed 's/^[^ ]* INFO h: //' "$CLAUDE_HOOK_LOG")
    [ "${#msg}" -le 8192 ]
}

@test "a secret straddling the cap is masked, not left as a fragment" {
    . "$LIB"
    pad=$(head -c 8182 /dev/zero | tr '\0' 'x')
    run mask_secrets "${pad}${GHP}"
    [ "$status" -eq 0 ]
    [ "${#output}" -le 8192 ]
    [[ "$output" != *ghp_* ]]
}

@test "missing pattern file fails closed: the message is replaced, never logged unmasked" {
    mkdir -p "$WORK/forge/claude-code/hooks/lib"
    cp "$LIB" "$WORK/forge/claude-code/hooks/lib/"
    . "$WORK/forge/claude-code/hooks/lib/aa-ma-log.sh"
    log_warn h "secret $GHP"
    run ! grep -qF "$GHP" "$CLAUDE_HOOK_LOG"
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
    [ "$(printf '%s' "$output" | jq -r '.systemMessage')" = "h: leaked [REDACTED:aws-access-key]" ]
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

@test "under set -e with stdout and stderr closed, no log function aborts the caller" {
    # why: a PATH with the tools the library needs, minus jq, exercises the no-jq branch
    NOJQ="$WORK/nojq"; mkdir -p "$NOJQ"
    ln -s "$(command -v date)" "$NOJQ/date"; ln -s "$(command -v mkdir)" "$NOJQ/mkdir"
    run bash -c '
        set -euo pipefail
        . "$1"
        HOOK_DEBUG=1
        fail_open_notice h "notice" >&- 2>&-
        log_debug h "debug" 2>&-
        CLAUDE_HOOK_LOG=/proc/aa-ma-no-such/hooks.log log_error h "lost" 2>&-
        PATH="$2" fail_open_notice h "no jq" >&- 2>&-
        echo survived' _ "$LIB" "$NOJQ"
    [ "$status" -eq 0 ]
    [ "$output" = "survived" ]
}

@test "a malformed rule line (empty regex or a second tab) fails closed (M7 §6.6)" {
    for bad in 'broken\t' 'two\tab\tcd'; do
        rm -rf "$WORK/forge"
        mkdir -p "$WORK/forge/claude-code/hooks/lib" "$WORK/forge/src/aa_ma"
        cp "$LIB" "$WORK/forge/claude-code/hooks/lib/"
        printf "ok\tabc\n${bad}\n" > "$WORK/forge/src/aa_ma/secret_patterns.tsv"
        run bash -c '. "$1"; mask_secrets "secret"' _ "$WORK/forge/claude-code/hooks/lib/aa-ma-log.sh"
        [ "$output" = "[redaction failed]" ]
    done
}

@test "patterns load lazily: sourcing the library alone does not read the pattern file (M7 §6.6)" {
    run bash -c '. "$1"; echo "ok=${_AA_MA_SECRET_PATTERNS_OK}"' _ "$LIB"
    [ "$output" = "ok=0" ]
    run bash -c '. "$1"; mask_secrets x >/dev/null; echo "ok=${_AA_MA_SECRET_PATTERNS_OK}"' _ "$LIB"
    [ "$output" = "ok=1" ]
}

@test "HOME unset under set -u: log calls return 0 and write no file, never a shared /tmp path (security notice)" {
    run --separate-stderr env -u HOME -u CLAUDE_HOOK_LOG HOOK_DEBUG=1 bash -c 'set -euo pipefail; cd "$2"; . "$1"; log_warn h m; log_debug h d; echo done' _ "$LIB" "$WORK"
    [ "$status" -eq 0 ]
    [ "$output" = done ]
    [[ "$stderr" == *" WARN h: m"* ]]    # no log file to write: the line goes to stderr instead
    run ! grep -nE ':-/tmp|/tmp/' "$LIB"  # a world-writable dir invites a symlink attack on the append
}

@test "date without -Is (BSD/macOS): the line uses a UTC fallback stamp, set -e caller survives (sole-dev-merge C1 HIGH)" {
    stub="$WORK/stub"; mkdir -p "$stub"
    real_date="$(command -v date)"
    printf '#!/bin/sh\ncase "$1" in -Is) echo "date: illegal option -- I" >&2; exit 1;; esac\nexec %s "$@"\n' "$real_date" > "$stub/date"
    chmod +x "$stub/date"
    run env PATH="$stub:$PATH" bash -c 'set -euo pipefail; . "$1"; log_warn h m; echo done' _ "$LIB"
    [ "$status" -eq 0 ]
    [[ "$output" == *done* ]]
    grep -qE '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z WARN h: m$' "$CLAUDE_HOOK_LOG"
}

@test "date missing entirely: the line still lands with a fixed stamp (sole-dev-merge C1 HIGH)" {
    stub="$WORK/stub2"; mkdir -p "$stub"
    printf '#!/bin/sh\nexit 1\n' > "$stub/date"; chmod +x "$stub/date"
    run env PATH="$stub:$PATH" bash -c 'set -euo pipefail; . "$1"; log_warn h m; echo done' _ "$LIB"
    [ "$status" -eq 0 ]
    grep -qE '^unknown-time WARN h: m$' "$CLAUDE_HOOK_LOG"
}

@test "a new hooks.log is private: file 600, dir 700 (sole-dev-merge C2 LOW)" {
    export CLAUDE_HOOK_LOG="$WORK/fresh/logs/hooks.log"
    . "$LIB"
    log_warn h m
    [ "$(stat -c %a "$CLAUDE_HOOK_LOG")" = 600 ]
    [ "$(stat -c %a "${CLAUDE_HOOK_LOG%/*}")" = 700 ]
}

@test "readlink without -f: patterns still load, through an installed symlink too (sole-dev-merge C1 LOW)" {
    stub="$WORK/stub3"; mkdir -p "$stub"
    printf '#!/bin/sh\ncase "$1" in -f) echo "readlink: illegal option -- f" >&2; exit 1;; esac\nexec %s "$@"\n' "$(command -v readlink)" > "$stub/readlink"
    chmod +x "$stub/readlink"
    mkdir -p "$WORK/home/hooks/lib"; ln -s "$LIB" "$WORK/home/hooks/lib/aa-ma-log.sh"
    for lib in "$LIB" "$WORK/home/hooks/lib/aa-ma-log.sh"; do
        run --separate-stderr env PATH="$stub:$PATH" bash -c '. "$1"; mask_secrets "t $2"' _ "$lib" "$GHP"
        [ "$output" = "t [REDACTED:github-token]" ]
        [ -z "$stderr" ]
    done
}
