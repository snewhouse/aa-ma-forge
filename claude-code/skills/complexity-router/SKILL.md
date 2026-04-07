---
name: complexity-router
description: Estimate task complexity and route high-complexity tasks (>=80%) to deep architectural review - use before plan generation
---

# Complexity Router Skill

Estimates task complexity using a weighted factor algorithm and routes high-complexity tasks (≥80%) to deep architectural review (human review, ultrathinking, or a dedicated architecture skill if available).

## When to Use

- Before plan generation in Phase 4 of aa-ma-plan-workflow
- To determine appropriate level of review for a task
- When deciding between standard vs enhanced validation
- To identify tasks requiring deep reasoning

## Complexity Estimation Algorithm

### Input Factors

| Factor | Weight | Description |
|--------|--------|-------------|
| Scope | 25% | Number of files/components affected |
| Architectural Impact | 25% | Level of system changes |
| Technical Risk | 20% | Unknowns and technical uncertainty |
| Dependencies | 15% | External service/library count |
| Uncertainty | 15% | Requirements ambiguity |

### Factor Scoring (0-100 each)

#### Scope (Files Affected)
```
1-3 files:   0-20
4-10 files:  21-40
11-20 files: 41-60
21-50 files: 61-80
50+ files:   81-100
```

#### Architectural Impact
```
No architecture changes:     0-20
Single component changes:    21-40
Multiple component changes:  41-60
Cross-service changes:       61-80
System-wide changes:         81-100
```

#### Technical Risk
```
Well-understood domain:      0-20
Minor unknowns:              21-40
Moderate unknowns:           41-60
Significant unknowns:        61-80
High uncertainty/new tech:   81-100
```

#### Dependencies
```
No external dependencies:    0-20
1-2 dependencies:            21-40
3-5 dependencies:            41-60
6-10 dependencies:           61-80
10+ dependencies:            81-100
```

#### Uncertainty
```
Clear requirements:          0-20
Minor ambiguity:             21-40
Moderate ambiguity:          41-60
Significant ambiguity:       61-80
High ambiguity:              81-100
```

### Calculation

```
Complexity = (Scope × 0.25) + (ArchImpact × 0.25) +
             (TechRisk × 0.20) + (Deps × 0.15) +
             (Uncertainty × 0.15)
```

## Routing Thresholds

| Complexity | Category | Routing Action |
|------------|----------|----------------|
| 0-29% | Low | Standard workflow, minimal review |
| 30-59% | Medium | Standard workflow with validation |
| 60-79% | High | Enhanced validation, flag in plan |
| **80-100%** | **Critical** | **Deep architectural review (human or dedicated skill)** |

## Auto-Trigger Indicators

The following automatically set complexity ≥80%:

### Architectural Triggers
- [ ] Changes to core authentication/authorization
- [ ] Database schema migrations
- [ ] API contract changes (breaking)
- [ ] Service decomposition or merging
- [ ] New external integrations with SLAs

### Risk Triggers
- [ ] Security-critical functionality
- [ ] Financial transaction handling
- [ ] Personal data processing (GDPR/HIPAA)
- [ ] Performance-critical paths (< 100ms SLA)
- [ ] Multi-team coordination required

### Scale Triggers
- [ ] 50+ files affected
- [ ] 10+ external dependencies
- [ ] Multi-week estimated effort
- [ ] Cross-repository changes

## Procedure

### Step 1: Gather Inputs

From Phase 2-3 outputs:
- Design concept and scope
- Research findings
- Impact assessment results
- Identified risks

### Step 2: Score Each Factor

Rate each factor on 0-100 scale:
```
Scope:         [__]/100
Arch Impact:   [__]/100
Tech Risk:     [__]/100
Dependencies:  [__]/100
Uncertainty:   [__]/100
```

### Step 3: Check Auto-Triggers

Scan for automatic high-complexity indicators:
```
Auto-Triggers Found:
- [ ] [Trigger 1]
- [ ] [Trigger 2]

If any trigger found: Complexity = max(calculated, 80)
```

### Step 4: Calculate and Route

```
Calculated Complexity: [X]%
Auto-Trigger Override: [Yes/No]
Final Complexity: [X]%

Routing Decision: [Standard / Enhanced / Senior-Architect]
```

### Step 5: Generate Report

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
COMPLEXITY ASSESSMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Task: [task-name]
Date: [YYYY-MM-DD]

FACTOR SCORES:
  Scope:              [XX]/100 (weight: 25%)
  Architectural:      [XX]/100 (weight: 25%)
  Technical Risk:     [XX]/100 (weight: 20%)
  Dependencies:       [XX]/100 (weight: 15%)
  Uncertainty:        [XX]/100 (weight: 15%)
  ──────────────────────────────────
  WEIGHTED TOTAL:     [XX]%

AUTO-TRIGGERS:
  [✓/✗] [Trigger description]
  [✓/✗] [Trigger description]

FINAL COMPLEXITY: [XX]% ([Low/Medium/High/Critical])

ROUTING DECISION: [Action]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Integration with aa-ma-plan-workflow

This skill is invoked at the start of Phase 4:

1. Complexity is assessed using this skill
2. If complexity ≥80%, deep architectural review is triggered (human review, ultrathinking, or a dedicated architecture skill)
3. Routing decision recorded in provenance.log
4. Plan generation proceeds with appropriate rigor

## Routing Actions

### Low Complexity (0-29%)
- Standard 5-phase workflow
- Basic validation gates
- No additional review

### Medium Complexity (30-59%)
- Standard 5-phase workflow
- Full validation gates
- Quality score must be ≥70%

### High Complexity (60-79%)
- Full validation gates
- Quality score must be ≥75%
- High-complexity steps flagged
- Recommend milestone-by-milestone execution

### Critical Complexity (80-100%)
- **MUST trigger deep architectural review** (human review, ultrathinking, or a dedicated architecture skill if available)
- Quality score must be ≥80%
- All high-complexity steps require deep reasoning
- Recommend human review before execution

## Checklist

When using this skill:

- [ ] Inputs gathered from Phase 2-3
- [ ] Each factor scored (0-100)
- [ ] Auto-triggers checked
- [ ] Complexity calculated
- [ ] Override applied if triggers found
- [ ] Routing decision made
- [ ] Report generated
- [ ] Decision logged to provenance
