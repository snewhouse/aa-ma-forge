# /aa-ma-plan errors, examples and integration — error handling and fallbacks, token use, usage examples, related commands, time estimates and troubleshooting.

## Contents

- [Error Handling & Fallbacks](#error-handling--fallbacks)
- [Token Optimization Strategy](#token-optimization-strategy)
- [Usage Examples](#usage-examples)
- [Integration with Other Commands](#integration-with-other-commands)
- [Time Estimates](#time-estimates)
- [Troubleshooting](#troubleshooting)
- [Design Principles Applied](#design-principles-applied)

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
- Review the planning artifacts with `git status` / `git diff`, then commit them (Conventional Commits + the `[AA-MA Plan]` footer)

**During implementation:**
- Load context from AA-MA files using delimited injection (see CLAUDE.md)
- Update tasks.md as steps complete
- Use context compaction when history grows large

**Before merging:**
- Run the project's release process if the plan represents a versioned release

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
