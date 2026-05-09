# aa-ma-engineering-standards Context Log

_This log captures architectural decisions, trade-offs, and unresolved issues for the aa-ma-engineering-standards task._

---

## [2026-05-09] Plan Approved

- Plan: aa-ma-engineering-standards
- Approved by: Stephen Newhouse (via ExitPlanMode)
- Milestones: 5 (M0, M1, M2, M3, M4)
- HARD gates: M0 (Setup), M3 (Planning Standard bump), M4 (Release)
- SOFT gates: M1 (Doctrine), M2 (Workflow integration)

---

## [2026-05-09] Initial Context

**Feature Request (Phase 1):**

Codify engineering standards for `/aa-ma-plan` and `/execute-aa-ma-*` workflows in aa-ma-forge so that six themes (Verification & Truth, Development Principles, Reasoning & Planning, Safety & Continuity, Execution Checklist, Sync & Commit Discipline) become explicit, verifiable, and enforced — not lost in skill-soup, not duplicated across artifacts. The user's global `~/.claude/CLAUDE.md` already requires KISS/DRY/SOLID/SOC/TDD/Socratic/12-Factor, but those are private and not exposed to plugin consumers.

**Key Decisions (Phase 2 Brainstorming, via 7-question grill-with-docs interview):**

- **Decision AD-001 (D1):** Sharper multi-artifact integration model: ship 1 new doctrine rule + amend existing skills/commands; do not introduce a new skill or new aa-ma-plan phase.
  - **Rationale:** Avoids competition with `operational-constraints` and `plan-verification` skills; minimizes phase renumbering churn; concentrates doctrine in one auto-loaded rule file.
  - **Alternatives Considered:**
    1. Classic multi-artifact (new skill + new phase) — rejected: skill competition + churn.
    2. Single-rule-only (no skill/command amendments) — rejected: doctrine without invocation = dead text.
  - **Trade-offs:** Gain — minimal surface area expansion. Sacrifice — amendments must be tight (≤ +20 lines per skill); risk of bloat if discipline slips.

- **Decision AD-002 (D2):** Tiered enforcement: step-level ADVISORY + milestone-level tiered HARD/SOFT.
  - **Rationale:** Step-light keeps atomic steps fast; milestone-rigorous catches drift before it compounds. HARD on 4 mechanically-verifiable items: tests pass, API/code evidence, non-breaking, AA-MA sync + clean git.
  - **Alternatives Considered:**
    1. Step-level HARD gates — rejected: too much friction per step.
    2. Milestone-only with no step advisory — rejected: nothing nudges per-step compliance.
  - **Trade-offs:** Gain — programmatic enforcement at meaningful boundaries. Sacrifice — agent self-report at step level is honor-system; mitigated by milestone HARD verifying outcomes.

- **Decision AD-003 (D3):** Planning Standard bumps 11 → 12 elements. Element #12 = "Engineering Standards Declaration".
  - **Rationale:** Explicit declaration > implicit assumption. Detected by extending plan-verification Angle 6.
  - **Alternatives Considered:**
    1. Keep 11 elements; embed engineering standards inside an existing element — rejected: dilutes both elements.
    2. Add a new file type (`[task]-engineering.md`) — rejected: file-type proliferation; provenance.log + per-task flags are lower-ceremony (see D5).
  - **Trade-offs:** Gain — explicit, gated, verifiable. Sacrifice — hardcoded-count drift across 6+ files (mitigated via D3 + Tier 6 sweep in M3.7).

- **Decision AD-004 (D4):** Cheap inline lessons scan in Phase 1 of `/aa-ma-plan`.
  - **Rationale:** Reads `docs/lessons.md` (if present) + `git log --grep="revert\|fix\|hotfix"` (6 months) + top-3 most-recent completed context-logs. ~30s budget. No subagent dispatch. Reliable across project layouts.
  - **Alternatives Considered:**
    1. New `lessons-scan` skill — rejected (preserves D1; preserves lean skill catalog).
    2. Subagent-driven deep scan — rejected: latency + complexity.
    3. No automation; rely on author memory — rejected: defeats the "avoid repeated mistakes" theme.
  - **Trade-offs:** Gain — sub-30s overhead. Sacrifice — scope-limited; deep cross-project lessons aggregation explicitly out of scope.

- **Decision AD-005 (D5):** Prototype/empirical/critical-path evidence via `provenance.log` entries + per-task flag in `tasks.md`.
  - **Rationale:** Conditional triggering (`Prototype-Required:`, `Critical-Path:`) avoids always-on overhead. No new file type. provenance.log already records execution telemetry.
  - **Alternatives Considered:**
    1. Always-on prototype/empirical requirement — rejected: too heavy for trivial tasks.
    2. New `[task]-evidence.md` file type — rejected: file-type proliferation.
  - **Trade-offs:** Gain — opt-in surfacing of high-risk tasks. Sacrifice — flag must be set during planning (humans/agents may forget); mitigated by milestone HARD gate refusing completion when flag present without provenance entry.

- **Decision AD-006 (D6):** Milestone-end commit gate only; no step-level commit nudges.
  - **Rationale:** Lowest ceremony. Existing `aa-ma-commit-drift.sh` hook covers post-commit drift advisory (NOTE: prior wording said "BLOCKING" — corrected by verification finding C1 to **ADVISORY**; hook always exits 0 and warns but does not refuse the commit). New milestone HARD gate is independent — it gates milestone-COMPLETE artifact-flips, not git operations. The two are complementary (advisory post-commit warning + pre-COMPLETE artifact gate).
  - **Alternatives Considered:**
    1. `commit-often` step-level hook — rejected: noise without proportional benefit; clashes with batch step authoring.
    2. Auto-commit on milestone COMPLETE — rejected: removes user review step.
  - **Trade-offs:** Gain — friction at meaningful boundaries only. Sacrifice — long milestones can accumulate uncommitted work; mitigated by sub-step Result Log discipline (L-080-082) keeping artifacts in sync even when code commits batch.

- **Decision AD-007 (D7):** Introduce ADR convention (`docs/adr/`); first ADR is `0001-engineering-standards-architecture.md` capturing D1–D8.
  - **Rationale:** All three ADR criteria pass — hard to reverse, surprising without context, real trade-off. MADR off-the-shelf format avoids invent-our-own.
  - **Alternatives Considered:**
    1. Embed rationale in CHANGELOG.md only — rejected: CHANGELOG is for users, not architects.
    2. Embed rationale in plan.md only — rejected: plans are task-scoped; ADR is project-scoped.
    3. Skip rationale capture — rejected: future readers can't reconstruct why.
  - **Trade-offs:** Gain — durable architectural memory. Sacrifice — overhead of an ADR convention; mitigated by scoping this plan to ship only INDEX.md, TEMPLATE.md, and ADR-0001 (future ADRs are opt-in, out of scope of this plan).

- **Decision AD-008 (D8):** Single coordinated minor bump v0.4.0 → v0.5.0.
  - **Rationale:** Matches existing CHANGELOG style. One tag. One CI run. Bump is additive (Planning Standard 11 → 12 is additive, not breaking).
  - **Alternatives Considered:**
    1. Multiple patch bumps per milestone (0.4.1, 0.4.2, …, 0.5.0) — rejected: tag noise + CI cost.
    2. Major bump 1.0.0 — rejected: behavior is additive, not breaking.
  - **Trade-offs:** Gain — single coordinated release. Sacrifice — all milestones must complete before tag; mitigated by HARD gate on M0 + M3 + M4.

**Research Findings (Phase 3):**

- Existing surface area mapped: KISS/DRY/SOLID/SOC and TDD already mentioned in `claude-code/commands/aa-ma-plan.md:30,116,756-761` and `claude-code/skills/operational-constraints/SKILL.md` — but as one-line mentions, not enforced gates.
- `claude-code/skills/plan-verification/SKILL.md` provides 6 angles with Phase 4.5 BLOCKING; Angle 6 is "specialist domain audit" (extension target for engineering-standards-applied detection).
- `claude-code/hooks/aa-ma-commit-drift.sh` is post-commit **ADVISORY** (always exits 0; warns only) — complements rather than competes with milestone HARD gate. *(Originally documented as BLOCKING; corrected via verification finding C1.)*
- Sub-step sync rule (L-080, L-081, L-082) lives at `claude-code/rules/aa-ma.md` lines 47-66 and already mandates "zero PENDING within milestone"; new milestone HARD gate extends with "git status clean" precondition.
- HARD/SOFT gate format reference: `claude-code/rules/aa-ma.md` lines 153-178 — reuse format verbatim for engineering-standards milestone gates.
- Tier 6 hardcoded-count drift detector exists at `~/.claude/rules/doc-drift-checks.md` — used in M3.7 to catch stale "11" references after the bump.
- `docs/adr/` does not yet exist — this plan introduces the convention; future ADRs are opt-in.
- `examples/` directory contains completed task artifacts; M2.7 (adding `Prototype-Required:`/`Critical-Path:` fields to tasks-template.md) requires checking that examples don't break.

**Remaining Questions / Unresolved Issues:**

- **Angle 6 extension vs new Angle 7:** is it cleaner to extend `plan-verification` Angle 6 to detect missing element #12, or to add a new Angle 7? Resolution path: M2.2 prototype both approaches in scratch branch and pick one; record outcome in this log as a new AD-NNN entry and in provenance.log as `[ts] PROTOTYPE — <verdict>`. Resolution must complete before M2.2 is marked COMPLETE. **Hard split criterion** (added by eng-review finding 1.3): if Angle 6 amendment exceeds 30 lines OR introduces a 7th distinct domain on top of existing 5, MUST split into Angle 6a/6b sub-domains.
- **`docs/lessons.md` presence in this repo:** the Phase 1 lessons-scan design assumes the file may or may not exist. As of plan authoring, no `docs/lessons.md` exists at the aa-ma-forge repo root. Resolution path: M2.3 implementation handles both cases (file present → read it; file absent → skip silently). No blocker. M2.3 also implements `--skip-lessons` opt-out flag (eng-review finding 1.4).

---

## [2026-05-09] Plan-Eng-Review Complete (gstack `/plan-eng-review`)

**Trigger:** User invoked `/plan-eng-review /home/sjnewhouse/.claude/plans/engineering-standards-for-eventual-toast.md` after AA-MA artifact creation in M0.

**Step 0 — Scope Challenge:**
- Complexity check TRIPS — 16+ files modified across M1–M4. Breakdown: 8 mechanical Planning Standard count-bump touchpoints (D3 driven), 6 doctrine + integration files, 2 top-level docs (README, CHANGELOG).
- Verdict: complexity is **structural to D3** (already grilled), not avoidable. Mitigated by M3 HARD gate, doc-drift Tier 6 detector, single coordinated v0.5.0 release.
- **PROCEED** — no scope reduction.

**Findings (5 architecture + 1 code-quality + 1 critical test gap):**

| ID | Finding | Confidence | Disposition |
|----|---------|------------|-------------|
| 1.1 | Sequencing risk: M2 references rule file before M1 ships — needs explicit `addBlockedBy: M1` | 9/10 | Applied via M2 dependencies (already implicit; reinforced via M0.6 cross-ref check) |
| 1.2 | ADR INDEX has no validator — future ADRs may silently drift | 8/10 | Applied as new sub-step **2.8** (validator script + integration into pre-commit-full or advisory-only with TODO) |
| 1.3 | Angle 6 risks becoming kitchen sink (5 existing domains + engineering-standards) | 7/10 | Applied as M2.2 split criterion (>30 lines or 7th domain → split into Angle 6a/6b) |
| 1.4 | Phase 1 lessons-scan latency unmeasured; no `--skip-lessons` opt-out | 6/10 | Applied to M2.3 acceptance criteria (`--skip-lessons` flag required) |
| 1.5 | `Critical-Path:` flag taxonomy is ad-hoc (no defined enum) | 8/10 | Applied to M1.1 (define enum in rule file Theme 1: `auth-flow`, `data-xform`, `external-api`, `version-pipeline`, `doc-count-drift`, `hook-modification`); also added to reference.md |
| 2.1 | Skill amendment line cap mentioned for `operational-constraints` only — also applies to `plan-verification` | 7/10 | Applied to M2 milestone acceptance criteria |
| test | No automated E2E smoke harness — coverage diagram showed 12 gaps including 7 [→E2E] paths | n/a | Applied as new sub-step **4.7** (smoke harness OR documented manual checklist + TODO) |

**User disposition:** APPLY ALL findings to plan now (boil-the-lake completeness mode).

**Architectural decision implications:**
- No re-litigation of D1–D8; findings are implementation refinements, not architectural pivots.
- Scope expands by 2 sub-steps (2.8, 4.7) and 5 acceptance criteria additions.
- Estimated incremental effort: ~30 min M2 (validator + line cap verification), ~60–90 min M4.7 (smoke harness if implemented; ~15 min if shipped as manual checklist + TODO).

**Outside voice:** SKIPPED — proceeding to plan-ceo-review (Sub-step 0.3b) instead.

---

## [2026-05-09] Plan-CEO-Review Complete (gstack `/plan-ceo-review` HOLD SCOPE)

**Trigger:** User invoked `/plan-ceo-review /home/sjnewhouse/.claude/plans/engineering-standards-for-eventual-toast.md HOLD SCOPE` to stress-test the plan with strategic CEO lens after eng review.

**Mode:** HOLD SCOPE — no scope expansion; rigor sweep on accepted scope.

**Step 0 — Premise & Existing Code Leverage:**
- **Premise question (CEO-1)**: Is aa-ma-forge a personal-use plugin (where the user's global `~/.claude/CLAUDE.md` already provides these standards) or a distribution plugin (where consumers don't have the user's config)?
- User confirmed: **distribution plugin**. The plan's premise holds — engineering standards must ship in the plugin itself, not depend on the user's private global config.

**Findings (8 — 4 P1 + 2 P2 + 2 P3):**

| ID | Severity | Finding | Disposition |
|----|----------|---------|-------------|
| CEO-1 | P2 | Premise: distribution plugin — auto-loaded rule affects all consumers | Resolved (premise confirmed); applied as M4.9 opt-out documentation in rule file + reference.md distribution-plugin fact |
| CEO-2 | P1 | v0.5.0 is **soft-breaking** for downstream consumers; not pure additive | Applied: M4.4 acceptance criterion adds CHANGELOG `### Behavior change (soft-breaking)` subsection with opt-out paths |
| CEO-3 | P1 | Phase 1 lessons-scan needs **hard timeout**, not soft 30s budget — risk of hang | Applied: M2.3 acceptance criterion specifies `timeout 30s ...` with notice-and-continue fallback; reference.md updated |
| CEO-4 | P2 | Plans authored before v0.5.0 (without element #12) need explicit grandfathering | Applied: M3 acceptance criterion + reference.md grandfathering fact; Angle 6 only flags missing #12 for v0.5.0+ plans |
| CEO-5 | P1 | **Silent compliance** — no observability for whether engineering-standards is actually applied | Applied: M2.3 acceptance criterion adds `[ts] ENG_STANDARDS_DECLARED: themes=[...]` provenance entry on every Phase 2 declaration |
| CEO-6 | P1 | **No rollback procedure** for v0.5.0 release | Applied: new sub-step M4.8 (author `docs/runbooks/rollback-v0.5.0.md`) + M4.4 CHANGELOG `### Rollback` subsection |
| CEO-7 | P3 | Numbered Planning Standard is one-way door; named sections more extensible | Captured as v0.6.0 TODO (see Remaining Questions below) |
| CEO-8 | P3 | Add post-install manual smoke test | Applied: M4 milestone acceptance criterion documents manual smoke checklist |

**User disposition:** APPLY ALL 8 findings (distribution-plugin context confirmed via CEO-1 resolution).

**Architectural decision implications:**
- **No re-litigation of D1–D8** — CEO findings are rigor refinements + premise confirmation, not architectural pivots.
- v0.5.0 release classification clarifies: **soft-breaking** (additive doctrine, but auto-loaded, observable behavior change). Documented in CHANGELOG subsection.
- Observability gap closed via simple provenance log entry (CEO-5) — no new infrastructure.
- Rollback procedure (CEO-6) is now an explicit deliverable, not implicit.
- Scope grew by 2 new sub-steps (M4.8 rollback runbook, M4.9 opt-out doc in rule) and 4–5 new acceptance criteria.

**Estimated incremental effort over eng review:** ~30 min M2.3 (provenance entry + timeout), ~20 min M4.4 (CHANGELOG subsections), ~20 min M4.8 (rollback runbook), ~15 min M4.9 (opt-out doc in rule file). Total: ~85 min on top of eng-review additions.

**Outside voice:** SKIPPED — proceeding to AA-MA validator (Sub-step 0.4) and plan-verification (Sub-step 0.5).

---

## [2026-05-09] Deferred items (v0.6.0 candidates)

Captured for follow-up release after v0.5.0 ships:

- **CEO-7 (TODO):** Move Planning Standard from numbered list (1–12) to named sections. Numbered counts create one-way door — every future addition (e.g., element #13 "Observability Declaration") triggers ~6+ file count drift. Named sections (e.g., `## Engineering Standards Declaration`) are extensible without count drift. Estimated effort: ~2 hours human / ~20 min CC. Risk: would require re-grilling D3 (since the structure changes); breaking change for tooling that parses numbered elements.
- **Eng-review-1.2 (deferred):** ADR INDEX validator could be promoted from advisory to pre-commit hook. M2.8 acceptance allows advisory-only as acceptable. v0.6.0 could harden.
- **Eng-review-test (deferred if M4.7 ships manual checklist):** Full automated E2E smoke harness. M4.7 acceptance allows manual checklist + TODO if effort exceeds 1 hour.

These items are **not blockers for v0.5.0**. They are post-release improvements.

---

## [2026-05-09] Plan-Verification Complete (AA-MA `plan-verification` skill, 6-angle adversarial)

**Trigger:** Sub-step 0.5 of M0. AA-MA's adversarial verification (different from gstack's plan-eng-review).

**Mode:** Automated. Wave 1 (Angles 1–4) ran in parallel. Wave 2 (Angles 5+6) skipped with documented justification.

**Findings: 5 CRITICAL + 12 WARNING + 8 INFO. All 5 CRITICALs and 8+ WARNINGs applied via plan revision in same cycle.**

| ID | Angle | Severity | Finding | Disposition |
|----|-------|----------|---------|-------------|
| C1 | 1 (Ground-Truth) | CRITICAL | `aa-ma-commit-drift.sh` mislabeled BLOCKING; actually ADVISORY (always exits 0) | Applied: reference.md + AD-006 + Phase 3 research findings corrected |
| A3 | 2 (Assumptions) | CRITICAL | Phase 4.5 supports user-selectable Skip mode; M0.5 acceptance allowed Skip | Applied: M0.5 acceptance criteria specifies `mode != Skip` + "all 6 angles ran or justified-skip" |
| A4 | 2 | CRITICAL | (DUPLICATE of C1) | Resolved by C1 fix |
| A10/I1 | 2 | CRITICAL | M3 file list undercounts stale "11" references — missing aa-ma-validator.md, PHASE_4/5 references, aa-ma-plan.md:462 | Applied: M3 acceptance + M3.5 widened to recursive scope under skills/aa-ma-plan-workflow/ + agents/aa-ma-validator.md added |
| C-install | 3 (Impact) | CRITICAL | scripts/install.sh hardcodes aa-ma.md symlink; new rule needs explicit addition | Applied: M4.3 acceptance now requires install.sh modification |
| C-version | 3 | CRITICAL | VERSION file at root contains `__version__="0.4.0"`; M4.5 didn't verify | Applied: M4.5 acceptance adds `grep '"0.5.0"' VERSION` assertion |
| C-PHASE | 3 | CRITICAL | PHASE_4_PLAN_GENERATION.md / PHASE_5_ARTIFACT_CREATION.md have 4 stale "11" references | Applied: M3.5 acceptance widened to recursive scope |
| - | 3 | WARNING | semantic-release tag-format collision risk | Applied: M4.6 pre-flight check |
| - | 3 | WARNING | aa-ma-plan.md:462, plan-template.md:6, foundations.md:75/126, README.md:88/97 — stale "11" lines | Applied: each line explicitly enumerated in M3 acceptance |
| - | 3 | WARNING | docs/narrative/how-we-got-here.md:65 has "11 mandatory outputs" | Applied: M3.7 allowlist (frozen historical doc) |
| - | 3 | WARNING | examples/ tasks may not have new optional fields → M2.5 absent-field semantic | Applied: M2.5 acceptance clarifies absent fields skip check |
| F1 | 4 (Falsifiability) | WARNING | M1 acceptance "≤ ~120 lines" hedges with tilde | Applied: tilde dropped + assertion command |
| F2 | 4 | WARNING | M2 "≤ 20 lines" baseline ambiguous | Documented but soft-applied (reviewer-discretion at M2.1) |
| F3 | 4 | WARNING | 0.2 "follow templates" semantic; 0.3 "captures D1-D8" vague; 2.7 "validate without modification" unspecified | Applied: validator-based assertions in verification.md |
| - | 5 (Fresh-Agent) | SKIPPED | Plan extensively reviewed (grilling + eng + ceo + validator); fresh-agent re-run would duplicate signal | Justified-skip documented in verification.md |
| - | 6 (Specialist) | SKIPPED | No Pydantic/API/migration/security domain keywords | Justified-skip documented |
| F4 | various | INFO (8) | Minor wording polish, drop "appropriate", deferred to v0.6.0 | Captured in deferred-items section |

**Result:** PASS WITH WARNINGS. Plan execution-ready. See `aa-ma-engineering-standards-verification.md` for full report.

**M0 progress after verification:** 0.1✓, 0.2✓, 0.3✓, 0.3a✓, 0.3b✓, 0.3c✓, 0.4✓, 0.5✓ → next: 0.6 cross-ref grep, 0.7 commit + push.

---

## [2026-05-09T16:15:44Z] Compaction Summary (auto-generated by hook)
- Active step at compaction: Sub-step 0.5: Run `plan-verification` skill → produces verification.md
- Snapshot saved to: /home/sjnewhouse/.claude/hooks/cache/compaction-snapshots/aa-ma-engineering-standards-snapshot.md
- Note: Context compacted. Reload AA-MA files to resume.
