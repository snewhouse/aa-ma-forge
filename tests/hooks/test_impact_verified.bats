#!/usr/bin/env bats
# test_impact_verified.bats — §6.7 fence 4, IMPACT_VERIFIED (code-conventions-impact 11.5).
#
# The fence is the FOURTH ```bash block in §6.7 (gate, diagram, tests, impact). It runs
# scripts/impact-verified.sh: base = aa_ma_milestone_base, then aa-ma-impact (the real CLI,
# the real codemem) on a throwaway repo with an origin. The fixture plan is `Created:
# 9999-12-31` — equal to the IMPACT_CUTOVER sentinel, so it is in force without any knob.
# Like test_tests_verified.bats, the fence is EXECUTED as shipped, never grepped.

bats_require_minimum_version 1.5.0

setup() {
    REPO_ROOT="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)"
    MILESTONE_CMD="${REPO_ROOT}/claude-code/skills/execute-aa-ma-milestone/SKILL.md"
    WORK="$(mktemp -d "${BATS_TMPDIR}/impact-verified.XXXXXX")"
    CLAUDE_HOME="$WORK/claude-home"
    mkdir -p "$CLAUDE_HOME/hooks/lib" "$CLAUDE_HOME/skills"
    ln -s "${REPO_ROOT}/claude-code/hooks/lib/aa-ma-parse.sh" "$CLAUDE_HOME/hooks/lib/aa-ma-parse.sh"
    ln -s "${REPO_ROOT}/claude-code/skills/execute-aa-ma-milestone" "$CLAUDE_HOME/skills/execute-aa-ma-milestone"
    CODEMEM_DB="$WORK/cm/index.db"
    R="$WORK/r"
    T="$R/.claude/dev/active/t"
    HEADING="Milestone 2: The one being gated"
    export REPO_ROOT MILESTONE_CMD WORK CLAUDE_HOME CODEMEM_DB R T HEADING
    unset CODEMEM_BIN
    _mkrepo "9999-12-31"
}

teardown() {
    rm -rf "$WORK"
}

_git() { git -C "$R" -c user.name=t -c user.email=t@t -c commit.gpgsign=false "$@"; }

_mkrepo() {
    git init -q --bare -b main "$WORK/origin.git"
    git clone -q "$WORK/origin.git" "$R" 2> /dev/null
    mkdir -p "$T" "$R/src"
    cp "${BATS_TEST_DIRNAME}/fixtures/gate-scans/one-active-tasks.md" "$T/t-tasks.md"
    printf '# t Plan\nCreated: %s\n\n### Milestone 2 — The one being gated\n#### Contract\n```\nFiles:\n  Modify  src/a.py\n```\n' "$1" > "$T/t-plan.md"
    printf '# ref\n' > "$T/t-reference.md"
    : > "$T/t-context-log.md"
    : > "$T/t-provenance.log"
    echo 'A = 1' > "$R/src/a.py"
    echo 'B = 1' > "$R/src/b.py"
    _git add -A
    _git commit -qm init
    _git push -q origin main
    git -C "$R" remote set-head origin -a > /dev/null
    _git checkout -q -b feat
    (cd "$R" && "${REPO_ROOT}/.venv/bin/codemem" build --repo-root "$R" > /dev/null)
}

# The FOURTH ```bash fence after the 6.7 heading, before 6.8.
_iv_fence() {
    awk '/^### 6\.7 /{f=1} /^### 6\.8 /{f=0}
         f && /^```bash$/{n++; if (n == 4) {g=1; next}}
         g && /^```$/{exit} g' "$MILESTONE_CMD"
}

_run_fence() {
    _iv_fence > "$WORK/fence.sh"
    run bash -c 'cd "$R" && TASK_NAME=t bash "$WORK/fence.sh"'
}

_line() { grep -F "IMPACT_VERIFIED — ${HEADING} — " "$T/t-provenance.log"; }

@test "fence 4 is the fourth §6.7 fence and runs impact-verified.sh" {
    run _iv_fence
    [[ "$output" == *impact-verified.sh* ]]
    run awk '/^### 6\.7 /{f=1} /^### 6\.8 /{f=0} f && /^```bash$/{n++; if (n == 3) {g=1; next}} g && /^```$/{exit} g' "$MILESTONE_CMD"
    [[ "$output" == *tests-verified.sh* ]]
}

@test "pass: every change predicted → IMPACT_VERIFIED line with the counts" {
    echo 'A = 2' > "$R/src/a.py"
    _run_fence
    [ "$status" -eq 0 ]
    [[ "$output" == *"IMPACT-GATE: PASS"* ]]
    run _line
    [ "$status" -eq 0 ]
    [[ "$output" == *"— changed=1 predicted=1 cochange=0 unexplained=0" ]]
}

@test "fail: an unpredicted file → exit 1, names it, writes no line" {
    echo 'A = 2' > "$R/src/a.py"
    echo 'B = 2' > "$R/src/b.py"
    _run_fence
    [ "$status" -eq 1 ]
    [[ "$output" == *BLOCKED* ]]
    [[ "$output" == *"unpredicted:src/b.py"* ]]
    run ! _line
}

@test "grandfathered plan → prints not applicable, exit 0, no line" {
    sed -i 's/^Created: .*/Created: 2026-10-08/' "$T/t-plan.md"
    _run_fence
    [ "$status" -eq 0 ]
    [[ "$output" == *"IMPACT-GATE: not applicable (grandfathered)"* ]]
    run ! _line
}

@test "grandfathered plan on the default branch (no milestone window) is still not applicable" {
    sed -i 's/^Created: .*/Created: 2026-10-08/' "$T/t-plan.md"
    _git checkout -q main
    _run_fence
    [ "$status" -eq 0 ]
    [[ "$output" == *"not applicable"* ]]
}

@test "a plan in force on the default branch → BLOCKED: no milestone window" {
    _git checkout -q main
    _run_fence
    [ "$status" -eq 1 ]
    [[ "$output" == *"no milestone window"* ]]
}

@test "a stale codemem answer never passes: exit 1 naming stale_reason" {
    echo 'A = 2' > "$R/src/a.py"
    cat > "$WORK/codemem" << 'STUB'
#!/usr/bin/env bash
if [ "$1" = query ]; then
    printf '{"files": [], "target": "src/a.py", "target_commits": 1, "error": null, "stale": true, "stale_reason": "behind"}\n'
fi
exit 0
STUB
    chmod +x "$WORK/codemem"
    export CODEMEM_BIN="$WORK/codemem"
    _run_fence
    [ "$status" -eq 1 ]
    [[ "$output" == *"stale"* && "$output" == *"behind"* ]]
    run ! _line
}

@test "a derived Critical-Path without its review → exit 1 naming the file" {
    mkdir -p "$R/claude-code/hooks"
    sed -i 's|  Modify  src/a.py|  Modify  claude-code/hooks/x.sh|' "$T/t-plan.md"
    echo '#!/bin/sh' > "$R/claude-code/hooks/x.sh"
    _run_fence
    [ "$status" -eq 1 ]
    [[ "$output" == *"hook-modification:claude-code/hooks/x.sh"* ]]
}
