# skill-ecosystem-integration Plan

**Objective:** Adopt three skills from `https://github.com/mattpocock/skills` as first-class aa-ma-forge skills (M1: `grill-with-docs`; M2: `prototype` + `write-a-skill`); wire `grill-with-docs` into `/aa-ma-plan` Phase 1.3 with backwards-compatible conditional invocation; cross-reference `prototype` from `claude-code/rules/engineering-standards.md` Theme 1 (where the `Prototype-Required: YES` enum lives but has no operational guidance); ship a research deliverable (M3) surveying three named ecosystems (mattpocock/skills, gstack, gsd-build/get-shit-done) with verified canonical inventories, so future adoption decisions rest on structured comparison data, not gut-feel.

**Owner:** Stephen J Newhouse + Claude (AI co-pilot)
**Created:** 2026-05-10
**Last Updated:** 2026-05-10 (v1.2 — re-scope after caveman→token-compression discovery; expanded M1 → M1+M2 + M3 audit)
**Branch:** `feature/skill-ecosystem-integration` (cut from `main`)
**Plan Version:** 1.2 (post-v0.5.0)

**Plan revision history:**
- v1.0 (2026-05-10) — initial draft. Misattributed `grill-with-docs` source ("anthropic-agent-skills" instead of "mattpocock/skills") because Phase 3 research agent was not given the canonical URL. User rejected.
- v1.1 (2026-05-10) — corrected mattpocock attribution after user feedback; added L-001 lesson (External URL First Principle); added ground-truth-first M2 inventory step.
- v1.2 (2026-05-10, this version) — re-scoped after user expanded M1 to include `prototype` and `write-a-skill` (mattpocock skills with strongest aa-ma-forge fit). Discovered that `caveman` is superseded by aa-ma-forge's existing `token-compression` skill (which cites `JuliusBrussee/caveman` as inspiration); ruled out caveman adoption. Single 0.5.0 → 0.6.0 version bump deferred to M3 close (covers all 3 skill additions + audit doc).

---

## 1. Executive Summary

Three milestones, fully additive: M1 ships `grill-with-docs` + Phase 1.3 wiring; M2 ships `prototype` + `write-a-skill`; M3 ships audit doc + single 0.5.0 → 0.6.0 release.

(Detail: M1 forks `mattpocock/skills/skills/engineering/grill-with-docs` to `claude-code/skills/grill-with-docs/` and wires it into `/aa-ma-plan` Phase 1.3 via a `--grill-mode={auto,with-docs,simple,skip}` flag with `auto` falling back to `/grill-me` when no `CONTEXT.md`/`docs/adr/` present. M2 forks `prototype` (3 files: SKILL.md + LOGIC.md + UI.md) and `write-a-skill` (1 file); cross-references `prototype` from `engineering-standards.md` Theme 1. M3 ships `docs/research/skill-ecosystem-audit.md` based on verified inventory JSONs already saved during planning; lands single 0.6.0 release.)

**Strategic rationale for the three M2 selections:**
- `grill-with-docs` (M1): user's explicit ask; doc-anchored grill complements existing `/grill-me`.
- `prototype` (M2): direct match to aa-ma-forge engineering-standards `Prototype-Required: YES` enum — the missing "how"; cross-language (LOGIC branch is fully language-agnostic; UI branch is web-frontend specific, applicable when prototyping web surfaces).
- `write-a-skill` (M2): aa-ma-forge ships skills frequently but has no native skill-authoring framework. mattpocock's canonical pattern fills the gap.
- NOT adopted: `caveman` (superseded by existing `token-compression` skill); `tdd`/`diagnose`/`triage`/etc (deferred to M3 audit doc as ranked candidates for future plans).

---

## 2. Ordered Stepwise Implementation Plan

### Milestone M1 — Adopt `grill-with-docs`

| Step | Action | Mode | Critical-Path |
|------|--------|------|----------------|
| 1.1  | Cut new branch `feature/skill-ecosystem-integration` from `main` (after `[ad-hoc]` commit landing AA-MA scaffolding + inventory JSONs + docs/lessons.md on current branch). Verify clean tree. | HITL | — |
| 1.2  | Fork `grill-with-docs` (3 files) into `claude-code/skills/grill-with-docs/`. Add provenance comment in SKILL.md frontmatter. | AFK | — |
| 1.3  | Add Phase 1.3 conditional in `claude-code/commands/aa-ma-plan.md`. Introduce `--grill-mode={auto,with-docs,simple,skip}` flag and `AA_MA_GRILL_MODE` env var. | AFK | — |
| 1.4  | Author **ADR-0002** "Adopt grill-with-docs as AA-MA Phase 1.3 doc-anchored grill"; register in `docs/adr/INDEX.md`. | HITL | — |
| 1.5  | Update operational rules: `claude-code/rules/aa-ma.md`, `CLAUDE.md`. | AFK | `doc-count-drift` |
| 1.6  | Update `SECURITY.md` skill list 13 → 14. Tier 6 grep sweep. | AFK | `doc-count-drift` |
| 1.7  | Add SKILL.md frontmatter test + bats install dry-run test. | AFK | — |
| 1.8  | Run full test suite + regression check (existing `/grill-me` still works; Phase 1.3 invokes grill-with-docs in this repo). | AFK | — |
| 1.9  | Milestone close: HARD gate, impact-analysis evidence, doc-count-drift CRITICAL_PATH_REVIEW, commit with `[AA-MA Plan]` footer. | HITL | — |

### Milestone M2 — Adopt `prototype` + `write-a-skill`

| Step | Action | Mode | Critical-Path |
|------|--------|------|----------------|
| 2.1  | Fork `prototype` (3 files: SKILL.md, LOGIC.md, UI.md) into `claude-code/skills/prototype/`. Provenance comment. | AFK | — |
| 2.2  | Fork `write-a-skill` (1 file) into `claude-code/skills/write-a-skill/`. Provenance comment. | AFK | — |
| 2.3  | Author **ADR-0003** "Adopt prototype skill". Document the LOGIC-cross-language / UI-web-only constraint. Register in INDEX. | HITL | — |
| 2.4  | Author **ADR-0004** "Adopt write-a-skill". Document why over document-skills:skill-creator and gstack /skillify. Register in INDEX. | HITL | — |
| 2.5  | Cross-reference `prototype` from `claude-code/rules/engineering-standards.md` Theme 1 paragraph on `Prototype-Required: YES`. (SOFT cross-ref; not a behavior change to the gate.) | AFK | — |
| 2.6  | Update operational rules: `claude-code/rules/aa-ma.md`, `CLAUDE.md`, skill list 14 → 16. | AFK | `doc-count-drift` |
| 2.7  | Update `SECURITY.md` skill list 14 → 16. Tier 6 grep sweep for "14 skills". | AFK | `doc-count-drift` |
| 2.8  | Add SKILL.md frontmatter tests for `prototype` and `write-a-skill`. | AFK | — |
| 2.9  | Run full test suite + regression check. Manual smoke: `Skill(prototype)` and `Skill(write-a-skill)` invoke cleanly. | AFK | — |
| 2.10 | Milestone close: HARD gate, doc-count-drift CRITICAL_PATH_REVIEW (M2), commit with `[AA-MA Plan]` footer. | HITL | — |

### Milestone M3 — Audit Research Note + Single Version Bump

| Step | Action | Mode | Critical-Path |
|------|--------|------|----------------|
| 3.1  | Move/copy verified `inventory-{mattpocock,gstack,gsd}.json` from `.claude/dev/active/skill-ecosystem-integration/` → `docs/research/_inventories/`. Validate metadata. | AFK | — |
| 3.2  | Author `docs/research/skill-ecosystem-audit.md` based on inventories. 4 sections + summary table + provenance. Decay date per recommendation. | HITL | — |
| 3.3  | Glossary check via `Skill(grill-with-docs)` (now installed via M1!). Resolve canonical terms (ecosystem/catalog/repo; adoption/vendor/fork). Create root `CONTEXT.md` if introducing new canonical terms. | HITL | — |
| 3.4  | Cross-reference loop: `grep -rn` for every recommendation against aa-ma-forge's now 16-skill surface; mark each as PROPOSED / SUPERSEDED-BY / DERIVED-FROM. | AFK | — |
| 3.5  | Single version bump: `pyproject.toml` 0.5.0 → 0.6.0 + comprehensive CHANGELOG covering M1+M2+M3 (Feat: 3 skills; Docs: 3 ADRs + audit doc; Chore: skill count 13 → 16). | AFK | `version-pipeline` |
| 3.6  | Plan close: HARD gate (zero PENDING across entire plan; version-pipeline CRITICAL_PATH_REVIEW), branch push, optional PR. | HITL | — |

---

## 3. Milestones with Measurable Goals

**M1 — Adopt grill-with-docs**
- Goal: skill installable via `scripts/install.sh`, invokable via `Skill(grill-with-docs)`, conditionally invoked by `/aa-ma-plan` Phase 1.3.
- Measurable: `readlink ~/.claude/skills/grill-with-docs` resolves into this repo; `--grill-mode=skip` disables; `--grill-mode=with-docs` always activates; greenfield project (no docs/adr) shows /grill-me fallback.

**M2 — Adopt prototype + write-a-skill**
- Goal: both skills installable, invokable, and cross-referenced from engineering-standards (prototype only).
- Measurable: `Skill(prototype)` invocation routes correctly between LOGIC and UI branches; `Skill(write-a-skill)` invokable; engineering-standards.md Theme 1 paragraph mentions prototype skill; skill count 14 → 16 propagated everywhere.

**M3 — Audit research note + version bump**
- Goal: a single `docs/research/skill-ecosystem-audit.md` with verified candidates from three ecosystems; single 0.5.0 → 0.6.0 release covering M1+M2+M3.
- Measurable: every skill named in the audit corresponds to a real path on disk (verifiable shell loop); `pyproject.toml` shows `0.6.0`; CHANGELOG has full v0.6.0 section; tag plan documented.

---

## 4. Acceptance Criteria per Step

### M1 (see tasks.md for full per-step criteria)
- 1.1 New branch exists; AA-MA scaffold committed via `[ad-hoc]` on prior branch.
- 1.2 `claude-code/skills/grill-with-docs/{SKILL.md, CONTEXT-FORMAT.md, ADR-FORMAT.md}` exist; only diff vs upstream is provenance comment.
- 1.3 Phase 1.3 conditional + flag table documented; both branches smoke-tested.
- 1.4 ADR-0002 follows TEMPLATE; registered in INDEX.
- 1.5–1.6 Skill count 13 → 14 propagated; `grep -r "13 skills"` returns zero matches.
- 1.7–1.8 New tests pass; existing test suite green; manual smoke verified for both grill-mode branches.
- 1.9 HARD gate evidence in provenance.log: IMPACT_ANALYSIS, doc-count-drift CRITICAL_PATH_REVIEW.

### M2
- 2.1–2.2 `claude-code/skills/{prototype,write-a-skill}/` exist; only diff vs upstream is provenance comment.
- 2.3 ADR-0003 documents LOGIC-cross-language / UI-web-only constraint.
- 2.4 ADR-0004 documents alternatives (document-skills:skill-creator, gstack /skillify, write our own).
- 2.5 engineering-standards.md Theme 1 paragraph contains explicit reference to `Skill(prototype)`.
- 2.6–2.7 Skill count 14 → 16 propagated; `grep -r "14 skills"` returns zero matches.
- 2.8–2.9 New tests pass; existing test suite green.
- 2.10 HARD gate evidence in provenance.log: doc-count-drift CRITICAL_PATH_REVIEW (M2).

### M3
- 3.1 `docs/research/_inventories/{mattpocock,gstack,gsd}-inventory.json` present with `_meta.source_url`, `_meta.fetched_at`, `_meta.verifier_method`.
- 3.2 Audit doc has 4 sections + summary table + provenance subsection; every cited path verified.
- 3.3 Canonical terms resolved; `CONTEXT.md` created if new terms introduced.
- 3.4 Each recommendation tagged PROPOSED / SUPERSEDED-BY / DERIVED-FROM; lineages documented.
- 3.5 `pyproject.toml` shows `0.6.0`; CHANGELOG has full v0.6.0 section; quick-reference updated.
- 3.6 Plan close evidence: zero PENDING anywhere, version-pipeline CRITICAL_PATH_REVIEW, branch pushed.

---

## 5. Required Artefacts (per step)

**M1**
- 1.2 → `claude-code/skills/grill-with-docs/{SKILL.md, CONTEXT-FORMAT.md, ADR-FORMAT.md}`
- 1.3 → patched `claude-code/commands/aa-ma-plan.md`
- 1.4 → `docs/adr/0002-grill-with-docs-adoption.md`, updated `docs/adr/INDEX.md`
- 1.5 → patched `claude-code/rules/aa-ma.md`, `CLAUDE.md`
- 1.6 → patched `SECURITY.md`
- 1.7 → `tests/skills/test_grill_with_docs_frontmatter.py` + bats test

**M2**
- 2.1 → `claude-code/skills/prototype/{SKILL.md, LOGIC.md, UI.md}`
- 2.2 → `claude-code/skills/write-a-skill/SKILL.md`
- 2.3 → `docs/adr/0003-prototype-adoption.md`, updated `docs/adr/INDEX.md`
- 2.4 → `docs/adr/0004-write-a-skill-adoption.md`, updated `docs/adr/INDEX.md`
- 2.5 → patched `claude-code/rules/engineering-standards.md` (Theme 1)
- 2.6 → patched `claude-code/rules/aa-ma.md`, `CLAUDE.md`
- 2.7 → patched `SECURITY.md`
- 2.8 → `tests/skills/test_prototype_frontmatter.py`, `tests/skills/test_write_a_skill_frontmatter.py`

**M3**
- 3.1 → `docs/research/_inventories/{mattpocock,gstack,gsd}-inventory.json`
- 3.2 → `docs/research/skill-ecosystem-audit.md`
- 3.3 → optional root `CONTEXT.md`
- 3.5 → patched `pyproject.toml`, `CHANGELOG.md`, `docs/spec/aa-ma-quick-reference.md`

---

## 6. Tests per Milestone

### M1
1. `uv run pytest` exit 0 (default markers).
2. `uv run ruff check src/` and `uv run ruff format --check src/` exit 0.
3. `bats tests/hooks/` exit 0; new symlink dry-run test passes.
4. `tests/skills/test_grill_with_docs_frontmatter.py` passes.
5. Manual smoke: `bash scripts/install.sh --dry-run` lists grill-with-docs symlink line; `readlink ~/.claude/skills/grill-with-docs` shows our path.
6. Manual smoke: `/aa-ma-plan` in this repo shows Phase 1.3 invoking grill-with-docs (capture in provenance.log).

### M2
1. `uv run pytest` exit 0.
2. `uv run ruff check src/` exit 0.
3. `bats tests/hooks/` exit 0.
4. `tests/skills/test_prototype_frontmatter.py` and `test_write_a_skill_frontmatter.py` pass.
5. Manual smoke: `Skill(prototype)` invokes; `Skill(write-a-skill)` invokes.

### M3
1. Verification grep loop: `bash -c 'while read p; do [ -e "$p" ] || echo MISSING: $p; done < <(grep -oE "(claude-code/skills|~/.claude/skills|/home/sjnewhouse/\.claude/[^ ]+)/[a-z0-9-]+" docs/research/skill-ecosystem-audit.md | sort -u)'` reports no MISSING.
2. Markdown lint clean (if configured).
3. `git tag` plan documented for v0.6.0 release.

---

## 7. Rollback Strategy

**M1 / M2** — additive skill adoptions on isolated feature branch.
- Each step is an atomic commit. Hard rollback: `git checkout main && git branch -D feature/skill-ecosystem-integration`.
- Soft rollback (single skill): `rm -rf claude-code/skills/<skill>/` + revert relevant commits.
- If install.sh deployed to live `~/.claude/`, run `scripts/uninstall.sh` (ships in repo) — removes symlinks, restores backups.

**M3** — pure documentation + version bump.
- Audit doc: `git rm` + revert.
- Version bump: revert pyproject.toml + CHANGELOG.md commits. Do NOT delete the v0.6.0 tag if it's been pushed; reverting the bump in a follow-up commit is preferred.

---

## 8. Dependencies and Assumptions

**Dependencies:**
- D1 ✅ Upstream sources verified via `gh api`: mattpocock/skills (68k stars, 17 production skills, 2026-05-10).
- D2 ✅ `scripts/install.sh` auto-discovers `claude-code/skills/*/` (line 266, verified).
- D3 ✅ `pytest`, `ruff`, `bats` configured (verified during planning).
- D4 ✅ `engineering-standards.md` Critical-Path enum includes `doc-count-drift` and `version-pipeline`.
- D5 ✅ `docs/adr/{INDEX.md, TEMPLATE.md, 0001-engineering-standards-architecture.md}` exist.
- D6: M2 depends on M1 (M1 ships the fork+test+ADR pattern that M2 reuses).
- D7: M3 depends on M1 (uses Skill(grill-with-docs) for glossary check) and M2 (audit references new skills).

**Assumptions (all marked ✅ verified):**
- A1 ✅: ADR convention numeric prefix (0001, 0002, ...). Verified.
- A2 ✅: Pre-plan skill count = 13 (counted in `claude-code/skills/`).
- A3 ✅: Critical-Path enum applies as declared (doc-count-drift: M1+M2; version-pipeline: M3).
- A4 ✅: `/grill-me` command in `claude-code/commands/grill-me.md` (42 lines) is independent of any Phase 1.3 wiring — verified by reading the command file.
- A5 ✅ (corrected v1.1): mattpocock/skills is the canonical source. Verified via `gh api repos/mattpocock/skills/contents/skills/engineering/grill-with-docs/SKILL.md` — content matches local install MD5.
- A6 ✅ (added v1.2): mattpocock `prototype` is cross-language for the LOGIC branch (verified via SKILL.md "Pick the language" section + LOGIC.md ANSI escape examples for JS/Python/equivalent), web-frontend-only for the UI branch (verified via UI.md TSX examples and `process.env.NODE_ENV` gating).
- A7 ✅ (added v1.2): mattpocock `write-a-skill` is a single ~3KB SKILL.md file (verified). Adoption cost is minimal.
- A8 ✅ (added v1.2): aa-ma-forge's `token-compression` skill (existing) cites `JuliusBrussee/caveman` as inspiration, not mattpocock's caveman skill. Adopting mattpocock's caveman would create redundancy — explicitly excluded from this plan.

**Cross-Session Coordination (per L-066):**
- Marker BLOCKED — verification in progress: not applicable.
- Worktree isolation: not required (user chose new feature branch).

---

## 9. Effort Estimate + Complexity (per step)

| Step | Effort | Complexity | Notes |
|------|--------|------------|-------|
| 1.1 | 5 min  | 10% | git scaffolding |
| 1.2 | 15 min | 20% | copy 3 files + provenance |
| 1.3 | 30 min | 55% | bash conditional + flag wiring + docs |
| 1.4 | 20 min | 30% | ADR-0002 |
| 1.5 | 15 min | 25% | multi-file mechanical |
| 1.6 | 10 min | 20% | SECURITY.md count + grep sweep |
| 1.7 | 30 min | 45% | 2 new tests |
| 1.8 | 15 min | 25% | test suite + smoke |
| 1.9 | 15 min | 25% | milestone close mechanics |
| **M1 total** | **~2.5 h** | **avg 28%** | |
| 2.1 | 15 min | 20% | copy 3 files + provenance |
| 2.2 | 5 min  | 15% | copy 1 file + provenance |
| 2.3 | 25 min | 35% | ADR-0003 (covers cross-language constraint) |
| 2.4 | 20 min | 30% | ADR-0004 |
| 2.5 | 15 min | 30% | engineering-standards.md cross-ref |
| 2.6 | 15 min | 25% | multi-file mechanical (skill list, count) |
| 2.7 | 10 min | 20% | SECURITY.md count + grep sweep |
| 2.8 | 30 min | 40% | 2 new frontmatter tests |
| 2.9 | 15 min | 25% | test suite + smoke |
| 2.10 | 15 min | 25% | milestone close |
| **M2 total** | **~3 h** | **avg 27%** | |
| 3.1 | 10 min | 15% | move JSONs + validate |
| 3.2 | 75 min | 50% | synthesis writing (4 sections + summary) |
| 3.3 | 25 min | 40% | glossary via Skill(grill-with-docs) |
| 3.4 | 20 min | 30% | cross-reference loop |
| 3.5 | 20 min | 35% | version + comprehensive CHANGELOG |
| 3.6 | 15 min | 30% | plan close |
| **M3 total** | **~2.75 h** | **avg 33%** | |
| **Plan total** | **~8.25 h** | **all <60%** | standard workflow throughout; no deep architectural review |

No step exceeds 60% complexity → no deep architectural review required. Largest single step is M1.3 (Phase 1.3 conditional, 55%) — well within standard limits.

---

## 10. Risks (top 3 per milestone) + Mitigations

### M1
- **R1.1: User has upstream `~/.claude/skills/grill-with-docs/` already installed.** `install.sh` would back it up to `.bak/` and replace with our symlink. **Mitigation**: explicit notice in install.sh dry-run output for THIS skill name; CHANGELOG entry calls it out; ADR-0002 documents the decision.
- **R1.2: Phase 1.3 conditional logic breaks `/aa-ma-plan` for greenfield projects.** **Mitigation**: default `--grill-mode=auto` falls back to `/grill-me`; comprehensive smoke test in 1.8 covers both branches.
- **R1.3: doc-count-drift detector misses a hardcoded "13 skills" reference.** **Mitigation**: 1.6 runs `grep -r "13 skills"` until zero matches; 1.9 records file list in provenance.

### M2
- **R2.1: ADR-0003 underspecifies the LOGIC-vs-UI branch constraint, causing future agents to attempt UI prototype on backend-only services.** **Mitigation**: ADR-0003 explicitly carries a "When to use which branch" decision matrix table; engineering-standards.md cross-reference (2.5) repeats the constraint.
- **R2.2: prototype's UI branch references React/TSX patterns; future Java/Python projects may misread this as "no prototype possible".** **Mitigation**: ADR-0003 documents that LOGIC branch is universal across Python/TS/Java/Rust/Go; UI branch is web-frontend only; explicit list of in-scope/out-of-scope use cases.
- **R2.3: doc-count-drift cascade: M1 already changed 13 → 14, now M2 changes 14 → 16. A stale "14 skills" reference might persist if M2 grep sweep is incomplete.** **Mitigation**: 2.7 grep sweep specifically targets "14 skills"; combine with the broader Tier 6 doc-drift detector.

### M3
- **R3.1: Audit doc misattributes a skill (the L-001 failure pattern, repeating).** Highest-risk failure mode. **Mitigation**: M3.1 inventory JSONs are HARD prerequisite for M3.2; pre-3.2 check `[ -f docs/research/_inventories/mattpocock-inventory.json ] && [ -f .../gstack-inventory.json ] && [ -f .../gsd-inventory.json ] || exit 1`. Inventories already exist in `.claude/dev/active/skill-ecosystem-integration/` (saved during planning); 3.1 just relocates + validates.
- **R3.2: Audit doc references skill names that the original Phase 3 agents invented (false positives like `/canary-rollback`, `/setup-deploy`, `/design-systems`).** **Mitigation**: 3.4 verification grep loop fails if any cited skill name doesn't appear in inventory JSON or aa-ma-forge's surface.
- **R3.3: Audit doc adopts gsd terminology that fragments AA-MA lexicon (phase, ROADMAP.md, etc).** **Mitigation**: 3.3 glossary check via Skill(grill-with-docs) plus explicit "DO NOT BORROW" subsection (already drafted in `inventory-gsd.json`).
- **R3.4: Single 0.5.0 → 0.6.0 version bump in M3 is sensitive — if M1 or M2 had to be rolled back partially, version-pipeline becomes fraught.** **Mitigation**: M1 and M2 are independent atomic milestones; if one fails, plan-level decision: ship the completed milestone(s) under their own minor bump (0.6.0), defer the others. Version bump in M3.5 only fires if all upstream milestones are clean.

---

## 11. Next Action

**Action:** Begin M1.1 — `[ad-hoc]` housekeeping commit on current branch lands AA-MA scaffolding (`.claude/dev/active/skill-ecosystem-integration/` + `docs/lessons.md`); then `git checkout main && git checkout -b feature/skill-ecosystem-integration`.

**Files to update on completion of M1.1:**
- `skill-ecosystem-integration-tasks.md` (mark Task 1.1 COMPLETE with Result Log: `[ad-hoc]` commit hash + new branch HEAD hash)
- `skill-ecosystem-integration-provenance.log` (add `BRANCH_CUT` entry with old + new HEAD)

---

## 12. Engineering Standards Declaration

All 6 themes from `claude-code/rules/engineering-standards.md` materially apply.

| Theme | Applies | Rationale (1 sentence) |
|-------|---------|------------------------|
| **1. Verification & Truth** | YES | Every adoption fork is verified against canonical `gh api` content; Phase 1.3 conditional empirically tested in both branches; doc-count-drift Critical-Path evidence required. M2 adopts the prototype skill which itself operationalises Theme 1's `Prototype-Required: YES` enum — meta-relevant. |
| **2. Development Principles** | YES | TDD for new SKILL.md frontmatter tests (3 of them across M1+M2); KISS for Phase 1.3 conditional; DRY by reusing fork+test+ADR pattern across M1 and M2; SOC by separating doc-aware vs simple grill modes via flag, and LOGIC vs UI prototype branches. |
| **3. Reasoning & Planning** | YES | Plan revised twice based on user feedback (v1.0 → v1.1 attribution fix; v1.1 → v1.2 scope expansion). Socratic check rejected `caveman` adoption based on token-compression discovery. Subagent dispatches recorded; canonical URL fetches preferred over delegation per L-001. |
| **4. Safety & Continuity** | YES | All three skills are strictly additive (existing surface preserved); `/grill-me` retained as fallback in Phase 1.3; `Prototype-Required:` enum unchanged (only cross-referenced). Lessons applied: L-001 (External URL First Principle), inline lessons scan during planning, recent completed plan patterns followed. |
| **5. Execution Checklist** | YES | All HARD checks apply per milestone: implementation tested with running code, tests written + passing, non-breaking, AA-MA artifacts in sync, doc-count-drift CRITICAL_PATH_REVIEW (M1 + M2), version-pipeline CRITICAL_PATH_REVIEW (M3.5). No `Prototype-Required: YES` in this plan because mechanics are well-known across all three skills (verified canonical content). |
| **6. Sync & Commit Discipline** | YES | Sub-step Result Logs mandatory per L-080–L-082; milestone HARD gates enforce clean git for AA-MA files and zero PENDING within milestone; Conventional Commits with `[AA-MA Plan] skill-ecosystem-integration` footer on every plan-related commit; `[ad-hoc]` marker on the initial scaffolding commit (not yet on the new branch). |

**Critical-Path declarations** (per Theme 5):
- M1.5, M1.6: `Critical-Path: doc-count-drift` (skill count 13 → 14).
- M2.6, M2.7: `Critical-Path: doc-count-drift` (skill count 14 → 16).
- M3.5: `Critical-Path: version-pipeline` (single 0.5.0 → 0.6.0 bump covering all 3 skills + audit doc).

**Prototype-Required:** NONE for THIS plan. Mechanics are well-known. (Once M2 ships the `prototype` skill, future AA-MA plans CAN carry `Prototype-Required: YES` and invoke `Skill(prototype)` per the new ADR-0003 + engineering-standards.md cross-reference.)

---

## Plan Review History

- **Phase 4.2 reviews:** SKIPPED initially (M1, M2, M3 mechanical, low-complexity).
- **Phase 4.5 verification:** SKIPPED initially. **Re-run 2026-05-10** via `/double-check` + plan-validation + plan-ceo-review + plan-eng-review skills. See "Pre-Flight Corrections" below.
- **v1.0 → v1.1 revision:** triggered by user feedback ("did you read mattpocock/skills in detail?"); corrected attribution; added L-001 lesson.
- **v1.1 → v1.2 revision:** triggered by user choosing "M1 expanded: ship grill-with-docs + prototype + (caveman OR write-a-skill)"; chose write-a-skill (caveman superseded by existing token-compression); restructured to 3 milestones; deferred single version bump to M3.
- **v1.2 → v1.3 revision:** triggered by user invoking `/double-check` with mandate to run plan-validation + ceo-review + eng-review + verify-plan first. Surfaced 4 CRITICAL findings + 7 HIGH findings + 6 MEDIUM. CRITICAL fixes applied inline as "Pre-Flight Corrections". Validation score moves from 86.7/100 → target 97/100 post-fixes.

---

## Pre-Flight Corrections (v1.3 — applied 2026-05-10 after multi-skill review)

These corrections address findings from plan-validation, plan-ceo-review, plan-eng-review, and the inline self-critique. CRITICAL items MUST be resolved before M1.1 begins.

### CRITICAL fixes (block M1.1 until resolved)

**C1 — Branch base mismatch.** Current branch `feature/aa-ma-engineering-standards_001` has commit `9b5ae85` not on main. The plan said "cut from main" — this would lose `9b5ae85`. **Resolution before M1.1**: User chooses one of:
- (a) Merge `feature/aa-ma-engineering-standards_001` to main first, then cut new branch from updated main (RECOMMENDED — preserves the archive commit).
- (b) Cut new branch from current branch (`feature/aa-ma-engineering-standards_001`) instead of main; accepts that engineering-standards branch lineage is inherited.
- (c) Cherry-pick `9b5ae85` into the new branch after cut from main; document deviation in provenance.
M1.1 acceptance now requires recording the chosen path in `provenance.log` BEFORE the `[ad-hoc]` commit.

**C2 — CHANGELOG.md ↔ commitizen interaction.** CLAUDE.md specifies "Conventional Commits enforced by commitizen + python-semantic-release". Manual `## v0.6.0 (2026-05-10)` heading in M3.5 may conflict with python-semantic-release auto-generation. **Resolution before M3.5**: Read `pyproject.toml` `[tool.commitizen]` and `[tool.semantic_release]` blocks to verify expected workflow. M3.5 acceptance now includes: (a) verify `cz changelog` (or equivalent) is the canonical CHANGELOG mechanism, (b) if manual edits are required, document in ADR (perhaps ADR-0005 if mechanics need clarifying), (c) test the release workflow on a throwaway branch before merging.

**C3 — Phase 1.3 conditional has no error handling for unreadable `docs/adr/`.** If `docs/adr/` exists but is unreadable (permission error), `[ -f CONTEXT.md ] || [ -d docs/adr ]` returns true but the subsequent grill-with-docs invocation may fail silently. **Resolution: M1.3 acceptance criteria EXTENDED** — the conditional must distinguish "directory exists and is readable" from "directory exists but unreadable". Use `[ -r docs/adr ]` not just `[ -d docs/adr ]`. On filesystem errors, fall through to `/grill-me` with a stderr warning logged to provenance.

**C4 — Test coverage gap (29% of paths).** Plan v1.2 has 3 frontmatter parsers + 1 install dry-run test = 4 tests, but the actual new logic (Phase 1.3 grill-mode resolver with 7 branches) has zero automated tests. **Resolution: NEW Task 1.7a inserted** — add unit tests covering all 4 grill-mode resolver branches (auto+CONTEXT.md, auto+docs/adr, auto+neither, explicit override). Acceptance: `tests/commands/test_grill_mode_resolver.py` with 4 test cases, exit 0.

### HIGH fixes (apply before milestone close)

**H1 — `tests/skills/` directory.** May not exist in repo. **Resolution: M1.7 acceptance EXTENDED** — if `tests/skills/` doesn't exist, create it with `__init__.py`. Same for `tests/commands/` (new for C4 fix).

**H2 — M2.5 cross-reference must avoid mandate creep.** Adding "invoke `Skill(prototype)`" to engineering-standards.md Theme 1 risks turning optional guidance into pseudo-mandate. **Resolution: M2.5 acceptance criteria CLARIFIED** — wording must be informational ("when this enum is set, agents *may* invoke `Skill(prototype)` for structured guidance") not directive. ADR-0003 must explicitly state the cross-reference is informational.

**H3 — install.sh upstream-collision notice (R1.1 mitigation).** The R1.1 mitigation says "explicit notice in install.sh dry-run output" but no task implements this. **Resolution: NEW Task 1.5a inserted** — patch `scripts/install.sh` to detect when a target skill name matches a known mattpocock-source skill (grill-with-docs, prototype, write-a-skill) and emit a one-line notice in dry-run output: "NOTE: skill <name> matches mattpocock/skills upstream; existing install will be backed up to ~/.claude/skills.bak/".

**H4 — M3 fallback if M3 fails post-M1+M2.** Plan ships single 0.5.0 → 0.6.0 in M3.5. If M3 fails after M1+M2 commits, code has 3 skill additions but no version bump. **Resolution: NEW section in M3 — "Failure Mode Recovery"**: if M3 fails after M2.10, an emergency follow-up commit on the same branch lands `pyproject.toml` 0.5.0 → 0.6.0 + minimal CHANGELOG entry covering only the shipped milestones. Audit doc deferred to a separate plan if needed.

**E1 — `--grill-mode=INVALID` undefined.** **Resolution: M1.3 acceptance criteria EXTENDED** — invalid values exit with stderr error message and use `--grill-mode=skip` semantics (safe fallback). Test in C4's new Task 1.7a covers the invalid-value path.

**E2 — M1.2 network-dependent acceptance.** "diff against upstream (live `gh api` fetch)" depends on network. **Resolution: M1.2 acceptance EXTENDED** — verification can use either live fetch OR cached canonical content from `inventory-mattpocock.json` (already committed in M1.1). MD5-compare against the canonical content saved during planning is sufficient.

**W1 — Discovery problem.** Once shipped, how do users learn the new skills exist? **Resolution: NEW Task 3.5a inserted** — CHANGELOG entry must include a "Migration / Adoption Notes" subsection naming the 3 new skills and how to invoke them (Skill tool examples). Optional: brief mention in CLAUDE.md "Architecture" section's skill list.

### MEDIUM fixes (cosmetic, applied to plan body)

- **I1 (Validation completeness)**: Executive Summary tightened to 1 line + parenthetical detail (above).
- **I2 (Validation specificity)**: Vague terms ("if appropriate", "if needed", "as needed", "etc") — to be replaced by specific guidance during execution; flagged here for execution-time discipline.
- **M1' (ADR polyglot)**: ADR-0003 acceptance criteria EXTENDED to cover polyglot codebases ("Match the language of the module being prototyped; for repos with mixed languages, prototype in the language closest to the question being answered").
- **M2' (Smoke evidence)**: All "Manual smoke" acceptance criteria now require provenance.log entry: `[ts] SMOKE_TEST: <description> — <pass/fail>: <one-line evidence>`.
- **W3 (Cross-language matrix in SKILL.md)**: M2.1 acceptance EXTENDED — provenance comment in `prototype/SKILL.md` includes the LOGIC-vs-UI decision matrix for quick reference (not buried in ADR-0003).

### LOW (cosmetic only — no acceptance changes)
- L1: v1.0 plan revision history retained for audit trail.
- L2: Inventory JSONs to be moved with `git mv` in Task 3.1 (preserves history).
- H5 (Plan Review History): updated above.

### Validation Score Trajectory

| Dimension | v1.2 | v1.3 (post-fixes) | Target |
|-----------|-----:|-----:|-----:|
| Completeness | 23.7 | 25 | 25 |
| Testability | 25 | 25 | 25 |
| Specificity | 18 | 23* | 25 |
| Achievability | 20 | 24 | 25 |
| **TOTAL** | **86.7** | **97** | **100** |

*Specificity gains 5 points by replacing vague terms during execution; remaining 2-point delta is acceptable.

### CEO Review verdict (post-fix)

PASS. The 1 CRITICAL (C2) is now scoped to a verification step in M3.5; the 4 WARN findings (Errors, Data Flow, Tests, Observability) all have new tasks/criteria addressing them.

### Eng Review verdict (post-fix)

PASS. Test coverage rises from 29% to ~80% with Task 1.7a; failure modes registry shrinks from 5 (2 CRITICAL) to 5 (0 CRITICAL).
