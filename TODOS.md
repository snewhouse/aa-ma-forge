# TODOS

## AA-MA Tooling

### Generate the milestone dependency graph from tasks.md

**What:** `aa-ma-tui --graph` (or an `aa_ma.render` sub-command) emits a mermaid `flowchart` of milestones from their `Dependencies:` fields.

**Why:** The planning standard (element #13, v0.11.0) says the milestone graph is never hand-authored because it is derivable. Today nothing derives it, so no plan has one.

**Context:** Decided during the plan-architecture-views grill (2026-09-11). `src/aa_ma/tui/model.py` already carries `Milestone.dependencies`; `tui/parser.py::discover_tasks` loads every active plan. Start in `src/aa_ma/tui/snapshot.py` next to `render_tree`. Output goes to stdout as a fenced block so it can be pasted or rendered.

**Effort:** S
**Priority:** P3
**Depends on:** milestone-grammar-ssot M5 (reliable `split_milestones`)

### Make aa-ma-tui runnable from any project

**What:** Resolve the aa-ma-forge checkout from the install.sh symlink (`readlink -f ~/.claude/commands/<any>.md` → repo root) and run `uv run --project <root> aa-ma-tui`, via a thin wrapper or documented alias.

**Why:** The TUI only works from inside the aa-ma-forge checkout; every client repo with an active AA-MA plan cannot use it. The same gap was found and fixed for `/aa-ma-share` (plan-eng-review D2, 2026-09-11).

**Context:** The resolution snippet lands in `claude-code/commands/aa-ma-share.md` at plan-architecture-views M3.1; reuse it verbatim. Needs one bats test that the wrapper resolves the root from a symlinked command file.

**Effort:** S
**Priority:** P3
**Depends on:** plan-architecture-views M3 (the snippet)

## mattpocock-trio-adoption follow-ups (eng review 2026-09-20)

### §6.8 M4 deferred INFOs — README skills-table test; `plan_elements=<N>/12` → `/13`

**What:** (a) Extend `tests/commands/test_aa_ma_share_command.py::test_command_count_sites_match_disk` to the README skills table (split on the skills heading, regex `^\| \`([a-z0-9-]+)\``) so the row-set is asserted against `claude-code/skills/*/` like the commands table is. (b) `docs/spec/plan-marker-grammar.md:59` and `claude-code/commands/aa-ma-plan.md:89` still read `plan_elements=<N>/12`; the planning standard has had 13 elements since v0.12.0 (element #13, Architecture View). Update both and any fixture that carries `/12`.

**Why:** Both surfaced by the M4 future-proofing audit (2026-09-21) as out-of-window / Tier-6 retroactive drift; neither is M4 work.

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

**What:** Extend the allowlist in `scripts/aa-ma-share-allow.sh` (`*-plan.md|docs/adr/*.md|docs/spec/*.md`) with `*-map.md`; add a bats case in `tests/commands/aa-ma-share-allow.bats`; update `README.md` (share section) and `claude-code/commands/aa-ma-share.md`.

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

## Completed
