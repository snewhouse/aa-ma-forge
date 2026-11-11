# 0024. `/sole-dev-merge` Is One Tested Script, GitHub Only

**Status:** Accepted
**Date:** 2026-10-22
**Deciders:** Ste
**Tags:** `skill`, `merge`, `testing`, `simplification`
**Supersedes (in part):** [ADR-0008](0008-sole-dev-merge-pr-workflow.md) — its stage-block implementation, the stage state file, GitLab support and the local scanner pass. ADR-0008's goals (a CI gate, review before merge, idempotent PR handling, worktree-safe cleanup) stand.

## Context and Problem Statement

`/sole-dev-merge` grew to 1,994 lines of markdown, 77% of it bash in fenced stage blocks that
the model copied into separate Bash calls. Values crossed calls through a stage state file,
whose loader existed in 13 copies kept identical by a test (L-062). Across two plans, 17 review
rounds produced 255 findings, none of which bit in real use, while running the skill found every
real bug (L-061). How do we keep the workflow's guarantees with code that can be tested as code?

## Decision Drivers

- The merge path must be testable end to end without GitHub (bats, local bare forge, gh stub).
- Each visible side effect (push, merge, branch delete) stays its own Bash call.
- One copy of each rule; no state file between model-run blocks (L-055, L-062).
- Review effort must end: a fixed round cap and a severity bar (L-060).

## Considered Options

1. **One bash script, `scripts/sdm.sh` (`check` / `ship` / `finish` / `help`)**, bats-tested; SKILL.md calls it.
2. **A Python CLI** — the work is git/gh orchestration; bash needs no venv.
3. **Trim the stage blocks** in place — keeps the state file and the copies.
4. **`gh pr merge --auto`** — with no branch protection it merges at once, without CI.

## Decision Outcome

**Chosen:** Option 1 (sole-dev-merge-simplify, decisions AD-001–AD-008 in its context-log).

- `sdm.sh` holds all the code and the exit table (`sdm.sh help`); SKILL.md (≤ 150 lines,
  `tests/skills/test_sole_dev_merge_skill.py`) says when to run each subcommand and what to do
  with its output.
- **GitHub only** (AD-002). GitLab/glab support is removed; the last release with it is v0.17.0.
- **No local Ruff S or ShellCheck pass** (AD-003): CI gates them — ShellCheck over every `.sh`,
  Ruff S (`ruff-security`) over `src/`, `packages/` and `scripts/`, and the `touched` job runs the
  pre-commit hooks over the PR's files. `check` still runs those pre-commit hooks locally on the
  branch's files.
- **No local pytest or mypy** (AD-004); pre-commit stays best-effort on changed files.
- **`check` stops on out-of-scope changes and names them; it never restores** (AD-006).
- **Two reviewers and the stop rule stay as SKILL.md steps** (AD-008): C1 code-reviewer, C2
  security-auditor, at most 2 rounds, only CRITICAL/HIGH with a failure path block.
- The migration banner for the retired fast-merge command is gone with the stage blocks.

**Proof:** M1 merged three real PRs with the script (#53, #56, #55), and the pre-M2 fix PR #57
merged itself in one run. The suite is `tests/commands/sdm/` (167 tests at the switch), run by
the CI bats job.

## Pros and Cons of the Options

### Option 1 — one script

- ✅ Each rule exists once; a fix touches one file and its test.
- ✅ bats runs every path against a local forge; no test reaches GitHub (L-058).
- ✅ Stdout carries only result, `STATUS:` and `ABORT:` lines, so the model acts on a contract.
- ❌ `sdm.sh` runs `git push` and `gh pr merge` inside one Bash call, so the permission prompt
  shows `sdm.sh ship`, not the push. Mitigation: SKILL.md names each side effect and runs the
  three subcommands as separate calls.

### Option 2 — Python CLI

- ✅ Richer tests.
- ❌ A venv on every machine that merges; the logic is shell orchestration anyway.

### Option 3 — trim the blocks

- ✅ Smallest change.
- ❌ Keeps the state file, the copies and the review surface that never converged.

### Option 4 — `gh pr merge --auto`

- ❌ Merges without CI on a repo with no branch protection (gh 2.46 contract research).

## Consequences

**Positive:** SKILL.md 491 → 130 lines; the old suite (199 tests) is replaced by the script's own suite (167 tests at the switch); GitLab code paths that this repo never ran are gone (L-057).

**Accepted risks:**
- A GitHub closing keyword (`Closes #N`) in model-written reviewer notes would close an issue on
  merge. SKILL.md tells the model not to write one; nothing enforces it.
- `finish` gates on check-runs only; commit statuses are not read (this repo's CI reports
  check-runs only).

**Neutral:** ADR-0022's "Ruff S in Stage C" and ADR-0018's Stage B example now describe history;
both carry an amendment note pointing here.

## References

- Plan: `.claude/dev/completed/sole-dev-merge-simplify/` (plan, context-log AD-001–AD-012, impl-review).
- Research: `docs/research/sole-dev-merge-simplify-gh-cli-merge-contract.md`, `docs/research/sole-dev-merge-simplify-behaviour-inventory.md`.
- Lessons: L-055, L-058, L-060, L-061, L-062.
