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
6. If still FAIL after retry → HALT and alert user: "Auto-recovery failed. Run `/aa-ma-plan` to recreate artifacts."
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
- Missing AA-MA files → "AA-MA files not found. Run /aa-ma-plan first."
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
3. **Dependency advisory — never blocks** (map Ticket 16). Show the user any line it
   prints, e.g. `Milestone 3 is ACTIVE but Milestone 2 (Dependencies) is PENDING`, and
   log it to provenance.log. It never halts and never changes an exit code; `aa-ma-gate`
   does not read `Dependencies:`.

```bash
TASKS_MD=".claude/dev/active/${TASK_NAME}/${TASK_NAME}-tasks.md"
for _cand in \
  "$(git rev-parse --show-toplevel 2>/dev/null)/claude-code/hooks/lib/aa-ma-parse.sh" \
  "${CLAUDE_HOME:-${HOME}/.claude}/hooks/lib/aa-ma-parse.sh"; do
  [[ -f "${_cand}" ]] && AA_MA_LIB="${_cand}" && break
done
# shellcheck source=/dev/null
[[ -n "${AA_MA_LIB:-}" ]] && . "${AA_MA_LIB}"
aa_ma_deps advisory "${TASKS_MD}" 2>/dev/null || echo "(dependency advisory unavailable — continuing)"
true
```

### 5.2 Execute All Sub-Tasks

**For each sub-task (### node) in milestone**:

1. **Start sub-task**:
   - Mark TodoWrite sub-task as `in_progress`

1.5. **Mode Dispatch (HITL / AFK)**:
   Resolve `Mode:` through the Python SSoT gate — the sub-step's own, else the
   parent milestone's, else `HITL`. Do not read the field by eye or with grep:
   the tolerant reader in `tui/parser.py` resolves `Mode: TYPO` to `AFK`, which
   silently converts a human-in-the-loop sub-step into one that auto-dispatches
   without asking. The gate refuses it instead, quoting the line.

   ```bash
   # MILESTONE_NUMBER is the `N` of `## Milestone N:`; STEP_ID the `N.M` of
   # `### Sub-step N.M:`. Self-sufficient on purpose: this runs ~300 lines
   # before the §6.7 preamble, and a fence that depends on another fence's
   # variables reads them as empty when run in a fresh shell (the awk gate
   # failed exactly that way — "GATE was always empty").
   TASKS_MD=".claude/dev/active/${TASK_NAME}/${TASK_NAME}-tasks.md"
   for _cand in \
     "$(git rev-parse --show-toplevel 2>/dev/null)/claude-code/hooks/lib/aa-ma-parse.sh" \
     "${CLAUDE_HOME:-${HOME}/.claude}/hooks/lib/aa-ma-parse.sh"; do
     [[ -f "${_cand}" ]] && AA_MA_LIB="${_cand}" && break
   done
   # shellcheck source=/dev/null
   . "${AA_MA_LIB:?aa-ma-parse.sh not found — run scripts/install.sh}"
   STEP_KV=$(aa_ma_gate "${TASKS_MD}" --milestone "${MILESTONE_NUMBER}" --step "${STEP_ID}")
   STEP_RC=$?
   if [[ "${STEP_RC}" -ne 0 ]]; then
     echo "BLOCKED: cannot resolve Mode for sub-step ${STEP_ID} (gate rc ${STEP_RC}):"
     printf '%s\n' "${STEP_KV}" | sed -n 's/^error=/  - /p'
     exit 1   # never dispatch a sub-step whose Mode the gate could not read
   fi
   MODE=$(printf '%s\n' "${STEP_KV}" | aa_ma_gate_field step_mode)          # HITL | AFK
   MODE_SOURCE=$(printf '%s\n' "${STEP_KV}" | aa_ma_gate_field step_mode_source)  # step | milestone | default
   ```

   **If Mode: HITL:**
   Display task summary and acceptance criteria, then use `AskUserQuestion`:
   - **Proceed**: Continue to step 2
   - **Skip**: Mark `Status: SKIPPED — User skipped at HITL gate`, move to next sub-task
   - **Abort**: Halt milestone execution, keep milestone `Status: ACTIVE`
   
   **If Mode: AFK:**
   - Proceed directly to step 2 without pause
   - Log in Result Log: `Mode: AFK — auto-dispatched`
   
   **Note:** HARD gates at milestone boundary (Section 7.1) always pause regardless of Mode.

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

### 6.2 Dependency Verification (advisory — never blocks)

Nothing to enforce here. The next milestone's `Dependencies:` are reported when it
becomes ACTIVE — §5.1 step 3 runs `aa_ma_deps advisory` — and that report never stops
execution (map Ticket 16; `aa-ma-gate` does not read the field). Name the next
milestone's dependencies in the completion report so the user sees what comes next,
e.g. `Next: Milestone 3 — Dependencies: Milestone 2` (canonical form).

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

### 6.7 Engineering Standards HARD Gate

Reference: `claude-code/rules/engineering-standards.md` (Themes 1, 4, 5, 6).
This gate is structural — it refuses to mark COMPLETE when any of 5 conditions
fails. Independent of `Gate: SOFT|HARD` in tasks.md (that controls the approval
artifact in 7.1; THIS gate enforces engineering posture for every milestone).

**Five conditions, evaluated in order:**

```bash
TASK_DIR=".claude/dev/active/${TASK_NAME}"
TASKS_MD="${TASK_DIR}/${TASK_NAME}-tasks.md"

# 1. AA-MA artifacts in sync (clean git for AA-MA files)
DIRTY_AA_MA=$(git status --porcelain "${TASK_DIR}/" | wc -l | tr -d ' ')
if [[ "${DIRTY_AA_MA}" -ne 0 ]]; then
  echo "BLOCKED: AA-MA artifacts have uncommitted changes."
  echo "Run sub-step Result Log discipline (L-080-082); commit and re-run."
  # Was `# HALT` — a comment. Measured against a dirty task dir: printed
  # BLOCKED and then PASS with exit 0. The gate contradicted itself and passed.
  exit 1
fi

# --- Gate preamble: every reading below comes from the Python SSoT -----------
#
# The awk that used to live here was a hand-written markdown parser whose
# accepted-string set was decided by reasoning, not measurement; ADR-0009
# records what three reviews found in it. So: bash asks, Python answers.
# `aa_ma_gate` is a launcher, not a parser; `aa-ma-gate` (src/aa_ma/gate.py)
# answers all seven questions over grammar.py + enforce.py + plan_parsers.py
# and refuses on ambiguity rather than choosing. Exit codes: `aa-ma-gate --help`.
#
# Resolution order matches the shipped hooks: repo-local first so a clone that
# has not run install.sh still works.
for _cand in \
  "$(git rev-parse --show-toplevel 2>/dev/null)/claude-code/hooks/lib/aa-ma-parse.sh" \
  "${CLAUDE_HOME:-${HOME}/.claude}/hooks/lib/aa-ma-parse.sh"; do
  [[ -f "${_cand}" ]] && AA_MA_LIB="${_cand}" && break
done
if [[ -z "${AA_MA_LIB:-}" ]]; then
  echo "BLOCKED: aa-ma-parse.sh not found — run scripts/install.sh."
  echo "Refusing to evaluate the gate with no way to run it:"
  echo "a gate that cannot read the milestone reports zero problems."
  exit 1
fi
# shellcheck source=/dev/null
. "${AA_MA_LIB}"

# One call answers every question. Exit codes are the contract's and fail
# closed: 0 one ACTIVE and every enforced field readable · 1 no ACTIVE ·
# 2 unreadable (missing file, unclosed fence, invalid field, orphan sub-step) ·
# 3 ambiguous (2+ ACTIVE, duplicate heading) · 127 the gate could not run.
# `aa_ma_gate` prints nothing but a BLOCKED line for 127, so the `error=`
# lines below are only ever the Python gate's own words.
GATE_KV=$(aa_ma_gate "${TASKS_MD}")
GATE_RC=$?
if [[ "${GATE_RC}" -ne 0 ]]; then
  case "${GATE_RC}" in
    1) echo "BLOCKED: no milestone is ACTIVE in ${TASK_NAME}-tasks.md."
       echo "§5.1 sets the target milestone to ACTIVE before its sub-steps run." ;;
    2) echo "BLOCKED: ${TASK_NAME}-tasks.md is unreadable to the gate:" ;;
    3) echo "BLOCKED: ambiguous — the gate cannot tell which milestone it is certifying:" ;;
    *) echo "BLOCKED: aa-ma-gate did not run (rc ${GATE_RC}). Python + uv are"
       echo "required at gate time; a gate that cannot run must not pass." ;;
  esac
  printf '%s\n' "${GATE_KV}" | sed -n 's/^error=/  - /p'
  exit 1
fi

# Question 1: the exact heading, consumed verbatim by §7.1's approval grep.
MILESTONE_TITLE=$(printf '%s\n' "${GATE_KV}" | aa_ma_gate_field heading)
if [[ -z "${MILESTONE_TITLE}" ]]; then
  echo "BLOCKED: gate returned 0 but no heading — refusing on an empty subject."
  exit 1
fi

# 2. Zero Status: PENDING sub-steps within the milestone (question 3)
PENDING_IN_MILESTONE=$(printf '%s\n' "${GATE_KV}" | aa_ma_gate_field pending_steps)
if [[ "${PENDING_IN_MILESTONE}" -gt 0 ]]; then
  echo "BLOCKED: ${PENDING_IN_MILESTONE} sub-step(s) still PENDING in ${MILESTONE_TITLE}."
  exit 1
fi

# 3. Tests-pass evidence (already enforced in 6.4; double-check Result Log mentions)
# 4. Impact-analysis evidence (already enforced in 6.3; double-check Result Log mentions)

# 5. Critical-Path / Prototype-Required provenance evidence (CONDITIONAL)
# Absent-field semantic: the gate reports an empty value when the field is
# absent, and the check is skipped. Only present-but-without-evidence fires.
#
# The evidence greps are MILESTONE-SCOPED. A bare `grep -q CRITICAL_PATH_REVIEW`
# over the whole provenance.log means that once ANY milestone writes the token,
# every later milestone's check is pre-satisfied. Entries must name the milestone:
#   [ts] CRITICAL_PATH_REVIEW — <milestone-title> — <value> — <evidence>
CRITICAL_PATH_TASKS=$(printf '%s\n' "${GATE_KV}" | aa_ma_gate_field critical_path)
if [[ -n "${CRITICAL_PATH_TASKS}" ]]; then
  if ! grep -F -- "CRITICAL_PATH_REVIEW" "${TASK_DIR}/${TASK_NAME}-provenance.log" \
       | grep -qF -- "${MILESTONE_TITLE}"; then
    echo "BLOCKED: Milestone declares Critical-Path: ${CRITICAL_PATH_TASKS} but"
    echo "provenance.log has no CRITICAL_PATH_REVIEW entry naming this milestone."
    exit 1
  fi
fi

PROTOTYPE_TASKS=$(printf '%s\n' "${GATE_KV}" | aa_ma_gate_field prototype_required)
if [[ "${PROTOTYPE_TASKS}" == "YES" ]]; then
  if ! grep -F -- "PROTOTYPE —" "${TASK_DIR}/${TASK_NAME}-provenance.log" \
       | grep -qF -- "${MILESTONE_TITLE}"; then
    echo "BLOCKED: the milestone or one of its sub-steps declares Prototype-Required: YES"
    echo "but provenance.log has no PROTOTYPE — <milestone heading> — <verdict> entry naming this milestone."
    exit 1
  fi
fi

echo "ENG-STANDARDS-GATE: PASS (all 5 conditions satisfied)"
```

**Absent-field semantic** (M2.5 verification finding): when `Critical-Path:` or
`Prototype-Required:` is **absent** from a task, the corresponding check is
**skipped (no failure)**. Only present-but-without-evidence triggers a HALT.
This preserves backward compat with `examples/` plans authored before v0.5.0.

**Bypass:** to override this gate (e.g. for diagnostic runs), set
`AA_MA_HOOKS_DISABLE=1` in the environment. The gate honors the master kill
switch but logs the override to provenance.log:
`[ts] ENG_STANDARDS_GATE: BYPASSED via AA_MA_HOOKS_DISABLE`.

**§13 sigil edges verified — HARD, opt-in** (ADR-0015; Execution Checklist row in
`engineering-standards.md` §5). HARD ≠ `gate.py`: `aa-ma-gate` reads only `tasks.md`,
while §13 lives in `plan.md`, so this item is enforced here and the gate CLI, its kv
envelope and the fence above are unchanged. It applies only when the plan's §13 carries
a sigil edge (`-->|"@import"|`, `-->|"@call"|`, …); a plan without one is a no-op.

| Lint says | Verdict |
|-----------|---------|
| `edges=0` | not applicable — no evidence written |
| `phantom>0` (`PHANTOM_EDGE` / `LABEL_UNKNOWN`) | BLOCKED — the diagram claims an edge the code does not hold |
| `invalid>0` — an edge to a missing file, a stale `(new)` on a file that exists, a path-less label, an unparsed edge form, a path outside the repo | BLOCKED — an authoring error the diagram can fix now |
| `index-unknown>0` (no, stale, too-old or unreadable index) | BLOCKED — the check did not run (L-012); run `codemem build` and re-run |
| no `sigils:` line / `sigils: UNKNOWN` (a sigil edge outside §13's views, an unterminated fence) / the lint did not run | BLOCKED — not every sigil edge could be read |
| otherwise | PASS — appends `[ts] DIAGRAM_VERIFIED — <milestone heading> — edges=N checked=C phantom=0 unknown=K` |

What still passes, counted in `unknown=K`: a claim that cannot be checked *yet* — a
genuinely planned `(new)` file, a plugin sigil (`@skill`/`@command`/`@agent`/`@hook`), a
language the graph does not model. `checked=C` is how many edges were actually compared
with the code. The fence run is the check; the `DIAGRAM_VERIFIED` line is its record.
This fence must stay AFTER the gate fence above: `tests/hooks/aa-ma-gate-python.bats`
(`_gate_fence`) executes the *first* ```bash fence after the `### 6.7 ` heading, and
`tests/hooks/test_diagram_verified.bats` asserts the order.

```bash
# Self-sufficient, like §7.1's fence: a fresh shell has none of the variables above.
# TASK_NAME builds the path this fence appends to: a plain slug only (no `/`, no `..`).
if ! [[ "${TASK_NAME:-}" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ && "${TASK_NAME}" != *..* ]]; then
  echo "BLOCKED: TASK_NAME must be a plain task slug (got '${TASK_NAME:-}')."
  exit 1
fi
TASK_DIR=".claude/dev/active/${TASK_NAME}"
for _cand in \
  "$(git rev-parse --show-toplevel 2>/dev/null)/claude-code/hooks/lib/aa-ma-parse.sh" \
  "${CLAUDE_HOME:-${HOME}/.claude}/hooks/lib/aa-ma-parse.sh"; do
  [[ -f "${_cand}" ]] && AA_MA_LIB="${_cand}" && break
done
# shellcheck source=/dev/null
. "${AA_MA_LIB:?aa-ma-parse.sh not found — run scripts/install.sh}"
GATE_KV=$(aa_ma_gate "${TASK_DIR}/${TASK_NAME}-tasks.md") || {
  echo "BLOCKED: cannot read the milestone to verify its §13 sigil edges (gate rc $?):"
  printf '%s\n' "${GATE_KV}" | sed -n 's/^error=/  - /p'
  exit 1
}
MILESTONE_TITLE=$(printf '%s\n' "${GATE_KV}" | aa_ma_gate_field heading)
[[ -n "${MILESTONE_TITLE}" ]] || { echo "BLOCKED: empty milestone heading."; exit 1; }

LINT=$(aa_ma_lint_views "${TASK_DIR}/${TASK_NAME}-plan.md" \
  --repo-root "$(git rev-parse --show-toplevel 2>/dev/null || pwd)")
LINT_RC=$?
# The CLI prints its own summary last; any earlier `sigils:` line is not its.
SIGILS=$(printf '%s\n' "${LINT}" | sed -n 's/^sigils: //p' | tail -n 1)
SIGILS_RE='^edges=([0-9]+) checked=([0-9]+) phantom=([0-9]+) unknown=([0-9]+) invalid=([0-9]+) index-unknown=([0-9]+)$'
if [[ "${LINT_RC}" -gt 1 ]] || ! [[ "${SIGILS}" =~ ${SIGILS_RE} ]]; then
  echo "BLOCKED: §13 sigil edges could not be checked (lint rc ${LINT_RC}, sigils: ${SIGILS:-absent})."
  echo "A check that did not run is not a pass (L-012)."
  printf '%s\n' "${LINT}" | grep -E ': (UNTERMINATED_FENCE|UNKNOWN):' | head -n 5
  exit 1
fi
EDGES=${BASH_REMATCH[1]} CHECKED=${BASH_REMATCH[2]} PHANTOM=${BASH_REMATCH[3]}
UNKNOWN=${BASH_REMATCH[4]} INVALID=${BASH_REMATCH[5]} INDEX_UNKNOWN=${BASH_REMATCH[6]}

if [[ "${EDGES}" -eq 0 ]]; then
  echo "DIAGRAM-GATE: not applicable — §13 carries no sigil edge"
elif [[ "${PHANTOM}" -gt 0 ]]; then
  echo "BLOCKED: ${PHANTOM} §13 sigil edge(s) the code does not hold:"
  printf '%s\n' "${LINT}" | grep -E ': (PHANTOM_EDGE|LABEL_UNKNOWN):'
  echo "Fix the diagram (or the code) in this milestone, then re-run."
  exit 1
elif [[ "${INVALID}" -gt 0 ]]; then
  echo "BLOCKED: ${INVALID} §13 sigil edge(s) the diagram makes uncheckable:"
  printf '%s\n' "${LINT}" | grep -E ': UNKNOWN: (marked \(new\) but exists|no repo path|endpoint outside|unparsed sigil|not in the codemem graph .*endpoint missing)'
  echo "Fix the diagram in this milestone (drop a stale (new), label the node with its path), then re-run."
  exit 1
elif [[ "${INDEX_UNKNOWN}" -gt 0 ]]; then
  echo "BLOCKED: the codemem index could not verify ${INDEX_UNKNOWN} §13 sigil edge(s):"
  printf '%s\n' "${LINT}" | grep -F 'codemem build' | head -n 1
  echo "Run \`codemem build\`, then re-run this check."
  exit 1
else
  echo "[$(date -Iseconds)] DIAGRAM_VERIFIED — ${MILESTONE_TITLE} — edges=${EDGES} checked=${CHECKED} phantom=0 unknown=${UNKNOWN}" \
    >> "${TASK_DIR}/${TASK_NAME}-provenance.log"
  echo "DIAGRAM-GATE: PASS — edges=${EDGES} checked=${CHECKED} phantom=0 unknown=${UNKNOWN}"
fi
```

---

### 6.8 Post-Impl Adversarial Review (NEW in v0.8.0)

Reference: ADR-0005 ([`docs/adr/0005-post-impl-adversarial-review.md`](../../docs/adr/0005-post-impl-adversarial-review.md)) and Skill: `verify-impl`.

Symmetric to plan-verification (which runs adversarially BEFORE execution),
§6.8 dispatches up to 5 audit agents AFTER the milestone's implementation has
landed and §6.7 has passed. Goal: close the asymmetry where pre-execution rigor
was high (6-angle plan-verification + 9 HARD gates) but post-execution rigor
was thin (only SOFT §6.6 simplification review).

**Grandfathering — when §6.8 does NOT fire:**

```bash
# Read plan's Created: front-matter
PLAN_CREATED=$(grep -m1 "^\*\*Created:\*\*\|^Created:" \
  "${TASK_DIR}/${TASK_NAME}-plan.md" | grep -oE '[0-9]{4}-[0-9]{2}-[0-9]{2}')

# v0.8.0 release tag commit date (cutover for §6.8)
# Tag v0.8.0 → commit 695f7b7, authored 2026-05-11 17:05:15 +0100.
# Strict less-than: plans Created: < 2026-05-11 are grandfathered.
# The post-impl-adversarial-review meta-plan (Created: 2026-05-11) sits at
# the boundary — see ADR-0005 self-bootstrap note. Future plans will be
# Created: 2026-05-12 or later and thus subject to §6.8.
V080_CUTOVER="2026-05-11"

if [[ -z "${PLAN_CREATED}" ]] || [[ "${PLAN_CREATED}" < "${V080_CUTOVER}" ]]; then
  echo "[$(date -Iseconds)] §6.8 SKIPPED — pre-v0.8.0 plan (grandfathered)" \
    >> "${TASK_DIR}/${TASK_NAME}-provenance.log"
  exit 0  # exit this section, continue to §7
fi

# AA_MA_AUDIT_BUDGET=off explicit skip (auditable bypass)
if [[ "${AA_MA_AUDIT_BUDGET:-normal}" == "off" ]]; then
  echo "[$(date -Iseconds)] AUDIT_BUDGET=off — bypassed §6.8" \
    >> "${TASK_DIR}/${TASK_NAME}-provenance.log"
  exit 0
fi
```

**Dispatch logic:**

1. Read `Audit-Profile:` from the current milestone block using
   `src/aa_ma/plan_parsers.py::parse_audit_profile`. If missing → emit a
   CRITICAL finding from the structural check (plan-verification Angle 6 #4
   should have caught this earlier; defensive double-check here).
2. Resolve the milestone's commit window (`<base_sha>..<head_sha>`) — use the
   first commit with `[AA-MA Plan] <task-name>` footer touching this milestone's
   tasks.md block, OR fall back to `git rev-parse HEAD~N` heuristic if commit
   markers are missing.
3. Invoke the `verify-impl` skill: `Skill(verify-impl)` with parameters
   `--task <task-name> --milestone <milestone-id>`. The skill orchestrator
   handles per-Audit-Profile agent dispatch (full/code-only/docs-only/infra/
   custom) per the matrix in `claude-code/skills/verify-impl/SKILL.md`. The
   5 audit agents are:
   - **code-reviewer** — KISS/SOLID/SOC/DRY + 5 mandatory patterns
     (scope discipline → L-007, mechanism duplication → L-005,
     schema-breaking output → L-006, dead code, magic numbers)
   - **security-auditor** — semantic OWASP review (mechanical handled
     upstream by `security-static-check.sh` PreToolUse hook)
   - **tdd-sequence-auditor** — git-log forensics, PASS/FAIL/WAIVED verdict
     (waivable via canonical `TDD-Waiver` enum)
   - **context7-evidence-auditor** — new PyPI deps + MAJOR-version bumps
     only; WARNING-only ceiling
   - **future-proofing-auditor** — hardcoded counts (proactive Tier 6+),
     magic numbers, version pins, premature abstractions
4. Skill returns an aggregated verdict and writes `[task]-impl-review.md`.

**Verdict outcomes:**

| Verdict | Behaviour |
|---|---|
| `PASS` | Continue to §7.1 |
| `PASS_WITH_WARNINGS` | Continue to §7.1; warnings logged in impl-review.md |
| `BLOCKED` | At least one CRITICAL finding was `accept`-ed via override panel. Halt §6.8; surface remediation guidance to user; do NOT proceed to §7.1 until accepted CRITICALs are fixed and §6.8 re-runs clean. |

**CRITICAL findings — override panel:**

For each CRITICAL finding emitted by any of the 5 dispatched agents, the
orchestrator surfaces an `AskUserQuestion` panel before continuing:

```
[CRITICAL] <pattern>: <file:line> — impact: "<X>" — suggested fix: "<Y>"

Options:
  - accept   → block until fixed (BLOCKED verdict)
  - dispute  → false-positive; logged for next-run "convention learned"
  - defer    → create new sub-task in tasks.md; continue (with warning)
```

User decisions are recorded in `[task]-impl-review.md` under "User Override
Decisions". If ANY decision is `accept`, the verdict is BLOCKED and §6.8 halts
the milestone. Disputes accumulate across runs and are fed back to agent
prompts as "conventions learned for this project" — over time, false-positive
rate drops.

**Defer creates a new sub-task** in the current milestone (or a follow-up
milestone if specified):

```markdown
### Sub-step N.M: [DEFERRED from §6.8 impl review] <pattern> <file:line>
- Status: PENDING
- Mode: AFK
- Acceptance: Address the deferred CRITICAL finding from impl-review.md
- Source: [task]-impl-review.md User Override Decisions table row N
```

**Provenance entry (always emitted on completion):**

```
[<ISO>] §6.8 POST_IMPL_REVIEW — Audit-Profile: <profile> — \
        agents: <slate> — verdict: <PASS|BLOCKED|PASS_WITH_WARNINGS> — \
        findings: <N> CRITICAL / <M> WARNING / <P> INFO
```

**Bypass mechanisms (auditable):**

| Mechanism | Effect | Logged where |
|---|---|---|
| `AA_MA_HOOKS_DISABLE=1` | Master kill switch — skips ALL aa-ma gates incl. §6.8 | n/a (existing) |
| `AA_MA_AUDIT_BUDGET=off` | Skips §6.8 specifically | provenance.log: `AUDIT_BUDGET=off — bypassed §6.8` |
| `AA_MA_AUDIT_BUDGET=low` | Runs §6.8 in sequential/diff-only mode | provenance.log: `§6.8 invoked under AUDIT_BUDGET=low` |
| `TDD-Waiver: <canonical>` per milestone | Bypasses tdd-sequence-auditor only | impl-review.md (WAIVED verdict) |
| `[security-bypass: <reason>]` in commit msg | Bypasses upstream security-static-check.sh hook; semantic security-auditor agent still runs | commit message footer |
| `Created: < v0.8.0` cutover | Grandfathered — §6.8 does not fire at all | provenance.log: `§6.8 SKIPPED — pre-v0.8.0 plan` |

---

## 7. Finalization Protocol — MANDATORY

Before marking the milestone COMPLETE and creating git checkpoint, execute this 4-step finalization protocol. **No exceptions.**

### 7.1 Integrity Check (Checklist Verification)

**HARD Gate Check:** If the milestone has `Gate: HARD`, verify that a signed approval artifact exists in `[task]-context-log.md`:

```bash
# Check for HARD gate approval.
#
# Self-sufficient: this fence asks the Python gate itself rather than trusting
# ${GATE} / ${MILESTONE_TITLE} left over from §6.7. Run in a fresh shell, those
# are empty, `[[ "" == "HARD" ]]` is false, and the HARD gate is skipped with
# rc 0 and no output — which is precisely how the awk it replaced failed
# ("GATE was always empty; no HARD gate ever fired"). Two calls to one SSoT
# cannot drift; two awks could, which is why the old comment forbade this.
TASK_DIR=".claude/dev/active/${TASK_NAME}"
TASKS_MD="${TASK_DIR}/${TASK_NAME}-tasks.md"
for _cand in \
  "$(git rev-parse --show-toplevel 2>/dev/null)/claude-code/hooks/lib/aa-ma-parse.sh" \
  "${CLAUDE_HOME:-${HOME}/.claude}/hooks/lib/aa-ma-parse.sh"; do
  [[ -f "${_cand}" ]] && AA_MA_LIB="${_cand}" && break
done
# shellcheck source=/dev/null
. "${AA_MA_LIB:?aa-ma-parse.sh not found — run scripts/install.sh}"
GATE_KV=$(aa_ma_gate "${TASKS_MD}") || {
  echo "BLOCKED: §7.1 cannot read the milestone (gate rc $?):"
  printf '%s\n' "${GATE_KV}" | sed -n 's/^error=/  - /p'
  exit 1
}
MILESTONE_TITLE=$(printf '%s\n' "${GATE_KV}" | aa_ma_gate_field heading)
GATE=$(printf '%s\n' "${GATE_KV}" | aa_ma_gate_field gate)
if [[ -z "${MILESTONE_TITLE}" || -z "${GATE}" ]]; then
  echo "BLOCKED: §7.1 read an empty heading or gate — refusing on an empty subject."
  exit 1
fi
if [[ "$GATE" == "HARD" ]]; then
  # -F: the title is data, not a pattern. Titles routinely contain '.' (version
  # numbers), so a BRE match let "GATE APPROVAL: M4 v0X8X0" satisfy the gate for
  # "M4 v0.8.0". A leading '-' would make grep misparse its own argument.
  # The heading alone is not an approval: the artifact's `Decision:` line may
  # say REJECTED, and a heading-only grep waved that through. Require
  # `Decision: APPROVED` within the block (the spec's artifact is 4 lines).
  if ! grep -A8 -F -- "GATE APPROVAL: ${MILESTONE_TITLE}" \
       "${TASK_DIR}/${TASK_NAME}-context-log.md" | grep -qE '^-[[:blank:]]+(\*\*)?Decision:(\*\*)?[[:blank:]]+APPROVED'; then
    echo "BLOCKED: Gate: HARD requires signed approval in context-log.md"
    echo "Required format: ## [date] GATE APPROVAL: ${MILESTONE_TITLE}"
    echo "                 ... followed by a line: - Decision: APPROVED"
    exit 1
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

### 7.2.5 Post-Completion Validator Dispatch (RECOMMENDED)

After auto-updating docs (7.2) and before requesting user approval (7.3), dispatch `aa-ma-validator` agent to audit the just-updated artifacts. This catches drift WHILE the user is reviewing, so issues get remediated in-flight rather than post-archive.

**Spawn the validator** with `subagent_type: "aa-ma-validator"`, prompt focused on these 6 dimensions:

1. **Existence** — all files present and non-empty
2. **Plan completeness** — 11 AA-MA planning standard elements present
3. **Reference completeness** — immutable facts extracted
4. **HTP structure** — milestone COMPLETE, all sub-steps COMPLETE with Result Logs
5. **Cross-file consistency** — no contradictions
6. **Completeness-claim accuracy** — every COMPLETE status backed by evidence:
   - Result Logs populated (no `[pending at commit time]` placeholders)
   - Commit SHAs recorded in both tasks.md and provenance.log
   - provenance.log terminates with `MILESTONE_N COMPLETE` entry
   - All acceptance criteria verified with cited evidence

**Verdict handling:**
- **READY_FOR_ARCHIVE** → proceed to 7.3 User Authorization
- **WARNINGS_BUT_USABLE** → back-fill inline (Edit artifact files: replace placeholders, append missing events), then proceed to 7.3. Inline back-fill avoids a separate post-archive audit commit.
- **GAPS_REQUIRE_FIX** → HALT. Present findings to user. Remediate or defer archive.

**Rationale:** Catching placeholders and missing events during finalization is one commit cheaper than post-archive remediation. Confirmed by `go-biological-process-disease-support` 2026-04-20 sprint audit (3 WARN items that required back-fill commit `d424ef8`).

**If agent spawning unavailable:** skip this step, log `validator dispatch skipped — agent unavailable` to provenance.log, continue to 7.3. Do NOT block finalization on validator unavailability.

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

The milestone commit above is the hash the record must name, so it is
**final before this step runs** — never amended afterwards (L-018: `--amend`
rewrites the hash, and M1/M2 of `mattpocock-trio-adoption` each recorded a
pre-amend hash that no longer existed).

```bash
# Get commit info — HEAD is the milestone commit and stays that commit.
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
# A separate, small docs commit — NOT `--amend` (L-018). The milestone commit
# keeps the hash that provenance.log now names.
git add .claude/dev/active/$TASK_NAME/${TASK_NAME}-provenance.log
git commit -m "docs(aa-ma): provenance — MILESTONE COMPLETE $MILESTONE_ID ($COMMIT_HASH)

[AA-MA Plan] $TASK_NAME .claude/dev/active/$TASK_NAME"
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
### Sub-step N.M: Resolve [validation failure]
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
