# Validation Checklist for [task-name]

## Pre-Execution Validation

### Gate 0: Operational Readiness (Phase 0)
- [ ] Ops-mode activation decision made: [Standard / Ops-Mode / Full Ops-Mode]
- [ ] Quick complexity estimate captured: [____]%
- [ ] Parallel research opportunities evaluated: [Yes / No]
- [ ] Pre-Task Checklist reviewed

### Gate 1: Brainstorm Output (Phase 2)
- [ ] >= 3 alternatives explored
- [ ] All key assumptions listed with validation method
- [ ] >= 3 edge cases identified
- [ ] KISS principle applied (simplest solution identified)
- [ ] Design concept clear (2-3 sentences)

### Gate 2: Research Completeness (Phase 3)
- [ ] All research needs from Phase 2 addressed
- [ ] Each finding has documented source
- [ ] Conflicting information resolved or escalated
- [ ] Impact assessment completed (upstream callers identified)
- [ ] All dependencies documented with versions
- [ ] Token efficiency evaluated: [Below 50% / 50-70% / Above 70%]
- [ ] Context compacted if above 70%: [N/A / Done]

#### System Mapping (if triggered)
*Trigger: 3+ files modified, unfamiliar code, external services, or data pipelines*
- [ ] System mapping required: [Yes / No]
- [ ] If Yes:
  - [ ] Architecture documented (files/modules involved)
  - [ ] Execution flows traced (call chains, async boundaries)
  - [ ] Logging/observability identified
  - [ ] Dependencies mapped (imports, external services)
  - [ ] Environment requirements documented (config, env vars)

### Gate 3: Criteria Quality (Phase 4)
- [ ] Each acceptance criterion is testable
- [ ] No vague terms used (works correctly, performs well, etc.)
- [ ] Each criterion is achievable within scope
- [ ] No circular dependencies between criteria
- [ ] Plan quality score >= 70%

### Gate 4: Cross-File Consistency (Phase 5)
- [ ] All facts in reference.md appear in plan.md
- [ ] All milestones in tasks.md match plan.md
- [ ] No contradictions between files
- [ ] All plan elements covered across files
- [ ] All cross-references valid

## AA-MA File Validation

### plan.md
- [ ] Executive summary ≤ 3 lines
- [ ] All 11 AA-MA elements present:
  1. [ ] Executive summary
  2. [ ] Ordered implementation steps
  3. [ ] Milestones with goals
  4. [ ] Acceptance criteria per step
  5. [ ] Required artifacts per step
  6. [ ] Tests per milestone
  7. [ ] Rollback strategies
  8. [ ] Dependencies & assumptions
  9. [ ] Effort estimates & complexity
  10. [ ] Risks & mitigations (top 3 per milestone)
  11. [ ] Next action identified

### reference.md
- [ ] All API endpoints extracted
- [ ] All file paths documented
- [ ] Configuration values listed
- [ ] Dependencies with versions
- [ ] Last updated timestamp present

### context-log.md
- [ ] Feature request documented
- [ ] Key decisions with rationale
- [ ] Research findings summarized
- [ ] Remaining questions listed

### tasks.md
- [ ] All milestones from plan present
- [ ] HTP structure correct (Status, Dependencies, Complexity)
- [ ] Acceptance criteria for each milestone
- [ ] Result Log placeholders present

### provenance.log
- [ ] Initialization timestamp
- [ ] Project path recorded
- [ ] Git commit baseline (if git repo)
- [ ] Phase completion timestamps

## Complexity Routing Check

- [ ] Complexity score calculated: [____]%
- [ ] Routing action taken: [Standard / Enhanced / Senior-Architect]

### High-Complexity Protocol (if >= 80%)
*Skip this section if complexity < 80%*
- [ ] High-complexity protocol required: [Yes / No]
- [ ] If Yes:
  - [ ] Full ops-mode activated
  - [ ] System mapping verified complete (from Phase 3)
  - [ ] Senior-architect skill invoked
  - [ ] Deep reasoning documented in context-log.md

## Final Sign-off

- [ ] All 5 gates passed (Gate 0-4)
- [ ] All 5 AA-MA files validated
- [ ] Complexity routing appropriate
- [ ] High-complexity protocol followed (if applicable)
- [ ] Ready for execution

**Validated by:** [AI/Human]
**Date:** [YYYY-MM-DD]
