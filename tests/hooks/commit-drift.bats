#!/usr/bin/env bats
# commit-drift.bats — tests for claude-code/hooks/aa-ma-commit-drift.sh
#
# Hook contract (PostToolUse matcher=Bash):
#   - Inspects last commit via `git log -1 --name-only HEAD`
#   - Warns (stderr) when committed-file count > AA_MA_DRIFT_THRESHOLD (default 1)
#     AND no active task's tasks.md/provenance.log is among those files
#   - [no-sync-check] on its own line in commit message suppresses the warning
#   - Kill switch respected
#   - Always exits 0 (advisory)
#   - Silent when no active plans, initial-commit case, below-threshold commits

load ../lib/hook_payloads

setup() {
    HOOK="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)/claude-code/hooks/aa-ma-commit-drift.sh"
    FIXTURE="${BATS_TEST_DIRNAME}/fixtures/build_active_dir.sh"
    BATS_TMP="$(mktemp -d)"
    BATS_TMP_HOME="$(mktemp -d)"
    export BATS_TMP BATS_TMP_HOME
}

teardown() {
    [ -n "${BATS_TMP:-}" ] && rm -rf "$BATS_TMP"
    [ -n "${BATS_TMP_HOME:-}" ] && rm -rf "$BATS_TMP_HOME"
}

# Builds: .claude/dev/active/task-N/ layouts + initial git commit of everything.
# After return, caller should modify files to create drift scenarios and commit.
setup_repo_with_tasks() {
    local count="$1"
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" "$count" plain
    (
        cd "$BATS_TMP"
        git init -q
        git -c user.email=t@e.i -c user.name=t -c commit.gpgsign=false add -A
        git -c user.email=t@e.i -c user.name=t -c commit.gpgsign=false \
            commit -q -m "fixture: initial"
    )
}

# Helper: make a commit touching N random files outside .claude/ with a message.
commit_files() {
    local count="$1" msg="$2"
    (
        cd "$BATS_TMP"
        for i in $(seq 1 "$count"); do
            printf 'line\n' >> "src-$i.txt"
        done
        git -c user.email=t@e.i -c user.name=t -c commit.gpgsign=false add -A
        git -c user.email=t@e.i -c user.name=t -c commit.gpgsign=false \
            commit -q -m "$msg"
    )
}

# Helper: build a PostToolUse-shape stdin JSON.
# The real captured PostToolUse(Bash) payload, carrying command $1.
make_input() {
    payload PostToolUse-Bash --arg cmd "$1" '.tool_input.command = $cmd'
}

run_hook() {
    local cmd="$1"
    local input
    input=$(make_input "$cmd")
    HOME="$BATS_TMP_HOME" run bash -c "printf '%s' \"\$1\" | bash \"$HOOK\"" _ "$input"
}

@test "tasks.md touched in commit → silent" {
    setup_repo_with_tasks 1
    (
        cd "$BATS_TMP"
        printf '\nnew\n' >> .claude/dev/active/task-1/task-1-tasks.md
        printf 'code\n' >> src.txt
        git -c user.email=t@e.i -c user.name=t -c commit.gpgsign=false add -A
        git -c user.email=t@e.i -c user.name=t -c commit.gpgsign=false \
            commit -q -m "feat: update tasks + code"
    )
    cd "$BATS_TMP"
    run_hook 'git commit -m "feat: update tasks + code"'
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "tasks.md not touched (above threshold) → warn naming top active task" {
    setup_repo_with_tasks 1
    commit_files 2 "feat: code only"
    cd "$BATS_TMP"
    run_hook 'git commit -m "feat: code only"'
    [ "$status" -eq 0 ]
    [[ "$output" == *"task-1"* ]]
    [[ "$output" == *"drift"* || "$output" == *"tasks.md"* ]]
}

@test "[no-sync-check] marker on own line → silent" {
    setup_repo_with_tasks 1
    (
        cd "$BATS_TMP"
        printf 'code\n' > src.txt
        printf 'code\n' > src2.txt
        git -c user.email=t@e.i -c user.name=t -c commit.gpgsign=false add -A
        git -c user.email=t@e.i -c user.name=t -c commit.gpgsign=false \
            commit -q -m "chore: unrelated

[no-sync-check]"
    )
    cd "$BATS_TMP"
    run_hook 'git commit -m "chore: unrelated

[no-sync-check]"'
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "no active tasks → silent" {
    # Git repo exists but no .claude/dev/active/ content
    (
        cd "$BATS_TMP"
        git init -q
        printf 'code\n' > src.txt
        git -c user.email=t@e.i -c user.name=t -c commit.gpgsign=false add -A
        git -c user.email=t@e.i -c user.name=t -c commit.gpgsign=false \
            commit -q -m "initial"
        printf 'more\n' >> src.txt
        git -c user.email=t@e.i -c user.name=t -c commit.gpgsign=false add -A
        git -c user.email=t@e.i -c user.name=t -c commit.gpgsign=false \
            commit -q -m "feat: code"
    )
    cd "$BATS_TMP"
    run_hook 'git commit -m "feat: code"'
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "kill switch (AA_MA_HOOKS_DISABLE=1) → silent even when drift would trigger" {
    setup_repo_with_tasks 1
    commit_files 2 "feat: code"
    cd "$BATS_TMP"
    AA_MA_HOOKS_DISABLE=1 HOME="$BATS_TMP_HOME" run bash -c "printf '%s' \"\$1\" | bash \"$HOOK\"" _ "$(make_input 'git commit -m "feat: code"')"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "below-threshold commit (AA_MA_DRIFT_THRESHOLD high) → silent" {
    setup_repo_with_tasks 1
    commit_files 2 "feat: only 2 files"
    cd "$BATS_TMP"
    AA_MA_DRIFT_THRESHOLD=10 HOME="$BATS_TMP_HOME" run bash -c "printf '%s' \"\$1\" | bash \"$HOOK\"" _ "$(make_input 'git commit -m "feat: only 2 files"')"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "multiple active tasks, none touched → warn naming each" {
    setup_repo_with_tasks 2
    commit_files 2 "feat: unrelated"
    cd "$BATS_TMP"
    run_hook 'git commit -m "feat: unrelated"'
    [ "$status" -eq 0 ]
    [[ "$output" == *"task-1"* ]]
    [[ "$output" == *"task-2"* ]]
}

@test "provenance.log touched (instead of tasks.md) → silent (either satisfies)" {
    setup_repo_with_tasks 1
    (
        cd "$BATS_TMP"
        printf 'log\n' >> .claude/dev/active/task-1/task-1-provenance.log
        printf 'code\n' >> src.txt
        git -c user.email=t@e.i -c user.name=t -c commit.gpgsign=false add -A
        git -c user.email=t@e.i -c user.name=t -c commit.gpgsign=false \
            commit -q -m "feat: code + provenance"
    )
    cd "$BATS_TMP"
    run_hook 'git commit -m "feat: code + provenance"'
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

# ---------------------------------------------------------------------------
# Ad-hoc co-change advisory (code-conventions-impact 10.7). A commit with no active
# plan (or one marked [ad-hoc]) gets ONE line naming the codemem co_changes partners
# (>= 5 shared commits, >= 50%) of its files that it left out. Fails open silently.
# ---------------------------------------------------------------------------

# _cochange_stub <json> [sleep-seconds]: CODEMEM_BIN records argv, prints <json>.
_cochange_stub() {
    mkdir -p "$BATS_TMP_HOME/cm"
    : > "$BATS_TMP_HOME/cm/index.db"
    printf '%s\n' "$1" > "$BATS_TMP_HOME/cm.json"
    cat > "$BATS_TMP_HOME/codemem" <<STUB
#!/usr/bin/env bash
printf '%s\n' "\$@" > "$BATS_TMP_HOME/codemem.args"
sleep ${2:-0}
cat "$BATS_TMP_HOME/cm.json"
STUB
    chmod +x "$BATS_TMP_HOME/codemem"
    export CODEMEM_DB="$BATS_TMP_HOME/cm/index.db" CODEMEM_BIN="$BATS_TMP_HOME/codemem"
}

# A repo with no active plan whose last commit touched src-1.txt and src-2.txt.
_adhoc_repo() {
    ( cd "$BATS_TMP" && git init -q )
    commit_files 2 "${1:-chore: ad-hoc}"
}

PARTNERS='{"src-1.txt": {"files": [{"path": "partner.py", "count": 7, "ratio": 0.7}, {"path": "src-2.txt", "count": 6, "ratio": 0.6}], "error": null},
 "src-2.txt": {"files": [{"path": "partner.py", "count": 5, "ratio": 0.5}, {"path": "other.md", "count": 5, "ratio": 0.5}], "error": null}}'

@test "ad-hoc commit (no active plan): one advisory line naming co-change partners left out" {
    _adhoc_repo
    _cochange_stub "$PARTNERS"
    cd "$BATS_TMP"
    run_hook 'git commit -m "chore: ad-hoc"'
    [ "$status" -eq 0 ]
    [ "${#lines[@]}" -eq 1 ]
    [[ "${lines[0]}" == *"co-change"*"other.md, partner.py"* ]]
    [[ "${lines[0]}" != *"src-2.txt"* ]]   # in the commit: not a miss
    run cat "$BATS_TMP_HOME/codemem.args"
    [[ "$output" == *$'co_changes'* ]]
    [[ "$output" == *$'--threshold\n5\n--min-ratio\n0.5'* ]]
    [[ "$output" == *$'--\nsrc-1.txt\nsrc-2.txt'* ]]
}

@test "ad-hoc commit whose partners are all in it → silent" {
    _adhoc_repo
    _cochange_stub '{"src-1.txt": {"files": [{"path": "src-2.txt", "count": 6, "ratio": 0.6}]}, "src-2.txt": {"files": []}}'
    cd "$BATS_TMP"
    run_hook 'git commit -m "chore: ad-hoc"'
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "ad-hoc commit, no codemem index → silent (fail open)" {
    _adhoc_repo
    _cochange_stub "$PARTNERS"
    rm "$BATS_TMP_HOME/cm/index.db"
    cd "$BATS_TMP"
    run_hook 'git commit -m "chore: ad-hoc"'
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "ad-hoc commit, no codemem binary → silent (fail open)" {
    _adhoc_repo
    _cochange_stub "$PARTNERS"
    export CODEMEM_BIN="$BATS_TMP_HOME/absent-codemem"
    cd "$BATS_TMP"
    run_hook 'git commit -m "chore: ad-hoc"'
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "ad-hoc commit, codemem garbage → silent (fail open)" {
    _adhoc_repo
    _cochange_stub 'not json'
    cd "$BATS_TMP"
    run_hook 'git commit -m "chore: ad-hoc"'
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "ad-hoc commit, codemem slower than 2 s → killed, silent, hook returns fast" {
    _adhoc_repo
    _cochange_stub "$PARTNERS" 10
    cd "$BATS_TMP"
    local t0=$SECONDS
    run_hook 'git commit -m "chore: ad-hoc"'
    [ "$status" -eq 0 ]
    [ -z "$output" ]
    [ $((SECONDS - t0)) -le 5 ]
}

@test "active plan + [ad-hoc] marker: the advisory line is printed too" {
    setup_repo_with_tasks 1
    commit_files 2 "chore: housekeeping

[ad-hoc]"
    _cochange_stub "$PARTNERS"
    cd "$BATS_TMP"
    run_hook 'git commit -m "chore: housekeeping"'
    [ "$status" -eq 0 ]
    [[ "$output" == *"co-change"*"other.md, partner.py"* ]]
}

@test "active plan, no [ad-hoc] marker: no co-change line (the drift check owns it)" {
    setup_repo_with_tasks 1
    commit_files 2 "feat: code"
    _cochange_stub "$PARTNERS"
    cd "$BATS_TMP"
    run_hook 'git commit -m "feat: code"'
    [ "$status" -eq 0 ]
    [[ "$output" != *"co-change"* ]]
    [[ "$output" == *"task-1"* ]]
}

# §6.6 W1: every fail-open path of the advisory leaves one hooks.log line (never stdout/stderr
# noise; the hook still exits 0). A missing index or binary is the common case: DEBUG.
_hooks_log() { cat "$BATS_TMP_HOME/.claude/logs/hooks.log" 2>/dev/null || :; }   # why: no log yet reads as empty

@test "ad-hoc commit, no codemem index → one DEBUG line (HOOK_DEBUG=1)" {
    _adhoc_repo
    _cochange_stub "$PARTNERS"
    rm "$BATS_TMP_HOME/cm/index.db"
    cd "$BATS_TMP"
    HOOK_DEBUG=1 run_hook 'git commit -m "chore: ad-hoc"'
    [ "$status" -eq 0 ]
    [ "$(_hooks_log | grep -c 'DEBUG aa-ma-commit-drift: co-change advisory skipped: no codemem index')" -eq 1 ]
}

@test "ad-hoc commit, no codemem binary → one DEBUG line (HOOK_DEBUG=1)" {
    _adhoc_repo
    _cochange_stub "$PARTNERS"
    export CODEMEM_BIN="$BATS_TMP_HOME/absent-codemem"
    cd "$BATS_TMP"
    HOOK_DEBUG=1 run_hook 'git commit -m "chore: ad-hoc"'
    [ "$status" -eq 0 ]
    [ "$(_hooks_log | grep -c 'DEBUG aa-ma-commit-drift: co-change advisory skipped: no codemem binary')" -eq 1 ]
}

@test "ad-hoc commit, codemem garbage → one WARN line, empty output" {
    _adhoc_repo
    _cochange_stub 'not json'
    cd "$BATS_TMP"
    run_hook 'git commit -m "chore: ad-hoc"'
    [ "$status" -eq 0 ]
    [ -z "$output" ]
    [ "$(_hooks_log | grep -c 'WARN aa-ma-commit-drift: co-change advisory skipped: codemem co_changes failed')" -eq 1 ]
}

@test "ad-hoc commit, codemem exits non-zero → one WARN line, empty output" {
    _adhoc_repo
    _cochange_stub "$PARTNERS"
    printf 'exit 3\n' >> "$BATS_TMP_HOME/codemem"
    cd "$BATS_TMP"
    run_hook 'git commit -m "chore: ad-hoc"'
    [ "$status" -eq 0 ]
    [ -z "$output" ]
    [ "$(_hooks_log | grep -c 'WARN aa-ma-commit-drift: co-change advisory skipped: codemem co_changes failed')" -eq 1 ]
}

@test "ad-hoc commit, codemem timeout → one WARN line naming the timeout" {
    _adhoc_repo
    _cochange_stub "$PARTNERS" 10
    cd "$BATS_TMP"
    run_hook 'git commit -m "chore: ad-hoc"'
    [ "$status" -eq 0 ]
    [ -z "$output" ]
    [ "$(_hooks_log | grep -c 'WARN aa-ma-commit-drift: co-change advisory skipped: codemem co_changes timed out')" -eq 1 ]
}
