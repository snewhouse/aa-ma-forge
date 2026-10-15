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
- Status: ACTIVE
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
- Status: PENDING
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

### Sub-step 1.2: GREEN — G3 implementation
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 1.1
- Acceptance Criteria:
  - `bats --tap SDM/test_stage_g_merge.bats` gives 0 not-ok, including the existing G3 tests named for timeout, failed, gitlab green, gitlab timeout and unknown CI state (matched by @test name, not line).
  - `extract stage-g3-merge … | shellcheck --enable=check-set-e-suppressed -` exits 0.
  - `extract stage-g3-merge … | awk '/2>\/dev\/null|\|\| true/ && !/# why:/ && prev !~ /# why:/ {n++} {prev=$0} END{print n+0}'` = 0. check-conventions skips `.md`, so this awk is the check.
  - SKILL.md `:13` no longer says `--delete-branch`.
- Result Log:

### Sub-step 1.3: RED — G4 worktree tests
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 1.2
- Acceptance Criteria:
  - `grep -c '_sandbox_worktree()' SDM/test_stage_g_merge.bats` = 1.
  - There are @tests for AC2.2, AC2.2b, AC2.3, AC2.3b, AC2.4, AC2.5 and AC2.6 (`grep -cE '@test "G4: AC2\.(2|2b|3|3b|4|5|6) '` = 7), and at least one uses branch `feature/x`.
  - The AC2.2 test asserts `git -C "$MAIN" rev-parse HEAD` = `git --git-dir="$BARE_REMOTE" rev-parse main`, and that the worktree's `branch --show-current` is unchanged.
  - RED evidence is recorded. AC2.4 (subdirectory) is expected to pass as a guard.
- Result Log:

### Sub-step 1.4: GREEN — G4 implementation
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 1.3
- Acceptance Criteria:
  - `extract stage-g4-cleanup … | grep -cE '\bgit (-C \S+ )?pull\b'` = 0.
  - In worktree mode the `else` branch contains no `checkout` (`awk '/^else/,/^fi/' | grep -c checkout` = 0).
  - `grep -c 'ORIGINAL_BRANCH:-feature'` = 0.
  - The branch-delete line has no `2>/dev/null || true`.
  - `bats --tap SDM/test_stage_g_merge.bats` gives 0 not-ok; shellcheck on the extracted G4 exits 0.
- Result Log:

### Sub-step 1.5: RED — footer helper tests
- Status: PENDING
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

### Sub-step 1.6: GREEN — footer helper and skill resolution chain
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 1.5
- Acceptance Criteria:
  - `grep -c 'merge-base' claude-code/hooks/lib/aa-ma-footer.sh` ≥ 1.
  - `grep -c 'CLAUDE_HOME:-\$HOME/.claude'` = 1 and `grep -c 'footer-resolve:begin'` = 1, in both SKILL.md and stage-d-triage.md (today both are 0).
  - The two `footer-resolve` snippets are byte-identical (an @test in aa-ma-footer.bats).
  - `bats --tap tests/hooks/aa-ma-footer.bats SDM/test_stage_b_scope.bats SDM/test_stage_d_triage.bats SDM/test_smoke_e2e.bats` gives 0 not-ok.
  - `shellcheck claude-code/hooks/lib/aa-ma-footer.sh` exits 0.
- Result Log:

### Sub-step 1.7: RED/GREEN — commit-signature trusts emit_aa_ma_footer
- Status: PENDING
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

### Sub-step 1.8: RED/GREEN — pre-compact never follows a symlink
- Status: PENDING
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

### Sub-step 1.9: RED/GREEN — install link for the footer helper
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 1.8
- Acceptance Criteria:
  - A new @test in `tests/hooks/install_dry_run.bats` asserts the dry run lists `hooks/lib/aa-ma-footer.sh`. RED evidence is recorded; then 0 not-ok.
  - `grep -c 'aa-ma-footer.sh' scripts/install.sh` ≥ 1.
  - `scripts/uninstall.sh` removes the link: either a dry-run assertion, or a grep showing generic `hooks/lib` handling (whichever applies, recorded in the Result Log).
- Result Log:

### Sub-step 1.10: Docs and lessons
- Status: PENDING
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

### Sub-step 1.11: Verify, impact, gate
- Status: PENDING
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

### Sub-step 1.12: PR, bootstrap merge, post-merge checks
- Status: PENDING
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

## Milestone 2: Stage state file
- Status: PENDING
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

### Sub-step 2.0: Post-merge of M1, and prototype the state file
- Status: PENDING
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

### Sub-step 2.1: RED — state tests
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 2.0
- Acceptance Criteria:
  - `test -f SDM/test_stage_state.bats` passes, and it has ≥ 16 @tests.
  - `grep -c 'sole-dev-merge.env' SDM/test_smoke_e2e.bats` ≥ 1.
  - RED evidence is recorded.
- Result Log:

### Sub-step 2.2: GREEN — loader and saver in every block
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 2.1
- Acceptance Criteria:
  - The loader is in the 12 non-A blocks, and Stage A has `rm -f`, `umask 077` and `mkdir -m 700` (`extract stage-a-preflight | grep -cE 'rm -f .*SDM_STATE|umask 077|mkdir -m 700'` = 3). `grep -c '^## State between stages' SKILL.md` = 1.
  - `bats --tap SDM` gives 0 not-ok, and shellcheck exits 0 on all 13 extracted blocks.
- Result Log:

### Sub-step 2.3: Docs, verify, gate, merge with the fixed skill
- Status: PENDING
- Mode: HITL
- Dependencies: Sub-step 2.2
- Acceptance Criteria:
  - `grep -c '^\*\*Stage state file\*\*' CONTEXT.md` = 1; L-055 has a "Fixed in" line; there is 1 CHANGELOG bullet.
  - PL has the IMPACT_ANALYSIS and CRITICAL_PATH_REVIEW lines; CL has the GATE APPROVAL.
  - The Result Log quotes Stage C's scanned-files line for a PR touching `.py`/`.sh`, showing ≥ 1 file each for Ruff S and ShellCheck.
- Result Log:

## Milestone 3: Stage B scoped commit, guard, check-conventions refs
- Status: PENDING
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

### Sub-step 3.0: Post-merge of M2
- Status: PENDING
- Mode: HITL
- Dependencies: None
- Acceptance Criteria:
  - `git -C <main> status --porcelain --untracked-files=no` is empty after the L-1347 check.
  - `git merge-base --is-ancestor origin/main HEAD` exits 0 on the M3 branch.
- Result Log:

### Sub-step 3.1: RED — Stage B tests and pre-commit stub
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 3.0
- Acceptance Criteria:
  - `test -x SDM/fixtures/bin/pre-commit` passes.
  - `grep -c 'STUB_DIR:\$PATH' SDM/test_stage_b_scope.bats` ≥ 1.
  - `git diff main -- SDM/test_stage_b_scope.bats` shows no change inside the 4 existing @test bodies.
  - RED evidence is recorded.
- Result Log:

### Sub-step 3.2: GREEN — Stage B steps 4-5, guard, B-commit
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 3.1
- Acceptance Criteria:
  - `bats --tap SDM` gives 0 not-ok, and shellcheck on the extracted B and B-commit exits 0.
  - `scripts/regen-generated.sh` exits 0, and `git status --porcelain tests/golden docs/architecture` is empty after commit.
- Result Log:

### Sub-step 3.3: Docs, verify, gate, merge with the fixed skill
- Status: PENDING
- Mode: HITL
- Dependencies: Sub-step 3.2
- Acceptance Criteria:
  - `grep -c 'the skill now sets the refs' docs/adr/0018-touched-code-lint-gate.md` = 1.
  - L-051 and L-053 have "Fixed in" lines, and there is 1 CHANGELOG bullet.
  - PL has `IMPACT_ANALYSIS — Milestone 3:` and `CRITICAL_PATH_REVIEW — Milestone 3:`; CL has `GATE APPROVAL: Milestone 3`. The live Stage B line is quoted (milestone AC 3).
- Result Log:

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
  - The status table has the 7 new rows: MERGE_FAILED, BRANCH_NOT_DELETED, MAIN_CHECKOUT_DIRTY, MAIN_NOT_UPDATED, REMOTE_UNKNOWN, PR_BODY_NOT_UPDATED, and the B-commit ABORT. The `comm` check (milestone AC 4) is empty.
  - `bats --tap SDM` gives 0 not-ok; shellcheck exits 0 on F, A and E3.
  - `scripts/regen-generated.sh` leaves no uncommitted diff.
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
