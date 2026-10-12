#!/usr/bin/env bash
# Event: PreToolUse(Bash)
# Mode: Blocking — exit 2 refuses a commit that adds a flagged pattern
# Exit: 0 allow · 2 block (policy) · 1 infra error (helper/jq missing, bad stdin; non-blocking, the commit proceeds)
# Fail-open: kill switch, bypass marker, not a repo, no staged .py pass with exit 0; infra errors exit 1 with a stderr line; no ruff, or ruff erroring on a file → a systemMessage + hooks.log line, the regex classes still run
#
# PreToolUse(Bash) hook — block commits that introduce mechanical security
# anti-patterns in Python files. Symmetric to aa-ma-commit-signature.sh but
# inspects the staged diff: Ruff S rules on each staged blob, plus two regex classes.
#
# Fires via Claude Code's PreToolUse event with matcher="Bash". Reads a JSON
# object from stdin of shape {tool_name: "Bash", tool_input: {command: "..."}}.
#
# Decision tree:
#   1. AA_MA_HOOKS_DISABLE=1                          -> exit 0 (kill switch)
#   2. stdin JSON malformed                            -> exit 1 (hook infra error)
#   3. command is not 'git commit ...'                 -> exit 0
#   4. editor-form commit (no -m/-F/--message/--file)  -> exit 0 (no msg to inspect)
#   5. command contains [security-bypass: <reason>]    -> exit 0 (auditable bypass)
#   6. not inside a git repo                           -> exit 0 (graceful skip)
#   7. no staged *.py files (Added/Modified)           -> exit 0
#   8. Ruff S + 2 regex classes on ADDED lines         -> if any -> exit 2
#   9. otherwise                                       -> exit 0
#
# Detection scope (Python files, ADDED lines in staged diff, any repo):
#   - Ruff S102,S301,S307,S602,S604,S608 on the STAGED blob (`git show :<file>`), forge-pinned
#     ruff with --isolated, so the repo's own config cannot switch them off. Only
#     INTRODUCED findings block: one whose innermost enclosing Python statement (ast) holds
#     an added line — so changed arguments inside an unchanged multi-line call count.
#     Fails closed: no python, a file ast cannot parse, or a lone CR (git and ast would
#     number lines differently) make every finding count; ruff erroring on a file blocks.
#     All of it goes through private temp files, never argv (no size limit to slip past).
#     Covers shell=True calls, the dynamic-code builtins, SQL string building and unsafe
#     binary deserialisation (D12; S102 keeps exec() covered).
#     --ignore-noqa: an in-file `# noqa` / `# ruff: noqa` is repo-controlled, so it cannot
#     suppress this check; the [security-bypass: <reason>] marker is the auditable escape.
#   - Hardcoded secrets (regex): api_key|token|password|secret = "literal_8+_chars"
#     Whitelist: placeholders (your-*, <KEY>, xxx*) and env-var reads
#   - Path traversal (regex): open() / Path() containing relative-up components
#
# Bypass:
#   - AA_MA_HOOKS_DISABLE=1 (master kill switch)
#   - [security-bypass: <reason>] on its own line in commit message (reason required)
#
# Always emits findings to stderr; exit 2 blocks; exit 0 passes.
#

set -euo pipefail

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

stdin_json=$(cat)
cmd=$(printf '%s' "$stdin_json" | jq -er '.tool_input.command // empty' 2>/dev/null) || {
    printf 'security-static-check: failed to parse stdin JSON\n' >&2
    exit 1
}

[ -z "$cmd" ] && exit 0

aa_ma_debug_cmd "security-static-check: examining command" "$cmd"

# -----------------------------------------------------------------------------
# 3. Word-boundary match on 'git commit'.
# -----------------------------------------------------------------------------
if ! printf '%s' "$cmd" | grep -Eq 'git commit([[:space:]]|$)'; then
    exit 0
fi

# -----------------------------------------------------------------------------
# 4. Editor-form detection. Editor form means we cannot see the message yet
#    AND there is no way to inspect a bypass marker. We pass through.
# -----------------------------------------------------------------------------
if ! printf '%s' "$cmd" | grep -Eq '([[:space:]]|^)(-m|-F|-c|-C|--message|--file|--reedit-message|--reuse-message)([[:space:]]|=|$)'; then
    aa_ma_debug "security-static-check: editor-form commit, passing through"
    exit 0
fi

# -----------------------------------------------------------------------------
# 5. [security-bypass: <reason>] marker.
#    Must be on its own line AND must include a non-empty reason.
# -----------------------------------------------------------------------------
normalized_cmd=$(printf '%s' "$cmd" | sed 's/\\n/\n/g')
if printf '%s\n' "$normalized_cmd" | grep -Eq '^[[:space:]]*\[security-bypass:[[:space:]]+[^]]+\][[:space:]"'"'"'\`]*$'; then
    aa_ma_debug "security-static-check: [security-bypass: ...] marker found, passing through"
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
# 7. Find staged Python files (Added or Modified).
# -----------------------------------------------------------------------------
# AMRC: a renamed or copied file with new lines is scanned too (its new name).
# why: not a repo or no index is handled above; an empty list means nothing to scan
py_files=$(git diff --cached --name-only --diff-filter=AMRC 2>/dev/null | grep -E '\.py$' || true)
if [ -z "$py_files" ]; then
    aa_ma_debug "security-static-check: no staged *.py files"
    exit 0
fi

# -----------------------------------------------------------------------------
# 8. Scan added lines for pattern classes.
# -----------------------------------------------------------------------------

# ruff comes ONLY from this forge's .venv or an absolute PATH entry — never from the repo being
# committed to, which may ship its own .venv/bin/ruff (the rule ruff-format.sh follows).
# ponytail: resolution duplicated from ruff-format.sh; move it to lib/ if a third hook needs it.
# why: no `readlink -f` (macOS < 12.3) → the path as invoked
REAL="$(readlink -f "${BASH_SOURCE[0]}" 2>/dev/null)" || REAL="${BASH_SOURCE[0]}"
REAL_DIR="${REAL%/*}"
FORGE="${REAL_DIR%/*/*}"
ruff=""
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
        *) printf 'security rule' ;;
    esac
}

# python scopes each finding to its statement; resolved like ruff (forge .venv, or absolute PATH).
py=""
if [ -x "${FORGE}/.venv/bin/python" ]; then
    py="${FORGE}/.venv/bin/python"
else
    py=$(command -v python3) || py=""
    [[ "$py" == /* ]] || py=""
fi
# argv: blob, ruff JSON, added-lines file. Prints row<TAB>rule<TAB>message per introduced finding.
# No single quotes inside: this is a single-quoted shell string.
SCOPE_PY='
import ast, json, sys
src = open(sys.argv[1], "rb").read()
added = {int(n) for n in open(sys.argv[3]).read().split()}
tree = None
if b"\r" not in src.replace(b"\r\n", b""):
    try:
        tree = ast.parse(src)
    except (SyntaxError, ValueError):
        tree = None
spans = [(n.lineno, n.end_lineno) for n in ast.walk(tree) if isinstance(n, ast.stmt)] if tree else []
for f in json.load(open(sys.argv[2])):
    if not f.get("code"):
        continue
    row = f["location"]["row"]
    lo, hi = row, f["end_location"]["row"]
    if tree is not None:
        inside = [sp for sp in spans if sp[0] <= lo and hi <= sp[1]]
        if inside:
            lo, hi = min(inside, key=lambda sp: sp[1] - sp[0])
        if not any(lo <= n <= hi for n in added):
            continue
    print("%s\t%s\t%s" % (row, f["code"], " ".join(f["message"].split())))
'
# Fail closed: exit 1/127 here would be a non-blocking error, i.e. the commit goes through.
work=$(mktemp -d) || {
    printf 'security-static-check: mktemp failed; refusing to pass an unscanned commit (exit 2)\n' >&2
    printf 'Emergency bypass: export AA_MA_HOOKS_DISABLE=1\n' >&2
    exit 2
}
trap 'rm -rf "$work"' EXIT

findings=()

while IFS= read -r file; do
    [ -z "$file" ] && continue
    diff_content=$(git diff --cached -U0 -- "$file" 2>/dev/null || true)
    [ -z "$diff_content" ] && continue

    : > "$work/added"
    line_num=0
    while IFS= read -r line; do
        # Hunk header: reset line counter to NEW-file line start
        if [[ "$line" =~ ^@@[[:space:]]\-[0-9]+(,[0-9]+)?[[:space:]]\+([0-9]+)(,[0-9]+)?[[:space:]]@@ ]]; then
            line_num="${BASH_REMATCH[2]}"
            continue
        fi
        # File header lines
        [[ "$line" == "+++"* ]] && continue
        [[ "$line" == "---"* ]] && continue
        # Only inspect ADDED lines (start with single +)
        [[ "$line" == "+"* ]] || continue

        content="${line:1}"
        printf '%s\n' "$line_num" >> "$work/added"

        # -- 1. Hardcoded secrets --------------------------------------------
        # Lowercase the content for case-insensitive identifier matching
        content_lc=$(printf '%s' "$content" | tr '[:upper:]' '[:lower:]')
        if [[ "$content_lc" =~ (api[_-]?key|apikey|token|password|secret)[[:space:]]*=[[:space:]]*[\"\'][^\"\']{8,}[\"\'] ]]; then
            # Whitelist common placeholders / env reads (check original content
            # for placeholder forms that include casing like <KEY> or os.environ)
            if [[ ! "$content" =~ (your-|\<[A-Z_]+\>|xxxx|os\.environ|os\.getenv|\$\{[A-Z_]+\}|\$[A-Z_]+) ]]; then
                findings+=("${file}:${line_num}: hardcoded secret/key/password literal")
            fi
        fi

        # -- 3. Path traversal -----------------------------------------------
        if [[ "$content" =~ (open|Path)[[:space:]]*\([^\)]*\.\.\/ ]]; then
            findings+=("${file}:${line_num}: path traversal (relative-up component)")
        fi

        line_num=$((line_num + 1))
    done <<< "$diff_content"

    [ -n "$ruff" ] || continue
    git show ":${file}" > "$work/blob"
    # why: stderr dropped — rc 1 means findings; rc 2+ (ruff failing) blocks below, fail closed
    "$ruff" 2>/dev/null check --isolated --ignore-noqa --select "$RUFF_RULES" --output-format json \
        --stdin-filename "$file" - < "$work/blob" > "$work/ruff.json" && rc=0 || rc=$?
    if [ "$rc" -gt 1 ]; then
        findings+=("${file}: ruff could not check this file (rc ${rc}); fix it or use the bypass marker")
        continue
    fi
    rows=""
    if [ -n "$py" ]; then
        # why: stderr dropped — a failed scoping falls back to counting every finding below
        rows=$("$py" 2>/dev/null -I -c "$SCOPE_PY" "$work/blob" "$work/ruff.json" "$work/added") || py_failed=1
    fi
    if [ -z "$py" ] || [ "${py_failed:-0}" = 1 ]; then
        py_failed=0
        # why: stderr dropped — unreadable output becomes a blocking finding just below
        rows=$(jq 2>/dev/null -r '.[] | select(.code != null)
            | [.location.row, .code, (.message | gsub("\\s+"; " "))] | @tsv' "$work/ruff.json") || {
            findings+=("${file}: ruff output unreadable; fix it or use the bypass marker")
            continue
        }
    fi
    while IFS=$'\t' read -r row code msg; do
        [ -n "${code:-}" ] || continue
        findings+=("${file}:${row}: $(ruff_label "$code") [${code}] ${msg}")
    done <<< "$rows"
done <<< "$py_files"

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
