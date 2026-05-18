#!/usr/bin/env bats
# test_stage_c_dispatch.bats — verifies Stage C1 (code-reviewer) and Stage C2
# (security-auditor) dispatch contracts.
#
# In production these stages instruct the AI to invoke the Agent tool. Bats
# can't invoke real Claude Code agents, so we exercise the
# MOCK_AGENT_DISPATCH=1 short-circuit: the stage copies a fixture file to the
# expected output path. This validates the wiring (env var → fixture path →
# downstream consumption by Stage D) without requiring the real Agent tool.

setup() {
  REPO_ROOT="$(cd "$BATS_TEST_DIRNAME/../../.." && pwd)"
  export PATH="$REPO_ROOT/.venv/bin:/home/sjnewhouse/miniforge3/envs/bio312_07_25/bin:$PATH"

  TMPDIR="$(mktemp -d)"
  cd "$TMPDIR" || return 1
  git init -b main -q
  git config user.email "test@test.com"
  git config user.name "test"
  git config commit.gpgsign false
  echo "x = 1" > baseline.py
  git add baseline.py
  git commit -q -m "baseline"
  git checkout -b feat -q

  # shellcheck source=fixtures/load_stages.bash
  source "$REPO_ROOT/tests/commands/sole-dev-merge/fixtures/load_stages.bash"
  eval "$(SOLE_DEV_MERGE_MD=$REPO_ROOT/claude-code/commands/sole-dev-merge.md load_stages)"

  export SOLE_DEV_MERGE_SLUG="dispatch-${BATS_TEST_NUMBER}"
  export AUQ_LOG="/tmp/sole-dev-merge-auq-${SOLE_DEV_MERGE_SLUG}.log"

  # Per-test fixture directory
  FIXDIR="$TMPDIR/fixtures"
  mkdir -p "$FIXDIR"
}

teardown() {
  cd /
  rm -rf "$TMPDIR"
  rm -f "/tmp/sole-dev-merge-review-${SOLE_DEV_MERGE_SLUG}".* \
        "/tmp/sole-dev-merge-security-${SOLE_DEV_MERGE_SLUG}".* \
        "/tmp/sole-dev-merge-findings-${SOLE_DEV_MERGE_SLUG}".* \
        "/tmp/sole-dev-merge-auq-${SOLE_DEV_MERGE_SLUG}".*
}

@test "Stage C1: MOCK_AGENT_DISPATCH=1 with fixture copies to expected output path" {
  cat > "$FIXDIR/c1-fixture.md" <<'MOCKEOF'
[CRITICAL] hardcoded password — src/auth.py:42
[HIGH] missing input validation — src/api.py:17
MOCKEOF

  export MOCK_AGENT_DISPATCH=1
  export MOCK_AGENT_FIXTURE_C1="$FIXDIR/c1-fixture.md"

  stage_c1_review_dispatch >/dev/null

  out="/tmp/sole-dev-merge-review-${SOLE_DEV_MERGE_SLUG}.md"
  [ -s "$out" ]
  run cat "$out"
  [[ "$output" == *"hardcoded password"* ]]
  [[ "$output" == *"missing input validation"* ]]
}

@test "Stage C1: MOCK_AGENT_DISPATCH=1 without fixture writes empty findings file" {
  export MOCK_AGENT_DISPATCH=1
  unset MOCK_AGENT_FIXTURE_C1 2>/dev/null || true

  stage_c1_review_dispatch >/dev/null

  out="/tmp/sole-dev-merge-review-${SOLE_DEV_MERGE_SLUG}.md"
  [ -f "$out" ]
  [ ! -s "$out" ]   # exists but empty (size 0)
}

@test "Stage C2: MOCK_AGENT_DISPATCH=1 with fixture copies to security output path" {
  cat > "$FIXDIR/c2-fixture.md" <<'MOCKEOF'
[MEDIUM] unquoted path traversal — src/file.py:9
MOCKEOF

  export MOCK_AGENT_DISPATCH=1
  export MOCK_AGENT_FIXTURE_C2="$FIXDIR/c2-fixture.md"

  stage_c2_security_dispatch >/dev/null

  out="/tmp/sole-dev-merge-security-${SOLE_DEV_MERGE_SLUG}.md"
  [ -s "$out" ]
  run cat "$out"
  [[ "$output" == *"unquoted path traversal"* ]]
}

@test "Stage C1+C2 mocked + Stage D: 1 CRITICAL + 1 HIGH + 1 MEDIUM ⇒ correct AUQ count" {
  # C1 fixture: 1 CRITICAL + 1 HIGH (agent-emitted CRITICAL = user review tag, not auto-fix)
  cat > "$FIXDIR/c1.md" <<'MOCKEOF'
[CRITICAL] dangerous eval call — src/x.py:1
[HIGH] missing input check — src/y.py:2
MOCKEOF
  # C2 fixture: 1 MEDIUM
  cat > "$FIXDIR/c2.md" <<'MOCKEOF'
[MEDIUM] minor crypto concern — src/z.py:3
MOCKEOF

  export MOCK_AGENT_DISPATCH=1
  export MOCK_AGENT_FIXTURE_C1="$FIXDIR/c1.md"
  export MOCK_AGENT_FIXTURE_C2="$FIXDIR/c2.md"

  stage_c1_review_dispatch >/dev/null
  stage_c2_security_dispatch >/dev/null

  # Skip C3/C4 — no Python/shell files committed; ensures they no-op
  stage_d_triage >/dev/null

  # Aggregated findings: 1 CRITICAL + 1 HIGH + 1 MEDIUM = 2 HIGH+MEDIUM ⇒ 1 panel
  n_panels=$(wc -l < "$AUQ_LOG")
  [ "$n_panels" -eq 1 ]
  [[ "$(head -1 "$AUQ_LOG")" == *"n_options=2"* ]]
}

@test "Stage C dispatch: MOCK_AGENT_DISPATCH unset ⇒ functions emit instruction text without writing fixtures" {
  unset MOCK_AGENT_DISPATCH 2>/dev/null || true

  # Production path: function should run without error, emit instruction text,
  # and NOT create the output file (real Agent dispatch is the AI's job).
  out_c1="/tmp/sole-dev-merge-review-${SOLE_DEV_MERGE_SLUG}.md"
  rm -f "$out_c1"

  run stage_c1_review_dispatch
  [ "$status" -eq 0 ]
  [[ "$output" == *"dispatch feature-dev:code-reviewer"* ]]
  [ ! -f "$out_c1" ]
}
