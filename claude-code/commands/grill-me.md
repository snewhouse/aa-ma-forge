---
name: grill-me
description: Relentlessly interview the user about a plan, design, proposal, or any artifact until reaching shared understanding
---

# /grill-me - Relentless Plan & Design Interview

Stress-test any artifact in context by walking down every branch of the decision tree.

## Instructions for AI

You are about to interview the user relentlessly about **$ARGUMENTS** (or whatever artifact is currently in context — a plan, architecture design, SOW, email draft, client proposal, API contract, or any other work product).

### Protocol

1. **Identify the artifact.** If `$ARGUMENTS` is provided, focus on that. Otherwise, identify the most recent plan, design, or proposal in the conversation. If nothing is obvious, ask: "What should I grill you on?"

2. **Interview relentlessly.** Walk down each branch of the design/decision tree, resolving dependencies between decisions one-by-one. For each question:
   - Provide your **recommended answer** with reasoning
   - If the question can be answered by **exploring the codebase**, explore the codebase instead of asking
   - Ask **one question at a time** — do not batch questions unless they are truly independent

3. **Cover all angles.** Ensure you probe:
   - **Assumptions** — What are we taking for granted? What if those assumptions are wrong?
   - **Alternatives** — Have we considered other approaches? Why this one over the alternatives?
   - **Dependencies** — What must be true for this to work? What breaks if a dependency changes?
   - **Edge cases** — What happens at the boundaries? Under load? With bad input? With no data?
   - **Scope** — What's in? What's explicitly out? Is the boundary crisp?
   - **Risks** — What's the worst that could happen? What's the recovery plan?
   - **Sequencing** — Does the order matter? Are there hidden dependencies between steps?

4. **Resolve, don't just surface.** Each question should drive toward a decision. When the user answers, confirm the decision and move to the next branch. Track resolved vs open decisions.

5. **Know when to stop.** The interview is complete when every branch of the decision tree has been resolved. Summarize all decisions made and any remaining open items.

### Constraints

- Be opinionated — don't just ask questions, recommend answers
- Be specific — "How will you handle auth?" not "Have you thought about security?"
- Be relentless — don't accept vague answers. Push for specifics.
- Be efficient — if codebase exploration can answer the question, do that instead of asking
- One question at a time — use `AskUserQuestion` for each decision point
