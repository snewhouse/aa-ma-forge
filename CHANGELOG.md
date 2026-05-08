# Changelog

All notable changes to this project will be documented in this file.

This project adheres to [Semantic Versioning](https://semver.org/).

## v0.4.0 (2026-05-08)

### Feat

- **codemem**: yek adapter + 5-tool harness (M2c)
- **codemem**: Repomix adapter (M2b)
- **codemem**: live 3-tool fairness harness (M2a)
- **aa-ma-plan-workflow**: add Mode/Gate/Baseline fields to plan template
- **codemem-token-benchmarks**: M3 Task 3.1 COMPLETE — fastapi pinned + sweep orchestrator
- **codemem-token-benchmarks**: M2 Task 2.6 GREEN — integration test
- **codemem-token-benchmarks**: M2 Task 2.5 GREEN — full CLI benchmark harness
- **codemem-token-benchmarks**: M2 Task 2.4 RED — tiktoken normalization tests
- **codemem-token-benchmarks**: M2 Task 2.3 GREEN — inline Aider prose parser
- **codemem-token-benchmarks**: M2 Task 2.2 RED — parser tests + golden Aider fixture
- **execute-aa-ma-milestone**: add Section 7.2.5 Post-Completion Validator Dispatch
- **codemem-token-benchmarks**: M2 Task 2.1 COMPLETE — add tiktoken dev dep
- **codemem-token-benchmarks**: M1 COMPLETE — Task 1.3 scope decision + milestone finalization
- **codemem-token-benchmarks**: M1 Task 1.2 COMPLETE — smoke tests + 1 AC reframe
- **codemem-token-benchmarks**: M1 Task 1.1 COMPLETE — pinned tool installs verified
- **aa-ma**: new plan — codemem-token-benchmarks (executes DEFERRED Task 4.2)
- **codemem**: M4 COMPLETE — review-response patch (5 fixes) + milestone finalization
- **codemem**: M4 Task 4.6 — codemem-scoped doc-drift hook + test gate
- **codemem**: M4 Task 4.8 — zero-config install + co_changes demo (L-254 fix)
- **codemem**: M3.5 COMPLETE — fix L-253 apply_schema-without-migrate defect
- **codemem**: M3.5 Task 3.5.3 — auto-build-on-first-query
- **codemem**: M3.5 Task 3.5.2 — integration tests prove 14 tools reachable via FastMCP
- **codemem**: M3.5 Task 3.5.1 — wire 6 M3 tools into FastMCP server
- **codemem**: M4 Task 4.7 — CI smoke test + ast-grep drift check
- **codemem**: M4 Task 4.1 — perf bench script + aa-ma-forge measurements
- **codemem**: M3 Task 3.7 — aa_ma_context() moat tool (326/326)
- **codemem**: M3 Task 3.6 — layers() MCP tool (318/318)
- **codemem**: M3 Task 3.5 — symbol_history() MCP tool (308/308)
- **codemem**: M3 Task 3.4 — owners() MCP tool (301/301)
- **codemem**: M3 Task 3.3 — co_changes() MCP tool (291/291)
- **codemem**: M3 Task 3.2 — hot_spots() MCP tool (279/279)
- **codemem**: M3 Task 3.1 — git mining base layer (269/269)
- **codemem**: M3 Task 3.8 — schema v2 migration (254/254)
- **codemem**: M2 Task 2.8 + M2 COMPLETE — WAL rotation (227/227)
- **codemem**: M2 Tasks 2.6 + 2.7 — WAL checkpoint + writer lock (217/217)
- **codemem**: M2 Task 2.5 — post-commit storm control + 4 tests (208/208)
- **codemem**: M2 Task 2.4 — WAL replay + round-trip property test
- **codemem**: M2 Task 2.3 — WAL JSONL journal + 14 tests (201/201)
- **codemem**: M2 Task 2.2 — incremental refresh driver + 10 tests (187/187)
- **codemem**: M2 Task 2.1 — symbol-set diff + 14 tests (177/177)
- **codemem**: M1 Tasks 1.12 + 1.13 — ARCHITECTURE.md + perf SLOs (M1 COMPLETE)
- **codemem**: M1 Task 1.11 — install wiring + import-linter + CLI + 11 tests
- **codemem**: M1 Task 1.10 — FastMCP server + aliases + 8 tests (152/152)
- **codemem**: M1 Task 1.8 — pure-Python PageRank + PROJECT_INTEL.json (144/144)
- **codemem**: M1 Task 1.7 — 6 MCP tools + sanitizers + canonical CTE (131/131)
- **codemem**: M1 Task 1.6 — 4-strategy cross-file resolver + 11 tests (98/98)
- **codemem**: M1 Task 1.5 — indexer driver + 15 tests (87/87 suite green)
- **codemem**: M1 Task 1.4 — ast-grep wrapper + 8 YAML rule files + 36 tests
- **codemem**: M1 Task 1.3 — Python stdlib `ast` parser + 20 tests passing
- **codemem**: M1 Task 1.2 — SQLite schema v1 + db.py + 16 tests passing
- **codemem**: M1 Task 1.1 — scaffold + dual-distribution packaging verified
- **codemem**: M1 Task 1.0 complete — packaging=uv_workspace, plan v3→v4
- **codemem**: AA-MA plan v3 — 41 tasks across 4 milestones, 12 MCP tools
- **hooks**: M5 post-commit drift detector — plan complete
- **hooks**: M4 SessionEnd dirty AA-MA detector
- **hooks**: M3 commit-signature + install.sh + docs + canonicalization
- **hooks**: M2 fix shipped hooks (mtime + path + both-paths)
- **hooks**: M1 foundations — bats harness + shared parser + CI

### Fix

- **codemem**: honest tiktoken budget enforcement (M1)
- **codemem-token-benchmarks**: resolve OBS-001 — add codemem-mcp to dev-deps
- **codemem**: M3.5 Task 3.5.5 — ship project-scope .mcp.json (Option B); L-244 files defect
- **hooks**: resolve helper across symlinked + project layouts

### Refactor

- **codemem**: M3.5 Task 3.5.4 — remove wheel MCP-server channel (AD-Q15)

## v0.3.0 (2026-04-10)

### Feat

- **spec**: add temporal validity markers for reference.md facts
- **commands**: add /aa-ma-search cross-task keyword search command
- **hooks**: add SessionStart hook with auto-detection and settings.json registration
- **skills**: add token-compression skill with HITL/AFK intensity mapping
- **execution**: implement HITL/AFK mode dispatch in execution skill and commands

### Fix

- **hooks**: write compaction entries to task provenance.log and context-log.md
- **docs**: correct two factual inaccuracies in README

## v0.2.0 (2026-04-07)

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
