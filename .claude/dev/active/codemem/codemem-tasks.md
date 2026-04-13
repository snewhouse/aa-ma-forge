# codemem — Tasks (HTP Execution Roadmap)

_Hierarchical Task Planning roadmap with dependencies and state tracking. 40 tasks across 4 milestones. See `codemem-plan.md` §4 for full rationale and acceptance narrative._

---

## Milestone M1: Foundation (shippable as v0.1)
- Status: PENDING
- Gate: SOFT
- Dependencies: None
- Complexity: 70%
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
- Status: PENDING
- Mode: HITL
- Dependencies: None
- Acceptance Criteria: `docs/codemem/design-scratchpad.md` committed capturing 5 readings (Aider repomap.py, `/index` pagerank.py, repowise symbol_diff, GitNexus last 30 days of issues, lessons.md L-052) + chosen packaging structure (one of: hatchling workspace / packages subdir / hatch build hook); packaging decision reflected in Step 1.1; any plan-altering findings flagged in `codemem-context-log.md`.
- Result Log:

### Task 1.1: Project scaffold + dual-distribution packaging
- Status: PENDING
- Mode: AFK
- Dependencies: Task 1.0
- Acceptance Criteria: `pip install -e .[codemem]` works; `pip install codemem-mcp` from a clean checkout produces a working wheel with NO `aa_ma` dependency; entry points `codemem-cli` and `codemem-mcp-server` resolve; `ast-grep-cli>=0.42,<0.43` and `fastmcp` in deps; `cat .gitignore | grep "\.codemem/"` returns a match; CI matrix builds wheel on Linux + macOS.
- Result Log:

### Task 1.2: SQLite schema + DDL (explicit, pinned)
- Status: PENDING
- Mode: AFK
- Dependencies: Task 1.1
- Acceptance Criteria: `schema.sql` created with pinned PRAGMAs (see `codemem-reference.md`), `files` / `symbols` / `edges` tables with FKs + CASCADE, 4 indexes (idx_edges_dst, idx_edges_src, idx_symbols_file_kind_name, idx_symbols_name). Schema validates; FK constraints enforced (insert on orphaned FK raises IntegrityError); explain-plan on the canonical recursive CTE for `who_calls(N=3)` uses indexes only (no table scan). `PRAGMA user_version` = 1. Forward-only migration framework scaffolded.
- Result Log:

### Task 1.2b: SCIP-shaped symbol ID grammar (pinned)
- Status: PENDING
- Mode: AFK
- Dependencies: Task 1.2
- Acceptance Criteria: `docs/codemem/symbol-id-grammar.md` committed with exact format (scheme/package/descriptor/kind-marker). One parser-emitted SCIP-ID per language fixture covering: Python decorated method, Python class with metaclass, Java inner class + anonymous class, TS namespace symbol, Go method on receiver, Rust impl block.
- Result Log:

### Task 1.3: Python parser via stdlib `ast`
- Status: PENDING
- Mode: AFK
- Dependencies: Task 1.2b
- Acceptance Criteria: `extract_python_signatures()` ported from `/index`; returns list of `Symbol` dataclasses with intra-file call edges and canonical SCIP ID per symbol. Unit tests cover function, method, class, nested class, decorated function.
- Result Log:

### Task 1.4: ast-grep parser via subprocess + batching
- Status: PENDING
- Mode: AFK
- Dependencies: Task 1.2b
- Acceptance Criteria: Wrapper invokes `sg run --json=stream` with YAML rule files; batches per language (single sg invocation across N files). Rules cover `function_definition`, `class_definition`, `method_definition`, `import_statement`, `call_expression` for TypeScript, JavaScript, Go, Rust, Java, Ruby, Bash. `languageGlobs` set for `.ts` ↔ `.tsx`. Parsing 100 mixed-language files completes in <10s on aa-ma-forge. Subprocess mocked in unit tests.
- Result Log:

### Task 1.5: File discovery + indexer driver
- Status: PENDING
- Mode: AFK
- Dependencies: Task 1.3, Task 1.4
- Acceptance Criteria: `git ls-files` based discovery respects `.gitignore`; per-language batched parser dispatched in one transaction per language; bulk insert uses `executemany` with `foreign_keys=OFF` toggle + re-enable + integrity check post-insert.
- Result Log:

### Task 1.6: Cross-file edge resolution
- Status: PENDING
- Mode: AFK
- Dependencies: Task 1.5
- Acceptance Criteria: Port 4-strategy import-resolver logic from `/index`; materialize cross-file edges in `edges` table with `dst_unresolved` populated for unresolved targets. Unit tests on fixture with known import graph.
- Result Log:

### Task 1.7: 6 ported MCP tools + input sanitization + canonical CTE
- Status: PENDING
- Mode: AFK
- Dependencies: Task 1.6
- Acceptance Criteria: `who_calls`, `blast_radius`, `dead_code`, `dependency_chain`, `search_symbols`, `file_summary` implemented. All call-graph walks use the canonical recursive CTE (see `codemem-reference.md`). Hard token budget default 8000, configurable. Input sanitization: path args via `Path.resolve(strict=False)` + `is_relative_to(repo_root)`; symbol/file string args via regex `^[A-Za-z0-9_./\-]{1,256}$` + reject `..` substring; rejection before SQL. Adversarial suite passes: `../../etc/passwd`, `/etc/passwd`, `foo/../../bar`, 10KB unicode, `'; DROP TABLE`, regex metachars in `-L` context — all return structured error, no exception/crash.
- Result Log:

### Task 1.8: PageRank-ranked JSON projection
- Status: PENDING
- Mode: AFK
- Dependencies: Task 1.7
- Acceptance Criteria: Aider-style algorithm implemented in ~50 LOC pure-Python power iteration (no scipy), damping=0.85; binary search to fit `--budget` token cap (default 1024); tie-breakers by file path stability + symbol kind (functions > vars); writes `PROJECT_INTEL.json`. Deterministic on fixture; output ≤ budget; ≤ 5KB on aa-ma-forge; covers ≥90% of `/index` `_meta.symbol_importance` top symbols.
- Result Log:

### Task 1.9: `/codemem` slash command
- Status: PENDING
- Mode: AFK
- Dependencies: Task 1.8
- Acceptance Criteria: `claude-code/codemem/commands/codemem.md` committed defining subcommands: `codemem build`, `codemem refresh` (M2 placeholder), `codemem query <tool> <args>`, `codemem status`, `codemem replay --from-wal` (M2 placeholder).
- Result Log:

### Task 1.10: MCP server with tool-name aliases
- Status: PENDING
- Mode: AFK
- Dependencies: Task 1.7
- Acceptance Criteria: `mcp/server.py` uses FastMCP with read-only SQLite connection (`mode=ro`) per request. 12 tool slots registered; M1 lights up first 6. Aliases registered: `dead_code` ↔ `find_dead_code`, `who_calls` ↔ `find_references` (for Anthropic Tool Search discoverability).
- Result Log:

### Task 1.11: Install integration + import-linter + git hook wiring
- Status: PENDING
- Mode: HITL
- Dependencies: Task 1.10
- Acceptance Criteria: `scripts/install.sh` symlinks `claude-code/codemem/` into `~/.claude/`. Post-commit hook wired by install.sh via one of: (a) guarded line appended to `.git/hooks/post-commit`, OR (b) `git config core.hooksPath claude-code/codemem/hooks`; trade-off documented in install.sh comments. After `install.sh`, `git commit` triggers `codemem refresh` (verified by post-commit log line). `import-linter` CI config enforces: `claude-code/codemem/` MUST NOT import from `aa_ma.codemem.{storage,parser,diff,journal}` directly (only via `aa_ma.codemem.mcp_tools`). CI fails on boundary violation.
- Result Log:

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
