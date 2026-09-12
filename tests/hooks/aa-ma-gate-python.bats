#!/usr/bin/env bats
# aa-ma-gate-python.bats — the §6.7 / §7.1 gate reads from the Python SSoT.
#
# milestone-grammar-ssot M5. Three §6.8 passes over the awk that used to
# answer the gate's questions found 8, 4, then 9 CRITICALs; the remediation
# round produced more than it closed. Enforcement now calls `aa-ma-gate`
# (src/aa_ma/gate.py) through the `aa_ma_gate` launcher. These tests:
#
#   1. drive the launcher — kv output, exit codes, and the interpreter-
#      unavailable path (a gate that cannot run must refuse, never skip);
#   2. EXECUTE the §6.7 fence as shipped in the command file against each
#      fixture, asserting exit status and message. Sub-step 4.14's lesson: an
#      exact-literal grep over markdown goes green if an edit merely adds
#      quotes; only running the text proves the shipped path.

bats_require_minimum_version 1.5.0

setup() {
    REPO_ROOT="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)"
    HELPER="${REPO_ROOT}/claude-code/hooks/lib/aa-ma-parse.sh"
    MILESTONE_CMD="${REPO_ROOT}/claude-code/commands/execute-aa-ma-milestone.md"
    FIXDIR="${BATS_TEST_DIRNAME}/fixtures/gate-scans"
    WORK="$(mktemp -d "${BATS_TMPDIR}/gate-py.XXXXXX")"
    # The fences resolve the lib from the git toplevel, else ${CLAUDE_HOME:-~/.claude}.
    # Fence tests run from a non-git temp dir, so give them a CLAUDE_HOME that holds the
    # in-repo lib — otherwise they pass only on a machine that ran install.sh (CI had
    # been red on exactly this since the file landed).
    CLAUDE_HOME="$WORK/claude-home"
    mkdir -p "$CLAUDE_HOME/hooks/lib" && ln -s "$HELPER" "$CLAUDE_HOME/hooks/lib/aa-ma-parse.sh"
    export REPO_ROOT HELPER MILESTONE_CMD FIXDIR WORK CLAUDE_HOME
}

teardown() {
    rm -rf "$WORK"
    unset AA_MA_PARSE_SH_LOADED 2>/dev/null || true
}

load_helper() {
    # shellcheck disable=SC1090
    . "$HELPER"
}

# The §6.7 fence, verbatim from the command file: the first ```bash block
# after the 6.7 heading.
_gate_fence() {
    awk '/^### 6\.7 /{f=1} f && /^```bash$/{g=1; next} g && /^```$/{exit} g' "$MILESTONE_CMD"
}

# Build `.claude/dev/active/<name>/` from a fixture so the fence's own path
# derivation is exercised, not bypassed. Runs from a fresh non-git dir so the
# dirty-tree condition is not in play unless a test wants it.
_task_dir_from() {  # <fixture> <task-name>
    local dir="$WORK/$2/.claude/dev/active/$2"
    mkdir -p "$dir"
    cp "$FIXDIR/$1-tasks.md" "$dir/$2-tasks.md"
    : > "$dir/$2-provenance.log"
    : > "$dir/$2-context-log.md"
    printf '%s\n' "$WORK/$2"
}

_run_fence() {  # <cwd> <task-name>
    _gate_fence > "$WORK/fence.sh"
    (cd "$1" && TASK_NAME="$2" bash "$WORK/fence.sh")
}

# ---------------------------------------------------------------------------
# The launcher
# ---------------------------------------------------------------------------

@test "aa_ma_gate returns kv lines and the contract exit code" {
    load_helper
    run aa_ma_gate "$FIXDIR/one-active-tasks.md"
    [ "$status" -eq 0 ]
    [[ "$output" == *"heading=Milestone 2: The one being gated"* ]]
    [[ "$output" == *"gate=HARD"* ]]
    [[ "$output" == *"pending_steps=0"* ]]
}

@test "aa_ma_gate_field returns the value after the first '=' verbatim" {
    load_helper
    printf 'heading=Milestone 1: a=b \\t C:\\dev\\path\nheading=second\n' > "$WORK/kv"
    run aa_ma_gate_field heading < "$WORK/kv"
    [ "$output" = 'Milestone 1: a=b \t C:\dev\path' ]
}

@test "aa_ma_gate refuses loudly when uv is not on PATH" {
    load_helper
    # Coreutils stay reachable; only uv is gone. A PATH of nothing would fail
    # for the wrong reason (no sed, no readlink).
    local bin="$WORK/bin"; mkdir -p "$bin"
    for t in bash sed grep head readlink dirname; do ln -s "$(command -v "$t")" "$bin/$t"; done
    run -127 env PATH="$bin" bash -c ". '$HELPER'; aa_ma_gate '$FIXDIR/one-active-tasks.md'"
    [[ "$output" == *"BLOCKED"* ]]
    [[ "$output" != *"exit_code="* ]]
}

@test "aa_ma_gate refuses when uv is present but the tool does not start" {
    load_helper
    # `uv run` exits 2 when it cannot spawn the script — the same 2 the
    # contract uses for "unreadable". The launcher must tell them apart.
    local bin="$WORK/bin"; mkdir -p "$bin"
    printf '#!/usr/bin/env bash\necho "error: Failed to spawn: aa-ma-gate" >&2\nexit 2\n' > "$bin/uv"
    chmod +x "$bin/uv"
    run -127 env PATH="$bin:$PATH" bash -c ". '$HELPER'; aa_ma_gate '$FIXDIR/one-active-tasks.md'"
    [[ "$output" == *"did not run"* ]]
}

@test "the interpreter-unavailable guard is not vacuous" {
    # The same call with uv present succeeds — so the failure above is the
    # missing interpreter, not a broken fixture.
    load_helper
    run aa_ma_gate "$FIXDIR/one-active-tasks.md"
    [ "$status" -eq 0 ]
}

# ---------------------------------------------------------------------------
# The §6.7 fence, executed as shipped
# ---------------------------------------------------------------------------

@test "§6.7 fence: one ACTIVE, zero pending, no provenance obligations -> PASS" {
    local cwd; cwd=$(_task_dir_from one-active one-active)
    run _run_fence "$cwd" one-active
    [ "$status" -eq 0 ]
    [[ "$output" == *"ENG-STANDARDS-GATE: PASS"* ]]
}

@test "§6.7 fence: two ACTIVE -> BLOCKED naming both" {
    local cwd; cwd=$(_task_dir_from two-active two-active)
    run _run_fence "$cwd" two-active
    [ "$status" -ne 0 ]
    [[ "$output" == *"ambiguous"* ]]
    [[ "$output" == *"Milestone 2: Older milestone left ACTIVE"* ]]
    [[ "$output" == *"Milestone 4: The one actually being gated"* ]]
    [[ "$output" != *"PASS"* ]]
}

@test "§6.7 fence: no ACTIVE -> BLOCKED" {
    local cwd; cwd=$(_task_dir_from no-active no-active)
    run _run_fence "$cwd" no-active
    [ "$status" -ne 0 ]
    [[ "$output" == *"no milestone is ACTIVE"* ]]
    [[ "$output" != *"PASS"* ]]
}

@test "§6.7 fence: PENDING sub-steps -> BLOCKED with the count" {
    local cwd; cwd=$(_task_dir_from two-active pend)
    # Leave only Milestone 4 ACTIVE; it has one PENDING sub-step.
    sed -i '0,/^- Status: ACTIVE$/s//- Status: COMPLETE/' "$cwd/.claude/dev/active/pend/pend-tasks.md"
    run _run_fence "$cwd" pend
    [ "$status" -ne 0 ]
    [[ "$output" == *"1 sub-step(s) still PENDING"* ]]
}

@test "§6.7 fence: Critical-Path without a milestone-scoped review entry -> BLOCKED; with one -> PASS" {
    local cwd; cwd=$(_task_dir_from one-active cp)
    local tasks="$cwd/.claude/dev/active/cp/cp-tasks.md"
    local prov="$cwd/.claude/dev/active/cp/cp-provenance.log"
    sed -i 's/^- Gate: HARD$/- Gate: HARD\n- **Critical-Path:** data-xform/' "$tasks"
    run _run_fence "$cwd" cp
    [ "$status" -ne 0 ]
    [[ "$output" == *"Critical-Path: data-xform"* ]]
    # An entry naming a DIFFERENT milestone must not satisfy it.
    echo "[ts] CRITICAL_PATH_REVIEW — Milestone 1: Done already — data-xform — x" >> "$prov"
    run _run_fence "$cwd" cp
    [ "$status" -ne 0 ]
    echo "[ts] CRITICAL_PATH_REVIEW — Milestone 2: The one being gated — data-xform — x" >> "$prov"
    run _run_fence "$cwd" cp
    [ "$status" -eq 0 ]
    [[ "$output" == *"PASS"* ]]
}

@test "§6.7 fence: Gate: TYPO -> BLOCKED, never SOFT" {
    local cwd; cwd=$(_task_dir_from one-active typo)
    sed -i 's/^- Gate: HARD$/- Gate: TYPO/' "$cwd/.claude/dev/active/typo/typo-tasks.md"
    run _run_fence "$cwd" typo
    [ "$status" -ne 0 ]
    [[ "$output" == *"unreadable"* ]]
    [[ "$output" == *"TYPO"* ]]
}

@test "§6.7 fence: a title with backslashes round-trips to the heading the gate derived" {
    local cwd; cwd=$(_task_dir_from one-active bs)
    local tasks="$cwd/.claude/dev/active/bs/bs-tasks.md"
    local prov="$cwd/.claude/dev/active/bs/bs-provenance.log"
    sed -i 's|^## Milestone 2: The one being gated$|## Milestone 2: Fix \\t handling in C:\\dev\\path|' "$tasks"
    sed -i 's/^- Gate: HARD$/- Gate: HARD\n- **Critical-Path:** data-xform/' "$tasks"
    printf '%s\n' '[ts] CRITICAL_PATH_REVIEW — Milestone 2: Fix \t handling in C:\dev\path — data-xform — x' >> "$prov"
    run _run_fence "$cwd" bs
    [ "$status" -eq 0 ]
}

@test "§6.7 fence: a dirty AA-MA task dir exits non-zero with no PASS line" {
    local cwd; cwd=$(_task_dir_from one-active dirty)
    (cd "$cwd" && git init -q && git add -A && git -c user.email=t@t -c user.name=t commit -q -m init)
    echo x >> "$cwd/.claude/dev/active/dirty/dirty-context-log.md"
    run _run_fence "$cwd" dirty
    [ "$status" -ne 0 ]
    [[ "$output" == *"uncommitted"* ]]
    [[ "$output" != *"PASS"* ]]
}

@test "§6.7 fence: with uv missing the gate BLOCKs rather than passing" {
    local cwd; cwd=$(_task_dir_from one-active nouv)
    local bin="$WORK/bin"; mkdir -p "$bin"
    for t in sed grep head readlink dirname git wc tr bash awk printf; do
        p=$(command -v "$t" 2>/dev/null) && ln -sf "$p" "$bin/$t"
    done
    _gate_fence > "$WORK/fence.sh"
    run env PATH="$bin" bash -c "cd '$cwd' && TASK_NAME=nouv bash '$WORK/fence.sh'"
    [ "$status" -ne 0 ]
    [[ "$output" == *"BLOCKED"* ]]
    [[ "$output" != *"PASS"* ]]
}

@test "§6.7 fence: the live plan is gateable through the shipped text" {
    # Runs in the real repo, so the dirty-tree condition applies: either a
    # clean PASS/BLOCK on substance, or BLOCK on uncommitted AA-MA files.
    # Never a bash error, never an empty subject.
    _gate_fence > "$WORK/fence.sh"
    run bash -c "cd '$REPO_ROOT' && TASK_NAME=milestone-grammar-ssot bash '$WORK/fence.sh'"
    [[ "$output" == *"PASS"* || "$output" == *"BLOCKED"* ]]
    [[ "$output" != *"command not found"* ]]
}

# ---------------------------------------------------------------------------
# §5.2 Mode dispatch — the HITL bypass
# ---------------------------------------------------------------------------

_mode_fence() {
    # The indented ```bash block under "1.5. **Mode Dispatch"; leading indent
    # stripped so bash sees plain lines.
    awk '/^1\.5\. \*\*Mode Dispatch/{f=1} f && /^   ```bash$/{g=1; next} g && /^   ```$/{exit} g' "$MILESTONE_CMD" \
        | sed 's/^   //'
}

_run_mode() {  # <task-root> <task-name> <milestone-number> <step-id>
    # No variables injected beyond the three the command documents — the first
    # version passed AA_MA_LIB in, so the shipped text (which did not resolve
    # it) was not what was tested.
    _mode_fence > "$WORK/mode.sh"
    (cd "$1" && TASK_NAME="$2" MILESTONE_NUMBER="$3" STEP_ID="$4" \
        bash -c ". '$WORK/mode.sh'; echo \"MODE=\$MODE SOURCE=\$MODE_SOURCE\"")
}

_task_dir_with() {  # <task-name> <tasks.md body>
    local dir="$WORK/$1/.claude/dev/active/$1"
    mkdir -p "$dir"
    printf '%b' "$2" > "$dir/$1-tasks.md"
    : > "$dir/$1-provenance.log"
    : > "$dir/$1-context-log.md"
    printf '%s\n' "$WORK/$1"
}

@test "§5.2 Mode: a step with Mode: TYPO is BLOCKED, never dispatched as AFK" {
    local cwd; cwd=$(_task_dir_with t '## Milestone 1: T\n- Status: ACTIVE\n### Sub-step 1.1: s\n- Status: PENDING\n- Mode: TYPO\n')
    run _run_mode "$cwd" t 1 1.1
    [ "$status" -ne 0 ]
    [[ "$output" == *"BLOCKED"* ]]
    [[ "$output" == *"TYPO"* ]]
    [[ "$output" != *"MODE=AFK"* ]]
}

@test "§5.2 Mode: own, inherited and default resolution through the shipped text" {
    local cwd; cwd=$(_task_dir_with t '## Milestone 1: T\n- Status: ACTIVE\n- Mode: HITL\n### Sub-step 1.1: own\n- Status: PENDING\n- Mode: AFK\n### Sub-step 1.2: inherits\n- Status: PENDING\n## Milestone 2: U\n- Status: COMPLETE\n### Sub-step 2.1: default\n- Status: COMPLETE\n')
    run _run_mode "$cwd" t 1 1.1
    [ "$status" -eq 0 ]; [[ "$output" == *"MODE=AFK SOURCE=step"* ]]
    run _run_mode "$cwd" t 1 1.2
    [ "$status" -eq 0 ]; [[ "$output" == *"MODE=HITL SOURCE=milestone"* ]]
    run _run_mode "$cwd" t 2 2.1
    [ "$status" -eq 0 ]; [[ "$output" == *"MODE=HITL SOURCE=default"* ]]
}

# ---------------------------------------------------------------------------
# §7.1 HARD-gate approval — executed as shipped, in a FRESH shell
#
# The §6.8 review of M5 found this fence relied on ${GATE} and
# ${MILESTONE_TITLE} left over from §6.7; in a shell that had not run §6.7 it
# skipped the approval check with rc 0 and no output. It now asks the gate
# itself. These cases run it alone, with nothing inherited.
# ---------------------------------------------------------------------------

_approval_fence() {
    awk '/^### 7\.1 /{f=1} f && /^```bash$/{g=1; next} g && /^```$/{exit} g' "$MILESTONE_CMD"
}

_run_approval() {  # <cwd> <task-name>
    _approval_fence > "$WORK/approval.sh"
    (cd "$1" && env -i PATH="$PATH" HOME="$HOME" CLAUDE_HOME="$CLAUDE_HOME" TASK_NAME="$2" bash "$WORK/approval.sh")
}

@test "§7.1 fence: HARD gate with no approval artifact -> BLOCKED, in a fresh shell" {
    local cwd; cwd=$(_task_dir_from one-active hard)
    run _run_approval "$cwd" hard
    [ "$status" -ne 0 ]
    [[ "$output" == *"GATE APPROVAL: Milestone 2: The one being gated"* ]]
}

@test "§7.1 fence: HARD gate with the exact approval artifact -> passes" {
    local cwd; cwd=$(_task_dir_from one-active hardok)
    printf '## [2026-09-11] GATE APPROVAL: Milestone 2: The one being gated\n- Gate: HARD\n- Approved by: user\n- Criteria verified: 4/4\n- Decision: APPROVED\n' >> "$cwd/.claude/dev/active/hardok/hardok-context-log.md"
    run _run_approval "$cwd" hardok
    [ "$status" -eq 0 ]
}

@test "§7.1 fence: an approval heading whose Decision is REJECTED does not pass" {
    # Pre-existing fail-open found by the M5 §6.8 security audit: the check
    # matched the heading line only.
    local cwd; cwd=$(_task_dir_from one-active hardrej)
    printf '## [2026-09-11] GATE APPROVAL: Milestone 2: The one being gated\n- Gate: HARD\n- Decision: REJECTED\n' >> "$cwd/.claude/dev/active/hardrej/hardrej-context-log.md"
    run _run_approval "$cwd" hardrej
    [ "$status" -ne 0 ]
    [[ "$output" == *"Decision: APPROVED"* ]]
}

@test "§7.1 fence: a heading with no Decision line at all does not pass" {
    local cwd; cwd=$(_task_dir_from one-active hardbare)
    echo "## [2026-09-11] GATE APPROVAL: Milestone 2: The one being gated" >> "$cwd/.claude/dev/active/hardbare/hardbare-context-log.md"
    run _run_approval "$cwd" hardbare
    [ "$status" -ne 0 ]
}

@test "§7.1 fence: an approval for a different milestone does not satisfy it" {
    local cwd; cwd=$(_task_dir_from one-active hardother)
    echo "## [2026-09-11] GATE APPROVAL: Milestone 1: Done already" >> "$cwd/.claude/dev/active/hardother/hardother-context-log.md"
    run _run_approval "$cwd" hardother
    [ "$status" -ne 0 ]
}

@test "§7.1 fence: SOFT gate needs no artifact" {
    local cwd; cwd=$(_task_dir_from one-active soft)
    sed -i 's/^- Gate: HARD$/- Gate: SOFT/' "$cwd/.claude/dev/active/soft/soft-tasks.md"
    run _run_approval "$cwd" soft
    [ "$status" -eq 0 ]
}

@test "§7.1 fence: an unreadable plan is BLOCKED, never a skipped check" {
    local cwd; cwd=$(_task_dir_from two-active amb)
    run _run_approval "$cwd" amb
    [ "$status" -ne 0 ]
    [[ "$output" == *"BLOCKED"* ]]
}

@test "the approval fence extractor is not vacuous" {
    _approval_fence | grep -q 'aa_ma_gate'
    _approval_fence | grep -q 'GATE APPROVAL'
}

@test "the Mode fence extractor is not vacuous" {
    _mode_fence | grep -q 'aa_ma_gate'
    _mode_fence | grep -q -- '--step'
}

@test "the fence extractor is not vacuous" {
    [ "$(_gate_fence | grep -c 'aa_ma_gate')" -ge 1 ]
    _gate_fence | grep -q 'ENG-STANDARDS-GATE: PASS'
}

@test "no bash function parses a milestone block for an enforcing decision" {
    # The enforcing sites are the §6.7/§7.1 fences and verify-impl Step 1.
    # Every reading there must come from aa_ma_gate; the retired awk helpers
    # must not be referenced.
    for f in "$MILESTONE_CMD" "$REPO_ROOT/claude-code/skills/verify-impl/SKILL.md"; do
        ! grep -qE 'aa_ma_(extract_milestone_block|field_value|count_field|active_milestone_strict|is_milestone_heading)' "$f"
    done
    grep -q 'aa_ma_gate' "$MILESTONE_CMD"
    grep -q 'aa_ma_gate' "$REPO_ROOT/claude-code/skills/verify-impl/SKILL.md"
}

@test "aa_ma_gate resolves the forge checkout through the install.sh symlink, from another directory" {
    # The launcher derives --project from readlink -f on its own path. Both
    # bats files source the in-repo lib directly, so until this case nothing
    # exercised the symlinked-into-~/.claude shape a consumer actually runs.
    local fake_home="$WORK/home"; mkdir -p "$fake_home/hooks/lib" "$WORK/elsewhere"
    ln -s "$HELPER" "$fake_home/hooks/lib/aa-ma-parse.sh"
    run bash -c "cd '$WORK/elsewhere' && . '$fake_home/hooks/lib/aa-ma-parse.sh' && aa_ma_gate '$FIXDIR/one-active-tasks.md'"
    [ "$status" -eq 0 ]
    [[ "$output" == *"heading=Milestone 2: The one being gated"* ]]
}

# ---------------------------------------------------------------------------
# Library resolution is written into every fence on purpose (each must run in
# a fresh shell — see the §7.1 history). Duplication is tolerable only while
# the copies are identical; plan-verification's had already diverged once.
# ---------------------------------------------------------------------------

_resolution_snippets() {  # prints one normalised snippet per site
    for f in "$MILESTONE_CMD" "$REPO_ROOT/claude-code/skills/verify-impl/SKILL.md" "$REPO_ROOT/claude-code/skills/plan-verification/SKILL.md"; do
        awk '/^[[:space:]]*for _cand in \\$/{f=1} f{print} f && /aa-ma-parse.sh"; do$/{g=1} g && /^[[:space:]]*done$/{f=0; g=0; print "--"}' "$f" \
            | sed -E 's/^[[:space:]]+//; s/\[\[ -f/[ -f/; s/\]\] &&/] \&\&/'
    done
}

@test "every lib-resolution snippet is byte-identical after normalisation" {
    local snippets; snippets=$(_resolution_snippets)
    local n; n=$(printf '%s\n' "$snippets" | grep -c '^--$')
    [ "$n" -ge 5 ] || { echo "expected >=5 resolution sites, found $n" >&2; false; }
    local distinct; distinct=$(printf '%s\n' "$snippets" | awk 'BEGIN{RS="--\n"} NF{print}' | sort -u | wc -l)
    # One canonical snippet (3 lines: for / cand1 / cand2 / done) => sort -u of
    # the concatenated lines has exactly as many lines as one snippet.
    local one; one=$(printf '%s\n' "$snippets" | awk 'BEGIN{RS="--\n"} NF{print; exit}' | wc -l)
    [ "$distinct" -eq "$one" ] || { printf '%s\n' "$snippets" >&2; false; }
}
