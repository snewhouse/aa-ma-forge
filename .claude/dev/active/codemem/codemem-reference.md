# codemem — Reference (Immutable Facts)

_This file is the highest-priority AA-MA memory artifact. Load FIRST when resuming this task. Facts below are extracted from `codemem-plan.md` v3 and are non-negotiable unless the plan itself is revised._

_Last Updated: 2026-04-14 (M3 Task 3.8 COMPLETE — schema v2 migration shipped)_

---

## Project Metadata

| Field | Value |
|---|---|
| Task name | `codemem` |
| Owner | Stephen Newhouse + AI |
| Repo | `aa-ma-forge` |
| Branch | `expt/code_mem_store_what` (from `main`, base commit `d44c1c8`) [valid: 2026-04-13] |
| Created | 2026-04-13 |
| Plan version | v3 (post adversarial verification) |
| Estimated effort | 14–18 focused-dev days across 4 calendar weeks |
| Milestones | M1 Foundation · M2 Incremental/WAL · M3 Git + AA-MA · M4 Polish |
| Max milestone complexity | 75% (M2) — no milestone requires CoT deep-reasoning gate |

---

## Distribution Model (Dual)

Source lives in `aa-ma-forge` repo. Two distribution channels:

1. **aa-ma-forge plugin** — deployed via `scripts/install.sh` symlinks; full AA-MA integration active (`aa_ma_context` tool live).
2. **`pip install codemem-mcp`** — standalone wheel; generic code intel only; `aa_ma_context` returns informative no-op message: `"AA-MA integration unavailable; install aa-ma-forge"`.

Packaging structure **decided in Task 1.0 (2026-04-13): Option B — `packages/codemem-mcp/` subdir with uv workspace**. Prototype validated at `/tmp/codemem-spike/`. Root `pyproject.toml` adds `[tool.uv.workspace] members = ["packages/codemem-mcp"]`; `packages/codemem-mcp/pyproject.toml` declares `name="codemem-mcp"`, own deps, own hatchling build. Standalone wheel MUST NOT depend on `aa_ma`.

---

## Hard Dependencies

| Package | Version | Scope | Notes |
|---|---|---|---|
| `ast-grep-cli` | `>=0.42,<0.43` | runtime | 0.42.1 verified on PyPI with wheels for Linux + macOS + Windows manylinux/musllinux [valid: 2026-04-13] |
| `fastmcp` | (unpinned; already used by `/index`) | runtime | MCP server framework |
| `pytest-benchmark` | (dev only) | test | M1 perf budget enforcement |
| `hypothesis` | (dev only) | test | M2 property-based round-trip tests |
| `import-linter` | (dev only) | test | M1 layer boundary enforcement |
| `portalocker` | optional, `[windows]` extra | runtime | only if pure-stdlib Windows lock infeasible |

**Python stdlib used:** `sqlite3`, `ast`, `subprocess`, `pathlib`, `json`, `hashlib`, `re`, `dataclasses`, `fcntl` (POSIX) / `msvcrt` (Windows), `uuid`, `os`.

**External binary required on PATH:** `git`.

**Explicit non-dependencies (rejected):** `networkx`, `scipy`, `tree-sitter` (native), `lancedb`, `chromadb`, `pgvector`, `alembic`, `sqlalchemy`, `anthropic-sdk`, `gitpython`, `pydriller`, `code-maat`.

**Minimum Python:** `requires-python = ">=3.11"` on the standalone wheel; explicit OS classifiers declared. Linux + macOS are primary support; Windows is best-effort.

---

## SQLite PRAGMA Values (Pinned, Step 1.2)

```
PRAGMA foreign_keys=ON;
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA busy_timeout=5000;
PRAGMA cache_size=-65536;
PRAGMA mmap_size=268435456;
PRAGMA temp_store=MEMORY;
PRAGMA application_id=0x434D454D;  -- 'CMEM' ASCII, fits signed int32 (was 0xC0DE3E33 in plan draft — overflowed, corrected at Task 1.2 implementation)
```

Read-side MCP connections use `sqlite://…?mode=ro`.

Schema version progression via `PRAGMA user_version`:
- **v1** (M1): `files`, `symbols`, `edges` + indexes
- **v1 unchanged** (M2): NO SQLite schema mutations — only filesystem journaling (`.codemem/wal.jsonl`) and runtime locking (`.codemem/db.lock`, `.codemem/refresh.pid`); user_version stays at 1
- **v2** (M3 Task 3.8, SHIPPED 2026-04-14): adds `commits`, `ownership`, `co_change_pairs` **+ supporting junction `commit_files`** (not named in original plan §4; required so hot_spots/co_changes/symbol_history can query file↔commit without per-query git subprocess calls). `CURRENT_SCHEMA_VERSION = 2`.

Rollback granularity: M3→pre-M3 means `PRAGMA user_version=1` + `DROP TABLE commits, commit_files, ownership, co_change_pairs`. FK cascades on `commit_files` handle junction rows automatically when `commits` is dropped. Reconciled with plan §7 v3 revision.

---

## SCIP Symbol ID Grammar (Pinned, Step 1.2b)

Exact format documented in `docs/codemem/symbol-id-grammar.md`:

```
SCIP-ID    := <scheme> ' ' <package> ' ' <descriptor>
scheme     := 'codemem'            (shape only — NOT Sourcegraph SCIP wire format)
package    := <repo-relative-dir>  (e.g. 'packages/codemem-mcp/src/codemem')
descriptor := <kind-marker><file>'#'<symbol-path>
kind-marker:= '/' (term/def) | '#' (type) | '.' (member)
```

Examples:
- Python function: `codemem packages/codemem-mcp/src/codemem /storage/db.py#init_db`
- Python method:   `codemem packages/codemem-mcp/src/codemem /storage/db.py#DBHelper.connect`
- TS class:        `codemem src/web #app.tsx#UserCard`

Mandatory fixture coverage in Step 1.2b acceptance: Python decorated method, Python class with metaclass, **Java inner class + anonymous class**, TS namespace symbol, Go method on receiver, Rust impl block.

---

## Canonical Recursive CTE (Pinned, Step 1.7)

All MCP tools that walk the call graph MUST use this exact CTE shape (cycle-safe via the `path` column):

```sql
WITH RECURSIVE callers(sid, depth, path) AS (
  SELECT src_symbol_id, 1, '|' || src_symbol_id || '|'
  FROM edges WHERE dst_symbol_id = :target AND kind='call'
  UNION
  SELECT e.src_symbol_id, c.depth+1, c.path || e.src_symbol_id || '|'
  FROM edges e JOIN callers c ON e.dst_symbol_id = c.sid
  WHERE c.depth < :max_depth
    AND c.path NOT LIKE '%|' || e.src_symbol_id || '|%'
)
SELECT DISTINCT sid FROM callers;
```

Acceptance enforces: explain-plan uses indexes only (no table scan).

---

## File System Layout

```
aa-ma-forge/
├── pyproject.toml                   # Root aa-ma + [tool.uv.workspace]
├── claude-code/codemem/             # User-facing plugin
│   ├── commands/                    # /codemem slash command (codemem.md)
│   ├── skills/                      # reusable procedures
│   ├── hooks/
│   │   └── post-commit.sh           # symlink-wired by install.sh
│   └── mcp/
│       └── server.py                # FastMCP server; 12 tool slots
├── src/aa_ma/                       # aa-ma package (unchanged by codemem)
└── packages/codemem-mcp/            # codemem engine — standalone-installable
    ├── pyproject.toml               # name="codemem-mcp", own deps
    └── src/codemem/
        ├── storage/                 # schema.sql, db.py
        ├── parser/                  # python_ast.py, ast_grep.py
        ├── diff/                    # symbol_diff.py         (M2)
        ├── journal/                 # wal.py                 (M2)
        ├── analysis/                # git_mining.py          (M3)
        ├── mcp_tools/               # public import boundary
        ├── aa_ma_integration.py     # Optional-import glue for aa_ma_context tool
        └── cli/                     # codemem-cli entry point
├── docs/codemem/
│   ├── ARCHITECTURE.md              # M1 deliverable, finalized M4
│   ├── symbol-id-grammar.md         # M1
│   ├── performance-slo.md           # M1
│   ├── design-scratchpad.md         # M1 Step 1.0
│   ├── migration-from-index.md      # M4
│   ├── install-zero-config.md       # M4
│   └── kill-criteria.md             # M4
├── docs/benchmarks/
│   ├── codemem-vs-index.md          # M4
│   └── codemem-vs-aider.md          # M4
├── docs/demo/
│   └── codemem-co-changes.{cast,gif}# M4
├── tests/codemem/                   # unit + integration
├── tests/perf/test_budgets.py       # pytest-benchmark
├── tests/fixtures/codemem/
│   ├── sample_repo/
│   ├── adversarial/                 # malicious paths, binaries, 100MB .ts, symlink loops
│   └── aa_ma_context/sample-task/   # golden: sample-tasks.md, sample-reference.md, expected.json
├── tests/golden/
│   └── layers_aa_ma_forge.txt       # M3 layers() golden output
└── examples/codemem/                # sample PROJECT_INTEL.json
```

**Runtime artifacts (git-ignored):**
- `.codemem/` — db, wal.jsonl, refresh.log, refresh.pid, db.lock
- `.codemem/wal.jsonl.{1,2,3}.gz` — rotated WAL archives (M2)

`.codemem/` MUST be listed in repo `.gitignore` (Step 1.1 acceptance enforces).

---

## 12 MCP Tools (Canonical Names + Aliases)

Registered in `mcp/server.py`. Aliases exposed for cross-tool discoverability via Anthropic Tool Search.

### Ported from `/index` (M1, tools 1–6)

| # | Canonical | Aliases |
|---|---|---|
| 1 | `who_calls` | `find_references` |
| 2 | `blast_radius` | — |
| 3 | `dead_code` | `find_dead_code` |
| 4 | `dependency_chain` | — |
| 5 | `search_symbols` | — |
| 6 | `file_summary` | — |

### Git mining (M3, tools 7–11)

| # | Canonical | Notes |
|---|---|---|
| 7 | `hot_spots` | top-N files by (commits last 90d) × (function count) |
| 8 | `co_changes` | files co-changing with input ≥3 commits, no import edge; excludes CHANGELOG/README by default |
| 9 | `owners` | per-file/dir author %; 2s timeout; `--no-owners` skip flag |
| 10 | `symbol_history` | `git log -L:symbol:file`; per-file if multi-file |
| 11 | `layers` | in-degree bucketing → 3-layer ASCII onion (core/middle/periphery) |

### AA-MA-native (M3, tool 12)

| # | Canonical | Notes |
|---|---|---|
| 12 | `aa_ma_context` | moat — validates task against `.claude/dev/active/*/`; optional `--write` mode |

All tools enforce hard token budget (default 8000, configurable). M1 lights up 1–6; M3 adds 7–12.

---

## Performance SLO Targets

Enforced by `tests/perf/test_budgets.py` with `pytest-benchmark`. CI fails when any budget regresses by >10%.

| SLO | Budget | Milestone gate |
|---|---|---|
| `codemem build` cold on `/index` repo (~10k LOC Python) | < 30s | M1 |
| `codemem build` warm (same) | < 5s | M1 |
| `who_calls("extract_python_signatures")` on `/index` index_utils.py | < 100ms | M1 |
| `codemem build` wall-clock vs `/index` on each reference repo | ≤ 1.5× | M4 |
| `codemem refresh` after 10-line edit | < 500ms | M2 |
| `codemem refresh` median on medium repo | < 800ms | M4 |
| Each M3 git-mining tool on aa-ma-forge | < 1s | M3 |
| `hot_spots()` on 50k-file synthetic fixture | < 5s | M3 |
| `PROJECT_INTEL.json` token size at default budget | ≤ 1024 tokens | M1 |
| `PROJECT_INTEL.json` overall size | ≤ 5KB on aa-ma-forge | M1 |

---

## Reference Repos for Benchmarks (M4 Step 4.1)

| Repo | Size | Role |
|---|---|---|
| `aa-ma-forge` | small | dogfood + AA-MA integration test bed |
| `repowise` | medium | symbol-level diff cross-check |
| A 50k-LOC OSS Python project | large | scale ceiling |

Bench script runs build, refresh, and 3 representative MCP queries against `/index` on each. Results to `docs/benchmarks/codemem-vs-index.md` with reproducibility notes (5 runs, median).

---

## Anchor Symbol for Tests (per audit V1)

**`extract_python_signatures`** in `~/.claude-code-project-index/scripts/index_utils.py` — verified-existent symbol used as:

- M1 AC: `who_calls("extract_python_signatures")` must return within 100ms
- M3 AC: `symbol_history("extract_python_signatures", file_path="~/.claude-code-project-index/scripts/index_utils.py")` must correctly identify the introducing commit

The 6 M1 ported MCP tools are also JSON-equality-tested against `/index` for 3 reference queries on aa-ma-forge OR on `/index` itself (pivot target, since `aa-ma-forge/src/aa_ma/` is an empty skeleton at plan time).

---

## Embeddings Exit Criterion (verbatim from §8, per CEO C3)

> **No semantic search in v1.** We will reconsider when EITHER (a) `search_symbols` exact-match returns zero results for >20% of agent queries over a 30-day measurement window (requires opt-in telemetry, M5+ feature), OR (b) a competitor demonstrates a clear quality lift on a public benchmark with embeddings + lightweight footprint (e.g. embedded ONNX model under 50MB total) AND that quality lift is reproducible on 3 of our reference repos. Until then, no.

---

## Kill Criteria (verbatim from §12, per CEO C5)

Committed publicly in `docs/codemem/kill-criteria.md`:

- **30 days post-ship:** < 25 GitHub stars on aa-ma-forge AND < 5 external installs of `codemem-mcp` → **signal-kill**, fold capabilities back into `/index`.
- **M1 exit:** `codemem build` > 1.5× `/index` wall-clock on reference repos AND PageRank projection doesn't beat Aider's repo-map token efficiency → **architectural kill**, the SQLite-canonical bet isn't paying off.
- **M3 exit:** `co_changes` produces noise > signal on 2/3 test repos (manual eval: <50% of top-5 results meaningful) → **headline-tool kill**, drop to 4 git-mining tools and reposition.
- **Anytime:** GitNexus or Axon ships git-mining in ≥3 of our 5 tools with comparable UX → **moat evaporated**, pivot positioning to AA-MA-coupled differentiator (the `aa_ma_context` tool) immediately.
- **M2 exit:** Crash-injection test cannot be made deterministic → **correctness-risk kill**, drop WAL JSONL feature, ship M1 + M3 only.

---

## WAL JSONL Replay State Diagram (Step 2.3, embedded in ARCHITECTURE.md §Dual-WAL-Semantics)

```
for entry in wal.jsonl (in order):
  if entry.id in acked_ids:                       # SQLite write completed
    continue                                       # skip, already applied
  if compute_current_state(entry.args) == entry.target_state:
    log_warning("idempotent skip", entry.id)      # crash AFTER commit, BEFORE ack write
    append_ack(entry.id)
    continue
  if entry.prev_user_version != current_user_version:
    raise ReplayConflict(entry.id,
                         expected=entry.prev_user_version,
                         got=current_user_version)
  apply_to_sqlite(entry)                           # txn-wrapped
  append_ack(entry.id)                             # mark applied
```

**Crash-safe ordering contract:** every mutation appends intent JSON line to `.codemem/wal.jsonl` BEFORE SQLite write → SQLite write (atomic txn) → SECOND append `{"ack": true, "id": <wal_id>}` AFTER commit. Append is atomic via `O_APPEND`.

**Entry schema:** `{"id": uuid, "ts": iso, "op": str, "args": dict, "prev_user_version": int, "content_sha": str}`.

**Idempotency key:** `(op, prev_user_version, content_sha)`.

Two engineers implementing this diagram independently MUST produce identical replay semantics.

**Rotation:** at 10MB → keep last 3 as `wal.jsonl.{1,2,3}.gz`; replay tool reads across rotation boundary.

---

## `aa_ma_context` Extraction Rule (Step 3.7, per audit V4)

Pinned to prevent divergent implementations.

**File mentions in `*-tasks.md` / `*-reference.md`:** any backticked path matching regex
```
\x60([a-zA-Z0-9_\-./]+\.[a-zA-Z0-9]{1,5})\x60
```
where the file exists relative to repo root.

- Match: `` `packages/codemem-mcp/src/codemem/storage/db.py` ``, `` `tests/conftest.py` ``
- No match: bare `src/foo.py` (no backticks), `` `not_a_real_file.py` `` (doesn't exist on disk)

**Symbol mentions in `*-reference.md`:** any backticked identifier matching
```
\x60([a-zA-Z_][a-zA-Z0-9_.]{0,63})\x60
```
that ALSO appears in the SQLite `symbols.name` column for the indexed repo. Filters out arbitrary backticked words like `True`, `None`, common verbs.

**Golden fixture:** `tests/fixtures/aa_ma_context/sample-task/` contains `sample-tasks.md`, `sample-reference.md`, and `expected.json` for byte-for-byte integration test.

Output: structured Markdown fragment, ~80 LOC implementation. Optional `--write` appends to reference.md with timestamp.

---

## Input Sanitization Contract (Step 1.7, per audit V5)

Applies to every MCP tool accepting user input.

- **Path args:** `Path(input).resolve(strict=False)` then assert `resolved.is_relative_to(repo_root)`. Rejects path traversal **even after canonicalization**.
- **Symbol/file string args:** allow-list regex `^[A-Za-z0-9_./\-]{1,256}$` PLUS explicit rejection of `..` substring.
- **Rejection happens BEFORE SQL.**

Adversarial test suite fixtures (M1 acceptance): `../../etc/passwd`, `/etc/passwd`, `foo/../../bar`, 10KB unicode strings, `'; DROP TABLE`, regex metacharacters in `-L` context, binary file tracked, 100MB .ts file, symlink loops, non-UTF8 source, submodule boundaries.

---

## Layering Contract (import-linter enforced, Step 1.11)

- `claude-code/codemem/` (user-facing surface) MUST NOT import directly from `aa_ma.codemem.{storage,parser,diff,journal}`.
- Only `aa_ma.codemem.mcp_tools` is a permitted import boundary.
- CI job runs `import-linter`; violation fails the pipeline.
- ARCHITECTURE.md §Layering-contract documents this invariant.

---

## Parser Public API (pinned, Step 1.3)

Module: `codemem.parser.python_ast`

```python
@dataclass
class Symbol:
    scip_id: str
    name: str
    kind: str              # 'function'|'async_function'|'method'|'async_method'|'class'
    line: int
    signature: str | None   # decorators as '@name' lines, then '(params) -> return'
    signature_hash: str | None  # sha256 hex of signature; None for classes in v1
    docstring: str | None   # first line only
    parent_scip_id: str | None  # string ref; driver (Task 1.5) resolves to FK

@dataclass
class CallEdge:
    src_scip_id: str
    dst_scip_id: str | None
    dst_unresolved: str | None
    kind: str = "call"

@dataclass
class ParseResult:
    symbols: list[Symbol]
    edges: list[CallEdge]

def extract_python_signatures(
    source: str, *, package: str, file_rel: str,
) -> ParseResult: ...
```

**Contract invariants:**
- Symbols emitted ONLY for: module-level functions, module-level classes, class-level methods, nested classes. No nested functions, lambdas, or comprehensions in v1.
- `parent_scip_id` is a string reference resolved to FK `symbols.parent_id` at insert time by the Task 1.5 driver.
- Call edges are intra-file ONLY (cross-file resolution = Task 1.6).
- On ambiguous name match (same-named methods across sibling classes), emit one edge per target — v1 over-emits by design; query-layer dedupe acceptable.
- `SyntaxError` → empty `ParseResult`. No regex fallback here; ast-grep wrapper (Task 1.4) handles broader cases.
- Signature format is stable — any change to `_build_signature` invalidates M2 `signature_hash` diffing and requires a schema migration plan.

---

## ast-grep Wrapper Invariants (pinned, Step 1.4)

Module: `codemem.parser.ast_grep`

- **Subprocess form**: `sg scan -r <RULE_YAML> --json=stream --include-metadata <FILES...>`. `sg run` is pattern-based and reserved for ad-hoc queries; `sg scan` takes rule files.
- **Per-language batching**: one subprocess per language. All files of that language pass as positional args in a single invocation. Empirically verified.
- **`.ts` vs `.tsx` split**: TypeScript and Tsx are distinct ast-grep languages. Never combine their rules or files — a TypeScript rule does NOT match a `.tsx` file. Rule filenames and the `SUPPORTED_LANGUAGES` map must agree.
- **Rule-id contract**: rules end with one of `-function-def`, `-class-def`, `-interface-def`, `-struct-def`, `-module-def`, `-type-alias`, `-method-def`, `-import`, `-call`. The wrapper's `_KIND_BY_RULE_SUFFIX` dispatches on these suffixes. Adding a new kind requires updating the map AND the grammar doc.
- **Parent inference**: methods find their enclosing container by line-range containment (`pstart < m.line AND m.end_line <= pend`). Innermost wins. Orphan methods (no enclosing class) are skipped, not emitted with `None` parents.
- **Edge emission**: `extract_with_ast_grep` returns `edges=[]` always. Imports + calls are deferred to Task 1.6 (cross-file resolver) because ast-grep matches carry no scope context for local-call resolution.
- **SCIP language scope**: rule files ship for the 7 AC-declared languages (TypeScript, Tsx, JavaScript, Go, Rust, Java, Ruby, Bash). Adding a language requires: (a) `SUPPORTED_LANGUAGES` entry, (b) `_RULE_FILE_BY_LANG` entry, (c) new `rules/*.yml`, (d) grammar-doc example, (e) `TestRuleFilesShipped` parametrization.

---

## Indexer Driver Contract (pinned, Step 1.5)

Module: `codemem.indexer`

- **Bulk-load ordering**: upsert_files → bulk_insert_symbols (parent_id NULL) → resolve_parent_ids (executemany UPDATE by scip_id) → bulk_insert_edges. This ordering matters: edges reference symbol IDs that only exist after symbols are inserted.
- **FK PRAGMA discipline**: `PRAGMA foreign_keys = OFF` must be set OUTSIDE any transaction per SQLite docs — toggling inside a tx is silently ignored. Sequence: OFF → BEGIN → executemany → COMMIT → ON → foreign_key_check → integrity_check.
- **Idempotency**: re-indexing the same file set deletes its rows first (`DELETE FROM files WHERE path IN (...)`) — CASCADE removes dependent symbols + edges — then re-inserts. Second run produces identical counts.
- **Discovery fallback**: `git ls-files` is preferred (free `.gitignore` respect); rglob fallback for non-git directories. Unsupported extensions are filtered at discovery, never passed to the parsers.
- **File paths**: `files.path` stores the POSIX-normalized path relative to repo_root. This is the join key across queries, the idempotency key for re-index, and the input to SCIP-ID construction.
- **Parser dispatch**: `.py` → stdlib `python_ast`; all other supported extensions → batched `ast_grep`. Python parse errors are counted in `BuildStats.python_parse_errors` (non-fatal).

---

## 4-Strategy Cross-File Resolver (pinned, Step 1.6)

Module: `codemem.resolver`

- **Strategy order**: direct → relative-to-source-dir → package-prefix (`src.`/`scripts.`/`lib.`/`app.`) → suffix-match. First-hit wins; never resolves to source file itself.
- **Import map**: `file_paths` → `{dotted_name: file_path}`. Python-only for v1. `__init__.py` registers both `pkg.__init__` and `pkg` (package-level shortcut).
- **Parser contract**: `ParseResult.imports` = dotted module names from `ast.Import` + `ast.ImportFrom`. `ParseResult.unresolved_edges` = cross-file call candidates (`dst_unresolved` populated, `dst_scip_id=None`). These are disjoint from `ParseResult.edges` (intra-file resolved).
- **Built-in filter**: `_CALL_EXCLUDE` (print, len, str, ...) applied in `_extract_call_names` — never leaks to either edge list.
- **Resolver output**: one row per (caller_symbol_id, matched_target_symbol_id, kind); when a callee name matches N targets in N resolved target files, N edges emit (over-emit acceptable per parser grammar v1 ambiguity policy).
- **Unresolved persistence**: when no target resolves OR no target's symbols match the callee name, the edge is persisted with `dst_unresolved` = callee name string. Schema CHECK guarantees at least one of `dst_symbol_id` / `dst_unresolved` is non-null.
- **Build-stats counters**: `cross_file_resolved` counts upgraded edges; `cross_file_unresolved` counts dangling ones. Total `edges_inserted = intra_file + cross_file_resolved + cross_file_unresolved`.

---

## MCP Tools Public Surface (pinned, Step 1.7)

Module: `codemem.mcp_tools` — 6 tool functions returning JSON-serialisable dicts.

```python
who_calls(db_path, name, *, max_depth=3, budget=8000) -> dict
blast_radius(db_path, name, *, max_depth=3, budget=8000) -> dict
dead_code(db_path, *, budget=8000) -> dict
dependency_chain(db_path, source, target, *, max_depth=5, budget=8000) -> dict
search_symbols(db_path, query, *, budget=8000) -> dict
file_summary(db_path, path, *, budget=8000, repo_root=None) -> dict
```

**Contract invariants:**
- **Read-only**: every tool opens SQLite with `mode=ro`. No tool mutates state.
- **Sanitization first**: every string arg passes through `sanitize_symbol_arg` or `sanitize_path_arg` BEFORE any SQL. Failure returns `{"error": str, ...}` — never raises.
- **Budget enforcement**: JSON char-count heuristic (1 token ≈ 4 chars). Binary-search truncation on the primary list; adds `truncated: bool` to payload.
- **Canonical CTEs**: `who_calls` and `blast_radius` use the pinned CTEs in `codemem.mcp_tools.queries` (WHO_CALLS_CTE, BLAST_RADIUS_CTE). These use the covering indexes (`idx_edges_dst`, `idx_edges_src`) — empirically verified via EXPLAIN QUERY PLAN.
- **Name resolution policy**: bare-name args resolve to ALL symbols with that name (methods on different classes, overloads across files). `who_calls`/`blast_radius` merge results; `dependency_chain` picks the shortest path across the Cartesian product.
- **Kind filter for `dead_code`**: only `function`/`method`/`async_function`/`async_method` — classes/type-aliases never flagged dead.
- **Zero exceptions on bad input**: the adversarial test suite (path traversal, 10KB unicode, SQL injection, regex metachars) returns structured errors; no tool raises under untrusted input.

---

## PROJECT_INTEL.json Schema v1 (pinned, Step 1.8)

Schema header: `codemem/project-intel@1`. Writer: `codemem.pagerank.write_project_intel`.

```json
{
  "_meta": {
    "schema": "codemem/project-intel@1",
    "budget": 1024,
    "damping": 0.85,
    "total_symbols": 321,
    "written_symbols": 89
  },
  "symbols": [
    {
      "scip_id": "codemem . /packages/.../foo.py#bar",
      "name": "bar",
      "kind": "function",
      "file": "packages/.../foo.py",
      "line": 42,
      "rank": 0.07321
    }
  ]
}
```

**Contract invariants:**
- Serialised with `separators=(",", ":"), sort_keys=True` for byte-level determinism.
- Primary sort: descending `rank`. Secondary tie-break: `_KIND_PRIORITY` (function=0, method=1, class=2, type_alias=3) → file → line → name.
- `symbols` list is truncated via binary search over char count ≤ `budget × 4` (1:4 token:char).
- Trailing newline always present (POSIX text-file convention, git-friendly).
- Schema version bump (v1→v2) required for any change to the `symbols` entry shape or `_meta` keys.

---

## V2 Schema DDL (pinned, Task 3.8)

Source of truth: `packages/codemem-mcp/src/codemem/storage/db.py :: _MIGRATION_V2_GIT_MINING`. Contract invariants below are enforced by `tests/codemem/test_schema_v2.py` (27 tests) + the existing test_schema.py integrity/FK cases.

```sql
-- commits: one row per cached commit (writer enforces ≤500 retention policy per Task 3.1)
CREATE TABLE commits (
    sha           TEXT    PRIMARY KEY,
    author_email  TEXT    NOT NULL,
    author_time   INTEGER NOT NULL,  -- unix epoch, from `git log --pretty=%at`
    message       TEXT    NOT NULL   -- subject line only (%s)
);
CREATE INDEX idx_commits_author_time ON commits(author_time);

-- commit_files: junction — required for hot_spots/co_changes/symbol_history.
-- Not named in plan §4 but documented as required implementation detail.
CREATE TABLE commit_files (
    commit_sha  TEXT NOT NULL REFERENCES commits(sha) ON DELETE CASCADE,
    file_path   TEXT NOT NULL,     -- repo-relative; may reference a now-deleted file
    PRIMARY KEY (commit_sha, file_path)
);
CREATE INDEX idx_commit_files_path ON commit_files(file_path);

-- ownership: cached `git blame --line-porcelain` percentages
CREATE TABLE ownership (
    file_path    TEXT    NOT NULL,
    author_email TEXT    NOT NULL,
    line_count   INTEGER NOT NULL,
    percentage   REAL    NOT NULL,   -- 0.0 .. 100.0
    computed_at  INTEGER NOT NULL,   -- unix epoch — cache key
    PRIMARY KEY (file_path, author_email)
);
CREATE INDEX idx_ownership_file ON ownership(file_path);

-- co_change_pairs: materialised co-change counts. CHECK canonicalises ordering.
CREATE TABLE co_change_pairs (
    file_a       TEXT    NOT NULL,
    file_b       TEXT    NOT NULL,
    count        INTEGER NOT NULL,
    last_commit  TEXT    REFERENCES commits(sha) ON DELETE SET NULL,
    PRIMARY KEY (file_a, file_b),
    CHECK (file_a < file_b)
);
CREATE INDEX idx_co_change_pairs_a ON co_change_pairs(file_a);
CREATE INDEX idx_co_change_pairs_b ON co_change_pairs(file_b);
```

**Migration contract invariants:**
- All DDL uses `CREATE TABLE/INDEX IF NOT EXISTS` — a crash between `executescript` and `PRAGMA user_version=2` leaves the DB still safely advanceable on retry.
- `migrate(conn)` wraps each step in `with conn:` so SQLite auto-rolls-back on failure.
- `CURRENT_SCHEMA_VERSION = 2` in `codemem.storage.db`. Fresh `apply_schema()` still produces v1 (schema.sql is frozen at v1); `migrate()` advances.
- `co_change_pairs.last_commit` uses `ON DELETE SET NULL` (not CASCADE) — evicting a cached commit must not delete an otherwise-valid pair.
- Ordering for co-change pair storage: caller MUST swap arguments if `a > b`. `tuple(sorted([a,b]))` is the canonical pattern.

---

## Git Integration

- **Commit base:** `d44c1c8` on `main`, branch `expt/code_mem_store_what` [valid: 2026-04-13].
- **Post-commit hook wiring (Step 1.11, per audit V6):** `install.sh` either (a) appends guarded line to `.git/hooks/post-commit`, OR (b) sets `git config core.hooksPath claude-code/codemem/hooks`. Trade-off documented in `install.sh` comments.
- **Commit signature (AA-MA active):** every commit footer must end with
  ```
  [AA-MA Plan] codemem .claude/dev/active/codemem
  ```
