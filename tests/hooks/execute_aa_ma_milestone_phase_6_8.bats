#!/usr/bin/env bats
# execute_aa_ma_milestone_phase_6_8.bats — integration tests for Phase 6.8
# Post-Impl Adversarial Review section in /execute-aa-ma-milestone.
#
# §6.8 lives inside a markdown command file (orchestrator instructions
# consumed by the LLM), so we verify the section's structural and
# logical invariants rather than executing it end-to-end:
#   - Section exists between §6.7 and §7.1
#   - Grandfathering logic by Created: date is documented
#   - 6 bypass mechanisms documented in the bypass table
#   - All 5 audit-agent names referenced
#   - 3 verdict outcomes documented (PASS / PASS_WITH_WARNINGS / BLOCKED)
#   - CRITICAL override panel (accept/dispute/defer) documented
#   - Provenance entry format documented
#   - Bash snippets are syntactically valid (bash -n)
#   - /execute-aa-ma-full.md delegates to milestone §6.8 (B.6 section)

setup() {
    REPO_ROOT="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)"
    MILESTONE_CMD="${REPO_ROOT}/claude-code/commands/execute-aa-ma-milestone.md"
    FULL_CMD="${REPO_ROOT}/claude-code/commands/execute-aa-ma-full.md"
    export REPO_ROOT MILESTONE_CMD FULL_CMD
}

@test "§6.8 section exists in execute-aa-ma-milestone.md" {
    grep -E "^### 6\.8 Post-Impl Adversarial Review" "$MILESTONE_CMD"
}

@test "§6.8 is positioned between §6.7 and §7.1 (line ordering)" {
    LINE_67=$(grep -nE "^### 6\.7 " "$MILESTONE_CMD" | head -1 | cut -d: -f1)
    LINE_68=$(grep -nE "^### 6\.8 " "$MILESTONE_CMD" | head -1 | cut -d: -f1)
    LINE_71=$(grep -nE "^### 7\.1 " "$MILESTONE_CMD" | head -1 | cut -d: -f1)
    [ -n "$LINE_67" ] && [ -n "$LINE_68" ] && [ -n "$LINE_71" ]
    [ "$LINE_67" -lt "$LINE_68" ]
    [ "$LINE_68" -lt "$LINE_71" ]
}

@test "§6.8 references ADR-0005" {
    grep -F "ADR-0005" "$MILESTONE_CMD"
}

@test "§6.8 references the verify-impl skill" {
    grep -E "verify-impl|Skill\(verify-impl\)" "$MILESTONE_CMD"
}

@test "§6.8 documents grandfathering by Created: date" {
    # Extract the §6.8 section content
    awk '/^### 6\.8/,/^### 7\.1/' "$MILESTONE_CMD" > "$BATS_TMPDIR/section_68.md"
    grep -E "Created:|grandfather|pre-v0\.8\.0" "$BATS_TMPDIR/section_68.md"
}

@test "§6.8 documents all 5 audit agents" {
    awk '/^### 6\.8/,/^### 7\.1/' "$MILESTONE_CMD" > "$BATS_TMPDIR/section_68.md"
    grep -F "code-reviewer" "$BATS_TMPDIR/section_68.md"
    grep -F "security-auditor" "$BATS_TMPDIR/section_68.md"
    grep -F "tdd-sequence-auditor" "$BATS_TMPDIR/section_68.md"
    grep -F "context7-evidence-auditor" "$BATS_TMPDIR/section_68.md"
    grep -F "future-proofing-auditor" "$BATS_TMPDIR/section_68.md"
}

@test "§6.8 documents 3 verdict outcomes" {
    awk '/^### 6\.8/,/^### 7\.1/' "$MILESTONE_CMD" > "$BATS_TMPDIR/section_68.md"
    grep -F "PASS_WITH_WARNINGS" "$BATS_TMPDIR/section_68.md"
    grep -E "^\| .PASS." "$BATS_TMPDIR/section_68.md"
    grep -E "BLOCKED" "$BATS_TMPDIR/section_68.md"
}

@test "§6.8 documents CRITICAL override panel (accept/dispute/defer)" {
    awk '/^### 6\.8/,/^### 7\.1/' "$MILESTONE_CMD" > "$BATS_TMPDIR/section_68.md"
    grep -F "accept" "$BATS_TMPDIR/section_68.md"
    grep -F "dispute" "$BATS_TMPDIR/section_68.md"
    grep -F "defer" "$BATS_TMPDIR/section_68.md"
    grep -i "AskUserQuestion" "$BATS_TMPDIR/section_68.md"
}

@test "§6.8 bypass table lists 6 mechanisms" {
    awk '/^### 6\.8/,/^### 7\.1/' "$MILESTONE_CMD" > "$BATS_TMPDIR/section_68.md"
    grep -F "AA_MA_HOOKS_DISABLE=1" "$BATS_TMPDIR/section_68.md"
    grep -F "AA_MA_AUDIT_BUDGET=off" "$BATS_TMPDIR/section_68.md"
    grep -F "AA_MA_AUDIT_BUDGET=low" "$BATS_TMPDIR/section_68.md"
    grep -F "TDD-Waiver" "$BATS_TMPDIR/section_68.md"
    grep -F "security-bypass" "$BATS_TMPDIR/section_68.md"
    grep -F "Created:" "$BATS_TMPDIR/section_68.md"
}

@test "§6.8 documents provenance entry format" {
    awk '/^### 6\.8/,/^### 7\.1/' "$MILESTONE_CMD" > "$BATS_TMPDIR/section_68.md"
    grep -F "§6.8 POST_IMPL_REVIEW" "$BATS_TMPDIR/section_68.md"
}

@test "§6.8 documents 'defer creates new sub-task' behaviour" {
    awk '/^### 6\.8/,/^### 7\.1/' "$MILESTONE_CMD" > "$BATS_TMPDIR/section_68.md"
    grep -i "DEFERRED" "$BATS_TMPDIR/section_68.md"
    grep -i "new sub-task\|create.*sub-task\|new backlog" "$BATS_TMPDIR/section_68.md"
}

@test "§6.8 bash snippets are syntactically valid" {
    # Extract code blocks marked ```bash from §6.8 and run `bash -n` on each
    awk '/^### 6\.8/,/^### 7\.1/' "$MILESTONE_CMD" > "$BATS_TMPDIR/section_68.md"
    # Pull bash code blocks
    awk '/^```bash$/{flag=1;next}/^```$/{flag=0;print "---SNIPPET---"}flag' \
        "$BATS_TMPDIR/section_68.md" > "$BATS_TMPDIR/snippets.sh"
    # Each snippet must be parseable. Concatenated parse is sufficient for syntax.
    # Strip the ---SNIPPET--- markers before bash -n
    grep -v -- "---SNIPPET---" "$BATS_TMPDIR/snippets.sh" > "$BATS_TMPDIR/cleaned.sh"
    [ -s "$BATS_TMPDIR/cleaned.sh" ] || skip "No bash snippets found in §6.8"
    run bash -n "$BATS_TMPDIR/cleaned.sh"
    [ "$status" -eq 0 ] || {
        echo "bash -n failed on §6.8 snippets:"
        echo "$output"
        false
    }
}

@test "execute-aa-ma-full.md delegates to §6.8 via B.6 section" {
    grep -E "^#### B\.6\.\s+Post-Impl Adversarial Review" "$FULL_CMD"
}

@test "execute-aa-ma-full.md B.6 references milestone §6.8" {
    awk '/^#### B\.6/,/^#### C\./' "$FULL_CMD" > "$BATS_TMPDIR/section_b6.md"
    grep -E "Section 6\.8|§6\.8" "$BATS_TMPDIR/section_b6.md"
}

@test "execute-aa-ma-full.md B.6 documents grandfathering and bypasses" {
    awk '/^#### B\.6/,/^#### C\./' "$FULL_CMD" > "$BATS_TMPDIR/section_b6.md"
    grep -F "Created:" "$BATS_TMPDIR/section_b6.md"
    grep -F "AA_MA_AUDIT_BUDGET" "$BATS_TMPDIR/section_b6.md"
    grep -F "AA_MA_HOOKS_DISABLE" "$BATS_TMPDIR/section_b6.md"
}

@test "execute-aa-ma-full.md B.6 documents BLOCKED-verdict halt behaviour" {
    awk '/^#### B\.6/,/^#### C\./' "$FULL_CMD" > "$BATS_TMPDIR/section_b6.md"
    grep -F "BLOCKED" "$BATS_TMPDIR/section_b6.md"
    grep -iE "halt|stop|do not.*advance|not.*proceed" "$BATS_TMPDIR/section_b6.md"
}
