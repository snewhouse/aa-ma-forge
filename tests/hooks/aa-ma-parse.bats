#!/usr/bin/env bats
# aa-ma-parse.bats — tests for claude-code/hooks/lib/aa-ma-parse.sh

bats_require_minimum_version 1.5.0

setup() {
    REPO_ROOT="$(cd "${BATS_TEST_DIRNAME}/.." && pwd)"
    HELPER="$REPO_ROOT/../claude-code/hooks/lib/aa-ma-parse.sh"
    if [ ! -f "$HELPER" ]; then
        # Fallback when tests/ is inside repo root (expected layout)
        HELPER="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)/claude-code/hooks/lib/aa-ma-parse.sh"
    fi
    FIXTURE="${BATS_TEST_DIRNAME}/fixtures/build_active_dir.sh"
    BATS_TMP="$(mktemp -d)"
    BATS_TMP_HOME="$(mktemp -d)"
    # why: aa_ma_debug writes through log_debug (M7.1); never touch the real hooks.log
    CLAUDE_HOOK_LOG="$BATS_TMP/hooks.log"
    export BATS_TMP BATS_TMP_HOME CLAUDE_HOOK_LOG
}

teardown() {
    [ -n "${BATS_TMP:-}" ] && rm -rf "$BATS_TMP"
    [ -n "${BATS_TMP_HOME:-}" ] && rm -rf "$BATS_TMP_HOME"
    unset AA_MA_HOOKS_DISABLE HOOK_DEBUG AA_MA_PARSE_SH_LOADED 2>/dev/null || true
}

load_helper() {
    # shellcheck disable=SC1090
    . "$HELPER"
}

@test "aa_ma_is_disabled returns non-zero when env unset" {
    load_helper
    unset AA_MA_HOOKS_DISABLE
    run aa_ma_is_disabled
    [ "$status" -ne 0 ]
}

@test "aa_ma_is_disabled returns 0 when AA_MA_HOOKS_DISABLE=1" {
    load_helper
    AA_MA_HOOKS_DISABLE=1
    run aa_ma_is_disabled
    [ "$status" -eq 0 ]
}

@test "aa_ma_is_disabled treats AA_MA_HOOKS_DISABLE=0 as not-disabled" {
    load_helper
    AA_MA_HOOKS_DISABLE=0
    run aa_ma_is_disabled
    [ "$status" -ne 0 ]
}

@test "aa_ma_debug silent when HOOK_DEBUG unset" {
    load_helper
    unset HOOK_DEBUG
    run aa_ma_debug "should not appear"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "aa_ma_debug emits a hooks.log-format DEBUG line when HOOK_DEBUG=1" {
    load_helper
    HOOK_DEBUG=1
    run aa_ma_debug "hello"
    [ "$status" -eq 0 ]
    [[ "$output" =~ ' DEBUG '.+': hello'$ ]]
    grep -q ': hello$' "$CLAUDE_HOOK_LOG"
}

@test "aa_ma_extract_active_milestone finds bold-format Status: ACTIVE" {
    "$FIXTURE" "$BATS_TMP" 1 bold
    load_helper
    result=$(aa_ma_extract_active_milestone "$BATS_TMP/task-1/task-1-tasks.md")
    [ "$result" = "Milestone 1: Foundation" ]
}

@test "aa_ma_extract_active_milestone finds plain-format Status: ACTIVE" {
    "$FIXTURE" "$BATS_TMP" 1 plain
    load_helper
    result=$(aa_ma_extract_active_milestone "$BATS_TMP/task-1/task-1-tasks.md")
    [ "$result" = "Milestone 1: Foundation" ]
}

@test "aa_ma_extract_active_milestone handles mixed format in multi-task fixture" {
    "$FIXTURE" "$BATS_TMP" 2 mixed
    load_helper
    bold_result=$(aa_ma_extract_active_milestone "$BATS_TMP/task-1/task-1-tasks.md")
    plain_result=$(aa_ma_extract_active_milestone "$BATS_TMP/task-2/task-2-tasks.md")
    [ "$bold_result" = "Milestone 1: Foundation" ]
    [ "$plain_result" = "Milestone 1: Foundation" ]
}

@test "aa_ma_extract_active_milestone returns empty for empty file" {
    empty_file="$BATS_TMP/empty.md"
    : > "$empty_file"
    load_helper
    result=$(aa_ma_extract_active_milestone "$empty_file")
    [ -z "$result" ]
}

@test "aa_ma_extract_active_step finds first PENDING step via fallback" {
    "$FIXTURE" "$BATS_TMP" 1 plain
    load_helper
    # Fixture has milestone ACTIVE but step PENDING → PENDING fallback
    result=$(aa_ma_extract_active_step "$BATS_TMP/task-1/task-1-tasks.md")
    [ "$result" = "Step 1.1: Initial step" ]
}

@test "HTML-comment false-positive guard: commented Status: ACTIVE ignored" {
    cat > "$BATS_TMP/html.md" <<'EOF'
## Milestone 1: Guard Test
<!-- Status: ACTIVE -->
- Status: PENDING
EOF
    load_helper
    # Should detect PENDING (fallback), NOT ACTIVE from the HTML comment
    result=$(aa_ma_extract_active_milestone "$BATS_TMP/html.md")
    [ "$result" = "Milestone 1: Guard Test" ]
}

@test "aa_ma_list_active_tasks sorts by mtime (newest first)" {
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 3 plain "-200,-100,0"
    load_helper
    cd "$BATS_TMP"
    mapfile -t tasks < <(aa_ma_list_active_tasks)
    [ "${#tasks[@]}" -eq 3 ]
    # task-3 has offset 0 (newest), task-1 has offset -200 (oldest)
    [[ "${tasks[0]}" == *"/task-3" ]]
    [[ "${tasks[1]}" == *"/task-2" ]]
    [[ "${tasks[2]}" == *"/task-1" ]]
}

@test "aa_ma_list_active_tasks applies project-first collision rule" {
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 1 plain
    "$FIXTURE" "$BATS_TMP_HOME/.claude/dev/active" 1 plain
    load_helper
    cd "$BATS_TMP"
    HOME="$BATS_TMP_HOME"
    export HOME
    mapfile -t tasks < <(aa_ma_list_active_tasks)
    [ "${#tasks[@]}" -eq 1 ]
    [[ "${tasks[0]}" == "$BATS_TMP"* ]]
    [[ "${tasks[0]}" != "$BATS_TMP_HOME"* ]]
}

@test "aa_ma_list_active_tasks merges non-colliding tasks from both paths" {
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 1 plain
    # Create a differently-named task in fake HOME
    fake_home_active="$BATS_TMP_HOME/.claude/dev/active/home-only-task"
    mkdir -p "$fake_home_active"
    touch "$fake_home_active/home-only-task-tasks.md"

    load_helper
    cd "$BATS_TMP"
    HOME="$BATS_TMP_HOME"
    export HOME
    mapfile -t tasks < <(aa_ma_list_active_tasks)
    [ "${#tasks[@]}" -eq 2 ]
}

@test "aa_ma_list_active_tasks <root> lists <root>/.claude/dev/active, not \$PWD's (sole-dev-merge-fixes M5)" {
    "$FIXTURE" "$BATS_TMP/root/.claude/dev/active" 1 plain
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 2 plain
    load_helper
    cd "$BATS_TMP"
    HOME="$BATS_TMP_HOME"
    export HOME
    mapfile -t tasks < <(aa_ma_list_active_tasks "$BATS_TMP/root")
    [ "${#tasks[@]}" -eq 1 ]
    [ "${tasks[0]}" = "$BATS_TMP/root/.claude/dev/active/task-1" ]
}

@test "aa_ma_list_active_tasks skips a task dir whose name holds a control character, and logs it" {
    # A name like $'x\n0\t..' would otherwise print `..` as a task path (live run 1, Stage D).
    mkdir -p "$BATS_TMP/.claude/dev/active/x"$'\n'"0"$'\t'".."
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 1 plain
    load_helper
    cd "$BATS_TMP"
    HOME="$BATS_TMP_HOME"
    export HOME
    mapfile -t tasks < <(aa_ma_list_active_tasks)
    [ "${#tasks[@]}" -eq 1 ]
    [ "${tasks[0]}" = "$BATS_TMP/.claude/dev/active/task-1" ]
    grep -qF 'control character' "$CLAUDE_HOOK_LOG"
}

@test "aa_ma_list_active_tasks skips names that END in a newline (\$(basename) would strip it)" {
    mkdir -p "$BATS_TMP/.claude/dev/active/"$'\n' "$BATS_TMP/.claude/dev/active/evil"$'\n'
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 1 plain
    load_helper
    cd "$BATS_TMP"
    HOME="$BATS_TMP_HOME"
    export HOME
    mapfile -t tasks < <(aa_ma_list_active_tasks)
    [ "${#tasks[@]}" -eq 1 ]
    [ "${tasks[0]}" = "$BATS_TMP/.claude/dev/active/task-1" ]
    [ "$(grep -cF 'control character' "$CLAUDE_HOOK_LOG")" -eq 2 ]
}

@test "aa_ma_list_active_tasks emits nothing when no task dirs exist" {
    load_helper
    cd "$BATS_TMP"
    HOME="$BATS_TMP_HOME"
    export HOME
    run aa_ma_list_active_tasks
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "aa_ma_list_active_tasks uses alphabetical tiebreak when mtimes equal" {
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 3 plain "0,0,0"
    load_helper
    cd "$BATS_TMP"
    mapfile -t tasks < <(aa_ma_list_active_tasks)
    [ "${#tasks[@]}" -eq 3 ]
    # All mtimes equal → alphabetical ascending (task-1, task-2, task-3)
    [[ "${tasks[0]}" == *"/task-1" ]]
    [[ "${tasks[1]}" == *"/task-2" ]]
    [[ "${tasks[2]}" == *"/task-3" ]]
}

@test "aa_ma_extract_active_milestone reads an em-dash milestone heading" {
    # milestone-grammar-ssot M1 Sub-step 1.8. The Python grammar was widened to
    # accept `## Milestone N — Title`; this pins that the bash/awk helper already
    # did, so a future tightening cannot silently regress it.
    #
    # Deliberately does NOT pin the helper's over-tolerance (it treats any `^## `
    # heading, e.g. `## Status: COMPLETE`, as a milestone). That is a known wart,
    # not a contract — pinning it would block a future correctness fix.
    load_helper
    local tasks="$BATS_TMP/em-dash-tasks.md"
    cat > "$tasks" <<'EOF'
## Milestone 1 — Pre-flight + scope-aware CI checks

- Status: ACTIVE

### Sub-step 1.1: Something

- Status: PENDING
EOF
    run aa_ma_extract_active_milestone "$tasks"
    [ "$status" -eq 0 ]
    [ "$output" = "Milestone 1 — Pre-flight + scope-aware CI checks" ]
}

@test "every public symbol is listed in the Exports header" {
    # The header is the discovery surface — the first thing anyone sourcing this
    # library reads. A symbol missing from it gets reimplemented rather than
    # reused, which is how this repo ended up with six milestone grammars.
    # M4 added two functions and a constant and did not update the header.
    HELPER_SRC="$HELPER"
    header=$(awk '/^# Exports:/{f=1;next} /^#$/{if(f)exit} f' "$HELPER_SRC")
    missing=""
    while read -r sym; do
        [ -n "$sym" ] || continue
        printf '%s' "$header" | grep -qF "$sym" || missing="$missing $sym"
    done <<< "$(grep -oE '^(aa_ma_[a-z_]+)\(\)' "$HELPER_SRC" | sed 's/()//'
               grep -oE '^AA_MA_[A-Z_]+=' "$HELPER_SRC" | sed 's/=//')"
    [ -z "$missing" ] || { echo "not in Exports header:$missing" >&2; false; }
}

@test "the Exports-header check is not vacuous" {
    # If the header scrape returned empty, the test above passes for free.
    header=$(awk '/^# Exports:/{f=1;next} /^#$/{if(f)exit} f' "$HELPER")
    [ -n "$header" ]
    printf '%s' "$header" | grep -qF "aa_ma_gate"
    # And a symbol that is definitely absent must be detected as absent.
    run ! grep -qF "aa_ma_definitely_not_a_real_symbol" <<< "$header"
}

# ---------------------------------------------------------------------------
# aa_ma_extract_active_step — a sub-step block must end at the next H2
#
# The extractor opened a block on /^### / and never closed it, so the first
# Status line after milestone N's last sub-step is milestone N+1's OWN
# milestone-level status — and it was attributed to that trailing sub-step.
#
# Not hypothetical and not display-only: pre-compact-aa-ma.sh feeds this into
# the `CHECKPOINT — ActiveStep:` line in provenance.log, which rules/aa-ma.md
# designates as the session-resume signal. This repo's own log recorded
# "Sub-step 2.4" and later "Sub-step 3.6" — in both cases the last sub-step of
# the milestone BEFORE the one actually being worked on.
# ---------------------------------------------------------------------------

write_two_milestone_fixture() {
    cat > "$BATS_TMP/steps.md" <<'EOF'
## Milestone 1: Finished milestone

- Status: COMPLETE

### Sub-step 1.1: Done early

- Status: COMPLETE

### Sub-step 1.2: Last step of M1

- Status: COMPLETE

## Milestone 2: The one being worked on

- Status: ACTIVE

### Sub-step 2.1: The real next step

- Status: PENDING
EOF
}

@test "a milestone-level ACTIVE is not attributed to the previous milestone's last step" {
    write_two_milestone_fixture
    load_helper
    result=$(aa_ma_extract_active_step "$BATS_TMP/steps.md")
    [ "$result" != "Sub-step 1.2: Last step of M1" ]
    [ "$result" = "Sub-step 2.1: The real next step" ]
}

@test "an ACTIVE sub-step still wins over the PENDING fallback" {
    write_two_milestone_fixture
    # Promote 2.1 to ACTIVE; it must be returned on its own merits.
    sed -i 's/^- Status: PENDING$/- Status: ACTIVE/' "$BATS_TMP/steps.md"
    load_helper
    result=$(aa_ma_extract_active_step "$BATS_TMP/steps.md")
    [ "$result" = "Sub-step 2.1: The real next step" ]
}

@test "a trailing prose H2 cannot become the active step" {
    cat > "$BATS_TMP/prose.md" <<'EOF'
## Milestone 1: All done

- Status: COMPLETE

### Sub-step 1.1: Done

- Status: COMPLETE

## Summary Counts

- Status: PENDING
EOF
    load_helper
    result=$(aa_ma_extract_active_step "$BATS_TMP/prose.md")
    [ -z "$result" ]
}

@test "aa_ma_debug_cmd logs a command's length and first word only, never its arguments (M7 §6.8)" {
    . "$HELPER"
    for cmd in 'curl -u admin:hunter2 https://x' 'mysql -phunter2 db' 'sshpass -p hunter2 ssh h'; do
        HOOK_DEBUG=1 aa_ma_debug_cmd "probe" "$cmd" 2>/dev/null
        grep -qF "probe (${#cmd} chars, first word '${cmd%% *}')" "$CLAUDE_HOOK_LOG"
    done
    run ! grep -qF hunter2 "$CLAUDE_HOOK_LOG"
}

@test "no hook passes a raw command to aa_ma_debug (M7 §6.8)" {
    run git -C "$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)" grep -nE 'aa_ma_debug .*[$][{]?cmd\b' -- ':(glob)claude-code/hooks/*.sh'   # top-level hooks; lib/ holds the capped helper
    [ "$status" -eq 1 ]
}

@test "aa_ma_debug_cmd skips leading NAME=value words: an env prefix is never logged (double-check F1)" {
    . "$HELPER"
    c="AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMIK7MDENG FOO=bar aws s3 ls"
    HOOK_DEBUG=1 aa_ma_debug_cmd p "$c" 2>/dev/null
    HOOK_DEBUG=1 aa_ma_debug_cmd q "  A=1 B=2" 2>/dev/null
    grep -qF "p (${#c} chars, first word 'aws')" "$CLAUDE_HOOK_LOG"
    grep -qF "q (9 chars, first word '')" "$CLAUDE_HOOK_LOG"
    run ! grep -qF wJalr "$CLAUDE_HOOK_LOG"
}

@test "aa_ma_debug_cmd: a quoted env value with a space never leaks; only a plain program name is logged (sole-dev-merge C1 MEDIUM)" {
    . "$HELPER"
    HOOK_DEBUG=1 aa_ma_debug_cmd a "PGPASSWORD='abc hunter2' psql -h db" 2>/dev/null
    HOOK_DEBUG=1 aa_ma_debug_cmd b 'PASSWORD="x topsecret" git log' 2>/dev/null
    HOOK_DEBUG=1 aa_ma_debug_cmd c "/usr/bin/git status" 2>/dev/null
    grep -qF "a (" "$CLAUDE_HOOK_LOG"
    grep -qF "first word '?'" "$CLAUDE_HOOK_LOG"
    grep -qF "c (19 chars, first word '/usr/bin/git')" "$CLAUDE_HOOK_LOG"
    run ! grep -qE "hunter2|topsecret" "$CLAUDE_HOOK_LOG"
}

@test "aa_ma_debug_cmd never truncates a first word: a long one (e.g. a pasted token) becomes '?' (security notice)" {
    . "$HELPER"
    gh="ghp_$(printf 'a%.0s' {1..36})"; ant="sk-ant-api03-$(printf 'B%.0s' {1..40})"
    HOOK_DEBUG=1 aa_ma_debug_cmd p "$gh push" 2>/dev/null
    HOOK_DEBUG=1 aa_ma_debug_cmd q "$ant" 2>/dev/null
    [ "$(grep -c "first word '?'" "$CLAUDE_HOOK_LOG")" -eq 2 ]
    run ! grep -qE 'ghp_a|sk-ant' "$CLAUDE_HOOK_LOG"
}

# ---------------------------------------------------------------------------
# aa_ma_cochange_partners (§6.6 W2): the one shell co_changes reader at the T7 constants.
# rc 0 ok | 2 usage | 3 no index | 4 no codemem binary (or no timeout(1)) | 5 codemem failed
# or printed no JSON | 6 timed out.
# ---------------------------------------------------------------------------

# _cm_stub <json-or-text> [sleep-s] [exit-rc]: an index file + a CODEMEM_BIN that records argv.
_cm_stub() {
    mkdir -p "$BATS_TMP/cm"
    : > "$BATS_TMP/cm/index.db"
    printf '%s\n' "$1" > "$BATS_TMP/cm.out"
    cat > "$BATS_TMP/codemem" <<STUB
#!/usr/bin/env bash
printf '%s\n' "\$@" > "$BATS_TMP/codemem.args"
sleep ${2:-0}
cat "$BATS_TMP/cm.out"
exit ${3:-0}
STUB
    chmod +x "$BATS_TMP/codemem"
    export CODEMEM_DB="$BATS_TMP/cm/index.db" CODEMEM_BIN="$BATS_TMP/codemem"
}

CM_MULTI='{"a.py": {"files": [{"path": "z.py"}, {"path": "b.py"}]}, "c.py": {"files": [{"path": "b.py"}]}}'

@test "aa_ma_cochange_partners: several paths → partners sorted, unique, at the T7 constants" {
    load_helper
    _cm_stub "$CM_MULTI"
    run aa_ma_cochange_partners "$BATS_TMP" "$BATS_TMP" 5 -- a.py c.py
    [ "$status" -eq 0 ]
    [ "$output" = $'b.py\nz.py' ]
    run cat "$BATS_TMP/codemem.args"
    [[ "$output" == *$'query\nco_changes\n--repo-root\n'"$BATS_TMP"$'\n--threshold\n5\n--min-ratio\n0.5\n--\na.py\nc.py'* ]]
    [ "$AA_MA_COCHANGE_MIN_SHARED" = 5 ]
    [ "$AA_MA_COCHANGE_MIN_RATIO" = 0.5 ]
}

@test "aa_ma_cochange_partners: one path (a bare result object) → its partners" {
    load_helper
    _cm_stub '{"files": [{"path": "q.py"}], "error": null}'
    run aa_ma_cochange_partners "$BATS_TMP" "$BATS_TMP" 5 -- a.py
    [ "$status" -eq 0 ]
    [ "$output" = "q.py" ]
}

@test "aa_ma_cochange_partners: no partners → rc 0, nothing printed" {
    load_helper
    _cm_stub '{"a.py": {"files": []}}'
    run aa_ma_cochange_partners "$BATS_TMP" "$BATS_TMP" 5 -- a.py
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "aa_ma_cochange_partners: no index → rc 3, codemem never run" {
    load_helper
    _cm_stub "$CM_MULTI"
    rm "$BATS_TMP/cm/index.db"
    run aa_ma_cochange_partners "$BATS_TMP" "$BATS_TMP" 5 -- a.py
    [ "$status" -eq 3 ]
    [ -z "$output" ]
    [ ! -e "$BATS_TMP/codemem.args" ]
}

@test "aa_ma_cochange_partners: no codemem binary → rc 4" {
    load_helper
    _cm_stub "$CM_MULTI"
    export CODEMEM_BIN="$BATS_TMP/absent"
    run aa_ma_cochange_partners "$BATS_TMP" "$BATS_TMP" 5 -- a.py
    [ "$status" -eq 4 ]
    [ -z "$output" ]
}

@test "aa_ma_cochange_partners: codemem exits non-zero → rc 5" {
    load_helper
    _cm_stub "$CM_MULTI" 0 3
    run aa_ma_cochange_partners "$BATS_TMP" "$BATS_TMP" 5 -- a.py
    [ "$status" -eq 5 ]
    [ -z "$output" ]
}

@test "aa_ma_cochange_partners: codemem prints no JSON → rc 5" {
    load_helper
    _cm_stub 'not json'
    run aa_ma_cochange_partners "$BATS_TMP" "$BATS_TMP" 5 -- a.py
    [ "$status" -eq 5 ]
    [ -z "$output" ]
}

@test "aa_ma_cochange_partners: codemem slower than the timeout → killed, rc 6" {
    load_helper
    _cm_stub "$CM_MULTI" 10
    SECONDS=0
    run aa_ma_cochange_partners "$BATS_TMP" "$BATS_TMP" 1 -- a.py
    [ "$status" -eq 6 ]
    [ -z "$output" ]
    (( SECONDS < 5 ))
}

@test "aa_ma_cochange_partners: usage errors → rc 2 (no --, no path, bad timeout)" {
    load_helper
    _cm_stub "$CM_MULTI"
    run aa_ma_cochange_partners "$BATS_TMP" "$BATS_TMP" 5 a.py
    [ "$status" -eq 2 ]
    run aa_ma_cochange_partners "$BATS_TMP" "$BATS_TMP" 5 --
    [ "$status" -eq 2 ]
    run aa_ma_cochange_partners "$BATS_TMP" "$BATS_TMP" 1s -- a.py
    [ "$status" -eq 2 ]
}

# ---------------------------------------------------------------------------
# aa_ma_default_base_ref (§6.6 W5): origin/HEAD → origin/main → origin/master → main → master.
# ---------------------------------------------------------------------------

# _base_repo <local-branch>: a one-commit repo on <local-branch>, cwd set to it.
_base_repo() {
    cd "$BATS_TMP"
    git init -q -b "$1"
    git -c user.email=t@e.i -c user.name=t -c commit.gpgsign=false \
        commit -q --allow-empty -m one
}

@test "aa_ma_default_base_ref: origin/HEAD wins" {
    load_helper
    _base_repo main
    git update-ref refs/remotes/origin/trunk HEAD
    git update-ref refs/remotes/origin/main HEAD
    git symbolic-ref refs/remotes/origin/HEAD refs/remotes/origin/trunk
    run aa_ma_default_base_ref
    [ "$status" -eq 0 ]
    [ "$output" = "origin/trunk" ]
}

@test "aa_ma_default_base_ref: no origin/HEAD → origin/main before local main" {
    load_helper
    _base_repo main
    git update-ref refs/remotes/origin/main HEAD
    run aa_ma_default_base_ref
    [ "$status" -eq 0 ]
    [ "$output" = "origin/main" ]
}

@test "aa_ma_default_base_ref: origin/master when there is no origin/main" {
    load_helper
    _base_repo main
    git update-ref refs/remotes/origin/master HEAD
    run aa_ma_default_base_ref
    [ "$output" = "origin/master" ]
}

@test "aa_ma_default_base_ref: no remote → local main, then local master" {
    load_helper
    _base_repo master
    run aa_ma_default_base_ref
    [ "$output" = "master" ]
    git branch main
    run aa_ma_default_base_ref
    [ "$output" = "main" ]
}

@test "aa_ma_default_base_ref: nothing to use → rc 1, nothing printed" {
    load_helper
    _base_repo feature
    run aa_ma_default_base_ref
    [ "$status" -eq 1 ]
    [ -z "$output" ]
}
