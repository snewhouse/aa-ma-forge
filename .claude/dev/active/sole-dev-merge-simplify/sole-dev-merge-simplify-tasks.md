# sole-dev-merge-simplify Tasks (HTP)

_Hierarchical Task Planning roadmap with dependencies and state tracking. PL = provenance.log, CL = context-log.md (this dir)._

## Milestone 1: sdm.sh beside the old skill, proven live
- Status: COMPLETE
- Dependencies: None
- Complexity: 55%
- Effort: 1.75 days
- Gate: HARD
- Audit-Profile: full
- Critical-Path: hook-modification
- Prototype-Required: YES
- Mode: HITL
- Acceptance Criteria:
  - The prototype merges the TODOS-only chore PR live (MERGED, remote branch gone, main = origin/main), and PL has the `PROTOTYPE — Milestone 1: sdm.sh beside the old skill, proven live — <verdict>` line.
  - The new suite `tests/commands/sdm` has N ≥ 115 tests (102 ported + new), RED committed before GREEN.
  - `bats --formatter pretty tests/commands/sdm` prints `N tests, 0 failures`; sdm.sh is 100755, ≤ 400 lines, one `sdm_footer()`, no glab/SDM_STATE/pytest/mypy/Ruff S/shellcheck calls; the old suite still prints `199 tests, 0 failures` and the old SKILL.md/references are unchanged.
  - `security.yml` runs `tests/commands/sdm`.
  - The M1 PR is merged by the branch's `sdm.sh` (`check` / reviews / `ship` / `finish` as separate Bash calls), with `STATUS: OK` quoted in PL.
  - CRITICAL_PATH_REVIEW, TESTS_VERIFIED and GATE APPROVAL lines are present.
- Result Log:
  - COMPLETE 2026-10-22, HARD gate approved by Ste (CL `GATE APPROVAL: Milestone 1`). PR #55 merged as `c612620b` by the branch's own sdm.sh (3 merge runs); deps PR #56 (`4eb03c7f`) and the 1.0 chore PR #53 (`6ad8ad38`) also merged by sdm.sh — 3 live merges.
  - All 6 ACs verified on main `c612620b`: PL PROTOTYPE line; N = 150 ≥ 115, RED first (tdd-sequence-auditor PASS); `150 tests, 0 failures`, 100755, 352 lines, 1 `sdm_footer()`, DROP 0, old suite `199 tests, 0 failures`, old SKILL.md/references diff 0; security.yml runs the suite (grep 2, live in PR #55); `STATUS: OK` in PL; CRITICAL_PATH_REVIEW, TESTS_VERIFIED (962), GATE APPROVAL present.

### Sub-step 1.0: Prototype + deferred work
- Status: COMPLETE
- Mode: HITL
- Dependencies: None
- Prototype-Required: YES
- Acceptance Criteria:
  - `gh pr view <n> --json state` = MERGED, and PL quotes the prototype's `STATUS: OK` line.
  - `git ls-remote --exit-code origin refs/heads/chore/sdm-todo-triage` gives rc 2.
  - `git rev-parse main` = `origin/main`.
  - The 7 entries (TODOS 25, 81, 88, 96, 104, 119, 157) are under Completed; the rest are listed for 1.1 (L-056).
  - CL has `PROTOTYPE FINDINGS: n=<k>` with one line each (k may be 0).
  - PL has `PROTOTYPE — Milestone 1: sdm.sh beside the old skill, proven live — <verdict>`.
  - The prototype branch `prototype/sdm-script` is not merged.
- Result Log:
  - Mode: HITL — Ste: Proceed; lease probe: yes (CL 2026-10-20).
  - Prototype `1fdfd468` on `prototype/sdm-script` (272 lines, 100755, local only). Run by path from the chore worktree, one Bash call each: `check` → `check OK (branch=chore/sdm-todo-triage, base=main, ahead=1)`, pre-commit rc=0; `ship` → `PR_NUM=53`, `PR_URL=…/pull/53`, `CI_STATE=green` (9/9 checks pass), rc 0; `finish 53` → `STATUS: OK worktree=…/.worktrees/chore/sdm-todo-triage`, rc 0.
  - AC: `gh pr view 53 --json state` = MERGED (merge commit `6ad8ad38`); `ls-remote --exit-code origin refs/heads/chore/sdm-todo-triage` rc 2; main = origin/main = `6ad8ad38`; 7 `**Closed:** sole-dev-merge-simplify 1.0` lines under Completed; `prototype/sdm-script` not on origin (ls-remote rc 2) and not an ancestor of main.
  - Merge runs: 1. Chore worktree removed after `git diff chore/sdm-todo-triage main` was empty.
  - Carried to 1.1 (L-056): TODOS "review notes for M1" (1.2 pre-commit env AC, 1.4 review output path, test 1 belongs in ship.bats, `baseRefName` not pinned, lease → test 15, MERGED-arm notes); TODO 88 bullet 3 (C-quoted names) → check.bats; still-open entries `emit_aa_ma_footer` helper, footer-only-inside-forge, install.sh backup, G2 first-check race, G2 appear-wait leading zero, commit-msg-stage signature: each a test or named as carried in 1.1's Result Log.
  - Findings: CL `PROTOTYPE FINDINGS: n=6`.

### Sub-step 1.1: RED — fixtures and tests
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 1.0
- Acceptance Criteria:
  - New fixtures `tests/commands/sdm/fixtures/{bin/gh,bin/pre-commit,helpers.bash}` (check-runs arm from `GH_CHECK_RUNS`, G1 rc control, `pr checks` rows, GraphQL-error arm, field-order-free `pr view`); old fixtures untouched.
  - The 102 KEEP/CHANGE tests ported to `tests/commands/sdm/{check,ship,finish}.bats` per the inventory's per-test map, plus the 13 new tests in plan §5 1.1; each open TODO from 1.0 is a test or named as carried.
  - Added at 1.0 (CL 2026-10-20): new test 14, `finish` on a PR already MERGED at HEAD makes no merge call and goes to the delete (validator W2).
  - Added at 1.0: new test 15, a remote branch moved after the merge is not deleted (lease refused) and `STATUS: BRANCH_NOT_DELETED` is printed (PROTOTYPE FINDINGS 2); new test 16, `ship` sees a github.com origin through the tests' `insteadOf` rewrite (finding 1).
  - `bats --count tests/commands/sdm` = N, recorded here; N = 102 + the new tests ≥ 115.
  - A RED log here lists each new test with its failure line.
  - The RED commit precedes any GREEN.
- Result Log:
  - Mode: AFK — auto-dispatched; 3 parallel port agents (check, ship, finish), lead wrote fixtures, spec and 4 gap tests.
  - Fixtures: `tests/commands/sdm/fixtures/{bin/gh,bin/pre-commit,helpers.bash}` (old fixtures untouched). gh stub: field-order-free `--json/--jq`, check-runs arm (`GH_CHECK_RUNS`, `_TOTAL`, `_RC`), G1 rc (`GH_API_REPO_RC`), `pr checks` rows (`GH_CHECKS_ROWS`), GraphQL mismatch arm (`GH_MERGE_HEAD_MISMATCH`), unmodelled call → rc 3. pre-commit stub: `PRE_COMMIT_RUN` plays a fixer. helpers: local bare forge + `GIT_CONFIG_*` rewrite of `https://github.com/` (no test git call reaches GitHub), empty `CLAUDE_HOME`, `SDM_UNDER_TEST` override. Smoke-tested end to end against the prototype before the port.
  - `bats --count tests/commands/sdm` = **N = 147** (check 42, ship 56, finish 49) = 102 ported (35 + 39 + 28) + 45 new ≥ 115.
  - RED log 1 (this commit, no sdm.sh on the branch): 147/147 `not ok`, each `run` rc 127 (script missing).
  - RED log 2 (`SDM_UNDER_TEST=` prototype `ca5aaff9`): 136 ok, 11 not ok — the GREEN gaps:
    - check.bats:443 `b_scope:480` — commits with nothing staged (set -e death);
    - check.bats:558 new 9 exit table — the prototype's table is empty;
    - finish.bats:365 `g_merge:556` / :387 `:578` — missing `(isCrossRepository=…)` / `(head/owner lookup failed)`;
    - finish.bats:398 `g_merge:620` and :617 new 12 — the oid is checked before the state, generic text;
    - ship.bats:397 `g_poll:134` — interval not validated;
    - ship.bats:417/:425 `g_merge:82/:91` — no `ship: strategy=` line;
    - ship.bats:548/:559 — `CI_APPEAR_TIMEOUT_S=09/010` read as octal.
  - New tests 1–16 present: 1 (ship cancel/fail rows), 2, 3 (finish check-runs), 4 (recovery hint), 5 (ship + finish G1), 6 (G4 plain checkout ×2), 7 (GraphQL mismatch), 8 (subdir: check + finish), 9 (help table), 10 (PR_NUM patterns), 11 (null), 12 (oid ≠ HEAD), 13 (merge fails ×2), 14 (MERGED at HEAD: no strategy, no check-runs, no merge), 15 (lease keeps a moved branch), 16 (insteadOf seam). Mutation-checked by the finish agent: lease, MAIN_NOT_UPDATED guard and `--match-head-commit` each turn a test red.
  - Open TODOs from 1.0: as tests — 88#3 C-quoted names (check.bats ×2), G2 leading zero (ship.bats `02`/`09`/`010`), review-notes test 1 and lease. Carried, not tested here: `baseRefName` not pinned (LOW), G2 first-check race (P3), commit-msg-stage signature, `emit_aa_ma_footer` merge-base helper, footer-only-inside-forge, install.sh backup, MERGED-arm "re-run only from the feature branch" note (→ M2 SKILL.md), 1.4 review output path (→ 1.4).

### Sub-step 1.2: GREEN — complete sdm.sh
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 1.1
- Acceptance Criteria:
  - `bats --formatter pretty tests/commands/sdm` prints `N tests, 0 failures` (N from 1.1).
  - `PRE_COMMIT_FROM_REF=main PRE_COMMIT_TO_REF=HEAD pre-commit run --files claude-code/skills/sole-dev-merge/scripts/sdm.sh $(find tests/commands/sdm -type f)` passes (the range env, else check-conventions exits 2 "no diff source"; TODOS review notes MEDIUM).
  - `git ls-files -s` shows mode 100755 for sdm.sh.
  - `wc -l sdm.sh` ≤ 400.
  - `grep -c '^sdm_footer()' sdm.sh` = 1.
  - `grep -nE '^[^#]*\b(glab|SDM_STATE|pytest|mypy)\b|^[^#]*(--select S|shellcheck )' sdm.sh` gives 0.
  - `bats --formatter pretty tests/commands/sole-dev-merge` prints `199 tests, 0 failures`, and `git diff origin/main -- claude-code/skills/sole-dev-merge/SKILL.md claude-code/skills/sole-dev-merge/references` is empty.
  - `scripts/regen-generated.sh` leaves `git diff --exit-code` clean (a changed plugin-surface golden is committed here).
  - `uv run pytest` passes.
- Result Log:
  - Mode: AFK — auto-dispatched (lead). Seeded from prototype `ca5aaff9`, then closed the 11 RED gaps (commit only when staged, exit table, finish texts and state-first order, interval validation, decimal `10#` caps, `ship: strategy=` line); removed the unreachable finish branch-name check; `sdm_slug ship|finish` prefixes; "ruff/pre-commit not found" lines (no silent skip).
  - `bats --formatter pretty tests/commands/sdm` → `147 tests, 0 failures` (N from 1.1).
  - `PRE_COMMIT_FROM_REF=main PRE_COMMIT_TO_REF=HEAD pre-commit run --files sdm.sh $(find tests/commands/sdm -type f)` → all Passed, rc 0. shellcheck `--enable=check-set-e-suppressed` clean.
  - mode 100755 (`git ls-files -s`, this commit); `wc -l` = 338 ≤ 400; `grep -c '^sdm_footer()'` = 1; DROP grep = 0.
  - Old suite `bats --formatter pretty tests/commands/sole-dev-merge` → `199 tests, 0 failures` after one scoping fix: `test_stage_state.bats:517` grepped the whole skill dir and so demanded sdm.sh's tokens in the OLD SKILL.md table → `--exclude-dir=scripts` (+ `# why:`). `git diff origin/main -- SKILL.md references` = 0 lines.
  - `scripts/regen-generated.sh` rc 0, `codemem draw --check: OK`; only the 4 `generated by … @ <sha>` stamps changed (golden JSON unchanged), committed here as the repo does.
  - `uv run pytest` → 3142 passed, 5 skipped, 0 failed (144 s).

### Sub-step 1.3: CI runs the new suite
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 1.2
- Acceptance Criteria:
  - `grep -c 'tests/commands/sdm' .github/workflows/security.yml` ≥ 1.
  - The PR's `Bats` check passing with the new count in its log is observed at 1.4, after `ship` pushes.
- Result Log:
  - Mode: AFK — auto-dispatched (lead). New step "Run bats on tests/commands/sdm/" in the `bats` job, after the old suite's step (M2 removes the old step and the stale comments at 145-158, "60+").
  - `grep -c 'tests/commands/sdm' .github/workflows/security.yml` = 2 (step name + run; AC ≥ 1); YAML parses. No `${{ }}` input in the step. The live `Bats` check is observed at 1.4.

### Sub-step 1.4: Verify, gate, merge by the new script
- Status: COMPLETE
- Mode: HITL
- Dependencies: Sub-step 1.3
- Acceptance Criteria:
  - §6.7 fences and §6.8 run once under plan §3.
  - The branch's `sdm.sh` is run by path, one Bash call each: `check`, C1/C2 reviews (prompts from `references/stage-c-review-and-security.md` + stop rule, no aggregate/triage bash), `ship --notes <mktemp file>`, `finish <n>`.
  - PR MERGED, and PL quotes `sdm.sh finish`'s `STATUS: OK` line.
  - `git ls-remote --exit-code origin refs/heads/refactor/sdm-script` gives rc 2.
  - main = origin/main.
  - This Result Log has the PR number and the number of merge runs (target 1).
- Result Log:
  - Mode: HITL — Ste: Proceed (boundary checks + live merge).
  - §6.0 CODE_INTEL_REFRESH at `90dbf97a`; §6.3 impact LOW (sdm.sh has no callers yet; old skill byte-identical); §6.6 skipped by rule (bash only); CRITICAL_PATH_REVIEW: 7 merge-gate guards mutation-tested (each turns ≥ 1 test red).
  - §6.7: fence 1 PASS (4 conditions); fence 2 not applicable (`edges=0`, lint clean); fence 3 TESTS_VERIFIED 959 → 960 → **962** (re-run after each code change; final on `ae90cd2b`).
  - §6.8 (5 agents): 1 CRITICAL accepted by Ste and fixed test-first (ruff `--force-exclude`: RED `49143045`, GREEN `e70f156f`), fix re-checked 0C/0W/1I; 14 WARNING + 15 INFO → TODOS. `…-impl-review.md` written.
  - Merge reviews C1 0C/0H/1M/3L, C2 0/0/0/0 (round 1); notes file in a private `mktemp -d` run dir (closes the "1.4 names no output path" TODO); MEDIUM/LOW → TODOS.
  - **PR #55, 3 merge runs** (target 1):
    1. `ship` → `CI_STATE=failed`: pip-audit only, 3 advisories published that week against locked certifi/virtualenv (unrelated). Ste: separate deps PR → #56 merged by this branch's sdm.sh (`STATUS: OK`, `4eb03c7f`). No rebase/force-push: pull_request CI tests the merge ref.
    2. `ship` → `STATUS: PR_BODY_NOT_UPDATED — PR #55 reason=not-this-branch`: GitHub's headRefOid lagged the re-push (the §6.8 WARNING at sdm.sh:151, proven live). Ste: fix now → RED `1e0b52d2`, GREEN `ae90cd2b` (150/150), fix re-checked 0C/0H/1M/4L → TODOS.
    3. `check OK` → `ship`: `PR #55 body updated (read-back matches)`, `CI_STATE=green` (9/9) → `finish 55`: `STATUS: OK worktree=/home/sjnewhouse/projects/github_private/aa-ma-forge/.worktrees/refactor/sdm-script`.
  - AC: PR #55 MERGED (`c612620b`); `ls-remote --exit-code origin refs/heads/refactor/sdm-script` rc 2; main = origin/main = `c612620b`; `git diff --name-only refactor/sdm-script main` = `uv.lock` only (#56). PR #55's CI ran `tests/commands/sdm` (`1..148` run 1; green run 3) — 1.3's live AC.

---

## Milestone 2: switch over and delete
- Status: ACTIVE
- Dependencies: Milestone 1
- Complexity: 40%
- Effort: 1.1 days
- Gate: HARD
- Audit-Profile: full
- Critical-Path: hook-modification
- Mode: HITL
- Acceptance Criteria:
  - M1's post-merge record (SHA map, `pending_steps=0`, `GATE APPROVAL: Milestone 1`) is on the M2 branch.
  - SKILL.md is ≤ 150 lines that call `sdm.sh check|ship|finish`, keeps `disable-model-invocation: true`, and has no fenced block over 3 lines.
  - The six `references/*.md` and `tests/commands/sole-dev-merge/` are gone; no `extract_stage|sole-dev-merge.env|SDM_KEYS` outside fixtures; `security.yml` runs only `tests/commands/sdm/`; the hook keeps the `/sole-dev-merge` token.
  - ADR-0024 exists and partly supersedes ADR-0008; CONTEXT.md, CHANGELOG ("GitLab/glab support; last in v0.17.0") and the stale docs/comments are updated.
  - `uv run pytest` and `bats -r tests` give 0 failures; regen leaves `git diff --exit-code` clean.
  - The M2 PR is merged by the new skill with `STATUS: OK` in PL; `scripts/install.sh` links an executable sdm.sh; FINALIZATION approved by Ste; plan dir archived.
  - CRITICAL_PATH_REVIEW, TESTS_VERIFIED and GATE APPROVAL lines are present.
- Result Log:

### Sub-step 2.0: Post-merge record of M1
- Status: COMPLETE
- Mode: HITL
- Dependencies: None
- Acceptance Criteria:
  - reference.md has a SHA map: the PR's commit subjects (`gh pr view <n> --json commits`) matched against `git log` of the merged range on origin/main.
  - `uv run aa-ma-gate .claude/dev/active/sole-dev-merge-simplify/sole-dev-merge-simplify-tasks.md --milestone 1 --format kv` shows `pending_steps=0`.
  - CL has `GATE APPROVAL: Milestone 1`.
  - Recorded on the M2 branch `refactor/sdm-switch-over` (L-037).
- Result Log:
  - HITL: Ste "Proceed" (2026-10-22). Met by `55e6dfc8` (in this branch): reference.md "Milestone 1 SHA map" 16/16 rows; `aa-ma-gate … --milestone 1` → `status=COMPLETE`, `pending_steps=0`; context-log:75 `GATE APPROVAL: Milestone 1` with `Decision: APPROVED`; branch `refactor/sdm-switch-over` (L-037).
  - AC path fixed: the gate command now names the repo-relative tasks.md path (TODOS "review notes for M1" LOW).

### Sub-step 2.1: RED — a test of SKILL.md's shape (Ste 2026-10-22, validator W4 option D)
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 2.0
- Acceptance Criteria:
  - `tests/skills/test_sole_dev_merge_skill.py` asserts on `claude-code/skills/sole-dev-merge/SKILL.md`: ≤ 150 lines; `sdm.sh check`, `sdm.sh ship` and `sdm.sh finish` each named; no fenced block longer than 3 lines; front-matter `disable-model-invocation: true`; no `glab|gitlab` anywhere (case-insensitive, same rule as 2.3); no copy of the exit table (it points at `sdm.sh help`).
  - Committed on its own before 2.2 and failing on the old SKILL.md (`uv run pytest tests/skills/test_sole_dev_merge_skill.py` rc 1, the failing assertions quoted in the Result Log).
  - CI never sees it red: CI runs on `pull_request` only and the M2 PR opens at 2.4, after 2.2 (validator W1, 2026-10-22).
- Result Log:

### Sub-step 2.2: The switch, as one commit
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 2.1
- Acceptance Criteria:
  - Hook tests: `tests/hooks/aa-ma-footer.bats:167-206` — 2 B-commit footer tests re-pointed at `sdm_footer` (source sdm.sh), the D-block run and "snippets byte-identical" tests dropped; `tests/hooks/commit-signature.bats:228-240` — 2 block-shape tests dropped (156-226 stay).
  - `disable-model-invocation: true` is kept.
  - SKILL.md points at `sdm.sh help` for the full exit table and lists only the STATUS lines the model acts on (validator W2: a 42-row copy would drift and cost ~28% of the budget).
  - `uv run pytest tests/skills/test_sole_dev_merge_skill.py` passes (2.1's RED goes GREEN).
  - `grep -cE 'sdm\.sh (check|ship|finish)' SKILL.md` ≥ 3.
  - No fenced block in SKILL.md is longer than 3 lines.
  - `wc -l SKILL.md` ≤ 150.
  - `test ! -e claude-code/skills/sole-dev-merge/references && test ! -e tests/commands/sole-dev-merge`.
  - `grep -c 'tests/commands/sole-dev-merge\|60+' .github/workflows/security.yml` = 0.
  - `grep -rn 'extract_stage\|sole-dev-merge.env\|SDM_KEYS' claude-code tests .github --exclude-dir=fixtures` gives 0.
  - `grep -c '/sole-dev-merge' claude-code/hooks/aa-ma-commit-signature.sh` ≥ 1.
  - `uv run pytest` and `bats -r tests` both 0 failures.
  - `scripts/regen-generated.sh` leaves `git diff --exit-code` clean.
  - The commit subject does not start with `refactor(skills): split sole-dev-merge `.
- Result Log:

### Sub-step 2.3: Docs
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 2.2
- Acceptance Criteria:
  - `test -f docs/adr/0024-sole-dev-merge-one-script.md`.
  - `grep -c 0024 docs/adr/INDEX.md` ≥ 1.
  - `grep -ci supersed docs/adr/0008-sole-dev-merge-pr-workflow.md` ≥ 1.
  - `grep -c 'Stage state file' CONTEXT.md` = 0 and `grep -c 'Stop rule' CONTEXT.md` ≥ 1.
  - `grep -c 'GitLab/glab support; last in v0.17.0' CHANGELOG.md` = 1.
  - `grep -c 'stage-d-triage' claude-code/hooks/lib/aa-ma-footer.sh` = 0.
  - `grep -rni 'glab\|gitlab' claude-code/skills/sole-dev-merge` gives 0.
  - `uv run pytest` passes.
  - Also done (no grep AC): ADR-0022/ADR-0018 amendment notes; README.md:226, `docs/spec/claude-code-foundations.md:91`, `docs/spec/aa-ma-quick-reference.md:156-157`; comments in `scripts/install.sh:385`, `src/aa_ma/analysis/measure.py:5`; lessons "Fixed in" pointers; TODOS re-homed.
- Result Log:

### Sub-step 2.4: Verify, gate, merge, finalize
- Status: PENDING
- Mode: HITL
- Dependencies: Sub-step 2.3
- Acceptance Criteria:
  - §6.7/§6.8 run under plan §3; the worktree's new SKILL.md is followed and its `sdm.sh` run by path.
  - PR MERGED with `STATUS: OK` quoted in PL.
  - After `scripts/install.sh`: `test -x "$(readlink -f ~/.claude/skills/sole-dev-merge/scripts/sdm.sh)"`.
  - FINALIZATION approved by Ste.
  - The plan dir is under `.claude/dev/completed/` (finalized on `chore/sdm-simplify-finalize`).
- Result Log:
