# TODOS

## AA-MA Tooling

### Fail the build on a dangling plugin reference

**What:** Generating `docs/architecture/plugin-surface.md` exits non-zero when a reference from `claude-code/` resolves nowhere — on disk or in the declared-external allowlist.

**Why:** Three instances of one class surfaced during the diagram-generation charting: `/codebase-deep-dive` (Ticket 9), `/index` in `REUSE-MAP.md` (Ticket 19), and the `senior-architect` stub. Each is a shipped skill telling a consumer to run something only the author's machine has. Ticket 8's `codemem draw --check` will **not** catch them: it is a regenerate-and-compare, and a dangling reference does not change the generated output.

**Context:** The detector already exists as a by-product — `docs/research/diagram-generation-plugin-surface-extraction.md` classifies 41 `Skill()` targets into 17 on-disk / 20 declared-external / 4 dangling, plus 7 orphans, in one regex pass. This is wiring, not new analysis. Needs the external allowlist the research already calls for (one of its three). Pairs with the three-valued reference contract now in `CLAUDE.md`. Belongs in the plugin-surface milestone of `/aa-ma-plan --from-map diagram-generation`.

**Effort:** S
**Priority:** P2
**Depends on:** the diagram-generation plan's plugin-surface milestone

### Fix the `edges` composite PK that never de-duplicates

**What:** Replace `edges`' NULL-bearing composite `PRIMARY KEY` with two partial unique indexes, and de-duplicate the existing rows.

**Why:** Measured on the live index 2026-09-22: **6516 rows, 3258 distinct — exactly 2x**. `schema.sql:62-69` declares `PRIMARY KEY(src_symbol_id, kind, dst_symbol_id, dst_unresolved)`, but SQLite treats NULLs as DISTINCT in the implicit unique index and does not enforce NOT NULL on PK columns of a rowid table. `dst_symbol_id` and `dst_unresolved` are mutually exclusive by design, so **every row carries a NULL in the key** and the index never matches — `INSERT OR IGNORE` (`resolver.py:159`, `indexer.py:310`, `journal/wal.py:447`) de-duplicates nothing. Every consumer that counts or weights edges is reading inflated numbers today.

**Context:** Found by the Phase 4.5 adversarial verification of the diagram-generation plan (2026-09-22), which was about to copy the same DDL shape into a new `file_edges` table. That table now ships partial unique indexes instead — verified empirically: 3 identical inserts collapse to 1 row on both the resolved and unresolved paths. The diagram-generation plan deliberately does NOT repair `edges`: M2's `render/graph.py` reads `SELECT DISTINCT`, which makes the `@call` tier correct without a data migration over a rebuildable, gitignored index. Fixing it properly needs a v4 migration plus a one-time de-dupe. Copy the working DDL from that plan's M1.

**Effort:** M
**Priority:** P2
**Depends on:** diagram-generation M1 (establishes the partial-unique-index pattern)

### Make aa-ma-tui runnable from any project

**What:** Resolve the aa-ma-forge checkout from the install.sh symlink (`readlink -f ~/.claude/skills/<any>/SKILL.md` → repo root) and run `uv run --project <root> aa-ma-tui`, via a thin wrapper or documented alias.

**Why:** The TUI only works from inside the aa-ma-forge checkout; every client repo with an active AA-MA plan cannot use it. The same gap was found and fixed for `/aa-ma-share` (plan-eng-review D2, 2026-09-11).

**Context:** The resolution snippet lands in `claude-code/skills/aa-ma-share/SKILL.md` (was `commands/aa-ma-share.md`) at plan-architecture-views M3.1; reuse it verbatim. Needs one bats test that the wrapper resolves the root from a symlinked command file.

**Effort:** S
**Priority:** P3
**Depends on:** plan-architecture-views M3 (the snippet)

## mattpocock-trio-adoption follow-ups (eng review 2026-09-20)

### install.sh: back up every `hooks/lib/` target it replaces; `lib/aa-ma-footer.sh` is never linked

**What:** `scripts/install.sh:149` backs up only `~/.claude/hooks/lib/pre-compact-aa-ma.sh`; the other seven `hooks/lib/` paths it `rm -rf`s (`aa-ma-parse.sh`, `aa-ma-plan-marker.sh`, the six `AA_MA_HOOKS` scripts at :314-323 via `register_hook` :373) get no backup. Loop the same list in the backup collector (:126-155). Separately decide whether `claude-code/hooks/lib/aa-ma-footer.sh` should be installed (it has no `create_symlink` block) or removed.

**Why:** Found by the M4.3 `aa-ma-researcher` live run (`docs/research/mattpocock-trio-adoption-install-backup.md`) and confirmed by hand 2026-09-21. L-016 (b) pattern: `hooks/lib` helpers are per-file, not auto-discovered.

**Effort:** S
**Priority:** P3

### §6.8 M4 deferred INFOs — README skills-table test; `plan_elements=<N>/12` → `/13`

**What:** (a) Extend `tests/commands/test_aa_ma_share_command.py::test_readme_slash_names_are_shipped_skills` (was `test_command_count_sites_match_disk`) to the README skills table (split on the skills heading, regex `^\| \`([a-z0-9-]+)\``) so the row-set is asserted against `claude-code/skills/*/` like the commands table is. (b) `docs/spec/plan-marker-grammar.md:59` and `claude-code/skills/aa-ma-plan/SKILL.md` (was `commands/aa-ma-plan.md:89`) still read `plan_elements=<N>/12`; the planning standard has had 13 elements since v0.12.0 (element #13, Architecture View). Update both and any fixture that carries `/12`.

**Why:** Both surfaced by the M4 future-proofing audit (2026-09-21) as out-of-window / Tier-6 retroactive drift; neither is M4 work.

**Effort:** S
**Priority:** P3

### `/aa-ma-share` refuses `*-map.md` — decide whether charting maps are shareable

**What:** `scripts/aa-ma-share-allow.sh` allowlists `*-plan.md`, `docs/adr/*.md`, `docs/spec/*.md`; a `[task]-map.md` / `.claude/dev/charting/<effort>/<effort>-map.md` is refused. Decide (maps hold decisions, not secrets — closer to a plan than to a context-log) and, if yes, add the glob + a bats case in `tests/commands/aa-ma-share-allow.bats`.

**Why:** M5 risk 3 — recorded as a follow-up rather than silently widening the allowlist during the charting milestone.

**Effort:** S
**Priority:** P3

### Teach fingerprint._phase_1_3 about grilling done in a charting session (`--from-map`)

**What:** Under `/aa-ma-plan --from-map`, Phase 1.3 asks only what the map did not settle — often nothing — so the transcript carries no `grill-with-docs`/`grilling` Skill call and `src/aa_ma/plan_markers/fingerprint.py::_phase_1_3` sees Phase 1.3 as unevidenced. Add a disjunct for the `MAP_IMPORTED` provenance line (or a `--from-map` marker) so grilling evidenced in the map counts; test case in `tests/plan_markers/test_fingerprint.py`; row in `docs/spec/plan-marker-grammar.md`.

**Why:** Same shape as the `_phase_3` entry below; surfaced while wiring `--from-map` (M5.4).

**Effort:** S
**Priority:** P3
**Depends on:** mattpocock-trio-adoption M5

### §6.8 M5 deferred INFOs — install.sh lib loop; mawk-shimmed bats; template-count test

**What:** (a) `scripts/install.sh` now carries three copies of the `if [ -f hooks/lib/X ]; then create_symlink X; fi` block (`aa-ma-parse.sh`, `aa-ma-chart-guard.sh`, plus `aa-ma-plan-marker.sh` from `hooks/`); replace with one `for f in "${REPO_ROOT}"/claude-code/hooks/lib/*.sh` loop so a new helper can never be forgotten (fixes L-005/L-016 at the root; fold into the existing install.sh backup entry above). (b) `tests/hooks/aa-ma-chart-guard.bats` runs under whichever `awk` is on PATH — add one skip-if-absent case that prepends a mawk shim (the `AA_MA_MILESTONE_ERE` comment exists because a mawk-only breakage once went unnoticed). (c) No test asserts the "9 AA-MA file types / 5 standard + 4 optional" sites against `docs/templates/`; extend `tests/commands/test_aa_ma_share_command.py` (pattern: `test_command_count_sites_match_disk`) to count `*-template.*` and check README.md, CLAUDE.md, `docs/templates/README.md`, `claude-code/rules/aa-ma.md`, foundations, quick-ref.

**Why:** Surfaced by the M5 §6.8 audit (code-reviewer, context7-evidence, future-proofing) as out-of-window hardening; none is M5 work.

**Effort:** S
**Priority:** P3

### Teach fingerprint._phase_3 about Skill(aa-ma-research) / aa-ma-researcher

**What:** Add two disjuncts to `src/aa_ma/plan_markers/fingerprint.py::_phase_3` (`Skill` with `skill=^aa-ma-research$`, `Agent` with `subagent_type=^aa-ma-researcher$`), a `_tc(...)` case in `tests/plan_markers/test_fingerprint.py`, and the PHASE_3 row in `docs/spec/plan-marker-grammar.md`.

**Why:** After mattpocock-trio-adoption M4, `/aa-ma-plan` Phase 3 delegates web/Context7 calls to the researcher agent, so the parent transcript has none of the tool calls `_phase_3` looks for. Nothing consumes the correlator yet (`aa-ma-plan-skip-warn.sh` is marker-only, hook :19-21), so this is spec debt, not a live bug.

**Context:** Deferred in eng-review scope decision D1. Start at `fingerprint.py::_phase_3`; mirror the `_phase_1_3` regex style.

**Effort:** S
**Priority:** P3
**Depends on:** mattpocock-trio-adoption M4

### docs/research/README.md with the Valid-Through rule

**What:** A short README in `docs/research/` stating: one file per question, the `Created / Author / Reviewed-Through-Date / Valid-Through / Sources` header, and that a file past its `Valid-Through` is re-verified against primary sources, never trusted.

**Why:** M4 makes `/aa-ma-plan` write a research file per plan; readers need the convention in one place.

**Context:** Deferred in eng-review D1 / TODO-2. Convention already exemplified by `docs/research/skill-ecosystem-audit.md:1-12` and `docs/research/mattpocock-trio-2026-09.md`.

**Effort:** XS
**Priority:** P3
**Depends on:** —

### Let /aa-ma-share publish charting maps

**What:** Extend the allowlist in `scripts/aa-ma-share-allow.sh` (`*-plan.md|docs/adr/*.md|docs/spec/*.md`) with `*-map.md`; add a bats case in `tests/commands/aa-ma-share-allow.bats`; update `README.md` (share section) and `claude-code/skills/aa-ma-share/SKILL.md`.

**Why:** A charting map is the kind of document you would share for a second opinion. Today it is refused.

**Context:** Found by the M5 impact analysis. Decide after the first real map exists — maps carry open questions and fog, so sharing half-formed thinking may not be the right default.

**Effort:** XS
**Priority:** P3
**Depends on:** mattpocock-trio-adoption M5

### Retire the dead global ~/.claude/skills/research

**What:** Remove or rename `~/.claude/skills/research/` (outside this repo). Its body runs `/conduct-research`, which does not exist, and names `perplexity-researcher` agents that are not installed.

**Why:** It advertises "do research" triggers that do nothing; once `aa-ma-research` exists the two names invite confusion.

**Context:** Verified dead 2026-09-20. Check other projects' CLAUDE.md/hooks for references to the name before removing (eng-review OV1).

**Effort:** XS
**Priority:** P3
**Depends on:** —

## diagram-generation follow-ups (carried forward at archive, 2026-09-27)

Each was deferred inside a milestone with Ste's agreement; the source line is in the archived
`diagram-generation-tasks.md` (M<n> carry-forwards).

### Tighten the render/explorer CSP
**What:** `script-src` to the exact mermaid bundle URL (not the whole cdn.jsdelivr.net host); add `base-uri 'none'; form-action 'none'`; regenerate `tests/golden/render_plan_ok.html` (the explorer inherits via `html.csp()`). **Why:** M12 §6.8, deferred by Ste; pre-existing. **Effort:** S · **Priority:** P2

### Record function-local imports in codemem
**What:** persist imports made inside a function (flagged, e.g. `lazy=1`) in `file_edges`, then re-lint every plan's §13. **Why:** today a true `@import` on one reads `PHANTOM_EDGE` and the §6.7 diagram item refuses; ADR-0015 tells authors to label such edges in prose meanwhile. **Effort:** M · **Priority:** P2

### TS/TSX/JS calls inside module-scope arrow functions
**What:** treat `variable_declarator` → `arrow_function | function_expression` as callables so their calls produce edges. **Why:** io.md undercounts JS/TS I/O (disclosed in its prose). Fresh impact analysis needed — they become symbols (component view, dead_code, who_calls change for every TS/JS repo); re-measure the polyglot band after. **Effort:** M · **Priority:** P3

### Plugin sigils checked like `@import`
**What:** if the index gains plugin-surface edges, delete `_PLUGIN_SIGILS` / `_PLUGIN_REASON` in `src/aa_ma/render/mermaid_lint.py` together and evaluate `@skill/@command/@agent/@hook` against the graph. **Why:** they read `UNKNOWN` today. **Effort:** M · **Priority:** P3

### Explorer captions
**What:** JS `_names` / `@start` rule pinned by caption cases in the shared fixture; `&` → `#38;` in both `escape_label` twins if names ever carry entities; escape any `edges.dst_unresolved` callee shown in the explorer (untrusted source text). **Why:** deferred at M12 (Ste). **Effort:** S · **Priority:** P3

### `cut._neighbourhood` early exit
**What:** `if not frontier: break` in the hop loop. **Why:** efficiency only — `diagram()` already bounds `hops` at 10 (M13 §6.8). **Effort:** XS · **Priority:** P3

## codebase-analysis-skills follow-ups (carried forward at M8, 2026-10-01)

Deferred with Ste's agreement. Source lines are in the plan's `context-log.md` (M2/M3/M7
backlogs) and `impl-review.md`.

### Incremental assess re-analysis (v2)
**What:** re-measure and re-judge only what changed since the last Fresh report. Reuse
`changed-since`'s section map idea for assess dimensions; carry unchanged findings forward by ID.
**Why:** a Standard run re-reads the whole repo every time (forge 251 s). **Effort:** L · **Priority:** P2

### `unshare -rn` hardening for `aa-ma-analysis run`
**What:** when `unshare -r -n` works, run approved commands with no network namespace. Fall back
to today's offline env otherwise, and say which in run.log. It also brings loopback down, so
tests binding localhost fail. Make it opt-in.
**Why:** the offline env is best-effort; `make test` can still reach the network
(`docs/research/codebase-analysis-skills-offline-command-run.md` §3). **Effort:** M · **Priority:** P2

### `codemem refresh` is still a placeholder
**What:** `codemem refresh` logs and exits 0 (`packages/codemem-mcp/src/codemem/cli.py`
`_cmd_refresh`). Implement the incremental driver or remove the subcommand. assess runs a full
`build` + `refresh-commits` per run today.
**Why:** a command that succeeds without doing anything misleads callers. **Effort:** M · **Priority:** P3

### Understand density: one `path:line` citation per factual unit
**What:** tighten the onboarding templates so every factual list item, row or sentence carries a
citation `ground` can check.
**Why:** M7 Conditional PASS. The private Python repo trailed on claim density by 0.05–0.08 on
both judges. **Effort:** S · **Priority:** P1

### Collapse measured-secret hits to one finding per file and rule
**What:** emit one `security.secret` finding per (path, rule) with a hit count, not one per hit.
**Why:** 2565 hits on one eval repo; most are fixtures, now MEDIUM. **Effort:** S · **Priority:** P2

### Review other measured-HIGH sources for refuter bypass
**What:** semgrep ERROR, lizard CCN > 25 and fixable vulns are measured HIGH and skip the refuter
(L-034). Each needs a severity that is safe by construction, plus a test pinning it on a shipped
path and a fixture path, before Deep is evaluated.
**Why:** Standard runs produced none in M7, so this is unmeasured. **Effort:** M · **Priority:** P1

### Smaller assess/understand hardening (M2/M3 backlog)
**What:**
- a repo owned by another uid (`safe.directory`) should get a "dubious ownership" message, not "not a git repo"
- ignore planted untracked baseline reports by keeping an index of dirs this tool wrote
- `run` reports a passing command as `timeout` when a detached grandchild holds the pipe
- assign live IDs before refuted twins
- cap `refutation_reason` below `EVIDENCE_MAX` after redaction
- validate `refutation_reason` against `refutation`
- follow git renames instead of reading a rename as fixed + new
**Why:** each fails closed or is a usability gap; none is a leak. **Effort:** M total · **Priority:** P3

## Completed

### Generate the milestone dependency graph from tasks.md

**What:** `aa-ma-tui --graph` (or an `aa_ma.render` sub-command) emits a mermaid `flowchart` of milestones from their `Dependencies:` fields.

**Why:** The planning standard (element #13, v0.11.0) says the milestone graph is never hand-authored because it is derivable. Today nothing derives it, so no plan has one.

**Context:** Decided during the plan-architecture-views grill (2026-09-11). `src/aa_ma/tui/model.py` already carries `Milestone.dependencies`; `tui/parser.py::discover_tasks` loads every active plan. Start in `src/aa_ma/tui/snapshot.py` next to `render_tree`. Output goes to stdout as a fenced block so it can be pasted or rendered.

**Effort:** S
**Priority:** P3
**Depends on:** milestone-grammar-ssot M5 (reliable `split_milestones`)

**Done:** diagram-generation M7 (2026-09-24) — `python -m aa_ma.deps graph <tasks.md>` (launcher `aa_ma_deps`); `/aa-ma-plan` Step 5.5 appends it to §13.

### `codemem draw --write` refuses to overwrite a hand-authored view
**What:** `codemem.draw.views.write_views` refuses a target whose line 1 lacks the generated stamp (`STAMP_RE`). **Why:** only the understand-codebase fence checks today (M13 §6.8 CRITICAL), so a bare `--write` in a consumer repo still overwrites a team's own `docs/architecture/README.md`. **Effort:** S · **Priority:** P2

**Done:** 2026-09-27 — `views.write_views` refuses a stampless target before any write; `--check` names it and says move it aside (`tests/codemem/test_draw_check.py`).

### Repoint the PROJECT_INDEX references outside the M13 rewire at codemem
**What:** `claude-code/skills/aa-ma-plan/SKILL.md` (was `commands/aa-ma-plan.md:181,184,857`), `claude-code/skills/execute-aa-ma-milestone/SKILL.md` (was `commands/…:332`), `claude-code/agents/codebase-onboarding-{runbook,conventions}.md` name codemem as default, PROJECT_INDEX.json as fallback; `aa-ma-plan.md:181` stops suggesting `/index`. **Why:** §6.3's blast-radius advice assumes project-index's upstream `blast_radius`; codemem's is downstream (callers are `who_calls`). The gate file is fence-position-tested — `Critical-Path: hook-modification`. **Effort:** S · **Priority:** P2

**Done:** 2026-09-27 — all four files name codemem as the default index with PROJECT_INDEX.json as fallback; `aa-ma-plan` Step 1.2 no longer suggests `/index`; §6.3's pre-check asks codemem's `who_calls` for callers (`tests/skills/test_understand_codebase_rewire.py`).
