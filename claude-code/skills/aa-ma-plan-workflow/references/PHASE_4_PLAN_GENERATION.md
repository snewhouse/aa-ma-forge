# Phase 4: Plan Generation with AA-MA Standard

## Objectives
- Generate comprehensive implementation plan
- Ensure all 11 AA-MA Planning Standard elements included
- Define clear acceptance criteria for each step
- Identify rollback strategies for risky changes
- Route high-complexity tasks for architectural review

## Skill Integration

**Primary skill:** `superpowers:writing-plans`
**Complexity routing:** `complexity-router` → deep architectural review (for >= 80%)
**Quality scoring:** `llm-evaluation` (always, for plan quality assessment)

## The AA-MA Planning Standard (11 Required Elements)

Every plan MUST include:

1. **Executive summary** (≤3 lines) - Concise objective and success criteria
2. **Ordered stepwise implementation plan** - Sequenced steps with dependencies
3. **Milestones** - Named checkpoints with measurable goals and dates/durations
4. **Acceptance criteria** - One clear, testable criterion per step/milestone
5. **Required artefacts** - Files, diagrams, APIs, schemas, credentials per step
6. **Tests to validate** - Unit/integration/manual tests with pass/fail thresholds
7. **Rollback strategy** - Explicit rollback or mitigation plan for risky changes
8. **Dependencies & assumptions** - External services, libraries, assumptions made
9. **Effort estimate & complexity** - Hours/days per step, complexity score (0-100%)
10. **Risks & mitigations** - Top 3 risks per milestone with proposed mitigations. Include **cascade risks** (changes that may break upstream callers or dependent modules)
11. **Next action** - Single concrete first step and which AA-MA file(s) to update

## Step-by-Step Procedure

### 4.1 Complexity Routing Check

**BEFORE generating plan, check complexity:**

Use `complexity-router` skill (or manual check):

| Complexity | Action |
|------------|--------|
| 0-59% | Proceed with standard planning |
| 60-79% | Add extra validation, flag in plan |
| **80-100%** | **Deep architectural review required** (human review, ultrathinking, or architecture skill) |

**High complexity indicators (>= 80%):**
- Architectural changes affecting multiple services
- Security-critical functionality
- Performance-critical paths
- External API integrations with SLAs
- Data migration or schema changes
- Multi-team coordination required

### 4.2 Invoke Write-Plan Skill

**Primary approach:** Use superpowers write-plan skill

```
Skill: superpowers:writing-plans
```

Pass to skill:
- Refined requirements from Phase 2
- Research findings from Phase 3
- AA-MA Planning Standard requirements (11 elements above)
- Project context and constraints

The skill will:
- Generate structured implementation plan
- Ensure all 11 elements present
- Create hierarchical milestone structure
- Define clear acceptance criteria
- Identify risks and rollback strategies

### 4.3 High-Complexity Protocol (>= 80%)

**If complexity >= 80%, MUST follow this protocol:**

#### Step 1: Ensure Full Ops-Mode Active
```
IF Skill(operational-constraints) not already loaded:
    → Invoke: Skill(operational-constraints)
    → Confirm: Full ops-mode discipline activated
```

#### Step 2: Verify System Mapping Complete
```
IF Skill(system-mapping) not invoked in Phase 3:
    → Invoke: Skill(system-mapping)
    → Pass: Entry points, module boundaries
    → Capture: Architecture summary, dependency map
```

#### Step 3: Deep Architectural Review
```
Trigger: complexity >= 80%
Method: Human review, ultrathinking, or architecture skill if available
```

Pass:
- Generated plan from write-plan skill
- Complexity assessment
- Architectural concerns identified
- System mapping output (if available)

Senior-architect will:
- Review architectural decisions
- Validate scalability and maintainability
- Identify potential issues
- Suggest improvements

#### Step 4: Document Deep Reasoning
```
For each step with Complexity >= 80%:
    → Document reasoning in context-log.md after compaction
    → Include: alternatives considered, trade-offs, rationale
```

**High-complexity indicators:**
- Architectural changes affecting multiple services
- Security-critical functionality
- Performance-critical paths
- External API integrations with SLAs
- Data migration or schema changes
- Multi-team coordination required

### 4.4 Fallback (if superpowers:writing-plans unavailable)

Use native planning prompt:

```markdown
You MUST produce a thorough implementation plan following AA-MA Planning Standard.

CONTEXT:
- Task: [name]
- Objective: [from Phase 1]
- Design: [refined concept from Phase 2]
- Research: [findings from Phase 3]
- Constraints: [known limitations]

Provide ALL 11 required elements:

1. Executive summary (≤3 lines)
2. Ordered stepwise implementation plan
3. Milestones with measurable goals and dates/durations
4. Acceptance criteria for EACH step (testable, specific)
5. Required artefacts for each step (files, configs, schemas)
6. Tests to validate each milestone (with pass criteria)
7. Rollback strategy for risky steps (explicit commands/procedures)
8. Dependencies and explicit assumptions
9. Effort estimate (hours/days) + Complexity (0-100%) per step
   - Flag steps with Complexity ≥ 80% for deep reasoning
10. Risks (top 3) and mitigations per milestone
    - Include **cascade risks** for shared/core module changes
11. ONE Next action (what to do first) + which AA-MA file(s) to update

Format in Markdown. Structure with:
- ## for Milestones
- ### for Steps within milestones
- Clear hierarchical dependencies

Output must be ready for direct insertion into [task]-plan.md
```

### 4.4b Domain-Aware Plan Structure (Advisory Guidance)

When `spec-driven-development` was accepted in Phase 2, the plan SHOULD
(not MUST) structure milestones to follow the spec-first sequence:

1. Design specification (OpenAPI/GraphQL SDL/Protobuf)
2. Validate and lint specification
3. Generate stubs and mock server
4. Implement business logic (TDD)
5. Contract testing and CI/CD

This is guidance, not a gate requirement. Plans that deviate must
document why in the context-log.

### 4.4b Architectural Constraints from CLAUDE.md

When generating plan steps, apply these design constraints with actionable triggers:

- **KISS/DRY/SOLID/SOC:** Apply per Phase 2 brainstorm output. If plan steps create new utilities, verify no existing implementation exists first.
- **12-Factor App:** If plan involves service deployment, API servers, or containerized applications, constrain architecture to 12-Factor principles (config via env, stateless processes, port binding). For ALL plans touching `.env` files, include env-var-drift check in acceptance criteria.
- **TDD:** For code-producing milestones, set acceptance criteria as machine-testable assertions. Include `superpowers:test-driven-development` invocation in the execution notes.

### 4.5 Plan Quality Scoring

**Always invoke `llm-evaluation` skill:**

Score plan on:
- Completeness (all 11 elements present)
- Testability (acceptance criteria are verifiable)
- Specificity (no vague steps)
- Achievability (realistic scope)

**Minimum passing score: 70%**

### 4.6 Validate Plan Completeness

**Validation checklist** (MUST pass before proceeding):

- [ ] Executive summary ≤ 3 lines
- [ ] All steps ordered with clear dependencies
- [ ] Each milestone has measurable goal
- [ ] Each step has testable acceptance criteria
- [ ] Required artifacts listed per step
- [ ] Test validation defined per milestone
- [ ] Rollback strategy for each risky change
- [ ] Dependencies and assumptions explicit
- [ ] Effort estimates and complexity scores present
- [ ] Steps with Complexity ≥ 80% flagged for deep reasoning
- [ ] Top 3 risks identified per milestone with mitigations
- [ ] Next action is concrete and actionable

**If validation fails:**
1. Re-generate plan with explicit checklist prompt
2. If second attempt fails, notify user and save partial plan
3. Request user input to complete missing elements

### 4.7 Planning Output Protocol

**At the end of plan generation, MUST:**

1. **Explicitly ask for approval** before proceeding to artifact creation
2. **Offer clear options:**
   - Proceed to Phase 5 (artifact creation)
   - Review specific sections first
   - Adjust/refine the plan
3. **Identify the single next action** to take

**Template:**
```markdown
## Plan Summary
[Concise overview: N milestones, N steps, N high-complexity]

## Proposed Approach
[Key architectural decisions]

## Ready to proceed?
- [ ] Approve and proceed to Phase 5 (artifact creation)
- [ ] Review section: [specify which]
- [ ] Need adjustments: [specify changes needed]
```

**IMPORTANT:** Never proceed to artifact creation without explicit user approval.

### 4.8 Display Phase Summary

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 4 COMPLETE: Plan Generated
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ [N] implementation steps
✓ [N] milestones defined
✓ All 11 AA-MA elements present
✓ Acceptance criteria clear and testable
✓ Rollback strategies included
✓ [N] high-complexity steps flagged (≥80%)
✓ Plan quality score: [X]%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Phase 4 Checklist

- [ ] Complexity routing check performed
- [ ] **High-complexity protocol** followed if complexity >= 80%:
  - [ ] Full ops-mode activated
  - [ ] System mapping verified complete
  - [ ] Senior-architect invoked
  - [ ] Deep reasoning documented
- [ ] Planning skill invoked (or fallback used)
- [ ] Plan generated in Markdown format
- [ ] All 11 AA-MA elements validated as present
- [ ] Plan quality scored (>= 70% required)
- [ ] Acceptance criteria testable and specific
- [ ] Complexity ≥80% steps flagged
- [ ] Next action clearly identified
- [ ] **Planning output protocol** followed (explicit user approval obtained)
- [ ] Plan ready for insertion into [task]-plan.md

## Validation Gate 3: Criteria Quality Validation

**MUST PASS before proceeding to Phase 5:**

| Criterion | Requirement | Check |
|-----------|-------------|-------|
| Testability | Each acceptance criterion can be verified programmatically or manually | [ ] |
| Specificity | No criterion uses vague terms (e.g., "works correctly", "performs well") | [ ] |
| Achievability | Each criterion is realistically achievable within stated scope | [ ] |
| Independence | Criteria don't have circular dependencies | [ ] |
| Quality Score | Plan quality score >= 70% | [ ] |

**On Failure:**
1. Re-generate specific criteria that failed
2. If fails twice, invoke `debugging-strategies` skill
3. Escalate to user for manual review
