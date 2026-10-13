#!/usr/bin/env bats
# test_tests_verified.bats — §6.7 fence 3, TESTS_VERIFIED (code-conventions-impact M9).
#
# The fence is the THIRD ```bash block in §6.7 (the first is the gate fence, the second
# the diagram fence). It runs scripts/tests-verified.sh, which reads `Test-Command:` and
# the optional `Test-Command-Pass-Regex:` from the MERGE-BASE copy of reference.md, runs
# the command as a shlex argv under a timeout, and appends
# `TESTS_VERIFIED — <heading> — passed=N cmd=<TEST_CMD>` only on a proven pass.
#
# Like test_diagram_verified.bats, the fence is EXECUTED as shipped, never grepped.

bats_require_minimum_version 1.5.0

setup() {
    REPO_ROOT="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)"
    MILESTONE_CMD="${REPO_ROOT}/claude-code/skills/execute-aa-ma-milestone/SKILL.md"
    WORK="$(mktemp -d "${BATS_TMPDIR}/tests-verified.XXXXXX")"
    # The throwaway repo has no forge files: the fence and the script fall back to
    # ${CLAUDE_HOME}, which points at this checkout (as install.sh would).
    CLAUDE_HOME="$WORK/claude-home"
    mkdir -p "$CLAUDE_HOME/hooks/lib" "$CLAUDE_HOME/skills"
    ln -s "${REPO_ROOT}/claude-code/hooks/lib/aa-ma-parse.sh" "$CLAUDE_HOME/hooks/lib/aa-ma-parse.sh"
    ln -s "${REPO_ROOT}/claude-code/skills/execute-aa-ma-milestone" "$CLAUDE_HOME/skills/execute-aa-ma-milestone"
    R="$WORK/r"
    T="$R/.claude/dev/active/t"
    HEADING="Milestone 2: The one being gated"
    export REPO_ROOT MILESTONE_CMD WORK CLAUDE_HOME R T HEADING
    _mkrepo
}

teardown() {
    rm -rf "$WORK"
}

_git() { git -C "$R" -c user.name=t -c user.email=t@t -c commit.gpgsign=false -c core.autocrlf=false "$@"; }

# The stub records its argv and prints stub.out, sleeps $STUB_SLEEP, exits with stub.rc.
_mkrepo() {
    mkdir -p "$T"
    cp "${BATS_TEST_DIRNAME}/fixtures/gate-scans/one-active-tasks.md" "$T/t-tasks.md"
    : > "$T/t-provenance.log"
    : > "$T/t-context-log.md"
    cat > "$R/stub.sh" <<'EOF'
#!/usr/bin/env bash
d="$(cd "$(dirname "$0")" && pwd)"
printf '%s\n' "$#" > "$d/stub.argc"
printf '%s\n' "$@" > "$d/stub.args"
[ -n "${STUB_SLEEP:-}" ] && sleep "$STUB_SLEEP"
cat "$d/stub.out"
exit "$(cat "$d/stub.rc")"
EOF
    chmod +x "$R/stub.sh"
    printf 'stub.*\n!stub.sh\n' > "$R/.gitignore"
    printf '# t Reference\n\nTest-Command: ./stub.sh\n' > "$T/t-reference.md"
    git init -q -b main "$R"
    _git add -A && _git commit -qm init
    _git checkout -q -b feat
    _out '=== 12 passed, 1 skipped in 0.50s ===' 0
}

# _out <stdout text> <rc>
_out() {
    printf '%s\n' "$1" > "$R/stub.out"
    printf '%s\n' "$2" > "$R/stub.rc"
}

# _base_ref <reference.md body>: commit it on main and rebuild feat from there, so the
# merge-base copy is exactly this text.
_base_ref() {
    _git checkout -q main
    printf '%s\n' "$1" > "$T/t-reference.md"
    _git add -A && _git commit -qm ref
    _git checkout -q -B feat
}

# The THIRD ```bash fence after the 6.7 heading, before 6.8.
_tv_fence() {
    awk '/^### 6\.7 /{f=1} /^### 6\.8 /{f=0}
         f && /^```bash$/{n++; if (n == 3) {g=1; next}}
         g && /^```$/{exit} g' "$MILESTONE_CMD"
}

_run_fence() {
    _tv_fence > "$WORK/fence.sh"
    run bash -c 'cd "$R" && TASK_NAME=t bash "$WORK/fence.sh"'
}

_line() { grep -F "TESTS_VERIFIED — ${HEADING} — " "$T/t-provenance.log"; }

# ---------------------------------------------------------------------------
# Placement
# ---------------------------------------------------------------------------

@test "fence 3 is the third §6.7 fence; the gate and diagram fences keep places 1 and 2" {
    run _tv_fence
    [[ "$output" == *tests-verified.sh* ]]
    run awk '/^### 6\.7 /{f=1} f && /^```bash$/{g=1; next} g && /^```$/{exit} g' "$MILESTONE_CMD"
    [[ "$output" == *"ENG-STANDARDS-GATE: PASS"* ]]
    [[ "$output" != *tests-verified* ]]
    run awk '/^### 6\.7 /{f=1} /^### 6\.8 /{f=0} f && /^```bash$/{n++; if (n == 2) {g=1; next}} g && /^```$/{exit} g' "$MILESTONE_CMD"
    [[ "$output" == *DIAGRAM_VERIFIED* ]]
}

@test "the §6.7 summary no longer claims a fixed 'all 5' conditions" {
    run grep -c 'all 5 conditions' "$MILESTONE_CMD"
    [ "$output" = "0" ]
}

# ---------------------------------------------------------------------------
# Default (pytest) summary
# ---------------------------------------------------------------------------

@test "pass: the banner line writes passed=N and the custom Test-Command ran" {
    _out $'2 snapshots passed.\n=== 12 passed, 1 skipped in 0.50s ===' 0
    _run_fence
    [ "$status" -eq 0 ]
    run _line
    [[ "$output" == *"— passed=12 cmd=./stub.sh" ]]
    [ -f "$R/stub.argc" ]
}

@test "pass: the -q summary line (no banner) writes passed=N" {
    _out '3004 passed, 6 skipped, 7 deselected, 3 warnings in 146.33s (0:02:26)' 0
    _run_fence
    [ "$status" -eq 0 ]
    run _line
    [[ "$output" == *"— passed=3004 cmd=./stub.sh" ]]
}

@test "a real pytest run: the default banner and -q output both pass" {
    mkdir -p "$WORK/pt" && printf 'def test_a():\n    assert True\n\ndef test_b():\n    assert True\n' > "$WORK/pt/test_x.py"
    _base_ref "Test-Command: uv run --quiet --project ${REPO_ROOT} pytest -p no:cacheprovider --rootdir ${WORK}/pt ${WORK}/pt"
    _run_fence
    [ "$status" -eq 0 ]
    run _line
    [[ "$output" == *"— passed=2 cmd=uv run"* ]]
    : > "$T/t-provenance.log"
    _base_ref "Test-Command: uv run --quiet --project ${REPO_ROOT} pytest -q -p no:cacheprovider --rootdir ${WORK}/pt ${WORK}/pt"
    _run_fence
    [ "$status" -eq 0 ]
    run _line
    [[ "$output" == *"— passed=2 cmd=uv run"* ]]
}

@test "a failing suite → exit 1, no provenance line" {
    _out '=== 1 failed, 11 passed in 0.50s ===' 1
    _run_fence
    [ "$status" -eq 1 ]
    [[ "$output" == *"BLOCKED: tests"* ]]
    run ! _line
}

@test "a real failing pytest run → exit 1, no line" {
    mkdir -p "$WORK/pt" && printf 'def test_a():\n    assert False\n' > "$WORK/pt/test_x.py"
    _base_ref "Test-Command: uv run --quiet --project ${REPO_ROOT} pytest -p no:cacheprovider --rootdir ${WORK}/pt ${WORK}/pt"
    _run_fence
    [ "$status" -eq 1 ]
    run ! _line
}

@test "rc 0 but no summary line → exit 1, no line" {
    _out $'ran some things\ndone' 0
    _run_fence
    [ "$status" -eq 1 ]
    [[ "$output" == *"BLOCKED: tests"* ]]
    run ! _line
}

@test "rc 5 (no tests collected) without the opt-out → BLOCKED naming the opt-out" {
    _out '=== no tests ran in 0.01s ===' 5
    _run_fence
    [ "$status" -eq 1 ]
    [[ "$output" == *"Test-Command: none"* ]]
    run ! _line
}

# ---------------------------------------------------------------------------
# Inputs: merge-base copy, argv, rejected characters, timeout
# ---------------------------------------------------------------------------

@test "Test-Command comes from the merge-base copy: a branch edit cannot change what runs" {
    printf '# t Reference\n\nTest-Command: ./other.sh\n' > "$T/t-reference.md"
    _git add -A && _git commit -qm "self-pass attempt"
    _run_fence
    [ "$status" -eq 0 ]
    run _line
    [[ "$output" == *"cmd=./stub.sh" ]]
}

@test "no Test-Command line → the default 'uv run pytest' is printed and run" {
    # A uv shim: `uv run pytest` is the suite; anything else (the gate's own uv call) is real uv.
    mkdir -p "$WORK/bin"
    cat > "$WORK/bin/uv" <<EOF
#!/usr/bin/env bash
if [ "\$*" = "run pytest" ]; then
    printf '%s\n' "\$*" > "$WORK/uv.args"
    echo "5 passed in 0.10s"
    exit 0
fi
exec "$(command -v uv)" "\$@"
EOF
    chmod +x "$WORK/bin/uv"
    _base_ref '# t Reference'
    _tv_fence > "$WORK/fence.sh"
    run bash -c 'cd "$R" && PATH="$WORK/bin:$PATH" TASK_NAME=t bash "$WORK/fence.sh"'
    [ "$status" -eq 0 ]
    [[ "$output" == *"uv run pytest"* ]]
    [ "$(cat "$WORK/uv.args")" = "run pytest" ]
    run _line
    [[ "$output" == *"— passed=5 cmd=uv run pytest" ]]
}

@test "a quoted argument reaches the command as one argv element (shlex, no bash -c)" {
    _base_ref 'Test-Command: ./stub.sh "a b" c'
    _run_fence
    [ "$status" -eq 0 ]
    [ "$(cat "$R/stub.argc")" = "2" ]
    [ "$(head -n 1 "$R/stub.args")" = "a b" ]
}

@test "a shell metacharacter in Test-Command is rejected and nothing runs" {
    _base_ref 'Test-Command: ./stub.sh; touch pwned'
    _run_fence
    [ "$status" -eq 1 ]
    [[ "$output" == *"rejected character"* ]]
    [ ! -f "$R/stub.argc" ]
    [ ! -e "$R/pwned" ]
}

@test "two Test-Command lines are ambiguous → BLOCKED" {
    _base_ref $'Test-Command: ./stub.sh\nTest-Command: ./other.sh'
    _run_fence
    [ "$status" -eq 1 ]
    [[ "$output" == *"more than one"* ]]
    [ ! -f "$R/stub.argc" ]
}

@test "a suite that outlives AA_MA_TEST_TIMEOUT → BLOCKED as a timeout, no line" {
    _tv_fence > "$WORK/fence.sh"
    run bash -c 'cd "$R" && AA_MA_TEST_TIMEOUT=1 STUB_SLEEP=5 TASK_NAME=t bash "$WORK/fence.sh"'
    [ "$status" -eq 1 ]
    [[ "$output" == *"timed out"* ]]
    run ! _line
}

# ---------------------------------------------------------------------------
# Opt-out (D10)
# ---------------------------------------------------------------------------

@test "opt-out with a GATE APPROVAL → skipped: <reason>, nothing runs" {
    _base_ref 'Test-Command: none — docs-only milestone'
    printf '## [2026-10-13] GATE APPROVAL: Test-Command none — %s\n- Decision: APPROVED\n' "$HEADING" > "$T/t-context-log.md"
    _run_fence
    [ "$status" -eq 0 ]
    run _line
    [[ "$output" == *"— skipped: docs-only milestone" ]]
    [ ! -f "$R/stub.argc" ]
}

@test "opt-out without a GATE APPROVAL → BLOCKED" {
    _base_ref 'Test-Command: none — docs-only milestone'
    _run_fence
    [ "$status" -eq 1 ]
    [[ "$output" == *"GATE APPROVAL"* ]]
    run ! _line
}

# ---------------------------------------------------------------------------
# Test-Command-Pass-Regex (scope change 2026-10-13)
# ---------------------------------------------------------------------------

PASS_RE='Test-Command-Pass-Regex: \[ FAIL 0 \| WARN [0-9]+ \| SKIP [0-9]+ \| PASS ([0-9]+) \]'

@test "custom Pass-Regex honoured (testthat summary)" {
    _base_ref $'Test-Command: ./stub.sh\n'"$PASS_RE"
    _out '[ FAIL 0 | WARN 0 | SKIP 0 | PASS 12 ]' 0
    _run_fence
    [ "$status" -eq 0 ]
    run _line
    [[ "$output" == *"— passed=12 cmd=./stub.sh" ]]
}

@test "custom Pass-Regex: a trailing praise line after the summary still passes" {
    _base_ref $'Test-Command: ./stub.sh\n'"$PASS_RE"
    _out $'[ FAIL 0 | WARN 1 | SKIP 1 | PASS 12 ]\nKeep up the good work.' 0
    _run_fence
    [ "$status" -eq 0 ]
    run _line
    [[ "$output" == *"— passed=12 cmd=./stub.sh" ]]
}

@test "custom Pass-Regex: rc 0 with a FAIL>0 summary → exit 1, no line" {
    _base_ref $'Test-Command: ./stub.sh\n'"$PASS_RE"
    _out '[ FAIL 1 | WARN 0 | SKIP 0 | PASS 11 ]' 0
    _run_fence
    [ "$status" -eq 1 ]
    run ! _line
}

@test "an invalid Pass-Regex → BLOCKED before anything runs" {
    _base_ref $'Test-Command: ./stub.sh\nTest-Command-Pass-Regex: PASS ([0-9]+'
    _run_fence
    [ "$status" -eq 1 ]
    [[ "$output" == *"invalid Test-Command-Pass-Regex"* ]]
    [[ "$output" != *"Unmatched"* ]]
    [ ! -f "$R/stub.argc" ]
}

@test "a Pass-Regex whose group 1 is not a number → BLOCKED" {
    _base_ref $'Test-Command: ./stub.sh\nTest-Command-Pass-Regex: (PASS [0-9]+)'
    _out 'PASS 12' 0
    _run_fence
    [ "$status" -eq 1 ]
    [[ "$output" == *"group 1"* ]]
    run ! _line
}

# ---------------------------------------------------------------------------
# Hostile inputs (L-049)
# ---------------------------------------------------------------------------

@test "an unbalanced quote in Test-Command → BLOCKED, nothing runs" {
    _base_ref "Test-Command: ./stub.sh \"unterminated"
    _run_fence
    [ "$status" -eq 1 ]
    [[ "$output" == *"cannot split Test-Command"* ]]
    [ ! -f "$R/stub.argc" ]
}

@test "a CRLF reference.md still yields the clean command (no stray carriage return)" {
    _base_ref $'# t Reference\r\n\r\nTest-Command: ./stub.sh\r'
    _run_fence
    [ "$status" -eq 0 ]
    run _line
    [[ "$output" == *"— passed=12 cmd=./stub.sh" ]]
}

@test "custom Pass-Regex: the LAST matching line wins over an earlier one" {
    _base_ref $'Test-Command: ./stub.sh\n'"$PASS_RE"
    _out $'[ FAIL 0 | WARN 0 | SKIP 0 | PASS 3 ]\nmore tests\n[ FAIL 0 | WARN 0 | SKIP 0 | PASS 12 ]' 0
    _run_fence
    [ "$status" -eq 0 ]
    run _line
    [[ "$output" == *"— passed=12 cmd=./stub.sh" ]]
}

# A committed symlink must never redirect the append (background security review of de3f390):
# the line carries repo-controlled text (the heading), so ~/.bashrc as a target is code execution.
@test "provenance.log as a symlink → BLOCKED, the link target is untouched" {
    : > "$WORK/victim"
    rm "$T/t-provenance.log" && ln -s "$WORK/victim" "$T/t-provenance.log"
    _run_fence
    [ "$status" -eq 1 ]
    [[ "$output" == *"symlink"* ]]
    [ ! -s "$WORK/victim" ]
}

@test "the task directory as a symlink → BLOCKED, nothing written through it" {
    mkdir -p "$WORK/elsewhere"
    mv "$T" "$WORK/elsewhere/t"
    ln -s "$WORK/elsewhere/t" "$T"
    : > "$WORK/elsewhere/t/t-provenance.log"
    _run_fence
    [ "$status" -eq 1 ]
    [[ "$output" == *"symlink"* ]]
    [ ! -s "$WORK/elsewhere/t/t-provenance.log" ]
}

@test "an approved opt-out still refuses a symlinked provenance.log" {
    _base_ref 'Test-Command: none — docs-only milestone'
    printf '## [2026-10-13] GATE APPROVAL: Test-Command none — %s\n- Decision: APPROVED\n' "$HEADING" > "$T/t-context-log.md"
    : > "$WORK/victim"
    rm "$T/t-provenance.log" && ln -s "$WORK/victim" "$T/t-provenance.log"
    _run_fence
    [ "$status" -eq 1 ]
    [ ! -s "$WORK/victim" ]
}

@test "opt-out: a REJECTED approval followed by another APPROVED block does not count (no bleed)" {
    _base_ref 'Test-Command: none — docs-only milestone'
    printf '## [2026-10-13] GATE APPROVAL: Test-Command none — %s\n- Decision: REJECTED\n\n## [2026-10-13] GATE APPROVAL: Milestone 1: Done already\n- Decision: APPROVED\n' "$HEADING" > "$T/t-context-log.md"
    _run_fence
    [ "$status" -eq 1 ]
    run ! _line
}

# ---------------------------------------------------------------------------
# §6.6 review fixes (M9): new-on-branch reference, unwritable provenance, no final
# newline, TERM-ignoring tests, a command that cannot run
# ---------------------------------------------------------------------------

@test "reference.md new on this branch → its HEAD copy is used, with a notice" {
    _git checkout -q main
    _git rm -q "$T/t-reference.md" && _git commit -qm "no reference yet"
    _git checkout -q -B feat
    printf '# t Reference\n\nTest-Command: ./stub.sh\n' > "$T/t-reference.md"
    _git add -A && _git commit -qm "plan created on the branch"
    _run_fence
    [ "$status" -eq 0 ]
    [[ "$output" == *"new on this branch (absent at the merge-base); using its HEAD copy"* ]]
    run _line
    [[ "$output" == *"— passed=12 cmd=./stub.sh" ]]
}

@test "reference.md new and uncommitted → the working-tree copy is used, with a notice" {
    _git checkout -q main
    _git rm -q "$T/t-reference.md"
    _git -c core.hooksPath=/dev/null commit -qm "no reference yet"
    _git checkout -q -B feat
    printf '# t Reference\n\nTest-Command: ./stub.sh\n' > "$T/t-reference.md"
    _run_fence
    [ "$status" -eq 0 ]
    [[ "$output" == *"uncommitted; using the working-tree copy"* ]]
    run _line
    [[ "$output" == *"— passed=12 cmd=./stub.sh" ]]
}

@test "an unwritable provenance.log → BLOCKED, never a PASS without its line" {
    chmod 444 "$T/t-provenance.log"
    _run_fence
    chmod 644 "$T/t-provenance.log"
    [ "$status" -eq 1 ]
    [[ "$output" != *"TESTS-GATE: PASS"* ]]
    run ! _line
}

@test "custom Pass-Regex: a summary on a last line with no trailing newline still passes" {
    _base_ref $'Test-Command: ./stub.sh\n'"$PASS_RE"
    printf 'start\n[ FAIL 0 | WARN 0 | SKIP 0 | PASS 7 ]' > "$R/stub.out"
    printf '0\n' > "$R/stub.rc"
    _run_fence
    [ "$status" -eq 0 ]
    run _line
    [[ "$output" == *"— passed=7 cmd=./stub.sh" ]]
}

@test "a test that ignores SIGTERM is killed after AA_MA_TEST_KILL_AFTER → BLOCKED as a timeout" {
    printf '#!/usr/bin/env bash\ntrap "" TERM\nsleep 30\n' > "$R/stub.sh"
    _tv_fence > "$WORK/fence.sh"
    SECONDS=0
    run bash -c 'cd "$R" && AA_MA_TEST_TIMEOUT=1 AA_MA_TEST_KILL_AFTER=1 TASK_NAME=t bash "$WORK/fence.sh"'
    [ "$status" -eq 1 ]
    [[ "$output" == *"timed out"* ]]
    [ "$SECONDS" -lt 15 ]
    run ! _line
}

@test "a Test-Command that cannot run (rc 127) says so, not 'tests failed'" {
    _base_ref 'Test-Command: ./no-such-runner.sh'
    _run_fence
    [ "$status" -eq 1 ]
    [[ "$output" == *"could not run"* ]]
    run ! _line
}

# Background security review of d5ae802 (gate integrity): a branch forked BEFORE an existing plan
# reached the default branch sees no reference.md at the merge-base. It must not be able to supply
# its own Test-Command for that plan: the default branch's tip copy wins.
@test "a branch forked before the plan existed cannot supply its own Test-Command" {
    _git checkout -q main
    _git rm -q "$T/t-reference.md"
    _git -c core.hooksPath=/dev/null commit -qm "A: plan without reference.md"
    _git checkout -q -B feat
    _git checkout -q main
    printf '# t Reference\n\nTest-Command: ./stub.sh\n' > "$T/t-reference.md"
    _git add -A
    _git -c core.hooksPath=/dev/null commit -qm "B: reference.md lands on main"
    _git checkout -q feat
    printf '# t Reference\n\nTest-Command: ./other.sh\n' > "$T/t-reference.md"
    printf '#!/usr/bin/env bash\necho "99 passed in 0.01s"\n' > "$R/other.sh"
    chmod +x "$R/other.sh"
    _git add -A
    _git -c core.hooksPath=/dev/null commit -qm "self-pass attempt from an early fork"
    _run_fence
    [ "$status" -eq 0 ]
    [[ "$output" == *"main"* ]]
    run _line
    [[ "$output" == *"— passed=12 cmd=./stub.sh" ]]
}

# ---------------------------------------------------------------------------
# §6.8 (M9): a repo cannot hijack the argv split, nor make the fence run an inherited TV
# ---------------------------------------------------------------------------

@test "a shlex.py committed at the repo root cannot replace the stdlib split (python3 -I)" {
    printf 'def split(s):\n    return ["./evil.sh"]\n' > "$R/shlex.py"
    printf '#!/usr/bin/env bash\ntouch "$(dirname "$0")/pwned"\necho "1 passed in 0.01s"\n' > "$R/evil.sh"
    chmod +x "$R/evil.sh"
    _run_fence
    [ "$status" -eq 0 ]
    [ ! -e "$R/pwned" ]
    [ -f "$R/stub.argc" ]
    run _line
    [[ "$output" == *"— passed=12 cmd=./stub.sh" ]]
}

@test "an inherited TV is never executed when the script cannot be found" {
    printf '#!/usr/bin/env bash\ntouch "%s/pwned"\n' "$WORK" > "$WORK/evil.sh"
    chmod +x "$WORK/evil.sh"
    _tv_fence > "$WORK/fence.sh"
    mkdir -p "$WORK/empty-home"
    run bash -c 'cd "$R" && CLAUDE_HOME="$WORK/empty-home" TV="$WORK/evil.sh" TASK_NAME=t bash "$WORK/fence.sh"'
    [ "$status" -ne 0 ]
    [ ! -e "$WORK/pwned" ]
}
