# Verification Report: [task-name]
Generated: [YYYY-MM-DDTHH:MM:SSZ] | Mode: [automated|interactive] | Revision: 1

## Summary
- CRITICAL: [N] findings ([M] resolved)
- WARNING: [N] findings
- INFO: [N] findings
- Overall: [PASS | FAIL | PASS WITH WARNINGS | SKIPPED]

## Angle 1: Ground-Truth Audit

Verifies that every factual claim in the plan (file paths, class names, API endpoints, config values, library versions) matches what actually exists in the codebase.

### Findings

<!-- One entry per verified claim. Use one of these formats: -->
<!-- - [CRITICAL] Claim: "X" | Reality: "Y" | Source: file:line -->
<!-- - [WARNING] Claim: "X" | Cannot verify — no evidence found -->
<!-- - [OK] Claim: "X" | Confirmed at file:line -->

No findings — all claims verified.

## Angle 2: Assumption Extraction & Challenge

Extracts every assumption (explicit and implicit) from the plan and challenges each one against evidence in the codebase.

### Assumptions Identified

<!-- One entry per assumption. Use one of these formats: -->
<!-- - [VERIFIED] "assumption text" — evidence: file:line -->
<!-- - [WARNING] "assumption text" — no evidence found, risk if wrong: [description] -->
<!-- - [CRITICAL] "assumption text" — contradicted by: file:line, actual: "Y" -->

1. [VERIFIED|WARNING|CRITICAL] "assumption text" — evidence or risk

## Angle 3: Impact Analysis on Proposed Changes

For each file the plan proposes to create, modify, or delete, assesses upstream callers, downstream dependencies, contract changes, test coverage, and side effects.

### Files Affected

<!-- One entry per file. Use one of these formats: -->
<!-- - [CRITICAL] file.py — HIGH risk: N callers, contract change, plan doesn't address -->
<!-- - [WARNING] file.py — MEDIUM risk: N callers, suggest adding mitigation -->
<!-- - [OK] file.py — LOW risk: N callers, plan accounts for changes -->

## Angle 4: Acceptance Criteria Falsifiability

Audits each acceptance criterion for testability. A criterion is falsifiable if a concrete pytest assertion can be written for it.

### Criteria Audit

<!-- One entry per criterion. Use one of these formats: -->
<!-- - [OK] M[n]-S[n]: "criterion text" → assert [assertion] -->
<!-- - [WARNING] M[n]-S[n]: "criterion text" → unfalsifiable. Suggested: "[rewrite]" -->

### Score: [N]/[M] falsifiable ([X]%)

## Angle 5: Fresh-Agent Simulation

Simulates a developer with zero project context attempting to implement Task 1 from the plan alone. Identifies gaps in paths, install commands, test commands, and acceptance criteria.

### Implementation Barriers

<!-- One entry per barrier. Use one of these formats: -->
<!-- - [CRITICAL] Cannot start: "[blocking gap description]" -->
<!-- - [WARNING] Ambiguous: "[needs clarification description]" -->
<!-- - [INFO] Suggestion: "[nice to have improvement]" -->

## Angle 6: Specialist Domain Audit

Dispatches domain-specific experts based on plan keywords (Pydantic, API, schema, database, security). Each specialist reviews the plan through their domain lens.

### Specialists Dispatched: [list or "None — no domain keywords detected"]

<!-- One entry per specialist finding. Use one of these formats: -->
<!-- - [CRITICAL] [domain] risk: "[description with evidence]" -->
<!-- - [WARNING] [domain] concern: "[description]" -->
<!-- - [INFO] [domain] suggestion: "[description]" -->

## Revision History

<!-- One entry per verification run. Format: -->
<!-- - v[N]: [YYYY-MM-DD] — [summary: N CRITICAL, N WARNING → PASS|FAIL|PASS WITH WARNINGS] -->
<!-- If plan was revised to address findings, note what changed. -->

- v1: [YYYY-MM-DD] — Initial verification: [N] CRITICAL, [N] WARNING → [result]
