#!/usr/bin/env bats
# aa-ma-gate-scans.bats — the §6.7 / §7.1 gate scans in
# claude-code/commands/execute-aa-ma-milestone.md.
#
# Why this file exists. Every one of those scans was measured broken before
# this suite was written, and not for the reason the plan predicted:
#
#   1. `awk "/^## Milestone.*$TITLE/,/^## Milestone/"` self-terminates. The
#      start line ALSO matches the end pattern, and awk evaluates the end
#      pattern on the same record — so the range is exactly one line, the
#      heading. Measured against the real milestone-grammar-ssot tasks.md:
#      0 pending sub-steps reported where 6 exist, Critical-Path empty on a
#      milestone that declares it. Style-independent: it fails on the
#      canonical heading form too.
#   2. `grep -A1 "## Milestone.*$TITLE" | grep -oP 'Gate: \K\w+'` cannot reach
#      the `- Gate:` line, because a blank line separates it from the heading.
#      Measured: GATE='' on a `Gate: HARD` milestone, so §7.1 never enforced a
#      HARD gate at all.
#   3. Only after those: the patterns are also blind to `## M1:` and
#      `## Milestone 1 — Title`, which four archived plans use.
#
# The fix moves block extraction into aa_ma_extract_milestone_block() so there
# is one bash-side implementation to test, mirroring what src/aa_ma/grammar.py
# did for the Python side. These tests drive the helper directly and assert the
# command file delegates to it.

setup() {
    REPO_ROOT="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)"
    HELPER="${REPO_ROOT}/claude-code/hooks/lib/aa-ma-parse.sh"
    MILESTONE_CMD="${REPO_ROOT}/claude-code/commands/execute-aa-ma-milestone.md"
    VERIFY_IMPL="${REPO_ROOT}/claude-code/skills/verify-impl/SKILL.md"
    FIXTURE="${BATS_TEST_DIRNAME}/fixtures/gate-scans/styles-tasks.md"
    FIX_ONE="${BATS_TEST_DIRNAME}/fixtures/gate-scans/one-active-tasks.md"
    FIX_TWO="${BATS_TEST_DIRNAME}/fixtures/gate-scans/two-active-tasks.md"
    FIX_NONE="${BATS_TEST_DIRNAME}/fixtures/gate-scans/no-active-tasks.md"
    export REPO_ROOT HELPER MILESTONE_CMD VERIFY_IMPL FIXTURE FIX_ONE FIX_TWO FIX_NONE
}

teardown() {
    unset AA_MA_PARSE_SH_LOADED 2>/dev/null || true
}

load_helper() {
    # shellcheck disable=SC1090
    . "$HELPER"
}

# ---------------------------------------------------------------------------
# Block extraction — every heading style the tolerant reader accepts
# ---------------------------------------------------------------------------

@test "extractor finds the canonical '## Milestone N: Title' form" {
    load_helper
    run aa_ma_extract_milestone_block "$FIXTURE" "Canonical form"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Sub-step 1.1"* ]]
    # Must stop at the next milestone, not run to EOF.
    [[ "$output" != *"Bare-M form"* ]]
}

@test "extractor finds the bare '## M2: Title' form" {
    load_helper
    run aa_ma_extract_milestone_block "$FIXTURE" "Bare-M form"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Sub-step 2.1"* ]]
    [[ "$output" != *"Milestone-M form"* ]]
}

@test "extractor finds the '## Milestone M3: Title' form" {
    load_helper
    run aa_ma_extract_milestone_block "$FIXTURE" "Milestone-M form"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Sub-step 3.1"* ]]
}

@test "extractor finds the em-dash '## Milestone 4 — Title' form" {
    load_helper
    run aa_ma_extract_milestone_block "$FIXTURE" "Em-dash form"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Sub-step 4.1"* ]]
    [[ "$output" == *"Sub-step 4.2"* ]]
}

# ---------------------------------------------------------------------------
# The three §6.7 field scans, per style
# ---------------------------------------------------------------------------

@test "PENDING count is correct in every heading style (was always 0)" {
    load_helper
    # Only non-zero expectations here. An `-eq 0` case cannot fail for the
    # regression this test names: the broken extractor returned 0, and so does
    # an empty block. The zero case lives in the bleed test below, where it is
    # paired with evidence the block was actually read.
    [ "$(aa_ma_extract_milestone_block "$FIXTURE" "Bare-M form" \
        | aa_ma_count_field Status PENDING)" -eq 1 ]
    [ "$(aa_ma_extract_milestone_block "$FIXTURE" "Em-dash form" \
        | aa_ma_count_field Status PENDING)" -eq 2 ]
    [ "$(aa_ma_extract_milestone_block "$FIXTURE" "Bold field forms" \
        | aa_ma_count_field Status PENDING)" -eq 1 ]
}

@test "bold field forms are read — 22 Status / 24 Gate in the corpus use them" {
    load_helper
    # The shipped Phase 5 writer emits `- **Status:** PENDING`, so a
    # plain-form-only gate made standard-path plans un-gateable.
    run aa_ma_extract_milestone_block "$FIXTURE" "Bold field forms"
    [ "$status" -eq 0 ]
    [ "$(printf '%s\n' "$output" | aa_ma_field_value Gate)" = "HARD" ]
    [ "$(printf '%s\n' "$output" | aa_ma_field_value Critical-Path)" = "version-pipeline" ]
    [ "$(printf '%s\n' "$output" | aa_ma_count_field Status PENDING)" -eq 1 ]
}

@test "a heading inside a fence or a multi-line comment does not truncate" {
    load_helper
    run aa_ma_extract_milestone_block "$FIXTURE" "Ghost headings must not truncate"
    [ "$status" -eq 0 ]
    # Reached only if neither ghost closed the block early.
    [[ "$output" == *"Sub-step 6.1"* ]]
    # ...and the ghosts' own PENDING lines must not be counted.
    [ "$(printf '%s\n' "$output" | aa_ma_count_field Status PENDING)" -eq 1 ]
}

@test "a duplicate milestone title is refused, not silently resolved" {
    load_helper
    run aa_ma_extract_milestone_block "$FIXTURE" "Duplicate title"
    [ "$status" -eq 3 ]
}

@test "exit codes distinguish every not-found case from a clean milestone" {
    load_helper
    run aa_ma_extract_milestone_block "$FIXTURE" "Canonical form"; [ "$status" -eq 0 ]
    run aa_ma_extract_milestone_block "$FIXTURE" "No such milestone"; [ "$status" -eq 1 ]
    run aa_ma_extract_milestone_block "/nonexistent/tasks.md" "X"; [ "$status" -eq 2 ]
    run aa_ma_extract_milestone_block "$FIXTURE" ""; [ "$status" -eq 2 ]
    run aa_ma_extract_milestone_block "$FIXTURE" "Duplicate title"; [ "$status" -eq 3 ]
}

@test "by-number extraction survives 2a and 3.5 (bash arithmetic could not)" {
    load_helper
    # verify-impl used $((N+1)); `2a` is a hard bash error, and the corpus ships
    # ## Milestone 2a/2b/2c.
    local corpus="${REPO_ROOT}/.claude/dev/completed/codemem-benchmark-fairness-v2/codemem-benchmark-fairness-v2-tasks.md"
    [ -f "$corpus" ] || skip "corpus plan not present"
    run aa_ma_extract_milestone_block_by_number "$corpus" "2a"
    [ "$status" -eq 0 ]
    [ -n "$output" ]
    run aa_ma_extract_milestone_block_by_number "$corpus" "99"
    [ "$status" -eq 1 ]
}

@test "Critical-Path is found, and only in the milestone that declares it" {
    load_helper
    aa_ma_extract_milestone_block "$FIXTURE" "Bare-M form" \
        | grep -qE '^- \*\*Critical-Path:\*\* data-xform'
    aa_ma_extract_milestone_block "$FIXTURE" "Em-dash form" \
        | grep -qE '^- \*\*Critical-Path:\*\* hook-modification'
    # Bleed check: the canonical milestone declares none, and must not inherit
    # one from a neighbouring block.
    ! aa_ma_extract_milestone_block "$FIXTURE" "Canonical form" \
        | grep -qE '^- \*\*Critical-Path:\*\*'
}

@test "Prototype-Required is found, and only where declared" {
    load_helper
    aa_ma_extract_milestone_block "$FIXTURE" "Milestone-M form" \
        | grep -qE '^- \*\*Prototype-Required:\*\* YES'
    ! aa_ma_extract_milestone_block "$FIXTURE" "Bare-M form" \
        | grep -qE '^- \*\*Prototype-Required:\*\*'
}

@test "Gate is reachable past the blank line that broke grep -A1" {
    load_helper
    # The replaced form was: grep -A1 "## Milestone.*TITLE" | grep -oP 'Gate: \K\w+'
    # -A1 returns the heading plus one blank line, so GATE was always empty and
    # the HARD gate never fired.
    #
    # Uses aa_ma_field_value — the same function the shipped gate calls. An
    # earlier version of this test re-implemented the pipeline with `[A-Z]+`
    # while the shipped code used `[A-Za-z]+`, so it did not exercise the
    # shipped expression at all.
    [ "$(aa_ma_extract_milestone_block "$FIXTURE" "Em-dash form" \
        | aa_ma_field_value Gate)" = "HARD" ]
    [ "$(aa_ma_extract_milestone_block "$FIXTURE" "Canonical form" \
        | aa_ma_field_value Gate)" = "SOFT" ]
}

@test "a mixed-case Gate value still fires the HARD gate" {
    load_helper
    # `- Gate: Hard` extracted as "Hard"; the shipped test is
    # [[ "$GATE" == "HARD" ]], so without normalisation the HARD gate silently
    # does not fire. The command file upper-cases before comparing.
    raw=$(aa_ma_extract_milestone_block "$FIXTURE" "Mixed case gate" | aa_ma_field_value Gate)
    [ "$raw" = "Hard" ]
    [ "$(printf '%s' "$raw" | tr '[:lower:]' '[:upper:]')" = "HARD" ]
    grep -qF "tr '[:lower:]' '[:upper:]'" "$MILESTONE_CMD"
}

# ---------------------------------------------------------------------------
# Negative controls — fail closed
# ---------------------------------------------------------------------------

@test "an ordinary prose '## Summary Counts' heading opens no block" {
    load_helper
    # This heading deliberately contains literal 'Status: PENDING',
    # '- Gate: HARD' and a Critical-Path line. A scan that matched it would
    # report phantom pending sub-steps on a plan that has none.
    run aa_ma_extract_milestone_block "$FIXTURE" "Summary Counts"
    [ "$status" -eq 1 ]
    [ -z "$output" ]
}

@test "'## Milestone Gate Types' — the word without a number — opens no block" {
    load_helper
    run aa_ma_extract_milestone_block "$FIXTURE" "Milestone Gate Types"
    [ "$status" -eq 1 ]
    [ -z "$output" ]
}

@test "an empty title is a configuration error, not a clean milestone" {
    load_helper
    # rc 2, not 0. The first version returned 0-and-empty here, which the gate
    # read as "no PENDING sub-steps" — fail-open.
    run aa_ma_extract_milestone_block "$FIXTURE" ""
    [ "$status" -eq 2 ]
    [ -z "$output" ]
}

@test "a missing file is a configuration error, not a clean milestone" {
    load_helper
    run aa_ma_extract_milestone_block "/nonexistent/tasks.md" "Canonical form"
    [ "$status" -eq 2 ]
    [ -z "$output" ]
}

# ---------------------------------------------------------------------------
# Portability — Debian/Ubuntu default awk is mawk, which lacks GNU extensions
# ---------------------------------------------------------------------------

@test "extractor produces identical results under mawk and gawk" {
    load_helper
    local tested=0
    for bin in mawk gawk; do
        command -v "$bin" >/dev/null 2>&1 || continue
        # Shim `awk` to the specific implementation via PATH, so the helper
        # resolves it exactly as it would on a host where that is the default.
        local shim="$BATS_TMPDIR/shim-$bin"
        mkdir -p "$shim"
        printf '#!/bin/sh\nexec %s "$@"\n' "$(command -v "$bin")" > "$shim/awk"
        chmod +x "$shim/awk"
        local got
        got=$(PATH="$shim:$PATH" aa_ma_extract_milestone_block "$FIXTURE" "Em-dash form" \
                | grep -cE '^- Status: PENDING')
        [ "$got" -eq 2 ] || { echo "$bin returned $got PENDING, expected 2" >&2; false; }
        tested=$((tested + 1))
    done
    # BOTH must have run. `-ge 1` let a gawk-only host pass a test named
    # "identical results under mawk and gawk" having compared nothing across
    # implementations — the same green-by-skipping shape hardened against in
    # the Stage C CI job.
    [ "$tested" -eq 2 ]
}

@test "no shipped awk pattern uses the GNU-only \\s escape" {
    # mawk silently matches nothing for \s, so verify-impl's block extractor
    # returned an EMPTY milestone block on any Debian/Ubuntu default awk.
    #
    # Two things went wrong in the first version of this guard, both of which
    # made it report clean against a file that plainly contained \s:
    #
    #   1. The ERE 'awk .*\\\\s' matches a literal DOUBLE backslash. Use -F.
    #   2. `! cmd` is exempt from `set -e` (POSIX: "-e shall be ignored when
    #      the command is the ! reserved word"), so a non-final `! cmd` line in
    #      a bats test NEVER fails the test — only the last command's status is
    #      the verdict. Two stacked `!` lines meant the first was decorative.
    #
    # Hence the explicit if/false form below.
    for f in "$VERIFY_IMPL" "$MILESTONE_CMD"; do
        if grep -F 'awk' "$f" | grep -q -F '\s'; then
            echo "GNU-only \\s found in $f — mawk matches nothing for it" >&2
            false
        fi
    done
}

@test "the \\s guard is not vacuous" {
    # Mutation check: plant the GNU-ism and require the guard above to catch it.
    # Without this, an over-escaped pattern reports clean forever.
    local probe="$BATS_TMPDIR/probe.md"
    printf 'MILESTONE_BLOCK=$(awk "/^## (Milestone\\s+)?M?1/" f)\n' > "$probe"
    grep -n -F 'awk' "$probe" | grep -q -F '\s'
}

# ---------------------------------------------------------------------------
# Regression guards on the shipped command file
# ---------------------------------------------------------------------------

# Executable lines only — the fixed command file *documents* both broken
# patterns in comments so the next reader knows why they went. A guard that
# greps the whole file would flag its own explanation.
_exec_lines() {
    # Accepts every fence tag the file uses — a snippet retagged ```sh would
    # otherwise drop silently out of both regression guards below. Trailing
    # comments are stripped too, so `X=1  # ,/^## Milestone/` is not a false
    # positive.
    awk '/^```(bash|sh|shell)$/{f=1;next} /^```$/{f=0;next} f' "$1" \
        | grep -vE '^[[:space:]]*#' \
        | sed 's/[[:space:]]#[^"'"'"']*$//'
}

@test "command file no longer uses the self-terminating awk range" {
    # /^## Milestone.../,/^## Milestone/ — the start line matches the end
    # pattern, so the range is one line and every field scan reads empty.
    if _exec_lines "$MILESTONE_CMD" | grep -q -F ',/^## Milestone/'; then
        echo "self-terminating awk range still live in $MILESTONE_CMD" >&2
        false
    fi
}

@test "command file no longer extracts Gate with grep -A1" {
    if _exec_lines "$MILESTONE_CMD" | grep -qE 'grep -A1 .*## Milestone'; then
        echo "grep -A1 Gate extraction still live in $MILESTONE_CMD" >&2
        false
    fi
}

@test "the regression guards above are not vacuous" {
    # Both guards passed trivially at one point because the patterns they hunt
    # now appear in explanatory comments. Prove they still bite on live code.
    local probe="$BATS_TMPDIR/probe-cmd.md"
    {
        printf '```bash\n'
        printf '# a comment mentioning ,/^## Milestone/ and grep -A1 "## Milestone.*x"\n'
        printf 'X=$(awk "/^## Milestone.*$T/,/^## Milestone/" f)\n'
        printf 'G=$(grep -A1 "## Milestone.*$T" f)\n'
        printf '```\n'
    } > "$probe"
    _exec_lines "$probe" | grep -q -F ',/^## Milestone/'
    _exec_lines "$probe" | grep -qE 'grep -A1 .*## Milestone'
    # ...and that the comment line alone would NOT trigger them.
    [ "$(_exec_lines "$probe" | grep -c '^#')" -eq 0 ]
}

@test "command file delegates block extraction to the shared helper" {
    grep -qF "aa_ma_extract_milestone_block" "$MILESTONE_CMD"
}

@test "every bash snippet in the command file is syntactically valid" {
    awk '/^```bash$/{f=1;next} /^```$/{f=0;print "";next} f' "$MILESTONE_CMD" \
        > "$BATS_TMPDIR/snippets.sh"
    run bash -n "$BATS_TMPDIR/snippets.sh"
    [ "$status" -eq 0 ]
}

@test "the block extractor accepts what aa_ma_extract_active_milestone returns" {
    load_helper
    # Integration seam, found by the gate refusing to certify M4 of its own plan:
    # aa_ma_extract_active_milestone returns the heading minus "## "
    # ("Milestone 4: Title"), the extractor was matching only the title portion,
    # and the §6.7 preamble pipes one straight into the other. rc 1 -> BLOCKED.
    # Under the old 0-and-empty contract this would have passed silently.
    local heading title
    heading=$(aa_ma_extract_active_milestone "$FIXTURE")
    [ -n "$heading" ]
    run aa_ma_extract_milestone_block "$FIXTURE" "$heading"
    [ "$status" -eq 0 ]

    # Both spellings must resolve to the same block.
    title="${heading#*: }"
    [ "$(aa_ma_extract_milestone_block "$FIXTURE" "$heading" | wc -l)" \
      -eq "$(aa_ma_extract_milestone_block "$FIXTURE" "$title" | wc -l)" ]
}

# ---------------------------------------------------------------------------
# Milestone DERIVATION — which milestone the gate believes it is certifying
#
# Sub-step 4.5 fixed the unset-MILESTONE_TITLE defect by wiring the gate to
# aa_ma_extract_active_milestone. That function takes the FIRST match and has
# no way to say "ambiguous", so with a stale second ACTIVE status the gate
# derived the wrong milestone and reported PENDING=0 / GATE=SOFT for a
# milestone that was 1 PENDING / Gate: HARD — a silent false PASS, which is
# the one failure direction none of this milestone's other defects produced.
#
# aa_ma_active_milestone_strict is the fail-closed replacement:
#   rc 0 -> exactly one ACTIVE milestone, heading (minus "## ") on stdout
#   rc 1 -> none ACTIVE
#   rc 2 -> file missing or unreadable
#   rc 3 -> more than one ACTIVE, all of them on stdout so the caller can name
#           them in the refusal
# ---------------------------------------------------------------------------

@test "strict derivation returns the single ACTIVE milestone" {
    load_helper
    run aa_ma_active_milestone_strict "$FIX_ONE"
    [ "$status" -eq 0 ]
    [ "$output" = "Milestone 2: The one being gated" ]
}

@test "strict derivation refuses when two milestones are ACTIVE" {
    load_helper
    run aa_ma_active_milestone_strict "$FIX_TWO"
    [ "$status" -eq 3 ]
    # Both must be named — a refusal that does not say which two is unactionable.
    [[ "$output" == *"Milestone 2: Older milestone left ACTIVE"* ]]
    [[ "$output" == *"Milestone 4: The one actually being gated"* ]]
}

@test "strict derivation refuses when no milestone is ACTIVE" {
    load_helper
    run aa_ma_active_milestone_strict "$FIX_NONE"
    [ "$status" -eq 1 ]
    # Specifically must NOT fall back to a prose H2.
    [[ "$output" != *"Summary Counts"* ]]
}

@test "strict derivation refuses on a missing file" {
    load_helper
    run aa_ma_active_milestone_strict "$BATS_TMPDIR/does-not-exist-$$.md"
    [ "$status" -eq 2 ]
}

@test "strict derivation ignores prose H2 sections entirely" {
    load_helper
    # The trailing "## Summary Counts" in FIX_ONE carries both a pending status
    # and Gate: HARD. It must never be a derivation candidate.
    run aa_ma_active_milestone_strict "$FIX_ONE"
    [ "$status" -eq 0 ]
    [[ "$output" != *"Summary"* ]]
}

@test "strict derivation output feeds the block extractor unchanged" {
    load_helper
    local heading
    heading=$(aa_ma_active_milestone_strict "$FIX_ONE")
    run aa_ma_extract_milestone_block "$FIX_ONE" "$heading"
    [ "$status" -eq 0 ]
    [[ "$output" == *"Sub-step 2.1"* ]]
    [[ "$output" != *"Summary Counts"* ]]
}

@test "the gate derives its milestone strictly, not from the tolerant reader" {
    # The §6.7 preamble must not resolve MILESTONE_TITLE via the tolerant
    # reader: that is what let it certify the wrong milestone.
    grep -qF "aa_ma_active_milestone_strict" "$MILESTONE_CMD"
    ! grep -qF 'MILESTONE_TITLE=$(aa_ma_extract_active_milestone' "$MILESTONE_CMD"
}

# ---------------------------------------------------------------------------
# One milestone grammar in aa-ma-parse.sh (sub-step 4.7)
#
# aa_ma_extract_active_milestone opened a block on bare /^## /, the third
# grammar in a file whose purpose after M1 is to hold one. Measured across the
# repo's 27 tasks files it changed exactly one row, a TUI fixture using
# "## Step N:" headings that grammar.py already matches 0 of 9 times.
# ---------------------------------------------------------------------------

@test "tolerant reader no longer treats a prose H2 as a milestone" {
    load_helper
    run aa_ma_extract_active_milestone "$FIX_NONE"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "tolerant reader still finds a real milestone" {
    load_helper
    # Non-breaking: the session-start hook depends on this path.
    run aa_ma_extract_active_milestone "$FIX_ONE"
    [ "$status" -eq 0 ]
    [ "$output" = "Milestone 2: The one being gated" ]
}

# ---------------------------------------------------------------------------
# One Status grammar (sub-step 4.10)
#
# aa_ma_active_milestone_strict shipped its own Status matcher,
# `^-?[[:blank:]]*(\*\*)?Status:...`, which permits a dash THEN blanks but not
# blanks THEN a dash. `  - Status: ACTIVE` was therefore invisible to it while
# _aa_ma_field_re and the Python SSoT both accept it — so the rc-3 ambiguity
# refusal could be walked straight past. Measured false PASS: gate reported
# PENDING=0 GATE=SOFT on a plan whose second ACTIVE milestone was 1 PENDING and
# Gate: HARD. Found by all three Phase 6.8 agents.
# ---------------------------------------------------------------------------

@test "strict derivation reads every Status form _aa_ma_field_re accepts" {
    load_helper
    local f="${BATS_TEST_DIRNAME}/fixtures/gate-scans/statusforms-tasks.md"
    run aa_ma_active_milestone_strict "$f"
    [ "$status" -eq 0 ]
    [ "$output" = "Milestone 2: Indented dash" ]
}

@test "strict derivation and aa_ma_field_value never disagree on a Status line" {
    load_helper
    local forms=(
        "- Status: ACTIVE"
        "  - Status: ACTIVE"
        "	- Status: ACTIVE"
        "- **Status**: ACTIVE"
        "- **Status:** ACTIVE"
        "- Status: **ACTIVE**"
    )
    local tested=0 form tmp
    for form in "${forms[@]}"; do
        tmp="$BATS_TMPDIR/form-$tested.md"
        printf '## Milestone 1: T\n\n%s\n' "$form" > "$tmp"
        # The permissive reader is the reference implementation.
        [ "$(aa_ma_field_value Status < "$tmp")" = "ACTIVE" ]
        run aa_ma_active_milestone_strict "$tmp"
        [ "$status" -eq 0 ]
        [ "$output" = "Milestone 1: T" ]
        tested=$((tested + 1))
    done
    [ "$tested" -eq 6 ]
}

@test "a bold-value PENDING sub-step is still counted by the gate" {
    load_helper
    local f="${BATS_TEST_DIRNAME}/fixtures/gate-scans/statusforms-tasks.md"
    [ "$(aa_ma_extract_milestone_block "$f" "Bold value" \
        | aa_ma_count_field Status PENDING)" -eq 1 ]
}
