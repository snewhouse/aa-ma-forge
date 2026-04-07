# Research Team Template

Ready-to-use configuration for spawning a research team with the Competing Hypotheses protocol.

---

## Configuration

| Setting | Value |
|---------|-------|
| Team name | `research-{topic}` |
| Team type | RESEARCH |
| Size | 2-4 researchers + optional synthesizer |
| Debate mode | YES (Competing Hypotheses) |
| Quality gates | Consistency Check only |

---

## Roles

### Researcher 1
- **Name**: `researcher-1`
- **Agent type**: `Explore`
- **Investigation angle**: {angle_1_description}
- **Spawn prompt**:
```
You are Researcher 1 on team "research-{topic}".

Your investigation angle: {angle_1_description}

Instructions:
1. Read your assigned tasks via TaskGet
2. Mark tasks in_progress via TaskUpdate when starting
3. Investigate "{topic}" from the perspective of: {angle_1_description}
4. Use Glob, Grep, Read, WebSearch, WebFetch as needed
5. Document ALL findings with specific evidence:
   - File paths and line numbers for code findings
   - URLs for external findings
   - Exact quotes or data points
6. SendMessage your findings to the team lead when done
7. Mark tasks completed via TaskUpdate
8. Check TaskList for next work (debate round)

IMPORTANT: Investigate independently. Do not assume conclusions — follow evidence.

Output your findings as:
## Findings: {angle_1_description}
### Evidence
- [source] finding description
### Conclusion
Your interpretation based on evidence
### Confidence: HIGH|MEDIUM|LOW
### Gaps
What you couldn't determine
```

### Researcher 2
- **Name**: `researcher-2`
- **Agent type**: `Explore`
- **Investigation angle**: {angle_2_description}
- **Spawn prompt**: (Same structure as Researcher 1, with {angle_2_description})

### Researcher 3 (Optional)
- **Name**: `researcher-3`
- **Agent type**: `Explore`
- **Investigation angle**: {angle_3_description}
- **Spawn prompt**: (Same structure, with {angle_3_description})

### Researcher 4 (Optional)
- **Name**: `researcher-4`
- **Agent type**: `Explore`
- **Investigation angle**: {angle_4_description}
- **Spawn prompt**: (Same structure, with {angle_4_description})

### Synthesizer (Optional)
- **Name**: `synthesizer`
- **Agent type**: `Explore`
- **Purpose**: Consolidate findings after debate round
- **Spawn prompt**:
```
You are the Synthesizer on team "research-{topic}".

Your task: After all researchers complete their investigation AND the
debate round finishes, consolidate the surviving findings into a unified
report.

Wait for the team lead to send you all findings and debate results.

Instructions:
1. Read your assigned tasks via TaskGet
2. Mark tasks in_progress via TaskUpdate when starting
3. Review all researcher findings (sent via messages)
4. Identify consensus findings (all agree)
5. Resolve contested findings (weigh evidence quality)
6. Produce consolidated report
7. SendMessage the report to the team lead
8. Mark tasks completed via TaskUpdate

Output as:
## Synthesis: {topic}
### Consensus Findings
{findings supported by multiple researchers}
### Contested Findings (Resolved)
{disagreements and how they were resolved}
### Knowledge Gaps
{what remains unknown}
### Recommendations
{actionable next steps}
### Overall Confidence: HIGH|MEDIUM|LOW
```

---

## Tasks Setup

```
Task 1: "Investigate {topic} — angle: {angle_1}" → researcher-1
  No dependencies

Task 2: "Investigate {topic} — angle: {angle_2}" → researcher-2
  No dependencies

Task 3: "Investigate {topic} — angle: {angle_3}" → researcher-3 [optional]
  No dependencies

Task 4: "Challenge and debate findings" → ALL researchers
  addBlockedBy: [Task 1, Task 2, Task 3]
  (Lead triggers this by sending findings to all researchers)

Task 5: "Synthesize findings into final report" → synthesizer (or lead)
  addBlockedBy: [Task 4]
```

Tasks 1-3 run in parallel. Task 4 (debate) requires all initial investigations to complete. Task 5 (synthesis) requires the debate round to complete.

---

## Competing Hypotheses Debate Protocol

### Step 1: Initial Investigation (Parallel)
All researchers investigate their angles independently. No communication between researchers.

### Step 2: Share Findings (Lead orchestrates)
Lead collects all findings, then sends to each researcher:
```
SendMessage to each researcher:
"All initial findings are in. Here is a summary:

Researcher 1 found: {summary}
Researcher 2 found: {summary}
Researcher 3 found: {summary}

Your task now: Review ALL findings and respond with:
1. Which findings do you AGREE with? (and why)
2. Which findings do you CHALLENGE? (cite counter-evidence)
3. What alternative explanations exist?
4. Rate each finding: AGREE / CHALLENGE / INSUFFICIENT_EVIDENCE"
```

### Step 3: Challenge Round (1 round max)
Each researcher responds with their challenges. Lead collects all challenges.

### Step 4: Resolution (Lead or Synthesizer)
- Findings surviving all challenges → HIGH confidence
- Findings challenged but with stronger evidence → MEDIUM confidence
- Findings successfully refuted → DROPPED
- Unresolved disagreements → flagged for user decision

---

## Expected Deliverable

```markdown
# Research Report: {topic}

## Executive Summary
{2-3 line summary of key findings}

## Methodology
- Team: {count} researchers with distinct investigation angles
- Protocol: Competing Hypotheses with adversarial debate
- Angles investigated: {list}

## High-Confidence Findings
{findings that survived adversarial challenge}

## Medium-Confidence Findings
{findings challenged but with stronger supporting evidence}

## Dropped Findings
{findings successfully refuted, with reason}

## Unresolved Questions
{disagreements requiring user decision}

## Recommendations
{actionable next steps based on findings}
```

---

## Example: Bug Investigation

```
Topic: "Why does the auth module timeout under load?"

Researcher 1 (angle: code history):
  "Check recent commits to auth module, identify changes that could affect performance"

Researcher 2 (angle: infrastructure):
  "Check dependencies, connection pooling, database query patterns"

Researcher 3 (angle: runtime behavior):
  "Check logs, metrics, trace data for patterns in timeout occurrences"

Debate: R1 found a recent connection pool change, R2 found pool config mismatch,
R3 found timeouts correlate with pool exhaustion. Consensus: pool config regression.
```

---

## Usage

To use this template:
1. Replace all {placeholders} with task-specific values
2. Choose 2-4 researchers based on topic complexity
3. Decide if synthesizer is needed (lead can synthesize for small teams)
4. Create team and tasks following the structure above
5. Execute following the 7-phase lifecycle in SKILL.md
