# Skill Ecosystem Audit — aa-ma-forge

**Created:** 2026-05-10
**Author:** Stephen Newhouse, Claude (skill-ecosystem-integration v1.2 plan)
**Reviewed-Through-Date:** 2026-05-10 (canonical inventories fetched same day)
**Valid-Through:** 2026-Q3 (re-fetch inventories if reviewing after this date)
**Plan-Version:** skill-ecosystem-integration v1.2
**Inventory-Files:**
- [`docs/research/_inventories/mattpocock-inventory.json`](_inventories/mattpocock-inventory.json) — 27 skills (17 production + 4 deprecated + 4 in-progress + 2 personal)
- [`docs/research/_inventories/gstack-inventory.json`](_inventories/gstack-inventory.json) — 34 canonical README commands + 12 additional skills with SKILL.md only
- [`docs/research/_inventories/gsd-inventory.json`](_inventories/gsd-inventory.json) — 90 workflows + 36 templates (inspiration only — ship nothing direct)

---

## Top summary — ranked M3+ candidates

| Ecosystem | Candidate | Status | Effort | Priority | Rationale |
|-----------|-----------|--------|--------|----------|-----------|
| mattpocock | `grill-with-docs` | **ADOPTED-M1** | done (1 day) | — | Forked v0.6.0-M1; ADR-0002. Phase 1.3 dispatcher with --grill-mode flag. |
| mattpocock | `prototype` | **ADOPTED-M2** | done (1 day) | — | Forked v0.6.0-M2; ADR-0003. Operationalises engineering-standards Theme 1 `Prototype-Required: YES`. |
| mattpocock | `write-a-skill` | **ADOPTED-M2** | done (1 day) | — | Forked v0.6.0-M2; ADR-0004. Canonical authoring procedure. |
| mattpocock | `tdd` | PROPOSED-M3+ | S | HIGH | Operationalises engineering-standards Theme 2 (TDD mandate). 1-file fork. ADR optional. |
| mattpocock | `to-prd` | PROPOSED-M3+ | M | MEDIUM | Candidate Phase 2.5 of /aa-ma-plan (output PRD before 12-element plan). Requires command wiring + ADR. |
| mattpocock | `diagnose` | PROPOSED-M3+ | S (diff first) | MEDIUM | Diff against existing `debugging-strategies` skill; either adopt+supersede or document overlap rationale. |
| mattpocock | `to-issues` | PROPOSED-M3+ | M | LOW-MEDIUM | Candidate post-Phase-4 export of plan tasks to GitHub/GitLab issues. Requires `glab`/`gh` integration. |
| mattpocock | `triage` | PROPOSED-M3+ | M | LOW-MEDIUM | Conceptual fit with HITL/AFK/SOFT/HARD gating; needs design discussion before adoption. |
| mattpocock | `improve-codebase-architecture` | PROPOSED-M3+ | S | LOW | Architecture refactoring loop; orthogonal to AA-MA but useful adjacent skill. |
| mattpocock | `zoom-out` | PROPOSED-M3+ | S | LOW | Contextual code explanation; orthogonal but lightweight. |
| mattpocock | `git-guardrails-claude-code` | DEFERRED | S (diff first) | MEDIUM | Diff against aa-ma-forge `commit-signature` + `commit-drift` hooks before deciding overlap. |
| mattpocock | `setup-pre-commit` | DEFERRED | S (diff first) | LOW | Diff against existing pre-commit/release hooks. |
| mattpocock | `caveman` | **SUPERSEDED** | n/a | n/a | Already superseded by aa-ma-forge `token-compression` skill (which is conceptually inspired by JuliusBrussee/caveman, not mattpocock/caveman). Do not adopt. |
| mattpocock | `grill-me` | **DERIVED-FROM** | n/a | n/a | aa-ma-forge `/grill-me` command (42 lines) is already a derivative extension of mattpocock's 4-line skill. Do not re-fork. |
| gstack | `/context-save` + `/context-restore` | PROPOSED-M3+ | M | **HIGH** | Direct overlap with AA-MA context-log/CHECKPOINT pattern; diff against current provenance.log CHECKPOINT entries before adopting. |
| gstack | `/freeze` + `/unfreeze` | PROPOSED-M3+ | S | MEDIUM | Lock-down pattern; complements milestone HARD gate. |
| gstack | `/careful` | PROPOSED-M3+ | S | MEDIUM | Defensive-mode toggler; relevant to milestone HARD gates. |
| gstack | `/guard` | PROPOSED-M3+ | S | MEDIUM | Guard rails; complements engineering-standards rules. |
| gstack | `/skillify` | PROPOSED-M3+ | S | LOW | Skill creation; complements adopted `write-a-skill`. Diff first. |
| gstack | `/investigate` | PROPOSED-M3+ | S (diff first) | LOW-MEDIUM | Diff against `debugging-strategies`. |
| gstack | `/autoplan` | DEFERRED-CONFLICT | M | n/a | Likely terminology collision with `/aa-ma-plan`; verify-plan or skip. |
| gstack | `/ship` | **EXCLUDED** | n/a | n/a | DO NOT USE — confirmed conflict with Commitizen + python-semantic-release pipeline. |
| gsd | (any direct adoption) | **EXCLUDED** | n/a | n/a | INSPIRATION ONLY per user decision at planning. Patterns extracted (see Section C). |

---

## A. mattpocock/skills — 17 production skills

**Source:** [`mattpocock-inventory.json`](_inventories/mattpocock-inventory.json) (68425 stars at fetch time; default branch `main`; description "Skills for Real Engineers. Straight from my .claude directory.")

### Engineering category (10 production)

| Skill | aa-ma-forge status | Disposition |
|-------|--------------------|-------------|
| `diagnose` | PROPOSED-M3+ | Disciplined diagnosis loop. Diff against `debugging-strategies` before adoption. |
| `grill-with-docs` | **ADOPTED-M1** | Forked v0.6.0-M1. ADR-0002. |
| `improve-codebase-architecture` | PROPOSED-M3+ | Architecture refactoring loop. Orthogonal but useful. |
| `prototype` | **ADOPTED-M2** | Forked v0.6.0-M2. ADR-0003. Operationalises Theme 1 `Prototype-Required:`. |
| `setup-matt-pocock-skills` | EXCLUDED | mattpocock-specific install/config flow. Not portable. |
| `tdd` | PROPOSED-M3+ HIGH | Operationalises Theme 2 (TDD mandate). Single-file fork; ADR optional. |
| `to-issues` | PROPOSED-M3+ | Breaking specs into tasks. Requires `gh` / `glab` CLI integration. |
| `to-prd` | PROPOSED-M3+ MEDIUM | Candidate Phase 2.5 of /aa-ma-plan (PRD before plan). Requires command wiring. |
| `triage` | PROPOSED-M3+ | Issue state machine. Conceptual fit with HITL/AFK/SOFT/HARD; design first. |
| `zoom-out` | PROPOSED-M3+ LOW | Contextual code explanation. Lightweight orthogonal. |

### Productivity category (3 production)

| Skill | aa-ma-forge status | Disposition |
|-------|--------------------|-------------|
| `caveman` | SUPERSEDED | aa-ma-forge `token-compression` (inspired by JuliusBrussee/caveman) is strictly more capable — 3 intensity levels mapped to HITL/AFK execution modes. Do not adopt mattpocock's caveman. |
| `grill-me` | DERIVED-FROM | aa-ma-forge `/grill-me` command (42 lines) extends mattpocock's 4-line canonical skill with explicit protocol numbering, constraint list, "Resolve don't just surface" rule, "Know when to stop" rule. Lineage recorded in CONTEXT-MAP. |
| `write-a-skill` | **ADOPTED-M2** | Forked v0.6.0-M2. ADR-0004. |

### Misc category (4 production)

| Skill | aa-ma-forge status | Disposition |
|-------|--------------------|-------------|
| `git-guardrails-claude-code` | DEFERRED-DIFF | Diff against `commit-signature.sh` + `commit-drift.sh` hooks before deciding. May overlap. |
| `migrate-to-shoehorn` | EXCLUDED | mattpocock-specific test migration tool. Not portable. |
| `scaffold-exercises` | EXCLUDED-LOW-FIT | Exercise structure generation; orthogonal to AA-MA mission. |
| `setup-pre-commit` | DEFERRED-DIFF | Diff against existing aa-ma-forge pre-commit configuration before deciding. |

### Excluded (10 total: 4 deprecated + 4 in-progress + 2 personal)

- **Deprecated:** `design-an-interface`, `qa`, `request-refactor-plan`, `ubiquitous-language` (the latter is the conceptual ancestor of `grill-with-docs`).
- **In-progress (not stable):** `handoff`, `writing-beats`, `writing-fragments`, `writing-shape`.
- **Personal (mattpocock-specific):** `edit-article`, `obsidian-vault`.

---

## B. gstack — 34 commands + 12 additional skills

**Source:** [`gstack-inventory.json`](_inventories/gstack-inventory.json) (92598 stars at fetch time; default branch `main`; description: Garry Tan's Claude Code setup, 23 specialists + 8 power tools per README; structure: each skill is a top-level repo directory, NOT nested under `skills/`.)

### Verified disposition (extends `~/.claude/CLAUDE.md` gstack disposition guide)

The existing `CLAUDE.md` global guide covers 12 entries. The full inventory is 34 README-canonical commands + 12 additional skills with SKILL.md only = 46 total. This audit assigns dispositions for the 21 not yet covered by the existing guide.

**HIGH RELEVANCE for aa-ma-forge M3+:**
- `/context-save`, `/context-restore` — Direct overlap with AA-MA context-log/CHECKPOINT pattern. Adoption candidate; diff against provenance.log CHECKPOINT format before forking.
- `/freeze`, `/unfreeze`, `/guard`, `/careful` — Lock-down + defensive-mode patterns; complement milestone HARD gate. Single-file skills.
- `/skillify` — Skill creation flow; complements adopted `write-a-skill`. Diff first.

**AA-MA SAFE (already covered or ready to use as-is):**
- Per existing CLAUDE.md guide: `/browse`, `/plan-{ceo,eng,design}-review`, `/review`, `/qa-only`, `/retro`, `/document-release`.
- New: `/office-hours`, `/design-html`, `/land-and-deploy`, `/canary`, `/benchmark`, `/setup-deploy`, `/setup-gbrain`, `/investigate`, `/codex`, `/cso`, `/plan-devex-review`, `/devex-review`, `/gstack-upgrade`, `/learn`, `/health`, `/sync-gbrain`.

**AA-MA CAUTION (verify mode interactions):**
- Per existing guide: `/design-consultation`, `/qa`, `/qa-design-review`.
- New: `/design-shotgun` (rapid ideation needs scope discipline), `/pair-agent` (verify mode interactions), `/scrape` (review compliance with Galactic API rules).

**SKIP:**
- Per existing guide: `/setup-browser-cookies` (macOS-specific; not relevant on WSL/Linux).
- New: `/connect-chrome` (browser plumbing — not core to AA-MA on WSL).

**DO NOT USE — explicit conflict:**
- `/ship` — Confirmed conflict with `release-prep` + Commitizen + python-semantic-release pipeline.
- `/autoplan` — DEFERRED-CONFLICT: likely terminology collision with `/aa-ma-plan` (which was renamed from `/ultraplan` in 2026-04 already). Verify or skip.

---

## C. get-shit-done — 6 patterns + DO-NOT-BORROW subsection

**Source:** [`gsd-inventory.json`](_inventories/gsd-inventory.json) (61215 stars at fetch time; description: "A light-weight and powerful meta-prompting, context engineering and spec-driven development system for Claude Code".)

**User decision (recorded at planning time):** **INSPIRATION ONLY** — extract patterns, ship nothing direct from gsd.

### Patterns worth borrowing (inspiration, not direct adoption)

1. **Optional spec template library** (source: `templates/AI-SPEC, UI-SPEC, SECURITY, UAT, VALIDATION`)
   - Pattern: a library of optional MADR-style specs that plans can opt into based on task type.
   - aa-ma fit: add `docs/templates/optional-specs/` with named optional templates (AI-SPEC.md, UI-SPEC.md, SECURITY-SPEC.md, UAT.md, VALIDATION.md).
   - Effort: M. Priority: MEDIUM. valid through 2026-Q3.

2. **Living `state.md` digest (forward-looking, ~100 lines)** (source: `templates/state.md`)
   - Pattern: complement the backward-looking `provenance.log` audit with a forward-looking digest of next-actions, open issues, and rolling state.
   - aa-ma fit: optional 8th AA-MA file, separate from existing 5 + 2 optional. Diff against the recurring "load PROVENANCE for telemetry" pattern.
   - Effort: M. Priority: LOW-MEDIUM. valid through 2026-Q3.

3. **Subagent triad (researcher → creator → checker)** (source: `plan-phase, ai-integration-phase, ui-phase`)
   - Pattern: high-complexity milestones use 3 distinct subagent roles instead of 2.
   - aa-ma fit: strengthen the `aa-ma-scribe` + `aa-ma-validator` pair into a triad for high-complexity (≥80%) milestones.
   - Effort: M. Priority: MEDIUM. valid through 2026-Q3.

4. **Revision-loop with max-iteration escalation** (source: `references/revision-loop.md`)
   - Pattern: optional revision mode in execute-step when verification fails N times — escalate to user after N attempts.
   - aa-ma fit: optional revision loop in `/execute-aa-ma-step` when acceptance criteria fail repeatedly.
   - Effort: S. Priority: LOW. valid through 2026-Q3.

5. **Auto/headless execution flag (`--auto`)** (source: `workflows/autonomous.md, fast.md, quick.md`)
   - Pattern: explicit no-pause autonomous flag that overrides per-task HITL.
   - aa-ma fit: already partial via `Mode: AFK` field; could expand to `/execute-aa-ma-full --mode auto` for full-plan autonomy with HARD gates as the only pause points.
   - Effort: S. Priority: LOW. valid through 2026-Q3.

6. **Context-window-aware prompt sizing** (source: `execute-phase.md`)
   - Pattern: detect available context window; adapt subagent prompt richness accordingly.
   - aa-ma fit: relevant to `aa-ma-execution` skill's context injection rules (priority order).
   - Effort: M. Priority: LOW. valid through 2026-Q3.

### EXPLICITLY DO NOT BORROW (terminology + structural)

| Item | Reason for exclusion |
|------|---------------------|
| `ROADMAP.md` as root artifact | AA-MA uses `[task]-plan.md`. ROADMAP language fragments lexicon. |
| Phase numbering (Phase 1, 2…) | AA-MA uses Milestone M1, M2. Mixing phase/milestone language confuses execution. |
| `PLAN.md` singular root convention | AA-MA has 1 plan per task/branch; gsd has 1 PLAN per phase. |
| `SUMMARY.md` as execution journal | AA-MA uses `provenance.log`. Renaming would fragment customer expectations. |
| `gsd-*` agent names | aa-ma-forge has `aa-ma-scribe`, `aa-ma-validator`. Importing gsd agent names creates registry collision. |
| `ultraplan-phase` workflow | Direct terminology collision with aa-ma-forge `/aa-ma-plan` (already navigated this naming once in 2026-04 when Anthropic shipped a built-in `ultraplan`). |

---

## D. Cross-source ranked M3+ candidates (top 6)

(Already surfaced in the **Top summary** table at the document head; consolidated here with detailed rationale and "valid through" decay dates.)

1. **mattpocock `tdd`** (PROPOSED-M3+, **HIGH**, valid through 2026-Q3)
   - Rationale: engineering-standards Theme 2 mandates TDD; mattpocock's `tdd` skill is the operational "how" (single-file). Effort S. ADR optional (the doctrine is already established; adoption is procedural, not architectural).

2. **gstack `/context-save` + `/context-restore`** (PROPOSED-M3+, **HIGH**, valid through 2026-Q3)
   - Rationale: direct overlap with AA-MA `provenance.log` CHECKPOINT pattern. Should be diffed against the existing CHECKPOINT format first to determine: adopt-as-pair, supersede-CHECKPOINT, or document-orthogonal-overlap.

3. **mattpocock `to-prd`** (PROPOSED-M3+, MEDIUM, valid through 2026-Q3)
   - Rationale: candidate Phase 2.5 of `/aa-ma-plan` — output a PRD before the 12-element plan when scope is large. Effort M (requires command wiring). ADR warranted (changes the planning workflow shape).

4. **mattpocock `git-guardrails-claude-code`** (DEFERRED-DIFF, MEDIUM, valid through 2026-Q3)
   - Rationale: functional overlap with `commit-signature.sh` + `commit-drift.sh` hooks. Diff first; adoption decision depends on what the upstream skill covers that current hooks don't.

5. **mattpocock `diagnose`** (PROPOSED-M3+, MEDIUM, valid through 2026-Q3)
   - Rationale: disciplined diagnosis loop overlaps with `debugging-strategies` skill. Diff first; either adopt+supersede or document orthogonal coverage.

6. **gstack `/freeze` + `/careful` + `/guard`** (PROPOSED-M3+, MEDIUM, valid through 2026-Q3)
   - Rationale: defensive-mode toggle patterns complement milestone HARD gates. Single-file each. Could ship as a triad in a single ADR.

---

## Provenance

This audit synthesizes three canonical inventories fetched on 2026-05-10 via `gh api`:

- [`docs/research/_inventories/mattpocock-inventory.json`](_inventories/mattpocock-inventory.json) — `gh api repos/mattpocock/skills` (68425 stars, default_branch=main, last_updated=2026-05-10T09:41:10Z)
- [`docs/research/_inventories/gstack-inventory.json`](_inventories/gstack-inventory.json) — `gh api repos/garrytan/gstack` (92598 stars, default_branch=main, last_updated=2026-05-10T09:50:10Z)
- [`docs/research/_inventories/gsd-inventory.json`](_inventories/gsd-inventory.json) — `gh api repos/gsd-build/get-shit-done` (61215 stars, default_branch=main, last_updated=2026-05-10T09:31:43Z)

Each JSON has `_meta.{source_url, fetched_at, verifier_method=gh-api, stars, default_branch, last_updated}` for staleness checks.

The L-001 lesson ("External URL First Principle") emerged from this plan's Phase 3 — the original Phase 3 audit dispatched a research agent without naming the canonical URL and the agent conflated locally-installed plugins with the source repo. Re-fetching directly from `gh api` produced the corrected inventories above and is the basis of every claim in this document.

## How to use this audit

- **Plan authors:** before authoring a new `/aa-ma-plan` for skill addition, check this document's Section A/B/C to see whether the candidate skill is already covered (ADOPTED, SUPERSEDED, DERIVED-FROM, EXCLUDED, or DEFERRED-DIFF).
- **Re-validation:** if reviewing this audit after 2026-Q3, re-run the fetch step (`gh api repos/<owner>/<repo>` for each of the 3 sources) and update `docs/research/_inventories/*.json`. Star counts, last_updated timestamps, and skill counts may have shifted.
- **Adopting a PROPOSED candidate:** follow the M1/M2 fork+ADR+test pattern (3 commits minimum: fork, ADR, frontmatter test). Use `Skill(write-a-skill)` if authoring net-new skills rather than forks.

## Status of this document

`Reviewed-Through-Date: 2026-05-10`. Re-validate by 2026-Q3 (next inventory refresh window). Adoption decisions herein are recommendations; per-skill adoption requires its own AA-MA plan with ADR.
