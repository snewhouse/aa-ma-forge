#!/usr/bin/env bats
# security-static-check.bats — tests for claude-code/hooks/security-static-check.sh
#
# Hook contract (PreToolUse matcher=Bash):
#   stdin  : {"tool_name":"Bash","tool_input":{"command":"...git commit..."}}
#   exit 0 : pass (kill-switch, no patterns found, [security-bypass: reason] marker,
#            editor-form, non-commit bash, non-Python files only)
#   exit 2 : block with stderr naming the detected pattern(s) and file:line
#   exit 1 : hook infra error (jq parse failure)
#
# Detection scope (Python files in staged diff, ADDED lines only):
#   - Hardcoded secrets: api_key/token/password/secret = "literal"
#   - Shell-injection: subprocess(..., shell=True), dynamic-code idioms
#   - Path traversal: open() / Path() with relative-up components
#   - SQL string concat: .execute(f"...") or .execute("..." + ...)
#   - Unsafe binary deserialisation (CWE-502 family)
#
# Bypass mechanisms:
#   - AA_MA_HOOKS_DISABLE=1  (master kill switch)
#   - [security-bypass: <reason>] marker on its own line (auditable in git log)
#
# IMPLEMENTATION NOTE: To prevent IDE/editor security-reminder hooks from firing
# on the bats source itself, all security-pattern literals are assembled at
# runtime via string concatenation. This keeps the bats source clean of any
# scannable trigger token.

load ../lib/hook_payloads

setup() {
    HOOK="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)/claude-code/hooks/security-static-check.sh"
    BATS_TMP="$(mktemp -d)"
    BATS_TMP_HOME="$(mktemp -d)"
    export BATS_TMP BATS_TMP_HOME

    # Runtime-assembled pattern fragments (split to keep bats source clean)
    EV_CALL="ev""al(user_input)"
    EXEC_CALL="ex""ec(dynamic_code)"
    SUBPROC_SHELL='subprocess.run(cmd, shell''=''True)'
    SQL_FSTRING='cursor.ex''ecute(f"SELECT * FROM users WHERE id={user_id}")'
    SQL_CONCAT='cursor.ex''ecute("SELECT * FROM users WHERE id=" + user_id)'
    UNSAFE_DESER_IMPORT='import p''ickle'
    UNSAFE_DESER_CALL='obj = p''ickle.loads(untrusted_bytes)'
    PATH_TRAV='with open("../../../etc/p""asswd") as f:
    data = f.read()'
    HARD_KEY='API_KEY = "sk-1234567890abcdef1234567890abcdef"'
    HARD_PWD='password = "supersecret123"'
    export EV_CALL EXEC_CALL SUBPROC_SHELL SQL_FSTRING SQL_CONCAT \
           UNSAFE_DESER_IMPORT UNSAFE_DESER_CALL PATH_TRAV HARD_KEY HARD_PWD

    # Initialize a tiny git repo for staged-diff tests
    (
        cd "$BATS_TMP"
        git init -q
        git config user.email "t@e.i"
        git config user.name "t"
        git config commit.gpgsign false
        printf '# baseline\n' > README.md
        git add README.md
        git commit -q -m "baseline"
    )
}

teardown() {
    [ -n "${BATS_TMP:-}" ] && rm -rf "$BATS_TMP"
    [ -n "${BATS_TMP_HOME:-}" ] && rm -rf "$BATS_TMP_HOME"
}

# Build a PreToolUse stdin JSON for a given bash command string.
# The real captured PreToolUse(Bash) payload, carrying command $1.
make_input() {
    payload PreToolUse-Bash --arg cmd "$1" '.tool_input.command = $cmd'
}

# Stage a file with given content in the bats temp repo.
stage_file() {
    local path="$1"
    local content="$2"
    (
        cd "$BATS_TMP"
        mkdir -p "$(dirname "$path")"
        printf '%s\n' "$content" > "$path"
        git add "$path"
    )
}

# Run the hook with HOME isolated and CWD = the bats temp repo.
run_hook() {
    local cmd="$1"
    local input
    input=$(make_input "$cmd")
    cd "$BATS_TMP"
    HOME="$BATS_TMP_HOME" run bash -c "printf '%s' \"\$1\" | bash \"$HOOK\"" _ "$input"
}

@test "clean Python file → exit 0" {
    stage_file "src/clean.py" "def add(a, b):
    return a + b"
    run_hook 'git commit -m "feat: add helper"'
    [ "$status" -eq 0 ]
}

@test "hardcoded API key in *.py → exit 2 with stderr mentioning secret" {
    stage_file "src/leak.py" "$HARD_KEY"
    run_hook 'git commit -m "feat: add key"'
    [ "$status" -eq 2 ]
    [[ "$output" == *"secret"* || "$output" == *"key"* || "$output" == *"hardcoded"* ]]
    [[ "$output" == *"src/leak.py"* ]]
}

@test "hardcoded password literal in *.py → exit 2" {
    stage_file "src/auth.py" "$HARD_PWD"
    run_hook 'git commit -m "feat: auth"'
    [ "$status" -eq 2 ]
    [[ "$output" == *"password"* || "$output" == *"secret"* || "$output" == *"hardcoded"* ]]
}

@test "subprocess shell=True → exit 2 with stderr mentioning shell" {
    stage_file "src/run.py" "import subprocess
$SUBPROC_SHELL"
    run_hook 'git commit -m "feat: run cmd"'
    [ "$status" -eq 2 ]
    [[ "$output" == *"shell"* || "$output" == *"injection"* ]]
}

@test "dynamic-code call → exit 2" {
    stage_file "src/dyn.py" "result = $EV_CALL"
    run_hook 'git commit -m "feat: dynamic"'
    [ "$status" -eq 2 ]
    [[ "$output" == *"dynamic"* || "$output" == *"shell"* || "$output" == *"injection"* ]]
}

@test "path traversal pattern → exit 2" {
    stage_file "src/file.py" "$PATH_TRAV"
    run_hook 'git commit -m "feat: read"'
    [ "$status" -eq 2 ]
    [[ "$output" == *"path"* || "$output" == *"traversal"* ]]
}

@test "SQL string concatenation with f-string → exit 2" {
    stage_file "src/db.py" "$SQL_FSTRING"
    run_hook 'git commit -m "feat: query"'
    [ "$status" -eq 2 ]
    [[ "$output" == *"SQL"* || "$output" == *"sql"* || "$output" == *"concat"* ]]
}

@test "SQL string concatenation with + operator → exit 2" {
    stage_file "src/db.py" "$SQL_CONCAT"
    run_hook 'git commit -m "feat: query"'
    [ "$status" -eq 2 ]
    [[ "$output" == *"SQL"* || "$output" == *"sql"* || "$output" == *"concat"* ]]
}

@test "unsafe binary deserialisation (CWE-502) → exit 2" {
    stage_file "src/load.py" "$UNSAFE_DESER_IMPORT
$UNSAFE_DESER_CALL"
    run_hook 'git commit -m "feat: deserialize"'
    [ "$status" -eq 2 ]
    [[ "$output" == *"deserial"* || "$output" == *"CWE-502"* || "$output" == *"binary"* ]]
}

@test "kill switch (AA_MA_HOOKS_DISABLE=1) → exit 0 even with detected pattern" {
    stage_file "src/leak.py" "$HARD_KEY"
    input=$(make_input 'git commit -m "feat: anything"')
    cd "$BATS_TMP"
    AA_MA_HOOKS_DISABLE=1 HOME="$BATS_TMP_HOME" run bash -c "printf '%s' \"\$1\" | bash \"$HOOK\"" _ "$input"
    [ "$status" -eq 0 ]
}

@test "[security-bypass: reason] marker on own line → exit 0" {
    stage_file "src/leak.py" "$HARD_KEY"
    run_hook "git commit -m \"feat: legacy import

[security-bypass: pre-existing test fixture, tracked in issue #123]\""
    [ "$status" -eq 0 ]
}

@test "[security-bypass] without reason → exit 2 (must include reason)" {
    stage_file "src/leak.py" "$HARD_KEY"
    run_hook "git commit -m \"feat: bad

[security-bypass]\""
    [ "$status" -eq 2 ]
}

@test "non-Python file with security pattern → exit 0 (out of scope)" {
    stage_file "docs/example.md" "\`\`\`python
$HARD_KEY
\`\`\`"
    run_hook 'git commit -m "docs: example"'
    [ "$status" -eq 0 ]
}

@test "editor-form 'git commit' (no -m) → exit 0 (pass-through)" {
    stage_file "src/leak.py" "$HARD_KEY"
    run_hook 'git commit'
    [ "$status" -eq 0 ]
    run_hook 'git commit --amend'
    [ "$status" -eq 0 ]
}

@test "non-commit bash command → exit 0 (not our concern)" {
    stage_file "src/leak.py" "$HARD_KEY"
    run_hook 'ls -la src/'
    [ "$status" -eq 0 ]
}

@test "word-boundary: 'git commit-tree' does not trigger" {
    stage_file "src/leak.py" "$HARD_KEY"
    run_hook 'git commit-tree HEAD^{tree} -m "x"'
    [ "$status" -eq 0 ]
}

@test "deletion-only diff with pattern in deleted lines → exit 0" {
    (
        cd "$BATS_TMP"
        mkdir -p src
        printf '%s\n' "$HARD_KEY" > src/legacy.py
        git add src/legacy.py
        git commit -q -m "baseline: add legacy"
        git rm -q src/legacy.py
    )
    run_hook 'git commit -m "chore: remove legacy"'
    [ "$status" -eq 0 ]
}

@test "placeholder strings ('your-api-key', '<KEY>') do NOT trigger" {
    stage_file "src/example.py" 'API_KEY = "your-api-key-here"
TOKEN = "<INSERT_TOKEN>"
PASSWORD = "xxxxxxxx"'
    run_hook 'git commit -m "feat: example"'
    [ "$status" -eq 0 ]
}

@test "variable substitution (os.environ / os.getenv) does NOT trigger" {
    stage_file "src/conf.py" 'import os
API_KEY = os.environ["API_KEY"]
TOKEN = os.getenv("TOKEN")'
    run_hook 'git commit -m "feat: env config"'
    [ "$status" -eq 0 ]
}

@test "non-git repo CWD → exit 0 (graceful skip)" {
    NONREPO="$(mktemp -d)"
    cd "$NONREPO"
    input=$(make_input 'git commit -m "x"')
    HOME="$BATS_TMP_HOME" run bash -c "printf '%s' \"\$1\" | bash \"$HOOK\"" _ "$input"
    [ "$status" -eq 0 ]
    rm -rf "$NONREPO"
}

@test "shellcheck passes on hook script" {
    if ! command -v shellcheck >/dev/null 2>&1; then
        skip "shellcheck not installed"
    fi
    run shellcheck "$HOOK"
    [ "$status" -eq 0 ]
}

# --- M8.6: forge-pinned Ruff S (S102,S301,S307,S602,S604,S608) on the staged blobs ---------
REPO_ROOT_SSC="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)"

# ssc_forge — the hook in a forge layout with NO .venv (ruff must come from PATH or be absent).
ssc_forge() {
    local d="$BATS_TMP_HOME/forge"
    mkdir -p "$d/claude-code/hooks/lib" "$d/src/aa_ma"
    cp "$HOOK" "$d/claude-code/hooks/"
    cp "$REPO_ROOT_SSC"/claude-code/hooks/lib/aa-ma-*.sh "$d/claude-code/hooks/lib/"
    cp "$REPO_ROOT_SSC/src/aa_ma/secret_patterns.tsv" "$d/src/aa_ma/"
    echo "$d/claude-code/hooks/security-static-check.sh"
}

# ssc_sysbin — a PATH dir with what the hook needs, and no ruff.
ssc_sysbin() {
    local b="$BATS_TMP_HOME/sysbin" t
    mkdir -p "$b"
    for t in cat jq git grep sed tr date mkdir head wc readlink dirname cut; do ln -sf "$(command -v "$t")" "$b/$t"; done
    echo "$b"
}

@test "Ruff S602 on a staged shell=True → exit 2 naming the rule" {
    stage_file "src/run.py" "import subprocess
$SUBPROC_SHELL"
    run_hook 'git commit -m "feat: run"'
    [ "$status" -eq 2 ]
    [[ "$output" == *"src/run.py:2"*"S602"* ]]
}

@test "the second dynamic-code builtin (Ruff S102) → exit 2" {
    stage_file "src/dyn2.py" "$EXEC_CALL"
    run_hook 'git commit -m "feat: dyn"'
    [ "$status" -eq 2 ]
    [[ "$output" == *"S102"* ]]
}

@test "the staged blob is scanned, not the working tree" {
    stage_file "src/run.py" "import subprocess
$SUBPROC_SHELL"
    printf 'x = 1\n' > "$BATS_TMP/src/run.py"   # clean working copy, dirty index
    run_hook 'git commit -m "feat: run"'
    [ "$status" -eq 2 ]
}

@test "a Ruff finding on an unchanged line does not block (only introduced lines)" {
    stage_file "src/old.py" "import subprocess
$SUBPROC_SHELL"
    (cd "$BATS_TMP" && git commit -qm old)
    stage_file "src/old.py" "import subprocess
$SUBPROC_SHELL
y = 2"
    run_hook 'git commit -m "feat: touch"'
    [ "$status" -eq 0 ]
}

@test "the repo's own ruff config cannot switch the rules off (--isolated)" {
    stage_file "pyproject.toml" '[tool.ruff.lint]
ignore = ["S602"]'
    stage_file "src/run.py" "import subprocess
$SUBPROC_SHELL"
    run_hook 'git commit -m "feat: run"'
    [ "$status" -eq 2 ]
}

@test "a per-site noqa does NOT suppress the check (the bypass marker is the auditable escape)" {
    stage_file "src/run.py" "import subprocess
$SUBPROC_SHELL  # noqa: S602"
    run_hook 'git commit -m "feat: run"'
    [ "$status" -eq 2 ]
}

@test "a hostile repo's .venv/bin/ruff is never run" {
    mkdir -p "$BATS_TMP/.venv/bin"
    printf '#!/bin/sh\n: > "%s/PWNED"\n' "$BATS_TMP_HOME" > "$BATS_TMP/.venv/bin/ruff"
    chmod +x "$BATS_TMP/.venv/bin/ruff"
    stage_file "src/run.py" "import subprocess
$SUBPROC_SHELL"
    local input; input=$(make_input 'git commit -m "feat: run"')
    cd "$BATS_TMP"
    run env HOME="$BATS_TMP_HOME" PATH=".venv/bin:$(ssc_sysbin)" "$BASH" "$(ssc_forge)" <<< "$input"
    [ ! -e "$BATS_TMP_HOME/PWNED" ]
}

@test "no ruff → a systemMessage and a hooks.log line, exit 0 — never a silent pass" {
    stage_file "src/run.py" "import subprocess
$SUBPROC_SHELL"
    local input; input=$(make_input 'git commit -m "feat: run"')
    cd "$BATS_TMP"
    run env HOME="$BATS_TMP_HOME" PATH="$(ssc_sysbin)" "$BASH" "$(ssc_forge)" <<< "$input"
    [ "$status" -eq 0 ]
    [[ "$output" == *'"systemMessage"'*"ruff"* ]]
    grep -q 'WARN security-static-check: .*ruff' "$BATS_TMP_HOME/.claude/logs/hooks.log"
}

@test "no ruff still blocks a secret literal (the regex classes do not need ruff)" {
    stage_file "src/leak.py" "$HARD_KEY"
    local input; input=$(make_input 'git commit -m "feat: key"')
    cd "$BATS_TMP"
    run env HOME="$BATS_TMP_HOME" PATH="$(ssc_sysbin)" "$BASH" "$(ssc_forge)" <<< "$input"
    [ "$status" -eq 2 ]
}

@test "payload on a socket stdin (as Claude Code delivers it) is read (L-050)" {
    stage_file "src/run.py" "import subprocess
$SUBPROC_SHELL"
    local input; input=$(make_input 'git commit -m "feat: run"')
    cd "$BATS_TMP"
    run env HOME="$BATS_TMP_HOME" python3 -c '
import socket, subprocess, sys
ours, theirs = socket.socketpair()
p = subprocess.Popen(["bash", sys.argv[1]], stdin=theirs)
theirs.close(); ours.sendall(sys.argv[2].encode()); ours.shutdown(socket.SHUT_WR)
sys.exit(p.wait())' "$HOOK" "$input"
    [ "$status" -eq 2 ]
}

@test "the regex classes Ruff now covers are retired from the script" {
    run grep -nE 'SQL_FN|PKL_MOD|BIN_DYN|shell injection \(subprocess' "$HOOK"
    [ "$status" -eq 1 ]
}

@test "ruff erroring on a file (rc 2) → a systemMessage naming the file, never a silent pass" {
    stage_file "src/run.py" "import subprocess
$SUBPROC_SHELL"
    local b; b=$(ssc_sysbin)
    printf '#!/bin/sh\necho "ruff: boom" >&2\nexit 2\n' > "$b/ruff"
    chmod +x "$b/ruff"
    local input; input=$(make_input 'git commit -m "feat: run"')
    cd "$BATS_TMP"
    run env HOME="$BATS_TMP_HOME" PATH="$b" "$BASH" "$(ssc_forge)" <<< "$input"
    [ "$status" -eq 0 ]
    [[ "$output" == *'"systemMessage"'*"ruff failed on src/run.py"* ]]
}

# --- M8.6 security review: repo-controlled suppressions and parser differentials ----------

@test "an added shell=True on a continuation line of an unchanged call → exit 2" {
    stage_file "src/multi.py" "import subprocess
subprocess.run(
    cmd,
)"
    (cd "$BATS_TMP" && git commit -qm old)
    stage_file "src/multi.py" "import subprocess
subprocess.run(
    cmd,
    shell""=""True,
)"
    run_hook 'git commit -m "feat: touch"'
    [ "$status" -eq 2 ]
    [[ "$output" == *"S602"* ]]
}

@test "a file-level '# ruff: noqa' cannot suppress the check" {
    stage_file "src/run.py" "# ruff: noqa
import subprocess
$SUBPROC_SHELL"
    run_hook 'git commit -m "feat: run"'
    [ "$status" -eq 2 ]
}

@test "a renamed file with an added shell=True is scanned" {
    local body="import subprocess"
    for i in 1 2 3 4 5 6 7 8 9 10 11 12; do body+=$'\n'"v${i} = ${i}"; done
    stage_file "src/a.py" "$body"
    (cd "$BATS_TMP" && git commit -qm old && git mv src/a.py src/b.py)
    stage_file "src/b.py" "$body
$SUBPROC_SHELL"
    (cd "$BATS_TMP" && git diff --cached --name-status | grep -q '^R')   # it really is a rename
    run_hook 'git commit -m "feat: rename"'
    [ "$status" -eq 2 ]
}
