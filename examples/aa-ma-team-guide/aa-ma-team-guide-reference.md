# AA-MA Team Guide - Reference

**Immutable facts and constants for this task.**

_Last Updated: 2025-11-26_

---

## Output Files

- `docs/aa-ma-team-guide.md` - Main detailed guide
- `docs/aa-ma-quick-reference.md` - 2-page cheat sheet

## AA-MA ↔ Cursor Memory Banks Mapping

| AA-MA File | Cursor Equivalent | Purpose |
|------------|-------------------|---------|
| `[task]-plan.md` | `projectbrief.md` | High-level strategy |
| `[task]-reference.md` | `techContext.md` + `systemPatterns.md` | Immutable facts |
| `[task]-context-log.md` | `productContext.md` | Decisions history |
| `[task]-tasks.md` | `activeContext.md` | Current work focus |
| `[task]-provenance.log` | `progress.md` | Completed work history |

## Command Equivalents

| Claude Code | Cursor | Purpose |
|-------------|--------|---------|
| `/aa-ma-plan` | `npx cursor-bank init` | Initialize AA-MA structure |
| `/execute-aa-ma-step` | Plan mode → Act mode | Single task execution |
| `/execute-aa-ma-milestone` | "Update memory bank" prompt | Complete milestone |
| Context injection (XML) | `.cursor/rules/*.mdc` | Persistent instructions |

## Directory Structures

### Claude Code
```
.claude/dev/active/[task-name]/
├── [task]-plan.md
├── [task]-reference.md
├── [task]-context-log.md
├── [task]-tasks.md
└── [task]-provenance.log
```

### Cursor
```
/memory_bank/
├── projectbrief.md
├── techContext.md
├── systemPatterns.md
├── productContext.md
├── activeContext.md
└── progress.md

.cursor/rules/
└── *.mdc
```

## Source Documentation

### Cursor
- Official: https://docs.cursor.com/context/rules
- Memory Banks: https://www.lullabot.com/articles/supercharge-your-ai-coding-cursor-rules-and-memory-banks
- cursor-bank npm: https://github.com/tacticlaunch/cursor-bank

### Claude Code AA-MA
- CLAUDE.md lines 87-307
- aa-ma-execution skill: ~/.claude/skills/aa-ma-execution/SKILL.md
- Commands: ~/.claude/commands/aa-ma-plan.md
- Design doc: ~/.claude/docs/plans/2025-11-17-aa-ma-execution-commands-design.md

## Core Principles (5)

1. **Think before coding** - Plan deliberately, execute methodically
2. **Single source of truth** - Reference file = immutable facts
3. **Explicit over implicit** - Write down decisions, don't assume
4. **Context is king** - Inject state at session start
5. **Validate and rollback** - Checkpoints enable safe experimentation

## Decision Framework

```
                         │ Low Complexity  │ High Complexity
─────────────────────────┼─────────────────┼─────────────────
Single Session           │ Ad-hoc          │ AA-MA (Step)
─────────────────────────┼─────────────────┼─────────────────
Multi-Session/Team       │ AA-MA (Mile.)   │ AA-MA (Full)
```

## The 5-Minute Rule

> If explaining what you're doing would take >5 minutes, use AA-MA.
