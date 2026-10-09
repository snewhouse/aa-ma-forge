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
- 2026-10-08 — double-check challenger (fresh subagent) found F1 (subdirectory run diffed nothing:
  name-status paths are root-relative, pathspecs cwd-relative), F2 (textconv honoured), F3 (FILE
  filter unnormalised). Ste chose "fix now in M1". Tests first (3 RED for the intended reasons), then:
  every diff runs from `rev-parse --show-toplevel`, `--no-textconv`, `os.path.normpath` on FILE
  args. ADR-0018 states that main pushes run no lint (PR-only). Security I1 (escape output) stays M6.

---

# Impl Review Report: code-conventions-impact / Milestone 2

**Milestone:** Milestone 2: Migrate 5 skills + ruff hook into the forge
**Audit-Profile:** full · **Budget:** normal (parallel, 5 agents) · **Date:** 2026-10-09
**Window:** `dc79b4b..<pre-rewrite>` (pre-rewrite SHAs; the branch was rewritten for the leak below — reviewed content identical except `logging-and-comments/SKILL.md:66`)

## Summary

| Agent                     | CRITICAL | WARNING | INFO | Verdict |
|---------------------------|:--------:|:-------:|:----:|---------|
| code-reviewer (+ §6.6 reuse/quality/efficiency) | 0 | 3 | 6 | WARN |
| security-auditor          | 0 | 3 | 7 | WARN |
| tdd-sequence-auditor      | 1 | 0 | 3 | FAIL → disputed |
| context7-evidence-auditor | 0 | 0 | 1 | PASS |
| future-proofing-auditor   | 0 | 3 | 7 | WARN |
| **TOTAL**                 | **1** | **9** | **24** | **PASS_WITH_WARNINGS** (CRITICAL disputed) |

## User Override Decisions (Ste, 2026-10-09)

| # | Finding | Decision | Action |
|---|---------|----------|--------|
| 1 | [CRITICAL] tdd-sequence: tests and src share commits (<pre-rewrite>/<pre-rewrite> pre-rewrite), so git cannot order RED before GREEN | **dispute** | RED runs are in the 2.3/2.4 Result Logs (15 failed; 9/10 failed). Convention learned: from now on, RED tests get their own `test(...)` commit (applied: `4e6889e` RED → `adb3524` GREEN) |

## Findings and dispositions

- **Security W1 — private repo name in a public repo** (`logging-and-comments/SKILL.md:66`, the "Exemplar:" line naming a private Carmen repo path). **Fixed + history rewritten** (Ste: rewrite + force-push): `git filter-branch --tree-filter` over `dc79b4b..HEAD`; `git log -p` hits = 0; GitHub Support purge of the orphaned SHAs is pending, for Ste to request. Lesson L-039 tightened.
- **Security W2 — secrets-management GitLab example echoes `$API_KEY`/`$DATABASE_URL`** (:205-206). **Fixed** (Ste: patch + derived).
- **Security W3 — trufflehog without `--fail` exits 0 on findings** (:323-342). **Fixed**: `--fail` on both calls; FORKS state current → derived, local md5 `ea0799c2…`.
- **Code W1 — settings-only backup dir hides real-file backups from `uninstall --restore`.** **Fixed, root cause broader:** any re-install backs up the copied spec docs into a new dir, which hid the older one (pre-existing). `--restore` now walks every `aa-ma-forge-*` dir newest-first; settings backups are sibling files `settings-aa-ma-forge-<ts>.json`. bats: "a later settings-only backup never hides the real-file backup from uninstall --restore".
- **Code W2 — ruff-format.sh ignores `AA_MA_HOOKS_DISABLE`.** **Fixed** (+ `CLAUDE_HOOK_LOG`, Future W3; `--` before the path, Security INFO). README kill-switch carve-out removed. ADR-0019: "Adoption, adapted".
- **Code W3 / Future I8 — `_helpers.py` mattpocock fallback.** **Fixed**: a FORKS.json entry is required.
- **Future W1 — README "nine hooks" invisible to the count test.** **Fixed**: "9 hooks".
- **Future W2 — literal SHAs in tests.** **Fixed**: `test_provenance_header_names_the_manifest_sha` reads them from FORKS.json.
- **Code I — stale write-a-skill message.** **Fixed.**
- **Not changed (INFO):** dual hook-row grammar (install.sh regex vs codemem `_HOOK_ROW`, cross-referenced); trailing comments after format-on-touch; repeated `load_manifest` at collection; jq-missing path not logged; fork-drift manifest values not validated (GET-only, committed input); Vault dev-mode/`--secret-string`/`$GITHUB_ENV` examples (upstream prose); upstream SHAs in README/foundations prose; orphan pin to be removed by M12; `licence` single-valued; ruff "0.15.4" in baseline prose; SECURITY.md name lists not set-checked; captured payload keeps real session/tool IDs (not credentials).
- **Out of scope, pre-existing:** `uninstall --restore` does not deregister hooks.

## Verification after fixes
`uv run pytest` 2482 passed / 7 skipped / 0 failed; `bats -r tests` 355/355; shellcheck rc=0.
