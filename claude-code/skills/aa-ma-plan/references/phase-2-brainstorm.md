# Phase 2: structured thinking — the brainstorming pass that refines the request before research.

## Contents

  - [Phase 2: Structured Thinking with Brainstorming](#phase-2-structured-thinking-with-brainstorming)

### Phase 2: Structured Thinking with Brainstorming

**Step 2.1: Invoke Brainstorm Skill**

```
Skill: superpowers:brainstorming
```

**Step 2.2: Pass Context to Brainstorm**

Provide the skill with:
- User's feature request
- Known constraints
- Project context (language, frameworks from file scan)
- Design principles: KISS, DRY, SOLID, SOC

**Step 2.3: Capture Refined Requirements**

The brainstorm skill will:
- Explore alternatives through Socratic questioning
- Validate assumptions
- Clarify ambiguities
- Produce refined design concept

**Step 2.4: Engineering Standards Declaration**

Reference: `claude-code/rules/engineering-standards.md` (the 6 themes). This step
produces element #12 of the AA-MA Planning Standard.

Use `AskUserQuestion` to capture which themes materially apply and how:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ENGINEERING STANDARDS DECLARATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Which themes from engineering-standards.md materially apply to this task?
  [1] Verification & Truth (empirical testing, prototype-first, critical paths)
  [2] Development Principles (TDD, KISS, DRY, SOLID, SOC)
  [3] Reasoning & Planning (first-principles, Socratic, skill assessment)
  [4] Safety & Continuity (non-breaking, lessons learned, incremental)
  [5] Execution Checklist (per-task HARD/SOFT enforcement)
  [6] Sync & Commit Discipline (sub-step Result Log, milestone HARD gate)
  [A] All themes apply
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Capture the user's selection plus a one-sentence rationale for each chosen theme.
The declaration text becomes element #12 of the plan output (Phase 4).

**Provenance entry (CEO-5):** every Phase 2 declaration writes ONE structured
entry to the task's provenance.log, providing per-plan audit trail and
eliminating the silent-compliance failure mode. Capture `THEMES` here; the
`echo` itself runs once, at the end of Step 2.5, when `PROTO` is also known
(the log is append-only — never edit a line after writing it):

```bash
TS=$(date -Iseconds)
THEMES="[1,2,5]"  # Whatever the user selected, comma-separated.
PROTO="M2,M4"     # Milestones flagged in Step 2.5 (or `none`).
echo "[${TS}] ENG_STANDARDS_DECLARED: themes=${THEMES} prototype=${PROTO}" \
    >> .claude/dev/active/${TASK_NAME}/${TASK_NAME}-provenance.log
```

If the task directory does not yet exist (Phase 5 hasn't run), buffer the entry
in memory and write it at Step 5.6 alongside the other initial provenance lines.

**Fallback (if skill unavailable):**

Use native brainstorming prompt:

```
I need to refine this feature request through structured thinking:

REQUEST: [user input]

Analyze:
1. Core problem being solved
2. Alternative approaches (list 3+)
3. Key assumptions to validate
4. Potential edge cases or constraints
5. Simplified solution (KISS principle)

Provide refined requirements in bullet format.
```

**Step 2.5: Prototype Decision**

Theme 1 ("prototype first on uncertain changes") is a planning-time question,
not something to discover mid-execution. For each milestone whose design is
genuinely uncertain — a state model nobody can reason about on paper, a UI
whose shape is open, an abstraction that might be wrong — use `AskUserQuestion`:

```
Prototype-Required for <milestone>? YES / NO
```

Record every YES: at Step 5.5 write `- Prototype-Required: YES` into that
milestone (or the specific sub-step — a sub-step's YES rolls up to the
milestone gate, ADR-0011) in tasks.md, then write the single
`ENG_STANDARDS_DECLARED` line from Step 2.4 with `prototype=<M-list>` — the
list names the milestone a flagged sub-step rolls up to (`M2,M4`), or
`prototype=none` when nothing is flagged. Never write the field with an empty
value — the gate refuses it (exit 2). Milestones flagged YES run `Skill(prototype)` during execution and
must leave a `[ts] PROTOTYPE — <milestone heading> — <verdict> — verdict-changes-plan: YES|NO`
provenance entry before COMPLETE (§6.7 condition 5); YES triggers a plan-verification
Angle-3 check on the decision delta. This is a step inside Phase 2 —
it writes no `PHASE_2.5` marker.

Display summary:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 2 COMPLETE: Requirements Refined
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Alternatives explored
✓ Assumptions validated
✓ Design concept clarified
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
