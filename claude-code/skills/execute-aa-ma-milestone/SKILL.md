---
name: execute-aa-ma-milestone
description: "Executes a whole AA-MA milestone: every sub-step, the milestone-boundary gates (acceptance criteria, impact, tests, HARD-gate approval), then a commit. The default way to advance an AA-MA plan. Use when asked to run, continue or finish an AA-MA milestone, or whether a milestone can be marked COMPLETE."
---

# AA-MA Milestone Execution (Recommended Default)

You are executing a **complete milestone** from an AA-MA (Advanced Agentic Memory Architecture) tracked plan.

**Scope**: One milestone (## header) with all sub-tasks
**Validation**: Hybrid (guidance within, strict at boundary)
**Git**: Auto-commit + provenance logging at milestone completion

---

## 1. Locate Active Task & Pre-Execution Validation

See [pre-execution-validation.md](references/pre-execution-validation.md#1-locate-active-task--pre-execution-validation) — the Tier 1 existence check and the Tier 2 validator dispatch, with auto-recovery.

---

## 2. Priority Context Injection

See [context-and-todos.md](references/context-and-todos.md#2-priority-context-injection) — context-injection order, the loaded-context checks, the HTP-to-TodoWrite mapping and the quality triggers applied during execution.

---

## 3. Validate Loaded Context

See [context-and-todos.md](references/context-and-todos.md#3-validate-loaded-context) — context-injection order, the loaded-context checks, the HTP-to-TodoWrite mapping and the quality triggers applied during execution.

---

## 4. Parse HTP & Create TodoWrite Todos

See [context-and-todos.md](references/context-and-todos.md#4-parse-htp--create-todowrite-todos) — context-injection order, the loaded-context checks, the HTP-to-TodoWrite mapping and the quality triggers applied during execution.

---

## 4.5 Quality Standards (Actionable Triggers)

See [context-and-todos.md](references/context-and-todos.md#45-quality-standards-actionable-triggers) — context-injection order, the loaded-context checks, the HTP-to-TodoWrite mapping and the quality triggers applied during execution.

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

**First, §6.0:** run `scripts/code-intel-refresh.sh` (CODE_INTEL_REFRESH) — see [boundary-checks.md](references/boundary-checks.md#60-code-intel-refresh-code_intel_refresh); BLOCKED stops here.

### 6.1 Acceptance Criteria Verification

See [boundary-checks.md](references/boundary-checks.md#61-acceptance-criteria-verification) — acceptance-criteria verification, impact analysis, test execution, optional web verification and the simplification review (§6.1, §6.3–§6.6).

### 6.2 Dependency Verification (advisory — never blocks)

Nothing to enforce here. The next milestone's `Dependencies:` are reported when it
becomes ACTIVE — §5.1 step 3 runs `aa_ma_deps advisory` — and that report never stops
execution (map Ticket 16; `aa-ma-gate` does not read the field). Name the next
milestone's dependencies in the completion report so the user sees what comes next,
e.g. `Next: Milestone 3 — Dependencies: Milestone 2` (canonical form).

### 6.3 Impact Analysis Verification (REQUIRED)

See [boundary-checks.md](references/boundary-checks.md#63-impact-analysis-verification-required) — the index pre-check, `scripts/predicted-vs-actual.sh` (one `UNPREDICTED <path>` per changed file the Contract and its co-change partners did not predict; the list goes to §6.8's code-reviewer, never self-graded) and `Skill(impact-analysis)`.

### 6.4 Test Execution (if specified)

See [boundary-checks.md](references/boundary-checks.md#64-test-execution-if-specified) — acceptance-criteria verification, impact analysis, test execution, optional web verification and the simplification review (§6.1, §6.3–§6.6).

---

### 6.5 Optional Web Verification (gstack integration)

See [boundary-checks.md](references/boundary-checks.md#65-optional-web-verification-gstack-integration) — acceptance-criteria verification, impact analysis, test execution, optional web verification and the simplification review (§6.1, §6.3–§6.6).

### 6.6 Post-Milestone Simplification Review

See [boundary-checks.md](references/boundary-checks.md#66-post-milestone-simplification-review) — acceptance-criteria verification, impact analysis, test execution, optional web verification and the simplification review (§6.1, §6.3–§6.6).

---

### 6.7 Engineering Standards HARD Gate

Reference: `claude-code/rules/engineering-standards.md` (Themes 1, 4, 5, 6).
This gate is structural — it refuses to mark COMPLETE when any condition
fails. Independent of `Gate: SOFT|HARD` in tasks.md (that controls the approval
artifact in 7.1; THIS gate enforces engineering posture for every milestone).

**Conditions, evaluated in order** (two more fences follow: §13 diagram edges, then tests):

```bash
TASK_DIR=".claude/dev/active/${TASK_NAME}"
TASKS_MD="${TASK_DIR}/${TASK_NAME}-tasks.md"

# 1. AA-MA artifacts in sync (clean git for AA-MA files)
DIRTY_AA_MA=$(git status --porcelain "${TASK_DIR}/" | wc -l | tr -d ' ')
if [[ "${DIRTY_AA_MA}" -ne 0 ]]; then
  echo "BLOCKED: AA-MA artifacts have uncommitted changes."
  echo "Run sub-step Result Log discipline (L-080-082); commit and re-run."
  exit 1
fi

# --- Gate preamble: every reading below comes from the Python SSoT (ADR-0009) ---
# bash asks, Python answers; repo-local lib first. Rationale: references/gate-fences.md.
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

# One call answers every question; exit codes fail closed (0 ok · 1 no ACTIVE ·
# 2 unreadable · 3 ambiguous · 127 could not run — references/gate-fences.md).
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

# 3. Tests pass: fence 3 below runs Test-Command and writes TESTS_VERIFIED.
# 4. Impact: fence 4 below runs aa-ma-impact and writes IMPACT_VERIFIED.
CONDITIONS=2   # conditions 1 and 2 above

# 5. Critical-Path / Prototype-Required provenance evidence (CONDITIONAL)
# Absent field → skipped. Evidence greps are milestone-scoped (references/gate-fences.md):
#   [ts] CRITICAL_PATH_REVIEW — <milestone-title> — <value> — <evidence>
CRITICAL_PATH_TASKS=$(printf '%s\n' "${GATE_KV}" | aa_ma_gate_field critical_path)
if [[ -n "${CRITICAL_PATH_TASKS}" ]]; then
  CONDITIONS=$((CONDITIONS + 1))
  if ! grep -F -- "CRITICAL_PATH_REVIEW" "${TASK_DIR}/${TASK_NAME}-provenance.log" \
       | grep -qF -- "${MILESTONE_TITLE}"; then
    echo "BLOCKED: Milestone declares Critical-Path: ${CRITICAL_PATH_TASKS} but"
    echo "provenance.log has no CRITICAL_PATH_REVIEW entry naming this milestone."
    exit 1
  fi
fi

PROTOTYPE_TASKS=$(printf '%s\n' "${GATE_KV}" | aa_ma_gate_field prototype_required)
if [[ "${PROTOTYPE_TASKS}" == "YES" ]]; then
  CONDITIONS=$((CONDITIONS + 1))
  if ! grep -F -- "PROTOTYPE —" "${TASK_DIR}/${TASK_NAME}-provenance.log" \
       | grep -qF -- "${MILESTONE_TITLE}"; then
    echo "BLOCKED: the milestone or one of its sub-steps declares Prototype-Required: YES"
    echo "but provenance.log has no PROTOTYPE — <milestone heading> — <verdict> — verdict-changes-plan: YES|NO entry naming this milestone."
    exit 1
  fi
fi

echo "ENG-STANDARDS-GATE: PASS (${CONDITIONS} conditions checked; fences 2–4 follow)"
```

See [gate-fences.md](references/gate-fences.md#absent-field-semantic-fence-1) — absent `Critical-Path:` / `Prototype-Required:` fields skip their check.

**Bypass:** to override this gate (e.g. for diagnostic runs), set
`AA_MA_HOOKS_DISABLE=1` in the environment. The gate honors the master kill
switch but logs the override to provenance.log:
`[ts] ENG_STANDARDS_GATE: BYPASSED via AA_MA_HOOKS_DISABLE`.

**§13 sigil edges verified — HARD, opt-in** (fence 2, ADR-0015): a plan whose §13 carries a sigil edge
must have every edge hold in the code. It stays the second fence (`test_diagram_verified.bats`).

See [gate-fences.md](references/gate-fences.md#fence-2--13-sigil-edges-verified) — the lint verdicts, what still passes, and why the fence order is fixed.

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

**Tests verified — HARD** (fence 3): runs the merge-base `Test-Command:` (default `uv run pytest`);
appends `[ts] TESTS_VERIFIED — <milestone heading> — passed=N cmd=<TEST_CMD>` only on rc 0 plus a
pass-count summary. A failure is BLOCKED, never retried. Long suite: raise `AA_MA_TEST_TIMEOUT` (540 s), run in background.

See [gate-fences.md](references/gate-fences.md#fence-3--tests_verified) — inputs, PASS rules, `Test-Command-Pass-Regex:`, the `none` opt-out and its approval.

```bash
# Fence 3 — TESTS_VERIFIED. All logic is in the skill's scripts/tests-verified.sh (bats-tested).
_s=skills/execute-aa-ma-milestone/scripts/tests-verified.sh
TV=""   # never run an inherited TV
# why: stderr dropped — outside a repo the first candidate is simply absent
for _tv in "$(git rev-parse --show-toplevel 2>/dev/null)/claude-code/${_s}" \
           "${CLAUDE_HOME:-${HOME}/.claude}/${_s}"; do
  [[ -f "${_tv}" ]] && TV="${_tv}" && break
done
bash "${TV:?tests-verified.sh not found — run scripts/install.sh}" "${TASK_NAME:-}"
```

**Impact verified — HARD** (fence 4): every change predicted by the Contract, or explained;
appends `[ts] IMPACT_VERIFIED — <milestone heading> — changed=N predicted=P cochange=C unexplained=0`.
See [gate-fences.md](references/gate-fences.md#fence-4--impact_verified) and [impact-gate.md](references/impact-gate.md) (how to read a BLOCKED report).

```bash
# Fence 4 — IMPACT_VERIFIED. All logic is in the skill's scripts/impact-verified.sh (bats-tested).
_s=skills/execute-aa-ma-milestone/scripts/impact-verified.sh
IV=""   # never run an inherited IV
# why: stderr dropped — outside a repo the first candidate is simply absent
for _iv in "$(git rev-parse --show-toplevel 2>/dev/null)/claude-code/${_s}" \
           "${CLAUDE_HOME:-${HOME}/.claude}/${_s}"; do
  [[ -f "${_iv}" ]] && IV="${_iv}" && break
done
bash "${IV:?impact-verified.sh not found — run scripts/install.sh}" "${TASK_NAME:-}"
```

---

### 6.8 Post-Impl Adversarial Review (NEW in v0.8.0)

See [post-impl-review.md](references/post-impl-review.md#68-post-impl-adversarial-review-new-in-v080) — when §6.8 fires, how Skill(verify-impl) dispatches the audit agents (ADR-0005), verdicts, the CRITICAL override panel and bypasses.

**A BLOCKED verdict stops the milestone here:** do not continue to §7.1 until every accepted CRITICAL is fixed and §6.8 re-runs clean.

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
  # Block-scoped and exact (aa-ma-parse.sh): the title is a string, never a pattern
  # ("M4 v0X8X0" is not "M4 v0.8.0"); the LAST block for it must say Decision: APPROVED,
  # and a REJECTED block can no longer borrow the next block's APPROVED (M9 §6.6).
  if ! aa_ma_has_gate_approval "${TASK_DIR}/${TASK_NAME}-context-log.md" "${MILESTONE_TITLE}"; then
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

See [finalization.md](references/finalization.md#72-documentation-auto-update) — the doc auto-update, validator dispatch, user approval and status change that follow §7.1.

### 7.2.5 Post-Completion Validator Dispatch (RECOMMENDED)

See [finalization.md](references/finalization.md#725-post-completion-validator-dispatch-recommended) — the doc auto-update, validator dispatch, user approval and status change that follow §7.1.

### 7.3 User Authorization (Approval Gate)

See [finalization.md](references/finalization.md#73-user-authorization-approval-gate) — the doc auto-update, validator dispatch, user approval and status change that follow §7.1.

**Never mark the milestone COMPLETE without the user's explicit approval through `AskUserQuestion`.**

### 7.4 Transparent Status Change

See [finalization.md](references/finalization.md#74-transparent-status-change) — the doc auto-update, validator dispatch, user approval and status change that follow §7.1.

---

## 8. Git Checkpoint Creation (Auto-commit)

See [checkpoint-and-errors.md](references/checkpoint-and-errors.md#8-git-checkpoint-creation-auto-commit) — the milestone commit and provenance entries (§8), status update (§9), completion report (§10), BLOCKED handling (§11), token use and rollback.

**Read it to the end:** after the commit, §9 sets the milestone COMPLETE and §10 reports it; if any check failed, §11 sets it BLOCKED, adds a remediation sub-task and HALTs instead.

---

**End of execute-aa-ma-milestone.md**
