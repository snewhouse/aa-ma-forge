#!/usr/bin/env bats
# aa-ma-gate-approval.bats — aa_ma_has_gate_approval, the block-scoped approval check shared by
# §7.1 (HARD gate) and §6.7 fence 3 (the `Test-Command: none` opt-out).
#
# The check it replaces was `grep -A8 -F "GATE APPROVAL: <title>" | grep Decision: APPROVED`,
# which read up to 8 lines past the heading — into the NEXT block. A REJECTED approval followed
# by another milestone's APPROVED one passed (M9 §6.6 review, verified by run).

bats_require_minimum_version 1.5.0

setup() {
    REPO_ROOT="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)"
    HELPER="${REPO_ROOT}/claude-code/hooks/lib/aa-ma-parse.sh"
    MILESTONE_CMD="${REPO_ROOT}/claude-code/skills/execute-aa-ma-milestone/SKILL.md"
    FIXDIR="${BATS_TEST_DIRNAME}/fixtures/gate-scans"
    WORK="$(mktemp -d "${BATS_TMPDIR}/gate-approval.XXXXXX")"
    CLAUDE_HOME="$WORK/claude-home"
    mkdir -p "$CLAUDE_HOME/hooks/lib" && ln -s "$HELPER" "$CLAUDE_HOME/hooks/lib/aa-ma-parse.sh"
    LOG="$WORK/context-log.md"
    T2="Milestone 2: The one being gated"
    export REPO_ROOT HELPER MILESTONE_CMD FIXDIR WORK CLAUDE_HOME LOG T2
}

teardown() {
    rm -rf "$WORK"
}

_has() {  # <title>
    run bash -c '. "$HELPER" && aa_ma_has_gate_approval "$LOG" "$1"' _ "$1"
}

_block() {  # <title> <decision>
    printf '## [2026-10-13] GATE APPROVAL: %s\n- Gate: HARD\n- Approved by: Ste\n- Decision: %s\n\n' "$1" "$2" >> "$LOG"
}

# ---------------------------------------------------------------------------
# The helper
# ---------------------------------------------------------------------------

@test "an APPROVED block for the title → 0" {
    _block "$T2" APPROVED
    _has "$T2"
    [ "$status" -eq 0 ]
}

@test "no block, or no file → non-zero" {
    : > "$LOG"
    _has "$T2"
    [ "$status" -ne 0 ]
    rm -f "$LOG"
    _has "$T2"
    [ "$status" -ne 0 ]
}

@test "a REJECTED block followed by another milestone's APPROVED block → non-zero (no bleed)" {
    _block "$T2" REJECTED
    _block "Milestone 1: Done already" APPROVED
    _has "$T2"
    [ "$status" -ne 0 ]
}

@test "the LAST block for the title decides: rejected then re-approved → 0" {
    _block "$T2" REJECTED
    _block "$T2" APPROVED
    _has "$T2"
    [ "$status" -eq 0 ]
}

@test "the LAST block for the title decides: approved then rejected → non-zero" {
    _block "$T2" APPROVED
    _block "$T2" REJECTED
    _has "$T2"
    [ "$status" -ne 0 ]
}

@test "a heading with no Decision line → non-zero" {
    printf '## [2026-10-13] GATE APPROVAL: %s\n- Gate: HARD\n' "$T2" >> "$LOG"
    _has "$T2"
    [ "$status" -ne 0 ]
}

@test "the title is matched exactly: a longer title or a regex look-alike does not count" {
    _block "Milestone 4: v0.8.0 release extra" APPROVED
    _has "Milestone 4: v0.8.0 release"
    [ "$status" -ne 0 ]
    : > "$LOG"
    _block "Milestone 4: v0X8X0" APPROVED
    _has "Milestone 4: v0.8.0"
    [ "$status" -ne 0 ]
}

@test "a bold Decision field and a Decision line deep in the block both count" {
    printf '## [2026-10-13] GATE APPROVAL: %s\n- a\n- b\n- c\n- d\n- e\n- f\n- g\n- h\n- i\n- **Decision:** APPROVED\n' "$T2" >> "$LOG"
    _has "$T2"
    [ "$status" -eq 0 ]
}

# ---------------------------------------------------------------------------
# §7.1 uses it, executed as shipped in a fresh shell
# ---------------------------------------------------------------------------

_approval_fence() {
    awk '/^### 7\.1 /{f=1} f && /^```bash$/{g=1; next} g && /^```$/{exit} g' "$MILESTONE_CMD"
}

@test "§7.1: a REJECTED approval followed by another milestone's APPROVED block → BLOCKED" {
    local d="$WORK/r/.claude/dev/active/h"
    mkdir -p "$d"
    cp "$FIXDIR/one-active-tasks.md" "$d/h-tasks.md"
    : > "$d/h-provenance.log"
    LOG="$d/h-context-log.md"
    _block "$T2" REJECTED
    _block "Milestone 1: Done already" APPROVED
    _approval_fence > "$WORK/approval.sh"
    run bash -c 'cd "$WORK/r" && env -i PATH="$PATH" HOME="$HOME" CLAUDE_HOME="$CLAUDE_HOME" TASK_NAME=h bash "$WORK/approval.sh"'
    [ "$status" -ne 0 ]
    [[ "$output" == *BLOCKED* ]]
}

@test "§7.1 calls the shared helper" {
    _approval_fence | grep -q 'aa_ma_has_gate_approval'
}

# ---------------------------------------------------------------------------
# §6.8 (M9): the title is a string even with backslashes; a code-fenced example is not an approval
# ---------------------------------------------------------------------------

@test "a title with a backslash is compared as a string (awk -v would unescape it)" {
    _block 'Milestone 2: grep \S fix' APPROVED
    _has 'Milestone 2: grep \S fix'
    [ "$status" -eq 0 ]
    : > "$LOG"
    _block 'Milestone 2: grep S fix' APPROVED
    _has 'Milestone 2: grep \S fix'
    [ "$status" -ne 0 ]
}

@test "an approval example pasted inside a code fence does not count" {
    printf 'How to approve:\n\n```markdown\n## [date] GATE APPROVAL: %s\n- Decision: APPROVED\n```\n' "$T2" >> "$LOG"
    _has "$T2"
    [ "$status" -ne 0 ]
    printf '\n## [2026-10-13] GATE APPROVAL: %s\n- Decision: APPROVED\n' "$T2" >> "$LOG"
    _has "$T2"
    [ "$status" -eq 0 ]
}
