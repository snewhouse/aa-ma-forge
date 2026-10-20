# What contract do gh CLI v2.46.0's `pr checks` / `pr create` / `pr view` / `pr merge` / REST body PATCH, and git's remote-branch delete and probe, offer a bash merge script?

**Created:** 2026-10-20
**Author:** aa-ma-researcher (Claude), for sole-dev-merge-simplify plan
**Reviewed-Through-Date:** 2026-10-20 (cli/cli source at tag `v2.46.0`, git source at tag `v2.53.0`, GitHub docs fetched on this date)
**Valid-Through:** until the installed gh leaves 2.46.0 (`/usr/bin/gh`, `gh version 2.46.0 (2025-12-13 Ubuntu 2.46.0-4)`) or git leaves 2.53.0. Newer gh changes `pr checks` (`--json`, documented exit 8) and `pr edit` (projects v1 fetch gated, v2.82.1). Also invalid if branch protection, rulesets or auto-merge get turned on for `snewhouse/aa-ma-forge`.
**Sources:**
- https://github.com/cli/cli/blob/v2.46.0/pkg/cmd/pr/checks/checks.go — `pr checks` flow, watch loop, exit mapping, "no checks reported"
- https://github.com/cli/cli/blob/v2.46.0/pkg/cmd/pr/checks/aggregate.go — how each check state maps to a bucket and a count
- https://github.com/cli/cli/blob/v2.46.0/pkg/cmd/pr/checks/output.go — non-TTY row format
- https://github.com/cli/cli/blob/v2.46.0/cmd/gh/main.go — process exit codes 0/1/2/4/8
- https://github.com/cli/cli/blob/v2.46.0/pkg/cmdutil/errors.go — SilentError / PendingError / CancelError
- https://github.com/cli/cli/blob/v2.46.0/pkg/cmd/pr/create/create.go — `pr create` push gate, existing-PR check, URL on stdout
- https://github.com/cli/cli/blob/v2.46.0/pkg/cmd/pr/shared/finder.go — how a PR is chosen (no arg, number, branch)
- https://github.com/cli/cli/blob/v2.46.0/api/queries_pr.go , https://github.com/cli/cli/blob/v2.46.0/api/query_builder.go — `--json` field names, Go types, `mergeCommit{oid}`
- https://github.com/cli/cli/blob/v2.46.0/pkg/cmd/pr/merge/merge.go , https://github.com/cli/cli/blob/v2.46.0/pkg/cmd/pr/merge/http.go — merge flow, `expectedHeadOid`, branch deletion
- https://github.com/cli/cli/blob/v2.46.0/git/client.go , https://github.com/cli/cli/blob/v2.46.0/pkg/cmd/factory/default.go — the git commands gh runs (current branch, checkout, `branch -D`)
- https://github.com/cli/cli/blob/v2.46.0/pkg/cmd/pr/edit/edit.go — `pr edit` always asks for `projectCards`
- https://github.com/cli/cli/blob/v2.46.0/pkg/cmd/api/fields.go , https://github.com/cli/cli/blob/v2.46.0/pkg/cmd/api/api.go — `gh api -F k=@file`, exit on HTTP > 299
- https://github.com/cli/cli/issues/7401 — maintainers declined a "wait for checks to appear" mode (closed not_planned)
- https://github.com/cli/cli/issues/11983 , https://github.com/cli/cli/issues/11986 , https://github.com/cli/cli/pull/11987 — Projects (classic) error in `pr edit`; fixed in v2.82.1
- https://docs.github.com/en/graphql/reference/pulls — `MergePullRequestInput.expectedHeadOid`, `MergeStateStatus`, `PullRequestState`
- https://docs.github.com/en/rest/pulls/pulls#update-a-pull-request — PATCH body; 200/403/422
- https://docs.github.com/en/rest/pulls/pulls#merge-a-pull-request — REST merge `sha` returns 409 on a head mismatch
- https://cli.github.com/manual/gh_pr_checks — current manual: "Additional exit codes: 8: Checks pending"
- https://git-scm.com/docs/git-ls-remote , https://git-scm.com/docs/git-push — documented `--exit-code` and `--delete` behaviour
- https://github.com/git/git/blob/v2.53.0/builtin/ls-remote.c , https://github.com/git/git/blob/v2.53.0/remote.c , https://github.com/git/git/blob/v2.53.0/transport.c , https://github.com/git/git/blob/v2.53.0/builtin/push.c , https://github.com/git/git/blob/v2.53.0/builtin/branch.c , https://github.com/git/git/blob/v2.53.0/branch.c , https://github.com/git/git/blob/v2.53.0/builtin/checkout.c — git exit paths, plus the worktree guards on checkout and `branch -D`
- Local: `gh pr checks|create|merge|view|api --help` and `gh help exit-codes` (2.46.0); `timeout --help` (coreutils)

## Answer
In gh 2.46.0, `pr checks` exits 0 when no check is failing and none is pending, 1 on any failure and on every error (including "no checks reported"), and 8 when checks are pending (only without `--watch`). `--watch` does **not** wait for checks to appear: the first fetch happens before the loop, so a missing check set exits 1 at once. `pr create --head` never pushes. On success it prints only the PR URL to stdout. If an open PR already exists it exits 1, with the existing URL on stderr. `pr merge` checks the head with `expectedHeadOid` and merges at once when the merge state is not BLOCKED/BEHIND/DIRTY. It prints nothing on success when stdout is not a TTY. `--delete-branch` runs `git checkout <base>` / `git branch -D` locally, and git refuses both when another worktree has the branch checked out. `pr edit` always asks GraphQL for `projectCards`, which GitHub now rejects, so `PATCH /repos/{o}/{r}/pulls/{n}` is the reliable way to set the body.

## Evidence

Base for gh cites: `B = https://github.com/cli/cli/blob/v2.46.0/`. For git cites: `G = https://github.com/git/git/blob/v2.53.0/`.

### 0. Process exit codes (every gh command)
- The codes are `exitOK=0, exitError=1, exitCancel=2, exitAuth=4, exitPending=8` (B`cmd/gh/main.go#L38-L42`).
- `SilentError` gives 1 with no message. `PendingError` gives 8. A user cancel or interrupt gives 2. An `AuthError` gives 4. A `NoResultsError` gives 0. Any other error is printed to stderr and gives 1 (B`cmd/gh/main.go#L124-L168`; B`pkg/cmdutil/errors.go#L34-L41`).
- Flag errors (`FlagErrorf`) take the generic path: they print usage and exit 1 (B`cmd/gh/main.go#L150-L168`).
- `gh help exit-codes` in 2.46 lists only 0/1/2/4 and warns that commands may add more. The 2.46 `pr checks --help` does **not** mention 8; the current manual does ("Additional exit codes: 8: Checks pending", https://cli.github.com/manual/gh_pr_checks). The 8 still exists in 2.46 code (see §1).
- If a script wraps gh in `timeout`, `timeout` itself exits 124 when the time runs out, and 137 on SIGKILL (`timeout --help`).

### 1. `gh pr checks <n>` / `--watch --interval N --fail-fast`
- **Flag rules:** `--fail-fast` without `--watch` is a flag error, and so is `--interval` without `--watch`. Both exit 1 (B`pkg/cmd/pr/checks/checks.go#L65-L72`). The default interval is 10 s (B`…/checks.go#L97`).
- **Final exit:** any `Failed > 0` gives `SilentError` (1). Otherwise `Pending > 0` gives `PendingError` (8). Otherwise 0 (B`…/checks.go#L219-L225`).
  - **Failed** covers `ERROR, FAILURE, TIMED_OUT, ACTION_REQUIRED`.
  - **Pending** covers every unrecognised state (`EXPECTED, REQUESTED, WAITING, QUEUED, PENDING, IN_PROGRESS, STALE`).
  - **Not failures:** `SUCCESS` is pass. `SKIPPED`/`NEUTRAL` are skipping. `CANCELLED` is cancel, which is **not** counted as failed, so a run whose only non-pass check was cancelled exits **0** (B`…/aggregate.go#L67-L83`).
  - In non-TTY output a cancelled row still *prints* `fail` in the STATUS column (B`…/output.go#L50-L56`). The exit code and the text disagree here.
- **Non-TTY stdout:** one tab-separated row per check: `NAME, STATUS(bucket), ELAPSED, URL, DESCRIPTION` (B`…/output.go#L50-L63`, `#L94-L100`). The summary line is printed only on a TTY (B`…/output.go#L88-L91`).
- **"No checks yet":** if the status rollup has no contexts, the command errors with `no checks reported on the '<headRefName>' branch`. With `--required` and no required checks, the error is `no required checks reported on the '<branch>' branch`. With no commit, it is `no commit found on the pull request` (B`…/checks.go#L257-L258`, `#L273-L280`). All three are plain errors, so they print to stderr and exit **1**, the same code as a CI failure.
- **`--watch` does not wait for checks to appear.** The first `populateStatusChecks` call runs *before* the loop, and its error is returned at once (B`…/checks.go#L159-L162`). Inside the loop, an error on a later fetch also breaks out and returns 1 (B`…/checks.go#L199-L208`). The maintainers declined to add a wait or a separate exit code, saying the API gives no sign that checks are scheduled (https://github.com/cli/cli/issues/7401, closed `not_planned` 2023-07-17).
- **Watch loop:** it exits when `Pending == 0`, or with `--fail-fast` on the first poll where `Failed > 0`, and otherwise sleeps `Interval` (B`…/checks.go#L176-L203`). So with `--watch`, the outcome is 0 or 1 (or an outside kill). It never returns 8: the loop only exits with pending checks left if `--fail-fast` fired, and then `Failed > 0` takes priority and gives 1.
- **Stdout in watch mode:** after the loop, the summary and table are printed again to the normal screen (B`…/checks.go#L210-L217`). In non-TTY mode every poll appends a table to stdout.
- **No-arg selection:** the same as `pr view` (§3).

### 2. `gh pr create --base B --head H --title T --body-file F`
- **No push with `--head`.** `isPushEnabled` is set true only when `--head` is empty (B`pkg/cmd/pr/create/create.go#L569-L582`), and `handlePush` pushes only when `IsPushEnabled` (B`…/create.go#L909-L935`). The help says the same: "Use `--head` to explicitly skip any forking or pushing behavior" (`gh pr create --help`). The head branch must already be on the remote.
- **Non-interactive path:** `--body-file` sets `BodyProvided` (B`…/create.go#L178-L185`). Title plus body goes straight to submit with no prompt (B`…/create.go#L317-L323`). With no TTY, a missing title or body is a flag error, exit 1 (B`…/create.go#L194-L196`). An empty title is an error (`pull request title must not be blank`, exit 1).
- **Existing PR:** before creating, gh looks for an **OPEN** PR whose head label equals `H` and whose base equals `B`. If one exists, it fails with `a pull request for branch "H" into branch "B" already exists:\n<URL>`: stderr, exit **1**, and the existing URL on the second line of stderr (B`…/create.go#L285-L298`). Closed or merged PRs on the same branch name do not block. A same-named branch on a fork does not match, because the head label is `owner:branch` for a cross-repository PR (B`pkg/cmd/pr/shared/finder.go#L357-L361`; `HeadLabel` at B`api/queries_pr.go#L299-L304`).
- **Stdout on success:** exactly `pr.URL` and a newline, printed whether or not stdout is a TTY (B`…/create.go#L736-L740`).
  - "Creating pull request for …" goes to stderr, and only when gh can prompt (B`…/create.go#L310-L315`).
  - `Warning: N uncommitted change(s)` goes to stderr (B`…/create.go#L584-L586`).
  - If the API returned a PR object *and* an error, the URL is still printed, and the command then fails with `pull request update failed: …` (exit 1) (B`…/create.go#L736-L746`).

### 3. `gh pr view <n|branch> --json state,headRefName,headRefOid,isCrossRepository,mergeCommit,url,number`
- **Field types,** from the Go struct (B`api/queries_pr.go#L19-L55`, `#L236-L238`):
  - `number` is int.
  - `state` is string: one of `OPEN|CLOSED|MERGED` (https://docs.github.com/en/graphql/reference/pulls, PullRequestState).
  - `url`, `headRefName` and `headRefOid` are strings.
  - `isCrossRepository` is bool.
  - `mergeCommit` is a `*Commit`, queried as `mergeCommit{oid}` (B`api/query_builder.go#L326-L327`). It is JSON `null` until the PR is merged, then `{"oid":"<sha>"}`.
  - All seven names are in `PullRequestFields` (B`api/query_builder.go#L248-L298`).
- **Selector parsing:** a URL is parsed first. A plain integer (an optional `#` is allowed) is read as a PR number. Anything else is a branch name (B`pkg/cmd/pr/shared/finder.go#L93-L126`).
- **Branch lookup:** `pullRequests(headRefName:…, first:30, orderBy CREATED_AT DESC)` over **all states**, with OPEN sorted first. The first PR whose `HeadLabel()` equals the selector is returned (B`…/finder.go#L306-L361`). If none matches, the error is `no pull requests found for branch "X"`, exit 1 (B`…/finder.go#L363`). `NotFoundError` is not `NoResultsError`, so it does not exit 0.
- **No argument (worktree-safe):** gh runs `git symbolic-ref --quiet HEAD` in the current directory (B`git/client.go#L168-L186`, via B`pkg/cmd/factory/default.go#L149-L156`). That resolves to the linked worktree's *own* HEAD branch. gh then reads `branch.<name>.remote/merge` (B`git/client.go#L326-L328`):
  - if `merge` is `refs/pull/N/head`, PR N is used directly;
  - if the upstream is on a fork, the selector becomes `owner:branch`;
  - otherwise gh runs the branch lookup above (B`…/finder.go#L235-L274`).
  - A detached HEAD fails with `could not determine current branch: …not on any branch`, exit 1.

### 4. `gh pr merge <n> --rebase --match-head-commit <sha>` (no `--delete-branch`)
- **`--match-head-commit`** is passed as `expectedHeadOid` on the GraphQL `mergePullRequest` mutation (B`pkg/cmd/pr/merge/http.go#L77-L80`, `#L98-L103`). GitHub documents it as: "OID that the pull request head ref must match to allow merge; if omitted, no check is performed" (https://docs.github.com/en/graphql/reference/pulls). gh does **no** local SHA comparison. On a mismatch the mutation fails, gh prints `GraphQL: <message>` to stderr, and the exit code is **1**. The exact server message was not found in primary docs. The REST equivalent (`PUT …/pulls/N/merge`, `sha`) documents **409** "if sha was provided and pull request head did not match" (https://docs.github.com/en/rest/pulls/pulls#merge-a-pull-request).
- **Order of steps:** find the PR, then the merge-queue check, then the diverged warning (no-arg only), then `canMerge`, then `merge`, then delete local branch, then delete remote branch (B`…/merge.go#L517-L551`).
  - `canMerge` refuses with `SilentError` (exit 1) only for `mergeStateStatus` of `BLOCKED` ("base branch policy prohibits the merge"), `BEHIND`, or `DIRTY`. The reason goes to stderr (B`…/merge.go#L242-L271`, `#L696-L713`).
  - `CLEAN`, `UNSTABLE` (non-passing commit status), `HAS_HOOKS`, `UNKNOWN` and `DRAFT` all go on to the mutation. **gh pr merge does not check CI itself.**
  - With no `--merge/--rebase/--squash` and no TTY, it is a flag error, exit 1 (B`…/merge.go#L300-L303`).
- **Immediate merge:** with `--auto` not given, `payload.auto = false` unless the PR has a merge queue (B`…/merge.go#L291-L298`, `#L510-L512`). So the plain `mergePullRequest` mutation runs **synchronously**, and the merge happens in that call when nothing blocks it. Read-only probe on 2026-10-20 of `snewhouse/aa-ma-forge`: `main` `protected:false`, branch rules `[]`, `allow_auto_merge:false`, `allow_rebase_merge:true`, `delete_branch_on_merge:false` (`gh api repos/snewhouse/aa-ma-forge`, `…/branches/main`, `…/rules/branches/main`). So there is no BLOCKED state from policy, and the PR merges at once.
- **Already merged:** `merged = pr.State == "MERGED"` makes `merge()` a no-op. It warns `Pull request X#N was already merged` on stderr and exits **0** (B`…/merge.go#L274-L277`, `#L378-L388`, `#L507`).
- **Output:** success lines ("✓ Rebased and merged pull request …") go through `infof`, which prints **only when stdout is a TTY**, and to stderr (B`…/merge.go#L362-L369`, `#L476-L482`). Under a non-TTY script a successful merge is silent with exit 0. Confirm the result with `gh pr view N --json state,mergeCommit`.
- **Why `--delete-branch` fails from a linked worktree:**
  - `deleteLocalBranch` runs when `--delete-branch` is set, `--repo` is not given, and the head branch exists locally (B`…/merge.go#L123-L124`, `#L390`, `#L511`). Local branches are shared by all worktrees.
  - If the current branch is the PR head, gh runs `git checkout <base>` (or `git checkout -b <base> --track <remote>/<base>`), then `git pull` (B`…/merge.go#L404-L431`; commands at B`git/client.go#L387-L403`).
  - git refuses to switch to a branch that another worktree uses: it dies with `'%s' is already used by worktree at '%s'` (G`branch.c#L855-L857`, called from G`builtin/checkout.c#L1575-L1581`, `#L1659-L1664`). `main` is checked out in the main worktree, so this fails.
  - If the current branch is *not* the head, gh runs `git branch -D <head>` (B`git/client.go#L374-L375`). That fails with `cannot delete branch '%s' used by worktree at '%s'` when the head is checked out in a linked worktree (G`builtin/branch.c#L266-L273`).
  - Either way gh returns an error, exit **1**, *after* the merge has already happened. `deleteRemoteBranch` never runs, so the remote branch survives (B`…/merge.go#L542-L548`).
  - When remote deletion does run, it uses the API and ignores a 422 (ref already gone) (B`…/merge.go#L446-L463`).

### 5. Setting the PR body: REST PATCH vs `gh pr edit`
- **REST:** `PATCH /repos/{owner}/{repo}/pulls/{pull_number}`, all body fields optional (`title`, `body`, `state` open|closed, `base`, `maintainer_can_modify`). It returns 200, 403 or 422 (https://docs.github.com/en/rest/pulls/pulls#update-a-pull-request).
  - In gh 2.46, `gh api -X PATCH repos/{owner}/{repo}/pulls/N -F body=@file` reads the file verbatim as a string (`@` prefix, B`pkg/cmd/api/fields.go#L154-L161`). `{owner}`/`{repo}` placeholders are filled in for `-F` values (same function, `#L175`), and gh's api help says the endpoint argument takes them too (`gh api --help`).
  - Any HTTP status above 299 prints `gh: <message> (HTTP nnn)` to stderr, sets `SilentError`, and exits 1 (B`pkg/cmd/api/api.go#L447-L459`).
- **Why `gh pr edit` fails:** `editRun` always asks the finder for `projectCards` (plus `projectItems`), *whichever* flags are used (B`pkg/cmd/pr/edit/edit.go#L177-L184`). The GraphQL selection is `projectCards(first:100){…}` (B`api/query_builder.go#L318-L319`). GitHub now rejects that Projects (classic) field with `GraphQL: Projects (classic) is being deprecated in favor of the new Projects experience, see: https://github.blog/changelog/2024-05-23-sunset-notice-projects-classic/. (repository.pullRequest.projectCards)`, reported against gh 2.45 with `--body-file` (https://github.com/cli/cli/issues/11983).
  - Because the lookup fails, the edit is never sent, and the command exits 1 (`if err != nil { return err }`, B`…/edit.go#L181-L184`). A `&&` chain stops there.
  - The upstream fix, "do not fetch V1 projects on unsupported GitHub hosts" (https://github.com/cli/cli/pull/11987, merged 2025-10-22, fixing https://github.com/cli/cli/issues/11986), shipped in v2.82.1. A maintainer told 2.62 users to upgrade (comment 2026-01-06 on #11983).
  - This matches forge lesson L-1309 (`~/.claude/docs/lessons.md:615-619`) and its REST workaround in `claude-code/skills/sole-dev-merge/references/stage-f-push.md:119`.

### 6. `git push origin --delete <b>` and `git ls-remote --heads origin <b>` (git 2.53.0)
- **Delete, branch present:** the ref is sent as a deletion and the push exits 0. The docs list `-` as the status flag "for a successfully deleted ref" (https://git-scm.com/docs/git-push, OUTPUT).
- **Delete, branch absent** (short name): the client-side refspec match errors with `unable to delete '<b>': remote ref does not exist` (G`remote.c#L1266-L1274`). `match_push_refs` fails, `transport_push` returns its default `-1` (G`transport.c#L1395`, `#L1430-L1431`), and push prints `error: failed to push some refs to '<url>'` (G`builtin/push.c#L390-L394`). The command returns `!!errs` = **1** (G`builtin/push.c#L445`, `#L664-L671`). An absent branch is therefore an exit-1 that looks just like a real failure; tell them apart with `ls-remote`.
- **`ls-remote` exit codes:**
  - Without `--exit-code`: **0** whenever it reached the remote, whether or not any refs matched. With `--exit-code`: **2** when nothing matched (https://git-scm.com/docs/git-ls-remote; G`builtin/ls-remote.c#L87-L89`, `#L171`).
  - **1** if the transport disconnect fails (G`…/ls-remote.c#L176-L178`).
  - Connection or authentication failures go through git's `die()` path. The exact code was not checked; see Not pursued.
- **`--heads` is deprecated** in 2.53: it is now a synonym for `--branches`/`-b` (G`…/ls-remote.c#L79-L81`; docs say it "may be removed in the future").
- **Pattern trap:** each pattern `<b>` becomes the wildmatch `*/<b>`, and wildmatch is called with flags `0`, so `*` crosses `/` (G`…/ls-remote.c#L23-L38`, `#L120`). `git ls-remote --heads origin foo` therefore also matches `refs/heads/feat/foo`. For an exact probe, use the full ref: `git ls-remote --exit-code origin refs/heads/<b>`, which gives 0 if present, 2 if absent, and anything else is an error.

## Not pursued
- Exact GraphQL error text when `expectedHeadOid` mismatches: no primary source found; only the REST 409 is documented.
- Exact exit code of `git ls-remote` / `git push` on connection or authentication failure (`die()` path in `usage.c`): not read.
- What `git push --delete refs/heads/<absent>` (fully qualified) returns from GitHub's side: that path skips the client-side check (G`remote.c#L1270-L1271`) and needs a live push, which was out of bounds.
- Whether the 2.46 non-TTY `tableprinter` prints a header row for `pr checks`: go-gh tableprinter not read.
- What `mergePullRequest` returns for `UNKNOWN`/`DRAFT` merge states, and for a disabled rebase method: server behaviour, not documented on the fetched pages.
- `gh pr checks --json` (`bucket` field) is in the current manual but missing from 2.46's flags; which release added it was not traced.
- Which gh release stopped requesting `projectCards` unconditionally (the fix for #10681, April 2025) versus the v2.82.1 fix: not traced; 2.46 is affected either way.
- Upstream `gh pr checks` after 2.46 may handle "no checks reported" differently: latest `checks.go` not diffed.
