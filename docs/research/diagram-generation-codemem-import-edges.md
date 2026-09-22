# Can codemem persist file-level import edges and qualified external callees?

**Created:** 2026-09-22
**Author:** Claude (aa-ma-researcher), charting effort diagram-generation Ticket 1
**Reviewed-Through-Date:** 2026-09-22
**Valid-Through:** 2026-Q4 (invalidated by any change to `packages/codemem-mcp/src/codemem/{parser,resolver.py,indexer.py,incremental.py,storage/schema.sql}`)
**Sources:** (all at commit 75f5491 unless noted)
- `packages/codemem-mcp/src/codemem/parser/python_ast.py` — import collection, call-name truncation
- `packages/codemem-mcp/src/codemem/parser/ast_grep.py` — rule-suffix dispatch, no edges, no imports
- `packages/codemem-mcp/src/codemem/parser/rules/*.yml` — which languages have import/call rules
- `packages/codemem-mcp/src/codemem/resolver.py` — imports consumed transiently, bare-name matching
- `packages/codemem-mcp/src/codemem/indexer.py` — bulk insert, WAL payload
- `packages/codemem-mcp/src/codemem/incremental.py` — refresh path
- `packages/codemem-mcp/src/codemem/storage/schema.sql`, `storage/db.py` — edges DDL, MIGRATIONS
- `packages/codemem-mcp/src/codemem/mcp_tools/queries.py`, `pagerank.py`, `journal/wal.py` — consumers
- `docs/codemem/symbol-id-grammar.md` — v1 kind-markers
- `tests/codemem/{test_resolver,test_python_parser,test_indexer,test_ast_grep_parser,test_wal_replay_roundtrip}.py`
- `.codemem/index.db` — live index, built at `5e2bf54` (2026-04-17, per `.codemem/last_sha`), not HEAD

## Answer

Not today, but both are tractable. (a) `ParseResult.imports` is collected for Python only and consumed transiently by the resolver; nothing writes `kind='import'` rows, and the `edges` table has no file-level endpoint (`src_symbol_id NOT NULL` → symbol). Persisting file→file imports needs either a synthetic per-file module symbol (grammar change, touches symbol counts) or a new `file_edges` table (schema v3, recommended). Six of eight ast-grep rule files have an `*-import` rule, but it captures no metavariable and the wrapper silently drops it. (b) The dotted callee is truncated in the Python call visitor (`func.attr` only); the resolver then matches by bare name. Keeping the qualified form is a ~15-LOC parser/resolver change that flips two pinned assertions. ast-grep languages emit no call edges at all, so there is nothing to qualify there yet.

## Evidence

### What is stored today (live DB, `sqlite3 .codemem/index.db`)

- `PRAGMA user_version` = 2; `edges` kinds: `call` 1460 only. 1024 of those have `dst_symbol_id IS NULL` (unresolved), 436 resolved.
- `symbols` kinds: `class` 140, `function` 215, `method` 324 — zero module/var/import rows. `files`: python 58, bash 10.
- Top `dst_unresolved`: `execute` 129, `connect` 69, `run` 42, `exists` 33, `close` 32, `get` 30 … `LIKE '%.%'` → 0 rows. No qualified names exist.
- Caveat: the DB is from `5e2bf54` (2026-04-17); counts are indicative, not HEAD-exact.

### (a) Import edges

- Python imports are collected at module top-level only: `python_ast.py:113-120`. `import a.b` → `a.b`; `from a.b import c` → `a.b`; `from . import x` is dropped (`node.module` is `None`, line 119) and `ImportFrom.level` is ignored — relative imports lose their leading dots.
- `ParseResult.imports` is consumed only in `resolver.py:131-134`, building a transient `resolved_targets: set[str]` used to scope callee matching. It is never inserted. `resolve_cross_file_edges` emits only `ue.kind` rows from `unresolved_edges` (`resolver.py:150,153`), i.e. `call`.
- `_resolve_import` (`resolver.py:55-92`) already returns a target *file path* for each import — the file→file mapping exists in memory today and is thrown away.
- `edges.src_symbol_id INTEGER NOT NULL REFERENCES symbols(id)` (`schema.sql:63`); `dst_symbol_id` also FK symbols (`:64`). Edges are symbol→symbol only; there is no file node. The schema comment promises `'call'|'import'|'inherit'` (`:58,66`) and `dst_unresolved` "e.g. 'requests.get'" (`:65`) — neither is honoured by any writer.
- No module-level symbol is ever emitted: `python_ast.py:193-197` emits only `FunctionDef`/`ClassDef` at top level; grammar v1 has three markers and no module marker (`symbol-id-grammar.md:39-47`). A file→file edge therefore needs either a synthetic module symbol or a new table.
- `indexer.py:355` serialises `imports` into the WAL payload, but `journal/wal.py` never reads the key (grep `imports` → no match); replay restores only `symbols` + intra-file `edges` (`wal.py:393,433-451`).
- Incremental refresh re-parses only dirty files and calls the resolver with `parses=dirty` (`incremental.py:220-233`); `_apply_file_delta` (`:337-433`) touches symbols only, never edges. Any import-edge writer must delete-then-reinsert per dirty file here, or import rows go stale after refresh.
- ast-grep: `*-import` rules exist for Go (`go.yml:30-33`), Java (`java.yml:29-32`), JavaScript (`javascript.yml:27-30`), Rust (`rust.yml:20-23`), Tsx (`tsx.yml:45-48`), TypeScript (`typescript.yml:50-53`) — all are bare `kind:` matches with no `$NAME`/source capture. Ruby (`ruby.yml`) and Bash (`bash.yml`) have none. `_KIND_BY_RULE_SUFFIX` has no `-import` entry (`ast_grep.py:62-71`, comment line 70: "imports + calls are edges — handled separately, no Symbol emission"), so `_rule_suffix` returns `None` and the match is skipped at `ast_grep.py:239-241`. `_build_parse_result` returns `ParseResult(symbols, edges)` with `imports` defaulting to `[]` (`:306`). The matched `text` is retained in `_SgMatch.text` (`:99,136`), so the module specifier is recoverable, but `parse_sg_output` reads only `NAME`/`name` metavariables (`:119-123`).
- `build_import_map` ignores non-`.py` paths (`resolver.py:44-45`) — the four resolution strategies are Python-dotted-module specific. TS `./b`, Go `"pkg/x"`, Rust `crate::x` need per-language path resolution that does not exist.
- Existing consumers already filter `kind = 'call'`: `WHO_CALLS_CTE` (`queries.py:30,36`), `BLAST_RADIUS_CTE` (`:50,57`), PageRank (`pagerank.py:81-82`). Adding `kind='import'` rows to `edges` would not pollute them. PageRank does iterate *all* symbol ids (`pagerank.py:70`), so a synthetic module symbol would appear in rankings.

### (b) Qualified callee

- Truncation point: `python_ast.py:370-377`. For `ast.Attribute` callees, `n = func.attr` (line 371) discards `func.value`; the name is recorded only when the receiver is a plain `ast.Name` (`:374-377`), so `conn.execute()` → `execute`, `sqlite3.connect()` → `connect`, and `self.conn.execute()` (receiver is an `Attribute`) is dropped entirely. `ast.unparse(func)` would yield the full dotted form; `_unparse` exists at `:247-252`.
- The resolver matches `callee` by bare name against `target_lookup[path][name]` (`resolver.py:140-146`) and writes the same bare string on the unresolved branch (`:153`). Keeping the qualified form requires either a second field on `CallEdge` (`python_ast.py:58-68`) or `rsplit(".", 1)[-1]` in the resolver before lookup.
- `CallEdge`/`unresolved_edges` are not in the WAL payload (`indexer.py:346-354` serialises `edges` only), so no replay change is needed.
- Pinned assertions that flip: `tests/codemem/test_resolver.py:131-133` (`dst_unresolved == "get"`) and `:210-211` (`"get" in names`). `test_python_parser.py:23-30` region (`test_external_call_emits_no_edge`) asserts `result.edges == []` for `requests.get` — unaffected (checks intra-file list).
- ast-grep: `*-call` rules capture nothing (`go.yml:35-38`, `java.yml:34-37`, `javascript.yml:32-35`, `ruby.yml:27-30`, `rust.yml:25-28`, `tsx.yml:50-53`, `typescript.yml:55-58`) and the wrapper emits zero edges by design (`ast_grep.py:299-304`). No receiver/object is captured. Qualified callees for these languages presuppose call edges that do not exist; the enclosing-function could be inferred with the same line-range technique used for containers (`ast_grep.py:229-236`).

## What changes are needed

Two designs for (a); **B recommended** — additive migration, no symbol-count or grammar churn, matches the file→file granularity a diagram wants.

| # | File | Change | Est. LOC | Tests affected |
|---|------|--------|---------:|----------------|
| A1 | `parser/python_ast.py:193-197` | Emit synthetic `kind='module'` Symbol per file (scip `codemem <pkg> /<file>#<stem>`) so import edges have a src/dst symbol | 15 | `test_python_parser.py:40,68,79,99`, `test_ast_grep_parser.py:173` (symbol counts), `test_wal_replay_roundtrip` symbol equality (should still hold), PageRank ordering tests |
| A2 | `docs/codemem/symbol-id-grammar.md:39-47` | Document module marker (v2 grammar) | 10 | none |
| B1 | `storage/schema.sql` + `storage/db.py:41,104-106` | `CURRENT_SCHEMA_VERSION = 3`; `_MIGRATION_V3_FILE_EDGES`: `file_edges(src_file_id FK files, dst_file_id FK files NULL, dst_unresolved TEXT, kind TEXT, PK(...), CHECK(...))` + two indexes | 25 | `test_schema.py`/`test_schema_v2.py` add v3 case; `test_wal.py` fixtures pass `prev_user_version` (no change) |
| B2 | `resolver.py:127-134` | Return `(target_file or None, imp)` per import and emit `file_edges` rows (`kind='import'`) alongside call edges; include unresolved imports as `dst_unresolved=imp` | 25 | `test_resolver.py` new cases; existing pass |
| B3 | `incremental.py:220-233` | `DELETE FROM file_edges WHERE src_file_id IN (dirty)` before re-resolve | 8 | `test_incremental.py` new case |
| B4 | `journal/wal.py:393-451` | Optional: replay `imports` from payload into `file_edges` (payload already carries it, `indexer.py:355`) | 15 | `test_wal_replay_roundtrip.py` (currently compares intra-file only) |
| P1 | `parser/python_ast.py:113-120` | Preserve `ImportFrom.level` (prefix `.`×level) and handle `from . import x` | 8 | `test_resolver.py:190-200` (adds cases) |
| P2 | `parser/python_ast.py:370-377` | Record `ast.unparse(func)` as `dst_unresolved` (qualified) and keep bare attr for matching — add `dst_qualified: str \| None` to `CallEdge` (`:58-68`) or split in resolver | 10 | `test_resolver.py:131-133,210-211` flip to `"requests.get"`; `test_python_parser.py` region 150-230 unaffected |
| P3 | `resolver.py:140-153` | Match on bare name, write qualified on unresolved branch | 5 | as P2 |
| S1 | `parser/rules/{go,java,javascript,rust,tsx,typescript}.yml` | Add `has: {field: source\|path, pattern: $SOURCE}` capture to each `*-import` rule (field name is per-grammar: `source` for JS/TS `import_statement`; Go `import_spec.path`; Java/Rust the declaration text — verify against tree-sitter node fields) | 6 files × 4 | `test_ast_grep_parser.py` new fixtures |
| S2 | `parser/rules/{ruby,bash}.yml` | New `rb-import` (`call` with method `require`/`require_relative`) / `sh-import` (`source`/`.` command) rules | 2 × 8 | as S1 |
| S3 | `parser/ast_grep.py:119-123,239-241,306` | Read `$SOURCE`; map `-import` suffix to an imports list instead of skipping; pass `imports=` to `ParseResult` | 20 | `test_ast_grep_parser.py:112-122` (rule-id handling) |
| S4 | `resolver.py:35-52,55-92` | Per-language path resolution for non-Python specifiers (relative `./x`, extensionless, `index.ts`, Go module paths, Rust `crate::`) | 40-80 | `test_resolver.py` new cases |
| S5 | ast-grep call edges + receiver (`*-call` rules + `ast_grep.py:299-304`) | Out of Ticket 1 scope; only needed if (b) must cover ast-grep languages — requires enclosing-function inference | 60+ | new |

Rough totals: Python-only (B1-B3 + P1-P3) ≈ 80 LOC across 5 files, 2 assertions flip. Adding ast-grep import edges (S1-S4) ≈ 100-140 LOC plus 8 YAML edits; the resolver (S4) is the uncertain part.

## Not pursued

- `_apply_file_delta` never re-inserts intra-file `fp.result.edges` for ADDED symbols on refresh (`incremental.py:337-433`) — pre-existing gap outside the question; would affect import-edge staleness reasoning only if design A is chosen.
- Exact tree-sitter field names for each language's import node (`source` vs `path` vs none) — needs a live `sg --debug-query` per grammar; not verified here.
- Whether `.codemem/index.db` should be rebuilt at HEAD before Ticket 1 uses counts — DB is 5 months stale (`5e2bf54`).
- `kind='inherit'` edges (also promised at `schema.sql:58`, also unimplemented) — same plumbing as import edges via `ClassDef.bases`, not asked.
- `_CALL_EXCLUDE` (`python_ast.py:30-37`) suppresses builtins like `open`; a qualified-name policy might want `pathlib.Path.open` kept — policy question, not code.
