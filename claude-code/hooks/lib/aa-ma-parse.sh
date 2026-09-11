#!/usr/bin/env bash
# aa-ma-parse.sh — Shared helper library for AA-MA hooks.
#
# Source this file (don't execute it):
#     . "$(dirname "$0")/lib/aa-ma-parse.sh"
#
# Exports:
#     aa_ma_is_disabled                       -> 0 if AA_MA_HOOKS_DISABLE=1 set, else 1
#     aa_ma_extract_active_milestone <file>   -> stdout: active milestone heading text   (DISPLAY)
#     aa_ma_extract_active_step <file>        -> stdout: active step heading text        (DISPLAY)
#     aa_ma_list_active_tasks                 -> stdout: mtime-sorted task-dir paths, one per line
#     aa_ma_debug <msg...>                    -> stderr line iff HOOK_DEBUG=1
#     AA_MA_PARSE_SH_LOADED                   -> set to 1 once sourced (re-source guard)
#     AA_MA_MILESTONE_ERE                     -> ERE mirroring grammar.py MILESTONE_RE (display readers only)
#     aa_ma_gate <file> [--milestone N] [--step N.M] -> kv lines from the Python SSoT gate; rc 0-4, 127 if it cannot run  (ENFORCING)
#     aa_ma_gate_field <key>  (stdin: kv)     -> value after the first `=`, verbatim
#
# This header is the discovery surface: it is the first thing anyone sourcing
# the library reads, and a symbol missing from it gets reimplemented instead of
# reused. `tests/hooks/aa-ma-parse.bats` asserts every public symbol appears
# here, so the list cannot drift from the definitions below.
#
# THE TOLERANT / STRICT BOUNDARY (ADR-0009, milestone-grammar-ssot M5)
#
#   Two kinds of reader live here and they must not be confused:
#
#   DISPLAY readers — aa_ma_extract_active_milestone, aa_ma_extract_active_step.
#     Tolerant, defaulting, always answer. Used by aa-ma-session-start.sh and
#     pre-compact-aa-ma.sh, where a wrong answer is a cosmetic line in a
#     briefing. They may NOT be used for any decision that blocks or passes a
#     gate: sub-step 4.5 wired the §6.7 gate to one and it certified the wrong
#     milestone (reported PENDING=0 / Gate: SOFT for one that was 1 PENDING /
#     Gate: HARD — a silent false PASS).
#
#   ENFORCING reads — aa_ma_gate only. It is a LAUNCHER for src/aa_ma/gate.py,
#     which answers every gate question over the Python SSoT (grammar.py +
#     enforce.py + plan_parsers.py) and refuses on ambiguity instead of
#     choosing. No bash in this file parses a milestone block for an enforcing
#     decision any more. The awk helpers that used to (block extractors, field
#     readers, the strict derivation) were deleted in M5 after three §6.8
#     passes found 8, 4, then 9 CRITICALs in them — hand-aligning a second
#     markdown parser with the first did not converge. If you need a new
#     enforcing question answered, add it to gate.py and its tests; do not
#     add awk here.
#
# Guard against double-sourcing: functions are idempotent but re-definition
# is noisy under `set -u`/strict mode in consumers.
# shellcheck disable=SC2317  # `return` / `exit` fallback both unreachable by design
if [ "${AA_MA_PARSE_SH_LOADED:-0}" = "1" ]; then
    # Prefer `return` when sourced; fall back to `exit 0` if someone executes
    # the file directly (which would be a usage bug, but cleanly handled).
    return 0 2>/dev/null || exit 0
fi
AA_MA_PARSE_SH_LOADED=1

# -----------------------------------------------------------------------------
# aa_ma_is_disabled — returns 0 (true) if the master kill switch is set.
# -----------------------------------------------------------------------------
aa_ma_is_disabled() {
    [ "${AA_MA_HOOKS_DISABLE:-0}" = "1" ]
}

# -----------------------------------------------------------------------------
# aa_ma_debug <msg...> — emits a `[aa-ma-debug]` prefixed stderr line when
# HOOK_DEBUG=1 is set. Silent otherwise.
# -----------------------------------------------------------------------------
aa_ma_debug() {
    [ "${HOOK_DEBUG:-0}" = "1" ] || return 0
    printf '[aa-ma-debug] %s\n' "$*" >&2
}

# -----------------------------------------------------------------------------
# _aa_ma_strip_html_comments <file> — cat <file> with <!-- ... --> blocks
# removed. Used before Status-pattern matching so commented-out examples don't
# trigger false positives. Handles single-line comments only (block comments
# spanning lines are extremely rare in AA-MA tasks.md).
# -----------------------------------------------------------------------------
_aa_ma_strip_html_comments() {
    # Portable sed: remove <!-- ... --> on a single line.
    sed 's/<!--[^>]*-->//g' "$1"
}

# -----------------------------------------------------------------------------
# aa_ma_extract_active_milestone <tasks-file>
#   Emits the active milestone heading (stripped of leading "## ").
#   Preference order:
#     1. Milestone whose body contains a line matching Status: ACTIVE
#     2. First milestone whose body contains Status: PENDING
#   Emits empty string if neither found.
# -----------------------------------------------------------------------------
#   Recognises milestone headings via AA_MA_MILESTONE_ERE, NOT bare `^## `.
#   The loose form was the third grammar in this file and it made a trailing
#   prose section — `## Summary Counts`, which real plans carry and which
#   contains field-shaped lines — a candidate active milestone. Measured across
#   the repo's 27 tasks files the tightening changes exactly one row: a TUI
#   fixture using `## Step N:` headings, which grammar.py already matches 0 of
#   9 times. So this makes bash agree with the Python SSoT rather than losing
#   information. `aa-ma-session-start.sh` degrades to "unknown" on empty, which
#   is more truthful than naming a heading no gate can act on.
aa_ma_extract_active_milestone() {
    local file="$1"
    [ -f "$file" ] || return 0
    _aa_ma_strip_html_comments "$file" | awk -v mre="$AA_MA_MILESTONE_ERE" '
        # A milestone heading opens a block; any other H2 closes one.
        /^## / {
            current = ""
            if ($0 ~ mre) {
                t = $0; sub(mre, "", t)
                gsub(/^[[:blank:]]+|[[:blank:]]+$/, "", t)
                if (t != "") { current = $0; sub(/^## /, "", current) }
            }
            next
        }
        # Status line: detect ACTIVE or PENDING within current milestone
        /(\*\*)?Status:(\*\*)? +ACTIVE/ {
            if (current != "") { active = current; exit }
        }
        /(\*\*)?Status:(\*\*)? +PENDING/ {
            if (current != "" && first_pending == "") {
                first_pending = current
            }
        }
        END {
            if (active != "") print active
            else if (first_pending != "") print first_pending
        }
    '
}

# -----------------------------------------------------------------------------
# AA_MA_MILESTONE_ERE — bash-side mirror of src/aa_ma/grammar.py MILESTONE_RE.
#
# POSIX ERE, deliberately, so it behaves identically under gawk and mawk (the
# Debian/Ubuntu default awk). Three choices are load-bearing:
#   * [[:blank:]] not \s — mawk has no \s and matches NOTHING for it, silently.
#     verify-impl's block extractor returned an empty block on any mawk host.
#   * [.] not \. — a dynamic regex passed via -v makes gawk warn on \. and then
#     treat it as "any character".
#   * The dash alternation is (-|–|—), never a bracket class. The en/em dashes
#     are multibyte; a bracket class of them is not portable to mawk, and a bare
#     hyphen inside one made `### Step 1.1-alpha:` parse as number 1.1.
# -----------------------------------------------------------------------------
AA_MA_MILESTONE_ERE='^##[[:blank:]]+(Milestone[[:blank:]]+M?|M)[0-9]+[a-z]?([.][0-9]+)*(:|[[:blank:]]+(-|–|—)[[:blank:]]+)'

# -----------------------------------------------------------------------------
# aa_ma_extract_active_step <tasks-file>
#   Emits the active step heading (stripped of leading "### ").
#   Preference order:
#     1. Step whose body contains Status: ACTIVE
#     2. First step whose body contains Status: PENDING
#   Empty string if neither found.
#
#   A step block ENDS at the next H2. Without that reset the first Status line
#   after milestone N's last sub-step is milestone N+1's own milestone-level
#   status, and it was attributed to that trailing sub-step — so the answer was
#   always "the last sub-step of the milestone before the one being worked on".
#   Measured in this repo's own provenance.log, which recorded `Sub-step 2.4`
#   while M3 ran and `Sub-step 3.6` while M4 ran. It also stole the ACTIVE
#   verdict outright: a genuinely ACTIVE sub-step was never reached, because
#   awk exits on the first ACTIVE it sees and the milestone's own line came
#   first. Not display-only — `pre-compact-aa-ma.sh` writes this into the
#   `CHECKPOINT — ActiveStep:` line that rules/aa-ma.md makes the session-resume
#   signal, so a wrong answer here resumes the next session on the wrong step.
# -----------------------------------------------------------------------------
aa_ma_extract_active_step() {
    local file="$1"
    [ -f "$file" ] || return 0
    _aa_ma_strip_html_comments "$file" | awk '
        # Any H2 closes the current step block. Disjoint from /^### / below:
        # "### x" has "#" where this pattern requires a blank.
        /^## / {
            current = ""
            next
        }
        /^### / {
            current = $0
            sub(/^### /, "", current)
            next
        }
        /(\*\*)?Status:(\*\*)? +ACTIVE/ {
            if (current != "") { active = current; exit }
        }
        /(\*\*)?Status:(\*\*)? +PENDING/ {
            if (current != "" && first_pending == "") {
                first_pending = current
            }
        }
        END {
            if (active != "") print active
            else if (first_pending != "") print first_pending
        }
    '
}

# -----------------------------------------------------------------------------
# aa_ma_list_active_tasks
#   Emits absolute paths to active task directories, one per line,
#   sorted newest-first by their tasks.md mtime.
#
#   Sources (checked in this order):
#     1. <cwd>/.claude/dev/active/
#     2. $HOME/.claude/dev/active/
#
#   Collision rule: if the same task name appears in both sources, the
#   project-local version wins (home version is suppressed).
# -----------------------------------------------------------------------------
aa_ma_list_active_tasks() {
    local project_dir="${PWD}/.claude/dev/active"
    local home_dir="${HOME}/.claude/dev/active"
    local -A seen_names=()
    local -a rows=()
    local task_name tasks_file mtime dir source_dir

    for source_dir in "$project_dir" "$home_dir"; do
        [ -d "$source_dir" ] || continue
        for dir in "$source_dir"/*/; do
            [ -d "$dir" ] || continue
            task_name=$(basename "$dir")
            # Collision: project-local wins (project is first in the outer loop).
            if [ -n "${seen_names[$task_name]:-}" ]; then
                continue
            fi
            seen_names[$task_name]=1
            tasks_file="${dir}${task_name}-tasks.md"
            if [ -f "$tasks_file" ]; then
                mtime=$(stat -c %Y "$tasks_file")
            else
                mtime=0
            fi
            rows+=("${mtime}"$'\t'"${dir%/}")
        done
    done

    # Sort numerically by mtime descending (newest first); on tie, sort by path
    # ascending for a stable deterministic fallback. Emit just the path column.
    if [ "${#rows[@]}" -gt 0 ]; then
        printf '%s\n' "${rows[@]}" \
            | sort -t$'\t' -k1,1rn -k2,2 \
            | awk -F'\t' 'NF==2 { print $2 }'
    fi
}

# -----------------------------------------------------------------------------
# aa_ma_gate <tasks-file> [--milestone N]
#   Runs the Python SSoT gate (`src/aa_ma/gate.py`, console script
#   `aa-ma-gate`) in kv format: one `key=value` per line, exit codes 0/1/2/3/4
#   per the M5 contract. This is a LAUNCHER, not a parser — nothing in bash
#   reads a milestone block for an enforcing decision any more (ADR-0009).
#
#   Fails CLOSED. If uv is not on PATH, or the tool does not start, the
#   function prints a BLOCKED line on stderr and returns 127 without any
#   kv output — a gate that cannot run must never look like a gate that
#   passed. The tool's own output is checked for `exit_code=` so a spawn
#   failure inside `uv run` (which also exits 2) is not mistaken for the
#   contract's "unreadable" 2.
#
#   Repo resolution: this file is symlinked into ~/.claude/hooks/lib by
#   install.sh, so `readlink -f` on it lands in the aa-ma-forge checkout,
#   whichever repo the gate is being run from.
# -----------------------------------------------------------------------------
aa_ma_gate() {
    local root out rc
    root="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/../../.." && pwd)"
    if ! command -v uv >/dev/null 2>&1; then
        echo "BLOCKED: aa-ma-gate needs uv on PATH and it is missing — refusing, not skipping" >&2
        return 127
    fi
    out=$(uv run --quiet --project "$root" aa-ma-gate --format kv "$@")
    rc=$?
    if ! printf '%s\n' "$out" | grep -q '^exit_code='; then
        echo "BLOCKED: aa-ma-gate did not run (uv rc ${rc}, project ${root}) — refusing, not skipping" >&2
        return 127
    fi
    printf '%s\n' "$out"
    return "$rc"
}

# -----------------------------------------------------------------------------
# aa_ma_gate_field <key>   (stdin: kv output of aa_ma_gate)
#   Everything after the first `=` on the first `key=` line, verbatim. No
#   quoting or escaping is applied on either side, which is what lets a
#   heading reach §7.1's `grep -F` byte-exact.
# -----------------------------------------------------------------------------
aa_ma_gate_field() {
    sed -n "s/^$1=//p" | head -n 1
}

# -----------------------------------------------------------------------------
# End of aa-ma-parse.sh
# -----------------------------------------------------------------------------
