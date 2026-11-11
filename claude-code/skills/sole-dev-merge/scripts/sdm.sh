#!/usr/bin/env bash
# sdm.sh — /sole-dev-merge as one script (ADR-0024): check | ship [--notes FILE] | finish <PR_NUM> | help
# Sourceable: main runs only when executed. Tests: tests/commands/sdm/.
# GitHub only. Each subcommand is one Bash call, so `ship` (push) and `finish` (merge, delete)
# stay visible to the operator. Progress goes to stderr; STATUS/ABORT and result lines to stdout.
set -euo pipefail

POLL_DEFAULT=900s        # CI watch cap (timeout(1) duration); env CI_POLL_TIMEOUT overrides
APPEAR_DEFAULT_S=120     # seconds to wait for checks to register after a push; env CI_APPEAR_TIMEOUT_S
INTERVAL_DEFAULT_S=10    # seconds between those looks; env CI_APPEAR_INTERVAL_S
GH_CALL_TIMEOUT_S=30     # seconds for one non-watch gh call: a stalled call must not outlast the caps
WATCH_INTERVAL_S=30      # seconds between --watch polls (gh's default is 10; fewer API calls)
PR_TITLE_MAX=70          # chars of the HEAD subject kept as the PR title (ADR-0008)
CHECK_RUNS_PER_PAGE=100  # GitHub's page maximum; more check-runs ABORT as "not all read"
CI_POLL_TIMEOUT="${CI_POLL_TIMEOUT:-$POLL_DEFAULT}"
CI_APPEAR_TIMEOUT_S="${CI_APPEAR_TIMEOUT_S:-$APPEAR_DEFAULT_S}"
CI_APPEAR_INTERVAL_S="${CI_APPEAR_INTERVAL_S:-$INTERVAL_DEFAULT_S}"

say() { printf '%s\n' "$*" >&2; }
die() { printf 'ABORT: %s\n' "$*"; exit 1; }

# The one footer resolver (L-054): explicit helper, this repo's copy, the ~/.claude link, else [ad-hoc].
sdm_footer() {
    local h
    for h in "${AA_MA_FOOTER_HELPER:-}" \
        "$(git rev-parse --show-toplevel)/claude-code/hooks/lib/aa-ma-footer.sh" \
        "${CLAUDE_HOME:-$HOME/.claude}/hooks/lib/aa-ma-footer.sh"; do
        # shellcheck source=/dev/null
        if [[ -n "$h" && -f "$h" ]]; then (source "$h"; emit_aa_ma_footer); return; fi
    done
    say "check: aa-ma-footer.sh not found — using the [ad-hoc] footer"
    printf '\n\n[ad-hoc]'
}

# Repo context shared by every subcommand: TOP, BRANCH, DEFAULT_BRANCH, BASE_REF (cd to TOP).
sdm_context() {
    # why: 2>/dev/null — git's "fatal:" is replaced by the ABORT line
    TOP=$(git rev-parse --show-toplevel 2>/dev/null) || die "Not inside a git repository"
    cd "$TOP"
    BRANCH=$(git branch --show-current)
    [[ -n "$BRANCH" ]] || die "Detached HEAD — check out the branch to merge"
    [[ "$BRANCH" != main && "$BRANCH" != master ]] || die "Cannot run /sole-dev-merge from $BRANCH branch"
    [[ -n "$(git remote)" ]] || die "No git remote configured (need a github.com origin)"
    # why: no origin/HEAD is normal; the default is main
    DEFAULT_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || true)
    DEFAULT_BRANCH="${DEFAULT_BRANCH:-main}"
    git check-ref-format --branch "$DEFAULT_BRANCH" >/dev/null \
        || die "DEFAULT_BRANCH '$DEFAULT_BRANCH' is not a valid branch name"
    [[ "$BRANCH" != "$DEFAULT_BRANCH" ]] || die "Cannot run /sole-dev-merge from $BRANCH branch"
    # why: origin's copy first — a local default branch can lag a web-UI merge and widen the scope
    if git rev-parse --verify -q "origin/$DEFAULT_BRANCH" >/dev/null; then BASE_REF="origin/$DEFAULT_BRANCH"
    elif git rev-parse --verify -q "$DEFAULT_BRANCH" >/dev/null; then BASE_REF="$DEFAULT_BRANCH"
    else die "Cannot resolve $DEFAULT_BRANCH or origin/$DEFAULT_BRANCH"; fi
}

# SLUG=owner/repo from origin's configured URL; never prints the URL (it can hold a token). $1 = ship|finish.
sdm_slug() {
    local url host path
    # why: the configured URL, not get-url: insteadOf expansion would hide the host (1.0 finding 1); no URL is not an error here
    url=$(git config --get remote.origin.pushurl || git config --get remote.origin.url) || die "$1: no origin remote"
    case "$url" in
        # why: userinfo ends at the authority's last '@' (a raw '@' in a password must not reach the host)
        *://*) host=${url#*://}; path=${host#*/}; host=${host%%/*}; host=${host##*@}; host=${host%%:*} ;;
        *@*:*) host=${url#*@}; path=${host#*:}; host=${host%%:*} ;;
        *)     die "$1: origin is not a github.com remote" ;;
    esac
    [[ "$host" == github.com ]] || die "$1: origin is on $host, not github.com"
    SLUG=${path%.git}
    [[ "$SLUG" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]] || die "$1: cannot read owner/repo from origin"
}

sdm_strategy() {   # rebase if allowed, else merge; an unreadable answer is never "allowed"
    local allow
    allow=$(gh api "repos/$SLUG" --jq '.allow_rebase_merge') || die "$1: cannot read allow_rebase_merge"
    case "$allow" in
        true) STRATEGY=rebase ;;
        false) STRATEGY=merge ;;
        *) die "$1: allow_rebase_merge is '$allow', not true or false" ;;
    esac
}

cmd_check() {
    sdm_context
    [[ -z "$(git status --porcelain)" ]] || die "Uncommitted changes detected (commit or stash first)"
    [[ "$(git rev-list --count "$BASE_REF..HEAD")" -gt 0 ]] || die "No commits ahead of $DEFAULT_BRANCH (nothing to merge)"
    export GIT_LITERAL_PATHSPECS=1   # why: a name like '*' is a file, never a pattern
    local -a files=() py=()
    mapfile -d '' -t files < <(git diff -z --name-only "$BASE_REF...HEAD")
    local f
    for f in "${files[@]}"; do [[ "$f" == *.py && -f "$f" ]] && py+=("$f"); done
    say "check: ${#files[@]} file(s) in scope, ${#py[@]} Python"
    if ((${#py[@]})) && ! command -v ruff >/dev/null; then
        say "check: ruff not found — Python files not formatted"
    elif ((${#py[@]})); then
        # why: best-effort; unfixable lint is the reviewers' and CI's job. --force-exclude: a named
        # file skips extend-exclude otherwise, and planted eval fixtures would be "fixed" (ADR-0021)
        ruff format --force-exclude -- "${py[@]}" >&2 || true
        # why: best-effort, as above
        ruff check --fix --force-exclude -- "${py[@]}" >&2 || true
    fi
    if [[ -f .pre-commit-config.yaml ]] && ((${#files[@]})) && ! command -v pre-commit >/dev/null; then
        say "check: pre-commit not found — hooks not run"
    elif [[ -f .pre-commit-config.yaml ]] && ((${#files[@]})); then
        local rc=0
        # why: the range in env, not flags (flags stash the fixes, ADR-0018); './' keeps '--x' a file
        PRE_COMMIT_FROM_REF="$BASE_REF" PRE_COMMIT_TO_REF=HEAD pre-commit run --files "${files[@]/#/./}" >&2 || rc=$?
        echo "check: pre-commit rc=$rc"
    fi
    declare -A scope=()
    for f in "${files[@]}"; do scope["$f"]=1; done
    local -a mine=() other=()
    local rec src
    while IFS= read -r -d '' rec; do
        f=${rec:3}
        if [[ "${rec:0:2}" == *[RC]* ]]; then IFS= read -r -d '' src; [[ -n "${scope[$src]:-}" ]] || other+=("$src"); fi
        if [[ -n "${scope[$f]:-}" ]]; then mine+=("$f"); else other+=("$f"); fi
    done < <(git status --porcelain -z)
    ((${#other[@]} == 0)) || die "check: files outside the branch changed: $(printf '%q ' "${other[@]}")(left as they are)"
    if ((${#mine[@]})); then
        git add -- "${mine[@]}"
    fi
    # why: an in-scope change undone back to HEAD stages nothing
    if ! git diff --cached --quiet; then
        local footer; footer=$(sdm_footer)
        git commit -q -m "chore(scope): pre-PR auto-fixes$footer" || die "check: auto-fix commit failed (rc=$?); the fixes are staged"
        say "check: committed in-scope auto-fixes ($(git rev-parse --short HEAD))"
    fi
    echo "check OK (branch=$BRANCH, base=$BASE_REF, ahead=$(git rev-list --count "$BASE_REF..HEAD"))"
}

# One lookup of this branch's PR (explicit branch with -R, never gh's no-arg guess from the
# upstream config); sets row num url xrepo href state oid, all empty when there is none.
sdm_pr_lookup() {
    row=$(timeout "$GH_CALL_TIMEOUT_S" gh pr view "$BRANCH" -R "$SLUG" --json number,url,isCrossRepository,headRefName,state,headRefOid \
        --jq '[.number,.url,.isCrossRepository,.headRefName,.state,.headRefOid]|@tsv' 2>/dev/null) || row=""   # why: "no pull requests found" is the normal first-run answer
    num="" url="" xrepo="" href="" state="" oid=""
    if [[ -n "$row" ]]; then IFS=$'\t' read -r num url xrepo href state oid <<<"$row"; fi
}

cmd_ship() {
    local notes=""
    case "${1:-}" in
        "") ;;
        --notes) notes=${2:-}
            [[ -n "$notes" ]] || die "ship: --notes needs a FILE"
            [[ -f "$notes" && -r "$notes" ]] || die "ship: notes file '$notes' is not a readable file"
            [[ "$notes" == /* ]] || notes="$PWD/$notes" ;;   # why: sdm_context cds to the toplevel
        *) die "ship: unknown argument '$1' (see sdm.sh help)" ;;
    esac
    sdm_context
    sdm_slug ship
    # why: the STATUS line replaces gh's message
    gh auth status >/dev/null 2>&1 || { echo "STATUS: AUTH_REQUIRED — run gh auth login"; exit 0; }
    BODY=$(mktemp); trap 'rm -f "$BODY"' EXIT
    {
        # shellcheck disable=SC2016  # why: the backticks are Markdown in the PR body, not a substitution
        printf '## Summary\n\nBranch `%s` proposes %s commit(s) ahead of `%s`.\n\n## Changes by area\n\n' \
            "$BRANCH" "$(git rev-list --count "$BASE_REF..HEAD")" "$BASE_REF"
        git log "$BASE_REF..HEAD" --format='- %s'
        printf '\n## Test plan\n\n- [ ] CI checks pass\n- [ ] Manual smoke test of changed paths\n\n## Reviewer notes\n\n'
        if [[ -s "$notes" ]]; then cat "$notes"; else echo "(none)"; fi
        echo
        [[ -z "${AA_MA_PLAN_DIR:-}" ]] || printf 'Plan context: %s\n\n' "$(printf '%s' "$AA_MA_PLAN_DIR" | tr -d '\n\r\t\b\f')"
        echo "<!-- Generated by /sole-dev-merge -->"
    } > "$BODY"
    local waited=0 out rc=0 ci=green cap=$CI_APPEAR_TIMEOUT_S step=$CI_APPEAR_INTERVAL_S
    # why: 10# — a leading zero is decimal ("09", "010"), never octal or an arithmetic error
    if [[ "$cap" =~ ^[0-9]+$ ]]; then cap=$((10#$cap))
    else say "ship: ignoring CI_APPEAR_TIMEOUT_S='$cap' (not a number) — using $APPEAR_DEFAULT_S"; cap=$APPEAR_DEFAULT_S; fi
    if [[ "$step" =~ ^[0-9]+$ ]] && ((10#$step >= 1)); then step=$((10#$step))
    else say "ship: ignoring CI_APPEAR_INTERVAL_S='$step' (not a whole number of seconds ≥ 1) — using $INTERVAL_DEFAULT_S"; step=$INTERVAL_DEFAULT_S; fi
    local poll=$CI_POLL_TIMEOUT
    # why: timeout(1) reads 0 as "no limit"; anything else it cannot parse would fail the watch, not CI
    if [[ ! "$poll" =~ ^([0-9]+)[smhd]?$ ]] || ((10#${BASH_REMATCH[1]} == 0)); then
        say "ship: ignoring CI_POLL_TIMEOUT='$poll' (not a duration > 0, e.g. 900s) — using $POLL_DEFAULT"; poll=$POLL_DEFAULT
    fi
    git push -q -u origin HEAD >&2 || die "ship: git push failed (rc=$?)"
    local head row num url xrepo href state oid reason=""
    head=$(git rev-parse HEAD)
    sdm_pr_lookup
    if [[ "$state" == OPEN ]]; then
        # why: GitHub can report the old head for seconds after a re-push (live, PR #55); same caps as the CI wait
        while [[ "$state" == OPEN && "$xrepo" == false && "$href" == "$BRANCH" && "$oid" != "$head" ]] && ((waited < cap)); do
            sleep "$step"; waited=$((waited + step)); sdm_pr_lookup
        done
        waited=0
        if [[ ! "$num" =~ ^[1-9][0-9]*$ ]]; then reason=no-pr-number
        elif [[ "$state" != OPEN ]]; then reason=not-open
        elif [[ "$xrepo" != false || "$href" != "$BRANCH" ]]; then reason=not-this-branch
        elif [[ "$oid" != "$head" ]]; then reason="head-not-updated"
        elif ! gh api -X PATCH "repos/$SLUG/pulls/$num" -F "body=@$BODY" >/dev/null; then reason=patch-failed
        elif ! cmp -s <(cat "$BODY"; echo) <(gh api "repos/$SLUG/pulls/$num" --jq .body); then reason=readback-differs
        fi
        if [[ -n "$reason" ]]; then
            echo "STATUS: PR_BODY_NOT_UPDATED — PR #$num reason=$reason"
            [[ "$reason" == patch-failed || "$reason" == readback-differs ]] || exit 0
        else say "ship: PR #$num body updated (read-back matches)"; fi
    else
        url=$(gh pr create -R "$SLUG" --base "$DEFAULT_BRANCH" --head "$BRANCH" \
            --title "$(git log -1 --format=%s | cut -c1-"$PR_TITLE_MAX")" --body-file "$BODY") || die "ship: gh pr create failed"
        num=${url##*/}
        [[ "$num" =~ ^[1-9][0-9]*$ ]] || die "ship: gh pr create printed no PR URL"
    fi
    echo "PR_NUM=$num"
    echo "PR_URL=$url"
    sdm_strategy ship   # why: after the result lines, so an ABORT here still names the open PR
    say "ship: strategy=$STRATEGY"
    while out=$(timeout "$GH_CALL_TIMEOUT_S" gh pr checks "$num" -R "$SLUG" 2>&1); [[ "$out" == *"no checks reported"* ]]; do
        if ((waited >= cap)); then say "ship: no checks registered after ${waited}s"; break; fi
        sleep "$step"; waited=$((waited + step))
    done
    # why: only the three result lines reach stdout; the rc decides
    timeout "$poll" gh pr checks "$num" -R "$SLUG" --watch --interval "$WATCH_INTERVAL_S" --fail-fast >/dev/null 2>&1 || rc=$?
    if ((rc == 0)); then
        local rr=0
        # why: gh exits 0 for a cancelled check; the non-TTY row says fail. 2>/dev/null: the rc is reported below
        out=$(timeout "$GH_CALL_TIMEOUT_S" gh pr checks "$num" -R "$SLUG" 2>/dev/null) || rr=$?
        # why: gh's rc 8 is "pending" — a check registered after the watch ended; finish gates it
        if ((rr == 8)); then say "ship: a check is still pending after the watch"; ci=timeout
        elif ((rr)); then say "ship: could not re-read the checks (rc=$rr) — not calling CI green"; ci=failed
        elif awk -F'\t' '$2=="fail" || $2=="cancel" {f=1} END {exit !f}' <<<"$out"; then ci=failed; fi
    elif ((rc == 124)); then ci=timeout; else ci=failed; fi
    case "$ci" in
        timeout) echo "STATUS: CI_TIMEOUT — see $url"; echo "  recovery: sdm.sh finish $num once CI completes" ;;
        failed)  echo "STATUS: CI_FAILED — see $url"; echo "  diagnostic: gh pr checks $num" ;;
    esac
    echo "CI_STATE=$ci"
}

cmd_finish() {
    local num=${1:-}
    [[ "$num" =~ ^[1-9][0-9]*$ ]] || die "finish: PR_NUM '$num' is not a PR number"
    sdm_context
    sdm_slug finish
    local sha row href xrepo state oid url
    sha=$(git rev-parse HEAD)
    row=$(gh pr view "$num" -R "$SLUG" --json headRefName,isCrossRepository,state,headRefOid,url \
        --jq '[.headRefName,.isCrossRepository,.state,.headRefOid,.url]|@tsv') || die "finish: cannot read PR $num (head/owner lookup failed)"
    IFS=$'\t' read -r href xrepo state oid url <<<"$row"
    [[ "$href" == "$BRANCH" ]] || die "finish: PR $num head is '$href', not '$BRANCH'"
    [[ "$xrepo" == false ]] || die "finish: PR $num is from another repository (isCrossRepository=$xrepo)"
    case "$state" in
        OPEN)
            [[ "$oid" == "$sha" ]] || die "finish: PR $num head is at $oid, not this branch's HEAD $sha — push, then re-run ship"
            sdm_strategy finish
            local total runs bad=0 pend=0 ok=0 s c
            runs=$(gh api "repos/$SLUG/commits/$sha/check-runs?filter=latest&per_page=$CHECK_RUNS_PER_PAGE" \
                --jq '.total_count, (.check_runs[] | "\(.status) \(.conclusion)")') || die "finish: cannot read check-runs"
            total=$(head -n1 <<<"$runs")
            [[ "$total" -eq "$(($(wc -l <<<"$runs") - 1))" ]] || die "finish: $total check-runs, not all read"
            while read -r s c; do
                [[ -n "$s" ]] || continue
                if [[ "$s" != completed ]]; then pend=$((pend + 1))
                elif [[ "$c" == success ]]; then ok=$((ok + 1))
                elif [[ "$c" != skipped && "$c" != neutral ]]; then bad=$((bad + 1)); fi
            done < <(tail -n +2 <<<"$runs")
            if ((pend)); then echo "STATUS: CI_NOT_DONE — $pend check-run(s) not completed; re-run sdm.sh finish $num"; exit 0; fi
            if ((bad || !ok)); then echo "STATUS: CI_FAILED — see $url"; exit 0; fi
            gh pr merge "$num" -R "$SLUG" --"$STRATEGY" --match-head-commit "$sha" >&2 \
                || say "finish: gh pr merge rc=$? — checking PR state"
            # why: an unreadable state counts as not merged (fails safe)
            state=$(gh pr view "$num" -R "$SLUG" --json state --jq .state 2>/dev/null || echo UNKNOWN)
            [[ "$state" == MERGED ]] || { echo "STATUS: MERGE_FAILED — state=$state — see $url"; exit 0; }
            say "finish: merged PR $num (strategy=$STRATEGY)" ;;
        MERGED)
            # why: a stale PR number of an earlier merged PR on a reused branch name must not delete new commits
            [[ "$oid" == "$sha" ]] || die "finish: PR $num is MERGED at $oid, not this branch's HEAD"
            say "finish: PR $num already merged at HEAD — no merge call" ;;
        *) die "finish: PR $num is $state, not OPEN" ;;
    esac
    # why: the lease keeps a commit pushed after the merge; ls-remote decides, not push's rc
    git push -q --force-with-lease="refs/heads/$BRANCH:$sha" origin ":refs/heads/$BRANCH" \
        || say "finish: branch delete rc=$? — checking ls-remote"
    local ls=0
    git ls-remote --exit-code origin "refs/heads/$BRANCH" >/dev/null || ls=$?
    if ((ls == 0)); then echo "STATUS: BRANCH_NOT_DELETED — $BRANCH"
    elif ((ls != 2)); then echo "STATUS: BRANCH_NOT_DELETED — $BRANCH (ls-remote rc=$ls, could not verify)"; fi
    sdm_cleanup "$url"
}

sdm_cleanup() {   # G4: bring the default branch up to date; worktree-safe (L-1332, L-1347)
    local url=$1 gd common main note="" wt=""
    gd=$(git rev-parse --path-format=absolute --git-dir)
    common=$(git rev-parse --path-format=absolute --git-common-dir)
    if [[ "$gd" == "$common" ]]; then
        main=$TOP
        # why: a checkout would carry tracked changes onto the default branch; same rule as the worktree path
        local dirty; dirty=$(git status --porcelain --untracked-files=no)
        [[ -z "$dirty" ]] || { echo "STATUS: MAIN_CHECKOUT_DIRTY — $(tr '\n' ' ' <<<"$dirty")"; exit 0; }
        { git checkout -q "$DEFAULT_BRANCH" && git fetch -q --prune origin && git merge -q --ff-only "origin/$DEFAULT_BRANCH"; } \
            || { echo "STATUS: MAIN_NOT_UPDATED — could not switch to and fast-forward $DEFAULT_BRANCH"; exit 0; }
        git branch -q -D "$BRANCH" || say "finish: local branch $BRANCH not deleted"
    else
        local list
        list=$(git worktree list --porcelain)
        main=$(awk '/^worktree /{sub(/^worktree /,""); print; exit}' <<<"$list")
        if ! git -C "$main" fetch -q --prune origin; then
            note="STATUS: MAIN_NOT_UPDATED — fetch from origin failed"
        elif [[ "$(git -C "$main" branch --show-current)" != "$DEFAULT_BRANCH" ]]; then
            if [[ $'\n'"$list"$'\n' == *$'\n'"branch refs/heads/$DEFAULT_BRANCH"$'\n'* ]]; then
                note="STATUS: MAIN_NOT_UPDATED — $DEFAULT_BRANCH is in use by another worktree"
            else
                git -C "$main" fetch -q origin "$DEFAULT_BRANCH:$DEFAULT_BRANCH" || note="STATUS: MAIN_NOT_UPDATED — non-fast-forward"
            fi
        elif [[ -n "$(git -C "$main" status --porcelain --untracked-files=no)" ]]; then
            echo "STATUS: MAIN_CHECKOUT_DIRTY — $(git -C "$main" status --porcelain --untracked-files=no | tr '\n' ' ')"; exit 0
        else
            git -C "$main" merge -q --ff-only "origin/$DEFAULT_BRANCH" || note="STATUS: MAIN_NOT_UPDATED — non-fast-forward"
        fi
        echo "Operator cleanup:"
        printf '  git -C %q worktree remove %q\n' "$main" "$TOP"
        printf '  git -C %q branch -D %q\n' "$main" "$BRANCH"
        wt=" worktree=$TOP"
    fi
    local m
    # why: no local default branch (never fetched) is reported in the summary, never a silent exit after the merge
    m=$(git -C "$main" rev-parse -q --verify --short "$DEFAULT_BRANCH") || m="(none)"
    echo "finish: cleanup done — $DEFAULT_BRANCH at $m$wt"
    echo "Final: branch=$BRANCH merged into $DEFAULT_BRANCH (sha=$m) — $url"
    echo "${note:-STATUS: OK$wt}"
}

cmd_help() {
    echo "usage: sdm.sh check | ship [--notes FILE] | finish <PR_NUM> | help"
    echo "exit 0 with STATUS lines; exit 1 with ABORT lines."
    sed -n '/^# exit-table:begin$/,/^# exit-table:end$/{/^# exit-table:/d;s/^# //;p}' "${BASH_SOURCE[0]}"
}
# exit-table:begin
# ABORT: Not inside a git repository | any: cwd is not in a git repo
# ABORT: Detached HEAD — check out the branch to merge | any: no branch checked out
# ABORT: Cannot run /sole-dev-merge from <b> branch | any: on main, master or origin's default branch
# ABORT: No git remote configured (need a github.com origin) | any: no remote
# ABORT: DEFAULT_BRANCH '<d>' is not a valid branch name | any: origin/HEAD names an invalid branch
# ABORT: Cannot resolve <d> or origin/<d> | any: no base ref
# ABORT: unknown subcommand '<x>' (see sdm.sh help) | not check, ship, finish or help
# ABORT: Uncommitted changes detected (commit or stash first) | check: the tree was dirty at the start
# ABORT: No commits ahead of <d> (nothing to merge) | check: nothing to merge
# ABORT: check: files outside the branch changed: <files> (left as they are) | check: a fixer changed files the branch does not touch; nothing committed or restored
# ABORT: check: auto-fix commit failed (rc=<n>); the fixes are staged | check: git or a git hook refused the auto-fix commit; git's message is on stderr
# ABORT: ship: unknown argument '<x>' (see sdm.sh help) | ship takes only --notes FILE
# ABORT: ship: --notes needs a FILE | ship: --notes was the last argument; nothing pushed
# ABORT: ship: notes file '<f>' is not a readable file | ship: the --notes path is missing or unreadable; nothing pushed
# ABORT: <cmd>: no origin remote | ship/finish: no remote named origin
# ABORT: <cmd>: origin is on <host>, not github.com | ship/finish: origin's configured URL is not on github.com; nothing pushed
# ABORT: <cmd>: origin is not a github.com remote | ship/finish: origin's URL has no host
# ABORT: <cmd>: cannot read owner/repo from origin | ship/finish: origin's path is not <owner>/<repo>
# STATUS: AUTH_REQUIRED — run gh auth login | ship: gh is not logged in; nothing pushed
# ABORT: ship: git push failed (rc=<n>) | ship: the push was rejected or failed; git's message is on stderr; no PR call
# STATUS: PR_BODY_NOT_UPDATED — PR #<n> reason=<r> | ship: the open PR's body was not set; not-this-branch/no-pr-number/not-open (closed during the wait)/head-not-updated (GitHub still shows another head after the wait) stop ship, patch-failed/readback-differs go on (set the body by hand)
# ABORT: ship: gh pr create failed | ship: no PR was created
# ABORT: ship: gh pr create printed no PR URL | ship: create gave no PR number
# ABORT: <cmd>: cannot read allow_rebase_merge | ship/finish: the repo settings call failed (ship: after PR_NUM/PR_URL)
# ABORT: <cmd>: allow_rebase_merge is '<v>', not true or false | ship/finish: the repo settings value is unusable
# STATUS: CI_TIMEOUT — see <url> | ship: CI did not finish within CI_POLL_TIMEOUT, or a check registered after the watch; run sdm.sh finish <n> once it completes
# STATUS: CI_FAILED — see <url> | ship: a check failed or was cancelled, or the checks re-read failed; finish: a check-run did not pass, or none succeeded
# ABORT: finish: PR_NUM '<x>' is not a PR number | finish: the argument is not a positive integer; nothing called
# ABORT: finish: cannot read PR <n> (head/owner lookup failed) | finish: gh pr view failed
# ABORT: finish: PR <n> head is '<h>', not '<b>' | finish: the PR is another branch's
# ABORT: finish: PR <n> is from another repository (isCrossRepository=<v>) | finish: a fork's PR
# ABORT: finish: PR <n> head is at <oid>, not this branch's HEAD <sha> — push, then re-run ship | finish: local HEAD is not what CI ran on
# ABORT: finish: PR <n> is MERGED at <oid>, not this branch's HEAD | finish: a stale PR number; nothing deleted
# ABORT: finish: PR <n> is <state>, not OPEN | finish: e.g. CLOSED
# ABORT: finish: cannot read check-runs | finish: the check-runs call failed
# ABORT: finish: <total> check-runs, not all read | finish: more than one page of check-runs
# STATUS: CI_NOT_DONE — <k> check-run(s) not completed; re-run sdm.sh finish <n> | finish: CI still running; nothing merged
# STATUS: MERGE_FAILED — state=<s> — see <url> | finish: the PR is not MERGED after the merge call; no branch delete
# STATUS: BRANCH_NOT_DELETED — <b> | finish: merged, but the remote branch is still there (moved after the merge, or the delete failed); cleanup goes on
# STATUS: MAIN_NOT_UPDATED — <reason> | finish: the default branch was not fast-forwarded (plain checkout failure, fetch from origin failed, in use by another worktree, non-fast-forward)
# STATUS: MAIN_CHECKOUT_DIRTY — <files> | finish: the checkout the default branch is updated in has tracked changes; left alone
# STATUS: OK[ worktree=<path>] | finish: merged, branch deleted, default branch updated; in a worktree, run the printed cleanup commands
# exit-table:end

sdm_main() {
    # why: no subcommand means help; shift has nothing to drop
    local sub=${1:-help}; shift || true
    case "$sub" in
        check) cmd_check ;;
        ship) cmd_ship "$@" ;;
        finish) cmd_finish "$@" ;;
        help|-h|--help) cmd_help ;;
        *) die "unknown subcommand '$sub' (see sdm.sh help)" ;;
    esac
}
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then sdm_main "$@"; fi
