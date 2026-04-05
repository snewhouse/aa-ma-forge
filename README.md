# AA-MA Forge

Structured external memory for Claude Code, so your AI agent stops forgetting what it's done.

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

## Credits and inspirations

Original work by Stephen J. Newhouse, November 2025 onwards. Built out of genuine frustration with context loss in agentic coding workflows.

Early catalyst: a Reddit post on agentic memory patterns that crystallised the idea of separating mutable state from immutable facts.

Matt Pocock's [skills repo](https://github.com/mattpocock/skills) inspired several refinements to the command and skill structure. AA-MA predates it, but the cross-pollination was valuable.

[Helix.ml](https://helix.ml) spec-driven workflow concepts informed the v2.1 specification, particularly around gate classification and session checkpoints.

## Supporting the project

I have multiple sclerosis. Some days are better than others, but the work continues regardless. If AA-MA saves you time or sanity, consider donating to an MS charity like the [MS Society](https://www.mssociety.org.uk/) or [MS Trust](https://mstrust.org.uk/). Or support a child protection organisation like the [NSPCC](https://www.nspcc.org.uk/) or [NAPAC](https://napac.org.uk/), who support adult survivors of childhood abuse. If domestic abuse has touched your life, [Refuge](https://refuge.org.uk/) and the [ManKind Initiative](https://mankind.org.uk/) are there for women and men respectively. Or simply buy a stranger a coffee. Small acts, big ripples.

## Fair warning

This is a one-person project built around my own workflows. Maintenance and improvements will be sporadic. If I've gone quiet, I'm either deep in client work, arguing with an API, or the MS is having a louder day than usual. Pull requests welcome, but don't hold your breath on response times. You've been warned.

## Licence

[Apache-2.0](LICENSE)
