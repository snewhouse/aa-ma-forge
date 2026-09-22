# Charting: diagram-generation

## Destination

The forge derives diagrams from code — module dependencies, call flow, data flow (I/O boundary), and the plugin's own markdown surface (commands→skills→agents→hooks) — for **two consumers**: (a) its own committed, CI-checked `docs/architecture/` living doc, and (b) **any project built with the plugin**, via one core in codemem exposed through three doors (MCP tool, `aa-ma-draw` CLI, `understand-codebase` Deep tier). Hand-authored §13 Component-view edges are verified against the derived graph (`PHANTOM_EDGE`, STALE_PATH tier), and the milestone graph is derived from a pinned `Dependencies:` grammar.

## Notes

- **Origin:** `~/.claude/docs/handover-aa-ma-forge-diagram-generation-2026-09-22.md` (audit @ `53a4ec7`). Correction to it: `PROJECT_INDEX.json` `deps` already holds file→imports (Python only) and **codemem** (in-repo, `packages/codemem-mcp`) parses Python `ast` + 9 ast-grep languages with `call` edges + `compute_pagerank`; neither parses markdown.
- **Graph source decided:** codemem (Q1). `.codemem/index.db` is stale (built at `5e2bf54`, 2026-04-17) — reindex before any prototype. `aa_ma` does not depend on `codemem` today; `.importlinter` `render-is-leaf` forbids `aa_ma.* → aa_ma.render`. `.codemem/index.db` is gitignored — CI `--check` must index first or read something committed (Ticket 8).
- **Standing constraints:** no new runtime dependency in `aa_ma` (ADR-0010 driver); pure-Python lint; `UNKNOWN` never `PASS` (L-012); `Diagram-Waiver` stays out of the gate (ADR-0009); mermaid text only (ADR-0010); `security.yml` / hooks changes carry `Critical-Path: hook-modification`; shellcheck `-S info` locally (L-019).
- **Glossary (CONTEXT.md:77-100):** Architecture View / View / Component view / Flow view / Data-State view / **Milestone graph** ("derived mechanically from tasks.md `Dependencies:` — never hand-authored" — promised, undelivered). Candidate terms for the plan-phase glossary update (charting does not edit CONTEXT.md): *Derived View* vs *Authored View*, *Phantom edge*, *Plugin surface*, *I/O-boundary view*, *Living architecture doc*.
- **Skills every session consults:** `Skill(grill-with-docs)` (HITL tickets), `Skill(aa-ma-research)` (research), `Skill(prototype)` (Ticket 3), `Skill(impact-analysis)` before any plan step touches `mermaid_lint.py` / `grammar.py`.
- Grill rounds 1–4 held 2026-09-22 with Ste; decisions Q1–Q10 recorded in ticket Answers / Destination.

## Decisions so far

<!-- one line per RESOLVED ticket, newest last -->

- [Ticket 1: Can codemem persist file-level `import` edges and qualified external callees?](#ticket-1-can-codemem-persist-file-level-import-edges-and-qualified-external-callees): yes — new `file_edges` table (MIGRATIONS v3), Python ≈80 LOC, ast-grep +100-140 LOC; keep dotted callee ≈15 LOC.
- [Ticket 10: Prior art — code→mermaid tools and their scoping heuristics](#ticket-10-prior-art--codemermaid-tools-and-their-scoping-heuristics): own emitter (no zero-dep reuse); heuristics = package collapse, 1–2 hop neighbourhood, regex filters, externals off; import-level for Component view; mermaid `maxEdges` 500.
- [Ticket 4: How reliably can the plugin surface be extracted from `claude-code/**/*.md`?](#ticket-4-how-reliably-can-the-plugin-surface-be-extracted-from-claude-codemd): regex suffices — 4 syntaxes, 163 edges, 52/59 nodes, 0 FPs; node id = file stem; docs/ out; 3 allowlists; 4 dangling + 7 orphans found.
- [Ticket 6: I/O-boundary sink catalogue per language](#ticket-6-io-boundary-sink-catalogue-per-language): feasible all 9, v1 = Py+TS/JS+Go; ast-grep `has: field: function` captures receivers (verified); wrapper ≈50 LOC; two confidence tiers; ≈55-row catalogue; CodeQL MaD reusable (MIT), Semgrep not.
## Tickets

### Ticket 1: Can codemem persist file-level `import` edges and qualified external callees?
- Type: research
- Mode: AFK
- Status: RESOLVED
- Blocked-by: —
#### Question
`python_ast.py` collects `imports: list[str]` and `resolver._resolve_import` maps them, but `edges` holds only `kind='call'` (1460 rows) and unresolved sinks are unqualified (`execute`, `connect`, `get`). What is needed — parser, resolver, `schema.sql`, `incremental.py` — to (a) persist `kind='import'` edges file→file for Python and the ast-grep languages, and (b) keep the qualified dotted callee (`sqlite3.connect`) in `dst_unresolved`? Does any ast-grep rule already capture the receiver? Cost per language. Read the code; do not guess.
#### Answer
**Yes, with a new table.** Today no import edges exist: `ParseResult.imports` (python_ast.py:113-120, Python only) is consumed transiently by `resolver.py:131-134` and never written; `edges` is symbol→symbol with no file node and no module-level symbols (1460 rows, all `kind='call'`, 0 dotted `dst_unresolved`). ast-grep: 6/8 rule files have a bare `*-import` rule with no capture and the wrapper drops it; Ruby/Bash have none; ast-grep emits zero edges. Callee is truncated at python_ast.py:370-377 (`func.attr`; `self.conn.execute()` dropped entirely) — ≈15 LOC to keep the dotted name, flips two `test_resolver.py` assertions. **Recommended design:** new `file_edges` table via MIGRATIONS v3 (db.py:41,104-106), not synthetic module symbols (those disturb 5 symbol-count tests + PageRank). Python-only ≈80 LOC / 5 files; ast-grep import edges ≈100-140 LOC + 8 YAML edits, non-Python specifier resolution is the uncertain part. Existing tools filter `kind='call'`, so nothing pollutes. Caveat: `.codemem/index.db` was built at `5e2bf54` (2026-04-17), not HEAD. See `docs/research/diagram-generation-codemem-import-edges.md`.

### Ticket 2: Where does the mermaid emitter live, and how does `aa_ma.render` read the graph?
- Type: grilling
- Mode: HITL
- Status: OPEN
- Blocked-by: 1
#### Question
Options: (a) emitter in `codemem` (MCP tool `diagram` + CLI) and `aa_ma.render.mermaid_lint` reads `.codemem/index.db` via stdlib `sqlite3` (no package import, `render-is-leaf` intact); (b) `aa_ma` gains a runtime dependency on `codemem` (workspace member — is that a "new runtime dependency" under ADR-0010?); (c) codemem exports a JSON graph file the lint and emitter both read. Decide direction, the CLI name (`aa-ma-draw`?), which package owns `pyproject` scripts, and the `.importlinter` contract changes.

### Ticket 3: What scoping makes a derived View readable?
- Type: prototype
- Mode: HITL
- Status: OPEN
- Blocked-by: —
#### Question
725 call edges is a hairball. On branch `prototype/diagram-generation-3`, draw this repo three ways from the existing `call` edges: module-level collapse; pagerank top-N (`compute_pagerank`) with edges; `--scope <path>` entry-point call flow. Ste picks the shape by looking. Output: the decision + node/edge caps; main keeps only the decision.

### Ticket 4: How reliably can the plugin surface be extracted from `claude-code/**/*.md`?
- Type: research
- Mode: AFK
- Status: RESOLVED
- Blocked-by: —
#### Question
Inventory every reference syntax in commands/skills/agents/hooks/rules: `Skill(name)`, `/command`, agent names (`subagent_type`, "Spawned by"), hook script names, `Read`/path refs, `Bash(...)` invocations. For each: regex, hit count in this repo, false-positive/negative examples. Is regex enough, or does it need a codemem markdown "parser" (rule out or confirm)? Compare with the manual cross-ref grep in CLAUDE.md ("No broken references").
#### Answer
**Regex is sufficient; no codemem markdown parser needed.** Four curated syntaxes — `Skill(x)`, `/x` filtered against `commands/*.md`, `subagent_type: x`, `<hook>.sh` literals — yield 163 edges from 42 files, reaching 52/59 on-disk nodes (13 cmd / 21 skill / 12 agent / 11 hook / 2 rule) with no observed false positives after the on-disk filter. **Node identity must come from dir/file stem, not frontmatter** (6/21 SKILL.md open with an HTML comment; 1 `name:` ≠ dirname; 2/13 commands lack `name:`). `Bash(...)` has 0 hits; `uv run aa-ma-*` misses 15/16 bare CLI mentions (drop it). Of 41 `Skill()` targets: 17 on disk, 20 external (`~/.claude/skills`, gstack → render as `external` node kind), 4 truly dangling (`Skill(aa-ma-plan)` wrong kind, `Skill(haiku-eval)`, `Skill(index)`, `Skill(codebase-deep-dive)`). 7 orphans (`aa-ma-search`, `sole-dev-merge`, `aa-ma-execution`, `complexity-router`, `debugging-strategies`, `write-a-skill`, `aa-ma-session-end-dirty.sh`) — backtick-only or wired solely in `scripts/install.sh:314-323`. **`docs/` is OUT of the graph** (historical names). Three small allowlists needed: install.sh hook-event table, external-skill list, self-edge/glob suppression. See `docs/research/diagram-generation-plugin-surface-extraction.md`.

### Ticket 5: Exact `PHANTOM_EDGE` grammar
- Type: grilling
- Mode: HITL
- Status: OPEN
- Blocked-by: 2, 4
#### Question
Decided: finding at STALE_PATH tier; escape hatch exists; no graph → `UNKNOWN`. Open: which edge kinds back an authored edge (import only, or import ∪ call)? Escape-hatch syntax — dotted `A -.-> B` vs label suffix `(intent)` vs both? Nodes the graph cannot see (`.md`, `.sh` without edges, `(new)` files) — per-edge `UNKNOWN` or silent skip? Subgraph edges? Does `Diagram-Waiver` interplay change?

### Ticket 6: I/O-boundary sink catalogue per language
- Type: research
- Mode: AFK
- Status: RESOLVED
- Blocked-by: 1
#### Question
For the 9 codemem languages, a curated list of source/sink symbols by category (DB, HTTP, filesystem, subprocess, env/secrets, message queue) that a data-flow View would key on, and whether each language's parser output can match them qualified. Prior art: Semgrep taint sources/sinks, CodeQL flow sources. Output a table the emitter can ship as data.
#### Answer
**Feasible for all 9 languages; v1 = Python + TS/TSX/JS + Go.** Verified live with ast-grep 0.42.1: adding `has: {field: function, pattern: $CALLEE}` to the existing `*-call` rules yields full `fs.readFileSync` / `this.db.query` / `s.conn.Exec` / `std::fs::read_to_string`; Java and Ruby need two metavariables joined in the wrapper (Ruby also a no-receiver rule), Bash a new `kind: command` rule. Shared wrapper change ≈50 LOC (`ast_grep.py:119-123` + a `-call` branch with enclosing-function inference) + 3–12 LOC YAML per language. Python: Ticket 1's ≈15 LOC gives `mod.func` / `obj.method` / chained `self.conn.execute` via `ast.unparse`, **plus** an import-alias map (≈10 LOC; `asname` / `from X import Y` dropped at python_ast.py:113-120); `open` must leave `_CALL_EXCLUDE`; `os.environ[...]` / `process.env` are non-call nodes needing a separate visitor/rule. Receiver typing (`conn.execute` → sqlite3) is resolver work → ship a **qualified tier (high precision) + bare-method tier (low confidence)**. Catalogue ≈55 rows (9 langs × 7 categories) with official-doc URL per row; proposed YAML row shape `lang/category/match/symbol/tier/source`. Prior art: Semgrep Rules License v1.0 forbids redistribution (borrow vocabulary only); CodeQL is MIT and its Models-as-Data `*.model.yml` is reusable seed data for Java/JS (injection-scoped, under-covers plain I/O). See `docs/research/diagram-generation-io-sink-catalogue.md`.

### Ticket 7: Pin the `Dependencies:` grammar and where the Milestone graph surfaces
- Type: grilling
- Mode: HITL
- Status: OPEN
- Blocked-by: —
#### Question
In the wild: `Dependencies: None` (52), `Milestone 1` (11), `Step 1.1` (9), `Task 3.1` (8), bold and plain forms. Canonical form for `grammar.py` (ADR-0009 SSoT), lenient parse of legacy, whether `aa-ma-gate` ever reads it (probably not — planning-time only, like `Diagram-Waiver`). Where the derived graph appears: `aa-ma-draw`, TUI TaskDetailScreen, plan §13, all three? Does the scribe write it?

### Ticket 8: Living-doc contract and CI `--check`
- Type: grilling
- Mode: HITL
- Status: OPEN
- Blocked-by: 2, 3
#### Question
`docs/architecture/` file set (one file per View kind? one per package?), front-matter marking them generated, `aa-ma-draw --check` exit semantics, and how `security.yml` gets a graph when `.codemem/index.db` is gitignored (index step in CI vs commit a JSON export vs compare against the committed doc only). `Critical-Path: hook-modification` applies.

### Ticket 9: `understand-codebase` Deep tier rewire
- Type: grilling
- Mode: HITL
- Status: OPEN
- Blocked-by: 2
#### Question
Deep tier (`references/DIMENSIONS.md:52-56`, `DEEPDIVE-TEMPLATES.md:315-317`, `SKILL.md:181-182`) tells agents to "generate Mermaid" or link `/codebase-deep-dive` output — a command the plugin does not ship (gap 6). Replace with the three doors: which door, what the tier does when no codemem index exists (`UNKNOWN`, degrade to prose, or refuse), and whether `/codebase-deep-dive` references are deleted or kept as optional.

### Ticket 10: Prior art — code→mermaid tools and their scoping heuristics
- Type: research
- Mode: AFK
- Status: RESOLVED
- Blocked-by: —
#### Question
pydeps, pyan3, code2flow, dependency-cruiser, madge, Structurizr/C4 generators, Sourcetrail, `import-linter` graph output: what each emits, how each tames size (clustering, max-depth, exclude patterns, rank), edge semantics (import vs call), mermaid support. Feed Ticket 3's prototype and Ticket 5's edge-kind decision. Primary sources only.
#### Answer
**Write our own emitter over codemem's index; nothing is reusable zero-dep.** All tools emit DOT first; mermaid is native only in dependency-cruiser (`--output-type mermaid`), tach (`tach show --mermaid`), pyreverse (`-o mmd`). None can be imported by `aa_ma` without a new dependency (pydeps→stdlib_list+dot, tach→networkx+pydot, pyan3/pyreverse GPL, import-linter emits no graph, grimp dev-only). **Recurring scoping heuristics** (feed Ticket 3): (1) collapse to package depth (`--max-module-depth`, `--collapse`, `squash_module`); (2) hop-limited entry-point neighbourhood (`--max-bacon` default 2, `--focus-depth` default 1); (3) include/exclude regex; (4) externals off by default, typed edges; (5) cycle/reverse views. **PageRank top-N has no diagram-tool prior art** — only aider's repo-map budget (already ported into codemem) — so it is Ticket 3's novel arm. **Edge semantics:** import-level is the universal default for architecture views; call-level tools all carry "approximate" disclaimers → import-level for Component view, call-level only inside a scoped entry-point view (input to Ticket 5). **Ceilings:** only hard number is mermaid `maxEdges` default 500 (`maxTextSize` 50000); practical ceiling is tool defaults (1–2 hops, top-level package collapse). See `docs/research/diagram-generation-prior-art.md`.

## Not yet specified

- Whether `/aa-ma-plan` seeds §13 Component view from the generator (scoped to files-to-modify) with the author editing after — decide after seeing Ticket 3 output (Q10).
- Type/schema-flow View (Pydantic/dataclass producers/consumers) — "both, I/O first" (Q6); graduates once codemem tracks class references.
- MCP `diagram` tool budget/truncation behaviour on large consumer repos (codemem `_DEFAULT_BUDGET` pattern).
- Does the forge's own living doc also carry a forge-specific AA-MA-artifact data-flow View (which modules/hooks read/write plan/tasks/reference/context-log/provenance/map), or only the generic I/O view?
- Multi-language consumer repos: one View per language, or merged with language subgraphs?
- Freshness of `PROJECT_INDEX.json`-based skills (`impact-analysis`, `understand-codebase` REUSE-MAP) once codemem is the graph source — retire or keep both?

## Out of scope

- SVG/PNG/excalidraw export — mermaid text only; gstack `/diagram` already renders (default from Q11, unconfirmed).
- Languages beyond codemem's 9 — no new parsers in this effort (default from Q11, unconfirmed).
- `senior-architect` `architecture_diagram_generator.py` stub — global skill, not forge; note in TODOS (default from Q11, unconfirmed).
- C4 / D2 / any non-mermaid notation — ADR-0010 chose mermaid (default from Q11, unconfirmed).
