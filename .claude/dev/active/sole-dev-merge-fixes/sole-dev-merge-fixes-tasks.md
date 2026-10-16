# sole-dev-merge-fixes Tasks (HTP)

Conventions used in the criteria:
- SDM = `tests/commands/sole-dev-merge/`; PL = `sole-dev-merge-fixes-provenance.log`; CL = `sole-dev-merge-fixes-context-log.md`.
- `extract <marker>` = `bash tests/commands/sole-dev-merge/fixtures/extract_stage.sh <marker> <file>`.
- "0 not-ok" = `bats --tap <files> | grep -c '^not ok'` prints 0 and the run exits 0.
- **RED evidence** (every RED sub-step): run the new tests on the unfixed code and record the `not ok` count in the Result Log. Name every new case that already passes there as a guard. The RED commit subject starts `test(…): RED`.
- **Impact evidence** (every verify sub-step): a PL line `IMPACT_ANALYSIS — Milestone N: HIGH=0 unresolved`.
- **Session root:** every execution session starts in `.worktrees/<branch>` (context-log decision 14).
- **Privacy check** (every milestone gate): over all AA-MA files plus `git diff main`, `grep -ciEf ~/.config/carmen/denylist` = 0 (count only) and `grep -cE '/ho[m]e/|/tm[p]/claude-'` = 0. Raw probe output is redacted to `<scratch>`, `<main>`, `<wt>` and `<home>` before it is recorded.
- **`[post-merge]`** marks a criterion that needs the merged state (L-037). It is verified at the next milestone's N.0 (M5: at 5.5). The HARD gate approves the other criteria; the milestone flips to COMPLETE once the `[post-merge]` ones are recorded.

## Milestone 1: Worktree-safe G3/G4, deterministic footer, lessons
- Status: COMPLETE
- Dependencies: None
- Complexity: 65%
- Effort: 2 days
- Gate: HARD
- Audit-Profile: full
- Critical-Path: hook-modification
- Prototype-Required: YES
- Mode: HITL
- Acceptance Criteria:
  - `bats --tap SDM tests/hooks` gives 0 not-ok, and the `ok` count is ≥ 75 + (the new SDM tests) + (the `tests/hooks` baseline recorded in 1.0) + (the new hooks tests).
  - `extract stage-g3-merge claude-code/skills/sole-dev-merge/references/stage-g-merge.md | grep -cE 'gh pr merge.*--delete-branch'` = 0.
  - `grep -cE 'STATUS: (MERGE_FAILED|BRANCH_NOT_DELETED|REMOTE_UNKNOWN)' claude-code/skills/sole-dev-merge/references/stage-g-merge.md` ≥ 3.
  - `grep -rcE 'ORIGINAL_BRANCH:-feature' claude-code/skills/sole-dev-merge/` totals 0.
  - `bats tests/hooks/aa-ma-footer.bats tests/hooks/commit-signature.bats tests/hooks/install_dry_run.bats tests/hooks/pre-compact.bats` gives 0 not-ok.
  - The privacy check gives 0 / 0.
  - PL has `PROTOTYPE — Milestone 1:`, `IMPACT_ANALYSIS — Milestone 1:` and `CRITICAL_PATH_REVIEW — Milestone 1:` (one each); CL has `GATE APPROVAL: Milestone 1` with `Decision: APPROVED`.
  - `[post-merge]` The Result Log names the PR number N. `gh pr view N --json state -q .state` = `MERGED`, and `git ls-remote origin refs/heads/fix/sole-dev-merge-fixes` exits 0 with 0 bytes.
- Result Log:
  - COMPLETE on 2026-10-15, recorded at Sub-step 2.0 (L-037). HARD gate APPROVED in CL (7/7 pre-merge criteria; `aa_ma_has_gate_approval` → found).
  - `[post-merge]`: PR #42 `MERGED c3ea041`; `git ls-remote origin refs/heads/fix/sole-dev-merge-fixes` → rc 0, 0 bytes. Details in 1.12.
  - The merged tree equals the gated tree: `git diff --name-only 240e89f c3ea041` → 0 files. Between `8ae211e` (fence 3 `TESTS_VERIFIED passed=638`) and `c3ea041`, only the 4 AA-MA files changed.
  - `aa-ma-gate --format kv` → `pending_steps=0`, rc 0. PL has 1 each of PROTOTYPE, IMPACT_ANALYSIS and CRITICAL_PATH_REVIEW for Milestone 1.

### Sub-step 1.0: Session root, plan commit, baselines, probe E6
- Status: COMPLETE
- Mode: HITL
- Dependencies: None
- Prototype-Required: YES
- Acceptance Criteria:
  - The session's `pwd` at start is the worktree path (in the Result Log).
  - `git log -1 --format=%s` on the branch = `docs(aa-ma): sole-dev-merge-fixes plan`, and `git status --porcelain .claude/dev/active/sole-dev-merge-fixes` is empty.
  - Baselines: `bats --tap SDM | grep -c '^ok'` = 75, and the `tests/hooks` ok count is recorded.
  - CL has `DECISION E6 probe: approved|declined — Ste`.
  - If approved: `gh auth status` shows the `delete_repo` scope; the repo name, gh's rc, its stderr's first line and the `ls-remote` output are in the Result Log. After `gh repo delete`, `gh repo view <owner>/sdm-e6-probe` exits ≠ 0.
  - PL has exactly one `PROTOTYPE — Milestone 1: Worktree-safe G3/G4, deterministic footer, lessons — <verdict>`. The verdict is `E6 rc=<n>` if approved, or `E6 [U] — covered by the 'gh rc=1 but MERGED' test` if declined.
- Result Log:
  - Mode: HITL — Ste approved proceeding at the gate (2026-10-15).
  - Session pwd at start = `<wt>` (`.worktrees/fix/sole-dev-merge-fixes`), branch `fix/sole-dev-merge-fixes`.
  - `git log -1 --format=%s` = `docs(aa-ma): sole-dev-merge-fixes plan` (1d760f1); `git status --porcelain <plan dir>` = 0 lines (checked before any 1.0 commit, validator W1).
  - Baselines at 1d760f1: `bats --tap SDM` ok=75 not-ok=0; `bats --tap tests/hooks` ok=505 not-ok=0 (27 files). Test-Command baseline total = 580.
  - E6 probe: **declined** by Ste (CL `DECISION E6 probe: declined — Ste`). Verdict `E6 [U] — covered by the 'gh rc=1 but MERGED' test` (1.1).
  - Pre-exec validator: WARN (0 FAIL, 4 WARN: W1 1.0 commit-order, W2 some M1 paths not in reference.md, W3 install.sh anchor re-check in 1.9, W4 cosmetic).

### Sub-step 1.1: RED — G3 tests
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 1.0
- Acceptance Criteria:
  - SDM/test_stage_g_merge.bats:
    - `setup()` has `export ORIGINAL_BRANCH=feature`.
    - The `:100-121` cases assert `grep -c -- --delete-branch "$CLI_LOG"` = 0.
    - The 7 new @tests named in plan §4 1.1 exist (`grep -c '^@test "G3:'` grows by ≥ 7).
  - `fixtures/bin/gh` contains `GH_PR_STATE`, `GH_MERGE_RC` and `GH_HEAD_REF` (`grep -c` ≥ 1 each). The `--json state` and `headRefName` arms sit before the `GH_PR_EXISTS` check.
  - The 5 security-audit cases exist: head-ref mismatch ABORT, `ORIGINAL_BRANCH=main` ABORT, `--output=x` ABORT with no file `x`, tag `feature` survives, and `other/feature` gives no false `BRANCH_NOT_DELETED`. In all, `grep -c '^@test "G3:'` grows by ≥ 12.
  - RED evidence is recorded.
- Result Log:
  - Mode: AFK — auto-dispatched.
  - `setup()` exports `ORIGINAL_BRANCH=feature`; the two `:100-121` cases now assert `grep -c -- --delete-branch` = 0 and `pr merge <n> --<strategy>$`.
  - gh stub: `--json state` → `${GH_PR_STATE:-MERGED}`, `--json headRefName` → `${GH_HEAD_REF:-feature}` (both before `GH_PR_EXISTS`), `pr merge` → `${GH_MERGE_RC:-0}`.
  - `grep -c '^@test "G3:'` 5 → 17 (+12: 7 plan cases + 5 security cases: head-ref mismatch, ORIGINAL_BRANCH=main, `--output=x`, tag survives, `other/feature`).
  - RED on unfixed G3: 14 not-ok (the 2 flipped + 12 new), 9 ok (existing G1/G3-timeout/failed/unknown/gitlab/G4). No new case passes as a guard: the tag and `other/feature` cases also assert `refs/heads/feature` is deleted.

### Sub-step 1.2: GREEN — G3 implementation
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 1.1
- Acceptance Criteria:
  - `bats --tap SDM/test_stage_g_merge.bats` gives 0 not-ok, including the existing G3 tests named for timeout, failed, gitlab green, gitlab timeout and unknown CI state (matched by @test name, not line).
  - `extract stage-g3-merge … | shellcheck --enable=check-set-e-suppressed -` exits 0.
  - `extract stage-g3-merge … | awk '/2>\/dev\/null|\|\| true/ && !/# why:/ && prev !~ /# why:/ {n++} {prev=$0} END{print n+0}'` = 0. check-conventions skips `.md`, so this awk is the check.
  - SKILL.md `:13` no longer says `--delete-branch`.
- Result Log:
  - Mode: AFK — auto-dispatched.
  - `stage-g-merge.md` G3 `green)` arm replaced per plan §4 1.2: ORIGINAL_BRANCH required; check-ref-format / not-default / PR-head refusals (rc 1) before any merge; `gh pr merge <n> --<strategy>` with no `--delete-branch`; decision from `gh pr view --json state`; `git push origin :refs/heads/<b>` then `ls-remote` assert; `STATUS: MERGE_FAILED|BRANCH_NOT_DELETED|REMOTE_UNKNOWN`; prints `MERGE_DISPATCHED=0|1`.
  - Deviation from the plan snippet: the `git push … :refs/heads/<b>` keeps its stderr (no `2>/dev/null`), so the operator sees git's reason on a refused delete; rc still printed.
  - `bats --tap SDM/test_stage_g_merge.bats` = 23 ok, 0 not-ok (incl. existing timeout, failed, gitlab green, gitlab timeout, unknown).
  - `extract stage-g3-merge | shellcheck --enable=check-set-e-suppressed -` rc 0; suppression awk = 0; `gh pr merge.*--delete-branch` in G3 = 0; `STATUS: (MERGE_FAILED|BRANCH_NOT_DELETED|REMOTE_UNKNOWN)` in stage-g-merge.md = 6.
  - G3 prose (`:26-37`) and SKILL.md `:13` updated; SKILL.md no longer says `--delete-branch`.

### Sub-step 1.3: RED — G4 worktree tests
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 1.2
- Acceptance Criteria:
  - `grep -c '_sandbox_worktree()' SDM/test_stage_g_merge.bats` = 1.
  - There are @tests for AC2.2, AC2.2b, AC2.3, AC2.3b, AC2.4, AC2.5 and AC2.6 (`grep -cE '@test "G4: AC2\.(2|2b|3|3b|4|5|6) '` = 7), and at least one uses branch `feature/x`.
  - The AC2.2 test asserts `git -C "$MAIN" rev-parse HEAD` = `git --git-dir="$BARE_REMOTE" rev-parse main`, and that the worktree's `branch --show-current` is unchanged.
  - RED evidence is recorded. AC2.4 (subdirectory) is expected to pass as a guard.
- Result Log:
  - Mode: AFK — auto-dispatched.
  - `_sandbox_worktree [main_dir] [branch]` added (count 1): main checkout, linked worktree at `<main>/.worktrees/<branch>`, bare remote with post-merge state. Plus `_fingerprint` (HEAD + `diff HEAD` + tracked status, sha256).
  - 7 tests `G4: AC2.(2|2b|3|3b|4|5|6) ` (count 7); AC2.3b uses branch `feature/x`. AC2.2 asserts main HEAD = bare `main` and the worktree branch/HEAD unchanged. AC2.2b evals the printed cleanup lines against a recording `git` function (dry run) and checks argv equals the spaced paths.
  - RED on unfixed G4: 6 not-ok (AC2.2, 2.2b, 2.3, 2.3b: `checkout main` fails in the worktree; AC2.5: the worktree is switched off `feature`; AC2.6: rc 0 with the `feature` default). AC2.4 (subdirectory, plain checkout) passes as the expected guard. Existing G4 test `:149` ok.

### Sub-step 1.4: GREEN — G4 implementation
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 1.3
- Acceptance Criteria:
  - `extract stage-g4-cleanup … | grep -cE '\bgit (-C \S+ )?pull\b'` = 0.
  - In worktree mode the `else` branch contains no `checkout` (`awk '/^else/,/^fi/' | grep -c checkout` = 0).
  - `grep -c 'ORIGINAL_BRANCH:-feature'` = 0.
  - The branch-delete line has no `2>/dev/null || true`.
  - `bats --tap SDM/test_stage_g_merge.bats` gives 0 not-ok; shellcheck on the extracted G4 exits 0.
- Result Log:
  - Mode: AFK — auto-dispatched.
  - G4 rewritten per plan §4 1.4: ORIGINAL_BRANCH required + check-ref-format; worktree detection via absolute `--git-dir` vs `--git-common-dir` (E7); plain checkout → checkout, `fetch --prune`, `merge --ff-only`, branch delete with rc line; worktree → `git -C <main wt>` fast-forward, MAIN_CHECKOUT_DIRTY / MAIN_NOT_UPDATED, `--stat`, `%q`-quoted cleanup commands. G4 prose updated.
  - Greps on extracted G4: `git … pull` = 0; `else…fi` `checkout` = 0; `ORIGINAL_BRANCH:-feature` in the skill = 0; branch-delete line has no `2>/dev/null || true`; unexplained-suppression awk = 0.
  - `bats --tap SDM/test_stage_g_merge.bats` 30 ok / 0 not-ok; shellcheck `--enable=check-set-e-suppressed` on G4 rc 0. Whole SDM 94 ok / 0 not-ok (75 + 19 new).

### Sub-step 1.5: RED — footer helper tests
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 1.0
- Acceptance Criteria:
  - `tests/hooks/aa-ma-footer.bats` exists with ≥ 9 @tests:
    - 0 plans → `[ad-hoc]`;
    - 1 plan → that plan;
    - 2 plans, b touched → `[AA-MA Plan] b`;
    - 2 plans, both touched → `[ad-hoc]` plus stderr `WARN: aa-ma-footer`;
    - 2 plans, neither touched → the same;
    - detached HEAD → no crash;
    - no `origin/HEAD` → `origin/main` fallback;
    - an untracked plan dir counts as touched;
    - helper path: in a repo without `claude-code/hooks/lib/`, the extracted B-commit and D still emit a footer.
  - The tests source the helper without `pipefail`.
  - RED evidence is recorded. The 0-plan, 1-plan and detached cases are expected guards.
- Result Log:
  - Mode: AFK — auto-dispatched.
  - New `tests/hooks/aa-ma-footer.bats`, 13 @tests: 0 plans; 1 plan; 2 plans b touched (+ mirror a); both touched → `[ad-hoc]` + `WARN: aa-ma-footer`; neither → same; uncommitted edit counts (+ mirror); detached HEAD; no `origin/HEAD` → `origin/main` (+ mirror); untracked plan dir; B-commit outside forge with helper under `CLAUDE_HOME`; B-commit with no helper → `[ad-hoc]` + notice; D outside forge rc 0; footer-resolve snippets byte-identical.
  - Helper sourced after `set +o pipefail`; `CLAUDE_HOME` is a temp dir and `AA_MA_FOOTER_HELPER` is unset.
  - First draft: the "b touched" cases passed on unfixed code by `find` order alone (L-045). Each "picks X" case now also checks the mirror plan.
  - RED on unfixed helper/skill: 9 not-ok, 4 ok. Guards: 0-plan, 1-plan and detached (expected); untracked-dir (`find` lists the newest dir first, so the unfixed helper picks it too; it fails if the fix drops `ls-files --others`).

### Sub-step 1.6: GREEN — footer helper and skill resolution chain
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 1.5
- Acceptance Criteria:
  - `grep -c 'merge-base' claude-code/hooks/lib/aa-ma-footer.sh` ≥ 1.
  - `grep -c 'CLAUDE_HOME:-\$HOME/.claude'` = 1 and `grep -c 'footer-resolve:begin'` = 1, in both SKILL.md and stage-d-triage.md (today both are 0).
  - The two `footer-resolve` snippets are byte-identical (an @test in aa-ma-footer.bats).
  - `bats --tap tests/hooks/aa-ma-footer.bats SDM/test_stage_b_scope.bats SDM/test_stage_d_triage.bats SDM/test_smoke_e2e.bats` gives 0 not-ok.
  - `shellcheck claude-code/hooks/lib/aa-ma-footer.sh` exits 0.
- Result Log:
  - Mode: AFK — auto-dispatched.
  - `emit_aa_ma_footer` rewritten (plan §4 1.6): one plan → it; several → the one touched since `merge-base HEAD origin/HEAD|origin/main` (tracked diff incl. uncommitted, or untracked plan dir); else `[ad-hoc]` + stderr WARN. Header "Behaviour" comment rewritten. `grep -c merge-base` = 3.
  - SKILL.md B-commit and stage-d-triage.md: hard `source` replaced by the `footer-resolve` chain (`AA_MA_FOOTER_HELPER` → repo copy → `${CLAUDE_HOME:-$HOME/.claude}/hooks/lib` → inline `[ad-hoc]` fallback with a notice). Per file: `CLAUDE_HOME:-$HOME/.claude` = 1, `footer-resolve:begin` = 1; byte-identical @test ok.
  - `bats --tap aa-ma-footer.bats SDM/test_stage_b_scope.bats SDM/test_stage_d_triage.bats SDM/test_smoke_e2e.bats` = 29 ok / 0 not-ok. shellcheck rc 0 on the helper and on the extracted B-commit and D.
  - Hostile probes: under `set -euo pipefail` with 2 plans and no remote → rc 0, `[ad-hoc]` + WARN; outside any repo → `[ad-hoc]`, rc 0.

### Sub-step 1.7: RED/GREEN — commit-signature trusts emit_aa_ma_footer
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 1.6
- Acceptance Criteria:
  - tests/hooks/commit-signature.bats has 6 new @tests:
    - an active plan plus `FOOTER=$(emit_aa_ma_footer); git commit -m "x${FOOTER}"` → rc 0;
    - no helper and no literal signature → rc 2;
    - the name only mentioned in a comment → rc 2;
    - a redefined `emit_aa_ma_footer(){ :; }` → rc 2;
    - the footer not at the end of the message → rc 2;
    - FOOTER reassigned after the helper call → rc 2.
  - RED: the first test fails before the fix.
  - GREEN: 0 not-ok across all 17 tests; shellcheck on the hook exits 0. The header rule table (`:13-22`) has the new rule, and TODOS has a `commit-msg`-stage entry.
- Result Log:
  - Mode: AFK — auto-dispatched.
  - RED (ba8777a): 8 new @tests. The 6 planned, plus the real extracted `stage-b-commit` and `stage-d-triage` text fed through the hook. 3 not-ok before the fix: the helper accept case and the two real blocks. The 5 bypass cases already returned rc 2 (guards).
  - GREEN: new rule 8 in `aa-ma-commit-signature.sh`, plus a header table row.
    - It strips the skill's exact `[ad-hoc]` fallback definition. It then requires `emit_aa_ma_footer` ×1 as `FOOTER=$(emit_aa_ma_footer)`, the word `FOOTER` ×2, one `git commit`, the helper before the commit, and `-m "…${FOOTER}"` with no later message flag.
  - `bats commit-signature.bats` 19/19 ok (11 + 8; the AC's "17" plus the 2 real-block cases). hook-headers ok. `shellcheck` rc 0 (the SC2016 literal moved into a named constant with `# why:`).
  - Hostile matrix (L-049), 17 probes.
    - Blocked (rc 2):
      - a second `-m`, `--trailer` or `-c`;
      - the helper call after the commit;
      - a second commit;
      - a `function`/`alias` redefinition, or a redefinition next to the fallback;
      - `printf -v FOOTER` or `unset FOOTER`;
      - a piped helper;
      - a single-quoted `${FOOTER}`.
    - Allowed (rc 0): a trailing pathspec, `--amend`, the `[ad-hoc]` fallback, `&& echo`.
    - One finding: `git commit -am "unsigned"` passes with rc 0. It also passes on the hook at `1d760f1` (step 4 "editor form"), so it predates this change and is out of 1.7 scope. It is recorded in the new TODO.
  - TODOS: new entry "Check the AA-MA commit signature at the `commit-msg` stage, not in the command text".

### Sub-step 1.8: RED/GREEN — pre-compact never follows a symlink
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 1.7
- Acceptance Criteria:
  - tests/hooks/pre-compact.bats has 4 new @tests with a fake `HOME`: symlinked provenance.log, symlinked context-log.md, symlinked reference.md, symlinked task dir. Each asserts:
    - the symlink target's sha256 is unchanged;
    - the snapshot has no copied target content;
    - rc 0;
    - one hooks.log skip line;
    - `jq -e .systemMessage` exits 0.
  - RED: at least the provenance.log and context-log.md cases fail before the fix.
  - GREEN: 0 not-ok across all 17 tests; `shellcheck claude-code/hooks/pre-compact-aa-ma.sh` exits 0.
  - `grep -cE '\[\[ -L |realpath' claude-code/hooks/pre-compact-aa-ma.sh` ≥ 2.
- Result Log:
  - Mode: AFK — auto-dispatched.
  - RED (37225cf): 4 new @tests with a fake HOME (symlinked provenance.log, context-log.md, reference.md, task dir). All 4 not-ok before the fix. Repro: the fake `<home>/.bashrc` went from 1 to 3 lines through a symlinked provenance.log.
  - GREEN: before any read or write, `pre-compact-aa-ma.sh` skips a task whose dir, or any of its 4 AA-MA files, is a symlink (`[[ -L ]]`). Each skip writes one `skipped task <name>: …` WARN line to hooks.log and is counted. Skips and append failures share one systemMessage. The Fail-open header is updated.
  - Deviation from the plan: no `realpath -e` containment check. With the `-L` checks in place, a regular file in a non-symlinked dir is always inside that dir, so the check adds nothing, and `realpath -e` is GNU-only. A symlinked parent (`.claude`) is out of scope, as the code comment says. `grep -cE '\[\[ -L |realpath'` = 2.
  - `bats pre-compact.bats` 17/17 ok; hook-headers ok; `shellcheck` rc 0; pre-commit shellcheck passed.
  - Fault probes:
    - a skip with stdout and stderr closed → rc 0;
    - a skip plus a failed append → rc 0 and exactly 1 JSON object naming both;
    - the symlink target is unchanged (1 line).

### Sub-step 1.9: RED/GREEN — install link for the footer helper
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 1.8
- Acceptance Criteria:
  - A new @test in `tests/hooks/install_dry_run.bats` asserts the dry run lists `hooks/lib/aa-ma-footer.sh`. RED evidence is recorded; then 0 not-ok.
  - `grep -c 'aa-ma-footer.sh' scripts/install.sh` ≥ 1.
  - `scripts/uninstall.sh` removes the link: either a dry-run assertion, or a grep showing generic `hooks/lib` handling (whichever applies, recorded in the Result Log).
- Result Log:
  - Mode: AFK — auto-dispatched.
  - RED (ebeda62): the new `install_dry_run.bats` case "announces the hooks/lib/aa-ma-footer.sh symlink" was not-ok before the fix.
  - GREEN: one `create_symlink` block for `hooks/lib/aa-ma-footer.sh`, added after the `aa-ma-log.sh` block. The live anchor is `scripts/install.sh:384-390`; validator W3 re-checked it. Like its neighbours, it has no backup step (TODOS "install.sh: back up every hooks/lib target").
    - `grep -c aa-ma-footer.sh scripts/install.sh` = 3.
    - `install_dry_run.bats` 33/33 ok; install-migration ok; `shellcheck scripts/install.sh` rc 0.
  - Uninstall: generic handling, no change needed. `scripts/uninstall.sh:99` puts `${CLAUDE_HOME}/hooks/lib` in `SEARCH_DIRS` and removes every link that `points_into_repo`.
  - Live check with a fake HOME laid out like the test setup: `install.sh` rc 0, link → `<wt>/claude-code/hooks/lib/aa-ma-footer.sh`; `uninstall.sh` rc 0, link removed.

### Sub-step 1.10: Docs and lessons
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 1.4, Sub-step 1.9
- Acceptance Criteria:
  - `grep -c 'the plan the branch changed' docs/spec/aa-ma-specification.md` = 1.
  - `grep -c '^\*\*Best-effort step\*\*' CONTEXT.md` = 1.
  - `grep -cE '^## L-05[1-5] ' docs/lessons.md` = 5, and the L-007 entry mentions `L-053`.
  - `git diff main -- . | grep -ciEf ~/.config/carmen/denylist` = 0 (count only), and the diff names no private repository (L-029, L-039; reviewed by eye and noted in the Result Log).
  - TODOS:
    - the G3/G4 entry sits under `## Completed` with a `**Done:** sole-dev-merge-fixes M1` line;
    - the footer half of `:239` is closed;
    - a new entry `### Hooks resolve the active plan from $PWD`, extracted with `awk '/^### Hooks resolve the active plan from/,/^\*\*Priority/' TODOS.md`, gives `grep -c` ≥ 1 for each of `commit-drift`, `session-end-dirty`, `session-start` and `commit-signature`.
  - `CHANGELOG.md`: 5 new bullets under `## Unreleased → ### Fixed`, and `grep -c '^## Unreleased' CHANGELOG.md` = 1.
  - ADR-0008 `:114` no longer says "checkout main".
- Result Log:
  - Mode: AFK — auto-dispatched.
  - Spec §VI: the "Detection Logic/Priority" lists are replaced by one detection rule (one plan → it; several → "the plan the branch changed"; else `[ad-hoc]` + warning), plus an Enforcement note: the hook accepts any plan and the canonical helper commit, and the banner's alphabetical order is a separate rule. `grep -c 'the plan the branch changed'` = 1.
  - CONTEXT.md: **Best-effort step** term added (`grep -c` = 1), plus a dated Flagged-ambiguities bullet.
  - docs/lessons.md: L-051..L-055 added at the top (`grep -cE '^## L-05[1-5] '` = 5). L-052 and L-054 carry "Fixed in: … M1"; L-051/L-053 (M3) and L-055 (M2) carry "Status: fix planned". L-007 gains a 2026-10-15 gap note naming L-053.
  - TODOS:
    - the G3/G4 entry moved under `## Completed` with `**Done:** sole-dev-merge-fixes M1`;
    - the footer half of the install.sh entry is struck and marked Done;
    - new `### Hooks resolve the active plan from $PWD` entry. Its awk range counts commit-drift 1, session-end-dirty 1, session-start 1, commit-signature 2. Anchors are re-checked at HEAD: commit-signature is now `:103`, moved by the 1.7 header rows.
  - CHANGELOG `## Unreleased → ### Fixed`: 5 new bullets (G3, G4, footer helper, commit-signature trust, install link); `^## Unreleased` = 1. The 1.8 symlink fix went under `### Security`, not Fixed, so Fixed stays at 5.
  - ADR-0008: the `:55` footer paragraph and the G3/G4 table rows are updated; `grep -c 'checkout main'` = 0.
  - Privacy: denylist count 0; `/ho[m]e/|/tm[p]/claude-` count 0. A by-eye check plus a grep for known private names gave 2 hits; both are the denylist file's own path (`~/.config/<org>/denylist`), quoted in this tasks.md by the planning commit. The diff names no private repository. (Corrected after commit 86a6403, which logged "0" before the grep output was read; global L-1352.)

### Sub-step 1.11: Verify, impact, gate
- Status: COMPLETE
- Mode: HITL
- Dependencies: Sub-step 1.10
- Acceptance Criteria:
  - `bats --tap SDM tests/hooks` gives 0 not-ok, and `uv run pytest -q` exits 0. The counts are in the Result Log.
  - shellcheck exits 0 on the extracted G3, G4, B-commit and D, and on `aa-ma-footer.sh`, `aa-ma-commit-signature.sh` and `pre-compact-aa-ma.sh`.
  - The privacy check gives 0 / 0.
  - `scripts/regen-generated.sh` exits 0, and `git status --porcelain tests/golden docs/architecture` is empty after commit.
  - PL has `IMPACT_ANALYSIS — Milestone 1: HIGH=0 unresolved` and `CRITICAL_PATH_REVIEW — Milestone 1:`.
  - CL has `## <date> GATE APPROVAL: Milestone 1` with `Decision: APPROVED`.
- Result Log:
  - Mode: HITL — Ste: "Proceed" at the gate; HARD gate "Approve".
  - Full suites at 9fbb57f: bats 625/625 and pytest 3 failed.
    - Fixed in 6b12a9d: 2 bare `!` bats assertions that could not fail. The pre-compact sentinel check now fails against the pre-fix hook (mutation-verified).
    - Plugin-surface drift: a new edge, hook commit-signature → skill sole-dev-merge. Orphan set updated.
  - §6.0 CODE_INTEL_REFRESH: codemem and graphify at 6b12a9d. Fence 2: no §13 sigil edges.
  - §6.8 PASS_WITH_WARNINGS (0/9/16). WARNINGs fixed test-first (RED 68a02bb; b31a9c0, e82da0d, 98b41ab, 1ce6b15) or deferred. See impl-review.md.
  - Final state at 8ae211e:
    - fence 3 TESTS_VERIFIED passed=638 (`bats --tap SDM tests/hooks`, 0 not-ok); `uv run pytest -q` 3136 passed;
    - shellcheck 0 on extracted G3/G4/B-commit/D and on aa-ma-footer.sh, aa-ma-commit-signature.sh, pre-compact-aa-ma.sh;
    - privacy 0/0;
    - `regen-generated.sh` rc 0; `git status --porcelain tests/golden docs/architecture` empty after commit 8ae211e.
  - PL has IMPACT_ANALYSIS (HIGH=0 unresolved) and CRITICAL_PATH_REVIEW. CL has `GATE APPROVAL: Milestone 1`, Decision: APPROVED.

### Sub-step 1.12: PR, bootstrap merge, post-merge checks
- Status: COMPLETE
- Mode: HITL
- Dependencies: Sub-step 1.11
- Acceptance Criteria:
  - `[post-merge]` (recorded at 2.0) The PR number N is in the Result Log and `gh pr view N --json state -q .state` = `MERGED`.
  - `[post-merge]` The Result Log quotes the manual steps (plan §0 bootstrap) and `git ls-remote origin refs/heads/fix/sole-dev-merge-fixes` exits 0 with 0 bytes.
  - `git -C <main> rev-parse HEAD` = `git -C <main> rev-parse origin/main`, and `git -C <main> status --porcelain --untracked-files=no` is empty.
  - `scripts/install.sh` exits 0. `readlink -f` of `~/.claude/skills/sole-dev-merge` and of `~/.claude/hooks/lib/aa-ma-footer.sh` both begin with the main checkout path.
  - The 1.12 evidence is written into the M2 branch's tasks.md at Sub-step 2.0 (L-037); this sub-step's Status flips to COMPLETE there.
  - The M1 worktree is removed with the printed cleanup commands; `git worktree list` no longer shows it.
  - `emit_aa_ma_footer`, run in a code-conventions-impact worktree that changed its plan dir, prints a line that `grep -c '^\[AA-MA Plan\] code-conventions-impact '` counts as 1. If no such worktree exists, a scratch clone with both plans and a CCI-only touch is used, and recorded.
- Result Log:
  - Mode: HITL — Ste chose the "direct gh path" for the bootstrap merge. Recorded at Sub-step 2.0 on `fix/sole-dev-merge-fixes-m2` (L-037), and every check re-run live on 2026-10-15 before this was written.
  - **PR #42.** `gh pr view 42 --json state,mergeCommit` → `MERGED c3ea041`.
  - **Manual steps (plan §0 bootstrap), as run:**
    1. `gh pr create`, then `gh pr checks 42 --watch` → all 9 checks passed;
    2. `gh pr merge 42 --rebase --match-head-commit 240e89f…`, with no `--delete-branch` → rc 0, MERGED `c3ea041`;
    3. `git push -q origin :refs/heads/fix/sole-dev-merge-fixes` → rc 0;
    4. `git ls-remote --exit-code origin refs/heads/fix/sole-dev-merge-fixes` → rc 2;
    5. `git -C <main> fetch -q --prune origin && git -C <main> merge -q --ff-only origin/main` → rc 0. The unfixed G4 was not run.
  - **Remote branch gone.** Re-run: `git ls-remote origin refs/heads/fix/sole-dev-merge-fixes` → rc 0, 0 bytes.
  - **Main checkout.** `rev-parse main` = `rev-parse origin/main` = `c3ea041`. `git -C <main> status --porcelain --untracked-files=no` gave 0 lines (read after the M1 worktree was removed, before this session was isolated in the M2 worktree).
    - Interim state: right after the merge, main held 2 lines that the pre-compact hook wrote during a 10:58 compaction of a main-rooted CCI session (L-1347). Ste chose to leave them (L-066). That CCI session saved them to its own scratchpad diff and discarded them before running `git pull`. No commit, no stash.
  - **Install.** Ste ran `scripts/install.sh` → rc 0 (68 links, 0 stale). `readlink -f` → `<main>/claude-code/skills/sole-dev-merge` and `<main>/claude-code/hooks/lib/aa-ma-footer.sh`.
  - **M1 worktree removed.** An inventory came first: tree clean; `git cherry origin/main fix/sole-dev-merge-fixes` → 0 unmerged; no stash. Its only unique ignored file, the 1.0 handover, was archived to `<main>/.claude/handovers/done/`. Ste then ran `git worktree remove .worktrees/fix/sole-dev-merge-fixes && git branch -D fix/sole-dev-merge-fixes` (was `240e89f`). `git worktree list` no longer shows it.
  - **CCI footer.** No CCI worktree exists, so a scratch clone of main `c3ea041` with both plans was used. Branch `probe-cci` appended one line to the CCI provenance.log. The installed `emit_aa_ma_footer` printed `[AA-MA Plan] code-conventions-impact .claude/dev/active/code-conventions-impact`; `grep -c '^\[AA-MA Plan\] code-conventions-impact '` = 1. The clone was deleted.

## Milestone 2: Stage state file
- Status: COMPLETE
- Dependencies: Milestone 1
- Complexity: 55%
- Effort: 1 day
- Gate: HARD
- Audit-Profile: full
- Critical-Path: hook-modification
- Prototype-Required: YES
- Mode: HITL
- Acceptance Criteria:
  - For each block A, B, B-commit, C, D, E0, E2, E3, F, G1, G2, G3, G4: `extract <block> | grep -c 'sole-dev-merge.env'` ≥ 1. Only A lacks `sdm_load`.
  - `bats --tap SDM/test_stage_state.bats` gives 0 not-ok with ≥ 16 @tests (the cases in plan §4 M2 2.1, hostile lines included).
  - `grep -rn 'eval' claude-code/skills/sole-dev-merge/ | grep -c sdm` = 0, and `grep -rc '/tmp/sole-dev-merge' claude-code/skills/sole-dev-merge/` totals 0 (all run files are under `$SDM_DIR`).
  - An @test asserts `stat -c %a "$SDM_DIR"` = 700, and that the state file mode is 600.
  - `grep -rnE 'SLUG.*date \+%s|PR_NUM:-0|ORIGINAL_BRANCH:-feature|SLUG:-NOSLUG' claude-code/skills/sole-dev-merge/ | wc -l` = 0 (today 4+).
  - `[post-merge]` (recorded at 3.0) The Result Log quotes the merge's G3 output containing `MERGE_DISPATCHED=1` and the G4 line `STATUS: OK`, and `git ls-remote origin refs/heads/fix/sole-dev-merge-fixes-m2` exits 0 with 0 bytes, with no manual steps.
  - The privacy check gives 0 / 0.
  - PL has PROTOTYPE, IMPACT_ANALYSIS and CRITICAL_PATH_REVIEW lines for Milestone 2; CL has a GATE APPROVAL for Milestone 2.
- Result Log:
  - Merged as PR #43 (rebase; main `c3ea041..52f4fd3`, 18 commits) by the branch's own M2 blocks, each stage in a separate Bash call. Pre-merge criteria 7/7 (CL GATE APPROVAL). The `[post-merge]` criterion is recorded in 2.3 (G3 `MERGE_DISPATCHED=1`, G4 `STATUS: OK`, ls-remote 0 bytes, no manual steps). Flipped to COMPLETE at Sub-step 3.0.

### Sub-step 2.0: Post-merge of M1, and prototype the state file
- Status: COMPLETE
- Mode: HITL
- Dependencies: None
- Prototype-Required: YES
- Acceptance Criteria:
  - The session starts in `.worktrees/fix/sole-dev-merge-fixes-m2` on branch `fix/sole-dev-merge-fixes-m2`, and `git merge-base --is-ancestor origin/main HEAD` exits 0.
  - Sub-step 1.12's Result Log and Status are completed here, and Milestone 1 is flipped to COMPLETE.
  - The scratch `proof.sh` output has 6 `PASS` lines (`grep -c '^PASS' proof.out` = 6):
    - survives separate `bash` calls;
    - survives `cd <wt> && bash`;
    - the per-worktree absolute git-dir holds;
    - `set -a` smoke chaining;
    - hostile values round-trip;
    - a non-empty explicit env wins.
  - PL has `PROTOTYPE — Milestone 2: Stage state file — <verdict>`.
- Result Log:
  - Mode: HITL — Ste: "Proceed".
  - **Session root.** The session was moved into `<main>/.worktrees/fix/sole-dev-merge-fixes-m2` (EnterWorktree, CL session note). Branch `fix/sole-dev-merge-fixes-m2`; `git merge-base --is-ancestor origin/main HEAD` → rc 0 at `c3ea041`. The hooks' plan scan from here sees both plans.
  - **1.12 and Milestone 1:** recorded and flipped to COMPLETE (`cd47f93`, provenance `f78bbf9`). Before the flip, `aa-ma-gate` gave `pending_steps=0` for M1, which answers the handover ❓.
  - **Q2 decision:** G3/G4 read `ORIGINAL_BRANCH` from the state file only (CL).
  - **Prototype** (`<scratch>/m2proto/proof.sh`, throwaway). Scratch repo with a main checkout and a linked worktree `feat`. The plan §4 M2 loader is copied verbatim; every block runs as `env -i bash` (empty env). `grep -c '^PASS' proof.out` = **6**:
    - separate-bash-calls: A then R in separate shells → `ORIGINAL_BRANCH=feat`, `SLUG=slug1`;
    - cd-then-bash: saved from `<wt>/sub`, read from the root → `PR_NUM=42`;
    - per-worktree-git-dir: main and wt hold separate files (`mainslug` / `slug1`); the absolute git-dir is `.git/worktrees/feat`;
    - set-a-chaining: `set -a; source A; source R` → both sources rc 0, values visible, and a later fresh shell reads them too;
    - hostile-round-trip: a value with spaces, both quote kinds, `$HOME`, backticks, `$(id)`, `;|&<>\`, a tab, an embedded newline and a trailing `=` round-trips byte-exact. Hand-written lines `PR_URL=$(touch PWN)`, ``CI_STATE=`touch PWN` ``, `GIT_SSH_COMMAND=…` and `BASH_ENV=…` give 4 messages (2 "bad value", 2 "unknown key"), and `PWN` count = 0;
    - explicit-env-wins: `PR_NUM=99` beats the file's 42; an empty `PR_NUM=` does not mask it (→ 42).
  - **Extras, all ok:** state file 600; `SDM_DIR` 700; a file from another branch is ignored with the message; group-writable and symlinked files are refused and nothing is loaded; a bad base64 line keeps the earlier good value; a trailing newline is dropped (documented); with no state file the block exits 0.
  - **First run** was 5 PASS + 1 FAIL + 3 EXTRA FAIL. All 4 were harness bugs, not design bugs:
    - check 4's Stage A had (correctly) truncated `PR_NUM`, so check 6 now re-saves it;
    - the foreign-branch check compared output that also held the hostile lines' messages;
    - two `cut -c1-36` checks were off by one.
  - **Mutation (L-045):** dropping the `[[ -n "${!k:-}" ]] ||` guard → explicit-env-wins FAILs; `printf -v` → `eval` → hostile-round-trip FAILs. The checks can fail.
  - **Notes for 2.1/2.2:**
    - Stage A's `rm -f` wipes every later key (PR_NUM etc.) by design, so a mid-flow re-run of A starts over;
    - loader messages go to stdout, and a file holding hostile lines repeats its messages on every load;
    - under `set -a` sourcing, `SDM_STATE`/`SDM_KEYS` are exported too (harmless).
  - Verdict: **PASS**.

### Sub-step 2.1: RED — state tests
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 2.0
- Acceptance Criteria:
  - `test -f SDM/test_stage_state.bats` passes, and it has ≥ 16 @tests.
  - `grep -c 'sole-dev-merge.env' SDM/test_smoke_e2e.bats` ≥ 1.
  - RED evidence is recorded.
- Result Log:
  - Mode: AFK — auto-dispatched.
  - **New file** `SDM/test_stage_state.bats`, **22 @tests**. Every block runs through `fresh` (`env -i` with only PATH/HOME, like a new Bash tool call) in a git sandbox with a bare origin. Loader cases use `probe`, which is G1's shipped loader text plus a printer. The cases cover:
    - A: writes the 5 keys; modes 600/700; truncates a stale file; an aborted A leaves none;
    - B saves CHANGED_*; C scans B's files from an empty env and prints `Stage C scanned: Ruff S n file(s), ShellCheck m file(s)`; D writes reviewer notes under SDM_DIR; E3 writes the body there and saves PR_BODY_FILE; G3 reads PR_NUM and saves MERGE_DISPATCHED; G4 reads ORIGINAL_BRANCH; the last write wins;
    - loader behaviour: hostile round-trip, 4 hostile lines inert (and reported), explicit env wins, empty env does not mask, foreign branch ignored, a bad line keeps the good value, a bad ORIGINAL_BRANCH voids the file, trailing newline dropped, symlink/g+w/o+w refused;
    - static checks: only `sdm_save` and A's `rm -f` touch the file; the loader is byte-identical in the 12 non-A blocks and absent from A; no masking defaults, `/tmp/sole-dev-merge` or `eval … sdm`.
  - **Smoke:** `test_smoke_e2e.bats` asserts the state file exists after Stage A (grep count 1).
  - **RED evidence:** `bats --tap SDM/test_stage_state.bats` → **22 not-ok / 0 ok**. Smoke E2E not-ok, at exactly the new assertion. No guards: every case needs the M2 change.
    - The first run had test 14 passing **vacuously**: bash does not inherit errexit into `$(probe)`, so the probe's guard was dead. It now fails through `|| return 1`.
    - The failure lines were checked by test: each fails at the behaviour under test, not at sandbox setup. `tests/test_bats_assertions.py` passes.
  - **Interface choices this RED fixes** (within plan §4 M2; see CL):
    - run files under `$SDM_DIR` with fixed names (`findings.md`, `reviewer-notes.md`, `body.md`, …);
    - A's `rm -f` runs before its checks;
    - C prints a scanned-files line (needed by 2.3's live check).
  - Hygiene: the RED runs of unfixed Stage C left 8 `/tmp/sole-dev-merge-findings-<epoch>.md` files. They were removed by name. The shared `/tmp/sole-dev-merge-body.md` was left alone.

### Sub-step 2.2: GREEN — loader and saver in every block
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 2.1
- Acceptance Criteria:
  - The loader is in the 12 non-A blocks, and Stage A has `rm -f`, `umask 077` and `mkdir -m 700` (`extract stage-a-preflight | grep -cE 'rm -f .*SDM_STATE|umask 077|mkdir -m 700'` = 3). `grep -c '^## State between stages' SKILL.md` = 1.
  - `bats --tap SDM` gives 0 not-ok, and shellcheck exits 0 on all 13 extracted blocks.
- Result Log:
  - Mode: AFK — auto-dispatched.
  - **Loader.** The plan §4 M2 loader text was inserted by script into the 12 non-A blocks, so it is byte-identical; the bats test enforces this. One comment was changed in all 12: `no eval anywhere` → `a value is assigned, never executed`. The plan's own AC (`grep eval | grep -c sdm` = 0) matched its verbatim comment, which also contains `_sdm`.
  - **Stage A:** the first statement is `rm -f "$SDM_STATE"`. A then generates `SLUG` (`%Y%m%d-%H%M%S-$$`) and creates `SDM_DIR` (`mkdir -m 700`, inside a `umask 077` subshell so a sourcing caller keeps its umask). It saves 5 keys and prints `Stage state: <file> (run dir <dir>)`.
  - **Saves:** B saves CHANGED_*; E2 REMOTE_CHOICE; E3 PR_BODY_FILE; F PR_NUM/PR_URL (never a 0); G1 MERGE_STRATEGY; G2 CI_STATE; G3 MERGE_DISPATCHED at all 7 sites.
  - **Required values:** C, D, E2 and E3 need `SDM_DIR`; G2/G3 need `PR_NUM`. F has no body default.
  - **Run files** moved to `$SDM_DIR/{review,security,findings,reviewer-notes,body}.md` and `{ruff,shellcheck,auq}.json`. C prints `Stage C scanned: Ruff S n file(s), ShellCheck m file(s)`.
  - **Prose:** SKILL.md `## State between stages`; the C, D and E2 prose updated; stage-f-push.md got a Contents TOC (it grew past 100 lines).
  - **Existing tests migrated** (CL deviation): c_dispatch, d_triage, e3_body and smoke now feed `SDM_DIR` and use the new names (45 path rewrites by script). `sweep_slug_tmp` is deleted from helpers.bash because nothing writes slug-named `/tmp` files any more. In `tests/hooks/aa-ma-footer.bats:193`, D is now fed `SDM_DIR`.
  - **Checks:**
    - `extract stage-a-preflight | grep -cE …` = **3**; `grep -c '^## State between stages'` = **1**;
    - every block greps `sole-dev-merge.env` ≥1; `sdm_load` is called in the 12 non-A blocks and absent from A;
    - masking-default grep 0; `/tmp/sole-dev-merge` 0; `eval|sdm` 0;
    - shellcheck rc 0 on all 13 extracted blocks (one SC2174 `mkdir -m -p` was fixed on the way).
  - **Suites:** `bats --tap SDM` → **121 ok / 0 not-ok**. Full `bats --tap SDM tests/hooks` → **660 / 0**. `uv run pytest -q` → **3136 passed**, 0 failed.
    - The first full run had 4 failures, all from this change and all fixed at the cause: D's test input (SLUG → SDM_DIR), the 100-line TOC rule, and a `/tmp` prose mention that the plugin-surface extractor read as a dangling `/tmp` command (reworded; no golden regen).
  - **Open finding for the gate:** E2 reads `n_github`/`n_gitlab` from E1. E1 is not one of the 13 blocks and those keys are not in the 15-key allowlist, so a fresh-shell E2 ABORTs ("only github.com and gitlab.com remotes supported") unless E1 and E2 run in one call. This is outside the decided key list, so it goes to Ste at 2.3.

### Sub-step 2.3: Docs, verify, gate, merge with the fixed skill
- Status: COMPLETE
- Mode: HITL
- Dependencies: Sub-step 2.2
- Acceptance Criteria:
  - `grep -c '^\*\*Stage state file\*\*' CONTEXT.md` = 1; L-055 has a "Fixed in" line; there is 1 CHANGELOG bullet.
  - PL has the IMPACT_ANALYSIS and CRITICAL_PATH_REVIEW lines; CL has the GATE APPROVAL.
  - The Result Log quotes Stage C's scanned-files line for a PR touching `.py`/`.sh`, showing ≥ 1 file each for Ruff S and ShellCheck.
- Result Log:
  - Mode: HITL — recorded at Sub-step 3.0 on the M3 branch (L-037). Pre-rebase SHAs are cited; map them to main with `git log --format='%h %s' c3ea041..origin/main` (18 commits).
  - **Docs** (checked on main `52f4fd3`): `grep -c '^\*\*Stage state file\*\*' CONTEXT.md` = **1**; L-055 has a "Fixed in: sole-dev-merge-fixes M2" line; CHANGELOG has 1 bullet ("stage state file").
  - **Gate:** PL has IMPACT_ANALYSIS and CRITICAL_PATH_REVIEW for Milestone 2. CL has `GATE APPROVAL: Milestone 2` (7/7 pre-merge). Fence 3: `TESTS_VERIFIED passed=670`, then **672** after the C1 fix (`6ebbb39`). pytest 3136 passed. §6.8 PASS_WITH_WARNINGS; 10 distinct WARNINGs were fixed test-first (RED `38d6560`).
  - **Live run 1** (from `a589249`): A OK; B 26 files, 0 py / 0 sh; check-conventions rc 2 "no diff source" (L-051, fixed in M3); B-commit no-op. C1/C2 wrote into `<git-dir>/sdm-<slug>/`. C printed `Stage C scanned: Ruff S 0 file(s), ShellCheck 0 file(s)`. A fresh-shell D read C's findings: 0C/0H/1M/4L. The MEDIUM (`sdm_save` neither refused g/o-writable files nor set mode 600) was applied (Ste): RED `22183e3` → GREEN `fa98510`. The merge restarted.
  - **Live run 2** (from `5a7a584`): A cleared run 1's dir, state file 600. C1: 2 LOW (prose; folded into M3 at 3.0, Ste). C2 clean. D: 0/0/0/2L → reviewer notes. E1+E2 ran in one call → `REMOTE_CHOICE=github`. E3 body came from `$SDM_DIR`. F: PR #43, title fixed with a `gh api` PATCH (F truncates at 70; cosmetic). G1 `MERGE_STRATEGY=rebase`. G2 first gave `CI_STATE=failed` (Bats, `tests/hooks/codemem-post-commit.bats` sidecar race), then `green` after the test-only fix (`c189f92`, on main as `52f4fd3`).
  - **`[post-merge]` criterion:**
    - G3 printed `MERGE_DISPATCHED=1` / `Stage G3: merged 43 (strategy=rebase)`.
    - G4 printed `Stage G4: cleanup done — main at 52f4fd3` … `STATUS: OK worktree=<wt>`. Ste ran it with `!` because the isolation guard blocks `git -C <main>`.
    - Corroborated at 3.0 from the run-2 state file (backed up to `<scratch>` before the M2 worktree was removed), decoded: `MERGE_DISPATCHED=1`, `PR_NUM=43`, `MERGE_STRATEGY=rebase`, `REMOTE_CHOICE=github`.
    - Re-run at 3.0: `gh pr view 43` → `MERGED 52f4fd3`; `git ls-remote origin refs/heads/fix/sole-dev-merge-fixes-m2 | wc -c` = **0**, `--exit-code` rc **2**. The skill deleted the branch; no manual merge steps were needed. `gh pr checks 43` → 9/9 pass.
  - **Scanned-files AC:** not applicable to PR #43. Its decoded `CHANGED_PY`/`CHANGED_SH` are empty (0 `.py`, 0 `.sh`). Moved to M3 3.3 (Ste, CL 2026-10-16).

## Milestone 3: Stage B scoped commit, guard, check-conventions refs
- Status: COMPLETE
- Dependencies: Milestone 2
- Complexity: 55%
- Effort: 1 day
- Gate: HARD
- Audit-Profile: full
- Critical-Path: hook-modification
- Mode: HITL
- Acceptance Criteria:
  - In SKILL.md:
    - `grep -c -- '--from-ref' claude-code/skills/sole-dev-merge/SKILL.md` = 0;
    - `grep -c 'PRE_COMMIT_FROM_REF="\$BASE_REF"'` = 1;
    - `grep -cE 'Stage B: (pytest|pre-commit) rc='` ≥ 2;
    - `grep -c 'git add -A'` = 0.
  - `bats --tap SDM/test_stage_b_scope.bats` gives 0 not-ok with ≥ 15 @tests (AC4.1–4.4, AC5.1–5.4, Q8, guard staged, guard untracked, and the 4 existing).
  - The Result Log quotes the PR's own Stage B `check_conventions` line, and `grep -c 'no diff source'` on it = 0.
  - The privacy check gives 0 / 0.
  - PL has the IMPACT_ANALYSIS and CRITICAL_PATH_REVIEW lines for Milestone 3; CL has the GATE APPROVAL.
- Result Log:
  - Merged as PR #44 (rebase, `07a8b45`) through two live `/sole-dev-merge` runs on the branch's own blocks. SKILL.md greps `--from-ref` 0 / `PRE_COMMIT_FROM_REF="$BASE_REF"` 1 / rc lines 3 / `git add -A` 0; `test_stage_b_scope.bats` 0 not-ok; live Stage B `check_conventions … Passed`, `no diff source` 0; privacy 0/0; PL + CL lines present. Detail in 3.3.

### Sub-step 3.0: Post-merge of M2
- Status: COMPLETE
- Mode: HITL
- Dependencies: None
- Acceptance Criteria:
  - `git -C <main> status --porcelain --untracked-files=no` is empty after the L-1347 check.
  - `git merge-base --is-ancestor origin/main HEAD` exits 0 on the M3 branch.
- Result Log:
  - Mode: HITL — Ste chose "EnterWorktree now" and approved folding the LOW prose fixes in at 3.0.
  - **Handover evidence re-run** (from `<main>`, before EnterWorktree):
    - E1 `MERGED 52f4fd3`; E2 0 bytes, rc 2; E3 HEAD = origin/main = `52f4fd3`; E5 9/9 pass; E6 M2 `ACTIVE`.
    - **E4 / AC1:** `<main>` tracked changes = **0**, and `git status --porcelain` in `<main>` was empty. No L-1347 hook lines.
  - **Worktrees:**
    - M3 worktree added from `origin/main` `52f4fd3`. **AC2:** `merge-base --is-ancestor origin/main HEAD` rc **0**.
    - The upstream that `worktree add -b … origin/main` set was unset; it pointed at main.
    - M2 worktree and branch removed after cherry showed 0 `+` (branch was at `c189f92`). The run-2 evidence was backed up to `<scratch>` first.
  - **M2 closed:**
    - 2.3 Result Log written and flipped COMPLETE. The gate gave `pending_steps=0` for M2, then Milestone 2 was flipped COMPLETE (`6963551`). Provenance `MILESTONE COMPLETE — Milestone 2` is committed separately (`f8390c6`, L-018).
    - Privacy 0/0 over the AA-MA files.
  - **Docs carry-in** `4644eb7`: SKILL.md "State between stages" now says `sdm_save` refuses not-owned and g/o-writable files and creates the file 600, and that E2 is re-answered by re-running E1+E2 together.
    - SDM bats 133/0; pytest 3136 passed.
    - regen rc 0. Its only diff was the `generated … @ <sha> on <date>` header in 4 `docs/architecture` files, which was restored rather than committed (no content drift).
  - **❓ 3.0's own criteria:** no probe or prototype is required; M3 has no `Prototype-Required`.
  - **CCI note for Ste:** CCI M16's flaky post-commit test item is covered by `52f4fd3` (await_eq plus refresh.log diagnostics). Closing it is the CCI session's call.

### Sub-step 3.1: RED — Stage B tests and pre-commit stub
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 3.0
- Acceptance Criteria:
  - `test -x SDM/fixtures/bin/pre-commit` passes.
  - `grep -c 'STUB_DIR:\$PATH' SDM/test_stage_b_scope.bats` ≥ 1.
  - `git diff main -- SDM/test_stage_b_scope.bats` shows no change inside the 4 existing @test bodies.
  - RED evidence is recorded.
- Result Log:
  - Mode: AFK — auto-dispatched. RED commit `04e2fd9`, made with an explicit pathspec (L-1334); the staged set was checked first (`A pre-commit`, `M test_stage_b_scope.bats`).
  - **Stub:** `SDM/fixtures/bin/pre-commit`, as plan §4 M3. `test -x` passes; shellcheck rc 0.
  - **Setup:** setup adds `STUB_DIR`, `CLI_LOG` (outside the repo) and `export PATH="$STUB_DIR:$PATH"`, and asserts the stub is first on PATH.
    - `grep -c 'STUB_DIR:\$PATH'` = **1**.
    - Helpers: `fresh` (`env -i`), `blk`, `b_sandbox` (flags NOCFG / EMPTY / TESTSDIR) and `pc_calls`. Teardown also removes the bare origin.
    - `git diff -U0 main` hunks: setup (`+25`, `+29-34`), teardown (`+41`), helpers (`+44-77`) and the appended tests (`+228-359`). **None falls inside the 4 existing @test bodies** (old lines 37–186).
  - **Cases:** 11 new, **15 @tests** in total. A → B → B-commit run as separate fresh shells, as the skill runs them. The cases are AC5.1, AC5.2, AC5.3, AC5.4 (no config), AC5.4 (no changed files, via an empty commit), Q8, guard staged, guard untracked, AC4.1, AC4.2 and AC4.4. AC4.3 (existing cases unchanged) is a constraint, not a test (spec §5).
    - Q8 uses a **per-test** `uv` stub under `SCRIPT_DIR`, not `fixtures/bin`, so real uv is never shadowed in other suites. The case asserts the stub ran.
  - **RED evidence:** `bats --tap SDM/test_stage_b_scope.bats` gives **7 not-ok / 8 ok**. Each not-ok fails at the assertion under test, not at setup:
    - AC5.1 at the exact log line (`:237`);
    - AC5.3 at the `pre-commit rc=1` line (`:256`);
    - Q8 at the `pytest rc=3` line (`:290`);
    - guard staged at `git diff --cached --quiet -- out.txt` (`:303`; E16: `checkout --` restores from the index);
    - guard untracked at the `left unstaged: stray.txt` line (`:315`);
    - AC4.1 at `stray.txt` being in the commit (`:329`; `git add -A`);
    - AC4.4 at `status -eq 1` (`:355`; it committed instead of aborting).
  - **Passing before the fix (guards, by design):** AC5.2 (no `--from-ref`; asserts the stub ran), both AC5.4 cases (the existing condition) and AC4.2 ("as today", spec AC4.2). The 4 existing cases pass.
  - **No collateral damage:** `bats --tap SDM tests/hooks` → 676 ok + 7 not-ok = 683 (672 + 11). The only not-oks are the 7 above. `tests/test_bats_assertions.py` 2 passed. No other `STUB_DIR` suite has a `.pre-commit-config.yaml`, so the new stub cannot fire there.
  - **Plan vs spec:** spec F4.2 has B-commit recompute `CHANGED_FILES` from `BASE_REF`. Plan §4 M3 3.2 (written after M2's state file) reads it from the state file. The tests follow the plan, running A → B → B-commit in fresh shells.

### Sub-step 3.2: GREEN — Stage B steps 4-5, guard, B-commit
- Status: COMPLETE
- Mode: AFK
- Dependencies: Sub-step 3.1
- Acceptance Criteria:
  - `bats --tap SDM` gives 0 not-ok, and shellcheck on the extracted B and B-commit exits 0.
  - `scripts/regen-generated.sh` exits 0, and `git status --porcelain tests/golden docs/architecture` is empty after commit.
- Result Log:
  - Mode: AFK — auto-dispatched. GREEN commit `21c57e9` (explicit pathspec; staged set checked: `M SKILL.md`, `M tests/hooks/aa-ma-footer.bats`).
  - **Extra RED first** `c739bb8`: guard case "staged NEW out-of-scope file is unstaged, kept and listed".
    - Probe (`<scratch>/probe-restore.sh`): `git restore --source=HEAD --staged --worktree` on a staged path HEAD lacks gives **rc 0 and the file deleted**. On a `??` path it gives rc 1 with "pathspec did not match".
    - Plan §4 M3's guard line would have deleted an operator's newly staged file. The new test failed at `status = "?? newstaged.txt"`. See CL.
  - **SKILL.md, via single-match Edits:**
    - Step 4 `|| PYTEST_RC=$?` plus `Stage B: pytest rc=N (best-effort)`.
    - Step 5 `PRE_COMMIT_FROM_REF="$BASE_REF" PRE_COMMIT_TO_REF=HEAD pre-commit run --files … || PC_RC=$?` plus the rc line.
    - Guard: `??` → listed; not in HEAD → `restore --staged` only, listed; tracked → `restore --source=HEAD --staged --worktree`. Each failure prints a line.
    - B-commit: `INTENDED` = CHANGED_FILES ∩ dirty, then `git add -- …` and the staged-set assert (`git reset -q`, `ABORT: …`, exit 1). Out-of-scope dirt is listed.
    - Prose says what each check sees. The exit-status table gains the B-commit ABORT row, and the contract reads "(Stages A, B-commit, E2, F)".
  - **Milestone greps:** `--from-ref` **0**; `PRE_COMMIT_FROM_REF="\$BASE_REF"` **1**; `Stage B: (pytest|pre-commit) rc=` **3**; `git add -A` **0**. `test_stage_b_scope.bats` has **16** @tests.
  - **AC1:** `bats --tap SDM tests/hooks` → **684 ok / 0 not-ok** (672 + 12). `test_stage_b_scope.bats` 16/16. shellcheck rc **0** on the extracted `stage-b-scope` and `stage-b-commit`.
  - **AC2:** regen rc **0**. Its only diff was the `generated … @ <sha> on <date>` header in 4 `docs/architecture` files (non-header diff lines = 0), which was restored. `tests/golden` was unchanged. After commit, `git status --porcelain tests/golden docs/architecture` gives **0** lines.
  - **pytest:** the first run had **1 failure**: `tests/test_prompt_size.py` "SKILL.md: 506 lines > cap 500". The new prose was tightened, not moved, and SKILL.md is now **495**. Re-run: **3136 passed**.
  - **Mutations (L-045), each reverted:**
    - guard's not-in-HEAD branch → full restore: the staged-NEW test FAILs at `cat newstaged.txt` (deleted);
    - staged-set assert disabled: AC4.4 FAILs at `status -eq 1`.
  - **Impact deviation:** `tests/hooks/aa-ma-footer.bats` (2 B-commit footer tests) now pass `CHANGED_FILES=f.txt`. B-commit stages only Stage B's files, and those tests run it alone. Checked empirically: without the input, the `[ad-hoc]` test FAILs because no commit is made. `commit-signature.bats:228` (literal `FOOTER=$(emit_aa_ma_footer)` / `-m "…${FOOTER}"`) is untouched and passes.

### Sub-step 3.3: Docs, verify, gate, merge with the fixed skill
- Status: COMPLETE
- Mode: HITL
- Dependencies: Sub-step 3.2
- Acceptance Criteria:
  - `grep -c 'the skill now sets the refs' docs/adr/0018-touched-code-lint-gate.md` = 1.
  - L-051 and L-053 have "Fixed in" lines, and there is 1 CHANGELOG bullet.
  - PL has `IMPACT_ANALYSIS — Milestone 3:` and `CRITICAL_PATH_REVIEW — Milestone 3:`; CL has `GATE APPROVAL: Milestone 3`. The live Stage B line is quoted (milestone AC 3).
  - (Moved from M2 2.3, Ste.) If the M3 PR changes any `.py` or `.sh` file, the Result Log quotes the live `Stage C scanned: Ruff S n file(s), ShellCheck m file(s)` line with n or m ≥ 1. If it changes neither, this carries to the next PR that does.
- Result Log:
  - Mode: HITL — recorded at Sub-step 4.0 on the M4 branch (L-037). PR #44 was rebase-merged (22 commits, `52f4fd3..07a8b45`), so pre-rebase SHAs are cited; map them by subject with `git log --format='%h %s' 52f4fd3..origin/main`.
  - **Docs** (checked on the M4 branch at `07a8b45`): `grep -c 'the skill now sets the refs' docs/adr/0018-touched-code-lint-gate.md` = **1**; L-051 and L-053 each have **1** "Fixed in" line; CHANGELOG has the Stage B bullet (`/sole-dev-merge` Stage B: check-conventions exited 2 …).
  - **Gate:** PL has `IMPACT_ANALYSIS — Milestone 3: HIGH=0 unresolved` (+ addendum after §6.8) and `CRITICAL_PATH_REVIEW — Milestone 3:`. CL has `GATE APPROVAL: Milestone 3` (7/7 pre-merge). Fence 3: `TESTS_VERIFIED passed=684`, then 692 after the §6.8 remediation, then **694** at `bc2b9d5`. pytest 3136 passed. §6.8 PASS_WITH_WARNINGS, 0C/6W/12I; all 6 WARNINGs fixed test-first (RED `6b9212d` → GREEN `10845fe`). Fence 2 n/a. Fence 1 was BLOCKED pre-merge by design (3.3 is the merge step) and is re-run at 4.0.
  - **Live run 1** (from `6e952f6`): A OK. **B: `check_conventions (added lines only)…Passed`; `grep -c 'no diff source'` = 0.** `Stage B: pytest rc=0 (best-effort)`, `Stage B: pre-commit rc=0 (best-effort)`, guard clean. B-commit no-op. C: `Ruff S 0 file(s), ShellCheck 0 file(s)`. D: 0C/0H/**1M**/6L. The MEDIUM (B-commit `${CHANGED_FILES:-}` masking default, L-055) was applied (Ste) with LOW `--no-renames` in `staged_outside`: RED `d9c43be` → GREEN `bc2b9d5`. The merge restarted.
  - **Live run 2** (from `1a122b7`): A OK (22 ahead). **B: `check_conventions … Passed`; `no diff source` 0**; pytest rc 0, pre-commit rc 0, guard clean. B-commit no-op. C: Ruff S 0 / ShellCheck 0. D: 0C/0H/0M/6L → reviewer notes. E1+E2 in one call → `REMOTE_CHOICE=github`; E0 OK; E3 body 44 lines, privacy 0/0. F: PR #44; title fixed with `gh api -X PATCH …/pulls/44 -f title=…` (cosmetic, as M2). G1 `MERGE_STRATEGY=rebase`; G2 `CI_STATE=green` (9/9).
  - **`[post-merge]`:** G3 `MERGE_DISPATCHED=1` / `Stage G3: merged 44 (strategy=rebase)`. G4 (Ste, `!`): `Stage G4: cleanup done — main at 07a8b45 worktree=<wt>` … `STATUS: OK worktree=<wt>`. Decoded state file: `PR_NUM=44 MERGE_STRATEGY=rebase REMOTE_CHOICE=github MERGE_DISPATCHED=1`. No manual merge steps.
  - **Re-run at 4.0** (from `<main>`): `gh pr view 44` → `MERGED 07a8b45`; `git ls-remote origin refs/heads/fix/sole-dev-merge-fixes-m3 | wc -c` = **0**, `--exit-code` rc **2**; `<main>` HEAD = origin/main = `07a8b45`; `<main>` tracked changes **0**; `git cherry origin/main fix/sole-dev-merge-fixes-m3` = 22 `-`, **0 `+`**, then the M3 worktree and branch were removed (rc 0, branch was `1a122b7`).
  - **Scanned-files AC:** N/A — PR #44 changed no `.py`/`.sh`. Carries to the next PR that does, by the AC's own wording.

## Milestone 4: Stage F REST body update, small fixes, docs drift
- Status: PENDING
- Dependencies: Milestone 3
- Complexity: 40%
- Effort: 0.75 day
- Gate: HARD
- Audit-Profile: full
- Critical-Path: hook-modification
- Mode: HITL
- Acceptance Criteria:
  - `extract stage-f-push references/stage-f-push.md | grep -c 'gh pr edit'` = 0.
  - An @test asserts `STATUS: PR_BODY_NOT_UPDATED` with rc 0 on a read-back mismatch.
  - An @test shows a stale `body.md` from another run's `SDM_DIR` is not posted, and an @test shows Stage A aborts when `DEFAULT_BRANCH=trunk` and HEAD is on `trunk`.
  - `comm -23 <(grep -rhoE '(STATUS|ABORT): [A-Z_]+' claude-code/skills/sole-dev-merge/references claude-code/skills/sole-dev-merge/SKILL.md | sort -u) <(<SKILL.md status-table rows> | sort -u)` is empty.
  - ADR-0008 `:99-122` names the same markers as `grep -rhoE '=== stage-[a-z0-9-]+' claude-code/skills/sole-dev-merge/`.
  - `bats --tap SDM` gives 0 not-ok, and the TODOS F entry (`:81-86`) sits under `## Completed` with a `**Done:**` line.
  - PL has `IMPACT_ANALYSIS — Milestone 4: HIGH=0 unresolved` and `CRITICAL_PATH_REVIEW — Milestone 4:`; CL has `GATE APPROVAL: Milestone 4` with `Decision: APPROVED`.
  - The privacy check gives 0 / 0.
- Result Log:

### Sub-step 4.0: Post-merge of M3, and live gh api probe
- Status: PENDING
- Mode: HITL
- Dependencies: None
- Acceptance Criteria:
  - The main checkout is clean and the M4 branch is cut from fresh main (`--is-ancestor` exits 0).
  - On this PR, the rc of `cmp body.md <(gh api repos/{owner}/{repo}/pulls/N --jq .body)` is recorded after the PATCH.
  - CL has `DECISION gh-api body: -F|--input, newline=<rule> — Ste`.
- Result Log:

### Sub-step 4.1: RED — Stage F/A/E3 tests
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 4.0
- Acceptance Criteria:
  - There are 5 new @tests: F existing-PR PATCH plus read-back; F mismatch → STATUS; F no-PR path unchanged (`:118-128`); A `trunk` abort; E3 per-SLUG body path.
  - The gh stub's `api)` arm branches on `-X PATCH` and `--jq .body` **before** its G1 default (`fixtures/bin/gh:74-80`).
  - RED evidence is recorded.
- Result Log:

### Sub-step 4.2: GREEN — Stage F, A, E3, prose, status table, ADR-0008
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 4.1
- Acceptance Criteria:
  - The status table has the 7 new rows: MERGE_FAILED, BRANCH_NOT_DELETED, MAIN_CHECKOUT_DIRTY, MAIN_NOT_UPDATED, REMOTE_UNKNOWN, PR_BODY_NOT_UPDATED, and the B-commit ABORT. It also has the G3/G4 ABORT rows (rc 1, since M1 §6.8), the exit-contract line (`SKILL.md` "non-zero only for A, E2, F") widened to G3/G4, and the `STATUS: OK` row reworded (in a worktree the local branch is left for the operator). The `comm` check (milestone AC 4) is empty.
  - `bats --tap SDM` gives 0 not-ok; shellcheck exits 0 on F, A and E3.
  - `scripts/regen-generated.sh` leaves no uncommitted diff.
  - (Added at M2 2.3, Ste.) E1 saves `n_github`/`n_gitlab`/`n_other` to the stage state file (allowlist 15 → 18 keys). An empty-env E2 case in `test_stage_state.bats` passes. The E1/E2 "one Bash call" prose line and its TODOS entry are removed.
- Result Log:

### Sub-step 4.3: Verify, gate, merge with the fixed skill
- Status: PENDING
- Mode: HITL
- Dependencies: Sub-step 4.2
- Acceptance Criteria:
  - PL has `IMPACT_ANALYSIS — Milestone 4:` and `CRITICAL_PATH_REVIEW — Milestone 4:`; CL has `GATE APPROVAL: Milestone 4`.
  - The Result Log quotes this PR's live Stage F read-back: a match, or the STATUS line.
- Result Log:

## Milestone 5: pre-compact writes into the worktree
- Status: PENDING
- Dependencies: Milestone 4
- Complexity: 65%
- Effort: 1 day
- Gate: HARD
- Audit-Profile: full
- Critical-Path: hook-modification
- Prototype-Required: YES
- Mode: HITL
- Acceptance Criteria:
  - A new @test shows `aa_ma_list_active_tasks "$T"` lists `$T/.claude/dev/active/*`, and the 5 existing list_active_tasks @tests pass (`bats --tap tests/hooks/aa-ma-parse.bats` gives 0 not-ok).
  - `bats --tap tests/hooks/pre-compact.bats` gives 0 not-ok with ≥ 24 @tests: the 17 after M1 (13 + 4 symlink cases from 1.8), cases (i)–(iii), the 3 fail-open paths, and the stdin-cwd validation case.
  - Case (ii) asserts:
    - `git -C "$MAIN" status --porcelain` is empty;
    - the snapshot file exists under the cache dir;
    - `jq -e .systemMessage` on stdout exits 0.
  - `[post-merge]` (recorded at 5.5) Live: the Result Log pastes the redacted systemMessage text from a real compaction in a worktree session, shows `git -C <main> status --porcelain --untracked-files=no` empty, and greps the CHECKPOINT line in the worktree's PL.
  - An @test with a stdin `cwd` that is relative or nonexistent shows the hook falls back to `pwd` and does not run `git -C` on it.
  - The privacy check gives 0 / 0.
  - The milestone's PROTOTYPE, IMPACT_ANALYSIS, CRITICAL_PATH_REVIEW and GATE APPROVAL lines are present.
- Result Log:

### Sub-step 5.0: Post-merge of M4, and PreCompact probe
- Status: PENDING
- Mode: HITL
- Dependencies: None
- Prototype-Required: YES
- Acceptance Criteria:
  - The M5 branch is cut from fresh main (`--is-ancestor` exits 0).
  - CL holds a 3-row table, (a) `cd` with MAINTAIN=1 / (b) MAINTAIN=0 / (c) EnterWorktree, with columns `pwd`, `.cwd`, `CLAUDE_PROJECT_DIR`. Ste ran `/compact` in each.
  - After removal, `jq '.hooks.PreCompact // null' <scratch>/.claude/settings.json` prints `null`.
  - PL has `PROTOTYPE — Milestone 5: pre-compact writes into the worktree — <verdict>`.
- Result Log:

### Sub-step 5.1: Design decision
- Status: PENDING
- Mode: HITL
- Dependencies: Sub-step 5.0
- Acceptance Criteria:
  - CL has `DECISION L-1347 design: A+C | MAINTAIN=0+A — approved by Ste`.
- Result Log:

### Sub-step 5.2: RED — parse and pre-compact tests
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 5.1
- Acceptance Criteria:
  - `grep -c '^@test' tests/hooks/pre-compact.bats` ≥ 24.
  - The cases use `payload PreCompact '.cwd = …'`, and the existing 16 no-stdin tests are unchanged.
  - RED evidence is recorded.
- Result Log:

### Sub-step 5.3: GREEN — helper root argument and pre-compact guard
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 5.2
- Acceptance Criteria:
  - `grep -c '\${1:-\$PWD}' claude-code/hooks/lib/aa-ma-parse.sh` = 1.
  - `grep -c 'timeout 2 cat' claude-code/hooks/pre-compact-aa-ma.sh` = 1.
  - `bats --tap tests/hooks` gives 0 not-ok, and shellcheck exits 0 on both files.
- Result Log:

### Sub-step 5.4: Verify, gate, merge, live compaction check
- Status: PENDING
- Mode: HITL
- Dependencies: Sub-step 5.3
- Acceptance Criteria:
  - The PR is merged by the fixed skill, with the PR number in the Result Log.
  - The PR merge is recorded. The live compaction evidence (`[post-merge]`) moves to 5.5.
  - The global L-1347 has a "Fixed in" line (`grep -c 'Fixed in' ~/.claude/docs/lessons.md` grows by 1).
  - A forge TODO for the DRY merge-base reuse with CCI's `aa_ma_milestone_base` exists, and there is 1 CHANGELOG bullet.
- Result Log:

### Sub-step 5.5: Finalize and archive
- Status: PENDING
- Mode: HITL
- Dependencies: Sub-step 5.4
- Acceptance Criteria:
  - The M5 `[post-merge]` live compaction evidence is recorded, and Milestone 5 flips to COMPLETE.
  - `test -d .claude/dev/completed/sole-dev-merge-fixes` passes, and `! test -d .claude/dev/active/sole-dev-merge-fixes` passes.
  - CL has a FINALIZATION entry approved by Ste.
- Result Log:
