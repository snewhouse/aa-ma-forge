# sole-dev-merge-simplify Reference

Test-Command: bats --formatter pretty -r tests
Test-Command-Pass-Regex: ^([0-9]+) tests, 0 failures
Architecture View: see plan.md §13

## Immutable Facts and Constants

_Non-negotiable facts from plan §3/§4/§6 and the two research files. All [valid: 2026-10-20] unless marked._

### Research files
docs/research/sole-dev-merge-simplify-gh-cli-merge-contract.md — gh 2.46 merge contract (Valid-Through: until gh leaves 2.46.0)
docs/research/sole-dev-merge-simplify-behaviour-inventory.md — v2 skill behaviour and per-test map (Valid-Through: until M2 deletes the stage blocks)

### Tool versions and repo settings (probed at `04d2490`)
- gh 2.46.0 (`/usr/bin/gh`); git 2.53.0; bats 1.13 (prints `N tests, 0 failures`).
- origin is github.com, repo `snewhouse/aa-ma-forge`.
- `main`: `protected:false`, branch rules `[]`, `allow_auto_merge:false`, `allow_rebase_merge:true`, `delete_branch_on_merge:false`.
- `security.yml` is the only workflow; triggers on pull_request; 9 jobs, all check-runs (no commit statuses).
- `install.sh:316-322` links whole skill dirs: only `claude-code/skills/sole-dev-merge/scripts/` gets installed.
- `claude-code/hooks/lib/aa-ma-footer.sh` is self-contained; install.sh links it into `~/.claude/hooks/lib/`.

### gh 2.46 contract
- gh exit codes: 0 OK, 1 error, 2 cancel, 4 auth, 8 pending; `timeout` gives 124 (137 on SIGKILL).
- `gh pr checks` exits 1 for "no checks reported" (same as a failure); `--watch` does not wait for checks to appear.
- A cancelled check exits 0 (non-TTY row still prints `fail`).
- `gh pr merge` does not check CI and merges an UNSTABLE PR immediately; success is silent under non-TTY.
- `--match-head-commit` is GraphQL `expectedHeadOid`: a mismatch gives exit 1 with `GraphQL:` on stderr.
- `--delete-branch` fails from a linked worktree, after the merge (remote branch survives).
- `gh pr create --head` never pushes; prints only the URL on stdout; an existing OPEN PR → exit 1, URL on stderr.
- `gh pr edit` fails (projectCards); set the body with `gh api -X PATCH repos/{o}/{r}/pulls/N -F body=@file`.
- No `pr checks --json` in 2.46. The combined `/status` endpoint says "pending" with 0 statuses: never used.
- `git push origin --delete <absent>` exits 1 like a real failure; probe with `git ls-remote --exit-code origin refs/heads/<b>` (0 present, 2 absent, else error). `--heads` pattern `<b>` also matches `*/<b>`.
- Not used: `gh pr merge --auto` (with no protection it merges at once, without CI).

### sdm.sh CLI contract (M1 Contract, verbatim)
```
CLI (sdm.sh, bash, set -euo pipefail; sourceable: main runs only when "${BASH_SOURCE[0]}" == "$0"):
  sdm.sh check                    # A + B + B-commit. 0 = "check OK (branch=<b>, base=<ref>, ahead=<n>)"; 1 = ABORT: <reason>
                                  # dirt outside the branch: "ABORT: check: files outside the branch changed: <list> (left as they are)"
                                  # pre-commit stays best-effort: prints "check: pre-commit rc=<n>" and goes on
  sdm.sh ship [--notes FILE]      # origin on github.com, gh auth, body, push, PR create or REST update + read-back, G1, G2.
                                  # prints three lines PR_NUM=<n>, PR_URL=<u>, CI_STATE=green|failed|timeout; STATUS lines exit 0; ABORT exit 1
                                  # body in a mktemp file removed by an EXIT trap; PATCH with `gh api -F body=@file`, read-back trims trailing newlines
                                  # repo slug from origin's URL, passed as -R/explicit path; origin not on github.com -> ABORT naming the host only (never the URL)
                                  # the PR is used only if OPEN, isCrossRepository=false and headRefOid == local HEAD; decide on gh's rc, never on stdout
                                  # `pr checks --watch` output goes to /dev/null; only the three lines reach stdout
  sdm.sh finish <PR_NUM>          # PR_NUM must match ^[1-9][0-9]*$ before any gh argv; SHA=$(git rev-parse HEAD), used for check-runs and --match-head-commit;
                                  # one lookup: headRefName == current branch (not the default; check-ref-format), isCrossRepository=false, state OPEN, headRefOid == SHA;
                                  # strategy re-read from allow_rebase_merge: only literal true/false; null or an API failure ABORTs;
                                  # check-runs at SHA: total_count == runs read (else ABORT), all completed, >=1 success, all in success|skipped|neutral,
                                  #   else STATUS: CI_NOT_DONE / CI_FAILED;
                                  # merge --<strategy> --match-head-commit "$SHA"; re-read state, MERGED required before any delete;
                                  # push origin :refs/heads/<b> (rc captured, not acted on); ls-remote --exit-code decides: 2 gone, 0 BRANCH_NOT_DELETED, else error; G4
                                  # exit: 0 = STATUS lines, 1 = ABORT
  sdm.sh help                     # usage + the exit-status table
Functions: sdm_footer (the one footer resolver: AA_MA_FOOTER_HELPER, repo copy, ~/.claude link, else [ad-hoc])
Env (operator, trusted; validated only where a bad value hangs): CI_POLL_TIMEOUT (900s), CI_APPEAR_TIMEOUT_S (120), CI_APPEAR_INTERVAL_S (10), AA_MA_FOOTER_HELPER, AA_MA_PLAN_DIR
Kept STATUS/ABORT texts: the inventory's KEEP strings, verbatim, except that a "Stage F:"/"Stage G2:"/"Stage G3:"/"Stage G4:" prefix becomes "ship:"/"finish:"; "Cannot run /sole-dev-merge from <b> branch" is unchanged.
Exit table: in sdm.sh between the comment lines "# exit-table:begin" and "# exit-table:end", one "STATUS-or-ABORT text | meaning" row per line; `sdm.sh help` prints it.
```
- Check-runs endpoint (fixture arm): `repos/{o}/{r}/commits/<sha>/check-runs?filter=latest&per_page=100`; fixture env `GH_CHECK_RUNS` (one `status conclusion` pair per line).
- G2 watch: `timeout $CI_POLL_TIMEOUT gh pr checks N --watch --interval 30 --fail-fast`; `timeout 30` per appear-wait look.
- CI_TIMEOUT hint: `sdm.sh finish <n>` once CI completes, never `gh pr merge --auto`.

### Constants and limits
- sdm.sh ≤ 400 lines (design audit sized it at 150–200); SKILL.md ≤ 150 lines (M2), ≤ 500 hard limit (`tests/test_prompt_size.py`); no SKILL.md fenced block > 3 lines.
- Old skill: 1,994 lines, 77% bash; 1,541 bash lines, ~62% DROP; old prose 317 lines.
- Tests: 199 old; 102 to port (79 KEEP + 23 CHANGE), 97 drop; new suite N ≥ 115.
- Merge runs: stop rule, at most 2 review rounds; target 1 merge run per milestone.
- PR title cut to 70 chars.
- 7 moot TODOS entries closed at 1.0: 25, 81, 88, 96, 104, 119, 157; still apply: 123, 182, 186, 196, 200, 354.

### File paths
- Create (M1): `claude-code/skills/sole-dev-merge/scripts/sdm.sh` (mode 100755); `tests/commands/sdm/{check,ship,finish}.bats`; `tests/commands/sdm/fixtures/{bin/gh,bin/pre-commit,helpers.bash}`.
- Modify (M1): `.github/workflows/security.yml`; `TODOS.md`; `tests/golden/plugin-surface.json`, `docs/architecture/plugin-surface.md` (only via `scripts/regen-generated.sh`).
- Modify (M2): `claude-code/skills/sole-dev-merge/SKILL.md`; `tests/hooks/aa-ma-footer.bats:167-206`; `tests/hooks/commit-signature.bats:228-240`; `.github/workflows/security.yml` (comments 145-158, "60+"); `claude-code/hooks/aa-ma-commit-signature.sh:149-153` (rule-8 comment, keeps `/sole-dev-merge`).
- Delete (M2): `claude-code/skills/sole-dev-merge/references/{stage-c-review-and-security,stage-d-triage,stage-e-remote-and-body,stage-f-push,stage-g-merge,stage-state}.md`; `tests/commands/sole-dev-merge/` (11 bats files + fixtures, glab, extract_stage.sh).
- Create (M2): `docs/adr/0024-sole-dev-merge-one-script.md`.
- Modify (M2 docs): `docs/adr/0008-sole-dev-merge-pr-workflow.md`, `docs/adr/0022-secops-baseline.md`, `docs/adr/0018-touched-code-lint-gate.md`, `docs/adr/INDEX.md`, `CONTEXT.md`, `README.md:226`, `docs/spec/claude-code-foundations.md:91`, `docs/spec/aa-ma-quick-reference.md:156-157`, `CHANGELOG.md`, `TODOS.md`, `docs/lessons.md`; comments only in `claude-code/hooks/lib/aa-ma-footer.sh:4-5`, `scripts/install.sh:385`, `src/aa_ma/analysis/measure.py:5`.
- Constraint tests: `tests/skills/test_model_invocation_list.py`, `tests/test_prompt_size.py`, `tests/skills/test_skill_links_resolve.py`, `tests/codemem/test_plugin_surface.py:94-106`.
- Frozen (keep old strings): `tests/fixtures/draw-node-ids.json`, `tests/fixtures/draw-prototype-graph.json`.
- Input retro: `.claude/dev/completed/sole-dev-merge-fixes/sole-dev-merge-fixes-retro-2026-10-20.md` §4 item 6.

### Branch names (each cut from fresh main, L-037)
- plan: `docs/sole-dev-merge-simplify-plan`
- prototype: `prototype/sdm-script` (never merged; worktree `.worktrees/prototype/sdm-script`)
- TODO triage (1.0): `chore/sdm-todo-triage`
- M1: `refactor/sdm-script`
- M2: `refactor/sdm-switch-over`
- finalize: `chore/sdm-simplify-finalize`
- M2 commit subject must not start with `refactor(skills): split sole-dev-merge `.

### Threat model (both milestones)
- **Trusted:** the operator, their machine, git config, their own repos' `.git`; operator env values (validated only where a bad value hangs or misreports).
- **Untrusted:** PR/issue text, remote branch names, fetched content, tool output that reaches a shell.
- **Out of scope:** hostile repo-local config, planted `.git` files, a concurrent local attacker, git < 2.53, gh < 2.46, exotic locales.
- **Accepted risk:** a closing keyword (`Closes #N`) in model-written review notes could close an issue on merge; commit statuses are not gated (both recorded in ADR-0024).
- **Visible side effects:** `ship` pushes and `finish` merges and deletes the remote branch; run `check`, `ship`, `finish` as three separate Bash calls.

### Release
- No release cut by this plan; changes ship in v0.18.0, cut by code-conventions-impact M14. CHANGELOG Removed: "GitLab/glab support; last in v0.17.0".

_Last Updated: 2026-10-20_
