---
name: plan-verification
description: "Verifies an AA-MA plan from 6 adversarial angles (facts, assumptions, impact, acceptance criteria, implementation barriers, domain risk) and lists its defects. Use when asked to verify, check or review an AA-MA plan, and at aa-ma-plan Phase 4.5."
---

# Plan Verification Skill

Verify AA-MA plans against external reality using 6 structured verification angles before plans reach execution.

<EXTREMELY-IMPORTANT>
This skill exists because plans that look internally consistent can contain factual errors, unverified assumptions, and implementation barriers that only surface after 3+ rounds of manual double-checking (L-054, L-058, L-059, L-067, L-069). Every angle catches a categorically different class of error. Do NOT skip angles or reduce scope.
</EXTREMELY-IMPORTANT>

## When to Use

- **Automatically:** Invoked by Phase 4.5 of aa-ma-plan workflow
- **Manually:** Via `/verify-plan [task-name]` command
- **Re-run:** After plan revision to verify fixes

## Inputs Required

1. **Plan text** — full plan content (from plan.md or in-memory)
2. **Project root** — path to the project being planned for
3. **Mode** — `automated` | `interactive` (set by caller or prompted)
4. **Previous findings** (optional) — from prior verification runs, to avoid re-flagging

## Severity Classification

| Severity | Definition | Automated Mode | Interactive Mode |
|----------|-----------|---------------|-----------------|
| CRITICAL | Plan claim factually wrong, or proposed change would break something | BLOCKS artifact creation | Report only |
| WARNING | Assumption unverified, criteria vague, or impact unclear | Report only | Report only |
| INFO | Suggestion for improvement, minor gap | Report only | Report only |

## Execution Protocol

### Step 1: Mode Selection

If not pre-selected by the calling command, prompt:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PLAN VERIFICATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Run verification?
  [A] Automated — CRITICALs block, WARNINGs report
  [I] Interactive — All findings report-only
  [S] Skip — No verification
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

If user selects **S (Skip)**, set verification status to SKIPPED and return immediately.

### Step 2: Extract Plan Claims

Before dispatching agents, parse the plan to extract:
- **File paths** referenced (create/modify/delete)
- **Class/function names** referenced
- **API endpoints/URLs** referenced
- **Library names and versions** referenced
- **Config values** referenced
- **Acceptance criteria** (all of them, with their milestone/step IDs)
- **Assumptions** (explicit and implicit)
- **Dependencies** listed

Format these as structured lists to feed into agent prompts.

### Step 3: Wave 1 — Parallel Verification (4 agents)

Dispatch all 4 agents simultaneously using the Agent tool. Each agent runs independently.

---

#### Angle 1: Ground-Truth Audit

See [angles-1-5.md](references/angles-1-5.md) — what each Wave 1 agent (ground truth, assumptions, impact, falsifiability) and the Wave 2 fresh-agent simulation checks, and how it reports.

---

#### Angle 2: Assumption Extraction & Challenge

See [angles-1-5.md](references/angles-1-5.md) — what each Wave 1 agent (ground truth, assumptions, impact, falsifiability) and the Wave 2 fresh-agent simulation checks, and how it reports.

---

#### Angle 3: Impact Analysis on Proposed Changes

See [angles-1-5.md](references/angles-1-5.md) — what each Wave 1 agent (ground truth, assumptions, impact, falsifiability) and the Wave 2 fresh-agent simulation checks, and how it reports.

---

#### Angle 4: Acceptance Criteria Falsifiability

See [angles-1-5.md](references/angles-1-5.md) — what each Wave 1 agent (ground truth, assumptions, impact, falsifiability) and the Wave 2 fresh-agent simulation checks, and how it reports.

---

### Step 4: Consolidate Wave 1 Results

Wait for all 4 agents to complete. Collect results and build summary:

```
wave1_findings = {
    "CRITICAL": [list of all CRITICALs from angles 1-4],
    "WARNING": [list of all WARNINGs from angles 1-4],
    "INFO": [list of all INFOs from angles 1-4],
    "angles_completed": [1, 2, 3, 4]
}
```

Display interim progress:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WAVE 1 COMPLETE (4/6 angles)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CRITICAL: [N] | WARNING: [N] | INFO: [N]
Proceeding to Wave 2...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Step 5: Wave 2 — Sequential Verification (2 agents)

Wave 2 agents receive Wave 1 findings to avoid re-flagging known issues.

---

#### Angle 5: Fresh-Agent Simulation

See [angles-1-5.md](references/angles-1-5.md) — what each Wave 1 agent (ground truth, assumptions, impact, falsifiability) and the Wave 2 fresh-agent simulation checks, and how it reports.

---

#### Angle 6: Specialist Domain Audit

**What it catches:** Domain-specific risks that generalist reviewers miss (L-068)

**Specialist detection:** Scan the plan text for keywords to determine which specialists to dispatch:

| Plan Contains | Specialist | Focus Areas |
|---------------|-----------|-------------|
| `BaseModel`, `Pydantic`, `model_dump`, `schema` | Pydantic v2 Auditor | Discriminators, `extra` config, serialization round-trip, `from __future__ import annotations` risk |
| `httpx`, `requests`, `API`, `endpoint`, `auth`, `header` | API Contract Auditor | Auth scheme accuracy, base URLs, rate limits, error codes, retry strategy |
| `schema`, `field`, `column`, `table`, `migration` | Schema Completeness Auditor | Field count vs source, type accuracy, nullable handling, default values |
| `sqlalchemy`, `alembic`, `migration`, `database` | Migration Auditor | State machine completeness, rollback safety, data loss risk |
| `auth`, `secret`, `token`, `permission`, `credential` | Security Auditor | OWASP top 10, credential handling, injection risks |
| (always evaluated — not keyword-driven) | Engineering Standards Auditor | Element #12 declaration present; themes from `claude-code/rules/engineering-standards.md` claimed-vs-applied; `Critical-Path:`/`Prototype-Required:` flag values valid (canonical enum); Architecture View present or validly waived (`Diagram-Waiver` canonical) Contract block per code milestone, and Contract paths drawn in §13 (checks #6/#7, check #8 WARNING; plans `Created:` ≥ 2026-09-11) |

Dispatch 1-3 specialists based on detection. If no domain keywords found, skip the keyword-driven dispatch (report as "No specialist domains detected") — but the **Engineering Standards Auditor always runs** regardless of keyword detection (see structural check below).

**Engineering Standards Structural Check (always runs):**

Independent of the keyword-driven specialist dispatch above, Angle 6 always
evaluates these structural conditions against the plan:

1. **Element #12 present.** Plan contains an "Engineering Standards Declaration"
   section listing which themes from `claude-code/rules/engineering-standards.md`
   apply, with one-sentence rationale per theme.
2. **Critical-Path values are canonical.** Any `Critical-Path:` field must parse
   against `CANONICAL_CRITICAL_PATHS`. Novel values are CRITICAL findings — add
   new values via plan + ADR, not ad-hoc. **Run the parser; do not eyeball the
   list.** The canonical values live in code and in
   `claude-code/rules/engineering-standards.md` §1 — deliberately not repeated
   here, because a third prose copy is what drifts:

   ```bash
   # The Python SSoT gate validates every milestone's own fields file-wide
   # (Critical-Path, Gate, Mode, Prototype-Required, Audit-Profile) on any
   # call and exits 2 with one `error=` line per refusal. The previous
   # snippet piped an undefined "$MILESTONE_BLOCK" into the parser, which
   # read an empty block as OK — the check passed vacuously.
   # TASK_NAME is the `/verify-plan [task-name]` argument (or the task being
   # planned). Phase 4.5 of /aa-ma-plan runs BEFORE Phase 5 writes tasks.md,
   # so on a fresh plan the file does not exist yet — that is a SKIP, not a
   # CRITICAL; re-run /verify-plan once the artifacts exist.
   TASKS_MD=".claude/dev/active/${TASK_NAME}/${TASK_NAME}-tasks.md"
   if [ ! -f "$TASKS_MD" ]; then
     echo "SKIP: $TASKS_MD not yet written (Phase 5) — re-run /verify-plan after artifacts exist"
   else
   for _cand in \
     "$(git rev-parse --show-toplevel 2>/dev/null)/claude-code/hooks/lib/aa-ma-parse.sh" \
     "${CLAUDE_HOME:-${HOME}/.claude}/hooks/lib/aa-ma-parse.sh"; do
     [ -f "${_cand}" ] && AA_MA_LIB="${_cand}" && break
   done
   # shellcheck source=/dev/null
   . "${AA_MA_LIB:?aa-ma-parse.sh not found — run scripts/install.sh}"
   GATE_KV=$(aa_ma_gate "$TASKS_MD"); rc=$?
   case $rc in
     0|1) echo "OK" ;;                       # 1 = no ACTIVE yet, normal pre-execution
     2)   echo "CRITICAL: unreadable fields:"; printf '%s\n' "$GATE_KV" | sed -n 's/^error=/  - /p' ;;
     3)   echo "CRITICAL: ambiguous:";        printf '%s\n' "$GATE_KV" | sed -n 's/^error=/  - /p' ;;
     *)   echo "CRITICAL: aa-ma-gate did not run (rc $rc) — cannot verify, refusing" ;;
   esac
   fi
   ```
3. **Theme claims are not contradictory.** When element #12 declares Theme 2
   (Development Principles → TDD), tasks producing code must carry test sub-tasks.
4. **Audit-Profile present per milestone (v0.8.0+).** For plans with
   `Created:` on-or-after the v0.8.0 release tag commit date, every milestone
   in `[task]-tasks.md` MUST declare `Audit-Profile:` with one of the 5
   canonical values: `full` | `code-only` | `docs-only` | `infra` | `custom`.
   Absent field on a post-v0.8.0 plan is a CRITICAL finding. Novel values are
   CRITICAL findings — add new values via plan + ADR (per ADR-0005). The
   field controls Phase 6.8 Post-Impl Adversarial Review trigger logic.
5. **TDD-Waiver values are canonical when present.** Any `TDD-Waiver:` field
   uses one of the 5 canonical values: `refactor` | `docs-only` | `prototype` |
   `hotfix-emergency` | `tooling-config`. Novel values are CRITICAL findings.
   Field-absence is permitted (most milestones have no waiver). Per ADR-0005.
6. **Architecture View present or validly waived (v0.12.0+).** For plans `Created:`
   on-or-after **2026-09-11**: either `## 13. Architecture View` exists with a
   `### Component view` containing a non-empty ```` ```mermaid ```` fence (plus a
   `### Flow view` when any milestone carries `Critical-Path:`), or the front-matter
   carries `**Diagram-Waiver:** <value>` with a canonical value (`none`, `docs-only`,
   `config-only`, `single-file`). A waiver alongside any milestone whose
   `Audit-Profile` ∈ {full, code-only, infra} is CRITICAL. Novel waiver value is
   CRITICAL. Run the lint rather than eyeballing the section:
   ```bash
   # Resolve the aa-ma-forge checkout from this skill's own installed symlink
   # (install.sh symlinks claude-code/skills/* into ~/.claude/skills/).
   AA_MA_ROOT=$(cd "$(dirname "$(readlink -f ~/.claude/skills/plan-verification/SKILL.md)")/../../.." && pwd)
   uv run --project "$AA_MA_ROOT" aa-ma-lint-views <plan.md> --repo-root <project-root>
   ```
   Exit 1 → one CRITICAL per finding line (`file:line: CODE: message`), including
   `PHANTOM_EDGE` (an `-->|"@import"|` / `-->|"@call"|` claim the codemem graph does not
   hold) and `LABEL_UNKNOWN` (a typo'd `@` sigil); a `file:line: UNKNOWN: reason` line is
   INFO — an unevaluable sigil claim (`(new)` endpoint, no/stale index, plugin sigil) that
   never sets the exit code and is never read as PASS;
   the `sigils: …` line is a count read by `/execute-aa-ma-milestone` §6.7 (ADR-0015) —
   informational at planning time;
   `render: FAIL` → CRITICAL (a mermaid parse error); `render: UNKNOWN` → INFO
   (no working `mmdc`/Chromium — never read UNKNOWN as PASS, L-012); exit 2 →
   CRITICAL (usage: plan path missing or not a file). Before `tasks.md` exists
   the lint reads `### Milestone` blocks from the plan itself; pass `--tasks`
   once it does.
7. **Contract block per code milestone (v0.12.0+).** Every milestone with
   `Audit-Profile` ∈ {full, code-only, infra} has a `#### Contract` heading followed
   by at least one fenced block. Missing → CRITICAL; the fresh-agent simulation
   (Angle 5) treats an unpinned signature as a WARNING at minimum.
8. **Contract paths drawn in §13 (v0.12.0+).** Every path a milestone's `#### Contract`
   block creates or modifies — `Create` / `Modify` rows and template `# file: <path>`
   lines — is covered by a §13 node: one naming the path, a directory above it, or the
   planned `(new)` file. Exempt: `Test` / `Verify` rows, paths under `tests/` and `docs/`,
   root docs (README, CHANGELOG, SECURITY, CONTEXT), and dependency manifests / lockfiles
   (`pyproject.toml`, `package.json`, `*.lock`). Planning time only — the same lint as
   check #6 with its opt-in flag, which nothing at execution time passes:
   ```bash
   AA_MA_ROOT=$(cd "$(dirname "$(readlink -f ~/.claude/skills/plan-verification/SKILL.md)")/../../.." && pwd)
   out=$(uv run --project "$AA_MA_ROOT" aa-ma-lint-views <plan.md> --repo-root <project-root> --coverage)
   rc=$?
   case $rc in
     0|1) printf '%s\n' "$out" | grep ': UNDRAWN_PATH: ' || echo "check 8: every Contract path is drawn" ;;
     *)   echo "CRITICAL: check 8 could not run (rc $rc) — never read as clean"
          printf '%s\n' "$out" | grep ': UNKNOWN: ' ;;
   esac
   ```
   One WARNING per `file:line: UNDRAWN_PATH: <path>: …` line — draw the path (the
   `/aa-ma-plan` Step 4.2b seed already holds the existing files), or say in the plan why
   it stays undrawn. Any other exit code (a crash is `UNKNOWN`, exit 2) is CRITICAL: a check
   that did not run is not a clean one. Other finding lines repeat check #6 and are read there.

Parsers for checks #2, #4, #5 and #6 live in `src/aa_ma/plan_parsers.py`
(`parse_critical_path`, `parse_audit_profile`, `parse_tdd_waiver`,
`parse_diagram_waiver`, and their `CANONICAL_*` frozensets); check #6/#7
structure is `aa_ma.render.mermaid_lint` (`CODE_AUDIT_PROFILES` decides which
milestones need a Contract block). Each parser returns `(value, is_valid, error)`;
the audit reports `CRITICAL` when `is_valid is False`.

**Grandfathering (CEO-4):**
- Checks #1, #2, #3 fire only for plans whose `Created: YYYY-MM-DD`
  front-matter is on-or-after the v0.5.0 release date.
- Check #4 (Audit-Profile presence) fires only for plans whose `Created:`
  is on-or-after the v0.8.0 release tag commit date.
- Check #5 (TDD-Waiver canonical values) fires for any plan with a
  `TDD-Waiver:` field, regardless of `Created:` date — validating values
  that have been written cannot regress an older plan.
- Pre-v0.5.0 plans emit `[INFO] Pre-v0.5.0 plan — engineering-standards
  check skipped` and continue. Pre-v0.8.0 plans emit
  `[INFO] Pre-v0.8.0 plan — Audit-Profile check skipped`.
- Checks #6, #7 and #8 fire only for plans whose `Created:` is on-or-after the
  literal date **2026-09-11** (v0.12.0 cutover, written as a date so the check
  never depends on a release tag); earlier plans emit
  `[INFO] Pre-2026-09-11 plan — Architecture View check skipped`.
- Plans missing `Created:` are grandfathered (absence → pre-cutover).
- Detection logic (regex parse of `Created:` field + comparison to release
  dates) lives inside the Engineering Standards Auditor agent prompt below.

**Agent dispatch (per specialist):**
```
Agent tool:
  subagent_type: general-purpose
  description: "[Specialist type] domain audit"
  prompt: |
    You are a [SPECIALIST TYPE] expert reviewing this plan for
    domain-specific risks that generalist reviewers typically miss.

    PROJECT ROOT: [project_root]

    FULL PLAN TEXT:
    [plan_text]

    ALREADY KNOWN ISSUES (do NOT re-flag these):
    [wave1_findings + angle5_findings summary]

    YOUR DOMAIN FOCUS — [SPECIALIST TYPE]:
    [domain-specific checklist items from table above]

    Review the plan ONLY through your specialist lens.
    Read actual project files as needed to verify domain-specific claims.

    OUTPUT FORMAT:
    - [CRITICAL] [domain] risk: "[description with evidence]"
    - [WARNING] [domain] concern: "[description]"
    - [INFO] [domain] suggestion: "[description]"

    Do NOT write any code. Read files and analyze.
```

---

### Step 6: Consolidate All Findings

Merge all 6 angle reports into a unified findings list:

```
all_findings = {
    "CRITICAL": [all CRITICALs from angles 1-6],
    "WARNING": [all WARNINGs from angles 1-6],
    "INFO": [all INFOs from angles 1-6]
}
```

De-duplicate findings that appear in multiple angles (keep the most specific version).

### Step 7: Apply Severity Gate

**Automated mode:**
- If `len(CRITICAL) > 0`: result = **FAIL** — plan must be revised
- If `len(CRITICAL) == 0 and len(WARNING) > 0`: result = **PASS WITH WARNINGS**
- If `len(CRITICAL) == 0 and len(WARNING) == 0`: result = **PASS**

**Interactive mode:**
- Always result = **PASS** (or PASS WITH WARNINGS if any findings)
- All findings presented as report for user decision

### Step 8: Generate Verification Report

Write `[task]-verification.md` in the AA-MA task directory (or in-memory if artifacts don't exist yet):

```markdown
# Verification Report: [task-name]
Generated: [ISO-8601 timestamp] | Mode: [automated|interactive] | Revision: [N]

## Summary
- CRITICAL: [N] findings ([M] resolved)
- WARNING: [N] findings
- INFO: [N] findings
- Overall: [PASS | FAIL | PASS WITH WARNINGS | SKIPPED]

## Angle 1: Ground-Truth Audit
### Findings
[findings from angle 1, grouped by severity]
[or "No findings — all claims verified."]

## Angle 2: Assumption Extraction & Challenge
### Assumptions Identified
[numbered list of assumptions with status]

## Angle 3: Impact Analysis on Proposed Changes
### Files Affected
[findings per file with risk level]

## Angle 4: Acceptance Criteria Falsifiability
### Criteria Audit
[per-criterion findings]
### Score: [N]/[M] falsifiable ([X]%)

## Angle 5: Fresh-Agent Simulation
### Implementation Barriers
[findings from fresh-agent perspective]

## Angle 6: Specialist Domain Audit
### Specialists Dispatched: [list or "None — no domain keywords detected"]
[per-specialist findings]

## Revision History
- v[N]: [date] — [summary: N CRITICAL, N WARNING → result]
```

### Step 9: Display Results

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
VERIFICATION COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Mode: [Automated | Interactive]
Angles: 6/6 complete
CRITICAL: [N] | WARNING: [N] | INFO: [N]
Result: [PASS | FAIL | PASS WITH WARNINGS]

[If FAIL in automated mode:]
Plan has [N] CRITICAL findings. Revision required.
CRITICALs:
  1. [brief description]
  2. [brief description]

[If PASS WITH WARNINGS:]
[N] warnings noted — review verification report for details.

Report: .claude/dev/active/[task]/[task]-verification.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```


## Reference Files

For detailed patterns and code examples, see [references/verification-standards.md](references/verification-standards.md).
