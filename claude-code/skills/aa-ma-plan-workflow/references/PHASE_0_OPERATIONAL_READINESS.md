# Phase 0: Operational Readiness

## Objectives
- Establish disciplined execution mode before planning begins
- Evaluate task complexity for routing decisions
- Identify parallelization opportunities early
- Load operational constraints as session baseline

## When Phase 0 Triggers

Phase 0 activates **automatically** when `/aa-ma-plan` is invoked. It ensures:
1. Operational discipline is established before cognitive load increases
2. Complex tasks (>=60%) get appropriate constraints upfront
3. Research parallelization is planned before Phase 3

## Step-by-Step Procedure

### 0.1 Check Current Operational Mode

Detect if ops-mode is already active:

```
Is Skill(operational-constraints) already loaded?
├── YES → Skip to 0.2 (avoid redundant loading)
└── NO → Load operational constraints
    - Invoke: Skill(operational-constraints)
    - Acknowledge activation with brief confirmation
```

### 0.2 Quick Complexity Heuristic

Before detailed gathering, estimate complexity from initial signals:

**Heuristic Indicators:**

| Signal | Complexity Boost |
|--------|------------------|
| "refactor" or "migrate" in request | +20% |
| Multiple systems mentioned | +15% |
| "integration" or "API" involved | +15% |
| Unfamiliar codebase | +20% |
| External dependencies | +10% |
| "security" or "auth" involved | +15% |
| Database schema changes | +15% |
| "OpenAPI" / "contract-first" / "spec-driven" in request | +10% |

**Quick Estimate Formula:**
```
Base: 30%
+ Sum of applicable indicators
= Quick Complexity Estimate
```

**Routing Decision:**
```
Complexity < 40%  → Continue normally
Complexity 40-60% → Enable ops-mode basics
Complexity >= 60% → Full ops-mode activation mandatory
Complexity >= 80% → Flag for deep architectural review in Phase 4
```

### 0.3 Parallel Opportunity Scan

Before Phase 1 begins, scan for parallel research potential:

**Ask yourself:**
1. Will research span multiple independent domains?
2. Are there 3+ distinct areas requiring investigation?
3. Can codebase exploration happen simultaneously with documentation lookup?

**If YES to any:**
- Flag `PARALLEL_RESEARCH: true` for Phase 3
- Note potential agent dispatch areas

### 0.4 Load Pre-Task Checklist

From `Skill(operational-constraints)`, review:

- [ ] Can this be parallelized? (from 0.3)
- [ ] Is system-mapping needed? (check triggers below)
- [ ] TDD applicable? (will we write code?)
- [ ] Impact analysis required? (will we modify code?)

**System-mapping triggers (for Phase 3):**
- Changes will touch 3+ files
- Code area is unfamiliar to user
- Integrating with external services
- Modifying data pipelines

### 0.5 Display Readiness Status

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 0 COMPLETE: Operational Ready
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Mode: [Standard | Ops-Mode | Full Ops-Mode]
Quick Complexity: [X%]
Parallel Research: [Yes/No]
System-Mapping: [Triggered/Not Needed]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Fallback Behavior

If `Skill(operational-constraints)` is unavailable:
1. Log: "Ops-mode skill unavailable, using inline constraints"
2. Apply core principles inline:
   - Token efficiency
   - Parallel execution evaluation
   - Tool selection hierarchy
3. Continue to Phase 1

## Integration Points

| Downstream | How Phase 0 Feeds |
|------------|-------------------|
| Phase 1 | Complexity estimate informs question depth |
| Phase 3 | `PARALLEL_RESEARCH` flag triggers agent dispatch |
| Phase 3 | System-mapping trigger passed forward |
| Phase 4 | Complexity >= 80% triggers deep architectural review |
| All Phases | Ops-mode discipline maintained |

## Phase 0 Checklist

- [ ] Ops-mode activation checked/confirmed
- [ ] Quick complexity estimate captured (X%)
- [ ] Parallel research opportunity identified (yes/no)
- [ ] System-mapping trigger evaluated
- [ ] Pre-Task Checklist items reviewed
- [ ] Readiness status displayed
