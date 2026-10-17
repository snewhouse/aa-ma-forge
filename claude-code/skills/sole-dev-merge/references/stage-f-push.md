# Stage F: push and PR/MR creation — the idempotent push and PR/MR creation.

## Contents

  - [Stage F — Push + PR/MR creation (idempotent)](#stage-f--push--prmr-creation-idempotent)

### Stage F — Push + PR/MR creation (idempotent)

`git push -u origin HEAD`, then check for an existing PR/MR and either update
the body or create fresh. Title is derived from the topmost Conventional
Commit subject (truncated to 70 chars) when not explicitly provided.

- **GitHub** — `gh pr view --json url` detects existing PR. To reuse it, Stage F
  resolves `PR_NUM`, updates the body over REST
  (`gh api -X PATCH repos/{owner}/{repo}/pulls/$PR_NUM -F "body=@$BODY"`), and
  reads it back. `--jq .body` adds one newline, so the check is
  `cmp <(cat "$BODY"; echo) <(gh api … --jq .body)`. A failed PATCH or a
  mismatch prints `STATUS: PR_BODY_NOT_UPDATED — PR #N` and keeps rc 0. The
  title is never touched. Never use gh's pr-edit subcommand here: it hits a
  Projects-classic GraphQL error and the body silently stays (L-1309). With no
  PR, Stage F creates one: `gh pr create --title "$TITLE" --body-file "$BODY"`.
- **GitLab** — `glab mr view` detects existing MR; reuse via
  `glab mr update --description "$(cat $BODY)"` or create via
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

if [[ "$REMOTE_CHOICE" == "github" ]]; then
    if gh pr view --json url >/dev/null 2>&1; then
        echo "PR_OP=update"
        PR_NUM=$(gh pr view --json number --jq '.number' 2>/dev/null || echo "0")   # why: the REST update needs the number first
        # why: REST, not gh's pr-edit subcommand — that hits a Projects-classic GraphQL error here and the body silently stays (L-1309)
        # why: --jq prints the body plus one newline, so the read-back is compared with the file plus one (4.0 probe)
        if [[ "$PR_NUM" =~ ^[1-9][0-9]*$ ]] \
            && gh api -X PATCH "repos/{owner}/{repo}/pulls/$PR_NUM" -F "body=@$PR_BODY_FILE" >/dev/null \
            && cmp -s <(cat "$PR_BODY_FILE"; echo) <(gh api "repos/{owner}/{repo}/pulls/$PR_NUM" --jq .body); then
            echo "Stage F: PR #$PR_NUM body updated (read-back matches)"
        else
            echo "STATUS: PR_BODY_NOT_UPDATED — PR #$PR_NUM (its body on GitHub is not $PR_BODY_FILE; set it by hand)"
        fi
    else
        echo "PR_OP=create"
        gh pr create --title "$PR_TITLE" --body-file "$PR_BODY_FILE"
    fi
    # §6.8 M4 CRITICAL-1 fix: extract PR identifiers for Stage G consumption.
    # Real gh CLI supports `--jq` filter on the json output; tests' gh stub
    # honours these filters explicitly.
    PR_URL=$(gh pr view --json url    --jq '.url'    2>/dev/null || echo "")
    PR_NUM=$(gh pr view --json number --jq '.number' 2>/dev/null || echo "0")
elif [[ "$REMOTE_CHOICE" == "gitlab" ]]; then
    if glab mr view >/dev/null 2>&1; then
        echo "MR_OP=update"
        glab mr update --description "$(cat "$PR_BODY_FILE")"
    else
        echo "MR_OP=create"
        glab mr create --title "$PR_TITLE" --description "$(cat "$PR_BODY_FILE")"
    fi
    # §6.8 M4 CRITICAL-1 fix: GitLab MR identifiers for Stage G.
    PR_URL=$(glab mr view --jq '.web_url' 2>/dev/null || echo "")
    MR_IID=$(glab mr view --jq '.iid'     2>/dev/null || echo "0")
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
