#!/usr/bin/env bash
# Event: PreToolUse(Bash)
# Mode: Blocking — exit 2 refuses a commit touching a .py file with a flagged pattern
#       (Ruff: anywhere in the file; regexes: on the lines it adds)
# Exit: 0 allow · 2 block (policy) · 1 infra error (helper/jq missing, bad stdin; non-blocking, the commit proceeds)
# Fail-open: kill switch, bypass marker (logged to hooks.log), not a repo, no staged or modified .py pass with exit 0; infra errors exit 1 with a stderr line; no ruff → a systemMessage + hooks.log line and the regex classes still run. Fails closed (exit 2): ruff or git erroring on a file, unreadable ruff output, a binary .py diff, a file listing that cannot run, an unresolvable git -C / --git-dir / --work-tree
#
# PreToolUse(Bash) hook — block commits that introduce mechanical security
# anti-patterns in Python files. Symmetric to aa-ma-commit-signature.sh but
# inspects every .py the commit can contain (staged, or modified for -a / a pathspec):
# Ruff S rules on each whole file, plus two regex classes on added lines.
#
# Fires via Claude Code's PreToolUse event with matcher="Bash". Reads a JSON
# object from stdin of shape {tool_name: "Bash", tool_input: {command: "..."}}.
#
# Decision tree:
#   0. stdin holds no 'commit' at all                  -> exit 0 before any fork (hot path)
#   1. AA_MA_HOOKS_DISABLE=1                          -> exit 0 (kill switch)
#   2. stdin JSON malformed                            -> exit 1 (hook infra error)
#   3. not `git [-c k=v | -C dir | --opt]... commit`  -> exit 0; -C <plain path> is
#      entered, an unresolvable -C / --git-dir / --work-tree -> exit 2
#   4. (none: a commit with no message flag is scanned too; it just cannot carry a marker)
#   5. command contains [security-bypass: <reason>]    -> exit 0 (auditable bypass)
#   6. not inside a git repo                           -> exit 0 (graceful skip)
#   7. no .py staged or modified (A/M/R/C), NUL-listed -> exit 0
#   8. Ruff S on each whole file (index + working tree) + 2 regexes on added lines -> exit 2 if any
#   9. otherwise                                       -> exit 0
#
# Detection scope (staged Python files, any repo):
#   - Ruff rules RUFF_RULES (below) on the WHOLE staged blob (`git show :<file>`): a touched
#     file complies in full (D8). Whole-file on purpose: three review rounds found bypasses in
#     every "only lines this commit added" filter (git, Ruff and ast number lines differently),
#     so none is attempted. Forge-pinned ruff, --isolated (the repo's config cannot switch the
#     rules off) and --ignore-noqa (nor can an in-file `# noqa` / `# ruff: noqa`); a pre-existing
#     site in a touched file needs the auditable [security-bypass: <reason>] marker.
#     Covers shell=True calls, the dynamic-code builtins, SQL string building and unsafe
#     binary deserialisation (D12; S102 keeps exec() covered).
#   - Hardcoded secrets (regex, ADDED lines): api_key|token|password|secret = "literal_8+_chars"
#     Whitelist: placeholders (your-*, <KEY>, xxx*) and env-var reads
#   - Path traversal (regex, ADDED lines): open() / Path() containing relative-up components
#
# Bypass:
#   - AA_MA_HOOKS_DISABLE=1 (master kill switch)
#   - [security-bypass: <reason>] on its own line in commit message (reason required)
#
# Always emits findings to stderr; exit 2 blocks; exit 0 passes.
#

set -euo pipefail

# Hot path: this runs on EVERY Bash call. Read stdin once and leave before sourcing the
# helper, jq or any fork unless the payload could hold a commit (step 3 needs 'git commit').
stdin_json=$(cat)
[[ "$stdin_json" == *commit* ]] || exit 0

# Resolve helper across two layouts (project / installed).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "${SCRIPT_DIR}/lib/aa-ma-parse.sh" ]; then
    HELPER="${SCRIPT_DIR}/lib/aa-ma-parse.sh"
elif [ -f "${SCRIPT_DIR}/aa-ma-parse.sh" ]; then
    HELPER="${SCRIPT_DIR}/aa-ma-parse.sh"
else
    printf 'security-static-check: cannot find aa-ma-parse.sh helper (looked in %s/lib and %s)\n' \
        "$SCRIPT_DIR" "$SCRIPT_DIR" >&2
    exit 1
fi
# shellcheck source=lib/aa-ma-parse.sh
# shellcheck disable=SC1090,SC1091
. "$HELPER"

# -----------------------------------------------------------------------------
# 1. Kill switch.
# -----------------------------------------------------------------------------
if aa_ma_is_disabled; then
    aa_ma_debug "security-static-check: AA_MA_HOOKS_DISABLE=1, passing through"
    exit 0
fi

# -----------------------------------------------------------------------------
# 2. Parse stdin JSON.
# -----------------------------------------------------------------------------
if ! command -v jq >/dev/null 2>&1; then
    printf 'security-static-check: jq not found in PATH\n' >&2
    exit 1
fi

cmd=$(printf '%s' "$stdin_json" | jq -er '.tool_input.command // empty' 2>/dev/null) || {
    printf 'security-static-check: failed to parse stdin JSON\n' >&2
    exit 1
}

[ -z "$cmd" ] && exit 0

aa_ma_debug_cmd "security-static-check: examining command" "$cmd"

# -----------------------------------------------------------------------------
# 3. `git [-c k=v | -C <dir> | --opt[=v]]... commit`, word-bounded (not commit-tree).
# -----------------------------------------------------------------------------
GIT_COMMIT_RE='(^|[;&|(`[:space:]])git(([[:space:]]+-[cC][[:space:]]+[^[:space:]]+)|([[:space:]]+--[a-z][a-z-]*(=[^[:space:]]*)?))*[[:space:]]+commit([[:space:]]|$)'
if ! [[ "$cmd" =~ $GIT_COMMIT_RE ]]; then
    exit 0
fi
git_prefix="${BASH_REMATCH[0]}"

# Global options that move the repository: scan the repo the commit lands in, or refuse.
if [[ "$git_prefix" == *--git-dir* || "$git_prefix" == *--work-tree* ]]; then
    printf 'security-static-check: --git-dir/--work-tree commits cannot be scanned; run git commit from the repository (exit 2)\n' >&2
    exit 2
fi
if [[ "$git_prefix" =~ [[:space:]]-C[[:space:]]+([^[:space:]]+) ]]; then
    c_dir="${BASH_REMATCH[1]}"
    # A quoted, expanded or home-relative path is not the path the shell will use.
    if [[ "$c_dir" == *[\"\'\$\`~\\]* ]] || ! cd -- "$c_dir" 2>/dev/null; then  # why: a failed cd is the refusal below
        printf 'security-static-check: cannot resolve git -C %s to scan it; use a plain path (exit 2)\n' "$c_dir" >&2
        exit 2
    fi
fi

# 4. (removed) A commit with no message flag (`--no-edit`, `--amend`, editor form) is scanned
#    like any other: it simply cannot carry the bypass marker.

# -----------------------------------------------------------------------------
# 5. [security-bypass: <reason>] marker.
#    Must be on its own line AND must include a non-empty reason.
# -----------------------------------------------------------------------------
normalized_cmd=$(printf '%s' "$cmd" | sed 's/\\n/\n/g')
if bypass_line=$(printf '%s\n' "$normalized_cmd" | grep -Em1 '^[[:space:]]*\[security-bypass:[[:space:]]+[^]]+\][[:space:]"'"'"'\`]*$'); then
    # The marker is honoured wherever it sits in the command, so it is logged here too:
    # an audit trail that does not depend on it reaching the commit message.
    log_warn "security-static-check" "bypass marker used: ${bypass_line}"
    exit 0
fi

# -----------------------------------------------------------------------------
# 6. Must be inside a git repo to scan a staged diff.
# -----------------------------------------------------------------------------
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    aa_ma_debug "security-static-check: not inside a git repo, skipping"
    exit 0
fi

# -----------------------------------------------------------------------------
# 7. Python files this commit can contain: staged (AMRC) plus modified-but-unstaged tracked
#    files, which `-a` and a pathspec commit. No flag parsing decides what is scanned.
# -----------------------------------------------------------------------------
# The listing below runs in a process substitution, whose failure would read as "no files":
# check the commands it needs first, and fail closed.
# why: stdout/stderr dropped — only the status matters; a failure is reported on the next line
if ! command -v sort >/dev/null 2>&1 || ! git diff --cached --name-only -z >/dev/null 2>&1 || ! git diff --name-only -z >/dev/null 2>&1; then
    printf 'security-static-check: cannot list the files this commit contains (git or sort failed); refusing (exit 2)\n' >&2
    exit 2
fi
py_files=()
# why: stderr dropped — the same commands just succeeded above
while IFS= read -r -d '' f; do
    [[ "$f" == *.py ]] && py_files+=("$f")
done < <({ git -c core.quotePath=false diff --cached --name-only -z --diff-filter=AMRC 2>/dev/null  # why: checked above
           git -c core.quotePath=false diff --name-only -z --diff-filter=AMRC 2>/dev/null; } | sort -zu)  # why: checked above
if [ "${#py_files[@]}" -eq 0 ]; then
    aa_ma_debug "security-static-check: no staged or modified *.py files"
    exit 0
fi

# -----------------------------------------------------------------------------
# 8. Ruff S on each whole file (index and working tree); two regex classes on added lines.
# -----------------------------------------------------------------------------

# ruff comes ONLY from this forge's .venv or an absolute PATH entry — never from the repo being
# committed to, which may ship its own .venv/bin/ruff (the rule ruff-format.sh follows).
# ponytail: resolution duplicated from ruff-format.sh; move it to lib/ if a third hook needs it.
# why: no `readlink -f` (macOS < 12.3) → the path as invoked
REAL="$(readlink -f "${BASH_SOURCE[0]}" 2>/dev/null)" || REAL="${BASH_SOURCE[0]}"
REAL_DIR="${REAL%/*}"
FORGE="${REAL_DIR%/*/*}"
if [ -x "${FORGE}/.venv/bin/ruff" ]; then
    ruff="${FORGE}/.venv/bin/ruff"
else
    ruff=$(command -v ruff) || ruff=""
    [[ "$ruff" == /* ]] || ruff=""
fi
if [ -z "$ruff" ]; then
    fail_open_notice "security-static-check" "ruff not found (forge .venv or an absolute PATH entry); shell, dynamic-code, SQL and deserialisation checks skipped"
fi

RUFF_RULES="S102,S301,S307,S602,S604,S608"
# A case, not `declare -A`: macOS /bin/bash 3.2 has no associative arrays.
ruff_label() {
    case "$1" in
        S102|S307) printf 'dynamic code execution' ;;
        S602|S604) printf 'shell injection' ;;
        S608) printf 'SQL string construction' ;;
        S301) printf 'unsafe binary deserialisation (CWE-502)' ;;
        invalid-syntax) printf 'unparsable Python (cannot be scanned)' ;;
        *) printf 'security rule' ;;
    esac
}

findings=()

# ruff_scan <file> <content> — append a finding per Ruff S hit in <content>, or one blocking
# finding when ruff cannot check it. Content goes by here-string: no argv size limit.
ruff_scan() {
    local out rc=0 rows row code msg
    # why: stderr dropped — rc 1 means findings; rc 2+ blocks below
    out=$("$ruff" 2>/dev/null check --isolated --ignore-noqa --select "$RUFF_RULES" \
        --output-format json --stdin-filename "$1" - <<< "$2") || rc=$?
    # why: jq's parse error becomes the blocking finding below
    if [ "$rc" -gt 1 ] || ! rows=$(jq 2>/dev/null -r '.[] | select(.code != null)
            | [.location.row, .code, (.message | gsub("\\s+"; " "))] | @tsv' <<< "$out"); then
        findings+=("${1}: ruff could not check this file (rc ${rc}); fix it or use the bypass marker")
        return 0
    fi
    while IFS=$'\t' read -r row code msg; do
        [ -n "${code:-}" ] || continue
        findings+=("${1}:${row}: $(ruff_label "$code") [${code}] ${msg}")
    done <<< "$rows"
}

for file in "${py_files[@]}"; do

    # -- Ruff S, whole file (D8): the index blob, and the working tree where it differs ------
    if [ -n "$ruff" ]; then
        # why: stderr dropped — no index entry (an unstaged-only change) is normal
        if git cat-file -e ":${file}" 2>/dev/null; then
            if blob=$(git show ":${file}" 2>/dev/null); then  # why: a failure is the finding below
                ruff_scan "$file" "$blob"
            else
                findings+=("${file}: git show failed; refusing to pass it unscanned")
            fi
        fi
        # why: rc 1 = the working tree differs from the index (what `-a` / a pathspec commits)
        if [ -f "$file" ] && ! git diff --quiet -- "$file" 2>/dev/null; then
            ruff_scan "$file" "$(cat -- "$file")"
        fi
    fi

    # -- Regex classes, added lines --------------------------------------------
    # Plain diff whatever the repo's config says: color, an external diff or a textconv
    # driver would change the text this parser reads.
    # why: stderr dropped — a failing git diff becomes a blocking finding (fail closed)
    if ! diff_content=$(git diff --cached --no-color --no-ext-diff --no-textconv -U0 -- "$file" 2>/dev/null &&
                       git diff --no-color --no-ext-diff --no-textconv -U0 -- "$file" 2>/dev/null); then  # why: as above
        findings+=("${file}: git diff failed; refusing to pass it unscanned")
        continue
    fi
    [ -z "$diff_content" ] && continue

    in_hunk=0
    line_num=0
    while IFS= read -r line; do
        # Hunk header: reset line counter to NEW-file line start
        if [[ "$line" =~ ^@@[[:space:]]\-[0-9]+(,[0-9]+)?[[:space:]]\+([0-9]+)(,[0-9]+)?[[:space:]]@@ ]]; then
            line_num="${BASH_REMATCH[2]}"
            in_hunk=1
            continue
        fi
        # File headers exist only before the first hunk; inside one, `+++x` is an added `++x`.
        [ "$in_hunk" = 1 ] || continue
        # Only inspect ADDED lines (start with single +)
        [[ "$line" == "+"* ]] || continue

        content="${line:1}"

        # -- 1. Hardcoded secrets --------------------------------------------
        # nocasematch, not a `tr` per line: a fork per added line made a 2000-line commit
        # outlast the 10 s hook timeout, and a timeout lets the commit through (bash 3.2 has it).
        shopt -s nocasematch
        secret_hit=0
        [[ "$content" =~ (api[_-]?key|apikey|token|password|secret)[[:space:]]*=[[:space:]]*[\"\'][^\"\']{8,}[\"\'] ]] && secret_hit=1
        shopt -u nocasematch   # the whitelist below is case-sensitive (<KEY>, $ENV)
        if [ "$secret_hit" = 1 ]; then
            # Whitelist common placeholders / env reads (check original content
            # for placeholder forms that include casing like <KEY> or os.environ)
            if [[ ! "$content" =~ (your-|\<[A-Z_]+\>|xxxx|os\.environ|os\.getenv|\$\{[A-Z_]+\}|\$[A-Z_]+) ]]; then
                findings+=("${file}:${line_num}: hardcoded secret/key/password literal")
            fi
        fi

        # -- 2. Path traversal -----------------------------------------------
        if [[ "$content" =~ (open|Path)[[:space:]]*\([^\)]*\.\.\/ ]]; then
            findings+=("${file}:${line_num}: path traversal (relative-up component)")
        fi

        line_num=$((line_num + 1))
    done <<< "$diff_content"
    # No hunk is normal for an empty file, a mode change or a pure rename (no added lines).
    # A binary diff hides its lines from the regexes, so it is refused.
    if [ "$in_hunk" = 0 ] && [[ "$diff_content" == *"Binary files "* ]]; then
        findings+=("${file}: binary diff; refusing to pass it unscanned")
    fi
done

# -----------------------------------------------------------------------------
# 9. Verdict.
# -----------------------------------------------------------------------------
if [ "${#findings[@]}" -gt 0 ]; then
    {
        printf '\n'
        printf 'security-static-check: %d issue(s) found in staged diff\n\n' "${#findings[@]}"
        for f in "${findings[@]}"; do
            printf '  %s\n' "$f"
        done
        printf '\n'
        printf 'Mechanical security check. If a finding is a false positive\n'
        printf '(e.g., test fixture, intentional pattern), append to commit message:\n\n'
        printf '  [security-bypass: <reason>]\n\n'
        printf 'Reason must be non-empty and on its own line.\n\n'
        printf 'Emergency bypass: export AA_MA_HOOKS_DISABLE=1\n'
    } >&2
    exit 2
fi

aa_ma_debug "security-static-check: no findings"
exit 0
