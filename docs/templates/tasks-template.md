# [task-name] Tasks (HTP)

<!-- AA-MA Tasks Template — Hierarchical Task Planning (HTP) Roadmap
     ================================================================
     This file is the execution roadmap for the task. It models milestones
     as high-level nodes and sub-steps as low-level actions, with explicit
     dependencies, state tracking, and result logging.

     HTP replaces simple checklists with structured hierarchy:
       ## Milestone = High-level goal with acceptance criteria and gate control
       ### Sub-step = Concrete action that produces a verifiable result

     Key principles:
     - All statuses start as PENDING
     - Mark ACTIVE when work begins, COMPLETE when acceptance criteria are met
     - Never proceed to the next task until the current task is fully synced
     - Complexity >= 80% requires human review or Chain-of-Thought reasoning
     - Result Log is MANDATORY after every sub-step — never batch to end of milestone

     Replace all [bracketed placeholders] with actual values.
     Delete these HTML comments once the file is populated.
-->

_Hierarchical Task Planning roadmap with dependencies and state tracking._

## Milestone 1: [Title]

<!-- Milestone = a high-level goal with measurable acceptance criteria.
     Every milestone MUST include ALL of these fields. -->

<!-- Status: PENDING | ACTIVE | COMPLETE
     - PENDING: not yet started
     - ACTIVE: work in progress (only ONE milestone should be ACTIVE at a time)
     - COMPLETE: all sub-steps done and acceptance criteria verified -->
- Status: PENDING

<!-- Dependencies: list prerequisite milestone IDs, or "None" if this is the first.
     Example: "Milestone 1" or "Milestones 1, 2" -->
- **Dependencies:** None

<!-- Complexity: 0-100%. Measures implementation difficulty.
     - 0-40%: straightforward, well-understood work
     - 41-79%: moderate complexity, some unknowns
     - 80-100%: HIGH COMPLEXITY — requires human review or deep reasoning
     Append the warning flag when >= 80%: "85% ⚠️ HIGH COMPLEXITY" -->
- **Complexity:** [N%]

<!-- Gate: SOFT | HARD — controls how finalization enforces human approval.
     - SOFT (default): convention-based — agent is instructed to seek approval
     - HARD: artifact-enforced — execution commands REFUSE to advance without
       a signed approval entry in context-log.md (see spec §IX Gate Classification)
     Use HARD for: irreversible actions, architectural decisions, external API
     integrations, production deployments -->
- **Gate:** SOFT

<!-- Mode: HITL | AFK — controls whether the task requires human interaction.
     - HITL (Human In The Loop): pauses for user input, review, or decision
     - AFK (Away From Keyboard): can be fully auto-dispatched to agents
     Use HITL for: architectural decisions, client-facing language, scope changes,
     irreversible actions, external API credential setup
     Use AFK for: implementation from clear specs, test writing, file creation,
     mechanical refactoring, documentation generation -->
- **Mode:** AFK

<!-- Acceptance Criteria: measurable, falsifiable conditions that prove the milestone
     is complete. Each criterion MUST be testable — if you cannot write a single-line
     pytest assertion from it, the criterion is not specific enough.
     Banned phrases: "handles edge cases gracefully", "works as expected",
     "validates input correctly", "behaves correctly for" -->
- **Acceptance Criteria:**
  - [Criterion 1 — must be testable and specific]
  - [Criterion 2]

### Sub-step 1.1: [Action description]

<!-- Sub-step = a concrete, atomic action that produces a verifiable result.
     Sub-steps live under their parent milestone (### under ##). -->

<!-- Status: PENDING | ACTIVE | COMPLETE -->
- Status: PENDING

<!-- Mode: HITL | AFK — inherited from milestone unless overridden.
     Override when a specific sub-step needs human input even though the
     milestone is AFK, or vice versa. -->
- **Mode:** AFK

<!-- Dependencies: list prerequisite sub-step IDs within this milestone,
     or "None" if this is the first sub-step.
     Example: "Step 1.1" or "Steps 1.1, 1.2" -->
- **Dependencies:** None

<!-- Acceptance Criteria: specific conditions for THIS sub-step.
     Optional at sub-step level if the milestone criteria are sufficient. -->
- **Acceptance Criteria:**
  - [Specific condition for this sub-step]

<!-- Result Log: MANDATORY after completion. Write specific evidence:
     commit hashes, test pass/fail counts, file paths created, error messages fixed.
     NEVER leave blank after marking COMPLETE.
     NEVER batch Result Log updates to "end of milestone" — this is the #1 cause
     of sub-step drift. Write immediately after each sub-step completes. -->
- **Result Log:**

### Sub-step 1.2: [Action description]
- Status: PENDING
- **Mode:** AFK
- **Dependencies:** Step 1.1
- **Acceptance Criteria:**
  - [Specific condition for this sub-step]
- **Result Log:**

---

## Milestone 2: [Title]
- Status: PENDING
- **Dependencies:** Milestone 1
- **Complexity:** [N%]
- **Gate:** SOFT
- **Mode:** HITL
- **Acceptance Criteria:**
  - [Criterion 1]
  - [Criterion 2]

### Sub-step 2.1: [Action description]
- Status: PENDING
- **Mode:** HITL
- **Dependencies:** None
- **Acceptance Criteria:**
  - [Specific condition for this sub-step]
- **Result Log:**

### Sub-step 2.2: [Action description]
- Status: PENDING
- **Mode:** AFK
- **Dependencies:** Step 2.1
- **Acceptance Criteria:**
  - [Specific condition for this sub-step]
- **Result Log:**
