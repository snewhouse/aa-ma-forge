# sole-dev-merge-pr-workflow Context Log

## [2026-05-18] Initial Context

**Feature Request (verbatim from user):**
> we need to update and improve the sole-dev-merge command,skill,workflow to now include pre commit make ci runs (lint,mypy etc and fixes as needed), making an PR and or MR depending on if pushing to gitub or gitlab; proper review and then fixes as need of the code following standard practices; please AskUserQuestion and brainstorm with me; web search as needed; use sub agents as needed

**Key Decisions captured via 5 rounds of AskUserQuestion:**

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Scope relative to existing /sole-dev-merge | **Replace entirely** (single command, always PR/MR) | Cleanest mental model; old fast-merge path retired |
| Location | **aa-ma-forge plugin** at `claude-code/commands/` | Versioned, install.sh-managed, CI-covered |
| Code review approach | **Local AI review BEFORE pushing PR + extra security pass** | Fast feedback, no GitHub API spend |
| Auto-fix aggression | **CRITICAL auto-apply; ask on HIGH/MEDIUM** | Safe default, tight loop |
| Remote detection | **Dual-remote aware; AskUserQuestion when both; default GitLab** | Matches Biorelate convention (gitlab=primary) |
| Pre-PR CI checks | **All 4: format+lint+fix, typecheck, pytest fast, pre-commit** | Catch all classes locally |
| Post-PR-open behaviour | **Poll CI green (30s × 15min) then auto-merge** | End-to-end, sole-dev spirit |
| Merge strategy | **Rebase + ff (linear history)** | Closest to existing /sole-dev-merge ff-only flavour |
| Shape | **Command + thin skill wrapper** (later REVISED → command-only) | Originally requested skill wrapper; verification revealed no precedent for skill/lib pattern; user re-chose command-only |
| PR body | **AI-generated from diff** | Better narrative than commit-bullet dump |
| AA-MA handling | **Preserve [AA-MA Plan] footers + link plan dir in PR body** | Continuity with existing AA-MA workflow |
| CI poll | **30s × 15min, then clean exit** | Background-friendly |
| Security pass (post-revision) | **All three: security-auditor agent + Bandit + ShellCheck** | Belt-and-braces |

**Lessons Scan Findings:**
- **L-007 (CRITICAL relevance):** `/sole-dev-merge` quality-check format pass may modify out-of-scope files. Full lesson read inline at planning time. **The new workflow's M1.3 scope-filter is the structural fix for L-007** — `git diff --name-only main...HEAD` constrains the scope of format/lint to only files the branch actually touched.
- **L-008 (low relevance):** cz bump --files-only chain broken with manual CHANGELOG promote — relates to release-prep, not to merge workflow.
- **L-005 (medium relevance):** CI-scope check — for every new test/check artifact, verify CI actually runs it. Drives M5.6 (append bats step to CI workflow).

**Research:**
- Verified `gh` v2.92.0 + `glab` v1.80.4 CLI surfaces via `--help` inline (no Context7 needed — CLIs aren't libraries)
- Checked existing `glab-gitlab-cli` skill for canonical patterns
- Verified `feature-dev:code-reviewer` and `code-reviewer` agents both exist
- Verified `security-auditor` agent exists; `superpowers:security-review` does NOT exist (caught in verification)
- Verified `Skill(doc-drift-detection)` exists for M5.9

**Adversarial Verification (Phase 4.5):**
- Ran `Skill(plan-verification)` mode=automated
- Wave 1 (4 angles): Ground-truth, Assumptions, Impact, Falsifiability
- Wave 2 (2 angles): Fresh-agent simulation, Specialist domain audit (API + Engineering Standards)
- **v1 Result: FAIL** — 17 CRITICAL + 23 WARNING findings
- 17 CRITICALs categorized into:
  - Factual errors (non-existent skills, fabricated CLI flags) — 6 findings
  - Design gaps (skill/lib pattern undefined, severity scheme mismatch) — 3 findings
  - Standards compliance gaps (Audit-Profile missing, non-canonical Critical-Path) — 3 findings
  - Impact omissions (SECURITY.md drift, phantom install.sh edit) — 2 findings
  - Plan-text gaps (Step 1.1 frontmatter undefined, rollback path broken) — 3 findings

**Revision Decision:**
User selected via AskUserQuestion:
- Pattern: **Command markdown only — helpers as inline bash blocks** (drops skill/lib entirely)
- Security: **All three (security-auditor agent + Bandit + ShellCheck)**

**v2 Plan Generated:** All 17 CRITICALs addressed via spot-check verification. Result: PASS WITH WARNINGS.

**Research Findings (consolidated):**

1. **install.sh auto-discovery:** Lines 257-269 of `scripts/install.sh` already loop over `claude-code/commands/*.md` and `claude-code/skills/*/` — new files picked up automatically. v1 plan's claim that install.sh needs editing was a phantom requirement.

2. **Pre-existing repo drift:** SECURITY.md says "19 skills" but CLAUDE.md says "18 reusable procedures" — actual count via `ls claude-code/skills/` is 19. The plan resolves this discrepancy in M5.4 (atomic doc-drift commit).

3. **CLI contract gotchas captured in reference.md:**
   - `glab mr create --description-file` is fabricated (use `-d "$(cat $BODY)"`)
   - `--remove-source-branch=false` syntactically invalid (boolean flag)
   - `glab ci status` is not script-safe (use `glab api` instead)
   - `gh pr checks --watch` + `timeout 900s` → RC=124 on timeout (must translate)

4. **Severity scheme mismatch handled:** code-reviewer agents emit 2-tier or 3-tier schemes, NOT the plan's 4-tier. Workflow handles by passing explicit prompt contract AND falling back to "all HIGH" classification on parse failure (no silent auto-fix without confirmation).

**Remaining Questions / Open Items:**
- WARNING findings W3, W4, W6 deferred to execution-time refinement
- Bats CI step (M5.6) — will need to ensure `bats-core` is available in the GitHub Actions runner image
- Concurrent invocation (multiple `/sole-dev-merge` runs in parallel) explicitly out of scope; document assumption in command markdown frontmatter

**Marker Log (Phase 0–4.5 traces):**
- Phase 0 INIT — written to `~/.claude/runtime/aa-ma-plan-sole-dev-merge-ci-pr-20260518105415.log`
- Phase 1 DONE (context gathering complete)
- Phase 1.3 SKIPPED (user_passed — explicit AskUserQuestion rounds substituted for grill protocol)
- Phase 1.5 DONE (lessons_loaded=3, git_grep_hits=10)
- Phase 2 DONE (brainstorm via 5 AskUserQuestion rounds, 12+ alternatives weighed)
- Phase 3 DONE (context7_calls=0, web_fetches=0 — local CLI docs sufficient)
- Phase 4 DONE (complexity_score=53%, plan_elements=12/12)
- Phase 4.2 SKIPPED (user_passed on CEO/Eng/Design review)
- Phase 4.5 DONE (verdict=RED initially → revision → PASS WITH WARNINGS)
- Phase 5 — pending (proceeding now)

**Next Action:** Phase 5 artifact creation complete with this file. Phase 5 marker to be written after all 5 AA-MA files exist.

---

## [2026-05-18] Milestone 1 Completion: Pre-flight + scope-aware CI checks

- **Status:** COMPLETE
- **Key outcome:** Implemented Stage A (4-branch pre-flight) + Stage B (scope-aware CI with L-007 GUARD) + Stage B-commit (auto-fix commit) inside `claude-code/commands/sole-dev-merge.md`; added 2 bats test files (10/10 tests PASS) + DRY `extract_stage.sh` helper. Structurally resolves L-007 (whole-tree ruff format drift).
- **Artifacts:**
  - `claude-code/commands/sole-dev-merge.md` (NEW — 311 lines; Stages A/B/B-commit implemented in markers; C–G are placeholders)
  - `tests/commands/sole-dev-merge/test_stage_a_preflight.bats` (NEW — 6 tests)
  - `tests/commands/sole-dev-merge/test_stage_b_scope.bats` (NEW — 4 tests)
  - `tests/commands/sole-dev-merge/fixtures/extract_stage.sh` (NEW — extractor helper)
- **Tests:** 10/10 bats PASS via `bats tests/commands/sole-dev-merge/`
- **Commits:** 5914df4, a7a437b, b6342e0, 38b8b8b, dbad361
- **§6.8 audit verdict:** PASS_WITH_WARNINGS (1 CRITICAL disputed, 14 LOW advisory) — see `[task]-impl-review.md`

## [2026-05-18] GATE APPROVAL: Milestone 1 — Pre-flight + scope-aware CI checks

- **Gate:** HARD
- **Approved by:** Stephen J Newhouse (via /execute-aa-ma-milestone HITL Step 1.7)
- **Criteria verified:** 4/4 acceptance criteria from M1 acceptance:
  1. ✅ Bats #1 (scope) passes — 4/4 tests green incl. canonical L-007 scenario
  2. ✅ Bats #2 (preflight) passes — 6/6 tests green incl. AC §4.1.2 verbatim match
  3. ✅ In-scope auto-fix commit lands with correct signature — empirically verified subject = `chore(scope): pre-PR auto-fixes`; AA-MA footer applied by hook
  4. ✅ Out-of-scope drift reverted via `git checkout --` — empirically verified zero-byte `git diff` on planted `tests/codemem/foo.py` post-Stage-B
- **Engineering Standards HARD gate (§6.7):** all 5 conditions PASS
  1. AA-MA artifacts in sync — `git status --porcelain .claude/dev/active/...` returns 0 dirty files (verified pre-this-commit)
  2. Zero `Status: PENDING` in M1 — Step 1.7 transitions to COMPLETE with this approval
  3. Tests pass — `bats tests/commands/sole-dev-merge/` 10/10 green
  4. Critical-Path evidence — `CRITICAL_PATH_REVIEW — doc-count-drift` entry in provenance.log
  5. Prototype-Required: absent → check skipped
- **§6.8 Post-Impl Adversarial Review:** 5 agents dispatched (code-only profile = full slate); verdict PASS_WITH_WARNINGS post user-dispute on the single tdd-sequence CRITICAL; details in `[task]-impl-review.md`
- **Decision:** APPROVED — proceed to M2

---

## [2026-05-18] Milestone 2 Completion: Review + 3-source security pass

- **Status:** COMPLETE
- **Key outcome:** Implemented Stage C (parallel agent dispatch contract + Bandit + ShellCheck aggregation with severity mapping) + Stage D (B602 auto-fix from Bandit JSON, line-precise + test_id equality; HIGH/MEDIUM HITL via AskUserQuestion; LOW → reviewer notes). Closed 1 CRITICAL + 4 HIGH §6.8 audit findings inline via 3 refactors: (1) severity tables to single source-of-truth, (2) Stage D refactor from agent-text to Bandit JSON, (3) shared aa-ma-footer.sh helper. Also closed M1 production gap (Stage B-commit footer).
- **Artifacts:**
  - `claude-code/commands/sole-dev-merge.md` (MODIFIED — Stage C + Stage D fully implemented; Stage B-commit refactored to use shared footer helper)
  - `claude-code/hooks/lib/aa-ma-footer.sh` (NEW — shared footer-helper)
  - `tests/commands/sole-dev-merge/test_stage_c_dispatch.bats` (NEW — 5 tests)
  - `tests/commands/sole-dev-merge/test_stage_d_triage.bats` (NEW — 4 tests incl. docstring-survival regression)
  - `tests/commands/sole-dev-merge/fixtures/helpers.bash` (NEW — extracted mkcommit, M1 cleanup)
  - `.claude/dev/active/sole-dev-merge-pr-workflow/sole-dev-merge-pr-workflow-reference.md` (MODIFIED — severity tables marked as mirror; canonical-source pointer to command file)
- **Tests:** 19/19 bats PASS (10 M1 + 5 Stage C + 4 Stage D)
- **TDD-sequence-auditor verdict:** PASS ✓ (M1 lesson applied — tests committed before impl in both Stage C and Stage D pairs)
- **§6.8 audit verdict:** PASS_WITH_WARNINGS (CRITICAL + 4 HIGH fixed inline; remaining LOW/MEDIUM noted in impl-review.md)
- **Commits:** f6f8497, 5d7ba98, 5feaf9c, bafa257, 814d57a, 245c662, 5d06a65 (7 commits, TDD-strict order)

## [2026-05-18] GATE APPROVAL: Milestone 2 — Review + 3-source security pass

- **Gate:** HARD
- **Approved by:** Stephen J Newhouse (via /execute-aa-ma-milestone HITL Step 2.8)
- **Criteria verified:** 3/3 acceptance criteria from M2 acceptance:
  1. ✅ 4 sources dispatched in parallel — Stage C documented as parallel Agent dispatch (C1, C2) + parallel-shell C3, C4; bats tests assert the aggregation contract
  2. ✅ Severity contract honoured OR safe-default fallback applied — both paths tested empirically (tests 11, 14)
  3. ✅ Planted Bandit B602 auto-fix verified — test 16 (canonical AC §4.2.5) + test 18 (docstring-survival regression) PASS
- **Engineering Standards HARD gate (§6.7):** all 5 conditions PASS
  1. AA-MA artifacts in sync — finalized in this commit
  2. Zero `Status: PENDING` in M2 — Step 2.8 transitions to COMPLETE with this approval
  3. Tests pass — 19/19 bats green
  4. Critical-Path evidence — M2 has NO Critical-Path declaration (per plan: SOFT discipline only); check skipped (absent-field semantic)
  5. Prototype-Required absent → check skipped
- **§6.8 Post-Impl Adversarial Review:** 5 agents dispatched (full profile); initial verdict BLOCKED (1 CRITICAL + 5 HIGH); user chose "Fix everything inline"; CRITICAL + 4 HIGH refactored inline (3 root-cause fixes in 1 commit + footer helper); final verdict PASS_WITH_WARNINGS. Details in `[task]-impl-review.md`.
- **Decision:** APPROVED — proceed to M3


## [2026-05-18] GATE APPROVAL: Milestone 3 — PR/MR creation with idempotency

- **Gate:** HARD
- **Approved by:** Stephen J Newhouse (via /execute-aa-ma-milestone HITL Step 3.8)
- **Criteria verified:** 3/3 acceptance criteria from M3 acceptance:
  1. ✅ Three-fixture remote-detect test passes — `test_stage_e_remote.bats` 8/8 PASS incl. AC §4.3.1 (github-only, gitlab-only, dual-remote) + fetch/push dedupe regression
  2. ✅ PR idempotency verified by mock — `test_stage_f_idempotent.bats` 9/9 PASS incl. canonical AC §4.3.4 (planted-PR → gh pr edit count=1, gh pr create count=0) + GitLab symmetric path + --description (NOT fabricated --description-file) guard
  3. ✅ AI body generation produces deterministic structure when AA-MA plan active — `test_stage_e3_body.bats` 9/9 PASS incl. AC §4.3.3 (≥5 bullets, `## Test plan` heading, `Plan context: …/.claude/dev/active/…` line) + §6.8 D→E3 integration regression + HIGH-1 control-char-strip regression
- **Engineering Standards HARD gate (§6.7):** all 5 conditions PASS
  1. AA-MA artifacts in sync — `git status --porcelain .claude/dev/active/...` returns 0 dirty files (verified pre-this-commit)
  2. Zero `Status: PENDING` in M3 — Step 3.8 transitions to COMPLETE with this approval
  3. Tests pass — `bats tests/commands/sole-dev-merge/` 45/45 green (42 + 3 new §6.8 regression); `uv run pytest --tb=short -q` 782 passed, 1 skipped, 7 deselected
  4. Impact-analysis evidence — IMPACT_ANALYSIS M3 entry in provenance.log (Risk: LOW; 8 files; no contract changes; 0 external refs)
  5. Critical-Path evidence — CRITICAL_PATH_REVIEW — external-api entry in provenance.log (gh/glab CLI surface; 9 idempotency tests with PATH-shadowed stubs; fabricated-flag guard for `--description-file`; title truncation; AUTH_REQUIRED contract honoured); Prototype-Required absent → check skipped (absent-field semantic)
- **§6.8 Post-Impl Adversarial Review (Audit-Profile: full):** 5 agents dispatched → initial verdict BLOCKED (1 CRITICAL + 3 HIGH + 8 MED + 11 LOW). User-directed inline fixes via override panel addressed CRITICAL-1 (reviewer-notes path mismatch — 3 agents converged on same root cause), HIGH-1 (AA_MA_PLAN_DIR markdown injection — CWE-117), MED-1 (ABORT vs STATUS contract widening), MED-2 (Stage F body-file guard). HIGH-3 (UTF-8 truncation) + 6×MED DEFERRED with documented rationale in impl-review.md. Final verdict: PASS_WITH_WARNINGS. **TDD-sequence-auditor PASS** ✓ (4 RED commits → GREEN, 10m04s delta — M2 lesson applied successfully again).
- **Decision:** APPROVED
- **Commits in M3 window:** a2e3635..HEAD (RED-1, RED-2, RED-3, RED-2 fixup, GREEN, IA/CPR evidence, §6.8 fixes)

## [2026-05-18] GATE APPROVAL: Milestone 4 — CI poll + auto-merge + cleanup

- **Gate:** SOFT (convention-based per spec; signed artifact recorded anyway for audit-trail symmetry with M1/M2/M3)
- **Approved by:** Stephen J Newhouse (via /execute-aa-ma-milestone — autonomous-mode directive)
- **Criteria verified:** 3/3 acceptance criteria from M4 acceptance:
  1. ✅ Poll respects 15-min timeout with clean exit code 0 — `test_stage_g_poll.bats` test 2 (AC §4.4.2 canonical): `GH_WATCH_HANG=1 CI_POLL_TIMEOUT=2s` produces `STATUS: CI_TIMEOUT` + clean exit 0 within 5s outer timeout. GitLab path symmetric via `${CI_POLL_TIMEOUT%s}` env-override (HIGH-5 fix verified by tests 8-10).
  2. ✅ Rebase-merge dispatched once with correct flags — `test_stage_g_merge.bats` test 3 (AC §4.4.3 canonical): `grep -cE 'pr merge [0-9]+ --rebase --delete-branch' = 1`. Test 4 verifies AC §4.4.1 fallback to `--merge` when `GH_ALLOW_REBASE=false`. GitLab symmetric merge via test 9: `glab mr merge 42 --rebase --remove-source-branch --yes` exactly once.
  3. ✅ Post-merge cleanup pulls main and prunes stale remote refs — `test_stage_g_merge.bats` test 7: post-G4, `git branch --show-current` = `main` AND local main matches bare-remote main (fast-forwarded). `git fetch --prune` invoked.
- **Engineering Standards HARD gate (§6.7):** all 5 conditions PASS
  1. AA-MA artifacts in sync — `git status --porcelain .claude/dev/active/...` returns 0 dirty files (verified pre-this-commit)
  2. Zero `Status: PENDING` in M4 — Step 4.8 transitions to COMPLETE with this approval
  3. Tests pass — `bats tests/commands/sole-dev-merge/` 65/65 green (56 pre-§6.8-fix + 9 new §6.8 regression); `uv run pytest --tb=short -q` 782 passed, 1 skipped, 7 deselected
  4. Impact-analysis evidence — IMPACT_ANALYSIS M4 entry in provenance.log (Risk: LOW; 5 files; no contract changes pre-fix; cross-refs to stage-g[1-4]- markers all in expected paths)
  5. Critical-Path evidence — CRITICAL_PATH_REVIEW — version-pipeline entry in provenance.log (6 evidence points: canonical merge count = 1, AC §4.4.1 fallback enforced, G4 main fast-forwarded, timeout/failed skip merge, GitLab JSON-poll uses glab api NOT glab ci status, RC=124 → clean exit 0 + STATUS:CI_TIMEOUT); Prototype-Required absent → check skipped (absent-field semantic)
- **§6.8 Post-Impl Adversarial Review (Audit-Profile: code-only = full 5-agent slate per project precedent):** initial verdict BLOCKED (1 CRITICAL + 5 HIGH + 7 MED + 11 LOW). User-directed inline fixes addressed:
  - CRITICAL-1: Stage F now exports PR_NUM/PR_URL/MR_IID (closes cross-milestone L-006 contract gap that 3 agents independently flagged)
  - HIGH-1: G3 timeout/failed branches use REMOTE_CHOICE-aware recovery hints (was hardcoded `gh pr merge` regardless of remote)
  - HIGH-2: G2 GitLab `manual|skipped` → STATUS:CI_BLOCKED (was burning 900s on manual gates)
  - HIGH-3+4: Exit-status contract table sync with emitted STATUS lines (write-time drift caught by future-proofing-auditor)
  - HIGH-5: GitLab branch honours `CI_POLL_TIMEOUT` via `${CI_POLL_TIMEOUT%s}` (was hardcoded 900, breaking M5 GitLab smoke test)
  - MED-1: G3 catchall emits STATUS:CI_UNKNOWN
  - MED-3 (partial): 9 new regression tests added covering GitLab branches + CRITICAL-1 + HIGH-1 + HIGH-2 + MED-1
  - DEFERRED: security TOCTOU (M3 carry-over, M5 backlog), magic-30s interval (M5 reference.md consolidation)
  - Final verdict: PASS_WITH_WARNINGS. **TDD-sequence-auditor PASS** ✓ (4 RED commits → GREEN → §6.8 fix, 6m17s delta — M2/M3 lesson applied successfully again).
- **Decision:** APPROVED
- **Commits in M4 window:** 4ccf8e2..HEAD (RED-1, RED-2, GREEN, IA/CPR evidence, §6.8 fixes, this finalization)

## [2026-05-18] GATE APPROVAL: Milestone 5 — Docs + ADR + drift + smoke + CI integration (FINAL)

- **Gate:** HARD
- **Approved by:** Stephen J Newhouse (via /execute-aa-ma-milestone HITL Step 5.10 — autonomous-mode directive)
- **Criteria verified:** 5/5 acceptance criteria from M5 acceptance:
  1. ✅ All 7 doc updates land atomically — M5.4 atomic commit (d4eb797) covers README + CHANGELOG + SECURITY + docs/spec/aa-ma-quick-reference.md. M5.5 (621d499) covers docs/lessons.md L-007 annotation. M5.9 (50acf8a) covers 5 suppression-marker files + README v0.10.0 reference. Post-§6.8 fix (THIS commit) covers docs/spec/claude-code-foundations.md (HIGH-2). CLAUDE.md is .gitignore'd (per-user) — updated locally.
  2. ✅ ADR-0008 lands — `docs/adr/0008-sole-dev-merge-pr-workflow.md` (236 lines, follows ADR-0001..0007 template); INDEX.md updated with row 0008.
  3. ✅ Smoke E2E passes — `test_smoke_e2e.bats` 4/4 PASS (banner ×3 + chained-stage 3-defect E2E ×1). Canonical AC §5.8 satisfied: out-of-scope dummy.py reverted (L-007 guard), in-scope auto-fix commit landed (chore(scope): pre-PR auto-fixes), Stage C emits [CRITICAL] B602, Stage D auto-fix commit subject matches ^fix(review): apply CRITICAL bandit, post-D dummy.py still matches main.
  4. ✅ Bats CI step added — `.github/workflows/security.yml` bats job now runs both `tests/hooks/` AND `tests/commands/sole-dev-merge/` so PRs that regress the workflow block before merge.
  5. ✅ Doc-drift detector clean — Tier 1 returns 0 CRITICAL findings post-§5.9 closure (8 legitimate non-canonical references suppressed via doc-drift-ignore-file/version markers); Tier 2 has Unreleased section present in CHANGELOG.md; Tier 6 silently skips (no project doc-counts.sh config). Foundations.md count surface (HIGH-2) closed in §6.8 fix.
- **Engineering Standards HARD gate (§6.7):** all 5 conditions PASS
  1. AA-MA artifacts in sync — `git status --porcelain .claude/dev/active/...` returns 0 dirty files (verified pre-this-commit)
  2. Zero `Status: PENDING` in M5 — Step 5.10 transitions to COMPLETE with this approval
  3. Tests pass — `bats tests/commands/sole-dev-merge/` 69/69 green; `uv run pytest --tb=short -q` 782 passed, 1 skipped, 7 deselected
  4. Impact-analysis evidence — IMPACT_ANALYSIS M5 entry in provenance.log (Risk: LOW; 11 files; additive only)
  5. Critical-Path evidence — CRITICAL_PATH_REVIEW — doc-count-drift entry in provenance.log (M5.4 atomic + §6.8 HIGH-2 foundations.md fix); Prototype-Required absent → skip per absent-field semantic
- **§6.8 Post-Impl Adversarial Review (Audit-Profile: docs-only):** 5 agents dispatched (project precedent: full slate). Initial verdict BLOCKED_BY_HIGH (0 CRITICAL + 2 HIGH + 7 MED + 8 LOW). User-directed inline fixes addressed:
  - HIGH-1: YAML parse-break in dispatching-parallel-agents/SKILL.md (`<!-- ... -->` inside YAML frontmatter caused `yaml.safe_load` to fail; replaced with `#` YAML-comment matching retro/SKILL.md — verified empirically via `yaml.safe_load`)
  - HIGH-2: docs/spec/claude-code-foundations.md missed by M5.4 atomic (still said "Commands (10)" with 10-row table) — fixed: 10→11, /sole-dev-merge row added
  - MED-3/5/6/7: ADR-0008 + CHANGELOG stale test counts ("60+ bats", "8 files", "9 stage blocks", per-file counts) → corrected to "69 bats across 10 files" + "15 stage markers" + per-file counts derived from `grep -cE '^@test'` source-of-truth
  - DEFERRED: security TOCTOU /tmp class (M3 carry-over, M5+1 backlog), smoke test `source || true` tolerance (M5+1 test hardening), 5.9 scope expansion ACKNOWLEDGED (forced by AC)
  - Final verdict: PASS_WITH_WARNINGS. **TDD-sequence-auditor PASS** ✓ (2m28s tests-before-src delta — M2/M3/M4 lesson applied for 4th consecutive milestone).
- **Decision:** APPROVED
- **Commits in M5 window:** b72a8f6..HEAD (Phase A ADR + verify, RED smoke+CI, GREEN banner+smoke, M5.4 atomic, M5.5 lessons, M5.9 tier-1 closure, §6.8 fix-and-finalize)
