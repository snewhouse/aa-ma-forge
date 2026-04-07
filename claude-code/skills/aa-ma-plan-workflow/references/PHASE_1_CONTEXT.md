# Phase 1: Context Gathering & Input Processing

## Objectives
- Understand user's feature request or problem
- Gather project context and current state
- Clarify ambiguities through questions
- Determine task name and scope

## Step-by-Step Procedure

### 1.1 Detect Input Method

Check for user context in this priority order:

1. **Selected text:** If user has selected code/text, use that as feature request
2. **Inline argument:** Accept natural language description provided with command
3. **Interactive prompt:** Use `AskUserQuestion` if no context provided

### 1.2 Gather Initial Project Context

```bash
# Check current project state
pwd
git rev-parse --short HEAD 2>/dev/null || echo "Not a git repo"
ls -la .claude/dev/active/ 2>/dev/null || echo "No active tasks"
```

**Capture:**
- Current working directory
- Git commit hash (if available)
- Existing AA-MA tasks (detect conflicts)
- Project type/language (from file scan)

### 1.3 Ask Clarifying Questions

Use `AskUserQuestion` to gather:

**Required:**
- **Task name:** For directory structure (kebab-case, e.g., "user-auth-oauth")
- **Primary objective:** 1-2 sentence goal statement
- **Known constraints:** Technical limitations, deadlines, dependencies

**Optional:**
- **Complexity estimate:** Simple/Medium/Complex (or 0-100%)
- **Priority:** High/Medium/Low
- **Success criteria:** What defines "done"?

**Example question structure:**
```
Question 1: What should we name this task? (will create .claude/dev/active/[name]/)
Header: Task Name
Options:
  - Use kebab-case format (e.g., "api-auth-refactor")
  - Keep it concise but descriptive
  - Avoid spaces or special characters

Question 2: What is the primary objective? (1-2 sentences)
Header: Objective
[Free text input via "Other" option]

Question 3: What is your estimated complexity?
Header: Complexity
Options:
  - Simple (0-30%): Few dependencies, straightforward implementation
  - Medium (30-60%): Some unknowns, moderate complexity
  - Complex (60-100%): Many dependencies, architectural changes, high uncertainty
```

### 1.4 Display Context Summary

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 1 COMPLETE: Context Gathered
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Task: [name]
Objective: [summary]
Complexity: [estimate]
Project: [path]
Commit: [hash or "N/A"]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Phase 1 Checklist

- [ ] Input method identified (selected text / inline / interactive)
- [ ] Task name validated (kebab-case, no conflicts)
- [ ] Objective clearly stated (1-2 sentences)
- [ ] Project context gathered (path, git hash, language)
- [ ] Constraints and assumptions documented
- [ ] Complexity estimate recorded
