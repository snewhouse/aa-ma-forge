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
- 5 additional skills: `complexity-router`, `agent-teams` (with references and templates), `defense-in-depth`, `dispatching-parallel-agents`, `debugging-strategies`
- verification.md documentation: anatomy in spec, template (`docs/templates/`), example (`examples/verification-example/`)
- `docs/ATTRIBUTION.md`: formal provenance mapping of all external influences (Diet-Coder, Matt Pocock, Helix.ml, gstack, superpowers, claude-mem, double-check, Context7) with "What's Original" section
- Standalone templates for all 7 AA-MA files in `docs/templates/` (plan, reference, context-log, tasks, provenance, tests, verification) with HTML comment instructions and placeholder syntax
- Attribution note in `retro/SKILL.md` crediting gstack integration
- Dependency note in `aa-ma-plan-workflow/SKILL.md` documenting superpowers as optional dependency
- Origin notes in 3 session-derived skills (dispatching-parallel-agents, defense-in-depth, debugging-strategies)
- Templates index (`docs/templates/README.md`) explaining how to use each template
- Dedicated anatomy sections in spec for reference.md, context-log.md, and provenance.log (previously underdocumented)
- tests.yaml example (`examples/aa-ma-team-guide/aa-ma-team-guide-tests.yaml`) completing the example set
- Skills table in README (13 skills documented)
- README banner image and five-files visual (green/orange, dark background)
- Mermaid workflow lifecycle diagram in README
- "What else helped" section documenting claude-mem and double-check plugins
- "Optional extras" section documenting superpowers, gstack, and Context7 MCP dependencies
- Post-install bridge in Quick Start ("open Claude Code and type /aa-ma-plan")
- Full command reference table in README (8 commands)

### Changed

- Renamed `/ultraplan` command to `/aa-ma-plan` to avoid collision with Anthropic's built-in Ultraplan feature (shipped 2026-04-04)
- Renamed `ultraplan-workflow` skill to `aa-ma-plan-workflow`
- Updated all cross-references across commands, skills, agents, specs, and documentation
- See `docs/ultraplan-rename-rationale.md` for full context and comparison
- install.sh now auto-discovers all skills via loop (was hardcoded to aa-ma-execution only)
- Expanded HITL/AFK acronyms inline in README
- Marked Python package as skeleton-only in README (honest labelling)
- Restructured charity section for clarity (MS leads, other causes get own paragraph)
- Updated claude-code-foundations.md: 6→8 commands, 1→13 skills
- Updated aa-ma-quick-reference.md: added /grill-me, /verify-plan, /archive-aa-ma, /ops-mode to cheat sheet
- Full command table in README updated to 8 commands (added /ops-mode)
- Replaced broken `senior-architect` references with "deep architectural review" in complexity-router and aa-ma-plan-workflow (senior-architect excluded as empty scaffold)

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
