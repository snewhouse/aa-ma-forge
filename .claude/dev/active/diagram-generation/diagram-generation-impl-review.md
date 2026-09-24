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
