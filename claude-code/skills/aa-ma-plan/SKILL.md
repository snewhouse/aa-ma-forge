---
name: aa-ma-plan
description: "Plans a feature or change with the AA-MA method: brainstorm, research, a 13-element plan, then the five AA-MA files. Use when the user asks to plan a feature, design an implementation or create an AA-MA plan, or asks what such a plan must contain."
---

<!-- Renamed from /ultraplan to /aa-ma-plan on 2026-04-06.
     Reason: Anthropic shipped built-in "ultraplan" in Claude Code on 2026-04-04. -->

# /aa-ma-plan - AA-MA Planning Workflow

Comprehensive planning command that follows the Advanced Agentic Memory Architecture (AA-MA) methodology for complex software development tasks.

## Purpose

Use this command when you need to:
- Plan complex features or architectural changes
- Create structured, maintainable implementation roadmaps
- Follow AA-MA methodology with proper artifact generation
- Leverage superpowers skills for deep thinking and planning
- Coordinate multi-agent workflows for parallel research
- Optimize token usage while maintaining thorough documentation

## Key Features

- **Multi-input support:** Accepts selected text, inline description, or interactive prompts
- **`--from-map <effort> [--dry-run]`:** seed Phase 1 from a cleared `/aa-ma-chart` map (ADR-0013) — Decisions so far + every Answer are pre-answered grill input; `--dry-run` prints the seed and creates nothing
- **Structured thinking:** Uses `/superpowers:brainstorming` for requirement refinement
- **Research integration:** Context7 MCP with automatic fallback, parallel agent dispatch
- **AA-MA compliance:** Auto-generates 6 files (plan, reference, context-log, tasks, provenance, verification)
- **Token optimized:** Concise screen output, verbose details saved to files
- **KISS/DRY/SOLID:** Follows fundamental design principles from CLAUDE.md

## Workflow Overview

```
Phase 1: Context Gathering    → Multi-method input + clarifications
Phase 2: Structured Thinking  → /superpowers:brainstorming refinement
Phase 3: Research & Docs      → Context7 MCP + parallel agents
Phase 4: Plan Generation      → /superpowers:writing-plans
Phase 4.5: Verification       → 6-angle adversarial plan check
Phase 5: AA-MA Artifacts      → Create .claude/dev/active/[task]/
```

---

## Instructions for AI

### Phase 0: Runtime Log Initialization

See [phase-0-runtime-log.md](references/phase-0-runtime-log.md#phase-0-runtime-log-initialization) — derive the plan slug and write the phase markers the plan-marker hook checks.

---

### Phase 1: Context Gathering & Input Processing

See [phase-1-context.md](references/phase-1-context.md#phase-1-context-gathering--input-processing) — --from-map import, input detection, the grill protocol, clarifying questions and the lessons scan.

---

### Phase 2: Structured Thinking with Brainstorming

See [phase-2-brainstorm.md](references/phase-2-brainstorm.md#phase-2-structured-thinking-with-brainstorming) — the brainstorming pass that refines the request before research.

---

### Phase 3: Research & Documentation Gathering

See [phase-3-research.md](references/phase-3-research.md#phase-3-research--documentation-gathering) — Context7-first documentation research with its fallbacks, and parallel research agents.

---

### Phase 4: Plan Generation with AA-MA Standard

**Step 4.1: Invoke Write-Plan Skill**

```
Skill: superpowers:writing-plans
```

**Step 4.2: Provide Complete Context**

Pass to skill:
- Refined requirements from Phase 2
- Research findings from Phase 3
- AA-MA Planning Standard requirements (from CLAUDE.md)

Ensure plan includes ALL 13 required elements:
1. Executive summary (≤3 lines)
2. Ordered stepwise implementation plan
3. Milestones with measurable goals
4. Acceptance criteria for each step
5. Required artefacts for each step
6. Tests to validate each milestone
7. Rollback strategy for risky steps
8. Dependencies and assumptions
9. Effort estimate + Complexity (0-100%) per step
10. Risks (top 3) and mitigations per milestone
11. Next action (what to do first)
12. Engineering Standards Declaration (which themes from `claude-code/rules/engineering-standards.md` materially apply, with one-sentence rationale per theme — captured in Phase 2 Step 2.4)
13. Architecture View (mermaid Component view; Flow view iff `Critical-Path:` present; or a canonical `Diagram-Waiver`) and a `#### Contract` block per milestone with `Audit-Profile ∈ {full, code-only, infra}`

**Step 4.2b: Seed §13 from the code graph**

The Component view starts from the code, not from memory. Run one cut over every
**existing** file the plan will `Modify` (Phase 3 found them) and paste its output under
`### Component view` unchanged: node labels are repo paths and edges carry the quoted
`@import` / `@call` sigils, so `aa-ma-lint-views` checks each one (`PHANTOM_EDGE`). Then
add what does not exist yet — `(new)` nodes and the intended edges, with prose labels
(`-->|will call|`), never a sigil. The seed is caption-free. A plan that only creates files
skips the cut. Phase 4.5 check 8 (`aa-ma-lint-views --coverage`) flags any `Create` /
`Modify` path the view leaves undrawn.

```bash
# The aa-ma-forge checkout, from this command's installed symlink (scripts/install.sh).
AA_MA_ROOT=$(cd "$(dirname "$(readlink -f ~/.claude/skills/aa-ma-plan/SKILL.md)")/../../.." && pwd)
if [[ ! -f "${AA_MA_ROOT}/packages/codemem-mcp/pyproject.toml" ]]; then
  echo "§13 seed unavailable: ${AA_MA_ROOT} is not an aa-ma-forge checkout (run scripts/install.sh)."
else
  SCOPES=()
  # One existing path per line. The quoted delimiter keeps every line literal: spaces,
  # globs and $(...) in a file name are data, never shell.
  while IFS= read -r f; do [[ -n "${f}" ]] && SCOPES+=(--scope "${f}"); done <<'PATHS'
<one existing path per line>
PATHS
  if (( ${#SCOPES[@]} == 0 )); then
    echo "No existing path to Modify: seed skipped (a scope-less draw is the whole repo)."
  # Run from the project root: codemem reads ./.codemem/index.db.
  elif ! uv run --project "${AA_MA_ROOT}" codemem draw --level L2 "${SCOPES[@]}" --hops 1 --direction both; then
    # codemem has printed why (no index / schema too old / unreadable) on stderr.
    echo "§13 seed unavailable (reason above): run \`codemem build\` in the project root and re-seed."
    echo "An empty seed is not 'nothing to draw'."
  fi
fi
```

**Step 4.3: Validate Plan Completeness**

Check generated plan against AA-MA standard:
- [ ] Contains all 13 required elements
- [ ] Steps have clear acceptance criteria
- [ ] Complexity ≥80% steps are flagged
- [ ] Rollback strategy defined for risky changes
- [ ] Next action is concrete and actionable

**Fallback (if skill unavailable):**

Use native planning prompt following the AA-MA template from CLAUDE.md:

```
You MUST produce a thorough implementation plan following AA-MA Planning Standard.

CONTEXT:
- Feature: [refined requirements]
- Research: [findings summary]
- Constraints: [known limitations]

Provide:
1. Executive summary (≤3 lines)
2. Ordered stepwise implementation plan
3. Milestones with dates/durations
4. Acceptance criteria for each step
5. Required artefacts
6. Tests to validate
7. Rollback strategy
8. Dependencies and assumptions
9. Effort (hours/days) + Complexity (0-100%) per step
10. Risks (top 3) + mitigations
11. ONE Next action + which AA-MA file(s) to update
12. Engineering Standards Declaration (themes from claude-code/rules/engineering-standards.md that materially apply; one-sentence rationale each)
13. Architecture View + Contract blocks (mermaid; spec §XI item 13; seed the Component view per Step 4.2b)

Format in Markdown for direct insertion into [task]-plan.md
```

Display summary:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 4 COMPLETE: Plan Generated
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ [N] implementation steps
✓ [N] milestones defined
✓ All acceptance criteria clear
✓ Rollback strategies included
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### Phase 4.2: Optional Plan Reviews (gstack integration)

See [phase-4-reviews-and-verification.md](references/phase-4-reviews-and-verification.md#phase-42-optional-plan-reviews-gstack-integration) — the optional gstack plan reviews and the adversarial verification of the generated plan.

---

### Phase 4.5: Adversarial Verification

See [phase-4-reviews-and-verification.md](references/phase-4-reviews-and-verification.md#phase-45-adversarial-verification) — the optional gstack plan reviews and the adversarial verification of the generated plan.

---

### Phase 5: AA-MA Artifact Creation

**Step 5.1: Create Task Directory Structure**

```bash
# Determine task name (sanitize for filesystem)
TASK_NAME="[user-provided-name-in-kebab-case]"
TASK_DIR=".claude/dev/active/${TASK_NAME}"

# Create directory and files
mkdir -p "${TASK_DIR}"
cd "${TASK_DIR}"

# Create all 5 AA-MA files
touch "${TASK_NAME}-plan.md"
touch "${TASK_NAME}-reference.md"
touch "${TASK_NAME}-context-log.md"
touch "${TASK_NAME}-tasks.md"
touch "${TASK_NAME}-provenance.log"
touch "${TASK_NAME}-verification.md"
```

**`--from-map` only:** move the map in through the guard (git mv when tracked,
mv + git add when not) and let it write the provenance line — the guard is
the only writer of `MAP_IMPORTED`:

```bash
cd - > /dev/null   # back to the project root; the guard cds to the git toplevel itself
"$GUARD" import "$MAP" "${TASK_NAME}" "${TASK_DIR}/${TASK_NAME}-provenance.log" || exit 1
# → .claude/dev/active/<task>/<task>-map.md ; provenance: [ts] MAP_IMPORTED effort=<effort> tickets=<N>
```

**Step 5.2: Populate [task]-plan.md**

Write the generated plan from Phase 4:

```markdown
# [task-name] Plan

**Objective:** [1-line goal]
**Owner:** [from git config or "AI + User"]
**Created:** [current date]
**Last Updated:** [current date]

## Executive Summary
[3-line overview from plan]

## Implementation Steps
[Full plan content with all 13 elements]

## Next Action
[Specific first step from plan]
```

**Step 5.3: Extract and Populate [task]-reference.md**

Parse the plan for immutable facts and write to reference:

```markdown
# [task-name] Reference

## Immutable Facts and Constants

[Extract from plan:]
- API endpoints
- File paths
- Configuration values
- Library versions
- Database schemas
- Model paths
- Research files: one `docs/research/<slug>-<topic>.md — <question> (Valid-Through: <date>)` line per Phase 3 file
- `--from-map`: one line per RESOLVED ticket — `Ticket N: <title> — <Answer gist> [valid: <date>]` (source: `[task]-map.md`)
- Append the pointer line `Architecture View: see plan.md §13` (or `Architecture View: waived (<value>)`)

_Last Updated: [date]_
```

**Index-enhanced (codemem by default; PROJECT_INDEX.json is codemem's fallback when present):**
Supplement the reference with structural facts from the index:
- Key symbols: codemem `layers()` core files + `file_summary` (fallback: `_meta.symbol_importance`, top 10)
- File→dependency mappings for files in scope: codemem `diagram(level="L2", scope=<file>)` (fallback: `deps`)
- Directory purposes for relevant directories: codemem `diagram(level="L1")` (fallback: `dir_purposes`)
- These provide implementing agents with architectural context they would otherwise need to discover via Grep

**Step 5.4: Initialize [task]-context-log.md**

Create initial log entry:

```markdown
# [task-name] Context Log

## [current-date] Initial Context

**Feature Request:** [original user input]

**Key Decisions:**
- [Decision 1 from brainstorm phase]
- [Decision 2 from research phase]

**Research Findings:**
- [Summary from Phase 3 — link each `docs/research/<slug>-*.md` file it wrote]

**Remaining Questions:**
- [Any unresolved items]

_This log will be updated via context compaction as the task progresses._
```

**Step 5.5: Create HTP Structure in [task]-tasks.md**

Convert plan steps into Hierarchical Task Planning format:

```markdown
# [task-name] Tasks (HTP)

## Milestone 1: [title]
- Status: PENDING
- Dependencies: None
- Complexity: [%]
- Acceptance Criteria: [from plan]

### Sub-step 1.1: [action]
- Status: PENDING
- Result Log: [placeholder]

### Sub-step 1.2: [action]
- Status: PENDING
- Result Log: [placeholder]

## Milestone 2: [title]
- Status: PENDING
- Dependencies: Milestone 1
- Complexity: [%]
- Acceptance Criteria: [from plan]

[Continue for all milestones/steps from plan]
```

Write `Dependencies:` in the canonical form only: `None`, `Milestone 2`,
`Milestone 2, Milestone 3`, `Sub-step 1.1`; another plan's milestone is
`<task-slug> Milestone 5` (cross-plan, exempt). Then generate the **Milestone
graph** — derived from tasks.md, never hand-authored — append it to plan.md's
`## 13. Architecture View`, and fix every `UNRESOLVED_DEPENDENCY` before Step 5.7:

```bash
for _cand in \
  "$(git rev-parse --show-toplevel 2>/dev/null)/claude-code/hooks/lib/aa-ma-parse.sh" \
  "${CLAUDE_HOME:-${HOME}/.claude}/hooks/lib/aa-ma-parse.sh"; do
  [[ -f "${_cand}" ]] && AA_MA_LIB="${_cand}" && break
done
# shellcheck source=/dev/null
. "${AA_MA_LIB:?aa-ma-parse.sh not found — run scripts/install.sh}"
aa_ma_deps graph "${TASK_DIR}/${TASK_NAME}-tasks.md"   # prints '### Milestone graph' + mermaid → append to §13
aa_ma_deps check "${TASK_DIR}/${TASK_NAME}-tasks.md"   # UNRESOLVED_DEPENDENCY lines; exit 1 on any
```

**Step 5.6: Initialize [task]-provenance.log**

Create initial log entry:

```text
# [task-name] Provenance Log

[current-timestamp] Task initialized via /aa-ma-plan
[current-timestamp] Commit: [git hash] — Phase: Planning
[current-timestamp] AA-MA artifacts created
```

**Step 5.7: Validate Artifact Creation**

```bash
# Verify all files exist and have content
ls -lh "${TASK_DIR}/"
wc -l "${TASK_DIR}/"*.md "${TASK_DIR}/"*.log
```

Check:
- [ ] All 6 files present
- [ ] plan.md has complete plan
- [ ] reference.md has extracted facts
- [ ] context-log.md has initial context
- [ ] tasks.md has HTP structure
- [ ] provenance.log has timestamps
- [ ] verification.md present (if verification was run in Phase 4.5)

**Step 5.8: Display Final Summary**

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PHASE 5 COMPLETE: AA-MA Artifacts Created
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Task Directory: .claude/dev/active/[task-name]/

Files created:
  ✓ [task]-plan.md         → Complete implementation plan
  ✓ [task]-reference.md    → Immutable facts/constants
  ✓ [task]-context-log.md  → Decision history
  ✓ [task]-tasks.md        → HTP roadmap
  ✓ [task]-provenance.log  → Execution telemetry
  ✓ [task]-verification.md  → Plan verification audit trail (if run)
  ✓ [task]-map.md           → Charting map (only with --from-map)

Next Action: [specific step from plan]

To begin implementation, load context with:
  <REFERENCE>
  (Contents of [task]-reference.md)
  </REFERENCE>

  <TASKS>
  (Contents of [task]-tasks.md)
  </TASKS>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
/aa-ma-plan workflow complete — Ready to implement
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Error Handling & Fallbacks

See [operations.md](references/operations.md#error-handling--fallbacks) — error handling and fallbacks, token use, usage examples, related commands, time estimates and troubleshooting.
