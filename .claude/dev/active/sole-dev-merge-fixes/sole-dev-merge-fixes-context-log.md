# sole-dev-merge-fixes Context Log

## [2026-10-15] Initial Context

**Feature Request:** Read and review the 2026-10-14 sole-dev-merge fixes spec (kept outside this repo) with fresh eyes and no assumptions. Plan the fixes as an AA-MA plan, log the recurring issues as lessons, then fix them. Grill Ste with docs.

**Trigger:** another session reported two `/sole-dev-merge` bugs it had worked around by hand:
- G3 `--delete-branch` from a worktree (L-1332);
- Stage B check-conventions always "Failed".
Both have recurred for weeks.

**Research findings (4 read-only agents + probes, 2026-10-15):**
- **Spec re-verify.**
  - All facts E1–E33 are CONFIRMED or MOVED at `1bc3849`; only E6 is still [U].
  - Baseline 75/75.
  - Spec errors found: F1 `push --delete` exits 1 when the branch is already gone (it would kill G3 under `set -e`); F2 counted untracked files as dirty; AC line references were stale; the 70/70 baseline figure was stale.
  - New defects found: the footer helper path outside forge; state isn't carried between blocks; the L-007 guard misses staged edits; G3 reports "merged" for an unknown remote; a shared `/tmp` body path; Stage A checks literal main/master only; stale prose.
- **Recurrence mining.**
  - L-1332 recurred on PRs #18, #19, #27, #30, #37 and #41 (#37 and #41 were not logged in the lesson). L-1309 on PR #30. L-1347 on #37 and #41 (not logged).
  - check-conventions exit 2 was recorded as "by design, best-effort" (CCI provenance:148) on every run since 2026-10-08.
  - None of these was fixed in code. The tests assert the bad commands.
  - Root pattern: the skill contradicts its own lessons, lessons and defects live in different repos, by-hand workarounds became routine, and `|| true` hid failures.
- **Multi-plan mechanics.**
  - CCI is active with M10–M14 and M16 pending; none of them touches the sole-dev-merge files.
  - The footer helper is arbitrary with 2 plans.
  - The commit-signature hook accepts any plan.
  - Plan detection is `$PWD`-based.
  - The live skill and hooks are symlinked to main.
- **L-1347 mechanics.**
  - The hook ignores stdin and uses `$PWD`. Sessions start in main and `cd` per command; `MAINTAIN_PROJECT_WORKING_DIR=1`.
  - Reproduced in a scratch repo, including the silent subdirectory miss.
- **Context7:** the gh manual confirms `-F key=@path` reads the value from a file. The Claude Code docs confirm MAINTAIN=1 resets the cwd on every command, and that hook input carries `cwd`.

## [2026-10-15] DECISIONS — grill-with-docs (3 rounds, 11 questions), approved by Ste

1. **Scope:** F1–F5, plus the footer helper (determinism and path), the L-1347 pre-compact hook, Q8 pytest rc visibility, the state handoff, the L-007 staged fix, and the small fixes (G3 unknown remote, per-run body path, Stage A `$DEFAULT_BRANCH`, prose). Deferred: Stage F hardcoded `origin` (dual-remote), Q3 GitLab assert, Q4 mirror push, Q6 `--match-head-commit`.
2. **Location:** forge worktree `.worktrees/fix/sole-dev-merge-fixes`. The AA-MA files live on the branch; merge before CCI M14.
3. **Lessons:** global lessons L-1332, L-1347 and L-1309 were iterated now, and meta-lesson L-1351 added (backup `~/.claude/backups/lessons-20261015-*.md`). Forge L-051..L-055 go in at M1, on the branch.
4. **Spec Q1–Q9:** all recommendations accepted.
   - Q1: explicit delete for all layouts.
   - Q2: print the cleanup commands; don't automate.
   - Q5: always stop on a dirty main.
   - Q7: add CHANGELOG Unreleased bullets.
   - Q8: print the rc lines.
   - Q9: option A (env refs plus `--files`, per ADR-0018).
5. **Exit codes:** the B-commit staged-set ABORT is rc 1 (nothing committed, index reset). A Stage F read-back mismatch prints `STATUS: PR_BODY_NOT_UPDATED` with rc 0.
6. **Delivery:** one PR per milestone. M1 is G3/G4 plus the footer (the footer must ship in the first PR that puts a second plan on main). M1 is merged with the manual L-1332 steps; M2–M5 are merged by the fixed skill.
7. **L-1347 design:** probe first (stdin cwd vs `$PWD` under `cd`, MAINTAIN=0, EnterWorktree). Then (A) the helper gets an optional root from stdin cwd → toplevel, and (C) the pre-compact guard skips tracked writes when a linked worktree holds the task.
8. **Hook reach:** the helper plus pre-compact only. The other 4 `$PWD` hooks get a TODO with evidence.
9. **Footer rule:** one plan → it. Several → the plan the branch changed. Otherwise `[ad-hoc]` plus a WARN. Resolve the helper through `~/.claude/hooks/lib` outside forge.
10. **Glossary:** CONTEXT.md gets **Best-effort step** (M1) and **Stage state file** (M2).
11. **Spec §VI:** amend the detection rule in M1. No ADR, because the rule is easy to reverse.
12. **Engineering themes:** all [A].
13. **Prototype-Required:** M1 (E6 gh rc), M2 (state file), M5 (PreCompact cwd).

14. **Session root (2026-10-15, after plan-verification Wave 1):** every execution session for this plan starts in its worktree.
    - A session rooted in main cannot see this plan before M1 merges, so `aa-ma-commit-signature` blocks its commits (probed rc=2).
    - Starting in the worktree also keeps pre-compact writes off main for this plan's work.
15. **Hook literal-text defect:** `aa-ma-commit-signature.sh` accepts a commit command that calls `emit_aa_ma_footer` (new Sub-step 1.7). The skill's `-m "…${FOOTER}"` commits were blocked whenever a plan was visible; this predates the plan.
16. **Footer install link:** `scripts/install.sh` links `hooks/lib/aa-ma-footer.sh` (new Sub-step 1.9), which closes the footer half of TODOS `:239`.
17. **Revisions after the Wave 1 findings (rev 2):**
    - The state loader is now last-write-wins, splits on the first `=`, uses an absolute git-dir, treats an empty env value as unset, and ignores a file left by another branch.
    - The footer's default-branch fallback works without the caller's pipefail, and an untracked plan dir counts as touched.
    - `ORIGINAL_BRANCH` is set in the G test `setup()`.
    - `Test-Command` is set in reference.md, because Fence 3 would otherwise run only pytest.
    - The CCI-shared files are listed in §0.
    - The bootstrap steps are extended (don't run the unfixed G4; check before B-commit; run Stage C scans by hand).
    - All acceptance criteria are rewritten as checks (Angle 4: 31 of 82 needed it).
    - The rollback text is corrected: main is not branch-protected.

18. **Pre-compact symlink defect into M1 (Ste, 2026-10-15):** the security audit reproduced a live defect. `pre-compact-aa-ma.sh` follows symlinks when it appends (`:123-130`, `:139-145`) and when it `cat`s reference.md (`:93`), so an untrusted clone could write into files outside the repo. The guard ships as Sub-step 1.8 in the first PR; M5 keeps the cwd/worktree redesign.
19. **Rev 3 (plan-verification Wave 2: fresh agent, engineering standards, security):**
    - G3 refuses before merging when ORIGINAL_BRANCH is invalid, is the default branch, or isn't the PR head; it deletes `:refs/heads/<b>` and asserts on the exact ref. G4 runs check-ref-format and uses `refs/heads/` forms.
    - 1.7 accepts only the canonical `FOOTER=$(emit_aa_ma_footer)` … `${FOOTER}"` shape, with bypass RED cases.
    - The state file uses no `eval`: base64 values, a 15-key allowlist, and a refusal of symlinked, foreign-owned or other-writable files. Stage A recreates it under umask 077. Run files move to a private `$SDM_DIR` under the git-dir instead of `/tmp`.
    - Probe output is redacted, and the privacy check runs at every gate.
    - `[post-merge]` criteria are verified at the next N.0 (L-037).
    - M4 names its gate lines. The 1.0 verdict string, the G4 cleanup quoting and the full G4 tail are fixed. 1.5 depends on 1.0; 1.10 depends on 1.4 and 1.9.
    - M1 is now 2 days at 65%.

**Remaining Questions:**
- E6 gh rc: probe 1.0, if Ste approves a throwaway private repo.
- PreCompact stdin `cwd` under `cd` / EnterWorktree: probe 5.0.
- `-F body=@file` vs `--input`, and trailing-newline handling: probe 4.0.

_This log will be updated via context compaction as the task progresses._

## [2026-10-15] PLAN APPROVAL
- Approved by: Ste ("approve the plan, commit the AA-MA files")
- Plan revision: 4 (verification PASS WITH WARNINGS)
- Decision: APPROVED — execution starts at Sub-step 1.0 in a session rooted in this worktree

## [2026-10-15] DECISION E6 probe: declined — Ste
- Asked at the Sub-step 1.0 HITL gate. No throwaway repo, no `delete_repo` token scope.
- E6 (gh's rc when `--delete-branch` fails locally in a worktree) stays [U]. G3 decides from `gh pr view --json state`, not gh's rc; the 1.1 test "gh pr merge rc=1 but state MERGED" covers the rc=1 case.

## [2026-10-15] §6.8 POST_IMPL_REVIEW — Milestone 1 (window 1d760f1..6b12a9d)
- Verdict: PASS_WITH_WARNINGS. 0 CRITICAL / 9 WARNING / 16 INFO across 5 agents; no override panel was needed.
- **Fixed before the gate** (RED 68a02bb, then GREEN):
  - G3: `ls-remote --exit-code` (code-reviewer W3), plus `DEFAULT_BRANCH` check-ref-format and a `MERGE_STRATEGY` allowlist (security INFO).
  - G4: a single terminal STATUS line, never `OK` after `MAIN_NOT_UPDATED` (code-reviewer W2); `sub()` replaces the `substr` magic number (W5).
  - commit-signature rule 8 redesigned as an exact-line allowlist after `set -e`. Two security WARNINGs found commits with an empty footer or with text after it. Under L-049 a second finding on the same mechanism means redesign, not patch. Matrix v2 passes 24/24.
  - pre-compact: one shared `AA_MA_FILES` list (future-proofing W2).
  - The stale TODOS install entry is rewritten (future-proofing W1).
- **Deferred as TODOs:**
  - pre-compact parent-dir symlinks (into M5);
  - repo-copy helper resolution outside forge;
  - `git -C`/`git -c` forms (in the commit-msg TODO).
  - M4 4.2's status rows are widened to the G3/G4 ABORTs and the exit contract (code-reviewer W4).
- **Scope note** (code-reviewer W1): `docs/architecture/{README,component,io}.md` (regen stamp) and `tests/codemem/test_plugin_surface.py` (orphan set) changed as outputs of `scripts/regen-generated.sh`. The Contract's "only if regen-generated.sh changes them" line covers them.

## [2026-10-15] GATE APPROVAL: Milestone 1: Worktree-safe G3/G4, deterministic footer, lessons
- Gate: HARD
- Approved by: Ste (AskUserQuestion, "Approve")
- Criteria verified: 7/7 pre-merge (bats 638/0 at 8ae211e via fence 3; G3 --delete-branch 0; STATUS markers 7; feature default 0; 4 hook suites 0 not-ok; privacy 0/0; PROTOTYPE/IMPACT_ANALYSIS/CRITICAL_PATH_REVIEW present). The `[post-merge]` criterion is recorded at Sub-step 2.0 (L-037).
- Decision: APPROVED

## [2026-10-15] DECISION G3/G4 take ORIGINAL_BRANCH from the state file only — Ste
- Asked in the M1 → M2 handover (§9 Q2). Ste accepted the recommendation.
- In M2's live merge, G3/G4 read `ORIGINAL_BRANCH` from the stage state file only. It is **not** also passed explicitly.
- Why:
  - `sdm_load` already ignores a file whose `ORIGINAL_BRANCH` ≠ `git branch --show-current`. A second explicit value would only duplicate that check.
  - A non-empty explicit env beats the file (plan §4 M2 contract). A stale or mistyped manual value would therefore override the correct one, and the first live run would test the operator, not M2.
  - G3 already ABORTs when the PR head ref ≠ `ORIGINAL_BRANCH` (`stage-g-merge.md:194`), so a wrong value cannot delete another branch.
- Visibility: before G3 in the 2.3 live merge, print the loaded `ORIGINAL_BRANCH`/`PR_NUM` as a read-only check. It is output only, never an input.

## [2026-10-15] SESSION NOTE — M2 runs in a worktree-isolated session
- This session moved into `.worktrees/fix/sole-dev-merge-fixes-m2` with EnterWorktree (decision 14 holds: the hooks' `$PWD` plan scan sees both plans from here).
- The isolation guard refuses `. file` in commands, `git -C <main>` and complex git forms. Multi-step logic runs as `bash <scratch script>`. 2.3's G4 fast-forwards `<main>`, so that step needs the isolation lifted or Ste's `!`.

## [2026-10-15] M2 interface choices (Sub-step 2.1), within plan §4 M2
- **Run file names.** Files under `$SDM_DIR` get fixed names: `review.md`, `security.md`, `ruff.json`, `shellcheck.json`, `findings.md`, `reviewer-notes.md`, `auq.json`, `body.md`. `SDM_DIR` is already per-run (`sdm-$SLUG`), so a slug in the file name would say it twice. Env overrides that tests already use (`BODY_OUT`, `REVIEWER_NOTES_FILE`, `AUQ_LOG`) stay as seams; only their `/tmp` defaults go.
- **Stage A's `rm -f "$SDM_STATE"` is its first statement.** An A that aborts (dirty tree, no remote, …) must not leave the last run's file, which a later block on the same branch would accept.
- **SLUG** = `${SLUG:-<date +%Y%m%d-%H%M%S>-$$}`, generated by A only. An explicit SLUG is honoured, so tests stay deterministic. It is never `date +%s`.
- **Stage C prints `Stage C scanned: Ruff S <n> file(s), ShellCheck <m> file(s)`.** 2.3's live check quotes this line, and C did not print such a count before.
- **Stage F:** no `PR_BODY_FILE` default. An empty or missing value hits the existing "requires non-empty body file" ABORT.
- **Deviation from the Contract's "review only":** `test_stage_c_dispatch.bats` (29 refs), `test_stage_d_triage.bats` (11) and `test_stage_e3_body.bats` (2) seed and read `/tmp/sole-dev-merge-*-$SLUG` paths. Moving run files to `$SDM_DIR` makes them real edits in 2.2: they set `SDM_DIR`/`SLUG` and use the new names. Behaviour is unchanged; only the inputs move.

## [2026-10-15] DECISION E1→E2 remote counts: prose now, fix in M4 — Ste
- Found in 2.2: E2 reads `n_github`/`n_gitlab` from E1. E1 is not one of the 13 state blocks, and the counts are not among the 15 decided keys, so a fresh-shell E2 aborts.
- Options put to Ste:
  - (1) prose now, fix in M4 — recommended, chosen;
  - (2) fix in M2: E1 saves, 18 keys;
  - (3) E2 recounts the remotes itself (duplicates E1).
- Done in M2: the E1 prose says to run E1 and E2 in one Bash call, and the TODOS entry is added. M4 4.2 gains the criterion: E1 saves its counts (18 keys) and an empty-env E2 test passes.
- Other 2.2 deviations, for the record:
  - Stage C requires `SDM_DIR`, not `SLUG`: its file names no longer contain the slug.
  - The loader comment `no eval anywhere` was reworded in all 12 copies, because the plan's own `eval|sdm` AC matched it.
  - Two more files outside the Contract list, both required by the change: `tests/commands/sole-dev-merge/fixtures/helpers.bash` (`sweep_slug_tmp` deleted, 0 callers left) and `tests/hooks/aa-ma-footer.bats` (D is fed `SDM_DIR`).

## [2026-10-15] §6.8 POST_IMPL_REVIEW — Milestone 2 (window f78bbf9..03f9008)
- Verdict: PASS_WITH_WARNINGS. 0 CRITICAL / 11 WARNING (10 distinct) / 19 INFO across 5 agents; no override panel was needed.
- **Fixed before the gate** (RED 38d6560, then GREEN):
  - the loader rejects an empty ORIGINAL_BRANCH; A ABORTs on a detached HEAD and outside a repo;
  - `sdm_save` refuses a symlinked or foreign file (fail closed, in all 13 copies);
  - G4 requires `MERGE_DISPATCHED=1`; G2/G3 require a numeric `PR_NUM`;
  - A validates `SLUG`, clears earlier `sdm-*` run dirs, and always makes a fresh 700 dir (this also stops stale reviewer notes reaching E3);
  - prose and CHANGELOG no longer hardcode "15 keys" or the false temp-dir claim; F's message is reworded;
  - the test block list is read from the markers.
- **Deferred:** `$CHANGED_*` word-splitting → M3; `REMOTE_CHOICE:-github` → M4 (one TODOS entry).
- Full record: `sole-dev-merge-fixes-impl-review.md` § Milestone 2.

## [2026-10-15] GATE APPROVAL: Milestone 2: Stage state file
- Gate: HARD
- Approved by: Ste (AskUserQuestion, "Approve")
- Criteria verified: 7/7 pre-merge:
  - 13 blocks name the state file, and only A lacks `sdm_load`;
  - `test_stage_state.bats` 32 @tests, 0 not-ok;
  - `eval|sdm` 0 and `/tmp/sole-dev-merge` 0; 600/700 asserted; masking grep 0;
  - privacy 0/0 (AA-MA files and `git diff origin/main`);
  - PROTOTYPE, IMPACT_ANALYSIS and CRITICAL_PATH_REVIEW in PL.
- Also checked: fence 3 `TESTS_VERIFIED passed=670` at c00137f; pytest 3136 passed; §6.8 PASS_WITH_WARNINGS (all WARNINGs fixed).
- The `[post-merge]` criterion is recorded at Sub-step 3.0 (L-037).
- Decision: APPROVED

## [2026-10-16] Live merge run 1 (2.3): Stage C/D triage — Ste
- The run used this branch's M2 blocks, each in its own Bash call, from `a589249`.
  - A, B and B-commit were OK. B's check-conventions still exits 2 "no diff source" (L-051; M3 fixes it).
  - C1 and C2 wrote `review.md`/`security.md` into `<git-dir>/sdm-<slug>/` with plain bash: no permission stall (closes the §6.8 INFO).
  - A fresh-shell D read C's findings through the state file: `0 CRITICAL, 0 HIGH, 1 MEDIUM, 4 LOW`.
- **MEDIUM** (C1): `sdm_save` checked only symlink/owner, so it appended to a g/o-writable file the loader refuses, and created a missing file under the caller's umask. **Applied** (Ste): RED 22183e3, then GREEN. `sdm_save` refuses exactly what the loader refuses and creates the file 600 (in all 13 copies). A's separate `umask 077` subshell became redundant and is gone.
- **LOWs:**
  - two prose fixes applied: the A "exports" sentence; "re-run E1 and E2 together";
  - B–G outside a repo give git's raw `fatal:` (rc 128): accepted, because A already aborts there first;
  - `SDM_DIR` is not re-checked after A (C2): it needs a co-tenant with git-dir write, the plan's residual. Left as advisory in the PR body.
- **2.3 AC (Stage C scanned ≥1 file each): N/A for this PR** (Ste). It changes no `.py`/`.sh`, and the live line read `Stage C scanned: Ruff S 0 file(s), ShellCheck 0 file(s)`. The empty-env bats case proves C receives B's files. The live ≥1 check moved to M3 3.3.
- After the fix the merge restarts from Stage A, with a fresh state file and run dir.


## [2026-10-16] SESSION NOTE + DECISIONS at Sub-step 3.0 — Ste
- M3 runs in an EnterWorktree session (Ste: "EnterWorktree now") from `<main>` into `.worktrees/fix/sole-dev-merge-fixes-m3`, cut from `origin/main` `52f4fd3`. The new branch's upstream was unset straight after `worktree add` (it tracked `origin/main`, so a bare push would target main).
- M2 worktree and branch removed after `git cherry origin/main fix/sole-dev-merge-fixes-m2` showed 0 `+` lines (branch was at `c189f92`). The run-2 run dir and state file were backed up to `<scratch>` first.
- Handover §9 Q1: the two run-2 C1 LOW prose fixes (`sdm_save` also refuses g/o-writable files and creates the file 600; re-answering E2 means re-running E1+E2 together) go in as a docs commit at 3.0, before the 3.1 RED (Ste: "Yes").
- Gate parser note: a Result Log bullet `- Mode: HITL. …` is read as a second `Mode:` field (rc 2, "conflicting values"). Use `Mode: HITL — …`, as 2.0 does.

## [2026-10-16] M3 3.2 deviations from plan §4 M3 (within spec F4 intent)
- **Guard: a newly staged out-of-scope file is unstaged, never restored from HEAD.**
  - Plan §4 M3 says tracked rows use `git restore --source=HEAD --staged --worktree`.
  - Probed: on a staged path HEAD lacks (`A `), that command exits 0 and deletes the file.
  - Spec F4.1's reason for leaving `??` rows alone ("it may be the operator's file") applies here too.
  - So a path absent from HEAD is unstaged with `git restore --staged`, kept, and listed on the same "left unstaged" line as `??` rows.
  - Test-first: RED `c739bb8`, GREEN `21c57e9`, mutation-checked.
- **B-commit reads CHANGED_FILES from the state file (plan), not by recomputing from BASE_REF (spec F4.2).**
  - The plan postdates M2's state file. With no CHANGED_FILES, nothing is in scope, so B-commit commits nothing and lists the dirty files.
  - `tests/hooks/aa-ma-footer.bats` (2 tests, not in the M3 Contract file list) now feed `CHANGED_FILES=f.txt`, the same kind of input change M2 made for D at `:193`.
- **SKILL.md prompt-size cap (500 lines, `tests/test_prompt_size.py`):** the new prose took the file to 506. It was tightened to 495 rather than moving inline Stage A/B detail into references/.

## [2026-10-16] §6.8 POST_IMPL_REVIEW — Milestone 3 (window f8390c6..fa55ec4) — decisions, Ste
- Verdict PASS_WITH_WARNINGS: 0 CRITICAL / 6 WARNING / 12 INFO (impl-review.md, Milestone 3).
- "Fix all 6 now": every WARNING was fixed test-first (RED 6b9212d → GREEN 10845fe).
- **B-commit abort semantics: "Check first, touch nothing".** This supersedes spec F4.4's "unstage with `git reset -q`", which would clear the operator's `add -p` staging.
  - The pre-check aborts before staging, leaving the index as it was.
  - The post-add check unstages only B-commit's own paths.
  - AC4.4's index assertion changed from "empty" to "unchanged".
- **`GIT_LITERAL_PATHSPECS=1`** adopted (INFO). Set after Stage B's pytest/pre-commit so the user's tests and hooks keep git globs.
- **W5 was already scheduled for M3** (TODOS:98, CL :160) and missed at 3.1. That miss is lesson L-056.
  - The TODO's `-- "${arr[@]}"` works for ruff and shellcheck, but not for pre-commit (argparse rc 1, probed), which gets `./`-prefixed names instead.

## [2026-10-16] GATE APPROVAL: Milestone 3: Stage B scoped commit, guard, check-conventions refs
- Gate: HARD
- Approved by: Ste (AskUserQuestion, "Approve + live merge")
- Criteria verified: 7/7 pre-merge:
  - SKILL.md greps: `--from-ref` 0, `PRE_COMMIT_FROM_REF="$BASE_REF"` 1, rc lines 3, `git add -A` 0;
  - `test_stage_b_scope.bats` 23 @tests, 0 not-ok (c_dispatch 8/8);
  - privacy 0/0 (AA-MA files and `git diff origin/main..HEAD`);
  - IMPACT_ANALYSIS (with addendum) and CRITICAL_PATH_REVIEW in PL;
  - 3.3 docs: ADR-0018 phrase, L-051/L-053 "Fixed in", 1 CHANGELOG bullet;
  - fence 3 `TESTS_VERIFIED passed=692` at 17cb01f..19b6a8d, pytest 3136 passed;
  - §6.8 PASS_WITH_WARNINGS, all 6 WARNINGs fixed test-first.
- Recorded during the live run: the PR's own Stage B `check_conventions` line (milestone AC 3).
- The Stage C scanned-files AC carries to the next PR that changes `.py`/`.sh`, since this one changes neither. Fence 1 and the COMPLETE flip happen at 4.0 (L-037).
- Decision: APPROVED

## [2026-10-16] Live merge run 1 (3.3): Stage C/D triage — Ste
- **A** OK (18 ahead of main).
- **B** (this branch's blocks, each in a separate Bash call): `check_conventions (added lines only)…Passed`, `no diff source` count 0. Also `pytest rc=0`, `pre-commit rc=0`, guard clean.
- **B-commit** no-op. **C** scanned `Ruff S 0 file(s), ShellCheck 0 file(s)`: the PR has no `.py`/`.sh`.
- **D:** 0C / 0H / 1M / 6L.
- **MEDIUM** (C1): B-commit's `${CHANGED_FILES:-}` masked a missing state file → **applied** (RED d9c43be → GREEN bc2b9d5).
- **LOW** (C1): `--no-renames` in `staged_outside` → **folded in** (Ste), same commits.
- **Other 5 LOWs → reviewer notes:**
  - names with `"`/`\`/control characters are still C-quoted by `--name-only`;
  - raw names are echoed unescaped (terminal spoofing);
  - out-of-scope files are listed only when nothing is committed;
  - one `git status` per file;
  - plus C2's duplicate of the quoting LOW.
- The merge restarts from Stage A (as M2 run 1 → run 2).

## [2026-10-16] Sub-step 4.0: M3 closed on the M4 branch; carry-ins decided — Ste
- **M3 closed (L-037):** 3.3's Result Log written from the handover evidence, re-run from `<main>` first (E1 `MERGED 07a8b45`, E2 0 bytes / rc 2, HEAD = origin/main = `07a8b45`, tracked changes 0, cherry 0 `+`). Fence 1 `pending_steps=0`; privacy 0/0; Milestone 3 flipped COMPLETE under the existing GATE APPROVAL.
- **Worktrees:** M3 worktree and branch removed (branch was `1a122b7`). M4 worktree cut from `origin/main` `07a8b45`; the upstream `worktree add -b … origin/main` set was unset; `--is-ancestor` rc 0. Session works in the M4 worktree by absolute path (EnterWorktree declined by Ste).
- **4.0 probe target (Ste):** an early **draft** M4 PR, not merged PR #44. Push the M4 branch, open a draft PR, PATCH its body with `-F body=@file`, read back, `cmp`. The 4.3 live Stage F then hits the existing-PR path, so the new PATCH + read-back code runs for real.
- **Handover §9 Q1 — run 2's 6 LOW notes (Ste, as recommended):** the 2 doc-only items (the "needs CHANGED_FILES" ABORT missing from the outcomes table and B-commit prose; the post-add `git reset -q -- INTENDED` wording) fold into M4's docs-drift work. The other 4 go in one TODOS entry; probe the Y=R guard item first (L-056).
- **Handover §9 Q2 — Stage C `${CHANGED_PY:-}`/`${CHANGED_SH:-}` defaults (Ste):** a TODOS entry with `file:line` (L-1351), not M4. The Stage C reference is outside M4's Contract files.

## [2026-10-17] DECISION gh-api body: -F, newline=exact+1 — Ste
- **Method:** Stage F updates an existing PR with `gh api -X PATCH repos/{owner}/{repo}/pulls/$PR_NUM -F "body=@$PR_BODY_FILE"`. It does not use `gh pr edit` (E15/L-1309).
- **Read-back:** `cmp -s <(cat "$PR_BODY_FILE"; echo) <(gh api repos/{owner}/{repo}/pulls/$PR_NUM --jq .body)`. On a mismatch Stage F prints `STATUS: PR_BODY_NOT_UPDATED — PR #N` and exits rc 0, as reference.md's exit contract requires.
- **Evidence** (4.0 probe, draft PR #45): both methods round-trip byte-exact. `-F` reads the file verbatim, with no `{owner}` expansion and no `true`/`123` typing. `--jq .body` always adds one `\n`, so the "+1" is exact rather than a normalisation, and a dropped or added trailing newline is still caught.
- **Rejected:**
  - Stripping trailing newlines: it is blind to trailing-newline drift.
  - `--input` + `jq -j`: it adds a `jq` binary dependency, and the skill has none today.
- **Stub consequence (4.1):** the gh stub's `--jq .body` arm must echo the stored body plus one `\n`, as real gh does. `GH_PR_BODY_READBACK` overrides it.

## [2026-10-17] L-056 carry-ins folded into M4; Contract widened — Ste
- **Grep** (TODOS, CL, impl-review and verification for `M4`/`Milestone 4`) found two items missing from 4.1/4.2:
  - `REMOTE_CHOICE:-github` → `${REMOTE_CHOICE:?}` (TODOS:99, CL:160, IR:74);
  - the Stage A part of the `DEFAULT_BRANCH` validation (IR:33; G3 does it at `stage-g-merge.md:269`).
  - Already covered: E1→E2 counts (4.2), G3/G4 ABORT rows (4.2).
- **Y=R probe** (`<scratch>/yr-probe`, git 2.53.0): `mv a b; git add -N b` gives ` R b.txt\0a.txt\0`. The guard (SKILL.md stage-b-scope, `[[ "${rec:0:1}" == [RC] ]]`) reads only X. The source `a.txt` then becomes a record `XY=[a.] path=[xt]`, and the guard would `restore --source=HEAD` a path named `xt`. B-commit's porcelain use is display-only and unaffected.
- **Decisions (Ste, AskUserQuestion):**
  - Y=R guard fix → M4 (1 RED + `${rec:0:2} == *[RC]*`, line-neutral).
  - `REMOTE_CHOICE` → M4 at all sites: F, E0/E3, G1–G3. `references/stage-g-merge.md` and the b_scope/g_merge/state test files are added to M4's Contract (plan §5 M4, marked "Added at 4.0").
  - The Stage A `check-ref-format` RED is added with them.
- **TODOS filed:** "Stage B: three LOWs from PR #44's Stage D (run 2)" (env CHANGED_FILES wins; `??` at a branch-deleted path re-added; C-quoting / unescaped echo) and "Stage C: `${CHANGED_PY:-}` / `${CHANGED_SH:-}` masking defaults" with `file:line` (L-1351).
- **Constraint for 4.2:** SKILL.md is 499/500 lines. Adding the 7 status rows plus the doc-only LOW wording will exceed the cap, so 4.2 must move prose into `references/` (not tighten it into unreadability). Record where it moved.

## [2026-10-17] 4.2 GREEN: scope deviations and design choices
- **Contract deviation (mechanical):** `references/stage-c-review-and-security.md` and `stage-d-triage.md` changed on the `SDM_KEYS` line only (15 → 18 keys). `test_stage_state.bats` requires the loader to be byte-identical in every block, so widening the allowlist touches all 12 copies.
- **New file `references/stage-state.md`:** SKILL.md was 504/500 after the code changes. The 34-line "State between stages" prose moved out, and a 3-line pointer section keeps the heading the 12 loader comments name. This was chosen over moving B-commit (`aa-ma-footer.bats:202` reads `footer-resolve` from SKILL.md) or the banner (`test_smoke_e2e.bats:54` greps SKILL.md). SKILL.md is now 488.
- **REMOTE_CHOICE criterion narrowed:** E2's `REMOTE_CHOICE:-gitlab` is the dual-remote prompt's default answer, which the executor overrides after AskUserQuestion. It is not a missing input, so it stays. E2's `n_github`/`n_gitlab` `:-0` became required (same L-055 shape, same item).
- **F with a non-numeric PR_NUM** goes to the STATUS path, so no PATCH reaches `pulls/0`.
- **Exit table vs the `comm` check:** the check's `[A-Z_]+` cuts ABORT messages at the first lowercase letter, so each Stage A ABORT is named by its leading words in one row. Table and code agree (comm empty).

## [2026-10-17] GATE APPROVAL: Milestone 4: Stage F REST body update, small fixes, docs drift
- Gate: HARD
- Approved by: Ste (AskUserQuestion, "Approve + live merge")
- Criteria verified: 8/8 pre-merge:
  - `extract stage-f-push | grep -c 'gh pr edit'` = 0;
  - @tests: read-back mismatch → `STATUS: PR_BODY_NOT_UPDATED … reason=readback-differs`, rc 0; stale `sdm-stale/body.md` not posted; Stage A aborts on `DEFAULT_BRANCH=trunk`;
  - status-table `comm` empty, and ADR-0008 markers == code (both now bats guards);
  - `bats --tap SDM tests/hooks` 714/0 (fence 3 `TESTS_VERIFIED passed=714`); TODOS Stage F entry under `## Completed` with `**Done:**`;
  - PL `IMPACT_ANALYSIS — Milestone 4: HIGH=0 unresolved` (+ addendum) and `CRITICAL_PATH_REVIEW — Milestone 4`;
  - privacy 0/0;
  - this approval.
- §6.8 PASS_WITH_WARNINGS (0C/11W/17I). All 11 WARNINGs fixed test-first (RED 7b22079 → GREEN b403f60); mutations 8/8 caught.
- Recorded during the live run: 4.3's quote of this PR's live Stage F read-back. Fence 1 and the COMPLETE flip happen at 5.0 (L-037).
- Decision: APPROVED

## [2026-10-17] Live merge run 1 (4.3): Stage C/D triage — Ste
- **A** OK (17 ahead). **B** (this branch's blocks, each in its own Bash call): 22 files (0 py, 0 sh), `check_conventions (added lines only)…Passed`, `no diff source` 0, `pytest rc=0`, `pre-commit rc=0`, guard clean. **B-commit** no-op.
- **C:** C1 and C2 wrote into `<git-dir>/sdm-<slug>/`; C scanned `Ruff S 0 file(s), ShellCheck 0 file(s)`. **D:** 0C / 0H / 1M / 6L.
- **MEDIUM** (C1): the exit-table sync test's `[A-Z_]+` token saw mixed-case ABORTs only as `ABORT: S`/`ABORT: C` → **applied**. Tokens are now `ABORT: <word>[ <word>]`; a planted `ABORT: Stage Z9:` is `ABORT: S` to the old regex and is caught by the new one (mutation).
- **All 6 LOWs applied** (Ste: "Apply MEDIUM + all 6 LOWs"): G3 one head/owner lookup with an ABORT on failure; F's ownership rule after create too (C2); a per-reason hint; E1 requires Stage A's `SDM_DIR`; the blank line before `---` restored (the table rewrite had dropped it: setext heading); stage-state.md H1→H2.
- RED `7a05ad3` (6 not ok) → GREEN `bfa312e`; 718/0; mutations 6/6. `test_stage_e_remote.bats` setup exports `SDM_DIR` (test-only, outside the Contract): E1's unit tests run without Stage A.
- Run 1 evidence was backed up to `<scratch>/m4-run1-evidence/` before the restart. The merge restarts from Stage A (as M2/M3 run 1 → run 2).

## [2026-10-17] Live merge run 2 (4.3): Stage D triage — Ste: "Fix all incl. GitLab"
- **A** OK (21 ahead). **B:** 23 files (0 py, 0 sh), `check_conventions … Passed`, `no diff source` 0, pytest rc 0, pre-commit rc 0, guard clean. **B-commit** no-op. **C** scanned Ruff S 0 / ShellCheck 0. **D:** 0C / 0H / 1M / 5L.
- **MEDIUM** (C2): the GitLab F/G3 path had no ownership check matching the new GitHub fork guard (pre-existing code). **Applied.**
  - Facts come from Context7 only, because glab isn't installed here (no live probe): `glab mr view` has `-F json` and `--jq`; MR fields include `iid`, `web_url`, `state` (`opened`), `source_branch`, `source_project_id` and `target_project_id`.
  - The lookup uses plain jq string interpolation, not `@tsv`, because glab's jq dialect is unverified.
- **LOWs applied:**
  - G2/G3 take `MR_IID` from the checked PR_NUM (C2; the G2 site was found by grep, same shape);
  - an open PR/MR only, so a reused branch name with a closed or merged PR leads to a new one (C1);
  - after create, GitHub reads the PR by the URL `gh pr create` printed;
  - the GitLab gap is fixed, not filed (C1);
  - the table now says `patch-failed`/`readback-differs` keep PR_NUM and Stage G continues (C1);
  - the dead gh stub single arms are removed (C1).
- RED `49194f3` (17 not ok: 10 at the new assertions, 7 from the stub's 5th field that F didn't read yet) + `5d7bcdd` (G2 RED shown in-session, plus a count fix to my own test: detect + re-check = 2) → GREEN `26b43e1`. 727/0, pytest 3137, mutations 8/8.
- **Risk:** the GitLab path is tested against the stub only. A future GitLab run should check the real `glab mr view -F json --jq` output once (TODOS).

## [2026-10-18] Live merge run 3 (4.3): Stage D triage; scope back to GitHub; dual-remote default — Ste
- **A** OK (26 ahead). **B:** 25 files (0 py, 0 sh), `check_conventions … Passed`, `no diff source` 0, rc 0/0, guard clean. **B-commit** no-op. **C** Ruff S 0 / ShellCheck 0. **D:** 0C / 0H / 2M / 3L.
- Ste chose "Fix all, run 4", then asked **"why glab? we use GitHub"**. aa-ma-forge has one remote (`origin` → github.com), glab is not installed, and the GitLab branch never runs here. **Decision (Ste): GitHub only in M4.** The GitLab items go to TODOS; `26b43e1`'s GitLab checks stay (tested on the stub, fail closed).
- Ste asked **"did you push to any biorelate glab?"** No, verified: the only remote is github.com, git config has 0 gitlab/biorelate URLs, glab is absent, every push went to `origin/fix/sole-dev-merge-fixes-m4` on GitHub, and the live runs stopped at Stage D (Stage F never ran). Lesson L-057.
- **M1 (C2), applied:** G3 (GitHub) requires `state=OPEN` in its one owner lookup before merging. A stale PR_NUM from an earlier merged PR could otherwise lead to deleting a branch that holds unmerged commits. RED `547cecf` → GREEN `245e676`; mutation caught.
- **Dead gh stub arms** (`--jq .url`/`.number`, C1) removed in `245e676`.
- **M2 (C1) and the glab merge-failure LOW** → TODOS (GitLab entry).
- **Dual-remote default (Ste: "Default to GitHub"):** E2's GitLab default, a Biorelate-era "project convention (bk_<project>.md)", flipped to GitHub: labels, default and the pre-answer value. RED `4117467` → guard tweak `591282a` → GREEN `2addbba`; mutations 2/2.

## [2026-10-18] Live merge run 4 (4.3): Stage D triage; an outbound push attempt from a test — Ste
- **A** OK (33 ahead). **B:** 26 files (0 py, 0 sh), `check_conventions … Passed`, `no diff source` 0, rc 0/0, guard clean. **B-commit** no-op. **C** Ruff S 0 / ShellCheck 0. **D:** 0C / 0H / 1M / 6L.
- **MEDIUM** (C1): my `2addbba` GitHub default was inconsistent in dual-remote repos where origin is GitLab (F pushes to origin, G3 deletes on origin). **Ste: "Default = origin's host + guard".** E2 defaults to the host origin pushes to (GitHub if neither); F ABORTs before any push when REMOTE_CHOICE names the other forge.
- **LOWs (Ste: "Fix 1–4 now, 5 → TODOS"):** G3 accepts this run's own PR when it is MERGED at the local HEAD (headRefOid) and skips the merge call; MERGED at another commit ABORTs. G3 prose lists the OPEN/cross-repo refusals. The stale TODOS line and the F test header are fixed. `--match-head-commit` → TODOS.
- **Incident (L-058):** the first RED draft set a sandbox origin to `https://gitlab.com/x/y.git`. With no guard yet, F ran a real `git push` that hung at the credential prompt (600 s timeout); I stopped it. Verified: no GitLab credentials (git's helpers are only for github.com/gist.github.com; no `~/.git-credentials`), so nothing was sent, and the github.com twin never ran. All SDM test remotes now use `.invalid` hosts and `GIT_TERMINAL_PROMPT=0`.
- RED `bd2973a` (4 not ok, each at its assertion, offline) → `e3311a4` (test tweaks) → GREEN `4a53a0d`. 732/0, pytest 3137, mutations 4/4. A first "MISSED" came from an invalid-regex bats filter (0 tests ran) and was re-run with a valid one.

## [2026-10-18] Live merge run 5 (4.3): Stage D clean of MEDIUM+ — Ste: "Fix bitbucket test, then merge"
- **A** OK (38 ahead). **B:** 26 files (0 py, 0 sh), `check_conventions … Passed`, `no diff source` 0, rc 0/0, guard clean. **B-commit** no-op. **C** Ruff S 0 / ShellCheck 0. **D:** 0C / 0H / 0M / 4L → reviewer notes.
- The L-058 breach (an E2 test origin at `https://bitbucket.org/x/y.git`; it reads `git remote -v` only, never pushes) was fixed to `.invalid`. This is a test-only change, so the e_remote suite was re-run and passes (9/9). The skill blocks reviewed in run 5 are unchanged.
- The other 3 LOWs (F guard: deny-list and substring match; the E2 prompt's second option) → TODOS ("deferred §6.8 INFOs").
- Run 5 continues E1 → G4 with no restart.
