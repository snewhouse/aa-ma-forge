# diagram-generation Reference

Immutable facts. Everything here was measured on running code at `d4d657f`
(2026-09-22) unless a line says otherwise. Re-measure before relying on a
figure that carries a decay note.

## Architecture View

Architecture View: see plan.md §13 (Component view + Flow view; `Diagram-Waiver: none`).

## Paths and constants

| Fact | Value | Source |
|---|---|---|
| Repo root | `/home/sjnewhouse/projects/github_private/aa-ma-forge` | — |
| codemem code | `packages/codemem-mcp/src/codemem/` | workspace member, `pyproject.toml:56` |
| codemem **tests** | `tests/codemem/` — **NOT** beside the package | CI runs `pytest tests/codemem/` |
| Live MCP server | `claude-code/codemem/mcp/server.py` | `packages/codemem-mcp/pyproject.toml:33` |
| Mermaid pin | `11.17.2` | `src/aa_ma/render/html.py:12` |
| Mermaid SRI | `sha384-EOXBFmc3gx5mb+vn0vPvvGqACToJD24hhacX5Yx+8NUUQrHIle/Qi5Bg9o3zKwW2` | `html.py:16` |
| mermaid `maxEdges` / `maxTextSize` | 500 / 50000 | Ticket 10 |
| Readability bands | ≤40 readable · ≤120 dense · 500 hard stop | Ticket 3 |
| Index build time | 0.44s (175 files / 1517 symbols) | Ticket 8 |
| `.codemem/` db path | `Path.cwd()/".codemem"/"index.db"` — hardcoded, no env var | `cli.py:33`, `mcp_tools/__init__.py:94`; `--db` at `cli.py:265` |
| Current schema version | `user_version = 3` since M1 (was 2); `CURRENT_SCHEMA_VERSION` at `db.py:41` | M1 |
| `PRAGMA foreign_keys` | ON for write connections | `db.py:120-122` |
| MCP budget | `_DEFAULT_BUDGET = 8_000` tokens | `mcp_tools/__init__.py:52` |
| CI jobs (5) | shellcheck · bandit · ruff · bats · codemem-smoke | `.github/workflows/security.yml` |
| `lint-imports` in CI | **absent** — 0 occurrences | measured; M2 adds it |
| `.importlinter` contracts | 3: `codemem-layers`, `parser-is-pure`, `render-is-leaf` | `lint-imports` → `3 kept, 0 broken` |
| Measurement repo | `medical-research-skills` — 2452 Py/TS/JS/Go files (16× this repo's 153) | M9, M13 |

## Load-bearing invariants — violating any of these breaks a test

1. **`schema.sql` is pinned at v1 forever.** Line 17 is `PRAGMA user_version = 1;`.
   Every later version arrives only through `db.MIGRATIONS`. Pinned by
   `tests/codemem/test_schema_v2.py:57`.
2. **`ensure_schema()` downgrades a newer DB today.** REPRODUCED: a v3 DB opened by
   v2-era code becomes v2 with the new table intact, because `ensure_schema()`
   (`db.py:208-209`) runs `apply_schema()` first and that re-executes schema.sql's
   line 17. Every writer calls it (`indexer.py:387`, `incremental.py:204`,
   `journal/wal.py:281`). `migrate()` alone is correct — it is not the production path.
3. **`migrate()` does NOT roll back DDL** despite its docstring (`db.py:179-181`).
   `executescript` commits first. `IF NOT EXISTS` is therefore mandatory
   (`db.py:45-46`), not stylistic.
4. **`edges` stores every edge exactly twice.** 6516 rows / 3258 distinct;
   multiplicity histogram `[(2, 3258)]`, zero singletons. `build_index` writes the
   set twice (`indexer.py:409`, then `:410-412`) and the composite PK never fires
   because SQLite treats NULLs as distinct and both `dst` columns are mutually
   exclusive. **Every reader of `edges` must `SELECT DISTINCT`.** Recorded in
   `TODOS.md` for a separate fix. `1185` resolved call edges IS the distinct count
   (raw 2370).
5. **`test_leaf_contract.py:24` computes its expectation live** via
   `pkgutil.iter_modules(aa_ma.__path__) - {aa_ma.render}`. A new top-level
   `aa_ma` module must join `.importlinter` `render-is-leaf` in the same commit.
6. **The §6.7 gate fence is extracted by position.**
   `tests/hooks/aa-ma-gate-python.bats:46` (`_gate_fence`) executes the FIRST ```bash
   fence after `### 6.7 `; `test_diagram_verified.bats` (AC7) asserts the order.
   (`aa-ma-gate-scans.bats` syntax-checks every fence; the §6.8 suite reads §6.8 only —
   corrected by the M11 §6.8 review.)
7. **`aa-ma-gate` reads `tasks.md` only** (`gate.py:462`, one positional arg).
   Milestone-level fields ARE honoured (`gate.py:205-209` `_own_text`, OR'd with the
   sub-step roll-up at `:428`). Fields living only in plan.md are never read.
8. **MCP tool count is pinned at 12** — `tests/codemem/test_mcp_server.py:47,50`.
9. **`understand-codebase` references/ inventory is pinned** —
   `tests/skills/test_understand_codebase_frontmatter.py:74`. Edit contents freely;
   adding or removing a file there breaks it.
10. **Angle 6 check numbering is pinned** — `tests/commands/test_plan_verification_angle6.py:29-31`
    asserts the literals for checks 6 and 7 and the date `2026-09-11`. Append, never renumber.
11. **`parser/rules/` holds 8 YAMLs and there is no `python.yml`.** Python is parsed
    natively by `parser/python_ast.py`.

## Decay notices — re-measure before asserting

- `Skill()` targets: **42** distinct (M4 re-measured 2026-09-24: 17 ON_DISK / 21 DECLARED_EXTERNAL / 4 DANGLING; the 42nd is plugin-namespaced `feature-dev:feature-dev`, invisible to Ticket 4's `[A-Za-z0-9_-]+`), while
  `claude-code/rules/engineering-standards.md:44` still pins 41 (17/20/4). M4 identifies
  the 42nd; M14 reconciles the rule.
- Plugin surface: 163 edges / 42 files / 52 of 59 nodes (13 cmd, 21 skill, 12 agent,
  11 hook, 2 rule). Invalidated by any rename — M4 pins a regenerable golden instead.
- `Dependencies:` corpus: **312** values in `.claude/dev/**/*tasks.md` + `examples/`,
  **53** of them `None`. Ticket 16's "59 None" is stale. Ticket 7's "383" is a broader
  corpus (whole-repo ≈395), not a contradiction. This plan's own tasks.md adds 14 more.

## Research files (all Valid-Through 2026-Q4, written 2026-09-22)

- `docs/research/diagram-generation-codemem-import-edges.md` — what it takes to persist file→file import edges (Ticket 1)
- `docs/research/diagram-generation-plugin-surface-extraction.md` — regex extraction of commands→skills→agents→hooks (Ticket 4)
- `docs/research/diagram-generation-io-sink-catalogue.md` — I/O sink catalogue per language (Ticket 6)
- `docs/research/diagram-generation-prior-art.md` — code→mermaid tools and scoping heuristics (Ticket 10)
- `docs/research/diagram-generation-export-and-notation.md` — export formats, notation re-evaluation (Ticket 13)

## Ticket answers (source: `diagram-generation-map.md`, 19/19 RESOLVED 2026-09-22)

1. `file_edges` via MIGRATIONS v3; Python ≈80 LOC; dotted callee ≈15 LOC
2. `aa_ma.render` reads `.codemem/index.db` via stdlib sqlite3; door is `codemem draw`; new `aa-ma-never-imports-codemem` contract
3. Layered zoom L0–L3, not one knob; tests excluded by default; PageRank ruled out as default
4. Regex suffices — 4 syntaxes, node id = file stem, `docs/` out, 3 allowlists
5. `PHANTOM_EDGE` opt-in by QUOTED sigil `A -->|"@import"| B` (bare `|@import|` is a mermaid 11.17.2 parse error — `@` lexes as LINK_ID; corrected 2026-09-24, Ste); unlabelled edges never checked; `LABEL_UNKNOWN` for typos
6. Sink catalogue feasible all 9 langs; v1 = Py + TS/TSX/JS + Go; two confidence tiers
7. `Dependencies:` canonical write mirrors headings; lenient read of all legacy forms; graph into plan §13
8. `docs/architecture/{README,component,io,plugin-surface}.md`, 100% generated; `--check` is regenerate-and-compare; line 1 stamp excluded
9. Deep tier always runs `codemem draw`; `docs/architecture/` canonical; only ~4 assertive refs fixed
10. Own emitter; no zero-dep reuse; import-level for Component view
11. Delegated DOM listener, `securityLevel: 'strict'` unchanged; `build/`-only
12. Flat path-keyed JSON sidecar with `@start`; `ORPHAN_CAPTION` at STALE_PATH tier
13. Mermaid only; optional SVG/PNG via the existing `MMDC_BIN` seam; pin held at 11.17.2
14. Phase 4 seeds §13 with the L2 cut and `@kind` sigils; Angle 6 coverage rule counters anchoring
15. HARD §6.7 item, not `gate.py`; `UNKNOWN` refuses; evidence is `DIAGRAM_VERIFIED`
16. Advisory warning only; `UNRESOLVED_DEPENDENCY` planning-time finding; resolver must be `M`-prefix aware
17. MCP budget carried into the plan with no default — measure first (M13)
18. One merged `io.md` with language subgraphs; revision trigger = 120-edge dense band
19. Keep both backends; codemem default, `PROJECT_INDEX.json` fallback; `/index` repointed at `codemem build`

_Last Updated: 2026-09-25 (M1–M10 facts sections below)_

## M1 facts (2026-09-24)

| Fact | Value | Source |
|---|---|---|
| `file_edges` writer | `resolver._persist_import_edges()` — per-file DELETE + INSERT OR IGNORE, kind `'import'`; returns `{src_path: {target paths}}` | M1 |
| Import resolution scope | DB-wide `files` set (not parse set) | M1 |
| Dotted callee format | `edges.dst_unresolved` = `ast.unparse` chain, head via `ParseResult.import_aliases` (`np.array` -> `numpy.array`) | M1 |
| `ParseResult.import_aliases` | `dict[str, str]`: `import a.b` -> `{a: a}`; `import x as y` -> `{y: x}`; `from m import n as k` -> `{k: m.n}` | M1 |
| `apply_schema()` | restores a higher pre-existing `user_version` after running schema.sql | M1 |
| `file_edges.line` | NULL (imports carry no line numbers) | M1 |
| Live counts, this repo @ M1 | 694 import edges, 162 resolved, 0 dups; build 0.55s | M1 |
| Renderer label safety | M3+ must escape/quote node labels; do not rely on parser identifier charset | M1 security INFO |

## M2 facts (2026-09-24)

| Fact | Value | Source |
|---|---|---|
| Seam module | `src/aa_ma/render/graph.py` — `open_graph(repo_root) -> GraphHandle(status, reason, conn)`; `import_edges(h)`, `call_edges(h)` -> `set[(src_path, dst_path)]` | M2 |
| GraphStatus | `OK`, `MISSING` (absent OR unreadable), `SCHEMA_TOO_OLD` (<3), `STALE` (advisory, conn kept) | M2 |
| DB location | `<repo_root>/.codemem/index.db`, opened `file:...?mode=ro`, `trusted_schema = OFF` | M2 |
| STALE definition | indexed file newer on disk (int seconds), deleted, or unusable path; does NOT detect never-indexed new files | M2 |
| conn ownership | caller closes `h.conn` | M2 |
| Import contracts | 4: codemem-layers, parser-is-pure, render-is-leaf, aa-ma-never-imports-codemem; asserted BY NAME | M2 |
| lint-imports in CI | `security.yml` codemem-smoke, step after `uv sync` | M2 |
| Live counts @ M2 | ~~163 / 175~~ measured on a CORRUPTED index; corrected @ M3 (healed): import_edges 171, call_edges 107 | M2, corrected M3 |
| ADR-0014 | Accepted; flip to Implemented when M3/M5 consumers ship | M2 |

## M3 facts (2026-09-24)

| Fact | Value | Source |
|---|---|---|
| CLI | `codemem [--db P] draw [--level L0..L3 (default L0)] [--scope] [--hops N>=0] [--include-tests] [--direction up/down/both] [--kind import/call/both (default both)]`; stdout mermaid, stderr summary; exit 0 / 1 no-old-unreadable index / 2 usage | M3 |
| API | `codemem.draw.cut.cut(conn, level, *, scope, hops, include_tests, direction, kind) -> Cut(nodes, edges, dropped)`; `to_mermaid(cut)`; `node_id(name, level)`; `MIN_SCHEMA_VERSION = 3`; `MAX_EDGES = 500` | M3 |
| Levels | L0 dir depth 1 · L1 dir depth 2 · L2 files · L3 `path::Class.method` (calls only; L3+import -> ValueError); scope neighbourhood BEFORE collapse | M3 |
| Edge syntax | `A -->|"@import"| B` / `-->|"@call"|` (QUOTED; bare is a mermaid 11 parse error) | M3 |
| Label escaping | `# " < > % { } \`` -> `#35; #quot; #lt; #gt; #37; #123; #125; #96;`; control chars -> `?` | M3 |
| node_id | `"n" + base36(h)`, h = seed 7, h*31 + charCodeAt(0) per code point (non-BMP = high surrogate), uint32, over `L<level>:<name>`; fixture `tests/fixtures/draw-node-ids.json` from independent JS `draw-node-ids.gen.mjs` | M3 |
| Build semantics | `build_index` clears edges/file_edges/symbols/files, then reloads (self-heals corrupted indexes) | M3 §3.5 |
| Live bands @ M3 | L0 2/1; L2 render call 5/4; call -tests 25/27; +tests 94/107; L3 299/355 | M3 |
| Local render env | mmdc 11.17.0 / mermaid 11.17.2; chrome-headless-shell 152.0.7977.75 in ~/.cache/puppeteer (manually extracted; no `unzip` on host); CI has no browser -> render UNKNOWN there | M3 |

## M4 facts (plugin surface, 2026-09-24)
- API: `codemem.draw.plugin_surface.extract(repo_root) -> Surface(cut, edges: list[SurfaceEdge], orphans, hook_events, errors)`; `SurfaceEdge(src, dst, kind, ref_class)`; `RefClass` ON_DISK | DECLARED_EXTERNAL | DANGLING; `as_json()` = golden shape.
- Node ids are `kind:stem` (kind ∈ command|skill|agent|hook|rule); edge `kind` = DESTINATION kind (M6 sigils `@skill/@command/@agent/@hook` filter on it). Cut built with `Level.L2` as a namespace seed only; DANGLING edges not drawn; orphans drawn as isolated nodes.
- Allowlist: `codemem.draw.surface_allowlist.EXTERNAL` (skill/agent/hook) and `HOOK_TABLE = scripts/install.sh`; an unreferenced entry fails `test_every_allowlisted_external_is_still_referenced`.
- Golden: `tests/golden/plugin-surface.json`; regenerate with `uv run python tests/codemem/test_plugin_surface.py` and review the diff. Any `claude-code/` edit that changes references changes it — M10/M11/M14 must regenerate.
- Live at 711e8b7: 191 edges (154 ON_DISK / 33 DECLARED_EXTERNAL / 4 DANGLING), 59 nodes, 7 orphans, 7 wired hooks, errors []. Measurements, not assertions.
- `cut.from_edges(edges, level, isolated=frozenset())` is the shared edges→Cut step (sort, MAX_EDGES cap, collision check).

## M5 facts (captions, 2026-09-24)
- Sidecar: `docs/architecture.captions.json` (`captions.CAPTIONS_PATH`), flat JSON; only directive `@start`; absent → `{}`; any malformation → `ValueError` naming the file.
- API: `load(repo_root)`, `orphans(captions, known_paths, planned_paths) -> list[CaptionFinding(path, code ∈ {ORPHAN_CAPTION, UNKNOWN}, reason)]`, `for_cut(cut, captions) -> {key: prose}`, `start_ids(cut, captions)`; `to_mermaid(c, *, captions=None)` adds only `classDef start stroke-width:4px` + `class <ids> start`.
- Matching: dir key `a/b/` covers node `a/b` and every node inside it, never ancestors; file key covers its file and `file::symbol` nodes; symbol keys exist when their file does. `@start` also highlights a collapsed ancestor dir.
- Prose is never in the mermaid; M6 `--check` compares fences only (Ste).

## M6 facts (living doc, 2026-09-24, v0.15.0)
- CLI: `codemem draw --write` regenerates every registered view; `codemem draw --check` compares; bare `codemem draw` = M3 stdout emitter. Views mode refuses every cut option (exit 2). No/pre-v3/unreadable index: `--check` → UNKNOWN exit 0; `--write` → exit 1.
- Registry: `codemem.draw.views.VIEWS` — `readme` (docs/architecture/README.md), `component` (L2 whole repo, both kinds, tests excluded), `plugin-surface` (only where `claude-code/` exists). `registered_paths(repo_root)`.
- `--check` findings: `DRIFT <path>: missing | line 1 is not a codemem draw stamp | hand-edited captions block | differs from the code`; `ORPHAN_CAPTION <path>` vs `indexer.git_tracked_files` (planned set empty).
- Compare rule: all lines except line 1 (shape `^<!-- generated by codemem draw @ [0-9a-f]{7,40} on \d{4}-\d{2}-\d{2} -->$` required) and the `<!-- captions -->`…`<!-- /captions -->` contents (each line must match `^(- |Start here: )[^<>]*$`).
- Stamp: sha = HEAD at regeneration (parent of the carrying commit), UTC date.
- Regenerate everything: `scripts/regen-generated.sh` (build → draw --write → plugin-surface golden → --check). CI job: `architecture-drift` in security.yml.
- ADR-0016 Accepted; ADR-0015 Implemented (M11).

## M7 facts (2026-09-24)

- `src/aa_ma/deps.py`: `DepRef(raw, kind: Kind, number, task_slug)`, `Kind = Literal["milestone","step","none","cross-plan"]`; `parse_dependencies`, `resolve` (unresolved only), `dependency_fields`, `check` → `UNRESOLVED_DEPENDENCY <owner>: <ref>`, `milestone_graph` (round `M<n>("Milestone N: title")` nodes; `"`/`<`/`>` → `#quot;`/`#lt;`/`#gt;`), `advisory` → `Milestone X is ACTIVE but Milestone Y (Dependencies) is <STATUS>`; `MAX_SPAN = 100`, `MAX_FINDINGS = 200`. [valid: 2026-09-24]
- CLI: `python -m aa_ma.deps {graph|check|advisory} <tasks.md>` — exit 0 / 1 (check findings) / 2 (usage, unreadable). Shell: `aa_ma_deps` in `claude-code/hooks/lib/aa-ma-parse.sh` (uv notice rc 127; `timeout ${AA_MA_DEPS_TIMEOUT:-30}` when available). [valid: 2026-09-24]
- `grammar.py` additions: `CANONICAL_DEPENDENCY_RE` (`None` | `Milestone N` | `Sub-step N.N` | `<task-slug> Milestone N`, comma-separated), `NUMBER_BODY`, `own_text(block)` (gate + deps), `field_pattern(name)` (tui + deps; linear). [valid: 2026-09-24]
- Surfaces: `/aa-ma-plan` Step 5.5 appends `### Milestone graph` to §13 and runs `check`; `/execute-aa-ma-milestone` §5.1 step 3 advisory (always rc 0); §6.2 and `/execute-aa-ma-full` defer to it — no HALT on `Dependencies:`. `aa-ma-gate` never reads the field. [valid: 2026-09-24]
- Corpus (2026-09-24): 324 `Dependencies:` fields / 61 None / 1 cross-plan / 0 unresolved; naive M-stripping resolver: 29 false failures. [valid: 2026-09-24]

## M8 facts (2026-09-24)

- Sigils: `SIGILS = ("@import", "@call", "@skill", "@command", "@agent", "@hook")` in `src/aa_ma/render/mermaid_lint.py` (graph-backed `_EDGE_READERS` + `_PLUGIN_SIGILS`); pinned to codemem's emitter vocabulary by a test. [valid: 2026-09-24]
- Tiers: `PHANTOM_EDGE` (evaluable claim absent from the graph) and `LABEL_UNKNOWN` (unreserved `@` label) are findings → exit 1; `LintReport.unknowns` holds `UNKNOWN` notes (`endpoint planned (new)`, `no repo path in node label`, `endpoint outside the repo`, `not in the codemem graph for @x (...)`, graph MISSING/SCHEMA_TOO_OLD/STALE/unreadable reason, `@skill…: plugin-surface edges are not in the codemem index`, `unparsed sigil edge form`), printed as `file:line: UNKNOWN: reason`, never the exit. [valid: 2026-09-24]
- Parsed edge form: one whole line `ID[decl]? -->|label| ID[decl]?` (also `-.->`, `==>`); node ids scoped per fence, last declaration wins; `%%` lines skipped. Evaluability: endpoint `files.lang` has ≥1 edge of that kind (data, not a language list). [valid: 2026-09-24]
- `aa_ma.render.graph`: `+file_langs(h)`, `printable` now public. [valid: 2026-09-24]
- codemem: `ParseResult.from_imports` (module, level, [(name, local)]); `resolver._package_dir` / `_submodule`; `_persist_import_edges` returns `(targets, submodules)`; `sub.run()` binds only in `sub`. [valid: 2026-09-24]

## M9 facts (2026-09-25)

IO_DENSE_BAND repo=medical-research-skills sha=efafac209f3690c02f1ffc0f297f91c89747df69 edges=289 threshold=120 verdict=OVER

- The band line is authoritative. The prototype's throwaway scanner measured 285 for the same sha; the shipped pipeline (with vendored node_modules call edges and the alias fix) measures 289. Same verdict.
- The line above is regenerated byte-identically by `scripts/measure_io_band.sh ~/projects/github_private/medical-research-skills efafac2`. It builds from `git archive <sha>`, never the worktree; at efafac2 the repo tracks 1918 vendored `node_modules` JS/TS files, which its worktree has deleted. `edges` is the FILE-level count (qualified + bare, tests excluded); the drawn `io.md` collapses to L1. This repo @598f749: 43 edges, UNDER. [valid: 2026-09-25]
- API: `codemem.draw.io_sinks` — `load_catalogue(path=SINKS_PATH) -> Catalogue(sinks, qualified, bare)` (ValueError names the row; `yaml.safe_load`; list-valued `lang`/`symbol`; https `source`; `(lang, symbol)` unique); `classify(lang, callee, cat) -> (category, tier) | None` (qualified = whole callee; bare = last segment when a receiver exists); `io_edges(conn, cat, *, include_tests=False) -> list[IoEdge(src, lang, category, tier, calls)]`; `choose_level(edges, threshold=DENSE_BAND=120) -> (Level.L2 | Level.L1, edges)`; `band_line(repo, sha, edges)`; `python -m codemem.draw.io_sinks band <db> <name> <sha>`. [valid: 2026-09-25]
- Vocabulary: `LANGS = python, typescript, tsx, javascript, go`; `CATEGORIES = db, http, fs, subprocess, env, queue`; `TIERS = qualified, bare`. `sinks.yaml` = 41 rows. `open` is absent from it and stays in `_CALL_EXCLUDE`. Non-call boundaries (`os.environ[...]`, `process.env`) are out of v1. [valid: 2026-09-25]
- Mermaid: `mermaid.io_to_mermaid(edges, level)` (imports `IoEdge` only under TYPE_CHECKING, so the renderer never loads yaml); `mermaid.CATEGORY_LABEL` (keys = `io_sinks.CATEGORIES`). Subgraph `io_<lang>`, sink node `io_<lang>_<category>`, edges `n.. eN@-->|"calls"| io_..`; `TIER_STYLE` qualified `stroke-width:2px,stroke-dasharray:0` / bare `stroke-dasharray:4 4`, applied by `class eA,eB <tier>` lines (mermaid has no `:::` on edges). [valid: 2026-09-25]
- Registry: `views.VIEWS["io"]` → `docs/architecture/io.md` ("I/O boundary"), no captions block. `cut.collapse(path, level)` is the public L0/L1 folder rule. [valid: 2026-09-25]
- Parser: ast-grep `*-call` rules (ts/tsx/js/go) capture `$CALLEE`; the wrapper emits one unresolved `CallEdge` per (innermost enclosing function/method, callee); top-level calls and call-chained callees (`fetch(x).then`) are dropped. Enclosing function = one sorted sweep over `(line, col)` spans (`_SgMatch.col/end_col`), linear. Go methods are still skipped as orphans (M1 behaviour), so calls inside them are lost. Python: `from m import n [as k]; k()` is stored as `m.n`. [valid: 2026-09-25]
- `scripts/measure_io_band.sh` runs `uv run --project <its own checkout>`, so it works from any cwd. `scripts/regen-generated.sh` refuses (rc 1) while untracked files with an indexable extension exist (L-026). [valid: 2026-09-25]

## M10 facts (2026-09-25)

- `aa_ma.render.coverage`: `coverage_findings(plan_text) -> list[Finding("UNDRAWN_PATH", line, "<path>: …")]`; `contract_paths(plan_text, stripped) -> [(line, path)]`; `drawn_paths(plan_text, stripped) -> set | None`; `COVERAGE_CUTOVER = "2026-09-11"`. Not applicable (→ `[]`): `Created:` absent or earlier (`**Created:**` or `Created:` before the first H2), unterminated fence, no §13. [valid: 2026-09-25]
- Contract grammar read: the fences directly under `#### Contract` (the scan stops at the first line outside a fence); `Create`/`Modify` rows (text before `#`, comma lists, `{a,b}` expansion) and `# file: <path>` lines. Exempt: `Test`/`Verify` rows, `tests/`, `docs/`, README/CHANGELOG/SECURITY/CONTEXT.md, `pyproject.toml`, `package.json`, `*.lock`. Covered = a §13 `[...]` node label (after `(new)` is stripped) equals the path or is a directory above it. [valid: 2026-09-25]
- CLI: `aa-ma-lint-views <plan> --repo-root R --coverage` adds UNDRAWN_PATH to the findings (exit 1). Opt-in: nothing at execution time passes it. `mermaid_lint.section_13(plan_text, stripped)` is the one §13 locator. [valid: 2026-09-25]
- Skill: plan-verification check **8** (WARNING), grandfathered with #6/#7. AC4's proxy is scoped to check 8's text (check 2 calls the gate launcher since 38dfc82). [valid: 2026-09-25]
- Seeding: `/aa-ma-plan` Step 4.2b; `codemem draw --scope` is `action="append"`, the union of prefixes (`cut()` already accepted a tuple). [valid: 2026-09-25]
- Measured 2026-09-25: this plan 51 Contract paths / 0 undrawn (after drawing `coverage.py` + 2 `scripts/`); mattpocock-trio-adoption 8 / 0; plan-architecture-views (completed) 5 / 1. [valid: 2026-09-25]
- §6.8 hardening (M10): every Contract row token is a path (fail closed; `# comments`, `(parentheticals)` dropped; backticks and `:12-40` stripped; `- `/`| `/`Create:` accepted); every §13 label token counts as drawn; `_expand` iterative, `MAX_EXPANSIONS = 256` (past it the token stays whole); `EXEMPT_DIRS`/`ROOT_DOCS`/`MANIFESTS` public and tied to SKILL.md by a test; `--coverage` crash → `UNKNOWN: coverage could not run` exit 2; check 8's fence reads rc ∉ {0,1} as CRITICAL; mermaid_lint helpers `NEW_RE`, `mermaid_fences`, `node_labels` now public. [valid: 2026-09-25]

## M11 facts (2026-09-25, revised by §6.8 2026-09-26)

- Lint stdout: `sigils: edges=<N> checked=<C> phantom=<P> unknown=<K> invalid=<V> index-unknown=<I>` printed before `render:` on every run; `sigils: UNKNOWN (§13 not fully read)` when any sigil-slot line in the plan's ```mermaid fences went unread by the §13 view scan (unterminated fence, misspelled §13 heading, view without `###`). `edges` = sigil claims read; `checked` = compared with the graph (held or PHANTOM_EDGE); `phantom` = PHANTOM_EDGE + LABEL_UNKNOWN; `invalid`, `index-unknown` ⊆ `unknown`. Exit codes unchanged. [valid: 2026-09-26]
- Code: `LintReport.sigil_edges: int | None` (default None), `LintReport.sigil_checked`; constants `PHANTOM_EDGE`, `LABEL_UNKNOWN`, `SIGIL_FINDINGS`, `UNKNOWN_INDEX` (index missing/too old/stale/unreadable), `UNKNOWN_INVALID` (missing endpoint, stale `(new)` on an existing file, path-less label, unparsed form, outside the repo); all still print `UNKNOWN:`. `cli._sigil_summary`; the plan path is printed through `printable`. [valid: 2026-09-26]
- Launcher: `aa_ma_lint_views` in `claude-code/hooks/lib/aa-ma-parse.sh` — rc 0/1 passed through, 127 when uv is missing or no `render:` line came back. [valid: 2026-09-26]
- §6.7: the diagram fence is the SECOND ```bash fence after `### 6.7 ` (the first, the gate fence, sha256 17be760b… unchanged). Extract: `awk '/^### 6\.7 /{f=1} /^### 6\.8 /{f=0} f && /^```bash$/{n++; if (n == 2) {g=1; next}} g && /^```$/{exit} g'`. Refuses (exit 1): TASK_NAME not a plain slug, no ACTIVE milestone, lint rc>1, absent/UNKNOWN `sigils:` (last line wins), phantom>0, invalid>0, index-unknown>0. `edges=0` → "not applicable", no evidence. [valid: 2026-09-26]
- Evidence: `[ts] DIAGRAM_VERIFIED — <milestone heading> — edges=N checked=C phantom=0 unknown=K`, appended by the fence itself on PASS; the fence run is the check, nothing reads the line back. This plan after the §6.8 correction: edges=14 checked=11 phantom=0 unknown=3. [valid: 2026-09-26]
- Known gap: codemem `file_edges` holds module-level imports only — a function-local import reads PHANTOM_EDGE; label such edges in prose (ADR-0015; carry-forward in tasks.md). [valid: 2026-09-26]
- Tests: `tests/hooks/test_diagram_verified.bats` (21); `tests/render/test_{cli,phantom_edge}.py`. [valid: 2026-09-26]
- ADR-0015 Implemented. `engineering-standards.md` §1 `hook-modification` names `.github/workflows/**`; §5 row "`@kind` sigil edges verified (when §13 carries any)". [valid: 2026-09-26]
