# Goal-condition synthesis patterns — optional `/goal` conditions built from AA-MA artefacts.

## IX.5 Goal-Condition Synthesis Patterns (Optional, Claude Code `/goal`)

Claude Code's built-in `/goal` command sets a cross-turn drive-to-completion
condition that a Haiku evaluator checks after every turn. aa-ma-forge integrates
this primitive at two surfaces; both are **opt-in** and rely on observable
artefacts so the evaluator can reach a verdict from transcript context alone.

| Surface | Where | What `/goal` adds |
|---|---|---|
| `/execute-aa-ma-full` AFK runs | §2.5 Goal Synthesis & Bind | Terminating condition tied to user intent (plan acceptance criteria), turn-cap as cost ceiling |
| `/verify-plan --iterate` | Step 4.5 Iterate Mode | Bounded iteration loop that converges on GREEN Verdict with 0 Criticals |

Per-milestone Haiku second-opinion verdicts are **deliberately out of scope**
at v0.9.x — Claude Code does not document a synchronous Haiku evaluation API,
and `/goal` is per-turn cross-turn only. Re-evaluate once either Claude Code
ships such an API or aa-ma-forge defines its own `Skill(haiku-eval)` wrapper.

### The Observable-Artifact Rule

The Haiku evaluator only sees what aa-ma-forge has surfaced in the conversation
transcript. It does **not** run tools. The canonical list of observable
artefacts lives in `Skill(goal-condition-synthesis)`; this section does not
restate it. Conditions that reference vague success states (`done`, `working`,
`correct`, `good`, `ready`) are rejected at construction time.

### Two Condition Templates

The canonical templates and turn-cap arithmetic live in
`Skill(goal-condition-synthesis)`. This section gives one-line summaries so
operators know which template each surface uses:

- **`full-execute`** (cross-turn driver, §2.5 of `/execute-aa-ma-full`):
  bound from plan Acceptance Criteria; turn cap
  `max(4, ceil(min(pending_milestones * 1.5, 30)))`.
- **`verify-iterate`** (cross-turn driver, `/verify-plan --iterate`):
  bound from `<task>-verification.md` Verdict block; iteration cap fixed at 3
  (heuristic, see synthesis SKILL).

### Verdict & Event Vocabulary

The canonical enum lives in `Skill(goal-condition-synthesis)` § "Verdict &
event vocabulary". This skill does not restate the token set — if you add or
rename a verdict token, edit the synthesis SKILL and re-grep call sites.

Audit a task's goal-integration history:

```bash
grep -E '^\[.*\] (GOAL_|VERIFY_ITERATE)' \
  .claude/dev/active/<task>/<task>-provenance.log
```

### Anti-Patterns

- **Per-step or per-sub-task goals:** `/goal` is one-per-session. Goals live
  at the **task** level. Don't try to make them milestone-scoped.
- **Auto-clearing goals on Stop hooks:** let the user own the `/goal`
  lifecycle. aa-ma-forge appends to provenance, never silently mutates goal
  state.
- **Vague conditions:** if the condition does not reference at least 2
  observable artefacts (per the synthesis skill's enumeration), construction
  fails with `SYNTHESIS_FAILED — reason=condition_too_vague`.

See `Skill(goal-condition-synthesis)` for the synthesis algorithm, validation
rules, failure modes, the canonical observable-artefact table, and the
canonical verdict-token enum.
