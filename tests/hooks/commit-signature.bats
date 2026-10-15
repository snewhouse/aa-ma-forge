#!/usr/bin/env bats
# commit-signature.bats — tests for claude-code/hooks/aa-ma-commit-signature.sh
#
# Hook contract (PreToolUse matcher=Bash):
#   stdin  : {"tool_name":"Bash","tool_input":{"command":"...git commit..."}}
#   exit 0 : pass (kill-switch, no active plan, sig present, [ad-hoc] marker, editor-open)
#   exit 2 : block with stderr naming the active task + signature template
#   exit 1 : hook infra error (jq parse failure)
#
# Against an absent hook these MUST be RED. Against the patched hook they MUST be GREEN.

load ../lib/hook_payloads

setup() {
    HOOK="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)/claude-code/hooks/aa-ma-commit-signature.sh"
    FIXTURE="${BATS_TEST_DIRNAME}/fixtures/build_active_dir.sh"
    BATS_TMP="$(mktemp -d)"
    BATS_TMP_HOME="$(mktemp -d)"
    export BATS_TMP BATS_TMP_HOME
}

teardown() {
    [ -n "${BATS_TMP:-}" ] && rm -rf "$BATS_TMP"
    [ -n "${BATS_TMP_HOME:-}" ] && rm -rf "$BATS_TMP_HOME"
}

# Build a PreToolUse stdin JSON for a given bash command string.
# Uses jq to handle quoting correctly.
# The real captured PreToolUse(Bash) payload, carrying command $1.
make_input() {
    payload PreToolUse-Bash --arg cmd "$1" '.tool_input.command = $cmd'
}

@test "no active plan → exit 0 (pass-through)" {
    cd "$BATS_TMP"
    input=$(make_input 'git commit -m "feat: x"')
    HOME="$BATS_TMP_HOME" run bash -c "printf '%s' \"\$1\" | bash \"$HOOK\"" _ "$input"
    [ "$status" -eq 0 ]
}

@test "signature present for active task → exit 0" {
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 1 plain
    cd "$BATS_TMP"
    input=$(make_input 'git commit -m "feat: x\n\n[AA-MA Plan] task-1 .claude/dev/active/task-1"')
    HOME="$BATS_TMP_HOME" run bash -c "printf '%s' \"\$1\" | bash \"$HOOK\"" _ "$input"
    [ "$status" -eq 0 ]
}

@test "[ad-hoc] marker on own line → exit 0" {
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 1 plain
    cd "$BATS_TMP"
    input=$(make_input "git commit -m \"feat: fix typo

[ad-hoc]\"")
    HOME="$BATS_TMP_HOME" run bash -c "printf '%s' \"\$1\" | bash \"$HOOK\"" _ "$input"
    [ "$status" -eq 0 ]
}

@test "missing signature AND missing [ad-hoc] → exit 2 with helpful stderr" {
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 1 plain
    cd "$BATS_TMP"
    input=$(make_input 'git commit -m "feat: unrelated"')
    HOME="$BATS_TMP_HOME" run bash -c "printf '%s' \"\$1\" | bash \"$HOOK\"" _ "$input"
    [ "$status" -eq 2 ]
    [[ "$output" == *"task-1"* ]]
    [[ "$output" == *"[AA-MA Plan]"* ]]
    [[ "$output" == *"AA_MA_HOOKS_DISABLE=1"* ]]
}

@test "kill switch (AA_MA_HOOKS_DISABLE=1) → exit 0 regardless" {
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 1 plain
    cd "$BATS_TMP"
    input=$(make_input 'git commit -m "unsigned"')
    HOME="$BATS_TMP_HOME" AA_MA_HOOKS_DISABLE=1 run bash -c "printf '%s' \"\$1\" | bash \"$HOOK\"" _ "$input"
    [ "$status" -eq 0 ]
}

@test "HEREDOC form with signature in body → exit 0 (substring match)" {
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 1 plain
    cd "$BATS_TMP"
    # HEREDOC body is visible in tool_input.command since Claude Code passes the literal invocation.
    cmd='git commit -m "$(cat <<'"'"'EOF'"'"'
feat: x

[AA-MA Plan] task-1 .claude/dev/active/task-1
EOF
)"'
    input=$(make_input "$cmd")
    HOME="$BATS_TMP_HOME" run bash -c "printf '%s' \"\$1\" | bash \"$HOOK\"" _ "$input"
    [ "$status" -eq 0 ]
}

@test "editor-open form (bare 'git commit' or --amend) → exit 0 (pass-through)" {
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 1 plain
    cd "$BATS_TMP"
    input=$(make_input 'git commit')
    HOME="$BATS_TMP_HOME" run bash -c "printf '%s' \"\$1\" | bash \"$HOOK\"" _ "$input"
    [ "$status" -eq 0 ]
    input=$(make_input 'git commit --amend')
    HOME="$BATS_TMP_HOME" run bash -c "printf '%s' \"\$1\" | bash \"$HOOK\"" _ "$input"
    [ "$status" -eq 0 ]
}

@test "unknown task name in signature → exit 2 (reject)" {
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 1 plain
    cd "$BATS_TMP"
    input=$(make_input 'git commit -m "feat: x

[AA-MA Plan] bogus-task .claude/dev/active/bogus-task"')
    HOME="$BATS_TMP_HOME" run bash -c "printf '%s' \"\$1\" | bash \"$HOOK\"" _ "$input"
    [ "$status" -eq 2 ]
}

@test "non-commit bash command → exit 0 (not our concern)" {
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 1 plain
    cd "$BATS_TMP"
    input=$(make_input 'ls -la')
    HOME="$BATS_TMP_HOME" run bash -c "printf '%s' \"\$1\" | bash \"$HOOK\"" _ "$input"
    [ "$status" -eq 0 ]
}

@test "word-boundary: 'git commit-tree' does not trigger the hook" {
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 1 plain
    cd "$BATS_TMP"
    # git commit-tree is a plumbing command, distinct from 'git commit'.
    input=$(make_input 'git commit-tree HEAD^{tree} -m "x"')
    HOME="$BATS_TMP_HOME" run bash -c "printf '%s' \"\$1\" | bash \"$HOOK\"" _ "$input"
    [ "$status" -eq 0 ]
}

@test "readlink without -f (macOS < 12.3): the hook still loads and still blocks (double-check F2)" {
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 1 plain
    cd "$BATS_TMP"
    stub="$BATS_TMP/stub"; mkdir -p "$stub"
    printf '#!/bin/sh\ncase "$1" in -f) echo "readlink: illegal option -- f" >&2; exit 1;; esac\nexec %s "$@"\n' "$(command -v readlink)" > "$stub/readlink"
    chmod +x "$stub/readlink"
    input=$(make_input 'git commit -m "feat: unrelated"')
    HOME="$BATS_TMP_HOME" PATH="$stub:$PATH" run bash -c "printf '%s' \"\$1\" | bash \"$HOOK\"" _ "$input"
    [ "$status" -eq 2 ]
    [[ "$output" == *"[AA-MA Plan]"* ]]
}

# ---------------------------------------------------------------------------
# Helper-built footers (sole-dev-merge-fixes 1.7). The skill commits with
# `FOOTER=$(emit_aa_ma_footer); git commit -m "…${FOOTER}"`, so the literal
# command never holds a signature. Only that canonical shape is trusted.
# ---------------------------------------------------------------------------

_run_hook_with_plan() {
    "$FIXTURE" "$BATS_TMP/.claude/dev/active" 1 plain
    cd "$BATS_TMP"
    input=$(make_input "$1")
    HOME="$BATS_TMP_HOME" run bash -c "printf '%s' \"\$1\" | bash \"$HOOK\"" _ "$input"
}

@test "helper footer: set -e, then FOOTER=\$(emit_aa_ma_footer) and git commit -m \"x\${FOOTER}\" on their own lines → exit 0" {
    _run_hook_with_plan $'set -euo pipefail\nFOOTER=$(emit_aa_ma_footer)\ngit commit -m "x${FOOTER}"'
    [ "$status" -eq 0 ]
}

# §6.8 security review: shapes that commit with an EMPTY footer, or put text
# after the signature. Each must block (rc 2).
@test "helper footer: no set -e (an undefined helper leaves FOOTER empty) → exit 2" {
    _run_hook_with_plan $'FOOTER=$(emit_aa_ma_footer)\ngit commit -m "x${FOOTER}"'
    [ "$status" -eq 2 ]
}

@test "helper footer: one-line '; ' form (no set -e) → exit 2" {
    _run_hook_with_plan 'FOOTER=$(emit_aa_ma_footer); git commit -m "x${FOOTER}"'
    [ "$status" -eq 2 ]
}

@test "helper footer: prefix assignment FOOTER=\$(…) git commit → exit 2" {
    _run_hook_with_plan $'set -e\nFOOTER=$(emit_aa_ma_footer) git commit -m "x${FOOTER}"'
    [ "$status" -eq 2 ]
}

@test "helper footer: assignment commented out → exit 2" {
    _run_hook_with_plan $'set -e\n# FOOTER=$(emit_aa_ma_footer)\ngit commit -m "x${FOOTER}"'
    [ "$status" -eq 2 ]
}

@test "helper footer: assignment in a subshell → exit 2" {
    _run_hook_with_plan $'set -e\n( FOOTER=$(emit_aa_ma_footer) )\ngit commit -m "x${FOOTER}"'
    [ "$status" -eq 2 ]
}

@test "helper footer: --trailer before -m → exit 2" {
    _run_hook_with_plan $'set -e\nFOOTER=$(emit_aa_ma_footer)\ngit commit --trailer "A: b" -m "x${FOOTER}"'
    [ "$status" -eq 2 ]
}

@test "helper footer: a second -m on a continuation line → exit 2" {
    _run_hook_with_plan $'set -e\nFOOTER=$(emit_aa_ma_footer)\ngit commit -m "x${FOOTER}" \\\n  -m "extra"'
    [ "$status" -eq 2 ]
}

@test "helper footer: set +e after set -e → exit 2" {
    _run_hook_with_plan $'set -e\nset +e\nFOOTER=$(emit_aa_ma_footer)\ngit commit -m "x${FOOTER}"'
    [ "$status" -eq 2 ]
}

@test "helper footer: neither helper nor literal signature → exit 2" {
    _run_hook_with_plan 'FOOTER=x; git commit -m "x${FOOTER}"'
    [ "$status" -eq 2 ]
}

@test "helper footer: name only mentioned in a comment → exit 2" {
    _run_hook_with_plan 'git commit -m "no footer" # emit_aa_ma_footer'
    [ "$status" -eq 2 ]
}

@test "helper footer: a redefined emit_aa_ma_footer → exit 2" {
    _run_hook_with_plan 'emit_aa_ma_footer(){ :; }; FOOTER=$(emit_aa_ma_footer); git commit -m "x${FOOTER}"'
    [ "$status" -eq 2 ]
}

@test "helper footer: footer not at the end of the message → exit 2" {
    _run_hook_with_plan 'FOOTER=$(emit_aa_ma_footer); git commit -m "${FOOTER} x"'
    [ "$status" -eq 2 ]
}

@test "helper footer: FOOTER reassigned after the helper call → exit 2" {
    _run_hook_with_plan 'FOOTER=$(emit_aa_ma_footer); FOOTER=x; git commit -m "y${FOOTER}"'
    [ "$status" -eq 2 ]
}

@test "helper footer: the skill's real stage-b-commit block → exit 0" {
    local root; root="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)"
    _run_hook_with_plan "$(bash "$root/tests/commands/sole-dev-merge/fixtures/extract_stage.sh" \
        stage-b-commit "$root/claude-code/skills/sole-dev-merge/SKILL.md")"
    [ "$status" -eq 0 ]
}

@test "helper footer: the skill's real stage-d-triage block → exit 0" {
    local root; root="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)"
    _run_hook_with_plan "$(bash "$root/tests/commands/sole-dev-merge/fixtures/extract_stage.sh" \
        stage-d-triage "$root/claude-code/skills/sole-dev-merge/references/stage-d-triage.md")"
    [ "$status" -eq 0 ]
}
