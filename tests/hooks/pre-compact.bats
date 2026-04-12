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
