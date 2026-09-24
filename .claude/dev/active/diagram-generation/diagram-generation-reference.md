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
   `tests/hooks/aa-ma-gate-python.bats:46` takes the FIRST ```bash fence after
   `### 6.7 `. 58 tests across three bats suites depend on it.
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

_Last Updated: 2026-09-22_

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
- ADR-0016 Accepted; ADR-0015 reserved for M11.

## M7 facts (2026-09-24)

- `src/aa_ma/deps.py`: `DepRef(raw, kind: Kind, number, task_slug)`, `Kind = Literal["milestone","step","none","cross-plan"]`; `parse_dependencies`, `resolve` (unresolved only), `dependency_fields`, `check` → `UNRESOLVED_DEPENDENCY <owner>: <ref>`, `milestone_graph` (round `M<n>("Milestone N: title")` nodes; `"`/`<`/`>` → `#quot;`/`#lt;`/`#gt;`), `advisory` → `Milestone X is ACTIVE but Milestone Y (Dependencies) is <STATUS>`; `MAX_SPAN = 100`, `MAX_FINDINGS = 200`. [valid: 2026-09-24]
- CLI: `python -m aa_ma.deps {graph|check|advisory} <tasks.md>` — exit 0 / 1 (check findings) / 2 (usage, unreadable). Shell: `aa_ma_deps` in `claude-code/hooks/lib/aa-ma-parse.sh` (uv notice rc 127; `timeout ${AA_MA_DEPS_TIMEOUT:-30}` when available). [valid: 2026-09-24]
- `grammar.py` additions: `CANONICAL_DEPENDENCY_RE` (`None` | `Milestone N` | `Sub-step N.N` | `<task-slug> Milestone N`, comma-separated), `NUMBER_BODY`, `own_text(block)` (gate + deps), `field_pattern(name)` (tui + deps; linear). [valid: 2026-09-24]
- Surfaces: `/aa-ma-plan` Step 5.5 appends `### Milestone graph` to §13 and runs `check`; `/execute-aa-ma-milestone` §5.1 step 3 advisory (always rc 0); §6.2 and `/execute-aa-ma-full` defer to it — no HALT on `Dependencies:`. `aa-ma-gate` never reads the field. [valid: 2026-09-24]
- Corpus (2026-09-24): 324 `Dependencies:` fields / 61 None / 1 cross-plan / 0 unresolved; naive M-stripping resolver: 29 false failures. [valid: 2026-09-24]
