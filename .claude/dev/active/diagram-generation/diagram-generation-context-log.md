# diagram-generation Context Log

## [2026-09-22] Initial Context

**Feature request:** `/aa-ma-plan --from-map diagram-generation` — seeded from a
cleared charting map (19/19 tickets RESOLVED, fog empty, guard `clear:
tickets=19`). The map's Destination is the request; charting had already run 15
grill rounds and 4 research dispatches, so Phase 2 started from *Decisions so far*
rather than from zero and Phase 3 was skipped (`reason=map_research_current`).

**Decisions taken during planning** (the map did not settle these):

1. **Plan shape — one plan, spine-first.** 14 milestones, ordered so M1–M6
   (file_edges → sqlite seam → `codemem draw` → `docs/architecture/` + CI drift job)
   is a releasable increment at `v0.15.0`, with `v0.16.0` at completion. Two
   plans were considered and rejected: the tickets are too interdependent to split
   cleanly and the tail risks never being planned.
2. **`.codemem/` in a consumer repo's `.gitignore`** — append idempotently if
   absent, declared up front in the skill's write footprint. Ticket 9 had already
   accepted an uninvited `docs/architecture/` diff; this is smaller.
3. **Node in CI** — added, so Ticket 11's Python↔JS contract fixture is real rather
   than decorative.
4. **Cross-plan `Dependencies:` exemption** — a slug-shaped hyphenated token
   immediately preceding the reference marks it cross-plan. Keeps the resolver pure;
   no filesystem lookup.
5. **MCP diagram budget** — measure on `medical-research-skills` (2452 files, 16×
   this repo) *first*, then reuse codemem's `_DEFAULT_BUDGET`/`_truncate`, auto-collapse
   on overflow, always report counts. Ticket 17 deliberately shipped no default.
6. **Glossary** — all 7 candidate terms land in CONTEXT.md at M14. *Explorer* is
   load-bearing: CONTEXT.md defines *Render* as markdown-sourced, which the explorer
   is not.
7. **Three ADRs** — 0014 (graph source + seam + doors), 0015 (diagram as acceptance
   criterion, and why `gate.py` is untouched), 0016 (living doc + CI contract).
8. **`--check` uses a view registry**, not Ticket 8's hardcoded 4-path list. Refines
   Ticket 8 without reopening it: `io.md` registering at M9 stops being a contract
   change, so the spine can ship at M6 without a 3-of-4 gap.
9. **Prototype-Required** — M9 and M13 at planning time; **M12 added during
   verification** once the prototype claim was found false (below).

## [2026-09-22] Phase 4.5 verification — 22 CRITICALs, 8 revisions

Automated mode, 6 angles. The plan went 973 → 1530 lines. Full findings in
`diagram-generation-verification.md`. The five that changed the plan's substance:

- **Tests were written to `packages/codemem-mcp/tests/`, which does not exist.**
  codemem tests live at `tests/codemem/`, and CI runs `pytest tests/codemem/` plus a
  catch-all that explicitly `--ignore`s it. Nothing in CI reaches `packages/`. Local
  `pytest` *would* collect them, so seven milestones of tests would have passed
  locally and never run in CI — a silent gap, not a loud one.

- **Gate fields lived only in `plan.md`.** `aa-ma-gate` takes one positional
  argument, `tasks_md`. Three `Prototype-Required: YES` gates and six
  `Critical-Path` reviews would have passed green while enforcing nothing. §2a is
  now the mandatory transcription table, and it was verified by asking the gate
  rather than by reading the file.

- **The `edges` composite PK never de-duplicates, and the plan was about to copy
  it.** Measured: 6516 rows / 3258 distinct, histogram `[(2, 3258)]` — every edge
  stored exactly twice, zero singletons. SQLite treats NULLs as distinct in the
  backing unique index and the two `dst` columns are mutually exclusive by design,
  so the constraint never matches and `INSERT OR IGNORE` suppresses nothing.
  `file_edges` now uses two partial unique indexes instead (verified: 3 identical
  inserts → 1 row). The stored defect is recorded in `TODOS.md`; `SELECT DISTINCT`
  in both `graph.py` and `draw/cut.py` contains it at all three doors.

- **The prototype never validated the drill listener.** Charting recorded A3 as
  "validated by `prototype/diagram-generation-3/demo.html`". It is not:
  that file has three handlers, all `b.onclick` on control-panel buttons
  (`:158-160`), and zero `addEventListener` / `.closest(` / SVG node handling. A
  false *positive* in the trust record is worse than a false negative, because
  nothing downstream re-checks it. M12 now carries `Prototype-Required: YES`.

- **Element #2 was effectively absent.** Milestones were the smallest unit, while
  §8 and two M4 criteria referenced sub-steps defined nowhere. Caught only by the
  context-free fresh-agent angle — every other reviewer knew AA-MA puts sub-steps in
  `tasks.md` and so read past the gap. 63 sub-steps added, TDD-ordered, 44 AFK / 19 HITL.

**Two agent CRITICALs were refuted by testing**, both failing the same way — reading
a comment as if it were behaviour. `.importlinter`'s "shared descendants" note does
not forbid `source_modules = aa_ma` here (verified: `4 kept, 0 broken`); its caveat
applies only when source and forbidden share a root.

**One refutation of mine was itself wrong.** I claimed `schema.sql` had no
`PRAGMA user_version` and that a v2 build could not downgrade a v3 DB. Line 17 *is*
`PRAGMA user_version = 1;`, and the downgrade reproduces (3 → 2, table intact). My
error was checking `migrate()` in isolation when `ensure_schema()` is the production
path — the observation was true and the conclusion false. M1 now carries the
reproduced transcript, an `apply_schema()` version guard, and `Critical-Path: data-xform`.

## [2026-09-22] Decision: dogfooding forced M10's coverage rule to be redesigned

M10 proposed an Angle 6 rule — "every file path in a milestone's `#### Contract`
block must appear as a §13 node". Run against this plan it flagged **66 of 92
paths**. Narrowed to `Create`/`Modify` outside `tests/` and `docs/` it was still 24.
The rule now uses **directory-node collapse** — the same mechanism M3's emitter
already builds — plus explicit `Test`/`Verify` and `tests/`/`docs/` exemptions. The
plan satisfies its own rule: 48 in-scope paths, 0 uncovered, 57 nodes.

A rule that fails its own author's plan gets `AA_MA_HOOKS_DISABLE=1`'d in week two,
and then protects nothing.

## [2026-09-22] Decision: widen `hook-modification` to cover CI workflows

M2, M6 and M12 carry `Critical-Path: hook-modification` solely for editing
`.github/workflows/security.yml`, which the engineering-standards §1 table does not
list. The gate accepts it — `plan_parsers` validates the *value* against an enum and
says nothing about scope — so this was doctrine drift, not a gate failure. Approved
with Ste 2026-09-22: M11 amends the §1 row to name `.github/workflows/**`, aligning
the shipped rule with the practice the charting map already established. Dropping
the field from three milestones was the alternative and was rejected — it would lose
the `CRITICAL_PATH_REVIEW` evidence step on every CI change.

_Updated via context compaction as the task progresses._

## [2026-09-24] Milestone 1 execution decisions
- **Validator pre-exec WARN** (0 FAIL): fixed plan.md AC3 self-contradiction (`CHECK (kind IN ('import'))` parenthetical removed — the Contract deliberately has no kind CHECK); widened Sub-step 1.1 to own all `file_edges` tests (AC5/5b/7 + dedup), closing the TDD gap before 1.6.
- **Invalidation lives in `resolver.py`, not `incremental.py`** (deviation from the Files list): both writers (`build_index`, `refresh_index`) call `resolve_cross_file_edges`, so one explicit `DELETE FROM file_edges WHERE src_file_id=?` covers both. `incremental.py` unchanged.
- **Import resolution is DB-wide** (`SELECT path, id FROM files`), not parse-set: `refresh_index` passes only dirty files, and an import of an unchanged file must resolve. After impl-review, call-edge resolution reuses the same targets — on a full index identical (1227=1227); on incremental refresh, call edges into unchanged files now resolve (previously they could not). Intended correction.
- **Callee lookup rule** (`_lookup_name`): dotted callees match on last segment only for bare names, single-Name receivers (pre-M1 behaviour), or receivers that are imported modules / alias targets. `self.conn.execute` stays unresolved — cannot bind to an unrelated `execute`. Chains through calls/subscripts are still not emitted.
- **Intended output-shape change**: `edges.dst_unresolved` now holds dotted, alias-qualified callees. No query tool reads the column; `codemem build` unresolved count shifts upward (2109 -> 2349 on this repo).
- **Known gap (pre-existing class)**: WAL replay-from-scratch does not re-run the resolver, so `file_edges` (like cross-file call edges) is empty until the next build. Pending WAL journals written at v2 hit ReplayConflict after the 3 bump — rebuild instead.
- **`line` column** left NULL (`ParseResult.imports` carries no line numbers); populate if a consumer needs it.

## [2026-09-24] Milestone Completion: codemem `file_edges` (schema v3) + qualified callees
- Status: COMPLETE (pending HARD-gate approval below)
- Key outcome: schema v3 `file_edges` persists 694 import edges on this repo (162 resolved, 0 dups); `apply_schema()` no longer downgrades newer DBs; call edges keep dotted, alias-qualified callees without changing the resolved call graph.
- Artifacts: storage/db.py, parser/python_ast.py, resolver.py; tests/codemem/test_file_edges.py (new), test_resolver.py, test_schema_v2.py; docs/codemem/{migration-from-index,ARCHITECTURE}.md; impl-review.md
- Tests: 1122 passed / 2 skipped (baseline 1101); ruff clean; tests/codemem/ collected by CI

## [2026-09-24] GATE APPROVAL: Milestone 1: codemem `file_edges` (schema v3) + qualified callees
- Gate: HARD
- Approved by: Ste (Stephen J Newhouse)
- Criteria verified: 8/8
- Decision: APPROVED

## [2026-09-24] Milestone 2 execution decisions
- **Tier 2 validation not re-run**: the pre-exec validator ran this session (WARN, 0 FAIL) over the whole plan; artifacts changed only by M1 sync since.
- **Staleness counts deleted files** (beyond plan's mtime-only definition): a vanished indexed file is equally out of date.
- **STALE is advisory**: the handle keeps its read-only connection; callers decide. Caller owns `conn`.
- **`call_edges` drops same-file edges**: a file graph has no self-loops.
- **Scope — `tests/codemem/test_install_and_cli.py` edited** (not in Files list): forced by the new contract — it asserted the total `Contracts: 3 kept`; now asserts contracts by name + `\b0 broken`. Exactly the total-vs-name hazard plan AC4 warned about; it would have turned CI red.
- **`.importlinter` header corrected**: it claimed CI ran `lint-imports`; it ran zero times until this milestone.
- **§6.8 CRITICAL accepted and fixed** (never-raises breach) — see impl-review.md. Hardening beyond the finding: path confinement (security WARNING), `trusted_schema = OFF`, control-char escaping, per-row mtime handling.
- **ADR-0014 Status: Accepted** (Ste, HITL 2.4) — flip to Implemented when M3/M5 consumers ship.
- **Deferred, out of scope**: `security.yml` lacks a top-level `permissions: contents: read`; actions pinned by tag not SHA (pre-existing).

## [2026-09-24] Milestone Completion: `aa_ma.render.graph` sqlite seam + import contract + ADR-0014
- Status: COMPLETE (pending HARD-gate approval below)
- Key outcome: aa_ma reads codemem's v3 graph read-only through a never-raising stdlib-sqlite3 seam; `aa-ma-never-imports-codemem` is enforced in CI for the first time along with the 3 pre-existing contracts.
- Artifacts: src/aa_ma/render/graph.py; tests/render/test_graph.py; tests/codemem/test_file_edges.py (+seam-on-real-index); tests/codemem/test_install_and_cli.py; .importlinter; .github/workflows/security.yml; docs/adr/0014-derived-architecture-views.md; docs/adr/INDEX.md; docs/codemem/ARCHITECTURE.md
- Tests: 1146 passed / 2 skipped; ruff clean; lint-imports 4 kept / 0 broken

## [2026-09-24] GATE APPROVAL: Milestone 2: `aa_ma.render.graph` sqlite seam + import contract + ADR-0014
- Gate: HARD
- Approved by: Ste (Stephen J Newhouse)
- Criteria verified: 7/7
- Decision: APPROVED

## [2026-09-24] Milestone 3 decisions (Ste, AskUserQuestion)
- **Edge kinds: import ∪ call, each labelled with its kind** — `--kind import|call|both`, default `both`. Serves Ticket 14's `@import`/`@call` seeding; L3 (symbol level) is call-only by nature. Measured at HEAD (tests excluded): call 31/40, import 42/56, both 43/67; L2 render/: call 6/7, import 5/4, both 6/7.
- **Tests excluded at EVERY level by default** (plan invariant kept). Discovered: Ticket 3's L0 4/3 and L1 10/9 were measured WITH tests (without, L0 on call edges is 0/0). `--include-tests` reproduces them; fidelity tests pin all bands on the prototype's frozen graph (`tests/fixtures/draw-prototype-graph.json`).
- **AC numbers are repo-state-dependent**: plan ACs 2/3 (L2 5/4, raw 27->96) are the prototype's c49d084 figures; the repo has grown (HEAD call raw 40 -> 175 with tests). They are verified as fidelity on frozen data; HEAD figures are recorded as observations, not asserted.
- **Level mapping (my call, recorded)**: L0 = dir depth 1; L1 = dir depth 2 (Ticket 3 listed "10/9 · 13/11" for depth 2/3 — depth 2 is the first listed and the natural "package" level); L2 = files; L3 = symbols (`path::symbol_path` from scip_id).
- **Scope at L0/L1** = the prototype's "hybrid" arm: file-level neighbourhood first, then collapse.
- **L2 hops>1 diverges from the prototype on purpose**: prototype walked the SYMBOL graph then projected; the port walks the FILE graph (import edges exist only at file level). Identical at hops=1 (verified 5/4).
- **Test path** = any path component named `tests` (prototype: `^tests/`; generalised for consumer repos with nested test dirs).
- **node_id** = prototype `nid` hash over `L<level>:<name>`, including its non-BMP quirk (charCodeAt(0) per code point = high surrogate). Fixture generated by independent JS.

## [2026-09-24] Sigil grammar correction (Ste, AskUserQuestion) — affects M5, M8, Ticket 14 seeding
- **Finding:** Ticket 5's `A -->|@import| B` is a mermaid 11.17.2 PARSE ERROR (the pinned `MERMAID_VERSION`): `@` after the pipe lexes as mermaid 11's edge-ID token (`LINK_ID`). Bisected with a working renderer: bare `|@import|` rc=1; `|"@import"|`, `-- "@import" -->`, `|#64;import|`, `|import|` all rc=0.
- **Why unseen until now:** every render check returned UNKNOWN — the local puppeteer cache held EMPTY browser dirs (failed installs; no `unzip` on the machine). Fixed locally by extracting chrome-headless-shell 152.0.7977.75 into `~/.cache/puppeteer` with Python zipfile. L-012 (UNKNOWN is never PASS) held; the gap was that nothing ever produced a non-UNKNOWN verdict.
- **Decision: QUOTED sigil `A -->|"@import"| B`.** `codemem draw` emits it; M5's PHANTOM_EDGE parser must read the quoted form. The plan's §13 had 24 bare sigils — quoted; `aa-ma-lint-views` render: FAIL -> PASS. reference.md item 5 updated. The charting map is the historical record and is left as written.

## [2026-09-24] CORRECTION — measurements taken on a corrupted live index
- The live `.codemem/index.db` was corrupted by the build_index FK-OFF defect (fixed in M3 §3.5): 4462 symbols vs 1649 real, 2819 misattributed to the wrong file, producing impossible edges (e.g. `plan_markers/parser.py -> render/cli.py`, forbidden by render-is-leaf).
- **Invalidated figures:** the "HEAD" numbers quoted in the M3 edge-kind question (call 31/40, import 42/56, both 43/67; L2 render call 6/7, both 6/7) and M2's recorded live counts (import_edges 163, call_edges 175). The decisions made on them (edge kinds = both, tests excluded) stand on their own merits — Ste's choice did not hinge on the magnitudes.
- **Corrected (healed index @ M3):** call-only L2 render 5/4 and raw -tests 25/27 — identical to the prototype; M2 seam live: import_edges 171, call_edges 107. M1 figures (694 import rows, 1784 dotted callees) were measured on fresh scratch builds and stand.
- Lesson: a scratch fresh build is the only trustworthy measurement base until an index is known clean.

## [2026-09-24] Milestone Completion: `codemem draw` emitter, layered cuts L0–L3
- Status: COMPLETE (pending HARD-gate approval below)
- Key outcome: `codemem draw` emits deterministic, renderer-verified mermaid at L0–L3 over import ∪ call edges with quoted kind sigils; the port reproduces every prototype band on the prototype's frozen data. Two pre-existing defects surfaced and fixed on the way: build_index misattributing symbols across rebuilds (§3.5) and the unparseable bare-sigil grammar (plan §13 corrected).
- AC note: AC2's "5 nodes / 4 edges" holds for `--kind call` (the measured configuration); the default `--kind both` gives 5/8 (the same 4 file pairs, each carrying @import and @call). AC3's 27 -> 96 holds on the frozen prototype data; the live repo has grown to 27 -> 107.
- Artifacts: codemem/draw/{__init__,cut,mermaid}.py; cli.py; indexer.py; tests/codemem/{test_draw_cut,test_draw_mermaid,test_indexer,test_file_edges}.py; tests/fixtures/draw-{node-ids.json,node-ids.gen.mjs,prototype-graph.json}; claude-code/codemem/commands/codemem.md; docs/codemem/migration-from-index.md; src/aa_ma/render/html.py (comment); plan.md (§13 sigils, API)
- Tests: 1195 passed / 2 skipped; ruff clean; 4 contracts kept
- Out-of-band (Ste request, [ad-hoc]): CI least-privilege + SHA pinning, 75f8d09, CI green.

## [2026-09-24] GATE APPROVAL: Milestone 3: `codemem draw` emitter, layered cuts L0–L3
- Gate: HARD
- Approved by: Ste (Stephen J Newhouse)
- Criteria verified: 5/5
- Decision: APPROVED

## [2026-09-24T11:16:19Z] Compaction Summary (auto-generated by hook)
- Active step at compaction: Sub-step 4.1: [measure] re-measure the surface; identify the 42nd `Skill()` target
- Snapshot saved to: /home/sjnewhouse/.claude/hooks/cache/compaction-snapshots/diagram-generation-snapshot.md
- Note: Context compacted. Reload AA-MA files to resume.

## [2026-09-24] M4 sub-step 4.1 — re-measurement + API-shape resolution
- **42nd `Skill()` target:** `feature-dev:feature-dev` (plugin-namespaced, `DIMENSIONS.md:252`). The Ticket 4 regex excluded `:`. Extractor regex widened to `[A-Za-z0-9_:-]+`; classified DECLARED_EXTERNAL (feature-dev plugin command). `engineering-standards.md:44` (41 = 17/20/4) is now 42 = 17/21/4 — M14 reconciles the prose, as planned.
- **Plan numbers moved:** 191 node-level distinct edges (was 163), 57 source files (was 42). Orphans and DANGLING sets unchanged — the named assertions hold.
- **API-shape conflict in plan (resolved, not assumed away):** the Contract says `extract() -> tuple[Cut, list[SurfaceEdge]]`, but AC4 asserts `result.orphans` / `result.errors`. A tuple cannot carry those. Resolution: `extract()` returns a frozen `Surface(cut, edges, orphans, hook_events, errors)`; `cut` and `edges` are exactly the contract's pair. Nothing consumes M4 until M6, so no caller breaks.
- **Edge kind = destination kind** (skill|command|agent|hook) so M6's `@skill/@command/@agent/@hook` sigils filter on it directly. No `event` edge kind: M6 would report an unreserved `@event` sigil as LABEL_UNKNOWN. The install.sh table therefore feeds `hook_events` (metadata) plus an error for any wired hook missing on disk.
- **Cut excludes DANGLING edges** (AC2: every drawn edge resolves on disk or is DECLARED_EXTERNAL); `edges` keeps all three classes (AC3).
- **Orphans** = command/skill/agent/hook nodes with no inbound ON_DISK edge from another node; rules are entry points (auto-loaded), never orphans.

## [2026-09-24] M4 §6.8 review decisions
- CRITICAL (two node-identity rules) accepted by Ste and fixed: the node set is the owners of the walked files.
- Orphans are `kind:stem` (Ste). AC4's named set is unchanged; the test compares stripped stems and asserts no duplicates. Deviation from AC4's literal `set(result.orphans)` recorded here.
- M14 scope widened (future-proofing WARNING): Sub-step 14.3 now includes `engineering-standards.md:44`. The 2026-09-22 "41" was a regex artefact (`:` excluded), not a count that later moved.
- `cut.from_edges()` extracted from `cut()` and given `isolated=`; it is outside M4's Files list but preserves behaviour (M3 suites green).

## [2026-09-24] GATE APPROVAL: Milestone 4: Plugin-surface extractor
- Gate: HARD
- Approved by: Ste (Stephen J Newhouse)
- Criteria verified: 5/5
- Decision: APPROVED

## [2026-09-24] Milestone Completion: Plugin-surface extractor
- Status: COMPLETE
- Key outcome: `codemem.draw.plugin_surface.extract()` recovers the commands→skills→agents→hooks graph with three-valued classification; 42 Skill() targets = 17/21/4; 7 named orphans; golden pinned.
- Artifacts: draw/plugin_surface.py, draw/surface_allowlist.py, draw/cut.py (from_edges), tests/codemem/test_plugin_surface.py, tests/golden/plugin-surface.json
- Tests: 1216 passed / 2 skipped; 21 surface tests

## [2026-09-24] M5 design reading (from map Ticket 12, not assumed)
- Caption prose renders OUTSIDE the mermaid fence (map Ticket 12 decisions 1/5: the emitter renders captions into the living doc's markdown; `%%` comments are invisible; a caption-only diff is not drift). So `to_mermaid(c, captions=None)` uses captions ONLY for `@start` (`classDef start` + `class <id> start`), and `captions.for_cut(cut, captions)` returns the captions that apply to a cut's nodes, for M6's markdown and M12's explorer.
- Matching: dir key `a/b/` ↔ node label `a/b` (collapsed levels); file key ↔ L2 label or L3 `path::symbol` file part. `@start` highlights the node that IS or CONTAINS the path, so collapsed levels still show where to start.
- Contract Files lists only captions.py / sidecar / test, but AC1 needs the emitter and Rollback names "the emitter's captions argument", so `draw/mermaid.py` is modified (default None → byte-identical M3 output). The `codemem draw` CLI is not wired here: M6's view registry is the caller (YAGNI until then).
- The "emitter refuses to write inside docs/architecture/" risk mitigation has no writer until M6; M5 pins the path constant outside that dir.

## [2026-09-24] M5 decision — directory caption matching (Ste)
- Measured: M3's L0/L1 collapse to depth 1/2, so the map's claim that collapsed levels have ids like `src/aa_ma/render/` is false; depth-3 dir keys named no node at any level.
- Options: exact-only (re-key the sidecar to depth ≤ 2), equal-or-contained, or also ancestors. **Ste chose equal-or-contained**: a dir caption covers the node that IS the dir and every node INSIDE it, never an ancestor. AC2 holds for depth-1/2 keys; deeper keys surface at L2/L3.
- `@start` highlights the node that is, contains, or is contained by the start path. At L0 on this repo `src` has no cross-dir edge, so nothing is highlighted there — correct: no node, no highlight.

## [2026-09-24] M5 §6.8 decisions (Ste)
- Fix all M5 findings now (done, 6f39194 → 185453c).
- **M6 `--check` compares only the ```mermaid fences** — resolves M6's AC4 vs whole-file comparison contradiction; caption prose edits are never drift, an `@start` edit is. Recorded as a 6.1 obligation (plan.md stays historical).
- **Scope change to future milestones** (tasks.md only): 6.1 fence-only compare + writer path guard; 6.2 `ORPHAN_CAPTION` wired into `--check` with `git ls-files` + plan §13 `(new)` set; 6.3 one escaping helper for prose + plugin-surface captions decision; 8.2 `classDef` lines in the fixture; 12.2 explorer caption parity + JSON-island escaping.

## [2026-09-24] GATE APPROVAL: Milestone 5: Captions sidecar
- Gate: HARD
- Approved by: Ste (Stephen J Newhouse)
- Criteria verified: 4/4
- Decision: APPROVED

## [2026-09-24] Milestone Completion: Captions sidecar
- Status: COMPLETE
- Key outcome: one authored JSON sidecar feeds per-level captions (`for_cut`) and the `@start` highlight; ORPHAN_CAPTION vs UNKNOWN findings; prose never enters the mermaid.
- Artifacts: draw/captions.py, draw/mermaid.py (captions=), docs/architecture.captions.json, tests/codemem/test_captions.py
- Tests: 1245 passed / 2 skipped; 29 caption tests

## [2026-09-24] M6 design decisions (Ste, before any code)
Measured first (fresh scratch index, L-024): L0 and L1 are 3 nodes / 2 edges on this repo (claude-code → packages → src); L2 whole repo (tests excluded) is 47 nodes / 91 edges both kinds, 62 import-only. codemem's indexer uses `git ls-files`, so local and CI builds see the same tracked set.
1. **component.md = L2 whole repo, both kinds** (Ste).
2. **CLI = `codemem draw --write` / `codemem draw --check`**; bare `codemem draw` stays M3's stdout emitter (nothing breaks). The remedy message names `codemem draw --write` (contains AC2's "codemem draw").
3. **`--check` compares every line except line 1 (the stamp) and the lines inside a `<!-- captions -->` … `<!-- /captions -->` block** (Ste). This refines the M5 "fences only" decision, which contradicted AC2, the plan's line-2 risk test, and left README.md (no fence) unchecked. Caption prose edits remain non-drift; `@start` edits remain drift (the classDef is inside the fence).
4. **`--check` planned set is empty**: `ORPHAN_CAPTION` (exit 1) for any caption naming a path not in `git ls-files`; author captions only for paths that exist (Ste). codemem has no aa_ma dependency and the lint's `(new)` parser is private.
5. Derived (not assumed, recorded for review): plugin-surface is registered only when `claude-code/` exists (consumer repos have none); it takes no captions by construction — its labels are `kind:stem`, which no path key matches. `--check` with no/pre-v3 index prints UNKNOWN and exits 0 for all views (AC3), including plugin-surface.

## [2026-09-24] M6 §6.8 decisions (Ste)
- CRITICAL (lessons.md outside Files) **disputed** — convention: lesson commits are exempt from a milestone's Files list.
- Fix all findings now; `--check` now also requires line 1 to have the stamp SHAPE and every captions-block line to be a generator shape. This refines decision 3 (masking stays, blind spot closed).
- Regen duty: `scripts/regen-generated.sh` + standing obligation on M7–M14 + CONTRIBUTING "Generated files".

## [2026-09-24] GATE APPROVAL: Milestone 6: Living doc + `--check` + CI drift job + ADR-0016 → release `v0.15.0`
- Gate: HARD
- Approved by: Ste (Stephen J Newhouse)
- Criteria verified: 7/7
- Decision: APPROVED

## [2026-09-24] Milestone Completion: Living doc + --check + CI drift job + ADR-0016 → v0.15.0
- Status: COMPLETE
- Key outcome: `docs/architecture/` is generated (`codemem draw --write`) and drift-checked in CI (`architecture-drift`); v0.15.0 released.
- Artifacts: draw/views.py, cli.py (--write/--check), indexer.git_tracked_files, captions guard hardening, docs/architecture/*, scripts/regen-generated.sh, security.yml job, ADR-0016, CONTRIBUTING/README/SECURITY/CHANGELOG.
- Tests: 1288 passed / 2 skipped.
- Note for M7: `## Unreleased` was consumed by the release; the next milestone that ships a user-facing change re-creates it (runbook).

## [2026-09-24T13:00:34Z] Compaction Summary (auto-generated by hook)
- Active step at compaction: Sub-step 7.1: [test] `deps-hazards.md` (`M1.0`, `M2a.1`, `2a`, cross-plan) + naive mutant, RED
- Snapshot saved to: /home/sjnewhouse/.claude/hooks/cache/compaction-snapshots/diagram-generation-snapshot.md
- Note: Context compacted. Reload AA-MA files to resume.

## [2026-09-24] M7 design decisions (measured first, L-024)
- Corpus re-measured with the repo's own field reader (`tui/parser._field_pattern` shape): **324** `Dependencies:` values, **61** `None`, **0** unresolved with an `M`-prefix-aware resolver. A naive `M`-stripping resolver reports **29** false failures (charting saw 30–36) — the hazard is real.
- Plan AC2 ("exactly two … names both", then lists one) does not hold: the tiktoken line is `- Dependencies table: tiktoken …`, a Result Log sub-bullet, not a `Dependencies:` field; the charting regex was looser. **Ste: AC2 asserts ZERO findings on the corpus**, names the cross-plan `milestone-grammar-ssot M5` as exempt, and pins the `Dependencies table:` line as not-a-field. Identity, not ratio.
- **Ste: surfacing is `python -m aa_ma.deps {graph,check,advisory} <tasks.md>`** (no pyproject change). `/aa-ma-plan` Phase 5 pastes `graph` output into §13 and runs `check`; `/execute-aa-ma-milestone` §5.1 runs `advisory` (exit 0 always). Spec §XI item 13 sentence updated. Two command files beyond the M7 contract's Files list — recorded here as the scope change.
- Active plans already write canonical `Dependencies:` (measured: `None` / `Milestone N[, Milestone N]`), so `CANONICAL_DEPENDENCY_RE` can be enforced on `.claude/dev/active/**` like the heading form.
- Pre-M7 `aa-ma-gate` golden: 33 files / 205 invocations, sha256 prefix `5444d16692fe1107`, base `dc4e90e` (scratch copy; 7.5 re-runs on identical inputs).
- 7.4 scope addition (recorded, KISS): `CANONICAL_DEPENDENCY_RE` also accepts `<task-slug> Milestone N`. Without it the canonical form could not express a cross-plan dependency at all, and the active-plans lint would have refused the one legitimate cross-plan shape the corpus holds (`plan-architecture-views` M2). `aa_ma_deps` launcher added to `aa-ma-parse.sh` (hooks/lib — inside `hook-modification`) so consumer repos reach the plugin's Python exactly as the gate does; `aa_ma_gate` itself unchanged.
- M7 §6.8 (Ste): CRITICAL accepted — `execute-aa-ma-milestone.md` §6.2 and `execute-aa-ma-full.md` no longer HALT on `Dependencies:`; §6.2 defers to the §5.1 advisory (at §6.2 the next milestone is still PENDING, so running the advisory there would only repeat §5.1's line). All WARNINGs fixed: shared `grammar.field_pattern` (linear; tui + deps) and `grammar.own_text` (gate + deps), `MAX_SPAN=100`, `MAX_FINDINGS=200`, launcher timeout + uv notice. Recorded, not fixed: hyphenated-word false cross-plan exemption (advisory only).

## [2026-09-24] GATE APPROVAL: Milestone 7: `Dependencies:` grammar + Milestone graph + advisory
- Gate: HARD
- Approved by: Ste
- Criteria verified: 8/8 (AC2 as amended by Ste: zero corpus findings)
- Decision: APPROVED

## [2026-09-24] Milestone Completion: Milestone 7: `Dependencies:` grammar + Milestone graph + advisory
- Status: COMPLETE
- Key outcome: `aa_ma.deps` reads every legacy `Dependencies:` form with an M-prefix-aware resolver; the Milestone graph is generated into plan §13 by `/aa-ma-plan`, `UNRESOLVED_DEPENDENCY` is a planning-time finding, and the advisory never blocks (§5.1; §6.2 and execute-aa-ma-full no longer HALT). `aa-ma-gate` output byte-identical.
- Artifacts: src/aa_ma/deps.py, grammar.py (CANONICAL_DEPENDENCY_RE, NUMBER_BODY, own_text, field_pattern), gate.py + tui/parser.py (shared helpers), aa-ma-parse.sh (aa_ma_deps), commands aa-ma-plan / execute-aa-ma-milestone / execute-aa-ma-full, scribe, tasks-template, spec §XI 13, foundations, CHANGELOG Unreleased, .importlinter, tests (test_deps.py, test_active_plans_canonical.py, hooks/aa-ma-deps.bats, fixtures/deps-hazards.md).
- Tests: pytest 1379 passed / 2 skipped; bats 210/210; lint-imports 4/4.
- AC2 supersession also covers plan.md's M7 Tests line ("corpus run asserting the 2/312 figure") and Risk row ("measured at 2/312"): both read as ZERO findings over the live corpus (324 fields on 2026-09-24). plan.md stays unedited (historical record).

## [2026-09-24] M8 design decisions (prototype first, L-024)
- Prototype on this plan's §13 against a fresh scratch index: 23 `@import` claims → 3 PHANTOM, 19 UNKNOWN (`(new)` endpoints, non-graph files `schema.sql`, `parser/rules/`), 0 OK. Node ids must be scoped per mermaid fence (prototype collided `A`/`B` across views).
- Of the 3 PHANTOMs, python_ast→resolver is a genuinely wrong claim; incremental→db and server→mcp_tools are TRUE claims codemem cannot see: its import resolution maps `from pkg import submodule` to `pkg/__init__.py`, never the submodule. **Ste: fix the codemem resolver in M8 (TDD)** — `from X import name` also yields an edge to `X/name.py` / `X/name/__init__.py` when that submodule exists. Scope beyond the M8 contract Files list (codemem resolver + test + regenerated docs), recorded here.
- **Ste: plugin sigils (`@skill` `@command` `@agent` `@hook`) report `UNKNOWN: plugin-surface edges are not in the codemem index`** — recognised (never LABEL_UNKNOWN), never PASS (L-012), exit unchanged. aa_ma cannot import codemem (ADR-0014) and the index stores no plugin-surface edges. Follow-up recorded for M13.
- Evaluability = both endpoints are rows in the index `files` table and the graph status is OK (not MISSING / SCHEMA_TOO_OLD / STALE); otherwise UNKNOWN with the reason. No language list needed.
- M8 8.4 (Ste): this plan's §13 line 279 `PY -->|"@import"| RES` relabelled `PY -->|feeds| RES` — the first PHANTOM_EDGE the new tier found in a live plan (python_ast.py and resolver.py import neither way; parser output reaches the resolver as data via indexer.py). The only plan.md edit; §13 is the live Architecture View.
- M8 §6.8 (Ste): all 3 CRITICALs accepted and fixed — unparsed sigil forms now UNKNOWN (never a silent pass); submodule edges derived from the module's own resolution with correct relative level and receiver-scoped call binding (the reviewer's reproduced `y.run()`→x.py false edge is gone); one shared label→path rule with the `_inside` guard. All WARNINGs fixed; carry-forwards for M13 (plugin sigils) and M14 (engineering-standards + ADR-0010) written into tasks.md.

## [2026-09-24] GATE APPROVAL: Milestone 8: `PHANTOM_EDGE` sigil grammar
- Gate: HARD
- Approved by: Ste
- Criteria verified: 6/6
- Decision: APPROVED

## [2026-09-24] Milestone Completion: Milestone 8: `PHANTOM_EDGE` sigil grammar
- Status: COMPLETE
- Key outcome: `aa-ma-lint-views` checks opt-in sigil edge claims against the codemem graph (`PHANTOM_EDGE`, `LABEL_UNKNOWN`, informational `UNKNOWN`); codemem now resolves `from pkg import submodule` from the module's own resolution with receiver-scoped call binding. First live catch: this plan's own §13 claim python_ast→resolver (relabelled).
- Artifacts: src/aa_ma/render/{mermaid_lint,graph,cli}.py; packages/codemem-mcp/src/codemem/{resolver.py,parser/python_ast.py}; claude-code/skills/plan-verification/SKILL.md; CHANGELOG; plan.md §13 line 279; tests/render/test_phantom_edge.py, tests/fixtures/sigil-edges.md, tests/codemem/test_file_edges.py; docs/architecture regenerated.
- Tests: pytest 1443 passed / 2 skipped; bats 210/210; lint-imports 4/4.
- M8 back-fill (validator): the evaluability rule recorded at M8 start ("both endpoints are rows in `files`") was superseded during 8.3 — `scripts/run.sh` is in `files` (bash, symbols) but can never be an `@import` endpoint. Shipped rule: an endpoint is evaluable for a sigil iff its `files.lang` has ≥1 edge of that kind. The "+26 import edges" in 8.3's Result Log is the pre-§6.8 count; after the §6.8 resolver rework it is +28 (adds `cli.py → graph.py` and the level-correct `views.py → indexer.py`).

## [2026-09-24T20:44:26Z] Compaction Summary (auto-generated by hook)
- Active step at compaction: Sub-step 9.1: [prototype] `Skill(prototype)` on this repo + `medical-research-skills`; `PROTOTYPE` provenance
- Snapshot saved to: /home/sjnewhouse/.claude/hooks/cache/compaction-snapshots/diagram-generation-snapshot.md
- Note: Context compacted. Reload AA-MA files to resume.

## [2026-09-25] M9 prototype verdict: REVISE (Ste)
- Question: which merged `io.md` shape stays inside the 120-edge dense band? Measured with a throwaway scanner on aa-ma-forge@d31e301 and medical-research-skills@efafac2 (local-only branch `prototype/diagram-generation-io` @ bdccfda).
- Finding 1: medical-research-skills breaches at file level (186 qualified / 285 with bare) and is 99% Python, so the plan's revision trigger (per-language files) cannot fix the breach. L1 folders fit (24). Decision: **auto level** — file when ≤120 edges, else L1. It is deterministic, so `--check` does not change.
- Finding 2: `open()` alone takes file-level edges from 186 to 381. `open` stays in `_CALL_EXCLUDE` (AC5), N=5 on the fixture tree.
- Finding 3: mermaid has no `:::class` on edges. Edge ids plus `class eN bare|qualified` are verified on mmdc 11.17. AC4 is amended.
- AC6 records the FILE-level count (the trigger), 285 OVER, not the drawn count.
- Prototype data holds external-repo paths, so the branch stays local and is never pushed (Ste).
- Neither repo has any TS/Go I/O; v1 TS/TSX/JS/Go coverage is proven by fixtures only.

## [2026-09-25] M9 §6.8 — PASS_WITH_WARNINGS (0 C / 7 W / 18 I)
- Fixed RED-first: script works from any cwd (`uv run --project`), linear column-precise enclosing-function sweep, renderer free of yaml (`CATEGORY_LABEL` → mermaid.py, `IoEdge` under TYPE_CHECKING), Contract Files amended, 285/289 note, `DENSE_BAND`-derived tests, band-line sanitising, extra-key message.
- Deferred (Ste): arrow-function / function-expression callables → M13 carry-forward; io.md prose discloses the gap.
- CI red on 83b6dbf was a process defect (regen before `git add`), not code: L-026; the regen script now refuses untracked sources.

## [2026-09-25] GATE APPROVAL: Milestone 9: I/O-boundary view — `Prototype-Required: YES`
- Gate: HARD
- Approved by: Ste
- Criteria verified: 6/6
- Decision: APPROVED

## [2026-09-25] Milestone Completion: Milestone 9: I/O-boundary view — `Prototype-Required: YES`
- Status: COMPLETE
- Key outcome: generated `docs/architecture/io.md` — per-file (else L1) arrows into language-subgraph sink categories, qualified solid / bare dashed via edge-id classes, classified at render time from `draw/sinks.yaml`; TS/TSX/JS/Go call edges now stored with receivers; AC6 band line for medical-research-skills@efafac2 = 289 OVER.
- Artifacts: codemem/draw/{io_sinks.py,sinks.yaml,mermaid.py,views.py,cut.py}, parser/{ast_grep.py,python_ast.py,rules/*.yml}, scripts/{measure_io_band.sh,regen-generated.sh}, pyproject (+pyyaml), src/aa_ma/render/html.py (comment), docs/architecture/io.md, tests/codemem/test_io_sinks.py, CHANGELOG, docs/lessons.md L-026.
- Tests: pytest 1485 passed / 2 skipped; bats 210/210; lint-imports 4/4; ruff + shellcheck clean; CI green on c136ac2.

## [2026-09-25] M10 start — design decisions (Ste), measured first
- Measured: the M10 Contract listed only markdown, yet AC1-AC3 need findings from a fixture — prose can't be run by pytest. Contract grammar differs across plans: this plan uses `Create`/`Modify` rows; the template (`docs/templates/plan-template.md:84`) and both other post-cutover plans use `# file: <path>`. A throwaway prototype (scratch `cov.py`) found: this plan 52 paths / 4 undrawn (pyproject.toml, uv.lock, 2 scripts — all from my M9 Contract amendment); mattpocock-trio-adoption 8 / 0; plan-architecture-views 6 / 6 (only when `# file:` is read). `codemem draw --scope` takes one prefix; a repeated flag silently keeps the last one.
- Decided: executable rule in `aa_ma.render.coverage` behind the opt-in `aa-ma-lint-views --coverage` (gate path never passes it); read both row grammars; exemption (d) = pyproject.toml, package.json, *.lock; draw `scripts/` in this plan's §13; repeatable `--scope`.

## [2026-09-25] M10 §6.8 — PASS_WITH_WARNINGS (0 C / 10 W / 14 I), all fixed (Ste)
- Coverage now fails closed: every Contract row token is a path; brace expansion is iterative and capped (MAX_EXPANSIONS = 256; past it the token stays whole); a crash is UNKNOWN (exit 2), and check 8's fence reads rc ∉ {0,1} as CRITICAL — never clean.
- Step 4.2b reads paths from a quoted heredoc (spaces, globs and `$(...)` stay data), skips the draw when there are none, and refuses a non-checkout AA_MA_ROOT.
- Both fences are executed by pytest against a stub `uv` under a fake `~/.claude` symlink tree, so the shipped text is tested, not paraphrased.

## [2026-09-25] GATE APPROVAL: Milestone 10: `/aa-ma-plan` §13 seeding + Angle 6 coverage rule
- Gate: HARD
- Approved by: Ste
- Criteria verified: 5/5
- Decision: APPROVED

## [2026-09-25] Milestone Completion: Milestone 10: `/aa-ma-plan` §13 seeding + Angle 6 coverage rule
- Status: COMPLETE
- Key outcome: `/aa-ma-plan` Step 4.2b seeds §13 from `codemem draw` (repeatable `--scope`, quoted heredoc, skip when empty); Angle 6 check 8 = `aa-ma-lint-views --coverage` (`aa_ma.render.coverage`, UNDRAWN_PATH, WARNING, fail closed, planning time only).
- Artifacts: src/aa_ma/render/{coverage,cli,mermaid_lint}.py, codemem {cli,draw/cut}.py, claude-code/commands/aa-ma-plan.md, claude-code/skills/plan-verification/SKILL.md, claude-code/rules/aa-ma.md, docs/spec/aa-ma-specification.md, tests/skills/test_angle6_coverage.py, tests/fixtures/seeded-plan.md, tests/codemem/test_draw_cut.py, CHANGELOG, plan §13.
- Tests: pytest 1538 passed / 2 skipped; bats 210/210; lint-imports 4/4; CI green on f1077cd.

- M10 validator back-fill: plan-architecture-views measured 6 / 6 by the throwaway prototype (it read the template placeholder inside an example fence); the shipped rule reads only the fences directly under `#### Contract`, giving 5 / 1. The §6.8 round also touched `claude-code/rules/aa-ma.md` (check 8 in the grandfathering line), now listed in the M10 Contract.

## [2026-09-25T17:57:46Z] Compaction Summary (auto-generated by hook)
- Active step at compaction: Sub-step 11.1: [test] `test_diagram_verified.bats` against `aa-ma-lint-views`, RED
- Snapshot saved to: /home/sjnewhouse/.claude/hooks/cache/compaction-snapshots/diagram-generation-snapshot.md
- Note: Context compacted. Reload AA-MA files to resume.

## [2026-09-25] Milestone 11 decisions (Ste)
- **Which UNKNOWN refuses — index-only.** Measured first: our own §13 lints 25 sigil edges, 19 UNKNOWN, 0 PHANTOM; the UNKNOWNs are `endpoint planned (new)` (17) and `no repo path in node label` (2), with no index UNKNOWN. The plan's literal "UNKNOWN refuses" would block every milestone of any plan that draws a planned file with a sigil — including M11 itself — until its last milestone. L-012 targets a check that *did not run*; that is the index class only (missing, schema too old, stale, unreadable — every reason naming `codemem build`). Per-claim UNKNOWNs pass and are counted (`unknown=K`) in the evidence line.
- **Edge count + opt-in — a lint summary line.** `aa-ma-lint-views` gains one stdout line before `render:`: `sigils: edges=N phantom=P unknown=K index-unknown=I`. The fence reads it; `edges=0` is the opt-out. A grep over plan.md would count sigils outside §13 (this plan has 2 in AC prose); a `python -c` over private internals would ship untested code in markdown. Contract amended: + `src/aa_ma/render/{mermaid_lint,cli}.py`, `tests/render/test_cli.py`; `gate.py` still untouched. AC3 amended, AC8 added.
- Pre-edit baselines (11.2 inputs, scratch): §6.7 extractor output 105 lines sha256 17be760b…; bats 32+10+16 = 58/58, full 210/210; `aa-ma-gate --format kv` over 33 corpus tasks.md files, 187 lines.

## [2026-09-26] Milestone 11 §6.8 decisions (Ste)
- **CRITICAL accepted, fixed:** an unread §13 (misspelled heading, view without `###`) printed `edges=0` and passed as opt-out. The lint now compares sigil-slot lines across every mermaid fence of the plan with those the view scan read; fewer → `sigils: UNKNOWN`.
- **"Index-only UNKNOWN refuses" tightened: authoring errors refuse too.** An edge to a missing non-`(new)` file, a stale `(new)` on an existing file, a path-less label, an unparsed edge form, a path outside the repo → `invalid`, refused. Still passing: a genuinely planned file, plugin sigils, unmodelled languages. `checked=C` in the summary and evidence.
- **Launcher:** `aa_ma_lint_views` in `aa-ma-parse.sh` (Contract amended; drawn in §13 as `PARSE`).
- **Own §13 corrected** (13 stale `(new)` dropped; 7 predicted-but-unbuilt `@import` edges fixed to the code; 1 function-local import relabelled in prose; `SQL`/`PRULES` prose). The first real use of the item found 8 false edges in the plan that built it.

## [2026-09-26] GATE APPROVAL: Milestone 11: §6.7 HARD item + `DIAGRAM_VERIFIED` + ADR-0015
- Gate: HARD
- Approved by: Ste
- Criteria verified: 8/8
- Decision: APPROVED

## [2026-09-26] Milestone Completion: Milestone 11: §6.7 HARD item + `DIAGRAM_VERIFIED` + ADR-0015
- Status: COMPLETE
- Key outcome: a §13 sigil edge that is false, uncheckable by authoring error, or unanswerable by the index now refuses milestone COMPLETE through a second §6.7 fence (opt-in; `gate.py` untouched); a pass records `DIAGRAM_VERIFIED — <heading> — edges=N checked=C phantom=0 unknown=K`. Its first real use found 8 false edges in this plan's own §13.
- Artifacts: src/aa_ma/render/{mermaid_lint,cli}.py; claude-code/commands/execute-aa-ma-milestone.md (§6.7); claude-code/hooks/lib/aa-ma-parse.sh (`aa_ma_lint_views`); claude-code/rules/engineering-standards.md (§1, §5); claude-code/skills/plan-verification/SKILL.md; docs/adr/0015-diagram-as-acceptance-criterion.md, docs/adr/INDEX.md; CHANGELOG.md; tests/hooks/test_diagram_verified.bats (new, 21); tests/render/test_{cli,phantom_edge}.py.
- Tests: pytest 1559 passed / 2 skipped; bats 231/231 (58 protected 32/10/16 unchanged); lint-imports 4/4; ruff clean; gate-fence sha256 17be760b… unchanged.

## [2026-09-26] Milestone 12 decisions (Ste)
- **Prototype verdict PROCEED** (12.1): mermaid 11.17.2 node = `<g class="node" id="<renderId>-flowchart-<nid>-<i>">` (no `data-id`); one delegated listener + `/flowchart-(n[0-9a-z]+)-\d+$/`; strict + hash CSP, 0 violations. The explorer renders on demand, so it cannot reuse html.py's `_INIT_JS` (`startOnLoad: true`): its one inline script is `explorer.js`, hashed into a CSP composed by a new `html.csp(*hashes)` (`_CSP = csp(_INIT_SHA)`, byte-identical, golden unchanged).
- **Captions deferred** from the explorer (no M12 AC names them; `aa_ma` may not import `codemem.captions`, which closes the "embed Python's for_cut output" route). Carry-forward: add them later with the JS `_names`/`@start` rule pinned by caption cases in draw-node-ids.json.
- **Index state:** missing or schema < 3 → exit 2 naming `codemem build`, nothing written; stale → page written with a visible stale banner + a stderr warning.
- **Scope:** import + call edges labelled `@import`/`@call`; tests hidden by default behind an on-page toggle; levels L0/L1/L2 (L3 symbols out of scope).
- **Fixture:** draw-node-ids.json pins node ids only today; the plan says it also pins the directory-collapse rule, so L2 rows gain an optional `collapse: [L0, L1]` generated by `codemem.draw.cut.collapse` — still the one shared source.
