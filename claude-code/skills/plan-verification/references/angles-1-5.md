# Verification angles 1-5 — what each Wave 1 agent (ground truth, assumptions, impact, falsifiability) and the Wave 2 fresh-agent simulation checks, and how it reports.

## Contents


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
