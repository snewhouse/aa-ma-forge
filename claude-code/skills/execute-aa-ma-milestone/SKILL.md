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

### 6.1 Acceptance Criteria Verification

See [boundary-checks.md](references/boundary-checks.md#61-acceptance-criteria-verification) — acceptance-criteria verification, impact analysis, test execution, optional web verification and the simplification review (§6.1, §6.3–§6.6).

### 6.2 Dependency Verification (advisory — never blocks)

Nothing to enforce here. The next milestone's `Dependencies:` are reported when it
becomes ACTIVE — §5.1 step 3 runs `aa_ma_deps advisory` — and that report never stops
execution (map Ticket 16; `aa-ma-gate` does not read the field). Name the next
milestone's dependencies in the completion report so the user sees what comes next,
e.g. `Next: Milestone 3 — Dependencies: Milestone 2` (canonical form).

### 6.3 Impact Analysis Verification (REQUIRED)

See [boundary-checks.md](references/boundary-checks.md#63-impact-analysis-verification-required) — acceptance-criteria verification, impact analysis, test execution, optional web verification and the simplification review (§6.1, §6.3–§6.6).

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
