## Revision Loop (Automated Mode Only)

When result is FAIL:

1. **Present** each CRITICAL finding with:
   - What the plan says (the claim)
   - What reality says (the evidence)
   - Suggested fix
2. **Revise** the plan to address each CRITICAL
3. **Re-run** ONLY the angles that produced CRITICALs (not all 6)
4. **Max 2 revision loops** — if still failing after 2 revisions, escalate to user:
   ```
   Plan still has [N] CRITICALs after 2 revision attempts.
   Manual intervention required. See verification report for details.
   ```
5. **Log** each revision in verification.md Revision History section

## Plan Authoring Standards Checklist

Supplementary checklist derived from `~/.claude/rules/plan-authoring-standards.md` (lessons L-054 through L-066). Verification angles should cross-reference these standards when relevant claims or structures appear in the plan. These are not a 7th angle — they are concrete checks that strengthen the existing 6 angles.

| ID | Standard | Relevant Angle(s) | Check |
|----|----------|-------------------|-------|
| L-054 | API Integration Contracts | 1 (Ground-Truth), 6 (Specialist) | Plan specifies exact auth scheme and header name, base URL with env variants, and at least one complete sample request — all verified against OpenAPI spec, not inferred |
| L-055 | Dependency Classification | 2 (Assumptions), 5 (Fresh-Agent) | Every dependency classified as Required / Optional extra / Dev-only with rationale: "Can a user use core value without this package?" |
| L-058 | Schema Documentation Completeness | 1 (Ground-Truth), 6 (Specialist) | Field count in plan matches field count in actual data source (golden file, spec, API example). If unknown, section marked `> INCOMPLETE — verify against golden data before implementing` |
| L-059 | Falsifiable Acceptance Criteria | 4 (Falsifiability) | Every criterion satisfies "Given [input X], system produces [output Y] / raises [error Z]". No banned phrases: "handles edge cases gracefully", "validates input correctly", "works as expected", "behaves correctly for" |
| L-061 | py.typed Deliverable | 5 (Fresh-Agent) | If plan creates a typed Python package with public API, `src/<package>/py.typed` (PEP 561 marker) is in Task 1 deliverables |
| L-062 | CLAUDE.md Content Specification | 5 (Fresh-Agent) | If plan includes "Create CLAUDE.md", it specifies 6 minimum sections: (1) project description, (2) package manager + install cmd, (3) test command with marker tiers, (4) lint + type check cmds, (5) architectural constraints, (6) pointer to architecture doc |
| L-063 | Precision Claims Scope Boundaries | 2 (Assumptions), 4 (Falsifiability) | Any claim that something is "impossible" or "structurally prevented" specifies the exact error class prevented AND a concrete adversarial case that is NOT prevented |
| L-064 | Pydantic Polymorphism | 6 (Specialist) | Any `list[BaseClass]` where subclasses carry unique fields specifies a serialization strategy: discriminator field, in-memory-only annotation, or custom serializer |
| L-065 | State Machine Completeness | 3 (Impact Analysis), 6 (Specialist) | Every non-initial state has an incoming transition, every non-terminal state has an outgoing transition, every terminal state is justified |
| L-066 | Cross-Session Coordination | 5 (Fresh-Agent) | Implementation tasks specify git worktree isolation; no tasks commit directly to main while sibling sessions are active |

**How to use this checklist:** During each verification angle, scan the plan for elements that trigger the relevant standards (column 3). If a standard applies but the plan does not satisfy the check, raise a WARNING (or CRITICAL if the gap would cause implementation failure). Include the lesson ID (e.g., "L-054") in the finding for traceability.

## Integration Points

| Caller | How It Invokes | Mode |
|--------|---------------|------|
| aa-ma-plan Phase 4.5 | After Gate 3, before Phase 5 | User-selected (prompted) |
| `/verify-plan [task]` | Standalone on existing plan | User-selected (prompted) |
| `/execute-aa-ma-milestone` | Pre-execution check | Read-only (warns if missing, doesn't block) |

## Design Reference

Full design rationale: `docs/plans/2026-03-08-aa-ma-plan-verification-design.md`
Evidence base: Lessons L-054, L-058, L-059, L-067, L-068, L-069
