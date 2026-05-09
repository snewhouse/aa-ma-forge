# 0001. Engineering Standards Architecture for aa-ma-plan Workflows

**Status:** Accepted
**Date:** 2026-05-09
**Deciders:** Stephen Newhouse, Claude (grill-with-docs interview)
**Tags:** `workflow`, `governance`, `aa-ma`, `release-v0.5.0`

## Context and Problem Statement

The aa-ma-forge plugin already has substantial workflow scaffolding for plan-driven development: 5-phase `/aa-ma-plan` command, 6-angle `plan-verification` skill (Phase 4.5, BLOCKING), 11-element Planning Standard, HARD/SOFT milestone gates, HITL/AFK execution modes. However, it is light on **codified engineering principles** that govern *how* a plan is executed once authored.

Engineering principles such as TDD, KISS, DRY, SOLID, SOC, first-principles thinking, Socratic questioning, empirical verification, prototype-first, and lessons-learned do appear in the plugin — but only as one-line mentions in `claude-code/commands/aa-ma-plan.md:30,116,756-761` (Phase 2 brainstorm namecheck) and `claude-code/skills/operational-constraints/SKILL.md`. They are not enforced gates, not consolidated into a single doctrine, not exposed as deliverables, and not verified during execution.

A separate problem: the user's existing global `~/.claude/CLAUDE.md` already requires these principles for the user's own work — but those rules are private and not exposed to consumers of this plugin.

**Question:** How do we codify and enforce engineering standards across `/aa-ma-plan` and `/execute-aa-ma-*` workflows in this plugin without duplicating existing skills, bloating phase numbering, or creating drift across redundant artifacts?

## Decision Drivers

- **Avoid skill competition** — the plugin already has `operational-constraints`, `plan-verification`, `impact-analysis`, `system-mapping`, and `dispatching-parallel-agents` skills covering parts of the territory. A new skill would compete and drift.
- **Avoid phase renumbering churn** — phase numbers (1, 2, 3, 4, 4.5, 5) are referenced in commands, skills, specs, and prompts. Inserting a new phase ripples across 4+ files.
- **Minimize hardcoded-count drift** — the plugin's own `doc-drift-checks.md` Tier 6 detector catches stale counts; multi-artifact designs create more touchpoints than single-source designs.
- **Make standards explicit, not implicit** — the goal is a documented, verifiable contract, not aspirational guidance.
- **Step-light, milestone-rigorous** — atomic AA-MA steps should not pay heavy ceremony tax; milestone gates can.
- **Preserve existing AA-MA conventions** — Sub-Step Sync Rule (L-080–L-082), `aa-ma-commit-drift.sh` post-commit hook, HARD/SOFT gate format must continue to work.

## Considered Options

1. **Rule + workflow integration** — single rule file as source of truth, referenced by aa-ma-plan and execute-aa-ma-* commands. No new skill, no new phase.
2. **New dedicated skill** — `claude-code/skills/engineering-standards/SKILL.md` invoked explicitly during planning Phase 2 and per-step execution.
3. **Extend aa-ma-plan-workflow skill in-place** — bake standards directly into the workflow skill's existing phases.
4. **Multi-artifact: rule + skill + new workflow phase (classic)** — comprehensive treatment with three artifacts and a new phase.
5. **Sharper multi-artifact** — one new doctrine rule + amendments to existing skills + extension to existing planning standard. No new skill, no new phase, no skill competition.

## Decision Outcome

**Chosen:** Option 5 — Sharper multi-artifact.

**Rationale:**

- Option 5 captures the layered defense-in-depth value of a multi-artifact approach (rule auto-loads, skill amendments enforce, planning standard requires declaration) **without** the drift cost of three redundant artifacts.
- Option 4 (classic multi-artifact) would create a 14th skill that duplicates four existing skills (`operational-constraints`, `plan-verification`, `impact-analysis`, `system-mapping`) and shifts phase numbering everywhere phase numbers appear (4+ files).
- Options 1 and 3 are too thin — the standards become aspirational rather than enforced.
- Option 2 alone fails the "always-loaded" requirement; users reading the rule file at session start would still need to invoke the skill explicitly.

## Pros and Cons of the Options

### Option 5: Sharper multi-artifact (chosen)

- ✅ Single doctrine artifact (`engineering-standards.md`) — one source of truth, one drift point
- ✅ No phase renumbering — extends existing 5+4.5 phase structure unchanged
- ✅ No skill competition — amends `operational-constraints` and `plan-verification` rather than duplicating them
- ✅ Layered enforcement: rule (always-loaded) + skill amendments (active) + planning standard #12 (mandatory)
- ❌ More edits to existing files — 5+ files modified (skills, commands, rule, spec, templates)
- ❌ Each amendment must be careful not to bloat the host artifact (cap +20 lines per skill)

### Option 4: Classic multi-artifact

- ✅ Cleanest separation between rule, skill, and phase — most discoverable
- ❌ Drift across three artifacts is near-certain (per repo's own L-052 architectural deficiency rule)
- ❌ Phase renumbering ripples across 4+ files
- ❌ New skill competes with 4 existing skills
- ❌ Hardcoded count touchpoints: skills (13→14), rules (1→2), README/CHANGELOG/foundations/quick-reference/SECURITY

### Option 1: Rule + workflow integration

- ✅ Smallest install footprint
- ❌ No active enforcement — rule is read-only doctrine, no gate triggers compliance
- ❌ Standards become aspirational

### Option 2: New dedicated skill

- ✅ Discoverable via `Skill()` tool
- ❌ Requires explicit invocation; standards not auto-loaded
- ❌ Duplicates `operational-constraints` and `plan-verification`

### Option 3: Extend aa-ma-plan-workflow in-place

- ✅ Simplest deployment
- ❌ Standards only available inside `/aa-ma-plan` — no reach into `/execute-aa-ma-*` or ad-hoc work
- ❌ Bloats the workflow skill; reduces single-responsibility

## Sub-Decisions

The sharper multi-artifact decision was reached through a structured grilling interview. Eight related sub-decisions are bundled here for traceability:

| ID | Sub-decision | Rationale |
|----|-------|---|
| **D1** | Sharper multi-artifact (above) | Avoids skill competition, preserves phase numbering, single doctrine source |
| **D2** | Tiered enforcement: step-level ADVISORY + milestone-level HARD/SOFT | Step-light keeps atomic steps fast; milestone-rigorous catches drift before it compounds |
| **D3** | Planning Standard 11 → 12 elements; element #12 = "Engineering Standards Declaration" | Explicit declaration > implicit assumption; detected by extending plan-verification Angle 6 |
| **D4** | Cheap inline lessons scan in Phase 1 | ~30s overhead; reads `docs/lessons.md` (if present) + `git log --grep="revert\|fix\|hotfix"` + top-3 most recent completed context-logs; no subagent |
| **D5** | Prototype/empirical/critical-path evidence in `provenance.log` + per-task flags (`Prototype-Required:`, `Critical-Path:`) | Conditional triggering; no new file type; reuses existing audit ledger |
| **D6** | Sync & commit cadence: milestone-end HARD gate only | Lowest ceremony; existing `aa-ma-commit-drift.sh` hook covers post-commit drift |
| **D7** | Introduce ADR convention (this directory) | All three ADR criteria pass: hard to reverse, surprising without context, real trade-off |
| **D8** | Single coordinated minor bump v0.4.0 → v0.5.0 | Matches existing CHANGELOG style; one tag, one CI run, one foundations doc count update |

## Consequences

**Positive:**
- One doctrine artifact (`claude-code/rules/engineering-standards.md`) — minimal drift surface.
- Existing skills absorb runtime gates without new artifacts.
- Per-task `Prototype-Required:` and `Critical-Path:` flags allow conditional enforcement without ceremony tax on trivial steps.
- Milestone HARD gate refuses COMPLETE while git is dirty — addresses the "AA-MA in sync, commit often" requirement structurally.
- Planning Standard element #12 makes engineering posture an explicit, verifiable plan output.
- ADR convention (`docs/adr/`) is now available for future architectural decisions.

**Negative:**
- 11 → 12 element bump touches 6+ files; mitigated by doc-drift Tier 6 detector run during M3 HARD gate.
- Skill amendments must be tightly capped (+20 lines max) to avoid bloating `operational-constraints` and `plan-verification`.
- The sub-step sync rule (L-080–L-082) gains a new precondition (`git status` clean for AA-MA files) — may interact with existing tooling.

**Neutral:**
- `aa-ma-commit-drift.sh` hook continues to operate post-commit; the new milestone HARD gate is pre-COMPLETE rather than post-commit (complementary, not duplicative).
- Phase 1 lessons scan adds ~30s to every plan; under budget for a 10–30 min planning workflow.

## Implementation Notes

**Execution model:** AA-MA workflow at `.claude/dev/active/aa-ma-engineering-standards/`. Five milestones M0–M4 (M0 covers AA-MA artifact creation + this ADR + plan-verification; M1–M4 ship doctrine, integrate workflow, bump standard, release).

**Critical files affected:**

| Type | Path |
|------|------|
| New rule | `claude-code/rules/engineering-standards.md` |
| New ADR (this file) | `docs/adr/0001-engineering-standards-architecture.md` |
| New ADR INDEX | `docs/adr/INDEX.md` |
| New ADR TEMPLATE | `docs/adr/TEMPLATE.md` |
| New optional template | `docs/templates/engineering-standards-template.md` |
| Amended skill | `claude-code/skills/operational-constraints/SKILL.md` |
| Amended skill | `claude-code/skills/plan-verification/SKILL.md` (Angle 6 extended) |
| Amended skill | `claude-code/skills/aa-ma-plan-workflow/SKILL.md` (Phase 4 description) |
| Amended command | `claude-code/commands/aa-ma-plan.md` (Phase 1 lessons scan + Phase 2 declaration + Phase 4 element #12) |
| Amended command | `claude-code/commands/execute-aa-ma-step.md` (per-step advisory checklist) |
| Amended command | `claude-code/commands/execute-aa-ma-milestone.md` (milestone HARD gate) |
| Amended rule | `claude-code/rules/aa-ma.md` (Planning Standard 11 → 12) |
| Amended specs | `docs/spec/aa-ma-specification.md`, `aa-ma-quick-reference.md`, `claude-code-foundations.md` |
| Amended templates | `docs/templates/plan-template.md`, `tasks-template.md` |
| Amended top-level | `README.md`, `CHANGELOG.md`, `SECURITY.md`, `pyproject.toml` |

**Status transitions:** This ADR will be updated from `Accepted` to `Implemented` once M1 ships (`claude-code/rules/engineering-standards.md` exists in main).

## References

- Working plan file (full grilling trail): `~/.claude/plans/engineering-standards-for-eventual-toast.md`
- AA-MA artifacts (execution-ready form): `.claude/dev/active/aa-ma-engineering-standards/`
- AA-MA specification: `docs/spec/aa-ma-specification.md`
- AA-MA quick reference: `docs/spec/aa-ma-quick-reference.md`
- Doc-drift Tier 6 detector definition: `~/.claude/rules/doc-drift-checks.md`
- Sub-step sync rule (L-080–L-082): `claude-code/rules/aa-ma.md` lines 47-66
- MADR format: https://adr.github.io/madr/
