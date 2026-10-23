# Milestone boundary checks — code-intel refresh, acceptance-criteria verification, impact analysis, test execution, optional web verification and the simplification review (§6.0, §6.1, §6.3–§6.6).

## Contents

  - [6.0 Code-intel refresh (CODE_INTEL_REFRESH)](#60-code-intel-refresh-code_intel_refresh)
  - [6.1 Acceptance Criteria Verification](#61-acceptance-criteria-verification)
  - [6.3 Impact Analysis Verification (REQUIRED)](#63-impact-analysis-verification-required)
  - [6.4 Test Execution (if specified)](#64-test-execution-if-specified)
  - [6.5 Optional Web Verification (gstack integration)](#65-optional-web-verification-gstack-integration)
  - [6.6 Post-Milestone Simplification Review](#66-post-milestone-simplification-review)

### 6.0 Code-intel refresh (CODE_INTEL_REFRESH)

Run first, so §6.3's impact analysis and §6.7's diagram fence read indexes that
match the code (report 03 T6). It refreshes codemem (`refresh` + `refresh-commits`)
and the graphify code graph (`graphify update .`, code-only) through the same
flock-serialised worker as the post-commit step, then appends one line naming
the **pre-commit** HEAD — a file cannot name the commit that contains it:

```
[ts] CODE_INTEL_REFRESH — <milestone heading> — codemem=<sha|skipped(codemem not installed)> graphify=<sha|WARN reason>
```

```bash
# The installed copy only: a repo-committed claude-code/ must never run as the gate.
CIR="${CLAUDE_HOME:-${HOME}/.claude}/skills/execute-aa-ma-milestone/scripts/code-intel-refresh.sh"
[[ -f "${CIR}" ]] || { echo "BLOCKED: ${CIR} not found — run scripts/install.sh."; exit 1; }
bash "${CIR}" "${TASK_NAME:-}"
```

- graphify failing or absent: `graphify=WARN …`, never blocks (graphify is leads-only).
- codemem installed: a missing index is built first, and an index that does not
  reach HEAD (a failed build included) is **BLOCKED** (exit 1) — run `codemem build`
  and re-run; gates must not read a stale index. No codemem binary at all:
  `codemem=skipped(codemem not installed)`. The index lives in codemem's cache dir
  (`${XDG_CACHE_HOME:-~/.cache}/codemem/<sha256(realpath repo)>/`, or `$CODEMEM_DB`'s
  dir), not the repo (M16).
- `--dry-run` refreshes and prints the line without appending it.

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

### 6.3 Impact Analysis Verification (REQUIRED)

**Before completing milestone, verify no breaking changes introduced:**

**Index-enhanced (codemem by default; PROJECT_INDEX.json is codemem's fallback when present):**
Before invoking the full impact-analysis skill, run a quick pre-check using the index:
- For each modified file's key symbols, ask for its transitive callers: codemem `who_calls(name, max_depth=2)`
  (with only PROJECT_INDEX.json, not codemem, the same question is its `blast_radius(symbol, depth=2)` —
  codemem's `blast_radius` returns callees instead)
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
