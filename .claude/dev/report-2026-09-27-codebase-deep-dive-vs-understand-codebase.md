# Report — `/codebase-deep-dive` vs `understand-codebase`: relationship, findings, recommendations

- **Date:** 2026-09-27 · **HEAD:** `d250ee3` · **Status:** UNCOMMITTED (saved for a later session, per Ste)
- **Revision:** v2 — every claim re-verified by `/double-check`; changes from v1 listed in §8.
- **Nothing in the repo was changed.** Read-only inspection plus one test run (F12).

---

## 1. Bottom line

- `/codebase-deep-dive` = a **whole-repo assessment** (quality grade, security audit). It lives only on
  Ste's machine; the forge does not ship it.
- `understand-codebase` = a **contributor onboarding** pack. The forge ships it.
- They overlap on the assessment slice (architecture, quality, security, deps, recommendations).
- The link is **one-way and conditional**: `understand-codebase` *reuses* a deep-dive's output if a
  previous run left one. It never *runs* the deep-dive. This is deliberate (Ticket 9) and test-guarded.
- Small leftovers remain (§4). None breaks anything; all are wording or detection gaps.

## 2. Facts (each verified against code at `d250ee3`)

| # | Fact | Evidence |
|---|---|---|
| F1 | `/codebase-deep-dive` is a **local-only** regular file, not shipped. | `~/.claude/commands/codebase-deep-dive.md` is `-rw-------`, not a symlink. `git ls-files \| grep -i codebase-deep-dive` → empty. No `claude-code/commands/codebase-deep-dive.md`. |
| F2 | 6 phases; **only Phases 2–4** run parallel agents (Structural, Flow, Quality & Security). Phases 1, 5, 6 are init, synthesis, handoff. | Headings at `codebase-deep-dive.md:82,157,333,491,736,977`. |
| F3 | Writes 9 reports to `.claude/reports/codebase-deep-dive-*/` — `00-executive-summary` … `08-recommendations` — plus `diagrams/*.mmd`. Assigns an overall **A–F quality/health grade**. | Report names: `grep -oE "0[0-9]-[a-z-]+\.md"`. Diagrams: `:415,463`. Grade: `:516,598-618`. |
| F4 | `understand-codebase` is **shipped** (`~/.claude/skills/understand-codebase` → symlink into this repo); adopted by ADR-0006 (Status: Implemented). Tiers Quick / Standard / Deep. Outputs: `ONBOARDING.md`; Standard/Deep add `.claude/onboarding/00–09` and optional `AGENTS.md`; Deep also writes `docs/architecture/` via `codemem draw`. | `SKILL.md:40-45,70-86,191-230`; `docs/adr/0006-understand-codebase-adoption.md:3`. |
| F5 | **Step 0 (every tier)** absorbs a prior `.claude/reports/codebase-deep-dive-*/`: reuse `01`, `04`, `05`, `06` + diagrams, link from `.claude/onboarding/`. | `SKILL.md:89-104` (row at `:99`). Other conditional refs: `REUSE-MAP.md:30,37,73`; `DIMENSIONS.md:37,53,92,189,211,231,309`; `agents/codebase-onboarding-health.md:25,32`; `agents/codebase-onboarding-synthesizer.md:6`. |
| F6 | **Quick** runs Step 0 but writes only `ONBOARDING.md` — no `.claude/onboarding/`, so F5's "link from `.claude/onboarding/`" has no target in Quick. | `SKILL.md:137-152`. |
| F7 | The **Deep-tier workflow does not invoke** `/codebase-deep-dive`. It spawns `gsd-codebase-mapper`×4, the 3 onboarding workers, the synthesizer, a reviewer, and runs `codemem draw`. | `SKILL.md:191-230`. |
| F8 | Removal of the non-conditional refs happened in **two passes**, each test-first: **(a) M13** `33465fe` (RED `f9be158`) removed the 7 instructions to *run* the deep-dive (`DEEP_DIVE_RUNS`). **(b)** `30b5b4f` (RED `673fdfc`) removed 8 routing / related-tools lines pointing at `/codebase-deep-dive` or `/index` (`ROUTES_TO_UNSHIPPED`), incl. 2 in `system-mapping/SKILL.md`. Conditional "reuse if it ran" refs were **kept on purpose** and a test (`KEPT`) keeps them. | `git log -S` on the phrases; `git show 673fdfc`; `git show 30b5b4f --stat`; `tests/skills/test_understand_codebase_rewire.py`. Decision: `.claude/dev/completed/diagram-generation/diagram-generation-map.md:35,197` (Ticket 9). |
| F9 | The plugin-surface extractor **never classifies** `/codebase-deep-dive`. A `/x` ref is kept only when `claude-code/commands/x.md` exists; otherwise it is **filtered as noise** — not ON_DISK, not DECLARED_EXTERNAL, not DANGLING. | `packages/codemem-mcp/src/codemem/draw/plugin_surface.py:9-13,40,106-108`. |
| F10 | `codebase-deep-dive` is **not** in the declared-external allowlist. ADR-0006 calls it an optional soft dependency in prose only (`:83`). | `packages/codemem-mcp/src/codemem/draw/surface_allowlist.py:14-25`. |
| F11 | The "fail the build on a dangling reference" gate is **not wired yet**: the generated doc lists 2 dangling edges and the build passes. | `TODOS.md:5` (open item under *AA-MA Tooling*); `docs/architecture/plugin-surface.md:286-289`; `tests/golden/plugin-surface.json`. |
| F12 | Guard and extractor tests pass. | `uv run pytest -q tests/skills/test_understand_codebase_rewire.py tests/codemem/test_plugin_surface.py` → **65 passed** (2026-09-27, `d250ee3`). |

## 3. Overlap map

Dimension numbers are from `references/DIMENSIONS.md` (1–19).

| Area | `/codebase-deep-dive` | `understand-codebase` | Note |
|---|---|---|---|
| Architecture & data flow, diagrams | `01`, `03`, `diagrams/*.mmd` | Dim 3 → `02-architecture.md`; Deep: `docs/architecture/` (codemem) | Real overlap. Forge has its own diagram source now. |
| Code quality / tech debt | `04`, A–F grade | Dim 13 (repo health) → `09-repo-health-and-verdict.md` | Overlap; deep-dive is deeper (grades). |
| Security | `05` (audit) | Dim 12 — "describe, don't audit" | Health agent defers to deep-dive explicitly (`codebase-onboarding-health.md:32`). |
| Design patterns | `06` | Part of dim 3 | — |
| Deps / tech stack | `07` | Dim 2 → `01-stack.md` (+ version currency in Deep) | Overlap. |
| Recommendations / verdict | `08` | Dim 14 pros / cons / watch-outs | Overlap. |
| Build/run/debug, tests, CI, env, conventions, versioning & git, rules files, contribute/add-feature playbooks, glossary, AGENTS.md (dims 5–11, 15–17, 19) | — | Yes | `understand-codebase` only. |

In short: deep-dive answers *"is this code good?"* (an assessor). `understand-codebase` answers *"how do I
ship here?"* (a contributor). It takes in deep-dive output when present, and otherwise produces a lighter
version of that slice itself.

## 4. Remaining inconsistencies (none decided or fixed)

| # | Where | Issue | Severity |
|---|---|---|---|
| R1 | `claude-code/skills/understand-codebase/SKILL.md:296` | Error-table row: "`gsd-codebase-mapper` / `/codebase-deep-dive` unavailable → Deep → enhanced-Standard". Deep never invokes the deep-dive (F7), so its absence cannot downgrade Deep. The deep-dive half of the row is stale. No test covers it. | Low — misleading, not breaking |
| R2 | `claude-code/commands/understand-codebase.md:40` | "don't redo `gsd-map-codebase`/`/codebase-deep-dive`/`/index` if fresh outputs exist". **This is conditional reuse, so it is consistent with Ticket 9 and Ticket 19 decision 2** (map `:20` — "fix the instructions that tell someone to *run* something, leave conditional reuse alone"). It does not name codemem as the default (Ticket 19 decision 1). The AC7 codemem test does not scan this file. | Cosmetic |
| R3 | `docs/adr/0006-understand-codebase-adoption.md:29,46,59,67,83` | Still says the Deep tier *composes* `/codebase-deep-dive` and `/index`. No note added after Ticket 9/19. **Precedent for amending exists:** `docs/adr/0003-prototype-adoption.md:139` has `## Amendment 2026-09-21 …`. CLAUDE.md freezes only `docs/plans/` (`CLAUDE.md:115`). | Low |
| R4 | Extractor (F9) + TODOS gate (F11) | Refs to unshipped `/commands` are invisible to the extractor. Once wired, the TODOS.md:5 gate **still would not catch** a future "run `/some-unshipped-command`" line. Today only the phrase-list tests (`DEEP_DIVE_RUNS`, `ROUTES_TO_UNSHIPPED`) catch the known phrasings. | Medium — a detection gap for the whole class |
| R5 | Quick tier (F6) | The absorb-and-link instruction has no link target in Quick. | Trivial |
| R6 | Live behaviour | The reuse path (F5) is specified but has **never been run end-to-end**. | Unknown |
| N1 | `SKILL.md:345` — `Skill(aa-ma-plan)` | Adjacent find, same file. This is a real **DANGLING** ref: `aa-ma-plan` is a *command* (`claude-code/commands/aa-ma-plan.md`); the skill is `aa-ma-plan-workflow`. It is already recorded as dangling (`docs/architecture/plugin-surface.md:289`) and is not fixed. | Low |

## 5. Recommendations (in order; none applied)

1. **R1** — test-first. Remove `/codebase-deep-dive` from the `SKILL.md:296` row (keep
   `gsd-codebase-mapper`), or reword it to "no prior deep-dive output → nothing to absorb; note in
   Provenance". Add the old phrase to a guard list so it can't return.
2. **N1** — change `Skill(aa-ma-plan)` to `/aa-ma-plan` (or `Skill(aa-ma-plan-workflow)`) at
   `SKILL.md:345`. Regenerate `docs/architecture/plugin-surface.md` and the golden in the same commit.
3. **R3** — add `## Amendment 2026-09-27` to ADR-0006, following the ADR-0003 format, pointing at Ticket
   9/19, `33465fe` and `30b5b4f`. Ste confirms (Q2).
4. **R2** — optional: name codemem as the default in `commands/understand-codebase.md:40`. Cosmetic only.
5. **R4** — decide this when wiring the TODOS.md:5 gate. The current filter exists to drop noise such as
   `/tmp` and `/goal` (`plugin_surface.py:13`). A narrower classification rule would need designing and
   measuring against the golden. That rule is **not yet designed** — do not assume one.
6. **R6** — optional live check: run `/understand-codebase --standard` on a scratch repo that already
   has a `.claude/reports/codebase-deep-dive-*/`, and confirm Provenance records it as absorbed.

## 6. Open questions for Ste (not assumed)

- **Q1 — what happens to `/codebase-deep-dive` long term:**
  (a) leave it local-only with conditional reuse, as now (Ticket 9);
  (b) ship it in the forge as the whole-repo audit — it becomes ON_DISK, and the "pure audit → …" pointer
  that `30b5b4f` replaced with "no whole-repo audit ships here" can come back;
  (c) add it to `surface_allowlist.EXTERNAL` — **this has no effect today**, because of F9;
  (d) retire it, and let `understand-codebase` own the assessment slice.
- **Q2 — ADR-0006:** add a dated amendment (precedent: ADR-0003), or leave it as a historical record?
- **Q3 — scheduling:** fold R1/N1 into the pending "fix the 6 items" task
  (`.claude/dev/handoff-2026-09-27.md` §3, `TODOS.md:137`), or do them as a separate `[ad-hoc]` fix?
- **Q4 — R4:** change the extractor's `/x` rule, or rely on the phrase-list guard tests?

## 7. Reproduce the evidence

```bash
cd ~/projects/github_private/aa-ma-forge
ls -la ~/.claude/commands/codebase-deep-dive.md; git ls-files | grep -i codebase-deep-dive
grep -n "^### Phase" ~/.claude/commands/codebase-deep-dive.md
grep -n -i "grade\|diagrams/" ~/.claude/commands/codebase-deep-dive.md | head
grep -rn "codebase-deep-dive" claude-code/ | cut -c1-160
git log --oneline -S'Also run `/codebase-deep-dive`' -- claude-code/
git show 673fdfc; git show 30b5b4f --stat
sed -n 1,20p packages/codemem-mcp/src/codemem/draw/plugin_surface.py
sed -n 14,25p packages/codemem-mcp/src/codemem/draw/surface_allowlist.py
sed -n 290,300p claude-code/skills/understand-codebase/SKILL.md; sed -n 343,346p claude-code/skills/understand-codebase/SKILL.md
sed -n 284,290p docs/architecture/plugin-surface.md
uv run pytest -q tests/skills/test_understand_codebase_rewire.py tests/codemem/test_plugin_surface.py
```

## 8. Double-check log — v1 → v2

| v1 claim | v2 verdict | Correction |
|---|---|---|
| F7: `30b5b4f` removed the "assertive" run instructions | **Contradicted** | The 7 run instructions went in M13 `33465fe`. `30b5b4f` removed 8 routing / related-tools lines (F8). |
| Overlap: "dim 9 verdict" for quality | **Contradicted** | Dim 9 is Conventions. Quality is dim 13; the verdict is dim 14 (§3). |
| R2 treated as an inconsistency | **Weakened** | Consistent with Ticket 19 decision 2. Only cosmetic (§4). |
| Q2 "ADR policy not stated" | **Partially answered** | An amendment precedent exists (ADR-0003:139). Still Ste's call. |
| F3 "+ Mermaid" | **Sharpened** | `diagrams/*.mmd`; A–F grade added. |
| "TODOS.md:9" | **Sharpened** | The item heading is at `TODOS.md:5`; the gate is not wired (F11). |
| — | **New** | N1: `Skill(aa-ma-plan)` dangling at `SKILL.md:345`. |
| Earlier session claims ("declared-external", then "dangling"; "parallel agents in each phase") | **Contradicted** (unchanged from v1) | See F2, F9, F10. |
