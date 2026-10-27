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

---

# Impl Review Report: code-conventions-impact / Milestone 4

- Milestone: Milestone 4: Prompt-as-code checks + writing-for-agents fork
- Audit-Profile: full — agents: code-reviewer, security-auditor, tdd-sequence-auditor, context7-evidence-auditor, future-proofing-auditor (parallel, budget normal)
- Window: 13de435..6802df7 (38 commits); fixes in 1157273
- Date: 2026-10-09

## Summary

| Agent                     | CRITICAL | WARNING | INFO | Verdict |
|---------------------------|:--------:|:-------:|:----:|---------|
| code-reviewer             | 0 | 4 | 5 | WARN |
| security-auditor          | 0 | 1 | 4 | WARN |
| tdd-sequence-auditor      | 0 | 0 | 0 | PASS (9 RED→GREEN pairs in order; first test 3m06s before first src) |
| context7-evidence-auditor | 0 | 0 | 0 | PASS (no new PyPI deps / MAJOR bumps) |
| future-proofing-auditor   | 0 | 3 | 8 | WARN |
| **TOTAL**                 | **0** | **8** | **17** | **PASS_WITH_WARNINGS** |

## Findings and outcomes (Ste: fix all 8 + one-liner INFOs)

- S1 [A01] eval session could reach Bash via a skill whose `allowed-tools` pre-approve it (retro, assess-codebase) — **fixed/verified**: LIVE hostile case `tests/scripts/fixtures/evals-sandbox/skill-escape` (grants Skill, loads the plugin, invokes retro, asks for a shell marker) passes; marker absent, real `~/.probe` absent.
- C4 `!`…`` only refused in forked skills — **fixed**: `test_no_loaded_skill_runs_dynamic_exec` covers every skill the evals load.
- C2 SKILL-MECHANICS.md not hash-checked — **fixed**: `test_skill_mechanics_is_unedited` vs FORKS.json upstream md5.
- C3 provenance said "upstream text unedited" after 4.7's `when_to_use` — **fixed** (provenance line, block sentence, test docstring; FORKS.json md5 updated).
- C1 eight one-line `_lib` wrappers — **kept by decision** (context-log): plugin eval resolves the case symlink fully, so the fixture name cannot come from the link name.
- F1 bats hardcoded 24 — **fixed**: counts `evals/*/*/case.yaml`.
- F2 exactly-3 vs "at least 3" — **fixed**: `test_each_eval_skill_has_its_minimum_cases`.
- F3 `max_turns: 12` ×24 without rationale — **fixed**: `MAX_TURNS` asserted per case; why in ADR-0021.
- INFOs fixed: `_helpers.py` docstring; release.sh `tail -n 2` why-comment; "24" removed from runbook and run-evals comment. INFOs acknowledged: install.sh scope note (context-log 4.4), TOC merge-base warn-only while pytest is local-only, model alias not pinned (record the resolved model at the 9.6/10.9/11.8 re-runs), c55ee46 prose copies (fork-drift process), duplicate small reads in tests (efficiency INFO).

## User Override Decisions

None — no CRITICAL findings.

## Verification

Guards C2/C4/F3 each proven by a temporary mutation (failed, restored). pytest 2728 passed / 6 skipped / 0 failed; `bats -r tests` 398/398; shellcheck rc=0; LIVE sandbox bats pass (3 hostile cases).

---

# Impl Review Report: code-conventions-impact / Milestone 5

- Milestone: Milestone 5: Split the six oversized prompt files (behaviour-preserving)
- Audit-Profile: code-only — agents: code-reviewer, security-auditor, tdd-sequence-auditor, context7-evidence-auditor, future-proofing-auditor (parallel, budget normal)
- Window: bc177e5..101dc00 (21 commits); fixes in 6a64cd2
- Date: 2026-10-11

## Summary

| Agent                     | CRITICAL | WARNING | INFO | Verdict |
|---------------------------|:--------:|:-------:|:----:|---------|
| code-reviewer             | 0 | 3 | 3 | WARN (all six SKILL.md usable entry points; no dangling above/below) |
| security-auditor          | 0 | 0 | 3 | PASS (safety text intact; no private names; extract_stage.sh safe) |
| tdd-sequence-auditor      | 0 | 0 | 1 | WAIVED (TDD-Waiver: refactor; RED 7957ddc 4m13s before first split) |
| context7-evidence-auditor | 0 | 0 | 0 | PASS (no PyPI deps / MAJOR bumps) |
| future-proofing-auditor   | 0 | 1 | 5 | WARN |
| **TOTAL**                 | **0** | **4** | **12** | **PASS_WITH_WARNINGS** |

## Findings and outcomes

- C-W1 pointer stubs name the file, not the section; §7.3 stub does not say it blocks — **fixed** (6a64cd2): 45 pointers deep-link `references/<file>#<anchor>`, anchor existence asserted when written.
- S-I1/S-I2 §6.8, §7.3, Stage D safety steps behind a descriptive pointer — **fixed**: one imperative line each in SKILL.md.
- C-W2 four bash copies of "SKILL.md + references" — **fixed**: `tests/lib/skill_files.bash` used by extract_stage.sh, gate-scans, deps bats (`_section_68` keeps its single named reference by design).
- C-W3 `pre-execution-validation.md` byte-identical in execute-aa-ma-milestone and execute-aa-ma-full (pre-existing duplication made visible) — **deferred** (context-log): consolidating is not a behaviour-preserving move.
- F-W1 CHANGELOG Unreleased said six files are held until split — **fixed**; split entry added under Changed.
- F-I "five audit agents", "6-angle" in new titles/pointers — **fixed** (counts dropped). F-I `angles-1-5.md` name encodes a range — **accepted** (angles are numbered in the spec). F-I SPLIT_SKILLS hand-maintained — **comment added**. F-I pointer purposes repeat titles — accepted cost of the format.
- C-I writing-for-agents test used rglob — **fixed** (skill_files). C-I L-047 outside declared artefacts — recorded in the 5.3 Result Log (self-improvement rule). C-I POINTER_RE purpose clause is free text — accepted, documented; all pointer lines read by the reviewer.
- S-I3 Stage F relies on Stage A's main-branch check — unchanged behaviour; noted for a later milestone.

## User Override Decisions

None — no CRITICAL findings.

## Verification

Widened checks proven by planted lines (gate-scans 2 fail, deps 1 fail; restored). pytest 2774 passed / 6 skipped / 0 failed; `bats -r tests` 403/403; shellcheck clean; regen edges/golden unchanged.

---

# Impl Review Report: code-conventions-impact / Milestone 6

- Milestone: Milestone 6: Comments, docstrings, KISS lint (T8, T11 §3)
- Audit-Profile: full — agents: code-reviewer, security-auditor, tdd-sequence-auditor, context7-evidence-auditor, future-proofing-auditor (parallel, budget normal)
- Window: f6a3af3..9d5c806 (11 commits); RED 25ff1eb, fixes cd64eda
- Date: 2026-10-11

## Summary

| Agent                     | CRITICAL | WARNING | INFO | Verdict |
|---------------------------|:--------:|:-------:|:----:|---------|
| code-reviewer             | 0 | 2 | 4 | WARN |
| security-auditor          | 0 | 3 | 4 | WARN |
| tdd-sequence-auditor      | 0 | 0 | 0 | PASS (c324b5c RED 49 s before 0b8faaa; process notes below) |
| context7-evidence-auditor | 0 | 0 | 0 | PASS (config only; no PyPI deps / MAJOR bumps) |
| future-proofing-auditor   | 0 | 2 | 6 | WARN |
| **TOTAL**                 | **0** | **7** | **14** | **PASS_WITH_WARNINGS** |

## Findings and outcomes

- S-W1 a committed file named `--from-ref=<sha>`/`--to-ref=<sha>` reached argparse as an option (pre-commit appends filenames with no `--`) and emptied the range → WHY001/TODO001 off in CI — **fixed** (cd64eda): hook `args: ["--"]`; test pins the args; proved live: with the fix pre-commit fails WHY001, old argv order exits 0.
- S-W2 `_has_why` walked back per line, O(n²) (8k lines 6.5 s) — **fixed**: one forward pass `_why_covered`; 20k-line test < 5 s. Arithmetic check O(1) (`_in_arithmetic`), not `"((" in stack`.
- S-W3 raw control characters in the not-tokenizable log line — **fixed**: `_printable` on path and exception; test.
- S-I `::`-prefixed path forges a GitHub annotation — **fixed** (`./::…`); S-I staged `1:evil.py` read as stage 1 — **fixed** (`:0:`); S-I eval grants Agent → subagent Bash — **accepted** (trusted fixture, remote-less scaffold); S-I same `--` hole in the ruff hooks (pre-dates M6) — **deferred to M8** (secops), recorded in context-log.
- C-W1 magic-constant rule stated twice (pattern 5 + new bullet), double-counts in SUMMARY — **fixed**: bullet removed, test asserts it stays out. C-W2 AUDIT_BUDGET=low silent on the new section — **fixed**: it runs (diff-local); test.
- C-I / F-W1 suffix lists duplicated between `_SCANNED_SUFFIXES` and `_scan` — **fixed** (`_PY_SUFFIXES`, `_SH_SUFFIXES`). F-W2 openers and closers in two lists — **fixed** (`_CONTEXTS` table, `_CLOSERS` derived). C-I unbalanced shell context at EOF silent — **fixed** (one warning; test). C-I/F-I `len(CHECKS) == 2` — **fixed** (asserts names). F-I ruff limits hard-coded in fixtures — **fixed** (read from pyproject). F-I `extend-ignore` exact set — **kept as ratchet**, `# why:` added. F-I inline `<<` regex — **named** `_HEREDOC_OP_RE`. C-I `new_text` parses the range string — **accepted** (one producer, tested both modes). F-I rule IDs named in code-reviewer prose, ADR-0018 line — **accepted** (update when checks change; ADR line is history).
- T-I process: the §6.6 fix 9edd103 carried its RED cases in the same commit, and the shellcheck-args test landed with its GREEN commit (seen RED locally first — it exposed the YAML comma split). §6.8 fixes went back to a separate RED commit (25ff1eb).

## User Override Decisions

None — no CRITICAL findings.

## Verification

7 mutations of the §6.8 fixes each fail ≥1 test (block reset/carry, stage 0, `::`, log escape, EOF warning, arithmetic top). test_check_conventions 83, test_ruff_config 14, agent rule tests 11 — 152 passed in the touched set; full suite recorded in provenance.

---

# Impl Review Report: code-conventions-impact / Milestone 7

- Milestone: Milestone 7: Logging standard (T9) + hook contracts (T15 §7)
- Audit-Profile: full. Agents: code-reviewer, security-auditor, tdd-sequence-auditor, context7-evidence-auditor, future-proofing-auditor (run in parallel, budget normal)
- Window: 74cc7e2..b8bb285 (26 commits); §6.6 fixes in 1dc490b
- Date: 2026-10-12

## Summary

| Agent                     | CRITICAL | WARNING | INFO | Verdict |
|---------------------------|:--------:|:-------:|:----:|---------|
| code-reviewer             | 0 | 5 | 4 | WARN |
| security-auditor          | 0 | 2 | 3 | WARN (no `[security-bypass:]` in the window) |
| tdd-sequence-auditor      | 0 | 0 | 0 | PASS (48e05a7 RED 29 min before the first src/ commit 5fc528b; every src/hook file paired) |
| context7-evidence-auditor | 0 | 0 | 0 | PASS (no PyPI deps or MAJOR bumps) |
| future-proofing-auditor   | 0 | 1 | 3 | WARN |
| **TOTAL**                 | **0** | **8** | **10** | **PASS_WITH_WARNINGS** |

## Findings

- S-W1: with `HOOK_DEBUG=1`, `aa_ma_debug` now writes whole Bash commands to hooks.log on disk; before, they went to stderr only.
- S-W2: masking gaps:
  - `export API_KEY="…"`, `PASSWORD='…'` (quoted value);
  - `Authorization: Bearer …`;
  - `token: "…"` (unquoted key, quoted value);
  - `--password x`;
  - url-credential stops at the first `@` or `/` in the password.
- C-W1: three hooks load aa-ma-log.sh three ways, each failing differently when it is missing.
- C-W2: the plan-skip-warn deprecation notice is stderr-only on exit 0, so it is never seen (L-1319).
- C-W3: ruff-format with malformed stdin JSON exits 0 with no log line.
- C-W4: logsetup JSON mode writes its fail-closed record without `ts` or `logger`.
- C-W5 / F-I: `{1,64}` bound on session_id in ruff-format has no name or reason.
- F-W1: the cap 8192 and overlap 256 are defined separately in bash and Python (tests pin both).
- S-I: text-mode CLI logs don't flatten CR/LF. S-I: an absolute PATH entry inside an untrusted venv is still trusted (user's choice). S-I: ruff output from the edited repo reaches the model (JSON-safe, capped at 10 lines).
- C-I: `configure_logging` has no non-test caller until M10. C-I: verbosity 2 maps to DEBUG via `.get` default. C-I: a missing jq gives a notice on every edit (dedupe needs session_id, which needs jq). C-I: hook-name cleanup written twice.
- F-I: "13 rules" in CHANGELOG is correct today. F-I: "≤10 lines" is repeated in docs.

## Outcomes (Ste: "Fix 6, defer 2")

RED 7c39826, GREEN fe79b23.
- S-W2, **fixed:**
  - generic-env accepts a quoted value and `--key value`;
  - new `bearer-token` rule (log-only id);
  - url-credential's password is `[^ ]{1,256}@`, so `@` and `/` are masked.
  - All of these are bounded, and the 100 KB timing cases were added.
- S-W1, **fixed:** `aa_ma_debug_cmd` logs `<label> (<n> chars): <first 120>`. All 3 command sites use it, and a guard bats test fails if a hook passes `$cmd` to aa_ma_debug.
- C-W2, **fixed:** the deprecation notice also goes to hooks.log through `log_warn`, and the alias stays on one line.
- C-W3, **fixed:** an unreadable payload writes one WARN line to hooks.log, and the Fail-open header says so.
- C-W4, **fixed:** the JSON fail-closed record has `ts`, `level`, `logger` and `message`.
- C-W5, **fixed:** `# why:` on the 64-char session-id bound.
- C-W1 (one aa-ma-log.sh loader) and F-W1 (cap and overlap in one place), **deferred:** TODOS.md "Hook hot-path and helper tidy-ups".
- INFO: S-I CR/LF in text-mode CLI logs, **deferred** to the same TODOS item. Other INFO items are **accepted** as recorded above. `configure_logging` gets its first caller in M10.

## User Override Decisions

None: no CRITICAL findings.

## Verification

Follow-up (2b6be1e): a third background security notice. Live probes showed the 120-char prefix still kept CLI secrets (`curl -u user:pw`), so debug lines now name only the length and first word. RED f644447.

Double-check follow-up (f8f7220, 4544060): env-prefix secrets; readlink -f / HOME / lib fail-open; CR/LF-safe CLI logs (closes the deferred S-I); no shared-/tmp fallback (4th security notice).

Mutations: removing bearer-token fails 2 tests; removing the quoted-value branch fails 3; a raw `$cmd` in aa_ma_debug fails the guard. bats 446/446, pytest 2964 passed / 6 skipped / 0 failed, lint-imports 6 kept, shellcheck clean.

---

# Milestone 8: SecOps CI baseline (T10) — post-impl review (§6.8)

- Audit-Profile: full · window 0df379c..e7f85ab (35 commits) · budget normal · parallel dispatch, 5 agents
- Date: 2026-10-13

## Summary

| Agent | CRITICAL | WARNING | INFO | Verdict |
|---|:-:|:-:|:-:|---|
| code-reviewer | 0 | 6 | 2 | WARN |
| security-auditor | 0 | 5 | 3 | WARN |
| tdd-sequence-auditor | 0 | 1 | 2 | PASS |
| context7-evidence-auditor | 0 | 1 | 3 | WARN |
| future-proofing-auditor | 0 | 3 | 9 | WARN |
| **TOTAL** | **0** | **16** | **19** | **PASS_WITH_WARNINGS** |

No CRITICAL, so no override panel. Ste chose "Fix A–G, defer 2".

## Findings and outcomes

| # | Finding (agent) | Outcome |
|---|---|---|
| A | Stage D auto-fixed literal-command S602 (Ruff reports it; Bandit's HIGH filter did not), counted unapplied sed edits, staged with `git add -A` (security, code-reviewer) | **Fixed** 70411d9 RED → 7bf4610: non-literal only, edit verified, only edited files staged |
| B | Hook read only the index and the literal `git commit`: -am, -a, pathspec, `git -C/-c`, `--no-edit` unscanned (security) | **Fixed** 5e5aa6f RED → e5241b5: staged ∪ modified tracked .py, index + working tree, `git -C/-c` recognised, no editor-form skip |
| C | Quoted non-ASCII names dropped (security) | **Fixed** e5241b5: NUL listing, `core.quotePath=false` |
| D | Bypass marker outside the message left no audit trail (security) | **Fixed** e5241b5: every use logs a hooks.log WARN line |
| E | `invalid-syntax` labelled "security rule" (Ste's question) | **Fixed** e5241b5: "unparsable Python (cannot be scanned)", still blocks |
| F | Pinned-SHA test would fail every Dependabot setup-uv PR; deps job did not check expiry; gitleaks pins unwatched (future-proofing, code-reviewer, security) | **Fixed** 18aa2a6 RED → ff92d48: shape + uniform pins, expiry step in deps, gitleaks rev/CI agreement test, TODOS pin review |
| G | secops pip-audit recipe ≠ CI; SSDF rule without reason; pip-audit pin without why; header step order; foundations row stale (code-reviewer, future-proofing) | **Fixed** b661861 (+ Go/Rust/Java/Ruby/PHP/.NET lockfile routing per osv-scanner docs) |
| — | Per-file fork ceiling (~700 files) (security) | **Deferred** TODOS P3 |
| — | Reusable secops-ci template for other repos (Ste) | **Deferred** TODOS P2 |
| — | TDD: 964e5b7 (whole-file redesign) and db3c46a (Stage C/D) changed tests in the same commit, no RED first | **Recorded** (verdict PASS at window level) |
| — | pip-audit: no CONTEXT7 evidence | **Recorded** honestly in provenance: verified by live runs, no docs consulted |
| — | Test-helper duplication across tests/security, owners logger name, scope notes | INFO; logger renamed (e1b5c88), helpers kept per house style |

## Background review rounds after §6.8

Two further commit reviews on the hook found a root-relative path mismatch (fixed c8467eb,
RED test first) and more command-parsing bypasses (`--git-dir <path>`, `cd x && git commit`,
env-var commits). **Decision (Ste, 2026-10-13): the hook is a best-effort guardrail, not a
security boundary** — ADR-0022 amendment and hook header list the non-goals; enforcement is CI
plus the repo's pre-commit; a git pre-commit move is the TODOS upgrade path.

## User Override Decisions

None (no CRITICAL).

## Verification

pytest 3004 passed / 6 skipped / 0 failed; bats 505/505 at b661861.

# Milestone 9: Testing gate `TESTS_VERIFIED` (T11 §5) — post-impl review (§6.8)

- Audit-Profile: full · window 1ff3178..972e783 · budget normal · parallel dispatch, 5 agents
- Date: 2026-10-13

## Summary

| Agent | CRITICAL | WARNING | INFO | Verdict |
|---|:-:|:-:|:-:|---|
| code-reviewer | 0 | 3 | 2 | WARN |
| security-auditor | 0 | 1 | 4 | WARN |
| tdd-sequence-auditor | 0 | 0 | 2 | PASS (6 RED→GREEN pairs) |
| context7-evidence-auditor | 0 | 0 | 1 | PASS (no new deps) |
| future-proofing-auditor | 1 | 2 | 2 | BLOCKED until accepted |
| **TOTAL** | **1** | **6** | **11** | **PASS_WITH_WARNINGS** (after the CRITICAL was accepted and fixed) |

## Findings and outcomes

| # | Finding (agent) | Outcome |
|---|---|---|
| C1 | ADR-0023 hard-coded "SKILL.md 497 lines" and "28 cases", both stale after §6.6 (future-proofing) | **Accepted, fixed** 449cb14: no drifting counts |
| W1 | A `shlex.py` at the repo root replaced the stdlib module in the argv split, so a branch could run any command and still record `cmd=uv run pytest` (security, reproduced) | **Fixed** RED a7bfd8f → GREEN 449cb14: `python3 -I` |
| W2 | `awk -v` unescaped backslashes in the approval title (code-reviewer, reproduced; security INFO) | **Fixed** 449cb14: the title is passed via `ENVIRON` |
| W3 | Working-tree fallback undocumented; a misleading "merge-base" label when no reference.md existed anywhere (code-reviewer) | **Fixed** 449cb14: header and gate-fences list every source; NOTE + `default: no reference.md anywhere` |
| W4 | 540 s / 30 s defaults with no reason; `tail -n 5`/`20` unnamed (code-reviewer, future-proofing) | **Fixed** 449cb14: `# why:` on both defaults; `TAIL_SHORT`/`TAIL_FAIL` |
| — | Totals note: 6 raw WARNINGs → 4 rows. W4 merges one code-reviewer and both future-proofing WARNINGs (the 540 s default rationale; the `tail -n 5`/`20` windows) | — |
| I | Inherited `TV` env var executed when neither script candidate exists (code-reviewer) | **Fixed** 449cb14: `TV=""` before the loop |
| I | A code-fenced approval example counted as an approval; fails open (security) | **Fixed** 449cb14: fenced lines skipped (an unclosed fence fails closed) |
| I | `timeout(1)` behaviour not cited (context7) | **Fixed** 449cb14: 124/137 cited in gate-fences.md and the ADR |
| I | Repo-local-first lookup of gate scripts (pre-existing pattern); a backreference Pass-Regex can hang the scan after the timeout (security) | **Deferred** TODOS P2 |
| I | "fences 2 and 3 follow" count wording (future-proofing) | **Accepted** as-is: test-guarded (`test_tests_verified.bats` fence-order case) |
| I | Out-of-list files (TDD-wording pointers, TOC) and resolver-loop duplication (code-reviewer) | **Recorded**: forced by tests (§6.3); duplication is the enforced pattern |

## Background review after §6.6

The commit review of d5ae802 flagged "gate integrity" in tests-verified.sh with no details. The
concrete vector found and reproduced: a branch forked before an existing plan reached the default
branch saw no merge-base reference.md and could supply its own Test-Command (decision B made that
possible). **Fixed** RED 61a9afb → GREEN 761c9b4: the default branch's copy wins; only a plan that
exists nowhere upstream uses its own copy.

## User Override Decisions

- C1 (future-proofing, hard-coded counts in ADR-0023): **Accept** (Ste) → fixed in 449cb14.

## Verification

test_tests_verified.bats 39/39, aa-ma-gate-approval.bats 12/12 (also under mawk 1.3.4); mutation
13/13 killed; full bats 561/561, pytest 3010 passed / 6 skipped / 0 failed; `codemem draw --check`
OK; all 7 real HARD approvals in this plan's context-log still pass. Final CI: see the CRITICAL_PATH_REVIEW addendum.

# Milestone 15: Codemem freshness (report 03 T2–T9) — post-impl review (§6.8)

- Audit-Profile: full · window 9546a2e..678fc82 · budget normal · parallel dispatch, 5 agents
- Date: 2026-10-14

## Summary

| Agent | CRITICAL | WARNING | INFO | Verdict |
|---|:-:|:-:|:-:|---|
| code-reviewer | 1 | 7 | 3 | BLOCKED until fixed (accepted) |
| security-auditor | 1 | 2 | 4 | BLOCKED until fixed (accepted, reproduced) |
| tdd-sequence-auditor | 0 | 0 | 2 | PASS (10 RED→GREEN pairs) |
| context7-evidence-auditor | 0 | 0 | 0 | PASS (no new deps) |
| future-proofing-auditor | 0 | 3 | 6 | WARN |
| **TOTAL** | **2** | **12** | **15** | **BLOCKED** (pending the fix pass below) |

## User Override Decisions

- C1 (security-auditor): a committed `.codemem/index.db -> <user file>` or `.codemem -> <dir>` made one codemem query overwrite the target with SQLite and delete `-wal`/`-shm` beside it — reproduced on the branch (victim replaced; `last_sha`, `tree_sig`, `db.lock`, `refresh.log` written beside it), not on main. **Accept** (Ste) → fix as one fail-closed boundary (L-049: third finding in the repo-controlled `.codemem/` mechanism → redesign, not patch).
- C2 (code-reviewer): `code-intel-refresh.sh` `sidecar()` followed symlinks and skipped the 40-hex check, so a committed `last_sha -> ../.git/refs/heads/<branch>` recorded `codemem=<HEAD>` for an index that never refreshed. **Accept** (Ste) → one shared shell reader.
- WARNINGs: fold in (Ste) — 40/64-hex SHAs, no sidecar write before the swap, `_git` timeout, lazy `Freshness` import, header reasons, `flock -w` + timeouts in the worker, `EXIT_LOCKED` in the test, `REFRESH_CAP_S` wording; the rest recorded (Contract/reference now, others TODOS).

## §6.8 re-run 1 (fix window ff6100c..f263dbc, 2026-10-14)

| Agent | CRITICAL | WARNING | INFO | Verdict |
|---|:-:|:-:|:-:|---|
| code-reviewer | 1 | 8 | 7 | BLOCKED (regression in the C1 fix; accepted) |
| security-auditor | 0 | 4 | 5 | WARN — C1 closed (35 hostile cases, 0 bad), C2 closed |

User Override Decisions (Ste, 2026-10-14):
- CRITICAL (code-reviewer): `check_db_path` caught only `FileNotFoundError`; a committed regular FILE `.codemem` made `ensure_fresh` (and every MCP tool) raise `NotADirectoryError` instead of returning the X2 envelope. **Accept — block until fixed.**
- Boundary (security-auditor W1/W2 + TOCTOU INFO): `codemem replay` wrote into a linked `index.db`; readers (status, draw, query, intel, `src/aa_ma/render/graph.py`) created `-wal`/`-shm` beside a linked target. **Chokepoint in `storage.db.connect()`** (refuse a linked DB file/dir for every reader and writer); `graph.py` drops `resolve()`.
- Committed index (security-auditor W4, A08): a git-tracked `.codemem/` was served as `stale=false` with poisoned rows. **Fix in M15**: a tracked `.codemem/` is refused; `connect()` sets `PRAGMA trusted_schema=OFF`.
- `aa_ma_context(write=True)` appended through a committed linked `reference.md` (security-auditor W3, pre-existing 814b9a0). **Fix now in M15.**
- code-reviewer WARNINGs: folded in (per Ste's standing "Fold them in" for §6.8 WARNINGs this milestone).

## §6.8 re-run 2 (window f263dbc..e9e511b, 2026-10-14)

| Agent | CRITICAL | WARNING | INFO | Verdict |
|---|:-:|:-:|:-:|---|
| code-reviewer | 0 | 4 | 9 | WARN — all re-run-1 findings fixed or recorded |
| security-auditor | 1 | 1 | 7 | BLOCKED — committed embedded repo in `.codemem/` defeats the git-tracked check (reproduced: phantom caller served stale:false; graph.py vouched for a planted edge) |

User Override Decisions (Ste, 2026-10-14):
- CRITICAL: **Redesign — trust token** (L-049: 4th bypass of git-based detection: dubious ownership, embedded repo, case alias, relative GIT_DIR). codemem serves only an index it built: a per-user record outside the repo holds a random nonce per DB directory; builds write it into the DB; readers and the graph.py twin compare. The git ls-files check is dropped; the link rule stays.
- WARNINGs + INFOs from both reports: **fold them in**.

## §6.8 re-run 3 (window e9e511b..4981491, 2026-10-14)

| Agent | CRITICAL | WARNING | INFO | Verdict |
|---|:-:|:-:|:-:|---|
| code-reviewer | 0 | 4 | 9 | WARN — re-run-2 findings fixed; trust-store errors fail silently (reproduced) |
| security-auditor | 1 | 1 | 7 | CRITICAL deferred (Ste) — a committed regular `.codemem/index.db-wal` beside a stamped index replays forged pages; the stamp page is untouched (reproduced end to end) |

User Override Decisions (Ste, 2026-10-14):
- CRITICAL (planted `-wal`): **Defer — root fix in a new milestone M15b, before M10**: move the default index out of the repo (`${XDG_CACHE_HOME:-~/.cache}/codemem/<sha256(realpath repo)>/`, `CODEMEM_DB` override kept), which removes the repo-controlled class (5 bypasses so far). M15 closes with it documented as a known limit (SECURITY.md, TODOS P1); still strictly better than main, which served any committed index.
- Fold-ins: non-ASCII stamp crash (byte compare, both twins), atomic nonce file, docs on differing `XDG_STATE_HOME`; plus the code-reviewer's 4 WARNINGs (standing "fold them in").

## §6.8 final verdict (2026-10-14): PASS_WITH_WARNINGS

| Round | Accepted CRITICALs | Outcome |
|---|---|---|
| First run | C1 `.codemem` link overwrite; C2 §6.0 sidecar reader | Fixed (fb7dd2a→4ad019c, a794c69→c896eb7, 8a34d54→71e78ab) |
| Re-run 1 | regular-file `.codemem` raised through every tool | Fixed (53b8b69→b0e1632); boundary moved to `db.connect` (e08ec0c→18fb83c) |
| Re-run 2 | committed embedded repo defeated git-tracked detection | Redesigned: trust token (1e3ac60→97b8ac9) |
| Re-run 3 | planted `index.db-wal` beside a stamped index | **Deferred by Ste** to Milestone 16 (move the index out of the repo); documented known limit |

WARNINGs from every round were folded in (latest: 6d752e6→54b8efb). Deferred items: TODOS.md (§6.6 follow-ups, §6.8 deferrals, M16 P1).

### Verification (at d594950)
- pytest 3121 passed (5 skipped); bats 633/633; no test writes `~/.local/state`.
- §6.7: fence 1 PASS (AA-MA clean, 0 pending, CRITICAL_PATH_REVIEW + PROTOTYPE present); fence 2 DIAGRAM_VERIFIED edges=25 checked=25 phantom=0; fence 3 TESTS_VERIFIED passed=3121.
- Live: the auditor's 35-case link harness → 0 bad; the 4 re-run-2 exploit repos no longer return the phantom caller; a committed index blob is refused by `open_graph`.

## §6.8 re-run 4 (targeted, window 4981491..bd10921, 2026-10-14)

| Agent | CRITICAL | WARNING | INFO | Verdict |
|---|:-:|:-:|:-:|---|
| security-auditor | 0 | 1 | 6 | WARN — no fail-open; `connect` could delete an index it did not create (TOCTOU) |
| code-reviewer | 0 | 4 | 9 | WARN — re-run-3 WARNINGs fixed; `draw --check` exit 1 on a broken store; empty record bricks builds; untested branches; `stale_reason: error` ambiguity |

Fold-ins (standing "fold them in"): RED 30e7f8d → GREEN c1df21f. Accepted known limits, not re-raised: planted `index.db-wal`; committing one's own `.codemem/` publishes the stamp; `replay --from-wal` trusts its journal (all → Milestone 16 / TODOS).
- Background review of c1df21f flagged a trust-store TOCTOU (path checked, then used): fixed by doing the check and every record operation through one directory fd (RED 118e199 → GREEN 3b50b5b), in both twins.

### Verification at 31afa8a (final)
- pytest 3136 passed (5 skipped); bats 633/633; no test writes `~/.local/state`; real `codemem build`/`status` work against the 0700 trust dir.
- §6.7: fence 1 PASS (0 pending, AA-MA clean); fence 2 DIAGRAM_VERIFIED edges=25 checked=25 phantom=0; fence 3 TESTS_VERIFIED passed=3136.

---

# Milestone 16: Move the codemem index out of the repo (M15b; §6.8 re-run 3 deferral) — post-impl review (§6.8)

Audit-Profile: full. Window 45d08ba0 (origin/main) .. e21e9bf1; round 2 on the fix e21e9bf1..5c4c9f9d. Threat model: local tooling (security-auditor.md). §6.6 had already run (24 findings, fix set 08c1b97b).

## Summary

| Agent | CRITICAL | WARNING | INFO | Verdict |
|---|:-:|:-:|:-:|---|
| code-reviewer | 1 | 5 | 5 | BLOCKED → fixed |
| security-auditor | 0 | 1 | 3 | WARN → fixed |
| tdd-sequence-auditor | 0 | 1 | 0 | PASS (rebase gave 11 commits one committer time; parentage + author dates order RED before GREEN in 16.1, 16.2, 16.3, §6.6) |
| context7-evidence-auditor | 0 | 0 | 0 | PASS (no dependency change) |
| future-proofing-auditor | 0 | 0 | 2 | PASS |
| **Round 1 total** | **1** | **7** | **10** | BLOCKED |
| Round 2 (fix only): code-reviewer / security-auditor | 0 / 0 | 0 / 0 | 2 / 0 | PASS |

Root fix confirmed by security-auditor: no default path reads repo-controlled files; the three resolvers agree.

## User Override Decisions

- [CRITICAL] `scripts/bench_codemem.py:74` cold build `rmtree`'d the parent of `$CODEMEM_DB` (introduced by the §6.6 fix set; `CODEMEM_DB=~/index.db` → `rmtree(~)`). Ste: **Accept**. RED cd6b695c (the RED run really deleted a tmp "home") → GREEN 5c4c9f9d: removes only `default_db_path(REPO_ROOT).parent`; `CODEMEM_DB` popped from the child env.
- WARNINGs folded (Ste): shell twin `CODEMEM_DB` trailing `/` (parity case); post-commit stderr line with no index dir; boundary-checks.md first-build step cap; `storage.db.db_files` / `remove_db_files` for every sidecar cleanup.
- Disputed: cli/server key on cwd vs shell on git toplevel — Ste chose cwd at 16.0 (pre-M16 also keyed on cwd); an MCP server started in a subdir reports "no DB" by path.
- Acknowledged (INFO): formula spelled out in 15 doc lines; deliberate twins (ADR-0014); `CODEMEM_DB` inside a repo keeps the M15 limits (documented); cache dir mode (TODOS P3); relative `CODEMEM_DB` resolved before the worker's `cd` (same dir in practice: both are the repo top); token value change `skipped(no index)` (no reader); AC names test_trust.py but the reproductions live in test_location.py; lessons edit vs the "frozen" list (additions only); no test for the post-commit no-index-dir stderr branch; `db_files` not in `__all__`.

## Verdict: PASS_WITH_WARNINGS (round 2 clean; stop rule: 2 rounds)

---

# Milestone 10: Impact tooling: codemem `callees`, pre-edit hook, wiring (T6, T13 git helper) — post-impl review (§6.8)

- Date: 2026-10-26 · Audit-Profile: full · Budget: normal (parallel) · Window: f0bfbd8b..e762e06b (48 commits, 91 files)
- Preceded by §6.6 (3 agents, 7 WARNING; W1–W5, W7 fixed a8830ad4..b21ad499; deferred items in TODOS.md "M10 §6.6 review: deferred …").
- code-reviewer received the §6.3 `<unpredicted-files>` list (38) per 10.7.

## Summary

| Agent | CRITICAL | WARNING | INFO | Verdict |
|---|:-:|:-:|:-:|---|
| code-reviewer | 0 | 8 | 4 | WARN |
| security-auditor | 0 | 0 | 3 | PASS |
| tdd-sequence-auditor | 0 | 0 | 0 | PASS |
| context7-evidence-auditor | 0 | 0 | 0 | PASS |
| future-proofing-auditor | 0 | 0 | 9 | PASS |
| **TOTAL** | **0** | **8** | **16** | **PASS_WITH_WARNINGS** |

## code-reviewer (0 / 8 / 4)
- [WARNING] schema: `who_calls` plugin entries `{name, kind, file, via}` lack `line` (code callers have it) — mcp_tools/__init__.py:413-421.
- [WARNING] dead code until M11: `derive_critical_paths` / `CRITICAL_PATH_GLOBS` have no non-test caller — plan_parsers.py:131.
- [WARNING] magic number: `file_impact` budget 2000 in cli.py:616 and mcp_tools:931, unnamed.
- [WARNING] DRY: `--threshold default=3` restates co_changes' default — cli.py:575-578.
- [WARNING] DRY: `_ANY_ROW_RE` copies `_ROW_RE` + 3 verbs — render/coverage.py:50-52.
- [WARNING] scope (L-007): ruff-format reflowed untouched lines in render/coverage.py.
- [WARNING] threat model: predicted-vs-actual.sh / commit-drift.sh strip only `[[:cntrl:]]`; repo paths reach §6.8 prompts unframed (vs the hook's Cc/Cf filter + "untrusted" framing).
- [WARNING] docstring: `aa_ma_cochange_partners` rc 4 reads as "timeout" (means timeout(1) missing) — aa-ma-parse.sh:305.
- [INFO] tests-verified base chain now prefers origin/main without origin/HEAD (intended, §6.6 W5).
- [INFO] git_mining stores HEAD names and drops deleted paths → hot_spots/symbol_history/owners counts change for renamed/deleted files (intended; say so in CHANGELOG).
- [INFO] `PluginEdgeRow` alias without docstring. [INFO] pre-edit hook clean on injection framing, jq --arg, sid regex, `--`, exit 0.
- Unpredicted files: 38, all missed impact (Contract too narrow: tests, aa-ma-parse.sh, aa-ma-install-lib.sh, doc-count files), none scope creep.

## security-auditor (0 / 0 / 3)
- [INFO] untrusted repo filenames can reach the model via the hook — bounded (sanitized, ≤3×200 chars, framed untrusted, jq --arg; same names visible via ls).
- [INFO] base refs never start with `-`; shell git without the gitutil prefix only matters with a hostile local config (out of scope).
- [INFO] session-scoped `rm -rf --` and markers bounded (sid regex, umask 077, set -C).

## tdd-sequence-auditor — PASS
- Every implementation commit has a preceding RED within its sub-step (10.2–10.7, §6.6); first tests 8b4b91cb precedes first src ac70a34b by 38 min.

## context7-evidence-auditor — PASS
- New dep griffe==2.3.2 (dev): rationale in reference/provenance/context-log. Advice: log a Context7 lookup of the griffe 2.x API before M11.4.

## future-proofing-auditor (0 / 0 / 9)
- All new counts (hooks 10, MCP tools 14, query tools 11) match their sources and are test-guarded; ADR-0026's "(14 MCP tools)" is a dated record.
- Carry to M11: a contract test that shell `AA_MA_COCHANGE_*` equals the Python twin; an AC that the gitutil twins and `derive_critical_paths` get a production caller or are removed.
- Nits: name the 200-char sanitize default; `CODEMEM_TIMEOUT_S` means 2 s and 30 s in two scripts; relax griffe to `>=2.3.2,<3` after cooldown.

## User Override Decisions
- None required (0 CRITICAL).

## §6.8 round 2 (fix only, window 9b8152c0..f8783074, 2026-10-26)
- Fixes (Ste: W1, W7, W8; rest deferred to TODOS "M10 §6.8: 5 deferred WARNINGs + carry-overs"): RED d350019b → a0bf2fd9 (who_calls plugin callers `line: null` + tool text), f8783074 (`aa_ma_sanitize_lines` — stdlib python3 -I -S, Cc/Cf/Co/Cs/Zl/Zp + invalid UTF-8 → `?`, stricter ASCII fallback + WARN; used by predicted-vs-actual and commit-drift; `<unpredicted-files>` framed untrusted in verify-impl + code-reviewer; rc-4 docstring).
- code-reviewer: 0 / 0 / 3 INFO (sanitising is output-only — comparison uses raw paths; `$(cat)` drops trailing blank lines/NUL; redundant `[[:cntrl:]]` pass; no test pins raw-path comparison).
- security-auditor: 0 / 0 / 5 INFO (fixed code string, paths only on stdin; no bypass found live incl. fallback; combining marks/homoglyphs out of scope; log line has no path content).
- Tests at f8783074: TESTS_VERIFIED passed=3401; bats 855/0.

## Verdict: PASS_WITH_WARNINGS (round 2 clean; stop rule: 2 rounds)

# Milestone 11: Gate-computed `IMPACT_VERIFIED` (T7) — post-impl review (§6.8)

- Date: 2026-10-27 · Audit-Profile: full · budget normal · window 169e4e81..a360c80c (45 commits, base = aa_ma_milestone_base)
- Unpredicted (§6.3, to code-reviewer as untrusted paths): TODOS.md, docs/lessons.md, tests/codemem/test_critical_path_globs.py — each has an `Impact-Explained:` line.

## Summary

| Agent | CRITICAL | WARNING | INFO | Verdict |
|---|:-:|:-:|:-:|---|
| code-reviewer | 0 | 7 | 5 | WARN |
| security-auditor | 0 | 3 | 5 | WARN |
| tdd-sequence-auditor | 1 | 0 | 1 | FAIL (mechanical) → disputed |
| context7-evidence-auditor | 0 | 0 | 1 | PASS |
| future-proofing-auditor | 0 | 1 | 8 | WARN |
| **Total** | **1** | **11** | **20** | |

## code-reviewer (0 / 7 / 5)
- W `enforce.has_gate_approval` is a second Python fence scanner beside `grammar.scan_fences` (they differ on indent and closer text) — doc why (shell parity) or align.
- W `impact.py` `git archive` timeout 60.0 unnamed.
- W KISS: `_api_diff` 67 lines, five jobs — split.
- W SRP: impact.py holds codemem adapter + API diff + classification + CLI — split when next touched (non-blocking).
- W reference.md As-built 11.3 kv line lists `api-break` kind (never emitted); misses `api_break=`, `derived_cp_file=`.
- W missing why: absolute-PATH-only codemem; T7 constant comment unreadable.
- I `_ARROWS` behaviour fix for coverage's milestone_contract_paths (note it); I §6.3 shell co-change ignores an approved Cochange-Threshold override (document); I 3 unpredicted files = process artefacts / forced tripwire.

## security-auditor (0 / 3 / 5)
- W A04 grandfathering read from the branch's own plan `Created:` → a back-dated plan skips fence 4 once IMPACT_CUTOVER is real; read it from the merge-base plan.
- W A04 API diff skipped still passes and the IMPACT_VERIFIED provenance line omits `api_diff=` — record it.
- W A03 fence 4 prints repo file names and `reason` raw — sanitize with `aa_ma_sanitize_lines`.
- I CRITICAL_PATH_REVIEW marker matched anywhere in a line — anchor to the line start; I IMPACT_CUTOVER sentinel (M14.1); I repo-local lib sourced first (out of scope); I `origin/*` refs movable by `update-ref` (reword comment); I `extractall(filter=)` needs Python ≥ 3.11.4 (TypeError on 3.11.0–3.11.3; fails closed via 127).

## tdd-sequence-auditor — FAIL (mechanical), disputed
- C 733069a3 `style(enforce)` (src/, 14:04) precedes the first tests/ commit 5bec8ac8 (14:17). Style-only (3 docstrings, Ste-approved L-065 at 11.0). Without it: PASS — every RED/GREEN pair test-first (11.2–11.5, §6.6).

## context7-evidence-auditor — PASS (0 / 0 / 1)
- No new deps; griffe Context7 evidence at provenance CONTEXT7 (11.4). I tarfile `filter="data"` (stdlib, PEP 706, 3.11.4+).

## future-proofing-auditor (0 / 1 / 8)
- W git archive timeout unnamed (same as code-reviewer).
- I "fences 2–4" / "FOURTH" ordinals; I shell `5)` mirrors EXIT_NOT_APPLICABLE; I API_PACKAGES not derived from the workspace; I IMPACT_CUTOVER sentinel → M14.1 AC; I regex purpose comments; M13 to list `aa-ma-impact` / IMPACT_VERIFIED / CHANGELOG.

## User Override Decisions
| # | Finding | Decision | Note |
|---|---|---|---|
| 1 | tdd-sequence CRITICAL (733069a3) | dispute | Ste 2026-10-27: style-only pre-RED commit to a Contract file, approved at 11.0; convention learned: a pre-RED style-only commit is not a TDD breach (land it before the base next time) |

WARNING fixes chosen (Ste): security 3 (+ CPR anchor, Python ≥ 3.11.4 / TypeError), small hygiene (timeout constant, why comments, has_gate_approval docstring, reference.md kv line, regex comments), `_api_diff` split, API_PACKAGES pinned to the workspace. To TODOS: impact.py module split (SRP), §6.3 override parity.

## §6.8 round 2 (fix only, window a360c80c..e10760a8, 2026-10-27)
- Round-1 fixes reviewed: RED 5a4b75fa → efece88f, c4cb3d4f (merge-base `Created:`, api_diff in IMPACT_VERIFIED, sanitised fence 4 output, line-anchored CPR marker, TypeError skip, API_PACKAGES pinned), e10760a8 regen.
- code-reviewer: 0 / 2 / 3 — W `MILESTONE_TITLE` written raw into fence provenance lines; W IMPACT_VERIFIED format in gate-fences.md, SKILL.md, spec, engineering-standards, reference.md lacks ` api_diff=`; I usage rc 5 → 2 for a bad --base; I `GIT_ARCHIVE_TIMEOUT_S` comment placement; I untyped `griffe` parameter.
- security-auditor: 0 / 2 / 2 — W a plan absent at the base (renamed task dir, new plan) is still dated by its working copy; W `_breaks` logs the skip reason raw; I impact-verified.sh header "grandfather check runs first" holds only with a valid --base; I any `git show` error read as "new on the branch".
- Fixes (Ste: all 4 WARNINGs + INFOs, then stop): RED f3fdb172 → GREEN 525083b6 — `_plan_date`: presence via `ls-tree` (literal pathspecs), a plan absent at the base is dated no earlier than the base commit (`%cs`) and never undated, any other git error is usage 2; `_breaks` logs `_printable(reason)`; `fence_init` sets `MILESTONE_TITLE_LOG` (sanitised) for fence 3 and 4 provenance lines, raw title kept for approval lookups; ` api_diff=<summary>` in all five format statements; header reworded; constant comment moved. Regen c41c89a5 (header only); CPR addendum 4a49e871.
- Verification at 4a49e871: pytest 3504 passed / 2 skipped; bats 655/655 (at 525083b6); fence 1 PASS (4 conditions); fence 2 DIAGRAM PASS edges=25; fence 3 TESTS_VERIFIED passed=3504; fence 4 dogfood (--ignore-cutover) rc 1 → named tests/hooks/test_tests_verified.bats unpredicted → one Impact-Explained line → rc 0 unexplained=0.
- Not re-reviewed by agents (stop rule: 2 rounds).

## Verdict: PASS_WITH_WARNINGS (round 2 fixes applied; stop rule: 2 rounds)
