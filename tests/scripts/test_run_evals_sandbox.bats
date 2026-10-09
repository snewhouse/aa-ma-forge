#!/usr/bin/env bats
# scripts/run-evals.sh — advisory skill evals in a sandbox (ADR-0021, code-conventions-impact M4.5).
#
# Always-on cases stub `claude` (CLAUDE_BIN) and check what the script hands it: the
# environment, the flags, the output. Cases tagged LIVE run the real `claude plugin eval`
# against hostile fixture cases and cost money; they run only with AA_MA_EVAL_LIVE=1.

bats_require_minimum_version 1.5.0

setup() {
  REPO_ROOT="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)"
  RUN_EVALS="${REPO_ROOT}/scripts/run-evals.sh"
  WORK="$(mktemp -d "${BATS_TMPDIR}/run-evals.XXXXXX")"
  export REPO_ROOT RUN_EVALS WORK
  export RUN_EVALS_RESULTS="$WORK/results"
}

teardown() { rm -rf "$WORK"; }

# A stub `claude`: records argv and env, then writes a plugin-eval-shaped result JSON.
_stub_claude() {
  mkdir -p "$WORK/bin"
  # The path is baked in: run-evals.sh runs claude under `env -i`, so no exported
  # variable reaches the stub (that is the point of the scrubbed-environment case).
  printf '#!/usr/bin/env bash\nSTUB_DIR=%q\n' "$WORK" > "$WORK/bin/claude"
  cat >> "$WORK/bin/claude" <<'EOF2'
printf '%s\n' "$@" > "$STUB_DIR/argv"
env > "$STUB_DIR/env"
pwd > "$STUB_DIR/pwd"
json=""; prev=""
for a in "$@"; do [[ "$prev" == "--json" ]] && json="$a"; prev="$a"; done
cat > "$json" <<JSON
{"costUsd": 0.0123, "cases": [
 {"name": "a-pass", "dir": "evals/x/a-pass", "aggregates": {"score": 1, "passRate": 1}, "arms": {"with": [{"error": null}]}},
 {"name": "b-fail", "dir": "evals/x/b-fail", "aggregates": {"score": 0.5, "passRate": 0}, "arms": {"with": [{"error": null, "graders": [{"name": "skill-fired", "passed": false}, {"name": "result", "passed": true}]}]}}
]}
JSON
exit 1
EOF2
  chmod +x "$WORK/bin/claude"
  export CLAUDE_BIN="$WORK/bin/claude"
}

@test "never bypasses permissions" {
  run grep -nE 'bypassPermissions|dangerously-skip-permissions' "$RUN_EVALS"
  [ "$status" -eq 1 ]
}

@test "runs claude plugin eval from the repo root with the fixed advisory flags" {
  _stub_claude
  run "$RUN_EVALS"
  [ "$status" -eq 0 ]
  [ "$(cat "$WORK/pwd")" = "$REPO_ROOT" ]
  argv="$(cat "$WORK/argv")"
  [[ "$argv" == plugin$'\n'eval$'\n'.* ]]
  for flag in --no-publish --scaffold --trust-plugin; do grep -qx -- "$flag" "$WORK/argv"; done
  grep -qx -- '--runs' "$WORK/argv" && grep -A1 -x -- '--runs' "$WORK/argv" | tail -1 | grep -qx 1
  grep -A1 -x -- '--ablation' "$WORK/argv" | tail -1 | grep -qx none
  grep -qx -- '--max-cost-usd' "$WORK/argv"
}

@test "grants no shell, write, network or gh tool to the agent" {
  _stub_claude
  run "$RUN_EVALS"
  [ "$status" -eq 0 ]
  run grep -nE '^(Bash|Write|Edit|WebFetch|WebSearch|NotebookEdit)|--allow-tools|--allow-real-servers|--mocks' "$WORK/argv"
  [ "$status" -eq 1 ]
}

@test "passes claude a scrubbed environment: no git, GitHub or SSH credentials" {
  _stub_claude
  GH_TOKEN=leak GITHUB_TOKEN=leak SSH_AUTH_SOCK=/tmp/leak AWS_SECRET_ACCESS_KEY=leak run "$RUN_EVALS"
  [ "$status" -eq 0 ]
  run grep -E '^(GH_TOKEN|GITHUB_TOKEN|SSH_AUTH_SOCK|AWS_SECRET_ACCESS_KEY)=' "$WORK/env"
  [ "$status" -eq 1 ]
  grep -q '^PATH=' "$WORK/env"
  grep -q '^HOME=' "$WORK/env"
}

@test "drops ANTHROPIC_API_KEY unless RUN_EVALS_ALLOW_API_KEY=1, so evals never switch to API billing" {
  _stub_claude
  ANTHROPIC_API_KEY=sk-test run "$RUN_EVALS"
  [ "$status" -eq 0 ]
  run grep -E '^ANTHROPIC_API_KEY=' "$WORK/env"
  [ "$status" -eq 1 ]
  [[ "$(cat "$WORK/env")" != *sk-test* ]]
  ANTHROPIC_API_KEY=sk-test RUN_EVALS_ALLOW_API_KEY=1 run "$RUN_EVALS"
  [ "$status" -eq 0 ]
  grep -qx 'ANTHROPIC_API_KEY=sk-test' "$WORK/env"
}

@test "writes one JSONL line per case and a summary, and exits 0 with rc in the last line" {
  _stub_claude
  run "$RUN_EVALS"
  [ "$status" -eq 0 ]
  f="$WORK/results/$(date +%F).jsonl"
  [ "$(wc -l < "$f")" -eq 2 ]
  jq -e 'select(.case=="evals/x/a-pass") | .verdict=="pass" and .score==1' "$f"
  jq -e 'select(.case=="evals/x/b-fail") | .verdict=="fail" and .failed==["skill-fired"]' "$f"
  jq -e 'select(.case=="evals/x/a-pass") | .failed==[]' "$f"
  [[ "$output" == *"run-evals: 2 cases, 1 pass, 1 fail"* ]]
  [ "${lines[-1]}" = "run-evals: rc=1" ]
}

@test "a claude that produces no result is reported, still exit 0" {
  mkdir -p "$WORK/bin"; printf '#!/usr/bin/env bash\necho boom >&2\nexit 7\n' > "$WORK/bin/claude"; chmod +x "$WORK/bin/claude"
  CLAUDE_BIN="$WORK/bin/claude" run "$RUN_EVALS"
  [ "$status" -eq 0 ]
  [[ "$output" == *"run-evals: no result"* ]]
  [ "${lines[-1]}" = "run-evals: rc=7" ]
}

@test "every fixture scaffold makes a git repo with no remote" {
  n=0
  for s in "$REPO_ROOT"/evals/_lib/*.sh; do
    d="$(mktemp -d "$WORK/ws.XXXXXX")"
    (cd "$d" && HOME="$WORK" bash "$s")
    git -C "$d" rev-parse --git-dir >/dev/null
    [ -z "$(git -C "$d" remote)" ]
    n=$((n + 1))
  done
  [ "$n" -ge 1 ]
}

# --- LIVE (AA_MA_EVAL_LIVE=1): real claude plugin eval, hostile fixture cases ---------

_live() { [[ "${AA_MA_EVAL_LIVE:-0}" == 1 ]] || skip "LIVE: set AA_MA_EVAL_LIVE=1 (paid)"; }

@test "LIVE: a case told to git push cannot run it, and a case told to write \$HOME/.probe leaves it absent" {
  _live
  rm -f "$HOME/.probe"
  RUN_EVALS_DIR=tests/scripts/fixtures/evals-sandbox RUN_EVALS_MODEL=haiku RUN_EVALS_MAX_COST_USD=0.5 run "$RUN_EVALS"
  [ "$status" -eq 0 ]
  f="$WORK/results/$(date +%F).jsonl"
  jq -e 'select(.case|endswith("git-push")) | .verdict=="pass"' "$f"
  jq -e 'select(.case|endswith("home-write")) | .verdict=="pass"' "$f"
  [ ! -e "$HOME/.probe" ]
}
