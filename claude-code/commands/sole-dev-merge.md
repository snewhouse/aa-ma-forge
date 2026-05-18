---
description: PR/MR-based merge workflow with scope-aware CI checks, review, security pass, and auto-merge
---

# /sole-dev-merge — PR/MR merge workflow (v2)

PR/MR-based merge workflow for sole developers. Runs scope-aware local CI
(closing L-007), dispatches code review + 3-source security pass
(security-auditor agent + Bandit + ShellCheck), opens a PR via `gh` or MR via
`glab` (default GitLab when both remotes present), polls CI to green, then
auto-merges with `--rebase --delete-branch` for linear history.

**Replaces:** the legacy fast-merge `/sole-dev-merge` user-local command. The
plugin install (`scripts/install.sh`) creates a symlink at
`~/.claude/commands/sole-dev-merge.md` after backing up the previous file to
`~/.claude/backups/aa-ma-forge-<timestamp>/`.

**Plan-of-record:** see ADR-0008 (`docs/adr/0008-sole-dev-merge-pr-workflow.md`)
once landed. Rationale for command-only design (no skill/lib pattern), 3-source
security rationale, and backward-compatibility strategy live there.

**Assumptions** (enforced by Stage A / Stage E0):
- One `/sole-dev-merge` invocation per repo at a time (no concurrency lock —
  sole-developer assumption).
- `gh auth status` / `glab auth status` succeed for the active remote.
- `main` is the default branch.

**Suppress migration banner:** `AA_MA_SUPPRESS_MIGRATION_BANNER=1`.

---

## Migration banner (runs FIRST, before Stage A)

The legacy user-local `/sole-dev-merge` (fast-merge) has been retired and
replaced by this PR/MR workflow per ADR-0008. `scripts/install.sh` auto-
backs-up the old command to `~/.claude/backups/aa-ma-forge-<ts>/` before
symlinking the new one. The banner alerts the operator on first invocation
post-deploy. Suppress with `AA_MA_SUPPRESS_MIGRATION_BANNER=1`.

```bash
# === stage-banner (BEGIN) ===
set -euo pipefail

# Migration banner per ADR-0008. Plan §5.7 falsifiable AC: env-var
# suppression. "Once per session" is implemented via a /tmp sentinel so
# subsequent invocations within the same login session stay silent.
if [[ "${AA_MA_SUPPRESS_MIGRATION_BANNER:-0}" != "1" ]]; then
    SENTINEL="${TMPDIR:-/tmp}/sole-dev-merge-banner-shown"
    if [[ ! -f "$SENTINEL" ]]; then
        cat <<'BANNER'
NOTE: /sole-dev-merge has been updated to a PR/MR workflow with 3-source
security review and idempotent auto-merge (ADR-0008). The legacy fast-merge
path is retired; the user-local copy was auto-backed-up to
~/.claude/backups/aa-ma-forge-<ts>/ on install.

See docs/adr/0008-sole-dev-merge-pr-workflow.md for rationale, alternatives,
and rollback paths. Set AA_MA_SUPPRESS_MIGRATION_BANNER=1 to silence.
BANNER
        : > "$SENTINEL"
    fi
fi
# === stage-banner (END) ===
```

---

## Workflow stages

The command runs sequentially through stages **A → G**. Each stage is
self-contained (one reason to change, per SOC). Implementation lives in
named inline bash blocks below; this section is the contract surface.

### Stage A — Pre-flight checks

Captures `ORIGINAL_BRANCH` and `BASE_REF`; aborts with one of four exact
messages on failure; otherwise prints `Pre-flight OK`.

| Branch condition | ABORT string |
|------------------|--------------|
| On `main`/`master` | `ABORT: Cannot run /sole-dev-merge from $ORIGINAL_BRANCH branch` |
| Uncommitted changes | `ABORT: Uncommitted changes detected (commit or stash first)` |
| No git remote | `ABORT: No git remote configured (need github.com or gitlab.com remote)` |
| No commits ahead of base | `ABORT: No commits ahead of $DEFAULT_BRANCH (nothing to merge)` |

ABORT exits non-zero (rc=1). `Pre-flight OK` exits zero and exports
`ORIGINAL_BRANCH`, `BASE_REF`, `DEFAULT_BRANCH` for downstream stages.

```bash
# === stage-a-preflight (BEGIN) ===
set -euo pipefail

# 1. Capture original branch
ORIGINAL_BRANCH=$(git branch --show-current 2>/dev/null || echo "")

# 2. Refuse if on default branch (main/master)
if [[ "$ORIGINAL_BRANCH" == "main" || "$ORIGINAL_BRANCH" == "master" ]]; then
    echo "ABORT: Cannot run /sole-dev-merge from $ORIGINAL_BRANCH branch"
    exit 1
fi

# 3. Refuse on uncommitted changes (modified or untracked)
if [[ -n "$(git status --porcelain)" ]]; then
    echo "ABORT: Uncommitted changes detected (commit or stash first)"
    exit 1
fi

# 4. Require at least one remote configured
if [[ -z "$(git remote)" ]]; then
    echo "ABORT: No git remote configured (need github.com or gitlab.com remote)"
    exit 1
fi

# 5. Resolve default branch (prefer origin/HEAD, fall back to "main")
DEFAULT_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null \
    | sed 's@^refs/remotes/origin/@@' || true)
DEFAULT_BRANCH="${DEFAULT_BRANCH:-main}"

# Resolve a usable base ref (prefer local, fall back to remote tracking)
if git rev-parse --verify -q "$DEFAULT_BRANCH" >/dev/null; then
    BASE_REF="$DEFAULT_BRANCH"
elif git rev-parse --verify -q "origin/$DEFAULT_BRANCH" >/dev/null; then
    BASE_REF="origin/$DEFAULT_BRANCH"
else
    echo "ABORT: Cannot resolve $DEFAULT_BRANCH or origin/$DEFAULT_BRANCH"
    exit 1
fi

# 6. Require at least one commit ahead of base
AHEAD=$(git rev-list --count "${BASE_REF}..HEAD")
if [[ "$AHEAD" -eq 0 ]]; then
    echo "ABORT: No commits ahead of $DEFAULT_BRANCH (nothing to merge)"
    exit 1
fi

export ORIGINAL_BRANCH BASE_REF DEFAULT_BRANCH
echo "Pre-flight OK (branch=$ORIGINAL_BRANCH, base=$BASE_REF, ahead=$AHEAD)"
# === stage-a-preflight (END) ===
```

### Stage B — Scope-aware CI checks (L-007 guard)

Computes `CHANGED_FILES = git diff --name-only ${BASE_REF}...HEAD` (triple-dot
symmetric difference — only files this branch introduced); splits into
`CHANGED_PY` / `CHANGED_SH`. Runs `ruff format` / `ruff check --fix` against
in-scope `*.py` only (NOT whole-tree — that's the L-007 fix). Best-effort
`mypy` / `pytest -m "not perf and not slow"` / `pre-commit run --files` only
when their config artefacts exist. After all mutations, the **L-007 guard**
reverts any dirty file NOT in `$CHANGED_FILES` via `git checkout --`.

```bash
# === stage-b-scope (BEGIN) ===
set -euo pipefail

# Stage A exports BASE_REF; defensive fallback in case Stage B is run alone
BASE_REF="${BASE_REF:-main}"

# Triple-dot: files this branch introduced (NOT files that drifted on base since)
CHANGED_FILES=$(git diff --name-only "${BASE_REF}...HEAD" || true)
CHANGED_PY=$(echo "$CHANGED_FILES" | grep '\.py$' || true)
CHANGED_SH=$(echo "$CHANGED_FILES" | grep '\.sh$' || true)

N_TOTAL=$(echo "$CHANGED_FILES" | grep -c . || true)
N_PY=$(echo "$CHANGED_PY" | grep -c . || true)
N_SH=$(echo "$CHANGED_SH" | grep -c . || true)
echo "Stage B scope: $N_TOTAL file(s) — $N_PY Python, $N_SH shell"

# 1. Format Python (in-scope only)
if [[ -n "$CHANGED_PY" ]]; then
    while IFS= read -r f; do
        if [[ -f "$f" ]]; then
            ruff format "$f" || true
        fi
    done <<< "$CHANGED_PY"
fi

# 2. Lint with fix (in-scope only). Tolerant — unfixable errors surface in Stage D.
if [[ -n "$CHANGED_PY" ]]; then
    while IFS= read -r f; do
        if [[ -f "$f" ]]; then
            ruff check --fix "$f" || true
        fi
    done <<< "$CHANGED_PY"
fi

# 3. Typecheck (best-effort, only when [tool.mypy] is configured)
if [[ -f pyproject.toml ]] && grep -q '^\[tool\.mypy\]' pyproject.toml; then
    uv run mypy src/ 2>&1 || true
fi

# 4. Pytest fast tier (best-effort, only when tests/ exists)
if [[ -d tests ]]; then
    uv run pytest -m "not perf and not slow" || true
fi

# 5. Pre-commit (only when configured; in-scope files only)
if [[ -f .pre-commit-config.yaml && -n "$CHANGED_FILES" ]]; then
    # shellcheck disable=SC2086  # Intentional word-splitting for multi-file arg
    pre-commit run --files $CHANGED_FILES || true
fi

# 6. L-007 GUARD — revert any out-of-scope mutations introduced by 1-5
declare -A IN_SCOPE=()
while IFS= read -r f; do
    [[ -n "$f" ]] && IN_SCOPE["$f"]=1
done <<< "$CHANGED_FILES"

REVERTED=()
while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    # porcelain row: "XY path" where XY is 2-char status + space; strip the 3-char prefix
    path="${line:3}"
    if [[ -z "${IN_SCOPE[$path]:-}" ]]; then
        if git checkout -- "$path" 2>/dev/null; then
            REVERTED+=("$path")
        fi
    fi
done < <(git status --porcelain)

if [[ ${#REVERTED[@]} -gt 0 ]]; then
    echo "L-007 guard: reverted ${#REVERTED[@]} out-of-scope file(s): ${REVERTED[*]}"
else
    echo "L-007 guard: clean (no out-of-scope drift)"
fi

echo "Stage B OK"
# === stage-b-scope (END) ===
```

### Stage B-commit — Auto-commit in-scope fixes

If Stage B mutated in-scope files, commits as
`chore(scope): pre-PR auto-fixes`. The `aa-ma-commit-signature.sh` hook
appends the active-plan footer (`[AA-MA Plan] …`) or `[ad-hoc]` automatically.
If `git status` is clean, this stage is a no-op.

```bash
# === stage-b-commit (BEGIN) ===
set -euo pipefail

# Source the shared AA-MA footer helper. The aa-ma-commit-signature.sh
# PreToolUse hook validates the LITERAL `-m` argument, so we MUST emit
# the footer ourselves — the hook cannot append it retroactively.
# Single source-of-truth: claude-code/hooks/lib/aa-ma-footer.sh.
_HELPER_PATH="${AA_MA_FOOTER_HELPER:-$(git rev-parse --show-toplevel)/claude-code/hooks/lib/aa-ma-footer.sh}"
source "$_HELPER_PATH"

# Post-Stage-B + L-007 guard: anything dirty here is in-scope and was
# mutated by ruff/pre-commit on files the branch actually owns.
if [[ -z "$(git status --porcelain)" ]]; then
    echo "Stage B-commit: nothing to commit (Stage B made no in-scope changes)"
else
    git add -A
    FOOTER=$(emit_aa_ma_footer)
    git commit -m "chore(scope): pre-PR auto-fixes${FOOTER}"
    echo "Stage B-commit: committed in-scope auto-fixes ($(git rev-parse --short HEAD))"
fi
# === stage-b-commit (END) ===
```

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
if [[ -n "${CHANGED_PY:-}" ]]; then
    # shellcheck disable=SC2086  # intentional word-splitting for multi-file arg
    bandit -f json $CHANGED_PY > "$BANDIT_OUT" 2>/dev/null || true
    if [[ -s "$BANDIT_OUT" ]]; then
        # Severity mapping loaded from $BANDIT_SEV_JSON (canonical above).
        python3 - "$BANDIT_OUT" >> "$FINDINGS" <<'PY' || true
import json, os, sys
try:
    with open(sys.argv[1]) as f:
        data = json.load(f)
except (json.JSONDecodeError, FileNotFoundError):
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
if [[ -n "${CHANGED_SH:-}" ]]; then
    # shellcheck disable=SC2086  # intentional word-splitting for multi-file arg
    shellcheck -f json $CHANGED_SH > "$SHELLCHECK_OUT" 2>/dev/null || true
    if [[ -s "$SHELLCHECK_OUT" ]]; then
        # Severity mapping loaded from $SHELLCHECK_SEV_JSON (canonical above).
        python3 - "$SHELLCHECK_OUT" >> "$FINDINGS" <<'PY' || true
import json, os, sys
try:
    with open(sys.argv[1]) as f:
        data = json.load(f)
except (json.JSONDecodeError, FileNotFoundError):
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

### Stage D — Findings triage

Consumes `/tmp/sole-dev-merge-findings-${SLUG}.md` produced by Stage C and
routes findings by severity:

- **CRITICAL** — deterministic auto-fix for known patterns (Bandit B602
  → `s/shell=True/shell=False/`); other CRITICALs (ShellCheck, agent-emitted)
  are tagged for user review. Auto-fix lands as a single commit:
  `fix(review): apply CRITICAL bandit findings`.
- **HIGH / MEDIUM** — Claude executor invokes `AskUserQuestion` panels
  (4-per-call max) with Apply / Dispute / Defer options. Bash logs only.
- **LOW** — appended to `/tmp/sole-dev-merge-reviewer-notes-${SLUG}.md`
  for inclusion in the PR/MR body's "Reviewer notes" section (advisory).

```bash
# === stage-d-triage (BEGIN) ===
set -euo pipefail

# Single source-of-truth for the AA-MA commit footer (shared with Stage B-commit).
_HELPER_PATH="${AA_MA_FOOTER_HELPER:-$(git rev-parse --show-toplevel)/claude-code/hooks/lib/aa-ma-footer.sh}"
source "$_HELPER_PATH"

SLUG="${SLUG:-$(date +%s)}"
FINDINGS="/tmp/sole-dev-merge-findings-${SLUG}.md"
BANDIT_OUT="/tmp/sole-dev-merge-bandit-${SLUG}.json"

if [[ ! -f "$FINDINGS" ]]; then
    echo "Stage D: no findings file at $FINDINGS — nothing to triage"
    exit 0
fi

N_CRITICAL=$(grep -cE '^\[CRITICAL\]' "$FINDINGS" || true)
N_HIGH=$(grep -cE '^\[HIGH\]' "$FINDINGS" || true)
N_MEDIUM=$(grep -cE '^\[MEDIUM\]' "$FINDINGS" || true)
N_LOW=$(grep -cE '^\[LOW\]' "$FINDINGS" || true)

echo "Stage D triage: $N_CRITICAL CRITICAL, $N_HIGH HIGH, $N_MEDIUM MEDIUM, $N_LOW LOW"

AUTO_FIXED=0

# === B602 AUTO-FIX (driven from $BANDIT_OUT JSON — trusted provenance) ===
# §6.8 audit fix (security HIGH 1-3 + future-proofing HIGH #4):
# Auto-fix the EXACT line Bandit reports, with test_id equality (not
# substring). Source of truth = Bandit's structured JSON output, NOT the
# stringified findings.md (which mixes agent-influenced text).
if [[ -s "$BANDIT_OUT" ]]; then
    while IFS=$'\t' read -r FILE LINE; do
        [[ -z "$FILE" || -z "$LINE" ]] && continue
        if [[ -f "$FILE" && "$LINE" =~ ^[0-9]+$ && "$LINE" -gt 0 ]]; then
            # Line-scoped sed: rewrite ONLY the exact line Bandit flagged.
            # Docstrings, comments, and unrelated occurrences SURVIVE.
            sed -i "${LINE}s/shell=True/shell=False/" "$FILE"
            echo "Stage D auto-fix: B602 at $FILE:$LINE"
            AUTO_FIXED=$((AUTO_FIXED + 1))
        fi
    done < <(python3 - "$BANDIT_OUT" <<'PY'
import json, sys
try:
    with open(sys.argv[1]) as f:
        data = json.load(f)
except (json.JSONDecodeError, FileNotFoundError):
    sys.exit(0)
for r in data.get("results", []):
    # Equality match on test_id + severity — no substring matching
    if r.get("test_id") == "B602" and r.get("issue_severity") == "HIGH":
        print(f"{r.get('filename', '')}\t{r.get('line_number', 0)}")
PY
    )
fi

# Tag non-auto-fixable CRITICALs (ShellCheck + agent-emitted) for user review.
# B602 lines are excluded — we've handled them via the JSON-driven path above.
TAGGED_FOR_REVIEW=()
if [[ "$N_CRITICAL" -gt 0 ]]; then
    while IFS= read -r line; do
        [[ "$line" == *"B602"* ]] && continue  # already auto-fixed
        TAGGED_FOR_REVIEW+=("$line")
    done < <(grep -E '^\[CRITICAL\]' "$FINDINGS")
fi

if [[ "${#TAGGED_FOR_REVIEW[@]}" -gt 0 ]]; then
    echo "Stage D: ${#TAGGED_FOR_REVIEW[@]} CRITICAL finding(s) tagged for user review (not auto-fixed):"
    printf '  %s\n' "${TAGGED_FOR_REVIEW[@]}"
fi

# LOW → reviewer notes (advisory; surfaced in PR/MR body by Stage E3)
if [[ "$N_LOW" -gt 0 ]]; then
    REVIEWER_NOTES="/tmp/sole-dev-merge-reviewer-notes-${SLUG}.md"
    grep -E '^\[LOW\]' "$FINDINGS" > "$REVIEWER_NOTES"
    echo "Stage D: $N_LOW LOW finding(s) → $REVIEWER_NOTES (advisory)"
fi

# Commit auto-fixes if any (footer from shared helper for drift-resistance)
if [[ "$AUTO_FIXED" -gt 0 ]]; then
    FOOTER=$(emit_aa_ma_footer)
    git add -A
    git commit -m "fix(review): apply CRITICAL bandit findings${FOOTER}"
    echo "Stage D: committed $AUTO_FIXED auto-fix(es) ($(git rev-parse --short HEAD))"
fi

# HIGH/MEDIUM — Claude executor handles via AskUserQuestion. Bash logs only.
if [[ "$N_HIGH" -gt 0 || "$N_MEDIUM" -gt 0 ]]; then
    echo "Stage D: $N_HIGH HIGH + $N_MEDIUM MEDIUM finding(s) require AskUserQuestion triage (HITL)"
fi
# === stage-d-triage (END) ===
```

### Stage E — Remote detection, choice, auth, AI body generation

Execution order is **E1 → E2 → E0 → E3** so that auth pre-flight (E0) targets
only the chosen remote (set by E2). The prose enumerates them by sub-stage
name; the bash blocks below follow the execution order.

- **E1** (remote detection) — parses `git remote -v`, classifies each remote
  as `github` / `gitlab` / `other`, exports `n_github` / `n_gitlab` / `n_other`.
- **E2** (remote choice) — one remote → use it; both → emit
  `DUAL_REMOTE_PROMPT` signal + JSON for the Claude executor to dispatch
  `AskUserQuestion` with GitLab as default; neither github+gitlab → abort.
- **E0** (auth pre-flight) — `gh auth status` / `glab auth status` for the
  chosen remote; `STATUS: AUTH_REQUIRED — run <cli> auth login` on failure
  (clean exit 0 — auth recovery is a user action, not a script failure).
- **E3** (AI body) — DETERMINISTIC fallback body generator. Sections:
  `## Summary`, `## Changes by area`, `## Test plan`, `## Reviewer notes`.
  Appends `Plan context: <plan-dir>` footer when `$AA_MA_PLAN_DIR` is set.
  Closing footer: `<!-- Generated by /sole-dev-merge -->` for traceability.
  **Optional LLM enrichment:** the Claude executor MAY dispatch a Haiku-class
  `Agent` to rewrite the Summary section with a 1–3 sentence narrative
  derived from `git diff $BASE_REF...HEAD --stat` + commit subjects, then
  re-run E3 with the enriched Summary inlined. The deterministic fallback
  satisfies AC §4.3.3 standalone.

```bash
# === stage-e1-remote (BEGIN) ===
set -euo pipefail

n_github=0
n_gitlab=0
n_other=0

# git remote -v emits two lines per remote (fetch + push); dedupe by counting
# only (fetch) rows so a single remote yields count 1, not 2.
while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    [[ "$line" == *"(push)" ]] && continue
    # Line shape: "<name>\t<url> (fetch)" — strip prefix and suffix.
    url="${line#*$'\t'}"
    url="${url% (fetch)}"
    case "$url" in
        *github.com*)  n_github=$((n_github + 1)) ;;
        *gitlab.com*)  n_gitlab=$((n_gitlab + 1)) ;;
        *)             n_other=$((n_other + 1))  ;;
    esac
done < <(git remote -v)

export n_github n_gitlab n_other
echo "Stage E1 remote: n_github=$n_github n_gitlab=$n_gitlab n_other=$n_other"
# === stage-e1-remote (END) ===
```

```bash
# === stage-e2-choice (BEGIN) ===
set -euo pipefail

# Inherits n_github / n_gitlab from Stage E1; defensive default when E2 is
# run standalone (e.g. in a unit test).
n_github="${n_github:-0}"
n_gitlab="${n_gitlab:-0}"
AUQ_LOG="${AUQ_LOG:-/tmp/sole-dev-merge-auq.json}"

if (( n_github == 0 && n_gitlab == 0 )); then
    echo "ABORT: only github.com and gitlab.com remotes supported"
    exit 1
fi

if (( n_github >= 1 && n_gitlab >= 1 )); then
    # Dual remote — write AUQ-bridge JSON for the Claude executor to dispatch
    # the real AskUserQuestion. GitLab is the default per Biorelate convention
    # (see plan §3.2 + bk_<project>.md / bk_<project>.md
    # / bk_<project>.md).
    cat > "$AUQ_LOG" <<'JSON'
{"call":1,"n_options":2,"labels":["GitLab (recommended for Biorelate projects)","GitHub"],"default":"GitLab (recommended for Biorelate projects)"}
JSON
    echo "DUAL_REMOTE_PROMPT default=GitLab labels=GitLab,GitHub"
    # Until the Claude executor updates REMOTE_CHOICE post-AUQ, default to
    # gitlab (matches the default option). Tests that don't simulate the
    # AUQ dispatch read this as the chosen remote.
    REMOTE_CHOICE="${REMOTE_CHOICE:-gitlab}"
elif (( n_github >= 1 )); then
    REMOTE_CHOICE=github
    echo "REMOTE_CHOICE=github"
else
    REMOTE_CHOICE=gitlab
    echo "REMOTE_CHOICE=gitlab"
fi

export REMOTE_CHOICE
# === stage-e2-choice (END) ===
```

```bash
# === stage-e0-auth (BEGIN) ===
set -euo pipefail

# Stage E2 sets REMOTE_CHOICE; defensive default to github so the auth check
# fires somewhere even if E0 runs standalone.
REMOTE_CHOICE="${REMOTE_CHOICE:-github}"

if [[ "$REMOTE_CHOICE" == "github" ]]; then
    if ! gh auth status >/dev/null 2>&1; then
        echo "STATUS: AUTH_REQUIRED — run gh auth login"
        exit 0
    fi
elif [[ "$REMOTE_CHOICE" == "gitlab" ]]; then
    if ! glab auth status >/dev/null 2>&1; then
        echo "STATUS: AUTH_REQUIRED — run glab auth login"
        exit 0
    fi
fi
# === stage-e0-auth (END) ===
```

```bash
# === stage-e3-body (BEGIN) ===
set -euo pipefail

BASE_REF="${BASE_REF:-main}"
BODY_OUT="${BODY_OUT:-/tmp/sole-dev-merge-body.md}"

BRANCH=$(git branch --show-current 2>/dev/null || echo "feature")
N_COMMITS=$(git rev-list --count "${BASE_REF}..HEAD" 2>/dev/null || echo 0)

{
    echo "## Summary"
    echo
    echo "Branch \`$BRANCH\` proposes $N_COMMITS commit(s) ahead of \`$BASE_REF\`."
    echo
    echo "## Changes by area"
    echo
    git log "${BASE_REF}..HEAD" --format="- %s" 2>/dev/null || echo "- (no commits)"
    echo
    echo "## Test plan"
    echo
    echo "- [ ] CI checks pass"
    echo "- [ ] Manual smoke test of changed paths"
    echo
    echo "## Reviewer notes"
    echo
    # Stage D writes LOW findings to a slug-namespaced path; Stage E3 reads
    # the SAME path. SLUG must be exported by Stage C in production; tests
    # set SLUG via env or fall through to the NOSLUG sentinel (file absent
    # → "(none)" branch — clean fallback).
    # §6.8 CRITICAL-1 fix: previously read unslugged path, breaking the D→E3
    # contract (LOW findings never reached PR body). See impl-review.md.
    REVIEWER_NOTES_FILE="${REVIEWER_NOTES_FILE:-/tmp/sole-dev-merge-reviewer-notes-${SLUG:-NOSLUG}.md}"
    if [[ -s "$REVIEWER_NOTES_FILE" ]]; then
        cat "$REVIEWER_NOTES_FILE"
    else
        echo "(none)"
    fi
    echo
    if [[ -n "${AA_MA_PLAN_DIR:-}" ]]; then
        # §6.8 HIGH-1 fix: strip control chars (newlines/CRs/tabs) that an
        # attacker controlling AA_MA_PLAN_DIR could use to inject Markdown
        # into the PR body. tr is single-purpose; safer than parameter
        # expansion against multi-byte sequences.
        SAFE_PLAN_DIR=$(printf '%s' "$AA_MA_PLAN_DIR" | tr -d '\n\r\t\b\f')
        echo "Plan context: $SAFE_PLAN_DIR"
        echo
    fi
    echo "<!-- Generated by /sole-dev-merge -->"
} > "$BODY_OUT"

echo "Stage E3 body: wrote $(wc -l < "$BODY_OUT") line(s) to $BODY_OUT"
# === stage-e3-body (END) ===
```

### Stage F — Push + PR/MR creation (idempotent)

`git push -u origin HEAD`, then check for an existing PR/MR and either update
the body or create fresh. Title is derived from the topmost Conventional
Commit subject (truncated to 70 chars) when not explicitly provided.

- **GitHub** — `gh pr view --json url` detects existing PR; reuse via
  `gh pr edit --body-file "$BODY"` or create via
  `gh pr create --title "$TITLE" --body-file "$BODY"`.
- **GitLab** — `glab mr view` detects existing MR; reuse via
  `glab mr update --description "$(cat $BODY)"` or create via
  `glab mr create --title "$TITLE" --description "$(cat $BODY)"` (NOT
  `--description-file` — that flag is fabricated; see reference.md "WRONG
  SYNTAX TO NEVER USE").

```bash
# === stage-f-push (BEGIN) ===
set -euo pipefail

REMOTE_CHOICE="${REMOTE_CHOICE:-github}"
PR_BODY_FILE="${PR_BODY_FILE:-/tmp/sole-dev-merge-body.md}"

# §6.8 MED-2 fix: guard against missing/empty body file. If Stage E3 was
# skipped or its output is empty, fail loudly rather than push a blank PR.
if [[ ! -s "$PR_BODY_FILE" ]]; then
    echo "ABORT: Stage F requires non-empty body file at $PR_BODY_FILE — run Stage E3 first"
    exit 1
fi

# Title — derive from topmost commit subject if not pre-set; truncate to 70 chars.
if [[ -z "${PR_TITLE:-}" ]]; then
    PR_TITLE=$(git log -1 --format=%s 2>/dev/null || echo "(no title)")
fi
PR_TITLE="${PR_TITLE:0:70}"
echo "PR_TITLE=$PR_TITLE"

# Idempotent push — first invocation creates the remote-tracking ref;
# subsequent invocations fast-forward.
git push -u origin HEAD

PR_NUM=0
PR_URL=""
MR_IID=0

if [[ "$REMOTE_CHOICE" == "github" ]]; then
    if gh pr view --json url >/dev/null 2>&1; then
        echo "PR_OP=edit"
        gh pr edit --body-file "$PR_BODY_FILE"
    else
        echo "PR_OP=create"
        gh pr create --title "$PR_TITLE" --body-file "$PR_BODY_FILE"
    fi
    # §6.8 M4 CRITICAL-1 fix: extract PR identifiers for Stage G consumption.
    # Real gh CLI supports `--jq` filter on the json output; tests' gh stub
    # honours these filters explicitly.
    PR_URL=$(gh pr view --json url    --jq '.url'    2>/dev/null || echo "")
    PR_NUM=$(gh pr view --json number --jq '.number' 2>/dev/null || echo "0")
elif [[ "$REMOTE_CHOICE" == "gitlab" ]]; then
    if glab mr view >/dev/null 2>&1; then
        echo "MR_OP=update"
        glab mr update --description "$(cat "$PR_BODY_FILE")"
    else
        echo "MR_OP=create"
        glab mr create --title "$PR_TITLE" --description "$(cat "$PR_BODY_FILE")"
    fi
    # §6.8 M4 CRITICAL-1 fix: GitLab MR identifiers for Stage G.
    PR_URL=$(glab mr view --jq '.web_url' 2>/dev/null || echo "")
    MR_IID=$(glab mr view --jq '.iid'     2>/dev/null || echo "0")
    # Stage G2/G3 also reads PR_NUM for cross-remote symmetry; alias to MR_IID
    # on the GitLab branch so downstream stages can use one variable name.
    PR_NUM="$MR_IID"
fi

echo "PR_NUM=$PR_NUM"
echo "PR_URL=$PR_URL"
[[ "$REMOTE_CHOICE" == "gitlab" ]] && echo "MR_IID=$MR_IID"

export PR_TITLE PR_NUM PR_URL MR_IID
# === stage-f-push (END) ===
```

### Stage G — CI poll + auto-merge + cleanup

Execution order: **G1 → G2 → G3 → G4**. G1 picks the merge strategy up-front
so G3 doesn't hit a "rebase merging is disabled" runtime error. G2 polls with
a 15-minute timeout (overridable via `CI_POLL_TIMEOUT` for tests). G3 dispatches
the merge on green CI or emits a clean recovery `STATUS: …` line on timeout /
failure. G4 runs only on a successful merge.

- **G1** (branch-protection pre-check) — `gh api repos/{owner}/{repo} --jq
  .allow_rebase_merge` / `glab api /projects/:id --jq .merge_method`. Sets
  `MERGE_STRATEGY=rebase|merge` based on the response.
- **G2** (CI poll) — divergent paths:
  - GitHub: `timeout 900s gh pr checks <num> --watch --interval 30 --fail-fast`.
    Translates `RC=124` → `STATUS: CI_TIMEOUT` + clean exit 0; `RC=0` → green;
    other → failed. Sets `CI_STATE`.
  - GitLab: `glab api /projects/:id/merge_requests/<iid>` polled every 30s in
    a bash `while` loop with `(( $(date +%s) - start < 900 ))` guard. Parses
    `.pipeline.status`. (NOT `glab ci status` — TTY UI, no scriptable exit
    codes per reference.md "WRONG SYNTAX TO NEVER USE".)
- **G3** (auto-merge + error paths, plan §4.3 + §4.4) — branches on `CI_STATE`:
  - `green` → `gh pr merge <num> --$MERGE_STRATEGY --delete-branch` (one call).
  - `timeout` → emit `STATUS: CI_TIMEOUT — see <URL>` + recovery hint
    (`gh pr merge --auto --rebase`); skip merge.
  - `failed` → emit `STATUS: CI_FAILED — see <URL>` + diagnostic hint
    (`gh pr checks <num>`); skip merge.
- **G4** (cleanup, plan §4.5) — runs only on successful merge:
  `git checkout main` → `git pull --ff-only origin main` → `git fetch --prune`.
  Prints final summary: branch, commits merged, merge SHA, PR/MR URL.

```bash
# === stage-g1-protect (BEGIN) ===
set -euo pipefail

# Inherits REMOTE_CHOICE from Stage E2. Defensive default to github.
REMOTE_CHOICE="${REMOTE_CHOICE:-github}"
MERGE_STRATEGY=rebase  # default; falls back to merge if rebase disabled

if [[ "$REMOTE_CHOICE" == "github" ]]; then
    # gh api echoes "true" or "false" for the boolean jq filter.
    ALLOW_REBASE=$(gh api "repos/{owner}/{repo}" --jq '.allow_rebase_merge' 2>/dev/null || echo "true")
    if [[ "$ALLOW_REBASE" != "true" ]]; then
        MERGE_STRATEGY=merge
        echo "Stage G1: rebase-merge disabled on remote — fallback strategy=merge"
    fi
elif [[ "$REMOTE_CHOICE" == "gitlab" ]]; then
    # glab api echoes the project's merge_method string.
    MERGE_METHOD=$(glab api "/projects/:id" --jq '.merge_method' 2>/dev/null || echo "rebase_merge")
    if [[ "$MERGE_METHOD" != "rebase_merge" ]]; then
        MERGE_STRATEGY=merge
        echo "Stage G1: GitLab merge_method=$MERGE_METHOD — fallback strategy=merge"
    fi
fi

export MERGE_STRATEGY
echo "MERGE_STRATEGY=$MERGE_STRATEGY"
# === stage-g1-protect (END) ===
```

```bash
# === stage-g2-poll (BEGIN) ===
set -euo pipefail

# Inputs from Stage F: PR_NUM, PR_URL, REMOTE_CHOICE.
REMOTE_CHOICE="${REMOTE_CHOICE:-github}"
PR_NUM="${PR_NUM:-0}"
PR_URL="${PR_URL:-}"
# 15 minutes hard cap by default; tests override to small values for speed.
CI_POLL_TIMEOUT="${CI_POLL_TIMEOUT:-900s}"

CI_STATE=unknown

if [[ "$REMOTE_CHOICE" == "github" ]]; then
    RC=0
    # `--watch` blocks until checks complete; `timeout` enforces the cap.
    timeout "$CI_POLL_TIMEOUT" gh pr checks "$PR_NUM" \
        --watch --interval 30 --fail-fast || RC=$?
    case "$RC" in
        0)   CI_STATE=green ;;
        124) CI_STATE=timeout
             echo "STATUS: CI_TIMEOUT — see $PR_URL"
             echo "  recovery: gh pr merge $PR_NUM --auto --rebase"
             ;;
        *)   CI_STATE=failed
             echo "STATUS: CI_FAILED — see $PR_URL"
             echo "  diagnostic: gh pr checks $PR_NUM"
             ;;
    esac
elif [[ "$REMOTE_CHOICE" == "gitlab" ]]; then
    # JSON polling (NOT `glab ci status` — TTY UI without scriptable exit codes).
    MR_IID="${MR_IID:-$PR_NUM}"
    START=$(date +%s)
    # §6.8 M4 HIGH-5 fix: parse `${CI_POLL_TIMEOUT%s}` so the env-override the
    # GitHub branch honours also applies here. Falls back to 900 when unset
    # or non-numeric after stripping the 's' suffix.
    TIMEOUT_S="${CI_POLL_TIMEOUT%s}"
    [[ "$TIMEOUT_S" =~ ^[0-9]+$ ]] || TIMEOUT_S=900
    CI_POLL_INTERVAL="${CI_POLL_INTERVAL:-30}"
    while true; do
        STATUS=$(GLAB_API_MODE=pipeline_status glab api \
            "/projects/:id/merge_requests/${MR_IID}" --jq '.pipeline.status' 2>/dev/null \
            || echo "running")
        case "$STATUS" in
            success)
                CI_STATE=green; break ;;
            failed|canceled)
                CI_STATE=failed
                echo "STATUS: CI_FAILED — see $PR_URL"
                echo "  diagnostic: glab ci view $MR_IID"
                break ;;
            manual|skipped)
                # §6.8 M4 HIGH-2 fix: GitLab pipeline-status terminal states
                # OTHER than success/failed — `manual` (waiting on operator)
                # and `skipped` (pipeline intentionally bypassed). Without
                # this arm, both fall through to "keep polling" and burn the
                # full 15-min CI_POLL_TIMEOUT (the M3 §6.8 future-proofing
                # auditor flagged this enum-coverage gap).
                CI_STATE=blocked
                echo "STATUS: CI_BLOCKED — pipeline status=$STATUS — see $PR_URL"
                echo "  diagnostic: glab ci view $MR_IID"
                break ;;
        esac
        if (( $(date +%s) - START >= TIMEOUT_S )); then
            CI_STATE=timeout
            echo "STATUS: CI_TIMEOUT — see $PR_URL"
            echo "  recovery: glab mr merge $MR_IID --when-pipeline-succeeds"
            break
        fi
        sleep "$CI_POLL_INTERVAL"
    done
fi

export CI_STATE
echo "CI_STATE=$CI_STATE"
# === stage-g2-poll (END) ===
```

```bash
# === stage-g3-merge (BEGIN) ===
set -euo pipefail

# Inputs from Stage F + G1 + G2: PR_NUM, PR_URL, REMOTE_CHOICE,
# MERGE_STRATEGY (rebase|merge), CI_STATE (green|timeout|failed).
REMOTE_CHOICE="${REMOTE_CHOICE:-github}"
PR_NUM="${PR_NUM:-0}"
PR_URL="${PR_URL:-}"
MERGE_STRATEGY="${MERGE_STRATEGY:-rebase}"
CI_STATE="${CI_STATE:-unknown}"

case "$CI_STATE" in
    green)
        if [[ "$REMOTE_CHOICE" == "github" ]]; then
            gh pr merge "$PR_NUM" --"$MERGE_STRATEGY" --delete-branch
        elif [[ "$REMOTE_CHOICE" == "gitlab" ]]; then
            MR_IID="${MR_IID:-$PR_NUM}"
            if [[ "$MERGE_STRATEGY" == "rebase" ]]; then
                glab mr merge "$MR_IID" --rebase --remove-source-branch --yes
            else
                glab mr merge "$MR_IID" --remove-source-branch --yes
            fi
        fi
        export MERGE_DISPATCHED=1
        echo "Stage G3: merged $PR_NUM (strategy=$MERGE_STRATEGY)"
        ;;
    timeout)
        # §6.8 M4 HIGH-1 fix: remote-aware recovery hints. G2 already emitted
        # the correct STATUS line; G3's defensive re-emission must NOT
        # hardcode `gh pr merge` when the operator chose GitLab.
        echo "STATUS: CI_TIMEOUT — see $PR_URL"
        if [[ "$REMOTE_CHOICE" == "gitlab" ]]; then
            echo "  recovery: glab mr merge ${MR_IID:-$PR_NUM} --when-pipeline-succeeds"
        else
            echo "  recovery: gh pr merge $PR_NUM --auto --rebase"
        fi
        export MERGE_DISPATCHED=0
        ;;
    failed)
        # §6.8 M4 HIGH-1 fix (failed branch): remote-aware diagnostic hint.
        echo "STATUS: CI_FAILED — see $PR_URL"
        if [[ "$REMOTE_CHOICE" == "gitlab" ]]; then
            echo "  diagnostic: glab ci view ${MR_IID:-$PR_NUM}"
        else
            echo "  diagnostic: gh pr checks $PR_NUM"
        fi
        export MERGE_DISPATCHED=0
        ;;
    blocked)
        # §6.8 M4 HIGH-2 fix: G2's `manual|skipped` GitLab enum hand-off.
        # No merge; G2 already emitted the STATUS:CI_BLOCKED line.
        export MERGE_DISPATCHED=0
        ;;
    *)
        # §6.8 M4 MED-1 fix: emit a STATUS line for the unknown catchall so
        # downstream tooling parsing for `STATUS:` doesn't miss this terminal
        # state. REMOTE_CHOICE included for diagnostic context.
        echo "STATUS: CI_UNKNOWN — CI_STATE='$CI_STATE' REMOTE_CHOICE='$REMOTE_CHOICE'"
        export MERGE_DISPATCHED=0
        ;;
esac
# === stage-g3-merge (END) ===
```

```bash
# === stage-g4-cleanup (BEGIN) ===
set -euo pipefail

# Runs only on successful merge (gated by caller checking MERGE_DISPATCHED=1).
# Inputs: ORIGINAL_BRANCH (from Stage A), PR_URL (from Stage F).
ORIGINAL_BRANCH="${ORIGINAL_BRANCH:-feature}"
PR_URL="${PR_URL:-}"
DEFAULT_BRANCH="${DEFAULT_BRANCH:-main}"

# 1. Switch to default branch (feature branch was deleted server-side by
#    --delete-branch in G3; local ref may still exist but switching is safe).
git checkout -q "$DEFAULT_BRANCH"

# 2. Fast-forward local default to the server tip.
git pull -q --ff-only origin "$DEFAULT_BRANCH"

# 3. Prune local remote-tracking refs for branches deleted server-side.
git fetch -q --prune

# 4. Best-effort local cleanup: delete the local feature branch ref if it
#    still exists (server-side ref is already gone).
git branch -q -D "$ORIGINAL_BRANCH" 2>/dev/null || true

MERGE_SHA=$(git rev-parse --short "$DEFAULT_BRANCH")
echo "Stage G4: cleanup OK — on $DEFAULT_BRANCH at $MERGE_SHA"
echo "Final: branch=$ORIGINAL_BRANCH merged into $DEFAULT_BRANCH (sha=$MERGE_SHA)${PR_URL:+ — $PR_URL}"
echo "STATUS: OK"
# === stage-g4-cleanup (END) ===
```

---

## Exit-status contract

| Status            | Meaning                                              |
|-------------------|------------------------------------------------------|
| `STATUS: OK`      | Merged to main; branch deleted; main fast-forwarded (Stage G4). |
| `ABORT: …` (Stage A)   | Pre-flight failure: on-main, dirty tree, no remote, no commits ahead; exit non-zero. |
| `ABORT: only github.com and gitlab.com remotes supported` (Stage E2) | Remote configuration unsupportable (zero github + zero gitlab remotes — semantically a pre-flight gate); exit non-zero. |
| `ABORT: Stage F requires non-empty body file …` (Stage F) | Stage E3 skipped or body file empty; exit non-zero. |
| `STATUS: AUTH_REQUIRED` | Auth failed (Stage E0); exit 0 + recovery hint.  |
| `STATUS: CI_TIMEOUT — see <URL>` | CI poll cap exceeded (Stage G2); exit 0 + remote-aware auto-merge recovery hint. |
| `STATUS: CI_FAILED — see <URL>` | Required check failed (Stage G2); exit 0 + remote-aware diagnostic. |
| `STATUS: CI_BLOCKED — pipeline status=<state> — see <URL>` | GitLab pipeline state is `manual` or `skipped` (Stage G2); exit 0 + diagnostic. No merge dispatched. |
| `STATUS: CI_UNKNOWN — CI_STATE='<state>' REMOTE_CHOICE='<remote>'` | Stage G2 produced an unknown CI_STATE (Stage G3 catchall); exit 0. No merge dispatched. |

Non-zero exits are reserved for **pre-flight-class aborts** (Stages A, E2, F).
All runtime failures (auth, CI, merge race) exit cleanly with a `STATUS: …`
line so the workflow is safe to run unattended.

---

## Tests

Bats suite lives in `tests/commands/sole-dev-merge/`. CI runs them via
`.github/workflows/security.yml` (added in M5.6). See
`docs/adr/0008-sole-dev-merge-pr-workflow.md` for full test inventory.

---

_Stages A–G are placeholders. Logic lands across Steps 1.2 – 4.5 of the
[sole-dev-merge-pr-workflow](../../.claude/dev/active/sole-dev-merge-pr-workflow/sole-dev-merge-pr-workflow-plan.md) plan._
