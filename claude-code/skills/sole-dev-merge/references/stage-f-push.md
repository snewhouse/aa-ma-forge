# Stage F: push and PR/MR creation — the idempotent push and PR/MR creation.

### Stage F — Push + PR/MR creation (idempotent)

`git push -u origin HEAD`, then check for an existing PR/MR and either update
the body or create fresh. Title is derived from the topmost Conventional
Commit subject (truncated to 70 chars) when not explicitly provided.

- **GitHub** — `gh pr view --json url` detects existing PR; reuse via
  `gh pr edit --body-file "$BODY"` or create via
  `gh pr create --title "$TITLE" --body-file "$BODY"`.
- **GitLab** — `glab mr view` detects existing MR; reuse via
  `glab mr update --description "$(cat $BODY)"` or create via
  `glab mr create --title "$TITLE" --description "$(cat $BODY)"` (NOT
  `--description-file` — that flag is fabricated; see reference.md "WRONG
  SYNTAX TO NEVER USE").

```bash
# === stage-f-push (BEGIN) ===
set -euo pipefail

REMOTE_CHOICE="${REMOTE_CHOICE:-github}"
PR_BODY_FILE="${PR_BODY_FILE:-/tmp/sole-dev-merge-body.md}"

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
        echo "PR_OP=edit"
        gh pr edit --body-file "$PR_BODY_FILE"
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

export PR_TITLE PR_NUM PR_URL MR_IID
# === stage-f-push (END) ===
```
