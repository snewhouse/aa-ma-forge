# [task-name] Provenance Log

<!-- AA-MA Provenance Log Template — Audit Trail & Session Resume
     =============================================================
     This file is a machine-readable, append-only log of execution history.
     It records every significant event: initialization, commits, context
     compaction, milestones, and session checkpoints.

     Purpose:
     - Audit trail: trace exactly what happened, when, and in what order
     - Session resume: the latest CHECKPOINT tells the next session exactly
       where to pick up, what to do next, and what context was loaded
     - Git correlation: links task progress to specific commits

     Rules:
     - APPEND ONLY — never edit or delete previous entries
     - One entry per line (except multi-line entries like TASK COMPLETE)
     - Use ISO-style timestamps: [YYYY-MM-DD HH:MM] or [YYYY-MM-DD HH:MM:SS]
     - Write entries IMMEDIATELY when the event occurs, not retroactively

     Entry types are documented below. Delete these HTML comments once
     the file is populated with real entries.
-->

<!-- INITIALIZATION ENTRY
     Written once when the AA-MA task directory is first created.
     Records the task creation event and the project context. -->
<!-- Format:
     [YYYY-MM-DD HH:MM] TASK INITIALIZED — AA-MA directory created
     [YYYY-MM-DD HH:MM] Project: [working directory absolute path]
     [YYYY-MM-DD HH:MM] Plan: [task-name] — Milestones: [N], Steps: [N]
     [YYYY-MM-DD HH:MM] Status: READY FOR EXECUTION -->

[YYYY-MM-DD HH:MM] TASK INITIALIZED — AA-MA directory created
[YYYY-MM-DD HH:MM] Project: [/absolute/path/to/project]
[YYYY-MM-DD HH:MM] Plan: [task-name] — Milestones: [N], Steps: [N]
[YYYY-MM-DD HH:MM] Status: READY FOR EXECUTION

<!-- COMMIT ENTRY
     Written after every git commit that relates to this task.
     Links the commit hash to the specific sub-step being executed. -->
<!-- Format:
     [YYYY-MM-DD HH:MM] Commit [short-hash] — TaskID: step-[N.M]
     Or with a brief description:
     [YYYY-MM-DD HH:MM] Commit [short-hash] — TaskID: step-[N.M] — [description] -->

<!-- CONTEXT COMPACTION ENTRY
     Written when the LLM context window is compacted (summarised and reset)
     to prevent token overflow. Records the event so the audit trail shows
     when context was lost and reconstituted. -->
<!-- Format:
     [YYYY-MM-DD HH:MM] Commit [short-hash] — Context compacted
     Or standalone:
     [YYYY-MM-DD HH:MM] CONTEXT COMPACTED — Summary written to context-log.md -->

<!-- CHECKPOINT ENTRY
     Written when context compaction occurs OR a session ends mid-task.
     This is the MOST IMPORTANT entry type for session resume.
     The next session reads the latest CHECKPOINT to know exactly:
     - Which step was active
     - What the next action should be
     - Which AA-MA files were loaded in context
     - How much of the token budget was used -->
<!-- Format (all on one line):
     [YYYY-MM-DD HH:MM] CHECKPOINT — ActiveStep: [step-id] — NextAction: "[description]" — ContextLoaded: [comma-separated file list] — TokenUsage: [N%]
     Example:
     [2025-10-29 10:15] CHECKPOINT — ActiveStep: 1.3 — NextAction: "Run integration tests" — ContextLoaded: REFERENCE,TASKS — TokenUsage: 68% -->

<!-- MILESTONE COMPLETE ENTRY
     Written when a milestone passes its acceptance criteria and is marked COMPLETE.
     Records the commit hash and how many criteria were verified. -->
<!-- Format:
     [YYYY-MM-DD HH:MM] MILESTONE COMPLETE — Milestone [N] — Commit [short-hash] — Criteria: [X/X] verified
     For HARD-gated milestones, also note the gate approval:
     [YYYY-MM-DD HH:MM] MILESTONE COMPLETE — Milestone [N] (HARD gate) — Commit [short-hash] — Criteria: [X/X] verified — Gate approval: context-log.md -->

<!-- SESSION CHECKPOINT ENTRY
     Written at the END of every session, even if no compaction occurred.
     Ensures the next session can resume cleanly without relying on
     context-log.md summaries alone. Uses the same format as CHECKPOINT. -->
<!-- Format:
     [YYYY-MM-DD HH:MM] CHECKPOINT — ActiveStep: [step-id] — NextAction: "[description]" — ContextLoaded: [file-list] — TokenUsage: [N%] -->

<!-- TASK COMPLETE ENTRY
     Written once when ALL milestones are complete and the task is finalized.
     This is a multi-line entry summarizing the full task outcome. -->
<!-- Format:
     [YYYY-MM-DD HH:MM] TASK COMPLETE — All deliverables created:
       - [deliverable 1]
       - [deliverable 2] -->
