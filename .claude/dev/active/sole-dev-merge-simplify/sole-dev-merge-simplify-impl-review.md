# Impl Review Report: sole-dev-merge-simplify / Milestone 1

**Milestone:** Milestone 1: sdm.sh beside the old skill, proven live · **Audit-Profile:** full · **Window:** `6ad8ad38..05718b5d` (fix: `49143045`, `e70f156f`) · **Date:** 2026-10-22
**Exit contract (plan §3):** one run; a CRITICAL with a failure path under the threat model is fixed and the fix alone re-checked once; WARNING/INFO go to TODOS ("sdm.sh M1 §6.8 review notes").

## Summary
| Agent | CRITICAL | WARNING | INFO | Verdict |
|---|:-:|:-:|:-:|---|
| code-reviewer | 1 | 11 | 4 | CRITICAL accepted → fixed |
| security-auditor | 0 | 2 | 5 | PASS |
| tdd-sequence-auditor | 0 | 0 | 1 | PASS |
| context7-evidence-auditor | 0 | 0 | 0 | PASS |
| future-proofing-auditor | 0 | 1 | 5 | PASS |
| **Total** | **1** | **14** | **15** | **PASS_WITH_WARNINGS** after the fix |

## Code Review (code-reviewer agent)
### Findings
- **[CRITICAL] correctness:** `sdm.sh:87,89` — `ruff format` / `ruff check --fix` without `--force-exclude` ignore pyproject `extend-exclude` for named files. Verified live: `ruff check --diff -- tests/fixtures/evals/py-logging/runner.py` strips the planted `# noqa: S603`; `check` would auto-commit it (ADR-0021). Inherited from the old Stage B. **Fixed:** RED `49143045` (check.bats "a ruff-excluded .py the branch touches is left byte-identical"), GREEN `e70f156f`; 148/148.
- WARNING (→ TODOS):
  - a rejected `git push` (:143) or a git-hook-refused auto-fix commit (:114) exits 1 with no `ABORT:` line;
  - worktree cleanup `fetch` (:257) / `rev-parse --short` (:275) unguarded after a successful merge;
  - `gh pr checks` re-read `|| true` (:183) without `# why:`; a failed re-read reports green (finish re-checks);
  - re-ship race: GitHub's `headRefOid` may lag the push → `reason=not-this-branch` (:151);
  - `--notes` with a missing path silently becomes `(none)` (:138);
  - the PR title is the HEAD subject, so after an auto-fix commit it is `chore(scope): pre-PR auto-fixes` (:161; the old skill had a `PR_TITLE` override);
  - pre-commit `./` prefix stops anchored `files:`/`exclude:` patterns from matching (:96; ported from SKILL.md:282);
  - magic numbers `70`, `timeout 30`, `--interval 30`, `per_page=100`;
  - fallback defaults `120`/`10` repeated (DRY);
  - read-back `<(cat "$BODY"; echo)` lacks its `# why:`; reference.md:44 says "trims trailing newlines", the code adds one.
- INFO: stamps and the old test's grep are outside the M1 Files list (recorded in 1.2); sdm.sh and the old blocks coexist (planned); `CI_POLL_TIMEOUT` unvalidated; `cut -c1-70` cuts bytes.

## Security (security-auditor agent)
### Mechanical pre-check (security-static-check.sh): PASS (no `[security-bypass]` in the window)
### Semantic findings
- LOW: `sdm_slug` strips the userinfo at the first `@`, git at the last — a raw `@` in the operator's password leaks its tail into the ABORT line (:54/58).
- LOW: `CI_POLL_TIMEOUT` unvalidated: `0` disables the watch timeout, a non-duration gives rc 125 → `CI_FAILED` (finish re-checks).
- INFO: `total_count` in `[[ -eq ]]` (:213) is bash-arithmetic on API output (always an integer); slug regex admits `..`; footer helper sourced from the working tree (same trust as pre-commit); `pr checks` column parse could shift on a tab in a check name (finish gates on the API); `AA_MA_PLAN_DIR` published verbatim.
- Clean: no credential printing; untrusted gh fields gated (fork, head name, head oid); `--match-head-commit` + lease; option-shaped names refused; tests cannot reach GitHub.

## TDD Sequence (tdd-sequence-auditor agent)
### Verdict: PASS
### Evidence
- RED `2c3e2c86` (2026-10-20T15:13:54) adds tests; sdm.sh absent there (`git ls-tree` empty). GREEN `1cd01f0d` (15:23:21) adds sdm.sh. Fix pair: RED `49143045` → GREEN `e70f156f`.
### Per-file pairing (informational only)
- sdm.sh ↔ tests/commands/sdm/{check,ship,finish}.bats. INFO: the GREEN commit also edits `test_stage_state.bats` (+2/−1, scope fix recorded in 1.2).

## External Library Evidence (context7-evidence-auditor agent)
### New PyPI dependencies in milestone diff
- None.
### Major version bumps in milestone diff
- None. gh/git contracts: `docs/research/sole-dev-merge-simplify-gh-cli-merge-contract.md`, probed live (PL, reference.md "Prototype facts").

## Future-Proofing (future-proofing-auditor agent)
### Findings
- WARNING: fallback defaults `120`/`10` written three times each (:9-10, :172, :174).
- INFO: `timeout 30` vs `--interval 30`; `cut -c1-70`; `per_page=100` (guarded); `124`/`2` exit codes uncommented; ~147 test titles cite old-suite `file:line` that M2 deletes (state the port base once per file header).

## User Override Decisions
| # | Finding | Decision | By | Date |
|---|---|---|---|---|
| 1 | [CRITICAL] ruff without `--force-exclude` (sdm.sh:87,89) | Accept — fixed now (`49143045`, `e70f156f`) | Ste | 2026-10-22 |

## Revision History
- 2026-10-22: run 1 (5 agents); CRITICAL fixed (`49143045`, `e70f156f`); fix re-check (code-reviewer, fix only): 0 CRITICAL, 0 WARNING, 1 INFO — both ruff calls fixed, in-scope formatting intact, test fails with the flags removed.
