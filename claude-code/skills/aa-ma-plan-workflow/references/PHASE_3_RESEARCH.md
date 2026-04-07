# Phase 3: Research & Documentation Gathering

## Objectives
- Gather technical documentation for libraries/APIs
- Explore existing codebase patterns
- Research architectural approaches
- Identify dependencies and constraints
- Assess impact of proposed changes

## Skill Integration

**Primary skill:** `dispatching-parallel-agents` (for 3+ research domains)
**Supporting skills:**
- `research-consolidation` (for cross-referencing)
- `impact-analysis` (for change assessment)
- `system-mapping` (for unfamiliar code areas)

## Tool Hierarchy

When researching, use the right tool for the job:

| Need | Primary Tool | Alternative |
|------|--------------|-------------|
| Library/API docs | Context7 MCP | WebSearch |
| Current information | WebSearch | WebFetch |
| 12-Factor compliance | `rules/env-var-drift.md` | WebSearch for 12-Factor patterns |
| Text pattern search | GrepTool | - |
| Structural code search | `Skill(ast-grep)` | GrepTool |
| Complex file analysis | Python script | - |
| File pattern matching | Glob | - |
| Codebase exploration | Task(Explore) | GrepTool + Glob |

**Selection guidance:**
- **Context7 MCP**: First choice for library documentation
- **GrepTool**: Fast pattern matching across files
- **ast-grep**: Find code structures (function definitions, class patterns)
- **Python**: When you need loops, conditionals, or aggregation
- **Task(Explore)**: Open-ended codebase investigation

## Step-by-Step Procedure

### 3.1 Identify Research Needs

Based on refined requirements from Phase 2, determine what needs research:

**Common research categories:**
- External APIs or libraries (use Context7 MCP)
- Architectural patterns (use WebSearch)
- Similar implementations in codebase (use Task tool with Explore agent)
- Technical constraints or dependencies (use Grep/Glob)
- Database schema or data models (use Read tool)
- **Impact assessment** - Identify files/modules that will be modified and their upstream callers (use Grep for imports/calls)

### 3.2 Context7 MCP Integration (Library/API Documentation)

**Primary approach:** Use Context7 MCP for official documentation

```
# Step 1: Resolve library ID
mcp__context7__resolve-library-id
  library_name: "[library-name]"
  # Returns: library ID(s)

# Step 2: Get documentation
mcp__context7__get-library-docs
  library_id: "[resolved-id]"
  # Returns: comprehensive library docs
```

**Fallback strategy (if MCP unavailable):**

1. **Retry once** - Connection/protocol errors may be transient
2. **If retry fails**, fall back to:
   - `WebSearch` for official documentation
   - `Read` existing code examples in codebase
   - Community-vetted code snippets (Stack Overflow, GitHub)

**Document fallback:** Log in notes for provenance:
```
Context7 MCP unavailable - used fallback: WebSearch + codebase examples
```

### 3.3 Parallel Agent Dispatch (Complex Research)

**Trigger:** Research needs >= 3 independent areas

Invoke `dispatching-parallel-agents` skill when:
- Research needs >= 3 independent areas
- Each area requires deep exploration (file searches, multiple reads)
- Time-sensitive (need results quickly)

**Example dispatch:**
```
Task tool with multiple concurrent calls:

Agent 1 (Explore):
  prompt: "Find all authentication patterns in codebase.
           Look for JWT handling, OAuth flows, session management.
           Return file paths and pattern descriptions."
  model: haiku  # Optimize tokens

Agent 2 (research-analyst):
  prompt: "Research best practices for [architectural pattern].
           Use WebSearch for 2024-2025 recommendations.
           Return structured summary with pros/cons."
  model: haiku

Agent 3 (Explore):
  prompt: "Investigate dependencies and constraints for [feature].
           Check package.json, requirements.txt, etc.
           Return compatibility matrix and version requirements."
  model: haiku
```

**Agent coordination:**
- Launch all agents in single message (parallel execution)
- Wait for all to complete before consolidating
- Stream findings directly to memory, not screen (token optimization)

### 3.4 System Mapping Integration

**Trigger:** Invoke `Skill(system-mapping)` when ANY of:
- Changes will touch 3+ files
- Code area is unfamiliar (flagged in Phase 0/1)
- Integrating with external services
- Modifying data pipelines or databases

**Invocation:**
```
Invoke: Skill: system-mapping
Pass:
  - Entry point files (from research findings)
  - Module boundaries to explore
  - 5-point protocol request:
    1. Architecture (files/modules involved)
    2. Execution flows (call chains, async boundaries)
    3. Logging (existing observability)
    4. Dependencies (imports, external services)
    5. Environment (config, env vars, flags)
```

**Parallelization:** System-mapping can run in PARALLEL with other research agents (dispatching-parallel-agents).

**Output → Phase 4:**
- Architecture summary feeds plan constraints
- Dependency map informs risk assessment
- Execution flow identifies integration points

**Fallback (if skill unavailable):**
```bash
# Grep-based manual exploration
grep -r "import\|from" --include="*.py" [entry_file]  # Dependencies
grep -r "logger\|logging" --include="*.py" [module]   # Observability
grep -r "environ\|getenv" --include="*.py" [module]   # Environment
```

### 3.5 Impact Assessment

**REQUIRED for all plans:**

Identify files/modules that will be modified:
```bash
# Find upstream callers of files to be modified
grep -r "import.*module_name" --include="*.py"
grep -r "from module_name import" --include="*.py"
```

Document:
- Files to be created
- Files to be modified
- Upstream callers of modified files
- Potential cascade effects

### 3.6 Token Efficiency Tracking

**Principle:** Monitor context usage to prevent mid-workflow context exhaustion.

**After research completes, evaluate:**
```
Current session context usage estimate:
├── Below 50%  → Proceed normally to Phase 4
├── 50-70%     → Compress verbose research findings before Phase 4
└── Above 70%  → MUST compact context before continuing
    - Summarise key findings into structured format
    - Discard verbose tool outputs
    - Retain only actionable information
```

**Compaction strategy (if needed):**
1. Summarise library docs → retain only API signatures and constraints
2. Compress codebase exploration → retain file paths and pattern summaries
3. Condense architectural research → retain decisions and trade-offs
4. Log compaction in provenance: `Context compacted at [X%] before Phase 4`

**Output to screen:**
```
Token efficiency: [X%] context used after research
Action: [Proceed | Compact | Compact (mandatory)]
```

### 3.7 Consolidate Research Findings

Use `research-consolidation` skill (or manual consolidation) to:
- Cross-reference findings with requirements
- Detect coverage gaps
- Resolve conflicting information
- Map findings to plan elements

**Save to memory (detailed):**
- Full library documentation excerpts
- Complete codebase pattern analysis
- Detailed architectural research
- Comprehensive dependency matrix

**Show on screen (concise):**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 3 COMPLETE: Research Gathered
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ [N] libraries documented (Context7/fallback)
✓ [N] codebase patterns identified
✓ [N] architectural approaches researched
✓ [N] constraints validated
✓ Impact assessment completed
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Phase 3 Checklist

- [ ] Research needs identified from Phase 2 design
- [ ] Context7 MCP attempted for library docs (or fallback used)
- [ ] Codebase exploration completed (if relevant)
- [ ] Architectural research gathered (if needed)
- [ ] Dependencies and constraints documented
- [ ] **System mapping** completed (if 3+ files OR unfamiliar code)
- [ ] **Impact assessment** completed (identify upstream callers for files to be modified)
- [ ] **Token efficiency** evaluated (compact if above 70%)
- [ ] Findings consolidated into structured summary
- [ ] Fallback strategy used if MCP unavailable (logged)

## Validation Gate 2: Research Completeness

**MUST PASS before proceeding to Phase 4:**

| Criterion | Requirement | Check |
|-----------|-------------|-------|
| Coverage | All research needs from Phase 2 addressed | [ ] |
| Sources | Each finding has documented source | [ ] |
| Conflicts | Any conflicting info resolved or escalated | [ ] |
| Impact | Upstream callers identified for modified files | [ ] |
| Dependencies | All external dependencies documented with versions | [ ] |

**On Failure:**
1. Identify gaps and dispatch additional research
2. If conflicts unresolved, use `AskUserQuestion` for user decision
3. If fails twice, invoke `debugging-strategies` skill
