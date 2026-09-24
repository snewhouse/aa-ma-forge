# Impl Review Report: diagram-generation / Milestone 1

**Milestone:** Milestone 1: codemem `file_edges` (schema v3) + qualified callees
**Audit-Profile:** code-only (all 5 agents)
**Window:** f8e44ed..9f72847 (fixes landed in cbf0564)
**Date:** 2026-09-24

## Summary

| Agent                     | CRITICAL | WARNING | INFO | Verdict |
|---------------------------|:--------:|:-------:|:----:|---------|
| code-reviewer (+§6.6)     |    0     |    2    |  5   | WARN    |
| security-auditor          |    0     |    0    |  6   | PASS    |
| tdd-sequence-auditor      |    0     |    0    |  0   | PASS    |
| context7-evidence-auditor |    0     |    0    |  0   | PASS    |
| future-proofing-auditor   |    0     |    1    |  4   | WARN    |
| **TOTAL**                 |  **0**   |  **3**  |**15**| **PASS_WITH_WARNINGS** |

§6.6 simplification review (reuse / quality / efficiency) was folded into the
code-reviewer brief rather than dispatched as 3 more agents over a ~140-line diff.

## Code Review (code-reviewer agent)

### Findings
- **WARNING — efficiency/DRY** `resolver.py`: every import was resolved twice (parse-set map for call edges, DB-wide map for `file_edges`). **FIXED cbf0564** — `_persist_import_edges` returns `{src: targets}` reused by call-edge resolution. Same-tree base vs head: resolved call edges 1227 = 1227, symbols 1550 = 1550.
- **WARNING — schema-shape change (L-006 class)** `python_ast.py`: `edges.dst_unresolved` now stores dotted callees (`requests.get`, `numpy.array`, `self.conn.execute`) instead of bare attrs. **ACCEPTED, intended** (it is M1's goal). No query tool reads `dst_unresolved` (grep); unresolved count on this repo 2109 -> 2349. Recorded in context-log.
- INFO — per-file DELETE in loop. **FIXED** (single `executemany`).
- INFO — `import_aliases` optional with one caller. **FIXED** (required).
- INFO — `file_edges_src` index overlaps the partial unique index. **KEPT** — the plan specifies it for unpredicated forward traversal (M3 `cut`).
- INFO — `test_schema_v2.py` fixture name `v2_db` now migrates to current; plan's `test_schema.py` "+ v3 case" not added. **ACCEPTED** — literal pin lives at `test_file_edges.py::test_current_schema_version_is_3`; v3 cases live in `test_file_edges.py`. Rename is churn.
- INFO — scope matches the Files list; `incremental.py` unchanged by design.

## Security (security-auditor agent)

### Mechanical pre-check (security-static-check.sh): PASS

### Semantic findings
6 INFO, 0 WARNING. PRAGMA f-string takes an `int` read from SQLite; all resolver SQL parameterised; parsed identifiers are charset-bounded by the AST. **Carried forward:** renderers (M3+) must escape/quote node labels themselves — do not rely on parser charset.

## TDD Sequence (tdd-sequence-auditor agent)

### Verdict: PASS

### Evidence
First tests/ commit 7925b38 (10:45:46) precedes first src commit e6026d4 (10:47:25). Second RED pair 567dba8 -> 3787633. e4dd3be is covered by `TestPersistence` from 7925b38. Mutation check: disabling the `apply_schema` guard turns both `TestDowngradeGuard` tests red.

## External Library Evidence (context7-evidence-auditor agent)

### New PyPI dependencies in milestone diff
None.

### Major version bumps in milestone diff
None.

## Future-Proofing (future-proofing-auditor agent)

### Findings
- **WARNING** — 7 literal `3` schema-version asserts in `test_file_edges.py`. **FIXED cbf0564** — track `db.CURRENT_SCHEMA_VERSION`; one deliberate pin kept. The downgrade test captures the version *before* monkeypatching (a naive replace would have asserted the downgrade).
- INFO — "eight tables" in `docs/codemem/migration-from-index.md`. **FIXED** — count dropped.
- INFO — `docs/codemem/ARCHITECTURE.md` lacked v3. **FIXED**.
- INFO — version-tagged comment on `CURRENT_SCHEMA_VERSION`; `range(3)` in dedup test. Accepted.

## User Override Decisions

No CRITICAL findings — no override panel required.

| Severity | Finding | Decision | Rationale |
|---|---|---|---|
| — | — | — | — |

## Revision History
- 2026-09-24: initial review; 3 WARNINGs — 2 fixed in cbf0564, 1 accepted as the milestone's intended change.

---

# Impl Review Report: diagram-generation / Milestone 2

**Milestone:** Milestone 2: `aa_ma.render.graph` sqlite seam + import contract + ADR-0014
**Audit-Profile:** code-only (all 5 agents) + targeted re-run (code-reviewer, security-auditor) after an accepted CRITICAL
**Window:** d0f3063..74dfcbb (review) · fixes 2421e50..ae1e97a
**Date:** 2026-09-24

## Summary

| Agent                     | CRITICAL | WARNING | INFO | Verdict |
|---------------------------|:--------:|:-------:|:----:|---------|
| code-reviewer (+§6.6)     |    1     |    2    |  4   | BLOCKED → fixed |
| security-auditor          |    0     |    1    |  4   | WARN → fixed |
| tdd-sequence-auditor      |    0     |    0    |  0   | PASS    |
| context7-evidence-auditor |    0     |    0    |  1   | PASS    |
| future-proofing-auditor   |    0     |    1    |  4   | WARN → fixed |
| **Re-run** code-reviewer  |    0     |    2    |  3   | PASS_WITH_WARNINGS → fixed |
| **Re-run** security       |    0     |    0    |  3   | PASS → 2 INFO fixed |
| **FINAL**                 |  **0 open** | **0 open** | — | **PASS_WITH_WARNINGS** |

## Code Review
- **CRITICAL — "never raises" breach** `graph.py:77`: `_stale_paths` caught only `FileNotFoundError`; NotADirectoryError / PermissionError / ELOOP / TypeError escaped `open_graph` and leaked the connection. **ACCEPTED by Ste → FIXED 0dd464b** (outer `except Exception` closes conn; per-row OSError/TypeError/ValueError → STALE). RED first in 2421e50.
- WARNING — scope: `tests/codemem/test_install_and_cli.py` edited outside the Files list. **ACCEPTED** — forced by the new contract (the old test asserted the 3-contract total); recorded in context-log.
- WARNING — two tests each spawned `lint-imports`. **FIXED 2421e50** — the named-contract check lives once, in `TestImportLinterContract`, now with `\b0 broken`.
- INFO — magic `3` → `_MAX_SHOWN` (**fixed**); MISSING conflates corrupt/absent and STALE misses never-indexed files + same-second edits (**documented in ADR-0014**).
- Re-run WARNINGs: no regression tests for symlink/loop/permission (**added in the RED commit before ae1e97a**); `resolve()` ran before containment (**fixed ae1e97a** — absolute/`..` rejected pre-resolve). Re-run INFOs: non-int mtime → MISSING (**fixed**, now one stale row), `Path(repo_root)` outside guard (**fixed**), conn ownership (**documented**).

## Security
- WARNING — unconfined DB-sourced paths stat'd (`/etc/x`, `../x`, symlinks). **FIXED** — confinement + tests with far-future mtime so they cannot pass for the wrong reason (L-023).
- INFO — `trusted_schema = OFF` (**added**); control chars in reason (**fixed**, `_printable`); TOCTOU resolve→stat (accepted: leaks one mtime comparison, needs repo write access).
- Out of scope, pre-existing: `security.yml` has no top-level `permissions:` block and pins actions by tag. Candidate for a separate hardening change.

## TDD Sequence — PASS
ca90667 (tests) 38s before 550312a (src); fix rounds each RED-first (2421e50 → 0dd464b; RED commit → ae1e97a).

## External Library Evidence — PASS
No new deps; `import-linter>=2.0` pre-existing dev dep (pyproject.toml:49).

## Future-Proofing
- WARNING — `docs/codemem/ARCHITECTURE.md` "defines two contracts" (4 exist). **FIXED 0dd464b**.
- INFO — seam hard-codes codemem table names. **Mitigated**: `tests/codemem/test_file_edges.py::TestRenderSeamOnRealIndex` runs the readers on a real `build_index` output, so a rename fails at test time.

## User Override Decisions

| Severity | Finding | Decision | Rationale |
|---|---|---|---|
| CRITICAL | `open_graph` "never raises" breach, graph.py:77 | accept | Ste: fix now — contract stated in ADR-0014 |

## Revision History
- 2026-09-24: 1 CRITICAL accepted and fixed; targeted re-run clean of CRITICALs; all WARNINGs fixed or recorded.

---

# Impl Review Report: diagram-generation / Milestone 3

**Milestone:** Milestone 3: `codemem draw` emitter, layered cuts L0–L3
**Audit-Profile:** code-only (all 5 agents)
**Window:** d985aa0..0e6966b (review; excludes 75f8d09 [ad-hoc] CI and 3d30b21, another session's docs) · fixes 8289371
**Date:** 2026-09-24

## Summary

| Agent                     | CRITICAL | WARNING | INFO | Verdict |
|---------------------------|:--------:|:-------:|:----:|---------|
| code-reviewer (+§6.6)     |    0     |    4    |  5   | WARN → fixed |
| security-auditor          |    0     |    1    |  4   | WARN → fixed (verified inert on real render) |
| tdd-sequence-auditor      |    0     |    0    |  1   | PASS (3 RED→GREEN pairs) |
| context7-evidence-auditor |    0     |    0    |  3   | PASS |
| future-proofing-auditor   |    0     |    1    |  6   | WARN → fixed |
| **TOTAL**                 |  **0**   |  **6**  |**19**| **PASS_WITH_WARNINGS** (all 6 WARNINGs fixed) |

## Code Review
- WARNING — `codemem draw --hops -1` / node-id collision raised a traceback. **FIXED**: argparse non-negative type; `ValueError` -> exit 2 via `parser.error`.
- WARNING — cut.py duplicates aa_ma.render.graph SQL. **MITIGATED, not merged**: aa_ma may not import codemem (ADR-0014 contract), so one shared module is impossible by design. Added `TestDrawSeamParity` (tests/codemem/test_file_edges.py): draw L2 == graph.py readers on one real index. The claimed drift (self-import filter) cannot occur — `_resolve_import` never resolves a file to itself.
- WARNING — two 4-way call joins in cut.py. **FIXED**: file-level calls projected from `_symbol_calls`.
- WARNING — `--level L3 --kind import` silently empty. **FIXED**: ValueError -> exit 2.
- INFO — `incremental.py:216` relies on cascade: **checked** — it uses `db.connect()` (FK ON) and never toggles it; not affected by the §3.5 defect.
- INFO — plan Contract API lacked `kind=`: **FIXED** in plan.md. AC2 as measured is `--kind call` (default `both` gives 5/8): recorded below. L3 self-loops for recursion: **deliberate**, commented.

## Security
- WARNING — `%%{init}%%` directive injection via file-name labels (demonstrated: theme restyle; themeCSS `url()` beacon under the html CSP's `img-src https:`). **FIXED**: `% { } \`` entity-encoded. Real render of the payload: label shows literally, theme unchanged, URL appears only as visible label text, never in `<style>`.
- INFO — no XSS (securityLevel protected keys held; click/href inert); node ids are hashes; edge kinds are literals; DELETE f-string over a fixed tuple.

## TDD Sequence — PASS
cut 32adf2c→e82add7 (68s) · mermaid+CLI d0b9564/5f5176d→b677fde (87s) · indexer fe90f6d→0e6966b (106s) · review fixes RED commit → 8289371.

## External Library Evidence — PASS
No new deps. Mermaid sigil + entity behaviour verified on mermaid 11.17.2 by bisection and SVG read-back (`q#quot;t#35;h#lt;a#gt;b.py` renders `q"t#h<a>b.py`).

## Future-Proofing
- WARNING — `codemem draw` missing from `claude-code/codemem/commands/codemem.md` and `docs/codemem/migration-from-index.md`. **FIXED** (reference section; migration doc points at `codemem --help` instead of a list).
- INFO — CLI choices duplicated enums (**fixed**, derived from `Level`/`KINDS`/`DIRECTIONS`); bare `3` (**fixed**, `MIN_SCHEMA_VERSION`); mermaid-version coupling (**fixed**, note at `MERMAID_VERSION`).

## User Override Decisions
No CRITICAL findings — no override panel required.

## Revision History
- 2026-09-24: 6 WARNINGs, all fixed in 8289371 (RED-first); security fix verified on a real renderer.

---

# Impl Review Report: diagram-generation / Milestone 4

**Milestone:** Milestone 4: Plugin-surface extractor
**Audit-Profile:** code-only (all 5 agents)
**Window:** 27fa477..c6346e7 (review) · fixes 29d1bd3 (RED) → 711e8b7
**Date:** 2026-09-24

## Summary

| Agent                     | CRITICAL | WARNING | INFO | Verdict |
|---------------------------|:--------:|:-------:|:----:|---------|
| code-reviewer (+§6.6)     |    1     |    7    |  6   | BLOCKED → fixed |
| security-auditor          |    0     |    0    |  3   | PASS (INFOs fixed) |
| tdd-sequence-auditor      |    0     |    0    |  3   | PASS (RED reproduced in a worktree) |
| context7-evidence-auditor |    0     |    0    |  0   | PASS (no dependency change) |
| future-proofing-auditor   |    0     |    2    |  4   | WARN → fixed |
| **TOTAL**                 |  **1**  |  **9**  |**16**| **PASS_WITH_WARNINGS** after fixes (CRITICAL accepted + fixed) |

## Code Review
- CRITICAL — mechanism duplication: `_nodes` and `_owner` were two rules for node identity; `hooks/README.md` / `commands/sub/x.md` became drawn-but-unclassified edge sources. **FIXED**: node set = owners of the walked files (`test_one_rule_decides_node_identity`).
- WARNING — orphans as bare stems collide across kinds (`understand-codebase` is a command AND a skill). **FIXED**: `kind:stem`; AC4 test strips to the plan's bare set and asserts no duplicates (Ste's decision).
- WARNING — hook literal `\b` matched after a hyphen (`test-aa-ma-foo.sh`) and the fixed prefix hid hooks named otherwise. **FIXED**: `(?<![\w.-])` lookbehind, on-disk + external hook names as alternatives, convention kept so missing hooks read DANGLING.
- WARNING — `/cmd.` at sentence end dropped. **FIXED**: `.` blocks only when followed by a filename char.
- WARNING — non-UTF-8 install.sh raised. **FIXED**: tolerant decode.
- WARNING — missing `claude-code/` gave a silent empty graph. **FIXED**: error.
- WARNING — matchers with `.*`/`(`/`|` silently dropped rows. **FIXED**: `[^"]*?` matcher; each quoted row of the `AA_MA_HOOKS=( )` block must parse, else an error naming the row number.
- WARNING — orphans never drawn. **FIXED**: `from_edges(..., isolated=)`; live Cut 84 nodes (80 + 4 edgeless orphans). `Level.L2` documented as a namespace seed only.
- INFO — `Cut.dropped` not surfaced: **FIXED** (error when > 0). Not pursued: `Skill("x")`/`Skill(x, args)` forms (none in corpus), bold `**/aa-ma**` glob ambiguity, `hooks/x.sh` vs `hooks/lib/x.sh` collapse (install.sh addresses hooks by basename), NodeKind enum (stringly `kind:stem` kept; `_stem()` helper added).

## Security
- INFO — quadratic hook regex on `aa-ma-aa-ma-…` (1 MB ≈ 90 s). **FIXED**: lookbehind + `{0,64}` cap; `test_hook_regex_is_linear_on_hostile_input`.
- INFO — symlinked files followed out of the tree. **FIXED**: `_owner` rejects symlinks; test.
- INFO — strict decode of install.sh. **FIXED** (above).
- Labels: regex char classes exclude `" % { } \``; file-name labels escaped by `mermaid.escape_label` (M3); node ids are hashes.

## TDD Sequence — PASS
beec7c1 (RED, ImportError reproduced) → c6346e7 (127 s). Fixes: 29d1bd3 (RED, 11 failing) → 711e8b7. INFO: the golden was generated by the independent scratch prototype before the src existed — recorded in the 4.2 Result Log.

## External Library Evidence — PASS
No new PyPI dependency or version bump.

## Future-Proofing
- WARNING — `engineering-standards.md:44` (41 = 17/20/4) deferral to M14 was not wired into M14's scope. **FIXED**: Sub-step 14.3 now names the rule; true figure 42 = 17/21/4.
- WARNING — hook prefix rot. **FIXED** (above).
- INFO — allowlist rot: **FIXED** — `test_every_allowlisted_external_is_still_referenced`. Docstring count removed. Row-drop **FIXED** (above). Self-certifying regen after the first golden: the regeneration diff is the required review step (docstring); tasks.md wording corrected.

## User Override Decisions
| Severity | Finding | Decision | Rationale |
|---|---|---|---|
| CRITICAL | two node-identity rules, plugin_surface.py `_nodes`/`_owner` | accept | Ste: fix now |
| WARNING | orphan id shape | kind:stem, test maps to bare | Ste |
| all WARNING/INFO | batch | fix all now | Ste |

## Revision History
- 2026-09-24: 1 CRITICAL accepted and fixed; all 9 WARNINGs and 6 INFOs fixed or recorded; golden diff = orphan ids only (edges unchanged).

---

# Impl Review Report: diagram-generation / Milestone 5

**Milestone:** Milestone 5: Captions sidecar
**Audit-Profile:** code-only (all 5 agents)
**Window:** bbdc743..25d70fe (review) · fixes 6f39194 (RED) → 185453c
**Date:** 2026-09-24

## Summary

| Agent                     | CRITICAL | WARNING | INFO | Verdict |
|---------------------------|:--------:|:-------:|:----:|---------|
| code-reviewer (+§6.6)     |    0     |    3    |  5   | WARN → fixed |
| security-auditor          |    0     |    2    |  3   | WARN → fixed / recorded downstream |
| tdd-sequence-auditor      |    0     |    0    |  3   | PASS (both REDs reproduced) |
| context7-evidence-auditor |    0     |    0    |  0   | PASS (stdlib json only) |
| future-proofing-auditor   |    0     |    6    |  5   | WARN → fixed / recorded downstream |
| **TOTAL**                 |  **0**  | **11**  |**16**| **PASS_WITH_WARNINGS** |

## Code Review
- WARNING — slashless dir key reported as deleted. **FIXED**: finding reason "a directory: the key needs a trailing /".
- WARNING — dir caption over planned `(new)` files read ORPHAN. **FIXED**: planned paths use the same containment rule → UNKNOWN.
- WARNING — `start_ids` re-implemented `_names`. **FIXED**: `start_ids = _names(start, label) or ancestor`.
- INFO — empty/unknown `@` keys, duplicate keys: **FIXED** in `load()`. Render test now asserts PASS or skips on UNKNOWN (**FIXED**). mermaid→captions coupling: kept (pure `start_ids` only). M8 fixture `classDef` line and plugin-surface captions: **recorded** as 8.2 / 6.3 obligations.

## Security
- WARNING — caption prose unescaped for M6/M12. **RECORDED** as 6.3 (one escaping helper outside the fence) and 12.2 (`<` JSON island, `textContent`, `</script>` test) obligations. No caption text reaches the mermaid: `class` lines carry hash ids only.
- WARNING — `RecursionError`/`OSError` escaped `load()`. **FIXED** (tests: deep nesting, chmod 0).
- INFO — duplicate keys (**FIXED**), no size cap (accepted: repo-committed file).

## TDD Sequence — PASS
1d6a3ec → 2a884e5 (130 s); 405f46c → 8f9edd3 (52 s); 6f39194 → 185453c. Widened expectations in 8f9edd3 are the recorded equal-or-contained spec change, still exact equality.

## External Library Evidence — PASS
No dependency change; stdlib `json` only.

## Future-Proofing
- WARNING W1 — M6 AC4 vs whole-file `--check`. **RESOLVED by Ste**: `--check` compares mermaid fences only; recorded in 6.1 with an `@start`-is-drift test.
- WARNING W2 — explorer caption matching. **RECORDED** in 12.2.
- WARNING W3 — `docs/architecture/` boundary unenforced. **RECORDED** in 6.1 (writer path guard, tested).
- WARNING W4 — `ORPHAN_CAPTION` had no owner. **RECORDED** in 6.2 (`--check`, `git ls-files`, plan §13 `(new)` set).
- WARNING W5 — prose escaping. **RECORDED** (see Security).
- WARNING W6 — 5.2 Result Log said 21 tests. **FIXED** (20).
- INFO — keyword-only `captions` (**FIXED**), `::` keys (**FIXED**), `4px` single use (accepted), forge test uses empty planned set (accepted: forge has no planned captions).

## User Override Decisions
No CRITICAL findings. Ste: fix all now; M6 `--check` = fences only; downstream obligations recorded in tasks.md.

## Revision History
- 2026-09-24: 11 WARNINGs — 6 fixed (RED-first), 5 recorded as named M6/M8/M12 obligations; 0 CRITICAL.
- 2026-09-24 (post-gate, Ste "fix all now"): RED ddb0f40 → GREEN 61eb4e4. M5: `escape_prose`, `json_island`, `check_generated_target` built and tested for the M6/M12 obligations (those sub-steps now call them); 1 MiB sidecar cap; `START_STYLE` constant; forge-test docstring on planned captions. M4 INFOs: quoted/spaced/argument `Skill()` and quoted `subagent_type` forms; `**/cmd**` is not a glob; `NodeKind` StrEnum; duplicate hook names and nested un-owned files reported in `errors`. Golden unchanged; live errors []. Still open by necessity (the consuming code does not exist yet): `ORPHAN_CAPTION` wiring in M6 `--check` (6.2), the `classDef` line in M8's fixture (8.2), explorer caption parity (12.2). Kept by design: mermaid→captions import (pure `start_ids` only).

---

# Impl Review Report: diagram-generation / Milestone 6

**Milestone:** Milestone 6: Living doc + `--check` + CI drift job + ADR-0016 → release `v0.15.0`
**Audit-Profile:** full (all 5 agents)
**Window:** 31446b3..153e8b9 (review) · fixes 30d2c88 (RED) → f3ca3af + docs
**Date:** 2026-09-24

## Summary

| Agent                     | CRITICAL | WARNING | INFO | Verdict |
|---------------------------|:--------:|:-------:|:----:|---------|
| code-reviewer (+§6.6)     |    1     |    3    |  6   | CRITICAL disputed; WARN → fixed |
| security-auditor          |    0     |    2    |  5   | WARN → fixed |
| tdd-sequence-auditor      |    0     |    0    |  1   | PASS (RED reproduced; AC5 red at d42cb50 = L-025) |
| context7-evidence-auditor |    0     |    0    |  0   | PASS (pyyaml already a dev dep; action pins reused) |
| future-proofing-auditor   |    0     |    4    |  9   | WARN → fixed |
| **TOTAL**                 |  **1**  |  **9**  |**21**| **PASS_WITH_WARNINGS** (CRITICAL disputed by Ste) |

## Code Review
- CRITICAL — scope: `docs/lessons.md` (L-025) outside M6 Files. **DISPUTED (Ste)**: lessons are mandated by the self-improvement rule; convention learned — lesson commits are exempt from a milestone's Files list.
- WARNING — captions-block masking accepts any hand text. **FIXED**: every masked line must match `^(- |Start here: )[^<>]*$`.
- WARNING — stamp never validated. **FIXED**: line 1 must match the stamp regex; sha/date still unchecked.
- WARNING — duplicate `git ls-files` helper. **FIXED**: `indexer.git_tracked_files` (now public) reused.
- INFO — views mode ignored `--hops/--direction/--kind/--include-tests`: **FIXED** (defaults None → any explicit value refused). ValueError prefix: **FIXED** (`who`). Repo root = cwd (`--repo-root` absent): **kept** — matches the default db location; recorded. Stale-index detection locally: **not pursued** (CI builds fresh; L-024 in CONTRIBUTING). CI UNKNOWN-as-pass: **not pursued** (build step precedes; low risk). `_head_sha` consolidation: **not pursued** (3 call sites, different error needs).

## Security
- WARNING — symlinked `docs/`/`docs/architecture` let `--write` escape the repo. **FIXED**: the generated dir is compared unresolved vs resolved; tests for both link points.
- WARNING — hand edits on line 1 / captions block passed. **FIXED** (above).
- INFO — plugin-surface names from file stems rendered raw. **FIXED**: `escape_prose`. CI supply chain: job fine (`pull_request`, read-only token, pinned); unpinned `pip install uv` is the existing pattern — recorded. Check-to-write TOCTOU: local-attacker only — recorded.

## TDD Sequence — PASS
552d663 → d42cb50 (144 s); AC5 satisfied by 6fab78e. Fixes: 30d2c88 (8 RED) → f3ca3af.

## External Library Evidence — PASS

## Future-Proofing
- WARNING — no regeneration obligation after M6. **FIXED**: standing obligation line on M7–M14.
- WARNING — two regenerations, remedy names one. **FIXED**: `scripts/regen-generated.sh` (build, `--write`, golden, `--check`); golden-test message and CONTRIBUTING point to it; codemem's own REMEDY stays generic for consumer repos.
- WARNING — contributors never told. **FIXED**: CONTRIBUTING "Generated files".
- WARNING — README hand-listed the views. **FIXED**: links the generated index.
- INFO — `ViewSpec.scope` unused: **kept** (plan registry contract). L2 fallback: **FIXED** (level required). `NO_SHA`: **FIXED**. Stamp UTC / parent-sha semantics: **documented** in ADR-0016. ADR measured basis: **annotated**. M14.3 re-hardcoding: **reworded** to cite the generated doc. CI literal duplication / Dependabot: **not pursued** (existing pattern, out of scope).

## User Override Decisions
| Severity | Finding | Decision | Rationale |
|---|---|---|---|
| CRITICAL | docs/lessons.md outside Files (153e8b9) | dispute | Ste: lessons are rule-mandated process artefacts |
| all WARNING/INFO | batch | fix all now | Ste |
| WARNING | regen duty | one script + standing obligation | Ste |

## Revision History
- 2026-09-24: 1 CRITICAL disputed; 9 WARNINGs fixed (RED-first where code); docs regenerated by `scripts/regen-generated.sh`; golden unchanged.

---

# Milestone 7 — `Dependencies:` grammar + Milestone graph + advisory

**Window:** dc4e90e..3b2dd32 · **Audit-Profile:** code-only · **Agents:** code-reviewer (incl. §6.6 reuse/quality/efficiency), security-auditor, tdd-sequence-auditor, context7-evidence-auditor, future-proofing-auditor · **Verdict:** PASS_WITH_WARNINGS (after fixes)

## Summary
| Agent | CRITICAL | WARNING | INFO | Verdict |
|---|:-:|:-:|:-:|---|
| code-reviewer | 1 | 4 | 6 | CRITICAL accepted → fixed |
| security-auditor | 0 | 2 | 3 | WARN → fixed |
| tdd-sequence-auditor | 0 | 0 | 3 | PASS |
| context7-evidence-auditor | 0 | 0 | 0 | PASS (no new deps) |
| future-proofing-auditor | 0 | 0 | 4 | PASS |
| **TOTAL** | **1** | **6** | **16** | **PASS_WITH_WARNINGS** |

## Code Review
- CRITICAL — mechanism duplication: `execute-aa-ma-milestone.md` §6.2 and `execute-aa-ma-full.md` (5.1, 5.3.B) HALTed on unmet `Dependencies:` while the new §5.1 advisory never blocks (Ticket 16). **FIXED**: §6.2 defers to the §5.1 advisory; full.md sets ACTIVE first, then runs the advisory; bats pins "no HALT" on both files.
- WARNING — unbounded `_span`. **FIXED**: `MAX_SPAN = 100`; wider range keeps only the endpoint, which `check` reports.
- WARNING — `_field_re` diverged from `tui.parser._field_pattern` on day one. **FIXED**: one `grammar.field_pattern` (stdlib, linear) used by tui and deps; both copies deleted.
- WARNING — `_head` duplicated gate `_own_text`. **FIXED**: `grammar.own_text` used by gate and deps; gate golden re-verified byte-identical.
- WARNING — stringly-typed label test / free-str `kind`. **FIXED**: `_fields` returns an explicit milestone-level flag; `Kind = Literal[...]`.
- INFO — `docs/M2.md` read as step `M2.md`: **FIXED** (`/` in lookbehind). `, and` dropped a number: **FIXED**. Slug false exemption (`follow-up Milestone 9`): **kept** — advisory-only; recorded. `M5-M7`, `1.5-2.1` shapes: **kept** — `check` flags them; absent from corpus. Repeated splits (0.139 s on the 136 KB corpus max): **not pursued**. Private `_NUM_S` import: **FIXED** (`grammar.NUMBER_BODY`). Launcher uv notice: **FIXED**.

## Security
- WARNING — `_field_re` quadratic on padded lines (14.2 s at 50k; 12.6 s end-to-end advisory). **FIXED**: `^[ \t]*(?:-[ \t]*)?…(\S(?:.*\S)?)[ \t\r]*$`; regression test < 0.5 s on 50k pads; launcher wrapped in `timeout ${AA_MA_DEPS_TIMEOUT:-30}` where coreutils `timeout` exists.
- WARNING — range expansion OOM (`1-99999999`). **FIXED** (MAX_SPAN); `check` CLI output capped at `MAX_FINDINGS = 200` + "… N more".
- INFO — mermaid label injection: none found (10 hostile titles render as single nodes). Hardening **FIXED**: `<`/`>` → `#lt;`/`#gt;`. Shell quoting clean. Repo-local lib lookup order: pre-existing pattern, recorded.

## TDD Sequence — PASS
6d01a0b (RED, ModuleNotFoundError) → b59ff60; 18b13b6 (RED, 3/3 bats not ok) → e9c6cdd. Fix round: ecf5323 (12 pytest + 3 bats RED; range test hung) → fix commit. INFO: bats test 4 landed with its implementation; b59ff60 left 2 writer tests red until e9c6cdd (never pushed red — L-025).

## External Library Evidence — PASS
No manifest changed; deps.py is stdlib-only.

## Future-Proofing
- INFO — "29 false failures" in the deps.py docstring: **FIXED** (dated context-log reference). `claude-code-foundations.md` aa-ma-parse.sh line: **FIXED** (names `aa_ma_deps`). CLAUDE.md tree (gitignored, local): **kept** — not tracked. 9 copies of the lib-locator loop: existing convention, recorded. Pre-existing drift noted for M14: `SECURITY.md` "21 skills" vs 22 on disk (aa-ma-research, 6479d21).

## User Override Decisions
| Severity | Finding | Decision | Rationale |
|---|---|---|---|
| CRITICAL | §6.2 / execute-aa-ma-full HALT on Dependencies | accept → fixed | Ste: fix now; Ticket 16 advisory-only |
| all WARNING/INFO | batch | fix all now | Ste |

## Revision History
- 2026-09-24: CRITICAL accepted and fixed; 6 WARNINGs fixed RED-first (ecf5323); gate output re-verified byte-identical (205 invocations, sha 5444d16692fe1107); pytest 1379 / 2 skipped, bats 210/210.

---

# Milestone 8 — `PHANTOM_EDGE` sigil grammar

**Window:** 54c2354..038c212 · **Audit-Profile:** code-only · **Agents:** code-reviewer (incl. §6.6), security-auditor, tdd-sequence-auditor, context7-evidence-auditor, future-proofing-auditor · **Verdict:** PASS_WITH_WARNINGS (after fixes)

## Summary
| Agent | CRITICAL | WARNING | INFO | Verdict |
|---|:-:|:-:|:-:|---|
| code-reviewer | 3 | 3 | 3 | CRITICALs accepted → fixed |
| security-auditor | 0 | 4 | 2 | WARN → fixed |
| tdd-sequence-auditor | 0 | 0 | 2 | PASS |
| context7-evidence-auditor | 0 | 0 | 0 | PASS |
| future-proofing-auditor | 0 | 1 | 5 | WARN → fixed |
| **TOTAL** | **3** | **8** | **12** | **PASS_WITH_WARNINGS** |

## Code Review
- CRITICAL — sigil claims silently skipped (chained, `&`, `-- "@x" -->`, `--->`, `<-->`, `--o`, trailing `& D`). **FIXED**: `_EDGE_RE` must consume the whole line; any line with an `@` in an edge-label slot it cannot parse → `UNKNOWN: unparsed sigil edge form`; `%%` comments skipped. 8 parametrized forms tested.
- CRITICAL — false call edges: `from . import x, y; y.run()` bound to x.py:run too (reproduced). **FIXED**: parser records `from_imports` (module, level, names); submodules derive from the module's OWN resolution (package dir), `from .. import x` climbs a level; `sub.run()` binds only in `sub`. Tests: receiver scoping, parent level, no independent suffix match.
- CRITICAL — label→path extraction duplicated and drifted (no `_inside`). **FIXED**: shared `_bracketed` / `_labels` / `_label_paths` used by STALE_PATH and sigil endpoints; endpoint outside the repo → `UNKNOWN: endpoint outside the repo: <p>`, never probed.
- WARNING — relative level ignored; alias names suffix-matched. **FIXED** (above).
- WARNING — `SIGIL_LABEL_RE` dead in production, AC5 test skipped sigil plans. **FIXED**: removed; AC5 now asserts every completed plan, no skip.
- INFO — quoted `|` inside a label: **FIXED**. Last declaration wins: **FIXED**. Graph queries on non-OK status: **FIXED** (early return).

## Security
- WARNING — host-file existence oracle via `../` endpoint. **FIXED** (`_inside`).
- WARNING — terminal escapes from `(new)` labels reach CLI output. **FIXED**: every printed message goes through `graph.printable` (now public); label truncated to `_MAX_TOKEN`.
- WARNING — partial v3 index crashed `aa-ma-lint-views`. **FIXED**: `sqlite3.Error` → UNKNOWN "unreadable; run `codemem build`".
- WARNING — quadratic `_node_labels` / `_unwrap`. **FIXED**: bounded look-back on `str.find` scanning; two-index peel. Hostile cases (node flood, 200k paren label) under budget.
- INFO — SQL read path fixed-text; resolver has no filesystem access.

## TDD Sequence — PASS
e8e4cfe (33 RED) → d80e3d5 (58 green). Fix round: a674e78 (RED: 14 lint + 3 resolver) → fix commit. INFO: hostile/isolated tests landed with the fix.

## External Library Evidence — PASS

## Future-Proofing
- WARNING — sigil vocabulary spelled in two packages, untested. **FIXED**: test pins codemem `KINDS` ∪ `NodeKind`−RULE ⊆ `SIGILS`; generated `docs/architecture/*.md` lint with no LABEL_UNKNOWN. `SIGILS` built from `_EDGE_READERS` + `_PLUGIN_SIGILS` (one spelling each).
- INFO — timing threshold named `_LINEAR_BUDGET_S`. M13 carry-forward (delete plugin UNKNOWN branch) and M14 carry-forward (engineering-standards + ADR-0010) written into tasks.md. CHANGELOG `## Unreleased` M8 entry added.

## User Override Decisions
| Severity | Finding | Decision | Rationale |
|---|---|---|---|
| CRITICAL | unparsed sigil forms silently pass | accept → fixed | Ste; L-012 |
| CRITICAL | false call edges via submodule targets | accept → fixed | Ste |
| CRITICAL | duplicated label→path extraction / oracle | accept → fixed | Ste |
| all WARNING/INFO | batch | fix all now | Ste |

## Revision History
- 2026-09-24: 3 CRITICAL accepted and fixed; all WARNINGs fixed RED-first (a674e78); import edges vs pre-M8: +28, all genuine, none lost; pytest 1443 / 2 skipped, bats 210/210, lint-imports 4/4, `draw --check` OK.
