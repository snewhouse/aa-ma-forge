<!-- ARCHIVED: 2026-04-12 17:29 UTC+01:00 -->
<!-- Plan: hooks-hardening-m1 - COMPLETE -->
<!-- Total Milestones: 5 | Duration: 2026-04-12 to 2026-04-12 -->

# hooks-hardening-m1 Reference

## Immutable Facts and Constants

_These are non-negotiable facts extracted from the plan and research. All facts carry a `[valid: 2026-04-12]` marker indicating the date of extraction._

### API / Hook Contracts (Claude Code)

Verified against Claude Code hook documentation during Wave 1 Angle 2.

| Contract | Specification | Notes |
|----------|---------------|-------|
| PreToolUse stdin JSON | `{session_id, hook_event_name, tool_name, tool_input: {command, ...}, tool_use_id}` | [valid: 2026-04-12] |
| PostToolUse stdin JSON | As PreToolUse + `tool_response` | `tool_response` shape UNDEFINED for Bash — DO NOT rely. [valid: 2026-04-12] |
| SessionEnd | Fires at session conclusion | Use this for end-of-session detection. [valid: 2026-04-12] |
| Stop | Fires per turn after each assistant response | NOT session-end; do not use for end-of-session work. [valid: 2026-04-12] |
| Matcher | Exact `tool_name` string, e.g. `"Bash"` | [valid: 2026-04-12] |
| Exit 0 | Pass (non-blocking) | [valid: 2026-04-12] |
| Exit 1 | Hook infrastructure error | Used for jq parse failure, not to block the user. [valid: 2026-04-12] |
| Exit 2 | Block with stderr sent to assistant | Used for commit-signature rejection. [valid: 2026-04-12] |

### File Paths

**Project root:** `/home/sjnewhouse/github_private/aa-ma-forge` [valid: 2026-04-12]

**To be created (10):**

| Path | Milestone | [valid] |
|------|-----------|---------|
| `claude-code/hooks/lib/aa-ma-parse.sh` | M1.3 | 2026-04-12 |
| `claude-code/hooks/aa-ma-commit-signature.sh` | M3.2 | 2026-04-12 |
| `claude-code/hooks/aa-ma-session-end-dirty.sh` | M4.1 | 2026-04-12 |
| `claude-code/hooks/aa-ma-commit-drift.sh` | M5.1 | 2026-04-12 |
| `tests/hooks/fixtures/build_active_dir.sh` | M1.1 | 2026-04-12 |
| `tests/hooks/fixtures/build_active_dir.bats` | M1.1.bis | 2026-04-12 |
| `tests/hooks/aa-ma-parse.bats` | M1.4 | 2026-04-12 |
| `tests/hooks/session-start.bats` | M2.1 | 2026-04-12 |
| `tests/hooks/pre-compact.bats` | M2.3 | 2026-04-12 |
| `tests/hooks/commit-signature.bats` | M3.1 | 2026-04-12 |
| `tests/hooks/session-end-dirty.bats` | M4.2 | 2026-04-12 |
| `tests/hooks/commit-drift.bats` | M5.2 | 2026-04-12 |

**To be modified:**

| Path | Milestone | Notes | [valid] |
|------|-----------|-------|---------|
| `claude-code/hooks/aa-ma-session-start.sh` | M2.2 | Fix line 72 path emission bug | 2026-04-12 |
| `claude-code/hooks/pre-compact-aa-ma.sh` | M2.4 | Iterate both paths via helper | 2026-04-12 |
| `scripts/install.sh` | M3.3 | Extend jq block, 5 hook registrations | 2026-04-12 |
| `scripts/uninstall.sh` | M3.3.bis | Deregister 5 hook entries | 2026-04-12 |
| `.github/workflows/security.yml` | M1.2 | Add bats job | 2026-04-12 |
| `README.md` | M3.4 | Troubleshooting section | 2026-04-12 |
| `CHANGELOG.md` | M3.4 | Unreleased entry | 2026-04-12 |
| `docs/templates/tasks-template.md` | M3.5 | Flip bold to plain at lines 35 and 80 | 2026-04-12 |
| `claude-code/agents/aa-ma-scribe.md` | M3.5 | Flip bold to plain at line 143 | 2026-04-12 |

**Pre-existing flagged (not fixed in this plan):**
- `~/.claude/hooks/lib/guard-protected-dirs.sh:14` — reads `.command` instead of `.tool_input.command` [valid: 2026-04-12]

### Configuration (Environment Variables)

| Variable | Purpose | Default | [valid] |
|----------|---------|---------|---------|
| `AA_MA_HOOKS_DISABLE` | Master kill switch. When set to `1`, all AA-MA hooks exit 0 immediately. | unset | 2026-04-12 |
| `HOOK_DEBUG` | When set to `1`, enables verbose stderr traces via `aa_ma_debug`. | unset | 2026-04-12 |
| `AA_MA_DRIFT_THRESHOLD` | M5 drift detector threshold (minimum files touched to trigger). | `1` | 2026-04-12 |
| `CLAUDE_CODE` | Used by M4 hook to detect CI context and exit 0 cleanly. | set in CC sessions | 2026-04-12 |

### Commit Message Markers

| Marker | Effect | Scope | [valid] |
|--------|--------|-------|---------|
| `[AA-MA Plan] <task-name> .claude/dev/active/<task-name>` | Required signature for AA-MA commits | Last footer line | 2026-04-12 |
| `[ad-hoc]` | M3 bypass for unsigned commits | Must be on its own line | 2026-04-12 |
| `[no-sync-check]` | M5 bypass for drift warnings | Must be on its own line | 2026-04-12 |

### Dependencies

| Dependency | Version / Pin | Role | [valid] |
|------------|---------------|------|---------|
| `bats-core/bats-action` | `@v4` (major-version pin) | CI bats runner | 2026-04-12 |
| `bats-core` | `>= 1.11` | Local test execution | 2026-04-12 |
| `jq` | any | stdin JSON parsing in hooks; install.sh settings.json editing | 2026-04-12 |
| `bash` | `>= 4` | Hook scripts | 2026-04-12 |
| `grep -E` | POSIX | Pattern matching with `-E` | 2026-04-12 |
| `shellcheck` | any | CI linting of shell scripts | 2026-04-12 |

### Constants

| Constant | Value | Context | [valid] |
|----------|-------|---------|---------|
| Canonical Status format | `Status: PENDING\|ACTIVE\|COMPLETE\|BLOCKED` (plain) | Per M3.5 canonicalization decision | 2026-04-12 |
| Format-agnostic Status regex | `(\*\*)?Status:(\*\*)? +<WORD>` | Helper library regex for defense-in-depth | 2026-04-12 |
| POSIX date format | `date -u +%Y-%m-%dT%H:%M:%SZ` | Cross-platform BSD/GNU-safe | 2026-04-12 |
| Task naming convention | `task-1`, `task-2`, ..., `task-N` | Fixture builder default | 2026-04-12 |
| Files per fixture task | 5 | `-plan.md`, `-tasks.md`, `-reference.md`, `-context-log.md`, `-provenance.log` | 2026-04-12 |
| Footer threshold (session-start) | 4+ active tasks | Triggers "and M more" footer | 2026-04-12 |
| AA-MA task dir convention | `.claude/dev/active/{task-name}/` | [valid: 2026-04-12] | 2026-04-12 |
| Drift detector default threshold | 1 file touched | `AA_MA_DRIFT_THRESHOLD` default | 2026-04-12 |
| Minimum bats cases M1 | 16 (fixture 4 + parser 12+) | Acceptance criterion | 2026-04-12 |
| Minimum bats cases M2 | 10 (session-start 6+ + pre-compact 4+) | Acceptance criterion | 2026-04-12 |
| Minimum bats cases M3 | 7 (commit-signature) | Acceptance criterion | 2026-04-12 |
| Minimum bats cases M4 | 5 (session-end-dirty) | Acceptance criterion | 2026-04-12 |
| Minimum bats cases M5 | 8 (commit-drift) | Acceptance criterion | 2026-04-12 |

### Helper Library Exports (`claude-code/hooks/lib/aa-ma-parse.sh`)

| Function | Signature / Behavior | [valid] |
|----------|----------------------|---------|
| `aa_ma_is_disabled` | Returns 0 if `AA_MA_HOOKS_DISABLE=1` is set, else 1 | 2026-04-12 |
| `aa_ma_extract_active_milestone <tasks-file>` | Emits the active milestone heading | 2026-04-12 |
| `aa_ma_extract_active_step <tasks-file>` | Emits the active step heading | 2026-04-12 |
| `aa_ma_list_active_tasks` | Iterates project-local + `$HOME`, mtime-sorted via `ls -t`, project-first collision | 2026-04-12 |
| `aa_ma_debug <msg>` | Emits msg to stderr iff `HOOK_DEBUG=1` | 2026-04-12 |

### Branch & Commit Base

| Key | Value | [valid] |
|-----|-------|---------|
| Branch base | `expt/rocket_mems_playground` | 2026-04-12 |
| Commit base | `7f52e18` | 2026-04-12 |

_Last Updated: 2026-04-12 12:00_
