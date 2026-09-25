#!/usr/bin/env bats
# test_diagram_verified.bats — the §6.7 HARD item for §13 sigil edges (ADR-0015).
#
# diagram-generation M11 (map Ticket 15). HARD ≠ gate.py: the item is a second
# ```bash fence in §6.7 that runs `aa-ma-lint-views` on plan.md, reads its
# `sigils:` summary line, and refuses COMPLETE on a PHANTOM_EDGE / LABEL_UNKNOWN or
# on an index that could not answer (missing, stale, unreadable — L-012). On a pass
# it appends `DIAGRAM_VERIFIED — <heading> — edges=N phantom=0 unknown=K` to
# provenance.log. Opt-in: a plan with no sigil in §13 is a no-op.
#
# Like aa-ma-gate-python.bats, the fence is EXECUTED as shipped, never grepped.

bats_require_minimum_version 1.5.0

setup() {
    REPO_ROOT="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)"
    HELPER="${REPO_ROOT}/claude-code/hooks/lib/aa-ma-parse.sh"
    MILESTONE_CMD="${REPO_ROOT}/claude-code/commands/execute-aa-ma-milestone.md"
    WORK="$(mktemp -d "${BATS_TMPDIR}/diagram-verified.XXXXXX")"
    # The fence resolves the lib from the git toplevel (the throwaway repo has none),
    # else ${CLAUDE_HOME:-~/.claude}: point that at the in-repo lib.
    CLAUDE_HOME="$WORK/claude-home"
    mkdir -p "$CLAUDE_HOME/hooks/lib" && ln -s "$HELPER" "$CLAUDE_HOME/hooks/lib/aa-ma-parse.sh"
    R="$WORK/r"
    T="$R/.claude/dev/active/t"
    export REPO_ROOT MILESTONE_CMD WORK CLAUDE_HOME R T
    _mkrepo
}

teardown() {
    rm -rf "$WORK"
}

_git() { git -C "$R" -c user.name=t -c user.email=t@t "$@"; }

# src/app/a.py imports src/app/b.py; an ACTIVE HARD milestone to gate.
_mkrepo() {
    mkdir -p "$R/src/app" "$T"
    printf '.codemem/\n' > "$R/.gitignore"
    : > "$R/src/app/__init__.py"
    printf 'from app.b import helper\n\ndef run():\n    return helper()\n' > "$R/src/app/a.py"
    printf 'def helper():\n    return 1\n' > "$R/src/app/b.py"
    cp "${BATS_TEST_DIRNAME}/fixtures/gate-scans/one-active-tasks.md" "$T/t-tasks.md"
    : > "$T/t-provenance.log"
    : > "$T/t-context-log.md"
    _plan '    A --> B'
    git init -q -b main "$R"
    _git add -A && _git commit -qm init
    _build
}

_build() {
    uv run --quiet --project "$REPO_ROOT" codemem --db "$R/.codemem/index.db" build --repo-root "$R" >/dev/null
}

_plan() {  # <mermaid edge line>
    cat > "$T/t-plan.md" <<EOF
# t Plan

## 13. Architecture View

### Component view

\`\`\`mermaid
graph TD
    A["src/app/a.py"]
    B["src/app/b.py"]
    N["src/app/new.py (new)"]
$1
\`\`\`
EOF
}

_lint() {
    uv run --quiet --project "$REPO_ROOT" aa-ma-lint-views "$T/t-plan.md" --repo-root "$R"
}

# The SECOND ```bash fence after the 6.7 heading, before 6.8. The first is the
# gate fence three suites extract (FENCE-ORDER CONSTRAINT, plan M11).
_diagram_fence() {
    awk '/^### 6\.7 /{f=1} /^### 6\.8 /{f=0}
         f && /^```bash$/{n++; if (n == 2) {g=1; next}}
         g && /^```$/{exit} g' "$MILESTONE_CMD"
}

_run_fence() {
    _diagram_fence > "$WORK/fence.sh"
    (cd "$R" && TASK_NAME=t bash "$WORK/fence.sh")
}

# ---------------------------------------------------------------------------
# aa-ma-lint-views — what the fence calls (AC1-AC3, AC8)
# ---------------------------------------------------------------------------

@test "AC1: a sigil-free plan has no PHANTOM_EDGE, exits 0 and reports edges=0" {
    run _lint
    [ "$status" -eq 0 ]
    [[ "$output" != *PHANTOM_EDGE* ]]
    [[ "$output" == *"sigils: edges=0 phantom=0 unknown=0 index-unknown=0"* ]]
}

@test "AC2: a broken sigil edge exits 1 with a PHANTOM_EDGE line" {
    _plan '    B -->|"@import"| A'
    run _lint
    [ "$status" -eq 1 ]
    [[ "$output" == *": PHANTOM_EDGE: "* ]]
    [[ "$output" == *"sigils: edges=1 phantom=1 unknown=0 index-unknown=0"* ]]
}

@test "AC3: with .codemem removed the output names codemem build and the tier is UNKNOWN" {
    _plan '    A -->|"@import"| B'
    rm -rf "$R/.codemem"
    run _lint
    [ "$status" -eq 0 ]   # the lint's own exit stays non-blocking (map Ticket 2)
    [[ "$output" == *": UNKNOWN: "*"codemem build"* ]]
    [[ "$output" == *"sigils: edges=1 phantom=0 unknown=1 index-unknown=1"* ]]
}

# ---------------------------------------------------------------------------
# The §6.7 fence, executed as shipped
# ---------------------------------------------------------------------------

@test "AC7: the diagram fence is the second fence; the first is still the gate fence" {
    run _diagram_fence
    [[ "$output" == *DIAGRAM_VERIFIED* ]]
    run awk '/^### 6\.7 /{f=1} f && /^```bash$/{g=1; next} g && /^```$/{exit} g' "$MILESTONE_CMD"
    [[ "$output" == *"ENG-STANDARDS-GATE: PASS"* ]]
    [[ "$output" != *DIAGRAM_VERIFIED* ]]
}

@test "opt-out: a sigil-free plan passes and writes no evidence" {
    run _run_fence
    [ "$status" -eq 0 ]
    [[ "$output" == *"not applicable"* ]]
    ! grep -q DIAGRAM_VERIFIED "$T/t-provenance.log"
}

@test "a true sigil edge passes and records DIAGRAM_VERIFIED naming the milestone" {
    _plan '    A -->|"@import"| B'
    run _run_fence
    [ "$status" -eq 0 ]
    grep -qF "DIAGRAM_VERIFIED — Milestone 2: The one being gated — edges=1 phantom=0 unknown=0" "$T/t-provenance.log"
}

@test "a PHANTOM_EDGE refuses COMPLETE and writes no evidence" {
    _plan '    B -->|"@import"| A'
    run _run_fence
    [ "$status" -eq 1 ]
    [[ "$output" == *BLOCKED* && "$output" == *PHANTOM_EDGE* ]]
    ! grep -q DIAGRAM_VERIFIED "$T/t-provenance.log"
}

@test "a typo'd sigil (LABEL_UNKNOWN) refuses COMPLETE" {
    _plan '    A -->|"@improt"| B'
    run _run_fence
    [ "$status" -eq 1 ]
    [[ "$output" == *LABEL_UNKNOWN* ]]
}

@test "no index refuses and names the remedy (L-012)" {
    _plan '    A -->|"@import"| B'
    rm -rf "$R/.codemem"
    run _run_fence
    [ "$status" -eq 1 ]
    [[ "$output" == *BLOCKED* && "$output" == *"codemem build"* ]]
    ! grep -q DIAGRAM_VERIFIED "$T/t-provenance.log"
}

@test "a stale index refuses; codemem build clears it" {
    _plan '    A -->|"@import"| B'
    touch -d '2100-01-01' "$R/src/app/b.py"
    run _run_fence
    [ "$status" -eq 1 ]
    [[ "$output" == *"codemem build"* ]]
    _build
    run _run_fence
    [ "$status" -eq 0 ]
}

@test "a planned (new) endpoint alone does not refuse; it is counted" {
    _plan '    A -->|"@import"| N'
    run _run_fence
    [ "$status" -eq 0 ]
    grep -qF "edges=1 phantom=0 unknown=1" "$T/t-provenance.log"
}

@test "an unread §13 (unterminated fence) refuses — never an opt-out" {
    printf '# t Plan\n\n## 13. Architecture View\n\n### Component view\n\n```mermaid\ngraph TD\n  A -->|"@import"| B\n' > "$T/t-plan.md"
    run _run_fence
    [ "$status" -eq 1 ]
    [[ "$output" == *BLOCKED* ]]
    ! grep -q DIAGRAM_VERIFIED "$T/t-provenance.log"
}

@test "no ACTIVE milestone refuses before linting" {
    sed -i 's/Status: ACTIVE/Status: PENDING/' "$T/t-tasks.md"
    _plan '    A -->|"@import"| B'
    run _run_fence
    [ "$status" -eq 1 ]
    [[ "$output" == *BLOCKED* ]]
}
