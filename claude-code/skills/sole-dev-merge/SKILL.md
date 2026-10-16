---
name: sole-dev-merge
description: PR/MR-based merge workflow with scope-aware CI checks, review, security pass, and auto-merge. Run only when the user asks to merge a branch or PR.
disable-model-invocation: true
---

# /sole-dev-merge — PR/MR merge workflow (v2)

PR/MR-based merge workflow for sole developers. Runs scope-aware local CI
(closing L-007), dispatches code review + 3-source security pass
(security-auditor agent + Ruff S + ShellCheck), opens a PR via `gh` or MR via
`glab` (default GitLab when both remotes present), polls CI to green, then
auto-merges with `--rebase` for linear history, then deletes the remote branch
itself and checks it is gone (worktree-safe, L-1332).

**Replaces:** the legacy fast-merge `/sole-dev-merge` user-local command. The
plugin install (`scripts/install.sh`) links `~/.claude/skills/sole-dev-merge/`
after backing up anything real in its way to
`~/.claude/backups/aa-ma-forge-<timestamp>/`, and removes the old
`~/.claude/commands/sole-dev-merge.md` link once its source is gone (ADR-0020).

**Plan-of-record:** see ADR-0008 (`docs/adr/0008-sole-dev-merge-pr-workflow.md`)
once landed. Rationale for command-only design (no skill/lib pattern), 3-source
security rationale, and backward-compatibility strategy live there.

**Assumptions** (enforced by Stage A / Stage E0):
- One `/sole-dev-merge` invocation per repo at a time (no concurrency lock —
  sole-developer assumption).
- `gh auth status` / `glab auth status` succeed for the active remote.
- `main` is the default branch.

**Suppress migration banner:** `AA_MA_SUPPRESS_MIGRATION_BANNER=1`.

---

## Migration banner (runs FIRST, before Stage A)

The legacy user-local `/sole-dev-merge` (fast-merge) has been retired and
replaced by this PR/MR workflow per ADR-0008. `scripts/install.sh` auto-
backs-up the old command to `~/.claude/backups/aa-ma-forge-<ts>/` before
symlinking the new one. The banner alerts the operator on first invocation
post-deploy. Suppress with `AA_MA_SUPPRESS_MIGRATION_BANNER=1`.

```bash
# === stage-banner (BEGIN) ===
set -euo pipefail

# Migration banner per ADR-0008. Plan §5.7 falsifiable AC: env-var
# suppression. "Once per session" is implemented via a /tmp sentinel so
# subsequent invocations within the same login session stay silent.
if [[ "${AA_MA_SUPPRESS_MIGRATION_BANNER:-0}" != "1" ]]; then
    SENTINEL="${TMPDIR:-/tmp}/sole-dev-merge-banner-shown"
    if [[ ! -f "$SENTINEL" ]]; then
        cat <<'BANNER'
NOTE: /sole-dev-merge has been updated to a PR/MR workflow with 3-source
security review and idempotent auto-merge (ADR-0008). The legacy fast-merge
path is retired; the user-local copy was auto-backed-up to
~/.claude/backups/aa-ma-forge-<ts>/ on install.

See docs/adr/0008-sole-dev-merge-pr-workflow.md for rationale, alternatives,
and rollback paths. Set AA_MA_SUPPRESS_MIGRATION_BANNER=1 to silence.
BANNER
        : > "$SENTINEL"
    fi
fi
# === stage-banner (END) ===
```

---

## State between stages

Every block below runs in its own Bash call, so a shell variable set in one
block is gone in the next (forge L-055). The values travel in a **stage state
file** instead: `"$(git rev-parse --absolute-git-dir)/sole-dev-merge.env"`. It
lives in this worktree's own git-dir, so it is untracked, never pushed, and
separate per worktree.

- **Stage A starts it.** It deletes the last run's file first (an aborted A
  leaves none) and the earlier run dirs, then saves `ORIGINAL_BRANCH`,
  `BASE_REF`, `DEFAULT_BRANCH`, `SLUG` and `SDM_DIR`. Its `Stage state:` line
  prints both paths.
- **Every later block loads it** with the same loader. A non-empty explicit
  env value beats the file, and the file beats a block's own defaults. A
  required value that is still missing stops the block loudly.
- **Saves are appended** as `KEY=<base64>` by `sdm_save`; the last write of a
  key wins. B saves `CHANGED_FILES/PY/SH`, E2 `REMOTE_CHOICE`, E3
  `PR_BODY_FILE`, F `PR_NUM`/`PR_URL`, G1 `MERGE_STRATEGY`, G2 `CI_STATE`, G3
  `MERGE_DISPATCHED` (G4 runs only when it is `1`).
- **Run files** (agent outputs, scanner reports, findings, reviewer notes, the
  AUQ bridge, the PR body) live in `SDM_DIR`, a mode-700 directory next to the
  state file. No run file is written to the shared temp directory.
- **The loader trusts nothing it reads.** It ignores a file written on another
  branch or with no branch (with a message), refuses a symlinked or
  group/world-writable file or one you don't own, accepts only the keys named in
  `SDM_KEYS`, and never `eval`s a value.
- **Saving refuses the same files.** `sdm_save` will not write through a
  symlinked state file, one you don't own, or one writable by group or others;
  the refusal stops the block. When it creates the file, the file is mode 600.
- **To re-answer a question** (for example the dual-remote choice), re-run the
  block with the answer set explicitly, such as `REMOTE_CHOICE=github`. The block
  saves the explicit value. For E2, re-run E1 and E2 together in one Bash call:
  E2 reads E1's remote counts, which are not in the state file.

## Workflow stages

The command runs sequentially through stages **A → G**. Each stage is
self-contained (one reason to change, per SOC). Implementation lives in
named bash blocks: inline below for Stages A–B, in `references/stage-*.md`
for Stages C–G. Read each stage's reference when you reach it.

### Stage A — Pre-flight checks

Captures `ORIGINAL_BRANCH` and `BASE_REF`; aborts with one of the exact
messages below on failure; otherwise prints `Pre-flight OK`.

| Branch condition | ABORT string |
|------------------|--------------|
| Not in a git repository | `ABORT: Not inside a git repository` |
| Detached HEAD | `ABORT: Detached HEAD — check out the branch to merge` |
| On `main`/`master` | `ABORT: Cannot run /sole-dev-merge from $ORIGINAL_BRANCH branch` |
| Uncommitted changes | `ABORT: Uncommitted changes detected (commit or stash first)` |
| No git remote | `ABORT: No git remote configured (need github.com or gitlab.com remote)` |
| No commits ahead of base | `ABORT: No commits ahead of $DEFAULT_BRANCH (nothing to merge)` |
| An explicit `SLUG` that is not a plain name | `ABORT: SLUG '<slug>' must be letters, digits, '.', '_' or '-'` |

ABORT exits non-zero (rc=1). `Pre-flight OK` exits zero and saves
`ORIGINAL_BRANCH`, `BASE_REF`, `DEFAULT_BRANCH`, `SLUG` and `SDM_DIR` to the
stage state file for the later stages (exports alone don't survive a Bash call).

```bash
# === stage-a-preflight (BEGIN) ===
set -euo pipefail

# 0. Stage state file (see "State between stages"). A writes it; it never loads it.
# why: 2>/dev/null — git's own "fatal:" text is replaced by the ABORT line below
_GIT_DIR=$(git rev-parse --absolute-git-dir 2>/dev/null) || { echo "ABORT: Not inside a git repository"; exit 1; }
SDM_STATE="$_GIT_DIR/sole-dev-merge.env"
rm -f "$SDM_STATE"   # why: first, so an A that aborts below never leaves the last run's state behind
sdm_save() { if [[ -L "$SDM_STATE" ]] || { [[ -e "$SDM_STATE" ]] && { [[ ! -O "$SDM_STATE" ]] || [[ -n "$(find "$SDM_STATE" \( -perm -g+w -o -perm -o+w \) -print)" ]]; }; }; then echo "Stage state: refusing to save $1 (${SDM_STATE##*/} is a symlink, not yours, or writable by others)"; return 1; fi; (umask 077; printf '%s=%s\n' "$1" "$(printf '%s' "$2" | base64 | tr -d '\n')" >> "$SDM_STATE"); }   # why: refuse exactly what the loader refuses, and create the file 600; base64 has no shell metacharacters, tr keeps one line

# 1. Capture original branch
ORIGINAL_BRANCH=$(git branch --show-current 2>/dev/null || echo "")
if [[ -z "$ORIGINAL_BRANCH" ]]; then
    echo "ABORT: Detached HEAD — check out the branch to merge"
    exit 1
fi

# 2. Refuse if on default branch (main/master)
if [[ "$ORIGINAL_BRANCH" == "main" || "$ORIGINAL_BRANCH" == "master" ]]; then
    echo "ABORT: Cannot run /sole-dev-merge from $ORIGINAL_BRANCH branch"
    exit 1
fi

# 3. Refuse on uncommitted changes (modified or untracked)
if [[ -n "$(git status --porcelain)" ]]; then
    echo "ABORT: Uncommitted changes detected (commit or stash first)"
    exit 1
fi

# 4. Require at least one remote configured
if [[ -z "$(git remote)" ]]; then
    echo "ABORT: No git remote configured (need github.com or gitlab.com remote)"
    exit 1
fi

# 5. Resolve default branch (prefer origin/HEAD, fall back to "main")
DEFAULT_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null \
    | sed 's@^refs/remotes/origin/@@' || true)
DEFAULT_BRANCH="${DEFAULT_BRANCH:-main}"

# Resolve a usable base ref (prefer local, fall back to remote tracking)
if git rev-parse --verify -q "$DEFAULT_BRANCH" >/dev/null; then
    BASE_REF="$DEFAULT_BRANCH"
elif git rev-parse --verify -q "origin/$DEFAULT_BRANCH" >/dev/null; then
    BASE_REF="origin/$DEFAULT_BRANCH"
else
    echo "ABORT: Cannot resolve $DEFAULT_BRANCH or origin/$DEFAULT_BRANCH"
    exit 1
fi

# 6. Require at least one commit ahead of base
AHEAD=$(git rev-list --count "${BASE_REF}..HEAD")
if [[ "$AHEAD" -eq 0 ]]; then
    echo "ABORT: No commits ahead of $DEFAULT_BRANCH (nothing to merge)"
    exit 1
fi

# 7. Start this run's state: one SLUG, a private run dir, the keys every later stage reads.
SLUG="${SLUG:-$(date +%Y%m%d-%H%M%S)-$$}"
if [[ ! "$SLUG" =~ ^[A-Za-z0-9._-]+$ ]]; then
    echo "ABORT: SLUG '$SLUG' must be letters, digits, '.', '_' or '-'"
    exit 1
fi
SDM_DIR="$_GIT_DIR/sdm-$SLUG"
# why: once the state file is gone, earlier run dirs are unreachable; removing them stops
# them piling up and means this run never inherits a dir (or a link) it did not make
rm -rf -- "$_GIT_DIR"/sdm-*
mkdir -m 700 "$SDM_DIR"   # why: -m sets the mode outright; sdm_save creates the state file 600 itself
for _k in ORIGINAL_BRANCH BASE_REF DEFAULT_BRANCH SLUG SDM_DIR; do sdm_save "$_k" "${!_k}"; done

export ORIGINAL_BRANCH BASE_REF DEFAULT_BRANCH SLUG SDM_DIR
echo "Pre-flight OK (branch=$ORIGINAL_BRANCH, base=$BASE_REF, ahead=$AHEAD)"
echo "Stage state: ${SDM_STATE} (run dir ${SDM_DIR})"
# === stage-a-preflight (END) ===
```

### Stage B — Scope-aware CI checks (L-007 guard)

Computes `CHANGED_FILES = git diff --name-only ${BASE_REF}...HEAD` (triple-dot
symmetric difference — only files this branch introduced); splits into
`CHANGED_PY` / `CHANGED_SH`. Runs `ruff format` / `ruff check --fix` against
in-scope `*.py` only (NOT whole-tree — that's the L-007 fix). Best-effort
`mypy` / `pytest -m "not perf and not slow"` / `pre-commit run --files` run
only when their config artefacts exist; best-effort means each prints its rc
(`Stage B: pytest rc=N (best-effort)`) and a non-zero rc never stops the skill.
ruff, mypy, pytest and pre-commit's file hooks see the working tree, ruff's
unstaged fixes included. pre-commit gets the branch range in its env
(`PRE_COMMIT_FROM_REF`/`PRE_COMMIT_TO_REF`, ADR-0018), never as flags (those
stash the fixes), so check-conventions checks the committed lines base..HEAD.
Then the **L-007 guard** restores any out-of-scope tracked file to HEAD (index
and working tree). A file HEAD lacks (untracked, or newly staged) is never
deleted: it is unstaged if needed, left in place, and listed.

```bash
# === stage-b-scope (BEGIN) ===
set -euo pipefail

# Stage state: load what earlier stages saved (SKILL.md "State between stages").
SDM_STATE="$(git rev-parse --absolute-git-dir)/sole-dev-merge.env"   # why: absolute, so a later cd can't break sdm_save
SDM_KEYS=" ORIGINAL_BRANCH BASE_REF DEFAULT_BRANCH SLUG SDM_DIR CHANGED_FILES CHANGED_PY CHANGED_SH REMOTE_CHOICE PR_BODY_FILE PR_NUM PR_URL MERGE_STRATEGY CI_STATE MERGE_DISPATCHED "
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

# Stage A exports BASE_REF; defensive fallback in case Stage B is run alone
BASE_REF="${BASE_REF:-main}"

# Triple-dot: files this branch introduced (NOT files that drifted on base since)
CHANGED_FILES=$(git diff --name-only "${BASE_REF}...HEAD" || true)
CHANGED_PY=$(echo "$CHANGED_FILES" | grep '\.py$' || true)
CHANGED_SH=$(echo "$CHANGED_FILES" | grep '\.sh$' || true)
for _k in CHANGED_FILES CHANGED_PY CHANGED_SH; do sdm_save "$_k" "${!_k}"; done   # why: B-commit and Stage C read these in their own shells

N_TOTAL=$(echo "$CHANGED_FILES" | grep -c . || true)
N_PY=$(echo "$CHANGED_PY" | grep -c . || true)
N_SH=$(echo "$CHANGED_SH" | grep -c . || true)
echo "Stage B scope: $N_TOTAL file(s) — $N_PY Python, $N_SH shell"

# 1. Format Python (in-scope only)
if [[ -n "$CHANGED_PY" ]]; then
    while IFS= read -r f; do
        if [[ -f "$f" ]]; then
            ruff format "$f" || true
        fi
    done <<< "$CHANGED_PY"
fi

# 2. Lint with fix (in-scope only). Tolerant — unfixable errors surface in Stage D.
if [[ -n "$CHANGED_PY" ]]; then
    while IFS= read -r f; do
        if [[ -f "$f" ]]; then
            ruff check --fix "$f" || true
        fi
    done <<< "$CHANGED_PY"
fi

# 3. Typecheck (best-effort, only when [tool.mypy] is configured)
if [[ -f pyproject.toml ]] && grep -q '^\[tool\.mypy\]' pyproject.toml; then
    uv run mypy src/ 2>&1 || true
fi

# 4. Pytest fast tier (best-effort, only when tests/ exists): the rc is printed, never hidden
if [[ -d tests ]]; then
    PYTEST_RC=0
    uv run pytest -m "not perf and not slow" || PYTEST_RC=$?
    echo "Stage B: pytest rc=$PYTEST_RC (best-effort)"
fi

# 5. Pre-commit (only when configured; in-scope files only). The range goes in env, not
# as flags: flags make pre-commit stash ruff's unstaged fixes (ADR-0018).
if [[ -f .pre-commit-config.yaml && -n "$CHANGED_FILES" ]]; then
    PC_RC=0
    # shellcheck disable=SC2086  # Intentional word-splitting for multi-file arg
    PRE_COMMIT_FROM_REF="$BASE_REF" PRE_COMMIT_TO_REF=HEAD pre-commit run --files $CHANGED_FILES || PC_RC=$?
    echo "Stage B: pre-commit rc=$PC_RC (best-effort)"
fi

# 6. L-007 GUARD — undo out-of-scope changes made by 1-5; never delete a file HEAD lacks
declare -A IN_SCOPE=()
while IFS= read -r f; do
    [[ -n "$f" ]] && IN_SCOPE["$f"]=1
done <<< "$CHANGED_FILES"

REVERTED=()
LEFT=()
while IFS= read -r line; do
    [[ -z "$line" ]] && continue
    # porcelain row: "XY path" where XY is 2-char status + space; strip the 3-char prefix
    path="${line:3}"
    [[ -n "${IN_SCOPE[$path]:-}" ]] && continue
    if [[ "${line:0:2}" == "??" ]]; then
        LEFT+=("$path")   # why: an untracked file may be the operator's; never delete it
    elif ! git cat-file -e "HEAD:$path" 2>/dev/null; then   # why: 2>/dev/null — "not in HEAD" is the answer, not an error
        # why: restoring a path HEAD lacks deletes it (rc 0); unstage only and keep the file
        if git restore --staged -- "$path"; then LEFT+=("$path"); else echo "L-007 guard: could not unstage $path"; fi
    elif git restore --source=HEAD --staged --worktree -- "$path"; then
        REVERTED+=("$path")   # why: --staged too — checkout -- restores from the index, so a staged edit survived
    else
        echo "L-007 guard: could not restore $path to HEAD"
    fi
done < <(git status --porcelain)

if [[ ${#REVERTED[@]} -gt 0 ]]; then
    echo "L-007 guard: reverted ${#REVERTED[@]} out-of-scope file(s): ${REVERTED[*]}"
fi
if [[ ${#LEFT[@]} -gt 0 ]]; then
    echo "L-007 guard: untracked out-of-scope file(s) left unstaged: ${LEFT[*]}"
fi
if [[ ${#REVERTED[@]} -eq 0 && ${#LEFT[@]} -eq 0 ]]; then
    echo "L-007 guard: clean (no out-of-scope drift)"
fi

echo "Stage B OK"
# === stage-b-scope (END) ===
```

### Stage B-commit — Auto-commit in-scope fixes

Commits Stage B's in-scope fixes as `chore(scope): pre-PR auto-fixes`, with the
active-plan footer (`aa-ma-footer.sh`) or `[ad-hoc]`. It stages only the
branch's own dirty files (`CHANGED_FILES`, from the state file) and lists any
other dirty file, leaving it alone. If the staged set then differs from that
list, it resets the index and exits 1 with `ABORT: Stage B-commit staged files
outside the intended list: …`. No dirty in-scope file → no-op.

```bash
# === stage-b-commit (BEGIN) ===
set -euo pipefail

# Stage state: load what earlier stages saved (SKILL.md "State between stages").
SDM_STATE="$(git rev-parse --absolute-git-dir)/sole-dev-merge.env"   # why: absolute, so a later cd can't break sdm_save
SDM_KEYS=" ORIGINAL_BRANCH BASE_REF DEFAULT_BRANCH SLUG SDM_DIR CHANGED_FILES CHANGED_PY CHANGED_SH REMOTE_CHOICE PR_BODY_FILE PR_NUM PR_URL MERGE_STRATEGY CI_STATE MERGE_DISPATCHED "
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

# Source the shared AA-MA footer helper. The aa-ma-commit-signature.sh
# PreToolUse hook validates the LITERAL `-m` argument, so we MUST emit
# the footer ourselves — the hook cannot append it retroactively.
# Single source-of-truth: claude-code/hooks/lib/aa-ma-footer.sh.
# footer-resolve:begin
# Resolve the footer helper: an explicit AA_MA_FOOTER_HELPER, then this repo's
# copy (aa-ma-forge), then the link install.sh puts under ~/.claude. Outside
# aa-ma-forge only the link exists. None found → an [ad-hoc] footer, said aloud.
_HELPER_PATH=""
for _cand in "${AA_MA_FOOTER_HELPER:-}" \
    "$(git rev-parse --show-toplevel)/claude-code/hooks/lib/aa-ma-footer.sh" \
    "${CLAUDE_HOME:-$HOME/.claude}/hooks/lib/aa-ma-footer.sh"; do
    if [[ -n "$_cand" && -f "$_cand" ]]; then _HELPER_PATH="$_cand"; break; fi
done
if [[ -n "$_HELPER_PATH" ]]; then
    # shellcheck source=/dev/null
    source "$_HELPER_PATH"
else
    echo "footer-resolve: aa-ma-footer.sh not found — using the [ad-hoc] footer"
    emit_aa_ma_footer() { printf '\n\n[ad-hoc]'; }
fi
# footer-resolve:end

# In scope = the branch's own files (CHANGED_FILES, saved by Stage B) that are dirty now.
# Never stage the whole tree: an operator's file outside that list stays out (L-007, L-048).
INTENDED=()
while IFS= read -r f; do
    if [[ -n "$f" && -n "$(git status --porcelain -- "$f")" ]]; then INTENDED+=("$f"); fi
done <<< "${CHANGED_FILES:-}"

if [[ ${#INTENDED[@]} -eq 0 ]]; then
    echo "Stage B-commit: nothing to commit (Stage B made no in-scope changes)"
    if [[ -n "$(git status --porcelain)" ]]; then
        echo "Stage B-commit: out-of-scope file(s) left as they are: $(git status --porcelain | cut -c4- | tr '\n' ' ')"
    fi
else
    git add -- "${INTENDED[@]}"
    WANTED=$(printf '%s\n' "${INTENDED[@]}" | sort)
    STAGED=$(git diff --cached --name-only | sort)
    if [[ "$STAGED" != "$WANTED" ]]; then
        git reset -q   # why: nothing half-staged survives the abort
        echo "ABORT: Stage B-commit staged files outside the intended list: $(comm -23 <(printf '%s\n' "$STAGED") <(printf '%s\n' "$WANTED") | tr '\n' ' ')"
        exit 1
    fi
    FOOTER=$(emit_aa_ma_footer)
    git commit -m "chore(scope): pre-PR auto-fixes${FOOTER}"
    echo "Stage B-commit: committed in-scope auto-fixes ($(git rev-parse --short HEAD))"
fi
# === stage-b-commit (END) ===
```

### Stage C — Code review + 3-source security pass

See [stage-c-review-and-security.md](references/stage-c-review-and-security.md#stage-c--code-review--3-source-security-pass) — the parallel code-reviewer and security-auditor dispatch, Ruff S and ShellCheck, and the findings aggregation.

### Stage D — Findings triage

See [stage-d-triage.md](references/stage-d-triage.md#stage-d--findings-triage) — how findings are routed by severity: the S602 auto-fix, user panels for HIGH/MEDIUM, LOW to reviewer notes.

**HIGH and MEDIUM findings go to the user (`AskUserQuestion`: Apply / Dispute / Defer) before Stage E starts.**

### Stage E — Remote detection, choice, auth, AI body generation

See [stage-e-remote-and-body.md](references/stage-e-remote-and-body.md#stage-e--remote-detection-choice-auth-ai-body-generation) — remote detection and choice, the auth check and the generated PR/MR body.

### Stage F — Push + PR/MR creation (idempotent)

See [stage-f-push.md](references/stage-f-push.md#stage-f--push--prmr-creation-idempotent) — the idempotent push and PR/MR creation.

### Stage G — CI poll + auto-merge + cleanup

See [stage-g-merge.md](references/stage-g-merge.md#stage-g--ci-poll--auto-merge--cleanup) — branch protection check, CI polling, the rebase merge and local cleanup.

---

## Exit-status contract

| Status            | Meaning                                              |
|-------------------|------------------------------------------------------|
| `STATUS: OK`      | Merged to main; branch deleted; main fast-forwarded (Stage G4). |
| `ABORT: …` (Stage A)   | Pre-flight failure: on-main, dirty tree, no remote, no commits ahead; exit non-zero. |
| `ABORT: Stage B-commit staged files outside the intended list: …` (Stage B-commit) | Something outside the branch's files was staged; the index is reset and nothing is committed; exit 1. |
| `ABORT: only github.com and gitlab.com remotes supported` (Stage E2) | Remote configuration unsupportable (zero github + zero gitlab remotes — semantically a pre-flight gate); exit non-zero. |
| `ABORT: Stage F requires non-empty body file …` (Stage F) | Stage E3 skipped or body file empty; exit non-zero. |
| `STATUS: AUTH_REQUIRED` | Auth failed (Stage E0); exit 0 + recovery hint.  |
| `STATUS: CI_TIMEOUT — see <URL>` | CI poll cap exceeded (Stage G2); exit 0 + remote-aware auto-merge recovery hint. |
| `STATUS: CI_FAILED — see <URL>` | Required check failed (Stage G2); exit 0 + remote-aware diagnostic. |
| `STATUS: CI_BLOCKED — pipeline status=<state> — see <URL>` | GitLab pipeline state is `manual` or `skipped` (Stage G2); exit 0 + diagnostic. No merge dispatched. |
| `STATUS: CI_UNKNOWN — CI_STATE='<state>' REMOTE_CHOICE='<remote>'` | Stage G2 produced an unknown CI_STATE (Stage G3 catchall); exit 0. No merge dispatched. |

Non-zero exits are reserved for **pre-flight-class aborts** (Stages A, B-commit, E2, F).
All runtime failures (auth, CI, merge race) exit cleanly with a `STATUS: …`
line so the workflow is safe to run unattended.

---

## Tests

Bats suite lives in `tests/commands/sole-dev-merge/`. CI runs them via
`.github/workflows/security.yml` (added in M5.6). See
`docs/adr/0008-sole-dev-merge-pr-workflow.md` for full test inventory.

---

_Stages A–G are placeholders. Logic lands across Steps 1.2 – 4.5 of the
[sole-dev-merge-pr-workflow](../../../.claude/dev/completed/sole-dev-merge-pr-workflow/sole-dev-merge-pr-workflow-plan.md) plan._
