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
#     aa_ma_list_active_tasks [root]          -> stdout: mtime-sorted task-dir paths, one per line (root defaults to $PWD)
#     aa_ma_debug <msg...>                    -> log_debug line (hooks.log + stderr) iff HOOK_DEBUG=1
#     aa_ma_debug_cmd <label> <command>       -> aa_ma_debug "<label> (<n> chars, first word '<word>')"; never the arguments
#     AA_MA_PARSE_SH_LOADED                   -> set to 1 once sourced (re-source guard)
#     AA_MA_MILESTONE_ERE                     -> ERE mirroring grammar.py MILESTONE_RE (display readers only)
#     aa_ma_gate <file> [--milestone N] [--step N.M] -> kv lines from the Python SSoT gate; rc 0-4, 127 if it cannot run  (ENFORCING)
#     aa_ma_gate_field <key>  (stdin: kv)     -> value after the first `=`, verbatim
#     aa_ma_has_gate_approval <log> <title>  -> rc 0 iff the LAST "GATE APPROVAL: <title>" block says Decision: APPROVED  (ENFORCING)
#     aa_ma_deps <graph|check|advisory> <tasks.md> -> `python -m aa_ma.deps` output; rc passed through  (ADVISORY — never a gate)
#     aa_ma_lint_views <plan.md> [args...] -> `aa-ma-lint-views` output; rc 0/1 passed through, 127 if it cannot run  (read by the §6.7 diagram item)
#     aa_ma_codemem_bin <forge-root>     -> stdout: the codemem binary to run ($CODEMEM_BIN, else the forge venv's, else PATH) (rc 0), nothing when none is executable (rc 1)
#     aa_ma_codemem_dir <repo-top>       -> stdout: the codemem index dir ($CODEMEM_DB's, else the XDG cache dir; M16) (rc 0), nothing when it cannot be computed (rc 1)
#     AA_MA_COCHANGE_MIN_SHARED / AA_MA_COCHANGE_MIN_RATIO -> the T7 co-change constants (5 commits, 0.5 share)
#     aa_ma_cochange_partners <top> <forge> <timeout-s> -- <path>... -> stdout: codemem co_changes partners at T7, sorted, unique; rc 0 ok | 2 usage | 3 no index | 4 no codemem binary or no timeout(1) | 5 codemem failed | 6 timed out
#     aa_ma_sanitize_lines  (stdin: lines) -> stdout: the same lines, every Cc/Cf/Co/Cs/Zl/Zp character (and bad UTF-8) as `?`; rc 0 always
#     aa_ma_default_base_ref             -> stdout: the merge-base ref (origin/HEAD, origin/main, origin/master, main, master) (rc 0), nothing (rc 1)
#     aa_ma_milestone_base               -> stdout: merge-base of origin's default branch and HEAD (rc 0); rc 2 + a reason line: no origin default branch | no milestone window
#     aa_ma_impact <plan> <tasks> --milestone N [--base SHA] -> aa-ma-impact kv lines; rc 0/1/2/3/5 passed through, 127 if it cannot run  (ENFORCING, §6.7 fence 4)
#     aa_ma_read_sidecar_sha <file>      -> stdout: the 40/64-hex SHA in a repo-controlled sidecar (rc 0), nothing for anything else (rc 1)
#     aa_ma_sha_behind <repo> <sidecar>  -> stdout: commits from the sidecar's SHA to HEAD (rc 0), or a reason: bad sha | not in history | git timeout | git failed (rc 1)
#
# Also sources aa-ma-log.sh from this file's real directory, so every hook that sources this
# library has log_info|log_warn|log_error|log_debug, fail_open_notice and mask_secrets.
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
#     readers, the strict derivation) were deleted in M5 — ADR-0009 records
#     the measurements. If you need a new enforcing question answered, add it
#     to gate.py and its tests; do not add awk here.
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

# Real directory, not the symlink's: install.sh links this file into ~/.claude/hooks/lib, and a
# checkout pulled before install.sh re-runs may not have aa-ma-log.sh linked there yet.
# why: one fork (hot path); no `readlink -f` (macOS < 12.3) → the path as sourced, which install.sh's lib/ link serves
_aa_ma_parse_real="$(readlink -f "${BASH_SOURCE[0]}" 2>/dev/null)" || _aa_ma_parse_real="${BASH_SOURCE[0]}"
# shellcheck disable=SC1091  # why: the path is computed at runtime; aa-ma-log.bats covers the source
. "${_aa_ma_parse_real%/*}/aa-ma-log.sh"

# -----------------------------------------------------------------------------
# aa_ma_is_disabled — returns 0 (true) if the master kill switch is set.
# -----------------------------------------------------------------------------
aa_ma_is_disabled() {
    [ "${AA_MA_HOOKS_DISABLE:-0}" = "1" ]
}

# -----------------------------------------------------------------------------
# aa_ma_debug <msg...> — log_debug under the calling hook's file name: a DEBUG line
# to hooks.log and stderr when HOOK_DEBUG=1. Silent otherwise.
# -----------------------------------------------------------------------------
aa_ma_debug() {
    log_debug "${0##*/}" "$*"
}

# Longest first word logged, in characters: enough for a program name; a longer word is '?'.
# No argument is ever logged: HOOK_DEBUG lines are written to hooks.log on disk, and a
# command line can carry a secret no mask pattern knows (`curl -u user:pw`, `mysql -pX`).
_AA_MA_DEBUG_WORD_CHARS=32

# aa_ma_debug_cmd <label> <command> — debug line naming the command's length and first word.
aa_ma_debug_cmd() {
    local cmd="${2-}" rest word
    rest="${cmd#"${cmd%%[![:space:]]*}"}"
    while :; do   # skip env assignments (`TOKEN=x cmd`): the value is exactly what must not be logged
        word="${rest%%[[:space:]]*}"
        [[ "${word}" =~ ^[A-Za-z_][A-Za-z0-9_]*= ]] || break
        rest="${rest#"${word}"}"
        rest="${rest#"${rest%%[![:space:]]*}"}"
    done
    # a quoted or odd word may be the tail of a quoted value (`P='a b' cmd`): log '?' instead
    [[ -z "${word}" || "${word}" =~ ^[A-Za-z0-9_./-]+$ ]] || word="?"
    # Never truncate: a cut token (ghp_…, sk-…) is too short for its mask rule and would leak.
    (( ${#word} <= _AA_MA_DEBUG_WORD_CHARS )) || word="?"
    aa_ma_debug "${1-} (${#cmd} chars, first word '${word}')"
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
# aa_ma_list_active_tasks [root]
#   Emits absolute paths to active task directories, one per line,
#   sorted newest-first by their tasks.md mtime.
#
#   Sources (checked in this order):
#     1. <root>/.claude/dev/active/  (root: $1, default $PWD — a hook passes
#        the git toplevel of its stdin cwd; sole-dev-merge-fixes M5, L-1347)
#     2. $HOME/.claude/dev/active/
#
#   Collision rule: if the same task name appears in both sources, the
#   project-local version wins (home version is suppressed).
# -----------------------------------------------------------------------------
aa_ma_list_active_tasks() {
    local project_dir="${1:-$PWD}/.claude/dev/active"
    local home_dir="${HOME}/.claude/dev/active"
    local -A seen_names=()
    local -a rows=()
    local task_name tasks_file mtime dir source_dir

    for source_dir in "$project_dir" "$home_dir"; do
        [ -d "$source_dir" ] || continue
        for dir in "$source_dir"/*/; do
            [ -d "$dir" ] || continue
            task_name=${dir%/}; task_name=${task_name##*/}   # not $(basename): it strips a trailing LF
            # A control character (e.g. $'x\n0\t..') would split the mtime/path rows below
            # and print a path outside the active dir.
            if [[ "$task_name" == *[[:cntrl:]]* ]]; then
                log_warn aa-ma-parse "skipped a task dir under $source_dir whose name holds a control character"
                continue
            fi
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
# aa_ma_gate <tasks-file> [--milestone N] [--step N.M]
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
# aa_ma_has_gate_approval <context-log.md> <title>
#   rc 0 iff the LAST heading that ends with "GATE APPROVAL: <title>" opens a block
#   (up to the next heading) holding `- Decision: APPROVED` (bold field accepted).
#   Block-scoped on purpose: the `grep -A8` it replaces read into the NEXT block,
#   so a REJECTED approval passed when another milestone's APPROVED one followed it.
#   The title is compared as a string (never a pattern, never unescaped); code-fenced lines
#   are skipped (an unclosed fence hides the rest of the file: that fails closed, never open).
#   Used by §7.1 and fence 3.
# -----------------------------------------------------------------------------
aa_ma_has_gate_approval() {
    [ -f "$1" ] || return 1
    # The title goes in through the environment: `awk -v` would process its backslash escapes.
    # Lines inside a ``` / ~~~ code fence are skipped, so a pasted example is never an approval.
    # A fence closes only on its own character at >= its own length, nothing after (CommonMark):
    # a ``` inside ````, or a ~~~ inside ```, must not end the skip (PR #37 Stage C).
    # Run lengths are counted by hand: mawk has no {n,m} intervals.
    AA_MA_WANT="GATE APPROVAL: $2" awk '
        BEGIN { want = ENVIRON["AA_MA_WANT"] }
        {
            s = $0; sub(/^[ \t]*/, "", s); c = substr(s, 1, 1)
            if ((c == "`" || c == "~") && substr(s, 1, 3) == c c c) {
                n = 3; while (substr(s, n + 1, 1) == c) n++
                if (!infence) { infence = 1; fc = c; fl = n }
                else if (c == fc && n >= fl && substr(s, n + 1) ~ /^[ \t]*$/) infence = 0
                next
            }
        }
        infence { next }
        /^#+[ \t]/ {
            line = $0; sub(/[ \t]+$/, "", line)
            inb = 0
            if (length(line) >= length(want) && substr(line, length(line) - length(want) + 1) == want) {
                inb = 1; found = 1; dec = ""
            }
            next
        }
        inb && /^-[ \t]+(\*\*)?Decision:(\*\*)?[ \t]+/ { dec = $0 }
        END { exit !(found && dec ~ /^-[ \t]+(\*\*)?Decision:(\*\*)?[ \t]+APPROVED/) }
    ' "$1"
}

# -----------------------------------------------------------------------------
# aa_ma_deps <graph|check|advisory> <tasks.md>
#   `python -m aa_ma.deps` from the plugin checkout, located as aa_ma_gate does.
#   Planning-time and advisory only (diagram-generation M7, map Ticket 16): the
#   exit code is passed through and the CALLER decides; nothing here blocks.
# -----------------------------------------------------------------------------
aa_ma_deps() {
    local root
    root="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/../../.." && pwd)"
    if ! command -v uv >/dev/null 2>&1; then
        echo "aa_ma_deps: uv not on PATH — dependency check skipped" >&2
        return 127
    fi
    # A padded tasks.md must not hang a command. coreutils `timeout` where present
    # (stock macOS lacks it); AA_MA_DEPS_TIMEOUT seconds, default 30.
    if command -v timeout >/dev/null 2>&1; then
        timeout "${AA_MA_DEPS_TIMEOUT:-30}" uv run --quiet --project "$root" python -m aa_ma.deps "$@"
    else
        uv run --quiet --project "$root" python -m aa_ma.deps "$@"
    fi
}

# -----------------------------------------------------------------------------
# aa_ma_lint_views <plan.md> [aa-ma-lint-views args...]
#   `aa-ma-lint-views` from the plugin checkout, located as aa_ma_gate does. Its
#   exit code passes through (0 clean / 1 findings); 127 — with nothing on stdout
#   — when it could not run, told apart by the `render:` line every real run
#   prints last. Read by the §6.7 HARD item for §13 sigil edges (ADR-0015).
# -----------------------------------------------------------------------------
aa_ma_lint_views() {
    local root out rc
    root="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/../../.." && pwd)"
    if ! command -v uv >/dev/null 2>&1; then
        echo "BLOCKED: aa-ma-lint-views needs uv on PATH and it is missing — refusing, not skipping" >&2
        return 127
    fi
    out=$(uv run --quiet --project "$root" aa-ma-lint-views "$@")
    rc=$?
    if ! printf '%s\n' "$out" | grep -q '^render: '; then
        echo "BLOCKED: aa-ma-lint-views did not run (uv rc ${rc}, project ${root}) — refusing, not skipping" >&2
        return 127
    fi
    printf '%s\n' "$out"
    return "$rc"
}

# aa_ma_codemem_dir <repo-top>
#   The dir holding <repo-top>'s codemem index and sidecars (M16): that of
#   $CODEMEM_DB when set, else ${XDG_CACHE_HOME:-~/.cache}/codemem/<sha256(realpath
#   repo-top)> (a relative XDG_CACHE_HOME is ignored, as the XDG spec says).
#   Python twins: codemem.paths.resolve_db_path, aa_ma.render.graph._resolve_db_path
#   (tests/codemem/test_safety_parity.py). Prints nothing, rc 1, when it cannot
#   be computed (no realpath/readlink -f, no sha256sum/shasum).
aa_ma_codemem_dir() {
    local top="$1" db="${CODEMEM_DB:-}" real cache key
    if [[ -n "$db" ]]; then
        [[ "$db" == /* ]] || db="$(pwd -P)/${db}"  # pwd -P: os.getcwd() in the Python twins
        while [[ "$db" == ?*/ ]]; do db="${db%/}"; done  # pathlib drops a trailing /
        db="${db%/*}"
        printf '%s' "${db:-/}"  # /index.db lives in /
        return 0
    fi
    # why: readlink -f is the fallback where realpath is missing; neither → rc 1
    real="$(realpath -- "$top" 2>/dev/null || readlink -f -- "$top" 2>/dev/null)" || return 1
    [[ -n "$real" ]] || return 1
    if command -v sha256sum > /dev/null 2>&1; then  # why: a presence probe
        key="$(printf '%s' "$real" | sha256sum)"
    elif command -v shasum > /dev/null 2>&1; then  # why: as above (macOS)
        key="$(printf '%s' "$real" | shasum -a 256)"
    else
        return 1
    fi
    key="${key%% *}"
    [[ "$key" =~ ^[0-9a-f]{64}$ ]] || return 1
    cache="${XDG_CACHE_HOME:-}"
    [[ "$cache" == /* ]] || cache="${HOME}/.cache"
    while [[ "$cache" == ?*/ ]]; do cache="${cache%/}"; done  # pathlib drops a trailing /
    printf '%s/codemem/%s' "$cache" "$key"
}

# aa_ma_codemem_bin <forge-root>
#   The codemem binary the post-commit worker and §6.0 run: $CODEMEM_BIN (no
#   fallback when set), else <forge-root>/.venv/bin/codemem, else an absolute
#   `codemem` on PATH. Prints it (rc 0) only when executable; else nothing, rc 1.
aa_ma_codemem_bin() {
    local bin
    if [[ -n "${CODEMEM_BIN:-}" ]]; then
        bin="${CODEMEM_BIN}"
    else
        bin="$1/.venv/bin/codemem"
        [[ -x "${bin}" ]] || bin="$(command -v codemem || true)"  # why: absent → rc 1 below
        # Absolute only: the worker drops relative PATH entries, so §6.0 must not count one.
        [[ "${bin}" == /* ]] || bin=""
    fi
    [[ -n "${bin}" && -x "${bin}" ]] || return 1
    printf '%s' "${bin}"
}

# T7 (plan Milestone 11 Contract; M11's aa_ma.impact COCHANGE_MIN_SHARED / _RATIO): a
# co_changes partner counts when it changed in >= 5 of the file's commits (unit: commits — fewer
# is chance) and in >= 0.5 of them (unit: share of the file's commits, 0-1 — "at least half
# the time"). Read by aa_ma_cochange_partners; callers print them in their advisory lines.
AA_MA_COCHANGE_MIN_SHARED=5
AA_MA_COCHANGE_MIN_RATIO=0.5

# aa_ma_cochange_partners <repo-top> <forge-root> <timeout-s> -- <path>...
#   The one shell co_changes reader (commit-drift's ad-hoc advisory, predicted-vs-actual.sh): the
#   codemem co_changes partners of <path>... at the T7 constants, one per line, sorted (C locale)
#   and unique; nothing when there are none. Index: aa_ma_codemem_dir; binary: aa_ma_codemem_bin
#   (from <forge-root>, never the repo); codemem runs under `timeout -k 1 <timeout-s>`, the paths
#   after `--`. codemem's stderr is dropped — the rc is the report, and the caller logs or
#   prints it. Safe under `set -e` as `x=$(aa_ma_cochange_partners …) || rc=$?`.
#   rc 0 ok | 2 usage (no `--`, no path, <timeout-s> not a positive integer) | 3 no index |
#   4 no codemem binary, or no timeout(1) to bound it | 5 codemem exited non-zero, or printed
#   no JSON (or jq is missing) | 6 timed out (timeout's 124, or 137 after the -k SIGKILL)
aa_ma_cochange_partners() {
    local top="${1-}" forge="${2-}" secs="${3-}" db_dir bin out partners rc=0
    [[ $# -ge 5 && "${4-}" == "--" && "${secs}" =~ ^[1-9][0-9]*$ ]] || return 2
    shift 4
    db_dir="$(aa_ma_codemem_dir "${top}")" || return 3
    [[ -f "${db_dir}/index.db" ]] || return 3
    bin="$(aa_ma_codemem_bin "${forge}")" || return 4
    command -v timeout > /dev/null 2>&1 || return 4   # why: a presence probe; no timeout → no unbounded call
    out="$(timeout -k 1 "${secs}" "${bin}" query co_changes --repo-root "${top}" \
        --threshold "${AA_MA_COCHANGE_MIN_SHARED}" --min-ratio "${AA_MA_COCHANGE_MIN_RATIO}" \
        -- "$@" 2>/dev/null)" || rc=$?   # why: codemem's stderr is replaced by the rc
    (( rc == 124 || rc == 137 )) && return 6
    (( rc == 0 )) || return 5
    # Several paths print one object keyed by path; one path prints its bare result object.
    # why: jq's parse error on a non-JSON answer is rc 5
    partners="$(jq -r 'if has("files") then [.] else [.[]] end | .[] | .files[]?.path' <<< "${out}" 2>/dev/null)" || return 5
    [[ -n "${partners}" ]] || return 0
    printf '%s\n' "${partners}" | awk 'NF' | LC_ALL=C sort -u
}

# aa_ma_sanitize_lines   (stdin: lines; stdout: the same lines, made safe to print)
#   For repo-controlled text (file names, codemem partner paths) about to reach a terminal or
#   an agent prompt. Every character in a Cc, Cf, Co, Cs, Zl or Zp Unicode category — the set
#   codemem's sanitize_context_line drops: controls, bidi overrides such as U+202E, zero-width
#   and tag characters — becomes `?`, as do bytes that are not UTF-8. `?`, not codemem's space:
#   a path keeps one visible mark per removed character. Stdlib-only `python3 -I -S` (aa_ma
#   must not need codemem). Fails open, never silent: with no working python3, every byte
#   outside printable ASCII becomes `?` (stricter, never looser) and one WARN line goes to
#   hooks.log. Empty input prints nothing. Always rc 0. A line's own newline is its end:
#   callers replace an embedded newline first (`${p//[[:cntrl:]]/?}`) when a value may hold one.
_AA_MA_SANITIZE_PY='
import sys, unicodedata
bad = frozenset(("Cc", "Cf", "Co", "Cs", "Zl", "Zp"))
text = sys.stdin.buffer.read().decode("utf-8", "surrogateescape")
lines = text[:-1].split("\n") if text.endswith("\n") else text.split("\n")
out = ["".join("?" if unicodedata.category(c) in bad else c for c in ln) for ln in lines]
sys.stdout.buffer.write(("\n".join(out) + "\n").encode("utf-8"))
'
aa_ma_sanitize_lines() {
    local input out
    input="$(cat)"
    [[ -n "${input}" ]] || return 0
    # why: python's traceback is replaced by the one WARN line below
    if out="$(printf '%s\n' "${input}" | python3 -I -S -c "${_AA_MA_SANITIZE_PY}" 2>/dev/null)"; then
        printf '%s\n' "${out}"
        return 0
    fi
    log_warn "${0##*/}" "aa_ma_sanitize_lines: python3 missing or failed; non-ASCII bytes printed as ?"
    printf '%s\n' "${input}" | LC_ALL=C sed 's/[^ -~]/?/g'
}

# aa_ma_default_base_ref
#   The ref a branch's merge-base is taken from, in the current repo: origin/HEAD's target
#   (short, e.g. origin/main), else the first of origin/main, origin/master, main, master that
#   names a commit. Remote-tracking first: a local default branch can lag upstream, and this
#   session can move it. Callers tell a local fallback by the missing `origin/` prefix. Prints
#   the ref (rc 0), or nothing when none resolves (rc 1).
aa_ma_default_base_ref() {
    local ref
    # why: no origin/HEAD is normal (a `git remote add`, no set-head); the candidates take over
    ref="$(git symbolic-ref -q --short refs/remotes/origin/HEAD 2>/dev/null)" || ref=""
    if [[ -n "${ref}" ]]; then
        printf '%s' "${ref}"
        return 0
    fi
    for ref in refs/remotes/origin/main refs/remotes/origin/master refs/heads/main refs/heads/master; do
        # why: a probe — only the exit status is read
        if git rev-parse --verify -q "${ref}^{commit}" > /dev/null 2>&1; then
            ref="${ref#refs/remotes/}"
            printf '%s' "${ref#refs/heads/}"
            return 0
        fi
    done
    return 1
}

# aa_ma_milestone_base
#   The milestone window's base for §6.7 fence 4 and verify-impl (R1): `git merge-base
#   origin/<default> HEAD`, where <default> is origin/HEAD's target (a refs/remotes/origin/<name>
#   ref that is not this branch's own), else origin/main, else origin/master — origin only,
#   never a local branch this session can move. Prints the SHA
#   (rc 0). rc 2, one line naming the reason, when there is no window to certify: no origin
#   default branch, no merge-base, or HEAD is the default branch tip (merge-base == HEAD).
aa_ma_milestone_base() {
    local ref="" full base head cand branch
    # origin/HEAD is a local, mutable symref: trust only a full refs/remotes/origin/<name>
    # target, and never this branch's own remote copy (that would narrow the window to
    # nothing and certify an empty milestone — commit security review, M11).
    # why: no origin/HEAD is normal (no `remote set-head`); the candidates take over
    full="$(git symbolic-ref -q refs/remotes/origin/HEAD 2>/dev/null)" || full=""
    if [[ "${full}" =~ ^refs/remotes/origin/[^/]+$ ]]; then
        ref="${full#refs/remotes/}"
        # why: detached HEAD has no branch name; then there is no self copy to compare
        branch="$(git symbolic-ref -q --short HEAD 2>/dev/null)" || branch=""
        if [[ -n "${branch}" && "${ref}" == "origin/${branch}" ]]; then
            echo "aa_ma_milestone_base: origin/HEAD points at this branch (${ref}); no milestone window to certify"
            return 2
        fi
    fi
    if [[ -z "${ref}" ]]; then
        for cand in origin/main origin/master; do
            # why: a probe — only the exit status is read
            if git rev-parse --verify -q "refs/remotes/${cand}^{commit}" > /dev/null 2>&1; then
                ref="${cand}"
                break
            fi
        done
    fi
    if [[ -z "${ref}" ]]; then
        echo "aa_ma_milestone_base: no origin default branch (origin/HEAD, origin/main, origin/master)"
        return 2
    fi
    # why: stderr dropped — no merge-base is reported as the named error below
    base="$(git merge-base "${ref}" HEAD 2>/dev/null)" || base=""
    head="$(git rev-parse -q --verify HEAD)" || head=""
    if [[ -z "${base}" || "${base}" == "${head}" ]]; then
        echo "aa_ma_milestone_base: no milestone window (merge-base of ${ref} and HEAD is ${base:-empty}; HEAD ${head:0:12})"
        return 2
    fi
    printf '%s\n' "${base}"
}

# aa_ma_impact <plan.md> <tasks.md> --milestone N [--base SHA] [...]
#   Launcher for the Python aa-ma-impact (§6.7 fence 4), the aa_ma_gate pattern: runs it from
#   the forge that ships this file, prints its kv output and returns its rc (0/1/2/3/5).
#   127, with a BLOCKED line, when uv is missing or the CLI printed no `exit_code=` line —
#   a gate that cannot run must not pass.
aa_ma_impact() {
    local root out rc
    root="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/../../.." && pwd)"
    if ! command -v uv > /dev/null 2>&1; then  # why: a presence probe; the BLOCKED line says it
        echo "BLOCKED: aa-ma-impact needs uv on PATH and it is missing — refusing, not skipping" >&2
        return 127
    fi
    out=$(uv run --quiet --project "$root" aa-ma-impact --format kv "$@")
    rc=$?
    if ! printf '%s\n' "$out" | grep -q '^exit_code='; then
        echo "BLOCKED: aa-ma-impact did not run (uv rc ${rc}, project ${root}) — refusing, not skipping" >&2
        return 127
    fi
    printf '%s\n' "$out"
    return "$rc"
}

# aa_ma_read_sidecar_sha <file>
#   The one shell reader of a repo-controlled sidecar (<codemem index dir>/last_sha,
#   graphify-out/.built_sha; M15 §6.8 C2). Prints the SHA only when <file> is
#   a regular file, neither it nor its directory a symlink, holding exactly one
#   SHA-1 (40-hex) or SHA-256 (64-hex) line; else prints nothing, rc 1. Python
#   twin: codemem.incremental._read_sha.
aa_ma_read_sidecar_sha() {
    local file="$1" sha
    [[ -f "$file" && ! -L "$file" && ! -L "${file%/*}" ]] || return 1
    # why: a sidecar is one SHA line; 128 bytes bounds the read of a planted huge file; unreadable → empty → rc 1
    sha="$(head -c 128 -- "$file" 2>/dev/null)" || return 1
    [[ "$sha" =~ ^([0-9a-f]{40}|[0-9a-f]{64})$ ]] || return 1
    printf '%s' "$sha"
}

# aa_ma_sha_behind <repo> <sidecar-file>
#   The one shell "SHA vs HEAD" computation (report 03 X1; X2 does the same in
#   Python, codemem.incremental.check_freshness — both are tested against
#   tests/fixtures/code-intel/make-repo.sh). The sidecar is read by
#   aa_ma_read_sidecar_sha, and the SHA reaches git after --end-of-options.
#   The value itself is never printed. Safe to call under `set -e`: it prints
#   its reason before returning 1.
aa_ma_sha_behind() {
    local repo="$1" file="$2" sha n rc=0
    if ! sha="$(aa_ma_read_sidecar_sha "$file")"; then
        printf 'bad sha'
        return 1
    fi
    # why: 1 s caps a hung git well inside the SessionStart hook's 5 s timeout; a healthy call takes ~5 ms
    if command -v timeout > /dev/null 2>&1; then  # why: a presence probe (absent on stock macOS)
        n="$(timeout 1 git -C "$repo" -c core.fsmonitor=false rev-list --count --end-of-options "${sha}..HEAD" 2>/dev/null)" || rc=$?  # why: git's own error text is replaced by the reason below
    else
        n="$(git -C "$repo" -c core.fsmonitor=false rev-list --count --end-of-options "${sha}..HEAD" 2>/dev/null)" || rc=$?  # why: as above
    fi
    if [[ "$rc" -eq 124 ]]; then
        printf 'git timeout'
        return 1
    fi
    if [[ "$rc" -ne 0 || ! "$n" =~ ^[0-9]+$ ]]; then
        if git -C "$repo" rev-parse --git-dir > /dev/null 2>&1; then  # why: a probe — only its exit status is read
            printf 'not in history'
        else
            printf 'git failed'
        fi
        return 1
    fi
    printf '%s' "$n"
}

# -----------------------------------------------------------------------------
# End of aa-ma-parse.sh
# -----------------------------------------------------------------------------

