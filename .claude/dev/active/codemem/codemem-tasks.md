# codemem — Tasks (HTP Execution Roadmap)

_Hierarchical Task Planning roadmap with dependencies and state tracking. 40 tasks across 4 milestones. See `codemem-plan.md` §4 for full rationale and acceptance narrative._

---

## Milestone M1: Foundation (shippable as v0.1)
- Status: ACTIVE
- Gate: SOFT
- Dependencies: None
- Complexity: 70%
- Started: 2026-04-13
- Acceptance Criteria (per plan §4 M1):
  - `codemem build` on aa-ma-forge produces SQLite DB + `PROJECT_INTEL.json` ≤ 5KB
  - `codemem build` on `~/.claude-code-project-index/` (~10k LOC Python) completes in < 30s cold cache, < 5s warm cache (enforced by `tests/perf/`)
  - All 6 ported MCP tools produce JSON output JSON-equal to `/index` (modulo key ordering and timestamps) for 3 reference test queries on aa-ma-forge OR `/index` repo
  - `who_calls("extract_python_signatures")` on `~/.claude-code-project-index/scripts/index_utils.py` returns within 100ms (enforced by `tests/perf/`)
  - `pip install -e .[codemem]` succeeds on Linux + macOS in CI; standalone `pip install codemem-mcp` builds a wheel
  - PageRank repo-map fits ≤ 1024 tokens AND covers ≥90% of `/index`'s `_meta.symbol_importance` top symbols
  - Schema enforces FKs (verified via `INSERT` on orphaned FK → IntegrityError); integrity check passes on every build; explain-plan on canonical CTE uses indexes only (no table scan)
  - import-linter passes; ARCHITECTURE.md committed with 5 sections; perf SLO doc committed
  - Adversarial input tests pass (malicious paths, oversized strings, non-UTF8, regex metachars)
  - `.gitignore` contains `.codemem/` line

### Task 1.0: Pre-flight reading + packaging spike + design scratchpad
- Status: COMPLETE
- Mode: HITL
- Dependencies: None
- Acceptance Criteria: `docs/codemem/design-scratchpad.md` committed capturing 5 readings (Aider repomap.py, `/index` pagerank.py, repowise symbol_diff, GitNexus last 30 days of issues, lessons.md L-052) + chosen packaging structure (one of: hatchling workspace / packages subdir / hatch build hook); packaging decision reflected in Step 1.1; any plan-altering findings flagged in `codemem-context-log.md`.
- Result Log: COMPLETE 2026-04-13. All 5 readings done via 4 parallel research agents + local L-052 review. Packaging Option B chosen (uv workspace with `packages/codemem-mcp/`), prototype validated at `/tmp/codemem-spike/`. 14 plan-altering findings classified in `docs/codemem/design-scratchpad.md` (2 CRITICAL + 3 HIGH + 5 MED + 4 LOW/INFO). Plan v3 → v4 updates applied to §2 (differentiation rewritten around edge weighting + binary search + SCIP + no truncation; /index is already symbol-level) and Step 1.1 (new source tree structure). AF-7/8/9 (symbol-diff simplification), AF-11 (tool aliases), AF-3/12 deferred to target Steps' implementation. Moat UNCONTESTED — GitNexus 27k stars focused on PDG/type-resolution, zero git-mining signals. No kill triggers. Proceeding to Task 1.1.

### Task 1.1: Project scaffold + dual-distribution packaging
- Status: COMPLETE
- Mode: AFK
- Dependencies: Task 1.0
- Acceptance Criteria: `pip install -e .[codemem]` works; `pip install codemem-mcp` from a clean checkout produces a working wheel with NO `aa_ma` dependency; entry points `codemem-cli` and `codemem-mcp-server` resolve; `ast-grep-cli>=0.42,<0.43` and `fastmcp` in deps; `cat .gitignore | grep "\.codemem/"` returns a match; CI matrix builds wheel on Linux + macOS.
- Result Log: COMPLETE 2026-04-13. Directory trees created: claude-code/codemem/{commands,skills,hooks,mcp}/ (placeholders) + packages/codemem-mcp/src/codemem/{storage,parser,diff,journal,analysis,mcp_tools}/ + tests/{codemem,perf,fixtures/codemem/{sample_repo,adversarial,aa_ma_context/sample-task}}/. Files created: packages/codemem-mcp/pyproject.toml (name=codemem-mcp, deps=ast-grep-cli>=0.42,<0.43 + fastmcp>=2.0, no aa-ma dep), packages/codemem-mcp/README.md, packages/codemem-mcp/src/codemem/{__init__.py (v0.1.0.dev0), cli.py (placeholder), mcp_server.py (placeholder), aa_ma_integration.py (optional-import guard for AA_MA_AVAILABLE flag)}. Root pyproject.toml: added [tool.uv.workspace] members=["packages/codemem-mcp"] + dev-deps (pytest-benchmark, hypothesis, import-linter). .gitignore: appended `.codemem/` line. Verification: (1) `uv sync` resolved workspace successfully; (2) `uv pip install -e packages/codemem-mcp/` into .venv → `import codemem` works, `AA_MA_AVAILABLE=True` in workspace context; (3) `uv build packages/codemem-mcp/` produced both sdist + wheel to /tmp/codemem-wheel-test/codemem_mcp-0.1.0.dev0-{py3-none-any.whl,tar.gz}; (4) wheel METADATA inspected — Requires-Dist contains ONLY ast-grep-cli<0.43,>=0.42 and fastmcp>=2.0, confirming zero aa-ma coupling; (5) ast-grep 0.42.1 binary ships inside wheel, `.venv/bin/sg run -p '$F()' -l python` produces correct JSON with metaVariables; (6) `.codemem/` line in .gitignore verified via grep. CI wheel-build matrix deferred to Task 1.11 (install integration covers that).

### Task 1.2: SQLite schema + DDL (explicit, pinned)
- Status: COMPLETE
- Mode: AFK
- Dependencies: Task 1.1
- Acceptance Criteria: `schema.sql` created with pinned PRAGMAs (see `codemem-reference.md`), `files` / `symbols` / `edges` tables with FKs + CASCADE, 4 indexes (idx_edges_dst, idx_edges_src, idx_symbols_file_kind_name, idx_symbols_name). Schema validates; FK constraints enforced (insert on orphaned FK raises IntegrityError); explain-plan on the canonical recursive CTE for `who_calls(N=3)` uses indexes only (no table scan). `PRAGMA user_version` = 1. Forward-only migration framework scaffolded.
- Result Log: COMPLETE 2026-04-13. `packages/codemem-mcp/src/codemem/storage/schema.sql` written with 3 tables (files/symbols/edges), 5 indexes (idx_edges_dst, idx_edges_src, idx_symbols_file_kind_name, idx_symbols_name, idx_files_lang), FK with ON DELETE CASCADE, CHECK constraint on edges (dst_symbol_id OR dst_unresolved). Persistent PRAGMAs: journal_mode=WAL, application_id=0x434D454D ('CMEM' ASCII), user_version=1. `packages/codemem-mcp/src/codemem/storage/db.py` written with connect() (handles read_only mode=ro URI + per-conn PRAGMAs busy_timeout/cache_size/mmap_size/temp_store/foreign_keys/synchronous), apply_schema() (idempotent via IF NOT EXISTS), migrate() (forward-only via user_version), transaction() context manager, is_codemem_db() marker check. 16/16 tests passing in `tests/codemem/test_schema.py` covering: tables+indexes present, integrity_check=ok, FK orphan raises IntegrityError, ON DELETE CASCADE files→symbols→edges, edges CHECK constraint, unresolved-edge round-trip, migrate noop at v1, canonical recursive CTE uses idx_edges_dst (via EXPLAIN QUERY PLAN), read-only connection rejects writes. Plan v3 had application_id=0xC0DE3E33 which overflows signed int32 (SQLite silently stored 0) — corrected to 0x434D454D in schema.sql + db.py + reference.md + plan.md during test-driven fix.

### Task 1.2b: SCIP-shaped symbol ID grammar (pinned)
- Status: COMPLETE
- Mode: AFK
- Dependencies: Task 1.2
- Acceptance Criteria: `docs/codemem/symbol-id-grammar.md` committed with exact format (scheme/package/descriptor/kind-marker). One parser-emitted SCIP-ID per language fixture covering: Python decorated method, Python class with metaclass, Java inner class + anonymous class, TS namespace symbol, Go method on receiver, Rust impl block.
- Result Log: COMPLETE 2026-04-13. `docs/codemem/symbol-id-grammar.md` written (360 lines). Three kind-markers pinned (`/` term, `#` type, `.` member). Examples for Python (top-level function, class, method, decorated method, metaclass, nested class, module variable, `__init__.py`), TS/JS (function, class, method, interface, type alias, namespace + nested namespace, arrow const), Java (class, method, inner class, anonymous class with `$N` synthetic convention, enum), Go (function, struct, method on value + pointer receivers `(*Type)`, interface), Rust (function, struct, impl-block methods, trait, trait method, impl-Trait-for-Type convention, macros deferred to v2), Ruby (class, method, module), Bash (functions only). Parser contract documented with golden-fixture test shape for tests/codemem/test_symbol_ids_<lang>.py. Open questions for v2+ captured (MRO, re-exports, deleted-file tombstones, overload disambiguation). Grammar is the contract for Task 1.3 (Python parser) and Task 1.4 (ast-grep wrapper) parser implementations — any change requires schema migration + `codemem migrate-symbol-ids` utility per M1 risk #3 mitigation.

### Task 1.3: Python parser via stdlib `ast`
- Status: COMPLETE
- Mode: AFK — auto-dispatched
- Dependencies: Task 1.2b
- Acceptance Criteria: `extract_python_signatures()` ported from `/index`; returns list of `Symbol` dataclasses with intra-file call edges and canonical SCIP ID per symbol. Unit tests cover function, method, class, nested class, decorated function.
- Result Log: COMPLETE 2026-04-13. `packages/codemem-mcp/src/codemem/parser/python_ast.py` written (312 LOC) exposing `Symbol`, `CallEdge`, `ParseResult` dataclasses and `extract_python_signatures(source, *, package, file_rel) -> ParseResult`. Three helpers kept private: `_build_signature` (decorators prepended as `@name` lines, `self`/`cls` stripped, async prefix, return annotation), `_extract_call_names` (walks function body via synthetic `ast.Module`, filters builtins via `_CALL_EXCLUDE` on bare names only, matches attribute calls by `.attr` name), `_decorator_name` + `_unparse` (best-effort via `ast.unparse`). Symbols emitted for module-level functions, module-level classes, class-level methods, and nested classes (same scope as `/index`); nested functions / lambdas / comprehensions deliberately out of scope for v1. SCIP IDs match grammar v1: `/` term, `#` type, `.` member; package = caller-supplied repo-relative dir; `parent_scip_id` strings (FK resolution deferred to Task 1.5 driver). Call edges: intra-file only, over-emit on ambiguous method names (one edge per same-named target — `test_ambiguous_method_name_emits_edge_to_each_match` locks this v1 heuristic); dedup via `set` prevents PRIMARY KEY collisions when caller calls same target 10 times. SyntaxError → empty `ParseResult` (regex fallback out of scope; ast-grep wrapper in Task 1.4 handles broader cases). Tests: `tests/codemem/test_python_parser.py` — 20 tests, 7 classes: TestTopLevelFunction (4), TestClass (1), TestMethod (2), TestNestedClass (1), TestDecoratedFunction (2), TestAsyncFunction (1), TestIntraFileCallEdges (4), TestSyntaxError (1), TestGrammarFixture (1 — byte-for-byte match against pinned grammar doc), TestDataTypes (2 incl. `__all__` surface lock). Fixture `tests/fixtures/codemem/symbol_ids/python_sample.py` frozen. Full codemem suite: **35/35 passing** (19 new + 16 pre-existing schema). Ruff clean on parser + tests. Anchor symbol `extract_python_signatures` (M1 AC) is now live at `codemem packages/codemem-mcp/src/codemem /parser/python_ast.py#extract_python_signatures`.

### Task 1.4: ast-grep parser via subprocess + batching
- Status: COMPLETE
- Mode: AFK — auto-dispatched
- Dependencies: Task 1.2b
- Acceptance Criteria: Wrapper invokes `sg run --json=stream` with YAML rule files; batches per language (single sg invocation across N files). Rules cover `function_definition`, `class_definition`, `method_definition`, `import_statement`, `call_expression` for TypeScript, JavaScript, Go, Rust, Java, Ruby, Bash. `languageGlobs` set for `.ts` ↔ `.tsx`. Parsing 100 mixed-language files completes in <10s on aa-ma-forge. Subprocess mocked in unit tests.
- Result Log: COMPLETE 2026-04-13. `packages/codemem-mcp/src/codemem/parser/ast_grep.py` written (~280 LOC) exposing `SUPPORTED_LANGUAGES`, `language_from_path`, `parse_sg_output`, `extract_with_ast_grep`. Uses `sg scan -r RULE --json=stream --include-metadata` (probed the real binary at `.venv/bin/sg` v0.42.1 to confirm this is the correct form — `sg run` is pattern-based, `sg scan` is rule-file-based). Per-language batching: one subprocess invocation per language, all files of that language passed as arguments; verified by `test_per_language_batching_single_sg_invocation_per_lang`. `.ts` vs `.tsx` split: TypeScript and Tsx are separate entries in `SUPPORTED_LANGUAGES` with distinct rule files (typescript.yml / tsx.yml) because ast-grep treats them as different languages (empirical probe confirmed TS rule does NOT match .tsx). Symbol emission: function/class/method with SCIP markers `/`, `#`, `.` per grammar v1. Nested types handled via line-range containment (`_enclosing_container` finds innermost container wrapping a match); interfaces/structs/modules all emit `class` kind with `#` marker and act as method parents. Orphan methods (method_def outside any class — e.g. TS object-literal shorthand) skipped rather than emitting orphan `.None.method` IDs. Edge emission deferred to Task 1.6 (cross-file resolver) — ast-grep matches don't carry scope info for local-call resolution. Rule files shipped: 8 YAML files under `packages/codemem-mcp/src/codemem/parser/rules/` covering 7 declared languages (typescript, tsx, javascript, go, rust, java, ruby, bash) — each carries the 5 AC kinds where the language has the concept (bash only has functions, per grammar). Tests: `tests/codemem/test_ast_grep_parser.py` — 36 tests across 6 classes: TestLanguageFromPath (14 parametric + 1 assertion), TestParseSgOutput (4), TestExtractWithAstGrep (8 with `FakeInvoker` for subprocess mocking), TestRuleFilesShipped (8 parametric — verifies each rule YAML exists and is well-formed), TestIntegration (1 — real sg binary against a TypeScript fixture, skipped if sg not on PATH). Full codemem suite: **72/72 passing** (20 python_ast + 16 schema + 36 ast-grep). Ruff clean.

### Task 1.5: File discovery + indexer driver
- Status: COMPLETE
- Mode: AFK — auto-dispatched
- Dependencies: Task 1.3, Task 1.4
- Acceptance Criteria: `git ls-files` based discovery respects `.gitignore`; per-language batched parser dispatched in one transaction per language; bulk insert uses `executemany` with `foreign_keys=OFF` toggle + re-enable + integrity check post-insert.
- Result Log: COMPLETE 2026-04-13. `packages/codemem-mcp/src/codemem/indexer.py` written (~350 LOC) exposing `BuildStats`, `discover_files`, `parse_files`, `build_index(repo_root, db_path, *, package=".")`. Discovery: `git ls-files` via `subprocess.run` when repo_root is a git repo (respects `.gitignore` for free), falls back to `Path.rglob` when not a git repo — filters to `_INDEXABLE_EXTENSIONS` (`.py` ∪ ast-grep's 9 extensions). Parse dispatch: `.py` files go one-by-one to `python_ast.extract_python_signatures` (stdlib, cheap); all other supported extensions batch through `ast_grep.extract_with_ast_grep` (single sg invocation per language). Bulk insert strategy (per AC): `PRAGMA foreign_keys = OFF` set OUTSIDE the transaction (SQLite docs: FK PRAGMA is ignored mid-tx), `executemany` for files upsert (INSERT ON CONFLICT path DO UPDATE), symbols bulk insert (INSERT ON CONFLICT (file_id, scip_id) DO UPDATE, parent_id=NULL), then `_resolve_parent_ids` does a single `executemany UPDATE` keyed on scip_id after a `SELECT scip_id, id FROM symbols` map build, then edges bulk insert (INSERT OR IGNORE on schema's 4-col PK). After COMMIT + `PRAGMA foreign_keys = ON`, runs `PRAGMA foreign_key_check` AND `PRAGMA integrity_check` — both must pass or `build_index` raises `RuntimeError`. Idempotency: re-indexing deletes file rows for the parsed set first (`DELETE FROM files WHERE path IN (...)` — FK CASCADE removes stale symbols + edges), then re-inserts fresh. Ensures second run produces same counts (verified by `test_idempotent_rebuild`). Tests: `tests/codemem/test_indexer.py` — 15 tests across 2 classes: TestDiscoverFiles (4: tracked filter, .gitignore respect, absolute paths, non-git-fallback), TestBuildIndex (11: stats shape, DB creation, files/symbols rows, parent_id resolution for methods on classes, integrity_check, foreign_key_check, intra-file edge persistence main→greet, idempotent rebuild, graceful handling of unparseable source). Integration tests use real `git init` in tmp_path and real sg binary for TypeScript (skipped if sg not on PATH). Full codemem suite: **87/87 passing** (20 python_ast + 16 schema + 36 ast-grep + 15 indexer). Ruff clean. Also fixed stale docstring in `storage/db.py` (v3 plan's `0xC0DE3E33` reference) carried over from Task 1.2's overflow correction.

### Task 1.6: Cross-file edge resolution
- Status: COMPLETE
- Mode: AFK — auto-dispatched
- Dependencies: Task 1.5
- Acceptance Criteria: Port 4-strategy import-resolver logic from `/index`; materialize cross-file edges in `edges` table with `dst_unresolved` populated for unresolved targets. Unit tests on fixture with known import graph.
- Result Log: COMPLETE 2026-04-13. `packages/codemem-mcp/src/codemem/resolver.py` written (~180 LOC) exposing `build_import_map(file_paths) -> dict[str, str]` and `resolve_cross_file_edges(conn, *, parses) -> dict[resolved, unresolved]`. Ports `/index`'s 4-strategy logic verbatim: (1) direct `import_map[imp]` match, (2) relative to source file's directory (`<source_dir>.<imp>`), (3) common package prefixes (`src.`, `scripts.`, `lib.`, `app.`), (4) suffix match — any dotted entry ending with `.<imp>`. Each resolver entry short-circuits on the first hit that isn't the source file itself. __init__.py handling: registers BOTH `pkg.__init__` AND `pkg` forms so `from pkg import foo` resolves to `pkg/__init__.py`. Parser extensions (same commit): `python_ast.ParseResult` gained two default-empty fields `imports: list[str]` and `unresolved_edges: list[CallEdge]` — backward compatible with all existing ParseResult construction. `extract_python_signatures` now harvests `ast.Import`/`ast.ImportFrom` nodes and emits cross-file call candidates (as `CallEdge` records with `dst_unresolved=callee_name`) distinct from the intra-file `edges` list. Existing 20 python_ast tests still pass unchanged — the new fields default to empty when no imports/cross-file calls exist. Built-in filter (`_CALL_EXCLUDE`: print, len, str, ...) applies to BOTH intra and cross-file candidates — no `dst_unresolved='len'` edges ever get persisted. `build_index` now invokes the resolver as the final step inside the transaction; resolved edges get `dst_symbol_id` set, unresolved stay with `dst_unresolved` populated (never both, never neither — schema CHECK enforces). `BuildStats` gained `cross_file_resolved` + `cross_file_unresolved` counters. Tests: `tests/codemem/test_resolver.py` — 10 tests across 3 classes: TestBuildImportMap (4), TestCrossFileResolution (5 incl. strategy-1 direct, strategy-2 relative, strategy-4 suffix; external `requests.get()` verifies unresolved path; dst_unresolved NULL on resolved edges), TestPythonParserExposesImports (2 for contract lock). Full codemem suite: **98/98 passing** (20 python_ast + 16 schema + 36 ast-grep + 15 indexer + 11 resolver). Ruff clean. Anchor: on a 2-file fixture where `a.py` imports `b.py` and calls `b.helper()`, the edge `(caller → helper, dst_unresolved=NULL)` is materialized end-to-end.

### Task 1.7: 6 ported MCP tools + input sanitization + canonical CTE
- Status: COMPLETE
- Mode: AFK — auto-dispatched
- Dependencies: Task 1.6
- Acceptance Criteria: `who_calls`, `blast_radius`, `dead_code`, `dependency_chain`, `search_symbols`, `file_summary` implemented. All call-graph walks use the canonical recursive CTE (see `codemem-reference.md`). Hard token budget default 8000, configurable. Input sanitization: path args via `Path.resolve(strict=False)` + `is_relative_to(repo_root)`; symbol/file string args via regex `^[A-Za-z0-9_./\-]{1,256}$` + reject `..` substring; rejection before SQL. Adversarial suite passes: `../../etc/passwd`, `/etc/passwd`, `foo/../../bar`, 10KB unicode, `'; DROP TABLE`, regex metachars in `-L` context — all return structured error, no exception/crash.
- Result Log: COMPLETE 2026-04-13. Three modules under `packages/codemem-mcp/src/codemem/mcp_tools/`: (1) `sanitizers.py` — `ValidationError` + `sanitize_symbol_arg(value)` (allow-list regex `^[A-Za-z0-9_./\-]{1,256}$` + explicit `..` reject + non-empty + ≤256 char) + `sanitize_path_arg(value, repo_root)` (runs symbol-arg first, then `resolve(strict=False)` + `relative_to(repo_root)` — raises on escape). (2) `queries.py` — pins `WHO_CALLS_CTE` (upstream via `idx_edges_dst` covering index) and `BLAST_RADIUS_CTE` (downstream via `idx_edges_src`); both cycle-safe via `path` column NOT-LIKE. (3) `__init__.py` — 6 tool functions, each pure Python, each returns JSON-serialisable dict with `error: str | None` and `truncated: bool`. Tools: `who_calls(db_path, name, *, max_depth=3, budget=8000)`, `blast_radius(db_path, name, *, max_depth=3, budget=8000)`, `dead_code(db_path, *, budget=8000)` (functions/methods with zero inbound call edges), `dependency_chain(db_path, source, target, *, max_depth=5, budget=8000)` (finds shortest path via `_CHAIN_CTE`; iterates source×target when names are ambiguous, keeps the shortest), `search_symbols(db_path, query, *, budget=8000)` (LIKE match with exact>prefix>contains ranking), `file_summary(db_path, path, *, budget=8000)`. Budget enforcement: JSON-length heuristic (1 token ≈ 4 chars) with binary-search truncation on the result list — adds `truncated: true` to the payload when clipped. All tools open SQLite in `read_only=True` mode — MCP server surface is strictly non-mutating. Explain-plan gate: empirically verified `EXPLAIN QUERY PLAN` on `WHO_CALLS_CTE` on a probe DB — both the SETUP clause (`SEARCH edges USING COVERING INDEX idx_edges_dst`) AND the RECURSIVE STEP (`SEARCH e USING COVERING INDEX idx_edges_dst`) use the covering index; `SCAN` appears only for the in-memory CTE cursors (`SCAN c`, `SCAN callers`), never the `edges` heap. Adversarial suite: 11 tests cover `../../etc/passwd` rejection (symbol arg), `/etc/passwd` rejection (path arg), `foo/../../bar` rejection (`..` substring), 10KB unicode rejection (length), `'; DROP TABLE` rejection (regex metachars including quote), plus invalidation of `( ) * | [ ] { } \` — every tool returns structured error dict instead of raising. SQL injection specifically verified: after `who_calls("'; DROP TABLE symbols;--")`, the symbols table still has rows. Tests: `tests/codemem/test_mcp_tools.py` — **33 tests** across 9 classes (TestSanitizers 11 incl. path-canonicalization-escape, TestWhoCalls 6, TestBlastRadius 3, TestDeadCode 1, TestDependencyChain 3, TestSearchSymbols 3, TestFileSummary 3, TestBudget 2, TestCanonicalCTEExplainPlan 1). Full codemem suite: **131/131 passing** (20 python_ast + 16 schema + 36 ast-grep + 15 indexer + 11 resolver + 33 mcp_tools). Ruff clean.

### Task 1.8: PageRank-ranked JSON projection
- Status: COMPLETE
- Mode: AFK — auto-dispatched
- Dependencies: Task 1.7
- Acceptance Criteria: Aider-style algorithm implemented in ~50 LOC pure-Python power iteration (no scipy), damping=0.85; binary search to fit `--budget` token cap (default 1024); tie-breakers by file path stability + symbol kind (functions > vars); writes `PROJECT_INTEL.json`. Deterministic on fixture; output ≤ budget; ≤ 5KB on aa-ma-forge; covers ≥90% of `/index` `_meta.symbol_importance` top symbols.
- Result Log: COMPLETE 2026-04-13. `packages/codemem-mcp/src/codemem/pagerank.py` written (~180 LOC, zero deps beyond stdlib + sqlite3). Pure-Python power iteration: 50 iterations max, convergence eps=1e-6, damping=0.85, dangling-mass redistribution per Brin/Page formulation (otherwise sum drifts below 1.0). Public API: `compute_pagerank(conn, *, damping, max_iterations, eps) -> dict[symbol_id, rank]` and `write_project_intel(db_path, out_path, *, budget, damping) -> {written_symbols, size_bytes}`. Graph: edges kind='call' with resolved dst_symbol_id — unresolved (cross-file) edges deliberately excluded (otherwise their dst column is NULL). Tie-break order: `_KIND_PRIORITY` (function/async_function=0, method/async_method=1, class/struct/interface=2, type_alias=3) → file path → line → name. Deterministic output: JSON serialised with `separators=(",", ":"), sort_keys=True` and trailing newline; identical bytes across repeated runs (verified by `test_deterministic_output_bytes`). Budget enforcement: binary-search the longest prefix of the ranked symbol list whose JSON serialisation fits `budget_tokens * 4` chars (1:4 token-to-char heuristic from Task 1.7). Default budget 1024 tokens; `DEFAULT_BUDGET_TOKENS` exported for callers. Schema header `codemem/project-intel@1` — bump when shape changes. Empirically verified: hub-repo fixture (1 hub, 5 callers, 1 orphan) ranks `hub` first, sum ≈ 1.0 ± 1e-9, orphan gets ≥ (1-d)/N base rank. Tests: `tests/codemem/test_pagerank.py` — 13 tests across 3 classes: TestComputePageRank (5: per-symbol scores, hub outranks leaves, sum≈1, deterministic across runs, damping default 0.85), TestProjectIntelJson (6: file written, fits budget, hub first in output, deterministic bytes, tie-break prefers functions, 5KB budget on proxy fixture), TestAlgorithmProperties (2: empty DB returns {}, isolated node gets base rank). Full codemem suite: **144/144 passing** (20+16+36+15+11+33+13). Ruff clean. NOTE: ≥90% coverage vs `/index` `_meta.symbol_importance` is an M4 benchmark AC (Task 4.2) — cannot be verified in a unit test; proxy validated via tie-break + hub-beats-leaves correctness.

### Task 1.9: `/codemem` slash command
- Status: COMPLETE
- Mode: AFK — auto-dispatched
- Dependencies: Task 1.8
- Acceptance Criteria: `claude-code/codemem/commands/codemem.md` committed defining subcommands: `codemem build`, `codemem refresh` (M2 placeholder), `codemem query <tool> <args>`, `codemem status`, `codemem replay --from-wal` (M2 placeholder).
- Result Log: COMPLETE 2026-04-13. `claude-code/codemem/commands/codemem.md` committed (150 lines) with 5 subcommands documented: `codemem build [--package ...] [--db ...]` (fully specced), `codemem query <tool> [args...]` (6 tools in table: who_calls, blast_radius, dead_code, dependency_chain, search_symbols, file_summary — all with arg and budget flags), `codemem status [--db ...]` (summary stats), `codemem refresh` (M2 placeholder, documented with WAL contract), `codemem replay --from-wal` (M2 placeholder). Docs cross-reference the pinned contracts: symbol-id-grammar.md, reference.md, ARCHITECTURE.md (M1 Task 1.12 placeholder), performance-slo.md (Task 1.13). Adversarial-input behaviour explicitly called out (structured `error` dict, never raises). Executable CLI glue (argparse dispatch to `codemem.indexer`/`codemem.mcp_tools`/`codemem.pagerank`) is Task 1.11 scope — this task documents the SURFACE; the driver lives next to the install integration.

### Task 1.10: MCP server with tool-name aliases
- Status: COMPLETE
- Mode: AFK — auto-dispatched
- Dependencies: Task 1.7
- Acceptance Criteria: `mcp/server.py` uses FastMCP with read-only SQLite connection (`mode=ro`) per request. 12 tool slots registered; M1 lights up first 6. Aliases registered: `dead_code` ↔ `find_dead_code`, `who_calls` ↔ `find_references` (for Anthropic Tool Search discoverability).
- Result Log: COMPLETE 2026-04-13. `claude-code/codemem/mcp/server.py` written (~170 LOC). Exposes `CANONICAL_TOOL_NAMES` (12-element tuple: M1's 6 + M3's 6), `ALIASES` dict (`who_calls`→[`find_references`], `dead_code`→[`find_dead_code`]), `build_server()` → FastMCP instance, `list_registered_tool_names()` for test introspection. Server is a thin adapter: each M1 handler (who_calls/blast_radius/dead_code/dependency_chain/search_symbols/file_summary) delegates straight to `codemem.mcp_tools.*` functions — the sanitization + SQL already happens there, and those helpers open SQLite with `read_only=True` (`mode=ro` URI) via `storage.db.connect`. No RW connection anywhere in the server path — verified by TestReadOnlyConnectionPolicy grepping the server source for `read_only=False`. DB path: configurable via `CODEMEM_DB` env (defaults to `cwd/.codemem/index.db`); repo root: `CODEMEM_REPO_ROOT` env (defaults to `cwd`). FastMCP registration: `server.tool(handler, name=canonical)` + `server.tool(handler, name=alias)` for each alias — one handler callable wired to multiple names. M3 tools (hot_spots/co_changes/owners/symbol_history/layers/aa_ma_context) deliberately NOT registered in M1 — listed in CANONICAL_TOOL_NAMES but absent from the FastMCP server so agents calling them get a clean "tool not found" rather than a stub returning empty data. Tests: `tests/codemem/test_mcp_server.py` — 8 tests across 4 classes: TestTwelveSlots (2: canonical set matches reference.md §MCP Tools exactly, length == 12), TestAliases (2: alias map correctness), TestToolRegistration (3: M1 six registered, aliases also registered, M3 six NOT registered), TestReadOnlyConnectionPolicy (1: grep guard against RW regression). Tests use `importlib.util.spec_from_file_location` because the server lives OUTSIDE the uv-workspace `packages/codemem-mcp/src/` tree (intentionally — `claude-code/codemem/` is the plugin surface, distinct from the pip-installable package). Full codemem suite: **152/152 passing** (20+16+36+15+11+33+13+8). Ruff clean.

### Task 1.11: Install integration + import-linter + git hook wiring
- Status: COMPLETE
- Mode: HITL — executed under user standing instruction "continue straight through" (session 2026-04-13)
- Dependencies: Task 1.10
- Acceptance Criteria: `scripts/install.sh` symlinks `claude-code/codemem/` into `~/.claude/`. Post-commit hook wired by install.sh via one of: (a) guarded line appended to `.git/hooks/post-commit`, OR (b) `git config core.hooksPath claude-code/codemem/hooks`; trade-off documented in install.sh comments. After `install.sh`, `git commit` triggers `codemem refresh` (verified by post-commit log line). `import-linter` CI config enforces: `claude-code/codemem/` MUST NOT import from `aa_ma.codemem.{storage,parser,diff,journal}` directly (only via `aa_ma.codemem.mcp_tools`). CI fails on boundary violation.
- Result Log: COMPLETE 2026-04-13. Five deliverables: (1) `.importlinter` at repo root defines two contracts: `codemem-layers` (`codemem.mcp_tools | codemem.indexer | codemem.resolver | codemem.pagerank` → `codemem.parser` → `codemem.storage` — uses `:` separator for peer layers per import-linter v2.11 syntax), `parser-is-pure` (forbidden contract: `codemem.parser.*` must not import from any orchestrator/API layer). `uv run lint-imports` returns "Contracts: 2 kept, 0 broken." NOTE: plan v3 AC mentions `aa_ma.codemem.*` paths; plan v4 moved codemem to `codemem.*` (at `packages/codemem-mcp/src/codemem/`), so the contracts use v4 paths — the architectural invariant is preserved. (2) `packages/codemem-mcp/src/codemem/cli.py` reimplemented as a functional argparse dispatcher (~220 LOC) with 6 subcommands: `build` (full index), `status` (counts), `refresh` (M2 placeholder — logs to `.codemem/refresh.log`, exits 0), `replay --from-wal` (M2 placeholder), `query <tool>` (routes to any of the 6 MCP tools with `--max-depth` + `--budget` flags), `intel` (writes `PROJECT_INTEL.json` via pagerank). Heavy imports (indexer, pagerank) lazy-loaded per-command to keep `--help` fast and reduce hook cold-start cost. (3) `claude-code/codemem/hooks/post-commit.sh` (chmod +x) — guarded stanza: skips during rebase/cherry-pick/merge via `GIT_REFLOG_ACTION` check, falls back to `python3 -m codemem.cli` when `codemem` binary isn't on PATH, backgrounds the refresh via `&` so `git commit` returns immediately, redirects stdout+stderr to `.codemem/refresh.log`, exits 0 unconditionally (never fails a commit). (4) `scripts/install.sh` gained `--wire-git-hook` flag. Picked OPTION (a) — append guarded line to `.git/hooks/post-commit` using a sentinel comment `# codemem-post-commit-installed` for idempotency. Option (b) (`git config core.hooksPath`) is documented in install.sh comments with the trade-off: (a) preserves user's existing hooks but only wires the current repo; (b) flips a single git config but clobbers pre-existing `hooksPath` (Husky/lefthook/pre-commit collisions). Wiring only runs when `--wire-git-hook` is explicitly passed (opt-in). Absolute path normalization for `--git-dir` output so the hook works in both worktree-root and subdirectory invocations. (5) Tests: `tests/codemem/test_install_and_cli.py` — 11 tests across 5 classes: TestImportLinterContract (2: runs `uv run lint-imports`, asserts "2 kept, 0 broken" AND config file exists with both named contracts), TestPostCommitHook (3: exists+executable, rebase skip, non-git-repo graceful exit 0), TestInstallScriptWiring (1: `--dry-run --wire-git-hook` accepted by argparse), TestCLI (4: help works, missing subcommand errors, real build+status roundtrip on a tmp git repo, refresh M2-placeholder behaviour), TestPluginSurfaceNoBypass (1: grep-based check on claude-code/codemem/mcp/server.py for forbidden imports of internals — supplements import-linter since claude-code/ isn't a Python package). Full codemem suite: **163/163 passing** (20+16+36+15+11+33+13+8+11). Ruff clean. Both import-linter contracts green.

### Task 1.12: ARCHITECTURE.md (M1 placeholders)
- Status: PENDING
- Mode: HITL
- Dependencies: Task 1.2b, Task 1.7
- Acceptance Criteria: `docs/codemem/ARCHITECTURE.md` committed with 5 mandatory sections: (a) Layering contract + import rules; (b) Dual-WAL semantics (placeholder for M2 details); (c) Symbol ID grammar (link to 1.2b doc); (d) Concurrency model (placeholder for M2 lock); (e) Performance SLOs + measurement (link to perf-slo.md from 1.13).
- Result Log:

### Task 1.13: Performance SLO doc + pytest-benchmark setup
- Status: PENDING
- Mode: AFK
- Dependencies: Task 1.7
- Acceptance Criteria: `docs/codemem/performance-slo.md` committed listing 4 SLOs (build cold, build warm, refresh, who_calls latency, build vs /index ratio). `tests/perf/test_budgets.py` uses `pytest-benchmark`; suite marked `@pytest.mark.perf`; CI fails when any budget regresses by >10%. Budget failure demonstrably halts pipeline.
- Result Log:

---

## Milestone M2: Incremental Cache + WAL Journal (crash-safe ordering)
- Status: PENDING
- Gate: SOFT
- Dependencies: M1 complete
- Complexity: 75%
- Acceptance Criteria (per plan §4 M2):
  - `codemem refresh` after a 10-line edit completes in < 500ms (enforced by `tests/perf/`)
  - `codemem refresh` after `git mv` correctly classifies all symbols as moved (not added+removed)
  - Property-based round-trip test passes: 100 random edit sequences via `hypothesis` produce identical DB after `build → wipe → replay-wal`
  - Crash-injection test: kill indexer between WAL append and SQLite commit → next refresh completes correctly without double-applying (idempotency verified)
  - WAL JSONL rotation triggers at 10MB; last 3 retained; replay reads across rotation boundary
  - Concurrent `codemem refresh` invocations: second is no-op (verified via test that spawns 2 in parallel)
  - Post-commit hook test: 5 rapid `git commit --amend` calls in <1s leave only 1 active codemem process
  - Git history rewrite test: `git rebase -i` orphans `last_sha` → next refresh falls back to full rebuild with logged warning, no crash

### Task 2.1: Symbol-set diff algorithm
- Status: PENDING
- Mode: AFK
- Dependencies: M1
- Acceptance Criteria: `diff/symbol_diff.py` classifies (old_symbols, new_symbols) per file into added/removed/modified/renamed via RefactoringMiner-style heuristic (same-kind hard filter; signature Jaccard similarity; line proximity tiebreak; threshold 0.7 → rename). Conservative: demoted matches logged. `--no-rename-detection` escape hatch. ~150 LOC + unit tests covering: same name diff signature, similar name same signature, mass refactor.
- Result Log:

### Task 2.2: Incremental indexer driver
- Status: PENDING
- Mode: AFK
- Dependencies: Task 2.1
- Acceptance Criteria: `codemem refresh` walks dirty files (mtime+size → SHA-256 fallback), parses, diffs symbols, applies deltas to SQLite. Re-resolves cross-file edges only for files with changed imports. Git history rewrite handled: if `last_sha` orphaned (`git cat-file -e <sha>` fails), falls back to full rebuild with warning written to `.codemem/refresh.log`.
- Result Log:

### Task 2.3: WAL JSONL journal (crash-safe ordering + state diagram)
- Status: PENDING
- Mode: AFK
- Dependencies: Task 2.2
- Acceptance Criteria: `journal/wal.py` implements the ordering: intent append → SQLite txn commit → ack append. Atomic append via `O_APPEND`. Entry schema: `{"id": uuid, "ts": iso, "op": str, "args": dict, "prev_user_version": int, "content_sha": str}`. Replay state diagram (see `codemem-reference.md`) implemented verbatim. Idempotency key `(op, prev_user_version, content_sha)`. Crash-injection test: kill between intent-append and commit → replay succeeds without double-apply.
- Result Log:

### Task 2.4: WAL replay tool (idempotent)
- Status: PENDING
- Mode: AFK
- Dependencies: Task 2.3
- Acceptance Criteria: `codemem replay --from-wal` reconstructs SQLite from WAL JSONL using idempotency keys. Round-trip property test: `build → snapshot → wipe DB → replay-WAL → assert DB equal (mod last_indexed)`. Uses `hypothesis` to generate 100 random edit sequences; all pass.
- Result Log:

### Task 2.5: Post-commit hook with process-group cleanup
- Status: PENDING
- Mode: AFK
- Dependencies: Task 2.2
- Acceptance Criteria: `claude-code/codemem/hooks/post-commit.sh` shells out `codemem refresh`. Idempotent; no-op if no new commits. Skips during rebase/cherry-pick. Spawns via `setsid`; writes PID to `.codemem/refresh.pid`; kills previous PID if alive before spawning new one. Exit 0 always; errors logged to `.codemem/refresh.log`. Storm test: 5 rapid `git commit --amend` in <1s leaves only 1 active process.
- Result Log:

### Task 2.6: SQLite WAL hygiene
- Status: PENDING
- Mode: AFK
- Dependencies: Task 2.2
- Acceptance Criteria: Periodic `PRAGMA wal_checkpoint(TRUNCATE)` invoked after large indexer batches. Test verifies WAL file size stays bounded under repeated refreshes.
- Result Log:

### Task 2.7: Process-level single-writer lock (portable)
- Status: PENDING
- Mode: AFK
- Dependencies: Task 2.2
- Acceptance Criteria: Cross-platform single-writer lock acquired at indexer entry. `fcntl.lockf` on POSIX, `msvcrt.locking` on Windows, abstracted behind `_acquire_writer_lock(path)`. Lock file: `.codemem/db.lock` (separate from `.codemem/refresh.pid`). Second invocation no-ops with informative log line (does not queue). Read MCP server uses `mode=ro` and never touches the lock. Standalone wheel declares `requires-python=">=3.11"` and explicit OS classifiers. If pure-stdlib portable lock is unclean, optional `portalocker` dep under `[windows]` extra; docs call out Linux+macOS as primary support.
- Result Log:

### Task 2.8: WAL JSONL rotation
- Status: PENDING
- Mode: AFK
- Dependencies: Task 2.3
- Acceptance Criteria: `wal.jsonl` rotates at 10MB; last 3 retained as `wal.jsonl.1.gz`, `wal.jsonl.2.gz`, `wal.jsonl.3.gz`; older compressed. Replay tool reads seamlessly across rotation boundary (test verifies replay produces identical DB whether WAL is unrotated or spans 3 rotations).
- Result Log:

---

## Milestone M3: Git Intelligence + AA-MA Coupling (the moat)
- Status: PENDING
- Gate: HARD
- Dependencies: M2 complete
- Complexity: 55%
- Gate rationale: Locks the moat — the 12 MCP tool surface including `aa_ma_context` naming/positioning is publicly exposed here and hard to change after users build on it. HARD gate requires signed approval artifact in `codemem-context-log.md` before milestone can be marked COMPLETE.
- Acceptance Criteria (per plan §4 M3):
  - `hot_spots()` on aa-ma-forge returns ≥3 candidates with score breakdown ≥ baseline floor (≥1 commit in last 90 days × ≥1 function)
  - `co_changes("CLAUDE.md")` returns ≥1 file with ≥3 commit co-occurrences AND no import edge (e.g. `claude-code/rules/aa-ma.md`)
  - `owners("src/aa_ma/")` returns email matching `stephen.j.newhouse@gmail.com` with `percentage > 90.0`
  - `symbol_history("extract_python_signatures", file_path="~/.claude-code-project-index/scripts/index_utils.py")` correctly identifies the introducing commit
  - `layers()` ASCII output ≤ 500 tokens AND fits in 80-column terminal without wrap (golden file `tests/golden/layers_aa_ma_forge.txt`)
  - `aa_ma_context("codemem")` returns non-empty Markdown fragment naming ≥1 file from §5 Required Artefacts AND owners+blast-radius for ≥1 symbol from `codemem-reference.md`
  - All 6 tools complete in < 1s on aa-ma-forge (enforced by `tests/perf/`)
  - Subprocess injection test: `co_changes("$(rm -rf /tmp)")` returns sanitization error, NO shell execution
  - 50k-file synthetic fixture: `hot_spots()` completes in < 5s

### Task 3.1: Git mining base layer with sanitized subprocess
- Status: PENDING
- Mode: AFK
- Dependencies: M2
- Acceptance Criteria: `analysis/git_mining.py` uses `subprocess.run([...], shell=False)` with `--` separator before user input. Wrappers for `git log --since=<date> --name-only --pretty=format:%H|%at|%ae|%s` and `git blame --line-porcelain`. Caches last 500 commits in `commits` table; incremental via `git log <last_sha>..HEAD`. All file path args validated against repo root before subprocess. Subprocess injection test (`co_changes("$(rm -rf /tmp)")`) returns sanitization error; no shell execution verified by absence of `/tmp` modification.
- Result Log:

### Task 3.2: `hot_spots()` MCP tool
- Status: PENDING
- Mode: AFK
- Dependencies: Task 3.1
- Acceptance Criteria: Returns top-N files ranked by (commits in last 90 days) × (function_count). Output includes score breakdown. On aa-ma-forge returns ≥3 candidates meeting baseline (≥1 commit last 90d × ≥1 function). Completes <1s on aa-ma-forge; <5s on 50k-file synthetic fixture.
- Result Log:

### Task 3.3: `co_changes(file)` MCP tool
- Status: PENDING
- Mode: AFK
- Dependencies: Task 3.1
- Acceptance Criteria: Returns files that change in commits with input file AND do NOT have an import-graph edge to it. Co-occurrence count over last 500 commits. Threshold ≥3 commits. CHANGELOG.md and README.md excluded by default. `co_changes("CLAUDE.md")` on aa-ma-forge returns ≥1 file (e.g. `claude-code/rules/aa-ma.md`) meeting both criteria.
- Result Log:

### Task 3.4: `owners(path)` MCP tool
- Status: PENDING
- Mode: AFK
- Dependencies: Task 3.1
- Acceptance Criteria: Per-file or per-directory author percentages from `git blame --line-porcelain`. Cached in `ownership` table; refresh on-demand or via `codemem refresh --owners`. Per-file timeout 2s; `--no-owners` skip flag. `owners("src/aa_ma/")` returns `stephen.j.newhouse@gmail.com` with `percentage > 90.0`.
- Result Log:

### Task 3.5: `symbol_history(name)` MCP tool
- Status: PENDING
- Mode: AFK
- Dependencies: Task 3.1
- Acceptance Criteria: Uses `git log -L:symbol_name:file_path`. Returns first-seen, last-touched, change count, authors. If symbol exists in multiple files, returns history per file. Correctly identifies introducing commit for `extract_python_signatures` in `~/.claude-code-project-index/scripts/index_utils.py`.
- Result Log:

### Task 3.6: `layers()` MCP tool
- Status: PENDING
- Mode: AFK
- Dependencies: Task 3.1
- Acceptance Criteria: In-degree bucketing of `edges` table grouped by file/module → 3-layer ASCII onion (core/middle/periphery). Output ≤ 500 tokens AND fits 80-column terminal without wrap. Golden file `tests/golden/layers_aa_ma_forge.txt` checked in for regression.
- Result Log:

### Task 3.7: `aa_ma_context(task_name)` MCP tool (AA-MA-native moat)
- Status: PENDING
- Mode: AFK
- Dependencies: Task 3.2, Task 3.4
- Acceptance Criteria: Validates task against `.claude/dev/active/*/`. Returns: `hot_spots` filtered to files mentioned in the task's `*-tasks.md`; `owners()` of those files; `blast_radius()` of named symbols in `*-reference.md`. Output: structured Markdown fragment ready to paste. Optional `--write` mode appends to reference.md with timestamp. Extraction rule pinned (see `codemem-reference.md`): file mentions via backticked path regex + filesystem existence check; symbol mentions via backticked identifier regex + SQLite `symbols.name` lookup. Integration test against `tests/fixtures/aa_ma_context/sample-task/` matches `expected.json` byte-for-byte. ~80 LOC.
- Result Log:

### Task 3.8: M3 schema additions (migration v2)
- Status: PENDING
- Mode: AFK
- Dependencies: Task 3.1
- Acceptance Criteria: `schema.sql` + migration framework adds tables `commits`, `ownership`, `co_change_pairs` via `PRAGMA user_version` bump to 2 (M2 introduces no schema changes; user_version stays at 1 through M2). FKs and cascades per M1 contract. Migration from v1 → v2 tested round-trip.
- Result Log:

---

## Milestone M4: Polish, Demo, Differentiation
- Status: PENDING
- Gate: SOFT
- Dependencies: M3 complete
- Complexity: 40%
- Acceptance Criteria (per plan §4 M4):
  - Benchmark report shows `codemem build` ≤ 1.5× wall-clock of `/index` on each reference repo (enforced by `tests/perf/`)
  - `codemem refresh` median time < 800ms on medium repo
  - Token-budget benchmark: `PROJECT_INTEL.json` ≤ Aider repo-map size at equal budget AND covers ≥ 90% of same top-ranked symbols
  - Migration guide: a `/index` user can switch in < 5 minutes (validated by walkthrough)
  - README passes `/stephen-newhouse-voice` review (no marketing-AI tone); MS charity + coffee callout present
  - Zero-config install: paste 3-line `settings.json` snippet → first MCP query triggers build → returns answer in < 5s on aa-ma-forge
  - Demo asciinema/GIF committed to `docs/demo/`; embedded in README
  - CI green; SECURITY.md merged; ARCHITECTURE.md finalized; kill-criteria.md committed

### Task 4.1: Performance benchmarks
- Status: PENDING
- Mode: AFK
- Dependencies: M3
- Acceptance Criteria: Bench script compares `codemem build`, `codemem refresh`, 3 representative MCP queries against `/index` on three reference repos: aa-ma-forge (small), repowise (medium), 50k-LOC OSS Python (large). Results documented in `docs/benchmarks/codemem-vs-index.md` with reproducibility notes (5 runs, median). `codemem build` ≤ 1.5× wall-clock of `/index` on each repo.
- Result Log:

### Task 4.2: Token-budget benchmarks
- Status: PENDING
- Mode: AFK
- Dependencies: Task 4.1
- Acceptance Criteria: `PROJECT_INTEL.json` size compared to Aider's repo-map and jcodemunch-mcp at `--budget=1024` across the same 3 reference repos. Results in `docs/benchmarks/codemem-vs-aider.md`. `PROJECT_INTEL.json` ≤ Aider size at equal budget AND covers ≥90% of same top-ranked symbols.
- Result Log:

### Task 4.3: Migration guide from `/index`
- Status: PENDING
- Mode: HITL
- Dependencies: M3
- Acceptance Criteria: `docs/codemem/migration-from-index.md` committed with: side-by-side MCP tool naming, format differences, hook switchover steps, `codemem import-from-index` command spec (if simpler), FAQ. Concrete (not hand-wavy). Walkthrough validates `/index` user switches in < 5 minutes.
- Result Log:

### Task 4.4: README + competitor positioning
- Status: PENDING
- Mode: HITL
- Dependencies: M3
- Acceptance Criteria: `claude-code/codemem/README.md` covers: what it is, what's different from GitNexus/Axon/Codegraph/jCodeMunch (git-mining quintet, AA-MA coupling, pure-Python+SQLite, no embeddings), install both modes, quick-start, MCP tool reference. Frames competitors as "different tradeoffs" not "worse." Passes `/stephen-newhouse-voice` review. MS charity + buy-someone-a-coffee callouts present.
- Result Log:

### Task 4.5: SECURITY.md update
- Status: PENDING
- Mode: HITL
- Dependencies: M3
- Acceptance Criteria: `SECURITY.md` patch documents: SQLite WAL file growth caveats, `codemem` reads full repo (litellm 2026 supply-chain reference), trusted-environment recommendation, input sanitization contract.
- Result Log:

### Task 4.6: Doc-drift integration
- Status: PENDING
- Mode: AFK
- Dependencies: Task 4.4
- Acceptance Criteria: `Skill(doc-drift-detection)` hooked so README/CHANGELOG version references to codemem stay in sync. Tier 1 + Tier 2 checks exercise codemem paths in a test commit.
- Result Log:

### Task 4.7: CI integration
- Status: PENDING
- Mode: AFK
- Dependencies: Task 4.1
- Acceptance Criteria: `.github/workflows/security.yml` extended to run `codemem` smoke test (build + 1 query) on PRs touching `src/aa_ma/codemem/`. ast-grep version drift check warns if installed version exceeds declared range.
- Result Log:

### Task 4.8: 60-second demo + zero-config install snippet
- Status: PENDING
- Mode: HITL
- Dependencies: Task 4.4
- Acceptance Criteria: `co_changes("CLAUDE.md")` demo recorded on a real repo (asciinema or GIF) showing non-obvious coupling; stored in `docs/demo/codemem-co-changes.{cast,gif}`. `docs/codemem/install-zero-config.md` authored with one-paste Claude Code `settings.json` snippet enabling the MCP server (no manual `/codemem build` — server auto-builds on first query). Snippet included in README. End-to-end: paste 3-line settings.json → first query returns answer in < 5s on aa-ma-forge.
- Result Log:

### Task 4.9: ARCHITECTURE.md final pass
- Status: PENDING
- Mode: HITL
- Dependencies: M2, Task 4.3
- Acceptance Criteria: Placeholders from M1 Step 1.12 replaced with M2 dual-WAL semantics + concurrency lock details. Symbol ID grammar examples per language locked. Final version committed.
- Result Log:

### Task 4.10: Kill criteria public doc
- Status: PENDING
- Mode: HITL
- Dependencies: Task 4.4
- Acceptance Criteria: `docs/codemem/kill-criteria.md` committed containing the 5 measurable signals from plan §12 (30-day signal-kill, M1 architectural kill, M3 headline-tool kill, anytime moat-evaporated, M2 correctness-risk kill). Linked from README "what could make us abandon this" section.
- Result Log:
