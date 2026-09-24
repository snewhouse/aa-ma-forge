# diagram-generation Tasks (HTP)

> Gate fields below are the ones `aa-ma-gate` actually reads — it takes only
> `tasks_md`. They mirror plan.md §2a, which is the single source. Never write a
> field with an empty value; the gate refuses it (exit 2).

## Milestone 1: codemem `file_edges` (schema v3) + qualified callees
- Status: ACTIVE
- Dependencies: None
- Gate: HARD
- Audit-Profile: code-only
- Critical-Path: data-xform
- Complexity: 70%
- Effort: 2
- Goal: `file_edges` holds file→file `import` rows for Python, and `dst_unresolved` keeps the dotted callee (`sqlite3.connect`, `self.conn.execute`).
- Acceptance Criteria: 8 criteria — see plan.md § Milestone 1

### Sub-step 1.1: [test] v3 migration + downgrade-guard tests, RED (`tests/codemem/test_schema_v2.py` v3 sibling; new `test_file_edges.py`)
- Status: COMPLETE
- Mode: AFK
- Scope (widened 2026-09-24, validator WARN #3): 1.1 owns ALL `file_edges` tests — AC1, AC2, AC5/5b (refresh_index row-set idempotency), AC6 (downgrade guard), AC7 (CASCADE), and the 3x-insert dedup regression.
- Result Log: Mode: AFK — auto-dispatched. New `tests/codemem/test_file_edges.py`, 14 tests: RED 12 failed / 2 passed (the passing 2 are pre-existing invariants: apply_schema-alone=v1, file_edges absent pre-migrate). Covers AC1, AC2, AC5, AC5b, AC6, AC7 + 3x-insert dedup. Baseline before M1: 1101 passed / 2 skipped @ f8e44ed.

### Sub-step 1.2: [impl] `_MIGRATION_V3_FILE_EDGES` + `CURRENT_SCHEMA_VERSION` 3 (`db.py:41,104`)
- Status: COMPLETE
- Mode: AFK
- Result Log: Mode: AFK — auto-dispatched. `_MIGRATION_V3_FILE_EDGES` (table + 2 partial UNIQUE + dst/src indexes, all IF NOT EXISTS, no kind CHECK) appended to MIGRATIONS; CURRENT_SCHEMA_VERSION 3; migrate() docstring corrected (DDL not rolled back). 4 v2 tests re-pointed at CURRENT_SCHEMA_VERSION (test_schema_v2.py). docs/codemem/migration-from-index.md:98 -> eight tables, user_version 3. WAL note: pending journals written at v2 now hit ReplayConflict (prev_user_version != 3) — rebuild instead.

### Sub-step 1.3: [impl] `apply_schema()` version guard so it honours its own docstring (`db.py:156-162`)
- Status: COMPLETE
- Mode: AFK
- Result Log: Mode: AFK — auto-dispatched. apply_schema() captures prior user_version and restores it when schema.sql lowered it (4 lines). TestDowngradeGuard 2/2 green (v2-era ensure_schema on v3 DB -> 3, file_edges intact). codemem suite: 534 passed / 3 failed (the 3 are 1.6 persistence tests, expected).

### Sub-step 1.4: [test] dotted-callee + asname fixtures, RED (2 assertions flip in `test_resolver.py`)
- Status: COMPLETE
- Mode: AFK
- Result Log: Mode: AFK — auto-dispatched. test_resolver.py: 2 assertions flipped get -> requests.get; + parametrized dotted-callee (sqlite3.connect, numpy.array via asname, self.conn.execute, os.path.join via from-import asname), import_aliases map shape, and 2 guards (import b; b.helper() still resolves; g().bar() not emitted). RED 7 failed / 11 passed (guards pass pre-change by design).

### Sub-step 1.5: [impl] `ast.unparse` callee + `import_aliases` map (`python_ast.py:113-120,370-377`)
- Status: COMPLETE
- Mode: AFK
- Result Log: Mode: AFK — auto-dispatched. python_ast.py: `ParseResult.import_aliases: dict[str,str]` (asname-or-head for `import`, `module.name` for from-imports); attribute callees on a pure Name/Attribute chain emitted as `ast.unparse` dotted string with head rewritten via aliases; chains through calls/subscripts still dropped. resolver.py: `_lookup_name()` matches on the last segment only for bare / single-Name receivers (pre-M1 behaviour) or receivers that are imported modules — `self.conn.execute` cannot bind to an unrelated `execute`. Guard test caught the naive version (b.helper lookup). codemem: 541 passed / 3 failed (1.6 tests only); PageRank + symbol-count tests unchanged-green.

### Sub-step 1.6: [impl] persist import edges in `resolver.py:131-134`; invalidate in `incremental.py`
- Status: COMPLETE
- Mode: AFK
- Result Log: Mode: AFK — auto-dispatched. resolver.py `_persist_import_edges()`: per parsed file, explicit `DELETE FROM file_edges WHERE src_file_id=?` then INSERT OR IGNORE import rows (resolved -> dst_file_id, else dst_unresolved=module). Resolves against the DB-wide `files` set, not the parse set (refresh passes dirty files only — an import of an unchanged file must resolve). DEVIATION: invalidation placed in the resolver, not incremental.py — both writers (build_index, refresh_index) call it, so one site covers both; incremental.py unchanged. Known gap (pre-existing, same as call edges): WAL replay does not re-run the resolver, so replay-from-scratch leaves file_edges empty until next build. codemem: 544 passed / 2 skipped.

### Sub-step 1.7: [verify] `CRITICAL_PATH_REVIEW` (data-xform) + full codemem suite green
- Status: PENDING
- Mode: HITL
- Result Log: [pending]

## Milestone 2: `aa_ma.render.graph` sqlite seam + import contract + ADR-0014
- Status: PENDING
- Dependencies: Milestone 1
- Gate: HARD
- Audit-Profile: code-only
- Critical-Path: hook-modification
- Complexity: 55%
- Effort: 1
- Goal: `aa_ma` reads the graph without importing codemem, and the coupling is pinned so it cannot later be "simplified" into an import.
- Acceptance Criteria: 7 criteria — see plan.md § Milestone 2

### Sub-step 2.1: [test] `test_graph.py` with stdlib-sqlite3-built v2/v3/missing/stale fixtures, RED
- Status: PENDING
- Mode: AFK
- Result Log: [pending]

### Sub-step 2.2: [impl] `render/graph.py`: `open_graph`, `import_edges`, `call_edges`
- Status: PENDING
- Mode: AFK
- Result Log: [pending]

### Sub-step 2.3: [impl] `.importlinter` contract + `uv run lint-imports` CI step
- Status: PENDING
- Mode: AFK
- Result Log: [pending]

### Sub-step 2.4: [docs] ADR-0014
- Status: PENDING
- Mode: HITL
- Result Log: [pending]

## Milestone 3: `codemem draw` emitter, layered cuts L0–L3
- Status: PENDING
- Dependencies: Milestone 2
- Gate: HARD
- Audit-Profile: code-only
- Complexity: 70%
- Effort: 2
- Goal: One command emits readable mermaid at four zoom levels from the codemem graph.
- Acceptance Criteria: 5 criteria — see plan.md § Milestone 3

### Sub-step 3.1: [test] `draw-node-ids.json` fixture + `test_draw_cut.py`, RED
- Status: PENDING
- Mode: AFK
- Result Log: [pending]

### Sub-step 3.2: [impl] `draw/cut.py`: `node_id`, collapse, `cut()`
- Status: PENDING
- Mode: AFK
- Result Log: [pending]

### Sub-step 3.3: [test] `test_draw_mermaid.py` incl. label escaping for `( ) -`, RED
- Status: PENDING
- Mode: AFK
- Result Log: [pending]

### Sub-step 3.4: [impl] `draw/mermaid.py` + `codemem draw` subcommand (`cli.py:269-309`)
- Status: PENDING
- Mode: AFK
- Result Log: [pending]

## Milestone 4: Plugin-surface extractor
- Status: PENDING
- Dependencies: Milestone 3
- Gate: HARD
- Audit-Profile: code-only
- Complexity: 50%
- Effort: 1
- Goal: `claude-code/**/*.md` yields a commands→skills→agents→hooks graph with three-valued reference classification.
- Acceptance Criteria: 5 criteria — see plan.md § Milestone 4

### Sub-step 4.1: [measure] re-measure the surface; identify the 42nd `Skill()` target
- Status: PENDING
- Mode: AFK
- Result Log: [pending]

### Sub-step 4.2: [test] generate `tests/golden/plugin-surface.json`; rename-behaviour test, RED
- Status: PENDING
- Mode: AFK
- Result Log: [pending]

### Sub-step 4.3: [impl] `draw/plugin_surface.py` + `draw/surface_allowlist.py`
- Status: PENDING
- Mode: AFK
- Result Log: [pending]

## Milestone 5: Captions sidecar
- Status: PENDING
- Dependencies: Milestone 3
- Gate: HARD
- Audit-Profile: code-only
- Complexity: 35%
- Effort: 0.5
- Goal: Authored prose reaches both the markdown emitter and the explorer from one file.
- Acceptance Criteria: 4 criteria — see plan.md § Milestone 5

### Sub-step 5.1: [test] `test_captions.py` incl. ORPHAN vs UNKNOWN, RED
- Status: PENDING
- Mode: AFK
- Result Log: [pending]

### Sub-step 5.2: [impl] `draw/captions.py` + authored `docs/architecture.captions.json`
- Status: PENDING
- Mode: AFK
- Result Log: [pending]

## Milestone 6: Living doc + `--check` + CI drift job + ADR-0016 → release `v0.15.0`
- Status: PENDING
- Dependencies: Milestone 4, Milestone 5
- Gate: HARD
- Audit-Profile: full
- Critical-Path: hook-modification
- Complexity: 60%
- Effort: 1.5
- Goal: `docs/architecture/` exists, is 100% generated, and CI fails when it drifts.
- Acceptance Criteria: 7 criteria — see plan.md § Milestone 6

### Sub-step 6.1: [test] `test_draw_check.py`: line-slice compare, stamp regex, caption-only diff, RED
- Status: PENDING
- Mode: AFK
- Result Log: [pending]

### Sub-step 6.2: [impl] `draw/views.py` registry + `codemem draw --check`
- Status: PENDING
- Mode: AFK
- Result Log: [pending]

### Sub-step 6.3: [impl] generate `docs/architecture/{README,component,plugin-surface}.md`
- Status: PENDING
- Mode: AFK
- Result Log: [pending]

### Sub-step 6.4: [impl] `architecture-drift` job in `security.yml` (Critical-Path)
- Status: PENDING
- Mode: HITL
- Result Log: [pending]

### Sub-step 6.5: [verify] CI green at this commit; `CRITICAL_PATH_REVIEW`
- Status: PENDING
- Mode: HITL
- Result Log: [pending]

### Sub-step 6.6: [docs] ADR-0016
- Status: PENDING
- Mode: HITL
- Result Log: [pending]

### Sub-step 6.7: [release] `scripts/release.sh minor --dry-run`, then cut v0.15.0
- Status: PENDING
- Mode: HITL
- Result Log: [pending]

## Milestone 7: `Dependencies:` grammar + Milestone graph + advisory
- Status: PENDING
- Dependencies: None
- Gate: HARD
- Audit-Profile: code-only
- Critical-Path: hook-modification
- Complexity: 60%
- Effort: 1.5
- Goal: Close CONTEXT.md's documented-undelivered Milestone graph promise, with an `M`-prefix-aware resolver.
- Acceptance Criteria: 8 criteria — see plan.md § Milestone 7

### Sub-step 7.1: [test] `deps-hazards.md` (`M1.0`, `M2a.1`, `2a`, cross-plan) + naive mutant, RED
- Status: PENDING
- Mode: AFK
- Result Log: [pending]

### Sub-step 7.2: [impl] `deps.py` parser/resolver + `CANONICAL_DEPENDENCY_RE` in `grammar.py`
- Status: PENDING
- Mode: AFK
- Result Log: [pending]

### Sub-step 7.3: [impl] `.importlinter` gains `aa_ma.deps`; `test_leaf_contract.py` green
- Status: PENDING
- Mode: AFK
- Result Log: [pending]

### Sub-step 7.4: [impl] Milestone graph into §13; scribe + template spelling
- Status: PENDING
- Mode: AFK
- Result Log: [pending]

### Sub-step 7.5: [verify] `aa-ma-gate` output byte-identical to the pre-M7 golden
- Status: PENDING
- Mode: AFK
- Result Log: [pending]

## Milestone 8: `PHANTOM_EDGE` sigil grammar
- Status: PENDING
- Dependencies: Milestone 2, Milestone 4
- Gate: HARD
- Audit-Profile: code-only
- Complexity: 75%
- Effort: 2
- Goal: The lint gains its first mermaid edge parser and verifies opt-in sigil edges against the derived graph.
- Acceptance Criteria: 6 criteria — see plan.md § Milestone 8

### Sub-step 8.1: [analysis] `Skill(impact-analysis)` on `mermaid_lint.py`; golden current `lint_text` output
- Status: PENDING
- Mode: AFK
- Result Log: [pending]

### Sub-step 8.2: [test] `sigil-edges.md` fixture: clean/phantom/LABEL_UNKNOWN/unlabelled/UNKNOWN, RED
- Status: PENDING
- Mode: AFK
- Result Log: [pending]

### Sub-step 8.3: [impl] edge parser + `PHANTOM_EDGE` tier
- Status: PENDING
- Mode: AFK
- Result Log: [pending]

### Sub-step 8.4: [verify] glob every completed `*-plan.md`: zero findings on sigil-free files
- Status: PENDING
- Mode: AFK
- Result Log: [pending]

## Milestone 9: I/O-boundary view — `Prototype-Required: YES`
- Status: PENDING
- Dependencies: Milestone 6
- Gate: HARD
- Audit-Profile: code-only
- Prototype-Required: YES
- Complexity: 85%
- Effort: 3
- Goal: A merged `io.md` with language subgraphs showing where the code touches DB, HTTP, filesystem, subprocess, env and queues.
- Acceptance Criteria: 6 criteria — see plan.md § Milestone 9

### Sub-step 9.1: [prototype] `Skill(prototype)` on this repo + `medical-research-skills`; `PROTOTYPE` provenance
- Status: PENDING
- Mode: HITL
- Result Log: [pending]

### Sub-step 9.2: [test] per-language sink fixtures (Py/TS/TSX/JS/Go), RED
- Status: PENDING
- Mode: AFK
- Result Log: [pending]

### Sub-step 9.3: [impl] `ast_grep.py` wrapper + 4 rule YAMLs + `draw/sinks.yaml`
- Status: PENDING
- Mode: AFK
- Result Log: [pending]

### Sub-step 9.4: [impl] `draw/io_sinks.py`, register `io` view, `IO_DENSE_BAND` line
- Status: PENDING
- Mode: AFK
- Result Log: [pending]

## Milestone 10: `/aa-ma-plan` §13 seeding + Angle 6 coverage rule
- Status: PENDING
- Dependencies: Milestone 8
- Gate: HARD
- Audit-Profile: full
- Critical-Path: hook-modification
- Complexity: 55%
- Effort: 1
- Goal: Every new plan ships real, checkable §13 edges, and a plan that creates files it does not draw is caught.
- Acceptance Criteria: 5 criteria — see plan.md § Milestone 10

### Sub-step 10.1: [test] `seeded-plan.md` fixture + `test_angle6_coverage.py`, RED
- Status: PENDING
- Mode: AFK
- Result Log: [pending]

### Sub-step 10.2: [impl] Phase 4 seeding in `aa-ma-plan.md` (Critical-Path)
- Status: PENDING
- Mode: HITL
- Result Log: [pending]

### Sub-step 10.3: [impl] Angle 6 **check 8**, appended, never renumbered
- Status: PENDING
- Mode: HITL
- Result Log: [pending]

### Sub-step 10.4: [verify] `test_plan_verification_angle6.py` + `test_planning_standard_count.py` green
- Status: PENDING
- Mode: HITL
- Result Log: [pending]

## Milestone 11: §6.7 HARD item + `DIAGRAM_VERIFIED` + ADR-0015
- Status: PENDING
- Dependencies: Milestone 10
- Gate: HARD
- Audit-Profile: full
- Critical-Path: hook-modification
- Complexity: 70%
- Effort: 1
- Goal: A §13 sigil edge still `UNKNOWN` at milestone COMPLETE blocks COMPLETE — without touching `gate.py`.
- Acceptance Criteria: 7 criteria — see plan.md § Milestone 11

### Sub-step 11.1: [test] `test_diagram_verified.bats` against `aa-ma-lint-views`, RED
- Status: PENDING
- Mode: AFK
- Result Log: [pending]

### Sub-step 11.2: [verify] capture pre-edit §6.7 awk extraction output
- Status: PENDING
- Mode: AFK
- Result Log: [pending]

### Sub-step 11.3: [impl] checklist row + fence **after** the existing gate fence (Critical-Path)
- Status: PENDING
- Mode: HITL
- Result Log: [pending]

### Sub-step 11.4: [verify] 58 bats tests green; extraction output unchanged; `CRITICAL_PATH_REVIEW`
- Status: PENDING
- Mode: HITL
- Result Log: [pending]

### Sub-step 11.5: [docs] ADR-0015
- Status: PENDING
- Mode: HITL
- Result Log: [pending]

## Milestone 12: Explorer + Node CI job
- Status: PENDING
- Dependencies: Milestone 3
- Gate: HARD
- Audit-Profile: full
- Critical-Path: hook-modification
- Prototype-Required: YES
- Complexity: 80%
- Effort: 2.5
- Goal: `aa-ma-render --explorer` produces a self-contained, clickable, level-deriving HTML file in `build/`.
- Acceptance Criteria: 8 criteria — see plan.md § Milestone 12

### Sub-step 12.1: [prototype] delegated listener against real mermaid SVG; `PROTOTYPE` provenance
- Status: PENDING
- Mode: HITL
- Result Log: [pending]

### Sub-step 12.2: [test] `explorer_contract.test.mjs` + `test_explorer_fixture.py` on the shared fixture, RED
- Status: PENDING
- Mode: AFK
- Result Log: [pending]

### Sub-step 12.3: [impl] `render/explorer.py` + `explorer.js` + `--explorer` flag
- Status: PENDING
- Mode: AFK
- Result Log: [pending]

### Sub-step 12.4: [impl] node job in `security.yml` (Critical-Path)
- Status: PENDING
- Mode: HITL
- Result Log: [pending]

### Sub-step 12.5: [verify] manual browser drill observation; `CRITICAL_PATH_REVIEW`
- Status: PENDING
- Mode: HITL
- Result Log: [pending]

## Milestone 13: MCP `diagram` tool + consumer rewire — `Prototype-Required: YES`
- Status: PENDING
- Dependencies: Milestone 6
- Gate: HARD
- Audit-Profile: code-only
- Critical-Path: hook-modification
- Prototype-Required: YES
- Complexity: 65%
- Effort: 2
- Goal: The third door works, and every skill that names a graph backend names the right one.
- Acceptance Criteria: 9 criteria — see plan.md § Milestone 13

### Sub-step 13.1: [prototype] measure L0-L3 on `medical-research-skills`; `PROTOTYPE` provenance
- Status: PENDING
- Mode: HITL
- Result Log: [pending]

### Sub-step 13.2: [test] `test_mcp_diagram.py` + update tool-count pins 12 -> 13, RED
- Status: PENDING
- Mode: AFK
- Result Log: [pending]

### Sub-step 13.3: [impl] `diagram()` + registration in `claude-code/codemem/mcp/server.py`
- Status: PENDING
- Mode: AFK
- Result Log: [pending]

### Sub-step 13.4: [impl] Deep tier rewire; `.gitignore` append; PROJECT_INDEX repoint
- Status: PENDING
- Mode: AFK
- Result Log: [pending]

### Sub-step 13.5: [verify] frontmatter inventory + xref tests green (no files added/removed)
- Status: PENDING
- Mode: AFK
- Result Log: [pending]

## Milestone 14: Glossary, spec, counts → release `v0.16.0`
- Status: PENDING
- Dependencies: Milestone 13
- Gate: HARD
- Audit-Profile: docs-only
- TDD-Waiver: docs-only
- Complexity: 30%
- Effort: 0.5
- Goal: The vocabulary and the counts match what shipped.
- Acceptance Criteria: 5 criteria — see plan.md § Milestone 14

### Sub-step 14.1: [docs] CONTEXT.md: 7 glossary terms
- Status: PENDING
- Mode: HITL
- Result Log: [pending]

### Sub-step 14.2: [docs] spec §XI body (no renumbering), quick-ref, foundations
- Status: PENDING
- Mode: AFK
- Result Log: [pending]

### Sub-step 14.3: [docs] hardcoded counts in the 5 files CLAUDE.md names; `Skill(doc-drift-detection)` clean
- Status: PENDING
- Mode: AFK
- Result Log: [pending]

### Sub-step 14.4: [release] dry-run, then cut v0.16.0
- Status: PENDING
- Mode: HITL
- Result Log: [pending]
