#!/usr/bin/env bats
# aa-ma-gate-scans.bats — regression guards on the awk that is LEFT in the
# shipped command/skill files, and on the two display readers.
#
# History. This file once tested a bash-side milestone-block extractor, field
# readers and a strict ACTIVE derivation that the §6.7 / §7.1 gate scans were
# built on. Three §6.8 passes over that awk found 8, 4, then 9 CRITICALs — the
# remediation round producing more than it closed — and milestone-grammar-ssot
# M5 moved every enforcing read to the Python SSoT (`aa-ma-gate`, see
# tests/hooks/aa-ma-gate-python.bats, which EXECUTES the shipped fences). The
# helpers and their tests are gone. What remains here:
#
#   1. guards that the two original defects never come back into the command
#      file as live code — the self-terminating awk range and the `grep -A1`
#      Gate read, both documented in comments there, so the guards look at
#      executable lines only;
#   2. the GNU-only `\s` guard (mawk matches nothing for it, silently);
#   3. the tolerant DISPLAY reader, which aa-ma-session-start.sh depends on and
#      which must never treat a prose H2 as a milestone; identical under gawk
#      and mawk.

setup() {
    REPO_ROOT="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)"
    HELPER="${REPO_ROOT}/claude-code/hooks/lib/aa-ma-parse.sh"
    MILESTONE_CMD="${REPO_ROOT}/claude-code/commands/execute-aa-ma-milestone.md"
    VERIFY_IMPL="${REPO_ROOT}/claude-code/skills/verify-impl/SKILL.md"
    FIXTURE="${BATS_TEST_DIRNAME}/fixtures/gate-scans/styles-tasks.md"
    FIX_ONE="${BATS_TEST_DIRNAME}/fixtures/gate-scans/one-active-tasks.md"
    FIX_NONE="${BATS_TEST_DIRNAME}/fixtures/gate-scans/no-active-tasks.md"
    export REPO_ROOT HELPER MILESTONE_CMD VERIFY_IMPL FIXTURE FIX_ONE FIX_NONE
}

teardown() {
    unset AA_MA_PARSE_SH_LOADED 2>/dev/null || true
}

load_helper() {
    # shellcheck disable=SC1090
    . "$HELPER"
}

# ---------------------------------------------------------------------------
# Portability — Debian/Ubuntu default awk is mawk, which lacks GNU extensions
# ---------------------------------------------------------------------------

@test "the display reader produces identical results under mawk and gawk" {
    load_helper
    local tested=0 first=""
    for bin in mawk gawk; do
        command -v "$bin" >/dev/null 2>&1 || continue
        # Shim `awk` to the specific implementation via PATH, so the helper
        # resolves it exactly as it would on a host where that is the default.
        # mktemp, not a fixed path: a fixed $BATS_TMPDIR/shim-$bin persisted
        # between runs and a symlink there once made another test's
        # `printf > $shim/awk` follow through to /usr/bin/mawk (EACCES).
        local shim; shim=$(mktemp -d "${BATS_TMPDIR}/shim-XXXXXX")
        printf '#!/bin/sh\nexec %s "$@"\n' "$(command -v "$bin")" > "$shim/awk"
        chmod +x "$shim/awk"
        local got
        got=$(PATH="$shim:$PATH" aa_ma_extract_active_milestone "$FIXTURE")
        rm -rf "$shim"
        [ -n "$got" ] || { echo "$bin returned nothing" >&2; false; }
        if [ -z "$first" ]; then first="$got"; else
            [ "$got" = "$first" ] || { echo "$bin: '$got' != '$first'" >&2; false; }
        fi
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

@test "no executable awk is left in the command file or verify-impl" {
    # The enforcing awk is gone; what is documented in comments stays. If a
    # future edit puts an awk back on an executable line, this is the alarm.
    for f in "$MILESTONE_CMD" "$VERIFY_IMPL"; do
        if _exec_lines "$f" | grep -qE '(^|[^a-z_])awk( |$)'; then
            echo "executable awk found in $f — enforcing reads belong in src/aa_ma/gate.py" >&2
            false
        fi
    done
}

@test "every bash snippet in the command file is syntactically valid" {
    awk '/^```bash$/{f=1;next} /^```$/{f=0;print "";next} f' "$MILESTONE_CMD" \
        > "$BATS_TMPDIR/snippets.sh"
    run bash -n "$BATS_TMPDIR/snippets.sh"
    [ "$status" -eq 0 ]
}

# ---------------------------------------------------------------------------
# The tolerant DISPLAY reader (sub-step 4.7)
#
# aa_ma_extract_active_milestone opened a block on bare /^## /, the third
# grammar in a file whose purpose after M1 is to hold one. It now opens only on
# AA_MA_MILESTONE_ERE. Display-only: aa-ma-session-start.sh depends on it, and
# the §6.7 gate must never (again) be wired to it — see the library header.
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
