---
name: operational-constraints
description: Activate comprehensive operational constraints for disciplined execution. Use at session start, before complex tasks, during planning phases, or when encountering friction. Enforces token efficiency, tool protocols, parallel execution, TDD, and system mapping.
triggers:
  - ops-mode
  - ultrathink
  - operational mode
  - disciplined execution
  - complex task
  - enable constraints
---

# Operational Constraints Skill

Comprehensive operational rules for disciplined Claude Code execution. This skill captures battle-tested constraints that prevent common pitfalls and ensure consistent, high-quality outputs.

## When to Use

**ALWAYS invoke this skill when:**
- Starting a session that will involve complex multi-step work
- Before `/aa-ma-plan` or any significant planning
- After encountering friction or repeated issues
- When you notice yourself making avoidable mistakes
- Any session requiring disciplined, methodical execution

**Quick activation:** `/ops-mode` command loads this automatically.

---

## Core Constraints

### 1. Token & Context Efficiency

**Principles:**
- ALWAYS be mindful of current session token and context usage
- Optimise token utilisation - load only essential context
- Keep reasoning minimal and focused on the task
- Compress verbose outputs; surface only essentials

**Actions:**
- When approaching 70% context usage, consider context compaction
- Prefer loading REFERENCE and TASKS files over full history
- Suppress verbose logs unless actively debugging
- Use structured summaries over lengthy explanations
- No redundant confirmation messages

**Anti-patterns to avoid:**
- Loading entire files when only specific sections needed
- Repeating information already established in context
- Verbose "thinking out loud" when concise reasoning suffices

---

### 2. Research & Tools Protocol

**Principles:**
- Use the right tool for the job
- Leverage external knowledge sources for current information
- Prefer specialized tools over bash commands

**Tool Selection Matrix:**

| Need | Primary Tool | Alternative |
|------|--------------|-------------|
| Library/API docs | Context7 MCP | WebSearch |
| Current information | WebSearch | WebFetch |
| Text pattern search | GrepTool | - |
| Structural code search | Skill(ast-grep) | GrepTool |
| Complex file analysis | Python script | - |
| File pattern matching | Glob | - |
| Codebase exploration | Task(Explore) | GrepTool + Glob |

**Context7 MCP Protocol:**
1. ALWAYS use Context7 for library/API documentation when available
2. If Context7 fails, retry once
3. If retry fails, fallback to:
   - Native Claude Code documentation tools
   - Community-vetted code snippets
   - Official documentation via WebFetch
4. Record and surface fallback status

**Search Tools:**
```
# Pattern-based content search
GrepTool: pattern="function_name", path="src/"

# Structural code search (AST-based)
Skill(ast-grep) for:
- Finding all function definitions matching pattern
- Refactoring code structures
- Complex code transformations

# Large file analysis
Python script when:
- Multiple processing steps required
- Complex logic needed
- Results need aggregation
```

---

### 3. Parallel Execution Mandate

**Principle:** MUST evaluate if parallel subagents can handle independent subtasks.

**Decision Tree:**
```
Are there multiple distinct subtasks?
├── NO → Execute sequentially
└── YES → Do they have dependencies between them?
    ├── YES → Identify dependency chain, parallelize independent portions
    └── NO → PARALLELIZE IMMEDIATELY
```

**When to use parallel agents:**
- 3+ independent research questions
- Multiple files need analysis without interdependencies
- Different aspects of a problem can be explored simultaneously
- Investigation tasks that don't share state

**How to parallelize:**
```
Use Task tool with multiple invocations in SINGLE message:
- Task 1: Explore agent for area A
- Task 2: Explore agent for area B
- Task 3: Plan agent for design

OR use Skill(dispatching-parallel-agents) for structured dispatch.
```

**Anti-patterns:**
- Sequential execution of clearly independent tasks
- Waiting for one exploration to complete before starting another
- Not considering parallelization at all

---

### 4. Development Discipline

**Core Principles:**
- **KISS** - Keep It Simple, Stupid
- **DRY** - Don't Repeat Yourself
- **SOLID** - Single responsibility, Open-closed, Liskov substitution, Interface segregation, Dependency inversion
- **SOC** - Separation of Concerns
- **12 Factor App** - For application architecture

**TDD Mandate:**
- Follow Test-Driven Development via `Skill(test-driven-development)`
- RED → GREEN → REFACTOR cycle
- Write test BEFORE implementation
- No rationalizations for skipping tests

**Impact Analysis:**
- Use `Skill(impact-analysis)` for ALL code changes
- Required at milestone boundaries during AA-MA execution
- HIGH risk impacts must be resolved before proceeding

**Code Quality:**
- Functional working code over perfection
- Self-documenting code with intention-revealing names
- Comments explain WHY, not WHAT
- Follow existing codebase patterns

---

### 5. System Mapping (Pre-Flight)

**Principle:** Before modifying code, understand the system context.

**5-Point Protocol:**

| Point | Question | Tools |
|-------|----------|-------|
| 1. Architecture | What files/modules are involved? | Glob, LS |
| 2. Execution Flows | How does data/control flow? | Grep, ast-grep |
| 3. Logging | What observability exists? | Grep "logger\|logging" |
| 4. Dependencies | What does this code depend on? | Grep "import\|from" |
| 5. Environment | What config/env vars matter? | Grep "environ\|getenv" |

**When to perform:**
- Changes touch 3+ files
- Unfamiliar code area
- Integrating with external services
- Modifying data pipelines

**Detailed protocol:** See `Skill(system-mapping)`

---

### 6. Planning Output Protocol

**At the end of any planning phase, MUST:**

1. **Explicitly ask for approval** before proceeding
2. **Offer clear options:**
   - Proceed with implementation
   - Create AA-MA artifacts first
   - Adjust/refine the plan
3. **Create AA-MA artifacts** when approved for complex tasks
4. **Identify the single next action** to take

**Template:**
```
## Plan Summary
[Concise overview]

## Proposed Approach
[Key decisions]

## Ready to proceed?
- [ ] Approve and proceed
- [ ] Create AA-MA artifacts first
- [ ] Need adjustments: [specify]
```

---

## Checklists

### Session Start Checklist
- [ ] Is this a complex multi-step task? If yes, invoke this skill
- [ ] Any active AA-MA plans? Check `.claude/dev/active/`
- [ ] What skills might apply? Review available skills

### Pre-Task Checklist
- [ ] Can this be parallelized? Evaluate subagent opportunities
- [ ] Is system-mapping needed? Check 5-point protocol triggers
- [ ] TDD applicable? Plan tests first if coding
- [ ] Impact analysis required? For code changes, always

### Pre-Commit Checklist
- [ ] All tests passing?
- [ ] Impact analysis completed for changes?
- [ ] AA-MA docs updated if active plan?
- [ ] Conventional commit message?

---

## Cross-References

| Skill/Command | Purpose | When to Use |
|---------------|---------|-------------|
| `Skill(system-mapping)` | Detailed 5-point pre-flight | Before code modifications |
| `Skill(test-driven-development)` | TDD enforcement | All coding tasks |
| `Skill(impact-analysis)` | Change risk assessment | Before and after code changes |
| `Skill(dispatching-parallel-agents)` | Parallel execution patterns | Independent subtasks |
| `Skill(ast-grep)` | Structural code search | Complex code analysis |
| `/ops-mode` | Quick constraint activation | Session start |
| `/aa-ma-plan` | Comprehensive planning | Major features |

---

## Quick Reference Card

```
TOKEN EFFICIENCY
├── Load only essential context
├── Compress outputs
└── No redundant confirmations

TOOLS
├── Context7 → Library docs
├── GrepTool → Pattern search
├── ast-grep → Structural search
└── Python → Complex analysis

PARALLEL
├── 3+ independent tasks → PARALLELIZE
├── No dependencies → PARALLELIZE
└── Use Task tool with multiple calls

DISCIPLINE
├── TDD: RED → GREEN → REFACTOR
├── KISS, DRY, SOLID, SOC
├── Impact analysis for all changes
└── System mapping for unfamiliar code

PLANNING
├── Ask approval before proceeding
├── Offer: proceed / AA-MA / adjust
└── Identify single next action
```

---

## Activation Confirmation

When this skill is loaded, acknowledge with:

```
OPERATIONAL CONSTRAINTS: ACTIVE

Enforcing:
- Token efficiency
- Tool protocols (Context7, GrepTool, ast-grep)
- Parallel execution evaluation
- TDD discipline
- System mapping pre-flight
- Planning approval protocol

Ready for disciplined execution.
```
