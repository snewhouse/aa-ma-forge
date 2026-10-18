#!/usr/bin/env bats
# pre-compact.bats — tests for claude-code/hooks/pre-compact-aa-ma.sh
#
# Validates the post-M2 behavior:
#   - Iterates BOTH project-local .claude/dev/active/ AND $HOME/.claude/dev/active/
#   - Project-first collision resolution
#   - Snapshot file created per unique task
#   - Empty state → silent exit 0
#
# Pre-M2 hook only reads $HOME. These tests MUST be RED against it.

bats_require_minimum_version 1.5.0

load ../lib/hook_payloads

setup() {
    HOOK="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)/claude-code/hooks/pre-compact-aa-ma.sh"
    FIXTURE="${BATS_TEST_DIRNAME}/fixtures/build_active_dir.sh"
    BATS_TMP="$(mktemp -d)"
    BATS_TMP_HOME="$(mktemp -d)"
    export BATS_TMP BATS_TMP_HOME

    # Hook writes snapshots under $HOME/.claude/hooks/cache/compaction-snapshots/.
    # Pre-create that dir so we can read it post-run.
    mkdir -p "$BATS_TMP_HOME/.claude/hooks/cache/compaction-snapshots"
}

teardown() {
    [ -n "${BATS_TMP:-}" ] && rm -rf "$BATS_TMP"
    [ -n "${BATS_TMP_HOME:-}" ] && rm -rf "$BATS_TMP_HOME"
}

@test "empty state: no active tasks → hook runs silently, exits 0" {
    cd "$BATS_TMP"
    HOME="$BATS_TMP_HOME" run bash "$HOOK"
    [ "$status" -eq 0 ]
    # No snapshot files should be created
    snap_count=$(find "$BATS_TMP_HOME/.claude/hooks/cache/compaction-snapshots" -name '*-snapshot.md' 2>/dev/null | wc -l)
    [ "$snap_count" -eq 0 ]
}

@test "project-local only: creates snapshot for each project task" {
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 2 plain
    cd "$BATS_TMP"
    HOME="$BATS_TMP_HOME" run bash "$HOOK"
    [ "$status" -eq 0 ]
    [ -f "$BATS_TMP_HOME/.claude/hooks/cache/compaction-snapshots/task-1-snapshot.md" ]
    [ -f "$BATS_TMP_HOME/.claude/hooks/cache/compaction-snapshots/task-2-snapshot.md" ]
}

@test "home only: creates snapshot (legacy behaviour preserved)" {
    "$FIXTURE" "$BATS_TMP_HOME/.claude/dev/active" 1 plain
    cd "$BATS_TMP"
    HOME="$BATS_TMP_HOME" run bash "$HOOK"
    [ "$status" -eq 0 ]
    [ -f "$BATS_TMP_HOME/.claude/hooks/cache/compaction-snapshots/task-1-snapshot.md" ]
}

@test "both-paths iteration: unique tasks in each source → N unique snapshots" {
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 1 plain
    # Differently-named task in HOME
    mkdir -p "$BATS_TMP_HOME/.claude/dev/active/home-only"
    cat > "$BATS_TMP_HOME/.claude/dev/active/home-only/home-only-tasks.md" <<'EOF'
## Milestone 1: Home
- Status: ACTIVE
EOF
    cd "$BATS_TMP"
    HOME="$BATS_TMP_HOME" run bash "$HOOK"
    [ "$status" -eq 0 ]
    [ -f "$BATS_TMP_HOME/.claude/hooks/cache/compaction-snapshots/task-1-snapshot.md" ]
    [ -f "$BATS_TMP_HOME/.claude/hooks/cache/compaction-snapshots/home-only-snapshot.md" ]
}

@test "collision: project-local wins; home version not snapshotted" {
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 1 plain
    # Same-named task in HOME with distinguishing content
    mkdir -p "$BATS_TMP_HOME/.claude/dev/active/task-1"
    cat > "$BATS_TMP_HOME/.claude/dev/active/task-1/task-1-reference.md" <<'EOF'
HOME VERSION MARKER
EOF

    cd "$BATS_TMP"
    HOME="$BATS_TMP_HOME" run bash "$HOOK"
    [ "$status" -eq 0 ]

    snap="$BATS_TMP_HOME/.claude/hooks/cache/compaction-snapshots/task-1-snapshot.md"
    [ -f "$snap" ]
    # Snapshot content should NOT include the HOME-only marker.
    run grep -q "HOME VERSION MARKER" "$snap"
    [ "$status" -ne 0 ]
}

@test "kill switch: AA_MA_HOOKS_DISABLE=1 → no snapshots written even when tasks exist" {
    # Fixture in HOME so legacy hook WOULD snapshot without kill-switch; flag must suppress.
    "$FIXTURE" "$BATS_TMP_HOME/.claude/dev/active" 2 plain
    cd "$BATS_TMP"
    HOME="$BATS_TMP_HOME" AA_MA_HOOKS_DISABLE=1 run bash "$HOOK"
    [ "$status" -eq 0 ]
    snap_count=$(find "$BATS_TMP_HOME/.claude/hooks/cache/compaction-snapshots" -name '*-snapshot.md' 2>/dev/null | wc -l)
    [ "$snap_count" -eq 0 ]
}

@test "audit-trail append failure: fail-open (exit 0), logged per file, user-visible systemMessage" {
    [ "$(id -u)" -eq 0 ] && skip "root ignores chmod 444"
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 1 plain
    task_dir="$BATS_TMP/.claude/dev/active/task-1"
    chmod 444 "$task_dir/task-1-provenance.log" "$task_dir/task-1-context-log.md"
    cd "$BATS_TMP"
    HOME="$BATS_TMP_HOME" run bash -c "bash '$HOOK' 2>/dev/null"
    chmod 644 "$task_dir/task-1-provenance.log" "$task_dir/task-1-context-log.md"
    [ "$status" -eq 0 ]
    # Hook stderr on exit 0 reaches only the debug log, so the gap must land in hooks.log
    # (each file named; compaction.log folded in at M7.3) AND in a user-visible systemMessage.
    log="$BATS_TMP_HOME/.claude/logs/hooks.log"
    grep -q " WARN pre-compact-aa-ma: could not append checkpoint to .*task-1-provenance.log" "$log"
    grep -q " WARN pre-compact-aa-ma: could not append compaction summary to .*task-1-context-log.md" "$log"
    [ ! -e "$BATS_TMP_HOME/.claude/hooks/cache/compaction.log" ]
    printf '%s' "$output" | jq -e '.systemMessage | test("2 audit-trail append")' >/dev/null
}

@test "clean compaction: stdout stays empty (no systemMessage noise)" {
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 1 plain
    cd "$BATS_TMP"
    HOME="$BATS_TMP_HOME" run bash -c "bash '$HOOK' 2>/dev/null"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "audit-trail append failure with stdout+stderr closed: still exits 0 (fail-open survives EPIPE)" {
    [ "$(id -u)" -eq 0 ] && skip "root ignores chmod 444"
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 1 plain
    task_dir="$BATS_TMP/.claude/dev/active/task-1"
    chmod 444 "$task_dir/task-1-provenance.log" "$task_dir/task-1-context-log.md"
    cd "$BATS_TMP"
    HOME="$BATS_TMP_HOME" run bash -c "bash '$HOOK' >&- 2>&-"
    chmod 644 "$task_dir/task-1-provenance.log" "$task_dir/task-1-context-log.md"
    [ "$status" -eq 0 ]
}

@test "compaction summary names the snapshot as ~/…, never the absolute home path" {
    # context-log.md is committed; an absolute path leaks the username into a public repo.
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 1 plain
    cd "$BATS_TMP"
    HOME="$BATS_TMP_HOME" run bash "$HOOK"
    [ "$status" -eq 0 ]
    grep -qF -- '- Snapshot saved to: ~/.claude/hooks/cache/compaction-snapshots/task-1-snapshot.md' \
        "$BATS_TMP/.claude/dev/active/task-1/task-1-context-log.md"
    run ! grep -qF -- "$BATS_TMP_HOME" "$BATS_TMP/.claude/dev/active/task-1/task-1-context-log.md"
}

@test "a real captured PreCompact payload on stdin: snapshot still written (M7.5)" {
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 1 plain
    cd "$BATS_TMP"
    HOME="$BATS_TMP_HOME" run bash -c 'bash "$1" < "$2"' _ "$HOOK" "$HOOK_PAYLOADS/PreCompact.json"
    [ "$status" -eq 0 ]
    [ -f "$BATS_TMP_HOME/.claude/hooks/cache/compaction-snapshots/task-1-snapshot.md" ]
}

@test "unwritable HOME: exit 0 with a systemMessage, as the Exit header says (double-check F2)" {
    [ "$(id -u)" -eq 0 ] && skip "root ignores chmod"
    ro="$BATS_TMP/ro-home"; mkdir -p "$ro"; chmod 500 "$ro"
    cd "$BATS_TMP"
    HOME="$ro" run bash -c "bash '$HOOK' 2>/dev/null"
    chmod 700 "$ro"
    [ "$status" -eq 0 ]
    printf '%s' "$output" | jq -e '.systemMessage | test("snapshot")' >/dev/null
}

@test "HOME unset (cron, env -i): exit 0, as the Exit header says (double-check F2)" {
    cd "$BATS_TMP"
    run env -u HOME bash "$HOOK"
    [ "$status" -eq 0 ]
}

# ---------------------------------------------------------------------------
# Symlinks (sole-dev-merge-fixes 1.8, security audit). An untrusted clone can
# commit a symlink in place of an AA-MA file; the hook must never append to,
# or copy from, a file outside the task dir. Each case: target unchanged, no
# target content in the snapshot, rc 0, one hooks.log skip line, systemMessage.
# ---------------------------------------------------------------------------

_symlink_case() {   # _symlink_case <file-suffix|DIR> — link it to a sentinel target
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 1 plain
    task_dir="$BATS_TMP/.claude/dev/active/task-1"
    target="$BATS_TMP_HOME/.bashrc"
    printf 'SENTINEL-OUTSIDE-REPO\n' > "$target"
    if [ "$1" = DIR ]; then
        mkdir -p "$BATS_TMP_HOME/outside"
        mv "$task_dir" "$BATS_TMP_HOME/outside/task-1"
        printf 'SENTINEL-OUTSIDE-REPO\n' >> "$BATS_TMP_HOME/outside/task-1/task-1-reference.md"
        ln -s "$BATS_TMP_HOME/outside/task-1" "$task_dir"
        target="$BATS_TMP_HOME/outside/task-1/task-1-provenance.log"
    else
        rm "$task_dir/task-1-$1"
        ln -s "$target" "$task_dir/task-1-$1"
    fi
    before=$(sha256sum < "$target")
    cd "$BATS_TMP"
    HOME="$BATS_TMP_HOME" run bash -c "bash '$HOOK' 2>/dev/null"
}

_assert_symlink_skipped() {
    [ "$status" -eq 0 ]
    [ "$(sha256sum < "$target")" = "$before" ]
    snap="$BATS_TMP_HOME/.claude/hooks/cache/compaction-snapshots/task-1-snapshot.md"
    # why: `if`, not a bare `!` — bats ignores a negated command's status (test_bats_assertions)
    if grep -qs 'SENTINEL-OUTSIDE-REPO' "$snap"; then echo "target content copied into $snap"; return 1; fi
    [ "$(grep -c 'skipped task task-1' "$BATS_TMP_HOME/.claude/logs/hooks.log")" -eq 1 ]
    printf '%s' "$output" | jq -e '.systemMessage | test("1 task")' >/dev/null
}

@test "symlinked provenance.log → never appended to, task skipped" {
    _symlink_case provenance.log
    _assert_symlink_skipped
}

@test "symlinked context-log.md → never appended to, task skipped" {
    _symlink_case context-log.md
    _assert_symlink_skipped
}

@test "symlinked reference.md → its target is never copied into the snapshot" {
    _symlink_case reference.md
    _assert_symlink_skipped
}

@test "symlinked task dir → skipped, nothing outside the repo written or copied" {
    _symlink_case DIR
    _assert_symlink_skipped
}

# ---------------------------------------------------------------------------
# Worktree root (sole-dev-merge-fixes M5, global L-1347). The 5.0 probe showed
# stdin `cwd` always equals the hook's pwd: under MAINTAIN=1 a `cd` into a
# worktree is invisible (main root); under MAINTAIN=0 it is the worktree or a
# subdirectory of it. A: ROOT = git toplevel of stdin cwd. C: when ROOT is the
# main checkout and a linked worktree holds the same task, write nothing there.
# ---------------------------------------------------------------------------

_snaps() { printf '%s' "$BATS_TMP_HOME/.claude/hooks/cache/compaction-snapshots"; }

_main_and_worktree() {   # MAIN: a repo with task-1 committed; WT: a linked worktree of it
    MAIN="$BATS_TMP/main"
    "$FIXTURE" "$MAIN/.claude/dev/active" 1 plain
    printf '.worktrees/\n' > "$MAIN/.gitignore"
    git -C "$MAIN" init -q -b main
    git -C "$MAIN" add -A
    git -C "$MAIN" -c user.name=t -c user.email=t@example.invalid commit -q -m init
    WT="$MAIN/.worktrees/x"
    git -C "$MAIN" worktree add -q -b x "$WT"
}

_run_with_cwd() {   # _run_with_cwd <cwd> [VAR=value...] — the hook with that stdin cwd, stderr dropped
    local c="$1"; shift
    HOME="$BATS_TMP_HOME" run env "$@" bash -c 'bash "$1" 2>/dev/null <<<"$2"' _ "$HOOK" \
        "$(payload PreCompact --arg c "$c" '.cwd = $c')"
}

_git_wrapper() {   # _git_wrapper <word|-> — a git on GITBIN that logs its args and fails when they hold <word>
    GITBIN="$BATS_TMP/gitbin"; GITLOG="$BATS_TMP/git.log"
    mkdir -p "$GITBIN"
    cat > "$GITBIN/git" <<EOF
#!/usr/bin/env bash
printf '%s\n' "\$*" >> '$GITLOG'
[[ " \$* " == *" $1 "* ]] && exit 1
exec '$(command -v git)' "\$@"
EOF
    chmod +x "$GITBIN/git"
}

@test "(i) stdin cwd in a worktree subdirectory → the CHECKPOINT lands in the worktree's provenance.log" {
    _main_and_worktree
    mkdir -p "$WT/sub"
    cd "$WT/sub"
    _run_with_cwd "$WT/sub"
    [ "$status" -eq 0 ]
    grep -q 'CHECKPOINT — ActiveStep' "$WT/.claude/dev/active/task-1/task-1-provenance.log"
    [ -f "$(_snaps)/task-1-snapshot.md" ]
    [ -z "$(git -C "$MAIN" status --porcelain)" ]
}

_plan_commit() {   # _plan_commit <worktree> — a commit on its branch that touches task-1's plan
    printf -- '- worked here\n' >> "$1/.claude/dev/active/task-1/task-1-tasks.md"
    git -C "$1" -c user.name=t -c user.email=t@example.invalid commit -q -am "plan: worked in $1"
}

@test "(ii) cwd = main checkout while a linked worktree's branch carries plan commits → main untouched, snapshot kept, systemMessage names the worktree" {
    _main_and_worktree
    _plan_commit "$WT"
    cd "$MAIN"
    _run_with_cwd "$MAIN"
    [ "$status" -eq 0 ]
    [ -z "$(git -C "$MAIN" status --porcelain)" ]
    [ -z "$(git -C "$WT" status --porcelain)" ]
    [ -f "$(_snaps)/task-1-snapshot.md" ]
    printf '%s' "$output" | jq -e --arg w "$WT" '.systemMessage | contains("CHECKPOINT") and contains($w)' >/dev/null
}

@test "(iii) a single checkout with no linked worktree → CHECKPOINT appended there, stdout empty" {
    MAIN="$BATS_TMP/main"
    "$FIXTURE" "$MAIN/.claude/dev/active" 1 plain
    git -C "$MAIN" init -q -b main
    cd "$MAIN"
    _run_with_cwd "$MAIN"
    [ "$status" -eq 0 ]
    grep -q 'CHECKPOINT — ActiveStep' "$MAIN/.claude/dev/active/task-1/task-1-provenance.log"
    [ -z "$output" ]
}

@test "stdin cwd relative or nonexistent → pwd fallback, never git -C on it, systemMessage" {
    _git_wrapper -
    local bad
    for bad in 'rel/dir' '/nonexistent-aa-ma-probe/x'; do
        rm -rf "$BATS_TMP/.claude" "$GITLOG"
        "$FIXTURE" "$BATS_TMP/.claude/dev/active" 1 plain
        cd "$BATS_TMP"
        _run_with_cwd "$bad" PATH="$GITBIN:$PATH"
        [ "$status" -eq 0 ]
        grep -q 'CHECKPOINT — ActiveStep' "$BATS_TMP/.claude/dev/active/task-1/task-1-provenance.log"
        # why: `if`, not a bare `!` — bats ignores a negated command's status (test_bats_assertions)
        if grep -qsF -- "-C $bad" "$GITLOG"; then echo "git -C ran on '$bad'"; return 1; fi
        printf '%s' "$output" | jq -e '.systemMessage | test("cwd")' >/dev/null
    done
}

@test "fail-open: jq missing → pwd fallback, hooks.log line, systemMessage" {
    _main_and_worktree
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 1 plain
    local b="$BATS_TMP/nojq" d
    mkdir -p "$b"
    # Every tool on PATH except jq, so a new command in the hook cannot break this test.
    # why: 2>/dev/null || true — cp -s skips (and reports) the subdirectories some PATH dirs
    # hold; -n keeps the first hit, as PATH lookup would
    IFS=: read -ra dirs <<<"$PATH"
    for d in "${dirs[@]}"; do
        [[ -d "$d" ]] || continue
        cp -sn "$d"/* "$b"/ 2>/dev/null || true
    done
    rm -f "$b/jq"
    [ ! -e "$b/jq" ]
    cd "$BATS_TMP"
    _run_with_cwd "$WT" PATH="$b"
    [ "$status" -eq 0 ]
    grep -q 'CHECKPOINT — ActiveStep' "$BATS_TMP/.claude/dev/active/task-1/task-1-provenance.log"
    grep -qF 'WARN pre-compact-aa-ma: jq not on PATH' "$BATS_TMP_HOME/.claude/logs/hooks.log"
    [[ "$output" == *'"systemMessage"'* ]]
}

@test "fail-open: stdin cwd not in a git repo → pwd fallback, hooks.log line, systemMessage" {
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 1 plain
    mkdir -p "$BATS_TMP/plain"
    cd "$BATS_TMP"
    _run_with_cwd "$BATS_TMP/plain"
    [ "$status" -eq 0 ]
    grep -q 'CHECKPOINT — ActiveStep' "$BATS_TMP/.claude/dev/active/task-1/task-1-provenance.log"
    grep -qF 'not in a git repo' "$BATS_TMP_HOME/.claude/logs/hooks.log"
    printf '%s' "$output" | jq -e '.systemMessage | test("git repo")' >/dev/null
}

@test "fail-open: git worktree list fails → writes as before, hooks.log line, systemMessage" {
    MAIN="$BATS_TMP/main"
    "$FIXTURE" "$MAIN/.claude/dev/active" 1 plain
    git -C "$MAIN" init -q -b main
    _git_wrapper worktree
    cd "$MAIN"
    _run_with_cwd "$MAIN" PATH="$GITBIN:$PATH"
    [ "$status" -eq 0 ]
    grep -q 'worktree list' "$GITLOG"
    grep -q 'CHECKPOINT — ActiveStep' "$MAIN/.claude/dev/active/task-1/task-1-provenance.log"
    grep -qF 'worktree list failed' "$BATS_TMP_HOME/.claude/logs/hooks.log"
    printf '%s' "$output" | jq -e '.systemMessage | test("worktree")' >/dev/null
}

@test "symlinked .claude, .claude/dev or .claude/dev/active under ROOT → its tasks skipped (TODOS carry-in)" {
    local parent
    for parent in .claude .claude/dev .claude/dev/active; do
        rm -rf "$BATS_TMP/.claude" "$BATS_TMP_HOME/outside" "$BATS_TMP_HOME/.claude/logs"
        "$FIXTURE" "$BATS_TMP_HOME/outside/.claude/dev/active" 1 plain
        printf 'SENTINEL-OUTSIDE-REPO\n' >> "$BATS_TMP_HOME/outside/.claude/dev/active/task-1/task-1-reference.md"
        mkdir -p "$(dirname "$BATS_TMP/$parent")"
        ln -s "$BATS_TMP_HOME/outside/$parent" "$BATS_TMP/$parent"
        target="$BATS_TMP_HOME/outside/.claude/dev/active/task-1/task-1-provenance.log"
        before=$(sha256sum < "$target")
        rm -f "$(_snaps)/task-1-snapshot.md"
        cd "$BATS_TMP"
        HOME="$BATS_TMP_HOME" run bash -c "bash '$HOOK' 2>/dev/null"
        _assert_symlink_skipped
    done
}

@test "ROOT = \$HOME with ~/.claude a dotfiles symlink → its tasks are still written (exempt)" {
    mv "$BATS_TMP_HOME/.claude" "$BATS_TMP/dotclaude"
    ln -s "$BATS_TMP/dotclaude" "$BATS_TMP_HOME/.claude"
    "$FIXTURE" "$BATS_TMP/dotclaude/dev/active" 1 plain
    cd "$BATS_TMP_HOME"
    HOME="$BATS_TMP_HOME" run bash -c "bash '$HOOK' 2>/dev/null"
    [ "$status" -eq 0 ]
    grep -q 'CHECKPOINT — ActiveStep' "$BATS_TMP/dotclaude/dev/active/task-1/task-1-provenance.log"
    [ -z "$output" ]
}

# §6.8 M5 (code-reviewer C1): plan dirs are tracked, so every worktree cut from a
# commit that carries the plan has the task dir. Only a branch that carries plan
# commits ROOT lacks shows the task is being worked there.

@test "C1: a detached linked worktree holding the task → main gets the CHECKPOINT, stdout empty" {
    _main_and_worktree
    git -C "$MAIN" worktree add -q --detach "$BATS_TMP/tool-wt"
    git -C "$MAIN" worktree remove "$WT"
    cd "$MAIN"
    _run_with_cwd "$MAIN"
    [ "$status" -eq 0 ]
    grep -q 'CHECKPOINT — ActiveStep' "$MAIN/.claude/dev/active/task-1/task-1-provenance.log"
    [ -z "$output" ]
}

@test "C1: a linked worktree on a branch with no plan commits ahead → main gets the CHECKPOINT" {
    _main_and_worktree
    cd "$MAIN"
    _run_with_cwd "$MAIN"
    [ "$status" -eq 0 ]
    grep -q 'CHECKPOINT — ActiveStep' "$MAIN/.claude/dev/active/task-1/task-1-provenance.log"
    [ -z "$output" ]
}

@test "C1: two branches carry plan commits → main untouched, both worktrees named" {
    _main_and_worktree
    WT2="$MAIN/.worktrees/y"
    git -C "$MAIN" worktree add -q -b y "$WT2"
    _plan_commit "$WT"
    _plan_commit "$WT2"
    cd "$MAIN"
    _run_with_cwd "$MAIN"
    [ "$status" -eq 0 ]
    [ -z "$(git -C "$MAIN" status --porcelain)" ]
    printf '%s' "$output" | jq -e --arg a "$WT" --arg b "$WT2" '.systemMessage | contains($a) and contains($b)' >/dev/null
}

@test "W2: no stdin, pwd = main checkout with a worked linked worktree → main still untouched" {
    _main_and_worktree
    _plan_commit "$WT"
    cd "$MAIN"
    HOME="$BATS_TMP_HOME" run bash -c "bash '$HOOK' 2>/dev/null </dev/null"
    [ "$status" -eq 0 ]
    [ -z "$(git -C "$MAIN" status --porcelain)" ]
    printf '%s' "$output" | jq -e --arg w "$WT" '.systemMessage | contains($w)' >/dev/null
}

@test "W3: stdin left open with no data → exit 0 after the read timeout, hooks.log says so" {
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 1 plain
    cd "$BATS_TMP"
    HOME="$BATS_TMP_HOME" run bash -c "sleep 4 | bash '$HOOK' 2>/dev/null"
    [ "$status" -eq 0 ]
    grep -q 'CHECKPOINT — ActiveStep' "$BATS_TMP/.claude/dev/active/task-1/task-1-provenance.log"
    grep -qF 'stdin read' "$BATS_TMP_HOME/.claude/logs/hooks.log"
}

@test "W6: a repo whose core.worktree points at another project → that project is never written" {
    VICTIM="$BATS_TMP/victim"
    "$FIXTURE" "$VICTIM/.claude/dev/active" 1 plain
    before=$(sha256sum < "$VICTIM/.claude/dev/active/task-1/task-1-provenance.log")
    mkdir -p "$BATS_TMP/tarball/sub"
    git init -q "$BATS_TMP/tarball"
    git -C "$BATS_TMP/tarball" config core.worktree "$VICTIM"
    cd "$BATS_TMP/tarball/sub"
    _run_with_cwd "$BATS_TMP/tarball/sub"
    [ "$status" -eq 0 ]
    [ "$(sha256sum < "$VICTIM/.claude/dev/active/task-1/task-1-provenance.log")" = "$before" ]
    grep -qF 'outside' "$BATS_TMP_HOME/.claude/logs/hooks.log"
}
