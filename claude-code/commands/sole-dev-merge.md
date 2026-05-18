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

# Post-Stage-B + L-007 guard: anything dirty here is in-scope and was
# mutated by ruff/pre-commit on files the branch actually owns.
if [[ -z "$(git status --porcelain)" ]]; then
    echo "Stage B-commit: nothing to commit (Stage B made no in-scope changes)"
else
    git add -A
    # NOTE: AA-MA / [ad-hoc] footer is appended by the
    # aa-ma-commit-signature.sh PreToolUse hook (see
    # claude-code/hooks/lib/aa-ma-commit-signature.sh). Tests that invoke
    # this stage outside Claude Code must either set AA_MA_HOOKS_DISABLE=1
    # or append the footer themselves.
    git commit -m "chore(scope): pre-PR auto-fixes"
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
        # Severity mapping per reference.md §"Bandit JSON → unified scheme":
        # HIGH → [CRITICAL] ; MEDIUM → [HIGH] ; LOW → [MEDIUM]
        python3 - "$BANDIT_OUT" >> "$FINDINGS" <<'PY' || true
import json, sys
try:
    with open(sys.argv[1]) as f:
        data = json.load(f)
except (json.JSONDecodeError, FileNotFoundError):
    sys.exit(0)
sev_map = {"HIGH": "CRITICAL", "MEDIUM": "HIGH", "LOW": "MEDIUM"}
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
        # Severity mapping per reference.md §"ShellCheck JSON → unified scheme":
        # error → [CRITICAL] ; warning → [HIGH] ; info → [MEDIUM] ; style → [LOW]
        python3 - "$SHELLCHECK_OUT" >> "$FINDINGS" <<'PY' || true
import json, sys
try:
    with open(sys.argv[1]) as f:
        data = json.load(f)
except (json.JSONDecodeError, FileNotFoundError):
    sys.exit(0)
sev_map = {"error": "CRITICAL", "warning": "HIGH", "info": "MEDIUM", "style": "LOW"}
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

_Implementation pending Step 2.5._

Concatenates the four source files. **CRITICAL** auto-fix attempted for
deterministic Bandit/ShellCheck patterns only (agent-emitted CRITICALs are
tagged for user review). Re-runs Stage B fast tier after auto-fix to verify no
regression. **HIGH / MEDIUM** routed to `AskUserQuestion` (4-per-call max) with
options: Apply / Dispute / Defer. **LOW** appended to PR body's "Reviewer
notes" section (advisory only).

On parse failure (agent output does not match the contract), safe-default:
classify ALL findings as `[HIGH]` and log the parse failure to
`provenance.log` — no silent auto-fix without confirmation.

### Stage E — Remote detection, choice, AI body generation

_Implementation pending Steps 3.1 – 3.5._

- **E0** (auth pre-flight) — `gh auth status` / `glab auth status` for the
  candidate remotes; abort with `STATUS: AUTH_REQUIRED` on failure.
- **E1** (remote detection) — parses `git remote -v`, classifies each remote
  as `github` / `gitlab` / `other`, outputs counts.
- **E2** (remote choice) — one remote → use it; both → `AskUserQuestion` with
  GitLab as default; neither github+gitlab → abort.
- **E3** (AI body generation) — writes body to absolute path
  `/tmp/sole-dev-merge-body-<slug>.md`. Sections: `## Summary`,
  `## Changes by area`, `## Test plan`, `## Reviewer notes`. Appends
  `Plan context: <plan-dir>` footer when an AA-MA plan is active. Closing
  footer: `<!-- Generated by /sole-dev-merge -->` for traceability.

### Stage F — Push + PR/MR creation (idempotent)

_Implementation pending Step 3.4._

`git push -u origin HEAD`, then:

- **GitHub** — `gh pr view --json url` to detect existing PR; reuse via
  `gh pr edit --body-file "$BODY"` or create via
  `gh pr create --title "$TITLE" --body-file "$BODY"`.
- **GitLab** — `glab mr view` to detect existing MR; reuse via
  `glab mr update --description "$(cat $BODY)"` or create via
  `glab mr create --title "$TITLE" --description "$(cat $BODY)"` (NOT
  `--description-file` — that flag is fabricated; see reference.md "WRONG
  SYNTAX TO NEVER USE").

Title is the topmost Conventional Commit subject, truncated to 70 chars.

### Stage G — CI poll + auto-merge + cleanup

_Implementation pending Steps 4.1 – 4.5._

- **G1** (branch-protection pre-check) — `gh api repos/{owner}/{repo} --jq
  .allow_rebase_merge` / `glab api /projects/:id --jq .merge_method`. Falls
  back from `--rebase` to `--merge` if rebase merging is disabled.
- **G2** (CI poll) — divergent paths:
  - GitHub: `timeout 900s gh pr checks <num> --watch --interval 30 --fail-fast`.
    Translates RC=124 → clean exit 0 + `STATUS: CI_TIMEOUT`.
  - GitLab: `glab api /projects/:id/merge_requests/<iid>` polled every 30s in
    a bash `while` loop with `(( $(date +%s) - start < 900 ))` guard.
    Parses `.pipeline.status`. (NOT `glab ci status` — TTY UI, no scriptable
    exit codes.)
- **G3** (auto-merge) — `gh pr merge <num> --rebase --delete-branch` /
  `glab mr merge <iid> --rebase --remove-source-branch --yes`. Falls back to
  `--merge` per G1.
- **G3-error** — on CI failure or timeout, exits cleanly (rc=0) with PR/MR URL
  and recovery command (`gh pr merge … --auto --rebase` for timeout;
  `gh pr checks …` for failure).
- **G4** (cleanup) — `git checkout main`, `git pull --ff-only origin main`,
  `git fetch --prune`. Prints final summary: branch, commits merged, merge
  SHA, PR/MR URL.

---

## Exit-status contract

| Status            | Meaning                                              |
|-------------------|------------------------------------------------------|
| `OK`              | Merged to main; branch deleted; main fast-forwarded. |
| `ABORT: …`        | Pre-flight failure (Stage A); exit non-zero.         |
| `STATUS: AUTH_REQUIRED` | Auth failed (Stage E0); exit 0 + recovery hint.  |
| `STATUS: CI_TIMEOUT`    | 15-min poll exceeded (Stage G2); exit 0 + auto-merge recovery hint. |
| `STATUS: CI_FAILED — see <URL>` | Required check failed (Stage G2); exit 0 + diagnostic. |

Non-zero exits are reserved for Stage A pre-flight aborts. All other failures
exit cleanly with a `STATUS: …` line so the workflow is safe to run unattended.

---

## Tests

Bats suite lives in `tests/commands/sole-dev-merge/`. CI runs them via
`.github/workflows/security.yml` (added in M5.6). See
`docs/adr/0008-sole-dev-merge-pr-workflow.md` for full test inventory.

---

_Stages A–G are placeholders. Logic lands across Steps 1.2 – 4.5 of the
[sole-dev-merge-pr-workflow](../../.claude/dev/active/sole-dev-merge-pr-workflow/sole-dev-merge-pr-workflow-plan.md) plan._
