# 0008. `/sole-dev-merge` — PR/MR Workflow with 3-Source Security + Idempotent Auto-Merge

**Status:** Implemented
**Date:** 2026-05-18
**Deciders:** Stephen Newhouse + AI
**Tags:** `command`, `pr-mr`, `security`, `idempotency`, `auto-merge`, `backward-compat`

## Context and Problem Statement

The legacy user-local `/sole-dev-merge` (lived at `~/.claude/commands/sole-dev-merge.md`,
not in plugin git) was a "fast-merge" workflow: switch to main, fast-forward
merge the feature branch, push. It had three persistent flaws:

1. **No CI gate** — commits could land on main without ever passing the test
   suite. Bypassed `.github/workflows/security.yml` by design.
2. **No code review** — neither a human nor an automated reviewer touched the
   diff before it became immutable on main.
3. **Scope-discipline drift (L-007)** — the format step (`ruff format src/ tests/`)
   ran whole-tree, dirtying 29 pre-existing test files outside the branch's
   intended scope. Out-of-scope drift then became part of the merge.

A sole-developer workflow MUST gate merges through CI and a review surface to
prevent broken/insecure code from landing, but should NOT require ceremony
that defeats the "sole developer" ergonomics (no second pair of eyes
mandatory, no manual approval click).

**Question:** How do we replace the fast-merge workflow with one that gates
on CI + automated review + automated security checks, while preserving
single-developer ergonomics and respecting the existing AA-MA plan/commit
discipline?

## Decision Drivers

- **CI must run before merge.** The 15-minute `gh pr checks --watch` is the
  workflow's load-bearing trust anchor. No merge unless required checks pass.
- **3-source security pass.** A single source (e.g., just Bandit, just an
  agent) creates a single point of failure. Combining `code-reviewer` agent +
  `security-auditor` agent + Bandit + ShellCheck triangulates findings; one
  source missing a finding is caught by another.
- **Idempotency on retry.** A workflow that creates duplicate PRs on every
  re-run is unusable. `gh pr view` detection + `gh pr edit` reuse means the
  command is safe to re-run on the same branch (operator typo, mid-flight
  interruption, retry-after-fix).
- **Scope discipline structural fix (L-007).** Format whole-tree was the root
  cause; the fix MUST operate on the changed-files set only. Belt-and-braces:
  L-007 guard re-runs `git status --porcelain` post-mutation and `git checkout
  --` reverts any out-of-scope drift.
- **Backward compatibility.** Users who already had the old fast-merge
  `/sole-dev-merge` should NOT lose their command — `scripts/install.sh`
  auto-backs-up to `~/.claude/backups/aa-ma-forge-<ts>/` before symlinking
  the new version. A migration banner alerts the operator on first
  invocation post-deploy.
- **Hook compatibility.** All Stage commits must honour the
  `aa-ma-commit-signature.sh` PreToolUse hook footer requirement. Stage F's
  auto-fix commits use the shared `aa-ma-footer.sh` helper.
- **No skill-with-lib pattern in repo precedent.** The previous v1 plan
  proposed `claude-code/skills/sole-dev-merge/` with library code; no
  existing AA-MA skill in the repo follows this pattern. Plan v2 dropped
  the skill entirely in favour of a command-only design.

## Considered Alternatives

### Alternative 1 — Keep fast-merge, add post-merge linting on main

**Rejected.** Post-merge linting can't prevent broken code from landing on
main; it can only revert. Reverts are noisy and destroy commit history. CI
must be the gate, not a post-hoc audit.

### Alternative 2 — Manual PR creation with `gh pr create` plus a docs note

**Rejected.** Three-source security pass (code review + security-auditor +
Bandit + ShellCheck) cannot be invoked manually each time without drift.
Auto-dispatching the four sources with a unified severity contract is the
load-bearing differentiator vs `gh pr create` alone.

### Alternative 3 — Command + skill + lib pattern (plan v1)

**Rejected.** No existing AA-MA skill in the repo splits logic across
`commands/X.md` + `skills/X/` + Python library. Plan-verification flagged
this as L-005 mechanism-duplication risk (six unverified library functions
that didn't exist). Plan v2 collapsed to a command-only design — all logic
in bash blocks inside the command markdown, with stage extraction for tests.

### Alternative 4 — Single-source review (code-reviewer agent only)

**Rejected.** Single-agent reviews routinely miss security-specific patterns
(B602 shell-injection, ShellCheck SC2086 word-splitting). The 3-source
triangulation closes the single-point-of-failure gap. Per L-052: "When the
same CLASS of issue appears in 2+ independent QA reviews, treat it as
architectural deficiency" — 3 sources from different perspectives is the
architectural response.

## Decision

Replace the legacy fast-merge `/sole-dev-merge` with a command-only PR/MR
workflow living at `claude-code/commands/sole-dev-merge.md`. The new command
is a single markdown file containing 9 stage bash blocks executed in order:

| Stage | Block | Purpose |
|-------|-------|---------|
| A | `stage-a-preflight` | 4 abort conditions: on-main, dirty, no-remote, no-commits-ahead |
| B | `stage-b-scope` | In-scope ruff/mypy/pytest + L-007 guard (porcelain walk + reversion) |
| B-commit | `stage-b-commit` | Auto-fix commit if Stage B mutated tracked files |
| C | `stage-c-aggregate` | Parallel dispatch of 4 sources (code-reviewer + security-auditor agents, Bandit, ShellCheck); unified severity contract |
| D | `stage-d-triage` | Auto-fix CRITICAL Bandit B602; HITL panel for HIGH/MEDIUM (Claude executor) |
| E1 | `stage-e1-remote` | `git remote -v` classification → `n_github` / `n_gitlab` / `n_other` |
| E2 | `stage-e2-choice` | Single → use it; dual → AUQ bridge with GitLab default; neither → abort |
| E0 | `stage-e0-auth` | `gh`/`glab auth status` for chosen remote → `STATUS: AUTH_REQUIRED` on failure |
| E3 | `stage-e3-body` | Deterministic PR/MR body generator + optional Haiku enrichment |
| F | `stage-f-push` | `git push` + idempotent PR/MR detection via `gh pr view`/`glab mr view` + create-or-edit |
| G1 | `stage-g1-protect` | Branch-protection: `--rebase` fallback to `--merge` when disabled |
| G2 | `stage-g2-poll` | 15-min CI poll (GitHub `--watch`, GitLab JSON `while`) → `CI_STATE` |
| G3 | `stage-g3-merge` | Green CI → merge; timeout/failed → `STATUS:` line + remote-aware recovery hint |
| G4 | `stage-g4-cleanup` | Post-merge: checkout main, fast-forward pull, fetch --prune, summary |

**Test harness** uses `extract_stage.sh` (fixed-string `awk index()` extract)
to pull each stage's bash into an isolated executable for `bats` testing.
PATH-shadowed `gh`/`glab` stubs at `tests/commands/sole-dev-merge/fixtures/bin/`
log every invocation to `$CLI_LOG`; behaviour is env-controlled (`GH_PR_EXISTS`,
`GLAB_MR_EXISTS`, `GH_WATCH_HANG`, `GH_CHECKS_RC`, `GH_ALLOW_REBASE`,
`GH_AUTH_OK`, `GLAB_AUTH_OK`, `GLAB_API_MODE`, `GLAB_PIPELINE_STATUS`,
`GLAB_MERGE_METHOD`, `GLAB_MR_EXISTS`).

**Migration strategy:** `scripts/install.sh` `create_symlink` helper
auto-backs up the legacy user-local `~/.claude/commands/sole-dev-merge.md`
to `~/.claude/backups/aa-ma-forge-<timestamp>/commands/sole-dev-merge.md`
before replacing it with a symlink to the new plugin-shipped version.
**Migration banner** at the top of the command markdown alerts the operator
on first invocation post-deploy; `AA_MA_SUPPRESS_MIGRATION_BANNER=1`
suppresses it.

## Consequences

### Positive

- **CI gate is non-bypassable** — merges to main go through `gh pr merge`,
  which requires required checks to pass. No way to bypass without
  manually editing the PR's required-status-checks configuration.
- **3-source security triangulation** — single source missing a finding is
  caught by another. Empirical: 4 sources → max coverage.
- **Idempotency on retry** — `gh pr view --json url` detection means
  re-running `/sole-dev-merge` after a failure updates the existing PR
  rather than creating a duplicate.
- **L-007 fix is structural, not procedural** — Stage B's porcelain walk +
  `git checkout --` reversion of out-of-scope drift means the format-step
  side effect that triggered L-007 cannot escape the branch.
- **Auto-merge with timeout** — `timeout 900s gh pr checks --watch`
  translates RC=124 to clean exit + `STATUS: CI_TIMEOUT` with recovery
  hint (`gh pr merge --auto --rebase`), letting the user re-trigger merge
  out-of-band when CI exceeds 15 minutes.
- **Remote-aware** — single-github, single-gitlab, and dual-remote cases
  all handled; GitLab default per project convention; AUQ bridge logs
  args for the Claude executor to dispatch real `AskUserQuestion`.
- **Backward-compatible install** — `scripts/install.sh` auto-discovers
  via `for f in claude-code/commands/*.md` (lines 257-260); zero edit
  required. Legacy user-local file is backed up before being replaced.

### Negative

- **15-min auto-poll requires unattended trust.** Operator must trust the
  `gh pr checks --watch` to fail-fast on first required-check failure.
  If a required check is mis-configured (e.g., flaky test passes
  intermittently), the 15-min poll could either succeed-with-broken-code
  or timeout-on-correct-code. Mitigation: `gh pr merge --auto --rebase`
  recovery command for the timeout case keeps the merge in the queue
  rather than abandoning it.
- **3-source dispatch adds latency.** Stage C dispatches code-reviewer +
  security-auditor agents in parallel via Claude Code's parallel-Agent
  pattern; latency dominated by the slower agent. Typical: 30-60s.
  Mitigation: parallel dispatch in a single Claude turn message.
- **Auth TOCTOU window.** Stage E0 verifies `gh auth status` once; Stage G3
  invokes `gh pr merge` 15+ minutes later. Token expiry between is loud
  (`set -euo pipefail` propagates non-zero rc) but does NOT re-emit
  `STATUS: AUTH_REQUIRED`. Tracked as M5 hardening backlog item per
  §6.8 audit MED-4.
- **Stage C/D dispatch requires Claude Code session.** Bats can mock
  `MOCK_AGENT_DISPATCH=1` via fixture files but cannot invoke real
  agents; smoke E2E test exercises stage chaining with mocks rather
  than a full live run.

### Neutral

- **Command-only design** (no skill, no lib) keeps the surface to one file
  (`sole-dev-merge.md`) + one directory (`tests/commands/sole-dev-merge/`).
  This matches repo precedent (no AA-MA skill ships library code) but
  diverges from richer command frameworks elsewhere.
- **Conventional Commits** title derivation (topmost commit subject,
  truncated to 70 chars) — works for the ASCII-Conventional-Commit common
  case; CJK / RTL multi-byte truncation tracked as backlog (`PR_TITLE:0:70`
  is byte-based).

## Reversibility / Migration Plan

**Reversible** at three levels:

1. **User-local rollback (per-user):**
   ```bash
   rm ~/.claude/commands/sole-dev-merge.md
   cp ~/.claude/backups/aa-ma-forge-<ts>/commands/sole-dev-merge.md \
      ~/.claude/commands/
   ```
2. **Plugin git rollback:** `git revert <commit>..HEAD` covers all 5 milestone
   commits atomically. AA-MA artifacts record each milestone's commit
   window in `provenance.log`.
3. **Master kill switch:** `export AA_MA_HOOKS_DISABLE=1` disables all
   aa-ma gating, allowing operators to bypass the new workflow entirely
   while diagnosing.

If the new workflow proves problematic, individual stages can be temporarily
short-circuited via env vars (`CI_POLL_TIMEOUT=0s`, `MOCK_AGENT_DISPATCH=1`,
`AA_MA_SUPPRESS_MIGRATION_BANNER=1`) without reverting the plugin.

## Validation

Empirically validated by 69 bats tests across 10 files
(`tests/commands/sole-dev-merge/`) covering every stage's canonical AC
across all 5 milestones. Verify via `grep -cE '^@test'
tests/commands/sole-dev-merge/*.bats` (the canonical source-of-truth):

- **M1:** test_stage_a_preflight.bats (6) + test_stage_b_scope.bats (4)
- **M2:** test_stage_c_dispatch.bats (5) + test_stage_d_triage.bats (4)
- **M3:** test_stage_e_remote.bats (8) + test_stage_e3_body.bats (9) +
  test_stage_f_idempotent.bats (11)
- **M4:** test_stage_g_poll.bats (7) + test_stage_g_merge.bats (11)
- **M5:** test_smoke_e2e.bats (4 — banner + chained-stage smoke)

Plus ShellCheck on all 15 stage bash markers (8 top-level stages A–G;
G splits into G1/G2/G3/G4 sub-stages; banner runs before A) — all clean,
pytest regression (0 failures across 782 tests), and 5-agent §6.8
post-impl audit at each milestone close.

## References

- Plan: `.claude/dev/completed/sole-dev-merge-pr-workflow/sole-dev-merge-pr-workflow-plan.md`
- Reference: `.claude/dev/completed/sole-dev-merge-pr-workflow/sole-dev-merge-pr-workflow-reference.md`
- Implementation review: `.claude/dev/completed/sole-dev-merge-pr-workflow/sole-dev-merge-pr-workflow-impl-review.md`
- Lessons: L-005, L-006, L-007, L-052, L-080-L-083 in `docs/lessons.md`
- Related ADRs: ADR-0001 (engineering standards), ADR-0005 (§6.8 post-impl review),
  ADR-0007 (TUI tracker)

---

*Editorial note (2026-08-09): employer/product names genericized post-departure. Technical rationale unchanged.*
