# Changelog

All notable changes to this project will be documented in this file.

This project adheres to [Semantic Versioning](https://semver.org/).

## Unreleased

### Added

- `/grill-me` command: relentless plan/design interview (adapted from Matt Pocock's concept)
- `aa-ma-plan-workflow` skill: 5-phase planning workflow with references and templates (planning counterpart to aa-ma-execution)
- `operational-constraints` skill: disciplined execution mode for complex tasks (mandatory for complexity >= 60%)
- `/ops-mode` command: activate operational constraints
- 4 supporting skills: `plan-verification`, `impact-analysis`, `system-mapping`, `retro`
- README banner image and five-files visual (green/orange, dark background)
- Mermaid workflow lifecycle diagram in README
- "What else helped" section documenting claude-mem and double-check plugins
- "Optional extras" section documenting superpowers, gstack, and Context7 MCP dependencies
- Post-install bridge in Quick Start ("open Claude Code and type /aa-ma-plan")
- Full command reference table in README (7 commands)

### Changed

- Renamed `/ultraplan` command to `/aa-ma-plan` to avoid collision with Anthropic's built-in Ultraplan feature (shipped 2026-04-04)
- Renamed `ultraplan-workflow` skill to `aa-ma-plan-workflow`
- Updated all cross-references across commands, skills, agents, specs, and documentation
- See `docs/ultraplan-rename-rationale.md` for full context and comparison
- install.sh now auto-discovers all skills via loop (was hardcoded to aa-ma-execution only)
- Expanded HITL/AFK acronyms inline in README
- Marked Python package as skeleton-only in README (honest labelling)
- Restructured charity section for clarity (MS leads, other causes get own paragraph)
- Updated claude-code-foundations.md: 6→7 commands, 1→5 skills
- Updated aa-ma-quick-reference.md: added /grill-me, /verify-plan, /archive-aa-ma to cheat sheet

### Fixed

- Broken doc reference in verify-plan.md (pointed to non-existent design doc)

## v0.1.0 (2026-04-05)

Initial release of AA-MA Forge.

### Added

- AA-MA specification v2.1 (canonical spec, quick reference, team guide)
- Claude Code foundations reference (built-in vs AA-MA layer mapping)
- 6 AA-MA commands: execute-full, execute-milestone, execute-step, archive, aa-ma-plan, verify-plan
- AA-MA execution skill (1,187 lines)
- 2 specialised agents: aa-ma-scribe (plan to artifacts), aa-ma-validator (read-only validation)
- Operational rules (aa-ma.md) and compaction hook (pre-compact-aa-ma.sh)
- Origin story narrative: how-we-got-here.md
- Python package skeleton (aa_ma) with validators, schemas, and CLI placeholders
- Install/uninstall scripts with symlink deployment and backup-first strategy
- Example completed task artifacts (aa-ma-team-guide)
- Semantic versioning with commitizen and python-semantic-release
- Apache-2.0 licence
