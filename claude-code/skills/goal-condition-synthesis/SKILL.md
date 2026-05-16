---
name: goal-condition-synthesis
description: Synthesize a Claude Code /goal condition from AA-MA plan artifacts. Produces a falsifiable condition referencing observable artifacts (provenance.log, tasks.md, git tags, test exit codes) plus a turn cap derived from plan effort. Owns the canonical verdict-token enum, observable-artifact list, hashing contract, and turn-cap formula. Used by /execute-aa-ma-full §2.5 and /verify-plan --iterate.
---

# Goal-Condition Synthesis Skill

Produce a `/goal` completion condition from AA-MA plan artefacts, suitable for
binding to a Claude Code session as the cross-turn drive-to-completion
primitive (https://code.claude.com/docs/en/goal.md).

This SKILL is the **canonical source** for:

- the observable-artifact list (used by `/goal` Haiku evaluator)
- the verdict-token enum (used in `provenance.log` audit lines)
- the turn-cap formula (cost ceiling)
- the condition-hash contract (auditable cross-reference primitive)

Other surfaces (`aa-ma-execution` §IX.5, `aa-ma-team-guide` §2.7,
`aa-ma-quick-reference`, `execute-aa-ma-full` §2.5, `verify-plan` Step 4.5)
**link back** to this SKILL rather than restating these values, to prevent
drift.

A reference Python implementation of the algorithm lives at
`src/aa_ma/goal_synthesis.py` (unit-tested in `tests/test_goal_synthesis.py`).
Treat the Python module as the executable spec and this SKILL.md as the
operator-facing protocol.

## When to Use This Skill

Invoke this skill when:

- `/execute-aa-ma-full` reaches §2.5 (Goal Synthesis & Bind) and must construct
  a goal condition before AFK execution.
- `/verify-plan --iterate` needs a condition that bounds the adversarial
  verification loop.
- A user explicitly asks "synthesise a goal for this plan" against an active
  AA-MA task.

Do NOT use this skill for:

- Per-step or per-sub-task goals — `/goal` is one-per-session. Goals live at
  the **task** level, not the milestone or step level.
- Tasks missing any of the 5 standard AA-MA files
  (`plan.md`, `reference.md`, `context-log.md`, `tasks.md`, `provenance.log`).
  The synthesiser needs `plan.md` Acceptance Criteria and `tasks.md` milestone
  count at minimum.

## Why Observable Artefacts Matter

The Haiku evaluator that `/goal` invokes after each turn only sees what is in
the conversation transcript. It does **not** run tools. A vague condition like
"feature is done" cannot be evaluated; the model has nothing to check.

### Canonical Observable-Artefact Table

This is the authoritative list. Other docs reference it; they do not restate it.

| # | Observable | Where it appears in the transcript |
|---|---|---|
| 1 | `provenance.log` lines | Bash `cat` output after milestone commits |
| 2 | `tasks.md` Status fields | Read tool output during finalisation |
| 3 | Git tag existence | `git tag -l` output |
| 4 | Test exit codes | `make ci` / `pytest` output |
| 5 | Commit footers (`[AA-MA Plan]` signature) | `git log` output |
| 6 | `<task>-verification.md` Verdict line | Read tool output after `/verify-plan` runs |

Conditions that reference at least **two** rows from this table can be evaluated
by Haiku from transcript context alone.

## Synthesis Algorithm

### Inputs

1. `<task-dir>` — path to `.claude/dev/active/<task-name>/`
2. `<task-name>` — the task slug
3. `<mode>` — one of `full-execute`, `verify-iterate`
4. (optional) `<override-turn-cap>` — explicit user override; otherwise auto-derived

### Step 1: Read plan and tasks

Read these files:

- `<task-dir>/<task-name>-plan.md` → extract `Acceptance Criteria` (per
  milestone or top-level), `Tests`, `Effort`, `Engineering Standards Declaration`.
- `<task-dir>/<task-name>-tasks.md` → count milestones with `Status: PENDING`
  or `Status: ACTIVE`.

### Step 2: Derive turn cap

```
turn_cap = max(4, ceil(min(pending_milestones * 1.5, 30)))
```

Floor of 4 prevents single-milestone plans from being capped below the
finalisation overhead (milestone commit + `/verify-plan` + finalize).
Ceiling of 30 is the cost ceiling for AFK runs.

If user provided `<override-turn-cap>`, use that value (still validated as
≥ 1 and ≤ 30 by `validate_condition`).

Reference implementation: `aa_ma.goal_synthesis.turn_cap(pending: int) -> int`.

### Step 3: Build the condition string

Templates by mode:

**`full-execute`:**

```
All remaining milestones in <task>/tasks.md have Status: COMPLETE;
<task>-provenance.log contains a "MILESTONE COMPLETE" line for each;
git tag <task-name>-complete exists;
`make ci` (or the project's quality gate equivalent) exits 0;
or stop after <turn_cap> turns.
```

**`verify-iterate`:**

```
<task>-verification.md latest "## Verdict" block shows GREEN with
0 Criticals AND every Critical from the previous Verdict block has a
"Resolution:" line in this block;
or stop after 3 iterations.
```

The iterate cap is fixed at 3 (heuristic: more than 3 verification iterations
on the same plan typically indicates the plan needs a human re-think, not
another mechanical pass).

### Step 4: Validate the condition

Self-check before returning. The Python reference implementation is
`aa_ma.goal_synthesis.validate_condition(condition: str, turn_cap: int)
-> (bool, reason_token | None)`. Checks:

1. Condition references at least 2 distinct observable artefacts from the
   canonical table above. Detected via regex against artefact-signature
   substrings (`provenance.log`, `tasks.md`, `git tag`, `make ci` /
   `pytest`, `[AA-MA Plan]`, `verification.md`).
2. `turn_cap` is an integer in `[1, 30]`.
3. Total condition length is ≤ 4 000 characters (Claude Code `/goal` limit).
4. Condition avoids any case-insensitive whole-word match of vague terms:
   `done`, `working`, `correct`, `good`, `ready`. The banned-word list is
   exported as `aa_ma.goal_synthesis.BANNED_VAGUE_TERMS`.

If any check fails, return `SYNTHESIS_FAILED` with the specific reason. Do
**not** return a degraded condition.

### Step 5: Compute the condition hash

The hash is the deterministic audit primitive for cross-referencing a bound
goal between `provenance.log`, sibling sessions, and future replay.

Reference implementation: `aa_ma.goal_synthesis.condition_hash(condition: str)
-> str`. Equivalent shell:

```bash
printf '%s' "$CONDITION_LF_NORMALISED" | sha256sum | cut -c1-12
```

Where `$CONDITION_LF_NORMALISED` is the condition with:

- all `\r\n` and `\r` replaced by `\n`
- trailing whitespace on each line stripped
- no trailing newline at end of string
- UTF-8 encoded

The first 12 hex characters of the SHA-256 digest are the hash. Two sessions
binding the same condition (semantically and byte-for-byte after normalisation)
produce the same hash.

### Step 6: Return structured result

```yaml
status: SYNTHESIZED | SYNTHESIS_FAILED
mode: full-execute | verify-iterate
condition: |
  <the full condition string>
turn_cap: <int>
condition_hash: <12-hex>     # only when status=SYNTHESIZED
observable_artifacts: [<list of artefact identifiers referenced>]
plan_inputs:
  acceptance_criteria_count: <int>
  milestone_count: <int>
  effort_estimate: <string from plan.md>
synthesis_warnings: [<list of any non-blocking concerns>]
```

## Canonical Verdict & Event Vocabulary

This is the single authoritative enum for `/goal`-integration provenance lines.
All other docs reference this table; they do not restate it.

| Event token | Where emitted | Allowed value tokens |
|---|---|---|
| `GOAL_BOUND` | After `AskUserQuestion → Bind` (full-execute §2.5) | `turn_cap=<int>` and `condition_hash=<12-hex>` |
| `GOAL_BIND_DECLINED` | User chose `[Skip /goal]` at §2.5 | `user_choice` |
| `GOAL_SYNTHESIS_SKIPPED` | Synthesis returned `SYNTHESIS_FAILED` | `reason={missing_plan, nothing_to_do, plan_incomplete, condition_too_long, condition_too_vague, turn_cap_out_of_range, observable_artifacts_insufficient}` |
| `GOAL_FINAL` | At plan completion (full-execute §6) | `verdict={MET, UNMET, TURN_CAP_HIT, CLEARED, NOT_BOUND}`, `turns=<int>`, `reason='<short>'` |
| `VERIFY_ITERATE` | At iterate-mode termination (verify-plan §4.5) | `verdict={GREEN, YELLOW, RED}`, `iterations=<int>`, `criticals=<int>`, `outcome={MET, EXHAUSTED, USER_HALTED}` |
| `VERIFY_ITERATE_SKIPPED` | `--iterate` requested but `/goal` unavailable or synthesis failed | `reason=<token>` |

Audit one-liner (covers every event token above):

```bash
grep -E '^\[.*\] (GOAL_|VERIFY_ITERATE)' \
  .claude/dev/active/<task>/<task>-provenance.log
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
  or stop after 5 turns.
turn_cap: 5            # max(4, ceil(min(3 * 1.5, 30))) = max(4, 5) = 5
condition_hash: a3f2b1c8d4e7
observable_artifacts: [tasks.md Status, provenance.log lines, git tag, test exit code]
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
| `turn_cap > 30` | Cost ceiling fails; AFK runs can burn through tokens unnoticed |
| No turn cap | Same as above — `/goal` will keep retrying indefinitely if the condition is unmet |
| Subjective criteria (`good`, `ready`, `correct`, `working`, `done`) | Haiku cannot evaluate subjective claims |

## Integration Points

- **Called by:** `/execute-aa-ma-full` §2.5; `/verify-plan --iterate`
- **Uses:** `Read` tool to load plan.md and tasks.md; `aa_ma.goal_synthesis`
  Python helpers
- **Does NOT call:** `/goal` directly — returns the condition string for the
  caller to invoke
- **Related skills:** `aa-ma-execution` (operator reference); `plan-verification`
  (consumed by the iterate-mode condition)

## Failure Modes

| Reason token | Cause | Resolution |
|---|---|---|
| `missing_plan` | `plan.md` missing or empty | Run `/aa-ma-plan` first |
| `nothing_to_do` | No PENDING milestones | Run `/archive-aa-ma` |
| `plan_incomplete` | Acceptance Criteria section absent from plan | Re-run `/aa-ma-plan` or `/verify-plan` |
| `condition_too_long` | Condition exceeds 4 000 chars | Narrow scope or trim per-milestone criteria |
| `condition_too_vague` | Condition matches a banned vague term | Reword to reference observable artefacts |
| `observable_artifacts_insufficient` | Fewer than 2 artefact references in the condition | Add explicit artefact-targeting clauses |
| `turn_cap_out_of_range` | User-provided override is < 1 or > 30 | Pick a value in `[1, 30]` |

---

**End of goal-condition-synthesis/SKILL.md**
