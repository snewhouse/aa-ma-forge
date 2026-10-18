# Stage F: push and PR/MR creation — the idempotent push and PR/MR creation.

## Contents

  - [Stage F — Push + PR/MR creation (idempotent)](#stage-f--push--prmr-creation-idempotent)

### Stage F — Push + PR/MR creation (idempotent)

`git push -u origin HEAD`, then check for an existing PR/MR and either update
the body or create fresh. Title is derived from the topmost Conventional
Commit subject (truncated to 70 chars) when not explicitly provided.

- **GitHub** — one `gh pr view --json number,url,isCrossRepository,headRefName,state`
  call finds the existing PR. Stage F updates its body only if it is open and
  this branch's own (same repository, head = the current branch). A closed or
  merged PR on a reused branch name leads to a new PR, which Stage F then reads
  by the URL `gh pr create` printed. It uses REST
  (`gh api -X PATCH repos/{owner}/{repo}/pulls/$PR_NUM -F "body=@$BODY"`) and
  reads the body back. `--jq .body` adds one newline, so the check is
  `cmp <(cat "$BODY"; echo) <(gh api … --jq .body)`. Any other outcome prints
  `STATUS: PR_BODY_NOT_UPDATED — PR #N reason=<r>` and keeps rc 0. A PR that is
  not this branch's is never saved for Stage G. The title is never touched. Never use gh's pr-edit subcommand here: it hits a
  Projects-classic GraphQL error and the body silently stays (L-1309). With no
  PR, Stage F creates one: `gh pr create --title "$TITLE" --body-file "$BODY"`.
- **GitLab** — one `glab mr view -F json` lookup (iid, url, same project,
  source branch, state) finds the existing MR. Stage F updates it only if it is
  open and this branch's own, by iid: `glab mr update "$MR_IID" --description
  "$(cat $BODY)"`. Otherwise it prints `STATUS: PR_BODY_NOT_UPDATED — MR !N
  reason=<r>`, and a foreign MR is never saved. With no open MR it creates one via
  `glab mr create --title "$TITLE" --description "$(cat $BODY)"` (NOT
  `--description-file` — that flag is fabricated; see reference.md "WRONG
  SYNTAX TO NEVER USE").

```bash
# === stage-f-push (BEGIN) ===
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

REMOTE_CHOICE="${REMOTE_CHOICE:?Stage F needs REMOTE_CHOICE from Stage E2 — run E2 first}"   # why: a defaulted github acts on the wrong host when the state file was refused (L-055)
PR_BODY_FILE="${PR_BODY_FILE:-}"   # why: from Stage E3 via the state file; no shared temp-dir default

# §6.8 MED-2 fix: guard against missing/empty body file. If Stage E3 was
# skipped or its output is empty, fail loudly rather than push a blank PR.
if [[ ! -s "$PR_BODY_FILE" ]]; then
    echo "ABORT: Stage F requires non-empty body file at $PR_BODY_FILE — run Stage E3 first"
    exit 1
fi

# Title — derive from topmost commit subject if not pre-set; truncate to 70 chars.
if [[ -z "${PR_TITLE:-}" ]]; then
    PR_TITLE=$(git log -1 --format=%s 2>/dev/null || echo "(no title)")
fi
PR_TITLE="${PR_TITLE:0:70}"
echo "PR_TITLE=$PR_TITLE"

# Idempotent push — first invocation creates the remote-tracking ref;
# subsequent invocations fast-forward.
git push -u origin HEAD

PR_NUM=0
PR_URL=""
MR_IID=0

# why: a no-arg `gh pr view` / `glab mr view` selects by branch name, so a fork's same-named
# PR/MR can come back (§6.8 SEC-2, live run 2): only this branch's own open one is used
NOT_OURS="is not this branch's own (a fork's, or another head branch's)"

if [[ "$REMOTE_CHOICE" == "github" ]]; then
    # One lookup for number, url, owner and state (gojq @tsv; gh 2.46.0). An argument picks the PR.
    # why: 2>/dev/null — "no pull requests found" is the expected answer on a first run
    pr_lookup() {
        local row
        row=$(gh pr view "$@" --json number,url,isCrossRepository,headRefName,state \
                  --jq '[.number,.url,.isCrossRepository,.headRefName,.state]|@tsv' 2>/dev/null) || return 1
        IFS=$'\t' read -r PR_NUM PR_URL PR_XREPO PR_HEAD PR_STATE <<<"$row"
    }
    pr_ours() { [[ "$PR_XREPO" == false && "$PR_HEAD" == "$(git branch --show-current)" ]]; }
    # why: a closed or merged PR on a reused branch name is history, not this run's PR
    if pr_lookup && [[ "$PR_STATE" == OPEN ]]; then
        echo "PR_OP=update"
        # why: REST, not gh's pr-edit subcommand — that hits a Projects-classic GraphQL error here and the body silently stays (L-1309)
        # why: --jq prints the body plus one newline (gh 2.46.0, 4.0 probe), so the read-back is compared with the file plus one
        REASON=""
        if [[ ! "$PR_NUM" =~ ^[1-9][0-9]*$ ]]; then
            REASON=no-pr-number
        elif ! pr_ours; then
            REASON=not-this-branch
        elif ! gh api -X PATCH "repos/{owner}/{repo}/pulls/$PR_NUM" -F "body=@$PR_BODY_FILE" >/dev/null; then
            REASON=patch-failed
        elif ! cmp -s <(cat "$PR_BODY_FILE"; echo) <(gh api "repos/{owner}/{repo}/pulls/$PR_NUM" --jq .body); then
            REASON=readback-differs
        fi
        case "$REASON" in
            "")              echo "Stage F: PR #$PR_NUM body updated (read-back matches)" ;;
            not-this-branch) echo "STATUS: PR_BODY_NOT_UPDATED — PR #$PR_NUM reason=not-this-branch (PR #$PR_NUM $NOT_OURS; open this branch's PR by hand — Stage G will stop)" ;;
            no-pr-number)    echo "STATUS: PR_BODY_NOT_UPDATED — PR #$PR_NUM reason=no-pr-number (gh pr view gave no PR number; check the PR by hand)" ;;
            *)               echo "STATUS: PR_BODY_NOT_UPDATED — PR #$PR_NUM reason=$REASON (its body on GitHub is not $PR_BODY_FILE; set it by hand before Stage G merges)" ;;
        esac
        # why: never hand Stage G a PR that is not this branch's own
        if [[ "$REASON" == no-pr-number || "$REASON" == not-this-branch ]]; then PR_NUM=0; PR_URL=""; fi
    else
        echo "PR_OP=create"
        CREATED=$(gh pr create --title "$PR_TITLE" --body-file "$PR_BODY_FILE")
        echo "$CREATED"
        PR_NUM=0; PR_URL=""
        # why: read the new PR by the URL create printed, not by branch name (live run 2); an unreadable PR stays 0, never saved below
        if pr_lookup "${CREATED##*$'\n'}" && ! pr_ours; then
            echo "Stage F: WARNING — PR #$PR_NUM $NOT_OURS; not saved"
            PR_NUM=0; PR_URL=""
        fi
    fi
elif [[ "$REMOTE_CHOICE" == "gitlab" ]]; then
    # One lookup for iid, url, owner and state (glab -F json; plain jq string interpolation).
    # why: 2>/dev/null — "no merge request" is the expected answer on a first run
    mr_lookup() {
        local row
        row=$(glab mr view -F json \
                  --jq '"\(.iid)\t\(.web_url)\t\(.source_project_id == .target_project_id)\t\(.source_branch)\t\(.state)"' 2>/dev/null) || return 1
        IFS=$'\t' read -r MR_IID PR_URL MR_SAMEPROJ MR_SRC MR_STATE <<<"$row"
    }
    mr_ours() { [[ "$MR_SAMEPROJ" == true && "$MR_SRC" == "$(git branch --show-current)" ]]; }
    if mr_lookup && [[ "$MR_STATE" == opened ]]; then
        echo "MR_OP=update"
        if [[ ! "$MR_IID" =~ ^[1-9][0-9]*$ ]] || ! mr_ours; then
            echo "STATUS: PR_BODY_NOT_UPDATED — MR !$MR_IID reason=not-this-branch (MR !$MR_IID $NOT_OURS; open this branch's MR by hand — Stage G will stop)"
            MR_IID=0; PR_URL=""
        elif ! glab mr update "$MR_IID" --description "$(cat "$PR_BODY_FILE")"; then
            echo "STATUS: PR_BODY_NOT_UPDATED — MR !$MR_IID reason=patch-failed (its description on GitLab is not $PR_BODY_FILE; set it by hand before Stage G merges)"
        fi
    else
        echo "MR_OP=create"
        glab mr create --title "$PR_TITLE" --description "$(cat "$PR_BODY_FILE")"
        MR_IID=0; PR_URL=""
        # why: the same ownership rule after create; an unreadable MR stays 0, never saved below
        if mr_lookup && ! mr_ours; then
            echo "Stage F: WARNING — MR !$MR_IID $NOT_OURS; not saved"
            MR_IID=0; PR_URL=""
        fi
    fi
    # Stage G2/G3 also reads PR_NUM for cross-remote symmetry; alias to MR_IID
    # on the GitLab branch so downstream stages can use one variable name.
    PR_NUM="$MR_IID"
fi

echo "PR_NUM=$PR_NUM"
echo "PR_URL=$PR_URL"
[[ "$REMOTE_CHOICE" == "gitlab" ]] && echo "MR_IID=$MR_IID"

# Stage G reads PR_NUM/PR_URL in its own shells. A 0 is never saved: G2/G3
# then stop on a missing PR_NUM instead of polling or merging PR 0.
if [[ -n "$PR_NUM" && "$PR_NUM" != 0 ]]; then
    sdm_save PR_NUM "$PR_NUM"
    sdm_save PR_URL "$PR_URL"
else
    echo "Stage F: WARNING — no PR/MR number resolved; not saved (Stage G uses an earlier saved PR_NUM, or stops if there is none)"
fi

export PR_TITLE PR_NUM PR_URL MR_IID
# === stage-f-push (END) ===
```
