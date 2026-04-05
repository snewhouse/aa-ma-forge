---
name: execute-aa-ma-milestone
description: Execute complete milestone from AA-MA plan with strict validation and auto-commit (RECOMMENDED DEFAULT)
---

# AA-MA Milestone Execution (Recommended Default)

You are executing a **complete milestone** from an AA-MA (Advanced Agentic Memory Architecture) tracked plan.

**Scope**: One milestone (## header) with all sub-tasks
**Validation**: Hybrid (guidance within, strict at boundary)
**Git**: Auto-commit + provenance logging at milestone completion

---

## 1. Locate Active Task & Pre-Execution Validation

Check `.claude/dev/active/` for the most recent task directory:

```bash
ls -lt .claude/dev/active/ | head -5
```

**Expected structure**: `.claude/dev/active/[task-name]/`

### Tier 1: Existence Check (Fast)

Verify all 5 required AA-MA files exist and are non-empty:

```bash
TASK_DIR=".claude/dev/active/[task-name]"
TASK_NAME="[task-name]"
MISSING=0
for file in "${TASK_NAME}-plan.md" "${TASK_NAME}-reference.md" "${TASK_NAME}-context-log.md" "${TASK_NAME}-tasks.md" "${TASK_NAME}-provenance.log"; do
  if [[ ! -s "${TASK_DIR}/${file}" ]]; then
    echo "❌ MISSING or EMPTY: ${file}"
    MISSING=$((MISSING + 1))
  fi
done
echo "Tier 1 result: ${MISSING} files missing"
```

**If Tier 1 fails (any files missing or empty):**

```
⚠️ AA-MA ARTIFACTS INCOMPLETE — AUTO-RECOVERY TRIGGERED

Missing/empty files detected: [list]

Auto-recovery: Triggering Phase 5 artifact creation with scribe+validator agents...
```

1. Notify user that auto-recovery is starting
2. Spawn `aa-ma-scribe` agent to create missing files from available plan context
3. Spawn `aa-ma-validator` agent to verify created files (5-dimension check)
4. If validator reports PASS/WARN → continue execution
5. If validator reports FAIL → retry once (re-scribe → re-validate)
6. If still FAIL after retry → HALT and alert user: "Auto-recovery failed. Run `/ultraplan` to recreate artifacts."
7. If agent spawning unavailable → fallback: create files directly inline, then continue

### Tier 2: Content Validation (Thorough)

After Tier 1 passes, spawn the `aa-ma-validator` agent for deep content checks:

```
Spawn aa-ma-validator with:
  subagent_type: "aa-ma-validator"
  prompt: Validate artifacts at [task-dir] in pre-execution context
  Tools: Read, Glob, Grep (NO Write, NO Bash)
```

**Validator checks 5 dimensions:**
1. **Existence** — all 5 files present and non-empty
2. **Plan completeness** — plan.md has the 11 AA-MA required elements
3. **Reference completeness** — reference.md has facts extracted from plan
4. **HTP structure** — tasks.md has proper milestone/step hierarchy with Status fields
5. **Cross-file consistency** — no contradictions between files

**Validator verdict handling:**
- **PASS**: All checks passed → continue to step 2
- **WARN**: Minor issues (non-blocking) → log warnings, continue to step 2
- **FAIL**: Critical issues → attempt remediation:
  1. Spawn `aa-ma-scribe` to fix identified issues
  2. Re-run validator
  3. If still FAIL → HALT and alert user

**If Tier 2 agent spawning unavailable:** Skip Tier 2 (Tier 1 existence check is sufficient to proceed). Log: "Tier 2 validation skipped — agent spawning unavailable."

---

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

---

## 3. Validate Loaded Context

**Required checks**:
- ✅ REFERENCE contains key constants (APIs, paths, configs)
- ✅ TASKS has clear HTP structure with Status fields
- ✅ At least one milestone has `Status: PENDING` or `Status: ACTIVE`
- ✅ Milestones have explicit Acceptance Criteria defined

**If validation fails**:
```
ERROR: [Specific issue]
- Missing AA-MA files → "AA-MA files not found. Run /ultraplan first."
- Malformed HTP → "tasks.md lacks proper HTP format. Review AA-MA Planning Standard."
- No pending milestones → "All milestones complete. Check tasks.md status."
- Missing acceptance criteria → "Milestone lacks acceptance criteria. Update tasks.md."
```

---

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

---

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

---

## 5. Execute Milestone

### 5.1 Set Milestone Status to ACTIVE

1. Update tasks.md: Change target milestone `Status: PENDING` → `Status: ACTIVE`
2. Update TodoWrite: Mark milestone todo as `in_progress`

### 5.2 Execute All Sub-Tasks

**For each sub-task (### node) in milestone**:

1. **Start sub-task**:
   - Mark TodoWrite sub-task as `in_progress`

2. **Execute sub-task**:
   - Follow task instructions and acceptance criteria
   - Use agents, skills, Context7 MCP as appropriate for efficiency
   - For high complexity (≥80%), use deep reasoning / Chain-of-Thought

3. **Verify completion (Guidance-based)**:
   - Trust your assessment of whether result meets expectations
   - No hard blocking at sub-task level

4. **Update tracking**:
   - Update `Result Log:` field in tasks.md with outcome summary
   - Mark TodoWrite sub-task as `completed`

5. **Continue to next sub-task**

---

## 6. Milestone Boundary Validation (STRICT)

**When all sub-tasks complete, REQUIRED validation before marking milestone COMPLETE:**

### 6.1 Acceptance Criteria Verification

**REQUIRED**:
- Milestone MUST have explicit Acceptance Criteria in tasks.md
- You MUST explicitly verify EACH criterion met
- Document verification method for each criterion

**For each acceptance criterion**:
1. Execute verification (run test, check metric, manual verification)
2. Document result: `✓ [criterion]: [verification method/result]`
3. If ANY criterion fails → HALT and set `Status: BLOCKED`

**Example verification**:
```
Acceptance Criteria Verification:
- ✓ PostgreSQL database running locally: Verified via `psql -c '\l'`, database exists
- ✓ Redis instance configured: Verified via `redis-cli ping`, returns PONG
- ✓ Environment variables loaded from .env: Verified via `echo $DATABASE_URL`, correct value
```

### 6.2 Dependency Verification

**Check next milestone dependencies**:
1. Read `Dependencies:` field of next milestone (if exists)
2. Verify all dependency milestones have `Status: COMPLETE`
3. If dependencies unmet → HALT and notify user

**Example**:
```
Next Milestone: ## Step 3: Deploy to Staging
Dependencies: Step 2
Verification: Step 2 Status: COMPLETE ✓
```

### 6.3 Impact Analysis Verification (REQUIRED)

**Before completing milestone, verify no breaking changes introduced:**

**Index-enhanced (when PROJECT_INDEX.json exists):**
Before invoking the full impact-analysis skill, run a quick pre-check using the index:
- For each modified file's key symbols, call `blast_radius(symbol, depth=2)` via MCP or CLI
- If any symbol has >10 transitive callers, flag it as HIGH risk early
- This pre-check is **advisory only** — never blocks, just surfaces risk earlier
- Skip silently if no index is available

1. **Invoke the impact-analysis skill** (`Skill(impact-analysis)`)
2. **Output consolidated impact analysis** for ALL files modified in this milestone
3. **Verify no unresolved cascade effects**

**Required output format** (consolidated for milestone):
```
📊 Impact Analysis: Milestone "[Milestone Title]"
┌─ Files Modified: [N]
│
├─ [file_path_1]
│  ├─ Upstream: [N] callers
│  ├─ Contract: [YES/NO]
│  └─ Risk: [LOW/MEDIUM/HIGH]
│
├─ [file_path_2]
│  └─ Risk: [LOW/MEDIUM/HIGH]
│
└─ Overall Risk: [LOW/MEDIUM/HIGH]
   [Action summary if risk > LOW]
```

**Validation rules**:
- If Overall Risk = LOW → Proceed to Test Execution
- If Overall Risk = MEDIUM → Document cascade updates made, then proceed
- If Overall Risk = HIGH → HALT, present options to user (auto-fix, manual review, or abort)

**Never complete milestone with unresolved HIGH risk impacts.**

### 6.4 Test Execution (if specified)

**If milestone has "Tests to validate:" section**:
1. Run ALL listed tests
2. ALL tests must pass (zero failures)
3. Document test command + results in Result Log
4. If ANY test fails → HALT and set `Status: BLOCKED`

**Auto-detect `[task]-tests.yaml`:** If the AA-MA task directory contains a `[task]-tests.yaml` file, parse it for the current milestone's tests and execute them:

```bash
# Check for executable test definitions
TESTS_FILE="${TASK_DIR}/${TASK_NAME}-tests.yaml"
if [[ -f "$TESTS_FILE" ]]; then
  echo "Found executable test definitions: $TESTS_FILE"
  # Parse and run each test for the current milestone
  # Each test has: name, command, expected (exact) or expected_pattern (regex)
  # ALL tests must pass — any failure → HALT
fi
```

**Test execution logic:**
1. Read `[task]-tests.yaml` for the current milestone key (e.g., `milestone_1`)
2. For each test entry:
   - Run the `command` in the project root directory
   - Compare output to `expected` (exact match) or `expected_pattern` (regex)
   - Log pass/fail with test name to Result Log
3. If ANY test fails → HALT and set `Status: BLOCKED`
4. If all pass → append summary: `Tests: [X/X] passed (from tests.yaml)`

**Fallback:** If no `tests.yaml` exists, use the existing prose-based test execution behavior.

**Error handling:** If `tests.yaml` exists but is malformed (invalid YAML), or the current milestone key is not found in the file, log a warning and fall back to prose-based testing. Do NOT block on a broken test definition file — treat it as a WARNING, not a HALT.

**Example**:
```bash
# Run tests from tests.yaml
# milestone_1:
#   - name: "Auth tests pass"
#     command: "pytest tests/auth/ -q --tb=short"
#     expected_pattern: "passed"

pytest tests/auth/ -q --tb=short
# Expected: output matches "passed"
# If failures → Status: BLOCKED, create remediation sub-task
```

---

### 6.5 Optional Web Verification (gstack integration)

**When to offer:** Project has a dev server (detect `Makefile` targets `run`/`dev`/`serve`, or `package.json` scripts `dev`/`start`) AND milestone tasks touch web-facing code.

**Detection logic:**
```bash
# Check for dev server capability
grep -qE '^(run|dev|serve):' Makefile 2>/dev/null || \
  jq -e '.scripts.dev // .scripts.start' package.json 2>/dev/null
```

**Prompt user:**
```
🌐 Run web verification for this milestone?
   Dev server detected. Options:
   [Q] /qa-only --quick — smoke test with health score
   [B] /browse — screenshot evidence for UI changes
   [A] Both /qa-only + /browse
   [N] Skip
```

**If /qa-only selected:**
1. ALWAYS use `Skill(qa-only)` — NEVER full `/qa` during AA-MA execution (provenance protection)
2. `/qa-only` produces a report with health score but makes NO commits
3. Store health score in tasks.md Result Log: `Web QA: [health score]% — [summary]`

**If /browse selected:**
1. Invoke `Skill(browse)` for screenshot evidence when milestone tasks touch UI files (`.html`, `.css`, `.tsx`, `.jsx`, Streamlit `*.py`)
2. Store screenshots reference in tasks.md Result Log: `Visual evidence: [screenshot description]`

**Critical constraint:** Use `/qa-only` (NEVER `/qa`) during AA-MA execution. Full `/qa` commits with `fix(qa):` format without AA-MA signatures, breaking provenance chain.

**If declined or detection fails:** Proceed directly to Finalization. This step is purely additive — all existing validation gates (6.1-6.4) have already passed.

**Soft-blocking gate:** If `/qa-only` reports a health score below 50% or flags CRITICAL issues:
```
⚠️  QA found critical issues (health: [X]%)
   [A] Acknowledge and proceed to finalization
   [F] Fix issues before finalizing (creates remediation sub-tasks)
   [R] Re-run QA after fixes
```
User must explicitly acknowledge to proceed. This prevents accidentally finalizing a milestone with known critical web issues.

### 6.6 Post-Milestone Simplification Review

**When:** After all validation gates pass (6.1-6.5), before finalization protocol.

**Skip if:** Only docs/config files changed (no `.py`, `.ts`, `.js`, `.jsx`, `.tsx`), OR total code diff < 20 lines, OR user passed `--skip-simplify`.

**Execution:**

1. Get milestone diff:
   ```bash
   # Find last milestone checkpoint or branch start
   LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || git merge-base HEAD main 2>/dev/null || echo "HEAD~10")
   git diff "$LAST_TAG"..HEAD -- '*.py' '*.ts' '*.js' '*.jsx' '*.tsx' '*.go' '*.rs'
   ```

2. Launch 3 review agents in parallel (pass full diff to each):

   **Agent 1 — Code Reuse:**
   Search the codebase for existing utilities that could replace newly written code.
   Flag: new functions duplicating existing functionality, inline logic that existing
   helpers already handle, hand-rolled patterns with library equivalents.

   **Agent 2 — Code Quality:**
   Review for: redundant state, parameter sprawl, copy-paste with slight variation,
   leaky abstractions, stringly-typed code, unnecessary comments explaining WHAT not WHY.

   **Agent 3 — Efficiency:**
   Review for: N+1 patterns, missed concurrency (independent operations run sequentially),
   hot-path bloat, unnecessary existence checks (TOCTOU), memory leaks, overly broad operations.

3. Aggregate findings:
   ```
   POST-MILESTONE REVIEW: [N] findings

   CRITICAL (must acknowledge):
     - [finding with file:line]

   WARNING (recommended fix):
     - [finding with file:line]

   INFO (optional improvement):
     - [finding with file:line]

   Clean: No issues found
   ```

4. If findings exist, offer:
   - **Fix now** — Apply non-controversial fixes before committing
   - **Acknowledge and proceed** — Log findings, continue to finalization
   - **Review details** — Show full agent reports before deciding

5. Log to provenance.log:
   ```
   [YYYY-MM-DD HH:MM:SS] Post-milestone review: N findings (C critical, W warning, I info) [fixed|acknowledged|skipped]
   ```

**If review agents fail or time out:** Skip review, log to provenance: `Post-milestone review: SKIPPED — agent failure`. Do NOT block finalization.

---

## 7. Finalization Protocol — MANDATORY

Before marking the milestone COMPLETE and creating git checkpoint, execute this 4-step finalization protocol. **No exceptions.**

### 7.1 Integrity Check (Checklist Verification)

**HARD Gate Check:** If the milestone has `Gate: HARD`, verify that a signed approval artifact exists in `[task]-context-log.md`:

```bash
# Check for HARD gate approval
GATE=$(grep -A1 "## Milestone.*${MILESTONE_TITLE}" "${TASK_DIR}/${TASK_NAME}-tasks.md" | grep -oP 'Gate: \K\w+')
if [[ "$GATE" == "HARD" ]]; then
  if ! grep -q "GATE APPROVAL: ${MILESTONE_TITLE}" "${TASK_DIR}/${TASK_NAME}-context-log.md"; then
    echo "BLOCKED: Gate: HARD requires signed approval in context-log.md"
    echo "Required format: ## [date] GATE APPROVAL: ${MILESTONE_TITLE}"
    # HALT — cannot proceed without approval artifact
  fi
fi
```

**If HARD gate and no approval artifact:** HALT immediately. Use AskUserQuestion to request approval. If approved, write the gate approval artifact to context-log.md, then continue.

Display acceptance criteria verification to the user:

```
Acceptance Criteria Verification:
- ✓ [Criterion 1]: Confirmed - [brief evidence]
- ✓ [Criterion 2]: Confirmed - [brief evidence]
- ✓ [Criterion 3]: Confirmed - [brief evidence]

Gate: [HARD|SOFT] — [Approval artifact found / Convention-based]
All [X] criteria verified. Ready for finalization.
```

**Rules:**
- Every acceptance criterion must be explicitly listed
- Each must have `✓` confirmation with brief evidence
- If ANY criterion cannot be confirmed → HALT, do not proceed
- If `Gate: HARD` and no approval artifact → HALT, request approval

### 7.2 Documentation Auto-Update

Automatically update all 5 AA-MA files:

| File | Auto-Update Action |
|------|-------------------|
| `tasks.md` | Mark milestone `Status: COMPLETE`, fill `Result Log:` |
| `reference.md` | Add any new immutable facts discovered during execution |
| `context-log.md` | Append completion summary (template below) |
| `provenance.log` | Append completion entry with timestamp + commit hash |
| `plan.md` | No change (historical record) |

**Context-log.md template:**
```markdown
## [YYYY-MM-DD] Milestone Completion: [Title]
- Status: COMPLETE
- Key outcome: [1-2 sentence summary]
- Artifacts: [list of files created/modified]
- Tests: [pass/fail summary]
```

**Provenance.log template:**
```
[TIMESTAMP] MILESTONE COMPLETE — [Milestone ID] — Commit: [hash] — Criteria: [X/X] verified
```

### 7.3 User Authorization (Approval Gate)

Use AskUserQuestion to get explicit user approval before changing status to COMPLETE:

**Question format:**
```
📋 Finalization Review

Milestone: [Title]
Acceptance Criteria: [X/X] verified ✓

Ready to mark this milestone COMPLETE?
```

**Options:**
- **Approve** → "Proceed with status change and commit"
- **Review First** → "Show me the detailed verification before approving"
- **Reject** → "Do not mark complete, keep as ACTIVE"

**Behavior by choice:**
- **Approve**: Proceed to Step 7.4 and git commit
- **Review First**: Display full integrity checklist with evidence, then re-prompt
- **Reject**: HALT execution, keep `Status: ACTIVE`, ask user what needs fixing

### 7.4 Transparent Status Change

After approval, display minimal confirmation:

```
✅ Milestone marked COMPLETE: [Title]
```

Then proceed to git commit.

**Archive Reminder** (only if this is the FINAL milestone):
If ALL milestones in tasks.md now have `Status: COMPLETE`, add:
```
💡 All milestones complete! Run: /archive-aa-ma [task-name]
```

---

## 8. Git Checkpoint Creation (Auto-commit)

**If validation passes, create git checkpoint automatically:**

### 8.1 Stage Changes
```bash
git add .
```

### 8.2 Create Structured Commit

```bash
# Extract milestone info from tasks.md
TASK_NAME="[task-name]"
MILESTONE_TITLE="[milestone title from ## header]"
MILESTONE_ID="[milestone-id, e.g., step-1-setup]"
COMPLEXITY="[complexity percentage]"

# Build acceptance criteria list
ACCEPTANCE_VERIFIED="$(cat <<'EOF'
- [criterion 1]: ✓ [verification method]
- [criterion 2]: ✓ [verification method]
EOF
)"

# Build completed tasks list
TASKS_COMPLETED="$(cat <<'EOF'
- [sub-task 1]
- [sub-task 2]
EOF
)"

# Build test status
TEST_STATUS="ALL PASS"  # or specific test summary

# Create commit
git commit -m "feat($TASK_NAME): Complete $MILESTONE_TITLE

Milestone: $MILESTONE_ID
Complexity: $COMPLEXITY%

Acceptance criteria verified:
$ACCEPTANCE_VERIFIED

Tasks completed:
$TASKS_COMPLETED

Tests: $TEST_STATUS

[AA-MA Plan] $TASK_NAME .claude/dev/active/$TASK_NAME"
```

### 8.3 Update Provenance Log

```bash
# Get commit info
COMMIT_HASH=$(git rev-parse --short HEAD)
TIMESTAMP=$(date -Iseconds)
MILESTONE_ID="[milestone-id]"

# Append milestone completion to provenance log
echo "[$TIMESTAMP] MILESTONE COMPLETE — $MILESTONE_ID — Commit: $COMMIT_HASH — Criteria: [X/X] verified" >> .claude/dev/active/$TASK_NAME/${TASK_NAME}-provenance.log
```

**Session Checkpoint (on compaction or session end):** If context compaction is triggered during milestone execution, also write a CHECKPOINT entry for reliable session resume:

```bash
# Write checkpoint for session resume
ACTIVE_STEP="[current-step-id]"
NEXT_ACTION="[description of next action]"
TOKEN_USAGE="[estimated %]"
echo "[$TIMESTAMP] CHECKPOINT — ActiveStep: $ACTIVE_STEP — NextAction: \"$NEXT_ACTION\" — ContextLoaded: REFERENCE,TASKS — TokenUsage: $TOKEN_USAGE%" >> .claude/dev/active/$TASK_NAME/${TASK_NAME}-provenance.log
```

### 8.4 Commit Provenance Update

```bash
# Add provenance log to same commit
git add .claude/dev/active/$TASK_NAME/${TASK_NAME}-provenance.log
git commit --amend --no-edit
```

### 8.5 Push to Remote

```bash
git push
```

---

## 9. Update Milestone Status

**After successful git checkpoint**:

1. Update tasks.md: Change milestone `Status: ACTIVE` → `Status: COMPLETE`
2. Fill in milestone-level `Result Log:` with summary
3. Update TodoWrite: Mark milestone todo as `completed`
4. Save all changes

---

## 10. Report Completion

**Success message**:
```
✅ Milestone completed: [milestone title]

Acceptance Criteria: All verified ✓
Tests: [status]
Commit: [commit-hash]
Provenance: Updated

Summary:
[Brief outcome summary]

Next steps:
- Run /execute-aa-ma-milestone again to continue with next milestone
- OR run /execute-aa-ma-full to execute all remaining milestones
- OR review changes and plan next phase manually
```

---

## 11. Error Handling at Checkpoint

**If validation fails at milestone boundary:**

### 11.1 Set Status to BLOCKED

Update tasks.md: Change milestone `Status: ACTIVE` → `Status: BLOCKED`

### 11.2 Create Remediation Sub-Task

Add new sub-task under milestone:
```markdown
### Sub-step: Resolve [validation failure]
- Status: PENDING
- Dependencies: None
- Complexity: [estimate]%
- Acceptance Criteria: [specific fix required]
- Result Log: (to be filled)
```

### 11.3 Alert User

```
🚫 Milestone blocked: [milestone title]

Validation Failure:
- Check: [which validation check failed]
- Details: [specific criterion/test that didn't pass]

Remediation:
Created new sub-task: "Resolve [validation failure]"

Suggested steps:
[remediation guidance]

Resolution:
1. Fix the blocking issue
2. Re-run /execute-aa-ma-milestone to retry validation
```

### 11.4 Update TodoWrite

- Mark milestone todo as `pending` (not completed)
- Add new todo for remediation sub-task
- Prefix milestone content with "BLOCKED: "

### 11.5 HALT Execution

- Do NOT proceed to next milestone
- Do NOT create git commit
- Wait for user intervention

---

## Token & Context Optimization

- **Monitor token usage**: Check current session context usage
- **If approaching limits**: Consider context compaction:
  1. Summarize completed milestones
  2. Preserve essential state, open issues, acceptance criteria
  3. Discard redundant tool outputs
  4. Update context-log.md with summary
  5. Reset session with compacted context

---

## Rollback Support

**Each milestone commit is a rollback point:**

- **View milestone history**: `git log --oneline --grep="feat([task-name])"`
- **Rollback specific milestone**: `git revert [milestone-commit-hash]`
- **Rollback to milestone**: `git reset --hard [milestone-commit-hash]` (destructive, use with caution)
- **Audit trail**: Provenance log provides complete execution history

**Provenance log format**:
```
[2025-11-17T10:30:00+00:00] Commit a1b2c3d — MilestoneID: step-1-setup — Status: COMPLETE
[2025-11-17T11:45:00+00:00] Commit e4f5g6h — MilestoneID: step-2-implement — Status: COMPLETE
```

---

**End of execute-aa-ma-milestone.md**
