---
description: PR/MR-based merge workflow with scope-aware CI checks, review, security pass, and auto-merge
---

# /sole-dev-merge — PR/MR-Based Merge Workflow

Replaces the legacy fast-forward merge with a PR/MR-based workflow for sole-developer repos.

The command runs **scope-aware** CI checks against the working branch (closing
[L-007](../../docs/lessons.md)), dispatches a local AI code review plus a 3-source
security pass (security-auditor agent + Bandit + ShellCheck), opens a PR (`gh`)
or MR (`glab`) — defaulting to GitLab when both remotes exist — generates the
body via a Haiku-class agent, polls CI to green (15-min timeout), then
auto-merges with `--rebase --delete-branch` for a linear main history.

See [ADR-0008](../../docs/adr/0008-sole-dev-merge-pr-workflow.md) for the full
design rationale (placeholder until M5.3 lands).

## Assumptions

- Sole-developer workflow — **no concurrent invocations** on the same repo.
- One `main` (or `master`) branch is the merge target.
- `gh` and/or `glab` CLIs are installed and authenticated.
- Branch has at least one commit ahead of `main`.

## Migration Banner

On first invocation per session (post-symlink-swap), the command prints a
one-line migration banner referring users to ADR-0008. Suppress via
`AA_MA_SUPPRESS_MIGRATION_BANNER=1`. Implemented in M5.7.

---

## Workflow Stages

The workflow is composed of seven self-contained stages (A–G). Each stage is
an inline bash block in the AI-instructions section below. Stages are ordered
strictly; a failure in one stage prints `STATUS: <reason>` and exits without
advancing.

| Stage | Name | Milestone | Status |
|-------|------|-----------|--------|
| A | Pre-flight checks | M1.2 | placeholder — filled in M1.2 |
| B | Scope-aware CI checks (format/lint/typecheck/pytest/pre-commit + L-007 guard) | M1.3 | placeholder — filled in M1.3 |
| C | Code review + 3-source security pass (C1–C4) | M2.1–M2.4 | placeholder — filled in M2 |
| D | Findings triage (CRITICAL auto-fix, HIGH/MEDIUM AskUserQuestion, LOW → PR body) | M2.5 | placeholder — filled in M2 |
| E | Auth pre-flight + remote detection + remote choice + AI body generation | M3.1–M3.3, M3.5 | placeholder — filled in M3 |
| F | Push + PR/MR creation (idempotent) | M3.4 | placeholder — filled in M3 |
| G | Branch-protection pre-check + CI poll + auto-merge + cleanup | M4.1–M4.5 | placeholder — filled in M4 |

---

## Instructions for AI

Execute the stages in order. If a stage produces a non-zero exit or sets a
`STATUS:` line, **abort immediately** and print the recovery command (where
applicable). Do not skip stages.

### Stage A — Pre-flight checks

Refuses to proceed unless: not on `main`/`master`, working tree is clean, at
least one git remote is configured, and the branch is at least one commit
ahead of `main`. Each abort prints a distinct `ABORT: …` message to stdout
and returns a non-zero status. Sets the global `ORIGINAL_BRANCH` for later
recovery semantics.

```bash
# Stage A: Pre-flight checks (M1.2)
stage_a_preflight() {
  local original_branch
  original_branch=$(git branch --show-current 2>/dev/null) || {
    echo "ABORT: Not in a git repository"
    return 5
  }

  # Capture for later stages (recovery / return-to-working-branch semantics).
  # shellcheck disable=SC2034  # consumed by later stages (G4 cleanup)
  ORIGINAL_BRANCH="$original_branch"

  # Abort 1: on main/master
  case "$original_branch" in
    main|master)
      echo "ABORT: Cannot run /sole-dev-merge from main branch"
      return 1
      ;;
  esac

  # Abort 2: dirty working tree
  if [ -n "$(git status --porcelain)" ]; then
    echo "ABORT: Working tree is dirty — commit or stash changes first"
    return 2
  fi

  # Abort 3: no remote configured
  if [ -z "$(git remote)" ]; then
    echo "ABORT: No remote configured — add an origin remote first"
    return 3
  fi

  # Abort 4: no commits ahead of main (orphan/empty branch case)
  local ahead
  ahead=$(git rev-list --count main..HEAD 2>/dev/null || echo 0)
  if [ "$ahead" -lt 1 ]; then
    echo "ABORT: Branch has no commits ahead of main — nothing to merge"
    return 4
  fi

  echo "Pre-flight OK (branch: ${original_branch}, ahead: ${ahead} commit(s))"
  return 0
}
```

The AI invokes `stage_a_preflight` after reading this block; a non-zero return
code halts the workflow immediately.

### Stage B — Scope-aware CI checks (L-007 guard)

Closes [L-007](../../docs/lessons.md) by *scoping* format/lint operations to
files the branch actually touched, then reverting any out-of-scope drift via
`git checkout HEAD --` at the end. Typecheck / pytest / pre-commit still run
project-wide because their job is to validate behaviour, not mutate files.

Order:

1. Compute scope set from `git diff --name-only main...HEAD`.
2. Format + lint **in-scope Python** files only (`ruff format`, `ruff check --fix`).
3. Typecheck best-effort (`uv run mypy src/`, failures non-fatal) if `[tool.mypy]` is in `pyproject.toml`.
4. Pytest fast tier (`uv run pytest -m "not perf and not slow"`) if `tests/` exists; failure → abort.
5. Pre-commit (`pre-commit run --files <in-scope>`) if `.pre-commit-config.yaml` exists.
6. **L-007 guard:** revert any tracked file that is currently dirty but not in the scope set.

```bash
# Stage B: Scope-aware CI checks (M1.3)
stage_b_scope() {
  local changed_files changed_py changed_sh
  changed_files=$(git diff --name-only main...HEAD 2>/dev/null || true)
  changed_py=$(echo "$changed_files" | grep '\.py$' || true)
  changed_sh=$(echo "$changed_files" | grep '\.sh$' || true)

  # Export for downstream stages (D triage, F PR body, G poll)
  # shellcheck disable=SC2034  # consumed by later stages
  CHANGED_FILES="$changed_files"
  # shellcheck disable=SC2034
  CHANGED_PY="$changed_py"
  # shellcheck disable=SC2034
  CHANGED_SH="$changed_sh"

  local n_total n_py n_sh
  n_total=$(echo "$changed_files" | grep -c . || true)
  n_py=$(echo "$changed_py" | grep -c . || true)
  n_sh=$(echo "$changed_sh" | grep -c . || true)
  echo "Stage B scope: ${n_total} file(s) — py=${n_py}, sh=${n_sh}"

  # 2. Format + lint Python in-scope only (the L-007 fix)
  if [ -n "$changed_py" ] && command -v ruff >/dev/null 2>&1; then
    echo "$changed_py" | xargs -r ruff format
    echo "$changed_py" | xargs -r ruff check --fix
  fi

  # 3. Typecheck (best-effort, project-wide; non-fatal)
  if [ -f pyproject.toml ] && grep -q '^\[tool\.mypy\]' pyproject.toml 2>/dev/null \
       && command -v uv >/dev/null 2>&1; then
    uv run mypy src/ 2>&1 || true
  fi

  # 4. Pytest fast tier (project-wide, fatal on failure).
  # Exit-code semantics: 0 = all pass, 5 = no tests collected (treat as
  # skip — `tests/` may hold only fixture data). 1-4 = real failures.
  if [ -d tests ] && command -v uv >/dev/null 2>&1; then
    uv run pytest -m "not perf and not slow" -q
    local pytest_rc=$?
    if [ "$pytest_rc" -ne 0 ] && [ "$pytest_rc" -ne 5 ]; then
      echo "ABORT: pytest fast tier failed (exit ${pytest_rc}) — fix tests before merging"
      return 7
    fi
  fi

  # 5. Pre-commit (in-scope files only)
  if [ -f .pre-commit-config.yaml ] && [ -n "$changed_files" ] \
       && command -v pre-commit >/dev/null 2>&1; then
    echo "$changed_files" | xargs -r pre-commit run --files
  fi

  # 6. L-007 guard: revert any out-of-scope drift
  local dirty f reverted=0
  dirty=$(git diff --name-only HEAD 2>/dev/null || true)
  while IFS= read -r f; do
    [ -z "$f" ] && continue
    if ! echo "$changed_files" | grep -Fxq "$f"; then
      git checkout HEAD -- "$f" 2>/dev/null
      echo "L-007 guard: reverted out-of-scope file: $f"
      reverted=$((reverted+1))
    fi
  done <<< "$dirty"

  echo "Stage B OK (in-scope auto-fixes possibly applied; out-of-scope reverted: ${reverted})"
  return 0
}
```

After this stage, any in-scope auto-fixes remain in the working tree; Stage A
guarantees the index was clean on entry, so `git status` after Stage B reports
exactly the in-scope fix delta. The next step (auto-commit) handles the commit.

#### Auto-commit in-scope fixes (M1.4)

If Stage B mutated tracked files, commit them under
`chore(scope): pre-PR auto-fixes`. The trailing signature is chosen based on
the AA-MA plan context: `[AA-MA Plan] <task> .claude/dev/active/<task>` when a
plan is active; `[ad-hoc]` otherwise. (The `aa-ma-commit-signature.sh`
session-level hook is idempotent against a pre-included signature, so this
function is safe to call inside or outside an active session.)

```bash
# Step 1.4: Auto-commit in-scope fixes (M1.4)
stage_b_autocommit() {
  # Skip if no tracked modifications (untracked artifacts like __pycache__
  # don't count — they're not what Stage B mutates).
  if [ -z "$(git status --porcelain --untracked-files=no)" ]; then
    echo "Step 1.4: no in-scope auto-fixes to commit"
    return 0
  fi

  # Detect AA-MA plan context for the signature
  local repo_root plan_dir task_name signature
  repo_root=$(git rev-parse --show-toplevel 2>/dev/null) || repo_root="."
  plan_dir=$(find "${repo_root}/.claude/dev/active" \
              -mindepth 1 -maxdepth 1 -type d 2>/dev/null | head -1)
  if [ -n "$plan_dir" ]; then
    task_name=$(basename "$plan_dir")
    signature="[AA-MA Plan] ${task_name} .claude/dev/active/${task_name}"
  else
    signature="[ad-hoc]"
  fi

  # Stage tracked modifications only (the in-scope auto-fixes from Stage B).
  git add -u

  # Empty-second-`-m` produces the blank line between subject and trailer.
  git commit -q -m "chore(scope): pre-PR auto-fixes" -m "" -m "${signature}"

  local sha
  sha=$(git rev-parse --short HEAD)
  echo "Step 1.4: auto-fix commit ${sha} (signature: ${signature})"
  return 0
}
```

### Stage C — Code review + 3-source security pass

<!-- placeholder: Stages C1 (code-reviewer agent), C2 (security-auditor agent),
     C3 (Bandit on changed Python), C4 (ShellCheck on changed shell) land in
     M2.1–M2.4. All four sources emit the same severity-tag contract:
     [CRITICAL]/[HIGH]/[MEDIUM]/[LOW] <finding> — <path:line>.
     Safe-default fallback: classify all as [HIGH] on parse failure. -->

### Stage D — Findings triage

<!-- placeholder: Stage D implementation lands in M2.5. Behaviour:
     - CRITICAL → attempt auto-fix (Bandit/ShellCheck deterministic patterns
       only; agent-emitted CRITICALs tagged for user review). Re-run Stage B
       fast tier post-fix; commit as `fix(review): apply CRITICAL <source> findings`.
     - HIGH/MEDIUM → AskUserQuestion panel (4-options max per call). Options:
       Apply / Dispute (annotate) / Defer (record to context-log).
     - LOW → append to PR body "Reviewer notes" section (advisory only). -->

### Stage E — Auth pre-flight + remote detection + AI body

<!-- placeholder: Stages E0 (gh/glab auth status pre-flight), E1 (remote
     detection from `git remote -v`), E2 (remote choice — AskUserQuestion with
     default GitLab when both present), E3 (AI body generation via Haiku-class
     agent to absolute path /tmp/sole-dev-merge-body-<slug>.md) land in
     M3.1–M3.3, M3.5. -->

### Stage F — Push + PR/MR creation (idempotent)

<!-- placeholder: Stage F implementation lands in M3.4. Idempotent:
     - GitHub: `gh pr view --json url 2>/dev/null` → if PR exists, reuse via
       `gh pr edit --body-file`; else create via `gh pr create --body-file`.
     - GitLab: `glab mr view 2>/dev/null` → if MR exists, reuse via
       `glab mr update --description`; else create via
       `glab mr create --description "$(cat $BODY)"`.
       NOTE: `glab mr create --description-file` does NOT exist (fabricated
       flag — never use). -->

### Stage G — Branch-protection + poll + merge + cleanup

<!-- placeholder: Stages G1 (branch-protection pre-check), G2 (CI poll — gh
     uses `pr checks --watch` wrapped in `timeout 900s`; glab uses
     `glab api /projects/:id/merge_requests/<iid>` polled every 30s — NOT
     `glab ci status` which is a TTY UI), G3 (auto-merge with --rebase
     --delete-branch), G4 (post-merge cleanup: checkout main, ff-pull,
     fetch --prune) land in M4.1–M4.5. Timeout (RC=124) → clean exit 0 with
     `STATUS: CI_TIMEOUT` + recovery command. -->

---

_End of skeleton. Stage implementations land per the milestone schedule
above. See [.claude/dev/active/sole-dev-merge-pr-workflow/](../../.claude/dev/active/sole-dev-merge-pr-workflow/)
for the AA-MA plan, tasks, and provenance log._
