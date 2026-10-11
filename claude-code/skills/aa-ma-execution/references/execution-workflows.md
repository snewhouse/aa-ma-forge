# AA-MA execution workflows — how a step, a milestone and a full plan are executed, sub-step by sub-step.

## Contents

- [IV. Execution Workflows](#iv-execution-workflows)
  - [A. Step Execution (Single Task)](#a-step-execution-single-task)
  - [B. Milestone Execution (RECOMMENDED)](#b-milestone-execution-recommended)
  - [C. Full Plan Execution (Automated)](#c-full-plan-execution-automated)

## IV. Execution Workflows

### A. Step Execution (Single Task)

**Use when**: Quick iteration, exploratory work, low-risk changes

**Workflow**:

1. **Mark Task ACTIVE**:
   ```markdown
   ## Task Title
   - Status: ACTIVE  ← Update from PENDING
   ```

1.5. **Mode Dispatch (HITL / AFK)**:
   - Parse `Mode:` from this task (inherit from milestone if absent, default HITL)
   - **HITL**: Display task summary and acceptance criteria, use `AskUserQuestion` [Proceed / Skip / Abort]. Only continue if Proceed.
   - **AFK**: Proceed directly to step 2 without pause

2. **Execute Task**:
   - Follow acceptance criteria exactly
   - Use appropriate tools, agents, skills as needed
   - Document decisions in real-time

3. **Sync Result Log (BLOCKING — L-080/L-082)**:

   **IMMEDIATELY after executing the task — before validation, before moving on:**
   - Write `Status: COMPLETE` on the sub-step in `tasks.md`
   - Write a concise `Result Log:` entry with specific evidence (IDs, counts, pass/fail verdicts, key findings)
   - If the sub-step is not applicable: write `Status: SKIPPED — [reason]`

   **WHY THIS IS BLOCKING**: When the lead orchestrator executes steps directly (not via agents), there is no automatic documentation pathway. Agents auto-populate Result Logs via their prompt contract. The lead orchestrator has no such forcing function — results exist in conversation context but never reach tasks.md unless explicitly written here. This step prevents the sub-step drift that occurs when Result Log updates are deferred to "end of milestone."

   **Verification**: Read back the sub-step in tasks.md to confirm the Result Log is non-empty. If empty, STOP — do not proceed to validation.

4. **Validation (Guidance-based)**:
   - Check acceptance criteria
   - If NOT met: **WARN** user but allow to proceed
   - Log warnings in Result Log:
     ```markdown
     ### Sub-step N.M: [Action]
     - Result Log:
       ⚠️ Acceptance criteria not fully met:
       - [Unmet criterion 1]
       - [Unmet criterion 2]
       [Output and decisions]
     ```

4. **Update State**:
   - Mark task COMPLETE (or leave ACTIVE if continuing)
   - Update Result Log with output
   - Extract new facts → add to `[task-name]-reference.md`
   - Document decisions → add to `[task-name]-context-log.md`

5. **Git Commit & Push**:
   ```bash
   git add .
   git commit -m "feat([task-name]): [brief description]

   Completed AA-MA step: [Task Title]
   Acceptance criteria: [met/partial]

   [AA-MA Plan] [task-name] .claude/dev/active/[task-name]"
   git push
   ```

6. **Log Provenance**:
   ```bash
   echo "[$(date '+%Y-%m-%d %H:%M')] Commit $(git rev-parse --short HEAD) — TaskID: [task-id] — Status: [COMPLETE/PARTIAL]" >> [task-name]-provenance.log
   ```

### B. Milestone Execution (RECOMMENDED)

**Use when**: Delivering complete feature, quality gates required, production changes

**Workflow**:

1. **Identify Milestone Tasks**:
   - Parse `[task-name]-tasks.md` for milestone boundary
   - Collect all tasks in milestone (typically 3-7 related tasks)

2. **Pre-Execution Validation**:
   - Check dependencies: All prerequisite tasks COMPLETE?
   - Check blockers: Any known issues in CONTEXT_LOG?
   - Check resources: Required artifacts available (per REFERENCE)?

   **If validation fails**: **STOP** and report:
   ```
   🚫 MILESTONE BLOCKED

   Unmet dependencies:
   - [Dependency 1]: Status PENDING
   - [Dependency 2]: Missing artifact

   Resolve these before proceeding.
   ```

3. **Execute Milestone Tasks** (in dependency order):
   - For each task in milestone:
     - Mark ACTIVE
     - **Mode Dispatch**: Parse `Mode:` from task (inherit from milestone if absent, default HITL). HITL: display summary + criteria, `AskUserQuestion` [Proceed/Skip/Abort]. AFK: execute directly.
     - Execute (following step workflow — **including step 3: Sync Result Log**)
     - **SUB-STEP SYNC GATE (L-080)**: Before proceeding to the next task, verify:
       - The just-completed sub-step has `Status: COMPLETE` (not PENDING)
       - The `Result Log:` field is non-empty with specific evidence
       - If either check fails: **STOP** — write the Result Log NOW, then continue
     - **STRICT VALIDATION**: Acceptance criteria MUST be met
     - If criteria NOT met: **STOP** entire milestone
     - Mark COMPLETE
     - Update state files

4. **Milestone Sub-Step Consistency Check (L-081 — BLOCKING)**:

   **After all tasks in the milestone are executed, BEFORE post-execution validation:**
   ```
   Count PENDING sub-steps within this milestone in tasks.md.
   If count > 0:
     🚫 MILESTONE BLOCKED — Sub-step drift detected

     [N] sub-steps still marked PENDING within this milestone:
     - [Step X.Y]: Status PENDING, Result Log empty
     - [Step X.Z]: Status PENDING, Result Log empty

     ACTION REQUIRED: Populate each Result Log with evidence from
     execution, then re-run this check. If a step was not applicable,
     mark it: Status: SKIPPED — [reason]

     DO NOT mark the milestone COMPLETE until this check passes.
   ```
   **Only proceed to post-execution validation when count = 0.**

5. **Post-Execution Validation**:
   - **Impact Analysis** (REQUIRED): Invoke `Skill(impact-analysis)` and output consolidated analysis for all files modified in milestone
   - Run tests (if applicable)
   - Verify all acceptance criteria met
   - Check for regressions
   - Verify no HIGH risk impacts remain unresolved

   **If validation fails**: **ROLLBACK**
   ```bash
   # Rollback to last known good state
   git reset --hard [previous-commit]

   # Update task status back to PENDING
   # Log failure in CONTEXT_LOG
   ```

5. **Milestone Completion**:
   - Update all milestone tasks to COMPLETE
   - Extract ALL new facts → `[task-name]-reference.md`
   - Document milestone summary → `[task-name]-context-log.md`:
     ```markdown
     ## [YYYY-MM-DD] Milestone: [Milestone Title] - COMPLETE

     **Acceptance Criteria**: All met ✅

     **Key Decisions**:
     - [Decision 1]
     - [Decision 2]

     **Artifacts Created**:
     - [File 1]
     - [File 2]

     **Tests**: [X] passing

     **Next Milestone**: [Title]
     ```

6. **Git Commit, Tag & Push**:
   ```bash
   git add .
   git commit -m "feat([task-name]): complete milestone [N] - [title]

   Milestone acceptance criteria:
   - ✅ [Criterion 1]
   - ✅ [Criterion 2]

   Artifacts:
   - [Artifact 1]
   - [Artifact 2]

   [AA-MA Plan] [task-name] .claude/dev/active/[task-name]"

   # Optional: Tag milestone
   git tag -a "[task-name]-milestone-[N]" -m "Milestone [N]: [Title]"

   # MUST push commits and tags
   git push && git push --tags
   ```

7. **Log Provenance**:
   ```bash
   echo "[$(date '+%Y-%m-%d %H:%M')] MILESTONE [N] COMPLETE — Commit $(git rev-parse --short HEAD) — Tests: PASS" >> [task-name]-provenance.log
   ```

### C. Full Plan Execution (Automated)

**Use when**: Long-horizon automation, well-defined plan, minimal human-in-the-loop

**Workflow**:

1. **Load Full Plan**:
   - Inject all 5 AA-MA files (required for full execution)
   - Parse entire task hierarchy from `[task-name]-tasks.md`

2. **Build Execution Graph**:
   - Identify all tasks and dependencies
   - Topologically sort by dependencies
   - Identify milestone boundaries

3. **Execute Milestones Sequentially**:
   ```
   For each milestone in plan:
     1. Execute milestone (using Milestone workflow above)
     2. Validate acceptance criteria (STRICT)
     3. If FAIL → STOP entire plan
     4. If PASS → Continue to next milestone
     5. Create checkpoint (git commit + tag)
   ```

4. **Automated Checkpoints**:
   - After each milestone: git commit + tag
   - Save execution state to `[task-name]-tasks.md`
   - Update `[task-name]-context-log.md` with summary

5. **Failure Handling**:
   - If any milestone fails:
     ```
     🚫 FULL PLAN EXECUTION STOPPED

     Failed at: Milestone [N] - [Title]
     Reason: [Failure reason]

     Last successful checkpoint: [task-name]-milestone-[N-1]

     Rollback command:
     git reset --hard [task-name]-milestone-[N-1]

     Review CONTEXT_LOG for details.
     ```

6. **Completion Report**:
   ```
   ✅ FULL PLAN EXECUTION COMPLETE

   Milestones completed: [N]/[N]
   Total tasks: [X]
   Total commits: [Y]
   Execution time: [Duration]

   Final state:
   - All acceptance criteria met ✅
   - All tests passing ✅
   - Artifacts created: [List]

   View provenance log: [task-name]-provenance.log
   ```
