# AA-MA Forge

Structured external memory for Claude Code, so your AI agent stops forgetting what it's done.

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

## What AA-MA is

AA-MA (Advanced Agentic Memory Architecture) gives Claude Code a structured external memory built from five specialised files. Each file segments a different kind of knowledge: strategy, facts, decisions, execution state, and audit history. It's designed for long-horizon, multi-session tasks where context loss kills productivity.

## What's in this repo

```
docs/spec/          The specification (v2.1), quick reference, team guide,
                    and Claude Code foundations reference
docs/narrative/     The origin story (how and why AA-MA exists)
claude-code/        Commands, skill, agents, rules, hooks
                    (the operational layer that plugs into Claude Code)
src/aa_ma/          Python package: validators, schemas, CLI (growing)
examples/           Real completed task artefacts (the five files in action)
scripts/            install.sh / uninstall.sh
```

## Quick start

```bash
git clone https://github.com/snewhouse/aa-ma-forge.git
cd aa-ma-forge
scripts/install.sh --dry-run  # preview what will be deployed
scripts/install.sh            # deploy to ~/.claude/
```

The installer creates symlinks from this repo into your `~/.claude/` directory. It backs up any existing files before touching them. Run `scripts/uninstall.sh` to reverse everything.

## The five files

Every AA-MA task lives in `.claude/dev/active/[task-name]/` and consists of:

| File | What it holds |
|------|---------------|
| `plan.md` | Strategy, rationale, high-level constraints |
| `reference.md` | Immutable facts: APIs, paths, constants, schemas |
| `context-log.md` | Decision history, trade-offs, gate approvals |
| `tasks.md` | Execution roadmap with status tracking and dependencies |
| `provenance.log` | Commit history, session checkpoints, audit trail |

The separation matters. Reference holds things that don't change. Context-log holds why you chose what you chose. Tasks holds where you are right now. When an agent picks up a new session, it loads reference and tasks first, and only pulls in the rest when it needs to make a decision.

## Typical workflow

Here's what using AA-MA looks like day to day.

**Planning:**
```
/aa-ma-plan "build a REST API for user authentication"
```

Claude brainstorms with you, then creates the five AA-MA artefact files in `.claude/dev/active/auth-api/`.

> **Note:** As of April 2026, Anthropic ships a built-in planning feature also called "Ultraplan" in Claude Code. Our `/aa-ma-plan` command is a separate, AA-MA-specific structured planning workflow. The two are complementary — see [`docs/ultraplan-rename-rationale.md`](docs/ultraplan-rename-rationale.md).

**Execution:**
```
/execute-aa-ma-milestone
```

The agent reads your plan, picks up the current milestone, works through each task, syncs the files after every step, and commits. HITL tasks pause for your input. AFK tasks run on their own.

**Repeat** for each milestone until the work is done.

**Archive:**
```
/archive-aa-ma auth-api
```

Moves completed artefacts to `.claude/dev/completed/` for future reference.

For the full details, see the [team guide](docs/spec/aa-ma-team-guide.md) and [quick reference](docs/spec/aa-ma-quick-reference.md). A real-world example of completed artefacts is in [examples/aa-ma-team-guide/](examples/aa-ma-team-guide/).

## Credits and inspirations

Original work by Stephen J. Newhouse, November 2025 onwards. Built out of genuine frustration with context loss in agentic coding workflows.

The spark came from [Diet-Coder's](https://dev.to/diet-code103/claude-code-is-a-beast-tips-from-6-months-of-hardcore-use-572n) brilliant "Dev Docs System" (also on [r/ClaudeCode](https://www.reddit.com/r/ClaudeCode/comments/1oivs81/claude_code_is_a_beast_tips_from_6_months_of/)): three files per task that give Claude structured memory. I took those three files and turned them into five. Massive thanks to Diet-Coder for planting the seed.

Matt Pocock's [skills repo](https://github.com/mattpocock/skills) inspired several refinements to the command and skill structure. AA-MA predates it, but the cross-pollination was valuable.

[Helix.ml](https://helix.ml) spec-driven workflow concepts informed the v2.1 specification, particularly around gate classification and session checkpoints.

The full story is in [how we got here](docs/narrative/how-we-got-here.md).

## Supporting the project

I have multiple sclerosis. Some days are better than others, but the work continues regardless. If AA-MA saves you time or sanity, consider donating to an MS charity like the [MS Society](https://www.mssociety.org.uk/) or [MS Trust](https://mstrust.org.uk/). Or support a child protection organisation like the [NSPCC](https://www.nspcc.org.uk/) or [NAPAC](https://napac.org.uk/), who support adult survivors of childhood abuse. If domestic abuse has touched your life, [Refuge](https://refuge.org.uk/) and the [ManKind Initiative](https://mankind.org.uk/) are there for women and men respectively. Or simply buy a stranger a coffee. Small acts, big ripples.

## Fair warning

This is a one-person project built around my own workflows. Maintenance and improvements will be sporadic. If I've gone quiet, I'm either deep in client work, arguing with an API, or the MS is having a louder day than usual. Pull requests welcome, but don't hold your breath on response times. You've been warned.

## Licence

[Apache-2.0](LICENSE)
