# Load context and build the todo list — context-injection order, the loaded-context checks, the HTP-to-TodoWrite mapping and the quality triggers applied during execution.

## Contents

- [2. Priority Context Injection](#2-priority-context-injection)
- [3. Validate Loaded Context](#3-validate-loaded-context)
- [4. Parse HTP & Create TodoWrite Todos](#4-parse-htp--create-todowrite-todos)
- [4.5 Quality Standards (Actionable Triggers)](#45-quality-standards-actionable-triggers)
  - [Pre-Execution Check (First Milestone Only)](#pre-execution-check-first-milestone-only)

## 2. Priority Context Injection

**REQUIRED - Auto-inject with XML delimiters:**

```xml
<REFERENCE>
{Read contents of [task-name]-reference.md}
# Immutable facts and constants. Treat as non-negotiable.
# Examples: API endpoints, file paths, configuration values, core function signatures
</REFERENCE>

<TASKS>
{Read contents of [task-name]-tasks.md}
# HTP (Hierarchical Task Planning) roadmap. Defines your required next action.
# Current execution scope: MILESTONE
# Status values: PENDING | ACTIVE | COMPLETE | BLOCKED
</TASKS>
```

**CONDITIONAL - Load if tokens allow (in priority order)**:

```xml
<CONTEXT_LOG>
{Read contents of [task-name]-context-log.md}
# Summarized architectural decisions and unresolved bugs
</CONTEXT_LOG>

<PLAN>
{Read contents of [task-name]-plan.md}
# Original strategy and rationale
</PLAN>

<PROVENANCE>
{Read contents of [task-name]-provenance.log}
# Execution telemetry and git history
</PROVENANCE>
```

## 3. Validate Loaded Context

**Required checks**:
- ✅ REFERENCE contains key constants (APIs, paths, configs)
- ✅ TASKS has clear HTP structure with Status fields
- ✅ At least one milestone has `Status: PENDING` or `Status: ACTIVE`
- ✅ Milestones have explicit Acceptance Criteria defined

**If validation fails**:
```
ERROR: [Specific issue]
- Missing AA-MA files → "AA-MA files not found. Run /aa-ma-plan first."
- Malformed HTP → "tasks.md lacks proper HTP format. Review AA-MA Planning Standard."
- No pending milestones → "All milestones complete. Check tasks.md status."
- Missing acceptance criteria → "Milestone lacks acceptance criteria. Update tasks.md."
```

## 4. Parse HTP & Create TodoWrite Todos

**Parse tasks.md for HTP structure**:
- `## headers` = Milestones (e.g., "## Step 1: Setup Infrastructure")
- `### headers` = Sub-tasks (e.g., "### Sub-step: Install dependencies")
- Extract `Status:`, `Dependencies:`, `Complexity:`, `Acceptance Criteria:` fields

**Identify target milestone**:
- Find first milestone with `Status: PENDING` or `Status: ACTIVE`
- This is your target milestone for this execution

**Create TodoWrite todos for**:
- The target milestone (## level)
- All its sub-tasks (### level)

**Todo format**:
```json
{
  "content": "[Milestone/Task title from HTP]",
  "status": "pending|in_progress|completed",
  "activeForm": "[Present continuous form]"
}
```

**Status mapping**:
- HTP `PENDING` → TodoWrite `pending`
- HTP `ACTIVE` → TodoWrite `in_progress`
- HTP `COMPLETE` → TodoWrite `completed`
- HTP `BLOCKED` → TodoWrite `pending` (prefix content with "BLOCKED: ")

**Complexity flagging**:
- If milestone or any sub-task has `Complexity: ≥ 80%` → Prefix content with "[High Complexity] "

## 4.5 Quality Standards (Actionable Triggers)

These principles apply DURING execution. Each has a trigger condition and skip condition.

- **KISS:** If implementation exceeds 200 lines for a single function or method, decompose before proceeding. Skip for generated code or data tables.
- **DRY:** Before writing a new utility function, grep the codebase for existing implementations. If a match exists, reuse it. Section 6.6 (Post-Milestone Simplification Review) catches misses post-hoc.
- **SOLID:** If a class has >5 public methods, evaluate single-responsibility. If a module mixes data access + business logic + presentation, separate. Skip for scripts and one-off tools.
- **SOC:** If a file grows beyond one clear responsibility, split. If a function handles both data transformation and side effects, separate.
- **TDD:** If this milestone produces code, invoke `superpowers:test-driven-development`. Let the skill decide test strategy. Skip for docs-only, config-only, or infrastructure-only milestones.
- **12-Factor:** If the task involves service deployment, API servers, or containerized applications, reference 12-Factor principles for config (env vars not files), statelessness, and port binding. For ALL tasks with `.env` files, verify env-var-drift compliance (see `rules/env-var-drift.md`).
- **Context7 MCP:** Use for library docs and code generation. Retry once on failure, then fall back to WebSearch + official docs.
- **WebSearch:** Fallback when Context7 fails. Also use proactively for unfamiliar APIs, recent library changes, or deployment patterns.

### Pre-Execution Check (First Milestone Only)

If this is the **first milestone** being executed and it touches 3+ files or unfamiliar code, invoke `Skill(system-mapping)` for the 5-point pre-flight check before starting execution. Skip for subsequent milestones unless they shift to a completely different subsystem.
