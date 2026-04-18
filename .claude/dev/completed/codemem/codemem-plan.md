<!-- ARCHIVED: 2026-04-18 13:10 -->
<!-- Plan: codemem - COMPLETE -->
<!-- Total Milestones: 5 (M1, M2, M3, M3.5, M4) | Duration: 2026-04-13 to 2026-04-18 -->

# codemem — Implementation Plan (v3 — post adversarial verification)

**Task:** `codemem` — Lightweight codebase intelligence MCP tool for Claude Code
**Owner:** Stephen Newhouse + AI
**Created:** 2026-04-13
**Last Updated:** 2026-04-13 (v1 → v2 post CEO+Eng reviews → v3 post adversarial verification, all CRITICALs + high-impact WARNs closed)
**Branch:** `expt/code_mem_store_what` (in `aa-ma-forge`)

## 1. Executive Summary

Build `codemem`, a lightweight codebase intelligence tool: pure Python + ast-grep + SQLite, exposing **12 MCP tools** to Claude Code (6 ported from `/index` + 5 git-mining + 1 AA-MA-native coupling tool). Differentiator vs the crowded 2026 field is the **git-mining quintet** (`hot_spots`, `co_changes`, `owners`, `symbol_history`, `layers`) plus an Aider-style PageRank-budgeted repo-map projection plus a unique **AA-MA auto-context** tool that nobody else can copy. Distributed as both an aa-ma-forge plugin component and a standalone `pip install codemem-mcp` package. Will supersede `/index` once stable; ships in 4 milestones over an estimated 14–18 days of focused work.

## 2. Context & Motivation

Current `/index` (`~/.claude-code-project-index/`) has solid bones — SQLite cache, monolithic JSON projection, 6 MCP tools, **and a 89-LOC pure-Python symbol-level PageRank in `scripts/pagerank.py`** (per Task 1.0 AF-4 finding; /index is ALREADY symbol-level, plan v3 misframed this). Three structural debts remain: ~1500 LOC of fragile JS/TS regex; a JSON-canonical model that couples index size to context budget; no git-derived intelligence. The 2026 landscape (GitNexus now 27k stars and accelerating, Axon, Codegraph, jCodeMunch, CodeMCP, RemembrallMCP, DevSwarm, Code Pathfinder, Kiro CLI) shows where the category is converging — semantic analysis + type resolution + PDG via tree-sitter + MCP — and where it isn't going (git mining + AA-MA-native context are uncontested).

**Sharpened differentiation vs `/index`'s existing PageRank (per Task 1.0 readings):** `/index` already does symbol-level PageRank; codemem adds four things it lacks — (1) **edge weighting** (subset of Aider's quality heuristics: `sqrt(num_refs)` dampening, private-name dampening, length-filtering for trivial names), (2) **token-budget binary search** over ranked output (Aider-style, adapted to fit SQLite-derived ranking), (3) **SCIP-shaped symbol IDs** for cross-tool interop, (4) **no top-200 truncation** — keep all scores. Implementation approach: **fork /index's 89-LOC pagerank.py** and extend (~150-200 LOC total, pure Python stdlib — NOT NetworkX/scipy despite that being Aider's approach).

This plan evolves `/index`'s strengths and adopts targeted ideas from `repowise` (unified parser abstraction, symbol-level diffs, co-change mining), `mempalace` (WAL JSONL journaling, hard token budgets, metadata-first filtering), and `Aider` (PageRank-budgeted repo-map), while explicitly rejecting heavy deps (no tree-sitter native packs, no NetworkX, no LanceDB, no embeddings, no LLM in the indexer).

## 3. Locked Design Decisions

| # | Decision | Source |
|---|---|---|
| 1 | Sibling tool in `aa-ma-forge`; supersedes `/index` after proven; **also** ships as standalone `pip install codemem-mcp` | Q1 + Q13 |
| 2 | `ast-grep-cli` as required Python dep (not PATH binary) | Q2 + research |
| 3 | SQLite canonical, ~50KB JSON projection (Aider-style PageRank-ranked) | Q3 + research |
| 4 | **12 MCP tools** (6 ported + 5 git-mining + 1 AA-MA-native) | Q4 + Q12 |
| 5 | No semantic search / embeddings in v1 (with explicit exit criterion — see §8) | Q5 + CEO C3 |
| 6 | Symbol-level diff cache + WAL JSONL journal **with post-commit ack marker + idempotent replay keys** | Q6 + Eng E1 |
| 7 | 4 milestones (foundation → incremental → git-intel + AA-MA hook → polish) | Q7 |
| 8 | `/codemem` slash command + MCP server + post-commit hook | Q8 |
| 9 | **AA-MA-native coupling: `aa_ma_context()` MCP tool auto-populates active task's reference.md** | Q12 |
| 10 | **ARCHITECTURE.md as M1 deliverable** with 5 mandatory sections (per Eng E9) | Eng E9 |

## 4. Stepwise Implementation Plan

### Milestone M1: Foundation (shippable as v0.1)

**Goal:** Working tool that matches `/index` capability on a SQLite-canonical foundation, with the Aider repo-map as its standout feature, plus performance budgets enforced as tests, plus ARCHITECTURE.md.

- **Step 1.0: Pre-flight reading + packaging spike + design scratchpad** (Mode: HITL) — (a) Read Aider's `aider/repomap.py` to validate PageRank claim empirically; (b) read `/index`'s `scripts/pagerank.py` to map the file-level vs our symbol-level differentiation precisely; (c) skim `repowise`'s `symbol_diff` to validate Jaccard threshold; (d) read GitNexus's last 30 days of issues to surface roadmap collisions; (e) review `lessons.md` L-052 (recurring issues = architectural deficiency) re embeddings decision. **Packaging spike (per V8):** validate dual-distribution claim — prototype either (i) hatchling workspace with two `[project]` blocks, OR (ii) `packages/codemem-mcp/` subdir with separate pyproject (uv workspace), OR (iii) hatch build hook. Pick one, document trade-offs in scratchpad. Output: `docs/codemem/design-scratchpad.md` capturing all 5 readings + chosen packaging structure. Acceptance: scratchpad committed; packaging structure decided and reflected in Step 1.1; any plan-altering findings flagged in context-log.md.

- **Step 1.1: Project scaffold + dual-distribution packaging** (AFK) — **Structure decided in Task 1.0 (Option B — uv workspace):**
  ```
  aa-ma-forge/
  ├── pyproject.toml                       # Root: aa-ma + [tool.uv.workspace] members=["packages/codemem-mcp"]
  ├── src/aa_ma/                           # aa-ma package (unchanged)
  ├── claude-code/codemem/                 # User-facing plugin: commands/, skills/, hooks/, mcp/
  └── packages/codemem-mcp/                # codemem source (new)
      ├── pyproject.toml                   # codemem-mcp standalone: name="codemem-mcp"
      └── src/codemem/                     # Engine: parser/, storage/, projection/, mcp_tools/, cli/, aa_ma_integration.py
  ```
  Create the two directory trees; write both pyproject.toml files. Root adds `[tool.uv.workspace]`; `packages/codemem-mcp/pyproject.toml` declares deps `ast-grep-cli>=0.42,<0.43`, `fastmcp>=2.0`; entry points `codemem-cli`, `codemem-mcp-server`. **AA-MA integration glue lives at `packages/codemem-mcp/src/codemem/aa_ma_integration.py` with optional-import guard** (no-op if aa-ma-forge not in PYTHONPATH) — single source of truth for the `aa_ma_context` tool (per AF-14). **Pin verified 2026-04-13:** ast-grep-cli 0.42.1 on PyPI with wheels for Linux+macOS+Windows manylinux/musllinux. **Append `.codemem/` to repo `.gitignore`.** Acceptance: from root, `uv sync` resolves workspace; `pip install .` installs aa-ma; from `packages/codemem-mcp/`, `pip install .` installs codemem-mcp standalone with zero aa-ma dep; both wheels build in CI on Linux + macOS; `cat .gitignore | grep "\.codemem/"` returns a match.

- **Step 1.2: SQLite schema + DDL — explicit DDL pinned** (AFK) — Write `schema.sql`. Pinned tables and constraints:
  ```sql
  PRAGMA foreign_keys=ON;
  PRAGMA journal_mode=WAL;
  PRAGMA synchronous=NORMAL;
  PRAGMA busy_timeout=5000;
  PRAGMA cache_size=-65536;
  PRAGMA mmap_size=268435456;
  PRAGMA temp_store=MEMORY;
  PRAGMA application_id=0x434D454D;  -- 'CMEM' ASCII (was 0xC0DE3E33 in plan v3; signed-int32 overflow caught during Task 1.2 test)

  CREATE TABLE files (
    id INTEGER PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
    lang TEXT NOT NULL,
    mtime INTEGER, size INTEGER, content_hash TEXT,
    last_indexed INTEGER NOT NULL
  );
  CREATE TABLE symbols (
    id INTEGER PRIMARY KEY,
    file_id INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    scip_id TEXT NOT NULL,           -- SCIP-shaped, see §SCIP grammar below
    name TEXT NOT NULL,
    kind TEXT NOT NULL,              -- function|class|method|var|import|...
    line INTEGER, signature TEXT, signature_hash TEXT,
    docstring TEXT,
    parent_id INTEGER REFERENCES symbols(id) ON DELETE CASCADE,
    UNIQUE(file_id, scip_id)
  );
  CREATE TABLE edges (
    src_symbol_id INTEGER NOT NULL REFERENCES symbols(id) ON DELETE CASCADE,
    dst_symbol_id INTEGER REFERENCES symbols(id) ON DELETE CASCADE,
    dst_unresolved TEXT,             -- for cross-file edges to unresolved targets
    kind TEXT NOT NULL,              -- call|import|inherit
    PRIMARY KEY(src_symbol_id, kind, dst_symbol_id, dst_unresolved)
  );
  CREATE INDEX idx_edges_dst ON edges(dst_symbol_id, kind, src_symbol_id);
  CREATE INDEX idx_edges_src ON edges(src_symbol_id, kind, dst_symbol_id);
  CREATE INDEX idx_symbols_file_kind_name ON symbols(file_id, kind, name);
  CREATE INDEX idx_symbols_name ON symbols(name);
  ```
  Forward-only `PRAGMA user_version` migration framework. Acceptance: schema validates; FK constraints enforced; explain-plan on `who_calls(N=3)` query uses indexes only.

- **Step 1.2b: SCIP-shaped symbol ID grammar — pinned** (AFK) — Define exact format and document in `docs/codemem/symbol-id-grammar.md`. Format:
  ```
  SCIP-ID := <scheme> ' ' <package> ' ' <descriptor>
  scheme   := 'codemem' (we are not emitting Sourcegraph SCIP wire format, just shape)
  package  := <repo-relative-dir> (e.g. 'src/aa_ma/codemem')
  descriptor := <kind-marker><file>'#'<symbol-path>
  kind-marker := '/' (term/def) | '#' (type) | '.' (member)
  ```
  Examples:
  - Python function: `codemem src/aa_ma/codemem /storage/db.py#init_db`
  - Python method: `codemem src/aa_ma/codemem /storage/db.py#DBHelper.connect`
  - TS class: `codemem src/web #app.tsx#UserCard`
  Acceptance: grammar doc committed; one parser-emitted ID per language fixture in tests.

- **Step 1.3: Python parser via stdlib `ast`** (AFK) — Port `extract_python_signatures()` from `/index`. Output: list of `Symbol` dataclasses + intra-file call edges + canonical SCIP ID per symbol.

- **Step 1.4: ast-grep parser via subprocess + batching** (AFK) — Wrapper that invokes `sg run --json=stream` with YAML rule files. **Batch invocations per language** (one sg invocation across N files, not N invocations) to amortize subprocess overhead (~50ms/invocation). Rules for: `function_definition`, `class_definition`, `method_definition`, `import_statement`, `call_expression` for TypeScript, JavaScript, Go, Rust, Java, Ruby, Bash. Set `languageGlobs` for `.ts` ↔ `.tsx` disambiguation. Acceptance: parsing 100 mixed-language files completes in <10s on aa-ma-forge.

- **Step 1.5: File discovery + indexer driver** (AFK) — `git ls-files` based discovery (respects .gitignore). Dispatch per-language batched parser, one transaction per language, `executemany`, `foreign_keys=OFF` during bulk insert + re-enable + integrity check.

- **Step 1.6: Cross-file edge resolution** (AFK) — Port import-resolver logic from `/index` (4-strategy fallback). Materialize cross-file edges in `edges` table with `dst_unresolved` for unresolved targets.

- **Step 1.7: 6 ported MCP tools with input sanitization contract + canonical CTE** (AFK) — Implement `who_calls`, `blast_radius`, `dead_code`, `dependency_chain`, `search_symbols`, `file_summary`. **Canonical recursive CTE** (embedded here so all queries are identical):
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
  Each tool has hard token budget (default 8000, configurable). **Input sanitization rule (per V5)**: (a) path args resolved via `Path(input).resolve(strict=False)` then assert `resolved.is_relative_to(repo_root)` — **rejects path traversal even after canonicalization**; (b) symbol/file string args validated via allow-list regex `^[A-Za-z0-9_./\-]{1,256}$` and additional rejection of `..` substring; (c) reject before SQL. Acceptance: malformed input returns structured error, not exception/crash; **adversarial test suite includes**: `../../etc/passwd`, `/etc/passwd`, `foo/../../bar`, 10KB unicode strings, `'; DROP TABLE`, regex metacharacters in `-L` context.

- **Step 1.8: PageRank-ranked JSON projection** (AFK) — Implement Aider-style algorithm: weighted graph from `edges`, PageRank (~50 LOC, pure-Python power iteration, no scipy, damping=0.85), binary-search to fit `--budget` token cap (default 1024). Tie-breakers: file path stability + symbol kind (functions > vars). Write `PROJECT_INTEL.json`. Acceptance: ranking deterministic on fixture; output ≤ budget.

- **Step 1.9: `/codemem` slash command** (AFK) — Markdown file in `claude-code/codemem/commands/codemem.md` defining: `codemem build`, `codemem refresh` (M2), `codemem query <tool> <args>`, `codemem status`, `codemem replay --from-wal` (M2).

- **Step 1.10: MCP server with tool-name aliases** (AFK) — `mcp/server.py` using FastMCP. Read-only SQLite connection (`mode=ro`) per request. Register 12 tool slots; M1 lights up first 6. Aliases (e.g. `dead_code` ↔ `find_dead_code`, `who_calls` ↔ `find_references`) for cross-tool discoverability via Anthropic Tool Search.

- **Step 1.11: Install integration + import-linter + git hook wiring** (HITL) — Update `scripts/install.sh` to symlink `claude-code/codemem/` into `~/.claude/`. **Per V6: install.sh ALSO wires the git post-commit hook** — either (a) writes `.git/hooks/post-commit` (or appends to existing if user has one) with a guarded `[ -x ./claude-code/codemem/hooks/post-commit.sh ] && ./claude-code/codemem/hooks/post-commit.sh` line, OR (b) sets `git config core.hooksPath claude-code/codemem/hooks`. Document trade-off in install.sh comments. Document `pip install -e .` for engine. Add `import-linter` config in CI: enforce `claude-code/codemem/` MUST NOT import from `aa_ma.codemem.{storage,parser,diff,journal}` directly — only via `aa_ma.codemem.mcp_tools`. Acceptance: after `install.sh`, `git commit` triggers `codemem refresh` (verified by post-commit log); import-linter passes; CI fails on boundary violation.

- **Step 1.12: ARCHITECTURE.md** (HITL) — Write `docs/codemem/ARCHITECTURE.md` with 5 mandatory sections: (a) Layering contract + import rules; (b) Dual-WAL semantics (placeholder for M2 details); (c) Symbol ID grammar (link to 1.2b doc); (d) Concurrency model (placeholder for M2 lock); (e) Performance SLOs + measurement (link to perf-slo.md from 1.13). Acceptance: file exists, all 5 sections present.

- **Step 1.13: Performance SLO doc + pytest-benchmark setup** (AFK) — Create `docs/codemem/performance-slo.md` listing the 4 SLOs (build cold/warm wall-clock, refresh wall-clock, who_calls latency, build wall-clock vs /index ratio). Add `tests/perf/test_budgets.py` using `pytest-benchmark`; mark suite as `@pytest.mark.perf`; configure CI to fail when any budget regresses by >10%. Acceptance: perf suite runs in CI; budget fail demonstrably halts pipeline.

**M1 Acceptance Criteria:**
- `codemem build` on aa-ma-forge produces SQLite DB + `PROJECT_INTEL.json` ≤ 5KB
- `codemem build` on `~/.claude-code-project-index/` (~10k LOC Python) completes in < 30s cold cache, < 5s warm cache (enforced by `tests/perf/`)
- **All 6 ported MCP tools produce JSON output JSON-equal to `/index` (modulo key ordering and timestamps) for 3 reference test queries** on aa-ma-forge OR `/index` repo (per V1: pivot anchor target since aa-ma-forge `src/aa_ma/` is empty skeleton at plan time)
- **`who_calls("extract_python_signatures")` on `~/.claude-code-project-index/scripts/index_utils.py`** returns within 100ms (enforced by `tests/perf/`) — verified-existent symbol per audit V1
- `pip install -e .[codemem]` succeeds on Linux + macOS in CI; standalone `pip install codemem-mcp` builds a wheel
- PageRank repo-map fits ≤ 1024 tokens AND covers ≥90% of `/index`'s `_meta.symbol_importance` top symbols
- Schema enforces FKs (verified via `INSERT` on orphaned FK → IntegrityError); integrity check passes on every build; explain-plan on canonical CTE uses indexes only (no table scan)
- import-linter passes; ARCHITECTURE.md committed with 5 sections; perf SLO doc committed
- Adversarial input tests pass (malicious paths `../../etc/passwd`, oversized strings 10KB, non-UTF8 source, regex metachars in `-L` context)
- `.gitignore` contains `.codemem/` line

### Milestone M2: Incremental Cache + WAL Journal (with crash-safe ordering)

**Goal:** Symbol-level diff invalidation + audit-grade WAL journal with crash-safe ordering. Post-commit refresh stays under 2s for typical commits.

- **Step 2.1: Symbol-set diff algorithm** (AFK) — `diff/symbol_diff.py`. Given (old_symbols, new_symbols) for a file: classify into added/removed/modified/renamed via RefactoringMiner-style heuristic (same kind hard filter; signature similarity via Jaccard on tokens; line proximity tiebreak; threshold 0.7 → rename). Conservative: log demoted matches; expose `--no-rename-detection` escape hatch. ~150 LOC + tests including: same name diff signature, similar name same signature, mass refactor.

- **Step 2.2: Incremental indexer driver** (AFK) — On `codemem refresh`: walk dirty files (mtime+size → SHA-256 fallback), parse, diff symbols, apply only deltas to SQLite. Re-resolve cross-file edges only for changed-import files. Handle git history rewrite: if `last_sha` is orphaned (`git cat-file -e <sha>` fails), fall back to full rebuild with warning to `.codemem/refresh.log`.

- **Step 2.3: WAL JSONL journal — crash-safe ordering with explicit replay state diagram** (AFK) — `journal/wal.py`. **Revised contract per Eng E1**: every mutation appends a JSON line to `.codemem/wal.jsonl` BEFORE SQLite write (intent), then SQLite write (atomic txn), then SECOND append `{"ack": true, "id": <wal_id>}` AFTER commit. Atomic append via `O_APPEND`. Schema per entry: `{"id": uuid, "ts": iso, "op": str, "args": dict, "prev_user_version": int, "content_sha": str}`. **Replay state diagram (per V9, also embedded in ARCHITECTURE.md §Dual-WAL-Semantics):**
  ```
  for entry in wal.jsonl (in order):
    if entry.id in acked_ids:                       # SQLite write completed
      continue                                       # skip, already applied
    if compute_current_state(entry.args) == entry.target_state:
      log_warning("idempotent skip", entry.id)      # crash AFTER commit, BEFORE ack write
      append_ack(entry.id)
      continue
    if entry.prev_user_version != current_user_version:
      raise ReplayConflict(entry.id, expected=entry.prev_user_version, got=current_user_version)
    apply_to_sqlite(entry)                           # txn-wrapped
    append_ack(entry.id)                             # mark applied
  ```
  Idempotency key: `(op, prev_user_version, content_sha)`. Two engineers implementing this from the diagram MUST produce identical replay semantics.

- **Step 2.4: WAL replay tool — idempotent** (AFK) — `codemem replay --from-wal` reconstructs SQLite from WAL JSONL using idempotency keys. Round-trip property test in M2 acceptance: `build → snapshot → wipe DB → replay-WAL → assert DB equal (mod last_indexed)`. Use `hypothesis` for random edit sequences.

- **Step 2.5: Post-commit hook with process-group cleanup** (AFK) — `claude-code/codemem/hooks/post-commit.sh` shells out `codemem refresh`. Idempotent, no-op if no new commits. Skips during rebase/cherry-pick. **Per Eng E8**: spawn via `setsid`, write PID to `.codemem/refresh.pid`, kill previous PID if alive before spawning new one (handles rapid `git commit --amend` loops without zombies). Exit 0 always; log errors to `.codemem/refresh.log`.

- **Step 2.6: SQLite WAL hygiene** (AFK) — Periodic `PRAGMA wal_checkpoint(TRUNCATE)` after large indexer batches.

- **Step 2.7: Process-level single-writer lock + Windows-portable file locking** (AFK) — Per Eng E4: cross-platform single-writer lock at indexer entry. **Per V10**: use `fcntl.lockf` on POSIX, `msvcrt.locking` on Windows; abstract behind `_acquire_writer_lock(path)` helper. Lock file: `.codemem/db.lock` (separate from `.codemem/refresh.pid`). Second invocation no-ops with informative log line, does not queue. Read MCP server uses `mode=ro` connection — never touches the lock. Standalone `pip install codemem-mcp` declares `requires-python=">=3.11"` and explicit OS classifiers; if pure-stdlib portable lock cannot be implemented cleanly, add optional `portalocker` dep gated by `[windows]` extra and document Linux+macOS as primary support.

- **Step 2.8: WAL JSONL rotation** (AFK) — Per Eng E8: rotate `wal.jsonl` at 10MB; keep last 3 (`wal.jsonl.1.gz`, `wal.jsonl.2.gz`, `wal.jsonl.3.gz`); compress older; replay tool can read across rotated files.

**M2 Acceptance Criteria:**
- `codemem refresh` after a 10-line edit completes in < 500ms (enforced by `tests/perf/`)
- `codemem refresh` after `git mv` correctly classifies all symbols as moved (not added+removed)
- **Property-based round-trip test passes**: 100 random edit sequences via `hypothesis` produce identical DB after `build → wipe → replay-wal`
- Crash-injection test: kill indexer between WAL append and SQLite commit → next refresh completes correctly without double-applying (idempotency verified)
- WAL JSONL rotation triggers at 10MB; last 3 retained; replay reads across rotation boundary
- Concurrent `codemem refresh` invocations: second is no-op (verified via test that spawns 2 in parallel)
- Post-commit hook test: 5 rapid `git commit --amend` calls in <1s leave only 1 active codemem process
- Git history rewrite test: `git rebase -i` orphans `last_sha` → next refresh falls back to full rebuild with logged warning, no crash

### Milestone M3: Git Intelligence + AA-MA Coupling (the moat)

**Goal:** Ship the 5 git-mining MCP tools that no competitor has as a combo, PLUS the AA-MA-native context tool that nobody else can build.

- **Step 3.1: Git mining base layer with sanitized subprocess** (AFK) — `analysis/git_mining.py`. Subprocess wrappers using `subprocess.run([...], shell=False)` with `--` separator before user input. Wrappers for `git log --since=<date> --name-only --pretty=format:%H|%at|%ae|%s`, `git blame --line-porcelain`. Cache last 500 commits in `commits` table; incremental via `git log <last_sha>..HEAD`. **All file path args validated against repo root** before subprocess invocation.

- **Step 3.2: `hot_spots()` MCP tool** (AFK) — Top-N files by (commits in last 90 days) × (function_count). Returns ranked list with score breakdown.

- **Step 3.3: `co_changes(file)` MCP tool** (AFK) — Files that change in commits with input file but DO NOT have an import-graph edge. Co-occurrence count over last 500 commits. Threshold ≥3 commits to filter noise; exclude global files (CHANGELOG.md, README.md) by default.

- **Step 3.4: `owners(path)` MCP tool** (AFK) — Per-file or per-directory: `git blame --line-porcelain` parsing → author percentages. Cached in `ownership` table; refresh on-demand or `codemem refresh --owners`. Per-file timeout 2s; expose `--no-owners` skip flag.

- **Step 3.5: `symbol_history(name)` MCP tool** (AFK) — `git log -L:symbol_name:file_path`. Returns first-seen, last-touched, change count, authors. If symbol exists in multiple files, returns history per file.

- **Step 3.6: `layers()` MCP tool** (AFK) — In-degree bucketing of `edges` table grouped by file/module. ASCII onion diagram (3 layers: core / middle / periphery).

- **Step 3.7: `aa_ma_context(task_name)` MCP tool — AA-MA-native moat with pinned extraction rule** (AFK) — Per Q12. When called with an active AA-MA task name (validated against `.claude/dev/active/*/`), returns: hot_spots filtered to files mentioned in the task's `*-tasks.md`; owners() of those files; blast_radius() of named symbols in the task's `*-reference.md`. Output: structured Markdown fragment ready to paste into `[task]-reference.md`. Optional auto-write mode (`--write`) appends to reference.md with timestamp. **Extraction rule (per V4 — pinned to prevent divergent implementations):**
  - **File mentions in tasks.md/reference.md**: any backticked path matching regex `\x60([a-zA-Z0-9_\-./]+\.[a-zA-Z0-9]{1,5})\x60` where the file exists relative to repo root. Examples that match: `` `src/aa_ma/codemem/storage/db.py` ``, `` `tests/conftest.py` ``. Examples that do NOT match: bare `src/foo.py` (no backticks), `` `not_a_real_file.py` `` (doesn't exist on disk).
  - **Symbol mentions in reference.md**: any backticked identifier matching `\x60([a-zA-Z_][a-zA-Z0-9_.]{0,63})\x60` that ALSO appears in the SQLite `symbols.name` column for the indexed repo. Filters out arbitrary backticked words like `True`, `None`, common verbs.
  - **Sample fixture committed**: `tests/fixtures/aa_ma_context/sample-task/` with sample-tasks.md + sample-reference.md and the expected extracted set as `expected.json` for golden-file test.
  ~80 LOC + integration test asserting extracted set matches `expected.json` byte-for-byte.

- **Step 3.8: M3 schema additions** (AFK) — Add tables `commits`, `ownership`, `co_change_pairs` to `schema.sql` via `PRAGMA user_version` migration. FKs and cascades per M1 contract.

**M3 Acceptance Criteria:**
- **`hot_spots()` on aa-ma-forge returns ≥3 candidates with score breakdown ≥ baseline floor (≥1 commit in last 90 days × ≥1 function)** — falsifiable replacement for "reasonable" per audit V11
- `co_changes("CLAUDE.md")` returns ≥1 file that has co-occurred in commits ≥3 times with CLAUDE.md AND has no import edge to it (e.g. `claude-code/rules/aa-ma.md` based on git history)
- `owners("src/aa_ma/")` returns email matching `stephen.j.newhouse@gmail.com` with `percentage > 90.0`
- **`symbol_history("extract_python_signatures", file_path="~/.claude-code-project-index/scripts/index_utils.py")`** correctly identifies the introducing commit (verified-existent symbol per audit V1)
- **`layers()` ASCII output ≤ 500 tokens AND fits in 80-column terminal without wrap (golden file `tests/golden/layers_aa_ma_forge.txt`)** — falsifiable replacement for "human-readable"
- `aa_ma_context("codemem")` returns a non-empty Markdown fragment naming ≥1 file from §5 Required Artefacts AND owners+blast-radius for ≥1 symbol from `codemem-reference.md`
- All 6 tools complete in < 1s on aa-ma-forge (enforced by `tests/perf/`)
- Subprocess injection test: `co_changes("$(rm -rf /tmp)")` returns sanitization error, NO shell execution (verified by absence of `/tmp` modification + structured error in MCP response)
- 50k-file synthetic fixture: `hot_spots()` completes in < 5s

### Milestone M4: Polish, Demo, Differentiation

**Goal:** Production-grade install story, benchmarks vs competitors, demo-driven README, migration guide, kill-criteria doc.

- **Step 4.1: Performance benchmarks** (AFK) — Bench script comparing `codemem build`, `codemem refresh`, 3 representative MCP queries against `/index` on three reference repos: aa-ma-forge (small), repowise (medium), a 50k-LOC OSS Python project (large). Document results in `docs/benchmarks/codemem-vs-index.md` with reproducibility notes.

- **Step 4.2: Token-budget benchmarks** (AFK) — Compare `PROJECT_INTEL.json` size vs Aider's repo-map vs jcodemunch-mcp on same 3 repos at `--budget=1024`. Document.

- **Step 4.3: Migration guide from `/index`** (HITL) — `docs/codemem/migration-from-index.md`: side-by-side MCP tool naming, format differences, hook switchover, `codemem import-from-index` command spec (if simpler), FAQ. **Concrete, not hand-wavy** per Eng review.

- **Step 4.4: README + competitor positioning** (HITL) — `claude-code/codemem/README.md` covering: what it is, what's different from GitNexus/Axon/Codegraph/jCodeMunch (git-mining quintet, AA-MA coupling, pure-Python+SQLite, no embeddings), install both modes, quick-start, MCP tool reference. Frame competitors as "different tradeoffs" not "worse." **Run through `/stephen-newhouse-voice` before commit** (per memory rule). MS charity + buy-someone-a-coffee callouts (per personal notes memory).

- **Step 4.5: SECURITY.md update** (HITL) — Document SQLite WAL file growth caveats, `codemem` reads full repo (litellm 2026 supply-chain reference), recommend trusted environments. Document input sanitization contract.

- **Step 4.6: Doc-drift integration** (AFK) — Hook into existing `Skill(doc-drift-detection)` so README/CHANGELOG version refs to codemem stay in sync.

- **Step 4.7: CI integration** (AFK) — Extend `.github/workflows/security.yml` to run `codemem` smoke test (build + 1 query) on PRs touching `src/aa_ma/codemem/`. Also: ast-grep version drift check (warn if installed version exceeds declared range).

- **Step 4.8: 60-second demo + zero-config install snippet** (HITL) — Per CEO C2: record a `co_changes("CLAUDE.md")` demo on a real repo (asciinema or GIF) showing non-obvious coupling surfaced. Author `docs/codemem/install-zero-config.md` with: one-paste Claude Code `settings.json` snippet enabling the MCP server (no manual `/codemem build` step — server auto-builds on first query). Include in README.

- **Step 4.9: ARCHITECTURE.md final pass** (HITL) — Update placeholders from M1 with M2 dual-WAL semantics + concurrency lock details. Lock symbol ID grammar examples per language. Commit final version.

- **Step 4.10: Kill criteria public doc** (HITL) — Per CEO C5: `docs/codemem/kill-criteria.md` with measurable signals (see §12 below). Linked from README "what could make us abandon this" section — honest framing.

**M4 Acceptance Criteria:**
- Benchmark report shows `codemem build` ≤ 1.5× wall-clock of `/index` on each reference repo (enforced by `tests/perf/`)
- `codemem refresh` median time < 800ms on medium repo
- Token-budget benchmark: `PROJECT_INTEL.json` ≤ Aider repo-map size at equal budget AND covers ≥ 90% of same top-ranked symbols
- Migration guide: a `/index` user can switch in < 5 minutes (validated by walkthrough)
- README passes `/stephen-newhouse-voice` review (no marketing-AI tone); MS charity + coffee callout present
- Zero-config install: paste 3-line `settings.json` snippet into Claude Code → first MCP query triggers build → returns answer in < 5s on aa-ma-forge
- Demo asciinema/GIF committed to `docs/demo/`; embedded in README
- CI green; SECURITY.md merged; ARCHITECTURE.md finalized; kill-criteria.md committed

## 5. Required Artefacts (per milestone)

| Milestone | Artefacts |
|---|---|
| M1 | `pyproject.toml` updates (dual-distribution), `src/aa_ma/codemem/**`, `claude-code/codemem/{commands,skills,mcp}/**`, `docs/codemem/{ARCHITECTURE,symbol-id-grammar,performance-slo,design-scratchpad}.md`, `tests/codemem/test_m1_*.py`, `tests/perf/test_budgets.py`, `tests/fixtures/codemem/{sample_repo,adversarial}/**`, `scripts/install.sh` patch, sample `PROJECT_INTEL.json` checked into `examples/codemem/`, `import-linter` CI config |
| M2 | `src/aa_ma/codemem/{diff,journal}/**`, `tests/codemem/test_m2_*.py` (incl. property-based round-trip), `claude-code/codemem/hooks/post-commit.sh`, sample `wal.jsonl` snippet in docs, ARCHITECTURE.md updates |
| M3 | `src/aa_ma/codemem/analysis/git_mining.py`, 6 new MCP tool files (5 git + `aa_ma_context`), schema migration v3, `tests/codemem/test_m3_*.py`, fixture AA-MA task for testing `aa_ma_context` |
| M4 | `docs/benchmarks/codemem-vs-{index,aider}.md`, `docs/codemem/{migration-from-index,install-zero-config,kill-criteria}.md`, `claude-code/codemem/README.md`, `docs/demo/codemem-co-changes.{cast,gif}`, `SECURITY.md` patch, CI workflow patch, ARCHITECTURE.md finalized |

## 6. Tests to Validate per Milestone

- **M1:** Unit tests for parser (Python AST + ast-grep wrapper, mocked subprocess), SQLite schema/migration (incl. FK enforcement + integrity check), PageRank algorithm (deterministic on small graph), each MCP tool (golden-file outputs on fixture repo), input-sanitization tests (path traversal, oversized strings, non-UTF8). Integration test: full build on `tests/fixtures/sample_repo/`. **Adversarial fixtures**: binary file accidentally tracked, 100MB .ts file, symlink loops, non-UTF8 source, submodule boundaries. **Performance budgets enforced via `pytest-benchmark` in CI**.
- **M2:** Symbol-diff unit tests (rename detection edge cases). **Property-based round-trip**: hypothesis-driven random edit sequences. Crash-injection test (kill between WAL + SQLite commit). Concurrent-refresh test (2 parallel invocations → 1 active). Post-commit-amend storm test (5 rapid amends → 1 process). Git history rewrite test (orphaned `last_sha` → graceful fallback). WAL rotation test.
- **M3:** Each git-mining tool tested against fixture repo with known commit history. `co_changes` correctness via fixture with explicit non-import coupling. **Subprocess injection test** for `git_mining.py` (malicious file paths). `aa_ma_context` integration test against fixture AA-MA task. **50k-file synthetic fixture** for scale testing.
- **M4:** Benchmark suite produces reproducible numbers (run 5×, median). CI smoke test < 60s. Migration walkthrough end-to-end. Zero-config install validated on clean machine.

## 7. Rollback Strategy

- **M1:** New code in isolated `src/aa_ma/codemem/` and `claude-code/codemem/`. Rollback = remove dirs + revert `pyproject.toml` + revert `scripts/install.sh` patch. No data loss. Standalone pip package can be yanked from PyPI if published.
- **M2:** WAL JSONL append-only and backward-compatible; rollback to M1 = delete `.codemem/wal.jsonl*` + remove diff/journal modules. Existing SQLite DB still works with M1 code.
- **M3:** New tables additive; rollback = drop new tables + remove 6 MCP tool files. **`PRAGMA user_version` rollback to v1** (M2 introduces NO SQLite schema changes — only file-system journaling and runtime locking; user_version stays at 1 through M2; M3 bumps to v2 by adding `commits`, `ownership`, `co_change_pairs`). Per audit W3 + scribe note: schema version progression is v1 (M1) → v1 unchanged (M2) → v2 (M3).
- **M4:** All M4 deliverables are docs/benchmarks/CI; rollback = revert relevant commits. Demo GIF removable.

## 8. Dependencies & Assumptions

**Hard dependencies:**
- `ast-grep-cli >= 0.42, < 0.43` (Python wheel, ~15-25MB binary, all major OS/arch)
- `fastmcp` (already used by `/index`)
- `pytest-benchmark` (dev dep only) for M1 perf budget enforcement
- `hypothesis` (dev dep only) for M2 property-based tests
- `import-linter` (dev dep only) for M1 layer boundary enforcement
- Python stdlib: `sqlite3`, `ast`, `subprocess`, `pathlib`, `json`, `hashlib`, `re`, `dataclasses`, `fcntl`, `uuid`
- External binary: `git` on PATH

**Explicit non-dependencies (rejected):** networkx, scipy, tree-sitter, lancedb, chromadb, pgvector, alembic, sqlalchemy, anthropic-sdk, gitpython, pydriller, code-maat. Confirmed: ast-grep wheel + fastmcp + stdlib + 3 dev deps = total install footprint.

**Embeddings exit criterion (per CEO C3):** No semantic search in v1. We will reconsider when EITHER (a) `search_symbols` exact-match returns zero results for >20% of agent queries over a 30-day measurement window (requires opt-in telemetry, M5+ feature), OR (b) a competitor demonstrates a clear quality lift on a public benchmark with embeddings + lightweight footprint (e.g. embedded ONNX model under 50MB total) AND that quality lift is reproducible on 3 of our reference repos. Until then, no.

**Distribution model (per CEO C4 / Q13):** Source lives in `aa-ma-forge` repo. Two distribution channels: (1) aa-ma-forge plugin via `scripts/install.sh` (full AA-MA integration); (2) `pip install codemem-mcp` standalone (generic code intel, no AA-MA features active). The `aa_ma_context` MCP tool is a no-op in standalone mode (returns informative message: "AA-MA integration unavailable; install aa-ma-forge").

**Assumptions:**
- Users will run `pip install -e .` once during setup
- `.codemem/` directory is git-ignored (add to user's `.gitignore` template)
- ast-grep's tree-sitter grammars are sufficient for our defs/calls/imports use case
- SQLite WAL mode on WSL2 works for our workload (verified in `/index` already)
- Repo size ≤ 50k files (above this we'd need sharded SQLite or perf rework)

## 9. Effort Estimate & Complexity

| Milestone | Effort (focused-dev days) | Complexity (0-100%) | Notes |
|---|---|---|---|
| M1 | 5-6 days | 70% | Heaviest — schema+SCIP grammar+ast-grep+PageRank+ARCHITECTURE.md+perf SLO infra. Below 80%. |
| M2 | 3-4 days | 75% | Symbol-diff novel; dual-WAL ordering needs care; property-based testing setup. Below 80%. |
| M3 | 3-4 days | 55% | Subprocess plumbing + SQL queries + AA-MA coupling tool + sanitization tests. |
| M4 | 3-4 days | 40% | Benchmarks + demo + dual-distribution packaging finalization. |
| **Total** | **14-18 days** | — | Realistic across 4 calendar weeks. |

No milestone exceeds 80% complexity → no Chain-of-Thought deep reasoning gate required.

## 10. Risks & Mitigations (top 3 per milestone)

### M1 Risks
1. **ast-grep YAML rules don't capture some construct cleanly.** *Mitigation:* Regression suite of fixtures from real-world TS/Python projects; multiple narrow rules per language vs one big rule.
2. **PageRank produces unintuitive rankings on small graphs.** *Mitigation:* Damping=0.85; tie-breakers by file path stability + symbol kind.
3. **SCIP grammar v1 turns out wrong by M3 (e.g. doesn't accommodate Java inner classes).** *Mitigation:* Per-language fixtures in 1.2b acceptance MUST include: Python decorated method, Python class with metaclass, **Java inner class + anonymous class**, TS namespace symbol, Go method on receiver, Rust impl block. If grammar revision needed in M2/M3: ship `codemem migrate-symbol-ids` data-migration utility (rewrites `symbols.scip_id` for all rows); add to rollback strategy §7. Test: round-trip rewrite produces identical edge graph.

### M2 Risks
1. **Rename heuristic produces false positives.** *Mitigation:* Conservative threshold (0.7); log demoted matches; `--no-rename-detection` escape hatch.
2. **Crash between WAL append and SQLite commit causes inconsistency.** *Mitigation:* Eng E1 fix — post-commit ack marker + idempotent replay keys. Crash-injection test in acceptance.
3. **Post-commit hook leaks zombie processes.** *Mitigation:* Eng E8 fix — `setsid` + PID file + kill-previous-before-spawn. Storm test in acceptance.

### M3 Risks
1. **`git blame` on large files is slow.** *Mitigation:* Cache `ownership` table; on-demand refresh; per-file timeout 2s; `--no-owners` skip.
2. **`co_changes` pollutes results with noise.** *Mitigation:* ≥3 commit threshold; exclude global files (CHANGELOG, README) by default.
3. **`aa_ma_context` produces wrong context (wrong files identified for the task).** *Mitigation:* Integration test against fixture AA-MA task with known expected output; manual review on first 3 real uses.

### M4 Risks
1. **Benchmarks show codemem is slower than `/index`.** *Mitigation:* >1.5× cold build → profile + optimize before shipping. Acceptance criterion enforces this.
2. **Demo doesn't produce a "wait, what?" moment on real repos (boring co_changes results).** *Mitigation:* Pre-test on 5 candidate repos; pick the one with the cleanest non-obvious coupling.
3. **Standalone pip distribution breaks in a way the aa-ma-forge install path masks.** *Mitigation:* CI matrix test both install paths on Linux + macOS; smoke test in clean container.

## 11. Next Action

**Immediate next step (after Phase 4.5 verification):**
Execute Phase 5 — create remaining AA-MA artifacts in `.claude/dev/active/codemem/` (5 more files: reference, context-log, tasks/HTP, provenance, verification). Then begin M1 Step 1.0 (pre-flight reading) on this branch.

**AA-MA file to update first:** `codemem-tasks.md` (the HTP roadmap). The 4 milestones decompose into the 15 + 8 + 8 + 10 = **41 tasks** above (M1 includes Step 1.2b symbol-ID grammar as a separate sub-step); each gets a `Status: PENDING`, `Mode: AFK/HITL`, `Acceptance Criteria`, `Result Log:` placeholder.

## 12. Kill Criteria (per CEO C5)

Measurable, time-boxed signals to abandon or pivot:

- **30 days post-ship:** < 25 GitHub stars on aa-ma-forge AND < 5 external installs of `codemem-mcp` → **signal-kill**, fold capabilities back into `/index`.
- **M1 exit:** `codemem build` > 1.5× `/index` wall-clock on reference repos AND PageRank projection doesn't beat Aider's repo-map token efficiency → **architectural kill**, the SQLite-canonical bet isn't paying off.
- **M3 exit:** `co_changes` produces noise > signal on 2/3 test repos (manual eval: <50% of top-5 results meaningful) → **headline-tool kill**, drop to 4 git-mining tools and reposition.
- **Anytime:** GitNexus or Axon ships git-mining in ≥3 of our 5 tools with comparable UX → **moat evaporated**, pivot positioning to AA-MA-coupled differentiator (the `aa_ma_context` tool) immediately.
- **M2 exit:** Crash-injection test cannot be made deterministic → **correctness-risk kill**, drop WAL JSONL feature, ship M1 + M3 only.

These criteria are public (committed in `docs/codemem/kill-criteria.md`) — honest framing per CEO review.

## Plan Review History

- **CEO Review (Phase 4.2a):** Verdict SELECTIVE-EXPAND. Top finding: AA-MA coupling is the real moat (adopted as Step 3.7 + tool #12). Other adopted findings: kill criteria (§12), exit criterion for embeddings (§8), demo + zero-config install (Step 4.8), required pre-flight reading (Step 1.0), dual-distribution (Step 1.1 + §8).
- **Eng Review (Phase 4.2b):** Verdict NEEDS-WORK with 3 CRITICAL + 6 WARNING findings. ALL 9 adopted: dual-WAL ordering fix (Step 2.3), explicit DDL with FKs/indexes/cascades (Step 1.2), SCIP grammar pinned (Step 1.2b), process-level lock (Step 2.7), import-linter CI rule (Step 1.11), test gap closures (M1+M2+M3 acceptance criteria), pytest-benchmark perf enforcement (Step 1.13), input sanitization contract (Step 1.7 + Step 3.1), WAL rotation (Step 2.8), hook process-group cleanup (Step 2.5), ARCHITECTURE.md as M1 deliverable (Step 1.12).
- **Adversarial Verification (Phase 4.5):** PASS WITH WARNINGS. 3 CRITICAL + 4 high-impact WARN findings adopted inline in v3 revision (this version): V1 (anchor symbol pivot to `extract_python_signatures`), V2 (ast-grep 0.42.1 confirmed on PyPI), V3 (/index pagerank reconciled in §2 with sharpened differentiation), V4 (aa_ma_context extraction rule pinned in Step 3.7), V5 (path traversal closed in Step 1.7), V6 (git hook wiring added to Step 1.11), V7 (.gitignore added to Step 1.1), V8 (packaging spike promoted to Step 1.0), V9 (replay state diagram embedded in Step 2.3), V10 (Windows fcntl portability + requires-python in Step 2.7). Falsifiability fixes applied to M3 acceptance criteria (replaced "reasonable", "human-readable" with concrete tests). Schema migration off-by-one fixed in §7. Java inner-class fixture added to M1 risk #3 mitigation. Verification verdict: cleared for Phase 5.
