<!-- ARCHIVED: 2026-04-12 17:29 UTC+01:00 -->
<!-- Plan: hooks-hardening-m1 - COMPLETE -->
<!-- Total Milestones: 5 | Duration: 2026-04-12 to 2026-04-12 -->

# hooks-hardening-m1 Context Log

_This log captures architectural decisions, trade-offs, and unresolved issues._

## 2026-04-12 Initial Context

**Feature Request (Phase 1):**

Harden the AA-MA hook subsystem. Three shipped hooks have correctness bugs (mtime ordering, path asymmetry, Status format mismatch). The AA-MA workflow lacks enforcement at commit time (signatures not auto-checked) and lacks observability (no drift detector for commits that don't touch tasks.md/provenance.log; no dirty-state warning at session end). All new hooks must be kill-switchable, testable via bats, and wired into CI.

**Key Decisions (Phase 2 Brainstorming — grill-me produced 16 decisions):**

- **Decision AD-001: Shared parser library extracted from existing hooks**
  - Rationale: DRY, single source of truth for Status/milestone/step extraction, enables test coverage of one regex instead of many.
  - Alternatives considered: inline parsing in each hook (status quo); a Python helper (requires python3 in hook runtime).
  - Trade-offs: bash helper sourced at hook startup adds a few milliseconds per hook invocation; accepted as negligible.

- **Decision AD-002: Format-agnostic Status regex in helper + plain canonical in source**
  - Rationale: Defense in depth. Source files move to plain format (`Status: PENDING`); helper accepts both plain and bold via `(\*\*)?Status:(\*\*)? +<WORD>` so it survives any drift.
  - Alternatives considered: canonicalize everything to bold; canonicalize everything to plain and make helper strict.
  - Trade-offs: slightly looser regex accepts both forms, including potential false positives on markdown like `<!-- Status: ACTIVE -->` (mitigation: strip HTML comments before grep; test case included).

- **Decision AD-003: Single kill switch `AA_MA_HOOKS_DISABLE=1`**
  - Rationale: one escape hatch to unblock the user if any hook misbehaves. Set-and-forget for CI environments.
  - Alternatives considered: per-hook disable vars; a config file.
  - Trade-offs: coarse-grained (all-or-nothing); acceptable given all hooks are low-risk by design.

- **Decision AD-004: Commit-signature enforcement via PreToolUse(Bash) with `[ad-hoc]` bypass**
  - Rationale: enforces the `[AA-MA Plan] <name>` footer without punishing genuine one-off work; `[ad-hoc]` marker is auditable in git log.
  - Alternatives considered: git pre-commit hook (requires per-repo install); silent logging only (no enforcement value).
  - Trade-offs: PreToolUse cannot see editor-opened commits (`git commit` with no `-m`); these pass through with documented limitation.

- **Decision AD-005: SessionEnd event for dirty detector (NOT Stop)**
  - Rationale: Stop fires per turn; using it would spam warnings after every assistant response. SessionEnd fires once at session conclusion (verified via Claude Code docs).
  - Alternatives considered: Stop with dedup state file; cron-like periodic check.
  - Trade-offs: warning only appears on graceful session end; accepted.

- **Decision AD-006: Post-hoc `git log -1 --name-only HEAD` for M5 drift detector (NOT `tool_response`)**
  - Rationale: `tool_response` shape is undocumented for Bash and unreliable; `git log` is guaranteed to reflect the committed state.
  - Alternatives considered: parse `tool_response` stdout (brittle); intercept PreToolUse(Bash) to pre-analyze (too early, no commit yet).
  - Trade-offs: PostToolUse only fires on SUCCESSFUL commits — failure cases never warn. Documented in README as a known limit.

- **Decision AD-007: Status format canonicalization scope limited to 3 files**
  - Rationale: Wave 1 Angle 3 found that canonicalizing 20+ files was out of proportion to the risk; helper is format-agnostic anyway. Canonical format applies to templates and the scribe (authoring surface), not to historical examples.
  - Alternatives considered: global flip (higher churn, higher review surface); no canonicalization (accepted format drift).
  - Trade-offs: two formats coexist in the codebase; helper tolerates both.

- **Decision AD-008: `bats-core/bats-action@v4` for CI**
  - Rationale: major-version pin catches patch fixes while bounding breaking-change risk.
  - Alternatives considered: pin to exact SHA (brittle); no pin (drift risk).
  - Trade-offs: minor version or patch regressions inside v4 could affect us; accepted and monitored via failing CI.

- **Decision AD-009: bats fixture builder with explicit signature and `--with-git` flag**
  - Rationale: Wave 2 fresh-agent review found fixture ambiguity; explicit signature with documented defaults removes guesswork for implementing agents.
  - Alternatives considered: hardcoded fixtures per test (duplication); a YAML spec file (over-engineered).
  - Trade-offs: 4 bats cases needed just to test the fixture — accepted as M1.1.bis.

- **Decision AD-010: Idempotent install.sh jq block with atomic tempfile+mv**
  - Rationale: re-running install.sh must not corrupt `~/.claude/settings.json`; `jq empty` post-write is a cheap validation gate.
  - Alternatives considered: in-place sed edits (fragile); a Python script (extra dependency).
  - Trade-offs: requires jq preflight check — acceptable (jq is already a runtime dependency for hooks).

- **Decision AD-011: `[no-sync-check]` marker for M5 drift bypass**
  - Rationale: symmetric with `[ad-hoc]`; keeps the escape hatch auditable in git log.
  - Alternatives considered: env var bypass only (less discoverable in commit history).
  - Trade-offs: two markers to remember; documented in README troubleshooting.

- **Decision AD-012: M5 (drift detector) kept in scope per Eng review**
  - Rationale: drift is the single most common AA-MA failure mode (commits don't touch tasks.md); deferring loses the main value of this plan.
  - Alternatives considered: defer M5 to a follow-up plan (Eng review recommendation).
  - Trade-offs: plan is larger; complexity rises from ~45% to ~55%. Accepted.

- **Decision AD-013: HARD gates on M2, M3, M5**
  - Rationale: these milestones change user-facing enforcement or settings.json; HARD gates require explicit approval artifact in context-log.md before advancing.
  - Alternatives considered: all SOFT (faster iteration); all HARD (friction on low-risk work).
  - Trade-offs: HARD gates pause `/execute-aa-ma-milestone` for user approval — desired for these milestones.

- **Decision AD-014: Fixture mtime_offsets spec precisely defined**
  - Rationale: Wave 2 flagged "mtime_offsets undefined" as CRITICAL; any agent picking up M1.1 must have zero ambiguity.
  - Alternatives considered: implicit (agent infers from context).
  - Trade-offs: spec is more verbose; accepted.

- **Decision AD-015: `scripts/uninstall.sh` updated alongside `install.sh`**
  - Rationale: Wave 1 Angle 3 caught this as missing. Any new registration must have a matching deregistration.
  - Alternatives considered: skip (rollback via settings.json.bak).
  - Trade-offs: additional sub-step (M3.3.bis); accepted.

- **Decision AD-016: jq preflight check with platform-specific install hint**
  - Rationale: install.sh should fail loudly with a fix, not silently corrupt settings.json.
  - Alternatives considered: bundle jq (over-engineered); assume presence (fragile).
  - Trade-offs: none — this is pure defensive engineering.

**Research Findings (Phase 3):**

- PreToolUse stdin JSON shape verified against Claude Code docs: `{session_id, hook_event_name, tool_name, tool_input: {command, ...}, tool_use_id}`.
- PostToolUse adds `tool_response` but shape is UNDEFINED for Bash — do not rely on it.
- SessionEnd vs Stop: SessionEnd fires once at session conclusion; Stop fires per turn.
- Exit code semantics: 0 = pass, 1 = hook infrastructure error, 2 = block with stderr to assistant.
- `bats-core/bats-action@v4` is current on GitHub Marketplace.
- Word-boundary `\bgit commit\b` via `grep -Eq` reliably distinguishes `git commit` from `git commit-tree` and `git commit-graph`.
- `git log -1 --name-only HEAD` reliably emits changed file paths for the most recent commit.
- Pre-existing bug in `~/.claude/hooks/lib/guard-protected-dirs.sh:14` reads `.command` instead of `.tool_input.command`; flagged but out of scope.

**Verification History (Phase 4.5 — Automated Mode):**

- **Wave 1 (4 parallel agents):**
  - Angle 1 Ground-Truth: 1 CRITICAL (pre-compact install.sh gap — plan addresses), 1 WARNING, 20 OK.
  - Angle 2 Assumptions: 2 CRITICAL (Stop hook semantics, Status format scope), 10 WARNING, 23 VERIFIED.
  - Angle 3 Impact: 4 CRITICAL (format scope, uninstall.sh, M3.5 incomplete file list, path emission), 4 WARNING, 4 OK.
  - Angle 4 Falsifiability: 0 CRITICAL, 2 WARNING, 15 OK (88% falsifiable; 2 rewrites applied to 1.2 and 3.4).
- **Wave 2 (fresh-agent simulation):**
  - Angle 5: 3 CRITICAL (mtime_offsets undefined, file set ambiguous, no M1.1 test), 5 WARNING, 3 INFO.
- **Angle 6 (specialist):** skipped — no domain keywords matched (Pydantic/API/schema/auth).

**Revisions applied (all 6 CRITICALs resolved across 2 revision loops):**

- R1: Stop to SessionEnd — M4 hook event corrected.
- R2: Status canonical — plain declared canonical; 3 files flip instead of 20+; helper stays format-agnostic.
- R3: uninstall.sh added — M3.3.bis created.
- R4: mtime_offsets spec — "comma-separated integer seconds offset from now".
- R5: file set spec — 5 standard AA-MA files per fixture task; optional `--with-git` flag.
- R6: M1.1.bis test — fixture builder has its own red-green bats test file.

**Final verification status: PASS** (0 unresolved CRITICALs after revisions).

**Remaining Questions / Unresolved Issues:**

- None blocking. Pre-existing bug in `guard-protected-dirs.sh` is logged and scheduled for a follow-up plan.
- Multi-active-plan behavior for M5 (warn per task) is documented but not field-tested; dogfood period post-M5 will inform any tuning of `AA_MA_DRIFT_THRESHOLD`.

## 2026-04-12T13:50:07Z Milestone Completion: M1 Foundations
- Status: COMPLETE
- Key outcome: Extracted shared bash parser (aa-ma-parse.sh, 5 exports) with bats harness wired into CI. All 22 bats cases green.
- Artifacts: tests/hooks/fixtures/build_active_dir.sh (+ .bats), claude-code/hooks/lib/aa-ma-parse.sh, tests/hooks/aa-ma-parse.bats, .github/workflows/security.yml (added bats job)
- Tests: 22/22 PASS (6 fixture + 16 parser)
- Dev fixes: (1) fixture flag parser ate negative mtime offsets → restricted --* matcher; (2) helper temp-file+trap race on process-substitution callers → refactored to in-memory bash array with sort pipe
- Next milestone: M2 Fix shipped hooks (tests-first) — HARD gate

## [2026-04-12] GATE APPROVAL: M2 Fix shipped hooks
- Gate: HARD
- Approved by: Stephen Newhouse
- Criteria verified: 6/6 — session-start bats 7/7 GREEN; pre-compact bats 6/6 GREEN; both hooks shellcheck clean; both hooks source helper; mtime-top + path fixes verified; both-paths iteration + project-first collision verified
- Impact: MEDIUM (session-start behavioural change — absolute path, mtime-top, multi-task footer) + LOW (pre-compact purely additive)
- Decision: APPROVED

## 2026-04-12T13:58:14Z Milestone Completion: M2 Fix shipped hooks
- Status: COMPLETE
- Key outcome: Both shipped hooks now source the M1 shared parser. Three silent bugs fixed (mtime ordering, path emission, pre-compact single-path). Added multi-task footer to session-start. Kill-switch respected.
- Artifacts: aa-ma-session-start.sh (rewrite), pre-compact-aa-ma.sh (rewrite), tests/hooks/session-start.bats (+), tests/hooks/pre-compact.bats (+)
- Tests: 13/13 new cases + 22/22 M1 cases = 35/35 PASS
- Next milestone: M3 Commit-signature + install.sh + docs + canonicalization — HARD gate, complexity 70% (close-to-threshold flag)

## [2026-04-12] GATE APPROVAL: M3 Commit-signature + install.sh + docs + canonicalization
- Gate: HARD
- Approved by: Stephen Newhouse
- Criteria verified: 7/7 — commit-signature bats 10/10 GREEN; install.sh dry-run + live + idempotent; uninstall.sh symmetric (dry-run validated); README troubleshooting section; CHANGELOG Unreleased entries with feat(hooks): commit-signature regex; Status format canonicalised in 3 files; helper compat verified with canonicalised template
- Impact: MEDIUM overall — commit-signature LIVE in user session (blocking behavior); install.sh refactor touches user settings.json (mitigated by .bak, atomic writes, path-substring idempotence).
- Decision: APPROVED

## 2026-04-12T14:18:11Z Milestone Completion: M3 Commit-signature + install.sh + docs + canonicalization
- Status: COMPLETE
- Key outcome: AA-MA commit signature enforcement is LIVE. install.sh now handles all 5 planned hooks idempotently (2 active, 3 skipped pending M4/M5). uninstall.sh is symmetric. Status format canonicalised to plain. Dogfood test: this very commit exercises the enforcer it contains.
- Artifacts: aa-ma-commit-signature.sh (+), commit-signature.bats (+), install.sh/uninstall.sh (M), README/CHANGELOG (M), tasks-template.md/scribe.md (M, canonicalised)
- Tests: 10 new commit-signature cases. Cumulative 45/45 across M1+M2+M3.
- Next milestone: M4 SessionEnd dirty detector — SOFT gate, complexity 50%

## 2026-04-12T14:29:34Z Milestone Completion: M4 SessionEnd dirty detector
- Status: COMPLETE
- Key outcome: SessionEnd hook now warns on dirty AA-MA artifacts at session end. Silent in CI, silent under kill switch, advisory-only (exits 0 always). install.sh auto-registered the new hook (idempotence demonstrated end-to-end — file-exists gate triggered registration on first post-author run).
- Artifacts: aa-ma-session-end-dirty.sh (+), session-end-dirty.bats (+)
- Tests: 7 new cases. Cumulative 52/52 across M1+M2+M3+M4.
- Next milestone: M5 Post-commit tasks.md drift detector — HARD gate, complexity 60%

## [2026-04-12] GATE APPROVAL: M5 Post-commit tasks.md drift detector
- Gate: HARD
- Approved by: Stephen Newhouse
- Criteria verified: 5/5 — commit-drift.bats 8/8 GREEN; PostToolUse(Bash) matcher + git log -1 --name-only post-hoc inspection; kill-switch + [no-sync-check] + threshold + initial-commit guard all tested; shellcheck clean
- Impact: MEDIUM — hook fires after every successful Bash tool call; word-boundary gate filters non-commits early; [no-sync-check] + AA_MA_DRIFT_THRESHOLD + kill switch provide three bypass layers
- Decision: APPROVED

## 2026-04-12T14:40:43Z Milestone Completion: M5 Post-commit drift detector
- Status: COMPLETE
- Key outcome: All 5 AA-MA hooks LIVE. Post-commit drift detector warns when a commit lands on an active AA-MA branch without touching any tasks.md or provenance.log, advisory-only, with 3-layer bypass.
- Artifacts: aa-ma-commit-drift.sh (+), commit-drift.bats (+)
- Tests: 8 new. Cumulative 60/60 across ALL milestones.

## 2026-04-12T14:40:43Z PLAN COMPLETION: hooks-hardening-m1
- Status: ALL 5 MILESTONES COMPLETE
- Total test cases: 60/60 GREEN (build_active_dir 6, aa-ma-parse 16, session-start 7, pre-compact 6, commit-signature 10, session-end-dirty 7, commit-drift 8)
- All 5 AA-MA hooks registered and LIVE in ~/.claude/settings.json: SessionStart, PreCompact, PreToolUse(Bash), SessionEnd, PostToolUse(Bash)
- Shellcheck: PASS on all scripts (8 files: 5 hooks + helper + 2 install scripts + fixture)
- Three critical silent bugs fixed: mtime-ordering, path-emission, format-mismatch
- One pre-existing gap fixed: PreCompact registration
- Next action: archive via `/archive-aa-ma hooks-hardening-m1`
