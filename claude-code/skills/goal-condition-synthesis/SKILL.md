---
name: goal-condition-synthesis
description: Synthesize a Claude Code /goal condition from AA-MA plan artifacts. Produces a falsifiable condition referencing observable artifacts (provenance.log, tasks.md, git tags, test exit codes) plus a turn cap derived from plan effort. Used by /execute-aa-ma-full §2.5 and /verify-plan --iterate.
---

# Goal-Condition Synthesis Skill

Produce a `/goal` completion condition from AA-MA plan artifacts, suitable for binding to a Claude Code session as the cross-turn drive-to-completion primitive.

## When to Use This Skill

Invoke this skill when:

- `/execute-aa-ma-full` reaches §2.5 (Goal Synthesis & Bind) and must construct a goal condition before AFK execution.
- `/verify-plan --iterate` needs a condition that bounds the adversarial verification loop.
- A user explicitly asks "synthesize a goal for this plan" against an active AA-MA task.

Do NOT use this skill for:

- Per-step or per-sub-task goals — `/goal` is one-per-session. Goals live at the **task** level, not the milestone or step level.
- Tasks without a complete 5-file AA-MA artifact set (the synthesizer needs `plan.md` Acceptance Criteria and `tasks.md` milestone count).

## Why Observable Artifacts Matter

The Haiku evaluator that `/goal` invokes after each turn only sees what is in the conversation transcript. It does **not** run tools. A vague condition like "feature is done" cannot be evaluated; the model has nothing to check.

Good conditions reference artifacts aa-ma-forge produces during execution and surfaces in the transcript:

| Observable | Where it appears in the transcript |
|---|---|
| `provenance.log` lines | Bash `cat` output after milestone commits |
| `tasks.md` Status fields | Read tool output during finalization |
| Git tag existence | `git tag -l` output |
| Test exit codes | `make ci` / `pytest` output |
| Commit SHA references | `git rev-parse` output, commit footers |
| `<task>-verification.md` Verdict line | Read tool output after `/verify-plan` runs |

Conditions that reference these can be evaluated by Haiku from transcript context alone.

## Synthesis Algorithm

### Inputs

1. `<task-dir>` — path to `.claude/dev/active/<task-name>/`
2. `<task-name>` — the task slug
3. `<mode>` — one of `full-execute`, `verify-iterate`
4. (optional) `<override-turn-cap>` — explicit user override; otherwise auto-derived

### Step 1: Read plan and tasks

Read these files:

- `<task-dir>/<task-name>-plan.md` → extract `Acceptance Criteria` (per milestone or top-level), `Tests`, `Effort`, `Engineering Standards Declaration`.
- `<task-dir>/<task-name>-tasks.md` → count milestones with `Status: PENDING` or `Status: ACTIVE`.

### Step 2: Derive turn cap

```
turn_cap = ceil(min(pending_milestones * 1.5, 30))
```

The cap is the **cost ceiling**. If user provided `<override-turn-cap>`, use it instead.

### Step 3: Build the condition string

Templates by mode:

**`full-execute`:**

```
All remaining milestones in <task>/tasks.md have Status: COMPLETE;
<task>-provenance.log contains a "MILESTONE COMPLETE" line for each;
git tag <task-name>-complete exists;
`make ci` (or the project's quality gate equivalent) exits 0;
each plan.md Acceptance Criterion has a "[Goal Verdict]" footer in its
corresponding milestone commit citing the evidence;
or stop after <turn_cap> turns.
```

**`verify-iterate`:**

```
<task>-verification.md latest "## Verdict" block shows GREEN with
0 Criticals AND every Critical from the previous Verdict block has a
"Resolution:" line in this block;
or stop after 3 iterations.
```

### Step 4: Validate the condition

Self-check before returning:

1. Does the condition reference at least 2 observable artifacts? (count from the table above)
2. Is the turn cap present and ≤ 30?
3. Is the total condition length under 4,000 characters (Claude Code `/goal` limit)?
4. Does the condition avoid vague terms (`done`, `working`, `correct`, `good`, `ready`)?

If any check fails, return `SYNTHESIS_FAILED` with the specific reason. Do **not** return a degraded condition.

### Step 5: Return structured result

```yaml
status: SYNTHESIZED | SYNTHESIS_FAILED
mode: full-execute | verify-iterate
condition: |
  <the full condition string>
turn_cap: <int>
observable_artifacts: [<list of artifact identifiers referenced>]
plan_inputs:
  acceptance_criteria_count: <int>
  milestone_count: <int>
  effort_estimate: <string from plan.md>
synthesis_warnings: [<list of any non-blocking concerns>]
```

## Worked Example

Input:

- `task-name`: `add-jwt-auth`
- `task-dir`: `.claude/dev/active/add-jwt-auth/`
- `mode`: `full-execute`
- `plan.md` has 4 milestones, 11 acceptance criteria total, Effort: "M (3-5 days)"
- `tasks.md` shows 3 milestones PENDING, 1 COMPLETE

Output:

```yaml
status: SYNTHESIZED
mode: full-execute
condition: |
  All remaining milestones in add-jwt-auth/tasks.md have Status: COMPLETE;
  add-jwt-auth-provenance.log contains a "MILESTONE COMPLETE" line for each;
  git tag add-jwt-auth-complete exists;
  `make ci` exits 0;
  each plan.md Acceptance Criterion has a "[Goal Verdict]" footer in its
  corresponding milestone commit citing the evidence;
  or stop after 5 turns.
turn_cap: 5
observable_artifacts: [tasks.md Status, provenance.log lines, git tag, test exit code, commit footers]
plan_inputs:
  acceptance_criteria_count: 11
  milestone_count: 4
  effort_estimate: "M (3-5 days)"
synthesis_warnings: []
```

## Anti-Patterns

| Anti-pattern | Why it fails |
|---|---|
| "Feature is complete" | Not observable — Haiku has nothing to check |
| "All tests pass" without saying *how the agent surfaces test results* | Haiku doesn't see tool output; the agent must `cat` results into the transcript |
| Per-milestone goals | `/goal` is one-per-session; replacing a goal mid-run loses cross-turn continuity |
| Turn cap > 30 | Cost ceiling fails; AFK runs can burn through tokens unnoticed |
| No turn cap | Same as above — `/goal` will keep retrying indefinitely if the condition is unmet |
| Subjective criteria ("looks good", "feels right") | Haiku cannot evaluate subjective claims |

## Integration Points

- **Called by:** `/execute-aa-ma-full` §2.5; `/verify-plan --iterate`
- **Uses:** `Read` tool to load plan.md and tasks.md
- **Does NOT call:** `/goal` directly — returns the condition string for the caller to invoke
- **Related skills:** `aa-ma-execution` (consumes the verdict at milestone boundaries), `plan-verification` (consumed by the iterate-mode condition)

## Failure Modes

| Failure | Cause | Resolution |
|---|---|---|
| `plan.md` missing or empty | Plan not yet synthesized | Return `SYNTHESIS_FAILED — reason=missing_plan`. Caller should run `/aa-ma-plan` first. |
| No PENDING milestones | Task already complete | Return `SYNTHESIS_FAILED — reason=nothing_to_do`. Caller should run `/archive-aa-ma`. |
| Acceptance Criteria section absent from plan | Plan does not meet AA-MA standard | Return `SYNTHESIS_FAILED — reason=plan_incomplete`. Caller should re-run `/aa-ma-plan` or `/verify-plan`. |
| Condition exceeds 4,000 chars | Plan has too many acceptance criteria for one condition | Return `SYNTHESIS_FAILED — reason=condition_too_long`. Caller should narrow scope. |

---

**End of goal-condition-synthesis/SKILL.md**
