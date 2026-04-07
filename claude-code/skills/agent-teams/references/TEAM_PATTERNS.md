# Team Patterns

Detailed orchestration patterns for each team type supported by the agent-teams skill.

---

## Research Team Pattern

### When to Use
- Investigating a bug with multiple possible root causes
- Comparing approaches, libraries, or architectures
- Analyzing a codebase from multiple angles
- Any investigation benefiting from diverse perspectives

### Structure
```
Team Lead (your session)
├── Researcher 1 (Explore) — angle: {perspective_1}
├── Researcher 2 (Explore) — angle: {perspective_2}
├── Researcher 3 (Explore) — angle: {perspective_3} [optional]
└── Synthesizer (Explore) — consolidates findings [optional, lead can do this]
```

### Workflow
1. **Define investigation angles** — each researcher gets a distinct perspective
   - Example: Bug investigation → R1 checks recent commits, R2 checks dependencies, R3 checks configuration
   - Example: Architecture comparison → R1 evaluates Option A, R2 evaluates Option B
2. **Spawn researchers** — all in parallel, each with their angle
3. **Initial findings** — researchers report independently
4. **Debate round** — trigger Competing Hypotheses Protocol (see below)
5. **Synthesis** — consolidate surviving conclusions
6. **Report** — present to user

### Investigation Angle Assignment
- Angles should be **non-overlapping** but **comprehensive**
- Each angle should be investigable independently
- Good: "Check git log for recent changes to auth module" vs "Check dependency versions for auth libraries"
- Bad: "Investigate auth" vs "Look into authentication" (overlapping)

### Example: Bug Investigation
```
Researchers:
  R1: "Investigate recent code changes that could cause {bug}" (angle: code history)
  R2: "Investigate dependency/environment changes" (angle: infrastructure)
  R3: "Investigate data/state that triggers {bug}" (angle: runtime state)
```

---

## Competing Hypotheses Protocol

The default mode for research teams. Researchers actively challenge each other's conclusions before synthesis.

### Why
- Prevents confirmation bias (single researcher finds what they expect)
- Surfaces alternative explanations
- Increases confidence in final conclusions
- Mimics scientific peer review

### Protocol Steps

**Step 1: Independent Investigation**
- Each researcher investigates their assigned angle
- No communication between researchers during this phase
- Each produces findings with evidence and confidence level

**Step 2: Findings Sharing**
- Lead collects all findings
- Lead sends each researcher a summary of ALL findings:
  ```
  SendMessage to each researcher:
  "Here are all findings. Review them and:
  1. Identify claims you disagree with and explain why
  2. Point out gaps in evidence
  3. Suggest alternative explanations
  4. Rate each finding: AGREE / CHALLENGE / INSUFFICIENT_EVIDENCE"
  ```

**Step 3: Challenge Round (1 round only)**
- Each researcher responds with challenges
- Lead collects all challenges
- This is capped at 1 round to prevent token explosion

**Step 4: Resolution**
- Lead (or Synthesizer) reviews challenges
- Findings that survived challenge → HIGH confidence
- Findings challenged but with strong evidence → MEDIUM confidence
- Findings successfully challenged → DROPPED or RECLASSIFIED
- Unresolved disagreements → flagged for user decision

**Step 5: Consolidated Report**
- Only surviving findings are reported
- Dropped findings are noted with reason
- User gets a confidence-rated, adversarially-tested result

### Debate Limits
- **Max 1 challenge round** (prevents token spiral)
- **Lead mediates** (researchers don't debate directly in extended exchanges)
- **Evidence-based only** (challenges must cite evidence, not just opinion)

---

## Implementation Team Pattern

### When to Use
- Building a new feature with multiple components
- Refactoring across multiple files/modules
- Any implementation benefiting from scope partitioning
- Tasks where quality review is essential

### Structure
```
Team Lead (your session)
├── Architect (Plan) — designs scope, patterns, dependencies
├── Implementer 1 (general-purpose) — scope: {module_A}
├── Implementer 2 (general-purpose) — scope: {module_B}
├── Implementer 3 (general-purpose) — scope: {module_C} [optional]
└── Reviewer (code-reviewer) — reviews all implementations
```

### Workflow
1. **Architect designs** — analyses codebase, defines non-overlapping scopes, recommends patterns
2. **Lead reviews design** — approve or adjust scope assignments
3. **Implementers execute** — each works within assigned scope, commits independently
4. **Reviewer reviews** — after each implementer finishes, reviewer checks their work
5. **Integration** — lead verifies all changes work together (run full tests)
6. **Final review** — reviewer does a holistic pass across all changes

### Scope Partitioning Rules
- **Non-overlapping**: No two implementers modify the same file
- **Architect defines**: Scopes are defined before implementation starts
- **Conflict prevention**: If scope overlap is unavoidable, implementers work sequentially on shared files
- **Communication**: Implementers flag when they need changes outside their scope

### Task Dependency Chain
```
Task: Design review (Architect) — no dependencies
Task: Implement module A (Impl 1) — blockedBy: [Design review]
Task: Implement module B (Impl 2) — blockedBy: [Design review]
Task: Review module A (Reviewer) — blockedBy: [Implement A]
Task: Review module B (Reviewer) — blockedBy: [Implement B]
Task: Integration test (Lead) — blockedBy: [Review A, Review B]
```

### Commit Strategy
- Each implementer commits their own scope
- Commit messages follow project conventions
- Lead does final integration commit if needed
- All commits include AA-MA signature if applicable

---

## Hybrid Team Pattern

### When to Use
- "Research this, then build a solution"
- Feature development requiring investigation first
- Migrations requiring analysis before execution
- Any task with distinct research → implementation phases

### Structure
```
Phase 1 (Research):
  Team Lead → Researcher 1 + Researcher 2 [+ Synthesizer]

Phase 2 (Implementation):
  Team Lead → Architect + Implementer 1 + Implementer 2 + Reviewer
```

### Workflow
1. **Phase 1: Research** — follow Research Team Pattern
   - Spawn research team
   - Execute with Competing Hypotheses
   - Synthesize findings
   - Shut down research teammates
2. **Handoff** — research findings inform implementation
   - Lead converts research conclusions into implementation requirements
   - If AA-MA active: update reference.md and tasks.md with findings
3. **Phase 2: Implementation** — follow Implementation Team Pattern
   - Spawn implementation team (new teammates)
   - Include research findings in spawn prompts
   - Execute with scope partitioning and quality gates
   - Shut down implementation teammates

### Phase Transition
- Research team is fully shut down before implementation team spawns
- This prevents token waste from idle teammates
- Research findings are passed via spawn prompts, not live messages
- TeamDelete for Phase 1 team, then TeamCreate for Phase 2 team

### Example: "Investigate auth options then implement the best one"
```
Phase 1: Research
  R1: "Evaluate JWT-based auth" (angle: token approach)
  R2: "Evaluate session-based auth" (angle: server approach)
  R3: "Evaluate OAuth2 integration" (angle: delegated approach)
  → Debate → Synthesis → Recommendation: JWT with refresh tokens

Phase 2: Implementation
  Architect: Design JWT auth module scope
  Impl 1: Auth middleware + token generation
  Impl 2: User model + login/register endpoints
  Reviewer: Security-focused review of all auth code
```

---

## Review Team Pattern

### When to Use
- Pre-merge comprehensive review
- Security audit of a module
- Quality assessment of recent changes
- Any multi-perspective code review

### Structure
```
Team Lead (your session)
├── Code Quality Reviewer (code-reviewer) — readability, patterns, DRY
├── Security Reviewer (security-auditor) — vulnerabilities, OWASP
└── Test Coverage Reviewer (test-automator) — coverage, edge cases
```

### Workflow
1. **Define review scope** — files, commits, or modules to review
2. **Spawn reviewers** — all in parallel with different lenses
3. **Independent review** — each reviews from their perspective
4. **Consolidation** — lead deduplicates and priority-sorts findings
5. **Report** — present consolidated findings to user

### Lens Assignment
Each reviewer has a specific focus ("lens"):
- **Code Quality**: naming, organization, complexity, error handling, patterns
- **Security**: injection, auth, data exposure, CSRF, dependency vulns
- **Test Coverage**: missing tests, edge cases, mock quality, integration gaps

### Finding Severity Levels
| Level | Definition | Action |
|-------|-----------|--------|
| Critical | Security vuln, data loss, crash | Must fix |
| Important | Bug potential, quality issue | Should fix |
| Minor | Style, naming, small improvement | Nice to have |
| Info | Observation, suggestion | No action needed |

### Consolidated Report Format
- Deduplicate: same issue found by multiple reviewers → merge with all attributions
- Cross-reference: security issue that's also a quality issue → note both perspectives
- Priority sort: Critical → Important → Minor → Info
- Actionable: each finding has a suggested fix or approach

---

## Team Size Guidelines

| Team Size | When | Notes |
|-----------|------|-------|
| 1 | Never for teams | Use subagent-driven-development instead |
| 2 | Small review, simple investigation | Minimum viable team |
| 3 | Standard implementation or research | Sweet spot |
| 4 | Complex multi-module implementation | Good for larger scope |
| 5 | Maximum | Beyond this, coordination overhead dominates |
| 6+ | Never | Split into phases (hybrid pattern) instead |

---

## Structural Analysis Team Pattern

### When to Use
- Pre-refactoring analysis (understand what will be affected)
- Unfamiliar codebase understanding (map architecture structurally)
- Architecture audit (validate actual structure vs documented design)
- Dependency mapping before migration
- Call graph analysis for impact assessment

### Structure
```
Team Lead (your session)
├── AST Analyst (Explore) — structural: call graphs, dependency maps via sg
├── Researcher (Explore) — contextual: docs, git history, patterns
└── Synthesizer (Explore) — consolidates into actionable report
```

### Workflow
1. **AST Analyst maps structure** — uses `sg` for call graphs, class hierarchies, import maps, decorator patterns
2. **Researcher gathers context** — git history, documentation, README, configuration patterns
3. **Synthesizer combines** — merges structural facts with contextual understanding
4. **Lead reviews** — validates findings, identifies gaps, presents to user

### When to Add AST Analyst to Other Teams
- **Research Team:** Add when investigating unfamiliar code (structural evidence strengthens hypotheses)
- **Implementation Team:** Add during Architect phase for structural pre-analysis
- **Hybrid Team:** Add to Phase 1 research for structural grounding

### Example: Pre-Refactoring Analysis
```
AST Analyst: "sg found 47 callers of process_data() across 12 files"
Researcher: "git blame shows this function was last refactored 18 months ago,
             3 contributors have touched it"
Synthesizer: "High blast radius (47 callers), but stable code (18 months).
              Recommend: phase the refactoring by module, starting with
              the 3 files that account for 70% of calls."
```

---

## Anti-Patterns

| Anti-Pattern | Problem | Solution |
|-------------|---------|----------|
| Too many researchers on same angle | Duplicate work, no new perspective | Assign distinct angles |
| Overlapping implementer scopes | File conflicts, merge hell | Architect defines non-overlapping scopes |
| Skipping debate in research | Confirmation bias, weak conclusions | Always use Competing Hypotheses |
| No reviewer on impl team | Quality issues ship | Always include reviewer role |
| Team too large (>5) | Coordination overhead > work output | Cap at 5, use phases |
| Research and impl in same phase | Token waste from idle teammates | Use hybrid pattern with shutdown between phases |
