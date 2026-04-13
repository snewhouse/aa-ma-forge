# codemem — Reference (Immutable Facts)

_This file is the highest-priority AA-MA memory artifact. Load FIRST when resuming this task. Facts below are extracted from `codemem-plan.md` v3 and are non-negotiable unless the plan itself is revised._

_Last Updated: 2026-04-13 14:30_

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
PRAGMA application_id=0xC0DE3E33;
```

Read-side MCP connections use `sqlite://…?mode=ro`.

Schema version progression via `PRAGMA user_version`:
- **v1** (M1): `files`, `symbols`, `edges` + indexes
- **v1 unchanged** (M2): NO SQLite schema mutations — only filesystem journaling (`.codemem/wal.jsonl`) and runtime locking (`.codemem/db.lock`, `.codemem/refresh.pid`); user_version stays at 1
- **v2** (M3): adds `commits`, `ownership`, `co_change_pairs`

Rollback granularity: M3→pre-M3 means `PRAGMA user_version=1` + drop the 3 new tables. Reconciled with plan §7 v3 revision (scribe-flagged inconsistency closed).

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

## Git Integration

- **Commit base:** `d44c1c8` on `main`, branch `expt/code_mem_store_what` [valid: 2026-04-13].
- **Post-commit hook wiring (Step 1.11, per audit V6):** `install.sh` either (a) appends guarded line to `.git/hooks/post-commit`, OR (b) sets `git config core.hooksPath claude-code/codemem/hooks`. Trade-off documented in `install.sh` comments.
- **Commit signature (AA-MA active):** every commit footer must end with
  ```
  [AA-MA Plan] codemem .claude/dev/active/codemem
  ```
