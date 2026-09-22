# Charting: diagram-generation

## Destination

The forge derives diagrams from code — module dependencies, call flow, data flow (I/O boundary), and the plugin's own markdown surface (commands→skills→agents→hooks) — for **two consumers**: (a) its own committed, CI-checked `docs/architecture/` living doc, and (b) **any project built with the plugin**, via one core in codemem exposed through three doors (MCP tool, `codemem draw` CLI, `understand-codebase` Deep tier). Hand-authored §13 Component-view edges are verified against the derived graph (`PHANTOM_EDGE`, STALE_PATH tier), and the milestone graph is derived from a pinned `Dependencies:` grammar.

**Audience (amended 2026-09-22):** the primary reader is a **new developer or reviewer onboarding to a codebase**, not only a cold planning agent. "Readable" therefore means *orienting*: a layered set of zoom levels, clickable drill-down in self-contained HTML, and authored captions over the derived graph. A diagram that passes an edge-count check but leaves a newcomer unable to say where to start has failed.

## Notes

- **Origin:** `~/.claude/docs/handover-aa-ma-forge-diagram-generation-2026-09-22.md` (audit @ `53a4ec7`). Correction to it: `PROJECT_INDEX.json` `deps` already holds file→imports (Python only) and **codemem** (in-repo, `packages/codemem-mcp`) parses Python `ast` + 9 ast-grep languages with `call` edges + `compute_pagerank`; neither parses markdown.
- **Graph source decided:** codemem (Q1). `.codemem/index.db` was stale (built at `5e2bf54`, 2026-04-17); reindexed at HEAD 2026-09-22 during Ticket 8 — a full build is 0.44s. `aa_ma` does not depend on `codemem` today; `.importlinter` `render-is-leaf` forbids `aa_ma.* → aa_ma.render`. `.codemem/index.db` is gitignored — CI `--check` must index first or read something committed (Ticket 8).
- **Standing constraints:** no new runtime dependency in `aa_ma` (ADR-0010 driver); pure-Python lint; `UNKNOWN` never `PASS` (L-012); `Diagram-Waiver` stays out of the gate (ADR-0009); mermaid text only (ADR-0010); `security.yml` / hooks changes carry `Critical-Path: hook-modification`; shellcheck `-S info` locally (L-019).
- **Glossary (CONTEXT.md:77-100):** Architecture View / View / Component view / Flow view / Data-State view / **Milestone graph** ("derived mechanically from tasks.md `Dependencies:` — never hand-authored" — promised, undelivered). Candidate terms for the plan-phase glossary update (charting does not edit CONTEXT.md): *Derived View* vs *Authored View*, *Phantom edge*, *Plugin surface*, *I/O-boundary view*, *Living architecture doc*, *Explorer* (Ticket 11 — the graph-sourced interactive HTML; **not** a *Render*, which CONTEXT.md defines as markdown-sourced).
- **Skills every session consults:** `Skill(grill-with-docs)` (HITL tickets), `Skill(aa-ma-research)` (research), `Skill(prototype)` (Ticket 3), `Skill(impact-analysis)` before any plan step touches `mermaid_lint.py` / `grammar.py`.
- Grill rounds 1–4 held 2026-09-22 with Ste; decisions Q1–Q10 recorded in ticket Answers / Destination.

## Decisions so far

<!-- one line per RESOLVED ticket, newest last -->

- [Ticket 1: Can codemem persist file-level `import` edges and qualified external callees?](#ticket-1-can-codemem-persist-file-level-import-edges-and-qualified-external-callees): yes — new `file_edges` table (MIGRATIONS v3), Python ≈80 LOC, ast-grep +100-140 LOC; keep dotted callee ≈15 LOC.
- [Ticket 10: Prior art — code→mermaid tools and their scoping heuristics](#ticket-10-prior-art--codemermaid-tools-and-their-scoping-heuristics): own emitter (no zero-dep reuse); heuristics = package collapse, 1–2 hop neighbourhood, regex filters, externals off; import-level for Component view; mermaid `maxEdges` 500.
- [Ticket 4: How reliably can the plugin surface be extracted from `claude-code/**/*.md`?](#ticket-4-how-reliably-can-the-plugin-surface-be-extracted-from-claude-codemd): regex suffices — 4 syntaxes, 163 edges, 52/59 nodes, 0 FPs; node id = file stem; docs/ out; 3 allowlists; 4 dangling + 7 orphans found.
- [Ticket 6: I/O-boundary sink catalogue per language](#ticket-6-io-boundary-sink-catalogue-per-language): feasible all 9, v1 = Py+TS/JS+Go; ast-grep `has: field: function` captures receivers (verified); wrapper ≈50 LOC; two confidence tiers; ≈55-row catalogue; CodeQL MaD reusable (MIT), Semgrep not.
- [Ticket 3: What scoping makes a derived View readable?](#ticket-3-what-scoping-makes-a-derived-view-readable): layered zoom levels L0–L3, not one knob; tests excluded by default; PageRank ruled out as default (surfaces sinks, not entry points); bands 40/120/500.
- [Ticket 13: Export formats and notation re-evaluation (re-admitted to scope)](#ticket-13-export-formats-and-notation-re-evaluation-re-admitted-to-scope): mermaid only (D2's layout edge expired — mermaid 12 bundles ELK); optional SVG/PNG via the existing `MMDC_BIN` seam; hosted renderers ruled out (source leaks); pin held at 11.17.2.
- [Ticket 2: Where does the mermaid emitter live, and how does `aa_ma.render` read the graph?](#ticket-2-where-does-the-mermaid-emitter-live-and-how-does-aa_marender-read-the-graph): direction (a) — `aa_ma.render` reads `.codemem/index.db` via stdlib `sqlite3` pinned at `user_version >= 3`; missing/stale ⇒ PHANTOM_EDGE tier `UNKNOWN`, never PASS; emitter and door are **`codemem draw`** (not `aa-ma-draw` — Destination amended); new `.importlinter` contract `aa-ma-never-imports-codemem` (verified: 4 kept, 0 broken).
- [Ticket 5: Exact `PHANTOM_EDGE` grammar](#ticket-5-exact-phantom_edge-grammar): opt-in by sigil label `A -->|@import| B` (reserved `@import @call @skill @command @agent @hook`); unlabelled/prose edges never checked (a blanket import∪call check would fire on ~14 of 21 correct edges in a real committed view); unknown `@x` ⇒ `LABEL_UNKNOWN`; one `UNKNOWN`+reason policy for `(new)`/unparsed/`docs/`/stale-graph; absent-but-evaluable ⇒ `PHANTOM_EDGE`, exit 1.
- [Ticket 11: Clickable drill-down — mechanics and where the HTML lives](#ticket-11-clickable-drill-down--mechanics-and-where-the-html-lives): delegated DOM listener with `securityLevel: 'strict'` unchanged (strict disables `click href` too, and `click` lines would pollute the committed fence); embedded-graph explorer deriving levels client-side, as the prototype proved; built by `aa-ma-render --explorer` in `aa_ma.render` reusing html.py's CSP/SRI/pin; Py+JS generators reconciled by a shared node-id/collapse fixture, not a golden render; `build/`-only, never committed.
- [Ticket 14: Does `/aa-ma-plan` seed the §13 Component view from the generator?](#ticket-14-does-aa-ma-plan-seed-the-13-component-view-from-the-generator): yes — Phase 4 pastes the L2 cut into §13 with `@kind` sigils already attached (47% / 23% of nodes in real committed views are `(new)` and underivable, but seeded edges are the only route to a non-vacuous PHANTOM_EDGE); anchoring countered by an Angle 6 coverage rule (every `#### Contract` file path must appear as a §13 node), planning-time only; intended edges carry sigils, so the diagram becomes an acceptance criterion that flips from UNKNOWN to checked when the code lands.
- [Ticket 12: Annotation layer — format and how the lint keeps it in sync](#ticket-12-annotation-layer--format-and-how-the-lint-keeps-it-in-sync): flat path-keyed JSON sidecar `{"@start": <path>, "<path>": "<prose>"}` read by both the Python emitter and the JS explorer generator (YAML ruled out — not a declared aa-ma dep; `%%` comments ruled out — invisible at render); zoom levels handled free by path keying; `ORPHAN_CAPTION` at STALE_PATH tier with prose never auto-deleted; edge rationale stays in prose, captions-only diffs are not drift.
- [Ticket 8: Living-doc contract and CI `--check`](#ticket-8-living-doc-contract-and-ci---check): `docs/architecture/{README,component,io,plugin-surface}.md`, all four 100% generated (captions render in from the Ticket 12 sidecar); `codemem draw --check` is regenerate-and-compare, exit 1 on diff, `UNKNOWN`+exit 0 when no graph; `<!-- generated … @ <sha> -->` line 1 excluded from the comparison (a byte check and a volatile stamp are otherwise mutually exclusive); dedicated `architecture-drift` CI job — CI already builds the index in 0.44s, so committing a JSON export has no case.
- [Ticket 15: Does a §13 sigil edge still `UNKNOWN` at milestone COMPLETE reach the gate?](#ticket-15-does-a-13-sigil-edge-still-unknown-at-milestone-complete-reach-the-gate): not the gate — a HARD §6.7 Execution Checklist item enforced by the command (HARD ≠ `gate.py`, which takes only `tasks_md` while §13 lives in `plan.md`); opt-in, so a plan without sigils never triggers it; `UNKNOWN` refuses per L-012 with `codemem build` named as the 0.44s remedy; evidence is a `DIAGRAM_VERIFIED` provenance line.
- [Ticket 9: `understand-codebase` Deep tier rewire](#ticket-9-understand-codebase-deep-tier-rewire): Deep tier always runs `codemem draw` in the target repo (uninvited-diff cost accepted over the consent-gated AGENTS.md-protocol alternative); `docs/architecture/` canonical, bundle links it, `.mmd` sidecars retired; only the ~4 assertive `/codebase-deep-dive` refs fixed of 45 (the rest are conditional reuse, a fall-through not a break); no-index is moot — `ensure_built` provisions in 0.44s; MCP door emits ASCII only today, so mermaid is new work through any door.
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
- Status: RESOLVED
- Blocked-by: 1
#### Question
Options: (a) emitter in `codemem` (MCP tool `diagram` + CLI) and `aa_ma.render.mermaid_lint` reads `.codemem/index.db` via stdlib `sqlite3` (no package import, `render-is-leaf` intact); (b) `aa_ma` gains a runtime dependency on `codemem` (workspace member — is that a "new runtime dependency" under ADR-0010?); (c) codemem exports a JSON graph file the lint and emitter both read. Decide direction, the CLI name (`aa-ma-draw`?), which package owns `pyproject` scripts, and the `.importlinter` contract changes.
#### Answer
**Direction (a), with the coupling made explicit rather than implicit.** Grill round 5 with Ste, 2026-09-22.

**Corrections to the ticket's framing, from the code:**
- `render-is-leaf` was never the constraint. `.importlinter:47-67` forbids only `aa_ma.* → aa_ma.render`; nothing there forbids `aa_ma.render → codemem`. All three options left it untouched.
- ADR-0010's driver reads "must keep working with what `uv sync` already installs" (`docs/adr/0010-…:36-37`), and `uv sync` **does** install `codemem-mcp` today (`pyproject.toml:56` — dev-dep + workspace member, added so `uv run codemem intel` resolves). So (b) breaks that driver only for a consumer installing `aa-ma` without dev-deps — who would then pull `fastmcp` + `ast-grep-cli` + `tiktoken` (`packages/codemem-mcp/pyproject.toml:22-26`) in order to run a lint. That consumer cost killed (b), not the contract.
- (c) already half-exists: `codemem intel` writes `PROJECT_INTEL.json` (`cli.py:249`, `pagerank.py`) — but it is PageRank-ranked, which Ticket 3 ruled out as default scoping.

**Decisions:**
1. **Graph read** — `aa_ma.render` opens `.codemem/index.db` with stdlib `sqlite3` (new `aa_ma/render/graph.py`). No new runtime dependency for `aa-ma`; the consumer install set is unchanged.
2. **Schema coupling is pinned, not implicit** — the read asserts `PRAGMA user_version >= 3` (`storage/db.py:12,104,166`; `file_edges` is v3 per Ticket 1, `MIGRATIONS` is at v2 today). Staleness comes from `files.mtime` (`schema.sql:26`) vs on-disk mtime — no commit SHA needed, and none is stored.
3. **Degradation contract** — DB missing, `user_version < 3`, or stale ⇒ the **PHANTOM_EDGE tier alone** reports `UNKNOWN` with the reason and the remedy (`run: codemem build`), never PASS (L-012). The existing structural checks (STALE_PATH, UNKNOWN_TYPE, render) run as today and keep owning the exit code. Mirrors the `render_status: PASS | FAIL | UNKNOWN` precedent at `mermaid_lint.py:76`. Exit codes unchanged: 0 / 1 / 2.
4. **Emitter + CLI door** — the emitter lives in `codemem` (where the graph and the heavy deps already are) and the door is **`codemem draw`**: one `add_parser` on the existing subcommand CLI (`cli.py:269-309`), **not** `aa-ma-draw`. An `aa-ma-*` console script must be declared by a package that can import the emitter — either `codemem-mcp` (a package named codemem shipping an `aa-ma-*` binary) or `aa-ma` (= option (b), rejected). No `[project.scripts]` change in either package. **Destination amended accordingly.**
5. **New `.importlinter` contract `aa-ma-never-imports-codemem`** (`type = forbidden`, `source_modules = aa_ma`, `forbidden_modules = codemem`) so the sqlite3 seam cannot later be "simplified" into an import. One-directional — `codemem → aa_ma` stays legal (`codemem/aa_ma_integration.py`). **Verified empirically** against a scratchpad copy of `.importlinter`: `Contracts: 4 kept, 0 broken` (it parses; the file's "shared descendants" caveat applies only when source and forbidden share a root package, which `aa_ma` and `codemem` do not).

**Downstream constraints this sets:** Ticket 8's CI `--check` inherits a gitignored `.codemem/` (`.gitignore:17-18`) plus a lint that tolerates its absence — so CI must index before checking, or knowingly accept an `UNKNOWN` PHANTOM_EDGE tier. Ticket 5's `PHANTOM_EDGE` grammar must carry an `UNKNOWN` state with a reason string, not merely found/not-found.


### Ticket 3: What scoping makes a derived View readable?
- Type: prototype
- Mode: HITL
- Status: RESOLVED
- Blocked-by: —
#### Question
725 call edges is a hairball. On branch `prototype/diagram-generation-3`, draw this repo three ways from the existing `call` edges: module-level collapse; pagerank top-N (`compute_pagerank`) with edges; `--scope <path>` entry-point call flow. Ste picks the shape by looking. Output: the decision + node/edge caps; main keeps only the decision.
#### Answer
**Not one scoping knob — a layered set of zoom levels, one mermaid block per level.** Prototype on branch `prototype/diagram-generation-3` (commit `1136dbe`, `prototype/diagram-generation-3/demo.html`, real codemem call edges at `c49d084`: 175 files, 1185 resolved call edges, 616 cross-file). Measured:

| Level | Cut | Nodes / edges |
|---|---|---|
| L0 | top dirs (depth 1) | 4 / 3 |
| L1 | dir depth 2 / 3 | 10 / 9 · 13 / 11 |
| L2 | file level, one scope, 1 hop both (`src/aa_ma/render/`) | 5 / 4 |
| L3 | symbol level, 1 hop down (`gate.py`) | 18 symbols / 27 |
| — | raw file level, whole repo | 85 / 96 (25 / 27 without `tests/`) |

Findings: (1) **tests dominate the raw graph** (96 → 27 edges when excluded) — exclude by default, but keep the tests→src coupling picture as its own L1 view, where weighted edges (`-- "170" -->`) read well. (2) **PageRank top-N is ruled out as the default**: its top-10 for this repo is `plan_parsers`, `grammar`, `tui/model`, `sanitizers` — most-depended-upon *sinks*, not entry points, so it answers "what is load-bearing", never "where do I start". Keep it as an optional annotation/ranking, not a scoping arm. (3) **Symbol level is dense even at 1 hop** (27 edges from one file) — reserve for a scoped Flow view. (4) Observed readability bands: ≤40 edges readable, ≤120 dense, mermaid `maxEdges` 500 the hard stop. (5) The interactive shell mattered as much as the cut: switching levels and watching node/edge counts is what made the trade-off visible — evidence for Ticket 11. Decided with Ste 2026-09-22.

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
- Status: RESOLVED
- Blocked-by: 2, 4
#### Question
Decided: finding at STALE_PATH tier; escape hatch exists; no graph → `UNKNOWN`. Open: which edge kinds back an authored edge (import only, or import ∪ call)? Escape-hatch syntax — dotted `A -.-> B` vs label suffix `(intent)` vs both? Nodes the graph cannot see (`.md`, `.sh` without edges, `(new)` files) — per-edge `UNKNOWN` or silent skip? Subgraph edges? Does `Diagram-Waiver` interplay change?
#### Answer
**Opt-in by sigil label: `A -->|@import| B`.** Grill round 6 with Ste, 2026-09-22.

**The framing was wrong, and the evidence says so.** The ticket assumed the question was "import only, or import ∪ call". Classifying all 21 edges of the committed Component view in `.claude/dev/completed/mattpocock-trio-adoption/mattpocock-trio-adoption-plan.md` against what any derived source could know: only ~7 are backable (plugin-surface `Skill()` / hook-literal edges from Ticket 4). The other ~14 encode relations **no graph models** — fork provenance (`UP -->|fork| GR`), CI-runs-test (`security.yml --> tests/test_gate.py`), reads-config (`FORKS.json --> forks.py`), paths with placeholders (`.claude/dev/charting/<effort>/…`), or point at `docs/`, which Ticket 4 put out of the graph. One is outright **reversed** by intent: the author drew `src/aa_ma/forks.py --> tests/skills/test_fork_manifest.py` ("is exercised by"), while the derived import edge runs test→src. A blanket check over import ∪ call would have fired on two-thirds of a diagram that is entirely correct.

**Also load-bearing:** the lint has **no edge parser today** — `lint_text` only scans path-shaped tokens (`_PATH_RE`, `mermaid_lint.py:60-63`) and never reads `A --> B`. PHANTOM_EDGE is the first check that must parse mermaid edges. Authored plans today use `-->` (120) and zero `-.->`  / `==>`, so a dotted-arrow escape hatch would introduce a syntax nobody uses; `(new)` is already house style (31 uses, `mermaid_lint.py:281`).

**Decisions:**
1. **Eligibility is opt-in, not inferred.** An authored edge is checked **only** when its label carries the sigil. Unlabelled and prose-labelled edges are never checked and never reported — the author states the claim, the lint verifies exactly that claim and nothing else. False-positive rate on every diagram committed to date: zero.
2. **Sigil syntax `@kind` inside the mermaid edge label** — `PL -->|@skill| GWD`. Reserved: **`@import` `@call` `@skill` `@command` `@agent` `@hook`**. `@import` reads `file_edges` (Ticket 1); `@call` reads `edges` (`kind='call'`, projected symbol→file); the other four read the plugin-surface edge set (Ticket 4), filtered on destination node kind. Prose labels (`|fork|`, `|runs|`, `|--from-map|`) never collide because they carry no sigil.
3. **Typos are loud, not silent.** Any `@`-prefixed label that is not reserved is a **`LABEL_UNKNOWN`** finding. This is the whole reason for the sigil: opt-in checks otherwise fail silently (`|imports|` skips, and the author believes the edge was verified — false assurance is worse than no check). A closed enum in the house style of `Critical-Path` / `Diagram-Waiver` is impossible here, because free prose labels must stay legal.
4. **One policy for anything unevaluable: `UNKNOWN` + a specific reason, informational, exit code unchanged.** Covers all four cases uniformly — endpoint marked `(new)` (planned, not built); endpoint in a language the graph never parses (`.sh`, `.yml`); endpoint under `docs/` (out of graph by Ticket 4); and graph missing / `user_version < 3` / stale (Ticket 2). No `LABEL_KIND_MISMATCH` tier: `@import` on a shell script is unevaluable, not wrong.
5. **PHANTOM_EDGE keeps its teeth** in the one case that matters — claim is evaluable (both endpoints have graph nodes, graph fresh) and the derived edge is **absent** ⇒ `PHANTOM_EDGE` finding at the STALE_PATH tier, exit 1. Direction is significant here, because an opt-in `@import` claim is explicitly directional.

**Follows without further decision:** a `subgraph` id is not a file path, so it is just another endpoint with no graph node ⇒ `UNKNOWN`, no special rule. A valid `Diagram-Waiver` means no Architecture View, hence no edges, hence the check never runs — no interplay change, and ADR-0009 keeps the waiver out of the gate regardless. The sigil applies in whichever View an author writes it; the Milestone graph is derived and never hand-authored (CONTEXT.md glossary), so it is exempt by definition.

**Downstream constraints this sets:** every diagram committed to date has zero sigils, so the check verifies nothing until authored views adopt them — **Ticket 14** (does `/aa-ma-plan` seed the §13 Component view from the generator?) now also owns whether the generator *emits* `@kind` labels, which is what makes the check non-vacuous. **Ticket 12** (annotation layer) must not invent a second in-diagram annotation syntax; `@kind` edge labels are now taken.


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
- Status: RESOLVED
- Blocked-by: 2, 3
#### Question
`docs/architecture/` file set (one file per View kind? one per package?), front-matter marking them generated, `aa-ma-draw --check` exit semantics, and how `security.yml` gets a graph when `.codemem/index.db` is gitignored (index step in CI vs commit a JSON export vs compare against the committed doc only). `Critical-Path: hook-modification` applies.
#### Answer
**Four fully-generated files in `docs/architecture/`, checked by a dedicated `architecture-drift` CI job.** Grill round 10 with Ste, 2026-09-22.

**The CI half was already answered by existing CI.** `security.yml`'s `codemem-smoke` job **already runs `uv run codemem build`** with `fetch-depth: 0`. Measured on this repo at HEAD: **0.44s** for 175 files / 1517 symbols / 3258 edges (616 resolved cross-file). Indexing in CI therefore costs essentially nothing, and "commit a JSON export" — carrying a generated artifact in git to avoid a sub-second command — has no case left. (That build also refreshed the local index the Notes recorded as stale at `5e2bf54`; `.codemem/` is gitignored, so nothing in the repo changed.) Ticket-text correction: the CLI is **`codemem draw`**, not `aa-ma-draw` (Ticket 2).

**Decisions:**
1. **File set — one file per View kind, plus an index.** `docs/architecture/{README,component,io,plugin-surface}.md`. Names match the CONTEXT.md **View** vocabulary, so each file has an obvious owner. The markdown is the read-without-building artifact (Ticket 11 made the explorer `build/`-only); it does not try to replicate the explorer's levels.
2. **All four are 100% generated, README included.** Because Ticket 12 put captions in a JSON sidecar that the emitter renders *into* the markdown, no hand-written prose needs to live in these files at all. The README is a generated index over the view files with the `@start` caption as its landing text. Nothing in `docs/architecture/` is ever hand-edited.
3. **`codemem draw --check` is regenerate-and-compare**, the same shape as `ruff format --check`: any difference is drift, exit 1, remedy `codemem draw`. **No graph** (missing, `user_version < 3`, per Ticket 2) ⇒ `UNKNOWN` and **exit 0** — CI always builds an index first, and a consumer without one should not be blocked by a check that could not run.
4. **Generated marker carries provenance, and `--check` skips it.** `<!-- generated by codemem draw @ <sha> on <date> -->` as line 1; the comparison excludes that line and compares the rest. **This exception is load-bearing, not incidental**: a byte-comparison check and a volatile provenance stamp are mutually exclusive — without the skip, every commit that did not regenerate would fail `--check` because the file legitimately differs. HTML comment rather than YAML front-matter because `yaml` is not an `aa-ma` dependency (Ticket 12) and no parser is needed; it also matches the repo's existing convention (archived plans open with `<!-- ARCHIVED: … -->`) and is stripped by `html.py` on render.
5. **Its own `architecture-drift` job in `security.yml`**, not a step inside `codemem-smoke`. Repeats checkout / setup-python / uv sync / `codemem build` — roughly 30s of runner time — so that a failure is named for what actually broke. A stale-docs failure surfacing as "codemem smoke test" would misdirect whoever reads the red X.

**Carried into the plan:** this ticket edits `.github/workflows/security.yml`, so its milestone carries **`Critical-Path: hook-modification`** (engineering-standards §1 names CI/hook surface changes) and needs a `CRITICAL_PATH_REVIEW` provenance entry before COMPLETE.


### Ticket 9: `understand-codebase` Deep tier rewire
- Type: grilling
- Mode: HITL
- Status: RESOLVED
- Blocked-by: 2
#### Question
Deep tier (`references/DIMENSIONS.md:52-56`, `DEEPDIVE-TEMPLATES.md:315-317`, `SKILL.md:181-182`) tells agents to "generate Mermaid" or link `/codebase-deep-dive` output — a command the plugin does not ship (gap 6). Replace with the three doors: which door, what the tier does when no codemem index exists (`UNKNOWN`, degrade to prose, or refuse), and whether `/codebase-deep-dive` references are deleted or kept as optional. **Amended 2026-09-22:** also decide whether the generated layered views land in the skill's `ONBOARDING.md` / `.claude/onboarding/02-architecture.md` as well as `docs/architecture/`, and which is the source of truth when both exist.
#### Answer
**Deep tier always runs `codemem draw`; `docs/architecture/` is canonical and the onboarding bundle links it; only the ~4 assertive `/codebase-deep-dive` references are fixed.** Grill round 12 with Ste, 2026-09-22. The first framing was rejected and reformulated — see below.

**Two verifications that reshaped the question:**
- **The MCP door cannot emit mermaid today.** The only renderer in the MCP surface is `_render_layers_onion` (`mcp_tools/__init__.py:991`) and it emits **ASCII**, ≤80 cols / ≤2000 chars. A mermaid-returning MCP tool is new work through any door, so this does not discriminate between options — it only removed a false advantage the first framing had assumed.
- **There is no cold-start problem.** `ensure_built` (`mcp_tools/__init__.py:61`) provisions the index transparently, writer-lock guarded, against a 5s cold-build SLO. The ticket's "`UNKNOWN` / degrade to prose / refuse" trilemma is therefore false: the answer is **build it** (0.44s measured in Ticket 8).

**Gap 6, measured:** 45 `/codebase-deep-dive` command references plus 16 output-dir references across **9 files** (6 in the skill; also `claude-code/skills/system-mapping/SKILL.md`, `agents/codebase-onboarding-health.md`, `agents/codebase-onboarding-synthesizer.md`). But most read *"reuse its `01-architecture-overview.md` if it ran"* — conditional on **output existing**, not on the command being invokable. A consumer without it hits a fall-through to the generate path, not a failure. Gap 6 is a documentation-honesty problem, not a functional break.

**Decisions:**
1. **Write scope — the Deep tier always writes `docs/architecture/` in the target repo**, via `codemem draw` (the CLI door; the Deep tier is a *consumer* of it rather than a third emitter). Every onboarded repo gains the Ticket 8 living doc and can `--check` it in CI. **Accepted cost, stated at decision time:** onboarding a repo you do not own produces four generated files in the first diff, uninvited. The consent-gated alternative — reusing this skill's own AGENTS.md SAFETY PROTOCOL shape (`SKILL.md:183-186`) — was offered and declined in favour of always delivering the living doc.
2. **`docs/architecture/` is canonical; the bundle links it.** `.claude/onboarding/02-architecture.md` carries links, not copies, so drift between the two is impossible by construction. The bundle is no longer self-contained — a reader follows a link to see a diagram. This **retires the `.mmd` files**: the `diagrams/` section of `DEEPDIVE-TEMPLATES.md` and the 14 `.mmd` / `diagrams/` references across 6 files become obsolete, since the bundle now points at generated markdown rather than carrying `.mmd` sidecars that never rendered on GitHub anyway.
3. **Minimal fix for gap 6 — ~4 edits, not 45.** Conditional "reuse if it ran" references stay: they are harmless and preserve a real reuse path for anyone who does have the output. Only the few that **assert the command is available** are fixed (e.g. `REUSE-MAP.md:67`, "invoke `Skill(codebase-deep-dive)` / the `/codebase-deep-dive` command"). A consumer is then never instructed to run something they do not have.

**Follows without further decision:** no-index is not a failure mode — the tier builds the index before drawing (`ensure_built` semantics, 0.44s), so the ticket's UNKNOWN/degrade/refuse options are moot.

**Flagged for the plan, not decided here:** `ensure_built` writes `.codemem/` into the target repo, which appears in that repo's `git status` unless ignored. Whether the tier appends `.codemem/` to the target's `.gitignore` is a write to a fourth user-owned file and needs an explicit call during planning. The skill should also declare its full write footprint up front, now that the footprint reaches outside the bundle.


### Ticket 10: Prior art — code→mermaid tools and their scoping heuristics
- Type: research
- Mode: AFK
- Status: RESOLVED
- Blocked-by: —
#### Question
pydeps, pyan3, code2flow, dependency-cruiser, madge, Structurizr/C4 generators, Sourcetrail, `import-linter` graph output: what each emits, how each tames size (clustering, max-depth, exclude patterns, rank), edge semantics (import vs call), mermaid support. Feed Ticket 3's prototype and Ticket 5's edge-kind decision. Primary sources only.
#### Answer
**Write our own emitter over codemem's index; nothing is reusable zero-dep.** All tools emit DOT first; mermaid is native only in dependency-cruiser (`--output-type mermaid`), tach (`tach show --mermaid`), pyreverse (`-o mmd`). None can be imported by `aa_ma` without a new dependency (pydeps→stdlib_list+dot, tach→networkx+pydot, pyan3/pyreverse GPL, import-linter emits no graph, grimp dev-only). **Recurring scoping heuristics** (feed Ticket 3): (1) collapse to package depth (`--max-module-depth`, `--collapse`, `squash_module`); (2) hop-limited entry-point neighbourhood (`--max-bacon` default 2, `--focus-depth` default 1); (3) include/exclude regex; (4) externals off by default, typed edges; (5) cycle/reverse views. **PageRank top-N has no diagram-tool prior art** — only aider's repo-map budget (already ported into codemem) — so it is Ticket 3's novel arm. **Edge semantics:** import-level is the universal default for architecture views; call-level tools all carry "approximate" disclaimers → import-level for Component view, call-level only inside a scoped entry-point view (input to Ticket 5). **Ceilings:** only hard number is mermaid `maxEdges` default 500 (`maxTextSize` 50000); practical ceiling is tool defaults (1–2 hops, top-level package collapse). See `docs/research/diagram-generation-prior-art.md`.

### Ticket 11: Clickable drill-down — mechanics and where the HTML lives
- Type: grilling
- Mode: HITL
- Status: RESOLVED
- Blocked-by: 2
#### Question
Decided: interaction = clickable mermaid in a self-contained HTML file (Q2, 2026-09-22). Open: mermaid `click` callback vs `click href` (security — `aa_ma/render/html.py` sets a CSP and `securityLevel`; `strict` blocks callbacks); does a node click drill to the next zoom level in-page (all levels inlined, as the prototype does) or open the file on GitHub/in the editor? Does this extend `aa-ma-render` or become a new `aa-ma-draw --html`? Is the interactive build committed or `build/`-only, given the markdown is the GitHub-rendered source of truth? Prototype `demo.html` is the reference shell.
#### Answer
**Delegated DOM listener under an unchanged `securityLevel: 'strict'`; the artifact is the prototype's embedded-graph explorer, built by `aa-ma-render --explorer` into `build/`.** Grill round 7 with Ste, 2026-09-22.

**Two corrections to the ticket's premises:**
- `strict` disables **both** `click call` and `click href`, not just callbacks — mermaid docs via Context7: "The default `strict` level encodes HTML tags and disables click functionality." (`antiscript` — tags except scripts, clicks enabled — was the unmentioned middle option.) So every mermaid-native route required loosening the level.
- "all levels inlined, as the prototype does" is not what the prototype does. `prototype/diagram-generation-3/demo.html` embeds the **whole graph** as JSON in a `<script id="graph">` block and *derives* each level in the browser (`compute()` :125-137, `Scope.mermaid()` :113) — 172 KB for 175 files / 1185 edges. It also keeps `securityLevel: 'strict'` (:164) and uses no mermaid `click` at all.

**Decisions:**
1. **Interaction mechanism — delegated DOM listener, `strict` retained.** The host page attaches one click handler to the rendered SVG and maps the node element back to a path via an emitted lookup table. No `click` lines are emitted into the mermaid fence: that fence is the committed markdown GitHub renders, where mermaid also runs `strict`, so interaction plumbing there would be inert noise in the source of truth. `aa_ma/render/html.py`'s `_CSP` and `securityLevel` are unchanged; the drill script is one more inline `<script>` carrying its own sha256, exactly as `_INIT_SHA` already does. Known coupling: mermaid's SVG node-id scheme.
2. **Artifact shape — embedded graph, levels derived client-side.** Ship what the prototype validated: graph JSON in a script block, `compute()` on click. Free-form drill to any scope and hop depth; size scales with repo (172 KB here). Accepted cost: the HTML is a tool, not a document — its content is not diff-reviewable and has no GitHub-rendered equivalent.
3. **Ownership — `aa-ma-render --explorer` in `aa_ma.render`.** It reads the DB through the Ticket 2 stdlib-`sqlite3` seam (`render/graph.py`), embeds the graph JSON and drill JS, and reuses `html.py`'s existing CSP, SRI hash and `MERMAID_VERSION` constant — pinned **once**, not duplicated into codemem. `codemem draw` (Ticket 2) remains the Python/static path for markdown diagrams.
4. **Two generators are accepted, with a narrow contract test.** Client-side derive means the explorer's mermaid generator is **JavaScript**, while `codemem draw`'s is **Python** — two implementations of the same cut logic by construction. Mitigation is *not* a full golden render: a shared JSON fixture pins only the surfaces that must agree — **node-id derivation** and the **directory-collapse rule** — read by a pytest case and a ~20-line JS test. Cheaper than a byte-identical golden, and it catches the drift that actually misleads a reader. Needs Node in CI, which `security.yml` (shellcheck / bandit / ruff) does not have today.
5. **`build/`-only, never committed.** `build/` is already gitignored (`.gitignore:34`). A 172 KB generated file that rewrites on most commits would churn git and produce unreadable diffs. A newcomer runs one command to get it.

**Glossary collision flagged for the plan-phase update** (charting does not edit CONTEXT.md): the explorer is **not** a *Render* as CONTEXT.md defines it — "a derived, disposable HTML file produced from **a markdown source**" — because it is produced from the graph database. It needs its own term (*Explorer*), added to the candidate list in `## Notes`.

**Downstream constraints this sets:** **Ticket 8**'s living doc must carry the static markdown diagrams as the readable-without-building artifact, since the explorer never lands in git — and Ticket 8 also inherits whether anything HTML is published at all. **Ticket 14** is now unblocked. **Ticket 12**'s annotation layer must render in both the static markdown path and the client-side generator, or state which one it is for.


### Ticket 12: Annotation layer — format and how the lint keeps it in sync
- Type: grilling
- Mode: HITL
- Status: RESOLVED
- Blocked-by: 2
#### Question
Decided: generated graph + authored captions (Q3, 2026-09-22). Open: where the prose lives (sidecar YAML next to the generated md, front-matter in it, or fenced `%%` mermaid comments), what it can say (cluster purpose, "start reading here", why an edge matters, deliberate ordering/colour hints), and the sync rule — a caption naming a node that no longer exists is what kind of finding (`ORPHAN_CAPTION`, STALE_PATH tier)? Does the emitter preserve captions across regeneration, and how does `--check` treat a captions-only diff?
#### Answer
**A flat, path-keyed JSON sidecar — `{"@start": <path>, "<path>": "<prose>"}` — read by both generators.** Grill round 9 with Ste, 2026-09-22.

**Two of the three candidate locations fall to facts, not taste:**
- **`%%` fenced comments are invisible to the reader.** Mermaid strips them at render, and this repo's lint already treats them as non-content (`_DIRECTIVE_RE`, `mermaid_lint.py:57`, applied at `:266`). A caption a newcomer cannot see fails the audience the Destination names.
- **Sidecar YAML is ruled out by the Ticket 2 constraint.** `yaml` is importable in the dev venv (6.0.3, transitive) but is **not** a declared runtime dep of `aa-ma`; importing it would breach L-055 and declaring it would be exactly the new runtime dependency ADR-0010's driver forbids. **JSON costs nothing** — stdlib `json` in Python, native `JSON.parse` in the browser, and the explorer already embeds a JSON payload (`demo.html:120`) captions can ride along in.

Anything stored *inside* the fence also dies on regeneration unless the emitter parses and re-emits it — which means it was structured data all along, stored in the worst place.

**Decisions:**
1. **Captions are structured data feeding both surfaces.** One authored JSON file; the Python emitter renders it into the living doc's markdown, the JS generator (Ticket 11) reads it for the explorer. Prose written loose around a fence would never reach the explorer — the thing with the clickable drill-down — so a living-doc-only annotation layer was rejected.
2. **Keyed by path only, flat.** Zoom levels need no special handling: collapsed levels have directory node ids (`src/aa_ma/render/`) and file levels have file node ids (`src/aa_ma/render/graph.py`), so path keying yields per-level captions for free. One entry serves every view.
3. **Schema is prose plus one reserved `@start` key** naming the repo's entry point. Both generators highlight that node (a `classDef`) and the explorer opens focused on it. The `@` prefix is already reserved by Ticket 5's sigils, so the convention is consistent. Nothing else: no per-view scoping, no colour or ordering hints (the generator owns layout).
4. **`ORPHAN_CAPTION` at the STALE_PATH tier — a finding, exit 1 — and authored prose is never deleted by a tool.** The human rewords or drops it. A caption naming a `(new)` file reads `UNKNOWN` until it lands, mirroring Ticket 5's one policy. Auto-pruning was rejected: a rename in progress would destroy text that was about to be re-pointed.
5. **Captions survive regeneration by construction** — they live outside the generated artifact, so the emitter only ever replaces the fence.

**Follows without further decision:** "why an edge matters" has **no home** under path keying, because edges are not paths. Edge rationale stays in the living doc's surrounding prose, where it makes no claim to being checked — an honest boundary rather than a silent gap. A **captions-only diff is not diagram drift**: `--check` compares generated diagram content, which a caption edit does not change. **Ticket 8** owns where `--check` runs and inherits that rule.

**Downstream:** **Ticket 14**'s seed stays caption-free at paste time — captions are authored afterwards against the node ids the seed produced.


### Ticket 13: Export formats and notation re-evaluation (re-admitted to scope)
- Type: research
- Mode: AFK
- Status: RESOLVED
- Blocked-by: —
#### Question
Ste re-admitted SVG/PNG export and non-mermaid notation on 2026-09-22. (a) Mermaid → SVG/PNG without a new *runtime* dependency: `mmdc` is already optional dev tooling in `mermaid_lint.py` (Node + Chromium) — what does it cost, what are the offline/CI failure modes, and is there a pure-Python or browser-free path? (b) Does D2 or excalidraw produce materially better *onboarding* layout than mermaid for a 13–40 node layered view — side-by-side examples from real published docs, not claims? (c) What would non-mermaid notation cost given ADR-0010 chose mermaid for its zero-toolchain GitHub render (amendment or superseding ADR?). Primary sources only.
#### Answer
**Stay on mermaid; add optional SVG/PNG via the existing `mmdc` seam; D2's case expired.** (a) **No browser-free mermaid renderer exists** — mermaid's own 12.0.0 note says "mermaid requires a browser". `mmdc` (MIT, Node+Chromium, already wired as the `MMDC_BIN` seam in `mermaid_lint.py:303-315`) is the only offline path that respects "no new *runtime* dependency"; hosted mermaid.ink / kroki.io put the repo's architecture in a third-party URL — ruled out in plan text, with the reason stated. (b) **D2's layout advantage expired 2026-09-10**: mermaid 12.0.0 bundles ELK as the *default* — the same engine D2 offers as an option — and D2 renders on neither GitHub, nor VS Code 1.121, nor the Artifact viewer. Its only surviving edge is browser-free PNG. Mermaid's own `architecture-beta` (fcose, overlap bug #6120) and `block` (manual columns) both lose to `flowchart` + `subgraph` at 13–40 nodes. (c) **Admitting D2 as an authoring notation breaks two ADR-0010 drivers and the `/aa-ma-share` premise outright → superseding ADR, not an amendment.** Optional SVG/PNG export is an amendment at most. **v1:** mermaid only, `flowchart`+`subgraph`, every zoom level; self-contained HTML as primary deliverable with the pin held at **11.17.2** (do not bump inside this effort — breaking, re-lays-out every diagram, +~500 kB, and mmdc would disagree); `--svg`/`--png` through `MMDC_BIN` reusing `render_check`'s UNKNOWN-never-PASS discipline; no `--iconPacks` (phones unpkg). **Later:** mermaid 12 + `layout: elk` once mermaid-cli ships a 12 line (cheapest remaining layout win — re-measure a 40-node L1 view); D2 as an *export* target only if a print artefact is ever required; never Excalidraw as a source format (`mermaid-to-excalidraw` converts one-way, cosmetic). See `docs/research/diagram-generation-export-and-notation.md`.

### Ticket 14: Does `/aa-ma-plan` seed the §13 Component view from the generator?
- Type: grilling
- Mode: HITL
- Status: RESOLVED
- Blocked-by: 2, 11
#### Question
Graduated from fog once Ticket 3 showed what generated output looks like (Q10 deferred 2026-09-22). With the L2 cut (`--scope <files-to-modify> --hops 1 --dir both`) a plan's Component view is 5 nodes / 4 edges — small enough to seed. Decide: does Phase 4 call the generator and paste the result for the author to edit, offer it as a suggestion, or leave §13 hand-authored with `PHANTOM_EDGE` (Ticket 5) as the only net? If seeded, how does the author mark deliberate additions (`(new)` files have no edges yet) and does the seed carry captions (Ticket 12)?
#### Answer
**Yes — Phase 4 pastes the L2 cut into §13 with `@kind` sigils, and the author edits on top.** Grill round 8 with Ste, 2026-09-22.

**What the measurement says.** A plan's §13 is about *intended change*; the generator knows only the *present*. Across the two committed Component views, **9/19** (`mattpocock-trio-adoption`) and **6/26** (`plan-architecture-views`) nodes are `(new)` — 47% and 23% — and no generator can draw them. Of the remainder, many are `.yml`, `.sh` or `docs/` files no derived source models (Ticket 4 put `docs/` out of the graph; Ticket 6's v1 languages are Py/TS/JS/Go). So a seed can only ever supply the *current neighbourhood* of the files about to change.

**Why seed anyway.** A derived `@import` edge is trivially true the day it is pasted — and that is not the point. Its value is that it **fails later**, when someone deletes the import and the plan's diagram silently becomes a lie. Seeded edges are the only realistic route to `PHANTOM_EDGE` (Ticket 5) being non-vacuous: no committed diagram carries a sigil today, and hand-authors will not add them unprompted.

**Decisions:**
1. **Phase 4 seeds §13 directly.** It runs the L2 cut (`--scope <files-to-modify> --hops 1 --dir both`, ~5 nodes / 4 edges per Ticket 3) and writes the result into the Component view with `@kind` labels already attached. The author then adds `(new)` nodes and intended edges on top. Every plan therefore ships real, checkable edges from day one.
2. **Anchoring is countered mechanically, not by exhortation.** `Skill(plan-verification)` Angle 6 gains a **coverage rule**: every file path named in a milestone's `#### Contract` block must appear as a node in §13, else a finding. A plan that creates three files and draws none of them is caught. This is **planning-time only** and never reaches the milestone gate — ADR-0009's separation holds.
3. **Intended edges carry sigils too.** `A -->|@import| B["src/new.py (new)"]` reads `UNKNOWN: endpoint planned` while the file does not exist (Ticket 5's one policy), and becomes a real check the moment the file lands and `(new)` is dropped. **The plan's diagram thereby becomes an acceptance criterion for its own implementation**, with no test written.

**Left to Ticket 12:** whether the seed carries captions, and in what format. Nothing here pre-empts that — the seed is caption-free until Ticket 12 decides.

**New question this created — Ticket 15.** "Diagram as acceptance criterion" only bites if something reads it at implementation time, and nothing does today.


### Ticket 15: Does a §13 sigil edge still `UNKNOWN` at milestone COMPLETE reach the gate?
- Type: grilling
- Mode: HITL
- Status: RESOLVED
- Blocked-by: 5, 14
#### Question
Ticket 14 made a `@kind` edge on a `(new)` node a promise that flips from `UNKNOWN` to checked once the file lands — "the diagram as an acceptance criterion". But nothing reads §13 at implementation time. Decide where, if anywhere, that promise is enforced: an eighth `aa-ma-gate` question (`src/aa_ma/gate.py` asks seven today; changing it is a `Critical-Path: hook-modification` change), a §6.7 Execution Checklist item at HARD tier, advisory output only, or an opt-in plan field (`Diagram-Promise:`) so a plan chooses whether its diagram binds. Weigh against ADR-0009, which deliberately keeps `Diagram-Waiver` out of the gate, and against Ticket 2's decision that the lint degrades to `UNKNOWN` rather than failing when the graph is missing — a gate question that can be `UNKNOWN` must fail closed (L-012).
#### Answer
**A HARD §6.7 Execution Checklist item, opt-in and enforced by the command — `aa-ma-gate` is not touched.** Grill round 11 with Ste, 2026-09-22.

**The eighth-gate-question option was structurally more expensive than the ticket implied.** `aa-ma-gate` takes **one positional argument, `tasks_md`** (`gate.py:465`), and all seven questions are answered over `tasks.md` milestone blocks. §13 lives in **`plan.md` only** (CONTEXT.md glossary). An eighth question would need a second input file, a change to the JSON envelope schema (`gate.py:74-78`) and edits to every §6.7/§7.1 fence that shells out to it — all under `Critical-Path: hook-modification`.

**The distinction that resolved it: HARD ≠ `gate.py`.** The §6.7 Execution Checklist already carries HARD items the gate never answers — tests passing, git clean, the `CRITICAL_PATH_REVIEW` provenance entry. Enforcement at HARD tier was available without touching the gate CLI at all, so ADR-0009's and ADR-0010's separation of diagram concerns from the gate binary survives intact.

**Decisions:**
1. **New HARD item in §6.7: "no `PHANTOM_EDGE` finding".** If the plan's §13 carries any sigil edges, `/execute-aa-ma-milestone` runs `aa-ma-lint-views` and refuses COMPLETE on a finding. **Opt-in all the way up** (Ticket 5's philosophy): a plan with no sigils has nothing to check and the item never applies. Enforced by the command; `gate.py`, its envelope and every calling fence are unchanged.
2. **`UNKNOWN` refuses.** A HARD item cannot be satisfied by a check that did not run — L-012 holds. This does **not** contradict Ticket 2, which kept the *lint's exit code* non-blocking (`UNKNOWN` ⇒ exit 0) so CI and consumers are not punished; the §6.7 item is a separate, stricter reader of the same verdict. Unlike CI, a milestone executor is a developer inside the repo, so the refusal names the remedy — `codemem build`, measured at 0.44s in Ticket 8 — making it a ten-second fix rather than a wall.
3. **Evidence is a provenance line: `[ts] DIAGRAM_VERIFIED — <milestone> — edges=<N> phantom=0`**, matching the shape of the existing evidence-bearing HARD items (`CRITICAL_PATH_REVIEW`, `PROTOTYPE`). Keeps the §6.7 table's Verification column uniform and leaves an audit trail.

**Net effect:** Ticket 14's "the diagram is an acceptance criterion" now has teeth, and they bite only on plans that opted in by writing a sigil.


## Not yet specified

- Bump to mermaid 12 + `layout: elk` — deferred out of this effort by Ticket 13; needs its own one-milestone decision once mermaid-cli ships a 12 line.
- Type/schema-flow View (Pydantic/dataclass producers/consumers) — "both, I/O first" (Q6); graduates once codemem tracks class references.
- MCP `diagram` tool budget/truncation behaviour on large consumer repos (codemem `_DEFAULT_BUDGET` pattern).
- Does the forge's own living doc also carry a forge-specific AA-MA-artifact data-flow View (which modules/hooks read/write plan/tasks/reference/context-log/provenance/map), or only the generic I/O view?
- Multi-language consumer repos: one View per language, or merged with language subgraphs?
- What a reviewer (as opposed to a new developer) needs that a newcomer does not — a diff-scoped "what changed in this PR" view?
- Whether the layered views need a per-level narrative page (prose + diagram) rather than a diagram with captions.
- Freshness of `PROJECT_INDEX.json`-based skills (`impact-analysis`, `understand-codebase` REUSE-MAP) once codemem is the graph source — retire or keep both?

## Out of scope

- Languages beyond codemem's 9 — no new parsers in this effort (confirmed 2026-09-22).
- `senior-architect` `architecture_diagram_generator.py` stub — global skill, not forge; note in TODOS (confirmed 2026-09-22).

<!-- Re-admitted 2026-09-22 (Ste, Q4): SVG/PNG export and non-mermaid notation are back in scope as Ticket 13, because the onboarding audience may need formats mermaid cannot serve. ONBOARDING.md integration folded into Ticket 9. -->
