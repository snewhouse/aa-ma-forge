#!/usr/bin/env bash
# run-evals.sh — run the advisory skill-eval suite (evals/, ADR-0021) with `claude plugin eval`.
#
#   scripts/run-evals.sh [extra `claude plugin eval` args, e.g. --case 'impact-*']
#
# Advisory: exit 0 always; the last line is `run-evals: rc=<claude's exit code>`.
# Results append to .claude/evals/<YYYY-MM-DD>.jsonl (gitignored), one line per case.
#
# Sandbox, in layers:
#   - claude sees only PATH, HOME (its credentials live there) and locale from the environment:
#     no GH_TOKEN, GITHUB_TOKEN, SSH_AUTH_SOCK or cloud keys. ANTHROPIC_API_KEY is dropped too
#     unless RUN_EVALS_ALLOW_API_KEY=1: with a claude.ai login, evals then count against plan
#     usage and can never switch to per-token API billing.
#   - `claude plugin eval` gives every run a temp HOME and an empty workspace; each case's
#     scaffold makes a git repo there with no remote (evals/_lib/).
#   - No tool beyond the read-only set the case lists is granted: Bash, Write, Edit,
#     WebFetch and WebSearch are removed from the session, so `git push`, `gh` and network
#     calls cannot run. This replaces the `claude -p --disallowedTools` plan (M4.3 context-log).
#   - Permissions are never bypassed; the report is never published (the repo is public).
#
# Env: RUN_EVALS_DIR (eval dir below the repo root, default evals), RUN_EVALS_MODEL
# (default sonnet), RUN_EVALS_MAX_COST_USD (default 5), RUN_EVALS_RESULTS (default
# <repo>/.claude/evals), RUN_EVALS_ALLOW_API_KEY (1 forwards ANTHROPIC_API_KEY),
# CLAUDE_BIN (default claude; tests stub it).
# Needs jq, GNU readlink -f / date -I (Linux, or macOS 12.3+ with coreutils-compatible tools).

set -uo pipefail

REPO_ROOT="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/.." && pwd)"
EVAL_DIR="${RUN_EVALS_DIR:-evals}"
MODEL="${RUN_EVALS_MODEL:-sonnet}"
MAX_COST="${RUN_EVALS_MAX_COST_USD:-5}"  # USD list-price estimate; the full suite on sonnet costs well under this
RESULTS="${RUN_EVALS_RESULTS:-${REPO_ROOT}/.claude/evals}"
CLAUDE_BIN="${CLAUDE_BIN:-claude}"

OUT="$(mktemp -d "${TMPDIR:-/tmp}/run-evals.XXXXXX")"
trap 'rm -rf "${OUT}"' EXIT

keep=" PATH HOME LANG CLAUDE_CODE_OAUTH_TOKEN CLAUDE_CONFIG_DIR "
[[ "${RUN_EVALS_ALLOW_API_KEY:-0}" == 1 ]] && keep+="ANTHROPIC_API_KEY "

# Scrub by un-exporting, not `env -i NAME=value`: argv is world-readable in
# /proc/<pid>/cmdline, so a token passed there shows in `ps`. `export -n` keeps the
# value for this shell (CLAUDE_BIN, MODEL… may arrive exported) and hides it from claude.
(
    cd "${REPO_ROOT}" || exit 127
    export LANG="${LANG:-C.UTF-8}"
    for var in $(compgen -e); do
        [[ "${keep}" == *" ${var} "* ]] || export -n "${var?}"
    done
    exec "${CLAUDE_BIN}" plugin eval . \
        --eval-dir "${EVAL_DIR}" --no-publish --runs 1 --ablation none --scaffold --trust-plugin \
        --model "${MODEL}" --max-cost-usd "${MAX_COST}" \
        --output-dir "${OUT}/run" --json "${OUT}/result.json" "$@" </dev/null
) >"${OUT}/eval.log" 2>&1
rc=$?

if ! command -v jq >/dev/null 2>&1; then
    echo "run-evals: jq not found; cannot read ${CLAUDE_BIN} plugin eval's result" >&2
    echo "run-evals: no result (jq missing)"
    echo "run-evals: rc=${rc}"
    exit 0
fi

if [[ ! -s "${OUT}/result.json" ]]; then
    echo "run-evals: no result from ${CLAUDE_BIN} plugin eval; log tail:" >&2
    tail -n 20 "${OUT}/eval.log" >&2
    echo "run-evals: no result"
    echo "run-evals: rc=${rc}"
    exit 0
fi

mkdir -p "${RESULTS}"
jsonl="${RESULTS}/$(date +%F).jsonl"
jq -c --arg ts "$(date -Iseconds)" --arg model "${MODEL}" --argjson rc "${rc}" '
    .cases[] | {ts: $ts, case: .dir, verdict: (if .aggregates.score >= 1 then "pass" else "fail" end),
                score: .aggregates.score, rc: $rc, model: $model, error: .arms.with[0].error,
                failed: [.arms.with[0].graders[]? | select(.passed | not) | .name]}' \
    "${OUT}/result.json" >>"${jsonl}"
jq -r --arg jsonl "${jsonl}" '
    [.cases[] | .aggregates.score >= 1] as $p
    | "run-evals: \($p | length) cases, \($p | map(select(.)) | length) pass, \($p | map(select(. | not)) | length) fail, cost $\((.costUsd // 0) * 100 | round / 100) → \($jsonl)"' \
    "${OUT}/result.json"
echo "run-evals: rc=${rc}"
exit 0
