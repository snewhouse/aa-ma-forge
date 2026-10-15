---
name: sole-dev-merge
description: PR/MR-based merge workflow with scope-aware CI checks, review, security pass, and auto-merge. Run only when the user asks to merge a branch or PR.
disable-model-invocation: true
---

# /sole-dev-merge — PR/MR merge workflow (v2)

PR/MR-based merge workflow for sole developers. Runs scope-aware local CI
(closing L-007), dispatches code review + 3-source security pass
(security-auditor agent + Ruff S + ShellCheck), opens a PR via `gh` or MR via
`glab` (default GitLab when both remotes present), polls CI to green, then
auto-merges with `--rebase` for linear history, then deletes the remote branch
itself and checks it is gone (worktree-safe, L-1332).

**Replaces:** the legacy fast-merge `/sole-dev-merge` user-local command. The
plugin install (`scripts/install.sh`) links `~/.claude/skills/sole-dev-merge/`
after backing up anything real in its way to
`~/.claude/backups/aa-ma-forge-<timestamp>/`, and removes the old
`~/.claude/commands/sole-dev-merge.md` link once its source is gone (ADR-0020).

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
named bash blocks: inline below for Stages A–B, in `references/stage-*.md`
for Stages C–G. Read each stage's reference when you reach it.

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

See [stage-c-review-and-security.md](references/stage-c-review-and-security.md#stage-c--code-review--3-source-security-pass) — the parallel code-reviewer and security-auditor dispatch, Ruff S and ShellCheck, and the findings aggregation.

### Stage D — Findings triage

See [stage-d-triage.md](references/stage-d-triage.md#stage-d--findings-triage) — how findings are routed by severity: the S602 auto-fix, user panels for HIGH/MEDIUM, LOW to reviewer notes.

**HIGH and MEDIUM findings go to the user (`AskUserQuestion`: Apply / Dispute / Defer) before Stage E starts.**

### Stage E — Remote detection, choice, auth, AI body generation

See [stage-e-remote-and-body.md](references/stage-e-remote-and-body.md#stage-e--remote-detection-choice-auth-ai-body-generation) — remote detection and choice, the auth check and the generated PR/MR body.

### Stage F — Push + PR/MR creation (idempotent)

See [stage-f-push.md](references/stage-f-push.md#stage-f--push--prmr-creation-idempotent) — the idempotent push and PR/MR creation.

### Stage G — CI poll + auto-merge + cleanup

See [stage-g-merge.md](references/stage-g-merge.md#stage-g--ci-poll--auto-merge--cleanup) — branch protection check, CI polling, the rebase merge and local cleanup.

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
[sole-dev-merge-pr-workflow](../../../.claude/dev/completed/sole-dev-merge-pr-workflow/sole-dev-merge-pr-workflow-plan.md) plan._
