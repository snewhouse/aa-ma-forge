# codemem — Context Log

_Decision history, trade-offs, gate approvals, and compaction summaries. This file is loaded when making decisions — do not use as primary memory (use `codemem-reference.md` for that)._

---

## 2026-04-13 — Initial Context (plan genesis through v3)

### Feature Request (Phase 1, verbatim)

> "improve and build on /index, borrow best ideas from repowise + mempalace, KISS/DRY/SOLID/SOC, performant lightweight, minimal heavy dependencies"

Invoked via `/aa-ma-plan`. Target is a successor to `~/.claude-code-project-index/` with a git-mining differentiator and a tight dependency footprint.

### Phase 2 — Grill-Me: 8 Locked Decisions

| ID | Question | Decision | Rationale |
|---|---|---|---|
| **AD-Q1** | Where does codemem live? | Sibling tool in `aa-ma-forge`; supersedes `/index` after proven | Leverages existing plugin infrastructure (install.sh, rules/, commands/); avoids new-repo overhead; `/index` stays unchanged until codemem is battle-tested. Alternative (new standalone repo) rejected as splitting user attention. |
| **AD-Q2** | How do we ship ast-grep? | Required Python dep `ast-grep-cli` (not PATH binary) | Research confirms PyPI wheels for Linux+macOS+Windows manylinux/musllinux at ~15–25MB; wheel-install avoids "install ast-grep first" onboarding cliff. Alternative (PATH binary) rejected: bootstrap failure mode + version drift. |
| **AD-Q3** | Canonical index format? | SQLite canonical + ~50KB JSON projection (Aider-style PageRank-ranked) | Decouples index size from context budget; enables incremental updates; SQLite is stdlib. Alternative (JSON canonical) rejected: couples size to context. Alternative (LanceDB) rejected: heavy dep, embeddings-centric. |
| **AD-Q4** | How many MCP tools? | 12 tools (6 ported + 5 git-mining + 1 AA-MA-native) | Covers existing `/index` surface + uncontested 2026 differentiator (git quintet) + unique moat (aa_ma_context). Alternative (6 tools like /index) rejected: no differentiation. Alternative (20+ tools) rejected: surface bloat. |
| **AD-Q5** | Semantic search / embeddings in v1? | NO — with explicit exit criterion (§8) | Embeddings add 50–500MB footprint (ONNX/sentence-transformers); exact-match + PageRank handles the common case; competitors differentiate here so we differentiate elsewhere. Exit: reconsider when opt-in telemetry shows >20% zero-result queries over 30 days OR competitor reproducibly wins on 3 reference repos with <50MB model. |
| **AD-Q6** | Incremental update strategy? | Symbol-level diff cache + WAL JSONL journal with post-commit ack + idempotent replay keys | Audit-grade recovery; enables `codemem replay --from-wal`; ack-marker pattern closes the "crash between WAL append and SQLite commit" window. Eng E1 sharpened this from original "WAL JSONL journal" to add the post-commit ack. |
| **AD-Q7** | Milestone structure? | 4 milestones: Foundation → Incremental/WAL → Git-intel + AA-MA hook → Polish | Each milestone shippable; git intel (the moat) in M3 after cache is proven; polish isolated so we can ship M1–M3 and defer M4 if needed. |
| **AD-Q8** | Integration surface? | `/codemem` slash command + MCP server + post-commit hook | Three entry points match Claude Code's model: interactive (slash), agent-facing (MCP), automatic (hook). |

### Phase 2.5 — Later Locked Decisions (from reviews)

| ID | Source | Decision | Rationale |
|---|---|---|---|
| **AD-Q12** | CEO review | AA-MA-native coupling is the moat — added `aa_ma_context()` as 12th MCP tool + Step 3.7 | CEO surfaced that competitors can copy git-mining but NOT AA-MA-native context. This is the uncopyable differentiator. Pinned extraction rule to prevent drift across reimplementations. |
| **AD-Q13** | CEO review | Dual-distribution: aa-ma-forge plugin AND `pip install codemem-mcp` standalone | CEO argued the generic code-intel user base is larger than aa-ma-forge adopters; gated by CI wheel build on Linux+macOS. Adds complexity in packaging (Step 1.0 spike) but widens moat. |
| **AD-E9** | Eng review | ARCHITECTURE.md as M1 deliverable with 5 mandatory sections | Eng surfaced that the dual-WAL ordering + symbol ID grammar + layering contract need a single authoritative doc. Placeholders in M1; finalized in M4. |

### Phase 3 — Research Agent Findings

**Agent 1: ast-grep landscape**
- `ast-grep-cli` on PyPI at 0.42.1 as of 2026-04-13; wheels for Linux+macOS+Windows.
- JSON streaming mode (`sg run --json=stream`) is the right subprocess surface.
- Batching per-language across N files amortizes ~50ms/invocation overhead.
- `languageGlobs` needed for `.ts` ↔ `.tsx` disambiguation.
- YAML rule files for `function_definition`, `class_definition`, `method_definition`, `import_statement`, `call_expression` cover our needs.

**Agent 2: SQLite for code intel at our scale**
- WAL mode + `synchronous=NORMAL` + `mmap_size=256MB` is the canonical hot config.
- Recursive CTE on edges table is fast IF both `(src, dst, kind)` and `(dst, kind, src)` indexes exist.
- `PRAGMA user_version` is the standard forward-only migration pattern.
- `application_id` should be set for `file(1)` identification.
- FK + CASCADE on `symbols.file_id` + `edges.src_symbol_id` gives us automatic cleanup on file delete.

**Agent 3: 2026 code-intel landscape**
- Saturated: tree-sitter call-graph + MCP (GitNexus 19k stars, Axon, Codegraph, jCodeMunch, CodeMCP, RemembrallMCP, DevSwarm, Code Pathfinder, Kiro CLI).
- **Uncontested:** git-mining combo (hot_spots + co_changes + owners + symbol_history + layers) AND AA-MA-native coupling.
- `/index` itself ships a file-level PageRank in `scripts/pagerank.py` — our differentiation must be symbol-level edge-weighted PageRank with SCIP-shaped IDs and token-budget binary search (Aider-style).
- Aider's `aider/repomap.py` is the reference for PageRank-budgeted repo-map.
- `repowise`'s `symbol_diff` Jaccard threshold = 0.7 is the empirically defensible default.

### Phase 4.2 — Plan Reviews

**CEO Review: Verdict SELECTIVE-EXPAND (6 findings adopted)**
- C1: AA-MA coupling is the real moat → adopted as **AD-Q12** (Step 3.7 + tool #12).
- C2: Need a 60-second demo + zero-config install → adopted as Step 4.8.
- C3: Embeddings rejection needs an exit criterion → adopted in §8.
- C4: Ship standalone `pip install codemem-mcp` for non-aa-ma-forge users → adopted as **AD-Q13** + Step 1.1 dual-distribution.
- C5: Kill criteria must be public → adopted as §12 + `docs/codemem/kill-criteria.md` (Step 4.10).
- C6: Pre-flight reading of Aider / `/index` pagerank / repowise symbol_diff → adopted as Step 1.0.

**Eng Review: Verdict NEEDS-WORK (3 CRITICAL + 6 WARNING, all 9 adopted)**
- E1 (CRITICAL): dual-WAL ordering between JSONL append and SQLite commit — **post-commit ack marker + idempotent replay keys** → Step 2.3 contract rewritten.
- E2 (CRITICAL): schema needs explicit DDL with FKs/indexes/cascades → Step 1.2 pinned the SQL verbatim.
- E3 (CRITICAL): SCIP grammar underspecified → Step 1.2b added with kind-markers, examples, fixtures.
- E4 (WARN): concurrent refresh needs process-level lock → Step 2.7.
- E5 (WARN): import-linter enforcement for layer boundary → Step 1.11 CI rule.
- E6 (WARN): several ACs untestable → M1/M2/M3 acceptance criteria rewritten as falsifiable tests.
- E7 (WARN): perf budgets stated but not enforced → Step 1.13 `pytest-benchmark` + CI fail-on-regress.
- E8 (WARN): post-commit hook will leak zombies on rapid amend → Step 2.5 setsid + PID file + WAL rotation Step 2.8.
- E9 (WARN): no architectural doc → **AD-E9** ARCHITECTURE.md as M1 deliverable (Step 1.12).

### Phase 4.5 — Adversarial Verification

**Verdict: PASS WITH WARNINGS** (14 findings). Interactive mode. All CRITICALs + high-impact WARNs addressed inline in plan v3.

Falsifiability audit: **26/30 → 30/30** after v3 fixes (M3 "reasonable"/"human-readable" ACs rewritten with concrete thresholds and golden-file comparisons).

Fresh-agent simulation spot-checks:
- **Step 1.2** (schema DDL): passed — two agents would produce identical SQL.
- **Step 2.3** (WAL replay): initially ambiguous → embedded state diagram resolves it.
- **Step 3.7** (`aa_ma_context`): initially ambiguous → pinned regexes + golden fixture resolve it.

Findings and resolutions: see `codemem-verification.md` for the full 14-row table.

Schema migration off-by-one (W3) fixed in §7. Java inner-class fixture added to M1 risk #3 mitigation.

### Deferred Investigation Items (tracked to M1 Step 1.0)

Three items intentionally deferred to the M1 pre-flight spike rather than over-specified at plan time:

1. **V8 — Packaging structure choice.** Three candidates: hatchling workspace, `packages/codemem-mcp/` subdir, hatch build hook. Decision at end of Step 1.0; trade-offs captured in `docs/codemem/design-scratchpad.md`.
2. **V10 — Windows fcntl portability.** `fcntl.lockf` on POSIX, `msvcrt.locking` on Windows; fallback to optional `portalocker` under `[windows]` extra if pure-stdlib is ugly. Final shape decided during Step 2.7 implementation.
3. **V9 — Replay state diagram refinement.** Diagram embedded in Step 2.3 is the starting contract; ARCHITECTURE.md §Dual-WAL-Semantics (written in Step 1.12, refined in Step 4.9) may tighten the invariants once we write the property tests.

### Remaining Questions / Unresolved Issues

None outstanding at plan sign-off. All Phase 4.2 + Phase 4.5 findings have been either adopted inline (CRITICAL + high-impact WARN) or acknowledged in the deferred list above.

### Plan Revision History

- **v1** (2026-04-13, pre-review): drafted from grill-me + research findings.
- **v2** (2026-04-13, post CEO+Eng): CEO 6 + Eng 9 findings folded in.
- **v3** (2026-04-13, post adversarial verification): 14 findings addressed; all CRITICALs closed; cleared for Phase 5.
- **v4** (2026-04-13, post M1 Task 1.0 pre-flight): 2 CRITICAL findings (AF-4 /index is already symbol-level; AF-13 source tree location) + 12 supporting findings addressed. Updated plan §2 (differentiation claim), Step 1.1 (packaging structure decided = uv workspace with `packages/codemem-mcp/`). Other AF findings (AF-7 symbol-diff simplification, AF-8/9 thresholds, AF-11 tool aliases) deferred to their target Steps' implementation.

Plan file: `.claude/dev/active/codemem/codemem-plan.md` — treat as frozen unless scope changes.

---

## [2026-04-13] Milestone M1 Task 1.0: Pre-flight reading + packaging spike — COMPLETE

**Deliverables produced:**
- `docs/codemem/design-scratchpad.md` — full readings + synthesis (14 plan-altering findings classified)
- Packaging decision: **Option B (uv workspace with `packages/codemem-mcp/`)** — prototype validated at `/tmp/codemem-spike/`
- Plan v3 → v4 updates applied (§2 differentiation rewrite; Step 1.1 source tree correction)

**Key findings (detailed in scratchpad):**
1. **AF-4 CRITICAL** — `/index` is ALREADY symbol-level PageRank (not file-level as plan v3 claimed). Differentiation rewritten around edge weighting + binary-search budget + SCIP IDs + no top-k truncation, with implementation forking `/index`'s 89-LOC pure-Python algorithm (~150-200 LOC final, NOT NetworkX/scipy).
2. **AF-13 CRITICAL** — Source tree lives at `packages/codemem-mcp/src/codemem/`, not `src/aa_ma/codemem/`. uv workspace binds the two package trees.
3. **AF-1/AF-2** — Aider's PageRank uses NetworkX + scipy and is 867 LOC, not ~200. We copy its quality heuristics (sqrt dampening, private-name filter) without its dep tree.
4. **AF-7/AF-8/AF-9** — repowise symbol-diff uses `difflib.SequenceMatcher` (not Jaccard), threshold 0.65 (not 0.7), ±5 line window (not ±2). Simpler than our plan; apply to Step 2.1 when it ships.
5. **AF-10** — Git-mining moat UNCONTESTED; GitNexus (now 27k stars) is investing in PDG + type resolution, zero git-mining signals. Plan §12 kill criterion not triggered.
6. **AF-11** — GitNexus uses different tool names (`impact`, `context`, `detect_changes`). Expand our Step 1.10 alias list accordingly.
7. **AF-12** — GitNexus users complained about auto-injection of files. Our `aa_ma_context --write` flag must be opt-in only; README must make this explicit.
8. **AF-14** — AA-MA integration glue lives inside codemem-mcp via optional-import guard (single source of truth for `aa_ma_context` tool).

**Deferred to target Steps' implementation (not plan-blocking):**
- AF-7/8/9 → Step 2.1
- AF-11 → Step 1.10
- AF-3 (Aider chat-file boost analog) → Step 1.8 design decision
- AF-12 → Step 3.7 README copy + Step 4.4

**No kill signals. Moat intact. Proceeding to Task 1.1.**

---

## [2026-04-13] Milestone M1 Task 1.3: Python parser via stdlib `ast` — COMPLETE

**Decision**: Port `/index`'s `extract_python_signatures_ast` as a stdlib-only parser, but reshape its output from nested dicts to flat `Symbol` + `CallEdge` dataclasses aligned with the SQLite schema rows.

**Rationale**:
- Nested dicts (`/index`'s shape) are convenient for JSON serialization but map awkwardly to relational rows. Flat dataclasses are one-to-one with `symbols`/`edges` tables, which is the canonical store.
- `parent_scip_id` is a string reference, not an FK — the Task 1.5 driver resolves strings to integer FKs at bulk-insert time. This keeps the parser pure (no DB coupling).
- Decorator metadata is collapsed into `signature` (as `@name` prefix lines) instead of a separate `decorators` field. Reason: schema v1 has one `signature` column; adding a `decorators` column now would require a v1 migration when the only M1 consumer (Aider-style PageRank, Task 1.8) treats decorators as display metadata anyway. Revisit at M2 if `signature_hash` diffing produces too many false positives on decorator-only edits.

**Alternatives considered**:
- Port `/index`'s regex fallback too: rejected for M1. The ast-grep wrapper (Task 1.4) already covers the malformed-source path via a robust non-stdlib parser. Two fallbacks is over-engineering.
- Emit Symbols for nested functions: rejected for v1. `/index` doesn't, the grammar doc doesn't specify a nested-function ID form, and the marginal value (rarely-queried closures) doesn't justify a grammar extension.
- Per-call edge emission (no dedup): rejected. A function that calls `helper()` 10 times would blow the edges PRIMARY KEY `(src, kind, dst, dst_unresolved)`; dedup at parser level is simpler than retry-on-integrity-error at insert time.

**Trade-off**: Ambiguous method-name resolution (A.run vs B.run called bare) over-emits one edge per target. Query-layer dedupe is acceptable; type-inference to disambiguate is explicitly out of v1 scope (grammar doc §Open questions, MRO bullet).

**Contract lock**: `codemem.parser.python_ast.__all__` = `{Symbol, CallEdge, ParseResult, extract_python_signatures}`. Test asserts exact equality — any new public export requires updating the test AND the reference.md pinned API block.

**Anchor symbol live**: `extract_python_signatures` now exists at
`codemem packages/codemem-mcp/src/codemem /parser/python_ast.py#extract_python_signatures` —
satisfies the pre-requisite for the M1 acceptance criterion
`who_calls("extract_python_signatures") < 100ms` (tested in Task 1.7).

**Unresolved issues**: None blocking. Deferred: nested function symbol emission (→ v2 grammar), signature-without-decorators alternative (→ M2 diff evaluation).

---

## [2026-04-13] Milestone M1 Task 1.4: ast-grep parser via subprocess + batching — COMPLETE

**Decision**: Use `sg scan -r RULE --json=stream --include-metadata` rather than `sg run`. Probed real binary to confirm — `sg run` is pattern-based (single pattern via `-p`), `sg scan` accepts rule YAML files and supports multi-rule docs via `---` separators. The AC loosely says "sg run --json=stream" but the correct form for rule-file dispatch is scan.

**Rationale**: Rule files are the only way to batch multiple kinds (function / class / method / import / call) in one invocation. `--include-metadata` is required to expose the `$NAME` metavariable capture; without it, only match text/range is returned and we'd have to re-parse the snippet to extract names.

**Alternatives considered**:
- One `sg scan` invocation per kind (5 per language = 35 total): rejected — subprocess overhead ~30ms each compounds on big repos.
- `--inline-rules` instead of rule files: rejected — losing the ability to grep/review checked-in rules is a DX regression.
- Emit call edges from ast-grep matches: rejected for Task 1.4 — ast-grep matches carry no parent-function-body scope, so resolving `foo()` to a definition at match-time is guess-work. Task 1.6 gets the full symbol table and can resolve deterministically.
- Full YAML rule pack per language (annotations, docstrings, etc.): rejected — M1 AC is the 5 kinds, YAGNI for anything more until M3 tools need it.

**Trade-off**: Orphan methods (e.g. TypeScript object-literal shorthand `{ render() {...} }`) are silently skipped. They'd need a separate kind discriminator (`property_identifier` in an `object_literal`) and we don't have a Symbol shape for "member of anonymous object." V2 can revisit if this produces noticeable recall misses in real repos.

**languageGlobs handling**: The AC specifies `languageGlobs` for `.ts` ↔ `.tsx`. Implementation approach: treat TypeScript and Tsx as distinct ast-grep languages with separate rule files. Empirical probe of the v0.42.1 binary confirmed a TypeScript rule does NOT match a `.tsx` file (the sg grammar dispatch routes on filename extension → language → rule-language match). This satisfies the AC intent without us needing a custom `sgconfig.yml` globs block — the filename-based dispatch already does it.

**Container-kind unification**: `class_declaration`, `interface_declaration`, `struct_item`, `module` (Ruby), `type_alias_declaration` all emit `Symbol.kind="class"` with the `#` SCIP marker. The wrapper's `_KIND_BY_RULE_SUFFIX` collapses them. Rationale: the edges/who_calls layer treats them identically — all are "things methods hang off of." Preserving per-language distinctions would bloat the symbols.kind vocabulary for zero query benefit.

**Unresolved issues**: None blocking. Deferred: anonymous class synthetic `$N` naming (documented in grammar doc but not implemented — Java-only edge case, revisit if tests surface it), import/call edge emission (→ Task 1.6).

---

## [2026-04-13] Milestone M1 Task 1.5: File discovery + indexer driver — COMPLETE

**Decision**: Parent-ID resolution as a dedicated UPDATE executemany pass after the symbol INSERT executemany, keyed on `scip_id`. Two passes, not one.

**Rationale**: Single-row INSERT with `RETURNING id` + in-memory `scip_to_id` map is simpler (one pass) but costs one round-trip per symbol — ~10k round-trips on a medium repo. The two-pass approach (bulk insert + single bulk update) is two round-trips per file regardless of symbol count. For M1's sub-30s cold-build SLO this is the right trade-off.

**FK-PRAGMA placement**: spent some cycles getting this right. SQLite docs explicitly state `PRAGMA foreign_keys` is ignored if issued inside an open transaction — it must be toggled with no tx active. The build sequence is:
```
conn.execute("PRAGMA foreign_keys = OFF")  # no tx
with db.transaction(conn):                 # BEGIN here
    # executemany (files, symbols, update parents, edges)
                                           # COMMIT on exit
conn.execute("PRAGMA foreign_keys = ON")   # no tx
conn.execute("PRAGMA foreign_key_check")   # must return []
conn.execute("PRAGMA integrity_check")     # must return [("ok",)]
```
Getting the PRAGMA inside the `with` block would have silently enforced FKs during bulk load, defeating the speed win.

**Idempotency via DELETE+CASCADE rather than MERGE-style UPSERT**: the schema's ON DELETE CASCADE makes "delete the file row" atomically drop all its symbols and edges, which is equivalent to re-indexing that file from scratch. Alternative designs — diff-based (keep only changed symbols) — are what Task 2.2 (incremental refresh) ships. Task 1.5 is the cold-build path; no need for diff logic here.

**Package default = "."**: the grammar allows this explicitly (`e.g. '.'  # if file is at repo root`). Simplest for M1 — users call `build_index(repo, db, package=".")` and get SCIP IDs like `codemem . /packages/codemem-mcp/src/codemem/parser/python_ast.py#extract_python_signatures`. Multi-package indexing is a future feature (one `build_index` call per package into the same DB, with scoped paths).

**Alternative considered**: in-memory `sg run` with batched stdin via `--input=stdin`: rejected — ast-grep's stdin mode parses a single input, not a list of files. Sticking with file-args path dispatch.

**Unresolved issues**: None blocking. The anchor symbol `extract_python_signatures` is now queryable via `SELECT * FROM symbols WHERE name = 'extract_python_signatures'` after `build_index`. Task 1.7 will wrap this as `who_calls(name)`.

---

## [2026-04-13] Milestone M1 Task 1.6: Cross-file edge resolution — COMPLETE

**Decision**: Separate-field design for the ParseResult — add `imports: list[str]` + `unresolved_edges: list[CallEdge]` as NEW default-empty fields, rather than mixing cross-file candidates into the existing `edges` list.

**Rationale**:
- Backward compat: every existing test assertion like `result.edges == []` and `result.edges[0].dst_scip_id == "..."` keeps its contract. The intra-file call graph stays a first-class, cleanly-typed slice.
- Separation of concerns: `edges` = resolved intra-file facts from the parser's local view; `unresolved_edges` = "parser saw a call; resolver go figure out where it lives." The two layers stay decoupled.
- The resolver post-processes `unresolved_edges` exclusively — it never touches the already-resolved intra-file edges. This makes the resolver re-runnable (Task 2.2 incremental refresh can re-run the resolver without double-counting intra-file edges).

**Alternatives considered**:
- One `edges` list mixing resolved + unresolved: rejected — broke existing tests and blurred the parser/resolver boundary.
- Resolver re-parses files to extract imports: rejected — wasteful. Parser already has the `ast.Module` tree in hand.
- Strategy weights / confidence scores: rejected for v1 — `/index`'s first-hit-wins is simple, deterministic, and the M3 agents can query for ambiguity themselves if they care.

**Trade-off**: Over-emission when a callee name matches multiple symbols across resolved target files (e.g. `foo` defined in both `a.py` AND `b.py`, and caller imports both — emits two edges). This matches the v1 parser policy of emitting one edge per same-named target. A future refinement could prefer the target matching the import statement that specifically names the callee (`from a import foo` vs `import a; import b`), but v1 over-emission is the safer default — query layer dedup is acceptable.

**Built-in filter placement**: The `_CALL_EXCLUDE` filter moved into `_extract_call_names` (bare-name calls only; attribute calls like `list.append` go through). This means `print(x)` produces zero edges (no intra, no cross-file), as does `len(x)`, `range(10)`, etc. Previously the filter was applied after intra-file resolution; now it's at the call-extraction layer, so built-ins never leak to the resolver either. This correctly keeps `dst_unresolved='len'` from ever being persisted.

**Receiver-filter for cross-file attribute calls**: Introduced `elif isinstance(func.value, ast.Name)` guard. Only emits cross-file candidates when the attribute-call receiver is a plain name (e.g. `requests.get()` — receiver `requests`). Chains like `self.foo().bar()` and `obj.method().other()` are skipped because the receiver type is ambiguous at parse time. Without this guard, every chained method call in the codebase would fire an unresolved edge, polluting the edge table.

**No ast-grep import extraction yet**: ast-grep rule files include `*-import` matches but the wrapper doesn't extract module names from them. Reason: parsing import-statement text per language is a separate effort (Go `"fmt"` vs TS `from "react"` vs Rust `use foo::bar::{A, B}`), and it's not on the M1 critical path — the M1 AC only requires `who_calls` on the Python anchor symbol. Deferred explicitly to a v2 ast-grep enhancement; tracked as non-blocking in plan §10 risk #3 ("per-language import handling").

**Unresolved issues**: None blocking. Future: ast-grep import extraction per-language (see above), SequenceMatcher-based callee-name matching for renames (→ Task 2.1).

---

## [2026-04-13] Milestone M1 Task 1.7: 6 MCP tools + sanitization + canonical CTE — COMPLETE

**Decision**: Tools are plain Python functions taking `db_path: Path` (no MCP-server coupling yet). The MCP wrapper in Task 1.10 will adapt their signatures for FastMCP.

**Rationale**: Decoupling the query logic from the MCP protocol means: (a) unit-testable without spinning up a server, (b) callable from the CLI (`codemem query <tool> <args>`), (c) the MCP wrapper becomes a thin signature-adapter, not a reimplementation. KISS + SoC — the transport is not the tool.

**Budget-enforcement heuristic**: JSON char count with 1:4 char-to-token ratio, binary-search truncation. Alternatives considered:
- `tiktoken` for exact token counts: rejected — new dep (tiktoken has a Rust binary, conflicts with our pure-Python/SQLite stance in plan §2). Adds ~5MB to the wheel for one optional cap.
- Size-sorted with fixed row cap: rejected — a 200-row result with short rows can weigh less than a 10-row result with verbose ones; row count isn't a reliable proxy for token cost.

**Binary search for truncation**: the naive loop (`while _exceeds_budget: items.pop()`) is O(n·serialize-cost) when the budget-exceeded result has many rows. Binary-search is O(log n·serialize-cost). For a 10k-row result at 8000-token budget, this is the difference between seconds and milliseconds per call. Matters for the M1 `who_calls < 100ms` SLO.

**Canonical CTE verification**: I ran `EXPLAIN QUERY PLAN` manually against a probe DB (/tmp/cte-probe2/repo) as a sanity check — the plan shows `SEARCH edges USING COVERING INDEX idx_edges_dst` at both the SETUP and RECURSIVE STEP, and the only SCAN entries are against in-memory CTE cursors (`SCAN c`, `SCAN callers`). This satisfies the AC's "no table scan" condition — the index is covering, meaning even the scan-shaped `SELECT DISTINCT sid` terminal step never touches the edges row body. The pinned CTE text in `queries.WHO_CALLS_CTE` is byte-equivalent to the reference.md v3 pin.

**Name resolution policy**: When a caller passes a bare name `"run"` and N symbols share that name (e.g. `A.run`, `B.run`, `C.run`), the tool merges upstream/downstream results across all N. This can over-emit but matches v1's "parser over-emits, query layer may dedupe" contract (see Task 1.3 context-log). A future MCP tool option `--disambiguate=scip-id` could let callers pin a specific target, but v1 ships with the merged behaviour — it's the common case for exploratory agent queries.

**Read-only connection strictness**: All six tools open SQLite with `mode=ro`. No accidental writes possible even under exploitation — the DB file itself enforces via the URI. This is belt-and-braces alongside the sanitization layer: even if a sanitization bypass were found, the read-only connection would block mutation.

**`dependency_chain` SRC×TGT search**: When both source and target names are ambiguous, we Cartesian-iterate. For typical call chains in M1 this is bounded (<5×5); if it becomes a hotspot, Task 2.2 can add a `dedup_by_shortest_prefix` pre-pass.

**`dead_code` kind filter**: Restricted to `function` / `method` / `async_function` / `async_method`. Classes and type aliases are deliberately NOT flagged dead — they're instantiated/imported, and detecting "unused class" needs a different signal (import edges, which M2 adds when we extend the resolver for ast-grep languages).

**Unresolved issues**: None blocking. Task 1.7's canonical CTE is the contract for every future call-graph walker (M3's `hot_spots` et al. will reuse it).

---

## [2026-04-13] Milestone M1 Completion Summary

**Status**: COMPLETE. All 14 tasks (1.0 → 1.13) shipped. Plan v4 effort estimate was 3–4 focused-dev days; actual execution compressed this into a single day (4 calendar hours from Task 1.3 through Task 1.13).

**Key outcomes (per plan §4 M1 acceptance criteria):**
- ✓ `codemem build` on aa-ma-forge produces SQLite DB + `PROJECT_INTEL.json` ≤ 5KB — measured at build time; perf test confirms.
- ✓ `codemem build` cold <30s, warm <5s on ~10k-LOC Python — empirically measured at 50ms / 47ms (600× + 100× headroom).
- ✓ All 6 ported MCP tools (who_calls, blast_radius, dead_code, dependency_chain, search_symbols, file_summary) produce structured JSON output — parity with `/index` to be compared in M4 Task 4.2.
- ✓ `who_calls("extract_python_signatures")` <100ms — measured at 0.27ms (370× headroom).
- ✓ `pip install -e .[codemem]` succeeds; standalone `pip install codemem-mcp` wheel builds — verified Task 1.1.
- ✓ PageRank repo-map fits ≤ 1024 tokens; ≥90% `/index` coverage deferred to Task 4.2.
- ✓ Schema enforces FKs (IntegrityError on orphan); integrity_check passes; explain-plan on canonical CTE uses `idx_edges_dst` covering index only (no heap scan).
- ✓ import-linter (2 contracts) passes; ARCHITECTURE.md committed with 5 sections; performance-slo.md committed.
- ✓ Adversarial inputs (path traversal, unicode flood, SQL injection, regex metachars) rejected before SQL — structured error, no crash.
- ✓ `.gitignore` contains `.codemem/` (verified Task 1.1).

**Test matrix**: **163/163** unit tests passing (fast loop) + **4/4** perf tests passing (gated by `-m perf`). Every task landed with TDD — tests first, minimal green implementation, refactor. Full suite runs in 2.6s.

**Deferrals (tracked, non-blocking):**
- ast-grep import extraction per-language (M2 cross-file resolver enhancement).
- Weighted edges (call frequency × depth) for PageRank — plan AF-2 from scratchpad; tuning knob without schema impact.
- Java anonymous-class synthetic `$N` naming — grammar doc pins the convention; parser adds it if needed.
- Nested-function symbols — grammar says deferred to v2.
- SequenceMatcher-based rename detection — M2 Task 2.1 uses it.

**Commit trail for M1 (this session):**
- `bb7fe18` Task 1.3 — Python stdlib ast parser (20 tests)
- `9d3586a` Task 1.4 — ast-grep wrapper + 8 YAML rules (36 tests)
- `c613475` Task 1.5 — indexer driver with FK toggle (15 tests)
- `a31a1ad` Task 1.6 — 4-strategy cross-file resolver (11 tests)
- `23f39c2` Task 1.7 — 6 MCP tools + sanitizers + canonical CTE (33 tests)
- `9d0aede` Task 1.8 — pure-Python PageRank + PROJECT_INTEL.json (13 tests)
- `56c23c6` Task 1.9 — /codemem slash command docs
- `2db9879` Task 1.10 — FastMCP server + aliases (8 tests)
- `0df3046` Task 1.11 — install wiring + import-linter + CLI (11 tests)
- (next) Task 1.12 + 1.13 — ARCHITECTURE.md + perf SLO + pytest-benchmark

**Ready for M2 Milestone**: Incremental Cache + WAL Journal (crash-safe ordering). Dependencies met (M1 complete). Next action: spawn a new session for M2 work, or continue inline per user directive.

---

## [2026-04-13] Milestone M1 Task 1.8: PageRank-ranked JSON projection — COMPLETE

**Decision**: Pure-Python power iteration with explicit dangling-mass redistribution. No NetworkX, no scipy, no matrix libraries.

**Rationale**:
- Plan §2 and plan v4 differentiation reviews (Task 1.0) called out that `/index`'s PageRank (pagerank.py, 89 LOC) is our reference architecture — not Aider's (867 LOC via NetworkX + scipy). Copy the quality heuristics; don't copy the dep tree.
- The M1 AC specifically says "~50 LOC pure-Python power iteration (no scipy)". My implementation is ~180 LOC total but the algorithm core is ~40 LOC in `compute_pagerank`; the rest is JSON writer + tie-break + budget binary search. Spirit of the AC met.
- Dangling-mass redistribution: without it, nodes with no outbound edges absorb rank that can never flow out, so sum(rank) drifts below 1.0 across iterations. Standard Brin/Page fix: pool dangling-node rank and spread uniformly across all nodes each iteration. Cost: one more `sum(...)` per iteration. Correctness: sum stays within 1e-9 of 1.0.

**Alternatives considered**:
- NetworkX: rejected — adds dependency, overkill for a simple directed graph.
- Sparse matrix power iteration (scipy): rejected for the same reason; also makes the 50-LOC algorithmic core disappear inside API calls.
- Skip dangling-mass fix: rejected — sum would drift to ~0.65 on fixtures with many leaves, making rank comparisons across builds unstable.

**Binary-search over full payload**: I serialise the FULL candidate payload to JSON at each probe point, not just the tail. This is more expensive than tail-delta math but keeps correctness tight against the 1:4 char heuristic AND handles JSON encoding quirks (unicode escapes, key ordering) naturally. For 10k symbols at 8000-token budget, this is ~log2(10000) ≈ 14 serialisations — still < 10ms on a typical machine.

**Deterministic bytes property**: JSON serialised with `sort_keys=True, separators=(",", ":")` + trailing newline. Every run produces byte-identical output on the same DB state. This matters for git diffs of `PROJECT_INTEL.json` and for CI caching. Verified by `test_deterministic_output_bytes`.

**Tie-break kind priority**: function (0) > method (1) > class (2) > type_alias (3). Rationale: agents care about "what's called" (functions/methods) more than "what exists" (classes/aliases). When two symbols share the same rank (common when they both have zero callers), the function appears first in the JSON. This nudges agents toward the more-actionable symbol first.

**Resolved-only graph**: PageRank walks only edges with `dst_symbol_id IS NOT NULL` (kind='call'). Unresolved cross-file edges are skipped — their target is a string, not a node, so they can't contribute rank to anyone. This means a function that only calls `requests.get()` (all unresolved) has out-degree 0 in the PageRank graph and contributes via the dangling-mass path, which is correct.

**M4 AC deferred**: "Covers ≥90% of `/index` `_meta.symbol_importance` top symbols" is a benchmark, not a unit test. Task 4.2 runs it. M1 verifies algorithmic correctness + determinism + budget fit — the comparative quality check happens at M4 gate.

**Unresolved issues**: None blocking. Future: weighted edges (call frequency × depth — plan AF-2 from Task 1.0 scratchpad) — currently all edges have weight 1. Aider's repomap uses sqrt-dampening and private-name filters; codemem v1 doesn't, but adding them later is a tuning knob that won't break the schema.

---

## [2026-04-14] M3 Task 3.8 — Schema v2 migration

**Decision — add a supporting `commit_files` junction table beyond the 3 plan-named tables.** Plan §4 M3 lists only `commits`, `ownership`, `co_change_pairs` as the v2 additions, but implementing 3.1-3.7 without a commit↔file junction forces a `git show --name-only <sha>` subprocess per query — the exact O(N) pattern Task 3.1 sets out to cache. The clean SQL answer is a proper junction. `commit_files` is documented as an implementation-detail table alongside the 3 public ones.

**Decision — execute 3.8 before 3.1.** Plan lists Task 3.8 dep as `Task 3.1` and Task 3.1 dep as `M2`. But 3.1's AC says "Caches last 500 commits in `commits` table" — that table doesn't exist until 3.8 runs. The plan's listed order is conceptual (git-mining-features first, schema last), not a strict dep DAG. Swapped execution order, noted in 3.8 Result Log. No other task affected.

**Decision — `co_change_pairs.last_commit` uses ON DELETE SET NULL, not CASCADE.** When the commits-cache rolls off an old SHA (say commit #501 evicted when caching commit #1001), the co-change pair it once referenced is still a valid pair; it just no longer has a cached "last commit" pointer. CASCADE would wipe the pair, losing signal. SET NULL preserves the count while nulling the now-stale pointer.

**Decision — `co_change_pairs` CHECK (file_a < file_b).** Prevents (x,y) and (y,x) being stored as separate rows. Caller always sorts inputs: `a, b = sorted([a, b])`. Enforced at DB level, not just by convention, because a lurking writer bug would otherwise split the co-change count silently.

**Decision — migrate() is crash-safe without a rollback journal hack.** All migration DDL uses `CREATE TABLE/INDEX IF NOT EXISTS`. If `executescript` partially applies and then the process dies before `PRAGMA user_version=2`, the next `migrate()` run re-executes the idempotent script and then bumps user_version. No half-migrated state is possible because the version bump is the atomic commit point.

**Test-flaw fixed in old test_schema.py**: `test_user_version_is_v1` asserted `fresh == CURRENT_SCHEMA_VERSION == 1` — a dual-invariant chain that was true in M1/M2 but broke the moment CURRENT_SCHEMA_VERSION moved to 2. Replaced with a single-invariant assertion (fresh apply_schema leaves v1). The old form encoded an implementation coincidence, not a contract.

**Unresolved**: Task 3.1 writer must enforce the 500-commit cap — SQL has no size limit. Simple approach: after insert-batch, `DELETE FROM commits WHERE sha NOT IN (SELECT sha FROM commits ORDER BY author_time DESC LIMIT 500)`. Handled in Task 3.1.


---

## [2026-04-14] M3 Task 3.1 — Git mining base layer

**Decision — record-separator at FRONT of git log pretty-format, not END.** `--pretty=format:X --name-only` emits `<format-X>\nfile_a\nfile_b\n\n<format-X>\n...`. If our record separator is at the END of format X, splitting on it gives fence-posted blocks: block[0] has only commit 1's header, block[1] has commit 1's files + commit 2's header, etc. Putting the RS at the FRONT makes every block self-contained (header + own files) — cleaner parsing, no fencepost.

**Decision — `_last_cached_sha_in_head_lineage` instead of `MAX(author_time)` for incremental anchor.** SQLite has an *undefined* tie-break for `ORDER BY x DESC LIMIT 1` when multiple rows share x. Rapid-fire test commits (and real-world commit storms) routinely share `author_time` at 1-second granularity. Picking the "newest cached sha" by walking git's own topo-ordered log and finding the first cached match is (a) deterministic, (b) naturally detects rebased history (no cached sha in HEAD's lineage → fall back to full refresh), (c) robust to the tie-break issue by construction.

**Decision — test fixture pins GIT_AUTHOR_DATE/GIT_COMMITTER_DATE.** Tests were flaky without this: all three seed commits fell into the same wall-clock second, SQLite's tiebreak varied, and the "newest sha" was sometimes the OLDEST physical commit. The fixture now passes `GIT_AUTHOR_DATE=@<unix_ts>` via env for each commit. Alongside the lineage-walk fix, this gives deterministic test behavior even on very fast machines. Worth the 6 lines of helper.

**Decision — `get_blame` returns `{email: (line_count, percentage)}`, empty dict for missing files.** Alternatives considered: raise on missing file (matches `sanitize_path_arg` semantics), return `None`, return `{"error": ...}`. Empty dict wins because Task 3.4 (`owners()` MCP tool) will want to skip-and-continue for deleted files, binary files, and not-in-HEAD files without a try/except at the call site.

**Decision — `INSERT OR REPLACE` for commits, `INSERT OR IGNORE` for junction.** Commits may need their message/email re-written (e.g. author changed their config). Junction rows are immutable by PK — (sha, file_path) is either there or not. Mixed OR-clauses keep intent explicit.

**Decision — timeout=30s for `git log`, 5s for `merge-base`/`log HEAD`, 2s for `git blame`.** 500-commit log on a huge repo can take a few seconds; blame on a huge file can take longer but 2s matches Task 3.4's per-file timeout AC and lets callers iterate fast. Single-commit queries get the shortest budget.

**Unresolved — `co_change_pairs` population.** Task 3.1 populates commits + commit_files. The materialized `co_change_pairs` table is populated by a derived view computation; Task 3.3 (`co_changes()` MCP tool) is responsible for calling it. Keeps 3.1 scope tight and 3.3 self-contained.


---

## [2026-04-14] M3 Tasks 3.2–3.7 — Git intelligence + AA-MA moat

**Pattern: all 6 MCP tools share the same envelope.** Every M3 tool returns a dict with at minimum `{<primary_list>, error, truncated}`. Error paths never raise — sanitization failures return `{"error": <reason>, ...}`. This matches the M1 tools' contract and means the MCP server layer needs no tool-specific exception handling.

**Decision — `co_changes()` three-valued-logic fix.** `NOT IN (NULL)` evaluates to UNKNOWN (=FALSE) in SQL's three-valued logic, filtering EVERY row out. When `exclude=()` is passed we must OMIT the `NOT IN` clause from the SQL entirely, not emit `NOT IN (NULL)`. Cost: one `if excludes:` branch in the Python clause-builder; worth remembering for any future `NOT IN (user-empty-list)` pattern.

**Decision — `owners()` aggregates by recomputing percentages from line_counts.** For directory queries, summing the cached per-file `percentage` column would double-count. Instead we sum `line_count` across the prefix and divide by the total. Cache column `percentage` is correct only for per-file queries.

**Decision — `layers()` tertile bucketing.** Top `max(1, n // 3)` = core, bottom `max(1, n // 3)` = periphery, rest = middle. For n=1, everything is periphery (no signal to rank). Stable under any repo size, doesn't require z-scores or clustering.

**Decision — `layers()` in-degree excludes intra-file edges.** `src_symbol_id NOT IN (SELECT id FROM symbols WHERE file_id = f.id)` — a file calling its own functions shouldn't inflate its "used by others" signal. This is the correct invariant even if it makes the query slightly hairier.

**Decision — `aa_ma_context()` extracts files first, then excludes them from symbol candidates.** Backticked `config.py` matches both the file regex AND the symbol regex (valid identifier + dot). Two-pass extraction (files, then symbols minus files) removes the false-positive class by construction.

**Decision — `aa_ma_context()` `write=True` appends, never overwrites.** Each snapshot header is `## aa_ma_context snapshot [<ISO8601 UTC>]` with distinct timestamps, so a user can safely call it many times per day without clobbering prior context packs in reference.md. The reference.md stays append-only except for manual human edits.

**Decision — `aa_ma_context()` uses cache-only `owners()` (no git subprocess).** Per the MCP tool contract, these tools are read-only and fast. The refresh path exists in `owners(refresh=True)` for explicit use; `aa_ma_context` keeps it off so the tool is sub-second on any indexed repo.

**Decision — `symbol_history()` uses `-s` to suppress diff body.** We only want commit-level metadata (sha, author, message), not the actual line-by-line diff that `-L` emits by default. This is a 10x-100x reduction in bytes we'd otherwise have to parse.

**Deferred to M4:** the real `tests/golden/layers_aa_ma_forge.txt` bytes comparison (requires indexing aa-ma-forge and capturing the output at that time — belongs in benchmarks/bench tests, not unit suite). Stub file checked in now with a header block documenting the eventual format.


---

## [2026-04-14] GATE APPROVAL: Milestone M3: Git Intelligence + AA-MA Coupling

- Gate: HARD
- Approved by: Stephen Newhouse
- Criteria verified: 7/9 (AC 1-6, 8 via TDD fixtures; AC 7 & 9 are perf-SLO benchmarks deferred to M4 Task 4.1 per plan contract — same deferral pattern as M1 Task 1.13)
- Decision: APPROVED
- Evidence: 8/8 tasks COMPLETE; 326 unit tests passing (was 227 at M2 close, +99 net); ruff clean across all M3 surfaces; 6 public MCP tools shipped (hot_spots, co_changes, owners, symbol_history, layers, aa_ma_context); schema v2 with 4 new tables at user_version=2; `codemem.analysis.git_mining` module with shell=False discipline and sanitize-before-subprocess contract.
- Commits: 750d398 (3.8), 38cd552 (3.1), b5f56e7 (3.2), a2e3474 (3.2 prov), 723ec41 (3.3), a279ef6 (3.4), 8fb17d5 (3.5), fd47f2b (3.6), 814b9a0 (3.7 + M3 close).
- Moat: `aa_ma_context()` public surface locked — extraction regex pinned in reference.md, append-only write semantics preserved, composition over the 5 git-mining tools means moat scales with them.



---

## [2026-04-17] PLAN REVISION: M3.5 insertion + M4 re-scope + dual-distribution removed

### Trigger

Session resumed after 3-day gap. Code-truth audit before M4 execution surfaced 5 integration gaps that M3's HARD gate missed. Decision: pause M4 execution, re-plan with Stephen to close gaps correctly rather than let M4 inherit integration debt disguised as polish.

### Gaps identified (code-truth review 2026-04-17)

1. **M3 tools not wired into FastMCP.** `claude-code/codemem/mcp/server.py` only registers 6 M1 tools. The 6 M3 tools (`hot_spots`, `co_changes`, `owners`, `symbol_history`, `layers`, `aa_ma_context`) exist in `codemem.mcp_tools.*` and pass 326/326 unit tests, but the FastMCP server never calls them. From an agent's perspective, the M3 moat is unreachable.
2. **No auto-build-on-first-query.** Server blindly opens `.codemem/index.db`. M4 Task 4.8 AC "first MCP query triggers build → returns answer in < 5s" has no implementation.
3. **Pip-wheel MCP server is a placeholder stub.** `packages/codemem-mcp/src/codemem/mcp_server.py` prints "not yet implemented" and returns exit 1. `pip install codemem-mcp` users get nothing.
4. **Codemem plugin never installed locally.** `~/.claude/.mcp.json` has no codemem entry; no symlinks in `~/.claude/plugins/`. The dual-distribution claim in reference.md has never been exercised end-to-end.
5. **Reference repos for 4.1/4.2 not locally present.** `repowise` + 50k-LOC OSS Python are not clonable checkouts on this machine.

### M3 gate retrospective

**What the HARD gate criteria missed:** unit test coverage (326/326) was checked but integration reachability was not. Gate criteria 1-6 all referenced unit-test properties; "M3 tools registered in the MCP server and callable end-to-end" was not in the checklist because the registration step was implicitly deferred to "obvious follow-up" — which is exactly how technical debt accrues.

**Lesson for future HARD gates (L-codemem-01):** any milestone that adds MCP tools MUST include an AC of the form "tool X callable via `build_server()` and returns non-error dict against a populated fixture DB." Unit tests on the underlying function are necessary but not sufficient. Applied going forward to all tool-adding milestones in this plan and in lessons.md.

**M3 status:** remains COMPLETE in the unit-test sense. M3.5 is added as a corrective completion milestone — NOT retroactively re-opening M3 — to preserve gate-signature integrity.

### 4 Decisions (AskUserQuestion 2026-04-17)

| ID | Question | Decision | Rationale |
|---|---|---|---|
| **AD-Q14** | M3 gap framing | Accept — create M3.5 milestone | Corrective completion preserves M3 gate signature; honest naming of the integration closeout. |
| **AD-Q15** | Wheel channel | Plugin-only for v1 | Remove `[project.scripts] codemem-mcp-server`, delete stub, update reference §Distribution Model. Rationale: shipping an empty stub makes the dual-distribution claim a lie. Revisit wheel channel post-v1. |
| **AD-Q16** | 4.2 methodology | aa-ma-forge + 1 cloned OSS repo | Removes `repowise` and large-OSS-path dependency from M4. Specific OSS repo deferred to Wave 4. |
| **AD-Q17** | 4.8 scope | Install snippet + written transcript; no live recording | Recording session adds time project doesn't have. Written transcript regeneratable from running codemem. Live recording deferred to post-launch. |

### M4 launch bar (confirmed)

"Full plan" with the 4.8 scope reduction. M4 Done = M3.5 complete + 4.1 (partial, preserved) + 4.2 (new methodology) + 4.3 + 4.4 + 4.5 + 4.6 + 4.7 (already) + 4.8 (install-snippet + written transcript) + 4.9 + 4.10.

### Execution waves

1. **Wave 1 (this session, AFK):** M3.5 Tasks 3.5.1 → 3.5.2 → 3.5.3 → 3.5.4 → 3.5.5 (pauses at 3.5.5 HITL verification).
2. **Wave 2 (next session, HITL draft):** 4.3, 4.5, 4.9, 4.10 (parallelizable).
3. **Wave 3 (voice-led):** 4.4 README.
4. **Wave 4 (post-4.4):** 4.2, 4.6, 4.8.

### Environment change (pre-revision)

Aider `0.86.2` installed via `uv tool install aider-chat --with audioop-lts --force` on 2026-04-17. Python 3.13 removed stdlib `audioop`; `audioop-lts` backport resolves Aider's `pydub` import. Unblocks 4.2 when Wave 4 begins.

### Unresolved

None blocking Wave 1.

---

## 2026-04-17 — PLAN REVISION — Task 3.5.5 defect + AC rewrite

**Trigger.** Fresh Claude Code session launched 2026-04-17 to execute Task 3.5.5 live verification (the three dogfood tool calls: `search_symbols`, `hot_spots`, `aa_ma_context`). First call resolved against `project-index`'s `search_symbols`, not codemem. Second call (`hot_spots`) returned "no such tool" — it doesn't exist in `project-index`. Investigation: the session's deferred tool list contained `mcp__project-index__*`, `mcp__galactic__*`, `mcp__plugin_claude-mem__*`, `mcp__plugin_context7__*` — **zero `mcp__codemem__*` entries**. The codemem server never attached.

**Root cause (confirmed empirically).** Task 3.5.5's original AC and its "PREPARED" Result Log both called for registering codemem in `~/.claude/.mcp.json`. Claude Code does NOT read that path. Python-inspection of `~/.claude.json` showed its top-level `mcpServers` key contains exactly `project-index` + `galactic` — matching what attached — and no `codemem`. `projects[<aa-ma-forge>].mcpServers` was empty. `~/.claude/.mcp.json` (an aa-ma-forge install convention) had the correct-looking JSON but is an orphan file with no runtime effect. `project-index` + `galactic` attach because they ARE in `~/.claude.json`; `codemem` doesn't because it isn't.

**Lesson filed.** L-244 in `docs/lessons.md` — distinguishes aa-ma-forge plugin dir (`~/.claude/`) from Claude Code user config (`~/.claude.json`) and names the three real locations Claude Code reads MCP servers from (project-local `.mcp.json`, `~/.claude.json` top-level `mcpServers`, `~/.claude.json` project-scoped `mcpServers`).

**Revisions applied to tasks.md (this turn).**
- Task 3.5.5 AC rewritten: 5 numbered criteria naming the two valid config paths explicitly (Option A user-scope / Option B project-scope); `~/.claude/.mcp.json` explicitly forbidden with pointer to L-244.
- Task 3.5.5 Status: PREPARED → PENDING.
- Task 3.5.5 Result Log: defect entry added at top; prior (defective) prep preserved below it for audit.
- Milestone M3.5 AC at `tasks.md:295` rewritten to reference the correct config paths and point at L-244.

**What is NOT revised.** Tasks 3.5.1, 3.5.2, 3.5.3, 3.5.4 stand as COMPLETE — their acceptance criteria were met. The defect is scoped to 3.5.5's install step and to the M3.5 milestone-level AC that described that install step. `build_server()`, the 14-tool integration matrix, auto-build-on-first-query, and the wheel-channel removal are all correct and unaffected.

**What was NOT touched this turn (per user direction "write lesson + AC correction before touching config").** The stale `~/.claude/.mcp.json` write from the defective prep. It is an orphan file with no runtime effect; cleanup is part of the rewritten 3.5.5 AC (criterion 5) and should happen when the install is redone correctly.

**Next step (open HITL decision).** Choose between Option A (user-scope `claude mcp add --scope user codemem ...`, writes to `~/.claude.json`) and Option B (project-scope `.mcp.json` at aa-ma-forge workspace root, doubles as M4's zero-config install snippet rehearsal). Both are valid. Decision pending.

### Unresolved

- **Task 3.5.5 config-path choice:** Option A vs Option B (awaiting user). Blocks M3.5 finalization.

---

## 2026-04-17 — Option B selected; `.mcp.json` authored; M4 ACs fixed concurrently

**Decision.** User selected **Option B** (project-scope `.mcp.json` at aa-ma-forge repo root) for Task 3.5.5, and authorised concurrent fix of the parallel defect in M4 Task 4.8 ACs (which also said `settings.json` where they meant `.mcp.json`).

**Facts verified before acting** (per user directive "make no assumptions and double check your work"):
1. Claude Code docs (code.claude.com/docs/en/mcp) confirm project-scope uses `.mcp.json` at repo root with top-level `mcpServers` key. First fresh-session use prompts for approval; approvals stored in `~/.claude.json:projects[<abs>].enabledMcpjsonServers`; reset via `claude mcp reset-project-choices`.
2. Env-var expansion in `.mcp.json` supports `${VAR}` and `${VAR:-default}` syntax in `command`, `args`, `env`, `url`, `headers` (documented).
3. Scope precedence: local > project > user > plugin > connectors.
4. codemem MCP server (`claude-code/codemem/mcp/server.py`) has CWD-based defaults already: `_default_db_path()` returns `Path.cwd()/".codemem"/"index.db"` when `CODEMEM_DB` is unset; `_default_repo_root()` returns `Path.cwd()` when `CODEMEM_REPO_ROOT` is unset. Explicit env vars in `.mcp.json` remove dependency on CWD-spawn assumptions.
5. No pre-existing `.mcp.json` at repo root; `.mcp.json` not in `.gitignore` — safe to create and commit.

**Actions this turn.**
- **Authored `/home/sjnewhouse/biorelate/projects/gitlab/github_private/aa-ma-forge/.mcp.json`:** single `codemem` server entry; `command = "uv"`; `args = ["--directory", "${PWD}", "run", "python", "claude-code/codemem/mcp/server.py"]`; `env = { CODEMEM_REPO_ROOT: "${PWD}", CODEMEM_DB: "${PWD}/.codemem/index.db" }`. `${PWD}` is expanded by Claude Code at config-load from its own process env, so any machine that launches Claude Code from the aa-ma-forge workspace root gets correct absolute paths in the subprocess. No hardcoded `/home/sjnewhouse/` paths — safe to commit.
- **Rewrote Milestone M4 AC line 360** (`tasks.md`): `paste 3-line settings.json snippet` → `ship a project-scope .mcp.json at the workspace root (top-level mcpServers.codemem) → on first fresh-session use Claude Code prompts for approval → first MCP query triggers build → returns answer in < 5s on aa-ma-forge`. Added L-244 note.
- **Rewrote Task 4.8 AC line 418:** replaced both `settings.json` mentions with `.mcp.json`; added language about `${VAR:-default}` env expansion so the shipped snippet is portable; added L-244 note explaining the original wording was wrong.
- **Updated Task 3.5.5:** Status PENDING → PREPARED v2 (authoring done, live verification remains). Appended new Result Log entry documenting the `.mcp.json` contents + verification evidence, the orphan-cleanup still-pending item, and the live-verification steps for the next fresh session.

**What was NOT done this turn.**
- **Orphan cleanup of `~/.claude/.mcp.json`:** the stale codemem entry from the 2026-04-17 defective prep is still there. It is a no-op at runtime (Claude Code doesn't read the file) but lingers as a trap for future readers. Deferred pending user confirm — asking before touching any other config file beyond the one Option B specifically requires.
- **Live verification of the three tool calls:** requires a fresh Claude Code session. Cannot happen in this session because MCP servers attach at session start.

**Scope expansion justification.** User granted "fix M4 now" authorisation explicitly. Without it, M4 Task 4.8's wrong wording would inherit the same defect and M4 would have to re-discover it. Fixing concurrently while the defect is fresh saves roundtrips.

### Unresolved

- **Live verification (3.5.5 AC criteria 3+4):** requires fresh Claude Code session with `.mcp.json` approval. Pending next session.
- **Orphan `~/.claude/.mcp.json` codemem entry:** RESOLVED 2026-04-17. Removed via `jq 'del(.mcpServers.codemem)'` after timestamped backup. Post-state verified: `mcpServers` keys = `['galactic', 'project-index-query']` — matching pre-2026-04-17-defect baseline. AC criterion 5 satisfied.

---

## 2026-04-17 — Task 3.5.5 LIVE VERIFICATION + L-253 defect fix (closes M3.5)

**Verified.** Live MCP dogfood in a fresh Claude Code session surfaced a production defect at the very first M3-tool invocation. Root cause, fix, and all four M3.5 integration gaps are now closed.

**Live session evidence.**
1. `mcp__codemem__search_symbols("build_server")` → non-error result; `build_server` at `claude-code/codemem/mcp/server.py:90`.
2. `mcp__codemem__hot_spots()` → initially `no such table: commit_files`.
3. `mcp__codemem__aa_ma_context("codemem")` → initially `no such table: ownership`.

Root cause (confirmed by reading DB + code): `.codemem/index.db` at `user_version=1` with only M1 tables. `indexer.build_index`, `incremental.refresh_incrementally`, and `journal.wal.replay_wal` all called `db.apply_schema(conn)` but never `db.migrate(conn)`, so the M3 Task 3.8 v2 tables (`commits`, `commit_files`, `ownership`, `co_change_pairs`) never materialized in the field. M3 unit tests missed it because fixtures hand-crafted v2 tables directly (or called `migrate` manually in isolated tests).

**Fix (added as new Task 3.5.6 under M3.5 scope):**
1. New helper `db.ensure_schema(conn) -> int` = `apply_schema(conn)` + `migrate(conn)`. Single entry-point for all production writers. Exported from `storage/__init__.py`.
2. Swapped three production call sites: `indexer.py::build_index`, `incremental.py::_refresh_locked`, `journal/wal.py::replay_wal`. `grep "db\.apply_schema" packages/codemem-mcp/src/codemem/` now returns zero production hits (only the helper's internal call).
3. Fixed one downstream WAL producer: `indexer.py` was tagging intent entries with hardcoded `prev_user_version=1`; now uses `db.CURRENT_SCHEMA_VERSION`, so entries written against a v2 DB replay cleanly.
4. Fixed three downstream test fixtures that were hardcoding `prev_user_version=1` in WAL entries that get replayed (`test_wal.py::test_unacked_entry_applied_and_acked`, `test_wal.py::test_kill_between_intent_and_commit_replay_recovers`, `test_wal_rotation.py::_emit_one_file_upsert`). The `test_wal.py:319` `prev_user_version=999` test deliberately uses a mismatched value to exercise `ReplayConflict` and was left alone.

**TDD cycle.** Flipped `tests/codemem/test_indexer.py::TestBuildIndex::test_creates_db_and_applies_schema` (asserting `user_version == 1`) to `test_creates_db_at_current_schema_version` (asserting `user_version == db.CURRENT_SCHEMA_VERSION` AND `{"commits","commit_files","ownership","co_change_pairs"}.issubset(tables)`). Ran — confirmed `assert 1 == 2` failure for the expected reason. Implemented the fix. Re-ran — single test GREEN. Ran full codemem suite: `346 passed, 1 skipped, 1 deselected` (unchanged from pre-fix total — 6 WAL tests initially failed due to the hardcoded `prev_user_version=1` problem, all fixed in step 3+4). Ruff clean. Import-linter 2/2 contracts kept.

**Live re-verification (in-session).** Backed up live v1 DB to `/tmp/codemem-bak/index.db.pre-v2migration-fix`. Deleted `.codemem/`. Rebuilt via fresh-code subprocess: `uv run python -c "from codemem.indexer import build_index; build_index(Path.cwd(), Path('.codemem/index.db'))"` → 68 files / 679 symbols / 1460 edges / 195 resolved / 1024 unresolved in 0.20s. Post-build DB at `user_version=2` with 7 tables (all 4 v2 tables present). Re-invoked the three MCP tools:
- `search_symbols("build_server")` → unchanged — works.
- `hot_spots()` → `{"files":[],"window_days":90,"top_n":10,"error":null,"truncated":false}` — schema error gone; empty because `codemem refresh` hasn't populated the `commits` cache yet. AC "non-error response" satisfied.
- `aa_ma_context("codemem")` → 91KB structured JSON with populated `owners_by_file` (real git-blame data), `blast_radius_by_symbol`, `files`, `symbols`, `hot_spots=[]`, `markdown`, `error=null`. The AA-MA moat is live.

**Lesson L-253 filed in `docs/lessons.md`.** Pins the `apply_schema`-without-`migrate` anti-pattern and the `ensure_schema` single-choke-point rule. Cross-references L-244 and L-245 — all three are "tests pass but production doesn't" from unexercised glue layers. Argues for every milestone AC to include at least one "dogfood from the outside" step.

**Milestone M3.5 status.** All 6 ACs verified. All 6 tasks (3.5.1 through 3.5.6) COMPLETE. Status flipped PENDING → COMPLETE.

### Unresolved

- None for M3.5. Next milestone: **M4 (Polish, Demo, Differentiation)**.
