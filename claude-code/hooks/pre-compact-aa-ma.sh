#!/usr/bin/env bash
# Event: PreCompact
# Mode: Advisory — never blocks compaction
# Exit: 0 always
# Fail-open: a failed audit-trail append is logged to hooks.log, counted, and reported in one systemMessage; helper missing → systemMessage
#
# PreCompact hook: snapshot AA-MA state before auto-compaction.
#
# Iterates ALL active task dirs (project-local .claude/dev/active/ first, then
# $HOME/.claude/dev/active/, with project-first collision resolution) via the
# shared aa-ma-parse helper. For each task, writes a snapshot file to
# $HOME/.claude/hooks/cache/compaction-snapshots/ and appends checkpoint
# entries to the task's provenance.log and context-log.md.
#
# Honours AA_MA_HOOKS_DISABLE=1 (master kill switch). Always exits 0.

set -euo pipefail

# Resolve helper across two layouts (project subdir OR installed sibling).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "${SCRIPT_DIR}/lib/aa-ma-parse.sh" ]; then
    HELPER="${SCRIPT_DIR}/lib/aa-ma-parse.sh"
elif [ -f "${SCRIPT_DIR}/aa-ma-parse.sh" ]; then
    HELPER="${SCRIPT_DIR}/aa-ma-parse.sh"
else
    printf 'pre-compact-aa-ma: cannot find aa-ma-parse.sh helper\n' >&2
    # why: stderr on exit 0 reaches only the debug log; systemMessage is shown to the user.
    printf '{"systemMessage":"pre-compact-aa-ma: helper aa-ma-parse.sh not found; AA-MA snapshot skipped"}\n'
    exit 0  # PreCompact must never block compaction
fi
# shellcheck source=lib/aa-ma-parse.sh
# shellcheck disable=SC1090,SC1091
. "$HELPER"

HOOK=pre-compact-aa-ma   # log name in hooks.log (aa-ma-log.sh; compaction.log folded in at M7.3)

# HOME unset (cron, env -i): no snapshot home, and set -u would abort; never write to a shared /tmp.
if [ -z "${HOME:-}" ]; then
    fail_open_notice "$HOOK" "HOME is not set; AA-MA snapshot skipped"
    exit 0   # PreCompact must never block compaction
fi
SNAPSHOT_DIR="$HOME/.claude/hooks/cache/compaction-snapshots"

# POSIX date format (cross-platform; works on both GNU and BSD date).
ts() { date -u +%Y-%m-%dT%H:%M:%SZ; }

mkdir -p "$SNAPSHOT_DIR" 2>/dev/null || {   # why: the notice below replaces mkdir's message
    fail_open_notice "$HOOK" "cannot create ${SNAPSHOT_DIR/#"$HOME"/\~}; AA-MA snapshot skipped"
    exit 0   # PreCompact must never block compaction
}

# Audit-trail append failures, reported once at exit (see end of file).
append_failures=0

# warn_append <what> <file> — record one failed append in hooks.log and count it.
# log_warn never fails, so this cannot abort compaction under set -e.
warn_append() {
    log_warn "$HOOK" "could not append $1 to $2"
    append_failures=$((append_failures + 1))
}

# Master kill switch honoured.
if aa_ma_is_disabled; then
    log_info "$HOOK" "disabled via AA_MA_HOOKS_DISABLE=1"
    exit 0
fi

# Collect all active task dirs (project-first, mtime-sorted, collision-resolved).
mapfile -t TASKS < <(aa_ma_list_active_tasks)

if [ "${#TASKS[@]}" -eq 0 ]; then
    log_info "$HOOK" "no active AA-MA tasks"
    exit 0
fi

for task_dir in "${TASKS[@]}"; do
    task_name=$(basename "$task_dir")
    snapshot_file="${SNAPSHOT_DIR}/${task_name}-snapshot.md"

    {
        printf '# AA-MA Compaction Snapshot: %s\n' "$task_name"
        printf '**Captured:** %s\n\n' "$(ts)"

        if [ -f "${task_dir}/${task_name}-tasks.md" ]; then
            printf '## Task Status\n'
            grep -E '(Milestone|Status|COMPLETE|IN.PROGRESS|PENDING|\[x\]|\[ \])' \
                "${task_dir}/${task_name}-tasks.md" 2>/dev/null | head -30 || true
            printf '\n'
        fi

        if [ -f "${task_dir}/${task_name}-reference.md" ]; then
            printf '## Reference (Full)\n'
            cat "${task_dir}/${task_name}-reference.md"
            printf '\n'
        fi

        if [ -f "${task_dir}/${task_name}-context-log.md" ]; then
            printf '## Context Log (Last 20 Lines)\n'
            tail -20 "${task_dir}/${task_name}-context-log.md"
            printf '\n'
        fi

        if [ -f "${task_dir}/${task_name}-provenance.log" ]; then
            printf '## Provenance (Last 10 Lines)\n'
            tail -10 "${task_dir}/${task_name}-provenance.log"
            printf '\n'
        fi
    } > "$snapshot_file"

    log_info "$HOOK" "snapshot saved: $task_name"

    # Best-effort: extract active step for CHECKPOINT entry.
    active_step="unknown"
    if [ -f "${task_dir}/${task_name}-tasks.md" ]; then
        s=$(aa_ma_extract_active_step "${task_dir}/${task_name}-tasks.md")
        [ -n "$s" ] && active_step="$s"
    fi

    prov_file="${task_dir}/${task_name}-provenance.log"
    ctx_file="${task_dir}/${task_name}-context-log.md"

    # Fail-open (compaction must proceed) but never silently: each lost audit-trail
    # entry is named in hooks.log and counted for the user-visible message at exit.
    if [ -f "$prov_file" ]; then
        # shellcheck disable=SC2310  # why: fail-open by design — set -e is meant to be off here; a failed append is counted, not fatal
        {
            printf '[%s] Context compacted — Snapshot saved, active step: %s\n' \
                "$(ts)" "$active_step"
            printf '[%s] CHECKPOINT — ActiveStep: %s — NextAction: "Resume from active step" — ContextLoaded: REFERENCE,TASKS — TokenUsage: N/A\n' \
                "$(ts)" "$active_step"
        } 2>/dev/null >> "$prov_file" || warn_append checkpoint "$prov_file"
    fi

    # context-log.md is committed (often to a public repo): name the snapshot as ~/…, never
    # the absolute home path, which carries the username.
    snapshot_shown="$snapshot_file"
    # shellcheck disable=SC2088  # why: a literal "~" is the point — it is text for a reader, not a path to expand
    [[ "$snapshot_shown" == "$HOME"/* ]] && snapshot_shown="~/${snapshot_shown#"$HOME"/}"

    if [ -f "$ctx_file" ]; then
        # shellcheck disable=SC2310  # why: fail-open by design — set -e is meant to be off here; a failed append is counted, not fatal
        {
            printf '\n## [%s] Compaction Summary (auto-generated by hook)\n' "$(ts)"
            printf -- '- Active step at compaction: %s\n' "$active_step"
            printf -- '- Snapshot saved to: %s\n' "$snapshot_shown"
            printf -- '- Note: Context compacted. Reload AA-MA files to resume.\n'
        } 2>/dev/null >> "$ctx_file" || warn_append "compaction summary" "$ctx_file"
    fi
done

# Hook stderr on exit 0 reaches only the debug log (code.claude.com/docs/en/hooks), so a
# systemMessage is the one channel the user actually sees; the paths are in hooks.log.
if [ "$append_failures" -gt 0 ]; then
    fail_open_notice "$HOOK" "$append_failures audit-trail append(s) failed; see ~/.claude/logs/hooks.log"
fi

exit 0
