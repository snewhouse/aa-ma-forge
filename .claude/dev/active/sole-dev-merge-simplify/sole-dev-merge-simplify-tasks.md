# sole-dev-merge-simplify Tasks (HTP)

_Hierarchical Task Planning roadmap with dependencies and state tracking. PL = provenance.log, CL = context-log.md (this dir)._

## Milestone 1: sdm.sh beside the old skill, proven live
- Status: PENDING
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

### Sub-step 1.0: Prototype + deferred work
- Status: PENDING
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

### Sub-step 1.1: RED — fixtures and tests
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 1.0
- Acceptance Criteria:
  - New fixtures `tests/commands/sdm/fixtures/{bin/gh,bin/pre-commit,helpers.bash}` (check-runs arm from `GH_CHECK_RUNS`, G1 rc control, `pr checks` rows, GraphQL-error arm, field-order-free `pr view`); old fixtures untouched.
  - The 102 KEEP/CHANGE tests ported to `tests/commands/sdm/{check,ship,finish}.bats` per the inventory's per-test map, plus the 13 new tests in plan §5 1.1; each open TODO from 1.0 is a test or named as carried.
  - `bats --count tests/commands/sdm` = N, recorded here; N = 102 + the new tests ≥ 115.
  - A RED log here lists each new test with its failure line.
  - The RED commit precedes any GREEN.
- Result Log:

### Sub-step 1.2: GREEN — complete sdm.sh
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 1.1
- Acceptance Criteria:
  - `bats --formatter pretty tests/commands/sdm` prints `N tests, 0 failures` (N from 1.1).
  - `pre-commit run --files claude-code/skills/sole-dev-merge/scripts/sdm.sh $(find tests/commands/sdm -type f)` passes.
  - `git ls-files -s` shows mode 100755 for sdm.sh.
  - `wc -l sdm.sh` ≤ 400.
  - `grep -c '^sdm_footer()' sdm.sh` = 1.
  - `grep -nE '^[^#]*\b(glab|SDM_STATE|pytest|mypy)\b|^[^#]*(--select S|shellcheck )' sdm.sh` gives 0.
  - `bats --formatter pretty tests/commands/sole-dev-merge` prints `199 tests, 0 failures`, and `git diff origin/main -- claude-code/skills/sole-dev-merge/SKILL.md claude-code/skills/sole-dev-merge/references` is empty.
  - `scripts/regen-generated.sh` leaves `git diff --exit-code` clean (a changed plugin-surface golden is committed here).
  - `uv run pytest` passes.
- Result Log:

### Sub-step 1.3: CI runs the new suite
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 1.2
- Acceptance Criteria:
  - `grep -c 'tests/commands/sdm' .github/workflows/security.yml` ≥ 1.
  - The PR's `Bats` check passing with the new count in its log is observed at 1.4, after `ship` pushes.
- Result Log:

### Sub-step 1.4: Verify, gate, merge by the new script
- Status: PENDING
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

---

## Milestone 2: switch over and delete
- Status: PENDING
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
- Status: PENDING
- Mode: HITL
- Dependencies: None
- Acceptance Criteria:
  - reference.md has a SHA map: the PR's commit subjects (`gh pr view <n> --json commits`) matched against `git log` of the merged range on origin/main.
  - `uv run aa-ma-gate sole-dev-merge-simplify-tasks.md --milestone 1 --format kv` shows `pending_steps=0`.
  - CL has `GATE APPROVAL: Milestone 1`.
  - Recorded on the M2 branch `refactor/sdm-switch-over` (L-037).
- Result Log:

### Sub-step 2.1: (merged into 2.2)
- Status: SKIPPED — folded into 2.2
- Mode: AFK
- Dependencies: Sub-step 2.0
- Acceptance Criteria:
  - None: the number is kept so step IDs stay stable; the work is in 2.2.
- Result Log:

### Sub-step 2.2: The switch, as one commit
- Status: PENDING
- Mode: AFK
- Dependencies: Sub-step 2.0
- Acceptance Criteria:
  - Hook tests: `tests/hooks/aa-ma-footer.bats:167-206` — 2 B-commit footer tests re-pointed at `sdm_footer` (source sdm.sh), the D-block run and "snippets byte-identical" tests dropped; `tests/hooks/commit-signature.bats:228-240` — 2 block-shape tests dropped (156-226 stay).
  - `disable-model-invocation: true` is kept.
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
