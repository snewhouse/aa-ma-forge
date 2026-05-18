# sole-dev-merge-pr-workflow Tasks (HTP)

## Milestone 1 — Pre-flight + scope-aware CI checks

- **Status:** ACTIVE
- **Dependencies:** None
- **Complexity:** 45%
- **Audit-Profile:** code-only
- **Gate:** HARD
- **Mode:** AFK
- **Critical-Path:** doc-count-drift
- **Acceptance Criteria:** Bats #1 (scope) + #2 (preflight) pass; in-scope auto-fix commit lands with correct signature; out-of-scope drift reverted via `git checkout --`.

### Step 1.1: Create command skeleton with frontmatter
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria: `claude-code/commands/sole-dev-merge.md` exists; frontmatter contains `description: PR/MR-based merge workflow with scope-aware CI checks, review, security pass, and auto-merge`; body has section placeholders A–G.
- Result Log: PASS. File created (118 lines). Frontmatter `description:` verified by `grep -Fxq` (exact-match). All 7 stage headings (A–G) present (verified by `grep -E '^### Stage X —'`). Commands directory inventory: 10 → 11 (matches plan delta).

### Step 1.2: Implement Stage A (pre-flight checks)
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria: All 4 abort conditions (on-main, dirty-tree, no-remote, no-commits-ahead) produce distinct ABORT messages matching exact strings in plan §4.1.2.
- Result Log: PASS. `stage_a_preflight()` added inline (52 lines). All 5 cases verified in isolated tmp git repos: on-main rc=1 + exact plan-§4.1.2 string match (`ABORT: Cannot run /sole-dev-merge from main branch`); dirty-tree rc=2 + `ABORT: Working tree is dirty`; no-remote rc=3 + `ABORT: No remote configured`; no-commits-ahead rc=4 + `ABORT: Branch has no commits ahead of main`; happy-path rc=0 + `Pre-flight OK`. ShellCheck of extracted bash: 0 advisories (after SC2034 disable for cross-stage `ORIGINAL_BRANCH`). Extraction helper `tests/commands/sole-dev-merge/fixtures/load_stages.bash` created (reusable by all bats tests).

### Step 1.3: Implement Stage B (scope-aware CI checks)
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria: Per plan §4 1.3 — out-of-scope file `tests/codemem/foo.py` shows zero `git diff` after Stage B AND in-scope file passes `ruff check`. L-007 guard active.
- Result Log: PASS. `stage_b_scope()` added inline (~55 lines). Empirical test (isolated tmp git repo): planted in-scope `src/scope_test.py` with unused-imports + bad-spacing lint errors; planted out-of-scope dirty `tests/codemem/foo.py`. Post Stage B: `git diff tests/codemem/foo.py` = 0 bytes (L-007 guard reverted), `ruff check src/scope_test.py` exits 0 (in-scope fix applied). Stage B exit code 0. Caught real bug: pytest exit-5 (no tests collected) was being treated as failure → fixed by explicit `pytest_rc -ne 5` check. ShellCheck of 109-line extracted bash: 0 advisories. Stage A regression: 5/5 pass.

### Step 1.4: Auto-commit in-scope fixes (if any)
- Status: COMPLETE
- Mode: AFK
- Acceptance Criteria: Per plan §4 1.4 — if Stage B mutated files, `git log -1 --format=%s` returns `chore(scope): pre-PR auto-fixes` AND last 3 lines of body match `\[AA-MA Plan\]|\[ad-hoc\]`.
- Result Log: PASS. `stage_b_autocommit()` added (~30 lines). Three scenarios verified empirically: (1) AD-HOC (no plan dir) → subject = `chore(scope): pre-PR auto-fixes`, tail-3 contains `[ad-hoc]`; (2) PLAN-ACTIVE (`.claude/dev/active/sole-dev-merge-pr-workflow/` present) → subject correct, tail-3 contains `[AA-MA Plan] sole-dev-merge-pr-workflow .claude/dev/active/sole-dev-merge-pr-workflow`; (3) CLEAN TREE → HEAD unchanged, function reports "no in-scope auto-fixes to commit". Stage A regression: 5/5 pass. ShellCheck (141 lines): 0 advisories. Field-discovery: parent session's commit-signature hook blocks tmp-repo commits unless cmd includes `[ad-hoc]` standalone line — bats fixtures will need a bypass-marker heredoc.

### Step 1.5: Write bats test for Stage B (scope)
- Status: ACTIVE
- Mode: AFK
- Acceptance Criteria: `bats tests/commands/sole-dev-merge/test_stage_b_scope.bats` passes; test plants out-of-scope + in-scope diffs and asserts L-007 reversion.
- Result Log: _pending_

### Step 1.6: Write bats test for Stage A (preflight)
- Status: PENDING
- Mode: AFK
- Acceptance Criteria: `bats tests/commands/sole-dev-merge/test_stage_a_preflight.bats` passes; 4 cases exercise each abort branch.
- Result Log: _pending_

### Step 1.7: M1 HARD gate (sub-step closure check)
- Status: PENDING
- Mode: HITL
- Acceptance Criteria: zero `Status: PENDING` in M1 sub-steps; `git status` clean for AA-MA files; CRITICAL_PATH_REVIEW for `doc-count-drift` entry in provenance.log; GATE APPROVAL recorded in context-log.md.
- Result Log: _pending_

---

## Milestone 2 — Review + 3-source security pass

- **Status:** PENDING
- **Dependencies:** Milestone 1
- **Complexity:** 65%
- **Audit-Profile:** full
- **Gate:** HARD
- **Mode:** HITL (Step 2.5 prompts on HIGH/MEDIUM findings)
- **Critical-Path:** _(none — but per Theme 5 SOFT discipline)_
- **Acceptance Criteria:** 4 sources dispatched in parallel; severity contract honoured OR safe-default fallback applied; planted Bandit B602 auto-fix verified in bats #6.

### Step 2.1: Implement Stage C1 (code-reviewer agent dispatch)
- Status: PENDING
- Mode: AFK
- Acceptance Criteria: Agent dispatched with explicit severity contract; output written to `/tmp/sole-dev-merge-review-<slug>.md`; parser regex returns matches OR safe-default-all-HIGH fallback triggers.
- Result Log: _pending_

### Step 2.2: Implement Stage C2 (security-auditor agent dispatch)
- Status: PENDING
- Mode: AFK
- Acceptance Criteria: Parallel to C1, same contract, output to `/tmp/sole-dev-merge-security-<slug>.md`. Agent path verified at `~/.claude/agents/security-auditor.md`.
- Result Log: _pending_

### Step 2.3: Implement Stage C3 (Bandit on changed Python)
- Status: PENDING
- Mode: AFK
- Acceptance Criteria: `bandit -f json -r $CHANGED_PY` produces parseable JSON; severity mapped per reference.md table; appended to findings buffer.
- Result Log: _pending_

### Step 2.4: Implement Stage C4 (ShellCheck on changed shell)
- Status: PENDING
- Mode: AFK
- Acceptance Criteria: `shellcheck -f json $CHANGED_SH` produces parseable JSON; severity mapped per reference.md table; appended to findings buffer.
- Result Log: _pending_

### Step 2.5: Implement Stage D (findings triage)
- Status: PENDING
- Mode: HITL
- Acceptance Criteria: Per plan §4 2.5 — Bandit B602 fixture auto-fix commit exists; post-fix `bandit -t B602` returns zero `Issue:` lines; HIGH/MEDIUM panel logged correct count of AUQ_DISPATCH events.
- Result Log: _pending_

### Step 2.6: Write bats test for Stage D (triage with planted B602)
- Status: PENDING
- Mode: AFK
- Acceptance Criteria: `bats tests/commands/sole-dev-merge/test_stage_d_triage.bats` passes; planted B602 in changed file; post-Stage-D verification per §4 2.5.
- Result Log: _pending_

### Step 2.7: Write bats test for Stage C (agent dispatch mocking)
- Status: PENDING
- Mode: AFK
- Acceptance Criteria: `bats tests/commands/sole-dev-merge/test_stage_c_dispatch.bats` passes; uses `MOCK_AGENT_DISPATCH=1` env var to stub agent output.
- Result Log: _pending_

### Step 2.8: M2 HARD gate
- Status: PENDING
- Mode: HITL
- Acceptance Criteria: zero `Status: PENDING` in M2; safe-default fallback documented in context-log if invoked; GATE APPROVAL.
- Result Log: _pending_

---

## Milestone 3 — PR/MR creation with idempotency

- **Status:** PENDING
- **Dependencies:** Milestone 2
- **Complexity:** 60%
- **Audit-Profile:** full
- **Gate:** HARD
- **Mode:** HITL (Step 3.2 prompts when dual remotes exist)
- **Critical-Path:** external-api
- **Acceptance Criteria:** Three-fixture remote-detect test passes; PR idempotency verified by mock; AI body generation produces deterministic structure when AA-MA plan active.

### Step 3.1: Implement Stage E1 (remote detection)
- Status: PENDING
- Mode: AFK
- Acceptance Criteria: Per plan §4 3.1 — github-only fixture → `n_github=1, n_gitlab=0`; dual fixture → `n_github=1, n_gitlab=1`.
- Result Log: _pending_

### Step 3.2: Implement Stage E2 (remote choice + AskUserQuestion default)
- Status: PENDING
- Mode: HITL
- Acceptance Criteria: Per plan §4 3.2 — dual fixture invokes AskUserQuestion with GitLab as default option.
- Result Log: _pending_

### Step 3.3: Implement Stage E3 (AI body generation via Haiku)
- Status: PENDING
- Mode: AFK
- Acceptance Criteria: Per plan §4 3.3 — body has ≥ N_COMMITS bullets, `## Test plan` heading, AA-MA plan-context footer when active.
- Result Log: _pending_

### Step 3.4: Implement Stage F (push + PR/MR with idempotency)
- Status: PENDING
- Mode: AFK
- Acceptance Criteria: Per plan §4 3.4 — planted-existing-PR fixture causes `gh pr edit` (not `gh pr create`); GitLab branch uses `-d "$(cat $BODY)"` (NOT `--description-file`).
- Result Log: _pending_

### Step 3.5: Implement Stage E0 (auth pre-flight)
- Status: PENDING
- Mode: AFK
- Acceptance Criteria: Per plan §4 3.5 — mocked non-zero auth status causes exit within 5s with `STATUS: AUTH_REQUIRED` in stdout.
- Result Log: _pending_

### Step 3.6: Write bats test for Stage E (remote)
- Status: PENDING
- Mode: AFK
- Acceptance Criteria: `bats tests/commands/sole-dev-merge/test_stage_e_remote.bats` passes for 3 fixtures (github-only, gitlab-only, dual).
- Result Log: _pending_

### Step 3.7: Write bats test for Stage F (idempotency)
- Status: PENDING
- Mode: AFK
- Acceptance Criteria: `bats tests/commands/sole-dev-merge/test_stage_f_idempotent.bats` passes; mocks `gh pr view` returning success → asserts `gh pr edit` IS called and `gh pr create` is NOT called.
- Result Log: _pending_

### Step 3.8: M3 HARD gate
- Status: PENDING
- Mode: HITL
- Acceptance Criteria: zero `Status: PENDING` in M3; `CRITICAL_PATH_REVIEW — external-api` entry in provenance.log; GATE APPROVAL.
- Result Log: _pending_

---

## Milestone 4 — CI poll + auto-merge + cleanup

- **Status:** PENDING
- **Dependencies:** Milestone 3
- **Complexity:** 50%
- **Audit-Profile:** code-only
- **Gate:** SOFT
- **Mode:** AFK
- **Critical-Path:** version-pipeline
- **Acceptance Criteria:** Poll respects 15-min timeout with clean exit code 0; rebase-merge dispatched once with correct flags; post-merge cleanup pulls main and prunes stale remote refs.

### Step 4.1: Implement Stage G1 (branch-protection pre-check)
- Status: PENDING
- Mode: AFK
- Acceptance Criteria: Per plan §4 4.1 — mocked `allow_rebase_merge=false` → merge dispatched with `--merge` instead of `--rebase`.
- Result Log: _pending_

### Step 4.2: Implement Stage G2 (CI poll — divergent paths)
- Status: PENDING
- Mode: AFK
- Acceptance Criteria: Per plan §4 4.2 — GitHub path translates RC=124 to clean exit 0 + STATUS:CI_TIMEOUT; GitLab path uses `glab api` JSON polling (NOT `glab ci status`).
- Result Log: _pending_

### Step 4.3: Implement Stage G3 (auto-merge dispatch)
- Status: PENDING
- Mode: AFK
- Acceptance Criteria: Per plan §4 4.3 — green CI → exactly one call to `gh pr merge --rebase --delete-branch` (counted via mock).
- Result Log: _pending_

### Step 4.4: Implement Stage G3 error paths (timeout / CI failure)
- Status: PENDING
- Mode: AFK
- Acceptance Criteria: Per plan §4 4.4 — CI failure or timeout → clean exit 0 with PR URL + recovery command printed.
- Result Log: _pending_

### Step 4.5: Implement Stage G4 (post-merge cleanup)
- Status: PENDING
- Mode: AFK
- Acceptance Criteria: Post-merge: on main, main fast-forwarded from origin, `git fetch --prune` cleans deleted-branch ref.
- Result Log: _pending_

### Step 4.6: Write bats test for Stage G poll
- Status: PENDING
- Mode: AFK
- Acceptance Criteria: `bats tests/commands/sole-dev-merge/test_stage_g_poll.bats` passes; never-returning watch mock with 5s timeout for test speed.
- Result Log: _pending_

### Step 4.7: Write bats test for Stage G merge dispatch
- Status: PENDING
- Mode: AFK
- Acceptance Criteria: `bats tests/commands/sole-dev-merge/test_stage_g_merge.bats` passes; gh stub logs args; one call with `pr merge --rebase --delete-branch`.
- Result Log: _pending_

### Step 4.8: M4 SOFT gate (per spec — SOFT means convention-based, not artifact-enforced)
- Status: PENDING
- Mode: HITL
- Acceptance Criteria: zero `Status: PENDING` in M4; `CRITICAL_PATH_REVIEW — version-pipeline` entry in provenance.log (evidence: merge SHA landed on main); user approves.
- Result Log: _pending_

---

## Milestone 5 — Docs + ADR + drift + smoke + CI integration

- **Status:** PENDING
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
