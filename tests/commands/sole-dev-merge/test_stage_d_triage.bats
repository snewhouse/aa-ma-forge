#!/usr/bin/env bats
# test_stage_d_triage.bats — verifies Stage D (findings triage):
#   - Bandit B602 (dynamic-input → CRITICAL) auto-fix commit lands with the
#     expected subject regex.
#   - Post-fix `bandit -t B602` returns zero Issue lines.
#   - HIGH/MEDIUM panel logging cardinality (ceil(N/4) panels, last panel
#     = remainder).
#   - Zero-findings → zero AUQ_DISPATCH events.
#
# Plan §4 2.5 acceptance verified.

setup() {
  REPO_ROOT="$(cd "$BATS_TEST_DIRNAME/../../.." && pwd)"
  # ruff from project venv + bandit from system miniforge
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

  # Unique slug per test so /tmp/... files don't collide across @tests
  export SOLE_DEV_MERGE_SLUG="batstest-${BATS_TEST_NUMBER}"
  export AUQ_LOG="/tmp/sole-dev-merge-auq-${SOLE_DEV_MERGE_SLUG}.log"
}

teardown() {
  cd /
  rm -rf "$TMPDIR"
  rm -f "/tmp/sole-dev-merge-review-${SOLE_DEV_MERGE_SLUG}".* \
        "/tmp/sole-dev-merge-security-${SOLE_DEV_MERGE_SLUG}".* \
        "/tmp/sole-dev-merge-bandit-${SOLE_DEV_MERGE_SLUG}".* \
        "/tmp/sole-dev-merge-shellcheck-${SOLE_DEV_MERGE_SLUG}".* \
        "/tmp/sole-dev-merge-findings-${SOLE_DEV_MERGE_SLUG}".* \
        "/tmp/sole-dev-merge-auq-${SOLE_DEV_MERGE_SLUG}".*
}

@test "Stage D: Bandit B602 (dynamic) → CRITICAL auto-fix commit + zero post-fix issues" {
  # IMPORTANT: bats `run` invokes commands in a subshell — globals like
  # CHANGED_PY_ARR set in stage_b_scope would NOT persist to stage_c3_bandit.
  # Call the chain directly (no `run`) so state propagates.
  mkdir -p src
  cat > src/danger.py <<'PYEOF'
import subprocess


def run(user_cmd):
    return subprocess.run(user_cmd, shell=True)
PYEOF
  git add src/danger.py
  git commit -q -m "feat-b602"

  stage_b_scope >/dev/null
  [ "${#CHANGED_PY_ARR[@]}" -eq 1 ]   # sanity: scope picked up src/danger.py

  stage_c3_bandit >/dev/null
  [ -s "/tmp/sole-dev-merge-review-${SOLE_DEV_MERGE_SLUG}.md.bandit" ]

  stage_d_triage >/dev/null

  # Acceptance 1: commit subject prefix per plan §4 2.5
  subj=$(git log -1 --format=%s)
  [[ "$subj" == "fix(review): apply CRITICAL bandit"* ]]

  # Acceptance 2: post-fix bandit -t B602 returns zero Issue lines
  n_b602=$(bandit -t B602 src/danger.py 2>&1 | grep -c '^>> Issue:' || true)
  [ "$n_b602" = "0" ]

  # Acceptance 3: src/danger.py now lacks shell=True
  ! grep -qF "shell=True" src/danger.py
}

@test "Stage D: 5 HIGH findings ⇒ 2 AUQ_DISPATCH panels (ceil(5/4))" {
  # Mock the review-output file directly (skip C1/C2/C3/C4 — focus on Stage D)
  for i in 1 2 3 4 5; do
    echo "[HIGH] finding $i — src/file.py:$i" >> "/tmp/sole-dev-merge-review-${SOLE_DEV_MERGE_SLUG}.md"
  done

  run stage_d_triage
  [ "$status" -eq 0 ]

  # Acceptance: 2 panels logged (ceil(5/4) = 2)
  n_panels=$(wc -l < "$AUQ_LOG")
  [ "$n_panels" -eq 2 ]

  # Acceptance: first panel = 4 options (full), second = 1 option (remainder)
  first=$(head -1 "$AUQ_LOG")
  last=$(tail -1 "$AUQ_LOG")
  [[ "$first" == *"n_options=4"* ]]
  [[ "$last" == *"n_options=1"* ]]
}

@test "Stage D: zero HIGH/MEDIUM ⇒ zero AUQ_DISPATCH events" {
  # Empty review file (no findings)
  : > "/tmp/sole-dev-merge-review-${SOLE_DEV_MERGE_SLUG}.md"

  run stage_d_triage
  [ "$status" -eq 0 ]

  # Acceptance: AUQ_LOG is either non-existent or empty
  if [ -f "$AUQ_LOG" ]; then
    [ ! -s "$AUQ_LOG" ]
  fi
}

@test "Stage D: LOW findings only ⇒ PR-body advisory file populated, no auto-fix, no AUQ" {
  for i in 1 2 3; do
    echo "[LOW] style finding $i — src/file.py:$i" >> "/tmp/sole-dev-merge-review-${SOLE_DEV_MERGE_SLUG}.md"
  done

  run stage_d_triage
  [ "$status" -eq 0 ]

  pr_notes="/tmp/sole-dev-merge-findings-${SOLE_DEV_MERGE_SLUG}.md.pr-notes"
  [ -s "$pr_notes" ]
  run bash -c "grep -c '^\[LOW\]' '$pr_notes'"
  [ "$output" = "3" ]

  # No auto-fix commit, no AUQ
  if [ -f "$AUQ_LOG" ]; then
    [ ! -s "$AUQ_LOG" ]
  fi
}

@test "Stage D: 4 MEDIUM ⇒ exactly 1 AUQ panel of size 4" {
  for i in 1 2 3 4; do
    echo "[MEDIUM] m finding $i — src/file.py:$i" >> "/tmp/sole-dev-merge-review-${SOLE_DEV_MERGE_SLUG}.md"
  done

  run stage_d_triage
  [ "$status" -eq 0 ]

  n_panels=$(wc -l < "$AUQ_LOG")
  [ "$n_panels" -eq 1 ]
  [[ "$(head -1 "$AUQ_LOG")" == *"n_options=4"* ]]
}
