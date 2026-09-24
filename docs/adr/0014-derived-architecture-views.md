# 0014. Derived architecture views: aa_ma reads codemem's graph through a stdlib-sqlite3 seam

**Status:** Accepted
**Date:** 2026-09-24
**Deciders:** Stephen Newhouse (sole maintainer)
**Tags:** `aa-ma`, `codemem`, `diagrams`, `render`, `import-linter`, `architecture`

## Context and Problem Statement

ADR-0010 made the plan's mermaid Architecture View (element #13) a hand-authored
statement of **intent**, with markdown as the only source. Nothing checks that
intent against the code: a §13 edge `A --> B` can name a dependency that does not
exist, and the diagram still passes lint. `diagram-generation` wants those edges
verified (`PHANTOM_EDGE`, M5+) and wants whole-repo diagrams generated from code.

The code graph already exists in codemem's SQLite index, and since schema v3
(diagram-generation M1) it holds file-level `import` edges in `file_edges`
alongside symbol-level `call` edges in `edges`. The question is: **how does
`aa_ma` read that graph without making `aa_ma` depend on codemem?**

`aa_ma` is the plugin's gate/lint core. It runs in every AA-MA session;
codemem is an optional workspace member with its own dependencies (ast-grep,
the MCP server). Coupling the core to it would make an optional tool a hard
requirement of the gate.

## Decision Drivers

- `aa_ma` must keep working when codemem is absent, old, or out of date.
- The coupling must be **pinned**, so it cannot later be "simplified" into a
  convenient `from codemem import ...`.
- The read must never raise into a gate or lint path; a failure is a status.
- No new runtime dependency for `aa_ma`.

## Considered Options

1. **Import codemem directly** — call `codemem.mcp_tools` / query helpers from `aa_ma.render`.
2. **Call the codemem MCP server** — go through the tool protocol at lint time.
3. **Subprocess `codemem query`** — shell out and parse the output.
4. **Read the SQLite file with stdlib `sqlite3`** — couple to the on-disk schema only.

## Decision Outcome

**Chosen option: 4 — a read-only stdlib-`sqlite3` seam, `aa_ma.render.graph`.**

- The contract between the packages is the **on-disk schema**, versioned by
  `PRAGMA user_version`. The seam requires `>= 3` (the version that introduced
  `file_edges`), not codemem's Python API.
- `open_graph(repo_root)` opens `.codemem/index.db` read-only
  (`file:...?mode=ro`) and returns a `GraphHandle(status, reason, conn)`, where
  `status` is one of `OK | MISSING | SCHEMA_TOO_OLD | STALE`. It **never raises**:
  a missing or unreadable file is `MISSING`, an old schema is `SCHEMA_TOO_OLD`,
  and every `reason` names the remedy (`codemem build`).
- `STALE` means an indexed file is newer on disk than its recorded `mtime`, or no
  longer exists. It is **advisory**: the handle keeps its connection and the graph
  stays readable. Callers decide whether behind-the-tree data is acceptable.
- `import_edges()` and `call_edges()` return `set[(src_path, dst_path)]`, both
  via `SELECT DISTINCT` (see Consequences). Call edges are projected from
  symbols to files; same-file calls are dropped.
- The coupling is enforced by the import-linter contract
  **`aa-ma-never-imports-codemem`** (`forbidden`, source `aa_ma`, forbidden
  `codemem`), and `uv run lint-imports` now runs in CI (`security.yml`,
  codemem-smoke job). Before this ADR, `lint-imports` ran in CI zero times, so
  every contract in `.importlinter` was local-only.

### Relationship to ADR-0010

This ADR **extends ADR-0010 and supersedes nothing**. Markdown stays the only
source of the plan's *intent*; the codemem graph becomes a second, derived source
of *fact*. The two meet in verification: a hand-authored §13 edge is checked
against the graph, and a disagreement is a lint finding, not an automatic
rewrite of the plan.

### Consequences

- **Good:** `aa_ma` has no codemem dependency, and the build fails if one appears.
  The seam degrades to a status instead of an exception, so lint and gate paths
  are unaffected when codemem is absent.
- **Good:** schema evolution is explicit. A codemem change that breaks the seam
  must bump `user_version`, which the seam checks.
- **Bad:** the seam hard-codes codemem table and column names (`files`, `symbols`,
  `edges`, `file_edges`). A column rename in codemem without a version bump would
  break it at runtime. Mitigation: codemem's migrations are forward-only and
  additive, and the seam's tests build fixtures that mirror only the columns it reads.
- **Bad:** staleness costs one `stat` per indexed file per `open_graph`. Measure on a
  large repo (M13) before caching.
- **Known limits of `STALE`:** it detects edited and deleted indexed files, not
  *new* files that were never indexed (a diagram can silently omit a new module), and
  it compares whole seconds (codemem stores `int(st_mtime)`), so an edit in the same
  second as indexing is missed.
- **`MISSING` covers "unusable", not only "absent":** a corrupt, locked or otherwise
  unreadable file is also `MISSING`; the `reason` distinguishes them. Split out an
  `UNREADABLE` status only if a caller needs to branch on it.
- **The index file is data, not trusted input.** `files.path` values are confined to
  the repo: NULL, absolute or `..` paths count as `STALE` without touching the
  filesystem, and a symlink leaving the tree is `STALE` and never followed by `stat`.
  Paths quoted in a `reason` have control characters replaced. The connection runs with
  `PRAGMA trusted_schema = OFF`, and an `OK`/`STALE` handle's connection is owned
  (and closed) by the caller.
- **Known defect, not fixed here:** codemem's v1 `edges` table stores exact duplicate
  rows. Its composite primary key contains the two mutually-exclusive `dst` columns,
  one always NULL, and SQLite treats NULLs as distinct, so `INSERT OR IGNORE` never
  fires (measured 2026-09-22: 6516 rows, 3258 distinct). The readers use `DISTINCT`,
  which is correct at no extra cost. Repairing `edges` is a data migration over a
  rebuildable, gitignored index and is left to a separate effort; `file_edges` (v3)
  avoids the bug with partial unique indexes.

### Why not the others

- **Option 1** makes an optional package a hard dependency of the gate core, and it
  is exactly the "simplification" the contract exists to prevent.
- **Option 2** needs a running MCP server at lint time and adds a protocol hop
  to answer what is a single SQL query.
- **Option 3** needs codemem installed on `PATH` and a parser for its text output,
  which is a more fragile contract than a versioned schema.

## References

- ADR-0010 — Architecture Views and markdown-only source (extended, not superseded)
- `src/aa_ma/render/graph.py`, `tests/render/test_graph.py`
- `.importlinter` contract `aa-ma-never-imports-codemem`
- `docs/research/diagram-generation-codemem-import-edges.md`
- `.claude/dev/active/diagram-generation/` — plan M1 (schema v3), M2 (this seam)
