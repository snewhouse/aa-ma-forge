# sole-dev-merge-pr-workflow Plan

**Objective:** Replace the existing `/sole-dev-merge` fast-merge command with a PR/MR-based workflow that runs scope-aware CI checks, dispatches a local code review + 3-source security pass (security-auditor agent + Bandit + ShellCheck), opens a PR via `gh` or MR via `glab` (prompting when both remotes exist, default GitLab), polls CI to green, then auto-merges via `--rebase --delete-branch`.

**Owner:** Stephen J Newhouse + Claude Code
**Created:** 2026-05-18
**Last Updated:** 2026-05-18 (Revision 2 — addresses 17 CRITICALs from v1 verification)
**AA-MA Slug:** sole-dev-merge-ci-pr-20260518105415

**Revision history:**
- v1 (2026-05-18 11:00): Initial plan. FAIL — 17 CRITICAL findings.
- v2 (2026-05-18 11:50): Major revision. Switched from skill/lib pattern → command-only with inline bash. Replaced fictional security skills with security-auditor agent + Bandit + ShellCheck. Fixed all gh/glab CLI contracts. Added Audit-Profile per milestone. Re-tagged Critical-Path. Removed phantom install.sh edit. Added SECURITY.md + ADR-0008 to MODIFY list.

---

## 1. Executive Summary

A single new file `claude-code/commands/sole-dev-merge.md` REPLACES the user-local `~/.claude/commands/sole-dev-merge.md` (deployed via install.sh auto-discovery). All workflow logic lives inline in the command markdown as named bash blocks — no `skill/lib/*.sh` scaffolding (no precedent in this repo for that pattern). The workflow runs format/lint on changed-files-only (closing L-007), typecheck/pytest/pre-commit project-wide, dispatches a code-reviewer subagent against `git diff main...HEAD` with explicit severity-tag contract, runs a 3-source security pass (security-auditor agent + Bandit on changed .py + ShellCheck on changed .sh), auto-applies CRITICAL findings (asks user on HIGH/MEDIUM), opens PR/MR with AI-generated body (idempotently — reuses existing PR if found), polls CI green via `gh pr checks --watch` / `glab api`, and merges with `--rebase --delete-branch` for linear history.

## 2. Stepwise Implementation Plan

### Milestone 1 — Pre-flight + scope-aware checks

**Audit-Profile:** code-only
**Gate:** HARD
**Mode:** AFK
**Critical-Path:** doc-count-drift (M1 touches no docs but the scope-filter logic is the L-007 fix — its absence is itself a doc-drift hazard)

- **1.1** Skeleton `claude-code/commands/sole-dev-merge.md` with frontmatter:
  ```yaml
  ---
  description: PR/MR-based merge workflow with scope-aware CI checks, review, security pass, and auto-merge
  ---
  ```
  Body has placeholders for stages A–G described below. No actual logic yet — this is the file shell.
- **1.2** Stage A (Pre-flight checks) — inline bash block. Captures `ORIGINAL_BRANCH`, refuses if on main/master, refuses on uncommitted changes, requires at least one remote, requires at least one commit ahead of main. Output `Pre-flight OK` or actionable ABORT message.
- **1.3** Stage B (Scope-aware CI checks) — inline bash block. Steps:
  1. `CHANGED_FILES=$(git diff --name-only main...HEAD)`
  2. `CHANGED_PY=$(echo "$CHANGED_FILES" | grep '\.py$' || true)`
  3. `CHANGED_SH=$(echo "$CHANGED_FILES" | grep '\.sh$' || true)`
  4. Format: `ruff format $CHANGED_PY` (when non-empty) — scopes drift to in-scope files only
  5. Lint with fix: `ruff check --fix $CHANGED_PY`
  6. Typecheck (best-effort): `uv run mypy src/ 2>&1 || true` if `[tool.mypy]` exists in `pyproject.toml`; else skip silently
  7. Pytest fast tier: `uv run pytest -m "not perf and not slow"` if `tests/` exists; else skip
  8. Pre-commit: `pre-commit run --files $CHANGED_FILES` if `.pre-commit-config.yaml` exists; else skip
  9. After steps 4-5, run `git status --porcelain` — if ANY out-of-scope file appears (not in `$CHANGED_FILES`), `git checkout -- <out-of-scope-path>` it (L-007 guard).
- **1.4** If `git status` is non-clean AFTER L-007 guard ran (i.e. in-scope auto-fixes were applied), commit them: `git commit -am "chore(scope): pre-PR auto-fixes"`. Plan-active commit signature applied by existing `aa-ma-commit-signature.sh` hook (or `[ad-hoc]` if no plan). If git status is clean, skip the commit.
- **1.5** Bats test `tests/commands/sole-dev-merge/test_stage_b_scope.bats` — given a feature branch with an in-scope formatting error AND an out-of-scope dirty `tests/codemem/foo.py`, verify post-Stage-B: in-scope file fixed + committed, out-of-scope file reverted to HEAD.
- **1.6** Bats test `tests/commands/sole-dev-merge/test_stage_a_preflight.bats` — verify pre-flight abort messages for each abort condition (on main, dirty tree, no remote, no commits ahead).

### Milestone 2 — Review + 3-source security pass

**Audit-Profile:** full
**Gate:** HARD
**Mode:** HITL (Step 2.5 prompts on HIGH/MEDIUM findings)

- **2.1** Stage C1 (Code review dispatch) — inline bash + Agent tool block. Dispatches `feature-dev:code-reviewer` (preferred; fall back to `code-reviewer` if unavailable) with explicit prompt contract:
  ```
  Review the diff against main: git diff main...HEAD
  Output findings using EXACTLY this severity prefix format:
  [CRITICAL] <one-line finding> — <path:line>
  [HIGH]     <one-line finding> — <path:line>
  [MEDIUM]   <one-line finding> — <path:line>
  [LOW]      <one-line finding> — <path:line>
  Output to /tmp/sole-dev-merge-review-<slug>.md
  ```
  This explicit contract bypasses the agent's native 2-tier/3-tier scheme by INSTRUCTING the format. Parsing falls back to "report all as HIGH" if agent output doesn't match the contract.
- **2.2** Stage C2 (security-auditor agent dispatch) — parallel to 2.1, same `[CRITICAL]/[HIGH]/[MEDIUM]/[LOW]` contract. Verified agent path: `~/.claude/agents/security-auditor.md`. Prompt focuses on: input validation, auth/secrets handling, command injection, path traversal, hardcoded credentials, OWASP top-10 patterns.
- **2.3** Stage C3 (Bandit on Python changes) — `bandit -f json -r $CHANGED_PY 2>/dev/null > /tmp/bandit-findings.json` if `$CHANGED_PY` non-empty. Parse JSON: severity `HIGH` → `[CRITICAL]`, `MEDIUM` → `[HIGH]`, `LOW` → `[MEDIUM]`. Append to findings buffer.
- **2.4** Stage C4 (ShellCheck on shell changes) — `shellcheck -f json $CHANGED_SH > /tmp/shellcheck-findings.json` if `$CHANGED_SH` non-empty. Parse: `error` → `[CRITICAL]`, `warning` → `[HIGH]`, `info`/`style` → `[MEDIUM]`. Append to findings buffer.
- **2.5** Stage D (Findings triage) — inline bash. Concatenate all 4 source findings into `/tmp/all-findings.md`. Parse counts by severity:
  - **CRITICAL** → attempt auto-fix only for deterministic patterns (Bandit/ShellCheck fixes via tool-suggested replacements; agent-emitted CRITICALs are tagged for user-review). After auto-fix, re-run Stage B fast tier (lint + pytest) to confirm no regression. Commit as `fix(review): apply CRITICAL <bandit|shellcheck|agent> findings`.
  - **HIGH/MEDIUM** → `AskUserQuestion` panel (4-per-call max), options: Apply / Dispute (annotate) / Defer (record to context-log).
  - **LOW** → append to PR body's "Reviewer notes" section (advisory only).
- **2.6** Bats test `tests/commands/sole-dev-merge/test_stage_d_triage.bats` — given a fixture with planted Bandit B602 (subprocess shell=True) in a changed Python file: verify auto-fix commit exists, `bandit -t B602 fixture.py` reports zero issues post-fix.
- **2.7** Bats test `tests/commands/sole-dev-merge/test_stage_c_dispatch.bats` — mock the Agent tool dispatcher to return a fixture severity-tagged file; verify Stage D processes it correctly.

### Milestone 3 — PR/MR creation with idempotency

**Audit-Profile:** full
**Gate:** HARD
**Mode:** HITL (Step 3.2 prompts when dual remotes exist)
**Critical-Path:** external-api (gh/glab CLI contract surface — flags, body formats, response parsing)

- **3.1** Stage E1 (Remote detection) — inline bash. Parses `git remote -v` (stripping fetch/push duplicates) into associative arrays. Classifies each remote: `github` if URL matches `github.com`, `gitlab` if matches `gitlab.com`, `other` else. Outputs counts: `n_github`, `n_gitlab`, `n_other`. No JSON envelope — bash-internal state.
- **3.2** Stage E2 (Remote choice) — decision logic:
  - 1 remote total → use it
  - github + gitlab (both present) → `AskUserQuestion` with default option "GitLab" (per Biorelate convention from `bk_galactic_agent.md`, `bk_langdock_dev_and_testing.md`, `bk_zoetis_safety_intelligence.md`)
  - zero github + zero gitlab → fail with actionable error ("only github.com and gitlab.com remotes supported")
- **3.3** Stage E3 (AI body generation) — inline bash + Agent tool with Haiku-class model. Writes body to absolute path `/tmp/sole-dev-merge-body-<slug>.md`. Body contains:
  - `## Summary` (1-3 sentence narrative AI-generated from `git diff main...HEAD --stat` + commit subjects)
  - `## Changes by area` (grouped bullet list, AI-grouped)
  - `## Test plan` (checkbox list seeded with "[ ] CI checks pass", "[ ] manual smoke test")
  - `## Reviewer notes` (LOW findings from M2 if any; "(none)" else)
  - If AA-MA plan active: `Plan context: <plan-dir-absolute-path>` line at the bottom, value extracted from the topmost `.claude/dev/active/*/` dir
  - Footer: `<!-- Generated by /sole-dev-merge -->` for traceability
- **3.4** Stage F (Push + PR/MR creation, **idempotent**) — inline bash:
  1. `git push -u origin HEAD` (idempotent — works for first-push and subsequent pushes)
  2. **GitHub branch:** `gh pr view --json url 2>/dev/null && PR_EXISTS=1 || PR_EXISTS=0`. If `$PR_EXISTS=1`, reuse existing PR (update body via `gh pr edit --body-file "$BODY"`). Else `gh pr create --title "$TITLE" --body-file "$BODY"`.
  3. **GitLab branch:** `glab mr view 2>/dev/null && MR_EXISTS=1 || MR_EXISTS=0`. If `$MR_EXISTS=1`, reuse. Else `glab mr create --title "$TITLE" --description "$(cat $BODY)"`. Note: glab uses `-d/--description` (string), NOT `--description-file` (which is a fabricated flag). No `--remove-source-branch=false` (boolean flag — omitted to keep source branch at creation time; deletion handled at merge time).
  4. Title = topmost Conventional Commit subject, truncated to 70 chars.
  5. Capture PR/MR URL for Stage G.
- **3.5** Auth pre-flight (Stage E0, runs at the start of M3): `gh auth status 2>/dev/null` (when dispatching gh) AND/OR `glab auth status 2>/dev/null` (when dispatching glab). If either returns non-zero, abort with: `STATUS: AUTH_REQUIRED — run gh auth login || glab auth login`. Prevents the 15-min unattended poll from hitting token expiry.
- **3.6** Bats test `tests/commands/sole-dev-merge/test_stage_e_remote.bats` — three fixtures (github-only, gitlab-only, dual). Verify classification + AskUserQuestion mock invocation for dual case.
- **3.7** Bats test `tests/commands/sole-dev-merge/test_stage_f_idempotent.bats` — mock `gh pr view` returning success → assert `gh pr create` NOT called, `gh pr edit` IS called.

### Milestone 4 — CI poll + auto-merge + cleanup

**Audit-Profile:** code-only
**Gate:** SOFT
**Mode:** AFK
**Critical-Path:** version-pipeline (release/merge mechanics — closes the loop that lands commits on main)

- **4.1** Stage G1 (Branch-protection pre-check) — inline bash. For GitHub: `gh api "repos/{owner}/{repo}" --jq '.allow_rebase_merge'`. If `false`, fall back to `--merge` strategy with a warning. For GitLab: `glab api "/projects/:id" --jq '.merge_method'` — if not `rebase_merge`, fall back to default `merge`. Avoids "rebase merging is disabled" runtime error.
- **4.2** Stage G2 (CI poll) — divergent code paths per CLI:
  - **GitHub:** `gh pr checks <pr-num> --watch --interval 30 --fail-fast`, wrapped in `timeout 900s ... ; RC=$?`. Translate exit code: `RC=0` → green; `RC=124` (timeout SIGTERM) → `STATUS: CI_TIMEOUT` + clean exit 0; `RC=8` → still pending after watch ended (shouldn't happen with `--watch` but guarded anyway); other → CI failure.
  - **GitLab:** `glab api /projects/:id/merge_requests/<iid>` polled every 30s via bash `while` loop with explicit `(( $(date +%s) - start < 900 ))` guard. Parse `.pipeline.status` field: `success` → green, `failed`/`canceled` → fail, `running`/`pending` → continue polling. No reliance on `glab ci status` (a TTY UI command without script-safe exit codes).
- **4.3** Stage G3 (Auto-merge on green) — divergent dispatch:
  - GitHub: `gh pr merge <pr-num> --rebase --delete-branch` (or `--merge` if rebase disabled per G1)
  - GitLab: `glab mr merge <iid> --rebase --remove-source-branch --yes` (or `glab mr merge --yes` if rebase disabled per G1)
- **4.4** On CI timeout or failure: exit cleanly with `STATUS: CI_TIMEOUT` (or `CI_FAILED — see <PR-URL>`). Print recovery commands: `gh pr merge <num> --auto --rebase` (for timeout) or `gh pr checks <num>` (for failure).
- **4.5** Stage G4 (Cleanup) — runs only on successful merge:
  1. `git checkout main` (branch is deleted; switching to main is safe)
  2. `git pull --ff-only origin main`
  3. `git fetch --prune` (clears stale remote-tracking ref for deleted branch)
  4. Print summary: feature branch name, commits merged, merge SHA, PR URL.
- **4.6** Bats test `tests/commands/sole-dev-merge/test_stage_g_poll.bats` — mock `gh pr checks --watch` to never return; wrap in 5s timeout for test speed; verify exit code 0 + `STATUS: CI_TIMEOUT` in stdout.
- **4.7** Bats test `tests/commands/sole-dev-merge/test_stage_g_merge.bats` — mock gh stub logging args; verify exactly one call with `pr merge --rebase --delete-branch`.

### Milestone 5 — Docs, ADR, doc-drift reconciliation, smoke test

**Audit-Profile:** docs-only
**Gate:** HARD
**Mode:** AFK
**Critical-Path:** doc-count-drift (M5 explicitly enumerates README/CHANGELOG/CLAUDE.md/SECURITY.md count updates and is the canonical Tier 6 surface)

- **5.1** Delete user-local `~/.claude/commands/sole-dev-merge.md` content (install.sh symlink replaces it). install.sh's `create_symlink` helper (lines 116-190 of `scripts/install.sh`) already backs up to `~/.claude/backups/aa-ma-forge-<ts>/` — rollback path lives in the backup, NOT in plugin git history.
- **5.2** Run `./scripts/install.sh --dry-run` to **verify** auto-discovery picks up the new command. **No install.sh edit needed** — `for f in claude-code/commands/*.md` (lines 257-260) handles it. Plan-v1's M5.2 "modify install.sh" was a phantom requirement, removed in v2.
- **5.3** Author `docs/adr/0008-sole-dev-merge-pr-workflow.md` — captures: why we replaced fast-merge with PR/MR; why command-only (no skill/lib pattern); 3-source security rationale; backward-compat strategy (migration banner).
- **5.4** Doc-drift reconciliation across 5 files (run in ONE commit to satisfy Tier 6 `Critical-Path: doc-count-drift`):
  - `SECURITY.md` lines 11-12: `10 command files` → `11`; `19 skills directories` → `19` (no skill added — pure command); add `sole-dev-merge` to inline command name list
  - `CLAUDE.md` lines 48-50: `commands/ 10 slash commands` → `11`; `skills/ 18 reusable procedures` → `19` (resolves pre-existing CLAUDE.md vs SECURITY.md drift — actual count via `ls claude-code/skills/` is 19)
  - `README.md`: add `/sole-dev-merge` to the user-facing command list (currently doesn't list it)
  - `CHANGELOG.md`: create `## Unreleased` section header (currently absent), add entry: `### Changed\n- **feat(sole-dev-merge):** replace fast-merge with PR/MR + 3-source review workflow (security-auditor + Bandit + ShellCheck). See docs/adr/0008-sole-dev-merge-pr-workflow.md.`
  - `docs/spec/aa-ma-quick-reference.md`: add `/sole-dev-merge — PR/MR-based merge workflow with review + auto-merge` to the commands section (create a "Commands" table if none exists)
- **5.5** Update `docs/lessons.md`: append note to L-007 marking it "Resolved structurally by sole-dev-merge-pr-workflow Step 1.3 scope-filter (commit SHA TBD)."
- **5.6** CI integration: append a `bats` step to `.github/workflows/security.yml` to run `bats tests/commands/sole-dev-merge/*.bats`. Without this, the 6 bats tests are local-only.
- **5.7** Migration banner: command markdown prints on first invocation post-symlink-swap: `NOTE: /sole-dev-merge has been updated to a PR/MR workflow. Old fast-merge path is retired. See docs/adr/0008-sole-dev-merge-pr-workflow.md.` Banner once per session, suppressed via `AA_MA_SUPPRESS_MIGRATION_BANNER=1`.
- **5.8** Smoke test `tests/commands/sole-dev-merge/test_smoke_e2e.bats` — end-to-end in a worktree (`git worktree add .worktrees/sdm-smoke main`):
  1. Plant a feature branch with: (a) an in-scope `ruff` violation, (b) an out-of-scope dirt file (touch `tests/codemem/dummy.py`), (c) a Bandit B602 in a changed file
  2. Run the full `/sole-dev-merge` command
  3. Assert: exit code 0; branch gone from `git branch -r`; `main` contains the rebased commits; in-scope auto-fix commit present; CRITICAL Bandit auto-fix commit present; out-of-scope dirt NOT present in any commit on main
  4. Cleanup: `git worktree remove .worktrees/sdm-smoke`
- **5.9** Run `Skill(doc-drift-detection)` — all tiers must pass before HARD gate close. M5.4 reconciles 5.4's hardcoded counts in the same commit.

## 3. Milestones with Measurable Goals

| # | Milestone | Goal | Audit-Profile | Gate | Mode | Critical-Path |
|---|-----------|------|--------------|------|------|---------------|
| M1 | Pre-flight + scope-aware checks | Bats #1 proves L-007 reversion works; bats #2 covers 4 abort branches | code-only | HARD | AFK | doc-count-drift |
| M2 | Review + security pass | 3 sources dispatched; severity contract honoured; CRITICAL auto-fix verified by planted bandit B602 | full | HARD | HITL | — |
| M3 | PR/MR creation | Dual-remote logic working; AI body generation deterministic via /tmp; idempotency verified by planted-PR test | full | HARD | HITL | external-api |
| M4 | CI poll + merge | Poll respects 15-min timeout (clean exit); rebase-merge dispatched; cleanup pulls main | code-only | SOFT | AFK | version-pipeline |
| M5 | Docs + ADR + drift + smoke + CI integration | doc-drift detector clean across all 5 docs; ADR-0008 lands; smoke E2E passes; bats step added to CI | docs-only | HARD | AFK | doc-count-drift |

## 4. Acceptance Criteria per Step (falsifiable)

- **1.2 pre-flight:** Given `git branch --show-current` returns `main`, the command exits with non-zero AND stdout contains exactly `ABORT: Cannot run /sole-dev-merge from main branch`.
- **1.3 scope-filter:** Given an in-scope `*.py` file with a lint error AND `tests/codemem/foo.py` untouched by the branch, after Stage B runs, `git diff tests/codemem/foo.py` produces zero bytes AND the in-scope file passes `ruff check`.
- **1.4 auto-fix commit:** If Stage B made in-scope changes, then `git log -1 --format=%s` equals `chore(scope): pre-PR auto-fixes` AND `git log -1 --format=%B | tail -3` matches regex `\[AA-MA Plan\]|\[ad-hoc\]`.
- **2.5 CRITICAL auto-fix:** Given a fixture file with `subprocess.run(cmd, shell=True)` (Bandit B602), after Stage D runs: `bandit -t B602 fixture.py 2>&1 | grep -c "Issue:"` returns 0 AND `git log -1 --format=%s` matches regex `^fix\(review\): apply CRITICAL bandit`.
- **2.5 HIGH/MEDIUM panel:** Given 5 HIGH findings in `/tmp/all-findings.md`, Stage D invokes a logged `AUQ_DISPATCH` event exactly twice (4-options max per panel, so ceil(5/4)=2). Given 0 HIGH findings, zero AUQ_DISPATCH events logged. (Test harness: `findings-triage` logs each dispatch as one line `AUQ_DISPATCH n_options=<N>` to `$AUQ_LOG`.)
- **3.1 remote detection:** Given `origin → github.com/foo/bar.git`, the variables resolve to `n_github=1, n_gitlab=0`. Given `origin → gitlab.com/x/y` + `github → github.com/a/b`, resolves to `n_github=1, n_gitlab=1`.
- **3.2 dual-remote prompt:** Given `n_github=1 AND n_gitlab=1`, `AskUserQuestion` is called with `options[0].label` matching `^GitLab` (default position) and an option matching `^GitHub` elsewhere. (Test harness logs args to `/tmp/auq_args.json`.)
- **3.3 AI body:** Given a 5-commit branch, `cat /tmp/sole-dev-merge-body-*.md | grep -cE '^[-*] '` returns `>=5`, AND `grep -q '^## Test plan$' /tmp/sole-dev-merge-body-*.md` returns 0. If AA-MA plan active: `grep -qE '^Plan context: /.+/\.claude/dev/active/.+/?$' /tmp/sole-dev-merge-body-*.md` returns 0.
- **3.4 PR idempotency (GitHub):** Given a planted prior PR exists for the branch, after Stage F runs: counter file `/tmp/gh_calls.log | grep -c 'pr create'` returns 0 AND `grep -c 'pr edit --body-file'` returns 1.
- **3.5 auth pre-flight:** Given mocked `gh auth status` returning non-zero, the command exits within 5 seconds with stdout containing `STATUS: AUTH_REQUIRED`.
- **4.1 branch-protection:** Given mocked `gh api repos/.../{}.allow_rebase_merge` returning `false`, the script's merge dispatch (test stub) uses `--merge` not `--rebase`.
- **4.2 timeout:** Given mocked `gh pr checks --watch` that never returns, with `timeout 5s` wrapper for test speed: the script exits 0 AND stdout contains `STATUS: CI_TIMEOUT`.
- **4.3 merge invocation:** Given green CI on a GitHub PR, `grep -c 'pr merge --rebase --delete-branch' /tmp/gh_calls.log` returns 1.
- **5.8 smoke:** Given a planted feature branch (3-defect), the workflow exits 0 AND `git branch -r | grep -c "origin/$BRANCH"` returns 0 AND `git log main --oneline | head -10 | grep -q "$PLANTED_FEAT_SUBJECT"` returns 0 AND the out-of-scope `tests/codemem/dummy.py` modification is absent from `git log main -p tests/codemem/dummy.py`.
- **5.9 doc-drift:** `bash scripts/doc-drift-detection-cli.sh` (or `Skill(doc-drift-detection)` driver) exits 0 for tiers 1, 2, 6, 7. Tier 3, 4, 5 are advisory.

## 5. Required Artefacts

**CREATE:**
- `claude-code/commands/sole-dev-merge.md` (new — replaces user-local file via install.sh auto-symlink)
- `tests/commands/sole-dev-merge/test_stage_a_preflight.bats`
- `tests/commands/sole-dev-merge/test_stage_b_scope.bats`
- `tests/commands/sole-dev-merge/test_stage_c_dispatch.bats`
- `tests/commands/sole-dev-merge/test_stage_d_triage.bats`
- `tests/commands/sole-dev-merge/test_stage_e_remote.bats`
- `tests/commands/sole-dev-merge/test_stage_f_idempotent.bats`
- `tests/commands/sole-dev-merge/test_stage_g_poll.bats`
- `tests/commands/sole-dev-merge/test_stage_g_merge.bats`
- `tests/commands/sole-dev-merge/test_smoke_e2e.bats`
- `tests/commands/sole-dev-merge/fixtures/` (containing planted-bandit, planted-PR mocks, etc.)
- `docs/adr/0008-sole-dev-merge-pr-workflow.md`

**MODIFY:**
- `README.md` (add `/sole-dev-merge` to user-facing command list)
- `CHANGELOG.md` (create `## Unreleased` header + entry)
- `CLAUDE.md` (lines 48-50: 10→11 commands; resolve 18→19 skills pre-existing drift)
- `SECURITY.md` (lines 11-12: 10→11 commands; 19 stays 19 since no skill added; add command name to inline list)
- `docs/spec/aa-ma-quick-reference.md` (add command row)
- `docs/lessons.md` (annotate L-007 as resolved)
- `.github/workflows/security.yml` (add bats step)

**DELETE / REPLACE:**
- `~/.claude/commands/sole-dev-merge.md` (user-local) — replaced by symlink to plugin version; install.sh auto-backs-up to `~/.claude/backups/aa-ma-forge-<ts>/`

**EXPLICITLY NOT MODIFIED (correcting v1 over-specification):**
- `scripts/install.sh` — auto-discovery handles new command and skill (no edit)
- `claude-code/skills/sole-dev-merge/` — entire skill directory dropped (no precedent for skill/lib pattern in repo)

## 6. Tests to Validate Each Milestone

- **M1:** `bats tests/commands/sole-dev-merge/test_stage_a_preflight.bats` + `test_stage_b_scope.bats` (≥ 2 bats files passing)
- **M2:** `bats tests/commands/sole-dev-merge/test_stage_c_dispatch.bats` + `test_stage_d_triage.bats` (≥ 2 bats files passing) + manual: planted Bandit B602 → verify auto-fix commit
- **M3:** `bats test_stage_e_remote.bats` + `test_stage_f_idempotent.bats` (≥ 2 bats files passing) + manual on aa-ma-forge (GitHub-only) + a Biorelate dual-remote project to confirm prompt
- **M4:** `bats test_stage_g_poll.bats` + `test_stage_g_merge.bats` (≥ 2 bats files passing) + manual: run against a real PR with quick CI (security.yml ~2 min)
- **M5:** `bats test_smoke_e2e.bats` + `Skill(doc-drift-detection)` reports clean for tiers 1, 2, 6, 7 + `./scripts/install.sh --dry-run` succeeds + ShellCheck on new command markdown's bash blocks (extracted via skill or `bash -n`) + ADR-0008 lands

## 7. Rollback Strategy

The user-local `~/.claude/commands/sole-dev-merge.md` is NOT in plugin git. install.sh's `create_symlink` helper backs it up to `~/.claude/backups/aa-ma-forge-<timestamp>/commands/sole-dev-merge.md` before replacing with a symlink.

1. **To rollback the user-local replacement:** `rm ~/.claude/commands/sole-dev-merge.md && cp ~/.claude/backups/aa-ma-forge-<ts>/commands/sole-dev-merge.md ~/.claude/commands/`
2. **To rollback the plugin changes:** `git revert <commit>..HEAD` covers all plan commits atomically. AA-MA artifacts record SHAs per milestone.
3. **Per-milestone rollback:** Each milestone's commits are tagged in `provenance.log`; revert only those if a single milestone misbehaves.
4. **Master kill switch:** `export AA_MA_HOOKS_DISABLE=1` disables all AA-MA gating, allowing direct commits to bypass the new workflow while diagnosing.

## 8. Dependencies and Assumptions

**Dependencies (all verified by ground-truth audit):**
- `gh` CLI v2.92.0+ (verified installed)
- `glab` CLI v1.80.4+ (verified installed)
- `ruff` (declared in `pyproject.toml`)
- `bandit` (will be added to dev-deps in M2.3 if not present — verify via `uv run bandit --version`)
- `shellcheck` (already in CI per `.github/workflows/security.yml`)
- `bats` (declared in CLAUDE.md: `sudo apt-get install -y bats`)
- `security-auditor` agent at `~/.claude/agents/security-auditor.md` (verified exists)
- `feature-dev:code-reviewer` agent (verified exists)
- `Skill(doc-drift-detection)` (verified exists)

**Assumptions:**
- User authenticated to `gh auth status` AND `glab auth status` — verified inline for snewhouse; M3.5 pre-flight guards mid-run expiry
- `main` is the default branch — verified (`git branch --show-current` baseline)
- Only one `/sole-dev-merge` invocation active per repo at a time (no concurrency lock — sole-dev assumption)
- Conventional Commits convention is honoured by branch commits (commitizen at release time; per-commit not enforced — Stage E3 title generation falls back gracefully if subject is non-conventional)
- `bandit` and `shellcheck` JSON output formats are stable (both v1.7+ / v0.9+ as of 2026-05)

## 9. Effort Estimate & Complexity (0-100%)

| Milestone | Estimate | Complexity | Notes |
|-----------|----------|------------|-------|
| M1 | 2 h | 45% | Inline bash + 2 bats tests; L-007 fix is the load-bearing piece |
| M2 | 3-4 h | 65% | 3-source security dispatch with severity contract; Agent tool prompt design needs care |
| M3 | 3 h | 60% | Dual-remote logic + idempotency + AI body gen via /tmp |
| M4 | 2 h | 50% | Polling with timeout + divergent gh/glab paths; branch-protection pre-check |
| M5 | 2-3 h | 45% | 6 docs to reconcile in 1 commit + ADR + smoke test + CI bats step |
| **Total** | **12-14 h** | **53% avg** | No step ≥ 80% → no Chain-of-Thought required |

## 10. Risks & Mitigations (Top 3 per Milestone)

### M1
1. **L-007 recurrence — format step still drifts out of scope.** Mitigation: bats test #1 specifically asserts no out-of-scope diff after Stage B; CI runs it on every push.
2. **Pre-commit hooks slow merges to >5 min.** Mitigation: skip when `.pre-commit-config.yaml` absent; document `--skip-pre-commit` flag for opt-out.
3. **`git diff main...HEAD` is empty on first commit / orphan branches.** Mitigation: Stage A explicitly checks `git rev-list --count main..HEAD > 0`.

### M2
1. **Agent ignores severity contract and emits free-form text.** Mitigation: parse with regex; on mismatch, classify all findings as `[HIGH]` (safe default — ask user about everything) AND log to provenance for follow-up. Plan does NOT auto-apply when contract is unmet.
2. **Bandit/ShellCheck "auto-fix" applies wrong fix and breaks tests.** Mitigation: after auto-fix commits, re-run lint + pytest. If they fail, revert the auto-fix commit AND demote the finding to HIGH (re-ask user).
3. **Token budget blown on >5000-LOC diffs.** Mitigation: cap agent input to top-20 files by lines changed; emit warning to user.

### M3
1. **Dual-remote prompt becomes annoying on every invocation.** Mitigation: read `.aa-ma/preferred-remote` config file at repo root if present; create on first prompt; honour silently thereafter.
2. **AI body hallucinates across many commits.** Mitigation: deterministic fallback (commit-list bullet body) if Haiku call fails or response unparseable; cap body at 500 tokens; include traceability footer.
3. **PR body leaks secrets from diff snippets.** Mitigation: AI prompt explicitly forbids inlining file contents (only filenames + commit subjects); pre-AI Bandit scan on diff content as belt-and-braces.

### M4
1. **CI status pending indefinitely (GitHub Actions queue stalled).** Mitigation: 15-min hard timeout via `timeout`; clean exit code 0 + `STATUS: CI_TIMEOUT`.
2. **Rebase merge fails due to mid-flight main update.** Mitigation: M4.1 pre-checks `allow_rebase_merge`; if rebase merge IS allowed, M4.3 first runs `gh pr update-branch` (best-effort — admin-only on protected branches, falls back to `git rebase origin/main && git push --force-with-lease`); retries merge once; second failure exits cleanly with diagnostic.
3. **No required checks configured — auto-merge waits forever.** Mitigation: detect zero required checks before polling; if so, merge immediately without poll.

### M5
1. **User mental model surprise — old fast-merge behaviour is gone.** Mitigation: migration banner on first invocation (M5.7); CHANGELOG entry under `## Unreleased`; ADR-0008 documents rationale.
2. **install.sh symlink overwrites user customization silently.** Mitigation: install.sh already backs up to `.bak.<ts>` (lines 116-190). M5.1 documents the backup path for recovery.
3. **Doc-drift detector flags stale counts post-M5.** Mitigation: M5.4 reconciles ALL 5 doc files in ONE commit (atomic Tier 6 fix); M5.9 runs the detector pre-gate close.

## 11. Next Action

**Step 1.1** — Create `claude-code/commands/sole-dev-merge.md` skeleton with frontmatter only (no stage logic yet). Update `[task]-tasks.md` to mark Step 1.1 IN_PROGRESS at the start.

**AA-MA file to update first:** `sole-dev-merge-pr-workflow-tasks.md` — mark Milestone 1 / Step 1.1 status to IN_PROGRESS once execution begins.

## 12. Engineering Standards Declaration

All 6 themes from `claude-code/rules/engineering-standards.md` materially apply.

| Theme | Applies | Rationale |
|-------|---------|-----------|
| 1. Verification & Truth | YES | `Critical-Path:` declared per milestone with canonical values: M1=doc-count-drift, M3=external-api, M4=version-pipeline, M5=doc-count-drift. Each Critical-Path-bearing milestone must write a `[ts] CRITICAL_PATH_REVIEW — <evidence>` entry to provenance.log before COMPLETE. Empirical validation required for M3 (gh/glab CLI contract surface) and M4 (auto-merge → main state). No `Prototype-Required:` declared — work has clear deterministic outputs throughout. |
| 2. Development Principles | YES | TDD enforced — bats tests precede each stage's implementation (8 named bats files). KISS — command-only (no skill/lib novel pattern). DRY — no duplication; each stage block is self-contained. SOLID/SOC — each stage A-G is one reason to change (preflight, scope, review, security, remote, push/create, poll/merge). |
| 3. Reasoning & Planning | YES | Brainstorm done via 5 rounds of AskUserQuestion (12+ alternatives weighed); skill assessment recorded per milestone (M2 dispatches 4 sources; M3 uses Haiku-class for body gen; M4 uses bash directly). v2 revision reflects adversarial verification feedback. |
| 4. Safety & Continuity | YES | L-007 directly applies and is structurally fixed in M1.3 (scope-filter). Non-breaking: pre-existing PRs/branches keep flowing; only the merge ceremony changes for new invocations. Incremental validation: each milestone independently testable AND revertable. Lessons-aware: L-007 annotated as resolved in M5.5. |
| 5. Execution Checklist | YES | Per-milestone HARD/SOFT gates declared (M1, M2, M3, M5 = HARD; M4 = SOFT). `Audit-Profile:` declared per milestone with canonical values: M1=code-only, M2=full, M3=full, M4=code-only, M5=docs-only. M1/M3/M4/M5 Critical-Path requires CRITICAL_PATH_REVIEW provenance entries pre-COMPLETE. |
| 6. Sync & Commit Discipline | YES | Plugin code → AA-MA signature `[AA-MA Plan] sole-dev-merge-pr-workflow .claude/dev/active/sole-dev-merge-pr-workflow` mandatory on every commit. Sub-step Result Log discipline (L-080/081/082) applies. Conventional Commits enforced. Atomic commit per logical change (Stage-B chore vs Stage-D fix vs M5 docs reconciliation each get their own commits). |

---

_End of plan v2. Generated by `/aa-ma-plan` workflow 2026-05-18. Slug: sole-dev-merge-ci-pr-20260518105415. Verification: 17 CRITICAL findings from v1 addressed; see verification.md v2 entry for verification of revision._
