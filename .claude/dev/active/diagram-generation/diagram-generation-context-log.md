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
