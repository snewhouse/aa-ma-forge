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
- 2026-10-22: merge run 2 proved the code-reviewer WARNING at `sdm.sh:151` live (GitHub's headRefOid lagged a re-push → `reason=not-this-branch`); Ste: fix now → RED `1e0b52d2`, GREEN `ae90cd2b` (re-read within the appear-wait caps, `reason=head-not-updated`); fix re-check 0C/0H/1M/4L → TODOS. That WARNING is fixed.
- 2026-10-22: run 1 (5 agents); CRITICAL fixed (`49143045`, `e70f156f`); fix re-check (code-reviewer, fix only): 0 CRITICAL, 0 WARNING, 1 INFO — both ruff calls fixed, in-scope formatting intact, test fails with the flags removed.

---

# Impl Review Report: sole-dev-merge-simplify / Milestone 2

**Milestone:** Milestone 2: switch over and delete · **Audit-Profile:** full · **Window:** `0efa790c..61423024` (switch commit `befb8bf6`) · **Date:** 2026-10-22
**Exit contract (plan §3):** one run; only a CRITICAL with a failure path blocks; WARNING/INFO go to TODOS. **Ste's decision (2026-10-22):** fix the SKILL.md wrong instructions, the two stale hook comments, and add a drift test tying SKILL.md's STATUS/reason/default tokens to `sdm.sh` (RED first); everything else to TODOS. No re-run (no CRITICAL).

## Summary
| Agent | CRITICAL | WARNING | INFO | Verdict |
|---|:-:|:-:|:-:|---|
| code-reviewer | 0 | 6 | 4 | PASS_WITH_WARNINGS |
| security-auditor | 0 | 1 | 3 | PASS_WITH_WARNINGS |
| tdd-sequence-auditor | 0 | 0 | 1 | PASS (RED `18e277c2` 15:56 before switch `befb8bf6` 16:03) |
| context7-evidence-auditor | 0 | 0 | 3 | PASS (no PyPI change; gh 2.46 research cited) |
| future-proofing-auditor | 0 | 3 | 5 | PASS_WITH_WARNINGS |
| **Total** | **0** | **10** | **16** | **PASS_WITH_WARNINGS** |

## Code Review (code-reviewer agent)
- WARNING wrong-instruction: SKILL.md BRANCH_NOT_DELETED row — in a plain checkout `finish` has already deleted the local branch and then prints `STATUS: OK`, so "re-run from the feature branch" is impossible and "STATUS: OK ends the run" hides the earlier line. **Fix now.**
- WARNING wrong-instruction: SKILL.md MERGE_FAILED row — "push and run ship again" after the remote head moved; no force-push ban; conflicts not covered. **Fix now.**
- WARNING drift: SKILL.md copies 9 STATUS names, 6 reasons, 3 env defaults and the footer order with no test tying them to `sdm.sh` (L-062 risk); `~/.claude` vs `${CLAUDE_HOME:-$HOME/.claude}`. **Fix now (drift test).**
- WARNING stale comments: `aa-ma-commit-signature.sh:22-25,167-169` still describe the deleted footer-resolve snippet; rule 8 now has no shipped user. **Comments fixed now; retiring rule 8 → TODOS.**
- WARNING scope: comment edits in `tests/commands/sdm/*.bats` headers and `tests/codemem/test_plugin_surface.py:99` are outside the Contract list. → recorded in context-log (deviation, justified).
- WARNING skill-gap: SKILL.md does not say what `check: pre-commit rc=<n>` non-zero means. **Fix now.**
- INFO: docs/architecture stamps by regen; measure.py deferral accepted; "Exit 1 prints one ABORT line" — a `set -e` exit can print none (**fix now**, with the rc gap); push/merge regex is shape-only.

## Security (security-auditor agent)
### Mechanical pre-check: PASS (no `[security-bypass]` in the window)
- WARNING A09: the notes file is published as the PR body; SKILL.md does not forbid quoting a secret value. **Fix now.**
- INFO A08 (out of scope): the branch's own `sdm.sh check` runs before review inside aa-ma-forge; sole-dev model only.
- INFO A04 (accepted, ADR-0024): check-runs only, no commit statuses; closing keywords.
- INFO A05: "no hand-made merges" does not name `gh api …/merge` or `git push origin :<b>`. **Fix now** (re-word as "no merge or delete outside sdm.sh").
- Verified: no lost security coverage from the deleted suite (the sdm suite covers the check-runs gate, cross-repo refusal, head-oid match, lease, URL/token never printed, control chars, option-shaped names); CI covers AD-003 (touched job ruff incl. S via pyproject, ruff-security, shellcheck).

## TDD Sequence (tdd-sequence-auditor agent)
### Verdict: PASS
- First test commit `18e277c2` (2026-10-22T15:56:07) precedes first implementation commit `befb8bf6` (16:03:23); RED failed on the 491-line SKILL.md (0 `sdm.sh` mentions); 6 failed / 1 passed per the 2.1 Result Log.

## External Library Evidence (context7-evidence-auditor agent)
- No `pyproject.toml`/`uv.lock` change in the window; the gh 2.46 contract is source-researched (`docs/research/sole-dev-merge-simplify-gh-cli-merge-contract.md`), valid while gh stays 2.46.0.

## Future-Proofing (future-proofing-auditor agent)
- WARNING restated defaults (SKILL.md Settings) and WARNING exit-table copy the guard misses (rows start with `|`) and WARNING quoted script output — **covered by the drift test now.**
- INFO: test names repeat the constants (`test_at_most_150_lines`) — **rename now**; ADR-0024 "167 tests" unqualified at line 80 — **qualify now**; TODOS measure.py "20 errors" → **give the command now**; dated counts in ADR/CHANGELOG/lessons are historical (keep).

## User Override Decisions
| # | Finding | Severity | Decision |
|---|---|---|---|
| — | none CRITICAL | — | Ste: fix text + drift test (2026-10-22) |

## Revision History
- 2026-10-22: M2 §6.8 run once; PASS_WITH_WARNINGS.
