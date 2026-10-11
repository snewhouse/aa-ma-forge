# Phase 3: research — Context7-first documentation research with its fallbacks, and parallel research agents.

### Phase 3: Research & Documentation Gathering

**Step 3.1: Identify Research Needs**

Based on refined requirements, determine what needs research:
- External APIs or libraries
- Architectural patterns
- Similar implementations in codebase
- Technical constraints or dependencies

**Step 3.2: Context7 MCP Integration**

If library/API documentation is needed:

```
# Primary attempt: Context7 MCP
mcp__context7__resolve-library-id for relevant libraries
mcp__context7__get-library-docs with resolved IDs

# Fallback if MCP unavailable (connection error, protocol error):
# 1. Retry once
# 2. If retry fails, fall back to:
#    - WebSearch for official documentation
#    - Read existing code examples in codebase
#    - Community-vetted code snippets
```

**Step 3.3: Parallel Agent Dispatch (if needed)**

Two kinds of research question, two dispatch paths:

1. **Primary-source questions** ("what does X actually do / say?" — a library
   API, a script's behaviour, a spec clause) → `Skill(aa-ma-research)`. It
   dispatches one `aa-ma-researcher` agent per question; the agent has no
   Agent tool (cannot nest), answers only the stated question, and writes
   **exactly one** cited file `docs/research/<slug>-<topic>.md` with the
   `Created / Author / Reviewed-Through-Date / Valid-Through / Sources`
   header. Its short return carries `tools: web_fetches=<N> context7_calls=<N>`
   — sum those into the Phase 3 marker.
2. **Codebase exploration** ("where do we already do X?") →
   `Agent(subagent_type: "Explore")`.

Load `Skill(aa-ma-research)` **once**, then dispatch one agent per question in
a single message (the Step 1.3 agent cap applies):

```
- Agent(subagent_type: "aa-ma-researcher"): "<question 1>"  → docs/research/<slug>-<topic>.md
- Agent(subagent_type: "aa-ma-researcher"): "<question 2>"  → docs/research/<slug>-<topic>.md
- Agent(subagent_type: "Explore", model: "haiku"): codebase patterns / dependencies
```

**Step 3.4: Consolidate Research Findings**

Gather findings into structured summary (save to memory, show brief on screen).
`research_files` = the number of `docs/research/` files Phase 3 wrote; link
each one from reference.md (Step 5.3) and context-log.md (Step 5.4).

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 3 COMPLETE: Research Gathered
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ [N] libraries documented
✓ [N] codebase patterns identified
✓ [N] constraints validated
✓ [N] research files → docs/research/<slug>-*.md
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Marker: `bash ~/.claude/hooks/lib/aa-ma-plan-marker.sh <slug> 3 DONE context7_calls=<N> web_fetches=<N> research_files=<N>`
— each `<N>` is an integer **you** compute from the returns; never paste an
agent's return text into the marker command line.
