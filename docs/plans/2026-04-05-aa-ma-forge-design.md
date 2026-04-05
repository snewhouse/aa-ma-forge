# aa-ma-forge: Ecosystem Design

**Date:** 2026-04-05
**Author:** Stephen J Newhouse
**Status:** Approved

## What this is

The canonical home for the Advanced Agentic Memory Architecture (AA-MA), a structured external memory system I built for Claude Code. It solves a real problem: LLM agents lose context across sessions, drift from plans, and forget what they've already done. AA-MA prevents that with five specialised files that segment knowledge, state, and history.

This repo packages everything into one place: the specification, the Claude Code integration artifacts, a Python tooling package, and the story of how it all came together.

## Audience

Primarily me. Structured so others can fork it, learn from it, or adapt it. This may evolve into a distributable framework, but we're not optimising for that yet.

## Repository structure

```
aa-ma-forge/
├── docs/
│   ├── narrative/
│   │   └── how-we-got-here.md       # The origin story
│   ├── spec/
│   │   ├── aa-ma-specification.md    # v2.1 canonical spec
│   │   ├── aa-ma-quick-reference.md  # 2-page cheat sheet
│   │   └── aa-ma-team-guide.md       # Adoption guide
│   ├── architecture/                 # ADRs, design decisions
│   └── images/                       # Diagrams
├── src/aa_ma/
│   ├── __init__.py
│   ├── validators/                   # Plan/task validators
│   ├── schemas/                      # Pydantic models for the 5 files
│   └── cli/                          # CLI tools
├── claude-code/
│   ├── commands/                     # 6 AA-MA commands
│   ├── skills/
│   │   └── aa-ma-execution/          # The execution skill
│   ├── agents/
│   │   ├── aa-ma-scribe.md
│   │   └── aa-ma-validator.md
│   ├── rules/
│   │   └── aa-ma.md
│   └── hooks/
│       └── pre-compact-aa-ma.sh
├── examples/
│   └── aa-ma-team-guide/             # Real completed task artifacts
├── scripts/
│   ├── install.sh                    # Symlink to ~/.claude/
│   └── uninstall.sh                  # Restore backups
├── tests/
├── pyproject.toml
├── LICENSE                           # Apache-2.0
├── README.md
└── .gitignore
```

## Key decisions

### Source of truth
This repo. Develop here, deploy to `~/.claude/` via symlink install script. Prevents drift between what's documented and what's deployed.

### Voice boundary
All prose (README, narrative, documentation for human readers) is written in my voice: UK English, no em dashes, no AI vocabulary, conversational, scientifically grounded but accessible. Technical artifacts (specs, command definitions, skill prompts, agent definitions) keep their existing instructional tone.

### Sync strategy
Symlinks with backup-first approach. `install.sh` backs up existing `~/.claude/` AA-MA files, then symlinks from the repo. `uninstall.sh` restores the backups. Spec docs get copied (not symlinked) because `~/.claude/docs/` contains non-AA-MA docs.

### Python package
Skeleton on day one (`src/aa_ma/`, `pyproject.toml` with uv). Room for validators, Pydantic schemas, and CLI tools. Complements the Claude Code artifacts without duplicating them.

### License
Apache-2.0.

## Content scope (first pass)

**In:**
- Full import of all 18 AA-MA files from `~/.claude/`
- Origin story narrative (new, written from scratch)
- README (new)
- Install/uninstall scripts (new)
- Python package skeleton (new)
- Example completed task artifacts
- Apache-2.0 licence

**Out:**
- Personal config (CLAUDE.md, settings.json)
- Non-AA-MA skills, commands, or rules
- Active task directories
- Claude-mem data or session history
- Web UI, server, database

## Inspirations (properly credited)

AA-MA is mostly original work, built from November 2025 onwards through hands-on experimentation with Claude Code.

- **Reddit post** on agentic memory: early catalyst (link TBD)
- **Matt Pocock's skills repo** (github.com/mattpocock/skills): inspired refinements to skills structure and the `/grill-me` approach. AA-MA predates this repo.
- **Helix.ml**: spec-driven workflow research that inspired v2.1 concepts (HARD/SOFT gates, tests.yaml, CHECKPOINT format). Concepts only, no code or text was reproduced. These are standard software engineering patterns (approval gates, executable tests, session checkpoints) with original implementations.

## What's not being built

- No web UI, server, or database
- No duplication of Claude Code command/skill functionality in Python
- No packaging for distribution (yet)

## Next steps

Transition to implementation planning via AA-MA workflow.
