# Stage C: code review and 3-source security pass — the parallel code-reviewer and security-auditor dispatch, Bandit and ShellCheck, and the findings aggregation.

## Contents

  - [Stage C — Code review + 3-source security pass](#stage-c--code-review--3-source-security-pass)

### Stage C — Code review + 3-source security pass

Four parallel sources, all writing severity-tagged findings to
`/tmp/sole-dev-merge-{review,security,bandit,shellcheck}-<slug>.{md,json}`
following the explicit `[CRITICAL]|[HIGH]|[MEDIUM]|[LOW]` contract from
reference.md.

**Step 1 — Dispatch in parallel (instructions to Claude executor):**

1. Pick a `SLUG` (e.g., `SLUG=$(date +%s)`). Export it so the bash aggregator
   below can find the output paths.
2. Dispatch **C1** and **C2** in a SINGLE message with two `Agent` tool calls:
   - **C1** — `feature-dev:code-reviewer` agent (fallback: `code-reviewer`).
     Prompt: review `git diff ${BASE_REF}...HEAD`. Emit findings using
     EXACTLY the severity-prefix contract:
     `[CRITICAL]|[HIGH]|[MEDIUM]|[LOW] <one-line> — <path>:<line>`. Write
     output to `/tmp/sole-dev-merge-review-${SLUG}.md`.
   - **C2** — `security-auditor` agent (`~/.claude/agents/security-auditor.md`).
     Same severity contract; output to `/tmp/sole-dev-merge-security-${SLUG}.md`.
     Focus: input validation, auth/secrets, command injection, path traversal,
     hardcoded creds, OWASP top-10.

**Step 2 — C3 (Bandit) + C4 (ShellCheck) + aggregation (single bash block):**

```bash
# === stage-c-aggregate (BEGIN) ===
set -euo pipefail

SLUG="${SLUG:-$(date +%s)}"
REVIEW_OUT="/tmp/sole-dev-merge-review-${SLUG}.md"
SECURITY_OUT="/tmp/sole-dev-merge-security-${SLUG}.md"
BANDIT_OUT="/tmp/sole-dev-merge-bandit-${SLUG}.json"
SHELLCHECK_OUT="/tmp/sole-dev-merge-shellcheck-${SLUG}.json"
FINDINGS="/tmp/sole-dev-merge-findings-${SLUG}.md"

: > "$FINDINGS"  # truncate / create

# === CANONICAL severity-mapping tables (single source-of-truth) ===
# These JSON literals are the AUTHORITATIVE mapping for unifying Bandit and
# ShellCheck severities into the [CRITICAL]/[HIGH]/[MEDIUM]/[LOW] contract.
# reference.md mirrors these tables for human consumption; the runtime
# source is HERE. When Bandit or ShellCheck adds a new severity tier,
# update these two literals AND the corresponding tables in reference.md
# in the SAME commit.
export BANDIT_SEV_JSON='{"HIGH": "CRITICAL", "MEDIUM": "HIGH", "LOW": "MEDIUM"}'
export SHELLCHECK_SEV_JSON='{"error": "CRITICAL", "warning": "HIGH", "info": "MEDIUM", "style": "LOW"}'
# === END canonical severity-mapping tables ===

SEVERITY_RE='^\[(CRITICAL|HIGH|MEDIUM|LOW)\][[:space:]]+'

# parse_agent_file: append contract-conforming lines from agent output.
# Safe-default per plan §M2 risk #1: if file has content but ZERO lines match
# the contract, classify ALL content as [HIGH] (forces user review) and log
# the parse failure to stdout.
parse_agent_file() {
    local file="$1" source_name="$2"
    [[ ! -s "$file" ]] && return 0
    if grep -qE "$SEVERITY_RE" "$file"; then
        grep -E "$SEVERITY_RE" "$file" >> "$FINDINGS"
    else
        echo "Stage C: parse failure on $source_name — applying safe-default [HIGH]"
        while IFS= read -r line; do
            [[ -z "$line" ]] && continue
            echo "[HIGH]     ${line} — (parse-failure: $source_name)" >> "$FINDINGS"
        done < "$file"
    fi
}

# C1 — code-reviewer agent output
parse_agent_file "$REVIEW_OUT" "code-reviewer"

# C2 — security-auditor agent output
parse_agent_file "$SECURITY_OUT" "security-auditor"

# C3 — Bandit on changed Python (only if any)
#
# Same contract as C4 below, and if anything this one matters more: bandit is
# not a declared dependency of this repo (absent from pyproject.toml, not
# installed by `uv sync`), and $BANDIT_OUT is the trusted input driving Stage D's
# B602 auto-remediation — so a missing scanner silently disabled detection AND
# fixing. Bandit exits 0 (clean) or 1 (findings); above 1, or an empty report,
# means it did not run.
BANDIT_BIN="${BANDIT_BIN:-bandit}"
if [[ -n "${CHANGED_PY:-}" ]]; then
    BANDIT_RC=0
    # shellcheck disable=SC2086  # intentional word-splitting for multi-file arg
    "$BANDIT_BIN" -f json $CHANGED_PY > "$BANDIT_OUT" 2>/dev/null || BANDIT_RC=$?
    if [[ "$BANDIT_RC" -gt 1 || ! -s "$BANDIT_OUT" ]]; then
        echo "Stage C: WARNING — '${BANDIT_BIN}' produced no report" \
             "(rc=${BANDIT_RC}); Python findings are UNKNOWN, not zero."
        echo "[HIGH]     C3 NOT RUN — '${BANDIT_BIN}' unavailable or produced no report (rc=${BANDIT_RC}); Python findings UNKNOWN — (scanner-unavailable)" >> "$FINDINGS"
    else
        # Severity mapping loaded from $BANDIT_SEV_JSON (canonical above).
        python3 - "$BANDIT_OUT" >> "$FINDINGS" <<'PY' || true
import json, os, sys
try:
    with open(sys.argv[1]) as f:
        data = json.load(f)
except (json.JSONDecodeError, FileNotFoundError):
    # stdout is appended to $FINDINGS — see the matching note in C4.
    print("[HIGH]     C3 REPORT UNPARSEABLE — scanner output was not valid JSON;"
          " Python findings UNKNOWN — (scanner-output-unparseable)")
    sys.exit(0)
sev_map = json.loads(os.environ["BANDIT_SEV_JSON"])
for r in data.get("results", []):
    sev = sev_map.get(r.get("issue_severity", ""), "LOW")
    msg = r.get("issue_text", "(no msg)")
    path = r.get("filename", "?")
    line = r.get("line_number", 0)
    test_id = r.get("test_id", "?")
    print(f"[{sev}]     {test_id} {msg} — {path}:{line}")
PY
    fi
fi

# C4 — ShellCheck on changed shell (only if any)
#
# A scanner that did not run must never be reported as a scanner that found
# nothing: the second is a clean bill of health on shell nobody reviewed.
#
# Test the REPORT, not the binary. `command -v` answers "is something on PATH",
# which is a different question — `true`, `:` and a present-but-broken install
# all resolve and all leave an empty report. ShellCheck exits 0 (clean) or 1
# (findings); anything above 1, or an empty report, means it did not run.
#
# SHELLCHECK_BIN is a seam for testing that degraded path without uninstalling
# anything.
SHELLCHECK_BIN="${SHELLCHECK_BIN:-shellcheck}"
if [[ -n "${CHANGED_SH:-}" ]]; then
    SHELLCHECK_RC=0
    # shellcheck disable=SC2086  # intentional word-splitting for multi-file arg
    "$SHELLCHECK_BIN" -f json $CHANGED_SH > "$SHELLCHECK_OUT" 2>/dev/null \
        || SHELLCHECK_RC=$?
    if [[ "$SHELLCHECK_RC" -gt 1 || ! -s "$SHELLCHECK_OUT" ]]; then
        # Safe-default, same contract parse_agent_file uses above: the degraded
        # state is written INTO $FINDINGS, not merely echoed. Stage D reads
        # $FINDINGS and nothing else, so a stdout-only warning would leave the
        # machine-readable verdict byte-identical to a clean scan and let the
        # gate advance on unscanned shell.
        echo "Stage C: WARNING — '${SHELLCHECK_BIN}' produced no report" \
             "(rc=${SHELLCHECK_RC}); shell findings are UNKNOWN, not zero."
        echo "[HIGH]     C4 NOT RUN — '${SHELLCHECK_BIN}' unavailable or produced no report (rc=${SHELLCHECK_RC}); shell findings UNKNOWN — (scanner-unavailable)" >> "$FINDINGS"
    else
        # Severity mapping loaded from $SHELLCHECK_SEV_JSON (canonical above).
        python3 - "$SHELLCHECK_OUT" >> "$FINDINGS" <<'PY' || true
import json, os, sys
try:
    with open(sys.argv[1]) as f:
        data = json.load(f)
except (json.JSONDecodeError, FileNotFoundError):
    # stdout is appended to $FINDINGS. A half-written or non-JSON report is
    # evidence the scanner died, not evidence the code is clean — exiting
    # quietly here was the last path by which C4 could report zero without
    # having run.
    print("[HIGH]     C4 REPORT UNPARSEABLE — scanner output was not valid JSON;"
          " shell findings UNKNOWN — (scanner-output-unparseable)")
    sys.exit(0)
sev_map = json.loads(os.environ["SHELLCHECK_SEV_JSON"])
items = data if isinstance(data, list) else data.get("comments", [])
for r in items:
    sev = sev_map.get(r.get("level", ""), "LOW")
    msg = r.get("message", "(no msg)")
    path = r.get("file", "?")
    line = r.get("line", 0)
    code = r.get("code", 0)
    print(f"[{sev}]     SC{code} {msg} — {path}:{line}")
PY
    fi
fi

TOTAL=$(grep -cE "^\[(CRITICAL|HIGH|MEDIUM|LOW)\]" "$FINDINGS" || true)
echo "Stage C aggregate: ${TOTAL} findings → $FINDINGS"
# === stage-c-aggregate (END) ===
```
