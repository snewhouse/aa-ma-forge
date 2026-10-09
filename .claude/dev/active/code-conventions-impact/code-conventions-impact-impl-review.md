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

---

# Impl Review Report: code-conventions-impact / Milestone 3

**Milestone:** Milestone 3: Commands → skills (13), install hygiene
**Audit-Profile:** full · **Budget:** normal (parallel, 5 agents) · **Date:** 2026-10-09
**Window:** `686abac..5795fe4` (fixes after it: `e72f8a7` RED → `196461b` GREEN)

## Summary

| Agent                     | CRITICAL | WARNING | INFO | Verdict |
|---------------------------|:--------:|:-------:|:----:|---------|
| code-reviewer             | 0 | 4 | 4 | WARN |
| security-auditor          | 0 | 2 | 5 | WARN |
| tdd-sequence-auditor      | 0 | 1 | 3 | PASS |
| context7-evidence-auditor | 0 | 0 | 2 | PASS |
| future-proofing-auditor   | 0 | 0 | 4 | PASS |
| **TOTAL**                 | **0** | **7** | **18** | **PASS_WITH_WARNINGS** |

(§6.6 ran first with 3 agents — 0 CRITICAL / 15 WARNING / 17 INFO — all fixed in `db1038c` → `41d8288`, Ste: "fix all incl. shared hook table".)

## User Override Decisions (Ste, 2026-10-09)

No CRITICAL, so no override panel. Two decisions taken on WARNINGs:

| # | Finding | Decision | Action |
|---|---------|----------|--------|
| 1 | [WARNING] security: execute-aa-ma-full and archive-aa-ma became model-invocable but commit/tag/push with no per-step gate | **D9 revised again: add both (4 total)** | `disable-model-invocation: true`; `EXPECTED` = 4; ADR-0020, reference D9, README, CHANGELOG |
| 2 | The other 6 WARNINGs + cheap INFOs | **fix now** | `e72f8a7` RED → `196461b` GREEN |

## Findings and dispositions

| Agent | Sev | Finding | Disposition |
|---|---|---|---|
| code-reviewer | W | `../` links broken by the git mv: aa-ma-chart:28, execute-aa-ma-milestone:737 | fixed (`../../../`); new `tests/skills/test_skill_links_resolve.py` (every `../` link in shipped skills; *TEMPLATE* files excluded — their links are relative to output) |
| code-reviewer | W | uninstall aborts half-done if the jq write fails | fixed: warns and returns 0 |
| code-reviewer | W | docs/ATTRIBUTION.md lists retired command paths | fixed |
| code-reviewer | I | TODOS.md stale test/path names | fixed |
| code-reviewer | I | sole-dev-merge:1057 dead plan link (dead before the move) | fixed → `.claude/dev/completed/…` |
| code-reviewer | I | aa-ma-plan `simple` says "/grill-me protocol preserved verbatim" | reworded |
| code-reviewer | I | dry-run carve-out hard to read | extracted `slot_free_for_restore` |
| security | W | planted `..` manifest row → `--restore` writes a link outside ~/.claude (reproduced by the auditor) | fixed: `manifest_slot_ok` accepts one name in `skills|agents|rules|commands|hooks/lib`; bats case |
| security | W | execute-aa-ma-full / archive-aa-ma model-invocable | fixed per decision 1 |
| security | I | aa-ma-share runs `./scripts/aa-ma-share-allow.sh` from cwd when the checkout is missing (pre-existing) | fixed: refuses |
| security | I | settings.json rewrite loses a 0600 mode (pre-existing) | fixed in install + uninstall (`chmod --reference`; superseded by 8e87d95: `cp -p` before the jq write — portable, no 0644 window); bats case |
| security | I | jq filters safe; symlink handling improved; leak rule clean | — |
| tdd-sequence | W | 210ca3f added `disable-model-invocation` + the readlink change with their test in the same commit | acknowledged: frontmatter/path changes rode the move commit; the readlink was verified empirically in a fake HOME (3.3 Result Log) and the flag mechanics by probe |
| tdd-sequence | I | **256237f's message says "format-only / No content change" but the commit also carries the 11 R100 renames** (they were already staged) | acknowledged; pushed history not rewritten — this row is the correction |
| tdd-sequence | I | 41d8288 GREEN adds `test_no_doc_claims_a_command_count` without its own RED | acknowledged (doc-wording guard) |
| tdd-sequence | I | 24c3676 deletes the frozen-regex test | acknowledged (vacuous with no commands; skill-glob test covers) |
| context7 | I | no new deps / bumps | — |
| context7 | I | `$ARGUMENTS` and `disable-model-invocation` not shown live | closed: isolated probe (provenance PROBE line) |
| future-proofing | I | SECURITY.md:11 / foundations counts guarded; `FORMER_COMMANDS` floor; bats `-ge 8` floor | bats floor → `-ge 1` |
| future-proofing | I | gitignored CLAUDE.md block stale | deferred to 4.0 (context-log) |

Totals note: the Summary counts each agent's raw findings (7 W / 18 I); the table merges rows that share a fix (the two `../` links into one row; security INFO "jq safe / symlinks improved / leak clean" into one; future-proofing count rows into one), so it lists fewer rows.

## Verification after fixes

pytest 2571 passed / 0 failed; `bats -r tests` 377/377; shellcheck (CI form, every `.sh`) rc=0.
