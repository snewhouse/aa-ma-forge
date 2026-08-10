#!/usr/bin/env bats
# aa-ma-parse.bats — tests for claude-code/hooks/lib/aa-ma-parse.sh

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
    export BATS_TMP BATS_TMP_HOME
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

@test "aa_ma_debug emits [aa-ma-debug] prefix when HOOK_DEBUG=1" {
    load_helper
    HOOK_DEBUG=1
    run aa_ma_debug "hello"
    [ "$status" -eq 0 ]
    [[ "$output" == *"[aa-ma-debug] hello"* ]]
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
    ! [[ "${tasks[0]}" == "$BATS_TMP_HOME"* ]]
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
    printf '%s' "$header" | grep -qF "aa_ma_extract_milestone_block"
    # And a symbol that is definitely absent must be detected as absent.
    ! printf '%s' "$header" | grep -qF "aa_ma_definitely_not_a_real_symbol"
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
