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
