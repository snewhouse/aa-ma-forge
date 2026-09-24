# diagram-generation Tasks (HTP)

> Gate fields below are the ones `aa-ma-gate` actually reads — it takes only
> `tasks_md`. They mirror plan.md §2a, which is the single source. Never write a
> field with an empty value; the gate refuses it (exit 2).

## Milestone 1: codemem `file_edges` (schema v3) + qualified callees
- Status: COMPLETE
- Dependencies: None
- Gate: HARD
- Audit-Profile: code-only
- Critical-Path: data-xform
- Complexity: 70%
- Effort: 2
- Goal: `file_edges` holds file→file `import` rows for Python, and `dst_unresolved` keeps the dotted callee (`sqlite3.connect`, `self.conn.execute`).
- Acceptance Criteria: 8 criteria — see plan.md § Milestone 1
- Result Log: COMPLETE 2026-09-24, HARD gate approved by Ste. 8/8 AC verified. schema v3 `file_edges` (694 import edges on this repo, 162 resolved, 0 dups); apply_schema downgrade guard; dotted alias-qualified callees; resolved call graph unchanged (1227=1227 same tree). Tests 1122 passed / 2 skipped. §6.8 PASS_WITH_WARNINGS (0C/3W/15I; 2W fixed cbf0564). Commits 7925b38 e6026d4 567dba8 3787633 e4dd3be 9f72847 cbf0564 80c2d34 + milestone commit.

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
- Status: COMPLETE
- Mode: HITL
- Result Log: Mode: HITL — Ste approved (Proceed). CRITICAL_PATH_REVIEW (data-xform) written to provenance.log naming this milestone. Full suite 1122 passed / 2 skipped (baseline 1101 +21 new); ruff clean; tests/codemem/ collected by CI (security.yml:157). Same-tree base vs head: symbols + resolved call edges identical.

## Milestone 2: `aa_ma.render.graph` sqlite seam + import contract + ADR-0014
- Status: COMPLETE
- Dependencies: Milestone 1
- Gate: HARD
- Audit-Profile: code-only
- Critical-Path: hook-modification
- Complexity: 55%
- Effort: 1
- Goal: `aa_ma` reads the graph without importing codemem, and the coupling is pinned so it cannot later be "simplified" into an import.
- Acceptance Criteria: 7 criteria — see plan.md § Milestone 2
- Result Log: COMPLETE 2026-09-24, HARD gate approved by Ste. 7/7 AC verified. `aa_ma.render.graph` read-only never-raising seam (live: OK, 163 import / 175 call edges); `aa-ma-never-imports-codemem` contract (mutation -> BROKEN) + `lint-imports` in CI for the first time; ADR-0014 Accepted. §6.8: 1 CRITICAL accepted+fixed (0dd464b, ae1e97a), re-run clean. Tests 1146 passed / 2 skipped. Commits ca90667 550312a 103aa7f 4fdb7d3 74dfcbb 2421e50 0dd464b ae1e97a c1c0b67 + milestone commit.

### Sub-step 2.1: [test] `test_graph.py` with stdlib-sqlite3-built v2/v3/missing/stale fixtures, RED
- Status: COMPLETE
- Mode: AFK
- Result Log: Mode: AFK — auto-dispatched. New `tests/render/test_graph.py` (14 tests): stdlib-sqlite3 fixtures at v2/v3 + missing + corrupt + stale (touch AND delete); readers (resolved-only imports, DISTINCT call projection dropping same-file/unresolved, empty on non-OK, readable when STALE); read-only conn; contract stanza by name + `lint-imports` named-contract KEPT. RED: collection error (module absent). Baseline lint-imports: 3 kept, 0 broken.

### Sub-step 2.2: [impl] `render/graph.py`: `open_graph`, `import_edges`, `call_edges`
- Status: COMPLETE
- Mode: AFK
- Result Log: Mode: AFK — auto-dispatched. `src/aa_ma/render/graph.py`: GraphStatus(StrEnum) OK/MISSING/SCHEMA_TOO_OLD/STALE; frozen GraphHandle; open_graph (file: URI mode=ro, user_version >= 3, never raises — sqlite3.Error -> MISSING with reason); staleness = disk mtime > files.mtime OR file deleted (deletion added beyond plan: a vanished file is equally out of date); STALE handles keep conn (advisory); import_edges / call_edges both SELECT DISTINCT, call projection drops same-file. 12/14 graph tests green; 2 remaining are 2.3 contract tests. ruff clean.

### Sub-step 2.3: [impl] `.importlinter` contract + `uv run lint-imports` CI step
- Status: COMPLETE
- Mode: AFK
- Result Log: Mode: AFK — auto-dispatched. `.importlinter`: + `aa-ma-never-imports-codemem` (forbidden, source aa_ma, forbidden codemem) + header comment 4; corrected header claim that CI already ran lint-imports (it ran 0 times). security.yml codemem-smoke: + `uv run lint-imports` step directly after `uv sync`. lint-imports: 4 kept, 0 broken. MUTATION: `import codemem` in graph.py -> "aa_ma never imports codemem BROKEN ... aa_ma.render.graph -> codemem (l.13)", restored. YAML parses; tests/render collected by CI catch-all step. render suite 81 passed.

### Sub-step 2.4: [docs] ADR-0014
- Status: COMPLETE
- Mode: HITL
- Result Log: Mode: HITL — Ste approved "Proceed — Accepted". `docs/adr/0014-derived-architecture-views.md` (Status: Accepted; flip to Implemented when M3/M5 consumers ship): option 4 stdlib-sqlite3 seam over import / MCP / subprocess; extends ADR-0010, supersedes nothing (markdown = intent, graph = fact); never-raises status contract; v1 `edges` duplicate-row defect recorded, repair deferred to a separate effort. `docs/adr/INDEX.md` row added. No hardcoded ADR counts in README/CHANGELOG/SECURITY/spec.

## Milestone 3: `codemem draw` emitter, layered cuts L0–L3
- Status: COMPLETE
- Dependencies: Milestone 2
- Gate: HARD
- Audit-Profile: code-only
- Critical-Path: data-xform
- Complexity: 70%
- Effort: 2
- Goal: One command emits readable mermaid at four zoom levels from the codemem graph.
- Acceptance Criteria: 5 criteria — see plan.md § Milestone 3
- Result Log: COMPLETE 2026-09-24, HARD gate approved by Ste. 5/5 AC (AC2 = --kind call 5/4; default both 5/8; AC3 27->96 on frozen prototype data, live 27->107). `codemem draw` L0-L3 over import ∪ call with QUOTED sigils; every Ticket 3 band reproduced on frozen data; 232/232 node ids vs independent JS; real renders PASS at every level. Fixed en route (Ste-approved): build_index rebuild misattribution (§3.5, live 2819 -> 0), bare-sigil parse error (plan §13 quoted), local renderer. §6.8 0C/6W (all fixed 8289371). Tests 1195 passed / 2 skipped. Commits 32adf2c e82add7 88e8bbc d0b9564 5f5176d b677fde fe90f6d 0e6966b 8289371 870bc33 + milestone commit; [ad-hoc] 75f8d09 CI hardening.

### Sub-step 3.1: [test] `draw-node-ids.json` fixture + `test_draw_cut.py`, RED
- Status: COMPLETE
- Mode: AFK
- Result Log: Mode: AFK — auto-dispatched. `tests/fixtures/draw-node-ids.json` (232 entries, levels 0-3, all unique) generated by an INDEPENDENT JS port of the prototype `nid` (`draw-node-ids.gen.mjs`, run with node v26) over `L<level>:<name>` — includes `( ) - " é 😀 space` names; caught + fixed my own divergence (code units vs the prototype's code-point/high-surrogate quirk). `tests/fixtures/draw-prototype-graph.json` = prototype graph.json @ c49d084 (158KB) so Ticket 3 bands are pinned on the data they were measured on. `test_draw_cut.py`: fidelity (raw 85/96 & 25/27, L0 4/3, L1 10/9, L2 render 5/4, L3 gate 18/27), kinds, DISTINCT, direction, hops, L3 call-only, dropped>500, is_test_path. RED: collection error (module absent).

### Sub-step 3.2: [impl] `draw/cut.py`: `node_id`, collapse, `cut()`
- Status: COMPLETE
- Mode: AFK
- Result Log: Mode: AFK — auto-dispatched. `codemem/draw/{__init__,cut}.py`: Level(IntEnum), frozen Cut, `node_id` (prototype hash incl. high-surrogate quirk), `is_test_path` (any dir component `tests`), `cut(conn, level, *, scope, hops, include_tests, direction, kind)` — SELECT DISTINCT on calls + imports, same-file dropped, scope neighbourhood BEFORE collapse, sorted truncation at MAX_EDGES=500 with `dropped`, node_id collision -> ValueError. test_draw_cut 28/28 incl. every Ticket 3 band on frozen data and 232/232 JS node ids. ruff clean; lint-imports 4 kept.

### Sub-step 3.3: [test] `test_draw_mermaid.py` incl. label escaping for `( ) -`, RED
- Status: COMPLETE
- Mode: AFK
- Result Log: Mode: AFK — auto-dispatched. `tests/codemem/test_draw_mermaid.py` (9 tests): header, node lines, QUOTED sigil edges `-->|"@kind"|` (bare form asserted absent), determinism, `( ) -` intact inside quotes, escape_label (`"`->#quot;, `#`->#35; first, `< >`->#lt;/#gt;, control chars->?), dropped reported as `%%` comment, empty cut header-only, render_check never FAIL on hostile labels (UNKNOWN in CI, PASS locally). RED: collection error (module absent). Precursor: local renderer fixed + sigil grammar corrected (88e8bbc).

### Sub-step 3.4: [impl] `draw/mermaid.py` + `codemem draw` subcommand (`cli.py:269-309`)
- Status: COMPLETE
- Mode: AFK
- Result Log: Mode: AFK — auto-dispatched. `draw/mermaid.py`: `escape_label` (#->#35; first, "->#quot;, <>->#lt;/#gt;, control->?), `to_mermaid` deterministic flowchart LR with QUOTED sigil edges, dropped as `%%` comment. `cli.py`: `codemem draw --level L0..L3 (default L0) --scope --hops --include-tests --direction --kind` — stdout pure mermaid, summary on stderr; exit 1 on missing/v<3/unreadable index (never creates the file, read-only), argparse exit 2. `captions=` param deferred to M5 (Ticket 12 owns its semantics). test_draw_* 41/41; REAL render PASS (hostile + empty) locally; full suite 1187 passed / 2 skipped; ruff clean; 4 contracts kept.

### Sub-step 3.5: [fix] `build_index` misattributes symbols across rebuilds (FK OFF before DELETE; file ids reused)
- Status: COMPLETE
- Mode: AFK
- Added: 2026-09-24 (Ste approved, circuit-breaker re-plan) — pre-existing codemem defect found while verifying M3 cuts; live index held 4462 symbols vs 1643 real, 2819 misattributed.
- Result Log: Mode: AFK — Ste approved. ROOT CAUSE (read + reproduced): indexer.build_index sets `PRAGMA foreign_keys = OFF` (l.391) BEFORE `DELETE FROM files` (l.402) -> no cascade -> orphaned symbols/edges re-attached to reused file ids; closing foreign_key_check passes because orphans now have a parent. Repro: build {b,c}, add a.py, rebuild -> beta under a.py, gamma under b.py. FIX: full build explicitly clears edges, file_edges, symbols, files inside its transaction (git-mining tables path-keyed, untouched) — also drops disk-deleted files and self-heals corrupted indexes. RED fe90f6d (3 tests) -> GREEN. Live index healed: 4462 -> 1649 symbols, 2819 -> 0 misattributed; build 0.45s (unchanged). Healed-index call cuts now match the prototype exactly (L2 render 5/4, raw -tests 25/27). codemem 589 passed.

## Milestone 4: Plugin-surface extractor
- Status: ACTIVE
- Dependencies: Milestone 3
- Gate: HARD
- Audit-Profile: code-only
- Complexity: 50%
- Effort: 1
- Goal: `claude-code/**/*.md` yields a commands→skills→agents→hooks graph with three-valued reference classification.
- Acceptance Criteria: 5 criteria — see plan.md § Milestone 4

### Sub-step 4.1: [measure] re-measure the surface; identify the 42nd `Skill()` target
- Status: COMPLETE
- Mode: AFK
- Result Log: Mode: AFK — auto-dispatched. Scratch prototype (scratchpad/m4proto.py, not committed) at 27fa477. **42nd target = `Skill(feature-dev:feature-dev)`** (`claude-code/skills/understand-codebase/references/DIMENSIONS.md:252`) — plugin-namespaced; Ticket 4's `[A-Za-z0-9_-]+` cannot match `:`, so it counted 41. Resolves externally (`~/.claude/plugins/.../feature-dev/commands/feature-dev.md`) → DECLARED_EXTERNAL. With `[A-Za-z0-9_:-]+`: 42 distinct = 17 ON_DISK / 21 DECLARED_EXTERNAL (all 20 prior names verified in `~/.claude/skills` + feature-dev) / 4 DANGLING {aa-ma-plan, codebase-deep-dive, haiku-eval, index}. Node-level distinct edges: 191 (154 ON_DISK / 33 DECLARED_EXTERNAL / 4 DANGLING) from 57 source files; nodes 59 (13 cmd / 21 skill / 12 agent / 11 hook / 2 rule). Orphans = exactly AC4's 7. Agent externals {Explore, general-purpose, gsd-codebase-mapper}; hook external {aa-ma-share-allow.sh} (lives in scripts/). 163 (Ticket 4) vs 191: Ticket 4 excluded externals and counted differently; order of magnitude holds.

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
