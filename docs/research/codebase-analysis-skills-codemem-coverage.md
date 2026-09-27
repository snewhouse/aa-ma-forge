# Which evidence needs of a whole-repo codebase assessment can codemem already answer?

**Created:** 2026-09-27
**Author:** aa-ma-researcher (Claude), for charting effort `codebase-analysis-skills` (map Ticket 2)
**Reviewed-Through-Date:** 2026-09-27 (codemem source at HEAD `d250ee3`; live checks run against a scratch index built from this repo the same day)
**Valid-Through:** 2026-Q4 (goes stale if codemem adds tools, languages or CLI query verbs, or wires `codemem refresh` to `incremental.py`)
**Sources:**
- `packages/codemem-mcp/src/codemem/mcp_tools/__init__.py:1-1330` — every tool's implementation, budget and truncation logic
- `claude-code/codemem/mcp/server.py:41-59,92-291` — the 13 registered MCP tools, the aliases, and auto-build
- `packages/codemem-mcp/src/codemem/cli.py:206-242,339-428` — the CLI surface (`query` exposes only 6 tools)
- `packages/codemem-mcp/src/codemem/indexer.py:36-101,360-493` — file discovery, the extensions it indexes, and full rebuild
- `packages/codemem-mcp/src/codemem/parser/ast_grep.py:33-58,165-187,310-330,351-400` — how non-Python files are parsed, and the hardcoded `sg` binary
- `packages/codemem-mcp/src/codemem/resolver.py:35-52,140-201` — import edges, which resolve for Python only
- `packages/codemem-mcp/src/codemem/draw/cut.py:7-35` — diagram levels L0–L3 and `MAX_EDGES=500`
- `packages/codemem-mcp/src/codemem/analysis/git_mining.py:80-100,107-170,224-240` — commit cache cap and git timeouts
- `packages/codemem-mcp/src/codemem/pagerank.py:34,138-147` — PageRank intel with a tiktoken budget
- `packages/codemem-mcp/src/codemem/storage/db.py:41,91-101` — schema v3; the `co_change_pairs` table
- `packages/codemem-mcp/pyproject.toml:24,31` — `ast-grep-cli` dependency; `codemem` entry point
- `claude-code/codemem/README.md:88,135,170,183,193,196` — documented budget contract, write footprint, scale caveats
- `docs/codemem/performance-slo.md:10-16,40-48` — enforced and unenforced perf budgets
- `tests/perf/test_budgets.py:84,101,121,152` — the only 4 perf tests
- `docs/adr/0014-derived-architecture-views.md:99-104` — the duplicate `edges` rows defect
- https://ast-grep.github.io/guide/quick-start.html — upstream says to use `ast-grep` instead of `sg` on Linux

## Answer
codemem covers 4 of the 14 needs well: call graph, co-change coupling, ownership raw data, and scale on small repos. It covers 5 more only in part: directory structure, layering, import graph, hot spots, and dead code. It gives no answer for 5: cyclomatic complexity, duplication, test coverage, anti-pattern or structural search, and non-Python import or call resolution (so language coverage is weak outside Python). codemem **cannot** replace an `sg` structural-search workflow. It has no ad-hoc pattern tool. The `ast-grep` binary that its dependency installs (`.venv/bin/ast-grep` 0.42.1) can, if you call it by the name `ast-grep`. codemem itself shells out to the bare name `sg`. On this machine a system-only PATH resolves that name to util-linux `newgrp`, and every non-Python file then silently indexes to zero symbols.

## Evidence

### Coverage matrix

| Need | Verdict | Tool / surface | Key evidence |
|---|---|---|---|
| Directory structure | **partial** | `diagram` / `codemem draw` L0 (depth-1 dirs), L1 (depth-2), L2 (files) | `draw/cut.py:7-13`. There is no tree or LOC tool. Only source files are indexed (`indexer.py:39-42`). Live: 208 of 659 tracked files indexed. The 334 `.md`, 31 `.bats` and all yml/json files are invisible. |
| Architectural layering | **partial** | `layers()` = tertiles of *call in-degree* (core/middle/periphery). `draw` gives a directory graph with `@import`/`@call` edges. `codemem intel` gives PageRank. | `mcp_tools/__init__.py:926-992`, `pagerank.py:150-205`. This measures centrality, not declared-layer conformance. There is no layer-rule or violation check. |
| Call graph | **covered (Python)** | `who_calls`, `blast_radius` (BFS CTE, `max_depth=3`), `dependency_chain` (shortest call path, `max_depth=5`), `diagram` L3 | `mcp_tools/__init__.py:160-203,210-253,307-357`. Misses dict and dynamic dispatch. Live: `dependency_chain main build_index` returned `null`, though `cli.py:419-428` dispatches `_cmd_build → build_index`. |
| Import / dependency graph | **partial** | `file_edges` table (kind `import`), exposed only through `draw`/`diagram --kind import` | `resolver.py:140-201`. `build_import_map` skips non-`.py` paths (`resolver.py:35-52`). `dependency_chain` walks **call** edges only (`e.kind = 'call'`, `mcp_tools/__init__.py:288-304`). No query tool returns an import list. Live: 933 import rows, all from Python, 255 resolved to repo files. |
| Hot spots (churn × complexity) | **partial** | `hot_spots(window_days=90, top_n=10)`: score = commits in window × **function count** | `mcp_tools/__init__.py:442-501`. Function count stands in for complexity. There is no test-path filter. Needs `codemem refresh-commits` first (`cli.py:100-174`). Live top-5 has 4 test files (e.g. `tests/test_gate.py` 7×52 = 364). |
| Ownership / bus factor | **covered (raw) / partial (bus factor)** | `owners(path, refresh=False)` on a file or a `dir/` prefix | `mcp_tools/__init__.py:613-707`. It reads a blame cache that is **empty until `refresh=True`** (then a 2 s per-file `git blame`, `git_mining.py:224-240`). The CLI has no `owners` verb. No bus-factor number is computed, but it can be derived from the author percentages. Live: cache miss gave `authors: []`. Refreshing `packages/codemem-mcp/src/codemem/` took 0.7 s and gave 1 author at 100%. |
| Co-change coupling | **covered (per file)** | `co_changes(file_path, threshold=3, top_n=50)` drops pairs already linked by an edge, to surface *implicit* coupling | `mcp_tools/__init__.py:508-606`. Works for any path, `.md` included, because `commit_files` records every path. There is no whole-repo pair ranking: `co_change_pairs` is created (`storage/db.py:91-101`) but nothing writes it (grep found no writer). Live: `execute-aa-ma-milestone.md` co-changes with `hooks/lib/aa-ma-parse.sh` (10 commits). |
| Dead code | **partial (noisy)** | `dead_code()` = function/method with zero incoming `call` edges | `mcp_tools/__init__.py:260-281`. There is no entry-point, test or dispatch awareness. Live: 1356 flagged, 1256 of them under `tests/`. `_cmd_build` is flagged (dispatched via dict). All 51 Bash functions are flagged, because Bash emits no resolved call edges. |
| Cyclomatic complexity | **missing** | — | `symbols` holds only `line`, `signature` and `signature_hash`, with no end line or body metrics (schema read live, `indexer.py:220-262`). |
| Duplication | **missing** | — | `signature_hash` hashes the signature, not the body (`indexer.py:232-243`). No clone detection. |
| Test coverage | **missing** | — | No coverage-file ingestion anywhere in `src/codemem/`. The only proxy is `who_calls` from `tests/` symbols. |
| Anti-pattern / structural search | **missing** | — | ast-grep runs only at index time with fixed rule files (`parser/ast_grep.py:1-12,165-187`, `parser/rules/*.yml`). `search_symbols` is a SQL `LIKE` on names (`mcp_tools/__init__.py:364-396`). |
| Language coverage | **partial** | Python via stdlib `ast`: symbols, signatures, calls, imports. TS/TSX/JS/Go/Rust/Java/Ruby/Bash via ast-grep: symbols plus *unresolved* calls only | `parser/ast_grep.py:36-45,310-330`. Cross-file resolution is Python-only (`resolver.py:35-52`). Live: bash 25 files / 55 symbols / 0 call edges; JS 26 call edges, 0 resolved; Python 5052 call rows, 2009 resolved. |
| Scale limits | **covered for small repos; unproven above ~10k LOC** | — | Live cold build on this repo: 0.48 s, 208 files, 2089 symbols, 5078 edges. Enforced SLOs cover only a ~10k-LOC repo (`performance-slo.md:10-16`, `tests/perf/test_budgets.py:84-152`). The 50k-file `hot_spots` SLO has no test (`performance-slo.md:46`; no match in `tests/perf/`). README says medium and large benchmarks are "pending" (`README.md:183`). |

### Response shapes and budget / truncation behaviour
- **Default budget.** 8000 "tokens" = `len(json.dumps(payload)) / 4` chars, a heuristic rather than a tokenizer (`mcp_tools/__init__.py:54-58,124-129`). The exception is `PROJECT_INTEL.json`, which uses tiktoken `cl100k_base` at a default 1024 (`pagerank.py:34,138-147`).
- **List tools** (`who_calls`, `blast_radius`, `dead_code`, `dependency_chain`, `search_symbols`, `file_summary`, `hot_spots`, `co_changes`, `owners`, `symbol_history`) use `_truncate`, which binary-searches the longest list prefix that fits and always sets `truncated: bool` (`mcp_tools/__init__.py:1305-1330`). Every row is `{scip_id, name, kind, file, line}`; `file_summary` adds `signature` (`:146-153,429-433`). Live: `who_calls build_index --budget 400` returned 7 callers with `"truncated": true`.
- **`layers` and `aa_ma_context` only *flag* over-budget output; they do not trim it** (`mcp_tools/__init__.py:986-992,1201-1203`). Live: `layers(budget=100)` returned 10,124 JSON chars with `truncated: True`. Only its ASCII art is hard-capped at 2000 chars (`:922-923,1040-1042`).
- **`diagram`** first collapses to a coarser level while that level still has edges, then truncates to a sorted edge prefix. It returns `{mermaid, level, nodes, edges, dropped, collapsed_from, truncated, error}` (`mcp_tools/__init__.py:1055-1115`). Mermaid is also hard-capped at `MAX_EDGES=500` (`draw/cut.py:31`). Live: L3 at budget 2000 collapsed to L1 (3 nodes / 3 edges).
- **Errors** come back as `{"error": ...}` dicts, never exceptions. Arguments pass an allow-list regex first (`README.md:90`, `mcp_tools/sanitizers.py`).
- **CLI vs MCP.** `codemem query` exposes only 6 tools (`cli.py:376-383`). `hot_spots`, `co_changes`, `owners`, `symbol_history`, `layers`, `aa_ma_context` and `diagram` need the MCP server (`server.py:41-59`) or a Python import (`from codemem import mcp_tools`). `codemem draw` is the CLI route to the diagram cut (`cli.py:265-313`).
- **Counts are inflated.** `edges` rows are stored twice; readers must use `DISTINCT` (`docs/adr/0014-derived-architecture-views.md:99-104`).

### Preconditions and side effects (checked before running anything)
- `codemem build` writes only `<db parent>/index.db` and `<db parent>/last_sha`; the CLI passes no WAL (`indexer.py:375,381,478-479`; `cli.py:36-49`). All live checks used `--db <scratchpad>/cm/index.db`, and `git status --porcelain` was identical before and after.
- The git-mining tools return empty until `codemem refresh-commits` runs. Its default cap is 500 newest commits (`cli.py:359-367`, `git_mining.py:107-170`). Live, with `--limit 5000`, it inserted 731 commits.
- `owners(refresh=True)` and `aa_ma_context(write=True)` are writers (`mcp_tools/__init__.py:656-657,1187-1188`).
- The CLI `refresh` is still an M1 placeholder that only logs (`cli.py:80-97`). The README says it is an "incremental refresh since last SHA" (`README.md:193`).

### Can codemem, or `ast-grep` by that name, replace an `sg` structural-search workflow?
- **codemem: no.** It has no pattern-query surface (see the matrix row above).
- **`ast-grep` binary: yes.** `ast-grep-cli>=0.42,<0.43` is a hard dependency (`pyproject.toml:24`) and installs both `.venv/bin/ast-grep` and `.venv/bin/sg` (both ELF, `ast-grep 0.42.1`, verified live). `uv run ast-grep run -p 'subprocess.run($$$ARGS)' -l python packages/codemem-mcp/src --json=stream` returned 7 matches, each with keys `charCount, file, language, lines, metaVariables, range, text`. Upstream: "Linux has a default command `sg` for `setgroups`. You can use the full command name `ast-grep` instead of `sg`." (https://ast-grep.github.io/guide/quick-start.html).
- **What `sg` resolves to on this machine.** `which -a sg ast-grep` gives `~/miniforge3/envs/bio312_07_25/bin/sg` (ast-grep 0.42.1, first on the interactive PATH), then `/usr/bin/sg`, then `/bin/sg`. `ast-grep` resolves only in that conda env and the repo venv; it is not on a system PATH.
- **`/usr/bin/sg` is not shadow-utils.** It is a symlink to `newgrp`, owned by `util-linux-extra` (checked with `dpkg -S`). Its `--help` prints `sg <group> [[-c] <command>]`.
- **codemem's own hazard.** `extract_with_ast_grep(..., sg_bin="sg")` (`parser/ast_grep.py:356`) runs `[sg_bin, "scan", ...]`. It discards stderr and treats empty stdout as "no matches" (`:165-187`). Live probe on a 2-function `.sh` file: under `uv run` (venv first on PATH) it found `['foo', 'bar']`. Under `env -i PATH=/usr/bin:/bin .venv/bin/python` it resolved `/usr/bin/sg` and returned `[]`, with exit 0 and no warning. The documented MCP launch uses `uv run python` (`README.md` quick start, `.mcp.json`), which masks this. Any launch without the venv on PATH (cron, a bare `.venv/bin/codemem`, a system-PATH hook) silently loses every non-Python language.

## Not pursued
- Whether `claude-code/codemem/hooks/post-commit.sh` calls `incremental.py` directly or the placeholder `codemem refresh`: this affects index freshness, not the capabilities in scope.
- `symbol_history` accuracy: live `build_index` showed `change_count: 1` although the function has clearly been edited since. The `git log -L:<name>:<file>` funcname matching was not investigated.
- `draw/plugin_surface.py` (markdown `Skill()` reference extraction): it could partly cover this markdown-heavy repo's "code", but it is a separate diagram feature, not an assessment tool.
- Throughput on medium or large repos: no external reference repo was cloned or benchmarked.
- `aa_ma_context` live run: skipped because it needs an active AA-MA task directory, and its write mode mutates `reference.md`.
- Import-linter layering contract for codemem's own packages (`docs/codemem/ARCHITECTURE.md`): this is a rule codemem obeys, not a tool it exposes.
- Context7 lookups for ast-grep: not needed. The upstream quick-start page was enough for the `sg` naming claim.
