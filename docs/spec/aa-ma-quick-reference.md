# AA-MA Quick Reference Card

*Print this 2-page cheat sheet for quick access*

---

## Page 1: The AA-MA Workflow

### What is AA-MA?

**Advanced Agentic Memory Architecture** - A structured way to give AI assistants persistent memory across sessions using 5 files.

### The 5 Files

| File | Purpose | Update When |
|------|---------|-------------|
| **plan.md** | Strategy & goals | Start of task (historical, not synced post-task) |
| **reference.md** | Facts (APIs, paths) | New facts found |
| **context-log.md** | Decisions & why | After decisions |
| **tasks.md** | Current work | Every session |
| **provenance.log** | Audit trail | After commits |

### The Workflow

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│  PLAN   │ ──▶ │ EXECUTE │ ──▶ │  TRACK  │
│ (think) │     │  (act)  │     │ (learn) │
└─────────┘     └─────────┘     └─────────┘
```

### Core Principles

1. **Think before coding** - Plan deliberately
2. **Single source of truth** - Reference file = facts
3. **Explicit over implicit** - Write it down
4. **Context is king** - Load state at session start
5. **Validate and rollback** - Checkpoints = safety

### When to Use AA-MA

```
                    │ Low Complex │ High Complex
────────────────────┼─────────────┼─────────────
Single Session      │   Ad-hoc    │   AA-MA
Multi-Session/Team  │   AA-MA     │   AA-MA
```

**Use AA-MA when:**
- Multi-session task
- Team handoff expected
- Complexity > 50%
- Need audit trail

**The 5-Minute Rule:**
> If explaining what you're doing takes > 5 minutes, use AA-MA.

### Task Status Values

| Status | Meaning |
|--------|---------|
| `PENDING` | Not started |
| `ACTIVE` | Working now (ONE only) |
| `COMPLETE` | Done |
| `BLOCKED` | Cannot proceed |

### Milestone Gate Types

| Gate | Enforcement |
|------|-------------|
| `SOFT` (default) | Convention-based — agent warned |
| `HARD` | Artifact-enforced — blocked without signed approval in context-log.md |

### Optional Files

| File | Purpose |
|------|---------|
| `[task]-tests.yaml` | Machine-executable test definitions per milestone |
| `[task]-verification.md` | Adversarial verification audit trail |

### Complexity Scoring

| Score | Level | Action |
|-------|-------|--------|
| 0-30% | Simple | Proceed |
| 31-50% | Moderate | Some care |
| 51-79% | Complex | Extra testing |
| **80-100%** | Expert | **Human review** |

---

## Page 2: Commands Cheat Sheet

### Claude Code Commands

```bash
# Initialize new AA-MA task
/aa-ma-plan [description]

# Phase 1.3 grill-mode dispatch (v0.6.0+):
#   --grill-mode=auto       (default) CONTEXT.md or docs/adr/ present → with-docs;
#                                     else falls through to /grill-me
#   --grill-mode=with-docs  force Skill(grill-with-docs) — see ADR-0002
#   --grill-mode=simple     force the v0.5.0 /grill-me protocol
#   --grill-mode=skip       bypass Phase 1.3 entirely
# Env-var equivalent: AA_MA_GRILL_MODE
# CLI > env > default. See scripts/grill-mode-resolver.sh for the canonical
# resolver (8 branches, 13 unit tests).

# Stress-test a plan before executing
/grill-me [artifact]

# Adversarial 6-angle verification
/verify-plan [task-name]

# Execute single step (warnings only)
/execute-aa-ma-step

# Execute milestone (RECOMMENDED - strict)
/execute-aa-ma-milestone

# Execute full plan (automation)
/execute-aa-ma-full

# Archive completed task
/archive-aa-ma [task-name]

# Activate disciplined execution mode
/ops-mode

# Onboard to a new / inherited / shared codebase (tiered)
/understand-codebase [path] [--quick | --standard | --deep]
```

### Claude Code Directory Structure

```
.claude/dev/active/[task-name]/
├── [task]-plan.md
├── [task]-reference.md
├── [task]-context-log.md
├── [task]-tasks.md
└── [task]-provenance.log
```

### Context Injection (Claude Code)

```xml
<REFERENCE>
[Facts - highest priority]
</REFERENCE>

<TASKS>
[Current state - required]
</TASKS>

<CONTEXT_LOG>
[Decisions - important]
</CONTEXT_LOG>
```

---

### Cursor Commands

```bash
# Initialize memory bank
npx cursor-bank init

# Update memory bank after work
"Update memory bank with today's progress"

# Switch modes
"Plan mode" / "Act mode"
```

### Cursor Directory Structure

```
/memory_bank/
├── projectbrief.md      # ≈ plan.md
├── techContext.md       # ≈ reference.md
├── systemPatterns.md    # ≈ reference.md
├── productContext.md    # ≈ context-log.md
├── activeContext.md     # ≈ tasks.md
└── progress.md          # ≈ provenance.log

.cursor/rules/*.mdc      # Persistent instructions
```

### Cursor Rule Types

| Type | Trigger | Use Case |
|------|---------|----------|
| Always | Every request | Coding standards |
| Auto | AI decides | Context-specific |
| Agent | Explicit ref | Specialized |

---

### File Mapping: Claude Code ↔ Cursor

| Claude Code | Cursor | Purpose |
|-------------|--------|---------|
| plan.md | projectbrief.md | Strategy |
| reference.md | techContext.md + systemPatterns.md | Facts |
| context-log.md | productContext.md | Decisions |
| tasks.md | activeContext.md | Current work |
| provenance.log | progress.md | History |

---

### Quick Start Checklist

**Starting a Session:**
- [ ] Say "Continue [task-name] task"
- [ ] Verify AA-MA files loaded
- [ ] Check current ACTIVE task

**Ending a Session:**
- [ ] Mark task COMPLETE or note progress
- [ ] Update reference.md with new facts
- [ ] Log decisions to context-log.md
- [ ] Commit and update provenance.log

**Handoff to Teammate:**
- [ ] Complete current step
- [ ] Update all 5 files
- [ ] Add handoff note to context-log.md
- [ ] Commit everything
- [ ] Notify teammate

---

### Common Fixes

| Problem | Fix |
|---------|-----|
| AI doesn't read files | "Load context from [path]" |
| Files out of sync | Update after EACH task |
| Token limit | Compact to context-log |
| Multiple ACTIVE | Mark others COMPLETE |

---

### Phase Markers (v0.7.0+)

`/aa-ma-plan` writes a runtime log at `~/.claude/runtime/aa-ma-plan-<slug>.log`
recording every phase. The advisory hook `aa-ma-plan-skip-warn.sh` warns at
`PreToolUse(ExitPlanMode)` / `SessionEnd` if any phase is missing or has a
SKIPPED marker without a `reason=<token>`.

**9 required markers** (plus PHASE_0 INIT):

```
PHASE_1   DONE — context_gathering=complete
PHASE_1.3 DONE — grill_mode=<mode> branches_resolved=<N> questions_asked=<N>
PHASE_1.5 DONE — lessons_loaded=<N> git_grep_hits=<N>
PHASE_2   DONE — brainstorm_skill=invoked alternatives_considered=<N>
PHASE_3   DONE — context7_calls=<N> web_fetches=<N>
PHASE_4   DONE — complexity_score=<N>% plan_elements=<N>/12
PHASE_4.2 DONE — reviews=<csv>             (or SKIPPED — reason=<token>)
PHASE_4.5 DONE — verdict=<G|Y|R> ...       (or SKIPPED — reason=<token>)
PHASE_5   DONE — artifacts=5 task_dir=<path>
```

**Bypass:** `export AA_MA_HOOKS_DISABLE=1` (existing master kill switch).
**Canonical contract:** `docs/spec/plan-marker-grammar.md`.

---

*Full guide: [aa-ma-team-guide.md](aa-ma-team-guide.md)*
*Last updated: 2026-05-11*
