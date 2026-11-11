<!-- ARCHIVED: 2026-10-23 09:41 -->
<!-- Plan: sole-dev-merge-simplify - COMPLETE -->
<!-- Total Milestones: 2 | Duration: 2026-10-20 to 2026-10-23 -->

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

### sdm.sh CLI contract (M1 Contract, as amended in M1's implementation review; superseded by `sdm.sh help`)
```
CLI (sdm.sh, bash, set -euo pipefail; sourceable: main runs only when "${BASH_SOURCE[0]}" == "$0"):
  sdm.sh check                    # A + B + B-commit. 0 = "check OK (branch=<b>, base=<ref>, ahead=<n>)"; 1 = ABORT: <reason>
                                  # dirt outside the branch: "ABORT: check: files outside the branch changed: <list> (left as they are)"
                                  # pre-commit stays best-effort: prints "check: pre-commit rc=<n>" and goes on
  sdm.sh ship [--notes FILE]      # origin on github.com, gh auth, body, push, PR create or REST update + read-back, G1, G2.
                                  # prints three lines PR_NUM=<n>, PR_URL=<u>, CI_STATE=green|failed|timeout; STATUS lines exit 0; ABORT exit 1
                                  # body in a mktemp file removed by an EXIT trap; PATCH with `gh api -F body=@file`, read-back compared with the file plus one newline (gh `--jq` adds one; impl-review W)
                                  # repo slug from origin's configured URL (pushurl, else url; no insteadOf expansion — 1.0 finding 1), passed as -R/explicit path; origin not on github.com -> ABORT naming the host only (never the URL)
                                  # the PR is used only if OPEN, isCrossRepository=false and headRefOid == local HEAD; decide on gh's rc, never on stdout
                                  # `pr checks --watch` output goes to /dev/null; only the three lines reach stdout
  sdm.sh finish <PR_NUM>          # PR_NUM must match ^[1-9][0-9]*$ before any gh argv; SHA=$(git rev-parse HEAD), used for check-runs and --match-head-commit;
                                  # one lookup: headRefName == current branch (not the default; check-ref-format), isCrossRepository=false, headRefOid == SHA; state OPEN → merge; MERGED → no merge call, go to the delete (a re-run after BRANCH_NOT_DELETED or a cleanup failure); any other state ABORTs;
                                  # strategy re-read from allow_rebase_merge: only literal true/false; null or an API failure ABORTs;
                                  # check-runs at SHA: total_count == runs read (else ABORT), all completed, >=1 success, all in success|skipped|neutral,
                                  #   else STATUS: CI_NOT_DONE / CI_FAILED;
                                  # merge --<strategy> --match-head-commit "$SHA"; re-read state, MERGED required before any delete;
                                  # push --force-with-lease=refs/heads/<b>:$SHA origin :refs/heads/<b> (rc captured, not acted on; 1.0 PROTOTYPE FINDINGS 2); ls-remote --exit-code decides: 2 gone, 0 BRANCH_NOT_DELETED, else error; G4
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

### Prototype facts (Sub-step 1.0, live run on PR #53, 2026-10-20)
- `git push --force-with-lease=refs/heads/<b>:<sha> origin :refs/heads/<b>` deletes the branch on GitHub (live: ls-remote rc 2 after). A stale lease is refused, rc 1, and the branch survives (probed locally).
- `git remote get-url --push` expands `insteadOf`; `git config --get remote.origin.pushurl || … remote.origin.url` does not. sdm.sh reads the configured URL; tests rewrite `https://github.com/` to a local forge with `GIT_CONFIG_COUNT/KEY_0/VALUE_0`, so no test git call reaches GitHub.
- This machine sets `safe.bareRepository=explicit`: tests read a bare repo with `git --git-dir=<bare>`, never `-C`.
- `gh pr checks` non-TTY rows: `NAME<TAB>BUCKET<TAB>ELAPSED…`; buckets seen: `pass`, `pending`.
- `gh pr view <branch> -R <slug>` finds the PR by head name even when the branch's upstream is `origin/main` (worktree cut with `-b … origin/main`).
- A rebase merge rewrites the SHA (head `99d0c845` → `6ad8ad38` on main), so G4's `branch -D` is required, never `-d`.

### Milestone 1 SHA map (PR #55 → main, rebase merge, 2026-10-22)
PR commits from `gh api repos/snewhouse/aa-ma-forge/pulls/55/commits`, matched by full subject to `git log 4eb03c7f..c612620b` on origin/main (16/16).
| PR #55 | main | subject |
|---|---|---|
| `6c4521ea` | `3cb8808b` | docs(aa-ma): sole-dev-merge-simplify 1.0 complete — prototype merged PR #53 |
| `2c3e2c86` | `00c14858` | test(sdm): RED — 147 bats tests and fixtures for sdm.sh check/ship/finish |
| `1cd01f0d` | `6adbcbe5` | feat(sole-dev-merge): GREEN — sdm.sh check/ship/finish, one tested script |
| `d13faa48` | `86dc14b0` | ci(security): run the sdm.sh bats suite in the bats job |
| `90dbf97a` | `9310510f` | docs(aa-ma): 1.3 Result Log — the security.yml grep counts 2, not 1 |
| `7e203bde` | `2877e5c7` | docs(aa-ma): M1 boundary — CODE_INTEL_REFRESH at 90dbf97a |
| `639d3593` | `f759c95c` | docs(aa-ma): M1 CRITICAL_PATH_REVIEW — merge gate mutation-tested |
| `05718b5d` | `4ced5c29` | docs(aa-ma): 1.4 in progress — boundary checks |
| `49143045` | `8cb583b5` | test(sdm): RED — check must leave a ruff-excluded .py untouched (§6.8 CRITICAL) |
| `e70f156f` | `4fc2e277` | fix(sole-dev-merge): check passes --force-exclude to ruff (§6.8 CRITICAL) |
| `3974d428` | `25f9677b` | docs(aa-ma): M1 §6.8 — impl-review, 1 CRITICAL fixed, warnings to TODOS |
| `6a8afdc9` | `42b8f2eb` | docs(todos): M1 PR review notes (C1 1 MEDIUM + 3 LOW); TESTS_VERIFIED 960 |
| `e90370a3` | `dd21068f` | docs(aa-ma): 1.4 — pip-audit unblocked by #56 (no rebase needed) |
| `1e0b52d2` | `32085606` | test(sdm): RED — ship re-reads a lagging PR head instead of calling it not-this-branch |
| `ae90cd2b` | `b2909213` | fix(sole-dev-merge): ship waits for GitHub to show the pushed head before judging the PR |
| `6474936a` | `c612620b` | docs(aa-ma): merge run 3 — head-lag fix re-checked; TESTS_VERIFIED on ae90cd2b |

### Milestone 1 live facts (2026-10-22)
- Right after a push to an open PR, `gh pr view` can still report the old `headRefOid` for seconds (live, PR #55). sdm.sh re-reads within the CI appear-wait caps; a head that never catches up is `reason=head-not-updated`.
- `pull_request` CI checks out `refs/pull/N/merge`, so a new push re-tests the PR against current main: a base-branch fix (PR #56) unblocks an open PR without a rebase or force-push.
- A file named on ruff's command line skips `extend-exclude` unless `--force-exclude` (sdm.sh `check` passes it).
- Local pip-audit on this machine fails `import venv` (the interpreter has no venv module); CI's pip-audit is authoritative.

### Pre-M2 fix PR #57 (`fix/sdm-failure-lines`, rebase merge `0ca6a5fa`, 2026-10-22)
SHA map (branch → main): `ee9dce3d`→`0e1bb4d1` RED · `9c81f9bf`→`ea649ad6` GREEN · `bc9aac40`→`5de1e8ed` RED (rc 8) · `f14891f1`→`0ca6a5fa` GREEN.
What M2's SKILL.md can now rely on (the exit table in `sdm.sh help` is canonical; the M1 Contract above predates this PR):
- Every failure prints a line: `ABORT: ship: git push failed (rc=<n>)`, `ABORT: check: auto-fix commit failed (rc=<n>); the fixes are staged`, `ABORT: ship: --notes needs a FILE`, `ABORT: ship: notes file '<f>' is not a readable file`; post-merge cleanup reports `STATUS: MAIN_NOT_UPDATED — fetch from origin failed` and `main at (none)` instead of a silent exit.
- `BASE_REF` is `origin/<d>` when it exists, else `<d>` (check's `check OK (… base=origin/main …)`, pre-commit `FROM=origin/main`).
- ship: `reason=not-open` when the PR closes during the head wait; PR_NUM/PR_URL print before the strategy read; a post-watch re-read rc 8 (pending) → `CI_STATE=timeout` + finish hint, any other non-zero → `failed`; `CI_POLL_TIMEOUT` must match `^[0-9]+[smhd]?$` and be > 0, else 900s with a stderr line; `--notes` relative paths resolve from the caller's cwd.
- finish: a plain checkout with tracked changes → `STATUS: MAIN_CHECKOUT_DIRTY` before any checkout.
- Named constants in sdm.sh: POLL_DEFAULT 900s, APPEAR_DEFAULT_S 120, INTERVAL_DEFAULT_S 10, GH_CALL_TIMEOUT_S 30, WATCH_INTERVAL_S 30, PR_TITLE_MAX 70, CHECK_RUNS_PER_PAGE 100. sdm.sh 384 lines; sdm suite 167 tests.

### Milestone 2 SHA map (PR #58 → main, rebase merge `7a904f72`, 2026-10-23)
PR commits from `gh api repos/snewhouse/aa-ma-forge/pulls/58/commits`, matched by full subject to `git log 66f9c610..7a904f72` (15/16; the 16th, `f74d80db` "chore: merge origin/main (PR #57 …)", is a merge commit that a rebase merge does not replay).
| PR #58 | main | subject |
|---|---|---|
| `55e6dfc8` | `8f75c23c` | docs(aa-ma): Milestone 1 COMPLETE — gate approved, PR #55 SHA map |
| `adb8c6b9` | `b0bbad19` | docs(aa-ma): pre-M2 decisions — fix PR first, 2.1 RED step, prototype deleted |
| `0efa790c` | `af88a8a0` | docs(aa-ma): record pre-M2 fix PR #57 — SHA map, review triage, TODOS closed |
| `fa7516ab` | `4ba91108` | docs(aa-ma): Milestone 2 ACTIVE — pre-execution validator WARN fixed |
| `1b17e55d` | `5313fa32` | docs(aa-ma): 2.0 complete — M1 post-merge record verified on the M2 branch |
| `18e277c2` | `d0de518b` | test(skills): RED — SKILL.md for /sole-dev-merge is a short sdm.sh caller |
| `befb8bf6` | `30a234d3` | refactor(sole-dev-merge): switch the skill to sdm.sh; delete the stage blocks and their tests |
| `4af64389` | `686171c0` | docs(aa-ma): 2.2 complete — the switch, bats 776/0 on befb8bf6 |
| `62955e26` | `f4228e35` | docs(sole-dev-merge): ADR-0024 one script, GitHub only; CHANGELOG, CONTEXT, lessons, TODOS |
| `61423024` | `8507d3b1` | docs(aa-ma): M2 boundary — code-intel refresh, impact analysis, critical-path review |
| `f4660491` | `461d1008` | docs(aa-ma): M2 TESTS_VERIFIED 776 and §6.8 PASS_WITH_WARNINGS |
| `f3e6176c` | `f6118a1d` | test(skills): RED — SKILL.md's copies of sdm.sh output are tied to the script; no secrets, no force-push |
| `96adf285` | `45e537ae` | fix(sole-dev-merge): SKILL.md instructions match what sdm.sh does (§6.8 M2) |
| `9d704c08` | `43b32388` | docs(aa-ma): M2 TESTS_VERIFIED 776 on 96adf285; pytest 3149 |
| `98b40bfc` | `7a904f72` | docs(aa-ma): 2.4 — pip-audit on #58 unblocked by deps PR #59 (no rebase) |

### Milestone 2 live facts (2026-10-22 to 2026-10-23)
- The new SKILL.md merged its own PR (#58): `check` → C1/C2 (round 1: C1 0C/0H/1M/2L, C2 none) → `ship` → `finish` → `STATUS: OK worktree=…`. pip-audit blocked the first `ship` (CVE-2026-114603, opentelemetry-api, transitive dev dep) → deps PR #59 (`66f9c610`) → re-`ship` (a new AA-MA commit re-tests the merge ref; no rebase) → green.
- The re-`ship` updated #58's body with read-back match right after a push (the M1 head-lag fix, live again).
- `scripts/install.sh` from a linked worktree re-links the skill to that worktree; run it from the main checkout (done after the merge: rc 0, 68 links; `~/.claude/skills/sole-dev-merge` → the main checkout).
- The commit-signature hook's `[ad-hoc]` rule needs the marker alone on its own line of the message (`^\s*\[ad-hoc\]["'`]*$`), not just last on the command line.

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
- Create (M2): `docs/adr/0024-sole-dev-merge-one-script.md`; `tests/skills/test_sole_dev_merge_skill.py` (2.1 RED).
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

_Last Updated: 2026-10-23 (M1 SHA map and live facts; pre-M2 PR #57 facts; M2 pre-execution validator fixes; M2 SHA map and live facts)_
