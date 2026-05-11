# 0005. Post-Impl Adversarial Review (Phase 6.8 + /verify-impl)

**Status:** Accepted (2026-05-11)
**Date:** 2026-05-11
**Deciders:** Stephen Newhouse, Claude (grill-with-docs interview)
**Tags:** `workflow`, `verification`, `aa-ma`, `release-v0.8.0`

## Context and Problem Statement

aa-ma-forge has substantial **pre-execution rigor**: 5-phase `/aa-ma-plan` workflow, 6-angle `plan-verification` skill (Phase 4.5, BLOCKING), 12-element Planning Standard with Engineering Standards Declaration (ADR-0001), 9 HARD gates at milestone close (Tier 1/2 existence, acceptance criteria, dependencies, impact analysis, tests, eng-standards §6.7, sub-step sync, HARD-gate artifact, user approval).

By contrast, **post-execution rigor is thin**. The only post-impl review is the §6.6 *Post-Milestone Simplification Review* — which is SOFT (findings advisory only) and explicitly skippable via `--skip-simplify`. No code review. No security review. No TDD-sequence audit. No KISS/SOLID/SOC audit. No verification that Context7 was consulted when external libraries were added.

The project's own lesson history confirms this asymmetry bites:

| Lesson | Class | What was missed |
|---|---|---|
| **L-005** | KISS / mechanism duplication | `scripts/install.sh` had two parallel symlink mechanisms; M2.4 registered the event hook but forgot the explicit symlink block. Post-install `/aa-ma-plan` failed with `No such file or directory`. |
| **L-006** | Schema-breaking output regression | `cz bump` stripped CHANGELOG prose (Test/Docs/Plan-close subsections) silently; caught only by manual post-bump read (commit 00d6519 → 480dd3f). |
| **L-007** | Scope discipline | M5 format-fix step reformatted 29 pre-existing test files outside declared scope, nearly bundled into release commit. |

v0.7.0 release notes were the **first** to explicitly claim "TDD-first" — implying prior releases were impl-first by default. The discipline lived in the user's head, not in any structural gate.

**Question:** How do we close the post-execution gap symmetric to pre-execution rigor, without breaking in-flight plans, without rubber-stamping subjective findings, and without burning tokens on milestones where the rigour is overkill?

## Decision Drivers

- **Symmetry with pre-execution rigor** — plan-verification runs 6 angles before code lands; impl deserves equivalent post-landing scrutiny
- **Don't break in-flight plans** — grandfathering by `Created:` date is the established precedent (ADR-0001 v0.5.0 cutover for Engineering Standards Declaration)
- **User autonomy preserved** — subjective findings (code-reviewer judgement calls) must have a dispute path; CRITICAL ≠ tyranny
- **Token discipline** — five parallel agents per milestone is meaningful cost; opt-in per milestone, not always-on
- **Reuse existing skill patterns** — adversarial agent dispatch (`plan-verification`), grandfathering (`Created:` date), canonical enums + ADR-for-new-values (`Critical-Path:` pattern), bypass env vars (`AA_MA_HOOKS_DISABLE`)
- **Mechanical vs semantic separation** — pattern-detection (regex) belongs in hooks (free); semantic judgement belongs in agents (worth the tokens)
- **Self-bootstrap safety** — the plan implementing this feature must NOT trip the new gates on itself; grandfathering by construction

## Considered Options

1. **Add Phase 6.8 + `/verify-impl` skill (5 parallel audit agents)** — symmetric to plan-verification, blocks user approval on CRITICAL
2. **Strengthen existing §6.6 simplification review only** — remove `--skip-simplify`, add CRITICAL severity, add security + TDD agents to the existing parallel-3 dispatch
3. **Re-purpose `/verify-plan` for impl mode** — add `--mode=impl` flag; re-run 6 angles against diff post-COMPLETE; plus a PreToolUse hook blocking commits without code-review provenance entry
4. **Leave asymmetry intentional** — argue post-impl review is a HUMAN responsibility (§7.3 user approval); document rationale in this ADR

## Decision Outcome

**Chosen:** Option 1 — Add Phase 6.8 + `/verify-impl` skill (5 parallel audit agents).

**Rationale:**

- Option 1 captures the **structural symmetry** that addresses the root asymmetry (pre-execution adversarial / post-execution trust-based) directly.
- Option 2 reuses §6.6 but inherits its limitations (no separate audit trail file, mixed-purpose skill, harder to evolve). The simplification review concept itself is too narrow for the full audit surface.
- Option 3 (re-purpose `/verify-plan`) couples two distinct workflows into one skill; future drift between plan-mode and impl-mode would create maintenance burden.
- Option 4 (leave it) is incompatible with the lesson history: L-005, L-006, L-007 are all cases where a human review would have caught the issue but did not, because no structural prompt asked the right question at the right time.

## Pros and Cons of the Options

### Option 1: Phase 6.8 + /verify-impl skill (chosen)

- ✅ Structural symmetry: plan-verification ↔ verify-impl
- ✅ Separate audit trail (`[task]-impl-review.md`) — clear provenance, evolvable
- ✅ Five focused agents > one mixed agent: code-reviewer, security-auditor, tdd-sequence-auditor, context7-evidence-auditor, future-proofing-auditor
- ✅ Plan-declared `Audit-Profile` per milestone caps token cost
- ✅ Grandfathered by `Created:` date — zero impact on in-flight plans
- ❌ New skill + 5 new agent files (artefact count grows)
- ❌ Subjective findings require user-override mechanism (handled via accept/dispute/defer panel)

### Option 2: Strengthen §6.6 only

- ✅ Cheapest in artefact count
- ❌ No separate audit trail file → poor provenance
- ❌ Mixed-purpose skill (simplification + security + TDD) violates single-responsibility
- ❌ `--skip-simplify` flag would need removal, creating breaking change for v0.7.x users

### Option 3: Re-purpose /verify-plan for impl mode

- ✅ Reuses existing 6-angle skill
- ❌ Plan-mode and impl-mode are subtly different; coupling forces compromises in both
- ❌ Adding `--mode=impl` flag breaks symmetry of the skill name (it's no longer "verify the plan")

### Option 4: Leave asymmetry intentional

- ✅ Zero new artefacts
- ❌ Lesson history (L-005, L-006, L-007) is direct evidence this approach fails
- ❌ Discipline that lives in human attention is the first thing to slip under deadline pressure

## Sub-Decisions

This decision was reached through a 7-question structured grilling interview (Q1–Q7b) recorded in the plan file. Eight related sub-decisions are bundled here for traceability:

| ID | Sub-decision | Rationale |
|----|-------|---|
| **D1** | Phase 6.8 + new `/verify-impl` skill | Structural symmetry; separate audit trail; evolvable |
| **D2** | Plan-declared `Audit-Profile` per milestone (`full | code-only | docs-only | infra | custom`) | Token discipline; author confirms scope per milestone |
| **D3** | Strict TDD commit-ordering with canonical `TDD-Waiver` values | Mechanically auditable; canonical waivers respect refactor / docs-only / prototype / hotfix-emergency / tooling-config |
| **D4** | Severity-gated CRITICAL override panel (accept/dispute/defer) | Preserves user autonomy; disputes logged as "convention learned" for next run |
| **D5** | `Audit-Profile` IS the budget; `AA_MA_AUDIT_BUDGET={low,off}` global escape valve | Budget knob is the profile; one global env var for context-pressured sessions; logged to provenance.log when used |
| **D6** | Grandfather by `Created:` date | Mirrors v0.5.0 precedent (ADR-0001 Engineering Standards Declaration element #12) |
| **D7a** | Security: mechanical → `security-static-check.sh` hook (commit-time, free); semantic → `security-auditor` agent (milestone close) | Mirrors `aa-ma-commit-drift.sh` / `aa-ma-validator` split; catches issues before commit when possible |
| **D7b** | Context7-evidence-auditor scope: new PyPI deps + MAJOR version bumps only | Skips minor/patch (uv.lock churn) and transitive deps; L-006-class patch regressions caught by code-reviewer's "schema-breaking output" check |

## Consequences

**Positive:**
- Lesson regressions (L-005, L-006, L-007) become structurally detectable — each maps to a specific agent's mandatory pattern check.
- Pre-execution and post-execution discipline are now symmetric. Plan rigor matches impl rigor.
- Audit trail (`[task]-impl-review.md`) joins `[task]-verification.md` as an optional but consistent file type — extends the AA-MA file vocabulary cleanly.
- TDD discipline gets a mechanical signal (not just project culture) — `tdd-sequence-auditor` checks commit-ordering within the milestone window.
- Security: mechanical checks fire at commit time (earliest possible); semantic checks fire at milestone close (when context is richest).
- New plans get the discipline by default; legacy plans are grandfathered, so no migration cost.

**Negative:**
- Token cost: a `full`-profile milestone close burns 100–200k tokens running 5 parallel agents. Mitigated by `Audit-Profile` per-milestone scoping and `AA_MA_AUDIT_BUDGET=low` global escape valve.
- Six new agent files + one new skill + one new hook expand the plugin surface. Mitigated by reusing existing dispatch patterns (no reinvention).
- Plan-verification structural check gains two new fields to enforce (`Audit-Profile`, `TDD-Waiver`). Adds complexity to Angle 6 logic; offset by direct precedent in element #12 enforcement.
- CRITICAL override panel introduces accept/dispute/defer triage — non-trivial user-facing flow inside `/execute-aa-ma-milestone`. Mitigated by reusing existing `AskUserQuestion` pattern from §7.3.

**Neutral:**
- §6.6 simplification review continues to operate; §6.8 complements rather than replaces it. (Future ADR may deprecate §6.6 once §6.8 is proven; not in scope here.)
- The plan implementing this feature has `Created: 2026-05-11` (pre-v0.8.0 release tag) — so §6.8 does NOT fire on its own milestones. Self-bootstrap safety by construction.

## Implementation Notes

**Execution model:** AA-MA workflow at `.claude/dev/active/post-impl-adversarial-review/`. Six milestones M1–M6:

- **M1** — this ADR + `aa-ma-specification.md` §6.8 anatomy subsection (docs-only)
- **M2** — `security-static-check.sh` PreToolUse hook (TDD-first, bats coverage, mirrors `aa-ma-commit-drift.sh`)
- **M3** — `Audit-Profile` + `TDD-Waiver` parsers in `Skill(plan-verification)` Angle 6 (TDD-first, pytest coverage, corpus test against completed plans)
- **M4** — `/verify-impl` skill + 5 agent prompts (Prototype-Required: YES via `Skill(prototype)` LOGIC branch)
- **M5** — Phase 6.8 integration into `execute-aa-ma-milestone.md` between §6.7 (L-481) and §7.1 (L-559); `execute-aa-ma-full.md` delegation; CRITICAL override panel via `AskUserQuestion`
- **M6** — Version bump v0.7.0 → v0.8.0 via `cz bump`; CHANGELOG verification per L-006 protocol; hardcoded-count sweep (Critical-Path: doc-count-drift)

**Critical files affected:**

| Type | Path |
|------|------|
| New ADR (this file) | `docs/adr/0005-post-impl-adversarial-review.md` |
| Amended ADR INDEX | `docs/adr/INDEX.md` |
| Amended spec | `docs/spec/aa-ma-specification.md` (new §6.8 subsection) |
| New skill | `claude-code/skills/verify-impl/SKILL.md` |
| New agents | `claude-code/agents/code-reviewer.md`, `security-auditor.md`, `tdd-sequence-auditor.md`, `context7-evidence-auditor.md`, `future-proofing-auditor.md` |
| New hook | `claude-code/hooks/security-static-check.sh` |
| New template | `docs/templates/impl-review-template.md` |
| New parser | `src/aa_ma/plan_parsers.py` |
| Amended skill | `claude-code/skills/plan-verification/SKILL.md` (Angle 6 extended with `Audit-Profile` + `TDD-Waiver` checks) |
| Amended command | `claude-code/commands/execute-aa-ma-milestone.md` (insert §6.8 between L-481 and L-559) |
| Amended command | `claude-code/commands/execute-aa-ma-full.md` (delegate §6.8) |
| Amended rule | `claude-code/rules/engineering-standards.md` (add canonical `TDD-Waiver` enum) |
| Amended top-level | `README.md`, `CHANGELOG.md` (via cz bump), `SECURITY.md`, `pyproject.toml`, `docs/spec/claude-code-foundations.md`, `docs/spec/aa-ma-quick-reference.md` |

**Canonical enums (validated by `Skill(plan-verification)` Angle 6):**

- `Audit-Profile`: `full | code-only | docs-only | infra | custom`
- `TDD-Waiver`: `refactor | docs-only | prototype | hotfix-emergency | tooling-config`
- `Critical-Path` (unchanged from ADR-0001): `auth-flow | data-xform | external-api | version-pipeline | doc-count-drift | hook-modification`

Novel values for any of the three enums require a plan + new ADR (matches the pattern established in ADR-0001 §1).

**Cutover:** Plans with `Created: < v0.8.0 release commit date` are grandfathered — §6.8 does not fire; `Audit-Profile` absence is not flagged by `plan-verification`. Mirrors the v0.5.0 cutover precedent for Engineering Standards Declaration element #12.

**Status transitions:** This ADR will move from `Accepted` to `Implemented` once M5 (Phase 6.8 integration) ships in main.

## References

- Working plan file (full grilling trail Q1–Q7b): `~/.claude/plans/and-brainstorm-with-me-sparkling-acorn.md`
- AA-MA artifacts (execution-ready form): `.claude/dev/active/post-impl-adversarial-review/`
- Related ADRs:
  - [ADR-0001](0001-engineering-standards-architecture.md) — Engineering Standards Architecture (established the canonical-enum pattern, Critical-Path enum, grandfathering precedent)
  - [ADR-0003](0003-prototype-adoption.md) — `Skill(prototype)` LOGIC + UI branches (referenced by M4)
- Lessons motivating this work:
  - L-001 (External URL First Principle) → Context7 evidence audit
  - L-005 (install.sh symlinks) → code-reviewer mechanism duplication check
  - L-006 (cz bump CHANGELOG) → code-reviewer schema-breaking output check + M6 post-bump verification protocol
  - L-007 (sole-dev-merge format pass) → code-reviewer scope discipline check
- AA-MA specification: `docs/spec/aa-ma-specification.md` (§6.8 anatomy added in M1)
- AA-MA quick reference: `docs/spec/aa-ma-quick-reference.md`
- Plan-verification skill (extended in M3): `claude-code/skills/plan-verification/SKILL.md`
- MADR format: https://adr.github.io/madr/
