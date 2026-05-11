<!-- ARCHIVED: 2026-04-10 21:35 -->
<!-- Plan: token-stack-integration - COMPLETE -->
<!-- Total Milestones: 5 | Duration: 2026-04-10 to 2026-04-10 -->

# token-stack-integration Reference

## Immutable Facts and Constants

_These are non-negotiable facts extracted from the plan and research._

### Source Repositories (Local Clones)

| Tool | Local Path | Key Reference File |
|------|-----------|-------------------|
| Caveman | `~/github_private/caveman/` | `skills/caveman/SKILL.md` (prompt patterns to fork) |
| MemPalace | `~/github_private/mempalace/` | `hooks/mempal_save_hook.sh` (auto-save pattern) |
| RTK | `~/github_private/rtk/` | `hooks/claude/rtk-rewrite.sh` (PreToolUse hook pattern) |

### API Endpoints

_None. This task creates no API endpoints and consumes no external APIs._

### File Paths -- To Create

| File | Milestone | Type |
|------|-----------|------|
| `claude-code/skills/token-compression/SKILL.md` | M1 | NEW skill |
| `claude-code/hooks/aa-ma-session-start.sh` | M2 | NEW hook |
| `claude-code/hooks/pre-compact-aa-ma.sh` | M2 | MODIFY — add CHECKPOINT line |
| `claude-code/commands/aa-ma-search.md` | M3 | NEW command |

### File Paths -- To Modify

| File | Milestone | Change |
|------|-----------|--------|
| `claude-code/skills/aa-ma-execution/SKILL.md` | M1 | Add token-compression integration |
| `claude-code/skills/operational-constraints/SKILL.md` | M1 | Replace vague token directive with pointer |
| `claude-code/agents/aa-ma-scribe.md` | M4 | Add temporal marker instruction |
| `claude-code/hooks/pre-compact-aa-ma.sh` | M2 | Add CHECKPOINT line to existing snapshot logic |
| `scripts/install.sh` | M2 | Register SessionStart hook (symlink + settings.json) |
| `scripts/uninstall.sh` | M2 | Unregister SessionStart hook |
| `docs/spec/aa-ma-specification.md` | M3, M4 | Add Cross-Task Search section + temporal markers |
| `docs/templates/reference-template.md` | M4 | Add temporal marker examples |
| `README.md` | M5 | Add Companion Tools section |
| `CHANGELOG.md` | M5 | Add entries for new assets |
| `SECURITY.md` | M5 | Update asset counts |
| `docs/spec/claude-code-foundations.md` | M5 | Update asset counts |
| `docs/spec/aa-ma-quick-reference.md` | M5 | Update asset counts |

### Configuration

| Key | Value | Context |
|-----|-------|---------|
| Active tasks directory | `.claude/dev/active/[task-name]/` | SessionStart hook scans this |
| Completed tasks directory | `.claude/dev/completed/[task-name]/` | Search command scans this |
| Existing hook | `claude-code/hooks/pre-compact-aa-ma.sh` | PreCompact event, not to be disturbed |

### Dependencies

_Zero new runtime dependencies. All artifacts are markdown files and shell scripts._

| Existing Dependency | Purpose |
|--------------------|---------|
| `shellcheck` | Validation of new .sh hook files |
| `uv` | Python package management (existing) |
| `rtk` | Already installed, no changes needed |

### Constants

| Constant | Value | Context |
|----------|-------|---------|
| Compression level: lite | HITL mode mapping | Interactive sessions, preserve clarity |
| Compression level: full | General use mapping | Default compression |
| Compression level: ultra | AFK mode mapping | Autonomous execution, maximum compression |
| SessionStart hook max latency | <100ms | Performance constraint |
| PreCompact CHECKPOINT | Added to existing hook | No new file — enhances pre-compact-aa-ma.sh |
| Hook exit code | Always 0 | Never block session start/stop |
| Search default scope | `--active` | Only active tasks unless specified |

### Temporal Marker Formats

| Format | Meaning |
|--------|---------|
| `[valid: YYYY-MM-DD]` | Fact valid from this date onward |
| `[valid: YYYY-MM-DD to YYYY-MM-DD]` | Fact valid within date range |
| `[superseded: YYYY-MM-DD by task-name]` | Fact replaced by newer task |

### Hook Event Types

| Event | Script | Behavior |
|-------|--------|----------|
| `PreCompact` | `pre-compact-aa-ma.sh` | Existing -- snapshots active tasks before context shrink |
| `SessionStart` | `aa-ma-session-start.sh` | NEW -- emits hidden context with active task state |
| `PreCompact` (enhanced) | `pre-compact-aa-ma.sh` | MODIFIED — adds CHECKPOINT line alongside existing snapshot logic |

### Project Context

| Fact | Value |
|------|-------|
| Project | aa-ma-forge |
| Branch | `expt/rocket_mems_playground` |
| HEAD at plan time | `24aa245` |
| Owner | Stephen Newhouse |
| Plan date | 2026-04-10 |

### Asset Counts (Pre-Change Baseline)

| Asset Type | Current Count | After This Task |
|-----------|--------------|-----------------|
| Skills | 12 | 13 (+token-compression) |
| Hooks | 1 | 2 (+session-start; pre-compact-aa-ma.sh enhanced, not new) |
| Commands | 8 | 9 (+aa-ma-search) |
| Agents | 2 | 2 (no change, scribe modified only) |

### Discovered Facts (During Execution)

| Fact | Value | Discovered |
|------|-------|------------|
| Caveman SKILL.md line count | 63 lines (source for fork) | [valid: 2026-04-10] |
| aa-ma-execution Mode section | Lines 228-257, Section 7 | [valid: 2026-04-10] |
| operational-constraints Section 1 | British spelling "Optimise" (not American) | [valid: 2026-04-10] |

_Last Updated: 2026-04-10_
