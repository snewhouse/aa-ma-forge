# [task-name] Context Log

<!-- Copy this template to .claude/dev/active/[task-name]/[task-name]-context-log.md -->
<!-- Replace all [bracketed-values] with actual content -->
<!-- -->
<!-- PURPOSE: This log captures the decision history of the task — architectural choices, -->
<!-- trade-offs, approvals, compaction summaries, and anything that future sessions need -->
<!-- to understand WHY the task evolved the way it did. -->
<!-- -->
<!-- RULES: -->
<!--   - Entries are append-only — never delete or rewrite past entries -->
<!--   - Each entry must have a date header in [YYYY-MM-DD] format -->
<!--   - New entries go at the BOTTOM of the file (chronological order) -->
<!--   - This file is loaded on-demand (Tier 3 priority) — only when making decisions -->
<!--   - Keep entries concise; the goal is decision traceability, not a narrative -->

---

## [YYYY-MM-DD] Plan Approved

<!-- WHEN: Immediately after the user approves the plan (Phase 5 of /aa-ma-plan). -->
<!-- This is always the FIRST entry in the context log. -->
<!-- Required by the Plan Approval Gate (spec Section XI). -->

- Plan: [task-name]
- Approved by: [user name]
- Milestones: [count]
- HARD gates: [list of milestone IDs with Gate: HARD, or "None"]

---

## [YYYY-MM-DD] Initial Context

<!-- WHEN: Written by the scribe agent during AA-MA file creation (Phase 5). -->
<!-- Captures the brainstorming and research that shaped the plan. -->

**Feature Request (Phase 1):**

<!-- The original user input, verbatim if available. -->

[Original request or problem statement]

**Key Decisions (Phase 2 Brainstorming):**

<!-- One entry per decision made during planning. Use the AD-NNN format. -->
<!-- Number decisions sequentially: AD-001, AD-002, etc. -->

- **Decision AD-001:** [What was decided]
  - **Rationale:** [Why this choice was made]
  - **Alternatives Considered:** [What else was evaluated and why it was rejected]
  - **Trade-offs:** [What was gained and what was sacrificed]

- **Decision AD-002:** [What was decided]
  - **Rationale:** [Why]
  - **Alternatives Considered:** [What else]
  - **Trade-offs:** [Gains vs sacrifices]

<!-- Repeat for each key decision. -->

**Research Findings (Phase 3):**

<!-- Factual findings from research. Verified facts should also go in reference.md. -->

- [Finding 1 — with source if available]
- [Finding 2]

**Remaining Questions / Unresolved Issues:**

<!-- Questions that could not be answered during planning. -->
<!-- These may become blockers during execution. -->

- [Question]: [Why it remains unresolved, and when it should be resolved]

---

<!-- ============================================================ -->
<!-- ENTRY TYPE REFERENCE -->
<!-- The sections below show the format for each entry type. -->
<!-- Copy the relevant format when adding new entries during execution. -->
<!-- ============================================================ -->

<!-- ============================================================ -->
<!-- ENTRY TYPE: Architectural Decision -->
<!-- WHEN: Any time a design choice is made during execution that -->
<!--       was not covered in the original plan. -->
<!-- ============================================================ -->

<!--
## [YYYY-MM-DD] Decision: [Short Title]

- **Decision AD-NNN:** [What was decided]
  - **Rationale:** [Why — with evidence from code, docs, or testing]
  - **Alternatives Considered:**
    1. [Alternative A] — rejected because [reason]
    2. [Alternative B] — rejected because [reason]
  - **Trade-offs:** [What was gained vs what was sacrificed]
  - **Impact:** [Which files, milestones, or steps are affected]
-->

<!-- ============================================================ -->
<!-- ENTRY TYPE: Gate Approval (HARD gates) -->
<!-- WHEN: A milestone with Gate: HARD requires explicit user approval -->
<!--       before it can be marked COMPLETE. -->
<!-- Required by spec Section IX — the /execute-aa-ma-milestone -->
<!-- finalization protocol checks for this artifact. -->
<!-- ============================================================ -->

<!--
## [YYYY-MM-DD] GATE APPROVAL: [Milestone Title]

- Gate: HARD
- Approved by: [user name]
- Criteria verified: [X/X — number of acceptance criteria passed]
- Decision: APPROVED
- Notes: [Any conditions or caveats on the approval]
-->

<!-- ============================================================ -->
<!-- ENTRY TYPE: Compaction Summary -->
<!-- WHEN: Context compaction occurs (at ~70% token usage) and the -->
<!--       conversation history is being compressed. Captures key -->
<!--       state so the compacted context retains decision history. -->
<!-- ============================================================ -->

<!--
## [YYYY-MM-DD] Compaction Summary

- **Active step:** [Step ID — e.g., 2.3]
- **Key decisions since last compaction:**
  - [Decision summary 1]
  - [Decision summary 2]
- **Bugs resolved:** [Brief description, or "None"]
- **Remaining issues:** [Brief description, or "None"]
- **Token usage at compaction:** [N%]
-->

<!-- ============================================================ -->
<!-- ENTRY TYPE: Milestone Completion -->
<!-- WHEN: A milestone is fully complete — all steps done, all -->
<!--       acceptance criteria verified, all artifacts delivered. -->
<!-- ============================================================ -->

<!--
## [YYYY-MM-DD] Milestone Complete: [Milestone Title]

- **Milestone:** [N] — [Title]
- **Steps completed:** [X/X]
- **Acceptance criteria:** [X/X verified]
- **Key deliverables:**
  - [File or artefact 1]
  - [File or artefact 2]
- **Commit:** [hash] — [commit message summary]
- **Lessons learned:** [Anything that should inform future milestones]
-->

<!-- ============================================================ -->
<!-- ENTRY TYPE: Bug Discovery -->
<!-- WHEN: A bug is found during execution — whether related to -->
<!--       the current task or pre-existing. Document it here so -->
<!--       the fix rationale is traceable. -->
<!-- ============================================================ -->

<!--
## [YYYY-MM-DD] Bug: [Short Description]

- **Discovered during:** [Step ID or activity]
- **Severity:** [CRITICAL / HIGH / MEDIUM / LOW]
- **Root cause:** [What caused the bug]
- **Fix:** [What was changed to resolve it]
- **Files affected:** [List of files modified]
- **Tests added:** [Test names or "existing tests now pass"]
- **Commit:** [hash]
-->

<!-- ============================================================ -->
<!-- ENTRY TYPE: Research Finding -->
<!-- WHEN: New information is discovered during execution that -->
<!--       affects the plan — API behavior, library limitations, -->
<!--       performance characteristics, etc. -->
<!-- Verified facts should also be added to reference.md. -->
<!-- ============================================================ -->

<!--
## [YYYY-MM-DD] Research: [Topic]

- **Question:** [What needed to be answered]
- **Finding:** [What was discovered]
- **Source:** [URL, file:line, API response, or experiment]
- **Impact on plan:** [How this changes the approach, or "None — confirms plan"]
- **Action:** [What needs to change — update reference.md, modify step, add risk]
-->

<!-- ============================================================ -->
<!-- ENTRY TYPE: Scope Change -->
<!-- WHEN: The plan scope changes after approval — features added, -->
<!--       removed, or modified based on new information. -->
<!-- ============================================================ -->

<!--
## [YYYY-MM-DD] Scope Change: [Short Description]

- **Change:** [What was added, removed, or modified]
- **Reason:** [Why the change is necessary]
- **Requested by:** [User or discovered during step N.M]
- **Impact:**
  - Tasks added: [list or "None"]
  - Tasks removed: [list or "None"]
  - Tasks modified: [list or "None"]
  - Effort change: [+/- hours]
- **Plan updated:** [yes/no — if yes, which sections]
-->

<!-- ============================================================ -->
<!-- ENTRY TYPE: Session Boundary -->
<!-- WHEN: A session ends and work will continue in a new session. -->
<!-- Complements the CHECKPOINT entry in provenance.log. -->
<!-- ============================================================ -->

<!--
## [YYYY-MM-DD] Session End

- **Last completed:** [Step ID]
- **Next step:** [Step ID] — [brief description of what to do]
- **Blockers:** [Any blockers for the next session, or "None"]
- **Context to load:** [Which AA-MA files the next session should prioritize]
-->
