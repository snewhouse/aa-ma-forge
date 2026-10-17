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
- **G4** (cleanup, plan §4.5) — runs only on successful merge. Needs
  `ORIGINAL_BRANCH` (fails loud without it). Detects a linked worktree by
  comparing the absolute `--git-dir` and `--git-common-dir`:
  - plain checkout: switch to the default branch, `git fetch --prune origin`,
    `git merge --ff-only origin/<default>`, delete the local branch (rc
    printed on failure). No `pull` (E10).
  - worktree: fast-forward the **main worktree** with `git -C`, never switch
    branches here. A tracked change there → `STATUS: MAIN_CHECKOUT_DIRTY`, stop
    (never auto-revert); main worktree on another branch → update the
    default branch ref by fetch, or `STATUS: MAIN_NOT_UPDATED`. Then show the
    `--stat` diff and print quoted `worktree remove` / `branch -D` commands
    for the operator to run.
  Prints final summary: branch, merge SHA, PR/MR URL.

```bash
# === stage-g1-protect (BEGIN) ===
set -euo pipefail

# Stage state: load what earlier stages saved (SKILL.md "State between stages").
SDM_STATE="$(git rev-parse --absolute-git-dir)/sole-dev-merge.env"   # why: absolute, so a later cd can't break sdm_save
SDM_KEYS=" ORIGINAL_BRANCH BASE_REF DEFAULT_BRANCH SLUG SDM_DIR CHANGED_FILES CHANGED_PY CHANGED_SH REMOTE_CHOICE PR_BODY_FILE PR_NUM PR_URL MERGE_STRATEGY CI_STATE MERGE_DISPATCHED n_github n_gitlab n_other "
sdm_load() {
    # why: a planted or shared file must never be read: symlink, other owner, or group/world-writable → refuse
    if [[ -L "$SDM_STATE" || ! -O "$SDM_STATE" || -n "$(find "$SDM_STATE" \( -perm -g+w -o -perm -o+w \) -print)" ]]; then
        echo "Stage state: refusing ${SDM_STATE##*/} (symlink, not owned by you, or writable by others)"; return 0
    fi
    local line k v dv
    declare -A _sdm=()
    while IFS= read -r line; do
        k=${line%%=*}; v=${line#*=}
        [[ "$SDM_KEYS" == *" $k "* ]] || { echo "Stage state: ignoring unknown key '$k'"; continue; }   # why: allowlist, never a free-form name
        # why: decode into a temp first, so a bad line never overwrites an earlier good value
        dv=$(printf '%s' "$v" | base64 -d 2>/dev/null) || { echo "Stage state: bad value for $k — ignored"; continue; }
        _sdm[$k]=$dv                                   # why: last good write wins
    done < "$SDM_STATE"
    # why: a missing or empty ORIGINAL_BRANCH counts as foreign (on a detached HEAD '' would equal '')
    if [[ -z "${_sdm[ORIGINAL_BRANCH]:-}" || "${_sdm[ORIGINAL_BRANCH]}" != "$(git branch --show-current)" ]]; then
        echo "Stage state: ${SDM_STATE##*/} is not for this branch — ignored (run Stage A first)"; return 0
    fi
    for k in "${!_sdm[@]}"; do
        [[ -n "${!k:-}" ]] || printf -v "$k" '%s' "${_sdm[$k]}"   # why: a non-empty explicit env wins; a value is assigned, never executed
    done
}
[[ -f "$SDM_STATE" ]] && sdm_load
sdm_save() { if [[ -L "$SDM_STATE" ]] || { [[ -e "$SDM_STATE" ]] && { [[ ! -O "$SDM_STATE" ]] || [[ -n "$(find "$SDM_STATE" \( -perm -g+w -o -perm -o+w \) -print)" ]]; }; }; then echo "Stage state: refusing to save $1 (${SDM_STATE##*/} is a symlink, not yours, or writable by others)"; return 1; fi; (umask 077; printf '%s=%s\n' "$1" "$(printf '%s' "$2" | base64 | tr -d '\n')" >> "$SDM_STATE"); }   # why: refuse exactly what the loader refuses, and create the file 600; base64 has no shell metacharacters, tr keeps one line

# From Stage E2 via the state file.
REMOTE_CHOICE="${REMOTE_CHOICE:?Stage G1 needs REMOTE_CHOICE from Stage E2 — run E2 first}"   # why: a defaulted github acts on the wrong host when the state file was refused (L-055)
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
sdm_save MERGE_STRATEGY "$MERGE_STRATEGY"   # why: G3 reads it in its own shell
# === stage-g1-protect (END) ===
```

```bash
# === stage-g2-poll (BEGIN) ===
set -euo pipefail

# Stage state: load what earlier stages saved (SKILL.md "State between stages").
SDM_STATE="$(git rev-parse --absolute-git-dir)/sole-dev-merge.env"   # why: absolute, so a later cd can't break sdm_save
SDM_KEYS=" ORIGINAL_BRANCH BASE_REF DEFAULT_BRANCH SLUG SDM_DIR CHANGED_FILES CHANGED_PY CHANGED_SH REMOTE_CHOICE PR_BODY_FILE PR_NUM PR_URL MERGE_STRATEGY CI_STATE MERGE_DISPATCHED n_github n_gitlab n_other "
sdm_load() {
    # why: a planted or shared file must never be read: symlink, other owner, or group/world-writable → refuse
    if [[ -L "$SDM_STATE" || ! -O "$SDM_STATE" || -n "$(find "$SDM_STATE" \( -perm -g+w -o -perm -o+w \) -print)" ]]; then
        echo "Stage state: refusing ${SDM_STATE##*/} (symlink, not owned by you, or writable by others)"; return 0
    fi
    local line k v dv
    declare -A _sdm=()
    while IFS= read -r line; do
        k=${line%%=*}; v=${line#*=}
        [[ "$SDM_KEYS" == *" $k "* ]] || { echo "Stage state: ignoring unknown key '$k'"; continue; }   # why: allowlist, never a free-form name
        # why: decode into a temp first, so a bad line never overwrites an earlier good value
        dv=$(printf '%s' "$v" | base64 -d 2>/dev/null) || { echo "Stage state: bad value for $k — ignored"; continue; }
        _sdm[$k]=$dv                                   # why: last good write wins
    done < "$SDM_STATE"
    # why: a missing or empty ORIGINAL_BRANCH counts as foreign (on a detached HEAD '' would equal '')
    if [[ -z "${_sdm[ORIGINAL_BRANCH]:-}" || "${_sdm[ORIGINAL_BRANCH]}" != "$(git branch --show-current)" ]]; then
        echo "Stage state: ${SDM_STATE##*/} is not for this branch — ignored (run Stage A first)"; return 0
    fi
    for k in "${!_sdm[@]}"; do
        [[ -n "${!k:-}" ]] || printf -v "$k" '%s' "${_sdm[$k]}"   # why: a non-empty explicit env wins; a value is assigned, never executed
    done
}
[[ -f "$SDM_STATE" ]] && sdm_load
sdm_save() { if [[ -L "$SDM_STATE" ]] || { [[ -e "$SDM_STATE" ]] && { [[ ! -O "$SDM_STATE" ]] || [[ -n "$(find "$SDM_STATE" \( -perm -g+w -o -perm -o+w \) -print)" ]]; }; }; then echo "Stage state: refusing to save $1 (${SDM_STATE##*/} is a symlink, not yours, or writable by others)"; return 1; fi; (umask 077; printf '%s=%s\n' "$1" "$(printf '%s' "$2" | base64 | tr -d '\n')" >> "$SDM_STATE"); }   # why: refuse exactly what the loader refuses, and create the file 600; base64 has no shell metacharacters, tr keeps one line

# Inputs from Stage F: PR_NUM, PR_URL, REMOTE_CHOICE.
REMOTE_CHOICE="${REMOTE_CHOICE:?Stage G2 needs REMOTE_CHOICE from Stage E2 — run E2 first}"   # why: a defaulted github acts on the wrong host when the state file was refused (L-055)
PR_NUM="${PR_NUM:?Stage G2 needs PR_NUM from Stage F}"
# why: it reaches gh/glab argv; a number can never be read as an option
[[ "$PR_NUM" =~ ^[0-9]+$ ]] || { echo "ABORT: Stage G2: PR_NUM '$PR_NUM' is not a number"; exit 1; }
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

sdm_save CI_STATE "$CI_STATE"   # why: G3 reads it in its own shell
export CI_STATE
echo "CI_STATE=$CI_STATE"
# === stage-g2-poll (END) ===
```

```bash
# === stage-g3-merge (BEGIN) ===
set -euo pipefail

# Stage state: load what earlier stages saved (SKILL.md "State between stages").
SDM_STATE="$(git rev-parse --absolute-git-dir)/sole-dev-merge.env"   # why: absolute, so a later cd can't break sdm_save
SDM_KEYS=" ORIGINAL_BRANCH BASE_REF DEFAULT_BRANCH SLUG SDM_DIR CHANGED_FILES CHANGED_PY CHANGED_SH REMOTE_CHOICE PR_BODY_FILE PR_NUM PR_URL MERGE_STRATEGY CI_STATE MERGE_DISPATCHED n_github n_gitlab n_other "
sdm_load() {
    # why: a planted or shared file must never be read: symlink, other owner, or group/world-writable → refuse
    if [[ -L "$SDM_STATE" || ! -O "$SDM_STATE" || -n "$(find "$SDM_STATE" \( -perm -g+w -o -perm -o+w \) -print)" ]]; then
        echo "Stage state: refusing ${SDM_STATE##*/} (symlink, not owned by you, or writable by others)"; return 0
    fi
    local line k v dv
    declare -A _sdm=()
    while IFS= read -r line; do
        k=${line%%=*}; v=${line#*=}
        [[ "$SDM_KEYS" == *" $k "* ]] || { echo "Stage state: ignoring unknown key '$k'"; continue; }   # why: allowlist, never a free-form name
        # why: decode into a temp first, so a bad line never overwrites an earlier good value
        dv=$(printf '%s' "$v" | base64 -d 2>/dev/null) || { echo "Stage state: bad value for $k — ignored"; continue; }
        _sdm[$k]=$dv                                   # why: last good write wins
    done < "$SDM_STATE"
    # why: a missing or empty ORIGINAL_BRANCH counts as foreign (on a detached HEAD '' would equal '')
    if [[ -z "${_sdm[ORIGINAL_BRANCH]:-}" || "${_sdm[ORIGINAL_BRANCH]}" != "$(git branch --show-current)" ]]; then
        echo "Stage state: ${SDM_STATE##*/} is not for this branch — ignored (run Stage A first)"; return 0
    fi
    for k in "${!_sdm[@]}"; do
        [[ -n "${!k:-}" ]] || printf -v "$k" '%s' "${_sdm[$k]}"   # why: a non-empty explicit env wins; a value is assigned, never executed
    done
}
[[ -f "$SDM_STATE" ]] && sdm_load
sdm_save() { if [[ -L "$SDM_STATE" ]] || { [[ -e "$SDM_STATE" ]] && { [[ ! -O "$SDM_STATE" ]] || [[ -n "$(find "$SDM_STATE" \( -perm -g+w -o -perm -o+w \) -print)" ]]; }; }; then echo "Stage state: refusing to save $1 (${SDM_STATE##*/} is a symlink, not yours, or writable by others)"; return 1; fi; (umask 077; printf '%s=%s\n' "$1" "$(printf '%s' "$2" | base64 | tr -d '\n')" >> "$SDM_STATE"); }   # why: refuse exactly what the loader refuses, and create the file 600; base64 has no shell metacharacters, tr keeps one line

# Inputs from Stage F + G1 + G2: PR_NUM, PR_URL, REMOTE_CHOICE,
# MERGE_STRATEGY (rebase|merge), CI_STATE (green|timeout|failed).
REMOTE_CHOICE="${REMOTE_CHOICE:?Stage G3 needs REMOTE_CHOICE from Stage E2 — run E2 first}"   # why: a defaulted github acts on the wrong host when the state file was refused (L-055)
PR_NUM="${PR_NUM:?Stage G3 needs PR_NUM from Stage F}"
# why: it reaches gh/glab argv; a number can never be read as an option
[[ "$PR_NUM" =~ ^[0-9]+$ ]] || { echo "ABORT: Stage G3: PR_NUM '$PR_NUM' is not a number"; exit 1; }
PR_URL="${PR_URL:-}"
MERGE_STRATEGY="${MERGE_STRATEGY:-rebase}"
CI_STATE="${CI_STATE:-unknown}"

case "$CI_STATE" in
    green)
        : "${ORIGINAL_BRANCH:?Stage G3 needs ORIGINAL_BRANCH from Stage A}"
        DEFAULT_BRANCH="${DEFAULT_BRANCH:-main}"
        # DEFAULT_BRANCH comes from the remote's HEAD; refuse an option-shaped one.
        git check-ref-format --branch "$DEFAULT_BRANCH" >/dev/null \
            || { echo "ABORT: Stage G3: DEFAULT_BRANCH '$DEFAULT_BRANCH' is not a valid branch name"; exit 1; }
        case "$MERGE_STRATEGY" in
            rebase|merge|squash) ;;
            *) echo "ABORT: Stage G3: MERGE_STRATEGY '$MERGE_STRATEGY' is not rebase, merge or squash"; exit 1 ;;
        esac
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
            # why: the head name alone matches a fork's same-named PR (§6.8 SEC-2)
            XREPO=$(gh pr view "$PR_NUM" --json isCrossRepository --jq .isCrossRepository)
            [[ "$XREPO" == false ]] \
                || { echo "ABORT: Stage G3: PR $PR_NUM is from another repository (isCrossRepository=$XREPO)"; exit 1; }
            # No --delete-branch: gh's local step fails in a worktree and then
            # skips the remote delete (L-1332). Merge, then decide from the
            # server state, not gh's rc (E6).
            gh pr merge "$PR_NUM" --"$MERGE_STRATEGY" \
                || echo "Stage G3: gh pr merge rc=$? — checking PR state"
            # why: an unreadable state counts as not merged, so the step fails safe (no delete)
            STATE=$(gh pr view "$PR_NUM" --json state --jq .state 2>/dev/null || echo UNKNOWN)
            if [[ "$STATE" != MERGED ]]; then
                echo "STATUS: MERGE_FAILED — state=$STATE — see $PR_URL"
                export MERGE_DISPATCHED=0; sdm_save MERGE_DISPATCHED 0
                echo "MERGE_DISPATCHED=0"
                exit 0
            fi
            # Full ref, so a same-named tag is never deleted. rc 1 when the
            # branch is already gone (E12); ls-remote decides, not the rc.
            git push -q origin ":refs/heads/$ORIGINAL_BRANCH" \
                || echo "Stage G3: push --delete rc=$? (already gone server-side?) — checking ls-remote"
            # --exit-code: rc 2 = gone, 0 = still there; anything else could not
            # check, which must never read as "deleted" (L-1332).
            LS_RC=0
            git ls-remote --exit-code origin "refs/heads/$ORIGINAL_BRANCH" >/dev/null || LS_RC=$?
            if [[ "$LS_RC" -eq 0 ]]; then
                echo "STATUS: BRANCH_NOT_DELETED — $ORIGINAL_BRANCH"
            elif [[ "$LS_RC" -ne 2 ]]; then
                echo "STATUS: BRANCH_NOT_DELETED — $ORIGINAL_BRANCH (ls-remote rc=$LS_RC, could not verify)"
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
            export MERGE_DISPATCHED=0; sdm_save MERGE_DISPATCHED 0
            echo "MERGE_DISPATCHED=0"
            exit 0
            ;;
        esac
        export MERGE_DISPATCHED=1; sdm_save MERGE_DISPATCHED 1
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
        export MERGE_DISPATCHED=0; sdm_save MERGE_DISPATCHED 0
        ;;
    failed)
        # §6.8 M4 HIGH-1 fix (failed branch): remote-aware diagnostic hint.
        echo "STATUS: CI_FAILED — see $PR_URL"
        if [[ "$REMOTE_CHOICE" == "gitlab" ]]; then
            echo "  diagnostic: glab ci view ${MR_IID:-$PR_NUM}"
        else
            echo "  diagnostic: gh pr checks $PR_NUM"
        fi
        export MERGE_DISPATCHED=0; sdm_save MERGE_DISPATCHED 0
        ;;
    blocked)
        # §6.8 M4 HIGH-2 fix: G2's `manual|skipped` GitLab enum hand-off.
        # No merge; G2 already emitted the STATUS:CI_BLOCKED line.
        export MERGE_DISPATCHED=0; sdm_save MERGE_DISPATCHED 0
        ;;
    *)
        # §6.8 M4 MED-1 fix: emit a STATUS line for the unknown catchall so
        # downstream tooling parsing for `STATUS:` doesn't miss this terminal
        # state. REMOTE_CHOICE included for diagnostic context.
        echo "STATUS: CI_UNKNOWN — CI_STATE='$CI_STATE' REMOTE_CHOICE='$REMOTE_CHOICE'"
        export MERGE_DISPATCHED=0; sdm_save MERGE_DISPATCHED 0
        ;;
esac
# === stage-g3-merge (END) ===
```

```bash
# === stage-g4-cleanup (BEGIN) ===
set -euo pipefail

# Stage state: load what earlier stages saved (SKILL.md "State between stages").
SDM_STATE="$(git rev-parse --absolute-git-dir)/sole-dev-merge.env"   # why: absolute, so a later cd can't break sdm_save
SDM_KEYS=" ORIGINAL_BRANCH BASE_REF DEFAULT_BRANCH SLUG SDM_DIR CHANGED_FILES CHANGED_PY CHANGED_SH REMOTE_CHOICE PR_BODY_FILE PR_NUM PR_URL MERGE_STRATEGY CI_STATE MERGE_DISPATCHED n_github n_gitlab n_other "
sdm_load() {
    # why: a planted or shared file must never be read: symlink, other owner, or group/world-writable → refuse
    if [[ -L "$SDM_STATE" || ! -O "$SDM_STATE" || -n "$(find "$SDM_STATE" \( -perm -g+w -o -perm -o+w \) -print)" ]]; then
        echo "Stage state: refusing ${SDM_STATE##*/} (symlink, not owned by you, or writable by others)"; return 0
    fi
    local line k v dv
    declare -A _sdm=()
    while IFS= read -r line; do
        k=${line%%=*}; v=${line#*=}
        [[ "$SDM_KEYS" == *" $k "* ]] || { echo "Stage state: ignoring unknown key '$k'"; continue; }   # why: allowlist, never a free-form name
        # why: decode into a temp first, so a bad line never overwrites an earlier good value
        dv=$(printf '%s' "$v" | base64 -d 2>/dev/null) || { echo "Stage state: bad value for $k — ignored"; continue; }
        _sdm[$k]=$dv                                   # why: last good write wins
    done < "$SDM_STATE"
    # why: a missing or empty ORIGINAL_BRANCH counts as foreign (on a detached HEAD '' would equal '')
    if [[ -z "${_sdm[ORIGINAL_BRANCH]:-}" || "${_sdm[ORIGINAL_BRANCH]}" != "$(git branch --show-current)" ]]; then
        echo "Stage state: ${SDM_STATE##*/} is not for this branch — ignored (run Stage A first)"; return 0
    fi
    for k in "${!_sdm[@]}"; do
        [[ -n "${!k:-}" ]] || printf -v "$k" '%s' "${_sdm[$k]}"   # why: a non-empty explicit env wins; a value is assigned, never executed
    done
}
[[ -f "$SDM_STATE" ]] && sdm_load
sdm_save() { if [[ -L "$SDM_STATE" ]] || { [[ -e "$SDM_STATE" ]] && { [[ ! -O "$SDM_STATE" ]] || [[ -n "$(find "$SDM_STATE" \( -perm -g+w -o -perm -o+w \) -print)" ]]; }; }; then echo "Stage state: refusing to save $1 (${SDM_STATE##*/} is a symlink, not yours, or writable by others)"; return 1; fi; (umask 077; printf '%s=%s\n' "$1" "$(printf '%s' "$2" | base64 | tr -d '\n')" >> "$SDM_STATE"); }   # why: refuse exactly what the loader refuses, and create the file 600; base64 has no shell metacharacters, tr keeps one line

# Runs only on a successful merge: it stops unless G3 recorded MERGE_DISPATCHED=1.
# Inputs: ORIGINAL_BRANCH (from Stage A), PR_URL (from Stage F), MERGE_DISPATCHED (from G3).
: "${ORIGINAL_BRANCH:?Stage G4 needs ORIGINAL_BRANCH from Stage A}"
# why: G3 saves MERGE_DISPATCHED on every path that finishes; absent or 0 means no merge to clean up after
[[ "${MERGE_DISPATCHED:-}" == 1 ]] || { echo "ABORT: Stage G4: no successful merge recorded (MERGE_DISPATCHED='${MERGE_DISPATCHED:-}')"; exit 1; }
PR_URL="${PR_URL:-}"
DEFAULT_BRANCH="${DEFAULT_BRANCH:-main}"
# Refuse option-shaped or invalid names before they reach diff/branch
# (security audit: `--output=` would clobber a file).
git check-ref-format --branch "$ORIGINAL_BRANCH" >/dev/null \
    || { echo "ABORT: Stage G4: invalid ORIGINAL_BRANCH '$ORIGINAL_BRANCH'"; exit 1; }
git check-ref-format --branch "$DEFAULT_BRANCH" >/dev/null \
    || { echo "ABORT: Stage G4: invalid DEFAULT_BRANCH '$DEFAULT_BRANCH'"; exit 1; }

# Absolute forms on both sides: the raw --git-common-dir is relative from a
# subdirectory, which would misread a plain checkout as a worktree (E7).
GIT_DIR_ABS=$(git rev-parse --path-format=absolute --git-dir)
COMMON_ABS=$(git rev-parse --path-format=absolute --git-common-dir)
if [[ "$GIT_DIR_ABS" == "$COMMON_ABS" ]]; then
    # Plain checkout: switch to the default branch and fast-forward it.
    git checkout -q "$DEFAULT_BRANCH"
    # No `pull`: with pull.rebase=true, `pull --ff-only` fails on a dirty tree (E10).
    git fetch -q --prune origin
    git merge -q --ff-only "origin/$DEFAULT_BRANCH"
    git branch -q -D "$ORIGINAL_BRANCH" \
        || echo "Stage G4: local branch $ORIGINAL_BRANCH not deleted (rc=$?)"
else
    # Linked worktree: the default branch belongs to the main worktree, so
    # update it there and leave this worktree and its branch alone (L-1332).
    WT_LIST=$(git worktree list --porcelain)   # captured once: no early-exit pipe under pipefail
    MAIN_WT=$(awk '/^worktree / && !w { sub(/^worktree /, ""); w = $0 } END { print w }' <<<"$WT_LIST")
    git -C "$MAIN_WT" fetch -q --prune origin
    if [[ "$(git -C "$MAIN_WT" branch --show-current)" != "$DEFAULT_BRANCH" ]]; then
        if [[ $'\n'"$WT_LIST"$'\n' == *$'\n'"branch refs/heads/$DEFAULT_BRANCH"$'\n'* ]]; then
            MAIN_NOTE="STATUS: MAIN_NOT_UPDATED — $DEFAULT_BRANCH is in use by another worktree"
        else
            git -C "$MAIN_WT" fetch -q origin "$DEFAULT_BRANCH:$DEFAULT_BRANCH" \
                || MAIN_NOTE="STATUS: MAIN_NOT_UPDATED — non-fast-forward"
        fi
    elif [[ -n "$(git -C "$MAIN_WT" status --porcelain --untracked-files=no)" ]]; then
        # Never auto-revert someone's edits in the main worktree (L-1347, Q5).
        echo "STATUS: MAIN_CHECKOUT_DIRTY — $(git -C "$MAIN_WT" status --porcelain --untracked-files=no | tr '\n' ' ')"
        exit 0
    else
        git -C "$MAIN_WT" merge -q --ff-only "origin/$DEFAULT_BRANCH"
    fi
    # why: shown for the L-1332 content check only; a missing local ref must not stop the cleanup hint
    git -C "$MAIN_WT" diff --stat "refs/heads/$ORIGINAL_BRANCH" "refs/heads/$DEFAULT_BRANCH" -- || true
    echo "Operator cleanup (after reviewing the diff above):"
    printf '  git -C %q worktree remove %q\n' "$MAIN_WT" "$(git rev-parse --show-toplevel)"
    printf '  git -C %q branch -D %q\n' "$MAIN_WT" "$ORIGINAL_BRANCH"
    WT_NOTE=" worktree=$(git rev-parse --show-toplevel)"
fi

MERGE_SHA=$(git -C "${MAIN_WT:-.}" rev-parse --short "$DEFAULT_BRANCH")
echo "Stage G4: cleanup done — $DEFAULT_BRANCH at $MERGE_SHA${WT_NOTE:-}"
echo "Final: branch=$ORIGINAL_BRANCH merged into $DEFAULT_BRANCH (sha=$MERGE_SHA)${PR_URL:+ — $PR_URL}"
# One terminal STATUS line: OK only when the default branch was really updated.
if [[ -n "${MAIN_NOTE:-}" ]]; then
    echo "$MAIN_NOTE"
else
    echo "STATUS: OK${WT_NOTE:-}"
fi
# === stage-g4-cleanup (END) ===
```
