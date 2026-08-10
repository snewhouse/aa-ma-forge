#!/usr/bin/env bash
# aa-ma-parse.sh — Shared helper library for AA-MA hooks.
#
# Source this file (don't execute it):
#     . "$(dirname "$0")/lib/aa-ma-parse.sh"
#
# Exports:
#     aa_ma_is_disabled                       -> 0 if AA_MA_HOOKS_DISABLE=1 set, else 1
#     aa_ma_extract_active_milestone <file>   -> stdout: active milestone heading text
#     aa_ma_extract_active_step <file>        -> stdout: active step heading text
#     aa_ma_list_active_tasks                 -> stdout: mtime-sorted task-dir paths, one per line
#     aa_ma_debug <msg...>                    -> stderr line iff HOOK_DEBUG=1
#     AA_MA_PARSE_SH_LOADED                   -> set to 1 once sourced (re-source guard)
#     AA_MA_MILESTONE_ERE                     -> ERE mirroring grammar.py MILESTONE_RE
#     aa_ma_is_milestone_heading <line>       -> rc 0 if the line is a milestone heading
#     aa_ma_extract_milestone_block <file> <title>   -> block; rc 0/1/2/3
#     aa_ma_extract_milestone_block_by_number <file> <num> -> block; rc 0/1/2/3
#     aa_ma_field_value <name>   (stdin: block) -> first value, bold or plain
#     aa_ma_count_field <name> <value> (stdin: block) -> count of matching lines
#     aa_ma_active_milestone_strict <file>    -> the ONE ACTIVE milestone; rc 0/1/2/3
#
# This header is the discovery surface: it is the first thing anyone sourcing
# the library reads, and a symbol missing from it gets reimplemented instead of
# reused. `tests/hooks/aa-ma-parse.bats` asserts every public symbol appears
# here, so the list cannot drift from the definitions below.
#
# Implementation notes:
#   - Format-agnostic Status regex: (\*\*)?Status:(\*\*)? +<WORD>
#     Accepts bold "**Status:** X" and plain "Status: X".
#   - HTML comments (<!-- ... -->) stripped before pattern-matching so block
#     examples in task files don't produce false positives.
#   - Milestone/step extraction uses an awk state machine instead of `grep -B2`
#     to avoid fragile line-context lookups across blank lines.
#   - Task listing iterates project-local `.claude/dev/active/` first, then
#     `$HOME/.claude/dev/active/`. Collisions resolve to project-local.
#     mtime order comes from `ls -t` on each task's `*-tasks.md` file.

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

# aa_ma_is_milestone_heading <line> — rc 0 if the line is a milestone heading.
#
# AA_MA_MILESTONE_ERE alone is the *prefix* pattern (block extraction strips it
# with `sub()` to recover the title, so it must not consume the title's first
# character). Recognition additionally requires a non-empty title, matching
# grammar.py's `(?P<title>.+?)`. Without this, `## Milestone 5:` is a heading in
# bash and is not one in Python — measured, and the reason this predicate exists
# rather than callers re-deriving it. `tests/test_grammar_parity.py` pins the
# two implementations against each other through this function.
# -----------------------------------------------------------------------------
aa_ma_is_milestone_heading() {
    printf '%s\n' "$1" | awk -v mre="$AA_MA_MILESTONE_ERE" '
        $0 ~ mre {
            t = $0
            sub(mre, "", t)
            gsub(/^[[:blank:]]+|[[:blank:]]+$/, "", t)
            if (t != "") { found = 1 }
        }
        END { exit found ? 0 : 1 }
    '
}

# -----------------------------------------------------------------------------
# _aa_ma_sanitize <file> — blank out everything that can look like markup
# without being it: fenced code blocks and HTML comments, the latter multi-line.
#
# Deliberately separate from `_aa_ma_strip_html_comments`, which is single-line
# only and is left untouched because `aa_ma_extract_active_milestone` and
# `aa_ma_extract_active_step` are pinned to its behaviour by existing tests.
#
# Both classes were measured to truncate a milestone block, and the second is
# live: three tasks.md files in this repo carry multi-line comments today, and
# `docs/templates/tasks-template.md` ships ten. A commented-out or
# fence-illustrated `## Milestone N:` line closed the block early, so the gate
# read zero PENDING sub-steps on a milestone that had them.
#
# Written without regex interval expressions (`{0,3}`) or multibyte classes so
# it behaves identically under gawk, mawk and busybox awk. Lines are blanked,
# never dropped, so line numbering is preserved for callers that care.
# -----------------------------------------------------------------------------
_aa_ma_sanitize() {
    awk '
        function fence_marker(line,   ind, rest, ch, k) {
            ind = 0
            while (substr(line, ind + 1, 1) == " " && ind < 4) ind++
            if (ind > 3) return ""
            rest = substr(line, ind + 1)
            ch = substr(rest, 1, 1)
            if (ch != "`" && ch != "~") return ""
            k = 0
            while (substr(rest, k + 1, 1) == ch) k++
            if (k < 3) return ""
            return ch ":" k
        }
        {
            line = $0
            if (incomment) {
                p = index(line, "-->")
                if (p == 0) { print ""; next }
                line = substr(line, p + 3)
                incomment = 0
            }
            while ((s = index(line, "<!--")) > 0) {
                e = index(substr(line, s + 4), "-->")
                if (e == 0) { line = substr(line, 1, s - 1); incomment = 1; break }
                line = substr(line, 1, s - 1) substr(line, s + 4 + e + 2)
            }
            m = fence_marker(line)
            if (!infence) {
                if (m != "") {
                    split(m, a, ":"); fch = a[1]; fk = a[2] + 0
                    infence = 1; print ""; next
                }
                print line; next
            }
            if (m != "") {
                split(m, a, ":")
                if (a[1] == fch && a[2] + 0 >= fk) infence = 0
            }
            print ""
        }
    ' "$1"
}

# -----------------------------------------------------------------------------
# aa_ma_field_value <field-name>   — reads a milestone block on STDIN
# aa_ma_count_field <field-name> <value>
#
#   Tolerate every field form the corpus actually uses. Measured across
#   .claude/dev/**/*-tasks.md: 435 `- Status:` but 22 `- **Status:**`, and
#   43 `- Gate:` against 24 `- **Gate:**`. The gate previously matched only the
#   plain form, so 24 of 67 `Gate:` declarations were invisible to it — and the
#   shipped Phase 5 writer
#   (skills/aa-ma-plan-workflow/references/PHASE_5_ARTIFACT_CREATION.md) emits
#   the BOLD form, so a plan authored through the standard path was born
#   un-gateable.
#
#   `aa_ma_extract_active_milestone` above already used `(\*\*)?Status:(\*\*)?`
#   — the library knew about bold; the gate did not.
# -----------------------------------------------------------------------------
_aa_ma_field_re() {
    printf '^[-[:blank:]]*[*]{0,2}%s[*]{0,2}:[*]{0,2}[[:blank:]]+' "$1"
}

# -----------------------------------------------------------------------------
# _AA_MA_VALUE_NORM — awk prelude defining aa_ma_norm(line, re).
#
# ONE definition of "given a field line and its pattern, what is the value".
# Every consumer prepends this rather than re-inlining sub()+gsub(), because
# each hand-rolled copy has drifted at least once: `aa_ma_active_milestone_strict`
# shipped a matcher permitting a dash then blanks but not blanks then a dash,
# so `  - Status: ACTIVE` was invisible to it while `_aa_ma_field_re` and the
# Python SSoT both accepted it — walking straight past the rc-3 ambiguity
# refusal and certifying the wrong milestone.
#
# The bold-pair strip is not cosmetic: `- Status: **PENDING**` is a form the
# corpus carries, and an unstripped value never equals "PENDING", so the gate
# counted zero pending sub-steps on a milestone that had them.
#
# Interval expressions `{0,2}` in _aa_ma_field_re are verified against mawk
# 1.3.4 as well as gawk — measured 5/5 on the full form table, not assumed.
# -----------------------------------------------------------------------------
_AA_MA_VALUE_NORM='
function aa_ma_norm(line, re,   v) {
    v = line
    sub(re, "", v)
    gsub(/^[[:blank:]]+|[[:blank:]]+$/, "", v)
    if (v ~ /^[*][*].*[*][*]$/) {
        v = substr(v, 3, length(v) - 4)
        gsub(/^[[:blank:]]+|[[:blank:]]+$/, "", v)
    }
    return v
}'

aa_ma_field_value() {
    awk -v re="$(_aa_ma_field_re "$1")" "${_AA_MA_VALUE_NORM}"'
        $0 ~ re { print aa_ma_norm($0, re); exit }
    '
}

aa_ma_count_field() {
    awk -v re="$(_aa_ma_field_re "$1")" -v want="$2" "${_AA_MA_VALUE_NORM}"'
        $0 ~ re { if (aa_ma_norm($0, re) == want) c++ }
        END { print c + 0 }
    '
}

# -----------------------------------------------------------------------------
# aa_ma_extract_milestone_block <tasks-file> <milestone-title>
#   Emits every line of the milestone whose heading contains <milestone-title>,
#   from the heading up to (not including) the next milestone heading, or EOF.
#   EXIT CODES — the point of this function. A gate whose only refusal signal is
#   *finding* something treats every parse failure as a clean milestone, so the
#   caller must be able to tell "nothing to report" from "I could not read it":
#     0  exactly one heading matched; block on stdout
#     1  no milestone heading carries that title
#     2  configuration error — file missing, or empty title
#     3  ambiguous — more than one heading carries that title
#   Callers MUST refuse on non-zero. Returning 0-and-empty for cases 1-3, as the
#   first version did, is the fail-open shape this milestone exists to remove.
#
#   Title matching is EXACT on the heading's title portion, not a substring.
#   `index($0, title)` took the first heading merely *containing* the title, so
#   with "## Milestone 1: Gate scans and grammar" preceding
#   "## Milestone 2: Gate scans", asking for "Gate scans" silently scanned
#   milestone 1 — reporting its SOFT gate and zero PENDING for milestone 2.
#
#   Replaces `awk "/^## Milestone.*$TITLE/,/^## Milestone/"`, which returned
#   exactly ONE line for every milestone in every plan: the start line also
#   matches the end pattern, and awk evaluates the end pattern on the same
#   record, so the range closed immediately. Every field scan built on it —
#   Status: PENDING counts, Critical-Path, Prototype-Required — read empty, and
#   the §6.7 gate could not refuse anything.
#
#   Start and end conditions are deliberately ASYMMETRIC:
#     * opens only on a heading matching AA_MA_MILESTONE_ERE (strict — prose
#       like "## Summary Counts" must never open a milestone block);
#     * closes on ANY H2 (tolerant — a milestone ends where the next level-2
#       section begins, whatever that section is).
#   Closing only on milestone headings looks symmetric and is wrong: the last
#   milestone in a file then runs to EOF and swallows the trailing "## Summary
#   Counts" section, whose prose contains literal "- Status: PENDING",
#   "- Gate: HARD" and Critical-Path lines. Measured on this plan's own
#   tasks.md, that inflated the last milestone's pending count by one and
#   handed the gate a Critical-Path value from prose. Sub-steps are H3, so they
#   are unaffected.
# -----------------------------------------------------------------------------
aa_ma_extract_milestone_block() {
    local file="$1" title="$2"
    [ -f "$file" ] || return 2
    [ -n "$title" ] || return 2
    # The title is FILE CONTENT and must reach awk byte-for-byte. POSIX awk
    # performs escape-sequence processing on -v assignments, so `-v title="$title"`
    # silently transforms it: a plan with `## Milestone 1: a\tb` (1 PENDING,
    # Gate: HARD) and `## Milestone 1: a<TAB>b` (COMPLETE, SOFT) made the strict
    # derivation name the first and this scan return the second — PENDING=0,
    # GATE=SOFT, a false PASS. The benign half is just as real: a milestone
    # titled `Fix \t handling in parser` produced rc 1 here, so the gate blocked
    # a valid plan citing a milestone it had derived itself. ENVIRON is not
    # escape-processed; -v remains fine for our own literal patterns.
    AA_MA_TITLE="$title" _aa_ma_sanitize "$file" \
        | AA_MA_TITLE="$title" awk -v mre="$AA_MA_MILESTONE_ERE" '
        BEGIN { title = ENVIRON["AA_MA_TITLE"] }
        /^##[[:blank:]]/ { if (inblk) inblk = 0 }
        $0 ~ mre {
            t = $0
            sub(mre, "", t)
            gsub(/^[[:blank:]]+|[[:blank:]]+$/, "", t)
            # Accept either the title portion ("Close the gate blindness") or the
            # whole heading minus "## " ("Milestone 4: Close the gate blindness").
            # aa_ma_extract_active_milestone returns the latter, and passing it
            # straight in is the obvious thing a caller does — it is what the
            # §6.7 preamble does. Matching only the title made that combination
            # return "no such milestone", which the new exit codes surfaced as a
            # BLOCK rather than as a silent pass.
            h = $0
            sub(/^##[[:blank:]]+/, "", h)
            gsub(/^[[:blank:]]+|[[:blank:]]+$/, "", h)
            if (t == title || h == title) { n++; inblk = 1 }
        }
        inblk { buf = buf $0 "\n" }
        END {
            printf "%s", buf
            if (n == 0) exit 1
            if (n > 1) exit 3
            exit 0
        }
    '
}

# -----------------------------------------------------------------------------
# aa_ma_extract_milestone_block_by_number <tasks-file> <number>
#   As above, but addressed by milestone number (`2`, `2a`, `3.5`) rather than
#   title. Same exit codes.
#
#   Exists because `verify-impl` keyed its own range on arithmetic:
#     awk "/^## ...M?$N(:|[[:blank:]])/,/^## ...M?$((N+1))(:|[[:blank:]])|^---$/"
#   `$((N+1))` is a hard bash error for the milestone numbers M1 legitimised —
#   `2a: value too great for base` — and the corpus ships `## Milestone 2a/2b/2c`.
#   The `|^---$` alternative also truncated any milestone containing a
#   horizontal rule. Neither failure was visible: the caller read an empty block
#   and reported `MISSING`.
# -----------------------------------------------------------------------------
aa_ma_extract_milestone_block_by_number() {
    local file="$1" number="$2" esc
    [ -f "$file" ] || return 2
    [ -n "$number" ] || return 2
    # Literal-match the number; only `.` is an ERE metacharacter in this grammar.
    esc=$(printf '%s' "$number" | sed 's/[.]/[.]/g')
    _aa_ma_sanitize "$file" | awk \
        -v mre="$AA_MA_MILESTONE_ERE" \
        -v nre="^##[[:blank:]]+(Milestone[[:blank:]]+M?|M)${esc}(:|[[:blank:]]+(-|–|—)[[:blank:]]+)" '
        /^##[[:blank:]]/ { if (inblk) inblk = 0 }
        $0 ~ mre { if ($0 ~ nre) { n++; inblk = 1 } }
        inblk { buf = buf $0 "\n" }
        END {
            printf "%s", buf
            if (n == 0) exit 1
            if (n > 1) exit 3
            exit 0
        }
    '
}

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
# aa_ma_active_milestone_strict <tasks-file>
#   Emits the ONE milestone whose own Status field is ACTIVE, heading text
#   stripped of "## ". Exit codes:
#     0  exactly one — the only case a gate may act on
#     1  none ACTIVE
#     2  file missing, unreadable, or no path given
#     3  more than one ACTIVE; ALL of them are printed so the caller can name
#        them in its refusal
#
# Why this exists alongside aa_ma_extract_active_milestone. That function is a
# *display* helper: it takes the first match and falls back to the first
# pending milestone, so it always answers, which is right for a session
# briefing and wrong for a gate. Wiring the §6.7 gate to it (sub-step 4.5)
# meant that with a stale second `Status: ACTIVE` the gate derived the WRONG
# milestone: measured reporting PENDING=0 / GATE=SOFT while certifying a
# milestone that was 1 PENDING / Gate: HARD. Every other defect this milestone
# closed produced a false BLOCK; that one produced a false PASS.
#
# Only the milestone's OWN Status counts — fields between the `##` heading and
# the first `###` sub-step. A sub-step left ACTIVE is normal mid-milestone and
# must not make its parent a derivation candidate, nor make two milestones look
# simultaneously active. Same first-block-wins convention as aa_ma_field_value.
# -----------------------------------------------------------------------------
aa_ma_active_milestone_strict() {
    local file="${1:-}" out rc
    { [ -n "$file" ] && [ -f "$file" ] && [ -r "$file" ]; } || return 2
    out=$(_aa_ma_sanitize "$file" \
        | awk -v mre="$AA_MA_MILESTONE_ERE" -v sre="$(_aa_ma_field_re Status)" \
              "${_AA_MA_VALUE_NORM}"'
        /^##[^#]/ {
            current = ""; in_header = 0
            if ($0 ~ mre) {
                t = $0; sub(mre, "", t)
                gsub(/^[[:blank:]]+|[[:blank:]]+$/, "", t)
                if (t != "") {
                    current = $0
                    sub(/^##[[:blank:]]+/, "", current)
                    gsub(/[[:blank:]]+$/, "", current)
                    in_header = 1
                }
            }
            next
        }
        /^###/ { in_header = 0; next }
        in_header && $0 ~ sre {
            if (aa_ma_norm($0, sre) == "ACTIVE") { print current; n++; in_header = 0 }
        }
        END { exit (n == 0 ? 1 : (n > 1 ? 3 : 0)) }
    ')
    rc=$?
    [ -n "$out" ] && printf '%s\n' "$out"
    return "$rc"
}

# -----------------------------------------------------------------------------
# End of aa-ma-parse.sh
# -----------------------------------------------------------------------------
