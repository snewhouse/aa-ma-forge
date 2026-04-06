---
name: aa-ma-plan
description: Advanced planning workflow with AA-MA methodology, superpowers skills, Context7 MCP, and multi-agent coordination
---

<!-- Renamed from /ultraplan to /aa-ma-plan on 2026-04-06.
     Reason: Anthropic shipped built-in "ultraplan" in Claude Code on 2026-04-04. -->

# /aa-ma-plan - AA-MA Planning Workflow

Comprehensive planning command that follows the Advanced Agentic Memory Architecture (AA-MA) methodology for complex software development tasks.

## Purpose

Use this command when you need to:
- Plan complex features or architectural changes
- Create structured, maintainable implementation roadmaps
- Follow AA-MA methodology with proper artifact generation
- Leverage superpowers skills for deep thinking and planning
- Coordinate multi-agent workflows for parallel research
- Optimize token usage while maintaining thorough documentation

## Key Features

- **Multi-input support:** Accepts selected text, inline description, or interactive prompts
- **Structured thinking:** Uses `/superpowers:brainstorming` for requirement refinement
- **Research integration:** Context7 MCP with automatic fallback, parallel agent dispatch
- **AA-MA compliance:** Auto-generates 6 files (plan, reference, context-log, tasks, provenance, verification)
- **Token optimized:** Concise screen output, verbose details saved to files
- **KISS/DRY/SOLID:** Follows fundamental design principles from CLAUDE.md

## Workflow Overview

```
Phase 1: Context Gathering    → Multi-method input + clarifications
Phase 2: Structured Thinking  → /superpowers:brainstorming refinement
Phase 3: Research & Docs      → Context7 MCP + parallel agents
Phase 4: Plan Generation      → /superpowers:writing-plans
Phase 4.5: Verification       → 6-angle adversarial plan check
Phase 5: AA-MA Artifacts      → Create .claude/dev/active/[task]/
```

---

## Instructions for AI

### Phase 1: Context Gathering & Input Processing

**Step 1.1: Detect Input Method**

Check for user context in this priority order:

1. **Context-aware (selected text):** If the user has selected text/code, use that as the feature request
2. **Interactive prompt:** If no selection, use `AskUserQuestion` to gather the request
3. **Inline argument:** Accept natural language description provided with the command

**Step 1.2: Gather Initial Context**

```bash
# Check current project state
pwd
git rev-parse --short HEAD 2>/dev/null || echo "Not a git repo"
ls -la .claude/dev/active/ 2>/dev/null || echo "No active tasks"
ls PROJECT_INDEX.json 2>/dev/null && echo "Index available" || echo "No index (suggest /index for structural awareness)"
```

If `PROJECT_INDEX.json` exists, include its structural context in planning:
- Read `dir_purposes` and `tree` for architecture overview
- Read `_meta.symbol_importance` for key entry points
- This pre-loads structural understanding so Phase 2-3 research is better targeted

**Step 1.3: Grill-Me Protocol**

Before moving to structured thinking, apply the `/grill-me` discipline: interview the user relentlessly about every aspect of their request. Walk down each branch of the design/decision tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer. If a question can be answered by exploring the codebase, explore the codebase instead of asking.

Continue until all major decision branches are resolved. This prevents building plans on unresolved assumptions.

**Step 1.4: Ask Clarifying Questions**

Use `AskUserQuestion` to clarify any remaining details:
- Task name (for directory structure)
- Primary objective (1-2 sentences)
- Known constraints or requirements
- Complexity estimate (simple/medium/complex)

Display gathered context in a clean summary:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 1 COMPLETE: Context Gathered
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Task: [name]
Objective: [summary]
Complexity: [estimate]
Project: [path]
Commit: [hash]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### Phase 2: Structured Thinking with Brainstorming

**Step 2.1: Invoke Brainstorm Skill**

```
Skill: superpowers:brainstorming
```

**Step 2.2: Pass Context to Brainstorm**

Provide the skill with:
- User's feature request
- Known constraints
- Project context (language, frameworks from file scan)
- Design principles: KISS, DRY, SOLID, SOC

**Step 2.3: Capture Refined Requirements**

The brainstorm skill will:
- Explore alternatives through Socratic questioning
- Validate assumptions
- Clarify ambiguities
- Produce refined design concept

**Fallback (if skill unavailable):**

Use native brainstorming prompt:

```
I need to refine this feature request through structured thinking:

REQUEST: [user input]

Analyze:
1. Core problem being solved
2. Alternative approaches (list 3+)
3. Key assumptions to validate
4. Potential edge cases or constraints
5. Simplified solution (KISS principle)

Provide refined requirements in bullet format.
```

Display summary:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 2 COMPLETE: Requirements Refined
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Alternatives explored
✓ Assumptions validated
✓ Design concept clarified
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### Phase 3: Research & Documentation Gathering

**Step 3.1: Identify Research Needs**

Based on refined requirements, determine what needs research:
- External APIs or libraries
- Architectural patterns
- Similar implementations in codebase
- Technical constraints or dependencies

**Step 3.2: Context7 MCP Integration**

If library/API documentation is needed:

```
# Primary attempt: Context7 MCP
mcp__context7__resolve-library-id for relevant libraries
mcp__context7__get-library-docs with resolved IDs

# Fallback if MCP unavailable (connection error, protocol error):
# 1. Retry once
# 2. If retry fails, fall back to:
#    - WebSearch for official documentation
#    - Read existing code examples in codebase
#    - Community-vetted code snippets
```

**Step 3.3: Parallel Agent Dispatch (if needed)**

For complex research across multiple domains, dispatch parallel agents:

```
Task tool with multiple concurrent calls:
- Agent 1: Explore codebase for similar patterns
- Agent 2: Research architectural approach
- Agent 3: Investigate dependencies/constraints

Use subagent_type: "Explore" for codebase investigation
Use model: "haiku" to optimize token usage
```

**Step 3.4: Consolidate Research Findings**

Gather findings into structured summary (save to memory, show brief on screen):

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 3 COMPLETE: Research Gathered
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ [N] libraries documented
✓ [N] codebase patterns identified
✓ [N] constraints validated
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### Phase 4: Plan Generation with AA-MA Standard

**Step 4.1: Invoke Write-Plan Skill**

```
Skill: superpowers:writing-plans
```

**Step 4.2: Provide Complete Context**

Pass to skill:
- Refined requirements from Phase 2
- Research findings from Phase 3
- AA-MA Planning Standard requirements (from CLAUDE.md)

Ensure plan includes ALL 11 required elements:
1. Executive summary (≤3 lines)
2. Ordered stepwise implementation plan
3. Milestones with measurable goals
4. Acceptance criteria for each step
5. Required artefacts for each step
6. Tests to validate each milestone
7. Rollback strategy for risky steps
8. Dependencies and assumptions
9. Effort estimate + Complexity (0-100%) per step
10. Risks (top 3) and mitigations per milestone
11. Next action (what to do first)

**Step 4.3: Validate Plan Completeness**

Check generated plan against AA-MA standard:
- [ ] Contains all 11 required elements
- [ ] Steps have clear acceptance criteria
- [ ] Complexity ≥80% steps are flagged
- [ ] Rollback strategy defined for risky changes
- [ ] Next action is concrete and actionable

**Fallback (if skill unavailable):**

Use native planning prompt following the AA-MA template from CLAUDE.md:

```
You MUST produce a thorough implementation plan following AA-MA Planning Standard.

CONTEXT:
- Feature: [refined requirements]
- Research: [findings summary]
- Constraints: [known limitations]

Provide:
1. Executive summary (≤3 lines)
2. Ordered stepwise implementation plan
3. Milestones with dates/durations
4. Acceptance criteria for each step
5. Required artefacts
6. Tests to validate
7. Rollback strategy
8. Dependencies and assumptions
9. Effort (hours/days) + Complexity (0-100%) per step
10. Risks (top 3) + mitigations
11. ONE Next action + which AA-MA file(s) to update

Format in Markdown for direct insertion into [task]-plan.md
```

Display summary:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 4 COMPLETE: Plan Generated
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ [N] implementation steps
✓ [N] milestones defined
✓ All acceptance criteria clear
✓ Rollback strategies included
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### Phase 4.2: Optional Plan Reviews (gstack integration)

After plan generation, optionally invoke multi-perspective review skills to challenge the plan before verification.

**Step 4.2.1: Prompt for Review Perspectives**

Use `AskUserQuestion` to ask:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PLAN GENERATED — REVIEW PERSPECTIVES?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Which review perspectives before verification?
  [C] CEO Review — challenge scope, find the 10-star product
  [E] Eng Review — architecture, data flow, test matrix
  [D] Design Review — rate design dimensions 0-10 (frontend only)
  [A] All applicable
  [S] Skip all — proceed to verification
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Recommendations:
  • Eng Review: recommended for Complexity >= 50%
  • CEO Review: recommended for new products/major pivots
  • Design Review: auto-skip when no frontend files detected
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Step 4.2.2: Execute Selected Reviews**

Run selected reviews in order: CEO (scope) → Eng (architecture) → Design (if frontend).

**CEO Review** (`Skill(plan-ceo-review)`):
- Challenges premises and scope
- 4 modes: expand, selective expand, hold, reduce
- Read-only — does not modify plan files
- Feed findings into Phase 4.5 verification context

**Eng Review** (`Skill(plan-eng-review)`):
- Architecture, data flow, edge cases, test matrix
- Interactive — may write ARCHITECTURE.md or update plan
- Feed architecture findings into Phase 4.5 verification context

**Design Review** (`Skill(plan-design-review)`):
- Only offered when frontend files detected (`.html`, `.css`, `.tsx`, `.jsx`, `.svelte`, Streamlit)
- Rates design dimensions 0-10
- May suggest plan edits for UX concerns
- Auto-skipped for backend-only/data projects

**Step 4.2.3: Capture Review Metadata**

Record which reviews ran in plan metadata for `/verify-plan` to reference later:

```
## Plan Review History
- CEO Review: [ran/skipped] — [key finding or "N/A"]
- Eng Review: [ran/skipped] — [key finding or "N/A"]
- Design Review: [ran/skipped/auto-skipped (no frontend)] — [key finding or "N/A"]
```

Display summary:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
REVIEWS COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ [N] reviews executed
✓ Findings fed into verification context
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### Phase 4.5: Adversarial Verification

**Step 4.5.1: Prompt for Verification Mode**

Use `AskUserQuestion` to ask:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PLAN GENERATED — VERIFY?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Run adversarial verification before creating artifacts?
  [A] Automated — CRITICALs block artifact creation
  [I] Interactive — All findings report-only
  [S] Skip — Proceed directly to artifact creation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**Step 4.5.2: Run Verification (if not skipped)**

Invoke the plan-verification skill:

```
Skill: plan-verification
```

Pass to the skill:
- Generated plan text from Phase 4
- Project root (pwd)
- User-selected mode (A/I/S)

The skill runs 6 verification angles in two waves:
- Wave 1 (parallel): Ground-truth audit, Assumption challenge, Impact analysis, Criteria falsifiability
- Wave 2 (sequential): Fresh-agent simulation, Specialist domain audit

**Step 4.5.3: Handle Verification Results**

- **PASS:** Proceed to Phase 5
- **PASS WITH WARNINGS:** Display warnings summary, proceed to Phase 5
- **FAIL (automated mode only):** Revise plan to address CRITICALs, re-verify (max 2 loops)
- **SKIPPED:** Proceed to Phase 5 immediately

If revision loop exhausts 2 attempts, present findings to user and ask how to proceed.

**Step 4.5.4: Display Summary**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 4.5 COMPLETE: Verification
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Mode: [Automated | Interactive | Skipped]
CRITICAL: [N] | WARNING: [N] | INFO: [N]
Result: [PASS | FAIL | PASS WITH WARNINGS | SKIPPED]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### Phase 5: AA-MA Artifact Creation

**Step 5.1: Create Task Directory Structure**

```bash
# Determine task name (sanitize for filesystem)
TASK_NAME="[user-provided-name-in-kebab-case]"
TASK_DIR=".claude/dev/active/${TASK_NAME}"

# Create directory and files
mkdir -p "${TASK_DIR}"
cd "${TASK_DIR}"

# Create all 5 AA-MA files
touch "${TASK_NAME}-plan.md"
touch "${TASK_NAME}-reference.md"
touch "${TASK_NAME}-context-log.md"
touch "${TASK_NAME}-tasks.md"
touch "${TASK_NAME}-provenance.log"
touch "${TASK_NAME}-verification.md"
```

**Step 5.2: Populate [task]-plan.md**

Write the generated plan from Phase 4:

```markdown
# [task-name] Plan

**Objective:** [1-line goal]
**Owner:** [from git config or "AI + User"]
**Created:** [current date]
**Last Updated:** [current date]

## Executive Summary
[3-line overview from plan]

## Implementation Steps
[Full plan content with all 11 elements]

## Next Action
[Specific first step from plan]
```

**Step 5.3: Extract and Populate [task]-reference.md**

Parse the plan for immutable facts and write to reference:

```markdown
# [task-name] Reference

## Immutable Facts and Constants

[Extract from plan:]
- API endpoints
- File paths
- Configuration values
- Library versions
- Database schemas
- Model paths

_Last Updated: [date]_
```

**Index-enhanced (when PROJECT_INDEX.json exists):**
Supplement the reference with structural facts from the index:
- Entry points and key symbols from `_meta.symbol_importance` (top 10)
- File→dependency mappings from `deps` for files in scope
- Directory purposes from `dir_purposes` for relevant directories
- These provide implementing agents with architectural context they would otherwise need to discover via Grep

**Step 5.4: Initialize [task]-context-log.md**

Create initial log entry:

```markdown
# [task-name] Context Log

## [current-date] Initial Context

**Feature Request:** [original user input]

**Key Decisions:**
- [Decision 1 from brainstorm phase]
- [Decision 2 from research phase]

**Research Findings:**
- [Summary from Phase 3]

**Remaining Questions:**
- [Any unresolved items]

_This log will be updated via context compaction as the task progresses._
```

**Step 5.5: Create HTP Structure in [task]-tasks.md**

Convert plan steps into Hierarchical Task Planning format:

```markdown
# [task-name] Tasks (HTP)

## Milestone 1: [title]
- Status: PENDING
- Dependencies: None
- Complexity: [%]
- Acceptance Criteria: [from plan]

### Step 1.1: [action]
- Status: PENDING
- Result Log: [placeholder]

### Step 1.2: [action]
- Status: PENDING
- Result Log: [placeholder]

## Milestone 2: [title]
- Status: PENDING
- Dependencies: Milestone 1
- Complexity: [%]
- Acceptance Criteria: [from plan]

[Continue for all milestones/steps from plan]
```

**Step 5.6: Initialize [task]-provenance.log**

Create initial log entry:

```text
# [task-name] Provenance Log

[current-timestamp] Task initialized via /aa-ma-plan
[current-timestamp] Commit: [git hash] — Phase: Planning
[current-timestamp] AA-MA artifacts created
```

**Step 5.7: Validate Artifact Creation**

```bash
# Verify all files exist and have content
ls -lh "${TASK_DIR}/"
wc -l "${TASK_DIR}/"*.md "${TASK_DIR}/"*.log
```

Check:
- [ ] All 6 files present
- [ ] plan.md has complete plan
- [ ] reference.md has extracted facts
- [ ] context-log.md has initial context
- [ ] tasks.md has HTP structure
- [ ] provenance.log has timestamps
- [ ] verification.md present (if verification was run in Phase 4.5)

**Step 5.8: Display Final Summary**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 5 COMPLETE: AA-MA Artifacts Created
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Task Directory: .claude/dev/active/[task-name]/

Files created:
  ✓ [task]-plan.md         → Complete implementation plan
  ✓ [task]-reference.md    → Immutable facts/constants
  ✓ [task]-context-log.md  → Decision history
  ✓ [task]-tasks.md        → HTP roadmap
  ✓ [task]-provenance.log  → Execution telemetry
  ✓ [task]-verification.md  → Plan verification audit trail (if run)

Next Action: [specific step from plan]

To begin implementation, load context with:
  <REFERENCE>
  (Contents of [task]-reference.md)
  </REFERENCE>

  <TASKS>
  (Contents of [task]-tasks.md)
  </TASKS>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
/aa-ma-plan workflow complete — Ready to implement
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Error Handling & Fallbacks

**Superpowers skills unavailable:**
- Fall back to native brainstorming/planning prompts
- Display warning: "Using fallback planning (superpowers unavailable)"

**Context7 MCP unavailable:**
- Retry once
- Fall back to WebSearch + native documentation tools
- Log fallback in provenance: "Context7 MCP unavailable, used fallback"

**Task directory collision:**
- Detect existing `.claude/dev/active/[task-name]/`
- Prompt user: "Task directory exists. Options: (1) Append timestamp, (2) Choose new name, (3) Overwrite"

**Missing git context:**
- Proceed without git hash in provenance
- Note in context-log: "Non-git project"

**Plan validation fails:**
- Re-generate plan with explicit AA-MA checklist
- If second attempt fails, save partial plan and notify user

---

## Token Optimization Strategy

**Screen Output (Concise):**
- Phase completion summaries only
- Checkmarks for completed items
- Brief statistics (N steps, N milestones)
- Final next action

**File Output (Verbose):**
- Full research findings → context-log.md
- Complete plan details → plan.md
- All extracted facts → reference.md
- Detailed step breakdown → tasks.md

**Agent Efficiency:**
- Use Haiku model for research agents (parallel Phase 3)
- Stream findings directly to files, not to screen
- Compress redundant tool outputs in memory

---

## Usage Examples

**Example 1: Context-aware (selected text)**

User selects this text:
```
Add user authentication with OAuth2 and JWT tokens
```

Then runs: `/aa-ma-plan`

Command automatically:
1. Uses selected text as feature request
2. Asks clarifying questions (task name, constraints)
3. Runs full 5-phase workflow
4. Creates `.claude/dev/active/user-auth-oauth/` with all artifacts

**Example 2: Interactive prompt**

User runs: `/aa-ma-plan`

Command prompts:
- "Describe the feature or change you want to plan:"
- [User types: "Refactor database layer to use repository pattern"]
- "What should we name this task?"
- [User types: "db-repository-refactor"]
- Continues with 5-phase workflow

**Example 3: Complex research needs**

User: `/aa-ma-plan` → "Implement GraphQL API with subscriptions"

Command:
1. Gathers context
2. Brainstorms approach
3. **Phase 3:** Dispatches 3 parallel agents:
   - Agent 1: Explore existing API patterns in codebase
   - Agent 2: Research GraphQL best practices (Context7 MCP)
   - Agent 3: Investigate subscription implementation options
4. Consolidates findings
5. Generates comprehensive plan
6. Creates AA-MA artifacts with all research embedded

---

## Integration with Other Commands

**After /aa-ma-plan completes:**
- Use `/commit-and-push` to commit the generated AA-MA files
- Use `/git-status-smart` to review planning artifacts before commit

**During implementation:**
- Load context from AA-MA files using delimited injection (see CLAUDE.md)
- Update tasks.md as steps complete
- Use context compaction when history grows large

**Before merging:**
- Use `/release-prep` if plan represents a versioned release

---

## Time Estimates

- **Simple task (3-5 steps):** 2-3 minutes
- **Medium task (6-10 steps):** 4-6 minutes
- **Complex task (10+ steps, multi-agent research):** 8-12 minutes

Actual time depends on:
- Research complexity (Context7 MCP lookups, parallel agents)
- User response time for clarifying questions
- Plan validation iterations

---

## Troubleshooting

**"Superpowers skill not found"**
- Verify skills installed: Check Skill tool output
- Fallback is automatic, but plan quality may be reduced
- Consider installing superpowers plugin

**"Context7 MCP connection failed"**
- Normal fallback behavior activated
- Check MCP server status if repeated failures
- Fallback uses WebSearch and native tools

**"Plan validation failed"**
- Review generated plan manually
- May be missing required AA-MA elements
- Command will retry once automatically

**"Task directory exists"**
- Choose different task name or append timestamp
- Or manually delete old task: `rm -rf .claude/dev/active/[old-task]/`

---

## Design Principles Applied

- **KISS:** Simple 5-phase (+4.5 verification) linear workflow, clear instructions
- **DRY:** Reuses superpowers skills, Context7 MCP, established patterns
- **SOC:** Each phase has single responsibility (gather/think/research/plan/create)
- **SOLID:** Open for extension (add new research sources), closed for modification (core workflow stable)

---

**Command created following AA-MA methodology and CLAUDE.md standards.**
