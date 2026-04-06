# Changelog

All notable changes to this project will be documented in this file.

This project adheres to [Semantic Versioning](https://semver.org/).

## Unreleased

### Changed

- Renamed `/ultraplan` command to `/aa-ma-plan` to avoid collision with Anthropic's built-in Ultraplan feature (shipped 2026-04-04)
- Renamed `ultraplan-workflow` skill to `aa-ma-plan-workflow`
- Updated all cross-references across commands, skills, agents, specs, and documentation
- See `docs/ultraplan-rename-rationale.md` for full context and comparison

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
