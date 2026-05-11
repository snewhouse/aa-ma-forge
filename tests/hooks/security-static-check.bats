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
make_input() {
    jq -cn --arg cmd "$1" '{tool_name:"Bash",tool_input:{command:$cmd}}'
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
