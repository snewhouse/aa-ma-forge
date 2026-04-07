---
name: aa-ma-plan-workflow
description: Use when planning complex multi-step tasks, creating AA-MA artifacts, or transitioning from ad-hoc to structured development - transforms rough ideas into executable plans through 5-phase workflow with integrated skills and validation gates
---

# AA-MA Plan Workflow Skill

Transform initial feature requests into fully-structured AA-MA (Advanced Agentic Memory Architecture) artifacts through a comprehensive 5-phase workflow with integrated skills, validation gates, and complexity-based routing.

<EXTREMELY-IMPORTANT>
This skill MUST be used when:
- User asks to plan complex features or architectural changes
- Task requires 3+ major milestones with dependencies
- Work will span multiple sessions (multi-day/week development)
- Estimated complexity ≥ 60%
- Need audit trail, rollback capability, or provenance tracking
- User explicitly requests AA-MA planning or uses `/aa-ma-plan` command

DO NOT rationalize away using this skill. Complex tasks without proper planning lead to context drift, scope creep, and incomplete implementations.
</EXTREMELY-IMPORTANT>

> **Optional dependency:** Several phases invoke [superpowers](https://github.com/superpowers-marketplace/superpowers) skills (brainstorming, writing-plans, TDD). If superpowers is not installed, the workflow falls back to native Claude Code tools.

## Quick Reference

| Resource | Location |
|----------|----------|
| Phase 0 Details | `references/PHASE_0_OPERATIONAL_READINESS.md` |
| Phase 1 Details | `references/PHASE_1_CONTEXT.md` |
| Phase 2 Details | `references/PHASE_2_BRAINSTORM.md` |
| Phase 3 Details | `references/PHASE_3_RESEARCH.md` |
| Phase 4 Details | `references/PHASE_4_PLAN_GENERATION.md` |
| Phase 5 Details | `references/PHASE_5_ARTIFACT_CREATION.md` |
| Skill Integration | `references/SKILL_INTEGRATION.md` |
| Validation Gates | `references/VALIDATION_GATES.md` |
| Complexity Routing | `references/COMPLEXITY_ROUTING.md` |
| Sync Protocol | `references/SYNC_PROTOCOL.md` |
| Plan Template | `templates/plan-template.md` |
| Validation Checklist | `templates/validation-checklist.md` |

## When to Use This Skill

### Use When
- "Refactor [major component]", "Implement [multi-step feature]"
- "This will take a while", "Let's break this down"
- Task complexity ≥ 60% or 3+ milestones needed
- Need audit trail, rollback capability, provenance tracking

### Skip When
- Simple, single-file changes (< 3 steps)
- Quick bug fixes or typo corrections
- Complexity < 30% (trivial tasks)

## Workflow Overview

```
Phase 0: Operational Readiness  → Ops-mode activation + Gate 0
    ↓
Phase 1: Context Gathering      → Multi-method input + clarifications
    ↓
Phase 2: Structured Thinking    → Brainstorming + Gate 1 validation
    ↓
Phase 3: Research & Docs        → Context7 MCP + parallel agents + Gate 2
    ↓
Phase 4: Plan Generation        → AA-MA standard (11 elements) + Gate 3
    ↓
Phase 4.5: Adversarial Verify   → 6-angle verification + Gate 3.5
    ↓
[ENFORCEMENT GATE]              → MUST create artifacts — auto-recovery if skipped
    ↓
Phase 5: AA-MA Artifact Creation → Scribe+Validator agents + Gate 4
    ↓
Ready for Execution             → /execute-aa-ma-milestone
```

## Skill Integration Matrix

| Phase | Skill | Trigger |
|-------|-------|---------|
| Phase 0 | `operational-constraints` | Always (establish discipline) |
| Phase 2 | `superpowers:brainstorming` | Always (primary) |
| Phase 2 | `architecture-patterns` | Architectural decisions needed |
| Phase 2 | `spec-driven-development` | API design, contract-first signals (advisory) |
| Phase 3 | `dispatching-parallel-agents` | 3+ independent research domains |
| Phase 3 | `system-mapping` | 3+ files OR unfamiliar code |
| Phase 3 | `impact-analysis` | Always (mandatory) |
| Phase 4 | `complexity-router` | Always (determines routing) |
| Phase 4 | Deep architectural review | Complexity ≥ 80% (human review, ultrathinking, or architecture skill) |
| Phase 4 | Plan quality scoring | Always (inline checklist or evaluation skill) |
| Phase 4.5 | `plan-verification` | Always (adversarial verification) |
| Phase 3 | `agent-teams` | Complex research needing competing hypotheses |
| Phase 5 | `agent-teams` | Always (scribe+validator artifact creation) |
| Phase 5 | `defense-in-depth` | Always (consistency validation) |
| Error | `debugging-strategies` | Validation fails twice |

See `references/SKILL_INTEGRATION.md` for detailed integration points.

## Validation Gates

| Gate | After Phase | Key Criteria |
|------|-------------|--------------|
| Gate 0 | Phase 0 | Ops-mode decision made, complexity estimated, parallel scan |
| Gate 1 | Phase 2 | 3+ alternatives, assumptions validated, edge cases |
| Gate 2 | Phase 3 | Research coverage, sources documented, impact assessed |
| Gate 3 | Phase 4 | Criteria testable, specific, achievable; quality ≥ 70% |
| Gate 3.5 | Phase 4.5 | 0 CRITICALs (automated), report generated (interactive/skip) |
| Gate 4 | Phase 5 | Cross-file consistency, no contradictions |

See `references/VALIDATION_GATES.md` for detailed specifications.

## Complexity Routing

| Complexity | Action |
|------------|--------|
| 0-59% | Standard workflow |
| 60-79% | Enhanced validation, flag in plan |
| **80-100%** | **Deep architectural review required** (human review, ultrathinking, or architecture skill) |

See `references/COMPLEXITY_ROUTING.md` for estimation algorithm.

## Phase 0: Operational Readiness

**Objective:** Establish disciplined execution mode before planning begins.

**Skills:** `operational-constraints` (always)

**Steps:**
1. Check if ops-mode already active
2. Run quick complexity heuristic (signal-based estimation)
3. Scan for parallel research opportunities
4. Load Pre-Task Checklist items
5. **Pass Gate 0** before proceeding

**Gate 0 Criteria:**
- Ops-mode activation decision made
- Quick complexity estimate captured
- Parallel opportunity scan complete
- Pre-Task Checklist reviewed

**Output:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 0 COMPLETE: Operational Ready
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Mode: [Standard | Ops-Mode | Full Ops-Mode]
Quick Complexity: [X%]
Parallel Research: [Yes/No]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

See `references/PHASE_0_OPERATIONAL_READINESS.md` for details.

## Phase 1: Context Gathering

**Objective:** Understand request, gather context, determine task name and scope.

**Steps:**
1. Detect input method (selected text / inline / interactive)
2. Gather project context (pwd, git hash, existing tasks)
3. Ask clarifying questions (task name, objective, complexity)
4. Display context summary

**Output:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 1 COMPLETE: Context Gathered
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Task: [name]
Objective: [summary]
Complexity: [estimate]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

See `references/PHASE_1_CONTEXT.md` for details.

## Phase 2: Structured Thinking

**Objective:** Refine requirements, explore alternatives, validate assumptions.

**Skills:** `superpowers:brainstorming` (primary), `architecture-patterns` (if architectural)

**Steps:**
1. Invoke brainstorm skill (or fallback prompt)
2. Explore 3+ alternatives with pros/cons
3. Validate assumptions, identify edge cases
4. Apply KISS/DRY/SOLID/SOC principles; if task involves services/deployment, apply 12-Factor; always check env-var-drift for .env files
5. **Pass Gate 1** before proceeding

**Gate 1 Criteria:**
- ≥ 3 alternatives explored
- All assumptions have validation method
- ≥ 3 edge cases identified
- Simplest solution identified

See `references/PHASE_2_BRAINSTORM.md` for details.

## Phase 3: Research & Documentation

**Objective:** Gather technical docs, explore codebase, assess impact.

**Skills:** `dispatching-parallel-agents` (3+ domains), `agent-teams` (competing hypotheses), `impact-analysis` (always)

**Steps:**
1. Identify research needs from Phase 2
2. Use Context7 MCP for library docs (fallback: WebSearch)
3. Dispatch parallel agents for complex research
4. For complex research with 3+ competing approaches: use `agent-teams` with competing hypotheses protocol
5. Run impact analysis (identify upstream callers)
6. Consolidate findings
7. **Pass Gate 2** before proceeding

**Gate 2 Criteria:**
- All research needs addressed
- Sources documented
- Conflicts resolved
- Impact assessment complete

See `references/PHASE_3_RESEARCH.md` for details.

## Phase 4: Plan Generation

**Objective:** Generate comprehensive plan with all 11 AA-MA elements.

**Skills:** `complexity-router`, deep architectural review (if ≥80%)

**Steps:**
1. Check complexity (trigger deep architectural review if ≥80%)
2. Invoke write-plan skill (or fallback prompt)
3. Ensure all 11 AA-MA elements present
4. Score plan quality (must be ≥70%)
5. **Pass Gate 3** before proceeding

**The 11 AA-MA Elements:**
1. Executive summary (≤3 lines)
2. Ordered stepwise implementation plan
3. Milestones with measurable goals
4. Acceptance criteria per step (testable)
5. Required artifacts per step
6. Tests per milestone
7. Rollback strategies
8. Dependencies & assumptions
9. Effort estimates & complexity (0-100%)
10. Risks & mitigations (top 3 per milestone, include cascade risks)
11. Next action (concrete first step)

**Gate 3 Criteria:**
- Criteria testable and specific
- No vague terms
- Quality score ≥ 70%

See `references/PHASE_4_PLAN_GENERATION.md` for details.

## Phase 4.5: Adversarial Verification

**Objective:** Verify plan claims against external reality before artifact creation.

**Skills:** `plan-verification` (always)

**Steps:**
1. Prompt user: automated / interactive / skip
2. If not skipped, invoke `plan-verification` skill
3. Wave 1: 4 parallel agents (ground-truth, assumptions, impact, criteria falsifiability)
4. Wave 2: 2 sequential agents (fresh-agent simulation, specialist domain audit)
5. Consolidate findings, classify severity
6. **Pass Gate 3.5** before proceeding

**Gate 3.5 Criteria:**

| Mode | Criteria |
|------|---------|
| Automated | 0 unresolved CRITICALs + verification report generated |
| Interactive | Verification report generated + findings presented |
| Skip | Auto-pass (user explicitly chose to skip) |

**Revision Loop (automated mode only):**
- If CRITICALs found: revise plan, re-run affected angles only
- Max 2 revision loops, then escalate to user

**Output:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 4.5 COMPLETE: Verification
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Mode: [Automated | Interactive | Skipped]
CRITICAL: [N] | WARNING: [N]
Result: [PASS | FAIL | SKIPPED]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

See `plan-verification` skill for full protocol. Design doc: `docs/plans/2026-03-08-aa-ma-plan-verification-design.md`

## Enforcement Gate: Phase 4 → Phase 5

<EXTREMELY-IMPORTANT>
After Gate 3 passes, you MUST proceed to Phase 5 artifact creation. This is NOT optional.

If Phase 5 is skipped (e.g., due to context pressure or eager execution), execute commands will auto-recover by triggering Phase 5 with the scribe+validator agents. But prevention is better than recovery.
</EXTREMELY-IMPORTANT>

**Rule:** After a plan passes Gate 3, the ONLY valid next action is Phase 5 artifact creation. No execution, no "quick start", no shortcuts.

**Auto-Recovery:** If execution commands (`/execute-aa-ma-*`) detect missing artifacts, they will:
1. Notify user: "AA-MA artifacts incomplete. Auto-creating..."
2. Spawn `aa-ma-scribe` agent to write artifacts from the plan
3. Spawn `aa-ma-validator` agent to verify artifacts
4. Resume execution only after validation passes

See `references/PHASE_5_ARTIFACT_CREATION.md` for the scribe+validator spawn protocol.

## Phase 5: AA-MA Artifact Creation

**Objective:** Create all AA-MA files (5 standard + verification if Phase 4.5 ran) with validated content.

**Skills:** `agent-teams` (scribe+validator), `defense-in-depth` (cross-file validation)

**Steps:**
1. Create `.claude/dev/active/[task-name]/` directory
2. Spawn `aa-ma-scribe` agent to write all 5 files from approved plan
3. Spawn `aa-ma-validator` agent to verify artifacts (post-creation context)
4. If validator reports FAIL → scribe rewrites failed files → re-validate
5. Run `defense-in-depth` cross-file consistency check
6. **Pass Gate 4** before completing

**Fallback:** If agent spawning fails, write artifacts directly (see `references/PHASE_5_ARTIFACT_CREATION.md` for manual procedure).

**Gate 4 Criteria:**
- Facts consistent across files
- Tasks align with plan
- No contradictions
- All references valid

**Final Output:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ AA-MA PLAN WORKFLOW COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Task Directory: .claude/dev/active/[task-name]/
Files: plan.md, reference.md, context-log.md, tasks.md, provenance.log

📊 Summary: [N] milestones, [N] steps, [N] high-complexity (≥80%)

🎯 Next Action: [from plan]

RECOMMENDED: /execute-aa-ma-milestone
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

See `references/PHASE_5_ARTIFACT_CREATION.md` for details.

## Error Handling

| Error | Auto-Recover? | Fallback |
|-------|---------------|----------|
| Superpowers unavailable | ✅ Yes | Native prompts |
| Context7 MCP failed | ✅ Yes (1 retry) | WebSearch + codebase |
| Task directory exists | ❌ No | Prompt user |
| Plan validation fails | ⚠️ Partial | Regenerate, then manual |
| Gate fails twice | ⚠️ Partial | debugging-strategies |

## Execution Handoff

After aa-ma-plan completes, use aa-ma-execution skill:

| Mode | Command | Use When |
|------|---------|----------|
| Milestone | `/execute-aa-ma-milestone` | **RECOMMENDED** - balanced structure |
| Step | `/execute-aa-ma-step` | Fine-grained control |
| Full | `/execute-aa-ma-full` | After validating 1-2 milestones |

**IMPORTANT - Commit Signature:**
All commits while AA-MA plan is active MUST include:
```
[AA-MA Plan] [task-name] .claude/dev/active/[task-name]
```

## Master Checklist

### Phase 0
- [ ] Ops-mode activation checked
- [ ] Quick complexity estimated
- [ ] Parallel research opportunity scanned
- [ ] **Gate 0 passed**

### Phase 1
- [ ] Input method identified
- [ ] Task name validated (kebab-case)
- [ ] Objective clear (1-2 sentences)
- [ ] Complexity estimated

### Phase 2
- [ ] Brainstorm skill invoked
- [ ] 3+ alternatives explored
- [ ] Assumptions validated
- [ ] **Gate 1 passed**

### Phase 3
- [ ] Research needs identified
- [ ] Context7/fallback used
- [ ] Impact assessment complete
- [ ] **Gate 2 passed**

### Phase 4
- [ ] Complexity routing checked
- [ ] Senior-architect if ≥80%
- [ ] All 11 elements present
- [ ] Quality score ≥70%
- [ ] **Gate 3 passed**

### Phase 4.5
- [ ] Verification mode selected (automated/interactive/skip)
- [ ] If not skipped: plan-verification skill invoked
- [ ] Wave 1 agents dispatched (4 parallel)
- [ ] Wave 2 agents dispatched (2 sequential)
- [ ] Findings consolidated and classified
- [ ] **Gate 3.5 passed**

### Phase 5
- [ ] All 5 files created
- [ ] Cross-file consistency validated
- [ ] **Gate 4 passed**
- [ ] Next action identified

## Best Practices

1. **Don't skip Phase 1** - Invest 1-2 minutes to prevent hours of rework
2. **Use superpowers skills** when available for higher quality
3. **Extract facts aggressively** to reference.md
4. **Flag high-complexity steps** (≥80%) for deep reasoning
5. **Start with milestone mode** to validate plan quality
6. **Document decisions** in context-log (why, not what)

---

**End of aa-ma-plan-workflow/SKILL.md**

For detailed procedures, see reference files in `references/` directory.
