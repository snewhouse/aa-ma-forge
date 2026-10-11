# Full context injection and goal binding — which AA-MA files to load for a full run, and the optional /goal synthesis and bind for AFK runs.

## Contents

- [2. Full Context Injection](#2-full-context-injection)
- [2.5 Goal Synthesis & Bind (Optional, Recommended for AFK Runs)](#25-goal-synthesis--bind-optional-recommended-for-afk-runs)

## 2. Full Context Injection

**REQUIRED - Auto-inject ALL 5 AA-MA files with XML delimiters:**

```xml
<REFERENCE>
{Read contents of [task-name]-reference.md}
# Immutable facts and constants. Treat as non-negotiable.
</REFERENCE>

<TASKS>
{Read contents of [task-name]-tasks.md}
# HTP roadmap. Current execution scope: FULL PLAN
# Status values: PENDING | ACTIVE | COMPLETE | BLOCKED
</TASKS>

<CONTEXT_LOG>
{Read contents of [task-name]-context-log.md}
# Summarized architectural decisions and unresolved bugs
</CONTEXT_LOG>

<PLAN>
{Read contents of [task-name]-plan.md}
# Original strategy, rationale, and high-level constraints
</PLAN>

<PROVENANCE>
{Read contents of [task-name]-provenance.log}
# Execution telemetry and git history
</PROVENANCE>
```

**Why load all 5**: Full plan execution requires complete context to make informed decisions across multiple milestones.

## 2.5 Goal Synthesis & Bind (Optional, Recommended for AFK Runs)

`/execute-aa-ma-full` is the natural surface for Claude Code's `/goal`
cross-turn driver (https://code.claude.com/docs/en/goal.md). When the user runs
full execution in AFK mode, binding a goal gives the run a measurable,
Haiku-evaluable terminating condition — and a turn cap that acts as a cost
ceiling. The canonical algorithm, verdict enum, and observable-artefact list
live in `Skill(goal-condition-synthesis)`; this section invokes them.

**Skip this section entirely if the user passed `--no-goal` to the command.**

Otherwise execute:

1. **Invoke** `Skill(goal-condition-synthesis)` with:
   - `task-name`: the active task slug
   - `task-dir`: `.claude/dev/active/<task-name>`
   - `mode`: `full-execute`

2. **On `SYNTHESIS_FAILED`:** log the reason (one of the canonical tokens — see
   synthesis SKILL's Failure Modes table) to `<task>-provenance.log` as
   `[TIMESTAMP] GOAL_SYNTHESIS_SKIPPED — reason=<token>`, continue to §3
   without binding a goal.

3. **On `SYNTHESIZED`:** present the proposed condition and turn cap to the
   user via `AskUserQuestion`:

   ```
   📍 Goal Synthesis Complete

   Proposed condition:
   <synthesized condition text>

   Turn cap: <N>
   Observable artefacts referenced: <list>

   Bind this goal for the run?
   ```

   Options:
   - **Bind** — invoke `/goal <condition>` immediately, then proceed to §3.
   - **Edit condition** — display the condition, accept user edits, re-validate
     via `aa_ma.goal_synthesis.validate_condition` (Step 4 of the synthesis
     SKILL), then re-prompt.
   - **Skip /goal** — proceed to §3 without binding. Log
     `[TIMESTAMP] GOAL_BIND_DECLINED — user_choice` to
     `<task>-provenance.log`.

   If the `/goal` slash command is not available in this Claude Code build
   (the slash command errors out, or `disableAllHooks` /
   `allowManagedHooksOnly` is set in managed settings — `/goal` is implemented
   as a Stop-hook wrapper), the user will see the `/goal` error directly;
   log `GOAL_SYNTHESIS_SKIPPED — reason=goal_unavailable` and proceed to §3.

4. **On bind success:** compute `condition_hash` via
   `aa_ma.goal_synthesis.condition_hash(condition)` (or the equivalent shell
   `printf '%s' "$CONDITION_LF_NORMALISED" | sha256sum | cut -c1-12`), then
   append `[TIMESTAMP] GOAL_BOUND — turn_cap=<N> condition_hash=<12-hex>` to
   `<task>-provenance.log`. The condition itself is stored by `/goal`; the
   hash is the cross-reference primitive.

**Mid-run goal lifecycle:**

- If `/goal` reports MET partway through the milestone loop in §5: continue
  execution to the next checkpoint, do **not** stop mid-milestone. The goal's
  job is to terminate at a clean boundary.
- If `/goal` reports turn-cap exhausted: HALT after the current milestone
  finalizes. Surface the evaluator's last reason to the user. Do not
  auto-clear the goal — user owns the lifecycle.
- The user can run `/goal clear` at any point to detach the goal; full
  execution continues without cross-turn drive.

**Why this is opt-in:** Existing aa-ma-forge workflows pre-date `/goal` and
complete fine without it. Goal binding adds Haiku evaluation cost per turn and
a second termination signal that can interact with the milestone-status
terminator. For users new to the integration, milestone-status termination is
enough.
