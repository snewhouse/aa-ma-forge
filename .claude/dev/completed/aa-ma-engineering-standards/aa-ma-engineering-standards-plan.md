<!-- ARCHIVED: 2026-05-09 18:05 -->
<!-- Plan: aa-ma-engineering-standards - COMPLETE -->
<!-- Total Milestones: 5 (M0-M4, all COMPLETE) | Duration: 2026-05-09 (single-day execution) -->
<!-- Release: v0.5.0 (tag 9d16d09 -> commit e1cf4cb) on origin -->

# aa-ma-engineering-standards Plan

**Objective:** Codify six themes of engineering standards into aa-ma-forge so that every `/aa-ma-plan` and `/execute-aa-ma-*` invocation explicitly invokes and verifies them, shipping as v0.5.0.
**Owner:** AI + User (Stephen Newhouse)
**Created:** 2026-05-09
**Last Updated:** 2026-05-09

## Executive Summary

Introduce a single doctrine rule (`claude-code/rules/engineering-standards.md`) plus targeted amendments to existing skills and commands so the six themes (Verification & Truth, Development Principles, Reasoning & Planning, Safety & Continuity, Execution Checklist, Sync & Commit Discipline) become explicit, verifiable, and tiered (step-advisory + milestone HARD/SOFT). Bump the AA-MA Planning Standard from 11 to 12 elements (#12 = "Engineering Standards Declaration"), introduce an ADR convention (`docs/adr/`), and ship as a single coordinated minor bump v0.4.0 → v0.5.0. Success is measured by: zero stale element-count references after Tier 6 drift sweep, all six themes resolvable via grep, install.sh dry-run shows new symlink, and the milestone HARD gate refuses dirty-git completion in a smoke test.

## Target Audience

- **Plugin consumers (downstream Claude Code users):** gain explicit, codified engineering doctrine instead of implicit one-line mentions buried in skill prose.
- **Plan authors / agents using `/aa-ma-plan`:** get a Phase 1 lessons scan, Phase 2 declaration prompt, and Phase 4 element #12 emission for free.
- **Step / milestone executors (`/execute-aa-ma-*`):** get a per-step advisory checklist and a milestone HARD gate that programmatically refuses to mark COMPLETE on dirty git or PENDING sub-steps.
- **Future plan reviewers:** get an extended `plan-verification` Angle 6 that flags missing element #12.
- **Future ADR authors:** get `docs/adr/INDEX.md` and `docs/adr/TEMPLATE.md` (MADR-style) seeded by ADR-0001.

## Implementation Steps

### Milestone 0: AA-MA Workflow Setup + ADR + Plan-Verification

- **Goal:** Land the AA-MA scaffolding for this plan itself: 5 standard artifacts written, ADR set seeded, plan validated by both `aa-ma-validator` and `plan-verification`, cross-references resolve, and the M0 deliverables are committed and pushed.
- **Effort:** 30–45 minutes
- **Complexity:** 35%
- **Mode:** AFK (with HITL fallback if validation surfaces blockers)
- **Gate:** HARD — no implementation milestone (M1+) may begin until M0 is signed off in `context-log.md`.
- **Baseline:** N/A — pure local code, no API exercised

**Acceptance Criteria:**
- [ ] All 5 standard AA-MA artifacts exist at `.claude/dev/active/aa-ma-engineering-standards/` and pass `aa-ma-validator` (read-only check).
- [ ] `docs/adr/INDEX.md`, `docs/adr/TEMPLATE.md`, and `docs/adr/0001-engineering-standards-architecture.md` exist; INDEX.md lists ADR-0001.
- [ ] `plan-verification` skill produces `aa-ma-engineering-standards-verification.md` with no CRITICAL findings (WARNINGs allowed if logged in context-log).
- [ ] `grep -r "engineering-standards" claude-code/ docs/ .claude/dev/active/aa-ma-engineering-standards/` returns no broken cross-references (every reference target resolves on disk).
- [ ] M0 deliverables committed with footer `[AA-MA Plan] aa-ma-engineering-standards .claude/dev/active/aa-ma-engineering-standards` and pushed to `feature/aa-ma-engineering-standards_001`.

**Required Artefacts:**
- `aa-ma-engineering-standards-plan.md` (this file)
- `aa-ma-engineering-standards-reference.md`
- `aa-ma-engineering-standards-context-log.md`
- `aa-ma-engineering-standards-tasks.md`
- `aa-ma-engineering-standards-provenance.log`
- `aa-ma-engineering-standards-verification.md` (produced by plan-verification skill)
- `docs/adr/INDEX.md`, `docs/adr/TEMPLATE.md`, `docs/adr/0001-engineering-standards-architecture.md`

**Tests:**
- `aa-ma-validator` agent on artifacts directory — exit clean
- `plan-verification` skill on this plan — no CRITICAL findings
- `grep -r "engineering-standards" claude-code/ docs/` — every match resolves

**Rollback Strategy:**
- Delete `.claude/dev/active/aa-ma-engineering-standards/` and `docs/adr/`; revert the M0 commit; abandon the feature branch.

**Risks:**
1. Scribe/validator/ADR work runs in parallel and one path produces inconsistent content. Mitigation: M0.4 cross-reference grep is the reconciliation gate before M0.7.
2. plan-verification surfaces CRITICAL findings that require plan revision. Mitigation: revisions land in M0 (before M1 start); decisions logged as new AD-NNN entries in context-log.md.
3. Cross-reference grep finds dangling references (e.g. ADR linked from rule but not yet authored). Mitigation: M0.6 explicitly runs the grep and blocks M0.7 commit until clean.

#### Step 0.1: Create task directory + `docs/adr/` directory scaffold

- **Effort:** 5 min
- **Complexity:** 5%
- **Acceptance:** `.claude/dev/active/aa-ma-engineering-standards/` and `docs/adr/` exist on disk.
- **Artefacts:** the two directories (already created prior to scribe dispatch)

#### Step 0.2: Write the 5 standard AA-MA artifacts

- **Effort:** 15 min
- **Complexity:** 20%
- **Acceptance:** Five files (`-plan.md`, `-reference.md`, `-context-log.md`, `-tasks.md`, `-provenance.log`) exist, follow templates in `docs/templates/`, contain no `[TODO]` / `[fill in]` placeholders.
- **Artefacts:** all 5 AA-MA files for this task

#### Step 0.3: Author ADR set (INDEX.md, TEMPLATE.md, 0001-engineering-standards-architecture.md)

- **Effort:** 15 min
- **Complexity:** 30%
- **Acceptance:** ADR-0001 captures decisions D1–D8 with MADR sections (Title / Status / Context / Decision / Consequences); INDEX.md lists ADR-0001 with Status = `Accepted`.
- **Artefacts:** `docs/adr/INDEX.md`, `docs/adr/TEMPLATE.md`, `docs/adr/0001-engineering-standards-architecture.md`

#### Step 0.4: Run `aa-ma-validator` agent on artifacts (read-only)

- **Effort:** 5 min
- **Complexity:** 10%
- **Acceptance:** Validator reports no missing-required-fields and no template-violation errors.
- **Artefacts:** validator output (logged into context-log.md)

#### Step 0.5: Run `plan-verification` skill → produces `aa-ma-engineering-standards-verification.md`

- **Effort:** 10 min
- **Complexity:** 30%
- **Acceptance:** verification.md exists; no CRITICAL findings; WARNING/INFO findings logged in context-log.md as decisions or accepted risks.
- **Artefacts:** `aa-ma-engineering-standards-verification.md`

#### Step 0.6: Cross-reference grep validation

- **Effort:** 3 min
- **Complexity:** 10%
- **Acceptance:** `grep -r "engineering-standards" claude-code/ docs/` produces no references to nonexistent files.
- **Artefacts:** grep output captured in provenance.log

#### Step 0.7: Commit + push M0 deliverables

- **Effort:** 5 min
- **Complexity:** 15%
- **Acceptance:** Single commit (or atomic series) on `feature/aa-ma-engineering-standards_001` with the required AA-MA footer; pushed to remote.
- **Artefacts:** commit hash recorded in provenance.log

---

### Milestone 1: Doctrine

- **Goal:** The 6-theme doctrine ships as a single rule file (`claude-code/rules/engineering-standards.md`) — principles, not procedures — and the corresponding ADR is marked Implemented.
- **Effort:** 15 min
- **Complexity:** 25%
- **Mode:** AFK
- **Gate:** SOFT
- **Baseline:** N/A — pure local code, no API exercised

**Acceptance Criteria:**
- [ ] `claude-code/rules/engineering-standards.md` exists with sections `### 1.` through `### 6.` (one per theme); `grep -E "^### [1-6]\." claude-code/rules/engineering-standards.md | wc -l` returns 6.
- [ ] File length ≤ ~120 lines (doctrine is concise; procedures live in skills, not here).
- [ ] `docs/adr/0001-engineering-standards-architecture.md` Status field updated from `Accepted` to `Implemented` with timestamp.

**Required Artefacts:**
- `claude-code/rules/engineering-standards.md`
- Updated `docs/adr/0001-engineering-standards-architecture.md`

**Tests:**
- `grep -E "^### [1-6]\." claude-code/rules/engineering-standards.md | wc -l` → 6
- `wc -l claude-code/rules/engineering-standards.md` → ≤ 120

**Rollback Strategy:**
- `git revert` the M1 commit; ADR Status reverts to `Accepted`.

**Risks:**
1. Doctrine grows beyond principles into procedures. Mitigation: hard cap on file length; reference `operational-constraints` and `plan-verification` for procedures.
2. ADR Status update forgotten. Mitigation: M1.2 is an explicit step.
3. Doctrine duplicates existing skill content. Mitigation: write principles only; reference skills by path.

#### Step 1.1: Write `claude-code/rules/engineering-standards.md`

- **Effort:** 12 min
- **Complexity:** 25%
- **Acceptance:** Six themed sections present; ≤ 120 lines; cross-references to `first-principles-framework`, `operational-constraints`, `impact-analysis`, `aa-ma-commit-drift.sh` resolve on disk.
- **Artefacts:** `claude-code/rules/engineering-standards.md`

#### Step 1.2: Update ADR-0001 Status: Accepted → Implemented

- **Effort:** 3 min
- **Complexity:** 5%
- **Acceptance:** ADR-0001 Status field reads `Implemented (YYYY-MM-DD)`; INDEX.md mirrors the change.
- **Artefacts:** `docs/adr/0001-engineering-standards-architecture.md`, `docs/adr/INDEX.md`

---

### Milestone 2: Workflow integration

- **Goal:** Existing skills and commands are amended (not duplicated) to invoke the new doctrine — operational-constraints references the rule, plan-verification Angle 6 detects missing element #12, and the three `/execute-aa-ma-*` and `/aa-ma-plan` commands carry the new advisory + HARD-gate logic.
- **Effort:** 60 min
- **Complexity:** 55%
- **Mode:** AFK except Step 2.2 which is HITL (prototype required for Angle 6 vs Angle 7 decision)
- **Gate:** SOFT
- **Baseline:** N/A — pure local code, no API exercised

**Acceptance Criteria:**
- [ ] `claude-code/skills/operational-constraints/SKILL.md` references `claude-code/rules/engineering-standards.md` and grows by ≤ 20 lines.
- [ ] `claude-code/skills/plan-verification/SKILL.md` Angle 6 (or new Angle 7 if prototype shows it cleaner) detects a plan with no element #12 and flags it.
- [ ] `claude-code/commands/aa-ma-plan.md` Phase 1 includes a "Lessons Scan" subsection; Phase 2 prompts for "Engineering Standards Declaration"; Phase 4 emits element #12 in plan output.
- [ ] `claude-code/commands/execute-aa-ma-step.md` includes the per-step advisory checklist (the 7 items from Theme 5) injected into the prompt contract.
- [ ] `claude-code/commands/execute-aa-ma-milestone.md` includes a milestone HARD gate that refuses to mark COMPLETE on (a) dirty git, (b) zero PENDING within milestone, (c) tests-pass evidence, (d) impact-analysis run, (e) provenance evidence for `Critical-Path:` and `Prototype-Required:` tasks.
- [ ] `docs/templates/engineering-standards-template.md` exists.
- [ ] `docs/templates/tasks-template.md` includes `Prototype-Required:` and `Critical-Path:` fields.

**Required Artefacts:**
- Modified: `operational-constraints/SKILL.md`, `plan-verification/SKILL.md`, `aa-ma-plan.md`, `execute-aa-ma-step.md`, `execute-aa-ma-milestone.md`, `tasks-template.md`
- New: `docs/templates/engineering-standards-template.md`
- Prototype branch / scratch artifact for Step 2.2 (Angle 6 vs Angle 7 decision)

**Tests:**
- Smoke: `/aa-ma-plan "trivial test feature"` emits Phase 1 Lessons Scan + Phase 2 declaration prompt + Phase 4 element #12 (manual run, not gated by CI).
- Smoke: plan with element #12 deleted → `plan-verification` flags it.
- Static: `wc -l` diff on `operational-constraints/SKILL.md` shows +≤20 lines.

**Rollback Strategy:**
- `git revert` the M2 commit (or commit series); doctrine rule from M1 stays in place but is no longer invoked from skills/commands.

**Risks:**
1. Skill amendments balloon past the +20-line cap. Mitigation: enforce reference-only edits; review diff size before committing.
2. Angle 6 extension conflicts with existing Angle 6 logic. Mitigation: prototype both Angle 6 extension and Angle 7 addition in a scratch branch (Step 2.2 Prototype-Required), pick one, document choice in context-log.
3. `aa-ma-plan.md` Phase 1 lessons scan exceeds 30s budget. Mitigation: cap scan to lessons.md + `git log --grep="revert\|fix\|hotfix"` since 6 months + top-3 most-recent completed context-logs; abort scan on timeout.

#### Step 2.1: Amend `operational-constraints/SKILL.md`

- **Effort:** 8 min
- **Complexity:** 30%
- **Acceptance:** Skill references `engineering-standards.md`; ≤ +20 lines; no doctrine duplication.
- **Artefacts:** `claude-code/skills/operational-constraints/SKILL.md`

#### Step 2.2: Prototype Angle 6 extension vs Angle 7 addition; pick one

- **Effort:** 15 min
- **Complexity:** 70%
- **HITL — Prototype-Required: YES**
- **Acceptance:** `plan-verification` skill flags a plan missing element #12; the chosen approach (Angle 6 extension OR new Angle 7) documented in context-log with rationale; provenance.log carries `[ts] PROTOTYPE — <verdict>`.
- **Artefacts:** scratch branch with both prototypes; final amended `claude-code/skills/plan-verification/SKILL.md`

#### Step 2.3: Amend `aa-ma-plan.md` (Phases 1, 2, 4)

- **Effort:** 12 min
- **Complexity:** 45%
- **Acceptance:** Phase 1 includes "Lessons Scan" with 30s budget cap; Phase 2 prompts for Engineering Standards Declaration; Phase 4 emits element #12.
- **Artefacts:** `claude-code/commands/aa-ma-plan.md`

#### Step 2.4: Amend `execute-aa-ma-step.md` (per-step advisory checklist)

- **Effort:** 8 min
- **Complexity:** 35%
- **Acceptance:** Prompt contract includes the 7-item checklist; SOFT items request declaration in context-log, HARD items defer enforcement to milestone gate.
- **Artefacts:** `claude-code/commands/execute-aa-ma-step.md`

#### Step 2.5: Amend `execute-aa-ma-milestone.md` (milestone HARD gate)

- **Effort:** 10 min
- **Complexity:** 60%
- **Acceptance:** Command refuses to mark COMPLETE while git is dirty, while any `Status: PENDING` remains, when tests-pass evidence missing, when impact-analysis not run, or when `Critical-Path:` / `Prototype-Required:` tasks lack provenance entries.
- **Artefacts:** `claude-code/commands/execute-aa-ma-milestone.md`

#### Step 2.6: Add `docs/templates/engineering-standards-template.md`

- **Effort:** 5 min
- **Complexity:** 15%
- **Acceptance:** Template provides optional per-task artifact format (one section per theme).
- **Artefacts:** `docs/templates/engineering-standards-template.md`

#### Step 2.7: Add `Prototype-Required:` and `Critical-Path:` fields to `tasks-template.md`

- **Effort:** 3 min
- **Complexity:** 10%
- **Acceptance:** Both fields documented as optional; default empty/absent; existing examples in `examples/` continue to validate.
- **Artefacts:** `docs/templates/tasks-template.md`

---

### Milestone 3: Planning Standard bump (11 → 12)

- **Goal:** Every reference to "11 elements" or "11 outputs" of the AA-MA Planning Standard is updated to 12, element #12 (Engineering Standards Declaration) is documented in spec/quick-ref/foundations/skill/template, and the Tier 6 hardcoded-count drift detector returns clean.
- **Effort:** 30 min
- **Complexity:** 50%
- **Mode:** AFK
- **Gate:** HARD
- **Critical-Path:** doc-count-drift
- **Baseline:** N/A — pure local code, no API exercised

**Acceptance Criteria:**
- [ ] `claude-code/rules/aa-ma.md` Planning Standard section lists 12 elements; element #12 is "Engineering Standards Declaration".
- [ ] `docs/spec/aa-ma-specification.md` Section XI lists 12 elements with full description of #12.
- [ ] `docs/spec/aa-ma-quick-reference.md` shows 12 (not 11).
- [ ] `docs/spec/claude-code-foundations.md` shows 12 + lists `engineering-standards.md` in the rules list (1 → 2 rules).
- [ ] `claude-code/skills/aa-ma-plan-workflow/SKILL.md` Phase 4 description references element #12.
- [ ] `docs/templates/plan-template.md` contains a placeholder for element #12.
- [ ] Tier 6 drift detector (per `~/.claude/rules/doc-drift-checks.md`) returns zero stale "11" references outside CHANGELOG.md.
- [ ] README.md and SECURITY.md show updated counts where applicable.

**Required Artefacts:**
- Modified: `claude-code/rules/aa-ma.md`, `docs/spec/aa-ma-specification.md`, `docs/spec/aa-ma-quick-reference.md`, `docs/spec/claude-code-foundations.md`, `claude-code/skills/aa-ma-plan-workflow/SKILL.md`, `docs/templates/plan-template.md`, `README.md`, `SECURITY.md`
- Tier 6 drift detector output (logged in provenance)

**Tests:**
- `grep -rn "11 elements\|11 outputs\|11 mandatory" claude-code/ docs/ README.md SECURITY.md | grep -v CHANGELOG` → zero hits.
- `grep -c "^[0-9]\+\." claude-code/rules/aa-ma.md` (within Planning Standard section) → 12.

**Rollback Strategy:**
- `git revert` the M3 commit series; element count returns to 11; subsequent milestones (M4) blocked.

**Risks:**
1. Hardcoded-count drift across 6+ files survives the bump. Mitigation: M3.7 explicitly runs Tier 6 detector; HARD gate refuses completion if hits remain.
2. Element #12 wording differs across docs. Mitigation: define canonical phrasing in `aa-ma.md` first (M3.1), then propagate verbatim.
3. plan-template.md placeholder conflicts with existing examples. Mitigation: grep `examples/` for any plan files and update if present (likely none — this template is bracketed).

#### Step 3.1: Update `claude-code/rules/aa-ma.md` Planning Standard section

- **Effort:** 5 min
- **Complexity:** 25%
- **Acceptance:** Section lists 12 elements; element #12 is "Engineering Standards Declaration" with one-line description.
- **Artefacts:** `claude-code/rules/aa-ma.md`

#### Step 3.2: Update `docs/spec/aa-ma-specification.md` Section XI

- **Effort:** 6 min
- **Complexity:** 30%
- **Acceptance:** Section XI lists 12 elements; element #12 has full prose description; canonical phrasing matches M3.1.
- **Artefacts:** `docs/spec/aa-ma-specification.md`

#### Step 3.3: Update `docs/spec/aa-ma-quick-reference.md`

- **Effort:** 3 min
- **Complexity:** 15%
- **Acceptance:** All "11"-element references updated to "12"; new element entry added.
- **Artefacts:** `docs/spec/aa-ma-quick-reference.md`

#### Step 3.4: Update `docs/spec/claude-code-foundations.md`

- **Effort:** 4 min
- **Complexity:** 20%
- **Acceptance:** Element count = 12; rule-file count updated (1 → 2); `engineering-standards.md` listed.
- **Artefacts:** `docs/spec/claude-code-foundations.md`

#### Step 3.5: Update `aa-ma-plan-workflow/SKILL.md` Phase 4 description

- **Effort:** 3 min
- **Complexity:** 15%
- **Acceptance:** Phase 4 references element #12; matches canonical phrasing.
- **Artefacts:** `claude-code/skills/aa-ma-plan-workflow/SKILL.md`

#### Step 3.6: Update `docs/templates/plan-template.md`

- **Effort:** 3 min
- **Complexity:** 15%
- **Acceptance:** Template includes placeholder for element #12 with bracketed prompt.
- **Artefacts:** `docs/templates/plan-template.md`

#### Step 3.7: Run hardcoded-count drift detector (Tier 6)

- **Effort:** 4 min
- **Complexity:** 25%
- **Acceptance:** `grep -rn "11 elements\|11 outputs\|11 mandatory" claude-code/ docs/ README.md SECURITY.md | grep -v CHANGELOG` returns zero; any hits found are fixed before milestone completion.
- **Artefacts:** Tier 6 output in provenance.log

#### Step 3.8: Update README.md and SECURITY.md if they cite element count

- **Effort:** 2 min
- **Complexity:** 10%
- **Acceptance:** No stale "11" references remain; counts mirror canonical wording.
- **Artefacts:** `README.md`, `SECURITY.md`

---

### Milestone 4: Release

- **Goal:** v0.5.0 ships as a single coordinated minor bump: tests green, ruff green, install dry-run shows new symlink, CHANGELOG [0.5.0] section authored, commitizen bumps version, single tag `v0.5.0` pushed.
- **Effort:** 30 min
- **Complexity:** 45%
- **Mode:** HITL (M4.6 push tag is human-gated)
- **Gate:** HARD
- **Critical-Path:** version-pipeline
- **Baseline:** N/A — pure local code; CI/release pipeline only

**Acceptance Criteria:**
- [ ] `uv run pytest` (default markers) returns exit 0.
- [ ] `bats tests/hooks/` returns exit 0 (or marked SKIP with reason if bats unavailable on host).
- [ ] `uv run ruff check src/` returns exit 0.
- [ ] `scripts/install.sh --dry-run` lists `claude-code/rules/engineering-standards.md` among new symlinks.
- [ ] `CHANGELOG.md` `[0.5.0]` section exists, summarizes the 6 themes + Planning Standard bump + ADR convention.
- [ ] `pyproject.toml` version = `0.5.0` (was `0.4.0`).
- [ ] Tag `v0.5.0` exists on the merge commit and is pushed to origin.

**Required Artefacts:**
- Updated `CHANGELOG.md`, `pyproject.toml`
- Tag `v0.5.0`

**Tests:**
- Pre-release: `uv run pytest`, `bats tests/hooks/`, `uv run ruff check src/`
- Post-release: `git log --oneline | head -5` shows the tag commit; `pyproject.toml` version matches `CHANGELOG.md` latest section.

**Rollback Strategy:**
- If tag pushed but CI fails: `git push --delete origin v0.5.0`, `git tag -d v0.5.0`, revert version commit, re-run M4 from M4.1.
- If commitizen mid-bump fails: rerun `cz bump` after fixing the issue; commitizen is idempotent.

**Risks:**
1. CI fails post-tag. Mitigation: run all M4.1–M4.3 checks locally before M4.5 bump.
2. install.sh dry-run misses new symlink (e.g. directory not created). Mitigation: M4.3 grep is explicit; failure blocks M4.4.
3. Version drift between `pyproject.toml`, `CHANGELOG.md`, and tag. Mitigation: commitizen + python-semantic-release is the single source; `cz bump` writes all three in one operation.

#### Step 4.1: Run `uv run pytest` (default suite) and `bats tests/hooks/`

- **Effort:** 5 min
- **Complexity:** 15%
- **Acceptance:** Both exit 0; failures fixed in same milestone before proceeding.
- **Artefacts:** test output captured in provenance.log

#### Step 4.2: Run `uv run ruff check src/`

- **Effort:** 1 min
- **Complexity:** 10%
- **Acceptance:** Exit 0.
- **Artefacts:** ruff output

#### Step 4.3: Run `scripts/install.sh --dry-run`; verify new symlinks listed

- **Effort:** 2 min
- **Complexity:** 15%
- **Acceptance:** Output includes `claude-code/rules/engineering-standards.md`, `docs/templates/engineering-standards-template.md` (if applicable), and `docs/adr/` content as expected.
- **Artefacts:** dry-run output in provenance.log

#### Step 4.4: Update `CHANGELOG.md` [0.5.0] section

- **Effort:** 6 min
- **Complexity:** 25%
- **Acceptance:** Section summarizes: 6-theme doctrine, ADR convention, Planning Standard 11 → 12, new templates and fields, milestone HARD gate. Conventional Commits style.
- **Artefacts:** `CHANGELOG.md`

#### Step 4.5: Run `cz bump` → version 0.4.0 → 0.5.0

- **Effort:** 3 min
- **Complexity:** 25%
- **Acceptance:** `pyproject.toml` version becomes `0.5.0`; commit created by commitizen; CHANGELOG line aligned.
- **Artefacts:** `pyproject.toml`, commitizen commit

#### Step 4.6: Tag and push `v0.5.0`

- **HITL — User confirms before tag push**
- **Effort:** 2 min
- **Complexity:** 25%
- **Acceptance:** Tag `v0.5.0` exists locally and on origin; `git push origin feature/aa-ma-engineering-standards_001 --tags` succeeds.
- **Artefacts:** tag `v0.5.0`, push confirmation

---

## Dependencies & Assumptions

### Dependencies

| Dependency | Class | Notes |
|-----------|-------|-------|
| `uv` (existing) | Required | Test runner, lint, dependency resolution |
| `bats` (system pkg) | Dev-only | Hook tests; install via `apt-get install -y bats` if missing |
| `commitizen` (`cz`) | Required | Version bump and CHANGELOG management |
| `python-semantic-release` | Required | Coupled with commitizen for tag automation |
| `ruff` | Dev-only | Lint and format Python source |
| `aa-ma-validator` agent | Required | Read-only artifact validation in M0.4 |
| `plan-verification` skill | Required | Adversarial plan verification in M0.5 |
| `first-principles-framework` skill | Optional (referenced) | Doctrine references it; existence verified by cross-reference grep |
| `impact-analysis` skill | Required (referenced) | Milestone HARD gate enforces it |

### Assumptions

1. **`docs/adr/` does not yet exist.** If it does, M0.3 must merge with existing convention rather than create from scratch. Impact if wrong: M0.3 rework; existing INDEX.md content preserved.
2. **No active plan currently uses element #12.** Historical docs are frozen per `CLAUDE.md:70`. Impact if wrong: nothing — historical plans don't get retroactive updates.
3. **The Tier 6 drift detector exists in `~/.claude/rules/doc-drift-checks.md`.** Verified earlier in plan context. Impact if wrong: M3.7 falls back to manual `grep -rn "11"` audit.
4. **`scripts/install.sh` symlinks any file matching `claude-code/rules/*.md` automatically.** Impact if wrong: M4.3 dry-run fails to show the new symlink → install.sh needs update (out of scope; would block release).
5. **`cz bump` will recognize the feat/refactor commits as a minor bump.** Impact if wrong: bump produces 0.4.1 (patch) or fails; manual override via `cz bump --increment minor`.
6. **No downstream consumer pins to AA-MA Planning Standard element count.** The bump 11 → 12 is additive, not breaking. Impact if wrong: minor-bump semantics violated; would need major bump (1.0.0). Considered low risk.

## Next Action

**Do this first:** Complete M0.2 by writing the 5 standard AA-MA artifacts (this scribe invocation), then proceed in parallel/sequence to M0.3 (ADR set authoring) and M0.4 (validator run). Block at M0.6 cross-reference grep before committing M0 deliverables.
**Update:** TASKS (mark Step 0.2 COMPLETE with Result Log; remaining M0 steps stay PENDING until executed) and PROVENANCE (append `AA_MA_SCRIBE_COMPLETE` event with file counts).

## 12. Engineering Standards Declaration

_Element #12 — this plan dogfoods the bump it advocates. The Planning Standard formally moves from 11 to 12 elements in M3; this plan is the first plan authored under the new format._

This plan applies the six engineering-standards themes as follows:

1. **Verification & Truth** — every milestone except M0/M1/M2 (pure local code) declares `Baseline: N/A` explicitly; M2.2 carries `Prototype-Required: YES` and will produce a `[ts] PROTOTYPE — <verdict>` provenance entry; M3 carries `Critical-Path: doc-count-drift`; M4 carries `Critical-Path: version-pipeline`.
2. **Development Principles** — Doctrine file is principles-only (KISS); skill amendments reference rather than duplicate (DRY); each amended skill remains single-responsibility (SOLID/SOC); commands carry the new advisory inline rather than fan out new files (KISS).
3. **Reasoning & Planning** — plan reached via 7-question grill-with-docs interview (Socratic); locked decisions D1–D8 captured in context-log.md; ADR-0001 captures the architectural rationale (first-principles).
4. **Safety & Continuity** — Phase 1 lessons scan is the mechanism; existing aa-ma-commit-drift hook remains in place (non-breaking); historical plans are NOT retroactively migrated (frozen-docs constraint per `CLAUDE.md:70`); milestone HARD gates block dirty-git completion.
5. **Execution Checklist** — M0/M3/M4 are HARD gates; M1/M2 are SOFT; per-step advisory injected via M2.4 amendment to `execute-aa-ma-step.md`.
6. **Sync & Commit Discipline** — every milestone ends with a commit carrying the AA-MA footer; sub-step Result Logs mandatory per L-080–082; milestone-end is the only commit gate (per locked decision D6).

**Lessons Scan summary:** prior aa-ma-forge plans (`hooks-hardening-m1`, `ship-missing-skills`, `token-stack-integration`, completed) reviewed for revert/fix/hotfix history; no past mistake patterns were identified that affect this plan's design. Past success patterns reused: HARD/SOFT gate format from `claude-code/rules/aa-ma.md`, sub-step sync rule (L-080–082), Tier 6 drift detector. Past failure patterns avoided: skill duplication (resolved via D1: amendments-not-new-skill), hardcoded-count drift (resolved via D3 + Tier 6 sweep in M3.7), big-bang releases (resolved via D8: single coordinated minor bump).

## AA-MA File Mapping

- **tasks.md:** Convert each Milestone (M0, M1, M2, M3, M4) to `## Milestone N` with `Status:`, `Mode:`, `Gate:`, `Complexity:`, `Critical-Path:`, `Prototype-Required:` fields; convert each Step to `### Sub-step N.M` with `Status: PENDING` (M0.1 and M0.2 carry IN_PROGRESS as the scribe runs).
- **reference.md:** Extract paths (new files, modified files, modified docs), branch name, target version, doctrine themes table, and external reference paths (e.g. `~/.claude/rules/doc-drift-checks.md`).
- **context-log.md:** Log plan creation (2026-05-09), 8 locked decisions D1–D8 as AD-001 … AD-008, research findings (existing surface area from Phase 1 exploration), and remaining questions (Angle 6 vs Angle 7 — resolved by M2.2 prototype).
- **provenance.log:** Initialize with PLAN_CREATED, GRILLING_COMPLETE, PLAN_APPROVED, M0_STARTED, AA_MA_SCRIBE_DISPATCHED entries; append CHECKPOINT and commit entries during execution.
