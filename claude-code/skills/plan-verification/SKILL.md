---
name: plan-verification
description: Adversarial verification of AA-MA plans using 6 independent angles. Catches factual errors, unverified assumptions, impact gaps, vague criteria, implementation barriers, and domain-specific risks before plans reach execution. Invoked by Phase 4.5 of aa-ma-plan and standalone /verify-plan command.
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

**What it catches:** Plan claims that contradict actual code, APIs, specs, configs (L-054, L-069)

**Agent dispatch:**
```
Agent tool:
  subagent_type: Explore
  description: "Ground-truth audit of plan"
  prompt: |
    You are a ground-truth auditor. Your ONLY job is to verify that every
    factual claim in this plan matches reality in the actual codebase.

    PROJECT ROOT: [project_root]

    PLAN CLAIMS TO VERIFY:
    File paths: [extracted list]
    Class/function names: [extracted list]
    API endpoints: [extracted list]
    Config values: [extracted list]
    Library versions: [extracted list]

    VERIFICATION PROTOCOL:
    For EACH claim above:
    1. Read the actual file or source using Read/Grep/Glob tools
    2. Compare the plan's claim against what actually exists
    3. Classify as:
       - MATCH: Plan claim matches reality (provide evidence)
       - CONTRADICTION: Plan claim conflicts with reality (provide both)
       - UNVERIFIABLE: Cannot find evidence for or against

    OUTPUT FORMAT (one per claim):
    - [CRITICAL] Claim: "X" | Reality: "Y" | Source: file:line
    - [WARNING] Claim: "X" | Cannot verify — no evidence found
    - [OK] Claim: "X" | Confirmed at file:line

    Be thorough. Read actual files. Do NOT guess or infer.
    Do NOT write any code. Only read and compare.
```

---

#### Angle 2: Assumption Extraction & Challenge

**What it catches:** Unstated assumptions that could be wrong (L-054, L-055)

**Agent dispatch:**
```
Agent tool:
  subagent_type: general-purpose
  description: "Assumption audit of plan"
  prompt: |
    You are a Socratic assumption auditor. Your job is to find every
    assumption in this plan — both stated and unstated — and challenge each one.

    PROJECT ROOT: [project_root]

    FULL PLAN TEXT:
    [plan_text]

    EXTRACTION PROTOCOL:
    1. Read the plan carefully
    2. For each statement, ask: "What must be true for this to work?"
    3. Categorize assumptions as EXPLICIT (plan says "we assume X") or
       IMPLICIT (unstated but required)

    CHALLENGE PROTOCOL:
    For EACH assumption found:
    1. State the assumption clearly in one sentence
    2. Search for evidence: read actual files, configs, docs in the project
    3. Ask: "What happens if this assumption is wrong?"
    4. Classify:
       - VERIFIED: Evidence found (cite file:line)
       - UNVERIFIED: No evidence found for or against
       - CONTRADICTED: Evidence found AGAINST this assumption

    OUTPUT FORMAT:
    - [VERIFIED] "assumption text" — evidence: file:line
    - [WARNING] "assumption text" — no evidence found, risk if wrong: [description]
    - [CRITICAL] "assumption text" — contradicted by: file:line, actual: "Y"

    Do NOT write any code. Read files to find evidence.
```

---

#### Angle 3: Impact Analysis on Proposed Changes

**What it catches:** Ripple effects the plan doesn't account for (L-037)

**Agent dispatch:**
```
Agent tool:
  subagent_type: general-purpose
  description: "Impact analysis of plan"
  prompt: |
    You are an impact analyst. For each file this plan proposes to
    create, modify, or delete, assess the ripple effects that the
    plan may not account for.

    PROJECT ROOT: [project_root]

    FILES THE PLAN PROPOSES TO CHANGE:
    [extracted file paths with proposed change descriptions]

    For EACH file, run the 5-point impact check:

    1. UPSTREAM: Who imports or calls this file?
       - Use Grep to search for imports of this module
       - Count callers
    2. DOWNSTREAM: What does this file depend on?
       - Read imports in the file
    3. CONTRACTS: What function signatures or class interfaces would change?
       - Compare plan's proposed changes against current signatures
    4. TESTS: What tests cover this file?
       - Search for test files that import or reference it
    5. SIDE EFFECTS: Any state mutations, IO operations, or global changes?

    RISK CLASSIFICATION:
    - LOW: 0-2 callers, no contract change
    - MEDIUM: 3-5 callers, manageable contract change
    - HIGH: 6+ callers, breaking contract change, or unclear effects

    OUTPUT FORMAT:
    - [CRITICAL] file.py — HIGH risk: N callers, contract change, plan doesn't address
    - [WARNING] file.py — MEDIUM risk: N callers, suggest adding mitigation to plan
    - [OK] file.py — LOW risk: N callers, plan accounts for changes

    Also flag: files the plan SHOULD modify but doesn't mention (discovered via
    upstream/downstream analysis).

    Do NOT write any code. Only analyze impact.
```

---

#### Angle 4: Acceptance Criteria Falsifiability

**What it catches:** Vague/untestable criteria that anything can "pass" (L-059)

**Agent dispatch:**
```
Agent tool:
  subagent_type: general-purpose
  description: "Criteria falsifiability audit"
  prompt: |
    You are a test engineer auditing acceptance criteria for falsifiability.
    A criterion is falsifiable if you can write a concrete test assertion for it.

    ACCEPTANCE CRITERIA FROM PLAN:
    [all extracted criteria with their milestone/step IDs]

    AUDIT PROTOCOL:
    For EACH criterion:
    1. Attempt to write a single-line pytest assertion that would verify it
       - If YES: Write the assertion as proof of falsifiability
       - If NO: Flag as unfalsifiable and explain why
    2. Check for banned vague terms:
       "works correctly", "performs well", "is fast", "looks good",
       "is complete", "is stable", "is secure", "handles edge cases gracefully",
       "as expected", "appropriate", "reasonable", "sufficient", "properly",
       "and so on", "etc", "various", "some", "several", "many", "few"
    3. Is the criterion measurable? (specific number, state, boolean, or output)
    4. If unfalsifiable, suggest a concrete rewrite

    OUTPUT FORMAT:
    - [OK] M1-S2: "response returns status 200" → assert response.status_code == 200
    - [WARNING] M2-S1: "handles edge cases gracefully" → unfalsifiable
      Suggested: "given empty input, raises ValueError with message 'input required'"
    - [WARNING] M3-S4: contains banned term "works correctly"
      Suggested: "given valid config, returns parsed Config object with N fields"

    SUMMARY:
    Falsifiable: N/M criteria (target: 100%)
    Banned terms found: [list]

    Do NOT write any code beyond example assertions.
```

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

**What it catches:** Implementation barriers invisible to context-aware reviewers (L-067)

**Agent dispatch:**
```
Agent tool:
  subagent_type: general-purpose
  description: "Fresh-agent simulation"
  prompt: |
    You are a developer who has NEVER seen this project before.
    You have been given ONLY this plan and told to implement Task 1.
    You have NO other context — no conversation history, no project knowledge.

    PLAN TEXT:
    [plan_text]

    YOUR TASK: Attempt to mentally execute Task 1 / Milestone 1 / Step 1.

    Answer these questions honestly:
    1. Can you find the project? Is the path specified?
    2. Can you install dependencies? Is the install command given?
    3. Can you find the files to modify? Are paths exact and unambiguous?
    4. Can you understand what to build? Is the spec clear enough to implement?
    5. Can you run the tests? Is the test command given with expected output?
    6. Do you know what "done" looks like? Are acceptance criteria concrete?
    7. What questions would you NEED answered before you could start?

    IMPORTANT — ALREADY KNOWN ISSUES (do NOT re-flag these):
    [wave1_findings summary — just the finding descriptions, not full details]

    OUTPUT FORMAT:
    - [CRITICAL] Cannot start: "[description of blocking gap]"
    - [WARNING] Ambiguous: "[description — would need clarification]"
    - [INFO] Suggestion: "[nice to have improvement]"

    Be brutally honest. If you'd be confused, say so.
```

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

Dispatch 1-3 specialists based on detection. If no domain keywords found, skip this angle (report as "No specialist domains detected").

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
