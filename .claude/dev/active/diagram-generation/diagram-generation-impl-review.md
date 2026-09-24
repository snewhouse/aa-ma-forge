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
