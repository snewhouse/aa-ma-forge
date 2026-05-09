# [task-name] Engineering Standards Declaration

<!-- OPTIONAL AA-MA artifact. Use when planning element #12 ("Engineering Standards
     Declaration") needs more detail than the inline plan.md section affords. Plans
     without this file are still valid; this is for tasks where the engineering
     posture itself warrants explicit elaboration (e.g. tasks that touch a
     critical-path domain, or that plan to apply prototype-first to multiple
     uncertain sub-steps). -->
<!-- File location: .claude/dev/active/[task-name]/[task-name]-engineering-standards.md -->
<!-- Reference: claude-code/rules/engineering-standards.md (the 6 themes) -->

**Task:** [task-name]
**Created:** [YYYY-MM-DD]
**Author:** [person or "AI + User"]

## Summary

<!-- 1-2 sentences. Which themes carry the most weight for this task and why?
     If a theme is not material, mark it "N/A" with one-line rationale below. -->

[Concise statement of engineering posture for this task]

---

## 1. Verification & Truth

<!-- Code/git as source of truth; empirical testing; prototype-first; double-check
     critical paths. -->

- **Material:** [YES | NO | N/A]
- **Empirical evidence plan:** [How will you validate against running code/API?
  Specific commands, fixtures, or recorded transcripts. "N/A" if pure docs.]
- **Critical-Path tasks:** [List any tasks marked `Critical-Path: <value>` and
  what `CRITICAL_PATH_REVIEW` evidence will look like.]
- **Prototype-Required tasks:** [List any tasks marked `Prototype-Required: YES`
  and what verdict criteria the POC must satisfy.]

## 2. Development Principles

<!-- TDD, KISS, DRY, SOLID, SOC. -->

- **TDD applicability:** [Code-producing? If yes, test strategy. If docs/config
  only, mark "Skipped per skip rule".]
- **KISS / DRY / SOLID / SOC notes:** [Any planned abstractions, shared utilities,
  or separation-of-concerns boundaries worth flagging upfront.]

## 3. Reasoning & Planning

<!-- First-principles, Socratic questioning, skill assessment, strategic subagent
     use. -->

- **Skills to invoke:** [List specific Skill(name) invocations the plan expects.]
- **Subagent dispatch plan:** [Which sub-tasks will dispatch agents, and what
  bounded specialist work each receives.]

## 4. Safety & Continuity

<!-- Non-breaking constraint; lessons learned; avoid repeated mistakes; incremental
     validation. -->

- **Non-breaking constraint posture:** [Will any change alter existing public
  contracts? If yes, what mitigations?]
- **Relevant lessons applied:** [Cite lessons from `docs/lessons.md` or recent
  retros that inform this plan. The Phase 1 lessons-scan output goes here.]
- **Past mistakes flagged:** [Any prior `revert`/`fix`/`hotfix` commits in
  affected files that this plan must not repeat.]

## 5. Execution Checklist Notes

<!-- The 7-item per-task advisory checklist (HARD/SOFT items) lives in the rule
     file. This section is for task-specific elaboration. -->

- **HARD-gate readiness:** [Anything unusual about how the milestone HARD gate
  will be satisfied — e.g. tests run in CI rather than locally, evidence captured
  from a prior session.]
- **SOFT-item commitments:** [Specific commitments for the 3 SOFT items
  (assumptions validated; skills consulted; past mistakes reviewed).]

## 6. Sync & Commit Discipline Notes

<!-- Sub-step Result Log discipline (L-080-082); milestone HARD gate; conventional
     commits with [AA-MA Plan] footer. -->

- **Commit cadence:** [Default is one commit per milestone. Note any exceptions
  here — e.g. "M3.7 Tier 6 sweep gets its own commit because it touches 13 files".]
- **Branch & footer:** [Branch name and the exact `[AA-MA Plan]` footer line that
  every commit will carry.]

---

## Decision Log References

<!-- Link to context-log.md AD-NNN entries that capture engineering-standards
     decisions specific to this task. -->

- AD-NNN: [decision title] — see `[task-name]-context-log.md`

## Out-of-Scope

<!-- Themes deliberately not addressed by this task — anything that would
     normally trigger a theme but is intentionally deferred. -->

- [Item]: [Reason for deferral]
