# AA-MA Team Workflow Guide

**Advanced Agentic Memory Architecture for AI-Assisted Development**

*A comprehensive guide for teams using Claude Code and Cursor*

---

## Table of Contents

- [Part 0: Quick Start](#part-0-quick-start)
- [Part 1: AA-MA Principles](#part-1-aa-ma-principles)
- [Part 2: Claude Code Implementation](#part-2-claude-code-implementation)
- [Part 3: Cursor Implementation](#part-3-cursor-implementation)
- [Part 4: Decision Framework](#part-4-decision-framework)
- [Part 5: Team Collaboration](#part-5-team-collaboration)
- [Appendix: Troubleshooting & FAQ](#appendix-troubleshooting--faq)

---

# Part 0: Quick Start

*Read time: 5 minutes*

## What is AA-MA?

**AA-MA (Advanced Agentic Memory Architecture)** is a structured way to give AI assistants persistent memory across sessions. Instead of re-explaining your project every time you start a new conversation, you maintain a set of files that capture your project's state, decisions, and progress.

Think of it as "external memory" for your AI assistant. Just as you might keep notes to remember what you were working on yesterday, AA-MA provides a standardized format for AI assistants to "remember" context between sessions.

## The Five Files

AA-MA uses five files, each with a specific purpose:

| File | Purpose | Update Frequency |
|------|---------|------------------|
| **plan.md** | Strategy, goals, rationale | Once at start (historical record, not synced post-task) |
| **reference.md** | Immutable facts (APIs, paths, constants) | Add new facts as discovered |
| **context-log.md** | Decision history, trade-offs | After each major decision |
| **tasks.md** | Current work, next steps | Every session |
| **provenance.log** | Audit trail (commits, milestones) | Automatically after commits |

## Your First AA-MA Task (Example)

Let's say you're building a user authentication feature that will take several sessions:

### Step 1: Create the Directory
```bash
mkdir -p .claude/dev/active/user-auth/
cd .claude/dev/active/user-auth/
```

### Step 2: Create the Five Files
```bash
touch user-auth-plan.md user-auth-reference.md user-auth-context-log.md user-auth-tasks.md user-auth-provenance.log
```

### Step 3: Bootstrap with Initial Content

**user-auth-plan.md:**
```markdown
# User Auth - Plan
Objective: Add JWT-based authentication to the API
Success criteria: Users can register, login, and access protected routes
```

**user-auth-reference.md:**
```markdown
# User Auth - Reference
- API_BASE: /api/v1/auth
- JWT_EXPIRY: 3600 seconds
- User table: users (id, email, password_hash, created_at)
```

**user-auth-tasks.md:**
```markdown
# User Auth - Tasks
## Current: Implement registration endpoint
- Status: ACTIVE
- Acceptance: POST /register creates user, returns JWT
```

### Step 4: Start Each Session by Loading Context
When you begin a new session, tell the AI:
> "Continue the user-auth task. Load context from .claude/dev/active/user-auth/"

The AI will read your files and pick up exactly where you left off.

## The Workflow in 30 Seconds

```
┌─────────┐     ┌─────────┐     ┌─────────┐
│  PLAN   │ ──▶ │ EXECUTE │ ──▶ │  TRACK  │
│ (think) │     │  (act)  │     │ (learn) │
└─────────┘     └─────────┘     └─────────┘
```

1. **PLAN**: Think before coding. Write down what you're doing and why.
2. **EXECUTE**: Do the work. Follow your acceptance criteria.
3. **TRACK**: Record what happened. Update files, commit, log provenance.

That's it. The rest of this guide explains the details.

---

# Part 1: AA-MA Principles

*The "why" behind the system*

## 1.1 The Problem: LLM Amnesia

Large Language Models don't remember previous conversations. Every new session starts with a blank slate. This creates several problems:

**The Re-Explanation Tax**: You spend the first 10 minutes of every session explaining what you're working on, what decisions were made, and what files matter.

**Context Drift**: Without a single source of truth, details get lost or changed. "Wait, were we using JWT or session tokens?"

**Handoff Hell**: Passing work to a teammate (or to yourself after a weekend) requires extensive catch-up.

**Lost Progress**: You make a decision, don't document it, and three sessions later you're re-debating the same options.

## 1.2 The Solution: Structured External Memory

AA-MA solves LLM amnesia by externalizing memory into files. Instead of relying on the AI to remember, you store state explicitly.

**Why five files instead of one?** Each file has a different purpose and update cadence:

| File | Analogy | Changes When |
|------|---------|--------------|
| plan.md | Project charter | Rarely (scope changes only, not part of post-task sync) |
| reference.md | Technical specs | New facts discovered |
| context-log.md | Decision journal | Major decisions made |
| tasks.md | Sprint board | Every session |
| provenance.log | Git history | Every commit |

This separation means you don't re-read unchanged content and can prioritize what matters now (tasks) over what's stable (plan).

## 1.3 The Workflow: Plan → Execute → Track

AA-MA enforces a deliberate workflow:

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   ┌─────────┐     ┌─────────┐     ┌─────────┐              │
│   │  PLAN   │ ──▶ │ EXECUTE │ ──▶ │  TRACK  │ ──┐          │
│   │ (think) │     │  (act)  │     │ (learn) │   │          │
│   └─────────┘     └─────────┘     └─────────┘   │          │
│        │                                         │          │
│        └─────────────────────────────────────────┘          │
│                       (iterate)                             │
└─────────────────────────────────────────────────────────────┘
```

### PLAN Phase
- Define what you're building and why
- Set acceptance criteria (how will you know it's done?)
- Estimate complexity (0-100%)
- Identify dependencies

### EXECUTE Phase
- Work on the current task
- Follow your acceptance criteria
- Stay focused on the immediate goal
- Don't skip ahead

### TRACK Phase
- Update task status (PENDING → ACTIVE → COMPLETE)
- Extract new facts to reference.md
- Document decisions in context-log.md
- Commit and log to provenance.log

**The key discipline**: Complete the tracking phase *before* starting the next task. Don't batch updates.

## 1.4 Core Principles

Five principles guide AA-MA usage:

### 1. Think Before Coding
> "Plan deliberately, execute methodically."

Don't dive into code. Spend time upfront understanding the problem, defining acceptance criteria, and identifying risks. A plan that takes 30 minutes to write can save 3 hours of wandering.

### 2. Single Source of Truth
> "The reference file is non-negotiable."

When something is in reference.md, it's a fact. API endpoints, database schemas, configuration values—once confirmed, they don't get debated again. This prevents context drift.

### 3. Explicit Over Implicit
> "Write it down. Don't assume anyone will remember."

If you made a decision, document it. If you discovered a constraint, add it to reference.md. If you chose option A over option B, explain why in context-log.md. Future-you (or a teammate) will thank you.

### 4. Context is King
> "Inject state at session start."

Every session should begin by loading your AA-MA files. The AI needs context to be useful. Five minutes of context injection beats 30 minutes of "let me explain what we're doing."

### 5. Validate and Rollback
> "Checkpoints enable safe experimentation."

Each milestone is a checkpoint. If something goes wrong, you can roll back to the last known good state. This safety net encourages experimentation without fear.

## 1.5 The Mental Model

Think of AA-MA as giving your AI assistant a "working memory notebook":

- **plan.md** = "What's the big picture?"
- **reference.md** = "What do I know for certain?"
- **context-log.md** = "What did we decide and why?"
- **tasks.md** = "What am I doing right now?"
- **provenance.log** = "What have we accomplished?"

When you start a session, you hand the AI this notebook. When you end a session, you update it. The AI becomes a powerful partner because it has the context it needs to help effectively.

---

# Part 2: Claude Code Implementation

*How to use AA-MA with Claude Code*

## 2.1 Directory Structure

Claude Code uses the following convention:

```
.claude/
└── dev/
    └── active/
        └── [task-name]/
            ├── [task-name]-plan.md
            ├── [task-name]-reference.md
            ├── [task-name]-context-log.md
            ├── [task-name]-tasks.md
            └── [task-name]-provenance.log
```

**Example**: For a task called "api-refactor":
```
.claude/dev/active/api-refactor/
├── api-refactor-plan.md
├── api-refactor-reference.md
├── api-refactor-context-log.md
├── api-refactor-tasks.md
└── api-refactor-provenance.log
```

## 2.2 The Five Files in Detail

### plan.md
**Purpose**: High-level strategy and rationale

```markdown
# [task-name] Plan

**Objective:** [What are you building?]
**Owner:** [Who's responsible?]
**Created:** YYYY-MM-DD
**Last Updated:** YYYY-MM-DD

## Executive Summary
[2-3 sentences on the goal and approach]

## Success Criteria
- [ ] [Criterion 1]
- [ ] [Criterion 2]

## Out of Scope
- [What you're explicitly NOT doing]

## Risks
- [Risk 1]: [Mitigation]
```

### reference.md
**Purpose**: Immutable facts (highest priority)

```markdown
# [task-name] Reference

_Last Updated: YYYY-MM-DD_

## API Endpoints
- POST /api/auth/login - JWT authentication
- GET /api/users/{id} - User profile

## File Paths
- src/auth/jwt.py - Token handling
- src/models/user.py - User model

## Configuration
- JWT_SECRET_KEY: Set in .env
- TOKEN_EXPIRY: 3600 seconds

## Database Schema
- users: id, email, password_hash, created_at
```

### context-log.md
**Purpose**: Decision history with rationale

```markdown
# [task-name] Context Log

## [YYYY-MM-DD] Decision: [Title]

**Context:** [What situation prompted this decision?]
**Decision:** [What was decided]
**Rationale:** [Why this approach]
**Alternatives Rejected:**
- [Option B]: [Why not]
- [Option C]: [Why not]
**Trade-offs:** [Pros and cons accepted]

---

## [YYYY-MM-DD] Compaction Summary
[Summary of previous decisions when context was compacted]
```

### tasks.md
**Purpose**: Hierarchical task tracking (HTP)

```markdown
# [task-name] Tasks (HTP)

## Milestone 1: [Title]
- Status: ACTIVE
- Dependencies: None
- Complexity: 45%
- Acceptance Criteria:
  - [Testable criterion 1]
  - [Testable criterion 2]

### Step 1.1: [Action]
- Status: COMPLETE
- Result Log: [What happened]

### Step 1.2: [Action]
- Status: ACTIVE
- Result Log:

---

## Milestone 2: [Title]
- Status: PENDING
- Dependencies: Milestone 1
- Complexity: 60%
```

**Status Values:**
- `PENDING` - Not started, waiting for dependencies
- `ACTIVE` - Currently being worked on (only ONE at a time)
- `COMPLETE` - Done, acceptance criteria met
- `BLOCKED` - Cannot proceed, needs resolution

### provenance.log
**Purpose**: Audit trail (machine-readable)

```
# [task-name] Provenance Log

[2025-11-26 14:32] Commit abc123 — TaskID: step-1.1 — Status: COMPLETE — Tests: PASS
[2025-11-26 15:45] Commit def456 — TaskID: step-1.2 — Status: COMPLETE — Tests: PASS
[2025-11-26 16:20] MILESTONE 1 COMPLETE — Commit ghi789 — Tests: PASS
[2025-11-26 17:00] CONTEXT COMPACTED — Session reset
```

## 2.3 Slash Commands

Claude Code provides four slash commands for AA-MA:

### `/aa-ma-plan` - Initialize a New Task

**When to use**: Starting a complex, multi-session task

**What it does**:
1. Brainstorms the approach with you
2. Creates the 5-file structure
3. Populates files with initial content
4. Extracts facts to reference.md

**Example**:
```
/aa-ma-plan Build a REST API for user management with JWT authentication
```

### `/execute-aa-ma-step` - Execute Single Task

**When to use**: Quick iteration, exploratory work

**Validation**: Guidance-based (warnings only)
**Git**: No auto-commit

```
/execute-aa-ma-step
```

### `/execute-aa-ma-milestone` - Execute Complete Milestone (RECOMMENDED)

**When to use**: Delivering complete features, production changes

**Validation**: Strict (blocks on failure)
**Git**: Auto-commit + provenance logging

```
/execute-aa-ma-milestone
```

### `/execute-aa-ma-full` - Execute Entire Plan

**When to use**: Long-horizon automation, well-tested plans

**Validation**: Strict at every milestone
**Git**: Auto-commit at each milestone + final tag

```
/execute-aa-ma-full
```

## 2.4 Context Injection

When starting a session, Claude Code loads AA-MA files with XML delimiters:

```xml
<REFERENCE>
[Contents of reference.md - strict facts, non-negotiable]
</REFERENCE>

<TASKS>
[Contents of tasks.md - current state, next action]
</TASKS>

<CONTEXT_LOG>
[Contents of context-log.md - decision history]
</CONTEXT_LOG>

<PLAN>
[Contents of plan.md - strategy, if tokens allow]
</PLAN>

<PROVENANCE>
[Contents of provenance.log - audit trail, if tokens allow]
</PROVENANCE>
```

**Priority Order** (load first when token-constrained):
1. REFERENCE (facts)
2. TASKS (current state)
3. CONTEXT_LOG (decisions)
4. PLAN (strategy)
5. PROVENANCE (history)

## 2.5 Complexity Scoring

Each task has a **Complexity** field (0-100%):

| Score | Meaning | Implications |
|-------|---------|--------------|
| 0-30% | Simple | Straightforward, low risk |
| 31-50% | Moderate | Some decisions needed |
| 51-79% | Complex | Significant reasoning required |
| **80-100%** | Expert | **Flag for deep review** |

**High complexity (≥80%)** triggers:
- Explicit human review checkpoint
- Chain-of-thought reasoning requirement
- Additional testing
- Reasoning documented in context-log.md

## 2.6 Tips & Tricks

### Preventing Context Loss
- **Start every session** with "Continue the [task-name] task"
- **Update files immediately** after task completion (don't batch)
- **Compact context at 70%** token usage to avoid losing work

### Context Compaction
When token limit approaches:
1. Summarize completed work and key decisions
2. Add summary to context-log.md
3. Start new session
4. Reload the 5 files

### Validation Modes
- **Step mode**: Warnings only (for exploration)
- **Milestone mode**: Must meet acceptance criteria (recommended)
- **Full mode**: Strict throughout (for automation)

### Writing Good Acceptance Criteria

**Good (testable)**:
- "POST /register returns 201 with valid JWT"
- "Password hashed with bcrypt, cost factor 12"
- "All tests pass, coverage ≥80%"

**Bad (vague)**:
- "Registration works"
- "Passwords are secure"
- "Tests are good"

---

# Part 3: Cursor Implementation

*How to apply AA-MA principles in Cursor*

## 3.1 Directory Structure

Cursor uses a different convention but the same principles:

```
/memory_bank/
├── projectbrief.md       # ≈ plan.md
├── techContext.md        # ≈ reference.md (tech facts)
├── systemPatterns.md     # ≈ reference.md (patterns)
├── productContext.md     # ≈ context-log.md
├── activeContext.md      # ≈ tasks.md
└── progress.md           # ≈ provenance.log

.cursor/
└── rules/
    └── *.mdc             # Persistent instructions
```

## 3.2 Memory Bank Files Mapping

| AA-MA File | Cursor File(s) | Purpose |
|------------|----------------|---------|
| `plan.md` | `projectbrief.md` | High-level overview |
| `reference.md` | `techContext.md` + `systemPatterns.md` | Tech stack + coding patterns |
| `context-log.md` | `productContext.md` | Features and business logic |
| `tasks.md` | `activeContext.md` | Current focus and immediate tasks |
| `provenance.log` | `progress.md` | Implementation history |

### projectbrief.md (≈ plan.md)
```markdown
# Project Brief

## Objective
[High-level project overview]

## Tech Stack
[Languages, frameworks, databases]

## Key Goals
- [Goal 1]
- [Goal 2]
```

### techContext.md (≈ reference.md facts)
```markdown
# Technical Context

## Technologies
- Python 3.11
- FastAPI 0.104
- PostgreSQL 15

## Development Setup
[How to run locally]

## API Base URLs
- Dev: http://localhost:8000
- Prod: https://api.example.com
```

### systemPatterns.md (≈ reference.md patterns)
```markdown
# System Patterns

## Architecture
[Describe the overall structure]

## Coding Standards
- Use type hints
- Follow PEP 8
- Write docstrings for public functions

## Common Patterns
[Recurring patterns in this codebase]
```

### productContext.md (≈ context-log.md)
```markdown
# Product Context

## Features
[What the product does]

## Business Logic
[Important rules and constraints]

## Recent Decisions
[Why things are the way they are]
```

### activeContext.md (≈ tasks.md)
```markdown
# Active Context

## Current Focus
[What you're working on right now]

## Immediate Tasks
- [ ] Task 1
- [ ] Task 2

## Blockers
[Anything preventing progress]
```

### progress.md (≈ provenance.log)
```markdown
# Progress

## Completed
- [Date] Feature X implemented
- [Date] Bug Y fixed

## In Progress
- Feature Z (started [date])
```

## 3.3 Cursor Rules Configuration

Rules provide persistent context. Create files in `.cursor/rules/`:

### Rule Types

| Type | Trigger | Use Case |
|------|---------|----------|
| **Always** | Every request | Core coding standards |
| **Auto** | AI decides | Context-specific guidance |
| **Agent** | Explicit reference | Specialized instructions |

### Example Rule: `.cursor/rules/coding-standards.mdc`

```markdown
---
description: Project coding standards
alwaysApply: true
---

# Coding Standards

- Use TypeScript strict mode
- Prefer async/await over callbacks
- Write tests before implementation (TDD)
- Use conventional commits format
```

### Example Rule: `.cursor/rules/api-patterns.mdc`

```markdown
---
description: API development patterns
globs: ["src/api/**/*.ts", "src/routes/**/*.ts"]
---

# API Patterns

- Use Zod for request validation
- Return consistent error format: { error: string, code: string }
- Include request ID in all responses
```

## 3.4 Plan/Act Workflow

Cursor supports a Plan/Act workflow similar to AA-MA:

### Plan Mode
- AI proposes changes without implementing
- You review the approach
- Modify or approve

### Act Mode
- AI executes the approved plan
- Implementation happens
- Review results

**To enforce Plan/Act**:
1. Install cursor-bank: `npx cursor-bank init`
2. Use the generated rules
3. Explicitly say "Plan mode" or "Act mode"

## 3.5 Setup Instructions

### Quick Setup with cursor-bank

```bash
# Initialize memory bank structure
npx cursor-bank init

# This creates:
# - /memory_bank/ directory with 6 files
# - .cursor/rules/ with core rules
```

### Manual Setup

```bash
# Create directories
mkdir -p memory_bank .cursor/rules

# Create memory bank files
touch memory_bank/projectbrief.md
touch memory_bank/techContext.md
touch memory_bank/systemPatterns.md
touch memory_bank/productContext.md
touch memory_bank/activeContext.md
touch memory_bank/progress.md

# Create core rule
cat > .cursor/rules/memory-bank.mdc << 'EOF'
---
description: Memory bank integration
alwaysApply: true
---

Always check memory_bank/ files for context before responding.
Update activeContext.md after completing tasks.
EOF
```

## 3.6 Tips & Tricks

### Model Selection
Different models follow rules differently:
- **GPT-4o**: Strong instruction following
- **Gemini 2.5 Pro**: Excellent compliance
- **Claude 3.5 Sonnet**: Creative but may ignore rules

For AA-MA workflows, prefer models with strong instruction following.

### Privacy Mode Considerations
If using enforced Privacy Mode:
- Memory banks and history may not sync
- Background agents may be restricted
- Validate with your organization's policy

### Keeping Memory Banks Fresh
After completing features:
1. Update `activeContext.md` with current focus
2. Move completed items to `progress.md`
3. Add any new technical facts to `techContext.md`
4. Commit the memory bank changes

**Critical**: Update memory banks *before* ending a session, not after starting the next one.

### Cursor + Claude Code Interoperability

If your team uses both tools:

1. **Keep both directory structures**:
   - `.claude/dev/active/` for Claude Code
   - `/memory_bank/` for Cursor

2. **Sync manually or via script**:
   ```bash
   # Sync Claude Code → Cursor
   cp .claude/dev/active/task/task-plan.md memory_bank/projectbrief.md
   cp .claude/dev/active/task/task-reference.md memory_bank/techContext.md
   # etc.
   ```

3. **Or maintain one source of truth** and symlink:
   ```bash
   # Use Claude Code as primary, symlink for Cursor
   ln -s ../.claude/dev/active/task/task-plan.md memory_bank/projectbrief.md
   ```

---

# Part 4: Decision Framework

*When to use AA-MA vs ad-hoc*

## 4.1 The Decision Matrix

```
                         │ Low Complexity  │ High Complexity
                         │   (< 30 min)    │   (> 30 min)
─────────────────────────┼─────────────────┼─────────────────
Single Session           │   AD-HOC        │   AA-MA
(one sitting)            │   (just do it)  │   (Step mode)
─────────────────────────┼─────────────────┼─────────────────
Multi-Session            │   AA-MA         │   AA-MA
(or team handoff)        │   (Milestone)   │   (Full mode)
```

## 4.2 Quick Signals: Use AA-MA When...

✅ **Use AA-MA** if ANY of these apply:

- Task will span multiple sessions
- Multiple team members will be involved
- Complexity > 50% (needs clear acceptance criteria)
- You need an audit trail for compliance/debugging
- Risk of "where was I?" moments
- Handoff to someone else is expected
- Making architectural decisions that affect future work

## 4.3 Quick Signals: Stay Ad-hoc When...

❌ **Skip AA-MA** if ALL of these apply:

- Quick fix (< 30 minutes)
- Single-file change
- Exploratory/research (no deliverable)
- No handoff to others expected
- Low risk, easily reversible
- You'll remember what you did

## 4.4 The 5-Minute Rule

> **If explaining what you're doing would take more than 5 minutes, use AA-MA.**

The time you spend writing a plan pays for itself in context restoration. A 10-minute plan saves 30 minutes of re-explanation next session.

## 4.5 Edge Cases

### "I'm not sure how long this will take"
Start ad-hoc. If it takes more than 30 minutes or you realize you'll need another session, **upgrade to AA-MA**.

### "It's just me, I don't need to document"
Future-you is a different person. Three days from now, you won't remember the nuances. Document for your future self.

### "The team doesn't use AA-MA yet"
Start using it yourself. When others see the benefits (faster handoffs, less re-explanation), adoption will follow.

### "This is exploratory research"
Research doesn't need AA-MA. But when research transitions to implementation, create the AA-MA structure.

---

# Part 5: Team Collaboration

*Multi-developer AA-MA patterns*

## 5.1 Shared Directory Patterns

### Option A: One AA-MA per Feature Branch

```
main branch:
  .claude/dev/active/  (empty or archived tasks)

feature/user-auth branch:
  .claude/dev/active/user-auth/
  ├── user-auth-plan.md
  ├── user-auth-reference.md
  └── ...
```

**Pros**: Clear ownership, no conflicts
**Cons**: Need to merge AA-MA files when merging branches

### Option B: Shared Active Directory

```
.claude/dev/active/
├── user-auth/      (owned by Alice)
├── api-refactor/   (owned by Bob)
└── bug-fix-123/    (owned by Charlie)
```

**Pros**: All tasks visible, easy handoff
**Cons**: Potential conflicts if not coordinated

### Recommended: Option A + Archive

1. Each feature branch has its own AA-MA task
2. When merged, move task to `.claude/dev/archive/`
3. Keep archive for historical reference

## 5.2 Handoff Protocol

When passing AA-MA work to a teammate:

### Before Handoff
1. **Complete current step** (don't hand off mid-task)
2. **Update all 5 files** (especially tasks.md and context-log.md)
3. **Commit everything**:
   ```bash
   git add .claude/dev/active/task-name/
   git commit -m "chore(task-name): handoff to [teammate]"
   ```
4. **Add handoff note** to context-log.md:
   ```markdown
   ## [YYYY-MM-DD] Handoff to [Name]

   **Current State:** [Where things are]
   **Next Steps:** [What needs to happen]
   **Known Issues:** [Any gotchas]
   **Contact:** [How to reach you for questions]
   ```

### After Receiving Handoff
1. **Read context-log.md first** (understand the history)
2. **Load full context** (all 5 files)
3. **Ask clarifying questions** before starting
4. **Update context-log.md** acknowledging receipt

## 5.3 Conflict Resolution

### When Reference Files Conflict
The **reference.md** is the source of truth. If two people add conflicting facts:
1. Discuss and agree on the correct fact
2. One person updates reference.md
3. Other updates their local copy

### When Tasks Conflict
If two people are working on the same task:
1. **Stop immediately**
2. Coordinate who owns what
3. Split the task or assign to one person
4. Update tasks.md to reflect the split

### General Rule
**Communicate before modifying someone else's AA-MA files.** A quick Slack message prevents merge conflicts.

## 5.4 Code Review for AA-MA

When reviewing PRs that include AA-MA files:

**Check for:**
- [ ] tasks.md shows all tasks COMPLETE
- [ ] reference.md has any new facts extracted
- [ ] context-log.md documents key decisions
- [ ] provenance.log shows commits match the work
- [ ] No secrets in any AA-MA files

**Don't require:**
- Perfect prose in context-log.md
- Exhaustive provenance logs
- Plan.md updates for minor changes

---

# Appendix: Troubleshooting & FAQ

## Common Issues

### "The AI doesn't read my AA-MA files"

**Cause**: Context wasn't loaded at session start
**Fix**: Explicitly say "Continue the [task-name] task from .claude/dev/active/[task-name]/"

### "My AA-MA files are out of sync"

**Cause**: Updates were batched instead of immediate
**Fix**: Update files after *each* task completion, not at end of session

### "Token limit reached mid-task"

**Cause**: Too much context loaded
**Fix**:
1. Use context compaction (summarize to context-log.md)
2. Start new session
3. Load only REFERENCE and TASKS initially

### "Multiple ACTIVE tasks in tasks.md"

**Cause**: Previous task wasn't marked COMPLETE
**Fix**: Only ONE task should be ACTIVE. Mark previous as COMPLETE or PENDING.

### "Cursor doesn't follow my rules"

**Cause**: Model may ignore rules, or rules not in Always mode
**Fix**:
1. Check rule has `alwaysApply: true`
2. Try a different model (GPT-4o follows rules better)
3. Explicitly reference the rule in your prompt

## FAQ

### Q: How long should I keep AA-MA files?

**A**: Archive after the task is complete (merged to main). Keep archives for 3-6 months for reference, then delete or compress.

### Q: Can I use AA-MA for non-coding tasks?

**A**: Yes! AA-MA works for any complex, multi-session task: writing documentation, research projects, design work.

### Q: What if my task changes scope mid-way?

**A**: Update plan.md with the new scope. Add a context-log.md entry explaining the change. Continue with updated acceptance criteria.

### Q: Should I commit AA-MA files to git?

**A**: Yes, but in `.claude/dev/active/`. This provides version history and enables team collaboration. Exclude sensitive information.

### Q: How detailed should provenance.log be?

**A**: Minimal: commit hash, task ID, status, test result. It's for debugging, not documentation. Let git provide the details.

### Q: Can I share AA-MA files between Claude Code and Cursor?

**A**: Yes, with manual syncing or symlinks. See Part 3.6 for details.

### Q: What's the minimum viable AA-MA?

**A**: If you're time-constrained, create only:
1. **reference.md** (critical facts)
2. **tasks.md** (current state)

Add the other files as needed.

### Q: How do I know if my complexity estimate is right?

**A**: After completing a few tasks, compare estimated vs actual. Adjust your calibration. Most people underestimate initially.

---

## Quick Reference

See the companion document: **[AA-MA Quick Reference Card](aa-ma-quick-reference.md)**

---

*Last updated: 2025-11-26*
