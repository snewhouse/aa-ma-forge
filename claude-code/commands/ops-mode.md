---
description: Activate full operational constraints mode for disciplined, efficient execution
---

# Operational Mode Activated

This session is now operating in **OPS-MODE** with comprehensive operational constraints enforced.

## Active Constraints

### Token & Context Efficiency
- Minimize context loading - only essential information
- Compress outputs - no verbose explanations unless requested
- Focused reasoning - minimal "thinking out loud"
- When approaching 70% context, initiate compaction

### Tool Protocols

**Documentation & Research:**
- Context7 MCP for library/API documentation (retry once on failure, then fallback)
- WebSearch for current information beyond training cutoff
- WebFetch for specific documentation pages

**Code Search:**
| Need | Tool |
|------|------|
| Text patterns | GrepTool |
| Code structures | Skill(ast-grep) |
| Complex analysis | Python script |
| File patterns | Glob |
| Exploration | Task(Explore) |

### Parallel Execution Mandate

Before any multi-step task, evaluate:
```
Independent subtasks exist?
├── NO → Sequential execution
└── YES → Dependencies between them?
    ├── YES → Parallelize independent portions
    └── NO → DISPATCH PARALLEL AGENTS NOW
```

Use multiple Task tool invocations in a single message for parallelization.

### Development Discipline

**Principles enforced:**
- KISS - Keep It Simple, Stupid
- DRY - Don't Repeat Yourself
- SOLID - Object-oriented design principles
- SOC - Separation of Concerns
- 12 Factor App - Application architecture

**TDD Mandate:**
- RED → GREEN → REFACTOR cycle
- Write test BEFORE implementation
- No rationalizations for skipping

**Impact Analysis:**
- Use Skill(impact-analysis) for ALL code changes
- HIGH risk impacts must be resolved before proceeding

### System Mapping Pre-Flight

Before modifying code, perform 5-point check (if applicable):
1. **Architecture** - Files, modules, entry points
2. **Execution Flow** - Call chains, async boundaries
3. **Logging** - Existing observability
4. **Dependencies** - Imports, external services
5. **Environment** - Config, env vars, flags

Use `Skill(system-mapping)` for detailed protocol.

### Planning Output Protocol

At end of any planning:
1. Explicitly ask for approval
2. Offer options: proceed / create AA-MA docs / adjust
3. Identify single next action

---

## Session Start: Lessons Review

Before executing any task, check if the project has a `docs/lessons.md` file. If it exists, read the top 10 entries and internalize them. If it doesn't exist, note this and continue.

This enforces the self-improvement-loop rule: "At the beginning of EVERY new session, your first operational action must be to review lessons."

---

## Pre-Task Checklist

Before proceeding with your task:

- [ ] **Lessons reviewed** - Read `docs/lessons.md` top entries (if exists)
- [ ] **Skills reviewed** - Checked available skills for relevance
- [ ] **Parallelization evaluated** - Identified if subagents can help
- [ ] **System mapping needed?** - For code changes to unfamiliar areas
- [ ] **TDD applicable?** - Plan tests first if implementing code
- [ ] **AA-MA active?** - Check `.claude/dev/active/` for existing plans

---

## Quick Commands

| Command | Purpose |
|---------|---------|
| `Skill(operational-constraints)` | Full constraint documentation |
| `Skill(system-mapping)` | 5-point pre-flight protocol |
| `Skill(test-driven-development)` | TDD workflow |
| `Skill(impact-analysis)` | Change risk assessment |
| `Skill(dispatching-parallel-agents)` | Parallel execution patterns |

---

## Confirmation

```
OPS-MODE: ACTIVE

Constraints enforced:
  ✓ Lessons review (self-improvement loop)
  ✓ Token efficiency
  ✓ Tool protocols (Context7, GrepTool, ast-grep)
  ✓ Parallel execution evaluation
  ✓ TDD discipline
  ✓ System mapping pre-flight
  ✓ Planning approval protocol

Session ready for disciplined execution.
```

---

**What task would you like to work on?**
