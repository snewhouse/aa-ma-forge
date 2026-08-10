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
    export REPO_ROOT HELPER MILESTONE_CMD VERIFY_IMPL FIXTURE
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
    # The bug this replaces reported 0 for all of them.
    [ "$(aa_ma_extract_milestone_block "$FIXTURE" "Canonical form" \
        | grep -cE '^- Status: PENDING')" -eq 0 ]
    [ "$(aa_ma_extract_milestone_block "$FIXTURE" "Bare-M form" \
        | grep -cE '^- Status: PENDING')" -eq 1 ]
    [ "$(aa_ma_extract_milestone_block "$FIXTURE" "Em-dash form" \
        | grep -cE '^- Status: PENDING')" -eq 2 ]
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
    [ "$(aa_ma_extract_milestone_block "$FIXTURE" "Em-dash form" \
        | grep -oE '^- Gate: [A-Z]+' | head -1 | awk '{print $3}')" = "HARD" ]
    [ "$(aa_ma_extract_milestone_block "$FIXTURE" "Canonical form" \
        | grep -oE '^- Gate: [A-Z]+' | head -1 | awk '{print $3}')" = "SOFT" ]
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
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "'## Milestone Gate Types' — the word without a number — opens no block" {
    load_helper
    run aa_ma_extract_milestone_block "$FIXTURE" "Milestone Gate Types"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "an empty title matches nothing rather than everything" {
    load_helper
    run aa_ma_extract_milestone_block "$FIXTURE" ""
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "a missing file is not an error and emits nothing" {
    load_helper
    run aa_ma_extract_milestone_block "/nonexistent/tasks.md" "Canonical form"
    [ "$status" -eq 0 ]
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
    # Guard against the loop silently testing nothing.
    [ "$tested" -ge 1 ]
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

@test "command file no longer uses the self-terminating awk range" {
    # /^## Milestone.../,/^## Milestone/ — the start line matches the end
    # pattern, so the range is one line and every field scan reads empty.
    ! grep -nF ',/^## Milestone/' "$MILESTONE_CMD"
}

@test "command file no longer extracts Gate with grep -A1" {
    ! grep -nE 'grep -A1 .*## Milestone' "$MILESTONE_CMD"
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
