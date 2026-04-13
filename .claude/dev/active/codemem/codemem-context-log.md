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
