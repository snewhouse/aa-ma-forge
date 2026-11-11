---
name: sole-dev-merge
description: GitHub PR merge for a sole developer — local fixes and checks, code and security review, push and PR, CI watch, merge and cleanup, through one tested script (sdm.sh). Run only when the user asks to merge a branch or PR.
disable-model-invocation: true
---

# /sole-dev-merge — check, review, ship, finish

The work is done by `scripts/sdm.sh` (ADR-0024; tests in `tests/commands/sdm/`). This file
says when to run each step and what to do with its output. The full list of `STATUS:` and
`ABORT:` lines, with their meaning, is `sdm.sh help`. GitHub only.

## Rules

- **Which copy.** Inside aa-ma-forge, run the branch's own
  `claude-code/skills/sole-dev-merge/scripts/sdm.sh` (the code being merged is the code that
  merges it). Anywhere else, `~/.claude/skills/sole-dev-merge/scripts/sdm.sh`. Below, `sdm.sh`
  means that path.
- **One Bash call per step.** `ship` pushes the branch and opens or updates the PR.
  `finish` merges the PR and deletes the remote branch. Run `check`, `ship` and `finish` as
  three separate Bash calls, never chained, so each side effect is visible to the operator.
- **Exit codes.** Exit 1 with an `ABORT: …` line: stop, report it, fix the cause, start
  again at step 1. Exit 0 with `STATUS: …` lines: act on each one, not only the last (table
  below). Any other non-zero exit (git or gh failed with no ABORT line): stop and report stderr.
- **No merge or delete outside sdm.sh.** Never run `gh pr merge`, `gh api …/merge`,
  `gh pr edit`, `git push --delete` or `git push origin :<branch>`, and never force-push.
  A failed step is re-run through `sdm.sh`.

## Step 1 — check

```
sdm.sh check
```

It formats in-scope Python with ruff, runs the repo's pre-commit hooks on the branch's files,
and commits any in-scope fixes as `chore(scope): pre-PR auto-fixes`. Success prints
`check OK (branch=<b>, base=<ref>, ahead=<n>)`; keep `<ref>` for the review diff.
A non-zero `check: pre-commit rc=<n>` is reported, not fatal: give it to C1; CI gates it.

**Inspect the auto-fix commit (L-031).** When `check` says it committed in-scope auto-fixes,
compare `git show --stat HEAD` with the branch's own changes (`git diff --stat <ref>...HEAD~1`),
and read `git show HEAD -- <file>` for any file the branch only partly changed. ruff formats
whole files, so the commit can change lines the branch never touched. If it does, stop and ask
the user: that drift belongs in its own `chore(format)` PR from the default branch. Re-running
`check` would only make the same commit again.

**Out-of-scope ABORT.** `ABORT: check: files outside the branch changed: …` means a fixer changed
files the branch does not touch. Nothing is committed, so the tree is left dirty and a bare re-run
stops at "Uncommitted changes". Work in the checkout `check` ran in (its toplevel), never another:
1. Show the user the listed files, `git status --porcelain` and `git diff --stat`. The tree was
   clean when `check` started, so these should all be a fixer's; an edit saved while `check` ran
   is not. Ask the user before discarding anything.
2. Once the user agrees, `git restore --staged --worktree -- .` from that toplevel undoes the
   tracked changes. Remove an untracked file only with the user's yes.
3. Fix the cause (the hook that touched other files), or commit that change on the branch, but
   only with the user's yes: the same fixer makes the same ABORT again. Then start again at step 1.

## Step 2 — review (C1 + C2) and the stop rule

1. Make a private run dir with `umask 077; mktemp -d` and use `<dir>/notes.md` as the notes
   file. Note the HEAD you review (`git rev-parse HEAD`): round 2 needs it.
2. In one message, dispatch two agents on `git diff <ref>...HEAD`:
   - **C1** `code-reviewer`: correctness, regressions, scope, KISS/DRY, dead code.
   - **C2** `security-auditor`: input validation, secrets, injection, path handling, OWASP.
   - Both apply `security-auditor.md` § Threat model (local tooling unless the plan's
     Contract says otherwise): CRITICAL/HIGH need a concrete failure path reachable under it.
     Each finding is one line, `[CRITICAL|HIGH|MEDIUM|LOW] <claim> — <path>:<line>`, followed
     by one line giving the failure path.
3. Triage:
   - **CRITICAL/HIGH** go to the user with `AskUserQuestion`: Apply / Dispute / Defer.
     Apply → fix it test-first, commit, run step 1 again, then round 2.
   - **MEDIUM/LOW** never restart the run. They go to the notes file and, after the merge,
     to one TODOS.md entry for this PR (no TODOS.md in the repo: list them in your final
     report instead).
4. **Round 2** reviews only the fix: `git diff <round-1 HEAD>..HEAD`.
5. **At most 2 rounds.** There is no round 3. If a CRITICAL/HIGH is still open after
   round 2, do not run `ship`: report it to the user and re-plan.
6. Never run `ship` while an accepted CRITICAL/HIGH is unfixed.

Notes file rules (it becomes the PR body's "Reviewer notes"):
- Append; never overwrite. Start each round with a `### Round <n>` line.
- One line per finding, plus the rounds' totals. For a security finding, name the class and
  `path:line`, not the steps to exploit it. Never quote a secret, token or credential value.
- No GitHub closing keywords (`Closes #12`, `Fixes #12`): they would close an issue on
  merge (accepted risk, ADR-0024).

## Step 3 — ship

```
sdm.sh ship --notes <dir>/notes.md
```

`ship` pushes the branch, then creates the PR or updates the open PR's body, then waits
for CI. When an AA-MA plan is active, prefix `AA_MA_PLAN_DIR=.claude/dev/active/<task>` to
add a "Plan context" line to the body. It prints `PR_NUM=<n>`, `PR_URL=<url>` and finally
`CI_STATE=green|failed|timeout`.
- `green` → step 4.
- `failed` → report the `diagnostic:` line. Fix the failure on the branch test-first, then
  start again at step 1. A re-run of `ship` updates the same PR's body.
- `timeout` → CI is still running. Run step 4 later; `finish` gates on CI itself.

## Step 4 — finish

```
sdm.sh finish <PR_NUM>
```

`finish` merges only when every check-run at HEAD has completed, at least one succeeded and
none failed. It merges with `--match-head-commit`, deletes the remote branch under a lease,
checks with `ls-remote` that the branch is gone, then fast-forwards the default branch.
It can print more than one STATUS line (for example `BRANCH_NOT_DELETED`, then `STATUS: OK`
for the cleanup); act on each. In a linked worktree `STATUS: OK` ends ` worktree=<path>`, and
`finish` prints "Operator cleanup" commands (`worktree remove`, `branch -D`). Show them to
the user; do not run them unasked.

## What to do with a STATUS line

| Line | Do |
|---|---|
| `STATUS: AUTH_REQUIRED` | Ask the user to run `! gh auth login`, then `ship` again. |
| `STATUS: PR_BODY_NOT_UPDATED … reason=patch-failed` or `readback-differs` | `ship` went on. Tell the user to set the PR body by hand before `finish`. |
| `STATUS: PR_BODY_NOT_UPDATED … reason=not-this-branch`, `no-pr-number`, `not-open` or `head-not-updated` | `ship` stopped. Report it; never edit another branch's or a closed PR. |
| `STATUS: CI_FAILED` | Nothing is merged. Report the URL and `gh pr checks <n>`. |
| `STATUS: CI_TIMEOUT`, `STATUS: CI_NOT_DONE` | Nothing is merged. Run `sdm.sh finish <n>` later. |
| `STATUS: MERGE_FAILED` | Nothing is deleted. Report the state and URL. If the remote head moved, fetch, review what changed and start again at step 1; never force-push. A conflict or branch protection goes to the user. |
| `STATUS: BRANCH_NOT_DELETED` | Merged, but the remote branch is still there. If it moved after the merge, it holds commits not on the default branch: report them; the user decides. If only the delete failed: from a linked worktree, run `sdm.sh finish <n>` again (a PR already MERGED at HEAD gets no merge call, no strategy or check-runs read, only the delete and cleanup); from a plain checkout the local branch is gone, so tell the user to delete the remote branch. |
| `STATUS: MAIN_NOT_UPDATED`, `STATUS: MAIN_CHECKOUT_DIRTY` | Merged. The default branch was not updated: report the reason; the user updates it. |

Any other line: read `sdm.sh help`.

## After the merge

File the MEDIUM/LOW findings (step 2) as one TODOS.md entry in the next commit on the
default branch, or on the active plan's next branch (L-037).

## Settings

Environment variables, all optional, operator-set (defaults and validation: the top of
`sdm.sh`):
- `CI_POLL_TIMEOUT`: the CI watch cap.
- `CI_APPEAR_TIMEOUT_S` and `CI_APPEAR_INTERVAL_S`: the wait for checks to appear.
- `AA_MA_PLAN_DIR`: adds the plan context line.
- `AA_MA_FOOTER_HELPER`: the footer helper for the auto-fix commit; else the repo's copy,
  else `${CLAUDE_HOME:-~/.claude}/hooks/lib/aa-ma-footer.sh`, else `[ad-hoc]`.

History: the stage-block design this replaces is ADR-0008; why one script is ADR-0024.
