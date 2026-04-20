# Changelog

All notable changes to this project will be documented in this file.

This project adheres to [Semantic Versioning](https://semver.org/).

## Unreleased

### Added

- `claude-code/hooks/lib/aa-ma-parse.sh` shared helper library: 5 exports (`aa_ma_is_disabled`, `aa_ma_extract_active_milestone`, `aa_ma_extract_active_step`, `aa_ma_list_active_tasks`, `aa_ma_debug`); format-agnostic Status regex; HTML-comment false-positive guard
- `tests/hooks/` bats test harness: fixture builder with self-tests, helper tests, hook integration tests. CI job via `bats-core/bats-action@v4`
- feat(hooks): commit-signature enforcement hook (PreToolUse/Bash): blocks unsigned `git commit` when an AA-MA plan is active. `[ad-hoc]` marker on its own line bypasses (auditable in git log). Word-boundary match distinguishes `git commit-tree`/`commit-graph`. Pretty stderr block message naming top active task.
- feat(hooks): SessionEnd dirty detector (`aa-ma-session-end-dirty.sh`): warns when AA-MA artifacts are git-dirty at session end. Advisory-only; silent in CI (`CLAUDE_CODE` unset).
- feat(hooks): PostToolUse drift detector (`aa-ma-commit-drift.sh`): warns when a git commit lands without touching any active task's `tasks.md`/`provenance.log`. `[no-sync-check]` marker bypasses. `AA_MA_DRIFT_THRESHOLD` env var (default 1) tunes sensitivity.
- `AA_MA_HOOKS_DISABLE=1` master kill switch: all AA-MA hooks early-exit 0 silently
- `HOOK_DEBUG=1` diagnostic mode: verbose stderr traces from `aa_ma_debug`
- README "AA-MA hook troubleshooting" section: kill switch, bypass markers, known scope limits, local bats install
- install.sh now registers 5 hooks idempotently: SessionStart, PreCompact, PreToolUse(Bash), SessionEnd, PostToolUse(Bash) — only those whose source files exist, with path-substring idempotence (works with both `<path>` and `bash <path>` command forms)
- install.sh preflight: fails cleanly with install instructions if `jq` missing
- install.sh symlinks helper library `aa-ma-parse.sh` into `~/.claude/hooks/lib/` so hooks can source it from their installed sibling path

### Changed

- `aa-ma-session-start.sh`: now surfaces the most-recently-touched task (was alphabetical-last); emits absolute resolved path (was hardcoded relative fragment); appends `(N other active tasks: a, b, c and M more)` footer when >1 active task; sources shared helper
- `pre-compact-aa-ma.sh`: now iterates both project-local AND `$HOME/.claude/dev/active/` (was HOME-only); project-first collision resolution; uses format-agnostic Status parser (was plain-only, missed bold-format templates); honours kill switch
- `uninstall.sh`: extended to deregister all 5 AA-MA hooks (was SessionStart only); path-substring match normalises `<path>` and `bash <path>` forms
- `docs/templates/tasks-template.md`: Status format canonicalised to plain `Status: X` (was bold `**Status:** X`) — helper tolerates both via defence-in-depth regex
- `claude-code/agents/aa-ma-scribe.md`: template block Status format canonicalised to plain
- All AA-MA hooks now resolve helper library via dual-layout probe (project subdir OR installed sibling), robust to symlink vs direct invocation
- `claude-code/commands/execute-aa-ma-milestone.md`: new Section 7.2.5 Post-Completion Validator Dispatch. After Section 7.2 doc auto-update and before Section 7.3 user approval, auto-dispatches `aa-ma-validator` agent to audit the just-updated artifacts against 6 dimensions (existence, plan completeness, reference completeness, HTP structure, cross-file consistency, completeness-claim accuracy). Three-verdict handling: READY_FOR_ARCHIVE proceeds; WARNINGS_BUT_USABLE back-fills inline (avoiding a separate post-archive audit commit); GAPS_REQUIRE_FIX halts. Graceful-skip fallback when agent spawning unavailable. Rationale: catches Result Log placeholders, missing commit SHAs, and missing MERGE_TO_MAIN events in-flight instead of requiring back-fill commits post-archive. Pattern derived from go-biological-process-disease-support 2026-04-20 sprint audit (3 WARN items that required back-fill commit `d424ef8` before archive).

### Fixed

- Silent correctness bug in `pre-compact-aa-ma.sh`: previously `grep 'Status: ACTIVE'` never matched bold `**Status:** ACTIVE` template output — CHECKPOINT entries always emitted "active step: unknown"
- Silent path-emission bug in `aa-ma-session-start.sh:72`: hardcoded `.claude/dev/active/` path even when task lived in `$HOME` — Claude would try to read non-existent project-local path
- Silent mtime-ordering bug in `aa-ma-session-start.sh:34-38`: loop picked alphabetical-last task despite comment claiming "most recently modified"
- Pre-existing `install.sh` gap: PreCompact hook symlinked but never registered in `settings.json` — fixed in the same multi-hook registration loop

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
