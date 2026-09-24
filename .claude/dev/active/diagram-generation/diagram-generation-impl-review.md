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
