# Phase 5: AA-MA Artifact Creation

## Objectives
- Create `.claude/dev/active/[task-name]/` directory structure
- Generate all 5 AA-MA files with proper content
- Extract immutable facts to reference.md
- Convert plan to HTP (Hierarchical Task Planning) structure
- Initialize provenance log with timestamps
- Validate cross-file consistency

## Skill Integration

**Primary skills:**
- `agent-teams` — Spawn `aa-ma-scribe` + `aa-ma-validator` for defense-in-depth artifact creation
- `defense-in-depth` — Cross-file consistency validation (additional layer)

## Scribe + Validator Spawn Protocol

Phase 5 uses a two-agent pattern for artifact creation reliability:

### Agent 1: aa-ma-scribe

**Purpose:** Write all 5 AA-MA files from the approved plan.

**Spawn:**
```
Task tool:
  subagent_type: "aa-ma-scribe"  (uses ~/.claude/agents/aa-ma-scribe.md)
  name: "scribe"
  prompt: |
    Create AA-MA artifacts for task: [task-name]
    Task directory: .claude/dev/active/[task-name]/

    PLAN CONTENT:
    [Full plan from Phase 4]

    PHASE 1-3 CONTEXT:
    [Key decisions, research findings, brainstorm output]

    Create all 5 files following your templates.
```

**Tools:** Read, Write, Glob, Grep (NO Bash)
**Output:** 5 AA-MA files created with content

### Agent 2: aa-ma-validator

**Purpose:** Independently verify artifacts are complete and consistent.

**Spawn:** After scribe completes.
```
Task tool:
  subagent_type: "aa-ma-validator"  (uses ~/.claude/agents/aa-ma-validator.md)
  name: "validator"
  prompt: |
    Validate AA-MA artifacts for task: [task-name]
    Task directory: .claude/dev/active/[task-name]/
    Validation context: post-creation

    Run all 5 validation dimensions and report findings.
```

**Tools:** Read, Glob, Grep (NO Write, NO Bash)
**Output:** Structured validation report with PASS/WARN/FAIL verdicts

### Remediation Loop

```
If validator verdict = FAIL:
  1. Parse failure details from validator report
  2. Re-spawn scribe with specific fix instructions
  3. Re-spawn validator to verify fixes
  4. Maximum 2 remediation cycles
  5. After 2 failures → escalate to user
```

### Fallback (Agent Spawning Fails)

If agent spawning is unavailable, write artifacts directly using the manual procedure below.

## AA-MA File Taxonomy

| File | Purpose | Priority | Update Frequency |
|------|---------|----------|------------------|
| `[task]-plan.md` | Core strategy, rationale, high-level constraints | Medium | Rarely (only if plan changes) |
| `[task]-reference.md` | **Strict, immutable facts** (APIs, paths, constants) | **HIGH** | Continuously (as facts discovered) |
| `[task]-context-log.md` | Summarized decision history, unresolved bugs | Medium | Via compaction (every N commits) |
| `[task]-tasks.md` | HTP roadmap, dependencies, state tracking | **HIGH** | Continuously (as tasks complete) |
| `[task]-provenance.log` | Machine-readable execution history, Git activity | Low | Automatically (Git hooks) |

## Step-by-Step Procedure

### 5.1 Create Task Directory Structure

```bash
# Sanitize task name (kebab-case, no special chars)
TASK_NAME="[user-provided-name-in-kebab-case]"
TASK_DIR=".claude/dev/active/${TASK_NAME}"

# Check for collisions
if [[ -d "${TASK_DIR}" ]]; then
  echo "⚠️  Task directory exists: ${TASK_DIR}"
  # Prompt user: (1) Append timestamp, (2) Choose new name, (3) Overwrite
fi

# Create directory and files
mkdir -p "${TASK_DIR}"
cd "${TASK_DIR}"

# Create all 5 AA-MA files
touch "${TASK_NAME}-plan.md"
touch "${TASK_NAME}-reference.md"
touch "${TASK_NAME}-context-log.md"
touch "${TASK_NAME}-tasks.md"
touch "${TASK_NAME}-provenance.log"
```

### 5.2 Populate [task]-plan.md

Write the complete generated plan from Phase 4:

```markdown
# [task-name] Plan

**Objective:** [1-line goal from Phase 1]
**Owner:** [from git config or "AI-Assisted"]
**Created:** [YYYY-MM-DD]
**Last Updated:** [YYYY-MM-DD]

## Executive Summary

[≤3 lines from plan]

## Implementation Steps

[Full plan content with all 11 AA-MA elements]

## Next Action

[Specific first step from plan]
```

### 5.3 Extract and Populate [task]-reference.md

**Critical:** Parse the plan for immutable facts and extract to reference.md

**What qualifies as "immutable fact":**
- API endpoints (exact URLs)
- File paths (absolute or relative)
- Configuration values (keys, connection strings - not secrets!)
- Library versions (pinned dependencies)
- Database schemas (table structures, column types)
- Model paths (trained model locations)
- Constants (magic numbers, fixed thresholds)

**Template:**
```markdown
# [task-name] Reference

## Immutable Facts and Constants

_These are non-negotiable facts extracted from the plan and research._

### API Endpoints
- `POST /api/auth/login` - JWT authentication endpoint

### File Paths
- `src/auth/jwt.py` - JWT token handling (to be created)

### Configuration
- `JWT_SECRET_KEY` - Must be set in `.env`

### Dependencies
- `PyJWT==2.8.0` - JWT encoding/decoding

_Last Updated: [YYYY-MM-DD HH:MM]_
```

### 5.4 Initialize [task]-context-log.md

Create initial log entry capturing Phase 1-3 context:

```markdown
# [task-name] Context Log

_This log captures architectural decisions, trade-offs, and unresolved issues._

## [YYYY-MM-DD] Initial Context

**Feature Request (Phase 1):**
[Original user input, verbatim]

**Key Decisions (Phase 2 Brainstorming):**
- **Decision:** [What was decided]
  - **Rationale:** [Why this approach chosen]
  - **Alternatives Considered:** [Other options and why rejected]
  - **Trade-offs:** [Pros and cons]

**Research Findings (Phase 3):**
- [Library/API documentation summary]
- [Codebase pattern analysis]

**Remaining Questions / Unresolved Issues:**
- [Question 1]: [Why unresolved]
```

### 5.5 Create HTP Structure in [task]-tasks.md

**Template:**
```markdown
# [task-name] Tasks (HTP)

_Hierarchical Task Planning roadmap with dependencies and state tracking._

## Milestone 1: [Title from plan]
- **Status:** PENDING
- **Dependencies:** None
- **Complexity:** [X%] [+ "⚠️ HIGH COMPLEXITY" if ≥80%]
- **Acceptance Criteria:**
  - [Criterion 1 from plan]
  - [Criterion 2 from plan]

### Step 1.1: [Action from plan]
- **Status:** PENDING
- **Result Log:** [Will be filled during execution]
```

**Status values:**
- `PENDING` - Not started yet
- `ACTIVE` - Currently being worked on
- `COMPLETE` - Finished and validated
- `BLOCKED` - Cannot proceed (unmet dependency or issue)

### 5.6 Initialize [task]-provenance.log

```text
# [task-name] Provenance Log

[YYYY-MM-DD HH:MM:SS] Task initialized via /aa-ma-plan command
[YYYY-MM-DD HH:MM:SS] Project: [/full/path/to/project]
[YYYY-MM-DD HH:MM:SS] Git commit: [hash] ← Planning baseline
[YYYY-MM-DD HH:MM:SS] Phase 1-5 complete
[YYYY-MM-DD HH:MM:SS] Status: READY FOR EXECUTION
```

### 5.7 Cross-File Consistency Validation

**Invoke `defense-in-depth` skill for validation:**

Verify:
- Facts in reference.md match plan.md
- Tasks in tasks.md align with plan milestones
- No contradictions between files
- All cross-references valid

### 5.8 Validate Artifact Creation

```bash
# Verify all files exist and have content
ls -lh "${TASK_DIR}/"
wc -l "${TASK_DIR}/"*.md "${TASK_DIR}/"*.log

# Check each file
for file in "${TASK_NAME}"-{plan,reference,context-log,tasks}.md "${TASK_NAME}-provenance.log"; do
  if [[ ! -f "${TASK_DIR}/${file}" ]]; then
    echo "❌ MISSING: ${file}"
    exit 1
  elif [[ ! -s "${TASK_DIR}/${file}" ]]; then
    echo "❌ EMPTY: ${file}"
    exit 1
  else
    echo "✅ VALID: ${file} ($(wc -l < "${TASK_DIR}/${file}") lines)"
  fi
done
```

### 5.9 Display Final Summary & Handoff

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 5 COMPLETE: AA-MA Artifacts Created
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ AA-MA PLAN WORKFLOW COMPLETE

Task Directory: .claude/dev/active/[task-name]/

📁 Files Created:
  ✓ [task]-plan.md         ([N] lines)
  ✓ [task]-reference.md    ([N] lines)
  ✓ [task]-context-log.md  ([N] lines)
  ✓ [task]-tasks.md        ([N] lines)
  ✓ [task]-provenance.log  ([N] lines)

📊 Plan Summary:
  • [N] milestones
  • [N] implementation steps
  • [N] high-complexity tasks (≥80%)

🎯 Next Action (from plan):
[Specific first step]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
READY TO IMPLEMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

To begin execution, use the aa-ma-execution skill.
RECOMMENDED: Start with milestone mode (/execute-aa-ma-milestone)
```

## Phase 5 Checklist

- [ ] Task directory created at `.claude/dev/active/[task-name]/`
- [ ] All 5 AA-MA files created and non-empty
- [ ] plan.md populated with complete plan (11 elements)
- [ ] reference.md populated with extracted immutable facts
- [ ] context-log.md initialized with Phase 1-3 context
- [ ] tasks.md converted to HTP structure (milestones + steps)
- [ ] provenance.log initialized with timestamps
- [ ] Cross-file consistency validated (defense-in-depth)
- [ ] Validation script passed (all files valid)
- [ ] Final summary displayed with handoff to execution
- [ ] Next action clearly stated

## Enforcement Gate: Phase 4 → Phase 5

<EXTREMELY-IMPORTANT>
Phase 5 is MANDATORY after Gate 3 passes. Proceeding to execution without artifacts is the #1 cause of "artifact amnesia."

The enforcement gate ensures:
1. Phase 5 CANNOT be skipped — it runs automatically after Gate 3
2. Auto-recovery exists at execution time — if artifacts are still missing, execute commands will trigger Phase 5 with scribe+validator
3. The enforcement is documented in SKILL.md, PHASE_5_ARTIFACT_CREATION.md, and VALIDATION_GATES.md

See `references/SYNC_PROTOCOL.md` for how artifacts stay synchronized with TaskList during team-based execution.
</EXTREMELY-IMPORTANT>

## Validation Gate 4: Cross-File Consistency

**MUST PASS before completing aa-ma-plan:**

| Criterion | Requirement | Check |
|-----------|-------------|-------|
| Fact Consistency | All facts in reference.md appear in plan.md | [ ] |
| Task Alignment | All tasks.md milestones match plan.md milestones | [ ] |
| No Contradictions | No conflicting information between files | [ ] |
| Complete Coverage | All plan elements represented across files | [ ] |
| Valid References | All cross-references between files are valid | [ ] |

**On Failure:**
1. Identify inconsistencies and fix
2. If fails twice, invoke `debugging-strategies` skill
3. Manual review required before proceeding
