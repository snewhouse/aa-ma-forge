# Implementation Team Template

Ready-to-use configuration for spawning an implementation team with architect-led scope partitioning and quality gates.

---

## Configuration

| Setting | Value |
|---------|-------|
| Team name | `impl-{feature}` |
| Team type | IMPLEMENTATION |
| Size | 1 architect + 1-3 implementers + 1 reviewer |
| Debate mode | No |
| Quality gates | Design Review → Code Review → Test Verification → Consistency Check |

---

## Roles

### Architect
- **Name**: `architect`
- **Agent type**: `Plan`
- **Purpose**: Analyze codebase, define non-overlapping scopes, recommend patterns
- **Spawn prompt**:
```
You are the Architect on team "impl-{feature}".

Feature to implement: {feature_description}

Instructions:
1. Read your assigned tasks via TaskGet
2. Mark tasks in_progress via TaskUpdate when starting
3. Analyse the relevant codebase:
   - Read existing code in {relevant_directories}
   - Identify patterns and conventions used
   - Map dependencies between modules
4. Produce a design that includes:
   - NON-OVERLAPPING file scopes for each implementer
   - Recommended patterns and approaches
   - Task dependencies (what must be built first)
   - Potential risks and mitigations
5. SendMessage your design to the team lead
6. Mark tasks completed via TaskUpdate

CRITICAL: File scopes MUST NOT overlap. Each implementer should have
a clear, exclusive set of files they are responsible for.

Output as:
## Design: {feature}
### Current State Analysis
{what exists, relevant patterns}
### Scope Assignments
- Implementer 1 ({name}): {files/dirs} — {what to build}
- Implementer 2 ({name}): {files/dirs} — {what to build}
### Task Order
{which tasks depend on which}
### Patterns to Follow
{existing patterns to maintain consistency}
### Risks
{potential issues}
```

### Implementer 1
- **Name**: `impl-1`
- **Agent type**: `general-purpose`
- **Scope**: {assigned by architect}
- **Plan mode**: {adaptive — see SKILL.md rules}
- **Spawn prompt**:
```
You are Implementer 1 on team "impl-{feature}".

Your assignment: {specific_task_description}
Your file scope: {list_of_files_or_directories}

IMPORTANT: ONLY modify files within your assigned scope:
{explicit_file_list}

If you need changes outside your scope, SendMessage the team lead.

Instructions:
1. Read your assigned tasks via TaskGet
2. Mark tasks in_progress via TaskUpdate when starting
3. Read the relevant existing code before making changes
4. Implement the required changes following existing patterns
5. Write tests for your changes
6. Run tests: {test_command}
7. Commit with descriptive message
8. SendMessage your summary to the team lead
9. Mark tasks completed via TaskUpdate
10. Check TaskList for additional work

Output as:
## Implementation: {task}
### Changes
- {file}: {what changed and why}
### Tests
- {test results}
### Commit
- {hash}: {message}
### Notes
{blockers, concerns, follow-up}
```

### Implementer 2
- **Name**: `impl-2`
- **Agent type**: `general-purpose`
- **Scope**: {assigned by architect — different from impl-1}
- **Spawn prompt**: (Same structure as Implementer 1 with different scope)

### Implementer 3 (Optional)
- **Name**: `impl-3`
- **Agent type**: `general-purpose`
- **Scope**: {assigned by architect — different from impl-1 and impl-2}
- **Spawn prompt**: (Same structure with different scope)

### Reviewer
- **Name**: `reviewer`
- **Agent type**: `superpowers:code-reviewer`
- **Purpose**: Review each implementer's work for quality, security, correctness
- **Spawn prompt**:
```
You are the Reviewer on team "impl-{feature}".

Your job: Review each implementation task after completion.
You will receive review assignments via TaskGet.

Instructions:
1. Read your assigned tasks via TaskGet
2. Mark tasks in_progress via TaskUpdate when starting
3. For each review task:
   - Read the implemented code changes
   - Check for correctness, security, patterns
   - Run tests if applicable
4. Report findings with severity:
   - Critical: Must fix before proceeding
   - Important: Should fix before merge
   - Minor: Nice to have
5. SendMessage your review to the team lead
6. Mark tasks completed via TaskUpdate
7. Check TaskList for next review

Output as:
## Review: {what was reviewed}
### Critical Issues
{list — blocks progress}
### Important Issues
{list — should fix}
### Minor Issues
{list}
### Strengths
{what's done well}
### Assessment: APPROVE | REQUEST_CHANGES
```

---

## Tasks Setup

```
Task 1: "Design {feature} — scope and pattern analysis" → architect
  No dependencies

Task 2: "Implement {component_A}" → impl-1
  addBlockedBy: [Task 1]

Task 3: "Implement {component_B}" → impl-2
  addBlockedBy: [Task 1]

Task 4: "Implement {component_C}" → impl-3 [optional]
  addBlockedBy: [Task 1]

Task 5: "Review {component_A}" → reviewer
  addBlockedBy: [Task 2]

Task 6: "Review {component_B}" → reviewer
  addBlockedBy: [Task 3]

Task 7: "Review {component_C}" → reviewer [optional]
  addBlockedBy: [Task 4]

Task 8: "Integration test — verify all components work together" → lead
  addBlockedBy: [Task 5, Task 6, Task 7]
```

### Dependency Flow
```
Architect Design ──┬──→ Implement A ──→ Review A ──┐
                   ├──→ Implement B ──→ Review B ──┼──→ Integration Test
                   └──→ Implement C ──→ Review C ──┘
```

Design blocks all implementation. Each review blocks on its implementation. Integration test blocks on all reviews.

---

## Scope Partitioning Guidelines

1. **Files, not features**: Assign specific files/directories, not abstract feature areas
2. **Explicit boundaries**: Each implementer gets a written list of files they own
3. **No shared files**: If two implementers need the same file, one does it and the other depends on it
4. **Interface contracts**: When implementers depend on each other's work, define the interface upfront
5. **Architect decides**: Scope assignments come from the architect's design review

### Example Scope Assignment
```
Feature: User dashboard

Implementer 1 (impl-1): Backend API
  Files: src/api/dashboard.py, src/api/schemas/dashboard.py, tests/api/test_dashboard.py
  Task: Create dashboard API endpoints

Implementer 2 (impl-2): Frontend Components
  Files: src/components/Dashboard/, src/hooks/useDashboard.ts, tests/components/Dashboard.test.tsx
  Task: Create dashboard UI components

Implementer 3 (impl-3): Data Layer
  Files: src/models/dashboard.py, src/repositories/dashboard.py, tests/models/test_dashboard.py
  Task: Create dashboard data models and repository
```

---

## Commit Strategy

- Each implementer commits their own scope independently
- Commit messages follow project conventions (Conventional Commits if configured)
- Reviewer does NOT commit (review-only role)
- Lead may do a final integration commit if needed
- If AA-MA active: all commits include AA-MA signature

---

## Expected Deliverable

After team completes:
```markdown
# Implementation Report: {feature}

## Summary
- Feature: {description}
- Team: 1 architect + {N} implementers + 1 reviewer
- Status: {COMPLETE|PARTIAL}

## Design
{architect's design summary}

## Implementation
{for each implementer:}
### {component}
- Files changed: {list}
- Tests: {pass/fail count}
- Commit: {hash}

## Review Results
- Critical issues: {count} (all resolved)
- Important issues: {count}
- Assessment: {APPROVED}

## Integration
- All tests passing: {yes/no}
- No conflicts: {yes/no}
```

---

## Usage

1. Replace all {placeholders} with feature-specific values
2. Adjust team size: 1 architect is always required, 1-3 implementers based on scope, 1 reviewer always required
3. Create team and tasks following the structure above
4. Execute following the 7-phase lifecycle in SKILL.md
