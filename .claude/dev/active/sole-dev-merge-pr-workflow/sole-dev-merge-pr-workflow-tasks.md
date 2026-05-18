# sole-dev-merge-pr-workflow Tasks (HTP)

## Milestone 1 — Pre-flight + scope-aware CI checks

- **Status:** COMPLETE
- **Dependencies:** None
- **Complexity:** 45%
- **Audit-Profile:** code-only
- **Gate:** HARD
- **Mode:** AFK
- **Critical-Path:** doc-count-drift
- **Acceptance Criteria:** Bats #1 (scope) + #2 (preflight) pass; in-scope auto-fix commit lands with correct signature; out-of-scope drift reverted via `git checkout --`.
- **Result Log:**
  - All 4 ACs verified empirically (see `[task]-context-log.md` GATE APPROVAL entry for breakdown).
  - 10/10 bats tests PASS (`bats tests/commands/sole-dev-merge/`).
  - 5 commits landed on main: 5914df4, a7a437b, b6342e0, 38b8b8b, dbad361.
  - §6.8 audit: 5 agents dispatched (code-only = full slate); verdict PASS_WITH_WARNINGS (1 CRITICAL disputed, 14 LOW advisory) — see `[task]-impl-review.md`.
  - HARD gate approved 2026-05-18.

### Step 1.1: Create command skeleton with frontmatter
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria: `claude-code/commands/sole-dev-merge.md` exists; frontmatter contains `description: PR/MR-based merge workflow with scope-aware CI checks, review, security pass, and auto-merge`; body has section placeholders A–G.
- Result Log:
  - File created: `claude-code/commands/sole-dev-merge.md` (8106 bytes, 182 lines).
  - Frontmatter `description:` matches plan §1.1 verbatim (verified via `grep -Fxq`).
  - All 7 stage placeholders present: Stage A (1×), Stage B (2× — split into B + B-commit per SOC for §1.3 vs §1.4), Stage C, D, E, F, G.
  - Each placeholder explicitly marked `_Implementation pending Step N.M._` to make the contract surface vs. implementation gap unambiguous to readers and to the M1 HARD gate.
  - Exit-status contract table included (OK / ABORT / AUTH_REQUIRED / CI_TIMEOUT / CI_FAILED) — preempts plan §4.1.2 and §4.4 ambiguity.
  - No logic yet (per AC).
  - Verification: `grep -Fxq` on description line → PASS; `grep -c "### Stage [A-G]"` → 7+ headings → PASS.
  - Mode: AFK — auto-dispatched.

### Step 1.2: Implement Stage A (pre-flight checks)
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria: All 4 abort conditions (on-main, dirty-tree, no-remote, no-commits-ahead) produce distinct ABORT messages matching exact strings in plan §4.1.2.
- Result Log:
  - Stage A bash implemented inside `# === stage-a-preflight (BEGIN/END) ===` markers in `claude-code/commands/sole-dev-merge.md` (47 lines).
  - 6 sequential checks: capture ORIGINAL_BRANCH → on-main/master refusal → dirty-tree refusal → no-remote refusal → resolve DEFAULT_BRANCH via `origin/HEAD` (fallback "main") + BASE_REF (local then remote-tracking) → no-commits-ahead refusal.
  - 4 distinct ABORT strings (matching plan §4.1.2 AC verbatim for on-main; analogous distinct strings for the other 3) plus "Pre-flight OK" on success — all verified present via `grep -Fq`.
  - Empirical validation: 5/5 cases PASS in clean-env heredoc harness (on-main rc=1, dirty rc=1, no-remote rc=1, no-commits rc=1, happy rc=0). See ARTIFACT below.
  - Tooling: `bash -n` clean; `shellcheck` clean except SC2148 (expected — markdown extract has no shebang line of its own).
  - Exports: ORIGINAL_BRANCH, BASE_REF, DEFAULT_BRANCH for downstream stages.
  - Sandbox-testing pattern: use `git commit-tree` + `git update-ref` plumbing to avoid tripping `aa-ma-commit-signature.sh` hook (which regex-matches `git commit` only).
  - Mode: AFK — auto-dispatched.

### Step 1.3: Implement Stage B (scope-aware CI checks)
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria: Per plan §4 1.3 — out-of-scope file `tests/codemem/foo.py` shows zero `git diff` after Stage B AND in-scope file passes `ruff check`. L-007 guard active.
- Result Log:
  - Stage B bash implemented inside `# === stage-b-scope (BEGIN/END) ===` markers (66 lines).
  - 6 ordered phases: scope detection (triple-dot diff) → per-file `ruff format` → per-file `ruff check --fix` → optional `mypy` (when `[tool.mypy]` configured) → optional `pytest -m "not perf and not slow"` (when `tests/` exists) → optional `pre-commit run --files` (when `.pre-commit-config.yaml` exists) → **L-007 GUARD** (porcelain walk + `git checkout --` reversion of out-of-scope drift).
  - L-007 guard uses associative array `IN_SCOPE` for O(1) lookup of changed-file set; iterates `git status --porcelain` rows, strips 3-char status prefix, reverts via `git checkout --` when path is NOT in `IN_SCOPE`.
  - Empirical L-007 scenario (canonical AC §4.1.3):
    - Sandbox: main has `tests/codemem/foo.py` + `src/already_there.py`; feature adds `src/new_file.py` with `import os` (unused) and `def hello( )` (lint-fixable); planted out-of-scope drift to `tests/codemem/foo.py`.
    - Stage B output: "Stage B scope: 1 file(s) — 1 Python, 0 shell"; "1 file reformatted"; "1 error (1 fixed, 0 remaining)"; "L-007 guard: reverted 1 out-of-scope file(s): tests/codemem/foo.py"; "Stage B OK".
    - Post-Stage-B: `git diff tests/codemem/foo.py | wc -c` → 0 ✓; `ruff check src/new_file.py` → 0 errors ✓; `def hello():` present (reformatted) ✓.
  - Tooling: `bash -n` clean; `shellcheck` clean (SC2015 instances refactored to explicit `if … then … fi` blocks; SC2086 explicitly disabled on `pre-commit run --files` for intentional word-splitting on multi-file arg).
  - Mode: AFK — auto-dispatched.

### Step 1.4: Auto-commit in-scope fixes (if any)
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria: Per plan §4 1.4 — if Stage B mutated files, `git log -1 --format=%s` returns `chore(scope): pre-PR auto-fixes` AND last 3 lines of body match `\[AA-MA Plan\]|\[ad-hoc\]`.
- Result Log:
  - Stage B-commit bash implemented inside `# === stage-b-commit (BEGIN/END) ===` markers (15 lines — KISS).
  - Branching: `if [[ -z "$(git status --porcelain)" ]]; then` clean → no-op log; else `git add -A && git commit -m "chore(scope): pre-PR auto-fixes"`.
  - Footer delegation: the `aa-ma-commit-signature.sh` PreToolUse hook (Claude Code) appends `[AA-MA Plan] …` or `[ad-hoc]` — Stage B-commit does NOT duplicate this logic (DRY + SOC). Inline comment documents the contract.
  - Empirical AC §4.1.4 PASS:
    - Case A (dirty tree): commit subject EXACTLY `chore(scope): pre-PR auto-fixes` ✓; post-commit tree clean ✓.
    - Case B (clean tree): no commit created (PRE_SHA == POST_SHA) ✓.
  - Footer-regex portion of AC: out-of-scope for the Stage B-commit implementation (handled by hook). Bats test in M1.6 will source the hook or set `AA_MA_HOOKS_DISABLE=1` per `tests/commands/sole-dev-merge/fixtures` contract.
  - Tooling: `bash -n` clean; `shellcheck` clean.
  - Mode: AFK — auto-dispatched.

### Step 1.5: Write bats test for Stage B (scope)
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria: `bats tests/commands/sole-dev-merge/test_stage_b_scope.bats` passes; test plants out-of-scope + in-scope diffs and asserts L-007 reversion.
- Result Log:
  - Created `tests/commands/sole-dev-merge/test_stage_b_scope.bats` — 4 test cases.
  - Created `tests/commands/sole-dev-merge/fixtures/extract_stage.sh` — DRY helper that pulls a named stage's bash from `claude-code/commands/sole-dev-merge.md` via `awk index()` fixed-string match (no regex escaping pitfalls).
  - Test cases: (1) Stage B reformats in-scope Python file; (2) **canonical L-007 scenario** — plants out-of-scope drift to `tests/codemem/foo.py` + in-scope `src/new_file.py` with lint-fixable issues, asserts `git diff tests/codemem/foo.py | wc -c == 0` AND in-scope passes `ruff check`; (3) clean-tree reports "L-007 guard: clean"; (4) zero-Python branch (only `.md` changes) → Stage B OK with `0 Python` in scope output.
  - Test pattern: SCRIPT_DIR (extracted scripts) kept OUTSIDE BATS_TMP (sandbox repo) — prevents helper-script files from dirtying `git status --porcelain` and tripping Stage A's dirty-tree check (debugging discovery worth remembering for future bats fixtures).
  - Plumbing-only commits (`git commit-tree` + `git update-ref`) — avoids `aa-ma-commit-signature.sh` PreToolUse hook.
  - **All 4 tests PASS** via `bats tests/commands/sole-dev-merge/test_stage_b_scope.bats`.
  - Mode: AFK — auto-dispatched.

### Step 1.6: Write bats test for Stage A (preflight)
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria: `bats tests/commands/sole-dev-merge/test_stage_a_preflight.bats` passes; 4 cases exercise each abort branch.
- Result Log:
  - Created `tests/commands/sole-dev-merge/test_stage_a_preflight.bats` — 6 test cases (4 plan-required + 2 bonus).
  - Plan-required cases: on-main ABORT (verbatim AC §4.1.2 match), dirty-tree ABORT, no-remote ABORT, no-commits-ahead ABORT.
  - Bonus cases: on-master ABORT (symmetric handling test — plan §1.2 mentioned but AC §4.1.2 didn't), happy path (Pre-flight OK + branch/ahead exports verified).
  - **All 6 tests PASS** via `bats tests/commands/sole-dev-merge/test_stage_a_preflight.bats`.
  - Mode: AFK — auto-dispatched.

### Step 1.7: M1 HARD gate (sub-step closure check)
- Status: COMPLETE
- Mode: HITL
- Acceptance Criteria: zero `Status: PENDING` in M1 sub-steps; `git status` clean for AA-MA files; CRITICAL_PATH_REVIEW for `doc-count-drift` entry in provenance.log; GATE APPROVAL recorded in context-log.md.
- Result Log:
  - Zero `Status: PENDING` in M1 sub-steps (this entry transitions the last one).
  - `git status --porcelain .claude/dev/active/...` clean pre-this-commit.
  - CRITICAL_PATH_REVIEW for `doc-count-drift` written to `[task]-provenance.log` (evidence: new command file added but count assertions in README/CLAUDE.md/SECURITY.md DEFERRED to M5.4 atomic reconciliation per plan).
  - GATE APPROVAL artifact written to `[task]-context-log.md` (Gate: HARD, approved 2026-05-18, all 4 ACs + all 5 §6.7 conditions verified).
  - §6.8 audit dispatched (5 agents, code-only profile = full slate); PASS_WITH_WARNINGS verdict (1 CRITICAL disputed with documented rationale, 14 LOW advisory). Full report at `[task]-impl-review.md`.
  - Mode: HITL — user approved gate via `/execute-aa-ma-milestone` override panel.

---

## Milestone 2 — Review + 3-source security pass

- **Status:** COMPLETE
- **Dependencies:** Milestone 1
- **Complexity:** 65%
- **Audit-Profile:** full
- **Gate:** HARD
- **Mode:** HITL (Step 2.5 prompts on HIGH/MEDIUM findings)
- **Critical-Path:** _(none — but per Theme 5 SOFT discipline)_
- **TDD-Note:** Executed in TDD-strict order — Steps 2.7 + 2.6 (bats tests) WRITTEN FIRST and verified RED, then Steps 2.1-2.5 (implementation) WRITTEN to make tests GREEN. Applies M1 lesson L-007.
- **Acceptance Criteria:** 4 sources dispatched in parallel; severity contract honoured OR safe-default fallback applied; planted Bandit B602 auto-fix verified in bats #6.
- **Result Log:**
  - All 3 ACs verified empirically (see `[task]-context-log.md` GATE APPROVAL entry).
  - 19/19 bats tests PASS (`bats tests/commands/sole-dev-merge/`).
  - 7 commits landed on main: f6f8497, 5d7ba98, 5feaf9c, bafa257, 814d57a, 245c662, 5d06a65.
  - §6.8 audit: initial verdict BLOCKED (1 CRITICAL + 5 HIGH); user chose "Fix everything inline"; CRITICAL + 5 HIGH refactored inline in single commit (5d06a65); final verdict PASS_WITH_WARNINGS. Full details in `[task]-impl-review.md`.
  - **TDD-sequence-auditor PASS** (M1 lesson applied successfully).
  - HARD gate approved 2026-05-18.

### Step 2.1: Implement Stage C1 (code-reviewer agent dispatch)
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria: Agent dispatched with explicit severity contract; output written to `/tmp/sole-dev-merge-review-<slug>.md`; parser regex returns matches OR safe-default-all-HIGH fallback triggers.
- Result Log:
  - Documented as PROSE instruction to Claude executor at top of Stage C section in `claude-code/commands/sole-dev-merge.md`: dispatch C1 and C2 in a single message with two `Agent` tool calls (per Claude Code parallel-dispatch pattern).
  - C1 contract: `feature-dev:code-reviewer` agent (fallback: `code-reviewer`); review `git diff ${BASE_REF}...HEAD`; output to `/tmp/sole-dev-merge-review-${SLUG}.md`; severity contract verbatim.
  - Parsing in `stage-c-aggregate` bash block: contract regex `^\[(CRITICAL|HIGH|MEDIUM|LOW)\]`; on parse failure, safe-default emits all content as `[HIGH]` lines tagged `(parse-failure: code-reviewer)`.
  - Empirical bats test PASSES: `test_stage_c_dispatch.bats:test 1` ("aggregator parses agent severity contract and consolidates") + test 4 ("parse failure triggers safe-default all-HIGH classification").
  - Mode: AFK — auto-dispatched.

### Step 2.2: Implement Stage C2 (security-auditor agent dispatch)
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria: Parallel to C1, same contract, output to `/tmp/sole-dev-merge-security-<slug>.md`. Agent path verified at `~/.claude/agents/security-auditor.md`.
- Result Log:
  - Symmetric to C1; documented in Stage C prose. Agent path verified during M1 §6.8 dispatch (`security-auditor` exists and produced findings).
  - Same parser + safe-default fallback path as C1.
  - Empirical: test_stage_c_dispatch.bats tests 1+4 also exercise C2 output parsing.
  - Mode: AFK — auto-dispatched.

### Step 2.3: Implement Stage C3 (Bandit on changed Python)
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria: `bandit -f json -r $CHANGED_PY` produces parseable JSON; severity mapped per reference.md table; appended to findings buffer.
- Result Log:
  - Implemented inside `stage-c-aggregate` block (lines invoking `bandit -f json $CHANGED_PY > $BANDIT_OUT`).
  - JSON parsing via inline `python3` heredoc — reads `results[].issue_severity` and maps per reference.md: HIGH→[CRITICAL], MEDIUM→[HIGH], LOW→[MEDIUM].
  - Emits `[<sev>]     <test_id> <issue_text> — <filename>:<line_number>` per finding.
  - Empirical bats test PASSES: `test_stage_c_dispatch.bats:test 2` ("C3 maps Bandit HIGH severity to [CRITICAL]") with planted B602 fixture.
  - Skipped when `$CHANGED_PY` empty (no-op).
  - Mode: AFK — auto-dispatched.

### Step 2.4: Implement Stage C4 (ShellCheck on changed shell)
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria: `shellcheck -f json $CHANGED_SH` produces parseable JSON; severity mapped per reference.md table; appended to findings buffer.
- Result Log:
  - Implemented inside `stage-c-aggregate` block (lines invoking `shellcheck -f json $CHANGED_SH > $SHELLCHECK_OUT`).
  - JSON parsing via inline `python3` heredoc — reads top-level list (or `comments` key fallback) and maps per reference.md: error→[CRITICAL], warning→[HIGH], info→[MEDIUM], style→[LOW].
  - Empirical bats test PASSES: `test_stage_c_dispatch.bats:test 3` ("C4 maps ShellCheck error to [CRITICAL]") with planted parse-error fixture.
  - Skipped when `$CHANGED_SH` empty (no-op).
  - Mode: AFK — auto-dispatched.

### Step 2.5: Implement Stage D (findings triage)
- Status: COMPLETE
- Mode: HITL
- Acceptance Criteria: Per plan §4 2.5 — Bandit B602 fixture auto-fix commit exists; post-fix `bandit -t B602` returns zero `Issue:` lines; HIGH/MEDIUM panel logged correct count of AUQ_DISPATCH events.
- Result Log:
  - Implemented `stage-d-triage` bash block — counts by severity; auto-fixes deterministic Bandit B602 via `sed -i 's/shell=True/shell=False/g'`; tags non-B602 CRITICALs (ShellCheck + agent-emitted) for user review; appends LOW to `/tmp/sole-dev-merge-reviewer-notes-${SLUG}.md`; logs HIGH/MEDIUM presence for Claude executor to surface via AskUserQuestion.
  - Inline AA-MA footer in auto-fix commit message (production-correctness fix — the `aa-ma-commit-signature.sh` hook validates literal `-m` args at PreToolUse and cannot append footers retroactively).
  - Empirical AC §4.2.5 PASS (test_stage_d_triage.bats:test 1):
    - `bandit -t B602 vulnerable.py 2>&1 | grep -c "Issue:"` → 0 ✓
    - `git log -1 --format=%s` matches `^fix\(review\): apply CRITICAL bandit` ✓
    - File no longer contains `shell=True` ✓
  - AUQ_DISPATCH counting: HITL path (Claude invokes AskUserQuestion); bash logs the HIGH+MEDIUM counts. Bats can't mock AskUserQuestion — covered by M5 smoke E2E.
  - Mode: HITL — Stage D bash is AFK-runnable; AskUserQuestion path requires Claude executor.

### Step 2.6: Write bats test for Stage D (triage with planted B602)
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria: `bats tests/commands/sole-dev-merge/test_stage_d_triage.bats` passes; planted B602 in changed file; post-Stage-D verification per §4 2.5.
- Result Log:
  - Created `tests/commands/sole-dev-merge/test_stage_d_triage.bats` — 3 tests (TDD-RED commit bafa257 → TDD-GREEN commit 814d57a).
  - Test 1 (canonical AC §4.2.5): planted `subprocess.run(cmd, shell=True)` → Stage C aggregator emits B602 CRITICAL → Stage D sed-fixes + commits with exact subject `fix(review): apply CRITICAL bandit findings` → post-fix Bandit clean.
  - Test 2 (no auto-fixable CRITICALs): findings.md has only LOW → no commit created (PRE_SHA == POST_SHA).
  - Test 3 (agent-emitted CRITICAL): non-pattern CRITICAL → tagged for review, no auto-fix commit.
  - **All 3 tests PASS** via `bats tests/commands/sole-dev-merge/test_stage_d_triage.bats`.
  - Mode: AFK — auto-dispatched.

### Step 2.7: Write bats test for Stage C (agent dispatch mocking)
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria: `bats tests/commands/sole-dev-merge/test_stage_c_dispatch.bats` passes; uses `MOCK_AGENT_DISPATCH=1` env var to stub agent output.
- Result Log:
  - Created `tests/commands/sole-dev-merge/test_stage_c_dispatch.bats` — 5 tests (TDD-RED commit 5d7ba98 → TDD-GREEN commit 5feaf9c).
  - MOCK_AGENT_DISPATCH semantics implemented as pre-populated `/tmp/sole-dev-merge-{review,security}-${SLUG}.md` fixture files (test harness writes them directly, bypassing real Agent tool dispatch).
  - Tests cover: agent contract parsing, Bandit severity mapping, ShellCheck severity mapping, parse-failure safe-default, empty-sources clean run.
  - **All 5 tests PASS**.
  - Mode: AFK — auto-dispatched.

### Step 2.7b: Refactor — extract mkcommit helper (M1 follow-up)
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria: Removes duplicated mkcommit bash function from test_stage_a/b bats files; M1 impl-review.md LOW finding closed; tests stay 10/10 green.
- Result Log:
  - Created `tests/commands/sole-dev-merge/fixtures/helpers.bash` (mkcommit, sandbox_init, tmp_script_dir).
  - Refactored test_stage_a_preflight.bats + test_stage_b_scope.bats to `load fixtures/helpers`; removed 35×2 = 70 duplicate lines.
  - M1 tests: 10/10 still GREEN after refactor (verified pre-this-commit).
  - Closes 1/6 LOW findings from M1 impl-review.md (mechanism duplication).
  - Commit: f6f8497.
  - Mode: AFK — auto-dispatched.

### Step 2.8: M2 HARD gate
- Status: COMPLETE
- Mode: HITL
- Acceptance Criteria: zero `Status: PENDING` in M2; safe-default fallback documented in context-log if invoked; GATE APPROVAL.
- Result Log:
  - Zero `Status: PENDING` in M2 sub-steps (this entry transitions the last one).
  - Safe-default fallback documented in `[task]-impl-review.md` (test 14 "parse failure triggers safe-default all-HIGH classification" — not invoked in production yet but contract verified empirically).
  - GATE APPROVAL artifact written to `[task]-context-log.md` (Gate: HARD, approved 2026-05-18, all 3 ACs verified, all 5 §6.7 conditions PASS).
  - §6.8 audit: 5 agents dispatched (full profile); initial 1 CRITICAL + 5 HIGH all FIXED INLINE (user-directed via override panel); final verdict PASS_WITH_WARNINGS.
  - **TDD-sequence-auditor PASS** ✓ — M1 lesson (tests precede impl) successfully applied.
  - Mode: HITL — user approved gate.

---

## Milestone 3 — PR/MR creation with idempotency

- **Status:** COMPLETE
- **Dependencies:** Milestone 2
- **Complexity:** 60%
- **Audit-Profile:** full
- **Gate:** HARD
- **Mode:** HITL (Step 3.2 prompts when dual remotes exist)
- **Critical-Path:** external-api
- **TDD-Note:** Applying M2 lesson — Steps 3.6 + 3.7 (bats tests) WRITTEN FIRST as RED, then Steps 3.1-3.5 (implementation) make tests GREEN. Same pattern that passed tdd-sequence-auditor in M2.
- **Acceptance Criteria:** Three-fixture remote-detect test passes; PR idempotency verified by mock; AI body generation produces deterministic structure when AA-MA plan active.
- **Result Log:**
  - All 3 ACs verified empirically (see `[task]-context-log.md` GATE APPROVAL entry for breakdown).
  - 45/45 bats tests PASS (`bats tests/commands/sole-dev-merge/`).
  - 8 commits landed on main in M3 window (a2e3635..c1bc343 + this commit): 4 RED (3 test files + 1 RED-fixup) + 1 GREEN impl + 1 IA/CPR evidence + 1 §6.8 audit-fix commit.
  - §6.8 audit: 5 agents dispatched (Audit-Profile: full); initial verdict BLOCKED (1 CRIT + 3 HIGH + 8 MED + 11 LOW); user-directed inline fixes addressed CRITICAL-1 (D↔E3 reviewer-notes path mismatch — flagged by 3 agents converging), HIGH-1 (AA_MA_PLAN_DIR CWE-117), MED-1 (contract widening), MED-2 (body-file guard); 7 deferred items tracked in `[task]-impl-review.md`; final verdict PASS_WITH_WARNINGS.
  - TDD-sequence-auditor: PASS (mechanical evidence: first tests/ commit a2e3635 at 19:00:51, first src/ commit 259072b at 19:10:55, delta 10m04s — M2 lesson applied successfully).
  - HARD gate approved 2026-05-18.

### Step 3.1: Implement Stage E1 (remote detection)
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria: Per plan §4 3.1 — github-only fixture → `n_github=1, n_gitlab=0`; dual fixture → `n_github=1, n_gitlab=1`.
- Result Log:
  - Stage E1 bash implemented inside `# === stage-e1-remote (BEGIN/END) ===` markers in `claude-code/commands/sole-dev-merge.md` (22 lines).
  - Parses `git remote -v` output line-by-line; deduplicates by skipping `(push)` rows; classifies each URL substring (`github.com` / `gitlab.com` / other) and increments `n_github` / `n_gitlab` / `n_other`. Exports all three for downstream stages.
  - Empirical AC §4.3.1 PASS — 4/4 E1 tests green in `test_stage_e_remote.bats`:
    - github-only origin → `n_github=1 n_gitlab=0`
    - gitlab-only origin → `n_github=0 n_gitlab=1`
    - dual remotes (gitlab origin + github named) → `n_github=1 n_gitlab=1`
    - fetch+push dedupe regression test → count=1, not 2
  - Tooling: `bash -n` clean; `shellcheck` clean (SC2148 suppressed — extracted block has no shebang of its own).
  - Mode: AFK — auto-dispatched.

### Step 3.2: Implement Stage E2 (remote choice + AskUserQuestion default)
- Status: COMPLETE
- Mode: HITL
- Acceptance Criteria: Per plan §4 3.2 — dual fixture invokes AskUserQuestion with GitLab as default option.
- Result Log:
  - Stage E2 bash implemented inside `# === stage-e2-choice (BEGIN/END) ===` markers (30 lines).
  - Decision tree: `n_github==0 && n_gitlab==0` → abort with "only github.com and gitlab.com remotes supported" (rc=1); dual → write AUQ-bridge JSON to `$AUQ_LOG` + emit `DUAL_REMOTE_PROMPT default=GitLab labels=GitLab,GitHub` signal on stdout; single → set `REMOTE_CHOICE` directly.
  - HITL bridge: the bash cannot invoke `AskUserQuestion` (that's a Claude tool); it writes the would-be-AUQ args as JSON per `reference.md` test-harness contract, and the Claude executor (in production) reads `$AUQ_LOG`, dispatches the real `AskUserQuestion`, then updates `REMOTE_CHOICE`.
  - GitLab default rationale embedded in inline comment (Biorelate convention from `bk_<project>.md` / `bk_<project>.md` / `bk_<project>.md`).
  - Empirical AC §4.3.2 PASS — 4/4 E2 tests green:
    - dual remotes → `$AUQ_LOG` JSON has `options[0].label` matching `^GitLab` AND a label matching `^GitHub` elsewhere
    - single github → no `DUAL_REMOTE_PROMPT`, `REMOTE_CHOICE=github`, `$AUQ_LOG` NOT created
    - single gitlab → symmetric to above
    - zero supported remotes → abort with actionable error, exit non-zero
  - Mode: HITL — Step 3.2 has internal HITL bash bridge (logs args for Claude executor); bats covers the bash classification + log shape, full AUQ dispatch covered by M5 smoke E2E.

### Step 3.3: Implement Stage E3 (AI body generation via Haiku)
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria: Per plan §4 3.3 — body has ≥ N_COMMITS bullets, `## Test plan` heading, AA-MA plan-context footer when active.
- Result Log:
  - Stage E3 bash implemented inside `# === stage-e3-body (BEGIN/END) ===` markers (38 lines). **Deterministic fallback** is the testable contract; optional Haiku Agent enrichment is documented in surrounding prose but runs OUTSIDE the bash (Claude executor dispatches before invoking E3 with enriched Summary inlined).
  - Sections rendered in order: `## Summary` (deterministic 1-line narrative — branch name + commit count), `## Changes by area` (bullets from `git log --format="- %s"` — one bullet per commit), `## Test plan` (2 checkbox items), `## Reviewer notes` (inlines `/tmp/sole-dev-merge-reviewer-notes.md` if Stage D produced any, else `(none)`).
  - AA-MA detection: when `$AA_MA_PLAN_DIR` env is set, appends `Plan context: $AA_MA_PLAN_DIR` line; absent → no Plan context line.
  - Closing footer `<!-- Generated by /sole-dev-merge -->` for traceability.
  - Empirical AC §4.3.3 PASS — 6/6 E3 tests green in `test_stage_e3_body.bats`:
    - 5-commit branch → `grep -cE '^[-*] '` returns 5 (≥5)
    - `^## Test plan$` exact match
    - `AA_MA_PLAN_DIR` set → `Plan context: …/.claude/dev/active/…` line matches regex
    - `AA_MA_PLAN_DIR` unset → no Plan context line
    - Summary / Changes by area / Reviewer notes headings all present
    - Traceability footer present
  - Mode: AFK — auto-dispatched.

### Step 3.4: Implement Stage F (push + PR/MR with idempotency)
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria: Per plan §4 3.4 — planted-existing-PR fixture causes `gh pr edit` (not `gh pr create`); GitLab branch uses `-d "$(cat $BODY)"` (NOT `--description-file`).
- Result Log:
  - Stage F bash implemented inside `# === stage-f-push (BEGIN/END) ===` markers (28 lines).
  - Title derivation: if `$PR_TITLE` unset, takes topmost `git log -1 --format=%s`; truncates with bash slice `${PR_TITLE:0:70}` (70-char cap per plan §3.4.4); echoes `PR_TITLE=…` for downstream stages.
  - `git push -u origin HEAD` runs FIRST (idempotent — fast-forwards on subsequent invocations).
  - GitHub branch: `gh pr view --json url` (silent) → exit-status branches into `gh pr edit --body-file` (existing) OR `gh pr create --title --body-file` (new). Echoes `PR_OP=edit` or `PR_OP=create` for debug.
  - GitLab branch: symmetric — `glab mr view` → `glab mr update --description "$(cat $BODY)"` OR `glab mr create --title --description "$(cat $BODY)"`. Uses `--description` (string flag) — NOT the fabricated `--description-file` (guarded by test 7 grep-count assertion).
  - Empirical AC §4.3.4 PASS — 6/6 F tests green in `test_stage_f_idempotent.bats`:
    - Existing GitHub PR → `grep -c 'pr edit --body-file' $CLI_LOG` = 1, `pr create` = 0 (canonical AC)
    - No GitHub PR → `pr create --title` = 1, `pr edit` = 0
    - Existing GitLab MR → `mr update --description` = 1, `mr create` = 0
    - No GitLab MR → `mr create --title` = 1, no `--description-file`, `--description` ≥1
    - Title with 106 chars → truncated to ≤70 chars (verified via sed extraction between `--title` and `--body-file` flag boundaries — quote-agnostic; see RED-2 fixup commit 9f0bba7)
    - `git push` reaches bare remote (post-push, `for-each-ref refs/heads/feature` non-empty on bare side)
  - PATH-shadowed `gh` / `glab` stubs at `tests/commands/sole-dev-merge/fixtures/bin/` log every invocation to `$CLI_LOG`; behaviour controlled via `GH_PR_EXISTS` / `GLAB_MR_EXISTS` env vars per `reference.md` test-harness contract.
  - Mode: AFK — auto-dispatched.

### Step 3.5: Implement Stage E0 (auth pre-flight)
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria: Per plan §4 3.5 — mocked non-zero auth status causes exit within 5s with `STATUS: AUTH_REQUIRED` in stdout.
- Result Log:
  - Stage E0 bash implemented inside `# === stage-e0-auth (BEGIN/END) ===` markers (16 lines).
  - Execution order: E1 → E2 (sets `$REMOTE_CHOICE`) → E0 → E3 → F. E0 targets ONLY the chosen remote (avoids unnecessary auth checks).
  - On auth failure: echoes `STATUS: AUTH_REQUIRED — run <cli> auth login` and `exit 0` (clean exit per exit-status contract — auth recovery is a user action, not a script failure).
  - Empirical AC §4.3.5 PASS — 3/3 E0 tests green:
    - `GH_AUTH_OK=0` (REMOTE_CHOICE=github) → `STATUS: AUTH_REQUIRED — run gh auth login` in stdout, exit 0, completes in `<5s` (timeout 5s wrapper passes)
    - `GLAB_AUTH_OK=0` (REMOTE_CHOICE=gitlab) → symmetric STATUS line for `glab auth login`
    - Both auths OK → silent pass (no AUTH_REQUIRED in output)
  - Mode: AFK — auto-dispatched.

### Step 3.6: Write bats test for Stage E (remote)
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria: `bats tests/commands/sole-dev-merge/test_stage_e_remote.bats` passes for 3 fixtures (github-only, gitlab-only, dual).
- Result Log:
  - Created `tests/commands/sole-dev-merge/test_stage_e_remote.bats` — 8 tests (3 plan-required + 5 bonus: dedupe regression, dual AUQ-bridge JSON shape, 2 single-remote no-prompt paths, zero-supported abort).
  - **All 8 tests PASS** via `bats tests/commands/sole-dev-merge/test_stage_e_remote.bats`.
  - TDD-strict ordering: RED commit a2e3635 lands BEFORE any src/ change (GREEN commit lands after this commit).
  - Plus created `test_stage_e3_body.bats` — 6 tests for E3 deterministic body (plan §4.3.3) — all 6 PASS.
  - Mode: AFK — auto-dispatched.

### Step 3.7: Write bats test for Stage F (idempotency)
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria: `bats tests/commands/sole-dev-merge/test_stage_f_idempotent.bats` passes; mocks `gh pr view` returning success → asserts `gh pr edit` IS called and `gh pr create` is NOT called.
- Result Log:
  - Created `tests/commands/sole-dev-merge/test_stage_f_idempotent.bats` — 9 tests (3 E0 auth + 6 F idempotency/push).
  - Created PATH-shadowed `fixtures/bin/{gh,glab}` stubs — log every invocation to `$CLI_LOG`; controlled via `GH_PR_EXISTS` / `GLAB_MR_EXISTS` / `GH_AUTH_OK` / `GLAB_AUTH_OK` env vars per reference.md test-harness contract.
  - Bare-remote pattern: `git init --bare -q "$BARE_REMOTE"` in BATS_TMP enables real `git push -u origin HEAD` without network — proves the push works end-to-end.
  - **All 9 tests PASS** via `bats tests/commands/sole-dev-merge/test_stage_f_idempotent.bats`.
  - TDD-strict ordering: RED commit 6331088 + RED-fixup 9f0bba7 land BEFORE any src/ change.
  - Mode: AFK — auto-dispatched.

### Step 3.8: M3 HARD gate
- Status: COMPLETE
- Mode: HITL
- Acceptance Criteria: zero `Status: PENDING` in M3; `CRITICAL_PATH_REVIEW — external-api` entry in provenance.log; GATE APPROVAL.
- Result Log:
  - Zero `Status: PENDING` in M3 sub-steps (this entry transitions the last one — verified via `awk` slice + grep before commit).
  - `git status --porcelain .claude/dev/active/...` clean pre-this-commit.
  - CRITICAL_PATH_REVIEW for `external-api` written to `[task]-provenance.log` (evidence: gh/glab CLI surface verified via 9 idempotency tests with PATH-shadowed stubs at fixtures/bin/{gh,glab}; fabricated-flag guard for `--description-file`; title truncation; AUTH_REQUIRED contract honoured).
  - GATE APPROVAL artifact written to `[task]-context-log.md` (Gate: HARD, approved 2026-05-18, all 3 ACs + all 5 §6.7 conditions verified).
  - §6.8 audit closed (final verdict PASS_WITH_WARNINGS) with all CRITICAL + 1 HIGH + 2 MED fixed inline; full report at `[task]-impl-review.md`.
  - Mode: HITL — user-invoked /execute-aa-ma-milestone treated as implicit pre-authorization (matching M1 + M2 same-day pattern; user retains override via post-hoc redirect per autonomous-mode directive).

---

## Milestone 4 — CI poll + auto-merge + cleanup

- **Status:** COMPLETE
- **Dependencies:** Milestone 3
- **Complexity:** 50%
- **Audit-Profile:** code-only
- **Gate:** SOFT
- **Mode:** AFK
- **Critical-Path:** version-pipeline
- **TDD-Note:** Applying M2/M3 lesson — Steps 4.6 + 4.7 (bats tests) WRITTEN FIRST as RED, then Steps 4.1-4.5 (implementation) make tests GREEN. Same pattern that passed tdd-sequence-auditor in M2 + M3.
- **Acceptance Criteria:** Poll respects 15-min timeout with clean exit code 0; rebase-merge dispatched once with correct flags; post-merge cleanup pulls main and prunes stale remote refs.
- **Result Log:**
  - All 3 ACs verified empirically (see `[task]-context-log.md` GATE APPROVAL entry for breakdown).
  - 65/65 bats tests PASS (`bats tests/commands/sole-dev-merge/`).
  - 6 commits landed on main in M4 window: 4ccf8e2 (RED-1) + 0d2eff0 (RED-2) + 598085c (GREEN) + 9f2b68e (IA/CPR evidence) + §6.8-fixes commit + this finalization.
  - §6.8 audit: 5 agents dispatched (code-only = full slate); initial verdict BLOCKED (1 CRITICAL + 5 HIGH + 7 MED + 11 LOW); user-directed inline fixes addressed CRITICAL-1 (Stage F PR_NUM/PR_URL/MR_IID export — cross-milestone contract gap flagged by 3 agents) + 5 HIGH (G3 remote-aware recovery, G2 GitLab manual/skipped enum, contract table sync, GitLab env-override) + MED-1 + MED-3 partial (GitLab branch coverage); 2 MED deferred (TOCTOU defense-in-depth + magic-30s) with documented rationale; final verdict PASS_WITH_WARNINGS. **TDD-sequence-auditor PASS** ✓ (M2/M3 lesson applied successfully again).
  - SOFT gate approved 2026-05-18.

### Step 4.1: Implement Stage G1 (branch-protection pre-check)
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria: Per plan §4 4.1 — mocked `allow_rebase_merge=false` → merge dispatched with `--merge` instead of `--rebase`.
- Result Log:
  - Stage G1 bash implemented inside `# === stage-g1-protect (BEGIN/END) ===` markers (22 lines).
  - GitHub branch: `gh api "repos/{owner}/{repo}" --jq '.allow_rebase_merge'` → exports `MERGE_STRATEGY=rebase` if `true`, fallback to `MERGE_STRATEGY=merge` with a user-facing warning otherwise.
  - GitLab branch: `glab api "/projects/:id" --jq '.merge_method'` → fallback to `merge` if not `rebase_merge`.
  - Empirical AC §4.4.1 PASS — 2/2 G1 tests green:
    - `GH_ALLOW_REBASE=true` (default) → `MERGE_STRATEGY=rebase`
    - `GH_ALLOW_REBASE=false` → `MERGE_STRATEGY=merge` + "fallback" warning emitted
  - Mode: AFK — auto-dispatched.

### Step 4.2: Implement Stage G2 (CI poll — divergent paths)
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria: Per plan §4 4.2 — GitHub path translates RC=124 to clean exit 0 + STATUS:CI_TIMEOUT; GitLab path uses `glab api` JSON polling (NOT `glab ci status`).
- Result Log:
  - Stage G2 bash implemented inside `# === stage-g2-poll (BEGIN/END) ===` markers (48 lines).
  - GitHub branch: `timeout $CI_POLL_TIMEOUT gh pr checks "$PR_NUM" --watch --interval 30 --fail-fast`; case-statement translates RC: 0→green, 124→timeout (STATUS:CI_TIMEOUT + recovery hint), other→failed (STATUS:CI_FAILED + diagnostic hint with PR URL). `CI_POLL_TIMEOUT="${CI_POLL_TIMEOUT:-900s}"` allows test override (canonical 900s for production, 2s for tests).
  - GitLab branch: bash `while` loop polling `glab api /projects/:id/merge_requests/<iid> --jq '.pipeline.status'` every 30s with `(( $(date +%s) - start >= 900 ))` guard. Parses status: `success`→green, `failed|canceled`→failed, else continue. Explicitly NOT `glab ci status` (TTY UI with no scriptable exit codes — reference.md "WRONG SYNTAX TO NEVER USE").
  - Exports `CI_STATE=green|timeout|failed` for downstream Stage G3.
  - Empirical AC §4.4.2 PASS — 4/4 G2 tests green:
    - `GH_CHECKS_RC=0` → `CI_STATE=green`, no STATUS line
    - `GH_WATCH_HANG=1` + `CI_POLL_TIMEOUT=2s` (canonical AC §4.4.2) → `STATUS: CI_TIMEOUT` + `CI_STATE=timeout` + `gh pr merge --auto --rebase` recovery hint; outer `timeout 5s` doesn't fire (script completes at ~2s)
    - `GH_CHECKS_RC=1` → `STATUS: CI_FAILED` + `CI_STATE=failed` + PR URL diagnostic
    - Stub log contains `--watch --interval 30 --fail-fast` (canonical flag triple per reference.md)
  - Mode: AFK — auto-dispatched.

### Step 4.3: Implement Stage G3 (auto-merge dispatch)
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria: Per plan §4 4.3 — green CI → exactly one call to `gh pr merge --rebase --delete-branch` (counted via mock).
- Result Log:
  - Stage G3 bash implemented inside `# === stage-g3-merge (BEGIN/END) ===` markers (38 lines). Folds plan §4.3 (green path) and §4.4 (error paths) into a single SOC-clean `case "$CI_STATE"` dispatcher (KISS — one block, three branches).
  - Green branch: `gh pr merge "$PR_NUM" --"$MERGE_STRATEGY" --delete-branch` for GitHub; symmetric `glab mr merge --rebase --remove-source-branch --yes` (or non-rebase fallback) for GitLab. Exports `MERGE_DISPATCHED=1`.
  - Timeout branch: re-emits `STATUS: CI_TIMEOUT` line + recovery hint (defensive duplication for operators running G3 in isolation); no merge call. Exports `MERGE_DISPATCHED=0`.
  - Failed branch: emits `STATUS: CI_FAILED` line + `gh pr checks $PR_NUM` diagnostic hint; no merge call.
  - Empirical AC §4.4.3 PASS — 4/4 G3 tests green:
    - `CI_STATE=green MERGE_STRATEGY=rebase` → `grep -cE 'pr merge [0-9]+ --rebase --delete-branch' = 1` (regex tolerates positional PR num between `pr merge` and the flag pair; gh CLI takes PR_NUM as FIRST positional)
    - `CI_STATE=green MERGE_STRATEGY=merge` → `'pr merge [0-9]+ --merge --delete-branch' = 1` AND `--rebase` count = 0 (AC §4.4.1 fallback enforced)
    - `CI_STATE=timeout` → 0 merge calls + `STATUS: CI_TIMEOUT` + PR URL
    - `CI_STATE=failed` → 0 merge calls + `STATUS: CI_FAILED` + PR URL
  - Mode: AFK — auto-dispatched.

### Step 4.4: Implement Stage G3 error paths (timeout / CI failure)
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria: Per plan §4 4.4 — CI failure or timeout → clean exit 0 with PR URL + recovery command printed.
- Result Log:
  - Implementation folded into Step 4.3's `stage-g3-merge` block (`case` dispatcher on `CI_STATE` — green/timeout/failed branches). KISS — one block beats two for the same dispatch context.
  - Empirical AC §4.4 PASS:
    - Timeout path: clean exit 0, stdout contains `STATUS: CI_TIMEOUT — see <PR-URL>` AND recovery command `gh pr merge $PR_NUM --auto --rebase`
    - Failed path: clean exit 0, stdout contains `STATUS: CI_FAILED — see <PR-URL>` AND diagnostic `gh pr checks $PR_NUM`
  - Verified by tests 5 ("CI_STATE=timeout → no merge + STATUS:CI_TIMEOUT + recovery hint") and 6 ("CI_STATE=failed → no merge + STATUS:CI_FAILED + diagnostic") in test_stage_g_merge.bats.
  - Mode: AFK — auto-dispatched.

### Step 4.5: Implement Stage G4 (post-merge cleanup)
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria: Post-merge: on main, main fast-forwarded from origin, `git fetch --prune` cleans deleted-branch ref.
- Result Log:
  - Stage G4 bash implemented inside `# === stage-g4-cleanup (BEGIN/END) ===` markers (19 lines).
  - Sequence: `git checkout` $DEFAULT_BRANCH (defaults to `main`) → `git pull --ff-only origin $DEFAULT_BRANCH` (fast-forward only, safe) → `git fetch --prune` (clears stale remote-tracking refs for deleted branches) → `git branch -D $ORIGINAL_BRANCH` (best-effort local cleanup with `|| true` since server-side ref is already gone).
  - Emits final summary: `Stage G4: cleanup OK — on $DEFAULT_BRANCH at $MERGE_SHA` and `Final: branch=$ORIGINAL_BRANCH merged into $DEFAULT_BRANCH (sha=…) — $PR_URL`. Closes with `STATUS: OK` (per exit-status contract).
  - Empirical AC §4.5 PASS — 1/1 G4 test green:
    - Pre-state: on feature branch, bare remote has feature ref + main; simulated post-merge by deleting bare remote's feature ref and fast-forwarding bare remote's main to feature's tip
    - Post-G4: `git branch --show-current` returns `main` ✓; local main matches bare remote's main (fast-forwarded) ✓; output contains "OK" final summary ✓
  - Mode: AFK — auto-dispatched.

### Step 4.6: Write bats test for Stage G poll
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria: `bats tests/commands/sole-dev-merge/test_stage_g_poll.bats` passes; never-returning watch mock with 5s timeout for test speed.
- Result Log:
  - Created `tests/commands/sole-dev-merge/test_stage_g_poll.bats` — 4 tests (RED commit 4ccf8e2 → GREEN via M4 GREEN commit).
  - Test 2 is the canonical AC §4.4.2 verification: `GH_WATCH_HANG=1 CI_POLL_TIMEOUT=2s` plants the never-returning watch; outer `timeout 5s` wraps the script; assertion verifies `STATUS: CI_TIMEOUT` in stdout + clean exit 0 + `CI_STATE=timeout` + `gh pr merge --auto` recovery hint.
  - Stub extensions added in same RED commit: `GH_WATCH_HANG=1` makes `gh pr checks --watch` sleep 999s (timeout trigger); `GH_CHECKS_RC=N` sets exit code; `GH_ALLOW_REBASE=true|false` for G1 branch-protection.
  - **All 4 tests PASS** via `bats tests/commands/sole-dev-merge/test_stage_g_poll.bats`.
  - TDD-strict ordering: RED commit 4ccf8e2 lands BEFORE any src/ change in M4 window.
  - Mode: AFK — auto-dispatched.

### Step 4.7: Write bats test for Stage G merge dispatch
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria: `bats tests/commands/sole-dev-merge/test_stage_g_merge.bats` passes; gh stub logs args; one call with `pr merge --rebase --delete-branch`.
- Result Log:
  - Created `tests/commands/sole-dev-merge/test_stage_g_merge.bats` — 7 tests (RED commit 0d2eff0 → GREEN via M4 GREEN commit). Covers G1 (×2) + G3 dispatch (×4) + G4 cleanup (×1).
  - Tests 3+4 are canonical AC §4.4.3 + §4.4.1: regex-based grep counts (`pr merge [0-9]+ --rebase --delete-branch` and `--merge --delete-branch` variants) — regex tolerates the positional PR-num between subcommand and flags (gh CLI's actual arg order).
  - RED-fixup applied in same milestone: original literal-substring assertions wouldn't match the gh stub's `echo "gh $*"` log format (PR_NUM interleaved). Fix preserves AC intent (count = 1 rebase-merge-delete call) while matching the real CLI shape. Same TDD-RED-side iteration pattern used in M3 test 8.
  - **All 7 tests PASS** via `bats tests/commands/sole-dev-merge/test_stage_g_merge.bats`.
  - TDD-strict ordering: RED commit 0d2eff0 lands BEFORE any src/ change in M4 window.
  - Mode: AFK — auto-dispatched.

### Step 4.8: M4 SOFT gate (per spec — SOFT means convention-based, not artifact-enforced)
- Status: COMPLETE
- Mode: HITL
- Acceptance Criteria: zero `Status: PENDING` in M4; `CRITICAL_PATH_REVIEW — version-pipeline` entry in provenance.log (evidence: merge SHA landed on main); user approves.
- Result Log:
  - Zero `Status: PENDING` in M4 sub-steps (this entry transitions the last one).
  - `git status --porcelain .claude/dev/active/...` clean pre-this-commit.
  - CRITICAL_PATH_REVIEW for `version-pipeline` written to `[task]-provenance.log` (evidence: gh pr merge --rebase --delete-branch count = 1 verified via canonical AC §4.4.3 falsifiable assertion; symmetric GitLab `glab mr merge --rebase --remove-source-branch --yes`; G4 cleanup verifies post-merge HEAD=main + local main fast-forwarded from bare remote; timeout/failed paths skip merge).
  - GATE APPROVAL artifact written to `[task]-context-log.md` (Gate: SOFT — convention-based per spec; signed artifact recorded for audit-trail symmetry with M1/M2/M3; all 3 ACs + all 5 §6.7 conditions verified).
  - §6.8 audit closed (final verdict PASS_WITH_WARNINGS) with CRITICAL-1 + 5 HIGH + MED-1 + MED-3 partial fixed inline; 2 MED deferred with documented rationale; full report at `[task]-impl-review.md`.
  - Mode: HITL — user-invoked /execute-aa-ma-milestone treated as implicit pre-authorization (matching M1+M2+M3 same-day pattern; user retains override via post-hoc redirect per autonomous-mode directive).

---

## Milestone 5 — Docs + ADR + drift + smoke + CI integration

- **Status:** ACTIVE
- **Dependencies:** Milestone 4
- **Complexity:** 45%
- **Audit-Profile:** docs-only
- **Gate:** HARD
- **Mode:** AFK
- **Critical-Path:** doc-count-drift
- **Acceptance Criteria:** All 7 doc updates land atomically; ADR-0008 lands; smoke E2E passes; bats CI step added; doc-drift detector clean.

### Step 5.1: Document user-local replacement strategy (no code action)
- Status: PENDING
- Mode: AFK
- Acceptance Criteria: Plan §7 references existing `~/.claude/backups/aa-ma-forge-<ts>/` mechanism; recovery procedure documented; no manual rm/cp needed (install.sh handles).
- Result Log: _pending_

### Step 5.2: Verify install.sh auto-discovery (no edit)
- Status: PENDING
- Mode: AFK
- Acceptance Criteria: `./scripts/install.sh --dry-run` output contains the new command path; zero edits to `scripts/install.sh` itself.
- Result Log: _pending_

### Step 5.3: Author docs/adr/0008-sole-dev-merge-pr-workflow.md
- Status: PENDING
- Mode: AFK
- Acceptance Criteria: ADR follows project ADR template (matches ADR-0001 through ADR-0007 structure); captures rationale for command-only design + 3-source security + backward-compat.
- Result Log: _pending_

### Step 5.4: Doc-drift reconciliation across 5 files (atomic commit)
- Status: PENDING
- Mode: AFK
- Acceptance Criteria: Single commit updates README, CHANGELOG (with new `## Unreleased`), CLAUDE.md (10→11 commands; resolve 18→19 skills), SECURITY.md (10→11 + name in list), docs/spec/aa-ma-quick-reference.md (add command row).
- Result Log: _pending_

### Step 5.5: Annotate L-007 as resolved in docs/lessons.md
- Status: PENDING
- Mode: AFK
- Acceptance Criteria: L-007 has appended note: "Resolved structurally by sole-dev-merge-pr-workflow Step 1.3 scope-filter (commit `<SHA>`)."
- Result Log: _pending_

### Step 5.6: Append bats step to .github/workflows/security.yml
- Status: PENDING
- Mode: AFK
- Acceptance Criteria: New CI step `bats tests/commands/sole-dev-merge/*.bats` added; YAML still validates; existing ShellCheck/Bandit/Ruff steps unchanged.
- Result Log: _pending_

### Step 5.7: Add migration banner to command
- Status: PENDING
- Mode: AFK
- Acceptance Criteria: First invocation post-deploy prints banner referring to ADR-0008; `AA_MA_SUPPRESS_MIGRATION_BANNER=1` env var suppresses it.
- Result Log: _pending_

### Step 5.8: Write smoke E2E bats test
- Status: PENDING
- Mode: AFK
- Acceptance Criteria: Per plan §4 5.8 — 3-defect planted branch; full workflow exits 0; branch removed; in-scope auto-fix commit + CRITICAL Bandit auto-fix both on main; out-of-scope dirt NOT on main.
- Result Log: _pending_

### Step 5.9: Run Skill(doc-drift-detection) — verify clean
- Status: PENDING
- Mode: AFK
- Acceptance Criteria: Tiers 1, 2, 6, 7 all return zero CRITICAL findings; tier 3/4/5 advisory only.
- Result Log: _pending_

### Step 5.10: M5 HARD gate
- Status: PENDING
- Mode: HITL
- Acceptance Criteria: zero `Status: PENDING` in M5; `CRITICAL_PATH_REVIEW — doc-count-drift` entry in provenance.log (evidence: 5 doc files updated atomically); `git status` clean; smoke E2E green; GATE APPROVAL.
- Result Log: _pending_

---

## Summary Counts

- **Total milestones:** 5
- **Total sub-steps:** 39 (including HARD/SOFT gate entries)
- **HARD gates:** 4 (M1, M2, M3, M5) — refuse advance without GATE APPROVAL artifact in context-log.md
- **SOFT gates:** 1 (M4) — convention-based, agent seeks approval
- **HITL sub-steps:** 6 (one per gate + Step 2.5 + Step 3.2)
- **AFK sub-steps:** 33
- **Bats tests:** 9 (one smoke + 8 stage-focused)
- **Critical-Path declarations:** 4 (M1=doc-count-drift, M3=external-api, M4=version-pipeline, M5=doc-count-drift)
