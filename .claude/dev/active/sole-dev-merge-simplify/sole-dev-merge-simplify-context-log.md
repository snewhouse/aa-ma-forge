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
