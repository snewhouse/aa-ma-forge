#!/usr/bin/env bash
# build_active_dir.sh — fixture builder for AA-MA hook tests
#
# Produces a mock .claude/dev/active/ layout with N task directories, each
# containing the 5 standard AA-MA files. Used by bats tests to exercise the
# parser helper and the shipped hooks without touching a real project.
#
# Usage:
#   build_active_dir <target_dir> <task_count> [status_format] [mtime_offsets] [active_ms] [--with-git]
#
# Arguments:
#   target_dir      Directory to populate (created if missing). Task dirs land
#                   as <target_dir>/task-1/, task-2/, ..., task-N/.
#   task_count      Integer >= 1. Number of task dirs to create.
#   status_format   plain (default) | bold | mixed
#                   - plain : `- Status: PENDING`
#                   - bold  : `- **Status:** PENDING`
#                   - mixed : alternates bold/plain across milestones, starting bold
#   mtime_offsets   Comma-separated integer seconds offsets from now (negative = past).
#                   Empty (default) = no mtime manipulation.
#                   Must either be empty or match task_count.
#                   Applied to the <task>-tasks.md file of each task dir via `touch -d`.
#   active_ms       1-based milestone index to mark ACTIVE (others PENDING).
#                   Default: 1. Only one milestone is emitted per fixture task;
#                   this selects its Status value (ACTIVE if matches, PENDING otherwise).
#   --with-git      Initialize a git repo in target_dir and commit the fixture.

set -euo pipefail

die() { printf 'build_active_dir: %s\n' "$*" >&2; exit 1; }

# ---- argument parsing -----------------------------------------------------

WITH_GIT=0
POSITIONAL=()
while [ "$#" -gt 0 ]; do
    case "$1" in
        --with-git) WITH_GIT=1; shift ;;
        --) shift; while [ "$#" -gt 0 ]; do POSITIONAL+=("$1"); shift; done ;;
        --*) die "unknown flag: $1" ;;
        *)   POSITIONAL+=("$1"); shift ;;
    esac
done

[ "${#POSITIONAL[@]}" -ge 2 ] || die "usage: build_active_dir <target_dir> <task_count> [status_format] [mtime_offsets] [active_ms] [--with-git]"

TARGET_DIR="${POSITIONAL[0]}"
TASK_COUNT="${POSITIONAL[1]}"
STATUS_FORMAT="${POSITIONAL[2]:-plain}"
MTIME_OFFSETS="${POSITIONAL[3]:-}"
ACTIVE_MS="${POSITIONAL[4]:-1}"

case "$TASK_COUNT" in
    ''|*[!0-9]*) die "task_count must be a non-negative integer, got: $TASK_COUNT" ;;
esac
[ "$TASK_COUNT" -ge 1 ] || die "task_count must be >= 1"

case "$STATUS_FORMAT" in
    plain|bold|mixed) ;;
    *) die "status_format must be plain|bold|mixed, got: $STATUS_FORMAT" ;;
esac

case "$ACTIVE_MS" in
    ''|*[!0-9]*) die "active_ms must be a positive integer" ;;
esac
[ "$ACTIVE_MS" -ge 1 ] || die "active_ms must be >= 1"

# Parse mtime_offsets into an array (bash 4+ indexed array)
MTIME_ARRAY=()
if [ -n "$MTIME_OFFSETS" ]; then
    IFS=',' read -ra MTIME_ARRAY <<< "$MTIME_OFFSETS"
    [ "${#MTIME_ARRAY[@]}" -eq "$TASK_COUNT" ] \
        || die "mtime_offsets count (${#MTIME_ARRAY[@]}) must match task_count ($TASK_COUNT)"
fi

# ---- format helpers -------------------------------------------------------

# emit_status <format> <value> — emits the "- Status: VALUE" bullet line
emit_status() {
    local fmt="$1" val="$2"
    case "$fmt" in
        bold)  printf -- '- **Status:** %s\n' "$val" ;;
        plain) printf -- '- Status: %s\n' "$val" ;;
    esac
}

# resolve_format_for_task <task_index_0based>
resolve_format_for_task() {
    local idx="$1"
    case "$STATUS_FORMAT" in
        plain) printf 'plain' ;;
        bold)  printf 'bold' ;;
        mixed) if [ $(( idx % 2 )) -eq 0 ]; then printf 'bold'; else printf 'plain'; fi ;;
    esac
}

# ---- directory creation ---------------------------------------------------

mkdir -p "$TARGET_DIR"

ts_iso() { date -u +%Y-%m-%dT%H:%M:%SZ; }

for i in $(seq 1 "$TASK_COUNT"); do
    idx0=$((i - 1))
    task_name="task-$i"
    task_dir="$TARGET_DIR/$task_name"
    mkdir -p "$task_dir"

    fmt=$(resolve_format_for_task "$idx0")
    # Active marker applies to milestone 1 if active_ms==1, else PENDING for all milestones
    if [ "$ACTIVE_MS" -eq 1 ]; then
        status_val="ACTIVE"
    else
        status_val="PENDING"
    fi

    # -------- tasks.md --------
    {
        printf '# %s Tasks (HTP)\n\n' "$task_name"
        printf '## Milestone 1: Foundation\n'
        emit_status "$fmt" "$status_val"
        printf -- '- Dependencies: None\n'
        printf -- '- Gate: SOFT\n'
        printf -- '- Acceptance Criteria:\n'
        printf -- '  - Fixture milestone exists.\n\n'
        printf '### Step 1.1: Initial step\n'
        emit_status "$fmt" "PENDING"
        printf -- '- Mode: AFK\n'
        printf -- '- Result Log:\n'
    } > "$task_dir/${task_name}-tasks.md"

    # -------- plan.md --------
    {
        printf '# %s Plan\n\n' "$task_name"
        printf '**Objective:** Fixture plan for %s.\n\n' "$task_name"
        printf '## Executive Summary\nFixture plan stub.\n'
    } > "$task_dir/${task_name}-plan.md"

    # -------- reference.md --------
    {
        printf '# %s Reference\n\n' "$task_name"
        printf '## Immutable Facts\n- Fixture task [valid: %s]\n' "$(ts_iso)"
    } > "$task_dir/${task_name}-reference.md"

    # -------- context-log.md --------
    {
        printf '# %s Context Log\n\n' "$task_name"
        printf '## %s Fixture init\nFixture context entry.\n' "$(ts_iso)"
    } > "$task_dir/${task_name}-context-log.md"

    # -------- provenance.log --------
    printf '[%s] Fixture initialized for %s\n' "$(ts_iso)" "$task_name" \
        > "$task_dir/${task_name}-provenance.log"

    # -------- apply mtime offset to tasks.md if requested --------
    if [ "${#MTIME_ARRAY[@]}" -gt 0 ]; then
        offset="${MTIME_ARRAY[$idx0]}"
        case "$offset" in
            ''|*[!0-9-]*) die "mtime offset must be an integer, got: $offset" ;;
        esac
        target_epoch=$(( $(date +%s) + offset ))
        # touch -d requires a date string; use POSIX-portable @epoch form
        touch -d "@${target_epoch}" "$task_dir/${task_name}-tasks.md"
    fi
done

# ---- optional git init ----------------------------------------------------

if [ "$WITH_GIT" -eq 1 ]; then
    (
        cd "$TARGET_DIR"
        if [ ! -d .git ]; then
            git init -q
            git -c user.email=fixture@example.invalid \
                -c user.name=fixture \
                -c commit.gpgsign=false \
                add -A
            git -c user.email=fixture@example.invalid \
                -c user.name=fixture \
                -c commit.gpgsign=false \
                commit -q -m "initial fixture state"
        fi
    )
fi
