#!/usr/bin/env bats
# test_smoke_e2e.bats — Smoke E2E for /sole-dev-merge.
#
# Plan §5.8 falsifiable AC: given a planted feature branch with 3 defects,
# the workflow exits 0 AND:
#   - branch removed from `git branch -r`
#   - main contains the rebased commits
#   - in-scope auto-fix commit is present
#   - CRITICAL Bandit B602 auto-fix is present
#   - out-of-scope `tests/codemem/dummy.py` modification is ABSENT on main
#
# Bats-feasible interpretation: bats cannot invoke `/sole-dev-merge` (a
# Claude Code slash command) and cannot run real `gh pr merge` against a
# live PR. The smoke chains the locally-executable stages
# (A → B → B-commit → C → D) end-to-end in a sandbox repo with mocked
# agent dispatch (MOCK_AGENT_DISPATCH=1) + Bandit + ShellCheck. Stages
# E0..G4 are covered by the per-stage bats suites with PATH-shadowed
# gh/glab stubs.
#
# Also covers Step 5.7 (migration banner): asserts the banner is present
# in the command markdown AND that AA_MA_SUPPRESS_MIGRATION_BANNER=1
# suppresses it (verified via stage-banner extract).

load fixtures/helpers

setup() {
    REPO_ROOT="$(cd "${BATS_TEST_DIRNAME}/../../.." && pwd)"
    COMMAND_MD="${REPO_ROOT}/claude-code/commands/sole-dev-merge.md"
    EXTRACT="${REPO_ROOT}/tests/commands/sole-dev-merge/fixtures/extract_stage.sh"

    SCRIPT_DIR="$(tmp_script_dir)"
    BATS_TMP="$(mktemp -d)"
    export BATS_TMP SCRIPT_DIR REPO_ROOT COMMAND_MD EXTRACT

    [[ -f "$COMMAND_MD" ]] || { echo "Missing $COMMAND_MD" >&2; return 1; }
    [[ -x "$EXTRACT"   ]] || { echo "Missing or non-exec $EXTRACT" >&2; return 1; }
}

teardown() {
    rm -rf "$BATS_TMP" "$SCRIPT_DIR"
    # SLUG is set inside the test body, which teardown still sees. Sweeping here
    # rather than at the end of the test is the point: an assertion that fails
    # mid-test aborts before any in-body cleanup, so the old placement only ever
    # cleaned up on the runs that had nothing to clean up after.
    sweep_slug_tmp
    # Remove the migration-banner sentinel so successive tests don't see
    # the "once per session" suppression effect.
    rm -f "${TMPDIR:-/tmp}/sole-dev-merge-banner-shown"
}

# ---------------------------------------------------------------------------
# Step 5.7 — migration banner
# ---------------------------------------------------------------------------

@test "Banner: command md contains stage-banner marker (Step 5.7)" {
    # Migration banner sits at the top of the command and prints on first
    # invocation post-deploy. ADR-0008 reference required per plan §5.7.
    grep -q '# === stage-banner (BEGIN) ===' "$COMMAND_MD"
    grep -q '# === stage-banner (END) ==='   "$COMMAND_MD"
}

@test "Banner: AA_MA_SUPPRESS_MIGRATION_BANNER=1 suppresses output (Step 5.7)" {
    local script="${SCRIPT_DIR}/banner.sh"
    bash "$EXTRACT" stage-banner "$COMMAND_MD" > "$script"
    chmod +x "$script"

    # With env var set → no output
    export AA_MA_SUPPRESS_MIGRATION_BANNER=1
    run bash "$script"
    [ "$status" -eq 0 ]
    [[ "$output" == "" ]]
}

@test "Banner: default (env var unset) prints banner with ADR-0008 reference (Step 5.7)" {
    local script="${SCRIPT_DIR}/banner.sh"
    bash "$EXTRACT" stage-banner "$COMMAND_MD" > "$script"
    chmod +x "$script"

    unset AA_MA_SUPPRESS_MIGRATION_BANNER || true
    run bash "$script"
    [ "$status" -eq 0 ]
    [[ "$output" == *"NOTE:"* ]]
    [[ "$output" == *"PR/MR workflow"* ]]
    [[ "$output" == *"ADR-0008"* ]]
}

# ---------------------------------------------------------------------------
# Step 5.8 — chained-stage smoke E2E (3-defect planted branch)
# ---------------------------------------------------------------------------

@test "Smoke E2E: 3-defect branch → out-of-scope reverted, in-scope fix + B602 fix committed (AC §5.8)" {
    # Extract all relevant stages into the script dir.
    local SA="${SCRIPT_DIR}/sa.sh" SB="${SCRIPT_DIR}/sb.sh"
    local SBC="${SCRIPT_DIR}/sbc.sh" SC="${SCRIPT_DIR}/sc.sh" SD="${SCRIPT_DIR}/sd.sh"
    bash "$EXTRACT" stage-a-preflight  "$COMMAND_MD" > "$SA"
    bash "$EXTRACT" stage-b-scope      "$COMMAND_MD" > "$SB"
    bash "$EXTRACT" stage-b-commit     "$COMMAND_MD" > "$SBC"
    bash "$EXTRACT" stage-c-aggregate  "$COMMAND_MD" > "$SC"
    bash "$EXTRACT" stage-d-triage     "$COMMAND_MD" > "$SD"
    chmod +x "$SA" "$SB" "$SBC" "$SC" "$SD"

    # Stage B-commit + Stage D source aa-ma-footer.sh via $AA_MA_FOOTER_HELPER
    # env override (sandbox repo doesn't ship the helper).
    export AA_MA_FOOTER_HELPER="${REPO_ROOT}/claude-code/hooks/lib/aa-ma-footer.sh"
    [[ -f "$AA_MA_FOOTER_HELPER" ]] || { echo "Missing helper at $AA_MA_FOOTER_HELPER" >&2; return 1; }

    cd "$BATS_TMP"
    sandbox_init
    # Plant baseline on main: an out-of-scope file that should NOT be touched.
    mkdir -p tests/codemem src
    echo "# pre-existing out-of-scope file" > tests/codemem/dummy.py
    echo "ok" > src/existing.py
    git add -A
    mkcommit "init: baseline"
    # Wire up a fake remote so Stage A doesn't abort.
    git init --bare -q "${BATS_TMP}.bare.git"
    git remote add origin "${BATS_TMP}.bare.git"
    git push -q origin main

    # Branch off and plant 3 defects per plan §5.8.
    git checkout -q -b feature

    # Defect 1 (in-scope): ruff-fixable lint violation in a new .py file.
    cat > src/new_feature.py <<'PY'
import os
def hello( ):
    return os.path.join('a','b')
PY
    git add src/new_feature.py
    mkcommit "feat: add new_feature"

    # Defect 2 (CRITICAL Bandit B602): shell=True in a NEW changed file.
    cat > src/vuln.py <<'PY'
import subprocess
def run_cmd(cmd):
    return subprocess.run(cmd, shell=True)
PY
    git add src/vuln.py
    mkcommit "feat: add subprocess wrapper"

    # Defect 3 (out-of-scope dirt) will be planted AFTER Stage A — Stage A's
    # preflight aborts on `git status --porcelain` non-empty, so we must
    # plant the working-tree drift AFTER Stage A has captured BASE_REF and
    # exported it. Stage B then runs the L-007 guard against this drift.

    # === RUN CHAIN: Stage A → plant drift → Stage B → Stage B-commit ===
    # Stage A first (in a sourced subshell so exports propagate).
    set -a
    # shellcheck disable=SC1090
    source "$SA"
    set +a

    # NOW plant the out-of-scope drift after Stage A's preflight passed.
    echo "# out-of-scope drift planted post-preflight" \
        >> tests/codemem/dummy.py

    # Verify drift is in working tree (precondition for Stage B's L-007 guard)
    [ -n "$(git diff tests/codemem/dummy.py)" ]

    # Stage B: in-scope fix + L-007 revert of out-of-scope drift
    set -a
    # shellcheck disable=SC1090
    source "$SB"
    set +a

    # AC §5.8 part 1: out-of-scope file's diff is zero (L-007 reverted it).
    [ -z "$(git diff tests/codemem/dummy.py)" ]
    # In-scope file was ruff-fixed (def hello( ): → def hello():)
    grep -q '^def hello():' src/new_feature.py

    # Stage B-commit: lands the in-scope auto-fix as `chore(scope): pre-PR auto-fixes`
    set -a
    # shellcheck disable=SC1090
    source "$SBC"
    set +a

    # AC §5.8 part 2: in-scope auto-fix commit is on the feature branch
    [ "$(git log -1 --format=%s)" = "chore(scope): pre-PR auto-fixes" ]

    # === Stage C: mock agent dispatch with planted B602 finding ===
    SLUG="smoke_$$"
    export SLUG
    # Pre-populate fixture files for MOCK_AGENT_DISPATCH (per reference.md
    # test-harness contract). Both agents emit zero CRITICAL findings; the
    # B602 will come from real Bandit invocation in Stage C.
    : > "/tmp/sole-dev-merge-review-${SLUG}.md"
    : > "/tmp/sole-dev-merge-security-${SLUG}.md"
    export MOCK_AGENT_DISPATCH=1

    set -a
    # shellcheck disable=SC1090
    source "$SC" || true  # tolerate any nuances in aggregation
    set +a

    # Stage C should have run Bandit on src/vuln.py and detected B602.
    # Findings emit to /tmp/sole-dev-merge-findings-${SLUG}.md as CRITICAL.
    local findings="/tmp/sole-dev-merge-findings-${SLUG}.md"
    [ -f "$findings" ]
    grep -q '^\[CRITICAL\]' "$findings"
    grep -q 'B602' "$findings"

    # === Stage D: auto-fix the B602 ===
    set -a
    # shellcheck disable=SC1090
    source "$SD"
    set +a

    # AC §5.8 part 3: CRITICAL Bandit B602 auto-fix commit landed on feature.
    [[ "$(git log -1 --format=%s)" =~ ^fix\(review\):\ apply\ CRITICAL\ bandit ]]
    # Verify the fix mutated src/vuln.py (shell=True → shell=False)
    ! grep -q 'shell=True' src/vuln.py
    grep -q 'shell=False' src/vuln.py

    # AC §5.8 part 4: out-of-scope tests/codemem/dummy.py is STILL clean
    # (L-007 guard's revert held through B-commit + C + D).
    cmp -s tests/codemem/dummy.py <(git show main:tests/codemem/dummy.py)

    # Cleanup runs in teardown() via sweep_slug_tmp — see the note there on why
    # in-body cleanup could not be trusted.
}
