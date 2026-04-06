# AA-MA Quick Reference Card

*Print this 2-page cheat sheet for quick access*

---

## Page 1: The AA-MA Workflow

### What is AA-MA?

**Advanced Agentic Memory Architecture** - A structured way to give AI assistants persistent memory across sessions using 5 files.

### The 5 Files

| File | Purpose | Update When |
|------|---------|-------------|
| **plan.md** | Strategy & goals | Start of task |
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

# Execute single step (warnings only)
/execute-aa-ma-step

# Execute milestone (RECOMMENDED - strict)
/execute-aa-ma-milestone

# Execute full plan (automation)
/execute-aa-ma-full
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

*Full guide: [aa-ma-team-guide.md](aa-ma-team-guide.md)*
*Last updated: 2026-04-05*
