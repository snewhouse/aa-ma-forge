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

- `Skill()` targets: **42** distinct as of 2026-09-22, while
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
5. `PHANTOM_EDGE` opt-in by sigil `A -->|@import| B`; unlabelled edges never checked; `LABEL_UNKNOWN` for typos
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
