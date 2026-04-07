# Phase 2: Structured Thinking with Brainstorming

## Objectives
- Refine vague requirements into clear design concept
- Explore alternative approaches
- Validate assumptions through Socratic questioning
- Apply KISS, DRY, SOLID, Separation of Concerns principles

## Skill Integration

**Primary skill:** `superpowers:brainstorming`
**Fallback skill:** `architecture-patterns` (for architectural decisions)

## Step-by-Step Procedure

### 2.1 Invoke Brainstorm Skill

**Primary approach:** Use superpowers brainstorming skill

```
Skill: superpowers:brainstorming
```

Pass to skill:
- User's feature request (from Phase 1)
- Known constraints and requirements
- Project context (language, frameworks discovered)
- Design principles: KISS, DRY, SOLID, SOC (from CLAUDE.md)

The skill will:
- Use Socratic questioning to explore alternatives
- Challenge assumptions and edge cases
- Clarify ambiguous requirements
- Iteratively refine through dialogue
- Produce refined design concept

### 2.2 Architecture Patterns Integration

**Trigger:** When architectural decisions are needed

If the task involves:
- System boundaries or service decomposition
- Data flow patterns or persistence strategies
- Integration patterns or API design
- Scalability or performance architecture

Then also invoke:
```
Skill: architecture-patterns
```

### 2.2b Spec-Driven Development (Advisory)

**Trigger:** Brainstorm output identifies API/service design work.

**Detection signals** (judgment-based, same pattern as architecture-patterns):
- Task involves designing new API endpoints or service contracts
- Discussion mentions consumers, clients, or external integrations
- Schema, specification, or contract-first approaches are relevant

**Action:** Display advisory (see `SKILL_INTEGRATION.md` "Advisory Triggers" section).
This is NOT automatically invoked — it is a recommendation.

**When NOT to trigger:**
- Bug fixes to existing APIs (use standard workflow)
- Internal refactoring that doesn't change API surface
- Tasks where the API spec already exists and isn't changing

### 2.3 Fallback (if superpowers:brainstorming unavailable)

Use native brainstorming prompt:

```
I need to refine this feature request through structured thinking:

REQUEST: [user input]

Analyze using KISS, DRY, SOLID, Separation of Concerns:

1. **Core Problem:** What problem are we actually solving?
2. **Alternative Approaches:** List 3+ different ways to solve this
   - Approach A: [description, pros/cons]
   - Approach B: [description, pros/cons]
   - Approach C: [description, pros/cons]
3. **Key Assumptions:** What are we assuming? How can we validate?
4. **Edge Cases & Constraints:** What could go wrong? What are limits?
5. **Simplified Solution (KISS):** What's the simplest approach that works?

Provide refined requirements in bullet format.
```

**Capture outputs:**
- Refined problem statement
- Chosen approach with rationale
- Validated assumptions
- Identified edge cases
- Simplified design concept

### 2.4 Display Phase Summary

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 2 COMPLETE: Requirements Refined
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ [N] alternatives explored
✓ [N] assumptions validated
✓ Design concept clarified
✓ KISS/DRY/SOLID principles applied
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Phase 2 Checklist

- [ ] Brainstorm skill invoked (or fallback used)
- [ ] At least 3 alternative approaches explored
- [ ] Key assumptions identified and validated
- [ ] Edge cases and constraints documented
- [ ] Simplified approach chosen (KISS principle)
- [ ] Design concept clearly articulated

## Validation Gate 1: Brainstorm Output Validation

**MUST PASS before proceeding to Phase 3:**

| Criterion | Requirement | Check |
|-----------|-------------|-------|
| Alternatives | >= 3 approaches explored | [ ] |
| Assumptions | All key assumptions listed with validation method | [ ] |
| Edge Cases | >= 3 edge cases or constraints identified | [ ] |
| KISS Applied | Simplest viable solution identified | [ ] |
| Design Clarity | Design concept expressible in 2-3 sentences | [ ] |

**On Failure:**
1. Re-run brainstorming with explicit checklist
2. If fails twice, invoke `debugging-strategies` skill
3. Document failure in context-log before proceeding
