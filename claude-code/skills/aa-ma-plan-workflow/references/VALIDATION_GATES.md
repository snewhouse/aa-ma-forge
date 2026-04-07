# Validation Gates Specification

## Overview

Validation gates are quality checkpoints at phase boundaries. Each gate ensures the output of one phase meets the requirements for the next phase to succeed.

## Gate Architecture

```
Phase 0 → [Gate 0] → Phase 1 → Phase 2 → [Gate 1] → Phase 3 → [Gate 2] → Phase 4 → [Gate 3] → Phase 4.5 → [Gate 3.5] → [ENFORCEMENT] → Phase 5 → [Gate 4] → Complete
```

**Enforcement Gate:** Hard gate between Phase 4 and Phase 5 that prevents skipping artifact creation. See `PHASE_5_ARTIFACT_CREATION.md` for auto-recovery protocol.

**Note:** Phase 0 establishes operational readiness; Phase 1 handles raw user input (no gate required after Phase 1).

---

## Gate 0: Operational Readiness (After Phase 0)

### Purpose
Ensure operational discipline is established and task complexity is assessed before detailed planning begins.

### Criteria

| ID | Criterion | Requirement | Validation Method |
|----|-----------|-------------|-------------------|
| G0.1 | Ops-Mode Decision | Activation decision made (activate/skip) | Check for explicit decision |
| G0.2 | Complexity Estimate | Quick complexity estimate captured (0-100%) | Verify percentage present |
| G0.3 | Parallel Scan | Parallel research opportunities evaluated | Check yes/no flag captured |
| G0.4 | Pre-Task Checklist | Pre-Task Checklist items reviewed | Verify checklist acknowledgment |

### Output Format

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GATE 0: Operational Readiness
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Ops-Mode: [Activated | Skipped | Standard]
✓ Complexity: [X%] estimated
✓ Parallel Research: [Yes | No] opportunities
✓ Pre-Task Checklist: Reviewed

RESULT: PASS / FAIL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Failure Recovery

1. **Missing ops-mode decision:** Prompt for explicit activation decision
2. **Missing complexity:** Re-evaluate using signal indicators
3. **Missing parallel scan:** Quick evaluation of research domains
4. **Second overall failure:** Proceed with defaults (standard mode, sequential research)

---

## Gate 1: Brainstorm Output Validation (After Phase 2)

### Purpose
Ensure brainstorming produced sufficient alternatives and validated assumptions before research begins.

### Criteria

| ID | Criterion | Requirement | Validation Method |
|----|-----------|-------------|-------------------|
| G1.1 | Alternatives | >= 3 approaches explored | Count alternatives in output |
| G1.2 | Assumptions | All key assumptions listed with validation method | Check each assumption has validation |
| G1.3 | Edge Cases | >= 3 edge cases or constraints identified | Count edge cases |
| G1.4 | KISS Applied | Simplest viable solution identified | Check for "simplest" or "KISS" recommendation |
| G1.5 | Design Clarity | Design concept expressible in 2-3 sentences | Check summary length |

### Output Format

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GATE 1: Brainstorm Validation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Alternatives: [N] explored (required: 3+)
✓ Assumptions: [N] listed, [N] validated
✓ Edge Cases: [N] identified (required: 3+)
✓ KISS: Simplest solution identified
✓ Design Clarity: Summary is [N] sentences

RESULT: PASS / FAIL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Failure Recovery

1. **First failure:** Re-run brainstorming with explicit checklist prompt
2. **Second failure:** Invoke `debugging-strategies` skill
3. **Third failure:** Escalate to user, document in context-log

---

## Gate 2: Research Completeness (After Phase 3)

### Purpose
Ensure research covered all identified needs and conflicts are resolved.

### Criteria

| ID | Criterion | Requirement | Validation Method |
|----|-----------|-------------|-------------------|
| G2.1 | Coverage | All research needs from Phase 2 addressed | Cross-reference needs vs findings |
| G2.2 | Sources | Each finding has documented source | Check source attribution |
| G2.3 | Conflicts | Any conflicting info resolved or escalated | Check for unresolved conflicts |
| G2.4 | Impact | Upstream callers identified for modified files | Verify impact assessment present |
| G2.5 | Dependencies | All external dependencies documented with versions | Check dependency list completeness |

### Output Format

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GATE 2: Research Completeness
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Coverage: [N]/[M] research needs addressed
✓ Sources: All findings have attribution
✓ Conflicts: [N] conflicts, [N] resolved
✓ Impact: Upstream callers documented
✓ Dependencies: [N] dependencies with versions

RESULT: PASS / FAIL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Failure Recovery

1. **Coverage gaps:** Dispatch additional research for missing areas
2. **Unresolved conflicts:** Use `AskUserQuestion` for user decision
3. **Missing impact:** Re-run impact analysis with explicit targets
4. **Second overall failure:** Invoke `debugging-strategies` skill

---

## Gate 3: Criteria Quality (After Phase 4)

### Purpose
Ensure acceptance criteria are testable, specific, and achievable.

### Criteria

| ID | Criterion | Requirement | Validation Method |
|----|-----------|-------------|-------------------|
| G3.1 | Testability | Each criterion can be verified programmatically or manually | Parse for measurable outcomes |
| G3.2 | Specificity | No criterion uses vague terms | Check for banned words |
| G3.3 | Achievability | Each criterion is realistically achievable | Scope vs effort assessment |
| G3.4 | Independence | Criteria don't have circular dependencies | Dependency graph analysis |
| G3.5 | Quality Score | Plan quality score >= 70% | Inline quality checklist |

### Banned Vague Terms

```
- "works correctly"
- "performs well"
- "is fast"
- "looks good"
- "is complete"
- "is stable"
- "is secure" (without specific controls)
```

### Output Format

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GATE 3: Criteria Quality
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Testability: [N]/[M] criteria verifiable
✓ Specificity: No vague terms found
✓ Achievability: All criteria within scope
✓ Independence: No circular dependencies
✓ Quality Score: [X]% (required: 70%+)

RESULT: PASS / FAIL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Failure Recovery

1. **Testability issues:** Rewrite criteria with measurable outcomes
2. **Vague terms:** Replace with specific, quantified statements
3. **Low quality score:** Re-generate plan with feedback
4. **Second overall failure:** Invoke `debugging-strategies` skill

---

## Gate 3.5: Verification Results (After Phase 4.5)

### Purpose
Ensure plan has been verified against external reality and all critical findings resolved before artifact creation.

### Criteria

| ID | Criterion | Requirement | Validation Method |
|----|-----------|-------------|-------------------|
| G3.5.1 | Mode Selected | User chose automated/interactive/skip | Check explicit choice recorded |
| G3.5.2 | Verification Run | If not skipped, all 6 angles executed | Check angle count in report |
| G3.5.3 | CRITICALs Resolved | 0 unresolved CRITICALs (automated mode) | Count in verification report |
| G3.5.4 | Report Generated | verification.md created or updated | File existence check |

### Output Format

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GATE 3.5: Verification Results
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Mode: [Automated | Interactive | Skipped]
✓ Angles Run: [N]/6
✓ CRITICALs: [N] found, [M] resolved
✓ Report: [Generated | Skipped]

RESULT: PASS / FAIL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Mode-Specific Behavior

| Mode | Pass Condition | Fail Condition |
|------|---------------|---------------|
| Automated | 0 unresolved CRITICALs + report generated | Any unresolved CRITICAL |
| Interactive | Report generated + findings presented | N/A (always passes) |
| Skip | Always passes | N/A |

### Failure Recovery

1. **Unresolved CRITICALs:** Revise plan to address each, re-run affected angles (max 2 loops)
2. **Angle execution failure:** Re-dispatch failed angle agent
3. **Second overall failure:** Escalate to user with full verification report

---

## Gate 4: Cross-File Consistency (After Phase 5)

### Purpose
Ensure all 5 AA-MA files are consistent with each other. Uses the `aa-ma-validator` agent for thorough verification when available.

### Criteria

| ID | Criterion | Requirement | Validation Method |
|----|-----------|-------------|-------------------|
| G4.1 | Fact Consistency | All facts in reference.md appear in plan.md | Cross-reference facts |
| G4.2 | Task Alignment | All tasks.md milestones match plan.md milestones | Compare milestone lists |
| G4.3 | No Contradictions | No conflicting information between files | Semantic analysis |
| G4.4 | Complete Coverage | All plan elements represented across files | Checklist verification |
| G4.5 | Valid References | All cross-references between files are valid | Link validation |
| G4.6 | Validator Verdict | aa-ma-validator reports PASS or WARN (not FAIL) | Validator agent report |

### Consistency Checks

```
plan.md ←→ reference.md
- Every API endpoint in plan appears in reference
- Every file path in plan appears in reference
- Configuration values match

plan.md ←→ tasks.md
- Milestone count matches
- Milestone titles match
- Step count per milestone matches

reference.md ←→ tasks.md
- Dependencies referenced in tasks exist in reference
- File paths in tasks exist in reference

context-log.md ←→ plan.md
- Decisions in context-log align with plan choices
- No contradictory rationale
```

### Output Format

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GATE 4: Cross-File Consistency
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Fact Consistency: [N] facts verified
✓ Task Alignment: [N] milestones match
✓ No Contradictions: 0 conflicts found
✓ Complete Coverage: All elements present
✓ Valid References: All links valid

RESULT: PASS / FAIL
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Validator-Enhanced Checking

When the `aa-ma-validator` agent is available (defined at `~/.claude/agents/aa-ma-validator.md`):

1. Spawn validator with `post-creation` context
2. Validator runs 5-dimension analysis (existence, plan completeness, reference completeness, HTP structure, cross-file consistency)
3. Gate 4 passes if validator verdict is PASS or WARN
4. Gate 4 fails if validator verdict is FAIL

This supplements (does not replace) the manual consistency checks above. The validator provides a structured, repeatable verification that catches issues the manual checks might miss.

### Failure Recovery

1. **Inconsistencies:** Fix specific inconsistencies identified
2. **Missing coverage:** Add missing elements to appropriate files
3. **Invalid references:** Update or remove broken links
4. **Validator FAIL:** Re-spawn scribe to fix identified issues, then re-validate
5. **Second overall failure:** Manual review required

---

## Gate Failure Escalation

```
Attempt 1: Automatic fix attempt
Attempt 2: Invoke debugging-strategies skill
Attempt 3: Escalate to user with:
  - Specific failures identified
  - Attempted fixes
  - Recommendations for manual resolution
```

## Gate Metrics Logging

All gate results logged to provenance.log:

```
[YYYY-MM-DD HH:MM:SS] Gate 1: PASS (5/5 criteria)
[YYYY-MM-DD HH:MM:SS] Gate 2: PASS (5/5 criteria)
[YYYY-MM-DD HH:MM:SS] Gate 3: FAIL (4/5 criteria) - Attempt 1
[YYYY-MM-DD HH:MM:SS] Gate 3: PASS (5/5 criteria) - Attempt 2
[YYYY-MM-DD HH:MM:SS] Gate 4: PASS (5/5 criteria)
```
