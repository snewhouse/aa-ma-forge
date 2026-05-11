---
name: verify-impl
description: Post-impl adversarial review symmetric to /verify-plan. Dispatches up to 5 parallel audit agents (code-reviewer, security-auditor, tdd-sequence-auditor, context7-evidence-auditor, future-proofing-auditor) based on the milestone's plan-declared Audit-Profile. CRITICAL findings surface via AskUserQuestion accept/dispute/defer panel before §7.3 user authorization. Introduced in v0.8.0 per ADR-0005. Invoked by Phase 6.8 of /execute-aa-ma-milestone.
---

# /verify-impl — Post-Impl Adversarial Review

Symmetric to `/verify-plan` but operates on the IMPLEMENTATION diff after a milestone closes, not on the plan before execution. Closes the asymmetry that motivated ADR-0005.

## When this skill fires

Three trigger paths:

1. **Phase 6.8 of `/execute-aa-ma-milestone`** — automatic invocation between §6.7 (Engineering Standards HARD Gate) and §7.1 (Integrity Check), for plans with `Created: >= v0.8.0` release tag commit date that have an `Audit-Profile:` field on the current milestone.
2. **Direct skill invocation** — for retroactive audit of a closed milestone: `Skill(verify-impl) --task <name> --milestone <id>`.
3. **`/execute-aa-ma-full`** — delegates to the per-milestone invocation above.

## When this skill does NOT fire

- Plans with `Created: < v0.8.0` release tag commit date (grandfathered)
- `AA_MA_HOOKS_DISABLE=1` env var set (master kill switch)
- `AA_MA_AUDIT_BUDGET=off` env var set (logged to provenance.log as `[ts] AUDIT_BUDGET=off — bypassed §6.8`)
- Milestone has no `Audit-Profile:` field AND plan-verification did not flag it as missing (impossible for v0.8.0+ plans; means grandfathered)

## Inputs

- `<task-name>` — the active task directory under `.claude/dev/active/`
- `<milestone-id>` — `M1` / `M2` / ... — matches the heading in `tasks.md`
- Computed: `<milestone-base-sha>` and `<milestone-head-sha>` — commits at milestone boundaries
- Computed: `<audit-profile>` — read from the milestone block in `tasks.md`

## Audit-Profile dispatch matrix

The plan-declared `Audit-Profile:` per milestone determines which of the 5 agents run:

| Audit-Profile | code-reviewer | security-auditor | tdd-sequence | context7-evidence | future-proofing |
|---|:-:|:-:|:-:|:-:|:-:|
| `full` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `code-only` | ✅ | ✅ | ✅ | ✅ | ✅ |
| `docs-only` | — | — | — | — | ✅ (check #1 only) |
| `infra` | ✅ | ✅ | — | — | ✅ (checks #1+#3) |
| `custom` | per `Audit-Run:` / `Audit-Skip:` declarations | | | | |

(`code-only` differs from `full` in that the impl-review.md write-up emphasises code-quality sections; both run all 5 agents.)

## Execution flow

### Step 1: Resolve inputs

```bash
# Active task name (single active task assumed; multiple → use --task)
TASK_NAME=$(ls -1 .claude/dev/active/ | head -1)
TASK_DIR=".claude/dev/active/$TASK_NAME"

# Milestone block from tasks.md
MILESTONE_ID="M$N"
MILESTONE_BLOCK=$(awk "/^## (Milestone\s+)?M?$N(:|\s)/,/^## (Milestone\s+)?M?$((N+1))(:|\s)|^---$/" \
                    "$TASK_DIR/$TASK_NAME-tasks.md")

# Audit-Profile from the milestone block (use the shared parser)
AUDIT_PROFILE=$(uv run python -c "
from aa_ma.plan_parsers import parse_audit_profile
import sys
v, ok, err = parse_audit_profile(sys.stdin.read())
print(v if ok and v else 'MISSING' if not v else f'INVALID: {err}')
" <<< "$MILESTONE_BLOCK")

# Milestone window — commits since the milestone start
# Convention: the milestone's first commit is the one that matches its
# scaffolding (or set Status: ACTIVE) in tasks.md. Use git log for the
# milestone signature footer if present.
MILESTONE_BASE_SHA=$(git log --format=%H --grep="^M$((N-1)) COMPLETE\|^Milestone $((N-1)) COMPLETE\|chore(aa-ma)" \
                            -1 -- "$TASK_DIR/$TASK_NAME-tasks.md" 2>/dev/null \
                       || git rev-parse HEAD~10)
MILESTONE_HEAD_SHA=$(git rev-parse HEAD)
```

### Step 2: Budget check

```bash
case "${AA_MA_AUDIT_BUDGET:-normal}" in
    off)
        echo "[$(date -Iseconds)] AUDIT_BUDGET=off — bypassed §6.8" \
            >> "$TASK_DIR/$TASK_NAME-provenance.log"
        exit 0
        ;;
    low)
        DISPATCH_MODE=sequential
        AGENT_CONTEXT_MODE=diff-only
        ;;
    normal|*)
        DISPATCH_MODE=parallel
        AGENT_CONTEXT_MODE=full
        ;;
esac
```

### Step 3: Dispatch agents per Audit-Profile

For each agent in the profile's slate, build a prompt with:
- `<task-name>`, `<milestone-id>`, `<base-sha>`, `<head-sha>`
- Path to reference.md, provenance.log
- The milestone's `Required Artefacts` list
- `AA_MA_AUDIT_BUDGET` mode

**Parallel dispatch (DISPATCH_MODE=parallel):**

```
Send a single message with multiple Task tool uses:
  Task(subagent_type=code-reviewer, prompt=<context>)
  Task(subagent_type=security-auditor, prompt=<context>)
  Task(subagent_type=tdd-sequence-auditor, prompt=<context>)
  Task(subagent_type=context7-evidence-auditor, prompt=<context>)
  Task(subagent_type=future-proofing-auditor, prompt=<context>)
```

**Sequential dispatch (DISPATCH_MODE=sequential):** dispatch one at a time, aggregate as you go.

### Step 4: Aggregate findings

Parse each agent's output (the trailing `SUMMARY: <N> CRITICAL, <M> WARNING, <P> INFO` line). Build a consolidated severity table:

```
| Agent                     | CRITICAL | WARNING | INFO | Verdict |
|---------------------------|:--------:|:-------:|:----:|---------|
| code-reviewer             |    1     |    2    |  0   | BLOCKED |
| security-auditor          |    0     |    0    |  0   | PASS    |
| tdd-sequence-auditor      |    0     |    0    |  0   | PASS    |
| context7-evidence-auditor |    0     |    1    |  0   | WARN    |
| future-proofing-auditor   |    0     |    0    |  2   | PASS    |
| TOTAL                     |    1     |    3    |  2   | BLOCKED |
```

### Step 5: Write `[task]-impl-review.md`

Use `docs/templates/impl-review-template.md` as the structure. Fill in each agent section verbatim from agent output. Update Summary block.

### Step 6: Surface CRITICAL findings via AskUserQuestion

If total CRITICAL > 0, build an `AskUserQuestion` panel per CRITICAL:

```
For each critical_finding:
    AskUserQuestion(
      question="[CRITICAL] <pattern>: <file:line> — <impact>. <suggested-fix>",
      header="<pattern-short>",
      options=[
        {"label": "Accept — block until fixed", ...},
        {"label": "Dispute — false positive, log and continue", ...},
        {"label": "Defer — add new backlog task, continue", ...}
      ]
    )
```

Record each decision in `[task]-impl-review.md` under "User Override Decisions".

If any decision is `accept`, set Overall verdict to BLOCKED and halt §7.3 user authorization.

If all decisions are `dispute` or `defer` (and no `accept`), the disputes are logged for next-run learning and the workflow continues to §7.1.

### Step 7: Log to provenance

```
[<ISO>] §6.8 POST_IMPL_REVIEW — Audit-Profile: <profile> — \
        agents: <slate> — verdict: <PASS|BLOCKED|PASS_WITH_WARNINGS> — \
        findings: <N> CRITICAL / <M> WARNING / <P> INFO
```

### Step 8: Hand back to milestone command

Return verdict to `/execute-aa-ma-milestone`. The milestone command's §7.3 user authorization uses this verdict:

- `PASS` or `PASS_WITH_WARNINGS` → proceed to §7.3 as normal
- `BLOCKED` → §7.3 cannot proceed until accepted CRITICALs are fixed and §6.8 re-runs clean

## Bypass mechanisms (auditable)

| Mechanism | Effect |
|---|---|
| `AA_MA_HOOKS_DISABLE=1` | Master kill switch — skips ALL AA-MA gates incl. §6.8 |
| `AA_MA_AUDIT_BUDGET=off` | Skips §6.8 only; logged in provenance.log |
| `AA_MA_AUDIT_BUDGET=low` | Runs §6.8 in sequential / diff-only mode |
| `TDD-Waiver: <canonical>` | Per-milestone bypass for tdd-sequence-auditor only |
| `[security-bypass: <reason>]` in commit msg | Bypasses upstream `security-static-check.sh` hook (mechanical layer); semantic security-auditor agent still runs |

## Cross-references

- ADR-0005: `docs/adr/0005-post-impl-adversarial-review.md`
- Phase 6.8 anatomy: `docs/spec/aa-ma-specification.md` §II Post-Impl Adversarial Review Report
- Mechanical security layer: `claude-code/hooks/security-static-check.sh`
- Plan-verification Angle 6 structural checks #4, #5: `claude-code/skills/plan-verification/SKILL.md`
- Canonical-enum parsers: `src/aa_ma/plan_parsers.py`
- Template: `docs/templates/impl-review-template.md`

## Symmetric counterpart

`/verify-plan` (existing) runs 6 angles on the plan BEFORE execution. `/verify-impl` (this skill) runs 5 agents on the implementation AFTER execution. Together they create symmetric pre-/post-execution rigor as discussed in ADR-0005.

## Agent specifications

The 5 dispatched agents live in `claude-code/agents/`:

- `code-reviewer.md` — KISS/SOLID/SOC/DRY + 5 mandatory patterns (scope, duplication, schema-regression, dead code, magic numbers)
- `security-auditor.md` — semantic OWASP review (mechanical handled by hook)
- `tdd-sequence-auditor.md` — git-log forensics: first tests/ commit < first src/ commit
- `context7-evidence-auditor.md` — new PyPI deps + MAJOR bumps audit
- `future-proofing-auditor.md` — hardcoded counts (proactive Tier 6+), magic numbers, version pins, premature abstractions

Each agent's prompt is the source-of-truth for that audit's logic.
