#!/usr/bin/env bash
# Event: PreCompact
# Mode: Advisory — never blocks compaction
# Exit: 0 always
# Fail-open: a failed audit-trail append, a task skipped for a symlink, no jq, an unusable stdin cwd or a failed `git worktree list` is logged to hooks.log and reported in one systemMessage; helper missing → systemMessage
#
# PreCompact hook: snapshot AA-MA state before auto-compaction.
#
# Iterates ALL active task dirs (<root>/.claude/dev/active/ first, then
# $HOME/.claude/dev/active/, with project-first collision resolution) via the
# shared aa-ma-parse helper. <root> is the git toplevel of stdin's `cwd`, else
# pwd. For each task, writes a snapshot file to
# $HOME/.claude/hooks/cache/compaction-snapshots/ and appends checkpoint
# entries to the task's provenance.log and context-log.md — except when <root>
# is the main checkout and a linked worktree holds the same task: then nothing
# is appended there, and a systemMessage names the worktree (L-1347).
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

# The AA-MA files this hook reads or appends to, per task. Every file named in
# the loop below must be in this list, so the symlink guard covers it.
readonly AA_MA_FILES=(tasks.md reference.md context-log.md provenance.log)

# Audit-trail append failures and skipped tasks, reported once at exit (see end of file).
append_failures=0
skipped_tasks=0

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

# Notices for the one systemMessage at exit (see end of file).
notices=()

# Project root (global L-1347). A live /compact probe (sole-dev-merge-fixes
# context-log, "PreCompact probe (5.0)") showed stdin `cwd` equals this hook's pwd,
# and with CLAUDE_BASH_MAINTAIN_PROJECT_WORKING_DIR=0 it can be a subdirectory,
# which `$PWD/.claude/dev/active` misses; its git toplevel finds the task. Stdin is
# read only when it is not a terminal (most tests give none), and with a timeout.
# why: seconds; must stay well under the 5 s PreCompact timeout that
# scripts/lib/aa-ma-install-lib.sh registers, leaving time for git and the task loop
readonly STDIN_READ_TIMEOUT_S=2

# root_of <dir> — the git toplevel that contains <dir>: rc 0, or 1 when <dir> is not
# in a repo. rc 2 when the toplevel does not contain <dir>: a repo-local
# core.worktree (a tarball or shared directory, not a clone) can point it at
# another project, whose AA-MA files this hook would then append to.
root_of() {
    local top real
    top=$(git -C "$1" rev-parse --show-toplevel 2>/dev/null) || return 1   # why: not a repo is the caller's case
    real=$(cd "$1" 2>/dev/null && pwd -P) || return 1   # why: an unreadable dir reads as not a repo
    [[ "$real/" == "$top/"* ]] || return 2
    printf '%s\n' "$top"
}

base=$PWD   # the directory whose toplevel becomes ROOT
from_stdin=0
INPUT=""
if [[ ! -t 0 ]]; then
    INPUT=$(timeout "$STDIN_READ_TIMEOUT_S" cat) || {
        rc=$?
        log_warn "$HOOK" "stdin read failed (rc $rc; 124 = timed out after ${STDIN_READ_TIMEOUT_S}s); using pwd"
        INPUT=""
    }
fi
if [[ -n "$INPUT" ]]; then
    # why: `command -v` prints the path on success; only its status is wanted
    if ! command -v jq >/dev/null 2>&1; then
        log_warn "$HOOK" "jq not on PATH; stdin cwd ignored, using pwd"
        notices+=("jq not on PATH, so pwd was used as the project root")
    else
        cwd=$(jq -r '.cwd // empty' <<<"$INPUT" 2>/dev/null || true)   # why: unparsable stdin → empty, reported below
        if [[ "$cwd" != /* || ! -d "$cwd" ]]; then
            log_warn "$HOOK" "stdin cwd '$cwd' is not an absolute directory; using pwd"
            notices+=("stdin cwd '$cwd' is not an absolute directory, so pwd was used")
        else
            base=$cwd
            from_stdin=1
        fi
    fi
fi

ROOT=$PWD
IN_REPO=0
rc=0
# shellcheck disable=SC2310  # why: root_of's rc is the answer (0/1/2), so set -e must not act on it
top=$(root_of "$base") || rc=$?
if [ "$rc" -eq 0 ]; then
    ROOT=$top
    IN_REPO=1
elif [ "$rc" -eq 2 ]; then
    log_warn "$HOOK" "the git toplevel of $base is outside it (core.worktree?); using pwd, linked-worktree check skipped"
    notices+=("the git toplevel of $base is outside it, so pwd was used and the linked-worktree check was skipped")
elif [ "$from_stdin" -eq 1 ]; then
    log_warn "$HOOK" "stdin cwd $cwd is not in a git repo; using pwd"
    notices+=("stdin cwd is not in a git repo, so pwd was used")
fi

# Linked-worktree guard (L-1347). Under MAINTAIN=1 a session rooted in the main
# checkout that `cd`s into a worktree for each command shows only the main root.
# Plan dirs are tracked, so every worktree has them; a task is being worked in a
# linked worktree only when its HEAD carries plan commits that ROOT's HEAD lacks
# (checked per task below). HEAD, not the branch: a rebase detaches it. Appending
# here would then dirty main's tracked files.
linked=()   # "<path>\t<HEAD sha>" of each linked worktree
if [ "$IN_REPO" -eq 1 ]; then
    if wt_list=$(git -C "$ROOT" worktree list --porcelain 2>/dev/null); then   # why: a failure is reported below
        main_wt="" wt=""
        while IFS= read -r line; do
            case "$line" in
                "worktree "*) wt=${line#worktree }; [ -n "$main_wt" ] || main_wt=$wt ;;
                "HEAD "*)     [ "$wt" = "$main_wt" ] || linked+=("$wt"$'\t'"${line#HEAD }") ;;
            esac
        done <<<"$wt_list"
        [ "$main_wt" = "$ROOT" ] || linked=()   # ROOT is itself a linked worktree: write there
    else
        log_warn "$HOOK" "git worktree list failed in $ROOT; linked-worktree check skipped"
        notices+=("git worktree list failed, so $ROOT was written without the linked-worktree check")
    fi
fi

# A symlinked .claude, .claude/dev or .claude/dev/active under ROOT can point every
# append at another project (security audit, M1 §6.8). $HOME/.claude is exempt:
# it is often a legitimate dotfiles symlink.
project_link=""
if [[ "$ROOT" != "$HOME" ]]; then
    for p in .claude .claude/dev .claude/dev/active; do
        if [[ -L "$ROOT/$p" ]]; then
            project_link="$p is a symlink"
            break
        fi
    done
fi

# Collect all active task dirs (project-first, mtime-sorted, collision-resolved).
mapfile -t TASKS < <(aa_ma_list_active_tasks "$ROOT")

if [ "${#TASKS[@]}" -eq 0 ]; then
    log_info "$HOOK" "no active AA-MA tasks"
    exit 0
fi

for task_dir in "${TASKS[@]}"; do
    task_name=$(basename "$task_dir")

    # Never follow a symlink (security audit, sole-dev-merge-fixes 1.8): an
    # untrusted clone can commit one in place of a task dir or an AA-MA file,
    # and the appends below would then write into, and the snapshot copy from,
    # any file outside the repo. A regular file in a non-symlinked task dir is
    # inside that dir; a symlinked parent under ROOT is caught by project_link.
    in_project=0
    [[ "$task_dir" == "$ROOT/.claude/dev/active/"* ]] && in_project=1
    skip_why=""
    if [ "$in_project" -eq 1 ] && [ -n "$project_link" ]; then
        skip_why="project $project_link"
    elif [[ -L "$task_dir" ]]; then
        skip_why="task dir is a symlink"
    else
        for f in "${AA_MA_FILES[@]}"; do
            if [[ -L "${task_dir}/${task_name}-${f}" ]]; then
                skip_why="${task_name}-${f} is a symlink"
                break
            fi
        done
    fi
    if [ -n "$skip_why" ]; then
        log_warn "$HOOK" "skipped task $task_name: $skip_why; nothing read or written"
        skipped_tasks=$((skipped_tasks + 1))
        continue
    fi

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

    worked=()   # linked worktrees whose branch carries plan commits ROOT's HEAD lacks
    if [ "$in_project" -eq 1 ]; then
        for entry in "${linked[@]}"; do
            wt=${entry%%$'\t'*}
            [[ -d "$wt/.claude/dev/active/$task_name" ]] || continue
            range="HEAD..${entry#*$'\t'}"
            # why: a failed log (a ref gone mid-run) reads as "not worked there": append here as before
            ahead=$(git -C "$ROOT" log -1 --format=%h "$range" -- ".claude/dev/active/$task_name" 2>/dev/null || true)
            [ -n "$ahead" ] && worked+=("$wt")
        done
    fi
    if [ "${#worked[@]}" -gt 0 ]; then
        where=$(printf '%s, ' "${worked[@]}")
        where=${where%, }
        log_info "$HOOK" "$task_name has plan commits in linked worktree(s) $where; nothing appended in $ROOT"
        notices+=("$task_name is active in worktree(s) $where: nothing written to $ROOT; log the CHECKPOINT in the one you are working in")
        continue
    fi

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
# Every notice goes into one systemMessage: stdout carries a single JSON object.
notice=""
for n in "${notices[@]}"; do
    notice="${notice:+$notice; }$n"
done
if [ "$skipped_tasks" -gt 0 ]; then
    notice="${notice:+$notice; }$skipped_tasks task(s) skipped: a symlinked AA-MA file, task dir or project .claude dir"
fi
if [ "$append_failures" -gt 0 ]; then
    notice="${notice:+$notice; }$append_failures audit-trail append(s) failed"
fi
if [ -n "$notice" ]; then
    fail_open_notice "$HOOK" "$notice; see ~/.claude/logs/hooks.log"
fi

exit 0
