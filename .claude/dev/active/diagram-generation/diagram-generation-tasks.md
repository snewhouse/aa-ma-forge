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
- Status: COMPLETE
- Dependencies: Milestone 3
- Gate: HARD
- Audit-Profile: code-only
- Complexity: 50%
- Effort: 1
- Goal: `claude-code/**/*.md` yields a commands→skills→agents→hooks graph with three-valued reference classification.
- Acceptance Criteria: 5 criteria — see plan.md § Milestone 4
- Result Log: 5/5 AC verified; HARD gate APPROVED (Ste, 2026-09-24). Commits e249695 (4.1), beec7c1 RED → c6346e7 GREEN, 29d1bd3 RED → 711e8b7 review fixes, 3a6c8c5 impl-review. §6.8: 1 CRITICAL accepted+fixed, re-review clean. 1216 passed; render PASS 84 nodes / 187 edges.

### Sub-step 4.1: [measure] re-measure the surface; identify the 42nd `Skill()` target
- Status: COMPLETE
- Mode: AFK
- Result Log: Mode: AFK — auto-dispatched. Scratch prototype (scratchpad/m4proto.py, not committed) at 27fa477. **42nd target = `Skill(feature-dev:feature-dev)`** (`claude-code/skills/understand-codebase/references/DIMENSIONS.md:252`) — plugin-namespaced; Ticket 4's `[A-Za-z0-9_-]+` cannot match `:`, so it counted 41. Resolves externally (`~/.claude/plugins/.../feature-dev/commands/feature-dev.md`) → DECLARED_EXTERNAL. With `[A-Za-z0-9_:-]+`: 42 distinct = 17 ON_DISK / 21 DECLARED_EXTERNAL (all 20 prior names verified in `~/.claude/skills` + feature-dev) / 4 DANGLING {aa-ma-plan, codebase-deep-dive, haiku-eval, index}. Node-level distinct edges: 191 (154 ON_DISK / 33 DECLARED_EXTERNAL / 4 DANGLING) from 57 source files; nodes 59 (13 cmd / 21 skill / 12 agent / 11 hook / 2 rule). Orphans = exactly AC4's 7. Agent externals {Explore, general-purpose, gsd-codebase-mapper}; hook external {aa-ma-share-allow.sh} (lives in scripts/). 163 (Ticket 4) vs 191: Ticket 4 excluded externals and counted differently; order of magnitude holds.

### Sub-step 4.2: [test] generate `tests/golden/plugin-surface.json`; rename-behaviour test, RED
- Status: COMPLETE
- Mode: AFK
- Result Log: Mode: AFK — auto-dispatched. Golden generated by the independent scratch prototype (not the src under test): 191 edges, 7 orphans, 7 wired hooks, errors []. `tests/codemem/test_plugin_surface.py` — 13 tests: golden equality (regenerate via `uv run python tests/codemem/test_plugin_surface.py`), AC2 on-disk/external resolution + Cut excludes exactly DANGLING, AC3 one-class-per-target + named DANGLING set + feature-dev:feature-dev external, AC4 named orphans + errors == [], codemem/docs out; fixture tree: rename dir-only moves exactly its 2 refs to DANGLING and beta is an orphan, full rename keeps the graph, dir-stem identity over frontmatter, /cmd on-disk filter + glob + self-drop + path-fragment, agent/hook/skill externals + unlisted → DANGLING, install.sh hook events, wired-missing and missing install.sh are errors. RED: collection ImportError (`codemem.draw.plugin_surface` absent).

### Sub-step 4.3: [impl] `draw/plugin_surface.py` + `draw/surface_allowlist.py`
- Status: COMPLETE
- Mode: AFK
- Result Log: Mode: AFK — auto-dispatched. `extract(repo_root) -> Surface(cut, edges, orphans, hook_events, errors)` (API-shape resolution in context-log 2026-09-24 4.1). `surface_allowlist.EXTERNAL` = 21 skills / 3 agents / 1 hook, `HOOK_TABLE = scripts/install.sh`. `cut.from_edges()` extracted from `cut()` (DRY: sort, MAX_EDGES cap, id-collision check) — M3 behaviour unchanged (M3 suites green). GREEN: 13/13; src output byte-identical to the independent prototype's golden (regen → no diff). Full suite 1208 passed / 2 skipped; ruff clean; bandit clean; lint-imports 4 kept / 0 broken. Live: 80 nodes / 187 drawn edges / 0 dropped; `render_check` = PASS on the real renderer.

## Milestone 5: Captions sidecar
- Status: COMPLETE
- Dependencies: Milestone 3
- Gate: HARD
- Audit-Profile: code-only
- Complexity: 35%
- Effort: 0.5
- Goal: Authored prose reaches both the markdown emitter and the explorer from one file.
- Acceptance Criteria: 4 criteria — see plan.md § Milestone 5
- Result Log: 4/4 AC verified; HARD gate APPROVED (Ste, 2026-09-24). Commits 1d6a3ec RED → 2a884e5, 405f46c RED → 8f9edd3 (equal-or-contained), 6f39194 RED → 185453c (§6.8 fixes), 4051113 records. §6.8: 0 CRITICAL / 11 WARNING (6 fixed, 5 recorded as M6/M8/M12 obligations). 1245 passed.

### Sub-step 5.1: [test] `test_captions.py` incl. ORPHAN vs UNKNOWN, RED
- Status: COMPLETE
- Mode: AFK
- Result Log: Mode: AFK — auto-dispatched. 20 tests: load (absent → {}, flat mapping, 4 malformed shapes → ValueError naming the file, path outside docs/architecture/); orphans (existing file/dir keys silent, deleted → ORPHAN_CAPTION, planned → UNKNOWN, stale @start reported by its path, never mutates prose, authored sidecar clean against `git ls-files`); for_cut (dir caption at L0/L1, file caption at L2/L3); @start classDef at exact node and at the containing node at L0, no-captions output unchanged, caption-only edit not drift, render never FAIL. RED: ImportError (`codemem.draw.captions` absent).

### Sub-step 5.2: [impl] `draw/captions.py` + authored `docs/architecture.captions.json`
- Status: COMPLETE
- Mode: AFK
- Result Log: Mode: AFK — auto-dispatched. `captions.py`: `load`, `orphans -> list[CaptionFinding]`, `for_cut`, `start_ids`; `mermaid.to_mermaid(c, captions=None)` adds `classDef start` + `class <ids> start` only (None → M3 output byte-identical). Sidecar = the plan's three example entries verbatim (no invented prose). Live finding: M3 collapses L1 to depth 2, so the plan's depth-3 dir keys matched no node at any level; Ste chose equal-or-contained (dir caption covers the dir node and nodes inside it, never ancestors) — RED 405f46c → GREEN 8f9edd3. Live on a fresh index: L2 shows both dir captions, L3 (scope render/) shows `src/aa_ma/render/`, @start highlighted at L2/L3; every level render PASS. 20 caption tests (corrected by §6.8: pytest collects 20); full suite 1236 passed / 2 skipped; ruff/bandit clean; lint-imports 4 kept.

## Milestone 6: Living doc + `--check` + CI drift job + ADR-0016 → release `v0.15.0`
- Status: COMPLETE
- Dependencies: Milestone 4, Milestone 5
- Gate: HARD
- Audit-Profile: full
- Critical-Path: hook-modification
- Complexity: 60%
- Effort: 1.5
- Goal: `docs/architecture/` exists, is 100% generated, and CI fails when it drifts.
- Acceptance Criteria: 7 criteria — see plan.md § Milestone 6
- Result Log: 7/7 AC verified; HARD gate APPROVED (Ste, 2026-09-24). RED 552d663 → d42cb50 (views + CLI), 7f7bfae docs, 6fab78e CI job, 7beb92c ADR-0016, a8812c7 changelog; §6.8 RED 30d2c88 → f3ca3af; release b469b08 = v0.15.0. §6.8: 1 CRITICAL disputed, 9 WARNING fixed. 1288 passed; CI 6/6 on b469b08. Known RED 91bdd5f → L-025.

### Sub-step 6.1: [test] `test_draw_check.py`: line-slice compare, stamp regex, caption-only diff, RED
- Status: COMPLETE
- Mode: AFK
- Obligations (M5 §6.8, Ste 2026-09-24): `--check` compares ONLY the ```mermaid fences (prose-only / caption edits are never drift; an `@start` edit IS drift — test both). Every write goes through `captions.check_generated_target()` (built + tested 61eb4e4); test the writer calls it.
- Result Log: Mode: AFK — auto-dispatched. `tests/codemem/test_draw_check.py` (18 tests) on a committed tmp git repo with a real `build_index`: --write stamps every registered view (AC1 regex) and a rewrite changes only line 1; component = L2 with @start classDef and `escape_prose` captions; plugin-surface registered only where `claude-code/` exists; a rogue registry entry onto the sidecar is refused by `check_generated_target` and the sidecar is untouched; --check clean after write, line-2 hand-edit / missing view / README stray line = exit 1 naming `codemem draw --write` (AC2), line-1 edit not drift, no index / schema v2 = UNKNOWN exit 0 (AC3), caption prose edit exit 0 (AC4), @start edit = drift, ORPHAN_CAPTION = exit 1; --write/--check refuse --level/--scope/each other (exit 2); bare draw still stdout; security.yml `architecture-drift` job builds before --check (AC5). RED: ImportError (`codemem.draw.views` absent).

### Sub-step 6.2: [impl] `draw/views.py` registry + `codemem draw --check`
- Status: COMPLETE
- Mode: AFK
- Obligations (M5 §6.8): wire `captions.orphans()` into `--check` as the `ORPHAN_CAPTION` finding (exit 1; `UNKNOWN` never PASS), with `known_paths` from `git ls-files` and `planned_paths` from the active plan's §13 `(new)` entries; writer path guard per 6.1.
- Result Log: Mode: AFK — auto-dispatched. d42cb50: `draw/views.py` — `ViewSpec(output_path, title, generator, level, scope, summary, applies)`, `VIEWS` = readme / component (L2) / plugin-surface (`applies` = `claude-code/` exists), `registered_paths`, `write_views` (all targets guard-checked before any write), `check_views` (DRIFT per stale/missing view, ORPHAN_CAPTION vs `git ls-files`, planned set empty). `cli.py`: `--write` / `--check` mutually exclusive, refuse `--level`/`--scope` (exit 2); `--level` default now None → L0 in stdout mode (bare `draw` unchanged, tested). No/pre-v3/unreadable index: `--check` UNKNOWN exit 0, `--write` exit 1. 17/18 draw-check tests GREEN (AC5 awaits 6.4); full suite 1280 passed / 2 skipped; ruff clean; bandit 2× B404 LOW (subprocess import, same as existing cli.py); lint-imports 4 kept.

### Sub-step 6.3: [impl] generate `docs/architecture/{README,component,plugin-surface}.md`
- Status: COMPLETE
- Mode: AFK
- Obligations (M5 §6.8): render `captions.for_cut()` prose outside the fence through `captions.escape_prose()` (built + tested 61eb4e4); decide and record whether the plugin-surface view (labels `kind:stem`, not paths) takes captions.
- Result Log: Mode: AFK — auto-dispatched. 7f7bfae: fresh `codemem build` (191 files / 1770 symbols / 4168 edges, 0.45s) then `codemem draw --write` → README (11 lines), component (160 lines; L2 100 edges), plugin-surface (299 lines; 4 dangling refs + 7 orphans listed under the diagram). `--check` OK immediately after. Both fences `render_check` = PASS on the real renderer. Captions render inside the captions block via `escape_prose` (`->` → `-&gt;`, displays `->`). Plugin-surface takes no captions by construction (labels `kind:stem`) — recorded context-log 2026-09-24 #5. Full suite 1280 passed (AC5 test deselected until 6.4).

### Sub-step 6.4: [impl] `architecture-drift` job in `security.yml` (Critical-Path)
- Status: COMPLETE
- Mode: HITL
- Result Log: Mode: HITL — Ste approved the job as previewed. 6fab78e: `architecture-drift` appended to security.yml (pinned checkout v4.4.0 / setup-python v5.6.0, py 3.13, uv sync, `codemem build`, `codemem draw --check`; inherits top-level `permissions: contents: read`). YAML job diff before/after: added [architecture-drift], removed [], changed []. AC5 test GREEN (18/18). Local simulation in a fresh `--depth 1` clone of 6fab78e: build 191 files, `--check` OK; a line-2 hand-edit → rc 1 naming the remedy; restored → rc 0. No `.sh` touched in M6 (AC6 shellcheck: nothing to scan).

### Sub-step 6.5: [verify] CI green at this commit; `CRITICAL_PATH_REVIEW`
- Status: COMPLETE
- Mode: HITL
- Result Log: Mode: HITL — Ste: Proceed. CI run 35999835675 on 716de43, commit-specific: 6/6 jobs success incl. `Architecture drift (docs/architecture)`. CRITICAL_PATH_REVIEW written to provenance naming the milestone heading. Known RED 91bdd5f recorded (AC5 test pushed before its job existed).

### Sub-step 6.6: [docs] ADR-0016
- Status: COMPLETE
- Mode: HITL
- Result Log: Mode: HITL — Ste: Accept as drafted. `docs/adr/0016-living-architecture-doc.md` (Accepted) + INDEX row; 0015 stays reserved for M11 (deliberate gap).

### Sub-step 6.7: [release] `scripts/release.sh minor --dry-run`, then cut v0.15.0
- Status: COMPLETE
- Mode: HITL
- Result Log: Mode: HITL — Ste: Cut v0.15.0. Dry-run passed twice (a8812c7 and final tree). `scripts/release.sh minor --headline "living architecture docs generated from the code (codemem draw --write/--check)"` → bump commit b469b08, annotated tag v0.15.0 pushed, GitHub Release published (not draft). Verified: `git describe` = v0.15.0, `importlib.metadata.version('aa-ma')` = 0.15.0, README current-version line, CI on b469b08 6/6 success incl. Architecture drift. `docs/spec` unchanged v0.14.0..v0.15.0 → no install.sh re-run needed.

## Milestone 7: `Dependencies:` grammar + Milestone graph + advisory
- Status: COMPLETE
- Dependencies: None
- Gate: HARD
- Audit-Profile: code-only
- Critical-Path: hook-modification
- Complexity: 60%
- Effort: 1.5
- Goal: Close CONTEXT.md's documented-undelivered Milestone graph promise, with an `M`-prefix-aware resolver.
- Acceptance Criteria: 8 criteria — see plan.md § Milestone 7
- Obligations (M6 §6.8, Ste 2026-09-24): before every push, `scripts/regen-generated.sh` leaves `git diff` reviewed and committed, and `uv run pytest -q` is green (L-025); the architecture-drift and plugin-surface checks move with any change to imports/calls, `claude-code/` references or the install.sh hook table.
- Result Log: COMPLETE 2026-09-24. 8/8 criteria (AC2 amended by Ste: zero corpus findings). `aa_ma.deps` + `python -m aa_ma.deps graph|check|advisory` via `aa_ma_deps`; Milestone graph into /aa-ma-plan §13; advisory in §5.1, never halts (§6.2/full rewritten after §6.8 CRITICAL). aa-ma-gate byte-identical (205 invocations). §6.8: 1 CRITICAL accepted+fixed, 6 WARNING fixed. pytest 1379/2 skipped, bats 210/210. HARD gate approved by Ste.

### Sub-step 7.1: [test] `deps-hazards.md` (`M1.0`, `M2a.1`, `2a`, cross-plan) + naive mutant, RED
- Status: COMPLETE
- Mode: AFK
- Result Log: Mode: AFK — auto-dispatched. `tests/fixtures/deps-hazards.md` (headings `Step M1.0`, `Step M2a.1`, `Milestone 2a`, cross-plan value) + `tests/test_deps.py` (EXPECTED for the 4 hazards, `_naive_strip_m` mutant tied to real heading numbers, 22 lenient legacy forms, corpus ZERO findings per Ste, `Dependencies table:` not-a-field, canonical accept/refuse, graph exact string, §13 lint-clean, advisory exact string, CLI exit codes) + `test_active_plans_canonical.py` (active plans + 2 writer templates must write canonical `Dependencies:`). RED: collection ImportError (`aa_ma.deps`, `CANONICAL_DEPENDENCY_RE` absent). Committed locally, not pushed (L-025).

### Sub-step 7.2: [impl] `deps.py` parser/resolver + `CANONICAL_DEPENDENCY_RE` in `grammar.py`
- Status: COMPLETE
- Mode: AFK
- Result Log: Mode: AFK — auto-dispatched. Impact analysis first (grammar.py pure addition, LOW). `src/aa_ma/deps.py`: `DepRef`, `parse_dependencies`, `resolve`, `dependency_fields`, `check`, `milestone_graph` (round `("…")` nodes — §13 lint reads only `[...]` labels as path claims), `advisory`, `main` (`python -m aa_ma.deps graph|check|advisory`, exit 0/1/2). Number shape reused from `grammar._NUM_S`; one fix during GREEN: a number may end at `-<digit>` so `Milestones 1-3` is a range (corpus `Milestones 1-4` surfaced it). `grammar.CANONICAL_DEPENDENCY_RE` added (pure addition). Live: corpus 324 fields / 61 None / 1 cross-plan ref / 0 findings; this plan's graph 14 nodes 14 edges; `render_check` PASS on 3 graphs (pinned mermaid). tests/test_deps.py 69 passed.

### Sub-step 7.3: [impl] `.importlinter` gains `aa_ma.deps`; `test_leaf_contract.py` green
- Status: COMPLETE
- Mode: AFK
- Result Log: Mode: AFK — auto-dispatched. Before the entry: `test_leaf_contract` FAILED `add to .importlinter render-is-leaf: ['aa_ma.deps']` (AC8 trap fired as documented). After: 1 passed; `uv run lint-imports` 4 kept / 0 broken.

### Sub-step 7.4: [impl] Milestone graph into §13; scribe + template spelling
- Status: COMPLETE
- Mode: AFK
- Result Log: Mode: AFK — auto-dispatched. RED first (`tests/hooks/aa-ma-deps.bats` 127 / cross-plan canonical case failing), then: `aa_ma_deps` launcher in `aa-ma-parse.sh` (locates the plugin checkout like `aa_ma_gate`, which is untouched; listed in the Exports header — the existing guard caught the omission); `/aa-ma-plan` Step 5.5 self-sufficient fence (graph → §13, `check` exit 1 on UNRESOLVED_DEPENDENCY) + canonical-form instruction; `/execute-aa-ma-milestone` §5.1 step 3 advisory fence (always rc 0, "advisory unavailable" with no uv); spec §XI item 13 sentence; scribe (2 lines) + tasks-template (2 comments, 2 examples) canonical spelling; `CANONICAL_DEPENDENCY_RE` gains `<task-slug> Milestone N` (cross-plan). CHANGELOG `## Unreleased` re-created. Regen: component.md +deps.py node, plugin-surface +1 edge (aa-ma-plan → aa-ma-parse.sh), golden +1 edge; `draw --check` OK. Verified: bats 207/207 (4 new, fences executed as shipped), pytest 1364 passed / 2 skipped, ruff clean, shellcheck clean, lint-imports 4/4.

### Sub-step 7.5: [verify] `aa-ma-gate` output byte-identical to the pre-M7 golden
- Status: COMPLETE
- Mode: AFK
- Result Log: Mode: AFK — auto-dispatched. Golden captured before any source edit at `dc4e90e` (33 tasks files incl. fixtures × default/kv/`--milestone N` = 205 invocations, sha256 `5444d16692fe1107`). Post-M7: current code (editable install, `CANONICAL_DEPENDENCY_RE` present) over the identical inputs via a scratch worktree at `dc4e90e` → `cmp` BYTE-IDENTICAL, same sha. `git diff dc4e90e..HEAD -- gate.py enforce.py plan_parsers.py` empty; `aa_ma_gate` launcher unchanged.

## Milestone 8: `PHANTOM_EDGE` sigil grammar
- Status: COMPLETE
- Dependencies: Milestone 2, Milestone 4
- Gate: HARD
- Audit-Profile: code-only
- Complexity: 75%
- Effort: 2
- Goal: The lint gains its first mermaid edge parser and verifies opt-in sigil edges against the derived graph.
- Acceptance Criteria: 6 criteria — see plan.md § Milestone 8
- Obligations (M6 §6.8, Ste 2026-09-24): before every push, `scripts/regen-generated.sh` leaves `git diff` reviewed and committed, and `uv run pytest -q` is green (L-025); the architecture-drift and plugin-surface checks move with any change to imports/calls, `claude-code/` references or the install.sh hook table.

- Result Log: COMPLETE 2026-09-24. 6/6 criteria. Opt-in sigil edges checked against the codemem graph: PHANTOM_EDGE / LABEL_UNKNOWN (exit 1), UNKNOWN informational (planned, no/stale/unreadable index, non-modelled language, outside repo, unparsed form, plugin sigils). codemem submodule import edges (+28 genuine) with receiver-scoped call binding (Ste). Own §13 false claim caught + relabelled (Ste). §6.8: 3 CRITICAL accepted+fixed, 8 WARNING fixed. pytest 1443/2 skipped, bats 210/210. HARD gate approved by Ste.

### Sub-step 8.1: [analysis] `Skill(impact-analysis)` on `mermaid_lint.py`; golden current `lint_text` output
- Status: COMPLETE
- Mode: AFK
- Result Log: Mode: AFK — auto-dispatched. Golden (scratch, pre-change, render stubbed UNKNOWN): `lint_text` over 23 plan/fixture files = 26 findings, sha256 `63dd5fea1b1cf16a`. Impact: mermaid_lint upstream = render/cli.py + tests; contract additive (`LintReport.unknowns`, default ()); plan-verification SKILL must read `file:line: UNKNOWN:` as INFO. Resolver fix (Ste): `from X import name` also resolves `X.name` from `import_aliases` (bare names relative-only, no suffix match); parser records `from . import x` aliases; MEDIUM — more import edges → docs regen, call resolution sees more targets. Overall MEDIUM, cascade planned.

### Sub-step 8.2: [test] `sigil-edges.md` fixture: clean/phantom/LABEL_UNKNOWN/unlabelled/UNKNOWN, RED
- Status: COMPLETE
- Mode: AFK
- Obligations (M5 §6.8): include `classDef start <START_STYLE>` / `class <ids> start` lines in `sigil-edges.md` so the edge parser is shown to ignore them.
- Result Log: Mode: AFK — auto-dispatched. `tests/fixtures/sigil-edges.md` (clean @import + @call, @improt typo, |fork| and bare edges, (new), non-graph .sh, @skill, label without a path, per-fence id scoping, classDef/class lines — obligation met) + `tests/render/test_phantom_edge.py` (AC1–AC6, stale graph, unquoted sigil, inline node decls, CLI UNKNOWN lines exit 0, AC5 glob over every completed plan) + 3 resolver tests in `tests/codemem/test_file_edges.py` (`from . import sub`, `from .store import db`, `from pkg import other` → submodule edges; bare relative name never suffix-matches; imported function adds nothing). RED: 31 lint failures (no `unknowns`/`SIGIL_LABEL_RE`), 2 resolver failures; suffix guard passes (regression pin). Committed locally, not pushed (L-025).

### Sub-step 8.3: [impl] edge parser + `PHANTOM_EDGE` tier
- Status: COMPLETE
- Mode: AFK
- Result Log: Mode: AFK — auto-dispatched. `mermaid_lint.py`: `SIGILS`, `SIGIL_LABEL_RE`, per-fence `_node_labels` (+ `_unwrap`: `(new)`'s `)` survives), `_EDGE_RE` (one edge per line, inline `[...]` on the source), `_sigil_claims` → `PHANTOM_EDGE` / `LABEL_UNKNOWN` findings + `UNKNOWN` notes in new `LintReport.unknowns` (default `()`); graph loaded lazily once per lint via `render.graph` (+ `file_langs`). Evaluability is from the graph's own data: an endpoint is modelled for a sigil iff its `files.lang` has ≥1 such edge (`.sh` indexed for symbols but never an `@import` node → UNKNOWN; an isolated Python file → still PHANTOM). Plugin sigils → UNKNOWN (Ste). CLI prints `file:line: UNKNOWN: reason`, exit from findings only; plan-verification SKILL reads UNKNOWN as INFO. Found + fixed during GREEN: `(new)` stripping bug; `\[+` quadratic (15 s on 50k `[` → linear, regression test). codemem resolver (Ste): `from X import name` resolves `X.name` via `import_aliases` (bare names relative-only), parser records `from . import x` → +26 genuine import edges, cross-file resolved 836→952; docs regenerated (`draw --check` OK). Tests: render 123+ / phantom 39 / codemem 690 pass; full pytest 1421 passed / 2 skipped; bats 210/210; ruff clean; lint-imports 4/4.

### Sub-step 8.4: [verify] glob every completed `*-plan.md`: zero findings on sigil-free files
- Status: COMPLETE
- Mode: AFK
- Result Log: Mode: AFK — auto-dispatched. AC5 test globs every `.claude/dev/completed/**/*-plan.md` (parametrized; skips only files carrying a sigil — none do): zero PHANTOM_EDGE / LABEL_UNKNOWN / UNKNOWN. Golden before/after (scratch, render stubbed): 22 of 24 files byte-identical in findings; changes only (a) this plan's §13 — one real PHANTOM_EDGE `python_ast -->|@import| resolver` (neither imports the other; the two resolver-gap claims now resolve), (b) the new `sigil-edges.md` fixture (linted against its throwaway repo in tests). Ste: relabelled that §13 claim to prose `|feeds|` (plan.md line 279); `aa-ma-lint-views` on this plan → exit 0, render PASS, 2 INFO UNKNOWNs (`.sql` / directory nodes).

## Milestone 9: I/O-boundary view — `Prototype-Required: YES`
- Status: COMPLETE
- Dependencies: Milestone 6
- Gate: HARD
- Audit-Profile: code-only
- Prototype-Required: YES
- Complexity: 85%
- Effort: 3
- Goal: A merged `io.md` with language subgraphs showing where the code touches DB, HTTP, filesystem, subprocess, env and queues.
- Acceptance Criteria: 6 criteria — see plan.md § Milestone 9
- Result Log: COMPLETE 2026-09-25, HARD gate APPROVED (Ste). 6/6 AC: PROTOTYPE REVISE line + exactly two classDefs; 5 langs qualified on fixture; `io` registered, `check_views` unchanged; edge ids in exactly one tier class line, dasharray differs; `open` excluded, fs ≤ 5; `IO_DENSE_BAND repo=medical-research-skills sha=efafac2… edges=289 OVER` reproduced byte-identically. §6.7 PASS; §6.8 PASS_WITH_WARNINGS 0/7/18 (6 W fixed, arrow-fn gap → M13). Commits cb12024 (RED) → 598f749 → 83b6dbf → eb1495f (drift fix, L-026) → c136ac2 (§6.8 fixes). pytest 1485/2 skipped; CI green.
- Obligations (M6 §6.8, Ste 2026-09-24): before every push, `scripts/regen-generated.sh` leaves `git diff` reviewed and committed, and `uv run pytest -q` is green (L-025); the architecture-drift and plugin-surface checks move with any change to imports/calls, `claude-code/` references or the install.sh hook table.

### Sub-step 9.1: [prototype] `Skill(prototype)` on this repo + `medical-research-skills`; `PROTOTYPE` provenance
- Status: COMPLETE
- Mode: HITL
- Result Log: HITL Proceed (Ste). Skill(prototype) LOGIC: single-file demo + throwaway scanner (Python `ast` + alias map; `sg` `has: field: function` for JS/TS/Go), committed on LOCAL-ONLY branch `prototype/diagram-generation-io` @ bdccfda (external paths; push blocked, Ste: never push). Measured non-test edges — aa-ma-forge@d31e301: file 18 qualified / 44 q+bare, L1 10; medical-research-skills@efafac2 (540 py + 19 js on disk; 1893 committed node_modules files deleted in its worktree): file 186 q / 285 q+b, with `open()` 381 / 436, L1 24. Breach is single-language → per-language split cannot fix it. mmdc 11.17: edge ids + `class eN bare` render `stroke-dasharray:4 4`; `:::` is node-only. Verdict REVISE: auto level (file if ≤120 else L1), AC4 → edge ids + class lines, AC5 N=5, AC6 records file-level 285 OVER. plan.md M9 amended. Provenance `PROTOTYPE — Milestone 9 — REVISE` written.

### Sub-step 9.2: [test] per-language sink fixtures (Py/TS/TSX/JS/Go), RED
- Status: COMPLETE
- Mode: AFK
- Result Log: Mode: AFK — auto-dispatched. Commit cb12024. `tests/codemem/test_io_sinks.py` (new): committed fixture tree with one I/O file per v1 language + `opener.py` (open-only) + `repo.py` (bare `self.db.execute`) + `tests/` (excluded); covers the catalogue (load/validate incl. YAML-1.1 `on`, duplicates, https source), `classify`, the Python Name-alias rewrite, the ast-grep `-call` edges (enclosing fn, chained callee dropped), AC2 (5 langs qualified), AC5 (`open` excluded, fs ≤ 5), tier merge, auto level (file vs L1), AC1/AC4 (two classDefs, edge ids in exactly one class line), subgraphs, escaping, AC3 (`io` registered, `--check` DRIFT), band line 120/121, AC6 script byte-identity + read-only. RED: collection ImportError (`codemem.draw.io_sinks` absent). Local commit only until GREEN (L-025). Decisions: PyYAML declared (Ste); AC6 builds from `git archive <sha>` (worktree not sha-pinned; external efafac2 tracks 1918 node_modules files); `match` field dropped from the row shape (call is the only v1 node class).

### Sub-step 9.3: [impl] `ast_grep.py` wrapper + 4 rule YAMLs + `draw/sinks.yaml`
- Status: COMPLETE
- Mode: AFK
- Result Log: Mode: AFK — auto-dispatched. Commit 598f749. `rules/{typescript,tsx,javascript,go}.yml`: `*-call` gains `has: {field: function, pattern: $CALLEE}`. `ast_grep.py`: `_SgMatch.callee`, `parse_sg_output` reads `CALLEE`, `_build_parse_result` records function/method spans and emits one unresolved `CallEdge(src=innermost enclosing callable, dst_unresolved=callee)` per (src, callee); `_callee` drops non-call rules, empty callees and callees chained through a call (`(`), and collapses whitespace. Top-level calls are dropped, as in python_ast. `python_ast._extract_call_names`: a bare-name callee is qualified through `import_aliases` (`from subprocess import run` → `subprocess.run`); resolver lookup name unchanged (`_lookup_name` still yields `run`). `draw/sinks.yaml`: 41 rows / 5 langs / 6 categories / 2 tiers, official-doc `source` per row, no `open`, no Semgrep. `pyyaml>=6,<7` declared in codemem-mcp (uv.lock +2 lines; already resolved at 6.0.3 via fastmcp; Context7 /yaml/pyyaml: safe_load, YAML 1.1 bools). Evidence: live smoke — a.ts → (outer, fs.readFileSync), (outer, fetch), (A.m, this.db.query); m.go → (Load, os.ReadFile); parser/resolver/file_edges suites 96 passed.

### Sub-step 9.4: [impl] `draw/io_sinks.py`, register `io` view, `IO_DENSE_BAND` line
- Status: COMPLETE
- Mode: AFK
- Result Log: Mode: AFK — auto-dispatched. Commit 83b6dbf. `draw/io_sinks.py` (new: catalogue load/validate, classify, `io_edges`, `choose_level`, `band_line`, `band` CLI); `mermaid.io_to_mermaid` + `TIER_STYLE` (exactly two classDefs, edge ids + class lines); `views.VIEWS["io"]` → `docs/architecture/io.md`; `cut.collapse`; `scripts/measure_io_band.sh` (shellcheck clean). GREEN: test_io_sinks 35/35; full `uv run pytest -q` 1478 passed / 2 skipped; ruff clean; lint-imports 4/4 kept; `test_draw_check` registry pin +`io.md` (intended). `scripts/regen-generated.sh` → io.md (43 edges, file level) + component.md gains 2 real call edges (`mermaid → cut`; `tui/__main__ → tui/json_output`, the `dump as json_dump` alias now resolves); `codemem draw --check` OK; mmdc renders io.md (edge styles applied). AC6: `IO_DENSE_BAND repo=medical-research-skills sha=efafac209f… edges=289 threshold=120 verdict=OVER`, byte-identical over 2 runs, external status unchanged → reference.md. Own plan `aa-ma-lint-views` exit 0.

## Milestone 10: `/aa-ma-plan` §13 seeding + Angle 6 coverage rule
- Status: COMPLETE
- Dependencies: Milestone 8
- Gate: HARD
- Audit-Profile: full
- Critical-Path: hook-modification
- Complexity: 55%
- Effort: 1
- Goal: Every new plan ships real, checkable §13 edges, and a plan that creates files it does not draw is caught.
- Acceptance Criteria: 5 criteria — see plan.md § Milestone 10
- Result Log: COMPLETE 2026-09-25, HARD gate APPROVED (Ste). 5/5 AC: 3 undrawn → 3 UNDRAWN_PATH; all drawn → none; grandfathered before 2026-09-11 (derived from COVERAGE_CUTOVER); AC4 proxy scoped to check 8 (amended, Ste) + coverage.py imports no gate; seeded fixture byte-identical to `codemem draw`, zero PHANTOM, every claim evaluated. §6.7 PASS + CRITICAL_PATH_REVIEW; §6.8 PASS_WITH_WARNINGS 0/10/14, all W fixed RED-first. Commits 6c7d3b6 (decisions) → d82d007 (RED) → 484f7d2 (10.2) → 9aaebf1 (10.3) → 05fa09f (10.4) → fd7da0b (CHANGELOG/reference) → 60f608d (§6.8 RED) → f1077cd (§6.8 fixes). pytest 1538 / 2 skipped; CI green.
- Obligations (M6 §6.8, Ste 2026-09-24): before every push, `scripts/regen-generated.sh` leaves `git diff` reviewed and committed, and `uv run pytest -q` is green (L-025); the architecture-drift and plugin-surface checks move with any change to imports/calls, `claude-code/` references or the install.sh hook table.

### Sub-step 10.1: [test] `seeded-plan.md` fixture + `test_angle6_coverage.py`, RED
- Status: COMPLETE
- Mode: AFK
- Result Log: Commit d82d007. Mode: AFK — auto-dispatched. `tests/fixtures/seeded-plan.md`: §13 seed captured from the real `codemem draw --level L2 --scope src/app/a.py --hops 1 --direction both` on a throwaway committed repo (4 nodes / 5 sigil edges incl. `@import`) plus one author `(new)` node. `tests/skills/test_angle6_coverage.py` (new): AC1 (3 undrawn → 3 `UNDRAWN_PATH`), AC2 (all drawn → none), AC3 (2026-09-10 / absent → none; 2026-09-11 fires), finding line = Contract row, 12 exempt rows (Test/Verify, tests/, docs/, root docs, pyproject.toml, package.json, *.lock), directory-node coverage (and a non-component prefix does not cover), `# file:` + braces + comments + comma lists, Contract inside an example fence ignored, no §13 → not this check's finding, CLI `--coverage` opt-in, gate path never yields UNDRAWN_PATH, AC4 proxy (SKILL.md) + coverage module never imports the gate, check 8 appended after 7 with 6/7 literals intact, Phase 4 seeding text, spec item 13, this plan passes its own rule, AC5 (fixture seed byte-identical to the command; zero PHANTOM and every sigil claim evaluated). `tests/codemem/test_draw_cut.py`: +2 (union cut — already green: `cut()` accepts a tuple at runtime; CLI `--scope` repeatable — RED). RED: collection ImportError (`aa_ma.render.coverage` absent) + CLI scope assertion. Local only until GREEN (L-025).

### Sub-step 10.2: [impl] Phase 4 seeding in `aa-ma-plan.md` (Critical-Path)
- Status: COMPLETE
- Mode: HITL
- Result Log: Commit 484f7d2. HITL Proceed (Ste). `claude-code/commands/aa-ma-plan.md`: new **Step 4.2b** (inserted, nothing renumbered) — one `codemem draw --level L2 --scope … --hops 1 --direction both` over every existing path to Modify, pasted unchanged into §13; author adds `(new)` nodes with prose-labelled edges; no-index path prints codemem's reason + remedy; fallback prompt item 13 points at 4.2b. codemem: `--scope` is `action="append"`, passed to `cut()` as a tuple (`cut` already matched any prefix via `str.startswith(tuple)`; type hints widened). Live: fence (shellcheck clean) on the throwaway repo with `--scope src/app/a.py --scope src/app/b.py` → one cut, 4 nodes / 5 edges; with no index → `codemem draw: no index at …; run \`codemem build\`` + the step's message. draw tests 72 passed.

### Sub-step 10.3: [impl] Angle 6 **check 8**, appended, never renumbered
- Status: COMPLETE
- Mode: HITL
- Result Log: Commit 9aaebf1. HITL Proceed (Ste). `src/aa_ma/render/coverage.py` (new): `coverage_findings(plan_text) -> [Finding("UNDRAWN_PATH", line, "<path>: …")]`, `contract_paths`, `drawn_paths`, `COVERAGE_CUTOVER = "2026-09-11"`; reads the fences directly under `#### Contract` (stops at the first line outside a fence — the test caught a later example fence being read), `Create`/`Modify` rows + `# file:` lines, `{a,b}` expansion, comments/commas; exemptions per decision (d). `mermaid_lint.section_13()` extracted and reused by `lint_text` (148 render tests unchanged). `aa-ma-lint-views --coverage` (opt-in; exit 1 on UNDRAWN_PATH). SKILL.md check **8** appended after 7 (6/7 literals intact), WARNING severity (Ste), grandfathering line now names #6/#7/#8. Spec §XI item 13 body gains seeding + coverage sentence (no renumbering). AC4 amended (Ste): proxy scoped to check 8's text — check 2 has called the gate launcher since 38dfc82. This plan's §13: +`coverage.py` (`RCLI -->|"@import"| COV`, `COV -->|"@import"| ML`, both graph-verified), +2 `scripts/` nodes; own plan `aa-ma-lint-views --coverage` clean, render PASS. Real plans: this plan 51 paths / 0 undrawn; mattpocock-trio-adoption 8 / 0; plan-architecture-views (completed, not re-verified) 5 / 1. test_angle6_coverage 32 passed; full pytest 1519 passed / 2 skipped; ruff clean; lint-imports 4/4; bats 210/210; regen: component.md +coverage.py edges, io.md cli fs 3→4 (both real).

### Sub-step 10.4: [verify] `test_plan_verification_angle6.py` + `test_planning_standard_count.py` green
- Status: COMPLETE
- Mode: HITL
- Result Log: Commit 05fa09f. HITL Proceed with dry run (Ste). Pinned suites 9/9 passed (check 6/7 literals, `2026-09-11`, 13-element count across 8 files). Manual `/aa-ma-plan` dry run (scratch, not committed): feature "add --json to aa-ma-lint-views" — Step 4.2b fence extracted verbatim, `--scope src/aa_ma/render/cli.py` on the live index → 8 real sigil edges; Contract Modify cli.py / Create json_report.py / Test …; `--coverage` before author edits → 1 `UNDRAWN_PATH` (json_report.py), rc 1; after adding `J["…/json_report.py (new)"]` + prose edge → clean, rc 0, render PASS, zero UNKNOWN. Check 8 fence run as shipped from /tmp with `AA_MA_ROOT` resolved from the installed SKILL.md symlink → the UNDRAWN_PATH line.

## Milestone 11: §6.7 HARD item + `DIAGRAM_VERIFIED` + ADR-0015
- Status: COMPLETE
- Dependencies: Milestone 10
- Gate: HARD
- Audit-Profile: full
- Critical-Path: hook-modification
- Complexity: 70%
- Effort: 1
- Goal: A §13 sigil edge still `UNKNOWN` at milestone COMPLETE blocks COMPLETE — without touching `gate.py`.
- Acceptance Criteria: 8 criteria — see plan.md § Milestone 11 (AC3 amended, AC8 added 2026-09-25)
- Result Log: COMPLETE 2026-09-26, HARD gate APPROVED (Ste). 8/8 AC: sigil-free → edges=0, exit 0, fence no-op (AC1); broken edge → exit 1 PHANTOM_EDGE (AC2); no index → `codemem build` + index-unknown, fence refuses, `(new)` alone passes; live stale-index refusal on this repo (AC3); gate/enforce/grammar/plan_parsers.py unchanged 6037f62..HEAD, kv corpus diff = own tasks.md only (AC4); 58 protected bats 32/10/16 before/after, 231/231 total (AC5); §1 names `.github/workflows/**` (AC6); gate-fence sha256 17be760b… unchanged (AC7); `sigils:` line on every run (AC8). §6.8: 2 CRITICAL / 5 WARNING / 13 INFO — all fixed RED-first (15b0e8c → ac66bd2); authoring errors refuse, `checked=`, `aa_ma_lint_views` (Ste). DIAGRAM_VERIFIED edges=14 checked=11 phantom=0 unknown=3. Commits: 3008afd, 9125296, 4a6fee5, adc3a0c, fa18c2f, 5d42edd, 15b0e8c, ac66bd2; milestone a0b0f70, provenance 2cd06a5.
- Obligations (M6 §6.8, Ste 2026-09-24): before every push, `scripts/regen-generated.sh` leaves `git diff` reviewed and committed, and `uv run pytest -q` is green (L-025); the architecture-drift and plugin-surface checks move with any change to imports/calls, `claude-code/` references or the install.sh hook table.

### Sub-step 11.1: [test] `test_diagram_verified.bats` against `aa-ma-lint-views`, RED
- Status: COMPLETE
- Mode: AFK
- Result Log: Mode: AFK — auto-dispatched. RED: `tests/hooks/test_diagram_verified.bats` 13/13 fail (3 lint: AC1/AC2/AC3 fail only on the missing `sigils:` line — PHANTOM_EDGE/`codemem build` assertions already hold; 10 execute the second §6.7 fence, still absent). Python 7 RED: `test_cli.py` (edges=0 opt-out; unterminated §13 → `sigils: UNKNOWN`), `test_phantom_edge.py` (fixture counts edges=7 phantom=1 unknown=4; phantoms; no/stale/partial index → index-unknown=3). 71 existing render tests still pass.

### Sub-step 11.2: [verify] capture pre-edit §6.7 awk extraction output
- Status: COMPLETE
- Mode: AFK
- Result Log: Mode: AFK — auto-dispatched. Captured at execute-aa-ma-milestone.md unchanged since 6037f62: extractor `awk '/^### 6\.7 /{f=1} f && /^```bash$/{g=1; next} g && /^```$/{exit} g'` → 105 lines, sha256 17be760b02d79a79b55b0a8423ef204f30ff8b8704fb40b0163b536424299eeb (first line `TASK_DIR=".claude/dev/active/${TASK_NAME}"`, last `echo "ENG-STANDARDS-GATE: PASS (all 5 conditions satisfied)"`). Bats before: aa-ma-gate-python 32, aa-ma-gate-scans 10, execute_aa_ma_milestone_phase_6_8 16 = 58/58; full tests/hooks 210/210. `aa-ma-gate --format kv` over 33 corpus tasks.md: 187 lines (scratch `m11-gate-kv-corpus.pre`).

### Sub-step 11.3: [impl] checklist row + fence **after** the existing gate fence (Critical-Path)
- Status: COMPLETE
- Mode: HITL
- Result Log: HITL Proceed (Ste). GREEN. `mermaid_lint`: `LintReport.sigil_edges` (None when an unterminated fence hides §13), index-class UNKNOWNs coded `UNKNOWN_INDEX` (still printed `UNKNOWN:`), `SIGIL_FINDINGS`; `cli`: `sigils: edges=N phantom=P unknown=K index-unknown=I` before `render:` (`sigils: UNKNOWN (§13 not read)` otherwise); exit codes unchanged. `execute-aa-ma-milestone.md` §6.7: verdict table + second ```bash fence after the Bypass paragraph (self-sufficient; canonical lib-resolution snippet; appends `DIAGRAM_VERIFIED — <heading> — edges=N phantom=0 unknown=K`). `engineering-standards.md`: §5 HARD row; §1 `hook-modification` names `.github/workflows/**` (AC6); absent-field note covers sigil-free §13. Evidence: test_diagram_verified.bats 13/13; pytest 1545 passed / 2 skipped (+7); bats 223/223; 58 protected tests 32/10/16; gate-fence extraction sha256 17be760b… unchanged (AC7); gate kv over 33 corpus files differs only in our own tasks.md PENDING→ACTIVE, gate/enforce/grammar/plan_parsers.py unchanged (AC4); ruff + lint-imports 4/4; regen = stamp-only; plugin-surface golden unchanged; own plan `--coverage` rc 0, `sigils: edges=23 phantom=0 unknown=19 index-unknown=0` (a whole-file grep counts 25 — 2 in AC prose).

### Sub-step 11.4: [verify] 58 bats tests green; extraction output unchanged; `CRITICAL_PATH_REVIEW`
- Status: COMPLETE
- Mode: HITL
- Result Log: HITL Proceed (Ste). 58/58 after the edit (32/10/16, identical to 11.2); gate-fence extraction sha256 17be760b… unchanged. Live on this repo: fence PASS (edges=23 phantom=0 unknown=19) → `touch src/aa_ma/render/graph.py` → BLOCKED rc 1 naming `codemem build` → rebuild (0.66s) → PASS; outputs in provenance.log. Live run exposed a false message ("0.44s on this repo" ships to consumer repos) — removed. `CRITICAL_PATH_REVIEW — Milestone 11: … — hook-modification` written.

### Sub-step 11.5: [docs] ADR-0015
- Status: COMPLETE
- Mode: HITL
- Result Log: HITL Proceed, status Implemented (Ste). `docs/adr/0015-diagram-as-acceptance-criterion.md` opens with "HARD ≠ `gate.py`", weighs the eighth-gate-question option, records the verdict table and both 2026-09-25 amendments (index-only UNKNOWN refuses; count from the lint, 25-vs-23 measured); `docs/adr/INDEX.md` row added. CHANGELOG Unreleased entry; reference.md M11 facts.

## Milestone 12: Explorer + Node CI job
- Status: COMPLETE
- Dependencies: Milestone 3
- Gate: HARD
- Audit-Profile: full
- Critical-Path: hook-modification
- Prototype-Required: YES
- Complexity: 80%
- Effort: 2.5
- Goal: `aa-ma-render --explorer` produces a self-contained, clickable, level-deriving HTML file in `build/`.
- Acceptance Criteria: 8 criteria — see plan.md § Milestone 12
- Result Log: COMPLETE 2026-09-26, HARD gate APPROVED (Ste). 8/8 AC: `aa-ma-render --explorer` → build/explorer.html exit 0 (AC1, AC2a); compute() differs L0 vs L2 under node --test (AC2b); Ste's browser drill, console clean (AC2c); strict + _CSP unchanged, inline script hash-allowed by its CSP (AC3); MERMAID_VERSION defined once, absent from explorer.js (AC4); pytest + node --test read the shared fixture, explorer-contract CI job green (AC5); node_id mutation → JS contract red (AC6); build/ ignored, nothing tracked (AC7); CSP composed by html.csp(), render golden unchanged (AC8). PROTOTYPE PROCEED (8e2a31f, local branch). §6.8: 1 CRITICAL (TDD timestamp tie) disputed, 8 WARNING + cheap INFOs fixed RED-first (fc5a270 → 3635168). DIAGRAM_VERIFIED edges=13 checked=13 phantom=0. Commits: 8360800, 1d47622, 842555f, 68be4b1, 7b9295e, d4df253, fc5a270, 3635168, 87eaa31.
- Obligations (M6 §6.8, Ste 2026-09-24): before every push, `scripts/regen-generated.sh` leaves `git diff` reviewed and committed, and `uv run pytest -q` is green (L-025); the architecture-drift and plugin-surface checks move with any change to imports/calls, `claude-code/` references or the install.sh hook table.
- Carry-forward (M9 §6.8, 2026-09-25): `edges.dst_unresolved` holds callee text taken verbatim from untrusted source files. If the explorer ever displays callees, pass them through `codemem.draw.mermaid.escape_label` (or the HTML equivalent) first.

### Sub-step 12.1: [prototype] delegated listener against real mermaid SVG; `PROTOTYPE` provenance
- Status: COMPLETE
- Mode: HITL
- Result Log: HITL Proceed; verdict PROCEED (Ste). Branch `prototype/diagram-generation-explorer` @ 8e2a31f, local only (build.py → demo.html; drive.py = headless Chromium via `uv run --no-project --with playwright`). Mermaid 11.17.2 node = `<g class="node" id="<renderId>-flowchart-<nid>-<i>">`, no `data-id`; one delegated listener + `/flowchart-(n[0-9a-z]+)-\d+$/` maps back; survives re-render; L0 3 → L1 2 → L2 26 nodes by real clicks; 0 CSP violations. JS nid matches draw-node-ids.json (`src`@L0 = n1wgktcl). Explorer init needs `startOnLoad:false`. PROTOTYPE provenance written. (Prototype commit bypassed hooks — L-027.)

### Sub-step 12.2: [test] `explorer_contract.test.mjs` + `test_explorer_fixture.py` on the shared fixture, RED
- Mode: AFK
- Obligations (M5 §6.8): caption matching must equal Python's `captions.for_cut`/`start_ids` — embed per-level `for_cut` output in the JSON (preferred, no JS re-implementation) or add caption cases to the shared fixture; the JSON island is `captions.json_island()` (built + tested 61eb4e4: no `<` `>` `&` survive a `</script>` caption); prose via `textContent`, never `innerHTML`. → Captions DEFERRED from the explorer (Ste 2026-09-26; `aa_ma` may not import codemem); the island escaping rule (no `< > &`) still applies, restated in explorer.py.
- Status: COMPLETE
- Result Log: Mode: AFK — auto-dispatched. Fixture: 183 L2 rows of draw-node-ids.json gain `collapse: [L0, L1]` from `codemem.draw.cut.collapse` (test_draw_cut 31/31 still green). RED: `tests/render/test_explorer_fixture.py` 11 fail / 2 pass (collapse pin + build/ ignored already true); `tests/render/explorer_contract.test.mjs` 10/10 fail — each on its own assertion (stubs `explorer.py`/`explorer.js` raise, so no import-time errors).

### Sub-step 12.3: [impl] `render/explorer.py` + `explorer.js` + `--explorer` flag
- Status: COMPLETE
- Mode: AFK
- Result Log: Mode: AFK — auto-dispatched. GREEN. `html.py`: `sha256_b64()` + `csp(*hashes)`; `_CSP = csp(_INIT_SHA)` byte-identical (golden green). `explorer.py`: `build_explorer(repo_root) -> (page, stale)` over graph.py (import + call edges), JSON island with `< > &` escaped, one inline script (explorer.js, refused at import if it holds a script tag), CSP composed by `csp(sha256_b64(js))`, `MAX_EDGES = 500` pinned to codemem's by a test; missing/too-old index → ValueError naming `codemem build`. `explorer.js`: `nid`, `collapse`, `isTest`, `escapeLabel`, `nodeIdOf`, `compute` (CJS-exported for node --test) + a guarded browser section (one delegated listener, trail with up/top, tests toggle, stale banner, `startOnLoad:false`, `securityLevel: "strict"`). CLI: `aa-ma-render --explorer [--repo-root R] [--out DIR]` → DIR/explorer.html (DIR default build), exit 2 on missing/old index (nothing written), stderr warning on stale; exclusive with markdown sources. Evidence: test_explorer_fixture 13/13, node contract 10/10 (run from pytest), render 182, full pytest 1572 passed / 2 skipped; ruff + lint-imports 4/4; wheel ships explorer.js; live `aa-ma-render --explorer` on this repo (45 KB) driven headless: L0 → src/ L1 → src/aa_ma/ L2 (30 nodes/77 edges) → file neighbourhood → up → top → tests on; 0 console/CSP errors. Regen: component view gains explorer.py edges, io view cli.py fs 4→5. Own §13: explorer (new) marks dropped → `edges=14 checked=14 phantom=0`.

### Sub-step 12.4: [impl] node job in `security.yml` (Critical-Path)
- Status: COMPLETE
- Mode: HITL
- Result Log: HITL Proceed (Ste: setup-node v7.0.0, Node 24). `explorer-contract` job appended to security.yml (7b9295e, 32 lines, additive only): checkout/setup-python pins reused, `uv sync`, `codemem build && aa-ma-render --explorer --out build`, `actions/setup-node@820762786026740c76f36085b0efc47a31fe5020 # v7.0.0` (node-version 24, package-manager-cache false per its README), `EXPLORER_HTML=build/explorer.html node --test tests/render/explorer_contract.test.mjs`. CI run 36247462754: all 7 jobs success; the new job 10 pass / 0 fail.

### Sub-step 12.5: [verify] manual browser drill observation; `CRITICAL_PATH_REVIEW`
- Status: COMPLETE
- Mode: HITL
- Result Log: Ste in a desktop browser with DevTools: drill works (level/scope change on node click; up/top/tests), console clean — AC2(c), recorded in provenance. AC6 by mutation (seed 7→8 → test_draw_cut red; fixture regenerated → JS node-id test red). `CRITICAL_PATH_REVIEW — Milestone 12: …` written (security.yml additive, permissions unchanged, sha-pinned; html._CSP byte-identical).

## Milestone 13: MCP `diagram` tool + consumer rewire — `Prototype-Required: YES`
- Status: ACTIVE
- Dependencies: Milestone 6
- Gate: HARD
- Audit-Profile: code-only
- Critical-Path: hook-modification
- Prototype-Required: YES
- Complexity: 65%
- Effort: 2
- Goal: The third door works, and every skill that names a graph backend names the right one.
- Acceptance Criteria: 9 criteria — see plan.md § Milestone 13
- Obligations (M6 §6.8, Ste 2026-09-24): before every push, `scripts/regen-generated.sh` leaves `git diff` reviewed and committed, and `uv run pytest -q` is green (L-025); the architecture-drift and plugin-surface checks move with any change to imports/calls, `claude-code/` references or the install.sh hook table.
- Carry-forward (M8 §6.8, 2026-09-24): if the index gains plugin-surface edges here, delete `_PLUGIN_SIGILS` / `_PLUGIN_REASON` in `src/aa_ma/render/mermaid_lint.py` together and evaluate `@skill/@command/@agent/@hook` like `@import`.
- Carry-forward (M12 §6.8, Ste 2026-09-26): tighten html.py's CSP — `script-src` to the exact mermaid bundle URL (not the whole cdn.jsdelivr.net host), add `base-uri 'none'; form-action 'none'`; regenerate tests/golden/render_plan_ok.html; the explorer inherits it via `html.csp()`.
- Carry-forward (M12, Ste 2026-09-26): explorer captions — JS `_names`/`@start` rule pinned by caption cases in the shared fixture; `&` → `#38;` in both escape_label twins if names ever carry entities.
- Carry-forward (M11 §6.8, 2026-09-26): codemem `file_edges` holds module-level imports only — a function-local import (`codemem/cli.py` → `draw.views`) is absent, so a true `@import` sigil on it reads `PHANTOM_EDGE` and the §6.7 diagram item refuses. Record function-local imports (flagged, e.g. `lazy=1`) and re-lint every plan's §13 after; until then ADR-0015 says to label such edges in prose.
- Carry-forward (M9 §6.8, Ste 2026-09-25): TS/TSX/JS calls inside arrow functions / function expressions bound at module scope (`const h = async () => fetch()`) produce no call edge, so io.md undercounts JS/TS I/O (disclosed in its prose). Add them as callables (`variable_declarator` → `arrow_function` | `function_expression`) with a fresh impact analysis: they become symbols, changing component view, dead_code and who_calls for every TS/JS repo. Re-measure the polyglot band after.

### Sub-step 13.1: [prototype] measure L0-L3 on `medical-research-skills`; `PROTOTYPE` provenance
- Status: COMPLETE
- Mode: HITL
- Result Log: Ste: Proceed. Scratch index from `git archive efafac2` (26 s, 2481 files, 1918 vendored node_modules; 2461 under one top-level dir, skills at depth 3). Whole repo, tests excluded: L0 0n/0e, L1 0n/0e (every edge is intra-dir at depth ≤2), L2 69n/97e 9099 mermaid chars (json 9692), L3 calls 522n/500e dropped 2793, 77520 chars — budget 8000 tokens = 32000 json chars. Prototype `scripts/PROTOTYPE_mcp_diagram.py` compared the planned collapse with a guarded one: scoped L3 `scientific-skills/Academic Writing/` (482 edges) collapses to an EMPTY L2 under the plan; guarded stops and truncates L3 to 188 edges / 31898 json chars. aa-ma-forge @ main: identical under both (L2 54n/141e json 8164; L0/L1 3 edges). Verdict PROCEED with amendment (Ste): guarded collapse; default level L2 (L1 empty on MRS). Branch `prototype/diagram-generation-mcp` @ 99b0c36, local only. PROTOTYPE provenance written.

### Sub-step 13.2: [test] `test_mcp_diagram.py` + update tool-count pins 12 -> 13, RED
- Status: COMPLETE
- Mode: AFK
- Result Log: Mode: AFK — auto-dispatched. RED 91562fe (tests only, L-028): tests/codemem/test_mcp_diagram.py (17: default L2 + all keys, AC2 L2→L1 collapsed_from, guarded no-empty-collapse, L0 still over → truncate at L0, sorted-prefix determinism, AC3 counts == mermaid over/under budget ×3 graphs, scope/hops, L3, bad args, pre-v3 names `codemem build`); test_mcp_server.py pins 12→13 + `diagram` in the name set; integration `_TOOL_CASES` + ("diagram", {}). 20 failed / 26 passed for the right reasons (AttributeError, `Unknown tool: diagram`).

### Sub-step 13.3: [impl] `diagram()` + registration in `claude-code/codemem/mcp/server.py`
- Status: COMPLETE
- Mode: AFK
- Result Log: Mode: AFK — auto-dispatched. `mcp_tools.diagram()` (reuses `_exceeds_budget`/`_DEFAULT_BUDGET`, `cut`/`from_edges`/`to_mermaid`; binary-search truncation) + server.py registration (13 canonical). 46/46 MCP tests; full pytest 1596 passed / 2 skipped; ruff clean; lint-imports 4 kept. Live over the MCP protocol (fastmcp Client, in-memory) on the MRS scratch index: 15 tools listed; `{}` → L2 69n/97e; `L3` → L2 collapsed_from L3; scoped L3 Academic Writing → L3 188e dropped 294 json 31913 ≤ 32000; `L1` → 0/0. AC1: `scripts/measure_mrs.sh` → 4 MRS_BUDGET lines, second run `cmp` byte-identical; lines + sha in reference.md. Tool counts 12→13 in SECURITY.md, claude-code/codemem/README.md (+ diagram table), packages/codemem-mcp/{README.md,pyproject.toml}, docs/codemem/install-zero-config.md. §13: `MCP -->|imports inside a function| CUT/MM`, `MMRS` node; lint sigils edges=13 checked=13 phantom=0. regen: stamps only.

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
- Obligations (M6 §6.8, Ste 2026-09-24): before every push, `scripts/regen-generated.sh` leaves `git diff` reviewed and committed, and `uv run pytest -q` is green (L-025); the architecture-drift and plugin-surface checks move with any change to imports/calls, `claude-code/` references or the install.sh hook table.
- Carry-forward (M8 §6.8, 2026-09-24): document `PHANTOM_EDGE` / `LABEL_UNKNOWN` / sigil `UNKNOWN` also in `claude-code/rules/engineering-standards.md` ("Diagram maintenance" bullet names only STALE_PATH) and `docs/adr/0010-architecture-views-and-render.md`, beside the spec/README/CHANGELOG already listed.

### Sub-step 14.1: [docs] CONTEXT.md: 7 glossary terms
- Status: PENDING
- Mode: HITL
- Result Log: [pending]

### Sub-step 14.2: [docs] spec §XI body (no renumbering), quick-ref, foundations
- Status: PENDING
- Mode: AFK
- Result Log: [pending]

### Sub-step 14.3: [docs] hardcoded counts in the 5 files CLAUDE.md names + `claude-code/rules/engineering-standards.md:44` (41 = 17/20/4 is stale; prefer citing the generated `docs/architecture/plugin-surface.md` / the M4 golden over re-hardcoding numbers); `Skill(doc-drift-detection)` clean
- Status: PENDING
- Mode: AFK
- Result Log: [pending]

### Sub-step 14.4: [release] dry-run, then cut v0.16.0
- Status: PENDING
- Mode: HITL
- Result Log: [pending]
