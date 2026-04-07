# Advanced Agentic Memory Architecture (AA-MA) — Specification

> **Version:** 2.1 (2026-04-05: Added HARD/SOFT gate classification, optional tests.yaml, CHECKPOINT format, plan approval gate, actionable Quality Standards. Inspired by Helix.ml spec-driven workflow research.)
> **Canonical reference** for the AA-MA system. Referenced by CLAUDE.md, skills, and commands.
> **Quick reference:** [aa-ma-quick-reference.md](aa-ma-quick-reference.md)
> **Team guide:** [aa-ma-team-guide.md](aa-ma-team-guide.md)

---

## I. Executive Summary

The Advanced Agentic Memory Architecture (AA-MA) provides a structured external memory system for Claude, designed for long-horizon software and data development. It explicitly manages task context, history, and state to prevent context drift and LLM amnesia. Use AA-MA when developing complex systems, running multi-step analyses, or maintaining continuity across sessions.

---

## II. File Taxonomy

The system uses five specialised documents to segment knowledge, ensuring Claude can efficiently retrieve and prioritise facts, state, and history.

| File Name               | Purpose                                                                                           | Citation |
| ----------------------- | ------------------------------------------------------------------------------------------------- | -------- |
| `[task]-plan.md`        | Core strategy, rationale, and high-level constraints.                                             | [2]      |
| `[task]-reference.md`   | **Strict, immutable facts** (APIs, file paths, constants, finalised specs). High-priority memory. | [2]      |
| `[task]-context-log.md` | Summarised history of architectural decisions, trade-offs, and unresolved bugs (via Compaction).  | [1]      |
| `[task]-tasks.md`       | Hierarchical execution roadmap, dependencies, and persistent state tracking (HTP).                | [6]      |
| `[task]-provenance.log` | Machine-readable log of execution history and Git activity (Telemetry).                           | [7]      |
| `[task]-tests.yaml`     | **Optional.** Machine-readable test definitions linked to milestone acceptance criteria.           | [8]      |
| `[task]-verification.md` | **Optional.** Adversarial verification audit trail from 6 independent angles.                     | [9]      |

### Optional: Adversarial Verification Report

The `[task]-verification.md` file stores the results of structured adversarial verification run against the plan before execution begins. It is produced by the `/verify-plan` command or Phase 4.5 of the `/aa-ma-plan` workflow.

**When it exists:**
- Documents findings from 6 independent verification angles (ground-truth audit, assumption challenge, impact analysis, acceptance criteria falsifiability, fresh-agent simulation, specialist domain audit)
- Classifies each finding as CRITICAL, WARNING, or INFO
- Records the overall verdict (PASS, FAIL, or PASS WITH WARNINGS)
- Tracks revision history when the plan is revised to address findings

**When it is absent:**
- The user chose to skip verification, or verification has not been run yet
- No execution commands are blocked — verification is advisory, not a gate

**Structure:**

```markdown
# Verification Report: [task-name]
Generated: [ISO-8601 timestamp] | Mode: [automated|interactive] | Revision: [N]

## Summary
- CRITICAL: [N] findings ([M] resolved)
- WARNING: [N] findings
- INFO: [N] findings
- Overall: [PASS | FAIL | PASS WITH WARNINGS | SKIPPED]

## Angle 1: Ground-Truth Audit
### Findings
- [SEVERITY] Claim: "X" | Reality: "Y" | Source: file:line
[or "No findings — all claims verified."]

## Angle 2: Assumption Extraction & Challenge
### Assumptions Identified
1. [VERIFIED|WARNING|CRITICAL] "assumption text" — evidence/risk

## Angle 3: Impact Analysis on Proposed Changes
### Files Affected
- [SEVERITY] file.py — [risk level]: [description]

## Angle 4: Acceptance Criteria Falsifiability
### Criteria Audit
- [OK|WARNING] M[n]-S[n]: "criterion text" → assertion or rewrite
### Score: [N]/[M] falsifiable ([X]%)

## Angle 5: Fresh-Agent Simulation
### Implementation Barriers
- [SEVERITY] "[description of gap or ambiguity]"

## Angle 6: Specialist Domain Audit
### Specialists Dispatched: [list or "None — no domain keywords detected"]
- [SEVERITY] [domain] risk/concern: "[description]"

## Revision History
- v[N]: [date] — [summary: N CRITICAL, N WARNING → result]
```

**Design principles:**
- Each angle runs independently and catches a categorically different class of error
- Findings are de-duplicated across angles (the most specific version is kept)
- In automated mode, CRITICAL findings block plan artifact creation; in interactive mode, all findings are report-only
- Revision history provides a full audit trail of plan improvements
- The file is optional — its absence never blocks execution

### Optional: Executable Test Definitions

The `[task]-tests.yaml` file provides machine-executable test stubs that bridge prose acceptance criteria in `tasks.md` with actual verification. When present, `/execute-aa-ma-milestone` Step 6.4 will auto-detect and run these tests.

```yaml
# [task]-tests.yaml — Optional executable test definitions
milestone_1:
  - name: "Registration returns 201"
    command: "curl -s -o /dev/null -w '%{http_code}' -X POST localhost:8000/register -d '{\"email\":\"t@t.com\"}'"
    expected: "201"
  - name: "Auth tests pass"
    command: "pytest tests/auth/ -q --tb=short"
    expected_pattern: "passed"
  - name: "No regressions"
    command: "pytest tests/ -q --tb=short"
    expected_pattern: "passed"

milestone_2:
  - name: "Protected endpoint requires auth"
    command: "curl -s -o /dev/null -w '%{http_code}' localhost:8000/api/protected"
    expected: "401"
```

**Design principles:**
- Each test has a `name`, `command`, and either `expected` (exact match) or `expected_pattern` (regex)
- Tests are scoped to milestones, matching the HTP structure in `tasks.md`
- The file is optional — if absent, Step 6.4 falls back to existing test execution behavior
- Commands run in the project root directory, not the AA-MA task directory

---

## III. Starting Large Tasks

When exiting plan mode with an accepted plan:

1. **Create Task Directory & Files:**

```bash
mkdir -p .claude/dev/active/[task-name]/
cd .claude/dev/active/[task-name]/
touch [task-name]-plan.md [task-name]-reference.md [task-name]-context-log.md [task-name]-tasks.md [task-name]-provenance.log
```

2. **Bootstrap References:** Immediately extract all non-negotiable facts (e.g., API endpoints, core function signatures) from the plan and write them to `[task]-reference.md`. This is Claude's **actionable memory store** for facts.

---

## IV. Context Injection Standard

Always load the five documents and wrap them in explicit delimiters (XML tags) to clearly indicate distinct boundaries and prevent context contamination. Anthropic models respond well to this structure.

* **Check Active Task:** Check `.claude/dev/active/` for existing tasks.

* **Inject Delimited Context:** Prioritise injecting `REFERENCE` and `TASKS` for immediate execution context.

  ```xml
  <REFERENCE>
  (Contents of [task-name]-reference.md: Strict Facts. Treat as non-negotiable.)
  </REFERENCE>

  <TASKS>
  (Contents of [task-name]-tasks.md: HTP Roadmap and Current Step. Defines your required next action.)
  </TASKS>

  <CONTEXT_LOG>
  (Contents of [task-name]-context-log.md: Summarised Decisions. Provides historical context.)
  </CONTEXT_LOG>
  (Include PLAN and PROVENANCE if tokens allow)
  ```

* **Update Immediately:** Mark tasks complete in `[task]-tasks.md` and write any new finalised facts to `[task]-reference.md` **before** moving to the next step.

---

## V. Sync Discipline

When following AA-MA workflow, you **MUST**:

1. **Update AA-MA docs immediately** after completing every task and milestone:
   - Mark task COMPLETE in `[task]-tasks.md`
   - Extract facts to `[task]-reference.md`
   - Document decisions in `[task]-context-log.md`
   - Log to `[task]-provenance.log`

2. **Commit and push** all changes:
   - `git add .`
   - `git commit -m "feat([task]): [description]"`
   - `git push`

**Never proceed to next task until current task is fully synced and pushed.**

---

## VI. Commit Signature for Active Plans

When an AA-MA plan is active in `.claude/dev/active/`, ALL commits MUST include a plan signature as the last line of the commit message footer.

**Signature Format:**
```
[AA-MA Plan] {task-name} .claude/dev/active/{task-name}
```

**Example:**
```
feat(api): add rate limiting middleware

- Implement token bucket algorithm
- Add Redis backend for distributed limiting

[AA-MA Plan] api-hardening .claude/dev/active/api-hardening
```

**Detection Logic:**
1. Check if `.claude/dev/active/` directory exists and contains task directories
2. For each task, parse `[task]-tasks.md` for milestone with `Status: ACTIVE`
3. Use the task name with an ACTIVE milestone as `{task-name}`

**Detection Priority:**
1. Task with `Status: ACTIVE` milestone
2. If none active, task with `Status: PENDING` milestones (plan exists but not started)
3. If multiple ACTIVE tasks, use alphabetically first
4. If `.claude/dev/active/` is empty or missing, no signature needed

**Applies To:**
- All AA-MA execution commits (`/execute-aa-ma-milestone`, `/execute-aa-ma-full`)
- All general commits while a plan is active (`/commit-and-push`, `/pre-commit-*`)
- Manual commits during plan execution

---

## VII. Finalization Protocol

Before marking any AA-MA milestone COMPLETE, follow this 4-step protocol:

**Step 1: Integrity Check**
Verbally confirm each acceptance criterion is met:
```
Acceptance Criteria Verification:
- [Criterion 1]: Confirmed - [brief evidence]
- [Criterion 2]: Confirmed - [brief evidence]
All [X] criteria verified.
```

**Step 2: Documentation Auto-Update**
Claude automatically updates all 5 AA-MA files:
- `tasks.md`: Mark milestone `Status: COMPLETE`, fill `Result Log:`
- `reference.md`: Add any new immutable facts discovered
- `context-log.md`: Append completion summary
- `provenance.log`: Append completion entry with timestamp + commit hash
- `plan.md`: No change (historical record)

**Step 3: User Authorization**
Use AskUserQuestion to get explicit approval:
```
Finalization Review
Milestone: [Title]
Acceptance Criteria: [X/X] verified
Ready to mark COMPLETE?
- Approve: Proceed with commit
- Review First: Show detailed verification
- Reject: Keep as ACTIVE
```

**Step 4: Confirmation**
After approval, display minimal confirmation:
```
Milestone marked COMPLETE: [Title]
```

**Applies To:**
- `/execute-aa-ma-milestone` (at milestone boundary)
- `/execute-aa-ma-full` (at each milestone boundary)

**Note:** `/execute-aa-ma-step` does NOT trigger finalization (steps accumulate until milestone).

---

## VIII. Archival

When ALL milestones are complete, archive the plan:
```
/archive-aa-ma {task-name}
```

This moves the task directory from `active/` to `completed/` with completion headers added to each file. Archives are local only (not committed to git).

---

## IX. Hierarchical Task Planning (HTP)

Replace the simple checklist in `[task]-tasks.md` with structured HTP using nested Markdown headers to model dependencies and control flow.[3, 4]

* **High-Level Node Structure:**
  `## Task Title`

  * `Status:` (PENDING/ACTIVE/COMPLETE)
  * `Dependencies:` (List required prerequisite Task IDs)
  * `Complexity:` [0-100%] (Use 80%+ to signal the need for deep reasoning/Chain-of-Thought) [5]
  * `Gate:` (HARD/SOFT — default SOFT) [8]

* **Low-Level Action:**
  `### Sub-step: [Action]`

  * `Result Log:` (Placeholder for agent output)

### Gate Classification

Milestones may declare a **gate type** that controls how the finalization protocol enforces human approval:

| Gate | Enforcement | When to Use |
|------|-------------|-------------|
| `SOFT` (default) | Convention-based — agent is instructed to seek approval | Reversible changes, low-risk milestones, AFK tasks |
| `HARD` | Artifact-enforced — execution commands **refuse to advance** without a signed approval entry in `context-log.md` | Irreversible actions, architectural decisions, external API integrations, production deployments |

**HARD gate approval artifact format** (must exist in `[task]-context-log.md`):
```markdown
## [YYYY-MM-DD] GATE APPROVAL: [Milestone Title]
- Gate: HARD
- Approved by: [user]
- Criteria verified: [X/X]
- Decision: APPROVED
```

The `/execute-aa-ma-milestone` finalization protocol (Step 7.1) checks for this artifact when `Gate: HARD` is set. If absent, the milestone cannot be marked COMPLETE.

---

## X. Advanced Procedures

### Context Compaction

When the message history nears the token limit, use Compaction to distil the context without performance degradation:[1, 2]

1. **Prompt Summary:** Instruct Claude to "Summarise the key architectural decisions and unresolved bugs from the history. Aggressively discard redundant tool outputs."
2. **Update Log:** Prepend the summary to `[task]-context-log.md`.
3. **Reset Session:** Start a new chat, reloading the five updated files.

### Automated Provenance (Recommended via Git Hooks)

Use local Git hooks to automate state synchronisation and ensure data freshness:

* **Logging (`post-commit`):** Automatically append the commit hash, timestamp, and active Task ID to `[task]-provenance.log`. This creates debugging telemetry.
* **Freshness (`pre-commit`):** Automatically update a "Last Updated" timestamp field in the five documents before the commit is finalised.

---

## XI. Planning Standard

When asked to **PLAN** something you **MUST** follow this standard. Plans must be deliberate, explicit, and immediately actionable so they can be converted into AA-MA artefacts (`[task]-plan.md`, `[task]-tasks.md`, `[task]-reference.md`).

> **Core behaviour:** Take time to reason carefully; perform deep, structured analysis; and produce a stepwise implementation plan that a team (or an agent) can execute with minimal additional clarification.

### Required Outputs (Every Plan)

1. **Executive summary (1-3 lines)** — concise objective and success criteria.
2. **Stepwise implementation plan** — ordered steps required to reach the objective.
3. **Milestones** — named checkpoints with measurable goals and suggested dates (or relative durations).
4. **Acceptance criteria** — one clear, testable acceptance criterion for each step/milestone.
5. **Required artefacts** — files, diagrams, APIs, schemas, credentials, or other deliverables needed for each step.
6. **Tests to validate** — unit/integration/manual test descriptions and pass/fail thresholds for each milestone.
7. **Rollback strategy** — explicit rollback or mitigation plan for each risky change.
8. **Dependencies & assumptions** — external services, people, libraries, and any assumptions made.
9. **Effort estimate & complexity** — rough effort (hours/days) per step and a `Complexity` score (0-100%). Mark steps with `Complexity >= 80%` to flag need for deep reasoning or human-in-the-loop review.
10. **Risks & mitigations** — top 3 risks per milestone and proposed mitigations.
11. **Next action** — the single concrete action required now (what to do first), and which AA-MA file to update (`REFERENCE`/`TASKS`).

### Format & Mapping into AA-MA

* The plan **must** be written so it can be copied into `[task]-plan.md`.
* Turn each plan step (and its metadata) into an HTP node in `[task]-tasks.md` using the HTP structure: `Status`, `Dependencies`, `Complexity`, `Acceptance criteria`, `Result Log`.
* Immediately extract any immutable facts (API endpoints, config values, file paths) into `[task]-reference.md`.

### Prompt Template for Claude

```
You MUST produce a thorough implementation plan for: <short objective>.
Follow the AA-MA Planning Standard exactly. Provide:

1. Executive summary (<=3 lines).
2. Ordered stepwise implementation plan.
3. Milestones with measurable goals and dates/durations.
4. Acceptance criteria for each step.
5. Required artefacts for each step.
6. Tests to validate each milestone.
7. Rollback strategy for risky steps.
8. Dependencies and explicit assumptions.
9. Effort estimate (hours/days) and Complexity (0-100%) per step — mark steps >=80% Complexity.
10. Risks (top 3) and mitigations per milestone.
11. ONE Next action the agent must perform now, and the AA-MA file(s) to update.

Format outputs in Markdown. After the plan, provide a 1-2 line mapping instructing
how to convert steps into [task]-tasks.md HTP nodes and which facts to add to
[task]-reference.md.
```

### Plan Approval Gate

Plan approval is a **formal gate** in the AA-MA workflow. No implementation may begin until the plan has been reviewed and approved by the user.

* In Claude Code, this is enforced by **plan mode** — `ExitPlanMode` presents the plan for user approval before execution can begin.
* In other tools, this must be enforced by convention: the user must explicitly approve the plan before any execution commands are run.
* The approval is logged as the first entry in `[task]-context-log.md`:

```markdown
## [YYYY-MM-DD] PLAN APPROVED
- Plan: [task-name]
- Approved by: [user]
- Milestones: [count]
- HARD gates: [list of milestone IDs with Gate: HARD, if any]
```

### Enforcement & Practical Notes

* **Complex steps (Complexity >= 80%)**: flag them and require an explicit human review or a Chain-of-Thought style deep reasoning pass (document the reasoning in `[task]-context-log.md` after compaction).
* **Do not proceed** to implement until `Acceptance criteria` for the first milestone are clear and recorded.
* **Gate classification**: When creating HTP nodes, classify each milestone's gate type. Default is `SOFT`. Use `HARD` for irreversible actions, architectural decisions, or production deployments.
* **Test definitions**: When acceptance criteria can be expressed as executable commands, add them to `[task]-tests.yaml` alongside the plan.
* **Automated flow**: `/aa-ma-plan` -> paste plan into `[task]-plan.md` -> run `/aa-ma-plan-to-tasks` (or a short script) to auto-generate HTP nodes in `[task]-tasks.md` and extract immutable facts to `[task]-reference.md`.

---

## XII. File Templates

### [task]-plan.md

```markdown
# [task-name] Plan

**Objective:** <goal>
**Owner:** <person>
**Created:** <date>
**Last Updated:** <date>

## Executive Summary
<3-line overview>

## Implementation Steps
(see Planning Standard)
```

### [task]-reference.md

```markdown
# [task-name] Reference

Immutable facts and constants:

- API_ENDPOINT: https://api.example.com/v1/
- MODEL_PATH: /models/pten-classifier.pkl
- DATABASE: postgres://user@localhost/db

_Last Updated: <date>_
```

### [task]-context-log.md

```markdown
# [task-name] Context Log

## [YYYY-MM-DD] Compaction Summary
- Key decision: ...
- Bug resolved: ...
- Remaining issue: ...
```

### [task]-tasks.md

```markdown
# [task-name] Tasks (HTP)

## Milestone 1: <title>
- Status: ACTIVE
- Dependencies: None
- Complexity: 45%
- Gate: SOFT
- Mode: AFK
- Acceptance Criteria: ...

### Sub-step 1.1: Execute <action>
- Status: PENDING
- Result Log:
```

### [task]-tests.yaml (Optional)

```yaml
# Machine-executable test definitions linked to milestones
milestone_1:
  - name: "Descriptive test name"
    command: "pytest tests/feature/ -q --tb=short"
    expected_pattern: "passed"
```

### [task]-verification.md (Optional)

```markdown
# Verification Report: [task-name]
Generated: <ISO-8601 timestamp> | Mode: <automated|interactive> | Revision: 1

## Summary
- CRITICAL: 0 findings (0 resolved)
- WARNING: 0 findings
- INFO: 0 findings
- Overall: <PASS | FAIL | PASS WITH WARNINGS | SKIPPED>

## Angle 1: Ground-Truth Audit
### Findings
No findings — all claims verified.

## Angle 2: Assumption Extraction & Challenge
### Assumptions Identified
(numbered list of assumptions with verification status)

## Angle 3: Impact Analysis on Proposed Changes
### Files Affected
(per-file findings with risk level)

## Angle 4: Acceptance Criteria Falsifiability
### Criteria Audit
(per-criterion findings)
### Score: N/M falsifiable (X%)

## Angle 5: Fresh-Agent Simulation
### Implementation Barriers
(findings from fresh-agent perspective)

## Angle 6: Specialist Domain Audit
### Specialists Dispatched: <list or "None — no domain keywords detected">
(per-specialist findings)

## Revision History
- v1: <date> — Initial verification: 0 CRITICAL, 0 WARNING → <result>
```

### [task]-provenance.log

```text
# [task-name] Provenance Log

[2025-10-29 09:32] Commit abc123 — TaskID: step-1
[2025-10-29 09:45] Commit def456 — Context compacted
[2025-10-29 10:15] CHECKPOINT — ActiveStep: 1.3 — NextAction: "Run integration tests" — ContextLoaded: REFERENCE,TASKS — TokenUsage: 68%
[2025-10-29 11:00] MILESTONE COMPLETE — Milestone 1 — Commit ghi789 — Criteria: 3/3 verified
```

### CHECKPOINT Entry Format

When context compaction occurs or a session ends mid-task, write a structured checkpoint to provenance.log:

```
[TIMESTAMP] CHECKPOINT — ActiveStep: [step-id] — NextAction: "[description]" — ContextLoaded: [files] — TokenUsage: [%]
```

This enables reliable session resume: the next session reads the latest CHECKPOINT and knows exactly where to pick up, what to do next, and what context was loaded.

---

## References

[1] Context compaction and summarisation techniques.
[2] Anthropic context injection best practices.
[3] Hierarchical task decomposition and dependency management.
[4] Chain-of-thought and structured reasoning for LLM orchestration.
[5] Complexity estimation heuristics.
[6] Hierarchical Task Planning (HTP) methodologies.
[7] Provenance and telemetry management in software pipelines.
[8] Inspired by Helix.ml spec-driven workflows (infrastructure-enforced gates, executable test definitions). See research: `.claude/plans/witty-puzzling-sonnet.md`.
[9] Adversarial plan verification. 6-angle structured review derived from lessons L-054, L-058, L-059, L-067, L-068, L-069. See skill: `claude-code/skills/plan-verification/SKILL.md`.
