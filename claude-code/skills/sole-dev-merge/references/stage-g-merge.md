# Stage G: CI poll, merge and cleanup — branch protection check, CI polling, the rebase merge and local cleanup.

## Contents

  - [Stage G — CI poll + auto-merge + cleanup](#stage-g--ci-poll--auto-merge--cleanup)

### Stage G — CI poll + auto-merge + cleanup

Execution order: **G1 → G2 → G3 → G4**. G1 picks the merge strategy up-front
so G3 doesn't hit a "rebase merging is disabled" runtime error. G2 polls with
a 15-minute timeout (overridable via `CI_POLL_TIMEOUT` for tests). G3 dispatches
the merge on green CI or emits a clean recovery `STATUS: …` line on timeout /
failure. G4 runs only on a successful merge.

- **G1** (branch-protection pre-check) — `gh api repos/{owner}/{repo} --jq
  .allow_rebase_merge` / `glab api /projects/:id --jq .merge_method`. Sets
  `MERGE_STRATEGY=rebase|merge` based on the response.
- **G2** (CI poll) — divergent paths:
  - GitHub: `timeout 900s gh pr checks <num> --watch --interval 30 --fail-fast`.
    Translates `RC=124` → `STATUS: CI_TIMEOUT` + clean exit 0; `RC=0` → green;
    other → failed. Sets `CI_STATE`.
  - GitLab: `glab api /projects/:id/merge_requests/<iid>` polled every 30s in
    a bash `while` loop with `(( $(date +%s) - start < 900 ))` guard. Parses
    `.pipeline.status`. (NOT `glab ci status` — TTY UI, no scriptable exit
    codes per reference.md "WRONG SYNTAX TO NEVER USE".)
- **G3** (auto-merge + error paths, plan §4.3 + §4.4) — branches on `CI_STATE`:
  - `green` → refuses (ABORT, rc 1) unless `ORIGINAL_BRANCH` is a valid
    branch name, is not the default branch, and is the PR's head ref. Then
    `gh pr merge <num> --$MERGE_STRATEGY` — **no `--delete-branch`**: gh's
    local step fails in a worktree and skips the remote delete (L-1332). G3
    reads `gh pr view --json state`: anything but `MERGED` (including a
    merge-queue repo, where the PR stays OPEN) → `STATUS: MERGE_FAILED`,
    nothing deleted. On `MERGED` it pushes `:refs/heads/<branch>` (a
    same-named tag survives) and asserts with `ls-remote`; a branch still
    there → `STATUS: BRANCH_NOT_DELETED` (warning, rc 0). An unknown
    `REMOTE_CHOICE` → `STATUS: REMOTE_UNKNOWN`. Prints `MERGE_DISPATCHED=0|1`.
  - `timeout` → emit `STATUS: CI_TIMEOUT — see <URL>` + recovery hint
    (`gh pr merge --auto --rebase`); skip merge.
  - `failed` → emit `STATUS: CI_FAILED — see <URL>` + diagnostic hint
    (`gh pr checks <num>`); skip merge.
- **G4** (cleanup, plan §4.5) — runs only on successful merge:
  `git checkout main` → `git pull --ff-only origin main` → `git fetch --prune`.
  Prints final summary: branch, commits merged, merge SHA, PR/MR URL.

```bash
# === stage-g1-protect (BEGIN) ===
set -euo pipefail

# Inherits REMOTE_CHOICE from Stage E2. Defensive default to github.
REMOTE_CHOICE="${REMOTE_CHOICE:-github}"
MERGE_STRATEGY=rebase  # default; falls back to merge if rebase disabled

if [[ "$REMOTE_CHOICE" == "github" ]]; then
    # gh api echoes "true" or "false" for the boolean jq filter.
    ALLOW_REBASE=$(gh api "repos/{owner}/{repo}" --jq '.allow_rebase_merge' 2>/dev/null || echo "true")
    if [[ "$ALLOW_REBASE" != "true" ]]; then
        MERGE_STRATEGY=merge
        echo "Stage G1: rebase-merge disabled on remote — fallback strategy=merge"
    fi
elif [[ "$REMOTE_CHOICE" == "gitlab" ]]; then
    # glab api echoes the project's merge_method string.
    MERGE_METHOD=$(glab api "/projects/:id" --jq '.merge_method' 2>/dev/null || echo "rebase_merge")
    if [[ "$MERGE_METHOD" != "rebase_merge" ]]; then
        MERGE_STRATEGY=merge
        echo "Stage G1: GitLab merge_method=$MERGE_METHOD — fallback strategy=merge"
    fi
fi

export MERGE_STRATEGY
echo "MERGE_STRATEGY=$MERGE_STRATEGY"
# === stage-g1-protect (END) ===
```

```bash
# === stage-g2-poll (BEGIN) ===
set -euo pipefail

# Inputs from Stage F: PR_NUM, PR_URL, REMOTE_CHOICE.
REMOTE_CHOICE="${REMOTE_CHOICE:-github}"
PR_NUM="${PR_NUM:-0}"
PR_URL="${PR_URL:-}"
# 15 minutes hard cap by default; tests override to small values for speed.
CI_POLL_TIMEOUT="${CI_POLL_TIMEOUT:-900s}"

CI_STATE=unknown

if [[ "$REMOTE_CHOICE" == "github" ]]; then
    RC=0
    # `--watch` blocks until checks complete; `timeout` enforces the cap.
    timeout "$CI_POLL_TIMEOUT" gh pr checks "$PR_NUM" \
        --watch --interval 30 --fail-fast || RC=$?
    case "$RC" in
        0)   CI_STATE=green ;;
        124) CI_STATE=timeout
             echo "STATUS: CI_TIMEOUT — see $PR_URL"
             echo "  recovery: gh pr merge $PR_NUM --auto --rebase"
             ;;
        *)   CI_STATE=failed
             echo "STATUS: CI_FAILED — see $PR_URL"
             echo "  diagnostic: gh pr checks $PR_NUM"
             ;;
    esac
elif [[ "$REMOTE_CHOICE" == "gitlab" ]]; then
    # JSON polling (NOT `glab ci status` — TTY UI without scriptable exit codes).
    MR_IID="${MR_IID:-$PR_NUM}"
    START=$(date +%s)
    # §6.8 M4 HIGH-5 fix: parse `${CI_POLL_TIMEOUT%s}` so the env-override the
    # GitHub branch honours also applies here. Falls back to 900 when unset
    # or non-numeric after stripping the 's' suffix.
    TIMEOUT_S="${CI_POLL_TIMEOUT%s}"
    [[ "$TIMEOUT_S" =~ ^[0-9]+$ ]] || TIMEOUT_S=900
    CI_POLL_INTERVAL="${CI_POLL_INTERVAL:-30}"
    while true; do
        STATUS=$(GLAB_API_MODE=pipeline_status glab api \
            "/projects/:id/merge_requests/${MR_IID}" --jq '.pipeline.status' 2>/dev/null \
            || echo "running")
        case "$STATUS" in
            success)
                CI_STATE=green; break ;;
            failed|canceled)
                CI_STATE=failed
                echo "STATUS: CI_FAILED — see $PR_URL"
                echo "  diagnostic: glab ci view $MR_IID"
                break ;;
            manual|skipped)
                # §6.8 M4 HIGH-2 fix: GitLab pipeline-status terminal states
                # OTHER than success/failed — `manual` (waiting on operator)
                # and `skipped` (pipeline intentionally bypassed). Without
                # this arm, both fall through to "keep polling" and burn the
                # full 15-min CI_POLL_TIMEOUT (the M3 §6.8 future-proofing
                # auditor flagged this enum-coverage gap).
                CI_STATE=blocked
                echo "STATUS: CI_BLOCKED — pipeline status=$STATUS — see $PR_URL"
                echo "  diagnostic: glab ci view $MR_IID"
                break ;;
        esac
        if (( $(date +%s) - START >= TIMEOUT_S )); then
            CI_STATE=timeout
            echo "STATUS: CI_TIMEOUT — see $PR_URL"
            echo "  recovery: glab mr merge $MR_IID --when-pipeline-succeeds"
            break
        fi
        sleep "$CI_POLL_INTERVAL"
    done
fi

export CI_STATE
echo "CI_STATE=$CI_STATE"
# === stage-g2-poll (END) ===
```

```bash
# === stage-g3-merge (BEGIN) ===
set -euo pipefail

# Inputs from Stage F + G1 + G2: PR_NUM, PR_URL, REMOTE_CHOICE,
# MERGE_STRATEGY (rebase|merge), CI_STATE (green|timeout|failed).
REMOTE_CHOICE="${REMOTE_CHOICE:-github}"
PR_NUM="${PR_NUM:-0}"
PR_URL="${PR_URL:-}"
MERGE_STRATEGY="${MERGE_STRATEGY:-rebase}"
CI_STATE="${CI_STATE:-unknown}"

case "$CI_STATE" in
    green)
        : "${ORIGINAL_BRANCH:?Stage G3 needs ORIGINAL_BRANCH from Stage A}"
        DEFAULT_BRANCH="${DEFAULT_BRANCH:-main}"
        case "$REMOTE_CHOICE" in
        github)
            # Refuse before any state change, so a wrong or hostile value can't
            # delete another ref (rc 1, pre-flight class).
            git check-ref-format --branch "$ORIGINAL_BRANCH" >/dev/null \
                || { echo "ABORT: Stage G3: ORIGINAL_BRANCH '$ORIGINAL_BRANCH' is not a valid branch name"; exit 1; }
            [[ "$ORIGINAL_BRANCH" != "$DEFAULT_BRANCH" ]] \
                || { echo "ABORT: Stage G3: ORIGINAL_BRANCH is the default branch '$DEFAULT_BRANCH'"; exit 1; }
            HEAD_REF=$(gh pr view "$PR_NUM" --json headRefName --jq .headRefName)
            [[ "$HEAD_REF" == "$ORIGINAL_BRANCH" ]] \
                || { echo "ABORT: Stage G3: PR $PR_NUM head is '$HEAD_REF', not '$ORIGINAL_BRANCH'"; exit 1; }
            # No --delete-branch: gh's local step fails in a worktree and then
            # skips the remote delete (L-1332). Merge, then decide from the
            # server state, not gh's rc (E6).
            gh pr merge "$PR_NUM" --"$MERGE_STRATEGY" \
                || echo "Stage G3: gh pr merge rc=$? — checking PR state"
            # why: an unreadable state counts as not merged, so the step fails safe (no delete)
            STATE=$(gh pr view "$PR_NUM" --json state --jq .state 2>/dev/null || echo UNKNOWN)
            if [[ "$STATE" != MERGED ]]; then
                echo "STATUS: MERGE_FAILED — state=$STATE — see $PR_URL"
                export MERGE_DISPATCHED=0
                echo "MERGE_DISPATCHED=0"
                exit 0
            fi
            # Full ref, so a same-named tag is never deleted. rc 1 when the
            # branch is already gone (E12); ls-remote decides, not the rc.
            git push -q origin ":refs/heads/$ORIGINAL_BRANCH" \
                || echo "Stage G3: push --delete rc=$? (already gone server-side?) — checking ls-remote"
            if [[ -n "$(git ls-remote origin "refs/heads/$ORIGINAL_BRANCH")" ]]; then
                echo "STATUS: BRANCH_NOT_DELETED — $ORIGINAL_BRANCH"
            fi
            ;;
        gitlab)
            MR_IID="${MR_IID:-$PR_NUM}"
            if [[ "$MERGE_STRATEGY" == "rebase" ]]; then
                glab mr merge "$MR_IID" --rebase --remove-source-branch --yes
            else
                glab mr merge "$MR_IID" --remove-source-branch --yes
            fi
            ;;
        *)
            echo "STATUS: REMOTE_UNKNOWN — REMOTE_CHOICE='$REMOTE_CHOICE'"
            export MERGE_DISPATCHED=0
            echo "MERGE_DISPATCHED=0"
            exit 0
            ;;
        esac
        export MERGE_DISPATCHED=1
        echo "MERGE_DISPATCHED=1"
        echo "Stage G3: merged $PR_NUM (strategy=$MERGE_STRATEGY)"
        ;;
    timeout)
        # §6.8 M4 HIGH-1 fix: remote-aware recovery hints. G2 already emitted
        # the correct STATUS line; G3's defensive re-emission must NOT
        # hardcode `gh pr merge` when the operator chose GitLab.
        echo "STATUS: CI_TIMEOUT — see $PR_URL"
        if [[ "$REMOTE_CHOICE" == "gitlab" ]]; then
            echo "  recovery: glab mr merge ${MR_IID:-$PR_NUM} --when-pipeline-succeeds"
        else
            echo "  recovery: gh pr merge $PR_NUM --auto --rebase"
        fi
        export MERGE_DISPATCHED=0
        ;;
    failed)
        # §6.8 M4 HIGH-1 fix (failed branch): remote-aware diagnostic hint.
        echo "STATUS: CI_FAILED — see $PR_URL"
        if [[ "$REMOTE_CHOICE" == "gitlab" ]]; then
            echo "  diagnostic: glab ci view ${MR_IID:-$PR_NUM}"
        else
            echo "  diagnostic: gh pr checks $PR_NUM"
        fi
        export MERGE_DISPATCHED=0
        ;;
    blocked)
        # §6.8 M4 HIGH-2 fix: G2's `manual|skipped` GitLab enum hand-off.
        # No merge; G2 already emitted the STATUS:CI_BLOCKED line.
        export MERGE_DISPATCHED=0
        ;;
    *)
        # §6.8 M4 MED-1 fix: emit a STATUS line for the unknown catchall so
        # downstream tooling parsing for `STATUS:` doesn't miss this terminal
        # state. REMOTE_CHOICE included for diagnostic context.
        echo "STATUS: CI_UNKNOWN — CI_STATE='$CI_STATE' REMOTE_CHOICE='$REMOTE_CHOICE'"
        export MERGE_DISPATCHED=0
        ;;
esac
# === stage-g3-merge (END) ===
```

```bash
# === stage-g4-cleanup (BEGIN) ===
set -euo pipefail

# Runs only on successful merge (gated by caller checking MERGE_DISPATCHED=1).
# Inputs: ORIGINAL_BRANCH (from Stage A), PR_URL (from Stage F).
ORIGINAL_BRANCH="${ORIGINAL_BRANCH:-feature}"
PR_URL="${PR_URL:-}"
DEFAULT_BRANCH="${DEFAULT_BRANCH:-main}"

# 1. Switch to default branch (feature branch was deleted server-side by
#    --delete-branch in G3; local ref may still exist but switching is safe).
git checkout -q "$DEFAULT_BRANCH"

# 2. Fast-forward local default to the server tip.
git pull -q --ff-only origin "$DEFAULT_BRANCH"

# 3. Prune local remote-tracking refs for branches deleted server-side.
git fetch -q --prune

# 4. Best-effort local cleanup: delete the local feature branch ref if it
#    still exists (server-side ref is already gone).
git branch -q -D "$ORIGINAL_BRANCH" 2>/dev/null || true

MERGE_SHA=$(git rev-parse --short "$DEFAULT_BRANCH")
echo "Stage G4: cleanup OK — on $DEFAULT_BRANCH at $MERGE_SHA"
echo "Final: branch=$ORIGINAL_BRANCH merged into $DEFAULT_BRANCH (sha=$MERGE_SHA)${PR_URL:+ — $PR_URL}"
echo "STATUS: OK"
# === stage-g4-cleanup (END) ===
```
