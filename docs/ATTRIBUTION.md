# Attribution & Provenance

This document maps every external influence on AA-MA Forge to what it shaped, what we changed, and where it lives now.

## External Influences

### Diet-Coder's Dev Docs System

- **Source:** [dev.to article](https://dev.to/diet-code103/claude-code-is-a-beast-tips-from-6-months-of-hardcore-use-572n) and [r/ClaudeCode post](https://www.reddit.com/r/ClaudeCode/comments/1oivs81/claude_code_is_a_beast_tips_from_6_months_of/)
- **What we took:** The concept of three structured files per task (plan, context, tasks) as external memory for an LLM agent
- **What we changed:** Expanded to five files by separating immutable facts into `reference.md` and adding `provenance.log` for audit trail. Added two optional files (`verification.md`, `tests.yaml`). Designed the separation principle: reference holds what doesn't change, context-log holds why decisions were made, tasks holds current execution state
- **Where it lives:** The entire AA-MA file system (`docs/spec/aa-ma-specification.md`)
- **Credit:** README "Credits and inspirations", `docs/narrative/how-we-got-here.md`

### Matt Pocock's Skills Repository

- **Source:** [github.com/mattpocock/skills](https://github.com/mattpocock/skills)
- **What we took:** Directory-based skill structure (each skill as a folder with SKILL.md + references/). The concept of a relentless interview technique for forcing decisions
- **What we changed:** Adapted the skill layout for AA-MA's command-skill-agent architecture. The `/grill-me` command was redesigned as an artifact-focused decision-forcing protocol rather than a general interview. `grilling` (`skills/productivity/grilling` @ c55ee46) is forked verbatim; `grill-with-docs` is Derived — it keeps its name and domain block from the 2026-05-10 fork and delegates the interview to `grilling` (upstream split it into `grilling` + `domain-modeling` in 2026-07). `aa-ma-research` (`skills/engineering/research` @ c55ee46) is Derived — upstream body verbatim, renamed so the pre-existing `~/.claude/skills/research` is never shadowed, plus an `## In this repo` block that binds it to the non-nesting `aa-ma-researcher` agent and the `docs/research/` header convention. Every fork is tracked in `claude-code/skills/FORKS.json`. **Charting** (`/aa-ma-chart`, `[task]-map.md`) — concept adapted from `wayfinder` (mattpocock/skills, c55ee46): destination / decision tickets typed `research|prototype|grilling|task` / fog of war / out of scope / claim-before-work; **no files forked** (no `FORKS.json` row), the map lives in `.claude/dev/charting/` instead of an issue tracker, and the invariant is reworded to '≤1 non-research ticket CLAIMED at a time' (OV5) — see ADR-0013
- **Where it lives:** `claude-code/skills/` directory structure, `claude-code/commands/grill-me.md`, `claude-code/skills/grilling/`, `claude-code/skills/grill-with-docs/`, `claude-code/skills/aa-ma-research/`, `claude-code/agents/aa-ma-researcher.md`, `claude-code/commands/aa-ma-chart.md`, `claude-code/hooks/lib/aa-ma-chart-guard.sh`, `docs/templates/map-template.md`
- **Credit:** README "Credits and inspirations", CHANGELOG

### Helix.ml

- **Source:** [helix.ml](https://helix.ml) spec-driven workflow concepts
- **What we took:** The idea of infrastructure-enforced gates in a specification-driven workflow
- **What we changed:** Implemented HARD/SOFT gate classification (HARD gates require signed approval artifacts, SOFT gates are convention-based). Added CHECKPOINT format for session resume. Designed `tests.yaml` for machine-executable acceptance criteria
- **Where it lives:** Spec v2.1 gate classification (`tasks.md` Gate field), CHECKPOINT entry format in `provenance.log`, `tests.yaml` optional file
- **Credit:** README "Credits and inspirations", specification references

### gstack Plugin

- **Source:** [Claude Code marketplace](https://github.com/anthropics/claude-code-marketplace)
- **What we took:** Plan review perspectives (CEO, engineering, design), QA testing workflows, session tracking, the "Boil the Lake" retrospective principle
- **What we changed:** Integrated as optional dependency. The `/retro` skill uses gstack binaries for update checking and session tracking. Plan review skills are invoked as optional phases during `/aa-ma-plan`. All features gracefully degrade when gstack is not installed
- **Where it lives:** `claude-code/skills/retro/SKILL.md`, optional plan review phases in `aa-ma-plan-workflow`
- **Credit:** README "Optional extras", attribution note in retro/SKILL.md

### superpowers Plugin

- **Source:** [superpowers marketplace](https://github.com/superpowers-marketplace/superpowers)
- **What we took:** Brainstorming skill, writing-plans skill, TDD workflow, systematic debugging, and other structured workflows
- **What we changed:** Invoked as optional phases within the AA-MA planning workflow. Brainstorming drives Phase 2, writing-plans drives Phase 4 plan generation, TDD drives test-first execution. All phases fall back to native Claude Code tools when superpowers is absent
- **Where it lives:** `claude-code/skills/aa-ma-plan-workflow/` (phases 1-4), dependency note in SKILL.md
- **Credit:** README "Optional extras", dependency note in aa-ma-plan-workflow/SKILL.md

### claude-mem

- **Source:** [github.com/thedotmack/claude-mem](https://github.com/thedotmack/claude-mem) by thedotmack
- **What we took:** Persistent cross-session memory via vector store
- **What we changed:** Used as a complementary system. AA-MA files hold plan-level structure; claude-mem indexes observations, tool results, and decisions into a searchable store that survives session boundaries
- **Where it lives:** Referenced as a recommended companion in README
- **Credit:** README "What else helped"

### double-check

- **Source:** [claudecodecommands.directory](https://claudecodecommands.directory/commands/double-check)
- **What we took:** The concept of forcing the agent to stop and verify completion before moving on
- **What we changed:** Used as-is as a complementary validation tool alongside AA-MA's own verification gates
- **Where it lives:** Referenced as a recommended companion in README
- **Credit:** README "What else helped"

### Context7 MCP

- **Source:** [github.com/upstash/context7](https://github.com/upstash/context7)
- **What we took:** Library/API documentation lookup via MCP server
- **What we changed:** Integrated as optional documentation source during planning Phase 3 (research) and execution. Retry-once with fallback to native tools and WebSearch
- **Where it lives:** `aa-ma-plan-workflow` Phase 3, execution commands
- **Credit:** README "Optional extras"

## What's Original

The following are Stephen Newhouse's original contributions, not derived from external sources:

- **The five-file separation principle** — reference (immutable facts) vs context-log (mutable decisions) vs tasks (execution state) vs provenance (audit trail), each with distinct update triggers and loading priority
- **Hierarchical Task Planning (HTP)** — the term echoes HTN (Hierarchical Task Networks) from classical AI planning literature, but the implementation is AA-MA-specific: milestone/sub-step structure with Status, Dependencies, Complexity, Gate (HARD/SOFT), Mode (HITL/AFK), and Result Log fields designed for LLM agent execution rather than automated planning
- **The AA-MA specification (v2.1)** — 560+ line formal specification with 12 sections covering file taxonomy, context injection, planning standard, finalization protocol, and file templates
- **Complexity routing** — weighted 5-factor algorithm (scope, architecture, risk, dependencies, uncertainty) with auto-trigger indicators and threshold-based review routing
- **6-angle adversarial verification** — ground-truth audit, assumption challenge, impact analysis, acceptance criteria falsifiability, fresh-agent simulation, specialist domain audit
- **Agent-teams orchestration** — 7-phase lifecycle (analyze, compose, approve, spawn, coordinate, shutdown, cleanup) with competing hypotheses protocol for research teams
- **Defense-in-depth validation pattern** — four-layer validation (entry, business, environment, debug) derived from real debugging experience
- **Dispatching parallel agents pattern** — concurrent independent investigation pattern with structured prompts and integration protocol
- **The install/uninstall mechanism** — symlink-based deployment with dry-run preview, automatic backups, and clean removal
- **The commit signature system** — `[AA-MA Plan]` footer line linking commits to active tasks
- **Session checkpoint format** — structured CHECKPOINT entries enabling reliable session resume
