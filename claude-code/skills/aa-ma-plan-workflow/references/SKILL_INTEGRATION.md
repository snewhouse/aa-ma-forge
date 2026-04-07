# Skill Integration Guide

## Integration Philosophy

Skills are integrated into the aa-ma-plan workflow at specific decision points where specialized expertise adds value. Integration follows the "commands compose skills" pattern - the aa-ma-plan workflow orchestrates skill invocation based on context.

## Integration Matrix

| Phase | Skill | Trigger Condition | Purpose |
|-------|-------|-------------------|---------|
| Phase 0 | `operational-constraints` | Always | Establish session discipline |
| Phase 2 | `superpowers:brainstorming` | Always (primary) | Structured thinking, alternatives exploration |
| Phase 2 | `architecture-patterns` | Architectural decisions needed | Design patterns, system boundaries |
| Phase 2 | `spec-driven-development` | API design, REST/GraphQL/gRPC, contract-first signals (advisory) | Spec-first methodology recommendation |
| Phase 3 | `dispatching-parallel-agents` | 3+ independent research domains | Parallel research coordination |
| Phase 3 | `system-mapping` | 3+ files OR unfamiliar code | Pre-flight architecture understanding |
| Phase 3 | `impact-analysis` | Always | Identify upstream callers, cascade risks |
| Phase 4 | `complexity-router` | Always | Determine routing based on complexity |
| Phase 4 | `senior-architect` | Complexity >= 80% | Architectural review, quality gate |
| Phase 4 | `superpowers:writing-plans` | Always (primary) | Plan generation |
| Phase 4 | `llm-evaluation` | Always | Plan quality scoring |
| Phase 3 | `agent-teams` | Complex research needing competing hypotheses | Adversarial debate, hypothesis synthesis |
| Phase 5 | `agent-teams` | Always | Scribe+Validator artifact creation |
| Phase 5 | `defense-in-depth` | Always | Cross-file consistency validation |
| Error | `debugging-strategies` | Validation fails twice | Root cause analysis, recovery |

## Detailed Integration Points

### Phase 0: Operational Readiness

**operational-constraints**
```
Trigger: Always (before Phase 1 begins)

Invoke: Skill: operational-constraints
Pass:
  - Session start context
  - Task preview (if available from command argument)

Captures:
  - Token efficiency principles
  - Tool selection protocols
  - Parallel execution mandate
  - TDD discipline reminders
  - Planning output protocol

Returns: Session discipline established, Pre-Task Checklist loaded
```

**Quick Complexity Heuristic** (inline, not skill-based):
```
Evaluated during Phase 0 using signal indicators:
  - "refactor" / "migrate" → +20%
  - Multiple systems → +15%
  - "integration" / "API" → +15%
  - Unfamiliar codebase → +20%
  - External dependencies → +10%
  - "security" / "auth" → +15%
  - Database schema changes → +15%
  - "OpenAPI" / "contract-first" / "spec-driven" → +10%

Routing:
  < 40%  → Standard mode
  40-60% → Enable ops-mode basics
  >= 60% → Full ops-mode mandatory
  >= 80% → Flag for senior-architect (Phase 4)
```

### Phase 2: Brainstorming

**Primary: superpowers:brainstorming**
```
Invoke: Skill: superpowers:brainstorming
Pass:
  - User's feature request (from Phase 1)
  - Known constraints and requirements
  - Project context (language, frameworks)
  - Design principles: KISS, DRY, SOLID, SOC
```

**Secondary: architecture-patterns**
```
Trigger: When task involves any of:
  - System boundaries or service decomposition
  - Data flow patterns or persistence strategies
  - Integration patterns or API design
  - Scalability or performance architecture

Invoke: Skill: architecture-patterns
Pass:
  - Brainstorm output
  - Architectural concerns identified
```

### 2.2b Advisory Triggers (New Pattern)

Unlike standard conditional triggers which invoke skills automatically,
advisory triggers DISPLAY a recommendation and wait for user confirmation.

Format:
```
┌─ 💡 [Skill Name] Recommended ───────────────────────┐
│ [1-2 sentence explanation of why this skill applies] │
│ Accept: Skill([skill-name]) loaded, context added    │
│ Ignore: Standard workflow continues unchanged        │
└──────────────────────────────────────────────────────┘
```

Advisory triggers do NOT count as gate criteria. Ignoring them
does not block any validation gate.

**spec-driven-development** (ADVISORY)
```
Trigger: Phase 2 brainstorm output mentions:
  - API endpoint design, REST/GraphQL/gRPC service contracts
  - Schema-first or contract-first approach
  - Service boundary definition with external consumers
  - OpenAPI, AsyncAPI, Protobuf specification work

Action: Display advisory recommendation:
  ┌─ 💡 Spec-Driven Development Recommended ──────────────┐
  │ This task involves API/service design. Consider using  │
  │ spec-first methodology: Skill(spec-driven-development) │
  │ For full API workflow: Skill(api-spec-workflow)         │
  └────────────────────────────────────────────────────────┘

If accepted:
  Invoke: Skill: spec-driven-development
  Pass:
    - API type (REST/GraphQL/gRPC/AsyncAPI) from brainstorm
    - Identified endpoints/operations
    - Consumer requirements (if known)
  Returns: Recommended spec type, toolchain, contract testing strategy
           → Fed into Phase 4 plan generation as domain context

If ignored: Continue standard workflow. No further prompts about spec-driven.
```

### Phase 3: Research

**dispatching-parallel-agents**
```
Trigger: Research needs >= 3 independent areas

Invoke: Skill: dispatching-parallel-agents
Pass:
  - Research domains (list)
  - Time budget
  - Output format requirements
```

**system-mapping**
```
Trigger: Any of the following:
  - Changes will touch 3+ files
  - Code area is unfamiliar (flagged in Phase 0/1)
  - Integrating with external services
  - Modifying data pipelines or databases

Invoke: Skill: system-mapping
Pass:
  - Entry point files (from research findings)
  - Module boundaries to explore
  - 5-point protocol request:
    1. Architecture (files/modules)
    2. Execution flows (call chains)
    3. Logging (observability)
    4. Dependencies (imports)
    5. Environment (config/env vars)

Returns: Architecture summary → feeds Phase 4 plan constraints

Note: Can run in PARALLEL with other research agents.
```

**impact-analysis**
```
Trigger: Always (mandatory for all plans)

Invoke: Skill: impact-analysis
Pass:
  - Files to be created/modified
  - Upstream caller identification request
```

### Phase 4: Plan Generation

**superpowers:test-driven-development** (Conditional)
```
Trigger: When plan milestones include code implementation tasks
  with machine-testable acceptance criteria (pytest assertions,
  API response checks, CLI output matches)

Invoke: Skill: superpowers:test-driven-development
Pass:
  - Milestone acceptance criteria
  - Test framework (from project context)
  - Code-producing task list

Skip: docs-only, config-only, infrastructure-only milestones

Note: During execution, the execute-aa-ma-* commands will also
invoke this skill for code-producing milestones. This Phase 4
integration ensures TDD is PLANNED, not just executed reactively.
```

**12-Factor App** (ADVISORY — narrow trigger)
```
Trigger: Phase 2/3 output indicates:
  - Service deployment, API servers, or containerized applications
  - Config management patterns (env vars, secrets)
  - Stateless process design
  - Port binding or service discovery

Action: Display advisory recommendation:
  ┌─ 💡 12-Factor App Principles Recommended ──────────────┐
  │ This task involves service architecture. Reference       │
  │ 12-Factor principles for config (env vars not files),    │
  │ statelessness, and port binding.                         │
  └─────────────────────────────────────────────────────────┘

Always applicable: For ANY task with .env files, verify
env-var-drift compliance (see rules/env-var-drift.md).
This is not advisory — it's mandatory.
```

**complexity-router**
```
Trigger: Always (before plan generation)

Invoke: Skill: complexity-router
Pass:
  - Task description
  - Research findings
  - Identified risks

Returns: Complexity score (0-100%), routing decision
```

**senior-architect**
```
Trigger: complexity-router returns >= 80%

Invoke: Skill: senior-architect
Pass:
  - Generated plan draft
  - Complexity assessment
  - Architectural concerns

Returns: Reviewed plan, recommendations
```

**llm-evaluation**
```
Trigger: Always (after plan generation)

Invoke: Skill: llm-evaluation
Pass:
  - Generated plan
  - Evaluation criteria (completeness, testability, specificity, achievability)

Returns: Quality score (0-100%)
```

### Phase 3: Research (Agent-Teams Integration)

**agent-teams** (competing hypotheses)
```
Trigger: Complex research with 3+ competing approaches where
  adversarial debate would improve quality (e.g., architecture
  decisions, technology selection, migration strategies)

Invoke: Skill: agent-teams
Pass:
  - Task classification: RESEARCH
  - Research domains from Phase 2 brainstorming
  - Competing hypotheses to investigate
  - Debate protocol: researchers challenge each other's conclusions

Returns: Synthesized findings that survived adversarial challenge

Fallback: dispatching-parallel-agents (one-shot, no debate)
```

### Phase 5: Artifact Creation

**agent-teams** (scribe+validator)
```
Trigger: Always (after Gate 3 passes)

Invoke: Skill: agent-teams (or direct agent spawn)
Pass:
  - Approved plan from Phase 4
  - Phase 1-3 context (decisions, research findings)
  - Task name and directory path
  - Agent definitions: aa-ma-scribe, aa-ma-validator

Spawns:
  1. aa-ma-scribe → writes all 5 AA-MA files
  2. aa-ma-validator → verifies post-creation (5 dimensions)

Returns: 5 validated AA-MA files + validation report

Remediation: If validator FAIL → re-scribe → re-validate (max 2 cycles)
Fallback: Direct artifact writing (manual procedure in PHASE_5_ARTIFACT_CREATION.md)
```

**defense-in-depth**
```
Trigger: Always (after all files created)

Invoke: Skill: defense-in-depth
Pass:
  - All 5 AA-MA files
  - Consistency check request

Returns: Validation result, inconsistencies found
```

### Error Recovery

**debugging-strategies**
```
Trigger: Any validation gate fails twice

Invoke: Skill: debugging-strategies
Pass:
  - Failing validation details
  - Context from failed phase
  - Error logs

Returns: Root cause analysis, recovery recommendations
```

## Fallback Handling

When a skill is unavailable:

| Skill | Fallback |
|-------|----------|
| `operational-constraints` | Apply inline: token efficiency, parallel eval, tool hierarchy |
| `system-mapping` | Grep-based exploration: imports, logging, env vars |
| `superpowers:brainstorming` | Native brainstorming prompt (see PHASE_2_BRAINSTORM.md) |
| `superpowers:writing-plans` | Native planning prompt (see PHASE_4_PLAN_GENERATION.md) |
| `architecture-patterns` | WebSearch for patterns + codebase analysis |
| `spec-driven-development` | ✅ Yes — Skip advisory, continue standard workflow |
| `dispatching-parallel-agents` | Sequential agent dispatch |
| `agent-teams` (Phase 3) | `dispatching-parallel-agents` (one-shot, no debate) |
| `agent-teams` (Phase 5) | Direct artifact writing (manual procedure) |
| `senior-architect` | Extra validation pass + user review flag |
| `llm-evaluation` | Manual checklist validation |
| `defense-in-depth` | Manual cross-file review |
| `debugging-strategies` | Escalate to user |

## Integration Best Practices

1. **Check skill availability** before invocation
2. **Log fallback usage** in provenance.log
3. **Pass complete context** - skills work better with full information
4. **Capture skill output** for next phase
5. **Don't skip integration points** - even if task seems simple
