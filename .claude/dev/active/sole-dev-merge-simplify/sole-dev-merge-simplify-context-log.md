# sole-dev-merge-simplify Context Log

_This log captures architectural decisions, trade-offs, and unresolved issues._

## [2026-10-20] Initial Context

**Feature Request (Phase 1):**
"/aa-ma-plan the /sole-dev-merge simplification" (retro `.claude/dev/completed/sole-dev-merge-fixes/sole-dev-merge-fixes-retro-2026-10-20.md` §4 item 6).

**Key Decisions (Phase 2 grill):**
- **AD-001 (Q1):** Rewrite as one script, `sdm.sh` (`check` / `ship` / `finish`), bats-tested. Decided with Ste 2026-10-20.
  - Rationale: 1,994 lines, 77% markdown-embedded bash forced a state file and 13 loader copies (L-060–L-062).
- **AD-002 (Q2):** Drop GitLab; GitHub only (CHANGELOG "Removed"). Decided with Ste 2026-10-20.
- **AD-003 (Q3):** Drop local Ruff S and ShellCheck; CI gates them. Decided with Ste 2026-10-20.
- **AD-004 (Q4):** Keep pre-commit (best-effort, changed files); drop pytest (and mypy). Decided with Ste 2026-10-20.
- **AD-005 (Q5):** Two milestones, a live run gating each (old skill stays the fallback until M2). Decided with Ste 2026-10-20.
- **AD-006 (Q6):** `check` stops on out-of-scope dirt and names the files; it never restores. Decided with Ste 2026-10-20.
- **AD-007 (Q7):** The original release decision was superseded at verification (Angle 3 CRITICAL): this plan cuts no release; its changes ship in code-conventions-impact M14's v0.18.0. Decided with Ste 2026-10-20.
- **AD-008 (Q8):** Keep both reviewers (C1 code-reviewer, C2 security-auditor) and the Stage D stop rule as SKILL.md steps. Decided with Ste 2026-10-20.
- **AD-009:** Engineering standards: all six themes declared (plan §2). Decided with Ste 2026-10-20.
- **AD-010:** Prototype-Required: M1 YES (1.0 prototype merges a real PR first), M2 NO. Decided with Ste 2026-10-20.
- **AD-011:** Phase 4.2 reviews skipped. Decided with Ste 2026-10-20.
- **AD-012:** Plan verification automated (6 angles). Decided with Ste 2026-10-20.

**Alternatives rejected (plan §4):**
- `gh pr merge --auto`: with no branch protection it merges at once, without CI.
- A Python CLI: the work is git/gh orchestration; bash needs no venv.
- A bare checklist: loses the L-1332/L-052/L-1309 fixes.
- Interim cut only: Ste chose the rewrite.

**Research Findings (Phase 3):**
- `docs/research/sole-dev-merge-simplify-gh-cli-merge-contract.md`: gh 2.46 `pr checks` exits 1 on "no checks reported" and 0 on a cancelled check; `--watch` does not wait for checks to appear; `pr merge` ignores CI and merges UNSTABLE at once; `--match-head-commit` = `expectedHeadOid` (mismatch → rc 1, `GraphQL:`); `--delete-branch` fails from a linked worktree after the merge; body via REST PATCH, not `pr edit`; exact remote probe is `ls-remote --exit-code origin refs/heads/<b>`.
- `docs/research/sole-dev-merge-simplify-behaviour-inventory.md`: KEEP/DROP behaviour list per subcommand; 199 tests → 102 to port (79 KEEP + 23 CHANGE), 97 drop; external files M2 must touch; 7 moot TODOS entries.

**Verification:**
- `sole-dev-merge-simplify-verification.md` — rev 4, automated, PASS WITH WARNINGS; 6 CRITICAL found, 6 resolved, 0 open.

**Remaining Questions / Unresolved Issues:**
- None blocking. Prototype findings are recorded at Sub-step 1.0 (`PROTOTYPE FINDINGS: n=<k>`).

## [2026-10-20] Milestone 1 started — pre-execution validation and Sub-step 1.0 decisions
- **Validator (pre-execution): WARN, 0 FAIL.**
  - W1: plan.md:233 / reference.md:49 changed after verification rev 4 (`19c86147`, "finish accepts MERGED at HEAD"). That change was the Round-1 HIGH from the plan's own /sole-dev-merge run; it is recorded here, not as a rev 5.
  - W2: the MERGED-at-start path had no test. Added to 1.1 as new test 14.
  - W3: provenance now records the plan-merge commits `8d27da91` and `19c86147`.
  - W4: M2 has no RED step and no TDD-Waiver. Decide at M2 start.
- **1.0 HITL (Ste): Proceed.** Live push / PR / rebase-merge of the TODOS-only chore PR on public `snewhouse/aa-ma-forge`.
- **Lease probe (Ste): yes.** The prototype's `finish` deletes the remote branch with `--force-with-lease=refs/heads/<b>:<sha>` (TODOS "review notes for M1", round 2 MEDIUM). If it holds live, the contract line and a 1.1 test follow.
- **Where M1 tracking lives:** 1.0's start sync rides the chore PR (docs only). 1.0's Result Log, and everything after it, goes on `refactor/sdm-script`, cut from main after the chore merge (L-037).
- **TODOS triage correction:** the inventory called entries 25, 81, 88, 96, 104, 119 and 157 moot. All 7 are closed, but only 81, 96 and 119 were wholly moot:
  - 25: the 4 security-static-check bullets stay open, split into their own entry.
  - 88 bullet 3 (C-quoted, unescaped names): carried to 1.1.
  - 104: folded into the sdm.sh contract (host match, `--match-head-commit`, lease, PR_NUM pattern).
  - 157: notes and round-cap items carried to an M2 SKILL.md entry.
  - Each closure line says where its bullets went.
- **Inventory line refs shifted:** the "still apply" 196/200/354 (at `04d2490`) are now the `emit_aa_ma_footer` helper, footer-only-inside-forge and install.sh-backup entries. The new "review notes for M1" entry (P2, before 1.1) is deferred work for this milestone (L-056).

## [2026-10-20] Sub-step 1.0 — PROTOTYPE FINDINGS: n=6
Prototype `1fdfd468` merged PR #53 end to end on its first run (check → ship → finish, 1 merge run). Verdict: the design holds; no plan risk falsified.
1. **Test seam (changes sdm.sh):** `sdm_slug` must read origin's configured URL (`pushurl`, else `url`). `get-url --push` expands `insteadOf`, so the tests' local-forge rewrite would hide `github.com`. A real-config `insteadOf` alias is then refused as "not github.com"; there is none on this machine (`git config --get-regexp ^url\.` is empty).
2. **Lease delete (changes contract):** `--force-with-lease=refs/heads/<b>:$SHA` worked live; a stale lease is refused and `ls-remote` rc 0 → `BRANCH_NOT_DELETED`. M1 Contract line "push origin :refs/heads/<b>" now reads with the lease; 1.1 new test 15: a remote branch moved after the merge is kept and reported.
3. **G4 diff --stat dropped in the prototype:** the old G4 printed `git diff --stat <branch> <default>` before the cleanup commands (L-1332 content check). Restore it in 1.2 if a ported G4 test asserts it; otherwise keep it out (KISS).
4. **Tests:** `safe.bareRepository=explicit` on this machine means `git --git-dir=` for the bare forge. The commit-signature hook reads `git commit` in any Bash command, so fixtures keep plumbing commits (`mkcommit`).
5. **Stdout discipline works:** `ship` printed only `PR_NUM`/`PR_URL`/`CI_STATE`; git's `remote:` lines went to stderr. bats `run` merges streams, so exact-output tests use `run --separate-stderr`.
6. **Upstream config is irrelevant:** both worktrees were cut with `-b … origin/main` (upstream origin/main). The lookup by explicit branch with `-R` found nothing before create and the right PR after, so no no-arg gh call remains.

## [2026-10-20] Sub-step 1.1 — RED design decisions
- **Output spec fixed before the port** (session scratch `sdm-spec.md`; GREEN's exit table becomes its canonical home): stdout carries STATUS/ABORT, `check OK`, `check: pre-commit rc=`, the three ship lines, hints, cleanup and `Final:`; everything else goes to stderr. Exit 0 = success or STATUS, 1 = ABORT.
- **Dropped as unreachable (YAGNI):**
  - the L-048 post-staging "staged outside" assert. The clean-start ABORT plus the pre-staging dirt check catch every out-of-scope staged path first (the check agent showed no test can reach it).
  - `finish`'s branch-name `check-ref-format`: the branch comes from `git branch --show-current`, and git cannot create a name that check rejects.
- **No `--untracked-files=all`:** a fixer-recreated file the branch deleted reads as `?? d/`, out of scope, so check ABORTs. With `-uall`, check would commit the re-added file (the old TODO 88 bullet 2 bug). Aborting is the safer default.
- **Old tests re-expressed:** `check` now refuses a dirty tree at start, so every drift scenario is created during check by the pre-commit stub (`PRE_COMMIT_RUN`). `:392`/`:494` now expect the out-of-scope ABORT; `:419`/`:434`/`:464` assert the earlier ABORT with the index unchanged. `g_poll:69`'s `--auto` hint is replaced by the `sdm.sh finish` hint (new 4).

## [2026-10-22] GATE APPROVAL: Milestone 1: sdm.sh beside the old skill, proven live
- Gate: HARD
- Approved by: Ste
- Criteria verified: 6/6
- Decision: APPROVED

## [2026-10-22] Milestone Completion: Milestone 1: sdm.sh beside the old skill, proven live
- Status: COMPLETE
- Key outcome: `claude-code/skills/sole-dev-merge/scripts/sdm.sh` (352 lines, 150 bats tests) merged three real PRs (#53 prototype, #56 deps, #55 itself); the old skill is unchanged and still the fallback until M2.
- Artifacts: sdm.sh; tests/commands/sdm/{check,ship,finish}.bats + fixtures; security.yml step; impl-review.md; TODOS entries ("sdm.sh M1 §6.8 review notes", "sdm.sh M1 PR review (C1/C2, round 1)").
- Tests: sdm 150/150, old suite 199/199, `bats -r tests` 962 (TESTS_VERIFIED), pytest 3142 passed.
- Decisions this milestone (Ste): §6.8 CRITICAL accepted and fixed; pip-audit advisories fixed in a separate deps PR (#56), no force-push; the live head-lag bug fixed now (merge run 3).
- Evidence for L-061: the one bug that bit in live use (head lag) had been rated WARNING by §6.8; the stub suite could not show it. Merge runs: 3 vs target 1 — one external (advisories), one real bug.
- Sub-step 2.0's ACs (SHA map in reference.md, M1 `pending_steps=0`, this GATE APPROVAL, recorded on `refactor/sdm-switch-over`) are met by this commit; M2 marks 2.0 when it starts.
- Next: Milestone 2 — Dependencies: Milestone 1. Open before M2 (P2): the failure-line items in TODOS "sdm.sh M1 §6.8 review notes" (M2's SKILL.md relies on ABORT lines), and validator W4 (M2 has no RED step and no TDD-Waiver).

## [2026-10-22] Pre-M2 decisions (Ste, session fixin-thursdaty-01 resume; handover §9)
- Handover evidence E1–E14 re-run: all match. Extra worktree `.worktrees/prototype/codemem-refresh-cap` belongs to code-conventions-impact; untouched.
- **Q1 = A:** the P2 sdm.sh items land as a separate PR, `fix/sdm-failure-lines` from fresh main, before M2: ABORT line on a rejected `git push` (ship) and on a hook-refused auto-fix commit (check); guarded cleanup `fetch`/`rev-parse` after a merge; `BASE_REF` prefers `origin/<d>`; the head wait re-reads `state` and stops on a non-OPEN PR. The M2 branch is not rebased (pushed; `pull_request` CI tests the merge ref).
- **Q4 = add to that PR:** ship silent paths (`--notes` missing path; a failed `gh pr checks` re-read reporting green); input validation (`CI_POLL_TIMEOUT`, URL userinfo cut at the last `@`); named constants; ship/finish LOWs (strategy read after `PR_NUM`, clean-tree check before a plain-checkout `finish` switches branch, `timeout 30` on the head-wait re-reads). Each gets its own RED first. Not taken: pre-commit `./` prefix, PR title after auto-fix, `ssh.github.com:443`, stub/test LOWs; they stay in TODOS.
- **Q2 = D:** validator W4 closed by a RED step: 2.1 revived as "RED — a test of SKILL.md's shape" (`tests/skills/test_sole_dev_merge_skill.py`); 2.2 now depends on 2.1. plan.md 2.1 carries a dated amendment note.
- **Q3 = delete:** `.worktrees/prototype/sdm-script` removed and local branch `prototype/sdm-script` deleted (was `ca5aaff9`; never pushed, `ls-remote` rc 2; no keep decision recorded, L-1350). PROTOTYPE line and findings stay in provenance and this log.
- TODOS "review notes for M1": 4 items marked done after checking each (tasks.md 1.2 AC, 1.4 Result Log, `ship.bats` "new: 1" + exit table, lease + `finish.bats` "new 15").
