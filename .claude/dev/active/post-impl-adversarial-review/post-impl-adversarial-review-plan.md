# Plan: Post-Impl Adversarial Review (Phase 6.8 + /verify-impl)

**Objective:** Close the post-execution discipline gap in aa-ma-forge by adding a Phase 6.8 *Post-Impl Adversarial Review* to `/execute-aa-ma-milestone` and `/execute-aa-ma-full`, plus a new `/verify-impl` skill symmetric to `/verify-plan`.
**Owner:** AI + User (Stephen Newhouse)
**Created:** 2026-05-11
**Last Updated:** 2026-05-11
**Status:** APPROVED — implementation begun
**Task Name:** `post-impl-adversarial-review`
**Target Directory:** `.claude/dev/active/post-impl-adversarial-review/`
**Plugin Version Target:** v0.7.0 → v0.8.0

---

## Pre-Flight Verification (grounded, not assumed)

Every claim in this plan was verified against code + git, not memory:

| Claim | Verified by | Status |
|---|---|---|
| Current version is 0.7.0 | `grep ^version pyproject.toml` | OK |
| Next ADR number is 0005 | `ls docs/adr/` shows 0001-0004 | OK |
| `verify-impl` skill name available | `find claude-code -iname "*verify*impl*"` returned no results | OK |
| `security-static-check.sh` hook name available | `find claude-code/hooks -iname "*security*"` returned no results | OK |
| Phase numbering §6.8 free | `execute-aa-ma-milestone.md` §6.7 at line 481, §7.1 at line 559 | OK |
| 8 templates exist | `ls docs/templates/` shows plan, tasks, reference, context-log, provenance, verification, tests, engineering-standards | OK |
| `Created:` front-matter pattern used | Confirmed in `.claude/dev/completed/harden-aa-ma-plan/harden-aa-ma-plan-plan.md` | OK |
| L-001 to L-007 all exist in `docs/lessons.md` | `grep -nE "^## L-[0-9]+" docs/lessons.md` | OK |
| `.claude/dev/active/` empty | `ls` returned no directories | OK |
| Existing agents: only `aa-ma-scribe`, `aa-ma-validator` | `ls claude-code/agents/` | OK |

---

## Executive Summary

**The problem:** Pre-execution rigor in aa-ma-forge is high (6-angle plan-verification + 9 HARD gates at milestone close), but post-execution review is thin — only one SOFT, skippable simplification review. Project's own lesson history (L-005 KISS violation, L-006 CHANGELOG regression, L-007 out-of-scope drift) confirms gaps bite.

**The approach:** Add Phase 6.8 *Post-Impl Adversarial Review* to `/execute-aa-ma-milestone` (mirrors plan-verification post-implementation). New `/verify-impl` skill dispatches five parallel audit agents per plan-declared `Audit-Profile`. Mechanical security checks move to a new `security-static-check.sh` pre-commit hook. Grandfathered by `Created:` date — does not break in-flight plans.

**Success criteria:** (1) Phase 6.8 fires on milestones with `Created: >= v0.8.0` and matching `Audit-Profile`; (2) CRITICAL findings block §7.3 user approval via accept/dispute/defer panel; (3) Project's own historical gaps (L-005, L-006, L-007) would have been caught by the new agents.

---

## Context

User invoked `/grill-with-docs` to stress-test aa-ma-forge's plan-execution discipline. Concerns enumerated: code review, security review, simplification, missing tests, TDD/KISS/DRY/SOLID/SOC adherence, Context7 usage, future-proofing. A 7-question grilling session (Q1–Q7b) walked the design tree branch-by-branch, with each decision grounded in code, git history, and the project's own lessons. This plan is the consolidated output.

---

## Target Audience

- **Plan authors using aa-ma-forge** — get assurance their implementations meet the same bar as their plans
- **Future contributors** — clear feedback on KISS/SOLID/SOC violations before merge
- **Plugin maintainers (Stephen)** — symmetry between plan and impl verification reduces post-ship surprises (L-006 class)

---

## Resolved Design Decisions

Captured during grilling Q1–Q7b. See `[task]-context-log.md` for full rationale; summary here.

| # | Branch | Decision |
|---|---|---|
| 1 | Asymmetry | Phase 6.8 + new `/verify-impl` skill; 5 parallel agents; CRITICAL blocks §7.3 |
| 2 | Trigger | Plan-declared `Audit-Profile` per milestone (`full | code-only | docs-only | infra | custom`) |
| 3 | TDD strictness | Strict commit-ordering; first `tests/` commit < first `src/` commit; canonical `TDD-Waiver` values |
| 4 | False-positive tolerance | Severity-gated user override panel: CRITICAL → accept/dispute/defer |
| 5 | Budget | `Audit-Profile` IS the budget; `AA_MA_AUDIT_BUDGET={low,off}` global escape valve |
| 6 | Backwards compat | Grandfather by `Created:` date (mirrors v0.5.0 precedent for element #12) |
| 7a | Security split | Mechanical → `security-static-check.sh` hook (commit-time, free); Semantic → `security-auditor` agent (milestone close) |
| 7b | Context7 scope | New deps + MAJOR version bumps only; minor/patch skipped (uv.lock noise) |

### Canonical `TDD-Waiver` values
`refactor` | `docs-only` | `prototype` | `hotfix-emergency` | `tooling-config`. Adding new values requires plan + ADR (matches `Critical-Path:` enum pattern).

---

## Implementation Steps

### Milestone 1: ADR-0005 + Spec Doc Update

- **Goal:** Document the cutover decision and Phase 6.8 anatomy in ADR-0005 and `docs/spec/aa-ma-specification.md`. Establishes architectural rationale before any code lands.
- **Effort:** 2h
- **Complexity:** 30%
- **Mode:** HITL
- **Gate:** SOFT
- **Baseline:** N/A — pure local code, no API exercised
- **Audit-Profile:** `docs-only`
- **Critical-Path:** doc-count-drift

**Acceptance Criteria:**
- [ ] `docs/adr/0005-post-impl-adversarial-review.md` exists, follows TEMPLATE.md structure, references ADR-0001 (engineering-standards-architecture)
- [ ] `docs/adr/INDEX.md` lists ADR-0005
- [ ] `docs/spec/aa-ma-specification.md` gains §6.8 Post-Impl Adversarial Review subsection with file:line references to where Phase 6.8 will live
- [ ] Cutover rule documented: "Plans with `Created: < v0.8.0-release-date` are grandfathered; §6.8 does not fire"

**Required Artefacts:**
- `docs/adr/0005-post-impl-adversarial-review.md` (NEW)
- `docs/adr/INDEX.md` (EDIT)
- `docs/spec/aa-ma-specification.md` (EDIT — add §6.8 anatomy)

**Tests:**
- ShellCheck on any code samples in ADR (n/a — pure prose)
- `markdownlint` on new files if configured
- Verify cross-references resolve: `grep -r "ADR-0005" docs/ claude-code/`

**Rollback Strategy:** `git revert <M1-commit-sha>` — pure docs, no behaviour change.

**Risks:**
1. ADR drifts from final implementation → mitigation: M1 commits AFTER M5 integration is complete; rewritten if §6.8 anatomy changes
2. Cutover date is wrong (e.g., v0.8.0 ships with hot-fix delays) → mitigation: cite "v0.8.0 release tag commit" instead of a fixed date
3. INDEX.md drift → mitigation: M1 includes `docs/adr/INDEX.md` edit in same commit

#### Step 1.1: Draft ADR-0005 from TEMPLATE.md
- **Effort:** 1h
- **Complexity:** 30%
- **Acceptance:** ADR-0005 exists; covers Context, Decision, Consequences, Alternatives Considered (mirror ADR-0001 structure)
- **Artefacts:** `docs/adr/0005-post-impl-adversarial-review.md`

#### Step 1.2: Update INDEX.md
- **Effort:** 15min
- **Complexity:** 10%
- **Acceptance:** INDEX.md lists ADR-0005 with one-line summary
- **Artefacts:** `docs/adr/INDEX.md`

#### Step 1.3: Add §6.8 anatomy to aa-ma-specification.md
- **Effort:** 45min
- **Complexity:** 40%
- **Acceptance:** New `### 6.8 Post-Impl Adversarial Review` subsection documents trigger, 5 agents, severity matrix, override panel, escape valves
- **Artefacts:** `docs/spec/aa-ma-specification.md`

---

### Milestone 2: `security-static-check.sh` Pre-Commit Hook (TDD-first)

- **Goal:** Catch mechanical security anti-patterns at commit time, zero-token cost. Mirrors `aa-ma-commit-drift.sh` PreToolUse pattern.
- **Effort:** 4h
- **Complexity:** 60%
- **Mode:** AFK
- **Gate:** HARD
- **Baseline:** N/A — pure local code, no API exercised
- **Audit-Profile:** `code-only`
- **Critical-Path:** hook-modification

**Acceptance Criteria:**
- [ ] `claude-code/hooks/security-static-check.sh` exists, executable, shellcheck-clean
- [ ] Detects 5 pattern classes: hardcoded secrets, shell-injection idioms, path-traversal, SQL string concatenation, unsafe binary deserialisation idioms (CWE-502)
- [ ] Bypassable via `AA_MA_HOOKS_DISABLE=1` and `[security-bypass: reason]` marker (auditable)
- [ ] Bats test suite covers: each pattern detected, each bypass mechanism, no-pattern → exit 0
- [ ] `scripts/install.sh` adds the hook to symlink list (verified via `--dry-run` grep)

**Required Artefacts:**
- `claude-code/hooks/security-static-check.sh` (NEW)
- `tests/hooks/security_static_check.bats` (NEW)
- `scripts/install.sh` (EDIT — register new hook)

**Tests:**
- `bats tests/hooks/security_static_check.bats` — all cases pass
- Each of the 5 pattern classes has a positive (caught) and negative (clean) case
- `shellcheck claude-code/hooks/security-static-check.sh` — exit 0

**Rollback Strategy:** `git revert`; un-symlink via `scripts/uninstall.sh`.

**Risks:**
1. False positives flood developer experience → mitigation: bypass marker `[security-bypass: <reason>]` documented; logged in commit msg
2. Hook fires on commits to other repos via global install → mitigation: check that `pwd` is a git repo and a project with `pyproject.toml` before scanning
3. Shellcheck violations in the hook itself → mitigation: TDD; bats test runs shellcheck as part of suite

#### Step 2.1: Write bats tests FIRST (red)
- **Effort:** 1.5h
- **Complexity:** 50%
- **Acceptance:** Bats file with 10+ test cases, all currently failing (no hook exists)
- **Artefacts:** `tests/hooks/security_static_check.bats`

#### Step 2.2: Implement hook to pass each test (green)
- **Effort:** 2h
- **Complexity:** 60%
- **Acceptance:** All bats tests pass; shellcheck clean
- **Artefacts:** `claude-code/hooks/security-static-check.sh`

#### Step 2.3: Register hook in `scripts/install.sh`
- **Effort:** 30min
- **Complexity:** 30%
- **Acceptance:** `scripts/install.sh --dry-run | grep security-static-check.sh` returns the new symlink line
- **Artefacts:** `scripts/install.sh`

---

### Milestone 3: `Audit-Profile` + `TDD-Waiver` Parsers in plan-verification (TDD-first)

- **Goal:** Extend plan-verification Angle 6 (Specialist Domain Audit / Engineering Standards Structural Check) to enforce `Audit-Profile` presence per milestone and validate `TDD-Waiver` canonical values.
- **Effort:** 5h
- **Complexity:** 70%
- **Mode:** AFK
- **Gate:** HARD
- **Baseline:** N/A — pure local code, no API exercised
- **Audit-Profile:** `code-only`

**Acceptance Criteria:**
- [ ] plan-verification structural check fails when a v0.8.0-or-later plan milestone lacks `Audit-Profile:` field
- [ ] plan-verification rejects non-canonical `TDD-Waiver:` values (e.g., `TDD-Waiver: idk`)
- [ ] Grandfathering: plans with `Created:` < v0.8.0 release date pass without `Audit-Profile`
- [ ] pytest cases cover: missing field, valid field, invalid field, grandfathered absence
- [ ] `Skill(plan-verification)` SKILL.md Angle 6 documents the new checks

**Required Artefacts:**
- `claude-code/skills/plan-verification/SKILL.md` (EDIT — Angle 6 additions)
- `src/aa_ma/plan_parsers.py` (NEW or EDIT — Audit-Profile + TDD-Waiver field parsers)
- `tests/codemem/test_audit_profile_parser.py` (NEW)
- `tests/codemem/test_tdd_waiver_parser.py` (NEW)

**Tests:**
- `uv run pytest tests/codemem/test_audit_profile_parser.py` — all pass
- `uv run pytest tests/codemem/test_tdd_waiver_parser.py` — all pass
- `uv run ruff check src/aa_ma/plan_parsers.py` — exit 0

**Rollback Strategy:** `git revert`; plan-verification reverts to v0.7.0 angle-6 logic.

**Risks:**
1. Grandfathering logic misfires (rejects pre-v0.8.0 plans) → mitigation: explicit pytest cases for boundary dates; test against actual completed plans in `.claude/dev/completed/`
2. Parser is too rigid (rejects valid edge cases) → mitigation: corpus-test against every completed plan's `tasks.md` for false-positive count
3. Canonical-value list drifts from `engineering-standards.md` → mitigation: parser imports the list from a single shared module

#### Step 3.1: Write pytest cases FIRST (red)
- **Effort:** 1.5h
- **Complexity:** 50%
- **Acceptance:** 15+ test cases across both parsers, all currently failing
- **Artefacts:** `tests/codemem/test_audit_profile_parser.py`, `tests/codemem/test_tdd_waiver_parser.py`

#### Step 3.2: Implement parsers (green)
- **Effort:** 2h
- **Complexity:** 70%
- **Acceptance:** All pytest cases pass; ruff clean
- **Artefacts:** `src/aa_ma/plan_parsers.py`

#### Step 3.3: Wire parsers into plan-verification Angle 6
- **Effort:** 1h
- **Complexity:** 50%
- **Acceptance:** `Skill(plan-verification)` Angle 6 SKILL.md documents the new structural checks; integration test verifies they fire on synthetic non-canonical inputs
- **Artefacts:** `claude-code/skills/plan-verification/SKILL.md`

#### Step 3.4: Corpus-test against existing completed plans
- **Effort:** 30min
- **Complexity:** 40%
- **Acceptance:** Running parser against every `.claude/dev/completed/*/*-tasks.md` produces zero false-positive failures (grandfathered)
- **Artefacts:** `tests/codemem/test_corpus_grandfathering.py`

---

### Milestone 4: `/verify-impl` Skill + 5 Agent Prompts

- **Goal:** Implement the skill and the 5 audit-agent prompts. **`Prototype-Required: YES`** — agent prompts are subjective; prototype first to test signal/noise on synthetic milestones before committing to final wording.
- **Effort:** 6h
- **Complexity:** **80%** ← HIGH COMPLEXITY — requires human review
- **Mode:** HITL
- **Gate:** HARD
- **Baseline:** N/A — pure local code, no API exercised
- **Audit-Profile:** `full`
- **Prototype-Required:** YES
- **Critical-Path:** (none — agent prompts have no external API or version-pipeline impact)

**Acceptance Criteria:**
- [ ] `claude-code/skills/verify-impl/SKILL.md` exists, follows Skill format, documents the 5-agent dispatch
- [ ] 5 agent files exist in `claude-code/agents/`: `code-reviewer.md`, `security-auditor.md`, `tdd-sequence-auditor.md`, `context7-evidence-auditor.md`, `future-proofing-auditor.md`
- [ ] Each agent prompt is documented with: trigger conditions, scope, severity classification rules, expected output schema (CRITICAL/WARNING/INFO with file:line + impact + fix)
- [ ] Prototype validation: feed synthetic milestone diff to each agent in isolation; verify it catches L-005, L-006, L-007 historical examples
- [ ] `[task]-impl-review.md` template exists in `docs/templates/`

**Required Artefacts:**
- `claude-code/skills/verify-impl/SKILL.md` (NEW)
- `claude-code/agents/code-reviewer.md` (NEW)
- `claude-code/agents/security-auditor.md` (NEW)
- `claude-code/agents/tdd-sequence-auditor.md` (NEW)
- `claude-code/agents/context7-evidence-auditor.md` (NEW)
- `claude-code/agents/future-proofing-auditor.md` (NEW)
- `docs/templates/impl-review-template.md` (NEW)

**Tests:**
- Prototype: dispatch each agent against a synthetic milestone constructed from L-005 (two-mechanism `install.sh`) — verify code-reviewer flags it CRITICAL
- Prototype: dispatch each agent against L-006 commit range (cz bump CHANGELOG) — verify code-reviewer's "schema-breaking output" check flags it
- Prototype: dispatch tdd-sequence-auditor against `harden-aa-ma-plan` git log — verify PASS/FAIL verdict
- All prototype runs logged to `[task]-provenance.log` as `[ts] PROTOTYPE — <agent> — <verdict>`

**Rollback Strategy:** `git revert`; skill + agent files are additive — no other code depends on them yet until M5 wires them in.

**Risks:**
1. Code-reviewer false-positive rate too high → mitigation: prototype iteration; severity gating; dispute mechanism (Branch 4)
2. Context7-evidence-auditor too noisy on uv.lock churn → mitigation: scope narrowed to NEW deps + MAJOR bumps only (Branch 7b)
3. tdd-sequence-auditor mis-attributes milestone window → mitigation: explicit milestone-boundary commits identified via `[AA-MA Plan]` signature in commit footer

#### Step 4.1: Build minimal prototype of `verify-impl` skill (`Skill(prototype)` — UI/LOGIC branch: LOGIC)
- **Effort:** 1h
- **Complexity:** 60%
- **Acceptance:** Skeleton skill that dispatches a single test agent and returns structured output
- **Artefacts:** `claude-code/skills/verify-impl/SKILL.md` (initial draft)

#### Step 4.2: Prototype each agent prompt iteratively
- **Effort:** 3h
- **Complexity:** 80%
- **Acceptance:** Each of 5 agents catches its target lesson example (L-005, L-006, L-007); false-positive count documented in `[task]-context-log.md`
- **Artefacts:** 5 agent prompt files in `claude-code/agents/`

#### Step 4.3: Write impl-review template
- **Effort:** 1h
- **Complexity:** 40%
- **Acceptance:** Template covers all 5 agent output sections, severity table, override panel record
- **Artefacts:** `docs/templates/impl-review-template.md`

#### Step 4.4: Finalize skill SKILL.md with prototype findings
- **Effort:** 1h
- **Complexity:** 50%
- **Acceptance:** SKILL.md cites prototype evidence, documents budget modes, escape valves; provenance.log has `[ts] PROTOTYPE — verify-impl-skill — <verdict>`
- **Artefacts:** `claude-code/skills/verify-impl/SKILL.md`

---

### Milestone 5: §6.8 Integration into `/execute-aa-ma-milestone` + Delegation in `/execute-aa-ma-full`

- **Goal:** Wire Phase 6.8 between §6.7 (Engineering Standards HARD Gate) and §7 (Finalization Protocol). `/execute-aa-ma-full` delegates to milestone logic.
- **Effort:** 6h
- **Complexity:** **80%** ← HIGH COMPLEXITY — touches enforcement code; mid-stream behaviour
- **Mode:** HITL
- **Gate:** HARD
- **Baseline:** N/A — pure local code, no API exercised
- **Audit-Profile:** `full`
- **Critical-Path:** doc-count-drift

**Acceptance Criteria:**
- [ ] `execute-aa-ma-milestone.md` gains §6.8 between current §6.7 (line 481) and §7.1 (line 559)
- [ ] §6.8 invokes `/verify-impl` skill with the current milestone's `Audit-Profile`
- [ ] CRITICAL findings from any agent surface via `AskUserQuestion` (accept/dispute/defer) BEFORE §7.3 user authorization
- [ ] `execute-aa-ma-full.md` delegates §6.8 invocation to milestone command
- [ ] `AA_MA_AUDIT_BUDGET={low,off}` env var honored
- [ ] Grandfathering: plans with `Created:` < cutover skip §6.8 entirely (logged to provenance.log)
- [ ] E2E bats test: synthetic milestone with `Audit-Profile: full` triggers §6.8; with `Audit-Profile: docs-only` triggers only future-proofing agent

**Required Artefacts:**
- `claude-code/commands/execute-aa-ma-milestone.md` (EDIT — insert §6.8)
- `claude-code/commands/execute-aa-ma-full.md` (EDIT — delegate §6.8 to milestone)
- `tests/hooks/execute_aa_ma_milestone_phase_6_8.bats` (NEW)

**Tests:**
- `bats tests/hooks/execute_aa_ma_milestone_phase_6_8.bats` — cases: full-profile triggers all 5; docs-only triggers 1; grandfathered skips all; budget=off logs bypass
- Manual E2E: synthetic plan with `Created: 2026-06-01` → §6.8 fires; synthetic plan with `Created: 2026-04-01` → §6.8 grandfathered

**Rollback Strategy:** `git revert <M5-commit>`; milestone command reverts to v0.7.0 §6.7 → §7 flow.

**Risks:**
1. §6.8 fires on the meta-plan implementing it → mitigation: this plan's `Created: 2026-05-11` is pre-cutover; grandfathered by construction
2. CRITICAL override panel deadlocks user (no input mechanism inside execute flow) → mitigation: use existing AskUserQuestion pattern from §7.3 (already proven)
3. Budget escape valve abuse → mitigation: `AA_MA_AUDIT_BUDGET=off` always logs `[ts] AUDIT_BUDGET=off — bypassed §6.8` to provenance.log (auditable)

#### Step 5.1: Draft §6.8 section in `execute-aa-ma-milestone.md`
- **Effort:** 2h
- **Complexity:** 70%
- **Acceptance:** §6.8 inserted between §6.7 and §7.1; references `/verify-impl` skill; documents Audit-Profile dispatch logic
- **Artefacts:** `claude-code/commands/execute-aa-ma-milestone.md`

#### Step 5.2: Wire CRITICAL override panel via `AskUserQuestion`
- **Effort:** 1.5h
- **Complexity:** 70%
- **Acceptance:** §6.8 documents accept/dispute/defer panel; defer creates new sub-task in `tasks.md`; dispute logged to `impl-review.md`
- **Artefacts:** `claude-code/commands/execute-aa-ma-milestone.md`

#### Step 5.3: Delegate from `execute-aa-ma-full.md`
- **Effort:** 30min
- **Complexity:** 40%
- **Acceptance:** Full command's per-milestone loop invokes §6.8 via delegation; no logic duplication
- **Artefacts:** `claude-code/commands/execute-aa-ma-full.md`

#### Step 5.4: E2E bats tests
- **Effort:** 2h
- **Complexity:** 70%
- **Acceptance:** All 4 trigger scenarios pass (full, docs-only, grandfathered, budget=off)
- **Artefacts:** `tests/hooks/execute_aa_ma_milestone_phase_6_8.bats`

---

### Milestone 6: Version Bump v0.7.0 → v0.8.0 + README/CHANGELOG Sweep

- **Goal:** Cut v0.8.0 release. Hardcoded-count sweep, CHANGELOG entry under `cz bump` rules (NOT manually edited per L-003), README updates, and final symlink deploy verification.
- **Effort:** 3h
- **Complexity:** 50%
- **Mode:** HITL
- **Gate:** HARD
- **Baseline:** N/A — pure local code, no API exercised
- **Audit-Profile:** `infra`
- **Critical-Path:** version-pipeline, doc-count-drift

**Acceptance Criteria:**
- [ ] `pyproject.toml` version 0.7.0 → 0.8.0 via `cz bump` (NOT manual edit per L-003)
- [ ] CHANGELOG.md regenerated by `cz bump`; post-bump manual read per L-006 confirms prose preserved (amend if not)
- [ ] README.md skill count updated; doc-count-drift sweep across `docs/spec/claude-code-foundations.md`, `docs/spec/aa-ma-quick-reference.md`, `SECURITY.md` confirms no stale counts
- [ ] `scripts/install.sh --dry-run | grep security-static-check.sh` returns the new symlink line
- [ ] Git tag `v0.8.0` pushed; release notes include §6.8 anatomy reference
- [ ] L-006 post-bump verification protocol followed: read CHANGELOG before `git push --tags`

**Required Artefacts:**
- `pyproject.toml` (EDIT via cz bump)
- `CHANGELOG.md` (EDIT via cz bump; post-bump amend if needed per L-006)
- `README.md` (EDIT — skill count, command count)
- `docs/spec/claude-code-foundations.md` (EDIT — sweep)
- `docs/spec/aa-ma-quick-reference.md` (EDIT — sweep)
- `SECURITY.md` (EDIT — sweep)

**Tests:**
- `uv run pytest` — full default suite passes
- `uv run ruff check src/` — clean
- `bats tests/hooks/` — all pass (M2 + M5 suites integrated)
- `scripts/install.sh --dry-run` — every new asset (hook, skill, agents, templates) appears
- Post-bump manual: `head -40 CHANGELOG.md` to confirm v0.8.0 entry has prose under Feat/Test/Docs sections

**Rollback Strategy:**
- Pre-tag: `git reset --hard HEAD~1` and re-run cz bump if CHANGELOG drift detected
- Post-tag: `git tag -d v0.8.0 && git push origin :refs/tags/v0.8.0` then revert commits

**Risks:**
1. `cz bump` strips CHANGELOG prose (L-006 pattern) → mitigation: post-bump read + amend + retag BEFORE push
2. Hardcoded-count drift after M2-M5 additions → mitigation: Critical-Path: doc-count-drift; sweep `grep -rn "\b1[0-9]\b skill" claude-code/ docs/ README.md`
3. `scripts/install.sh` misses a new asset → mitigation: explicit `--dry-run | grep` per asset added in M2-M5

#### Step 6.1: Hardcoded-count sweep across docs
- **Effort:** 45min
- **Complexity:** 40%
- **Acceptance:** All stale counts replaced; verified via grep for old counts
- **Artefacts:** README.md, foundations.md, quick-reference.md, SECURITY.md

#### Step 6.2: Run `cz bump`
- **Effort:** 30min
- **Complexity:** 40%
- **Acceptance:** version 0.8.0; new git tag; CHANGELOG entry generated
- **Artefacts:** pyproject.toml, CHANGELOG.md, .git/refs/tags/v0.8.0

#### Step 6.3: Post-bump CHANGELOG verification (L-006 protocol)
- **Effort:** 30min
- **Complexity:** 50%
- **Acceptance:** CHANGELOG v0.8.0 entry has prose; if stripped, amend + retag BEFORE pushing
- **Artefacts:** CHANGELOG.md (amended if needed)

#### Step 6.4: Install dry-run verification
- **Effort:** 15min
- **Complexity:** 20%
- **Acceptance:** `--dry-run` output shows symlinks for security-static-check.sh, verify-impl/, all 5 agents, impl-review-template.md
- **Artefacts:** (verification only)

#### Step 6.5: Push tag + release notes
- **Effort:** 30min
- **Complexity:** 30%
- **Acceptance:** `git push origin v0.8.0` succeeds; GitHub/GitLab release notes link to ADR-0005
- **Artefacts:** (release-only; no file changes)

---

## Dependencies & Assumptions

### Dependencies

| Dependency | Class | Notes |
|-----------|-------|-------|
| `commitizen >= 3.0` (already installed) | Required | cz bump for version + CHANGELOG |
| `bats-core` (system package) | Dev-only | `sudo apt-get install -y bats` per CLAUDE.md |
| `shellcheck` (system package) | Dev-only | Validates hook scripts |
| `uv >= 0.7` (already installed) | Required | Runs pytest + ruff |
| `Skill(prototype)` (ADR-0003) | Required | M4 prototype phase |
| Existing `aa-ma-validator` agent | Required | M5 reuses for Tier 2 content checks |
| Existing `Skill(plan-verification)` | Required | M3 extends Angle 6 |
| Existing `Skill(impact-analysis)` | Required | §6.8 invokes before user approval |

### Assumptions

1. **`Created:` front-matter is consistently present in v0.5.0+ plans** — verified for `harden-aa-ma-plan`; corpus test in M3.4 confirms across all completed plans. If wrong: grandfathering falls back to "absent → grandfathered" rule (still safe).
2. **`cz bump` will work cleanly under M6** — verified by recent v0.7.0 release (commit 480dd3f). If wrong: rollback via Step 6.3 amend protocol (L-006).
3. **Existing `AskUserQuestion` pattern works inside execute-aa-ma-milestone flow** — verified by §7.3 user authorization already using it. If wrong: fallback to writing CRITICAL findings to `impl-review.md` and pausing for manual file inspection.
4. **5 parallel agents fit in orchestrator context** — token estimate 100-200k per milestone close. If wrong: `AA_MA_AUDIT_BUDGET=low` forces sequential mode.
5. **No external API exercised in any milestone** — confirmed by pure-local nature; all `Baseline:` fields = N/A.
6. **Plan-verification structural check is the right enforcement layer for Audit-Profile presence** — verified Angle 6 already handles Engineering Standards element #12 with identical pattern.

---

## Next Action

**Do this first:** After ExitPlanMode approval, dispatch the `aa-ma-scribe` agent to create `.claude/dev/active/post-impl-adversarial-review/` with 5 files (plan.md, reference.md, context-log.md, tasks.md, provenance.log) using this plan file as the source of truth. Plus optional verification.md (the grilling output) and tests.yaml (M2 + M3 test specs).

**Update:** REFERENCE (extract immutable facts: file paths, ADR-0005 number, version-target v0.8.0, canonical TDD-Waiver values, Audit-Profile values, env-var names) and TASKS (create HTP nodes for all 6 milestones with Status: PENDING, Mode, Gate, Audit-Profile fields).

---

## Engineering Standards Declaration (Element #12)

All 6 themes from `claude-code/rules/engineering-standards.md` materially apply to this work because we are literally building the post-impl verification system.

| Theme | Rationale |
|---|---|
| **1. Verification & Truth** | Entire plan's purpose is to enforce empirical verification post-impl. M2 declares `Critical-Path: hook-modification`; M6 declares `Critical-Path: version-pipeline`; M5 declares `Critical-Path: doc-count-drift`. M4 declares `Prototype-Required: YES` for agent prompt iteration. |
| **2. Development Principles** | TDD-first explicitly declared in M2.1 and M3.1 (write tests RED first); KISS in agent-prompt brevity (no over-engineering); DRY in M5.3 (delegation, not duplication); SOLID/SOC in security split (hook = mechanical layer, agent = semantic layer). |
| **3. Reasoning & Planning** | 6-branch grilling (Q1-Q7b) applied Socratic questioning and first-principles to surface the structural asymmetry. Subagent dispatch used in pre-flight (3 parallel Explore agents for grounding). Decisions traced in `[task]-context-log.md`. |
| **4. Safety & Continuity** | Grandfathering by `Created:` date preserves all in-flight and completed plans (non-breaking). Lessons applied: L-001 (external URL → Context7 evidence), L-005 (KISS → code-reviewer mechanism duplication), L-006 (schema regression → code-reviewer schema-breaking check + post-bump amend protocol), L-007 (scope discipline → code-reviewer Required Artefacts check). |
| **5. Execution Checklist** | Each milestone has falsifiable acceptance criteria (no banned phrases). Critical-Path evidence required on M2/M5/M6. Prototype-Required on M4 with `Skill(prototype)` LOGIC branch. Sub-step Result Log mandatory per L-080. |
| **6. Sync & Commit Discipline** | Every milestone close commits via `/execute-aa-ma-milestone` with `[AA-MA Plan] post-impl-adversarial-review` footer. M6 follows L-003 (never manually edit cz-bump headings) and L-006 (post-bump verification). |

---

## Tests for the Plan Itself (Verification Plan)

End-to-end empirical tests that prove this work actually solves the gap:

1. **Positive case:** Create a synthetic plan with `Created: 2026-06-01` (post-v0.8.0), milestone with `Audit-Profile: full`, milestone touching `src/`. Run `/execute-aa-ma-milestone`. Confirm §6.8 fires, all 5 agents dispatched, results aggregate to `impl-review.md`.
2. **TDD pass case:** Synthetic plan where test commit precedes src commit → tdd-sequence-auditor returns PASS.
3. **TDD fail case:** Synthetic plan where src commit precedes test commit, no `TDD-Waiver` → CRITICAL → blocks user approval.
4. **TDD waived case:** Synthetic plan with `TDD-Waiver: refactor` → returns WAIVED.
5. **Grandfathering case:** Plan with `Created: 2026-04-15` (pre-v0.8.0) → §6.8 does not fire.
6. **Budget escape case:** `AA_MA_AUDIT_BUDGET=off` → §6.8 skipped, `provenance.log` records the bypass.
7. **CRITICAL override panel:** code-reviewer flags mechanism duplication → user dispatched `AskUserQuestion` → dispute → logged, no block.
8. **L-005 regression test:** Feed synthetic milestone touching install.sh with two-mechanism pattern → code-reviewer flags CRITICAL "mechanism duplication" with file:line.
9. **L-006 regression test:** Feed synthetic milestone touching CHANGELOG.md with stripped prose → code-reviewer flags CRITICAL "schema-breaking output regression".
10. **L-007 regression test:** Feed synthetic milestone with diff outside `Required Artefacts` list → code-reviewer flags CRITICAL "scope discipline".
11. **Self-bootstrap test:** This plan (`Created: 2026-05-11`) is grandfathered; §6.8 does NOT fire on its own milestones. Confirmed by construction.

---

## Critical Files to Modify (consolidated)

**New files:**
- `claude-code/skills/verify-impl/SKILL.md`
- `claude-code/agents/code-reviewer.md`
- `claude-code/agents/security-auditor.md`
- `claude-code/agents/tdd-sequence-auditor.md`
- `claude-code/agents/context7-evidence-auditor.md`
- `claude-code/agents/future-proofing-auditor.md`
- `claude-code/hooks/security-static-check.sh`
- `docs/templates/impl-review-template.md`
- `docs/adr/0005-post-impl-adversarial-review.md`
- `src/aa_ma/plan_parsers.py`
- `tests/codemem/test_audit_profile_parser.py`
- `tests/codemem/test_tdd_waiver_parser.py`
- `tests/codemem/test_corpus_grandfathering.py`
- `tests/hooks/security_static_check.bats`
- `tests/hooks/execute_aa_ma_milestone_phase_6_8.bats`

**Modified files:**
- `claude-code/commands/execute-aa-ma-milestone.md` — insert §6.8 between L-481 and L-559
- `claude-code/commands/execute-aa-ma-full.md` — delegate §6.8 to milestone
- `claude-code/skills/plan-verification/SKILL.md` — Angle 6 adds Audit-Profile + TDD-Waiver structural checks
- `claude-code/rules/engineering-standards.md` — add canonical `TDD-Waiver` enum (mirrors `Critical-Path:` pattern)
- `docs/spec/aa-ma-specification.md` — document §6.8 and `[task]-impl-review.md` file type
- `docs/adr/INDEX.md` — list ADR-0005
- `scripts/install.sh` — register `security-static-check.sh` and `verify-impl/` and 5 agents
- `CHANGELOG.md` — feat entry via `cz bump` (NOT manual)
- `pyproject.toml` — version 0.7.0 → 0.8.0 via `cz bump`
- `README.md` — skill count, agent count, hook count
- `docs/spec/claude-code-foundations.md` — count sweep
- `docs/spec/aa-ma-quick-reference.md` — count sweep
- `SECURITY.md` — count sweep

---

## Reuses Existing Patterns (no reinvention)

- **Grandfathering by `Created:` date** — `claude-code/skills/plan-verification/SKILL.md` Angle 6 already does this for Engineering Standards element #12 (v0.5.0 cutover)
- **Canonical-enum + ADR-for-new-values** — `Critical-Path:` enum in `engineering-standards.md` §1 already operates this way
- **Bypass env vars** — `AA_MA_HOOKS_DISABLE=1` master switch already present
- **HARD gate refusal mechanics** — `aa-ma-commit-signature.sh` exit-2 pattern for PreToolUse hooks
- **Adversarial agent dispatch** — `plan-verification/SKILL.md` 6-angle pattern (parallel agents → aggregated severity)
- **Audit trail file** — `[task]-verification.md` precedent (optional file pattern)
- **AskUserQuestion in execution flow** — `execute-aa-ma-milestone.md` §7.3 already uses for user authorization

---

## Effort Total

| Milestone | Effort | Complexity | Mode | Gate |
|---|---|---|---|---|
| M1: ADR-0005 + spec | 2h | 30% | HITL | SOFT |
| M2: security hook | 4h | 60% | AFK | HARD |
| M3: parsers | 5h | 70% | AFK | HARD |
| M4: skill + 5 agents | 6h | **80% — HIGH** | HITL | HARD |
| M5: §6.8 integration | 6h | **80% — HIGH** | HITL | HARD |
| M6: release v0.8.0 | 3h | 50% | HITL | HARD |
| **Total** | **26h** | — | — | — |

M4 and M5 are HIGH COMPLEXITY (>=80%) and require human review at each step boundary.

---

## Open Questions for User Before Proceeding

None — all 8 branches grilled and resolved. Plan is execution-ready upon ExitPlanMode approval.
