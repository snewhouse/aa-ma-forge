# Phase 4.2 and 4.5: plan reviews and verification — the optional gstack plan reviews and the adversarial verification of the generated plan.

## Contents

  - [Phase 4.2: Optional Plan Reviews (gstack integration)](#phase-42-optional-plan-reviews-gstack-integration)
  - [Phase 4.5: Adversarial Verification](#phase-45-adversarial-verification)

### Phase 4.2: Optional Plan Reviews (gstack integration)

After plan generation, optionally invoke multi-perspective review skills to challenge the plan before verification.

**Step 4.2.1: Prompt for Review Perspectives**

Use `AskUserQuestion` to ask:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PLAN GENERATED — REVIEW PERSPECTIVES?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Which review perspectives before verification?
  [C] CEO Review — challenge scope, find the 10-star product
  [E] Eng Review — architecture, data flow, test matrix
  [D] Design Review — rate design dimensions 0-10 (frontend only)
  [A] All applicable
  [S] Skip all — proceed to verification
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Recommendations:
  • Eng Review: recommended for Complexity >= 50%
  • CEO Review: recommended for new products/major pivots
  • Design Review: auto-skip when no frontend files detected
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Step 4.2.2: Execute Selected Reviews**

Run selected reviews in order: CEO (scope) → Eng (architecture) → Design (if frontend).

**CEO Review** (`Skill(plan-ceo-review)`):
- Challenges premises and scope
- 4 modes: expand, selective expand, hold, reduce
- Read-only — does not modify plan files
- Feed findings into Phase 4.5 verification context

**Eng Review** (`Skill(plan-eng-review)`):
- Architecture, data flow, edge cases, test matrix
- Interactive — may write ARCHITECTURE.md or update plan
- Feed architecture findings into Phase 4.5 verification context

**Design Review** (`Skill(plan-design-review)`):
- Only offered when frontend files detected (`.html`, `.css`, `.tsx`, `.jsx`, `.svelte`, Streamlit)
- Rates design dimensions 0-10
- May suggest plan edits for UX concerns
- Auto-skipped for backend-only/data projects

**Step 4.2.3: Capture Review Metadata**

Record which reviews ran in plan metadata for `/verify-plan` to reference later:

```
## Plan Review History
- CEO Review: [ran/skipped] — [key finding or "N/A"]
- Eng Review: [ran/skipped] — [key finding or "N/A"]
- Design Review: [ran/skipped/auto-skipped (no frontend)] — [key finding or "N/A"]
```

Display summary:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REVIEWS COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ [N] reviews executed
✓ Findings fed into verification context
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Phase 4.5: Adversarial Verification

**Step 4.5.1: Prompt for Verification Mode**

Use `AskUserQuestion` to ask:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PLAN GENERATED — VERIFY?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Run adversarial verification before creating artifacts?
  [A] Automated — CRITICALs block artifact creation
  [I] Interactive — All findings report-only
  [S] Skip — Proceed directly to artifact creation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Step 4.5.2: Run Verification (if not skipped)**

Invoke the plan-verification skill:

```
Skill: plan-verification
```

Pass to the skill:
- Generated plan text from Phase 4
- Project root (pwd)
- User-selected mode (A/I/S)

The skill runs 6 verification angles in two waves:
- Wave 1 (parallel): Ground-truth audit, Assumption challenge, Impact analysis, Criteria falsifiability
- Wave 2 (sequential): Fresh-agent simulation, Specialist domain audit

**Step 4.5.3: Handle Verification Results**

- **PASS:** Proceed to Phase 5
- **PASS WITH WARNINGS:** Display warnings summary, proceed to Phase 5
- **FAIL (automated mode only):** Revise plan to address CRITICALs, re-verify (max 2 loops)
- **SKIPPED:** Proceed to Phase 5 immediately

If revision loop exhausts 2 attempts, present findings to user and ask how to proceed.

**Step 4.5.4: Display Summary**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 4.5 COMPLETE: Verification
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Mode: [Automated | Interactive | Skipped]
CRITICAL: [N] | WARNING: [N] | INFO: [N]
Result: [PASS | FAIL | PASS WITH WARNINGS | SKIPPED]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
