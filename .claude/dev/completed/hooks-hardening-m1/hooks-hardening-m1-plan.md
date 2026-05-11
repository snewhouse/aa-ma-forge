<!-- ARCHIVED: 2026-04-12 17:29 UTC+01:00 -->
<!-- Plan: hooks-hardening-m1 - COMPLETE -->
<!-- Total Milestones: 5 | Duration: 2026-04-12 to 2026-04-12 -->

# hooks-hardening-m1 Plan

**Objective:** Harden AA-MA hooks — extract shared parser, fix 3 shipped-hook correctness bugs (mtime ordering, path asymmetry, format mismatch), add commit-signature enforcement with `[ad-hoc]` bypass, add SessionEnd dirty-detector, add PostToolUse drift-detector. Kill switch (`AA_MA_HOOKS_DISABLE=1`) for rollback. Bats test harness for all hooks.

**Owner:** Stephen Newhouse (via Claude Code + Agent team reviews)
**Created:** 2026-04-12
**Last Updated:** 2026-04-12
**Branch base:** expt/rocket_mems_playground (commit 7f52e18)

## Executive Summary

Refactor two buggy shipped hooks (`aa-ma-session-start.sh`, `pre-compact-aa-ma.sh`) to use a new shared parser library (`claude-code/hooks/lib/aa-ma-parse.sh`), add three new enforcement/observer hooks (commit-signature, session-end-dirty, commit-drift), and wire a bats test harness into CI via `bats-core/bats-action@v4`. A single kill-switch env var (`AA_MA_HOOKS_DISABLE=1`) enables safe rollback at any point. All behavior covered by ~45 bats cases across 6 test files. Blast radius: 15 files touched (5 modified, 10 created).

Complexity: ~55% overall (M3 at 70% is highest; none trigger deep architectural review at the 80% threshold).
Total effort estimate: ~22 hours.

## Implementation Steps

### Milestone 1 — Foundations (bats + helper + CI + HOOK_DEBUG)

- **Gate:** SOFT
- **Complexity:** 45%
- **Effort:** 5.5h
- **Goal:** `bats tests/hooks/aa-ma-parse.bats` + `bats tests/hooks/fixtures/build_active_dir.bats` pass in CI with >=16 cases combined.

Sub-steps:

- **1.1** Create `tests/hooks/fixtures/build_active_dir.sh`. Signature: `build_active_dir <target_dir> <task_count> [status_format=plain] [mtime_offsets] [active_ms=1] [--with-git]`. Emits 5 standard AA-MA files per task (`{task}-plan.md`, `-tasks.md`, `-reference.md`, `-context-log.md`, `-provenance.log`). `mtime_offsets` = comma-separated integer seconds offset from now (negative = past); empty or matches task_count. `status_format` accepts `plain` (default), `bold`, or `mixed` (round-robin starting bold). `active_ms` = 1-based milestone index to mark ACTIVE. `--with-git` runs `git init && git add -A && git commit -m initial` for M4 tests. Task naming: `task-1`, `task-2`, ..., `task-N`. POSIX date format. Shellcheck clean.
- **1.1.bis** Create `tests/hooks/fixtures/build_active_dir.bats` with 4 cases: task_count produces N dirs; status_format variants emit expected markup; mtime_offsets applied verifiable via `stat -c %Y`; `--with-git` creates committed repo.
- **1.2** Extend `.github/workflows/security.yml` with a bats job using `bats-core/bats-action@v4` (latest major pin). Yamllint passes.
- **1.3** Create `claude-code/hooks/lib/aa-ma-parse.sh`. Exports: `aa_ma_is_disabled` (checks `AA_MA_HOOKS_DISABLE=1`, returns 0 if set), `aa_ma_extract_active_milestone <tasks-file>`, `aa_ma_extract_active_step <tasks-file>`, `aa_ma_list_active_tasks` (iterates project-local + `$HOME`, mtime-sorted via `ls -t`, project-first collision), `aa_ma_debug <msg>` (emits stderr if `HOOK_DEBUG=1`). Regex: `(\*\*)?Status:(\*\*)? +<WORD>` (format-agnostic). Use awk state machine for milestone/step extraction (not `grep -B2`). Shellcheck clean.
- **1.4** Create `tests/hooks/aa-ma-parse.bats` with >=12 cases: bold form, plain form, mixed, empty, kill-switch, mtime order, project-first collision, HOOK_DEBUG on/off.

Artifacts produced: `tests/hooks/fixtures/build_active_dir.sh`, `tests/hooks/fixtures/build_active_dir.bats`, `tests/hooks/aa-ma-parse.bats`, `claude-code/hooks/lib/aa-ma-parse.sh`, updated `.github/workflows/security.yml`.

Tests: M1.1.bis (4 fixture cases) + M1.4 (12+ parser cases) = 16 cases minimum.

Acceptance:
- `bats tests/hooks/aa-ma-parse.bats` exits 0 with >=12 cases reported.
- `bats tests/hooks/fixtures/build_active_dir.bats` exits 0 with >=4 cases.
- `shellcheck claude-code/hooks/lib/aa-ma-parse.sh tests/hooks/fixtures/build_active_dir.sh` exits 0.
- `yamllint .github/workflows/security.yml` exits 0.

### Milestone 2 — Fix shipped hooks (tests-first)

- **Gate:** HARD
- **Complexity:** 55%
- **Effort:** 3.5h
- **Goal:** Both shipped hooks use the shared helper; all target-behavior bats tests green.

Sub-steps:

- **2.1** Write failing `tests/hooks/session-start.bats` with >=6 cases: mtime-top selection; resolved `$HOME` path emission; "(N other active tasks: a, b, c and M more)" footer at N=4+; empty state.
- **2.2** Patch `claude-code/hooks/aa-ma-session-start.sh`: source helper, use `aa_ma_list_active_tasks` for mtime-sorted list, emit resolved absolute path (fix line 72 bug), append footer. Shellcheck clean; bats green.
- **2.3** Write failing `tests/hooks/pre-compact.bats` with >=4 cases: both-paths iteration; project-first collision; snapshot file creation; empty state.
- **2.4** Patch `claude-code/hooks/pre-compact-aa-ma.sh`: source helper, iterate both paths via `aa_ma_list_active_tasks`, collision resolution project-first. Bats green.

Artifacts: `tests/hooks/session-start.bats`, `tests/hooks/pre-compact.bats`, modified `claude-code/hooks/aa-ma-session-start.sh`, modified `claude-code/hooks/pre-compact-aa-ma.sh`.

Acceptance:
- Both `.bats` test files exit 0 with all cases green.
- Given two active tasks where task-B has newer mtime, the session-start hook emits task-B's absolute path first.
- Given a trailing-slash `$HOME`, session-start emits a normalized path without a double slash.
- Given 4+ active tasks, session-start emits the footer "(N other active tasks: ... and M more)".
- Shellcheck passes on both modified hook files.

### Milestone 3 — Commit-signature + install.sh + docs + canonicalization

- **Gate:** HARD
- **Complexity:** 70% (flagged — within 10% of the 80% deep-review threshold)
- **Effort:** 7h
- **Goal:** An unsigned commit in an active AA-MA context is blocked with a pretty hint; `[ad-hoc]` marker bypasses; kill switch disables; install.sh auto-registers the new hook and fixes the PreCompact gap.

Sub-steps:

- **3.1** Write failing `tests/hooks/commit-signature.bats` with >=7 cases: signature present (any active task name); `[ad-hoc]` marker on its own line; no active plan (pass); HEREDOC form (substring match works); editor-open pass-through (bare `git commit` or `--amend`); kill switch; unknown task name rejection.
- **3.2** Create `claude-code/hooks/aa-ma-commit-signature.sh`: PreToolUse(Bash) matcher. Reads stdin via `jq -e '.tool_input.command // empty'`. Exit 1 if jq parse fails (hook infrastructure error, not block). Word-boundary `\bgit commit\b` via `grep -Eq`. Check `aa_ma_is_disabled` then exit 0. Check no active plans then exit 0. Check command contains `[ad-hoc]` on own line then exit 0. Check command contains `[AA-MA Plan] <name>` matching any active task name then exit 0. Else: exit 2 with pretty stderr block message naming the top active task, signature template, and `AA_MA_HOOKS_DISABLE=1` emergency bypass. Shellcheck clean.
- **3.3** Extend `scripts/install.sh` jq block: (a) preflight jq presence check — fail clean with "Install jq: sudo apt-get install -y jq (Ubuntu/WSL) or brew install jq (Mac)" if missing; (b) idempotent PreToolUse(Bash) registration of commit-signature hook; (c) fix pre-existing gap — register PreCompact hook; (d) register SessionEnd hook (M4); (e) register PostToolUse(Bash) hook (M5). All via atomic tempfile+mv with `jq empty` validation post-write. `install.sh --dry-run` shows expected registrations; second run reports "already registered"; `jq empty ~/.claude/settings.json` clean.
- **3.3.bis** Update `scripts/uninstall.sh` to deregister all 5 hook entries (SessionStart + PreCompact + PreToolUse(Bash) + SessionEnd + PostToolUse(Bash)) by exact command-string match.
- **3.4** Add README "AA-MA hook troubleshooting" section (kill switch, `[ad-hoc]` marker, escape procedure, local bats install commands). Append CHANGELOG entry under Unreleased matching regex `feat\(hooks\): commit-signature`. `/doc-sync` no drift. Markdown lints clean.
- **3.5** Canonicalize Status format to **plain** in 3 files only: `docs/templates/tasks-template.md` (flip bold to plain at line 35 and 80), `claude-code/agents/aa-ma-scribe.md` template block (flip bold to plain at line 143), `claude-code/hooks/aa-ma-session-start.sh` grep pattern (already handled via M2 helper extraction). Integration test: aa-ma-validator agent reports no parse errors on canonicalized template when scribe generates from it. Other files (commands, skills, rules, spec, examples) already plain — no edits needed.

Artifacts: `tests/hooks/commit-signature.bats`, `claude-code/hooks/aa-ma-commit-signature.sh`, modified `scripts/install.sh`, modified `scripts/uninstall.sh`, modified `README.md`, modified `CHANGELOG.md`, modified `docs/templates/tasks-template.md`, modified `claude-code/agents/aa-ma-scribe.md`.

Acceptance:
- Given an active task "hooks-hardening-m1" and a commit message containing the line `[AA-MA Plan] hooks-hardening-m1 .claude/dev/active/hooks-hardening-m1`, the hook exits 0.
- Given the same active context and a commit message containing `[ad-hoc]` on its own line, the hook exits 0.
- Given the same active context and a commit message with no signature and no marker, the hook exits 2 and stderr contains the top active task name and the signature template.
- Given `AA_MA_HOOKS_DISABLE=1`, the hook exits 0 unconditionally.
- `install.sh` run twice produces "already registered" on the second run for all 5 hook entries.
- `jq empty ~/.claude/settings.json` exits 0 after install.sh runs.
- `uninstall.sh` removes all 5 hook entries; subsequent `jq 'paths' ~/.claude/settings.json` has zero matches for those command strings.

### Milestone 4 — SessionEnd dirty AA-MA detector (renamed from Stop per verification finding)

- **Gate:** SOFT
- **Complexity:** 50%
- **Effort:** 2.5h
- **Goal:** Warn on dirty AA-MA artifacts when a session ends.

Sub-steps:

- **4.1** Create `claude-code/hooks/aa-ma-session-end-dirty.sh`: fires on SessionEnd event (NOT Stop — Stop fires per turn). Sources helper. For each active task dir, runs `git status --porcelain` in that dir's project; if output is non-empty and contains any AA-MA artifact files, emits stderr warning. Kill switch respected. HOOK_DEBUG verbose mode. Shellcheck clean.
- **4.2** Create `tests/hooks/session-end-dirty.bats` with >=5 cases: clean state (silent); dirty tasks.md (warn); no active tasks (silent); kill switch (silent); HOOK_DEBUG on (verbose stderr). Uses fixture with `--with-git`.

Artifacts: `claude-code/hooks/aa-ma-session-end-dirty.sh`, `tests/hooks/session-end-dirty.bats`.

Acceptance:
- Given an active task with uncommitted changes to its `tasks.md`, the SessionEnd hook writes a single warning to stderr naming the dirty file.
- Given a clean working tree, the hook emits nothing to stderr and exits 0.
- Given `AA_MA_HOOKS_DISABLE=1`, the hook exits 0 with no output.
- Given `HOOK_DEBUG=1`, the hook emits a trace line per task directory inspected.

### Milestone 5 — Post-commit tasks.md drift detector

- **Gate:** HARD
- **Complexity:** 60%
- **Effort:** 4h
- **Goal:** Warn when AA-MA-active commits do not touch `tasks.md` or `provenance.log`.

Sub-steps:

- **5.1** Create `claude-code/hooks/aa-ma-commit-drift.sh`: PostToolUse(Bash) matcher on `git commit`. Uses `git log -1 --name-only HEAD` post-hoc to list committed files (NOT `tool_response` — undocumented shape). If commit-touched-files > threshold (configurable `AA_MA_DRIFT_THRESHOLD`, default 1) AND no active task's `tasks.md` or `provenance.log` appears in committed-files, emit stderr warning unless `[no-sync-check]` marker is present in the commit message. Kill switch respected. Only fires for SUCCESSFUL commits (PostToolUse limitation — documented in README). Shellcheck clean.
- **5.2** Create `tests/hooks/commit-drift.bats` with >=8 cases: tasks.md touched (silent); tasks.md not touched (warn); `[no-sync-check]` marker (silent); no active task (silent); kill switch (silent); below-threshold (silent); multiple active tasks (warn for all); non-AA-MA branch commit (silent).

Artifacts: `claude-code/hooks/aa-ma-commit-drift.sh`, `tests/hooks/commit-drift.bats`.

Acceptance:
- Given a commit touching `src/foo.py` (1 file) with no AA-MA file and `AA_MA_DRIFT_THRESHOLD=1`, the hook emits stderr warning naming the top active task.
- Given a commit touching `<task>-tasks.md`, the hook emits nothing.
- Given `[no-sync-check]` on its own line in the commit message, the hook emits nothing.
- Given `AA_MA_HOOKS_DISABLE=1`, the hook exits 0 with no output.
- Given no active task directories, the hook emits nothing.

## Milestones with measurable goals

| Milestone | Goal (measurable) | Gate | Complexity | Effort |
|-----------|-------------------|------|------------|--------|
| M1 | >=16 bats cases green in CI across parser + fixture files | SOFT | 45% | 5.5h |
| M2 | 2 shipped hooks refactored; >=10 bats cases green; no regressions | HARD | 55% | 3.5h |
| M3 | commit-signature hook installed and 7+ cases green; install.sh idempotent for 5 hook entries | HARD | 70% | 7h |
| M4 | SessionEnd hook live; 5 cases green | SOFT | 50% | 2.5h |
| M5 | PostToolUse drift hook live; 8 cases green | HARD | 60% | 4h |

## Acceptance criteria per step

See each sub-step above. All acceptance criteria are falsifiable (Wave 1 Angle 4 audit: 88% falsifiable pre-revision; 2 rewrites applied to 1.2 and 3.4 brought this to 100%).

## Required artifacts per step

**Created (12 files):**
- `claude-code/hooks/lib/aa-ma-parse.sh` (M1.3)
- `claude-code/hooks/aa-ma-commit-signature.sh` (M3.2)
- `claude-code/hooks/aa-ma-session-end-dirty.sh` (M4.1)
- `claude-code/hooks/aa-ma-commit-drift.sh` (M5.1)
- `tests/hooks/fixtures/build_active_dir.sh` (M1.1)
- `tests/hooks/fixtures/build_active_dir.bats` (M1.1.bis)
- `tests/hooks/aa-ma-parse.bats` (M1.4)
- `tests/hooks/session-start.bats` (M2.1)
- `tests/hooks/pre-compact.bats` (M2.3)
- `tests/hooks/commit-signature.bats` (M3.1)
- `tests/hooks/session-end-dirty.bats` (M4.2)
- `tests/hooks/commit-drift.bats` (M5.2)

**Modified (5 files + docs):**
- `claude-code/hooks/aa-ma-session-start.sh` (M2.2)
- `claude-code/hooks/pre-compact-aa-ma.sh` (M2.4)
- `scripts/install.sh` (M3.3)
- `scripts/uninstall.sh` (M3.3.bis)
- `.github/workflows/security.yml` (M1.2)
- `README.md` (M3.4)
- `CHANGELOG.md` (M3.4)
- `docs/templates/tasks-template.md` (M3.5)
- `claude-code/agents/aa-ma-scribe.md` (M3.5)

## Tests per milestone

- M1: 16+ cases total (fixture 4 + parser 12+)
- M2: 10+ cases (session-start 6+, pre-compact 4+)
- M3: 7+ cases (commit-signature)
- M4: 5+ cases (session-end-dirty)
- M5: 8+ cases (commit-drift)
- **Total:** ~46+ bats cases across 6 test files.

## Rollback strategies

- **Global:** `export AA_MA_HOOKS_DISABLE=1` bypasses all AA-MA hooks immediately.
- **M1:** revert commit; no user surface changed.
- **M2:** revert commits 2.2/2.4; restores prior (buggy) hook behavior but safe.
- **M3:** `rm ~/.claude/hooks/lib/aa-ma-commit-signature.sh` symlink, run `uninstall.sh`, then re-install from prior commit.
- **M4:** revert file; `uninstall.sh` deregisters the SessionEnd entry.
- **M5:** revert file; `uninstall.sh` deregisters the PostToolUse entry.

## Dependencies & assumptions

**VERIFIED assumptions (Wave 1 Angle 2):**
- PreToolUse stdin JSON: `{session_id, hook_event_name, tool_name, tool_input: {command}, tool_use_id}` — verified against Claude Code docs.
- Exit 2 = block with stderr to assistant; exit 0 = pass — verified.
- PostToolUse fires after SUCCESSFUL tool execution only — verified; documented limit.
- SessionEnd exists (NOT Stop, which fires per turn) — verified via docs.
- `bats-core/bats-action@v4` current — verified on GitHub Marketplace.
- Users have write access to `~/.claude/settings.json` — standard path.
- `$HOME` always set — low risk.
- Task file convention: `{task-name}-tasks.md` inside `.claude/dev/active/{task-name}/` — verified.

**Inter-milestone dependencies:** M2, M3, M4, and M5 all depend on M1 (helper + fixtures). No circular deps.

**External dependencies:** `jq`, `bash >= 4`, `grep -E`, shellcheck (CI), bats-core 1.11+ (CI via action).

## Effort estimates & complexity (0–100%)

| Milestone | Effort | Complexity | Deep-review (>=80%)? |
|-----------|--------|------------|----------------------|
| M1 | 5.5h | 45% | No |
| M2 | 3.5h | 55% | No |
| M3 | 7h | 70% | No (flagged, close) |
| M4 | 2.5h | 50% | No |
| M5 | 4h | 60% | No |
| **Total** | **22.5h** | **~55% avg** | **None trigger** |

## Risks & mitigations (top 3 per milestone)

**M1:**
1. bats-action drift → pin to `@v4` (major-version pin, caches patches).
2. Fixture path collisions in parallel tests → `mktemp -d` per test + teardown cleanup.
3. Format-agnostic regex matches markdown comments (`<!-- Status: ACTIVE -->`) → strip HTML comments before grep; test case included.

**M2:**
1. session-start path emission fails on trailing slash in `$HOME` → explicit normalization test.
2. pre-compact collision logic drops snapshot → assert snapshot count matches unique task names.
3. mtime tie → alphabetical fallback (documented).

**M3:**
1. jq failure on malformed stdin → `jq -e` strict, exit 1 (not 2) with clear error.
2. HEREDOC false-positive (marker in unrelated string) → regex anchored to line-start post-newline, adversarial fixture.
3. install.sh jq corruption → atomic tempfile+mv, `jq empty` validation post-write, `settings.json.bak`.

**M4:**
1. SessionEnd fires too late (after git state already clean) → test covers normal session flow.
2. Hook invoked during CI (no session) → detect via `CLAUDE_CODE` env var, exit 0.
3. False-positive on unrelated git changes outside AA-MA files → filter output by task-dir artifacts only.

**M5:**
1. False-positive warnings erode trust → `[no-sync-check]` marker + `AA_MA_DRIFT_THRESHOLD` + dogfood period.
2. git log inspection fails on initial commit (no parent) → guard against empty result.
3. Multi-active-plan confusion → warn per task; document behavior.

## Known limitations (documented, out of scope)

- Bare `git commit` / `git commit --amend` editor forms: PreToolUse cannot see the message yet; passes through.
- `git commit -F file` form: marker in file not visible via `tool_input.command`; accept false negatives.
- M5 only catches SUCCESSFUL commits (PostToolUse does not fire on failures).
- Pre-existing bug: `~/.claude/hooks/lib/guard-protected-dirs.sh:14` reads `.command` instead of `.tool_input.command` — flagged, not fixed in this plan.

## Plan review history

- **CEO review** (SELECTIVE EXPANSION mode): All 5 expansion candidates accepted — HOOK_DEBUG, pre-compact install gap, Status canonicalization, Stop/dirty detector, post-commit drift.
- **Eng review:** 7 findings, 1 decision (M5 kept, not deferred), 6 obvious fixes applied.
- **Phase 4.5 Verification** (automated mode, CRITICALs block): 6 CRITICALs across 2 revision loops, all resolved.
  - Wave 1: Stop to SessionEnd; M3.5 scope revision; uninstall.sh added.
  - Wave 2 (fresh-agent): mtime_offsets spec; file-set enumeration; M1.1.bis test added.
  - Angle 6 (specialist): skipped — no domain keywords (Pydantic/API/schema/auth) matched.

## Shared mechanisms

- **Kill switch:** `AA_MA_HOOKS_DISABLE=1` → all AA-MA hooks exit 0 immediately.
- **Debug:** `HOOK_DEBUG=1` → verbose stderr traces via `aa_ma_debug`.
- **Commit-message markers:** `[ad-hoc]` (M3 bypass), `[no-sync-check]` (M5 bypass) — auditable in git log.
- **Format-agnostic Status regex:** `(\*\*)?Status:(\*\*)? +<WORD>`.
- **Canonical Status format:** plain (`Status: PENDING|ACTIVE|COMPLETE`), per Wave 1 finding.
- **POSIX date:** `date -u +%Y-%m-%dT%H:%M:%SZ` (cross-platform BSD/GNU-safe).

## Next Action

Begin M1.1: create `tests/hooks/fixtures/build_active_dir.sh` fixture builder. Mark M1 ACTIVE in `tasks.md`; log start timestamp in `provenance.log`. File to update: `hooks-hardening-m1-tasks.md`.
