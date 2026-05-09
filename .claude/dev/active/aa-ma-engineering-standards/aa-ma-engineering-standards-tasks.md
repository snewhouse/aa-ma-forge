# aa-ma-engineering-standards Tasks (HTP)

_Hierarchical Task Planning roadmap with dependencies and state tracking._

## Milestone 0: AA-MA Workflow Setup + ADR + Plan-Verification

- Status: COMPLETE (2026-05-09 ~16:10 UTC, commit 598b4b3)
- **Dependencies:** None
- **Complexity:** 35%
- **Gate:** HARD
- **Mode:** AFK
- **Critical-Path:**
- **Prototype-Required:**
- **Acceptance Criteria:**
  - All 5 standard AA-MA artifacts exist at `.claude/dev/active/aa-ma-engineering-standards/` and pass `aa-ma-validator` read-only check.
  - `docs/adr/INDEX.md`, `docs/adr/TEMPLATE.md`, and `docs/adr/0001-engineering-standards-architecture.md` exist; INDEX.md lists ADR-0001.
  - `aa-ma-engineering-standards-verification.md` exists with no CRITICAL findings.
  - `grep -r "engineering-standards" claude-code/ docs/ .claude/dev/active/aa-ma-engineering-standards/` reports no broken cross-references.
  - M0 deliverables committed with `[AA-MA Plan] aa-ma-engineering-standards .claude/dev/active/aa-ma-engineering-standards` footer and pushed to `feature/aa-ma-engineering-standards_001`.

### Sub-step 0.1: Create task directory + `docs/adr/` directory scaffold
- Status: COMPLETE
- **Mode:** AFK
- **Dependencies:** None
- **Acceptance Criteria:**
  - `.claude/dev/active/aa-ma-engineering-standards/` exists.
  - `docs/adr/` exists.
- **Result Log:** Both directories created prior to scribe dispatch (per task prompt: target directory "already created").

### Sub-step 0.2: Write the 5 standard AA-MA artifacts
- Status: COMPLETE
- **Mode:** AFK
- **Dependencies:** Step 0.1
- **Acceptance Criteria:**
  - Five files present: `-plan.md`, `-reference.md`, `-context-log.md`, `-tasks.md`, `-provenance.log`.
  - Files follow templates in `docs/templates/`.
  - No `[TODO]` / `[fill in]` placeholder text remains.
- **Result Log:** aa-ma-scribe agent completed 2026-05-09 ~15:00 UTC. Files written: plan.md (470 lines), reference.md (177 lines), context-log.md (99 lines), tasks.md (370 lines), provenance.log (11 lines). Element #12 dogfooded in plan.md per scribe note. No placeholder text. Total: 1127 lines across 5 artifacts. Agent ID: aa78673669071d39b.

### Sub-step 0.3: Author ADR set (INDEX.md, TEMPLATE.md, 0001-engineering-standards-architecture.md)
- Status: COMPLETE
- **Mode:** AFK
- **Dependencies:** Step 0.1
- **Acceptance Criteria:**
  - ADR-0001 captures D1–D8 in MADR sections (Title / Status / Context / Decision / Consequences).
  - INDEX.md lists ADR-0001 with Status `Accepted`.
- **Result Log:** Authored in parallel with scribe. INDEX.md (31 lines), TEMPLATE.md (66 lines), 0001-engineering-standards-architecture.md (151 lines). MADR format applied. INDEX.md cross-references resolve (TEMPLATE.md ✓, 0001-...md ✓, MADR external link ✓). ADR-0001 captures all 8 sub-decisions D1–D8 with rationale, considered options, and consequences.

### Sub-step 0.3a: Run `/plan-eng-review` on the plan
- Status: COMPLETE
- **Mode:** AFK
- **Dependencies:** Steps 0.2, 0.3
- **Acceptance Criteria:**
  - gstack `plan-eng-review` skill executed against `~/.claude/plans/engineering-standards-for-eventual-toast.md`.
  - All review sections complete: Step 0 scope challenge, Architecture, Code Quality, Test Review, Performance.
  - Findings disposition decided by user.
- **Result Log:** Eng review run 2026-05-09 ~15:10 UTC. 5 architecture findings + 1 code-quality + 1 critical test gap. User disposition: APPLY ALL findings to plan now (boil-the-lake). Findings: (1.1) M2 sequencing addBlockedBy M1, (1.2) ADR INDEX validator, (1.3) Angle 6 split criterion, (1.4) `--skip-lessons` flag, (1.5) Critical-Path enum, (2.1) line cap on plan-verification SKILL.md amendment, (test) automated E2E smoke harness. All applied via Sub-step 0.3c.

### Sub-step 0.3b: Run `/plan-ceo-review` on the plan (HOLD SCOPE mode)
- Status: COMPLETE
- **Mode:** HITL
- **Dependencies:** Step 0.3a
- **Acceptance Criteria:**
  - gstack `plan-ceo-review` skill executed in HOLD SCOPE mode (don't expand, just stress-test).
  - Findings logged in context-log.md.
  - User dispositions any expansion proposals.
- **Result Log:** CEO review run 2026-05-09 ~15:30 UTC in HOLD SCOPE mode (no scope expansion). 8 findings: CEO-1 (premise: distribution plugin), CEO-2 (soft-breaking CHANGELOG), CEO-3 (lessons-scan hard timeout), CEO-4 (grandfathering pre-v0.5.0 plans), CEO-5 (observability silence — provenance entry), CEO-6 (rollback runbook), CEO-7 (numbered standard one-way door — TODO v0.6.0), CEO-8 (post-install smoke). User disposition: APPLY ALL 8 (distribution-plugin context confirmed). Findings applied via Sub-step 0.3c.

### Sub-step 0.3c: Apply review findings to AA-MA artifacts
- Status: COMPLETE
- **Mode:** AFK
- **Dependencies:** Steps 0.3a, 0.3b
- **Acceptance Criteria:**
  - All accepted eng-review findings reflected in tasks.md (new sub-steps, new acceptance criteria, dependencies).
  - All accepted ceo-review findings reflected (if any).
  - reference.md updated with Critical-Path enum.
  - context-log.md captures the review event + decisions.
  - provenance.log records review events.
- **Result Log:** Findings applied 2026-05-09 ~15:35 UTC. Eng review (7 findings): tasks.md M1.1 +Critical-Path enum, M2 +line cap on plan-verification, M2.2 +split criterion, M2.3 +`--skip-lessons` flag, new sub-steps 2.8 (ADR INDEX validator) + 4.7 (E2E smoke harness); reference.md +Critical-Path enum table; context-log.md +eng-review section. CEO review (8 findings): tasks.md M2.3 +CEO-3 hard timeout +CEO-5 observability provenance entry, M3 +CEO-4 grandfathering, M4 +CEO-8 post-install smoke +CEO-6 rollback reference, M4.4 +CEO-2 soft-breaking subsection +CEO-6 rollback subsection, new sub-steps 4.8 (rollback runbook) + 4.9 (opt-out documentation); reference.md +distribution-plugin fact (CEO-1); context-log.md +ceo-review section; CEO-7 captured as v0.6.0 TODO. Total 15 findings applied (7 eng + 8 ceo). 2 new sub-steps from eng (2.8, 4.7) + 2 new sub-steps from ceo (4.8, 4.9) = 4 new total in M2/M4. M0 milestone progresses to validator + plan-verification + cross-ref + commit.

### Sub-step 0.4: Run `aa-ma-validator` agent (read-only)
- Status: COMPLETE
- **Mode:** AFK
- **Dependencies:** Steps 0.2, 0.3
- **Acceptance Criteria:**
  - Validator reports no missing-required-fields and no template-violation errors.
- **Result Log:** Validator agent abb0f9b46d4aa56fc completed 2026-05-09 ~15:40 UTC. **25/25 checks PASS, 0 FAIL, 0 WARN.** Verified: 5 standard files exist with correct names; templates followed; no unfilled placeholders; cross-file consistency (M0–M4 alignment plan↔tasks; sub-step IDs unique, no broken refs; D1–D8 traceable across context-log AD-001–AD-008 and reference.md Locked decisions table); all milestones have Gate/Mode/AC; all 26 sub-steps have Status/Mode/Dependencies/AC/Result Log; element #12 dogfooded at plan.md L450-463; eng-review markers present (M1.1, M2 AC, M2.2, M2.3, M2.8); CEO-review markers present (M2.3, M3 AC, M4 AC, M4.4, M4.8); provenance log format compliant (23 events). Status: ARTIFACTS READY for plan-verification skill (Sub-step 0.5).

### Sub-step 0.5: Run `plan-verification` skill → produces verification.md
- Status: COMPLETE
- **Mode:** AFK
- **Dependencies:** Steps 0.2, 0.3
- **Acceptance Criteria:**
  - `aa-ma-engineering-standards-verification.md` exists.
  - **(verification finding A3)** Verification ran in `mode=Automated` OR `mode=Interactive` (NOT `mode=Skip`); verification.md "Mode:" field reflects this.
  - **(verification finding A3)** All 6 angles either ran or were explicitly justified-as-skipped in verification.md (Wave 1 Angles 1–4 minimum; Wave 2 may skip with justification).
  - Zero CRITICAL findings remain after revision (CRITICAL findings caught during verification MUST be applied to plan via revision; final state shows "all addressed").
  - Any WARNING/INFO findings logged in context-log.md or verification.md.
- **Result Log:** Verification ran 2026-05-09 ~15:50 UTC, mode=Automated. Wave 1 dispatched 4 parallel agents (Angles 1-4). Wave 2 (Angles 5+6) skipped with documented justification (extensive prior reviews + no domain keywords). Findings: **5 CRITICAL** (C1 BLOCKING/ADVISORY mismatch — duplicated by Angle 2 A4; A3 plan-verification Skip mode; A10/I1 M3 file undercount; C-install scripts/install.sh not in modify list; C-version VERSION file not in M4.5; C-PHASE references/ files missed). **12 WARNING** (mostly file-list expansions + 6 falsifiability rewrites). **8 INFO** (deferred to v0.6.0). **All 5 CRITICALs and 8+ WARNINGs applied via plan revision in same cycle.** Final verdict: **PASS WITH WARNINGS**. Artifacts execution-ready. See `aa-ma-engineering-standards-verification.md` for full report.

### Sub-step 0.6: Cross-reference grep validation
- Status: COMPLETE
- **Mode:** AFK
- **Dependencies:** Steps 0.2, 0.3
- **Acceptance Criteria:**
  - `grep -r "engineering-standards" claude-code/ docs/` produces no references to nonexistent files.
- **Result Log:** Cross-ref validation 2026-05-09 ~16:05 UTC. All `engineering-standards` references in `claude-code/`, `docs/`, and AA-MA artifact directory resolve to real files OR to forward-looking "Files to Create" entries (correctly noted in reference.md). All 6 AA-MA artifacts present (5 standard + verification.md). ADR set complete (INDEX.md, TEMPLATE.md, 0001-...md). Currently 15 stale "11 element" references exist on disk — these are KNOWN M3 scope, enumerated in M3 acceptance criteria after verification revisions, NOT M0 blockers. Verdict: PASS.

### Sub-step 0.7: Commit + push M0 deliverables
- Status: COMPLETE
- **Mode:** AFK
- **Dependencies:** Steps 0.4, 0.5, 0.6
- **Acceptance Criteria:**
  - Single commit (or atomic series) on `feature/aa-ma-engineering-standards_001` with footer `[AA-MA Plan] aa-ma-engineering-standards .claude/dev/active/aa-ma-engineering-standards`.
  - Pushed to remote.
- **Result Log:** Commit `598b4b3` `chore(aa-ma): set up workflow + ADR convention for engineering-standards plan (M0)` 2026-05-09 ~16:10 UTC. 9 files / 1816 insertions: 6 AA-MA artifacts in `.claude/dev/active/aa-ma-engineering-standards/` + 3 ADR files in `docs/adr/`. AA-MA Plan footer present (last line). Pushed to `origin/feature/aa-ma-engineering-standards_001` (new branch on remote). PR creation URL: https://github.com/snewhouse/aa-ma-forge/pull/new/feature/aa-ma-engineering-standards_001 (deferred — M0 is setup; PR opens after M4 release).

---

## Milestone 1: Doctrine

- Status: COMPLETE (2026-05-09 ~16:35 UTC, commit 1313598)
- **Dependencies:** Milestone 0
- **Complexity:** 25%
- **Gate:** SOFT
- **Mode:** AFK
- **Critical-Path:**
- **Prototype-Required:**
- **Acceptance Criteria:**
  - `claude-code/rules/engineering-standards.md` exists with sections `### 1.` through `### 6.`; `grep -E "^### [1-6]\." claude-code/rules/engineering-standards.md | wc -l` returns 6. **VERIFIED: 6.**
  - File length ≤ 120 lines (principles, not procedures). **(verification finding — falsifiability)** Tilde dropped; assertion: `[ "$(wc -l < claude-code/rules/engineering-standards.md)" -le 120 ]` returns 0. **VERIFIED: 118 lines.**
  - `docs/adr/0001-engineering-standards-architecture.md` Status updated from `Accepted` to `Implemented` with timestamp. **VERIFIED: line 3 reads "Implemented (2026-05-09)".**

### Sub-step 1.1: Write `claude-code/rules/engineering-standards.md`
- Status: COMPLETE
- **Mode:** AFK
- **Dependencies:** Milestone 0
- **Acceptance Criteria:**
  - Six themed sections present.
  - File length ≤ 120 lines.
  - Cross-references (`first-principles-framework`, `operational-constraints`, `impact-analysis`, `aa-ma-commit-drift.sh`) resolve on disk.
  - **(eng-review finding 1.5)** Theme 1 defines `Critical-Path:` enum with 5–8 canonical values (e.g. `auth-flow`, `data-xform`, `external-api`, `version-pipeline`, `doc-count-drift`, `hook-modification`). Reject novel values via plan-verification or document escape hatch.
- **Result Log:** Wrote `claude-code/rules/engineering-standards.md` 2026-05-09 ~16:30 UTC. **118 lines** (cap: ≤120). Six themed sections present (`### 1.` Verification & Truth → `### 6.` Sync & Commit Discipline; grep returns 6). Theme 1 defines Critical-Path enum table with all 6 canonical values (`auth-flow`, `data-xform`, `external-api`, `version-pipeline`, `doc-count-drift`, `hook-modification`). Theme 5 includes 9-row Execution Checklist (6 HARD + 3 SOFT) with `Critical-Path:`/`Prototype-Required:` absent-field semantic note. Cross-refs verified resolvable: `claude-code/rules/aa-ma.md`, `claude-code/skills/operational-constraints/`, `claude-code/skills/plan-verification/`, `claude-code/skills/impact-analysis/`, `claude-code/hooks/aa-ma-commit-drift.sh`, `docs/adr/0001-engineering-standards-architecture.md` (all OK). `first-principles-framework` referenced as `Skill(first-principles-framework)` — user-global skill, not shipped by this plugin (described inline as principle, no broken cross-ref). Note: M4.9 amends this file with `## Opt-out` section in Milestone 4 — kept out of M1.1 to maintain milestone atomicity.

### Sub-step 1.2: Update ADR-0001 Status: Accepted → Implemented
- Status: COMPLETE
- **Mode:** AFK
- **Dependencies:** Step 1.1
- **Acceptance Criteria:**
  - ADR-0001 Status field reads `Implemented (YYYY-MM-DD)`.
  - INDEX.md mirrors the change.
- **Result Log:** ADR-0001 Status flipped 2026-05-09 ~16:33 UTC. `docs/adr/0001-engineering-standards-architecture.md` line 3: `**Status:** Accepted` → `**Status:** Implemented (2026-05-09)`. `docs/adr/INDEX.md` row updated: `Accepted` → `Implemented`. Both edits use single-line in-place replacement; no other text disturbed. Cross-reference parity: INDEX.md status column matches ADR file Status field.

---

## Milestone 2: Workflow integration

- Status: PENDING
- **Dependencies:** Milestone 1
- **Complexity:** 55%
- **Gate:** SOFT
- **Mode:** AFK
- **Critical-Path:**
- **Prototype-Required:** (Step 2.2 only)
- **Acceptance Criteria:**
  - `operational-constraints/SKILL.md` references `engineering-standards.md`; grew by ≤ 20 lines.
  - **(eng-review finding 2.1)** `plan-verification/SKILL.md` amendment also capped at ≤ 20 lines (or split into Angle 6a/6b if larger — see step 2.2).
  - `plan-verification/SKILL.md` flags a plan with no element #12 (via Angle 6 extension or new Angle 7 — decision recorded in context-log).
  - `aa-ma-plan.md` Phase 1 includes "Lessons Scan" subsection; Phase 2 prompts for declaration; Phase 4 emits element #12.
  - `execute-aa-ma-step.md` includes per-step advisory checklist (7 items from Theme 5).
  - `execute-aa-ma-milestone.md` includes milestone HARD gate (5 conditions: clean git, zero PENDING, tests-pass evidence, impact-analysis run, provenance evidence for `Critical-Path:`/`Prototype-Required:`).
  - `docs/templates/engineering-standards-template.md` exists.
  - `docs/templates/tasks-template.md` includes `Prototype-Required:` and `Critical-Path:` fields.
  - **(eng-review finding 1.2)** `docs/adr/` has a validator (pre-commit hook OR doc-drift Tier 5 implementation) that flags ADRs missing from INDEX.md.

### Sub-step 2.1: Amend `operational-constraints/SKILL.md`
- Status: PENDING
- **Mode:** AFK
- **Dependencies:** Milestone 1
- **Acceptance Criteria:**
  - References `engineering-standards.md`.
  - Diff ≤ +20 lines.
  - No doctrine duplication.
- **Result Log:**

### Sub-step 2.2: Prototype Angle 6 extension vs Angle 7 addition; pick one
- Status: PENDING
- **Mode:** HITL
- **Prototype-Required:** YES
- **Dependencies:** Milestone 1
- **Acceptance Criteria:**
  - `plan-verification` skill flags a plan missing element #12.
  - Decision documented in context-log.md as a new AD-NNN entry.
  - provenance.log carries `[ts] PROTOTYPE — <verdict>`.
  - **(eng-review finding 1.3)** Hard split criterion: if Angle 6 amendment exceeds 30 lines OR introduces a 7th distinct domain on top of existing 5 (Pydantic, API contracts, schema, migrations, OWASP), MUST split into Angle 6a/6b sub-domains rather than collapse all engineering checks into Angle 6.
- **Result Log:**

### Sub-step 2.3: Amend `aa-ma-plan.md` (Phases 1, 2, 4)
- Status: PENDING
- **Mode:** AFK
- **Dependencies:** Step 2.1
- **Acceptance Criteria:**
  - Phase 1 includes "Lessons Scan" with 30s budget cap.
  - **(eng-review finding 1.4)** Phase 1 supports `--skip-lessons` opt-out flag for fast iteration / CI / smoke tests; flag suppresses scan and emits a notice in plan output.
  - **(ceo-review finding CEO-3)** Phase 1 lessons scan uses hard timeout (`timeout 30s ...` or equivalent), not a soft budget. On timeout, emit notice and continue without scan results — never hang.
  - Phase 2 prompts for "Engineering Standards Declaration".
  - **(ceo-review finding CEO-5 — observability)** Phase 2 emits a `[ts] ENG_STANDARDS_DECLARED: themes=[1,2,5]` provenance log entry on every `/aa-ma-plan` invocation that produces a declaration. Provides per-plan audit trail; eliminates silent-compliance failure mode.
  - Phase 4 emits element #12 in plan output.
- **Result Log:**

### Sub-step 2.4: Amend `execute-aa-ma-step.md` (per-step advisory checklist)
- Status: PENDING
- **Mode:** AFK
- **Dependencies:** Step 2.3
- **Acceptance Criteria:**
  - Prompt contract includes the 7-item advisory checklist.
  - SOFT items request declaration in context-log; HARD items defer enforcement to milestone gate.
- **Result Log:**

### Sub-step 2.5: Amend `execute-aa-ma-milestone.md` (milestone HARD gate)
- Status: PENDING
- **Mode:** AFK
- **Dependencies:** Step 2.4
- **Acceptance Criteria:**
  - Command refuses to mark COMPLETE when (a) git is dirty, (b) any `Status: PENDING` remains in the milestone, (c) tests-pass evidence missing, (d) impact-analysis not run, or (e) `Critical-Path:`/`Prototype-Required:` tasks lack provenance entries.
  - **(verification finding M2.5 absent-field semantic)** Condition (e) explicitly skips the check (NO failure) when `Critical-Path:`/`Prototype-Required:` fields are absent on the task. Only fires when fields are present-but-without-evidence. Preserves backward compat with existing `examples/` plans.
- **Result Log:**

### Sub-step 2.6: Add `docs/templates/engineering-standards-template.md`
- Status: PENDING
- **Mode:** AFK
- **Dependencies:** Milestone 1
- **Acceptance Criteria:**
  - Template provides optional per-task artifact format (one section per theme).
- **Result Log:**

### Sub-step 2.7: Add `Prototype-Required:` and `Critical-Path:` fields to tasks-template.md
- Status: PENDING
- **Mode:** AFK
- **Dependencies:** None (within Milestone 2)
- **Acceptance Criteria:**
  - Both fields documented as optional.
  - Existing `examples/` continue to validate without modification.
- **Result Log:**

### Sub-step 2.8: ADR INDEX validator (eng-review finding 1.2)
- Status: PENDING
- **Mode:** AFK
- **Dependencies:** Step 2.6
- **Acceptance Criteria:**
  - Validator script at `scripts/check_adr_index.sh` (or extension to existing `~/.claude/rules/doc-drift-checks.md` Tier 5 implementation in this repo).
  - Script verifies count: `find docs/adr -maxdepth 1 -name "[0-9]*.md" | wc -l` matches the count of pipe-table entries in `docs/adr/INDEX.md`.
  - Script integrated into `/pre-commit-full` workflow OR documented as advisory-only with rationale.
  - Acceptable outcome (per locked decision): advisory-only with explicit TODO if pre-commit integration deferred.
- **Result Log:**

---

## Milestone 3: Planning Standard bump (11 → 12)

- Status: PENDING
- **Dependencies:** Milestone 2
- **Complexity:** 50%
- **Gate:** HARD
- **Mode:** AFK
- **Critical-Path:** doc-count-drift
- **Prototype-Required:**
- **Acceptance Criteria:**
  - `claude-code/rules/aa-ma.md` Planning Standard section lists 12 elements; #12 is "Engineering Standards Declaration".
  - `docs/spec/aa-ma-specification.md` Section XI lists 12 elements with full description of #12.
  - `docs/spec/aa-ma-quick-reference.md` shows 12.
  - `docs/spec/claude-code-foundations.md` shows 12 + lists `engineering-standards.md` in rules list (1 → 2 rules).
  - `claude-code/skills/aa-ma-plan-workflow/SKILL.md` Phase 4 references element #12.
  - `docs/templates/plan-template.md` contains a placeholder for element #12.
  - Tier 6 drift detector returns zero stale "11" references outside CHANGELOG.md AND outside the documented allowlist (`docs/narrative/how-we-got-here.md` is a frozen historical doc per CLAUDE.md line 70 — allowlist).
  - README.md and SECURITY.md show updated counts where applicable.
  - **(ceo-review finding CEO-4 — grandfathering)** Plans authored before v0.5.0 (those without element #12) are explicitly grandfathered: `plan-verification` Angle 6 only flags missing #12 when plan front-matter `Created: YYYY-MM-DD` field is on-or-after v0.5.0 release date. Mechanism: parse `Created:` from plan.md front-matter; if absent or pre-v0.5.0 release, skip element #12 check. Documented in `claude-code/rules/aa-ma.md` and CHANGELOG.
  - **(verification findings A10/I1, C-install, C-version, I3, C-PHASE)** Additional files in M3 scope:
    - `claude-code/agents/aa-ma-validator.md:143` — change `/11` → `/12` (M3.5)
    - `claude-code/skills/aa-ma-plan-workflow/references/PHASE_4_PLAN_GENERATION.md` — 3 stale "11" references (M3.5 widened)
    - `claude-code/skills/aa-ma-plan-workflow/references/PHASE_5_ARTIFACT_CREATION.md` — 1 stale "11" reference (M3.5 widened)
    - `claude-code/commands/aa-ma-plan.md:462` — embedded example template (M3.7 catches via Tier 6 grep)
    - `docs/templates/plan-template.md:6` — comment update (M3.6)
    - `docs/spec/claude-code-foundations.md:75,126` — 2 stale lines (M3.4)
    - `README.md:88,97` — 2 stale references (M3.8)
    - `docs/adr/0001-engineering-standards-architecture.md:10` — self-update (M3.5; ADR self-updates concurrent with the change it described)
    - `VERSION` — bumped via `cz bump` `version_files=["VERSION:__version__"]` (M4.5; explicit verification step)
    - `scripts/install.sh` — add `create_symlink` for `engineering-standards.md` (M4.3; lines 145, 283-284 currently hardcode `aa-ma.md` only)

### Sub-step 3.1: Update `claude-code/rules/aa-ma.md` Planning Standard section
- Status: PENDING
- **Mode:** AFK
- **Dependencies:** Milestone 2
- **Acceptance Criteria:**
  - Section lists 12 elements; #12 is "Engineering Standards Declaration" with one-line description.
  - Canonical phrasing established here.
- **Result Log:**

### Sub-step 3.2: Update `docs/spec/aa-ma-specification.md` Section XI
- Status: PENDING
- **Mode:** AFK
- **Dependencies:** Step 3.1
- **Acceptance Criteria:**
  - Section XI lists 12 elements with full prose description of #12.
  - Canonical phrasing matches Step 3.1.
- **Result Log:**

### Sub-step 3.3: Update `docs/spec/aa-ma-quick-reference.md`
- Status: PENDING
- **Mode:** AFK
- **Dependencies:** Step 3.1
- **Acceptance Criteria:**
  - All "11"-element references updated to "12".
  - New element entry added.
- **Result Log:**

### Sub-step 3.4: Update `docs/spec/claude-code-foundations.md`
- Status: PENDING
- **Mode:** AFK
- **Dependencies:** Step 3.1
- **Acceptance Criteria:**
  - Element count = 12.
  - Rule-file count updated (1 → 2); `engineering-standards.md` listed.
- **Result Log:**

### Sub-step 3.5: Update `aa-ma-plan-workflow/SKILL.md` Phase 4 description + downstream references
- Status: PENDING
- **Mode:** AFK
- **Dependencies:** Step 3.1
- **Acceptance Criteria:**
  - `claude-code/skills/aa-ma-plan-workflow/SKILL.md` Phase 4 references element #12.
  - **(verification finding C-PHASE)** All files under `claude-code/skills/aa-ma-plan-workflow/` (including `references/PHASE_4_PLAN_GENERATION.md`, `references/PHASE_5_ARTIFACT_CREATION.md`) updated for 11 → 12 — verified via `grep -rn "11 elements\|11 outputs\|11 mandatory" claude-code/skills/aa-ma-plan-workflow/` returning zero hits.
  - **(verification finding I3)** `claude-code/agents/aa-ma-validator.md:143` updated: `Score: [N]/11 elements present` → `/12 elements present`.
  - **(verification finding I5)** `docs/adr/0001-engineering-standards-architecture.md:10` self-updated: "11-element Planning Standard" → "12-element Planning Standard" — concurrent with this milestone since the ADR documents the change being made.
  - Matches canonical phrasing established in M3.1.
- **Result Log:**

### Sub-step 3.6: Update `docs/templates/plan-template.md`
- Status: PENDING
- **Mode:** AFK
- **Dependencies:** Step 3.1
- **Acceptance Criteria:**
  - Template includes placeholder for element #12 with bracketed prompt.
- **Result Log:**

### Sub-step 3.7: Run hardcoded-count drift detector (Tier 6)
- Status: PENDING
- **Mode:** AFK
- **Dependencies:** Steps 3.1–3.6
- **Acceptance Criteria:**
  - `grep -rn "11 elements\|11 outputs\|11 mandatory" claude-code/ docs/ README.md SECURITY.md | grep -v CHANGELOG | grep -v "docs/narrative/how-we-got-here.md"` returns zero.
  - **(verification finding I6)** `docs/narrative/how-we-got-here.md` is explicitly allowlisted as a frozen historical doc (per CLAUDE.md "Historical docs are frozen"); its "11 mandatory outputs" reference at line 65 is preserved as historical record.
  - Allowlist documented inline in command output and in `docs/narrative/how-we-got-here.md` itself (note added: "Historical: this doc references the 11-element Planning Standard from prior to v0.5.0; the post-v0.5.0 standard is 12 elements — see ADR-0001").
  - Hits found outside allowlist are fixed before milestone completion.
- **Result Log:**

### Sub-step 3.8: Update README.md and SECURITY.md if they cite element count
- Status: PENDING
- **Mode:** AFK
- **Dependencies:** Step 3.7
- **Acceptance Criteria:**
  - No stale "11" references remain.
  - Counts mirror canonical wording.
- **Result Log:**

---

## Milestone 4: Release

- Status: PENDING
- **Dependencies:** Milestone 3
- **Complexity:** 45%
- **Gate:** HARD
- **Mode:** HITL
- **Critical-Path:** version-pipeline
- **Prototype-Required:**
- **Acceptance Criteria:**
  - `uv run pytest` (default markers) returns exit 0.
  - `bats tests/hooks/` returns exit 0 (or marked SKIP with reason if bats unavailable).
  - `uv run ruff check src/` returns exit 0.
  - `scripts/install.sh --dry-run` lists `claude-code/rules/engineering-standards.md` among new symlinks.
  - `CHANGELOG.md` `[0.5.0]` section exists.
  - `pyproject.toml` version = `0.5.0` (was `0.4.0`).
  - Tag `v0.5.0` exists on the merge commit and is pushed to origin.
  - **(ceo-review finding CEO-8 — post-install smoke)** Manual smoke checklist documented in CHANGELOG and runbook: open a fresh `claude-code` session after install, query "what engineering principles do you apply?", verify all 6 themes from `engineering-standards.md` appear in the response. Low-cost, high-signal verification that the rule file is being loaded.
  - **(ceo-review finding CEO-6 — rollback runbook)** `docs/runbooks/rollback-v0.5.0.md` exists with explicit revert steps (see Sub-step 4.8).

### Sub-step 4.1: Run `uv run pytest` (default suite) and `bats tests/hooks/`
- Status: PENDING
- **Mode:** AFK
- **Dependencies:** Milestone 3
- **Acceptance Criteria:**
  - Both exit 0.
  - Failures fixed in same milestone before proceeding.
- **Result Log:**

### Sub-step 4.2: Run `uv run ruff check src/`
- Status: PENDING
- **Mode:** AFK
- **Dependencies:** Step 4.1
- **Acceptance Criteria:**
  - Exit 0.
- **Result Log:**

### Sub-step 4.3: Modify `scripts/install.sh` + run `--dry-run`; verify new symlinks listed
- Status: PENDING
- **Mode:** AFK
- **Dependencies:** Step 4.2
- **Acceptance Criteria:**
  - **(verification finding C-install — CRITICAL)** `scripts/install.sh` updated: add `create_symlink "${REPO_ROOT}/claude-code/rules/engineering-standards.md" "${CLAUDE_HOME}/rules/engineering-standards.md"` adjacent to existing `aa-ma.md` symlink call (current lines 145, 283-284 hardcode aa-ma.md only). Also add `collect_backup_target` entry if symmetric pattern is used.
  - Output of `scripts/install.sh --dry-run` includes `claude-code/rules/engineering-standards.md`.
  - Output includes `docs/templates/engineering-standards-template.md` (if applicable to install path).
  - `docs/adr/` content present as expected.
- **Result Log:**

### Sub-step 4.4: Update CHANGELOG.md `[0.5.0]` section
- Status: PENDING
- **Mode:** AFK
- **Dependencies:** Step 4.3
- **Acceptance Criteria:**
  - `[0.5.0]` section summarizes 6-theme doctrine, ADR convention, Planning Standard 11 → 12, new templates and fields, milestone HARD gate.
  - Conventional Commits style.
  - **(ceo-review finding CEO-2 — soft-breaking)** `[0.5.0]` includes an explicit `### Behavior change (soft-breaking)` subsection documenting that consumers re-running `install.sh` will receive a new auto-loaded `engineering-standards.md` rule on next session. Subsection lists the opt-out path (`AA_MA_HOOKS_DISABLE=1` master kill switch OR remove the symlink at `~/.claude/rules/engineering-standards.md`).
  - **(ceo-review finding CEO-6 — rollback)** `[0.5.0]` includes a `### Rollback` subsection with explicit steps: `git checkout v0.4.0 -- claude-code/rules/ docs/spec/ docs/adr/ docs/templates/` then `scripts/install.sh` (or `uninstall.sh` for full removal). Documents that pre-v0.5.0 plans remain valid (per CEO-4 grandfathering).
- **Result Log:**

### Sub-step 4.5: Run `cz bump` → version 0.4.0 → 0.5.0
- Status: PENDING
- **Mode:** AFK
- **Dependencies:** Step 4.4
- **Acceptance Criteria:**
  - `pyproject.toml` version becomes `0.5.0`.
  - **(verification finding C-version)** `VERSION` file at repo root reads `__version__ = "0.5.0"` (cz `[tool.commitizen] version_files=["VERSION:__version__"]` should bump it automatically; explicit assertion: `grep -F '"0.5.0"' VERSION` returns 1 hit).
  - Commitizen commit created.
  - CHANGELOG line aligned.
- **Result Log:**

### Sub-step 4.6: Tag and push `v0.5.0`
- Status: PENDING
- **Mode:** HITL
- **Dependencies:** Step 4.5
- **Acceptance Criteria:**
  - **(verification finding — semantic-release collision)** Pre-flight check: `grep -l "semantic_release\|semantic-release" .github/workflows/` does not return any workflow that auto-tags on push to feature branches. If a workflow auto-tags on push to main, document the merge-after-tag sequence (cz creates tag locally → push branch → merge PR → push tag — semantic-release CI does not double-tag if tag already exists).
  - Tag `v0.5.0` exists locally and on origin.
  - `git push origin feature/aa-ma-engineering-standards_001 --tags` succeeds.
  - User confirmed before tag push.
- **Result Log:**

### Sub-step 4.7: Automated E2E smoke harness for `/aa-ma-plan` (eng-review critical test gap)
- Status: PENDING
- **Mode:** AFK
- **Critical-Path:** version-pipeline
- **Dependencies:** Step 4.3
- **Acceptance Criteria:**
  - Bash-driven (or pytest+subprocess) smoke harness at `tests/smoke/test_aa_ma_plan_workflow.sh` (or equivalent) runs `/aa-ma-plan "trivial test feature"` against a temp directory and asserts:
    1. Phase 1 output contains the substring `Lessons Scan` (subsection appears).
    2. Phase 2 output prompts for `Engineering Standards Declaration`.
    3. Phase 4 output contains `12.` (element #12 emitted).
    4. `/execute-aa-ma-milestone` against a milestone with `git status --short` non-empty exits non-zero with a recognizable refusal reason.
    5. `/execute-aa-ma-milestone` against a clean milestone exits 0.
    6. `Critical-Path: auth-flow` task completion produces a `CRITICAL_PATH_REVIEW` line in `provenance.log`.
    7. `Prototype-Required: YES` task completion produces a `PROTOTYPE` line in `provenance.log`.
  - Smoke runs in CI (GitHub Actions `security.yml` or new `smoke.yml`) on PRs touching `claude-code/`.
  - Acceptable outcome (per locked decision): if E2E harness exceeds 1 hour effort, ship a documented manual smoke-test checklist and capture as TODO; do not block v0.5.0 release.
- **Result Log:**

### Sub-step 4.8: Author rollback runbook `docs/runbooks/rollback-v0.5.0.md` (ceo-review finding CEO-6)
- Status: PENDING
- **Mode:** AFK
- **Critical-Path:** version-pipeline
- **Dependencies:** Step 4.4
- **Acceptance Criteria:**
  - File `docs/runbooks/rollback-v0.5.0.md` exists with explicit `## Rollback Procedure` section.
  - Steps documented in order: (1) `git checkout v0.4.0 -- claude-code/rules/ docs/spec/ docs/adr/ docs/templates/`; (2) `scripts/install.sh` (or `scripts/uninstall.sh` for clean removal); (3) verify `~/.claude/rules/engineering-standards.md` symlink is removed; (4) optional emergency override `export AA_MA_HOOKS_DISABLE=1` for users still seeing issues.
  - Notes: pre-v0.5.0 plans remain valid (CEO-4 grandfathering); element #12 is reverted along with the rule.
  - Cross-referenced from CHANGELOG `[0.5.0]` Rollback subsection (M4.4).
- **Result Log:**

### Sub-step 4.9: Author opt-out documentation in rule file (ceo-review finding CEO-1 — distribution-plugin context)
- Status: PENDING
- **Mode:** AFK
- **Dependencies:** Step 1.1
- **Acceptance Criteria:**
  - `claude-code/rules/engineering-standards.md` includes a final `## Opt-out` section documenting that the rule is auto-loaded for any session in projects using aa-ma-forge.
  - Opt-out path documented: (a) `AA_MA_HOOKS_DISABLE=1` master kill switch, (b) remove the `~/.claude/rules/engineering-standards.md` symlink, (c) project-local override via custom rules file.
  - `docs/templates/engineering-standards-template.md` (M2.6) similarly documents that the per-task artifact is OPTIONAL — plans without it are valid.
  - Reasoning sentence: "These standards are opinionated. The plugin ships them as defaults to encourage discipline; consumers may opt out at any layer."
- **Result Log:**
