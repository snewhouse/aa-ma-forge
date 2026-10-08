# Impl Review Report: code-conventions-impact / Milestone 1

**Milestone:** Milestone 1: Touched-files lint harness + baseline
**Audit-Profile:** full · **Budget:** normal (parallel, 5 agents) · **Date:** 2026-10-08
**Window:** `9ed9b18..3edcec6` (effective milestone base `4ccf14f`; see code-reviewer W1)

## Summary

| Agent                     | CRITICAL | WARNING | INFO | Verdict |
|---------------------------|:--------:|:-------:|:----:|---------|
| code-reviewer (+ §6.6 reuse/quality/efficiency) | 0 | 2 | 6 | WARN |
| security-auditor          | 0 | 0 | 2 | PASS |
| tdd-sequence-auditor      | 0 | 0 | 2 | PASS |
| context7-evidence-auditor | 0 | 0 | 2 | PASS |
| future-proofing-auditor   | 0 | 0 | 5 | PASS |
| **TOTAL**                 | **0** | **2** | **17** | **PASS_WITH_WARNINGS** |

§6.6 (post-milestone simplification review) was folded into the code-reviewer pass so the
session stays within `/rigor`'s 5-concurrent-agent cap.

## Code Review (code-reviewer agent)

### Findings

- **W1 [scope]** `docs/lessons.md:18,29` — commit `4ccf14f` (`[ad-hoc]` lessons cross-refs) sits in the
  window because the base was taken as `origin/main` (`9ed9b18`) before that local main commit.
  Not milestone work. **Disposition:** no code change; effective base recorded as `4ccf14f`.
- **W2 [DRY]** `scripts/check_conventions.py` — the `-z` name-status walk re-implements
  `src/aa_ma/analysis/changed.py` and handled only `R`, not `R`/`C`. **Fixed:** same walk and
  `"RC"` width as changed.py, `# why:` pointer to keep them in step (import impossible: stdlib-only).
- I1 docstring's stdlib-only reason contradicted the `uv run` entry. **Fixed:** reason reworded (leaf, any python3).
- I2 per-file `git diff` and pre-commit batching. **Partly fixed:** `require_serial: true`; one-call diff deferred to M6 if latency shows.
- I3 `--all-files` exits 2 "no diff source". **Fixed:** stated in ADR-0018 Consequences.
- I4 ref-injection test wrote to a fixed `/tmp/pwned`. **Fixed:** sink under `tmp_path`.
- I5 `touched` job syncs the full dev group. **Accepted** (simplicity; ~15 s job).
- I6 shellcheck runs twice on touched `.sh`. **Fixed:** overlap stated in ADR-0018 Neutral.

## Security (security-auditor agent)

### Mechanical pre-check (security-static-check.sh): PASS

### Semantic findings

- I1 [A03] `scripts/check_conventions.py` prints raw paths/messages; a newline in a PR filename could
  inject `::` workflow commands into the job log once M6 checks print content. No privilege gain
  (read-only token, no secrets). **Deferred to M6** (escape control chars when checks print).
- I2 [A08] setup-uv caches by default; PR-scoped, `uv sync --locked` verifies hashes. **No action.**
- Clean: ref verification (`--end-of-options`, SHAs only), `--literal-pathspecs`, `--` separation,
  no shell; `pull_request` trigger, `contents: read`, `persist-credentials: false`, env-passed
  `base_ref`, SHA pins; no private/client names in the diff.

## TDD Sequence (tdd-sequence-auditor agent)

### Verdict: PASS

### Evidence

No `src/` commit in the window (automatic PASS). Tests and implementation share commits `7a821ed`
and `97687ab`, so git cannot confirm the RED runs recorded in Sub-step 1.2/1.3 Result Logs; git does
show `tests/test_precommit_config.py` (7a821ed) preceding `.pre-commit-config.yaml` (97687ab).

### Per-file pairing (informational only)

- `scripts/check_conventions.py` ↔ `tests/scripts/test_check_conventions.py` (same commit)
- `.pre-commit-config.yaml` ↔ `tests/test_precommit_config.py` (test first)
- `.github/workflows/security.yml` ↔ canary PR #17 (FAIL on F401) and PR #18 (PASS)

## External Library Evidence (context7-evidence-auditor agent)

### New PyPI dependencies in milestone diff

- `pre-commit>=4.5` (locked 4.6.2), `bandit==1.9.4` — evidence in reference.md Dependencies/Tool
  Versions. 10 specs moved unchanged from `[tool.uv] dev-dependencies` (not new). Transitive: cfgv,
  distlib, filelock, identify, nodeenv, python-discovery, stevedore, virtualenv.
- I: reference.md said pre-commit 4.5.1 (conda). **Fixed:** now 4.6.2 (uv.lock).

### Major version bumps in milestone diff

None.

## Future-Proofing (future-proofing-auditor agent)

### Findings

- I1 ADR-0018 named Ruff 0.15.9. **Fixed:** version dropped.
- I2 ADR-0018 duplicated the uv 0.12.3 pin. **Fixed:** "uv pinned in the job".
- I3 `bandit==1.9.4` appears in pyproject and its test. **Accepted:** deliberate guard.
- I4 gitignored project `CLAUDE.md` CI/CD section says "Ruff lint on `src/`". **Post-merge** local edit (Sub-step 2.0).
- I5 unexplained regex in `tests/test_precommit_config.py`. **Fixed:** `# why:` added.

## User Override Decisions

None required (0 CRITICAL).

## Revision History

- 2026-10-08 — initial run; fixes applied in the same milestone (W2, I1–I4, I6 code-review; FP I1, I2, I5; C7 I2).
