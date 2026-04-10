<p align="center">
  <img src="docs/images/aa-ma-forge-banner.png" alt="AA-MA Forge" width="900">
</p>

<p align="center">
  Structured external memory for Claude Code, so your AI agent stops forgetting what it's done.
</p>

[![License](https://img.shields.io/github/license/snewhouse/aa-ma-forge)](LICENSE)
[![GitHub tag](https://img.shields.io/github/v/tag/snewhouse/aa-ma-forge?sort=semver)](https://github.com/snewhouse/aa-ma-forge/tags)
[![Python](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2Fsnewhouse%2Faa-ma-forge%2Fmain%2Fpyproject.toml)](https://github.com/snewhouse/aa-ma-forge)
[![GitHub last commit](https://img.shields.io/github/last-commit/snewhouse/aa-ma-forge)](https://github.com/snewhouse/aa-ma-forge/commits/main)
[![Security](https://github.com/snewhouse/aa-ma-forge/actions/workflows/security.yml/badge.svg)](https://github.com/snewhouse/aa-ma-forge/actions/workflows/security.yml)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-yellow.svg)](https://conventionalcommits.org)
[![Semantic Versioning](https://img.shields.io/badge/semver-2.0.0-blue)](https://semver.org/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

## The problem

LLM agents lose context across sessions. They drift from plans, forget decisions, repeat work you've already covered. Every new conversation starts from scratch, and you're back to re-explaining the same architecture, the same constraints, the same goals. It's maddening.

<p align="center">
  <img src="docs/images/aa-ma-forge-triptych.jpg" alt="Context Lost → The AA-MA Forge → Context Retained: a triptych showing the journey from session amnesia through structured memory forging to multi-session persistence" width="900">
</p>

## What AA-MA is

AA-MA (Advanced Agentic Memory Architecture) gives Claude Code a structured external memory built from five specialised files. Each file segments a different kind of knowledge: strategy, facts, decisions, execution state, and audit history. Built for long-horizon, multi-session tasks where context loss kills productivity.

## What's in this repo

```
docs/spec/          The specification (v2.1), quick reference, team guide,
                    and Claude Code foundations reference
docs/narrative/     The origin story (how and why AA-MA exists)
docs/templates/     Ready-to-use templates for all 7 AA-MA file types
claude-code/        Commands, skills, agents, rules, hooks
                    (the operational layer that plugs into Claude Code)
src/aa_ma/          Python package (planned — package skeleton only)
examples/           Real completed task artefacts (five files plus optional tests)
scripts/            install.sh / uninstall.sh
```

## Quick start

Requires [Claude Code](https://docs.anthropic.com/en/docs/claude-code) installed and configured.

```bash
git clone https://github.com/snewhouse/aa-ma-forge.git
cd aa-ma-forge
scripts/install.sh --dry-run  # preview what will be deployed
scripts/install.sh            # deploy to ~/.claude/
```

The installer creates symlinks from this repo into your `~/.claude/` directory. It backs up any existing files before touching them. Run `scripts/uninstall.sh` to reverse everything.

Once installed, open Claude Code in any project directory and type:

```
/aa-ma-plan "describe your task"
```

## The five files

<p align="center">
  <img src="docs/images/five-files.png" alt="The five AA-MA files" width="800">
</p>

Every AA-MA task lives in `.claude/dev/active/[task-name]/` and consists of:

| File | What it holds |
|------|---------------|
| `plan.md` | Strategy, rationale, high-level constraints |
| `reference.md` | Immutable facts: APIs, paths, constants, schemas |
| `context-log.md` | Decision history, trade-offs, gate approvals |
| `tasks.md` | Execution roadmap with status tracking and dependencies |
| `provenance.log` | Commit history, session checkpoints, audit trail |

The separation matters. Reference holds things that don't change. Context-log holds why you chose what you chose. Tasks holds where you are right now. When an agent picks up a new session, it loads reference and tasks first, and only pulls in the rest when it needs to make a decision.

## What makes this different

Most approaches to LLM memory boil down to "put more stuff in CLAUDE.md." AA-MA goes further. The five files are the foundation, but the real substance is in the planning, execution, and safety layers built on top.

At a glance:

- **11 mandatory planning outputs** per task, from executive summary through rollback strategy to risk register
- **6-angle adversarial verification** that attacks the plan before a single line of code is written
- **HITL/AFK task dispatch** so the agent knows which tasks need you and which it can run alone
- **Compaction-safe memory** that survives Claude Code's context window resets

### Planning that doesn't hand-wave

"We'll figure it out as we go" is how projects die. Every AA-MA plan ships with a rollback strategy, risk register, and acceptance criteria you could turn into test assertions.

The `/aa-ma-plan` command produces structured plans with **11 mandatory outputs**:

1. Executive summary
2. Stepwise implementation plan
3. Milestones with measurable goals
4. Acceptance criteria per step
5. Required artefacts
6. Tests to validate
7. Rollback strategy
8. Dependencies and assumptions
9. Effort estimates with complexity scores
10. Top 3 risks per milestone
11. The concrete next action

If you can't write a pytest assertion from the acceptance criteria, they're not specific enough.

Before execution begins, `/verify-plan` attacks the plan from **6 independent angles** using parallel agents:

- **Ground-truth audit**: do the files and APIs referenced in the plan actually exist?
- **Assumption extraction and challenge**: what are we taking for granted, and what breaks if we're wrong?
- **Impact analysis**: what ripples through the system when we change these files?
- **Acceptance criteria falsifiability**: can each criterion be tested with a single assertion?
- **Fresh-agent simulation**: could an agent with no prior context execute this plan?
- **Specialist domain audit**: are there domain-specific risks the generalist missed?

CRITICALs block execution in automated mode. The verification report persists as an audit trail.

Tasks with a **complexity score at or above 80%** (calculated from a weighted 5-factor algorithm covering scope, architectural impact, technical risk, dependencies, and requirements ambiguity) automatically route to deeper review: human sign-off, chain-of-thought reasoning, or both.

See a complete set of real plan artefacts in [examples/](examples/aa-ma-team-guide/).

### Execution that knows when to stop

The agent knows which tasks need you and which it can handle alone.

Every task carries a **mode**: HITL (human in the loop) or AFK (away from keyboard). The agent auto-dispatches AFK tasks without interruption. HITL tasks pause and wait for your input. Architectural decisions, scope changes, and irreversible actions are HITL. Implementation from clear specs, test writing, and mechanical refactoring are AFK. You decide which is which at planning time.

Milestones carry a **gate classification**: SOFT (convention-based, the agent seeks approval) or HARD (artefact-enforced, the execution command refuses to advance without a signed approval entry in the context log). Production deployments and architectural decisions get HARD gates. Routine milestones get SOFT.

Here's what a real execution roadmap looks like:

```markdown
## Milestone 2: Authentication API
- Status: ACTIVE
- Gate: HARD
- Dependencies: Milestone 1
- Complexity: 65%
- Acceptance Criteria: JWT tokens issued on login, refresh flow works, tests pass

### Task 2.1: Implement token endpoints
- Status: COMPLETE
- Mode: AFK
- Result Log: Created /auth/login and /auth/refresh, 12 tests passing

### Task 2.2: Review security model with user
- Status: PENDING
- Mode: HITL
- Acceptance Criteria: User confirms token expiry policy and scope design
```

### Memory that survives compaction

Claude Code compacts its context window when it fills up. Without intervention, your agent's working memory vanishes mid-task.

Three mechanisms prevent that:

- **Compaction hook**: `pre-compact-aa-ma.sh` intercepts the compaction event, snapshots the current task state to a cache file, and writes checkpoint entries to the task's `provenance.log` and `context-log.md`. The next session reads those entries and knows exactly where to resume.
- **Priority-based loading**: reference and tasks load first because they carry the highest-value context (immutable facts and current execution state). The context log and plan load only when the agent needs to make a decision or review strategy. The agent gets the most important context even when tokens are tight.
- **Sync discipline**: after every completed task, the agent syncs four of the five files (tasks, reference, context log, and provenance) and commits. The plan file stays untouched as a historical record. No proceeding until the current state is recorded. It sounds bureaucratic. It's what keeps multi-week projects coherent.

## Typical workflow

Here's what using AA-MA looks like day to day.

```mermaid
flowchart LR
    A["/aa-ma-plan"] -->|Creates 5 files| B[Plan + Reference\n+ Context-Log\n+ Tasks + Provenance]
    B --> C["/execute-aa-ma-milestone"]
    C -->|Work · Sync · Commit| D{More\nmilestones?}
    D -->|Yes| C
    D -->|No| E["/archive-aa-ma"]
```

**Planning:**
```
/aa-ma-plan "build a REST API for user authentication"
```

Claude brainstorms with you, then creates the five AA-MA artefact files in `.claude/dev/active/auth-api/`.

> **Note:** Anthropic now ships a built-in "Ultraplan" in Claude Code. We had ours first (November 2025), but naming collisions being what they are, we renamed to `/aa-ma-plan`. The two are unrelated. [Details here](docs/ultraplan-rename-rationale.md).

**Execution:**
```
/execute-aa-ma-milestone
```

The agent reads your plan, picks up the current milestone, works through each task, syncs the files after every step, and commits. HITL (human-in-the-loop) tasks pause for your input. AFK (away-from-keyboard) tasks run on their own.

**Repeat** for each milestone until the work is done.

**Archive:**
```
/archive-aa-ma auth-api
```

Moves completed artefacts to `.claude/dev/completed/` for future reference.

### All commands

| Command | What it does |
|---------|-------------|
| `/aa-ma-plan` | Brainstorm and create a structured plan with all five artefact files |
| `/execute-aa-ma-milestone` | Execute the current milestone with strict validation and auto-commit *(recommended)* |
| `/execute-aa-ma-step` | Execute a single task with lightweight validation |
| `/execute-aa-ma-full` | Execute the entire plan from current position to completion |
| `/verify-plan` | Run adversarial verification against the plan before execution |
| `/grill-me` | Relentlessly interview you about a plan or design until every decision is resolved |
| `/ops-mode` | Activate disciplined execution mode (token efficiency, parallel eval, tool protocols) |
| `/archive-aa-ma` | Move completed artefacts to `.claude/dev/completed/` |
| `/aa-ma-search` | Keyword search across active and completed AA-MA task files |

### Skills

Skills are reusable procedures that plug into the planning and execution workflow. They live in `claude-code/skills/` and the installer symlinks them into `~/.claude/`.

| Skill | What it does |
|-------|-------------|
| `aa-ma-plan-workflow` | The 5-phase planning engine behind `/aa-ma-plan` |
| `aa-ma-execution` | Task execution contract used by the `/execute-aa-ma-*` commands |
| `plan-verification` | Adversarial 6-angle verification for plans |
| `impact-analysis` | Pre-change dependency and blast-radius analysis |
| `system-mapping` | 5-point pre-flight checklist before code changes |
| `operational-constraints` | Disciplined execution mode (token efficiency, tool protocols) |
| `retro` | Weekly engineering retrospective generator |
| `complexity-router` | Weighted complexity scoring that routes high-risk tasks to deeper review |
| `agent-teams` | Multi-agent team orchestration with roles, debate, and shutdown protocols |
| `defense-in-depth` | Four-layer validation pattern for making bugs structurally impossible |
| `dispatching-parallel-agents` | Pattern for concurrent independent agent investigations |
| `debugging-strategies` | Systematic debugging process with multi-language tooling |
| `token-compression` | Output token reduction with HITL/AFK intensity mapping (lite/full/ultra) |

Start with the [quick reference](docs/spec/aa-ma-quick-reference.md) for a five-minute overview. The [team guide](docs/spec/aa-ma-team-guide.md) covers the full workflow in detail (originally written for internal use, so some model references may be dated). To see what the five files look like in practice, check [examples/aa-ma-team-guide/](examples/aa-ma-team-guide/).

## What else helped

AA-MA is the structure, but a couple of Claude Code plugins earned their place alongside it through trial and error.

[claude-mem](https://github.com/thedotmack/claude-mem) gives Claude persistent memory across sessions. AA-MA files hold the plan and the state, but they live inside one conversation. claude-mem indexes everything (decisions, tool results, observations) into a searchable vector store that survives session boundaries. When you pick up a multi-week project on a Monday morning, it's the difference between starting cold and starting informed.

[double-check](https://claudecodecommands.directory/commands/double-check) is almost embarrassingly simple: it forces the agent to stop and ask itself "am I actually done?" before moving on. Define the angles, define what complete means, then check. It catches the false positives that slip through when agents optimistically claim a task is finished. Cheap, fast, and surprisingly effective.

Neither is required for AA-MA to work. Both made it work better.

## Optional extras

Some AA-MA commands can use these third-party Claude Code plugins when available. Everything works without them. They just make it better.

| Plugin | What it enhances | Install |
|--------|-----------------|--------|
| [superpowers](https://github.com/superpowers-marketplace/superpowers) | Brainstorming, structured planning, TDD workflows in `/aa-ma-plan` and execute commands | Claude Code plugin marketplace |
| [gstack](https://github.com/anthropics/claude-code-marketplace) | Plan reviews (CEO, eng, design perspectives), QA testing, browser screenshots | Claude Code plugin marketplace |
| [Context7](https://github.com/upstash/context7) | Library documentation lookup during planning and execution | MCP server setup |

If a plugin isn't installed, the commands fall back to native tools or skip the optional step.

## Companion tools and the token stack

AA-MA handles structured task memory. Three community tools handle the layers around it: CLI noise, output verbosity, and cross-session recall.

```
Layer 4: TASK MEMORY      AA-MA (structured files, priority loading, gates)
Layer 3: SESSION MEMORY   MemPalace (ChromaDB, cross-session recall)
Layer 2: OUTPUT TOKENS    Caveman (prompt compression, ~65% reduction)
Layer 1: CLI TOKENS       RTK (CLI proxy, ~89% noise reduction)
```

| Tool | What it does |
|------|-------------|
| [RTK](https://github.com/rtk-ai/rtk) | Rust CLI proxy that sits between your shell and the context window. Intercepts git, cargo, pytest and strips the noise. 60-90% fewer tokens wasted on test pass lines and ANSI junk. |
| [Caveman](https://github.com/JuliusBrussee/caveman) | Makes Claude talk like a smart caveman. Drops articles, filler, pleasantries. Technical accuracy stays. Token bill drops ~65%. |
| [MemPalace](https://github.com/milla-jovovich/mempalace) | Local-first memory system with ChromaDB for semantic search across past sessions. 19 MCP tools, roughly 170 tokens to recall everything. |

None are required. AA-MA works without any of them.

### What we adopted

Digging through these codebases led to real improvements in AA-MA Forge (April 2026):

- **From Caveman**: output compression patterns, forked into the `token-compression` skill with intensity mapped to HITL/AFK execution modes
- **From MemPalace**: temporal validity for facts, adapted as lightweight `[valid: date]` markers in reference.md
- **From RTK and Caveman**: hook architecture patterns, used for the SessionStart hook that auto-detects active tasks

Attribution lives in the relevant skill and spec files.

## Credits and inspirations

Original work by Stephen J. Newhouse, November 2025 onwards. Built out of genuine frustration with context loss in agentic coding workflows.

The spark came from [Diet-Coder's](https://dev.to/diet-code103/claude-code-is-a-beast-tips-from-6-months-of-hardcore-use-572n) brilliant "Dev Docs System" (also on [r/ClaudeCode](https://www.reddit.com/r/ClaudeCode/comments/1oivs81/claude_code_is_a_beast_tips_from_6_months_of/)): three files per task that give Claude structured memory. I took those three files and turned them into five. Massive thanks to Diet-Coder for planting the seed.

Matt Pocock's [skills repo](https://github.com/mattpocock/skills) inspired several refinements to the command and skill structure. AA-MA predates it, but the cross-pollination was valuable.

[Helix.ml](https://helix.ml) spec-driven workflow concepts informed the v2.1 specification, particularly around gate classification and session checkpoints.

The full story is in [how we got here](docs/narrative/how-we-got-here.md), and the shorter version is on [dev.to](https://dev.to/snewhouse/my-ai-agent-keeps-forgetting-everything-3p2k).

## Fair warning

This is a one-person project built around my own workflows. It's provided as-is. Take what's useful, fork it, adapt it, make it your own. Maintenance and improvements will be sporadic. If I've gone quiet, I'm either deep in client work, arguing with an API, or the MS is having a louder day than usual. Pull requests welcome, but don't hold your breath on response times. You've been warned.

## Licence

[Apache-2.0](LICENSE)

### A little request...

I have multiple sclerosis. Some days are better than others, but the work continues regardless. If AA-MA saves you time or sanity, consider donating to an MS charity like the [MS Society](https://www.mssociety.org.uk/) or [MS Trust](https://mstrust.org.uk/).

Other causes close to my heart: [NSPCC](https://www.nspcc.org.uk/) and [NAPAC](https://napac.org.uk/) for child protection, [Refuge](https://refuge.org.uk/) and [ManKind Initiative](https://mankind.org.uk/) for domestic abuse survivors. Or just hug someone who needs it. Small acts, big ripples.
