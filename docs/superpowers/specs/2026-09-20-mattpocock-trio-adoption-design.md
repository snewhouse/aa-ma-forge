# mattpocock-trio-adoption — design

**Date:** 2026-09-20 · **Status:** approved in brainstorming (Phase 2 of `/aa-ma-plan`) · **Release:** v0.13.0 after M5
**Inputs:** [research note](../../research/mattpocock-trio-2026-09.md) · ADR-0011 / ADR-0012 / ADR-0013 (Proposed) · `drift-scope` grounding (grill Phase 1.3) · `CONTEXT.md` fork-lifecycle terms (Re-fork, Drift, Orphan, Adaptation)

## Goal

Bring every mattpocock fork to a known, detectable lifecycle state; re-fork what drifted; adopt `research`; adapt `wayfinder` as a pre-plan **charting** step; make the prototype decision explicit in planning. One memory system, one directory tree, ≤5 agents at a time.

## Decisions (all HITL, 2026-09-20)

| # | Decision | Alternatives rejected |
|---|---|---|
| D1 | Glossary gains **Re-fork / Drift / Orphan / Adaptation**; "sync" and "vendor" banned | — |
| D2 | `grill-with-docs` keeps its **name** (Phase 1.3 dispatch + fingerprint contract); fork upstream `grilling` only; `grill-with-docs` becomes **Derived** with its interview block replaced by a call to `grilling` | faithful two-dir re-fork (+2 dirs, file moves); verbatim stub (breaks dispatch) |
| D3 | Our `CONTEXT-FORMAT.md` stays **Derived** (retains Relationships / Example dialogue / Flagged ambiguities); `ADR-FORMAT.md` byte-identical upstream | migrate CONTEXT.md to upstream's stricter format |
| D4 | `write-a-skill` → **Derived** (`DERIVED-FROM-UPSTREAM`); recipe retained; `writing-for-agents` re-evaluated as a Candidate in the audit refresh | retire; re-fork successor; adopt both |
| D5 | **Fork manifest** `claude-code/skills/FORKS.json` + detector test; Drift/Orphan reported as warnings; `tests/skills` added to CI | detector parsing ADR prose; manual checks |
| D6 | `prototype`: Re-fork at 1.2.3; Step 2.5 "Prototype decision" in `/aa-ma-plan`; gate rolls up sub-step `Prototype-Required` | re-fork only; drop sub-step slot |
| D7 | `research`: fork + two hardening lines; new **`aa-ma-researcher` agent** (no Agent tool) writes `docs/research/<plan-slug>-<topic>.md` | Explore returns text, main writes |
| D8 | `wayfinder` → **charting** Adaptation: `/aa-ma-chart` + single-file map under `.claude/dev/charting/<effort>/`; exits via `/aa-ma-plan --from-map`; optional 9th AA-MA file type | verbatim on GitHub Issues; document only |
| D9 | Order M1 manifest → M2 grill → M3 prototype → M4 research → M5 charting; one release | charting first |

## Milestones

### M1 — Fork manifest, detector, Derived reclassifications (`Audit-Profile: code-only`)
- `claude-code/skills/FORKS.json` — SSoT: `{ "<skill>": { "upstream": "<repo path>", "forked_at", "adr", "state": "current|derived", "files": { "<file>": "<md5 of tail -n +2>" } } }`.
- `tests/skills/test_fork_manifest.py` — (a) every skill dir whose `SKILL.md` line 1 starts `<!-- Forked from` or `<!-- Derived from` is in the manifest and vice-versa; (b) provenance URL ⊇ manifest `upstream`; (c) local MD5s match (hard fail); (d) if `~/.claude/plugins/cache/claude-plugins-official/mattpocock-skills/*/skills/` exists → compare, `warnings.warn("DRIFT: …")` / `("ORPHAN: …")`, never fail. `_helpers.assert_skill_frontmatter` reads `upstream` from the manifest.
- `.github/workflows/security.yml` — add `tests/skills` to the pytest job.
- `write-a-skill/SKILL.md` line 1 → `<!-- Derived from (deleted) https://github.com/mattpocock/skills/skills/productivity/write-a-skill, forked 2026-05-10, upstream removed 1.0.0 (2026-06-17) — aa-ma-forge v0.13.0 -->`; `test_write_a_skill_frontmatter.py` docstring; `README.md:250` prose; ADR-0004 amended (Status: Implemented — Derived); ADR-0002:128-129 stale rows corrected.
- Tests first: manifest test written red against an empty manifest.

### M2 — `grilling` fork; `grill-with-docs` Derived (`Audit-Profile: code-only`)
- Fork `productivity/grilling/SKILL.md` (1.2.3 md5 `9f7179e83f79d9a62d6ee9c250e46592`) → `claude-code/skills/grilling/`; `tests/skills/test_grilling_frontmatter.py`.
- `grill-with-docs/SKILL.md`: line 1 → Derived provenance; `<what-to-do>` block → "Call the Skill tool with `grilling`; during the session apply the domain awareness below" (keeps `CONTEXT-FORMAT.md` / `ADR-FORMAT.md` in place; test unchanged); adopt upstream's stricter glossary sentence ("devoid of implementation details… a glossary and nothing else") since our Derived FORMAT already honours it at term level.
- `CONTEXT-FORMAT.md` line 2: `<!-- Derived: retains Relationships / Example dialogue / Flagged ambiguities (upstream removed 2026-07); still glossary-level, never implementation. -->`
- `aa-ma-plan.md:196-200` prose: note the delegation; `fingerprint.py` untouched (outer call still `grill-with-docs`).
- ADR-0002 amended; `FORKS.json` rows for `grilling` (current) and `grill-with-docs` (derived).

### M3 — `prototype` Re-fork + planning gate (`Audit-Profile: full`, `Critical-Path: hook-modification`)
- Re-fork `SKILL.md`, `LOGIC.md`, `UI.md` (1.2.3 md5s `f59e7362…`, `5a29fb2c…`, `0531f4c5…`; re-verify against HEAD at fork time); `FORKS.json` updated; `test_prototype_frontmatter.py` green.
- `engineering-standards.md` Theme 1 wording (HTML logic demo; `prototype/<name>` branch capture).
- `aa-ma-plan.md` **Step 2.5 Prototype decision** after 2.4: per uncertain milestone, AskUserQuestion `Prototype-Required: YES|NO`; written into tasks.md; `ENG_STANDARDS_DECLARED` line gains `prototype=<milestones>`.
- `src/aa_ma/gate.py::_read_milestone`: `prototype_required = own YES or any(sub-step YES)`; `tests/test_gate.py` + `tests/hooks/fixtures/gate-scans/styles-tasks.md` case "milestone absent / sub-step YES → YES" written **first**. Schema unchanged.
- `execute-aa-ma-milestone.md:594-620` note (roll-up); `execute-aa-ma-step.md:242-246` advisory; `docs/templates/tasks-template.md:111-113` comment; spec `:302-326` provenance grammar gains `PROTOTYPE — <milestone heading> — <verdict>[; branch=prototype/<name>]` and `CRITICAL_PATH_REVIEW — <evidence>`.
- ADR-0011 → Implemented.

### M4 — `research` adoption + `aa-ma-researcher` agent (`Audit-Profile: code-only`, `Prototype-Required: YES`)
- Fork `engineering/research/SKILL.md` (md5 `506b3477…`) → `claude-code/skills/research/`; append: "Dispatch as the `aa-ma-researcher` agent (no Agent tool — it cannot re-delegate)"; "Answer the stated question only; list open threads under `## Not pursued`"; "Here that place is `docs/research/<plan-slug>-<topic>.md` with the `skill-ecosystem-audit.md` header".
- `claude-code/agents/aa-ma-researcher.md` — `tools: Read, Glob, Grep, Bash, WebSearch, WebFetch, Write`; prompt contract: primary sources, cite every claim, write exactly one file, return a ≤10-line summary + path.
- `aa-ma-plan.md` Phase 3.3 → dispatch `Skill(research)` per domain (≤5 concurrent); 3.4 writes files; marker row :88 + `docs/spec/plan-marker-grammar.md` gain `research_files=<N>`; Step 5.3/5.4 link the files. `PHASE_3_RESEARCH.md` tool hierarchy row; `research-consolidation` references marked optional-external.
- Install: `~/.claude/skills/research` (real dir) is backed up by `install.sh:116-180` then replaced — record backup path in provenance. **Prototype:** one live run of the forked skill against a real question; verdict in provenance.
- ADR-0012 → Implemented. Counts: skills 19→21 (grilling, research), agents 11→12.

### M5 — Charting (Adaptation) (`Audit-Profile: code-only`, `Prototype-Required: YES`)
- `claude-code/commands/aa-ma-chart.md` — `chart <effort> "<idea>"` / `work <effort> [ticket]`; resolvers: research → `Skill(research)` (AFK, parallel ≤5); prototype → `Skill(prototype)` on `prototype/<effort>-<ticket>` (HITL); grilling → `Skill(grill-with-docs)` + AskUserQuestion, never self-answer (HITL); task → human checklist. Invariants: no-fog early exit; claim before work; one non-research ticket per session; charting never writes outside `.claude/dev/charting/`, `docs/research/`, `prototype/*`.
- `docs/templates/map-template.md`; ticket grammar `### Ticket N: Title` + `Type/Mode/Status/Blocked-by` + `#### Question` / `#### Answer` (headings distinct from `MILESTONE_RE`/`STEP_RE`; TUI ignores by design — parser reads only `-tasks.md`).
- `aa-ma-plan.md --from-map <effort>`: Phase 1 pre-answered from *Decisions so far*; Phase 5 moves map to `.claude/dev/active/<task>/<task>-map.md`; Step 5.3 extracts Answers with `[valid: date]`; provenance `MAP_IMPORTED effort=<effort> tickets=<N>`.
- Spec file taxonomy (8→9 optional), `CLAUDE.md` table, quick-reference, foundations (commands 12→13), README, SECURITY, CHANGELOG, ATTRIBUTION ("concept adapted from wayfinder; no files forked"); `tests/commands/` bats: no-fog exit, second-ticket refusal.
- **Prototype:** chart one real effort first (candidate: evaluate `writing-for-agents` as a Candidate) before freezing the template. ADR-0013 → Implemented.
- Then: `scripts/release.sh minor --headline "…"` → v0.13.0.

## Edge cases surfaced

1. Plugin cache absent (other machine / CI) → detector skips comparison with a `SKIP: cache not found` warning; hard checks still run.
2. Sub-step `Prototype-Required` with an invalid token → gate exit 2 (same as milestone-level); documented.
3. `research` skill name also exists as `mattpocock-skills:research` (plugin) — namespaced, no collision; `~/.claude/skills/research` real dir → install.sh backup.
4. Map with zero fog at chart time → command stops: "no map needed — run /aa-ma-plan".
5. `--from-map` on a map with open tickets → refuse with the frontier list (map must be clear).
6. Doc-count-drift fires per milestone (L-002): each milestone updates its own counts, not "at the end".
7. `tests/skills` joining CI may expose today's latent failures — run locally in M1 before flipping the workflow.

## Engineering Standards Declaration (element #12)

All six themes: [1] V&T — M3 hook-modification, M4/M5 Prototype-Required, upstream verified by `gh api`; [2] TDD for gate roll-up + manifest, KISS ×2; [3] Socratic grill → 4 terms + 2 refinements; [4] name-contract non-breaking, gate semantics widen only, lessons L-001/002/005/011/013; [5] five gated milestones; [6] per-sub-step Result Logs.
