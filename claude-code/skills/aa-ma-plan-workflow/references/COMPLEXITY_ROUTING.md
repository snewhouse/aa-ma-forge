# Complexity Routing Logic

## Overview

Complexity routing determines the appropriate level of review and planning rigor based on task complexity. Tasks with complexity >= 80% automatically route to `senior-architect` for architectural review.

## Complexity Estimation Algorithm

### Input Factors

| Factor | Weight | Scale |
|--------|--------|-------|
| Scope (files affected) | 25% | 0-100 |
| Architectural Impact | 25% | 0-100 |
| Technical Risk | 20% | 0-100 |
| Dependencies | 15% | 0-100 |
| Uncertainty | 15% | 0-100 |

### Factor Scoring

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
Complexity = (Scope × 0.25) + (ArchImpact × 0.25) + (TechRisk × 0.20) + (Deps × 0.15) + (Uncertainty × 0.15)
```

## Routing Thresholds

| Complexity | Category | Routing Action |
|------------|----------|----------------|
| 0-29% | Low | Standard workflow, minimal review |
| 30-59% | Medium | Standard workflow with checklist validation |
| 60-79% | High | Enhanced validation, flag in plan |
| **80-100%** | **Critical** | **MUST route to senior-architect** |

## High Complexity Indicators (Auto >= 80%)

The following indicators automatically set complexity >= 80%:

### Architectural Triggers
- [ ] Changes to core authentication/authorization
- [ ] Database schema migrations
- [ ] API contract changes (breaking)
- [ ] Service decomposition or merging
- [ ] New external integrations with SLAs

### Risk Triggers
- [ ] Security-critical functionality
- [ ] Financial transaction handling
- [ ] Personal data processing (GDPR/HIPAA scope)
- [ ] Performance-critical paths (< 100ms SLA)
- [ ] Multi-team coordination required

### Scale Triggers
- [ ] 50+ files affected
- [ ] 10+ external dependencies
- [ ] Multi-week estimated effort
- [ ] Cross-repository changes

## Routing Actions

### Low Complexity (0-29%)
```
1. Standard 5-phase workflow
2. Minimal validation gates
3. No additional review
```

### Medium Complexity (30-59%)
```
1. Standard 5-phase workflow
2. Full validation gates
3. Quality score must be >= 70%
```

### High Complexity (60-79%)
```
1. Standard 5-phase workflow
2. Full validation gates
3. Quality score must be >= 75%
4. Flag high-complexity steps in plan
5. Recommend milestone-by-milestone execution
```

### Critical Complexity (80-100%)
```
1. Standard 5-phase workflow
2. Full validation gates
3. MUST invoke senior-architect after Phase 4
4. Quality score must be >= 80%
5. All high-complexity steps require deep reasoning
6. Recommend human review before execution
7. Auto-set execution mode to milestone-only
```

## Integration with senior-architect

When complexity >= 80%, invoke senior-architect with:

```
Skill: senior-architect

Pass:
- Generated plan (from Phase 4)
- Complexity score and breakdown
- High-complexity indicators triggered
- Architectural concerns from research

Senior-architect reviews:
- Architectural soundness
- Scalability implications
- Security considerations
- Performance impacts
- Alternative approaches

Returns:
- Approval or rejection
- Required modifications
- Risk assessments
- Recommended safeguards
```

## Complexity Override

User can override complexity:

```
AskUserQuestion:
  Question: Estimated complexity is [X]%. Do you want to:
  Options:
    - Accept and proceed with [routing action]
    - Override to lower complexity (explain why)
    - Override to higher complexity (request more review)
```

**Override logged in provenance.log:**
```
[YYYY-MM-DD HH:MM:SS] Complexity override: [X]% → [Y]% (user: "[reason]")
```

## Complexity Logging

All complexity assessments logged:

```
[YYYY-MM-DD HH:MM:SS] Complexity assessment:
  - Scope: 45/100 (12 files)
  - Arch Impact: 60/100 (cross-component)
  - Tech Risk: 40/100 (moderate unknowns)
  - Dependencies: 30/100 (3 deps)
  - Uncertainty: 25/100 (clear requirements)
  - TOTAL: 43% (Medium)
  - Routing: Standard workflow with validation
```
