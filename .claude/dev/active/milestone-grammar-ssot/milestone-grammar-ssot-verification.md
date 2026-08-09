# Verification Report: milestone-grammar-ssot
Mode: automated | Angles: 6/6 | Revisions: 3 | Base: b11c46d

## Summary
- CRITICAL: 11 (all addressed in revision 3)
- WARNING: 19
- Result: FAIL on revisions 1 and 2; revision 3 addresses every CRITICAL, each fix verified empirically, but has not itself been through a full 6-angle pass.

## Angle 1 — Ground truth
3 CRITICAL: codemem-benchmark-fairness-v2 3->6 milestones; 6 of 14 files show 0 steps; 2 of 6 "blind tasks" are outside the repo; step-style attributions wrong.
12 claims OK. Off-by-one: aa-ma-parse.sh pattern at :75 not :74.

## Angle 2 — Assumptions
3 CRITICAL: int("2a") ValueError escapes discover_tasks; M2 acceptance unachievable; canonical form is Sub-step not Step (spec has ZERO "### Step").
Verified: goldens .txt/SVG unaffected; suite baseline 783/1/1/7; 65/368 totals; no fenced-heading occurrences.

## Angle 3 — Impact
Milestone.number int->str is the blocking defect; model.py never mentioned. SCHEMA_VERSION must bump. Six grammars, not three -- #5 drives the HARD gate. rules/aa-ma.md is symlinked live. Fixture security-quality-remediation 0->24 steps.

## Angle 4 — Falsifiability
16/32 falsifiable (50%). M1-NB4 empirically false and self-blocking; M2-AC1 machine-local; M4-AC3 vacuous at HEAD; M3-AC2 fixture unspecified; "785+" monotone floor.

## Angle 5 — Fresh-agent simulation
5 CRITICAL: grammar.py API undefined (predecessors return different types); discover_tasks takes list[Path]; pinned table does not exist; 2 of 9 negatives MATCH the mandated regex; int->str breaks 5 test files + golden while M1's test command excluded tests/tui/.

## Angle 6 — Pydantic v2 + Engineering Standards
Pydantic: no lax int->str coercion by default; data.json golden pins number:1 and schema_version:1; 3 tests pin SCHEMA_VERSION==1; test_parser_properties.py:152 is @slow (deselected); --root . returns 23 junk entries, --root .claude returns 14.
Standards: parse_audit_profile returned (None,True,None) for ALL 5 milestones (mid-line + backticked); Critical-Path gate scan requires bold line-anchored form -- the plan reproduced the exact blindness its own M4 exists to fix. M3 mis-profiled docs-only. Theme 3 evidenced but not declared. N_new 22 vs 27.

## Revision history
- v1: 6 CRITICAL -> FAIL
- v2: 5 CRITICAL -> FAIL
- v3: all addressed; each fix verified empirically (separator, --root .claude, field format, discover_tasks signature, SCHEMA_VERSION sites, awk CI check, coerce_numbers_to_str)
