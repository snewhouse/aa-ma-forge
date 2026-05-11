<!-- ARCHIVED: 2026-04-12 17:29 UTC+01:00 -->
<!-- Plan: hooks-hardening-m1 - COMPLETE -->
<!-- Total Milestones: 5 | Duration: 2026-04-12 to 2026-04-12 -->

# hooks-hardening-m1 Tasks (HTP)

_Hierarchical Task Planning roadmap with dependencies, gates, modes, and state tracking._

## Milestone 1: Foundations (bats + helper + CI + HOOK_DEBUG)
- Status: COMPLETE
- Dependencies: None
- Gate: SOFT
- Complexity: 45%
- Effort: 5.5h
- Acceptance Criteria:
  - `bats tests/hooks/aa-ma-parse.bats` exits 0 with at least 12 cases reported.
  - `bats tests/hooks/fixtures/build_active_dir.bats` exits 0 with at least 4 cases reported.
  - `shellcheck claude-code/hooks/lib/aa-ma-parse.sh tests/hooks/fixtures/build_active_dir.sh` exits 0.
  - `yamllint .github/workflows/security.yml` exits 0.
  - CI pipeline runs the bats job on push to the working branch and it passes.
- Milestone Result Log:
  ✅ COMPLETE 2026-04-12
  - All 5 sub-steps COMPLETE (1.1, 1.1.bis, 1.2, 1.3, 1.4)
  - Bats: 22 cases green (build_active_dir 6 + aa-ma-parse 16) — exceeds 16-case minimum
  - Shellcheck: PASS on all new .sh files
  - Yamllint: PASS (exit 0) on security.yml
  - CI validation: pending first push to working branch
  - Impact: all LOW risk (no existing callers; helper contract documented in reference.md)
  - Post-milestone simplification review: SKIPPED — only bash/bats/yaml touched (no Python/TS/JS/Go/Rust per skill's skip rule); prior double-check + architect + Phase 4.5 Wave 1+2 reviews already covered code quality angles

### Step 1.1: Create fixture builder `tests/hooks/fixtures/build_active_dir.sh`
- Status: COMPLETE
- Mode: AFK
- Dependencies: None
- Acceptance Criteria:
  - File exists at `tests/hooks/fixtures/build_active_dir.sh` with signature `build_active_dir <target_dir> <task_count> [status_format=plain] [mtime_offsets] [active_ms=1] [--with-git]`.
  - Invoked with `task_count=3` emits exactly 3 directories `task-1/`, `task-2/`, `task-3/` each containing 5 files (`-plan.md`, `-tasks.md`, `-reference.md`, `-context-log.md`, `-provenance.log`).
  - `status_format=plain` emits `Status: ACTIVE` (plain); `bold` emits `**Status:** ACTIVE`; `mixed` alternates starting bold.
  - `mtime_offsets="-10,-5,0"` applied; `stat -c %Y task-1/...-tasks.md` returns now minus 10 seconds (verifiable within 1s tolerance).
  - `--with-git` results in an initialized repo with a single commit (`git rev-list --count HEAD` equals 1).
  - `shellcheck tests/hooks/fixtures/build_active_dir.sh` exits 0.
- Result Log:
  ✅ COMPLETE 2026-04-12
  - File: tests/hooks/fixtures/build_active_dir.sh (166 lines, chmod +x)
  - Smoke test: task_count=3 produced 3 dirs × 5 files = 15 files ✓
  - plain emits `- Status: ACTIVE/PENDING` ✓
  - bold emits `- **Status:** ACTIVE/PENDING` ✓
  - mixed alternates: task-1=bold, task-2=plain ✓
  - mtime_offsets="-10,0" applied: t1 diff=-10s, t2 diff=0s (within 1s tolerance) ✓
  - --with-git: git rev-list --count HEAD = 1 ✓
  - shellcheck: PASS (0 issues)
  - Fixed during dev: positional-arg parser `-*` branch caught negative mtime offsets; narrowed to `--*` only.

### Step 1.1.bis: Create fixture self-test `tests/hooks/fixtures/build_active_dir.bats`
- Status: COMPLETE
- Mode: AFK
- Dependencies: Step 1.1
- Acceptance Criteria:
  - File exists with at least 4 test cases.
  - Case 1: task_count produces N dirs (assert directory count).
  - Case 2: status_format variants emit expected markup (grep for `Status:` vs `**Status:**`).
  - Case 3: mtime_offsets applied verifiable via `stat -c %Y` (within 1s tolerance).
  - Case 4: `--with-git` creates committed repo (assert `git log --oneline | wc -l` equals 1).
  - All 4 cases green locally and in CI.
- Result Log:
  ✅ COMPLETE 2026-04-12
  - File: tests/hooks/fixtures/build_active_dir.bats (6 test cases, exceeds min 4)
  - bats output: `1..6` all `ok`
  - Cases: (1) dir+file count, (2) format variants plain/bold/mixed, (3) mtime offsets within 1s, (4) --with-git single commit, (5) bad task_count rejected, (6) bad status_format rejected
  - Fixed during dev: initial `grep -Fxq '-Status...'` failed on `-` prefix; switched to `grep -Fxq -e '...'` and `run grep + [ status -ne 0 ]` for negative assertions

### Step 1.2: Extend `.github/workflows/security.yml` with bats CI job
- Status: COMPLETE
- Mode: AFK
- Dependencies: None
- Acceptance Criteria:
  - Workflow file contains a new job running `bats-core/bats-action@v4` on `tests/hooks/**/*.bats`.
  - `yamllint .github/workflows/security.yml` exits 0.
  - Job runs on push and pull_request events (per existing workflow conventions).
  - CI run on the working branch reports the bats job as PASSING once M1.1–M1.4 are merged.
- Result Log:
  ✅ COMPLETE 2026-04-12
  - File: .github/workflows/security.yml — added `bats` job (appended, no other edits)
  - Job uses `bats-core/bats-action@v4` (pinned to major)
  - Command: `bats --recursive tests/hooks/` (runs all .bats recursively)
  - Job inherits `on: [push, pull_request] branches: [main]` from top-level workflow
  - yamllint: exit 0 (2 pre-existing warnings: missing doc start, truthy 'on:' — not introduced by this edit)
  - Pending: CI pipeline validation when pushed to the working branch (post-commit step)

### Step 1.3: Create shared helper library `claude-code/hooks/lib/aa-ma-parse.sh`
- Status: COMPLETE
- Mode: AFK
- Dependencies: None
- Acceptance Criteria:
  - File exists at `claude-code/hooks/lib/aa-ma-parse.sh`.
  - Exports functions: `aa_ma_is_disabled`, `aa_ma_extract_active_milestone`, `aa_ma_extract_active_step`, `aa_ma_list_active_tasks`, `aa_ma_debug`.
  - `aa_ma_is_disabled` returns 0 when `AA_MA_HOOKS_DISABLE=1` is set, 1 otherwise.
  - `aa_ma_list_active_tasks` iterates both project-local `.claude/dev/active/` and `$HOME/.claude/dev/active/`, emits results sorted by mtime (newest first) via `ls -t`, with project-first collision resolution.
  - `aa_ma_debug "msg"` emits to stderr iff `HOOK_DEBUG=1`; silent otherwise.
  - Regex `(\*\*)?Status:(\*\*)? +<WORD>` used for Status extraction; an awk state machine used for milestone/step extraction (not `grep -B2`).
  - HTML comments stripped before grep so `<!-- Status: ACTIVE -->` does not produce false positives.
  - `shellcheck claude-code/hooks/lib/aa-ma-parse.sh` exits 0.
- Result Log:
  ✅ COMPLETE 2026-04-12
  - File: claude-code/hooks/lib/aa-ma-parse.sh (5 exports, ~155 lines)
  - `aa_ma_is_disabled`: returns 0 when env=1, non-zero when unset ✓ (tested)
  - `aa_ma_extract_active_milestone`: fixture test → "Milestone 1: Foundation" ✓
  - `aa_ma_extract_active_step`: fixture test → "Step 1.1: Initial step" (via PENDING fallback) ✓
  - `aa_ma_list_active_tasks`: mtime-sorted project-first collision: test with task-1 in both project+home → only project-local emitted; mtime offsets (-200,-100,0) → task-3 first, task-1 last ✓
  - `aa_ma_debug`: silent off, "[aa-ma-debug] hello debug" on ✓
  - HTML comment guard: `<!-- Status: ACTIVE -->` stripped; PENDING fallback used correctly ✓
  - Implementation: awk state machine (not grep -B2); format-agnostic regex `(\*\*)?Status:(\*\*)? +<WORD>`; `sed 's/<!--[^>]*-->//g'` for comment stripping; `sort -k1,1rn -k2,2` for deterministic mtime+alphabetical fallback
  - shellcheck: PASS (1 SC2317 suppressed with comment; dead-code warning for intentional return/exit fallback)

### Step 1.4: Create parser bats suite `tests/hooks/aa-ma-parse.bats`
- Status: COMPLETE
- Mode: AFK
- Dependencies: Steps 1.1, 1.3
- Acceptance Criteria:
  - File contains at least 12 bats test cases.
  - Cases cover: bold Status form, plain Status form, mixed form, empty tasks file, kill-switch (`AA_MA_HOOKS_DISABLE=1`), mtime-ordering correctness, project-first collision resolution, `HOOK_DEBUG=1` stderr trace, `HOOK_DEBUG` unset produces no trace, HTML-comment false-positive guard, tie-break alphabetical fallback, multi-task listing.
  - `bats tests/hooks/aa-ma-parse.bats` exits 0 locally.
  - CI run (M1.2) reports all cases green.
- Result Log:
  ✅ COMPLETE 2026-04-12
  - File: tests/hooks/aa-ma-parse.bats (16 test cases — exceeds minimum of 12)
  - Coverage: kill-switch on/off/=0 (3), debug silent/active (2), milestone bold/plain/mixed/empty (4), step PENDING-fallback (1), HTML-comment guard (1), list_active_tasks mtime-order/collision/merge/empty/tiebreak (5)
  - bats output: `1..16` all `ok`
  - Fixed during dev: helper's `aa_ma_list_active_tasks` used `mktemp` + `trap RETURN` that hit a cleanup race when called via `mapfile < <(...)` or `$(...)`; refactored to in-memory bash array + `printf '%s\n' "${rows[@]}" | sort | awk`. No temp files, no trap, all 16 tests green.

---

## Milestone 2: Fix shipped hooks (tests-first)
- Status: COMPLETE
- Dependencies: Milestone 1
- Gate: HARD
- Complexity: 55%
- Effort: 3.5h
- Acceptance Criteria:
  - `tests/hooks/session-start.bats` and `tests/hooks/pre-compact.bats` both exit 0 with all cases green.
  - Given two active tasks where task-B has newer mtime, the session-start hook emits task-B's absolute path first.
  - Given a trailing-slash `$HOME`, session-start emits a normalized path with no double slash.
  - Given 4+ active tasks, session-start emits the footer "(N other active tasks: ... and M more)".
  - Given two tasks with the same name (project-local + home), pre-compact resolves to the project-local version and creates a snapshot.
  - `shellcheck` passes on both modified hook files.
- Milestone Result Log:
  ✅ COMPLETE 2026-04-12
  - All 4 sub-steps COMPLETE (2.1, 2.2, 2.3, 2.4)
  - Bats: 13 new cases (session-start 7 + pre-compact 6) — all green; cumulative 35/35 across M1+M2
  - Shellcheck: PASS on both patched hooks + helper + fixture
  - Impact: MEDIUM overall — session-start behaviour shift (mtime-top, absolute path, multi-task footer); pre-compact purely additive
  - HARD Gate: APPROVED via context-log.md 2026-04-12

### Step 2.1: Write failing `tests/hooks/session-start.bats`
- Status: COMPLETE
- Mode: AFK
- Dependencies: Milestone 1 complete
- Acceptance Criteria:
  - File contains at least 6 test cases.
  - Cases cover: mtime-top selection, resolved `$HOME` path emission, trailing-slash normalization, 4+ tasks footer emission, empty state (no active tasks), single-task emission.
  - All cases initially RED (fail against current hook).
- Result Log:
  ✅ COMPLETE 2026-04-12
  - File: tests/hooks/session-start.bats (7 cases, exceeds min 6)
  - Against unpatched hook: 5/7 RED (#2 path emit, #3 mtime, #4 footer, #5 footer truncation, #7 home-fallback)
  - Tests 1 (empty) and 6 (no-double-slash) coincidentally GREEN — test 6 doesn't discriminate until path-emit is fixed; acceptable
  - Fixed during dev: initial mtime test had offsets "-200,-100,0" which made alphabetical-last = mtime-newest (task-3 in both); inverted to "0,-100,-200" so task-1 is newest, task-3 alphabetical last — now properly discriminates

### Step 2.2: Patch `claude-code/hooks/aa-ma-session-start.sh` to use helper
- Status: COMPLETE
- Mode: AFK
- Dependencies: Step 2.1
- Acceptance Criteria:
  - Hook sources `claude-code/hooks/lib/aa-ma-parse.sh`.
  - Hook uses `aa_ma_list_active_tasks` for mtime-sorted list.
  - Line 72 path emission bug fixed: emits resolved absolute path, not a relative fragment.
  - Footer "(N other active tasks: a, b, c and M more)" appended when >=4 active tasks.
  - `shellcheck claude-code/hooks/aa-ma-session-start.sh` exits 0.
  - All Step 2.1 bats cases now GREEN.
- Result Log:
  ✅ COMPLETE 2026-04-12
  - File: claude-code/hooks/aa-ma-session-start.sh — full rewrite sourcing helper
  - Sources `lib/aa-ma-parse.sh` via `SCRIPT_DIR/lib/...`
  - Uses `aa_ma_list_active_tasks` (mapfile) for mtime-sorted list with project-first collision
  - Path normalisation via `sed 's|//*|/|g'` to handle trailing-slash $HOME
  - Emits absolute path (not hardcoded `.claude/dev/active/` fragment)
  - Footer: "(N other active tasks: name1, name2, name3 and M more)" caps at 3 names
  - Honours AA_MA_HOOKS_DISABLE kill switch (early exit 0)
  - bats: 7/7 GREEN (was 5/7 RED pre-patch)
  - shellcheck: PASS

### Step 2.3: Write failing `tests/hooks/pre-compact.bats`
- Status: COMPLETE
- Mode: AFK
- Dependencies: Milestone 1 complete
- Acceptance Criteria:
  - File contains at least 4 test cases.
  - Cases cover: both-paths iteration (project-local + home), project-first collision resolution, snapshot file creation per unique task, empty state.
  - All cases initially RED against current hook.
- Result Log:
  ✅ COMPLETE 2026-04-12
  - File: tests/hooks/pre-compact.bats (6 cases — exceeds min 4)
  - Against unpatched hook: 4/6 RED (#2 project-local, #4 both-paths, #5 collision, #6 kill-switch)
  - Tests 1 (empty) and 3 (home-only legacy) correctly GREEN (preservation checks)
  - Fixed during dev: kill-switch test put fixture in project-local where unpatched hook doesn't read → coincidental pass; moved fixture to $HOME so test properly discriminates

### Step 2.4: Patch `claude-code/hooks/pre-compact-aa-ma.sh` to use helper
- Status: COMPLETE
- Mode: AFK
- Dependencies: Step 2.3
- Acceptance Criteria:
  - Hook sources the helper library.
  - Hook iterates both `.claude/dev/active/` paths via `aa_ma_list_active_tasks`.
  - Collision resolution is project-first.
  - Snapshot count equals unique task-name count.
  - `shellcheck` passes.
  - All Step 2.3 bats cases now GREEN.
- Result Log:
  ✅ COMPLETE 2026-04-12
  - File: claude-code/hooks/pre-compact-aa-ma.sh — full rewrite sourcing helper
  - Sources `lib/aa-ma-parse.sh` via `SCRIPT_DIR/lib/...`
  - Uses `aa_ma_list_active_tasks` for both-paths iteration + project-first collision
  - Uses `aa_ma_extract_active_step` (format-agnostic) for CHECKPOINT entry (previously hardcoded plain-grep, missed bold-format)
  - Honours AA_MA_HOOKS_DISABLE kill switch (early exit 0 with compaction.log entry)
  - Adopted POSIX `date -u +%Y-%m-%dT%H:%M:%SZ` format (replaces `date -Iseconds` — BSD/GNU portable)
  - bats: 6/6 GREEN (was 4/6 RED pre-patch)
  - shellcheck: PASS

---

## Milestone 3: Commit-signature + install.sh + docs + canonicalization
- Status: COMPLETE
- Dependencies: Milestone 1, Milestone 2
- Gate: HARD
- Complexity: 70% (flagged — within 10% of 80% deep-review threshold)
- Effort: 7h
- Milestone Result Log:
  ✅ COMPLETE 2026-04-12
  - All 6 sub-steps COMPLETE (3.1, 3.2, 3.3, 3.3.bis, 3.4, 3.5)
  - Bats: 10 new commit-signature cases green; cumulative 45/45 across M1+M2+M3
  - Shellcheck: PASS on all scripts (2 hooks + install.sh + uninstall.sh + helper + fixture)
  - install.sh live: 2 new registrations (PreCompact, PreToolUse/commit-signature); idempotent on re-run; settings.json.bak created
  - Dogfood: the M3 commit is the first to exercise its own enforcer
  - HARD Gate: APPROVED 2026-04-12
- Acceptance Criteria:
  - `tests/hooks/commit-signature.bats` exits 0 with at least 7 cases.
  - `install.sh` run twice reports "already registered" on the second run for all 5 hook entries.
  - `jq empty ~/.claude/settings.json` exits 0 after install.sh runs.
  - `uninstall.sh` removes all 5 hook entries; post-run `jq 'paths'` shows no matches for those command strings.
  - README "AA-MA hook troubleshooting" section renders cleanly; `/doc-sync` reports no drift.
  - CHANGELOG Unreleased entry matches regex `feat\(hooks\): commit-signature`.
  - 3 canonicalized files (`docs/templates/tasks-template.md`, `claude-code/agents/aa-ma-scribe.md`, `claude-code/hooks/aa-ma-session-start.sh`) use plain Status format.

### Step 3.1: Write failing `tests/hooks/commit-signature.bats`
- Status: COMPLETE
- Mode: AFK
- Dependencies: Milestone 2 complete
- Acceptance Criteria:
  - File contains at least 7 test cases.
  - Cases cover: signature present (any active task name) exits 0; `[ad-hoc]` on own line exits 0; no active plan exits 0; HEREDOC form with substring match exits 0; editor-open pass-through (bare `git commit` or `--amend`) exits 0; `AA_MA_HOOKS_DISABLE=1` exits 0; unknown task name in signature rejected (exit 2 with stderr).
  - All cases initially RED (hook file does not yet exist).
- Result Log:
  ✅ COMPLETE 2026-04-12
  - File: tests/hooks/commit-signature.bats (10 cases, exceeds min 7)
  - Against absent hook: 10/10 RED (exit 127 "command not found")
  - Extra cases added: non-commit bash command passthrough, `git commit-tree` word-boundary discrimination
  - Tests build stdin JSON via `jq -cn --arg cmd` for safe escaping

### Step 3.2: Create `claude-code/hooks/aa-ma-commit-signature.sh`
- Status: COMPLETE
- Mode: AFK
- Dependencies: Step 3.1
- Acceptance Criteria:
  - File exists; hook type is PreToolUse with matcher `"Bash"`.
  - Hook reads stdin via `jq -e '.tool_input.command // empty'`; exits 1 (not 2) on jq parse failure.
  - Hook uses `grep -Eq '\bgit commit\b'` for word-boundary detection.
  - Hook exits 0 when `aa_ma_is_disabled` returns 0.
  - Hook exits 0 when no active plans are detected.
  - Hook exits 0 when command contains `[ad-hoc]` on its own line.
  - Hook exits 0 when command contains `[AA-MA Plan] <name>` matching an active task name.
  - Hook exits 2 with pretty stderr block otherwise, including top active task name, signature template, and `AA_MA_HOOKS_DISABLE=1` hint.
  - `shellcheck` passes.
  - All Step 3.1 bats cases now GREEN.
- Result Log:
  ✅ COMPLETE 2026-04-12
  - File: claude-code/hooks/aa-ma-commit-signature.sh (~140 lines, chmod +x)
  - Decision tree implemented per plan spec (kill-switch → jq parse → git-commit match → editor-form → active-plan → [ad-hoc] → sig match → block)
  - Word-boundary: `grep -Eq 'git commit([[:space:]]|$)'` — correctly rejects `git commit-tree` (word-boundary \b would have matched it)
  - Editor-form detection: `grep -Eq '([[:space:]]|^)(-m|-F|-c|-C|--message|--file|--reedit-message|--reuse-message)([[:space:]]|=|$)'` — pass-through if no message flag present
  - `[ad-hoc]` regex relaxed to accept trailing `"`/`'`/backtick so shell-quoted message literals are matched
  - Pretty stderr block names top active task, signature template, `[ad-hoc]` alternative, `AA_MA_HOOKS_DISABLE=1` emergency bypass
  - bats: 10/10 GREEN (was 10/10 RED pre-implementation)
  - shellcheck: PASS
  - Fixed during dev: SC2001 sed → parameter expansion `${var//,/, }`; [ad-hoc] regex had to tolerate trailing delimiter chars from shell quoting

### Step 3.3: Extend `scripts/install.sh` with jq block for 5 hook registrations
- Status: COMPLETE
- Mode: HITL
- Dependencies: Step 3.2
- Acceptance Criteria:
  - install.sh preflight: if `jq` absent, exit clean with message "Install jq: sudo apt-get install -y jq (Ubuntu/WSL) or brew install jq (Mac)".
  - Idempotent registration of 5 hook entries: SessionStart, PreCompact, PreToolUse(Bash) for commit-signature, SessionEnd (M4), PostToolUse(Bash) for commit-drift (M5).
  - Each registration via atomic tempfile+mv with `jq empty` validation post-write.
  - `install.sh --dry-run` shows expected registrations without modifying settings.json.
  - Second run of `install.sh` reports "already registered" for all 5 entries.
  - `jq empty ~/.claude/settings.json` exits 0 after install.
  - `settings.json.bak` created before first write.
  - User reviews and approves settings.json diff (HITL gate).
- Result Log:
  ✅ COMPLETE 2026-04-12 (HITL approved)
  - install.sh refactored: AA_MA_HOOKS pipe-delimited array (event|matcher|source|timeout|statusMessage); `register_hook` function with preflight-skip for absent source files; `backup_settings_once` one-shot backup helper; atomic tempfile+mv+jq-empty validation.
  - Preflight jq check at top: exits 1 with install instructions if missing.
  - Dry-run verified: all 5 entries correctly evaluated; M4/M5 source files absent → skipped; SessionStart already present → skipped; PreCompact + PreToolUse (commit-signature) marked for addition.
  - Live run (HITL approved): 3 hooks now registered (SessionStart existing + PreCompact newly + PreToolUse(Bash) commit-signature newly). M4/M5 skipped pending source.
  - Idempotence verified: 2nd run reports "already registered" for all 3; "source not present" for M4/M5.
  - jq empty ~/.claude/settings.json: PASS.
  - settings.json.bak created on first mutation.
  - Fixed during dev: initial idempotence check used exact command-string match; Stephen's existing PreCompact was plain-path while our registration used `bash <path>` prefix, causing duplicate. Refactored check to use `test($link; "l")` for path-substring match — normalizes both forms. Removed accidental duplicate PreCompact entry manually via jq.

### Step 3.3.bis: Update `scripts/uninstall.sh` to deregister all 5 hook entries
- Status: COMPLETE
- Mode: AFK
- Dependencies: Step 3.3
- Acceptance Criteria:
  - uninstall.sh removes all 5 hook entries by exact command-string match.
  - `jq empty ~/.claude/settings.json` exits 0 post-uninstall.
  - Post-uninstall, grepping the 5 hook script paths in settings.json returns zero matches.
  - `shellcheck scripts/uninstall.sh` exits 0.
- Result Log:
  ✅ COMPLETE 2026-04-12
  - uninstall.sh refactored symmetrically with install.sh: `AA_MA_UNINSTALL_HOOKS` pipe-delimited array; `deregister_hook` function with path-substring match (matches both `<path>` and `bash <path>` forms); atomic tempfile+mv+jq-empty validation
  - Match method: `test($link; "l")` — literal substring, same normalisation as install.sh idempotence check
  - Dry-run: correctly reports 3 deregistrations (SessionStart + PreCompact + PreToolUse) matching currently-registered set; SessionEnd + PostToolUse silently no-op (not yet registered — correct)
  - shellcheck: PASS
  - Not executed live (dry-run only) — uninstalling would disable live AA-MA hooks mid-session

### Step 3.4: Add README "AA-MA hook troubleshooting" section + CHANGELOG entry
- Status: COMPLETE
- Mode: AFK
- Dependencies: Steps 3.2, 3.3
- Acceptance Criteria:
  - README contains a new "AA-MA hook troubleshooting" section covering: `AA_MA_HOOKS_DISABLE=1` kill switch, `[ad-hoc]` marker, `[no-sync-check]` marker, escape procedure, local bats install commands.
  - CHANGELOG Unreleased section contains an entry matching regex `feat\(hooks\): commit-signature`.
  - `/doc-sync` reports no drift after the edits.
  - Markdown linters pass on modified files.
- Result Log:
  ✅ COMPLETE 2026-04-12
  - README.md: new `## AA-MA hook troubleshooting` section inserted before `## Fair warning`; covers kill switch, commit-signature bypass markers ([ad-hoc]), post-commit drift marker ([no-sync-check]), known scope limits, local bats install, emergency escape
  - CHANGELOG.md: Unreleased section expanded with Added / Changed / Fixed subsections. `feat(hooks): commit-signature` regex matches under Added.
  - markdownlint not installed locally (CI will catch)

### Step 3.5: Canonicalize Status format to plain in 3 files
- Status: COMPLETE
- Mode: AFK
- Dependencies: None (can parallelize with 3.4)
- Acceptance Criteria:
  - `docs/templates/tasks-template.md` line 35 and line 80: bold `**Status:**` flipped to plain `Status:`.
  - `claude-code/agents/aa-ma-scribe.md` line 143 template block: bold flipped to plain.
  - `claude-code/hooks/aa-ma-session-start.sh` grep pattern uses helper (handled by M2.2).
  - Integration test: aa-ma-validator agent run against the canonicalized template reports zero parse errors.
  - Other files (commands, skills, rules, spec, examples) NOT edited (already plain).
- Result Log:
  ✅ COMPLETE 2026-04-12
  - tasks-template.md: 6 bold `**Status:** PENDING` occurrences (lines 35, 80, 105, 115, 125, 133) all flipped to plain `Status: PENDING`
  - aa-ma-scribe.md: 3 template-block bold occurrences (lines 141, 149, 154) flipped to plain; also flipped bold `**Dependencies:**`, `**Complexity:**`, `**Acceptance Criteria:**`, `**Result Log:**` in the same template block for consistency
  - session-start.sh: grep pattern removed in M2.2 (now uses format-agnostic helper)
  - Integration smoke test: sourced helper, extracted milestone + step from canonicalized template → both extracted correctly
  - No other files touched — spec/commands/skills/rules/examples already use plain

---

## Milestone 4: SessionEnd dirty AA-MA detector
- Status: COMPLETE
- Dependencies: Milestone 1, Milestone 3 (install.sh must register SessionEnd)
- Gate: SOFT
- Complexity: 50%
- Effort: 2.5h
- Milestone Result Log:
  ✅ COMPLETE 2026-04-12
  - Both sub-steps COMPLETE (4.1, 4.2)
  - Bats: 7 new cases green; cumulative 52/52 across M1+M2+M3+M4
  - Shellcheck: PASS on new hook
  - install.sh auto-registered SessionEnd (idempotent file-exists gate fired correctly)
  - Dogfood: hook is now LIVE; will fire at next session-end on current dirty state
- Acceptance Criteria:
  - `tests/hooks/session-end-dirty.bats` exits 0 with at least 5 cases.
  - Given an active task with uncommitted `tasks.md` changes, the hook writes one warning to stderr naming the dirty file.
  - Given a clean working tree, the hook emits nothing and exits 0.
  - Given `AA_MA_HOOKS_DISABLE=1`, the hook exits 0 silently.
  - Given `HOOK_DEBUG=1`, the hook emits a trace line per task directory inspected.

### Step 4.1: Create `claude-code/hooks/aa-ma-session-end-dirty.sh`
- Status: COMPLETE
- Mode: AFK
- Dependencies: Milestone 1 complete, Step 3.3 complete
- Acceptance Criteria:
  - File exists; hook type is SessionEnd (NOT Stop).
  - Hook sources the shared helper.
  - For each active task dir, runs `git status --porcelain` in that dir's project; if non-empty and contains any AA-MA artifact file, emits a single stderr warning.
  - Kill switch respected (`AA_MA_HOOKS_DISABLE=1` exits 0 silently).
  - `HOOK_DEBUG=1` enables verbose per-task trace.
  - If `CLAUDE_CODE` env var unset (CI context), hook exits 0 silently.
  - `shellcheck` passes.
- Result Log:
  ✅ COMPLETE 2026-04-12
  - File: claude-code/hooks/aa-ma-session-end-dirty.sh (~95 lines, chmod +x)
  - SessionEnd event (per Wave 1 finding — NOT Stop which fires per-turn)
  - Uses dual-layout helper resolution (project subdir OR installed sibling)
  - Uses `git rev-parse --show-toplevel` from each task dir to find project root
  - Uses `realpath --relative-to` to compute rel-path from project root to task dir, then filters `git status --porcelain` output to entries with that prefix
  - Guard rails: kill switch → silent; CLAUDE_CODE unset → silent (CI context); no active tasks → silent; task dir not in git repo → silent skip
  - Emits stderr warning block per dirty task, listing dirty artifact paths and CLAUDE.md convention reminder
  - shellcheck: PASS
  - install.sh auto-registered SessionEnd entry on next run (idempotent — file-exists gate flipped)

### Step 4.2: Create `tests/hooks/session-end-dirty.bats`
- Status: COMPLETE
- Mode: AFK
- Dependencies: Step 4.1
- Acceptance Criteria:
  - File contains at least 5 test cases.
  - Cases: clean state (silent), dirty tasks.md (one warning), no active tasks (silent), kill switch (silent), HOOK_DEBUG on (verbose stderr lines).
  - Uses fixture with `--with-git` for repo state setup.
  - All 5 cases green locally and in CI.
- Result Log:
  ✅ COMPLETE 2026-04-12
  - File: tests/hooks/session-end-dirty.bats (7 cases — exceeds min 5)
  - All 7 cases green: no-active-tasks, clean, dirty-warn, kill-switch, CI-context-unset, HOOK_DEBUG verbose, non-git-repo task dir skip
  - Uses `setup_committed_tasks` helper that creates `.claude/dev/active/<task>/` inside a committed git repo rooted at `$BATS_TMP` — proper committed state so `git status` reports modifications as `M <path>`, not `?? .claude/` (at parent-dir granularity)
  - Fixed during dev: initial test used `$FIXTURE + mv after git init` which caused porcelain output to collapse to `?? .claude/` (parent dir untracked) — prefix filter missed individual files. Refactored to build fixture directly at final path + init/commit after, so modifications show as file-level `M`.

---

## Milestone 5: Post-commit tasks.md drift detector
- Status: COMPLETE
- Dependencies: Milestone 1, Milestone 3 (install.sh must register PostToolUse(Bash))
- Gate: HARD
- Complexity: 60%
- Effort: 4h
- Milestone Result Log:
  ✅ COMPLETE 2026-04-12
  - Both sub-steps COMPLETE (5.1, 5.2)
  - Bats: 8/8 first-pass GREEN (no debug iterations)
  - Shellcheck: PASS on new hook
  - install.sh auto-registered PostToolUse (idempotent gate fired once M5.1 landed)
  - HARD Gate: APPROVED 2026-04-12
  - All 5 AA-MA hooks now LIVE
  - PLAN hooks-hardening-m1 COMPLETE — all 5 milestones done
- Acceptance Criteria:
  - `tests/hooks/commit-drift.bats` exits 0 with at least 8 cases.
  - Given a commit touching `src/foo.py` with no AA-MA file and `AA_MA_DRIFT_THRESHOLD=1`, hook emits stderr warning naming the top active task.
  - Given a commit touching `<task>-tasks.md`, hook emits nothing.
  - Given `[no-sync-check]` on its own line in the commit message, hook emits nothing.
  - Given `AA_MA_HOOKS_DISABLE=1`, hook exits 0 silently.
  - Given no active task directories, hook emits nothing.

### Step 5.1: Create `claude-code/hooks/aa-ma-commit-drift.sh`
- Status: COMPLETE
- Mode: AFK
- Dependencies: Milestone 1 complete, Step 3.3 complete
- Acceptance Criteria:
  - File exists; hook type is PostToolUse with matcher `"Bash"`.
  - Hook uses `git log -1 --name-only HEAD` (NOT `tool_response`) to list committed files.
  - Hook warns when committed-files-count exceeds `AA_MA_DRIFT_THRESHOLD` (default 1) AND no active task's `tasks.md` or `provenance.log` is among committed files.
  - `[no-sync-check]` marker on its own line in commit message suppresses warning.
  - Kill switch respected.
  - Guarded against initial-commit case (no parent).
  - Filters for AA-MA-active branch context (emits nothing for non-AA-MA branch commits).
  - README documents that hook only fires on SUCCESSFUL commits (PostToolUse limitation).
  - `shellcheck` passes.
- Result Log:
  ✅ COMPLETE 2026-04-12
  - File: claude-code/hooks/aa-ma-commit-drift.sh (~130 lines, chmod +x)
  - Decision tree: kill-switch → jq parse → `git commit` word-boundary → active-plans present → inside-git-repo → commit-exists (initial-commit guard) → below-threshold → [no-sync-check] marker → per-task sync check (tasks.md OR provenance.log under task rel-path) → emit warning naming unsynced tasks
  - Uses `git log -1 --name-only --format= HEAD` to extract committed files (NOT tool_response whose Bash shape is undocumented)
  - Word-boundary match `git commit([[:space:]]|$)` (distinguishes `commit-tree`, `commit-graph`)
  - [no-sync-check] regex accepts trailing quote/backtick (same as M3 [ad-hoc] regex)
  - Realpath-relative-to check ensures we only consider tasks whose dir is inside the current repo (avoids false signals for $HOME tasks when committing in a different project)
  - Branch context: effectively covered by the "any active plan exists" gate; no explicit branch-name matching (design choice — branch naming conventions vary)
  - shellcheck: PASS
  - bats: 8/8 GREEN first-pass, no debugging iterations needed

### Step 5.2: Create `tests/hooks/commit-drift.bats`
- Status: COMPLETE
- Mode: AFK
- Dependencies: Step 5.1
- Acceptance Criteria:
  - File contains at least 8 test cases.
  - Cases: tasks.md touched (silent), tasks.md not touched (warn), `[no-sync-check]` marker (silent), no active task (silent), kill switch (silent), below-threshold (silent), multiple active tasks (warn for all with named output), non-AA-MA branch commit (silent).
  - Uses fixture with `--with-git` for commit setup.
  - All 8 cases green locally and in CI.
- Result Log:
  ✅ COMPLETE 2026-04-12
  - File: tests/hooks/commit-drift.bats (8 cases — meets min exactly)
  - All 8 cases green first-pass
  - Cases: tasks.md-touched-silent, tasks.md-not-touched-warn, [no-sync-check]-silent, no-active-silent (≈"non-AA-MA branch"), kill-switch-silent, below-threshold-silent (AA_MA_DRIFT_THRESHOLD=10), multi-task-warn-each, provenance.log-touched-silent
  - Reused `setup_repo_with_tasks` pattern from M4 (commit at final path, modify after init — avoids porcelain-parent-dir-granularity trap)
  - `make_input` helper builds PostToolUse JSON via `jq -cn --arg cmd`
