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

  # Abort 1: on main (plan §8 documents main as the default branch)
  if [ "$original_branch" = "main" ]; then
    echo "ABORT: Cannot run /sole-dev-merge from main branch"
    return 1
  fi

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
# Stage B: Scope-aware CI checks (M1.3, hardened in M2.0 per §6.8 review)
#
# Uses null-delimited paths (`git diff -z --name-only`) and bash arrays
# throughout — robust against filenames containing spaces, tabs, or literal
# newlines (legal in git). Membership test for the L-007 guard is an
# associative-array lookup (O(1) per file) rather than newline-scan.
stage_b_scope() {
  # 1. Compute scope set into bash arrays (null-delimited from git).
  # Arrays are GLOBAL (no `local`) so downstream Stages C-G can consume them.
  CHANGED_FILES_ARR=()
  CHANGED_PY_ARR=()
  CHANGED_SH_ARR=()
  local f
  while IFS= read -r -d '' f; do
    CHANGED_FILES_ARR+=("$f")
    case "$f" in
      *.py) CHANGED_PY_ARR+=("$f") ;;
      *.sh) CHANGED_SH_ARR+=("$f") ;;
    esac
  done < <(git diff -z --name-only main...HEAD 2>/dev/null || true)

  # Export array names for later stages (Bash 4.3+ `declare -n` indirect).
  # Downstream stages source the same markdown so they see the arrays directly.
  # shellcheck disable=SC2034  # consumed by later stages
  CHANGED_FILES_COUNT=${#CHANGED_FILES_ARR[@]}
  local n_py=${#CHANGED_PY_ARR[@]}
  local n_sh=${#CHANGED_SH_ARR[@]}
  echo "Stage B scope: ${CHANGED_FILES_COUNT} file(s) — py=${n_py}, sh=${n_sh}"

  # 2. Format + lint Python in-scope only (the L-007 fix). Pass arrays
  # directly to ruff — no xargs, no shell-splitting.
  if [ "$n_py" -gt 0 ] && command -v ruff >/dev/null 2>&1; then
    ruff format "${CHANGED_PY_ARR[@]}"
    ruff check --fix "${CHANGED_PY_ARR[@]}"
  fi

  # 3. Typecheck (best-effort, project-wide). Capture rc + count so the
  # user has visible signal even when non-fatal.
  if [ -f pyproject.toml ] && grep -q '^\[tool\.mypy\]' pyproject.toml 2>/dev/null \
       && command -v uv >/dev/null 2>&1; then
    local mypy_out mypy_rc mypy_err_count
    mypy_out=$(uv run mypy src/ 2>&1)
    mypy_rc=$?
    if [ "$mypy_rc" -ne 0 ]; then
      mypy_err_count=$(printf '%s\n' "$mypy_out" | grep -cE ':[0-9]+: (error|note)' || true)
      echo "Stage B: mypy reported ${mypy_err_count} issue(s) (non-fatal — see plan §6)"
    fi
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

  # 5. Pre-commit (in-scope files only). Pass array directly.
  if [ -f .pre-commit-config.yaml ] && [ "${CHANGED_FILES_COUNT}" -gt 0 ] \
       && command -v pre-commit >/dev/null 2>&1; then
    pre-commit run --files "${CHANGED_FILES_ARR[@]}"
  fi

  # 6. L-007 guard: associative-array O(1) membership test. Use git's
  # null-delimited output so filenames with whitespace/newlines work.
  local -A in_scope=()
  for f in "${CHANGED_FILES_ARR[@]}"; do in_scope["$f"]=1; done

  local reverted=0
  while IFS= read -r -d '' f; do
    if [ -z "${in_scope[$f]+x}" ]; then
      git checkout HEAD -- "$f" 2>/dev/null
      echo "L-007 guard: reverted out-of-scope file: $f"
      reverted=$((reverted+1))
    fi
  done < <(git diff -z --name-only HEAD 2>/dev/null || true)

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

Four parallel finding sources, all emitting the same severity-tag contract:

```
[CRITICAL] <one-line finding> — <path>:<line>
[HIGH]     <one-line finding> — <path>:<line>
[MEDIUM]   <one-line finding> — <path>:<line>
[LOW]      <one-line finding> — <path>:<line>
```

Parser regex: `^\[(CRITICAL|HIGH|MEDIUM|LOW)\][[:space:]]+(.+?)[[:space:]]+—[[:space:]]+(.+?):([0-9]+)$`

**Safe-default fallback:** if any source's output fails the parser, classify
ALL of its findings as `[HIGH]` (forces user review of everything; no
auto-fix). Log the parse failure to provenance.log.

```bash
# Common helpers for Stages C1-C4 + D (M2.1-M2.5)

# Per-invocation slug; tests can override via SOLE_DEV_MERGE_SLUG env var.
_sdm_slug() {
  echo "${SOLE_DEV_MERGE_SLUG:-$$-$(date +%s)}"
}

_sdm_paths() {
  local slug; slug=$(_sdm_slug)
  SDM_REVIEW_OUT="/tmp/sole-dev-merge-review-${slug}.md"
  SDM_SECURITY_OUT="/tmp/sole-dev-merge-security-${slug}.md"
  SDM_BANDIT_JSON="/tmp/sole-dev-merge-bandit-${slug}.json"
  SDM_SHELLCHECK_JSON="/tmp/sole-dev-merge-shellcheck-${slug}.json"
  SDM_FINDINGS_OUT="/tmp/sole-dev-merge-findings-${slug}.md"
  export SDM_REVIEW_OUT SDM_SECURITY_OUT SDM_BANDIT_JSON SDM_SHELLCHECK_JSON SDM_FINDINGS_OUT
}

# Severity-line parser. Reads a file; emits normalised TSV: SEV<TAB>MSG<TAB>PATH<TAB>LINE
# Falls back to all-HIGH classification (one row per non-empty line) when zero
# severity-tagged lines are found — the safe-default fallback contract.
_sdm_parse_findings() {
  local file="$1" source_label="$2"
  if [ ! -s "$file" ]; then
    return 0
  fi
  local parsed_count=0
  while IFS= read -r line; do
    if [[ "$line" =~ ^\[(CRITICAL|HIGH|MEDIUM|LOW)\][[:space:]]+(.+)[[:space:]]+—[[:space:]]+(.+):([0-9]+)$ ]]; then
      printf '%s\t%s\t%s\t%s\t%s\n' \
        "${BASH_REMATCH[1]}" "${BASH_REMATCH[2]}" "${BASH_REMATCH[3]}" "${BASH_REMATCH[4]}" "$source_label"
      parsed_count=$((parsed_count+1))
    fi
  done < "$file"
  if [ "$parsed_count" -eq 0 ]; then
    # Safe-default fallback: every non-empty line → HIGH
    echo "[SDM] WARN: parser failure on $file ($source_label); applying safe-default all-HIGH classification" >&2
    while IFS= read -r line; do
      [ -z "$line" ] && continue
      printf 'HIGH\t%s\t%s\t0\t%s\n' "${line//$'\t'/ }" "<unparsed>" "$source_label"
    done < "$file"
  fi
}
```

#### Stage C1 — Code-reviewer agent dispatch (M2.1)

Prepares the output path, then dispatches the `feature-dev:code-reviewer`
agent (fallback: `code-reviewer`) against `git diff main...HEAD`. The bash
sets up the contract; the **AI executing this command** invokes the Agent
tool with the prompt below. Tests short-circuit via `MOCK_AGENT_DISPATCH=1`.

Agent prompt template:

> Review this diff for KISS/SOLID/SOC/DRY + 5 mandatory patterns (scope
> discipline, mechanism duplication, schema-breaking output, dead code,
> magic numbers). DIFF: `git diff main...HEAD`. Emit findings using
> EXACTLY this format (parser regex pinned):
>
>     [CRITICAL] <one-line finding> — <path>:<line>
>     [HIGH]     <one-line finding> — <path>:<line>
>     [MEDIUM]   <one-line finding> — <path>:<line>
>     [LOW]      <one-line finding> — <path>:<line>
>
> Output to file: `$SDM_REVIEW_OUT`. End with `SUMMARY: <N> CRITICAL, <M>
> WARNING, <P> INFO`. Be fair on documented design choices.

```bash
# Stage C1: Code-reviewer agent dispatch (M2.1)
stage_c1_review_dispatch() {
  _sdm_paths

  if [ "${MOCK_AGENT_DISPATCH:-0}" = "1" ]; then
    if [ -n "${MOCK_AGENT_FIXTURE_C1:-}" ] && [ -f "$MOCK_AGENT_FIXTURE_C1" ]; then
      cp "$MOCK_AGENT_FIXTURE_C1" "$SDM_REVIEW_OUT"
      echo "Stage C1: MOCKED — copied $MOCK_AGENT_FIXTURE_C1 → $SDM_REVIEW_OUT"
    else
      : > "$SDM_REVIEW_OUT"  # empty fixture = "no findings"
      echo "Stage C1: MOCKED — empty findings file at $SDM_REVIEW_OUT"
    fi
    return 0
  fi

  # Production path: signal to the AI to invoke the Agent tool.
  echo "Stage C1: dispatch feature-dev:code-reviewer (fallback: code-reviewer) → $SDM_REVIEW_OUT"
  echo "  prompt: review git diff main...HEAD with severity contract; output to $SDM_REVIEW_OUT"
  return 0
}
```

#### Stage C2 — Security-auditor agent dispatch (M2.2)

Parallel to C1. Same severity contract. Same MOCK pattern.

Agent prompt template:

> Semantic OWASP review of this diff: input validation, auth/secrets
> handling, command injection, path traversal, hardcoded credentials,
> OWASP top-10. DIFF: `git diff main...HEAD`. Output format identical
> to C1 (`[CRITICAL]/[HIGH]/[MEDIUM]/[LOW] <finding> — <path>:<line>`).
> Output file: `$SDM_SECURITY_OUT`.

```bash
# Stage C2: Security-auditor agent dispatch (M2.2)
stage_c2_security_dispatch() {
  _sdm_paths

  if [ "${MOCK_AGENT_DISPATCH:-0}" = "1" ]; then
    if [ -n "${MOCK_AGENT_FIXTURE_C2:-}" ] && [ -f "$MOCK_AGENT_FIXTURE_C2" ]; then
      cp "$MOCK_AGENT_FIXTURE_C2" "$SDM_SECURITY_OUT"
      echo "Stage C2: MOCKED — copied $MOCK_AGENT_FIXTURE_C2 → $SDM_SECURITY_OUT"
    else
      : > "$SDM_SECURITY_OUT"
      echo "Stage C2: MOCKED — empty findings file at $SDM_SECURITY_OUT"
    fi
    return 0
  fi

  echo "Stage C2: dispatch security-auditor → $SDM_SECURITY_OUT"
  echo "  prompt: semantic OWASP review of git diff main...HEAD; output to $SDM_SECURITY_OUT"
  return 0
}
```

#### Stage C3 — Bandit on changed Python (M2.3)

Runs `bandit -f json -r` against the `CHANGED_PY_ARR` array from Stage B.
Parses JSON, maps Bandit severity to the unified scheme per
[`reference.md`](../../.claude/dev/active/sole-dev-merge-pr-workflow/sole-dev-merge-pr-workflow-reference.md)
(HIGH→CRITICAL, MEDIUM→HIGH, LOW→MEDIUM).

```bash
# Stage C3: Bandit on changed Python (M2.3)
stage_c3_bandit() {
  _sdm_paths
  : > "$SDM_BANDIT_JSON"  # always create — empty if nothing to scan

  if [ "${#CHANGED_PY_ARR[@]}" -eq 0 ] || ! command -v bandit >/dev/null 2>&1; then
    echo "Stage C3: skipped (no Python files in scope or bandit not installed)"
    return 0
  fi

  bandit -f json "${CHANGED_PY_ARR[@]}" > "$SDM_BANDIT_JSON" 2>/dev/null || true

  # Convert to severity-tagged lines (append to a per-source findings file)
  local out="$SDM_REVIEW_OUT.bandit"  # use a side file so C1/C2/C3/C4 don't collide
  : > "$out"
  if command -v jq >/dev/null 2>&1; then
    jq -r '.results[]? | "\(.issue_severity)\t\(.test_id) \(.issue_text)\t\(.filename)\t\(.line_number)"' \
       "$SDM_BANDIT_JSON" | while IFS=$'\t' read -r sev msg file line; do
      local mapped="LOW"
      case "$sev" in
        HIGH) mapped="CRITICAL" ;;
        MEDIUM) mapped="HIGH" ;;
        LOW) mapped="MEDIUM" ;;
      esac
      printf '[%s] %s — %s:%s\n' "$mapped" "$msg" "$file" "$line" >> "$out"
    done
  fi

  local n; n=$(wc -l < "$out" 2>/dev/null || echo 0)
  echo "Stage C3: Bandit produced ${n} finding(s) at $out"
  return 0
}
```

#### Stage C4 — ShellCheck on changed shell (M2.4)

Runs `shellcheck -f json1` (newline-delimited JSON, easier to parse) against
the `CHANGED_SH_ARR` array. Maps `error/warning/info/style` →
`CRITICAL/HIGH/MEDIUM/LOW` per reference.md.

```bash
# Stage C4: ShellCheck on changed shell (M2.4)
stage_c4_shellcheck() {
  _sdm_paths
  : > "$SDM_SHELLCHECK_JSON"

  if [ "${#CHANGED_SH_ARR[@]}" -eq 0 ] || ! command -v shellcheck >/dev/null 2>&1; then
    echo "Stage C4: skipped (no shell files in scope or shellcheck not installed)"
    return 0
  fi

  shellcheck -f json "${CHANGED_SH_ARR[@]}" > "$SDM_SHELLCHECK_JSON" 2>/dev/null || true

  local out="$SDM_REVIEW_OUT.shellcheck"
  : > "$out"
  if command -v jq >/dev/null 2>&1 && [ -s "$SDM_SHELLCHECK_JSON" ]; then
    jq -r '.[]? | "\(.level)\tSC\(.code) \(.message)\t\(.file)\t\(.line)"' \
       "$SDM_SHELLCHECK_JSON" 2>/dev/null | while IFS=$'\t' read -r level msg file line; do
      local mapped="LOW"
      case "$level" in
        error) mapped="CRITICAL" ;;
        warning) mapped="HIGH" ;;
        info) mapped="MEDIUM" ;;
        style) mapped="LOW" ;;
      esac
      printf '[%s] %s — %s:%s\n' "$mapped" "$msg" "$file" "$line" >> "$out"
    done
  fi

  local n; n=$(wc -l < "$out" 2>/dev/null || echo 0)
  echo "Stage C4: ShellCheck produced ${n} finding(s) at $out"
  return 0
}
```

### Stage D — Findings triage (M2.5)

Aggregates all four finding sources into a single consolidated file, then
triages by severity:

- **CRITICAL** — attempt deterministic auto-fix for Bandit B602 (narrow:
  `shell=True` → removed). Re-run Stage B fast tier to confirm no
  regression. Commit as `fix(review): apply CRITICAL bandit findings`.
  Agent-emitted CRITICALs (no deterministic fix) get tagged for user review.
- **HIGH/MEDIUM** — `AskUserQuestion` panel (4-options max per call).
  Test harness: each panel writes `AUQ_DISPATCH n_options=<N>` to `$AUQ_LOG`.
- **LOW** — append to PR body's "Reviewer notes" section (advisory only).

```bash
# Stage D: Findings triage (M2.5) — HITL on HIGH/MEDIUM
stage_d_triage() {
  _sdm_paths

  # Aggregate all 4 sources
  : > "$SDM_FINDINGS_OUT"
  for src in "$SDM_REVIEW_OUT" "$SDM_SECURITY_OUT" \
             "$SDM_REVIEW_OUT.bandit" "$SDM_REVIEW_OUT.shellcheck"; do
    [ -s "$src" ] && cat "$src" >> "$SDM_FINDINGS_OUT"
  done

  # Count by severity. Note: grep -c outputs "0" AND exits 1 when there
  # are no matches — `|| echo 0` would duplicate output. Use `|| true` and
  # default-substitute instead. `grep -c` always outputs a number.
  local n_critical n_high n_medium n_low
  n_critical=$(grep -cE '^\[CRITICAL\]' "$SDM_FINDINGS_OUT" 2>/dev/null) || n_critical=0
  n_high=$(grep -cE '^\[HIGH\]' "$SDM_FINDINGS_OUT" 2>/dev/null) || n_high=0
  n_medium=$(grep -cE '^\[MEDIUM\]' "$SDM_FINDINGS_OUT" 2>/dev/null) || n_medium=0
  n_low=$(grep -cE '^\[LOW\]' "$SDM_FINDINGS_OUT" 2>/dev/null) || n_low=0

  echo "Stage D: findings — CRITICAL=${n_critical} HIGH=${n_high} MEDIUM=${n_medium} LOW=${n_low}"

  # CRITICAL → attempt narrow auto-fix for Bandit B602
  if [ "${n_critical}" -gt 0 ]; then
    _sdm_apply_b602_autofix
  fi

  # HIGH/MEDIUM → AskUserQuestion panel logging (production: AI invokes AUQ)
  if [ "${n_high}" -gt 0 ] || [ "${n_medium}" -gt 0 ]; then
    _sdm_log_auq_dispatches "${n_high}" "${n_medium}"
  fi

  # LOW → append to PR-body advisory file
  if [ "${n_low}" -gt 0 ]; then
    local pr_notes="${SDM_FINDINGS_OUT}.pr-notes"
    : > "$pr_notes"
    grep -E '^\[LOW\]' "$SDM_FINDINGS_OUT" > "$pr_notes" || true
    echo "Stage D: ${n_low} LOW finding(s) → ${pr_notes} (advisory only)"
  fi

  return 0
}

# Narrow B602 auto-fix: remove `, shell=True` from subprocess calls.
# Limited to the exact pattern Bandit reports as B602; broader fixes are tagged
# for user review.
_sdm_apply_b602_autofix() {
  if [ ! -s "$SDM_BANDIT_JSON" ] || ! command -v jq >/dev/null 2>&1; then
    return 0
  fi

  local fixed_files=()
  local f
  while IFS= read -r f; do
    [ -z "$f" ] && continue
    # Narrow regex: handles common forms `shell=True` and `, shell=True`
    if grep -q 'shell[[:space:]]*=[[:space:]]*True' "$f"; then
      sed -i -E 's/,[[:space:]]*shell[[:space:]]*=[[:space:]]*True//g; s/shell[[:space:]]*=[[:space:]]*True,?[[:space:]]*//g' "$f"
      fixed_files+=("$f")
    fi
  done < <(jq -r '.results[]? | select(.test_id == "B602") | .filename' "$SDM_BANDIT_JSON" 2>/dev/null | sort -u)

  if [ "${#fixed_files[@]}" -gt 0 ]; then
    # Commit the fix with an AA-MA-aware signature trailer (same logic as M1.4)
    local repo_root plan_dir task_name signature
    repo_root=$(git rev-parse --show-toplevel 2>/dev/null) || repo_root="."
    plan_dir=$(find "${repo_root}/.claude/dev/active" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | head -1)
    if [ -n "$plan_dir" ]; then
      task_name=$(basename "$plan_dir")
      signature="[AA-MA Plan] ${task_name} .claude/dev/active/${task_name}"
    else
      signature="[ad-hoc]"
    fi

    git add "${fixed_files[@]}"
    git commit -q -m "fix(review): apply CRITICAL bandit findings" -m "" -m "${signature}"
    local sha; sha=$(git rev-parse --short HEAD)
    echo "Stage D: B602 auto-fix landed in ${sha} (files: ${fixed_files[*]})"
  fi
}

# AskUserQuestion panel logging — the AI invokes the actual AUQ at runtime.
# We log the dispatch count so the test harness can verify panel cardinality.
_sdm_log_auq_dispatches() {
  local n_high="$1" n_medium="$2"
  local total=$((n_high + n_medium))
  # 4-options max per panel → ceil(total/4) panels
  local n_panels=$(( (total + 3) / 4 ))
  local AUQ_LOG="${AUQ_LOG:-/tmp/sole-dev-merge-auq-$(_sdm_slug).log}"
  : > "$AUQ_LOG"
  local i
  for ((i=0; i < n_panels; i++)); do
    local panel_size=4
    if [ "$i" -eq $((n_panels - 1)) ] && [ "$((total % 4))" -gt 0 ]; then
      panel_size=$((total % 4))
    fi
    echo "AUQ_DISPATCH n_options=${panel_size}" >> "$AUQ_LOG"
  done
  echo "Stage D: ${n_panels} AskUserQuestion panel(s) logged to ${AUQ_LOG} (HIGH=${n_high}, MEDIUM=${n_medium})"
}
```

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
