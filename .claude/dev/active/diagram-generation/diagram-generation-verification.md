# Verification Report: diagram-generation

Generated: 2026-09-22 | Mode: automated | Revision: 8

## Summary

- CRITICAL: **22 findings, 22 resolved, 0 outstanding**
- WARNING: 36
- Refuted on testing: 2 agent claims + 1 of my own refutations reversed
- Overall: **PASS**

Plan grew 973 → 1530 lines across 8 revisions.

## Angle 1 — Ground-Truth Audit

29 claims checked against `d4d657f`. Confirmed: `python_ast.py:113-120,370-377`;
`resolver.py:131-134`; `db.py:12,41,104-106,166`; `schema.sql:26`;
`cli.py:269-309`; `mcp_tools/__init__.py:52,61,991`; `mermaid_lint.py:57,60-63,76,266,281`;
`html.py:12,16,21,22` (mermaid **11.17.2**); `.gitignore:17-18,34`;
`grammar.py:74-83,264`; `tui/model.py:203`; `aa-ma-scribe.md:145,153`; 7 gate questions.

- **[CRITICAL] `.importlinter` has 3 contracts, not 4-going-on-5.** Plan A2 said "4
  kept" and M2-AC4 said "5 kept"; they could not both hold. `lint-imports` → `3 kept,
  0 broken`; M2 makes it 4. **Fixed:** the criterion now asserts the *named* contract,
  never a total.
- [WARNING] `gate.py` positional arg is at `:462`, not `:465`. Substance correct.

## Angle 2 — Assumption Challenge

- **[CRITICAL] A3 was false.** `prototype/diagram-generation-3/demo.html` does not
  validate the delegated DOM listener — 3 handlers, all `b.onclick` on buttons
  (`:158-160`), zero `addEventListener`/`.closest(`/SVG node handling. **Fixed:** M12
  gains `Prototype-Required: YES` and the mechanism list is marked `[proven]` /
  `[UNPROVEN]` per item.
- **[CRITICAL] `ensure_schema()` downgrades a newer DB.** Reproduced: v3 → 2, table
  survives. **Fixed:** M1 adds an `apply_schema()` version guard and
  `Critical-Path: data-xform`. *(I initially refuted this finding incorrectly — see
  "Refuted" below.)*
- [VERIFIED] `Prototype-Required:` at milestone level IS honoured independently of
  sub-steps (`gate.py:205-209`, `:428`; consumed at `execute-aa-ma-milestone.md:613-621`).
- [VERIFIED] stdlib-sqlite3 dependency-freedom holds (`grep -rn codemem src/aa_ma/` empty).
- [WARNING] `.codemem/` path is hardcoded (`cli.py:33`), no env var.

## Angle 3 — Impact Analysis

- **[CRITICAL] Seven milestones wrote tests to `packages/codemem-mcp/tests/`, which
  does not exist.** CI would never run them; local `pytest` would. **Fixed:** 16 paths → `tests/codemem/`.
- **[CRITICAL] `schema.sql` must stay v1** (`test_schema_v2.py:57`). **Fixed:** v3 moved to `db.MIGRATIONS`.
- **[CRITICAL] `src/aa_ma/deps.py` breaks `test_leaf_contract.py`**, which computes its
  expectation live via `pkgutil.iter_modules`. **Fixed:** M7 adds `.importlinter`.
- **[CRITICAL] §6.7 fence order** — the `awk` at `aa-ma-gate-python.bats:46` takes the
  FIRST ```bash fence; 58 tests across 3 suites depend on it. **Fixed:** hard fence-order constraint + before/after capture.
- **[CRITICAL] MCP registration lives in `claude-code/codemem/mcp/server.py`**, and
  `test_mcp_server.py:47,50` pin the tool count at 12. **Fixed:** added to M13.
- **[CRITICAL] `lint-imports` is absent from CI** (0 occurrences). The new contract
  would be local-only. **Fixed:** M2 adds the step.
- **[CRITICAL] Angle 6 renumbering breaks 6 tests** (`test_plan_verification_angle6.py:29-31`).
  **Fixed:** appended as check 8, never renumbered.
- **[CRITICAL] `rules/python.yml` does not exist** — 8 YAMLs, Python is native. **Fixed.**
- [WARNING] `CURRENT_SCHEMA_VERSION` 2→3 invalidates pending WAL replay intents.
- [WARNING] `understand-codebase` `references/` inventory is pinned — content edits free, add/remove not.

## Angle 4 — Criteria Falsifiability

43/79 falsifiable on first pass (54%). Rewritten: M3-C1 ("parses as mermaid" named no
command and resolved to neither pass nor fail under L-012), M3-C2/C3 (numbers
invalidated by this plan's own later milestones), M4-C1/C3/C4/C5 (hardcoded integers
and a claim about test *style*), M5-C4 (`-> list[str]` had no channel for a verdict),
M6-C1 (**`git diff` has no line-exclusion mode**), M6-C6 (`gh run list --limit 1` is
racy), M7-C1 ("resolve correctly"), M7-C6 (a markdown command has no exit code),
M8-C5 (breaks when this plan is archived), M9-C1/C4/C5/C6, M10-C4/C5, M11-C1/C2/C3/C5
(the Contract ships no executable), M12-C2 ("offline" contradicts CDN loading),
M12-C4 (false on HEAD), M13-C1/C5.

Final: **0 banned terms** across 88 criteria.

## Angle 5 — Fresh-Agent Simulation

- **[CRITICAL] No stepwise implementation plan (element #2).** Milestones were the
  smallest unit, yet §8 and two M4 criteria referenced sub-steps defined nowhere; no
  `Mode:`, no `Gate:`. **Fixed:** §4 adds 63 TDD-ordered sub-steps, 44 AFK / 19 HITL.
- **[CRITICAL] M1 criterion 3 was unassignable to a table** — `sqlite3.connect` is a
  call, but `file_edges` is `CHECK (kind IN ('import'))`, so read against the table
  criterion 2 established it was unsatisfiable. Chain depth and asname-map shape were
  also unspecified. **Fixed:** names `edges`, pins three exact fixture values, specifies
  `ast.unparse` and `import_aliases: dict[str, str]`.
- **[CRITICAL] The plan never named the repository or a setup command.** **Fixed:** §0.

Only a context-free reader could find these: every other angle knew AA-MA convention
and read past the gap.

## Angle 6 — Specialist Audit (SQLite + Engineering Standards)

**Lens A — SQLite**

- **[CRITICAL] The composite PK prevents zero duplicates, and the v1 precedent is
  already broken in production.** Live index: 6516 rows / 3258 distinct; histogram
  `[(2, 3258)]`, zero singletons; 0 rows with both `dst` columns set. SQLite treats
  NULLs as distinct in the backing unique index, so `INSERT OR IGNORE`
  (`resolver.py:159`, `indexer.py:310`, `journal/wal.py:447`) suppresses nothing.
  Cause is a cold-build double write (`indexer.py:409`, then `:410-412`). **Fixed:**
  `file_edges` uses two partial unique indexes (verified: 3 identical inserts → 1 row);
  `SELECT DISTINCT` pushed into both `graph.py` and `draw/cut.py`; stored defect → `TODOS.md`.
- **[CRITICAL] DDL omitted `IF NOT EXISTS`**, which `db.py:45-46` requires because
  `migrate()` does not roll back DDL. **Fixed**, plus M1 corrects the false docstring.
- **[CRITICAL] `ON DELETE CASCADE` does not cover edit-in-place**, the dominant path —
  the `files` row survives an edit, so CASCADE never fires. **Fixed:** explicit
  `DELETE ... WHERE src_file_id = ?`, and AC5 re-pointed at `refresh_index`, since
  `build` deletes `files` rows first and would pass trivially.
- [WARNING] Missing `CHECK`, missing reverse index. **Fixed** — column order mirrors
  `schema.sql:74-75`. Single-value `CHECK (kind IN ('import'))` dropped as a one-way door.

**Lens B — Engineering Standards**

- **[CRITICAL] Theme 1 contradicted itself.** Element #12 still named four milestones
  for `hook-modification` after M2 and M7 gained it — the declaration desynchronised
  from its own plan inside one editing session, violating themes 1 and 4 at once.
  **Fixed:** §2a is the single source; element #12 references it instead of restating.
- **[CRITICAL] M13 should carry `Critical-Path`** — it edits
  `claude-code/skills/impact-analysis/SKILL.md`, the mechanism the §5 Execution
  Checklist names for a HARD row. **Fixed.**
- [WARNING] Theme 4's rationale named the wrong sharpest risk. **Fixed:** now names the
  shared writer path (`ensure_schema()` callers).
- Themes 2, 3, 4, 5, 6 assessed as honestly claimed. **Doctrine gap accepted with Ste:**
  M11 widens the §1 table to cover `.github/workflows/**`.

## Refuted

- `forbidden` rejects `source_modules = aa_ma` — **false.** Appending the exact stanza
  gave `Contracts: 4 kept, 0 broken`. The "shared descendants" caveat applies only when
  source and forbidden share a root.
- `migrate()` alone downgrades a v3 DB — **false**, but irrelevant: `ensure_schema()`
  is the production path and it does. **My refutation of the downgrade finding was
  itself wrong** and is retracted; the finding stands and is fixed.

## Revision History

- v8: 2026-09-22 — 22 CRITICAL / 36 WARNING → PASS (0 outstanding)
