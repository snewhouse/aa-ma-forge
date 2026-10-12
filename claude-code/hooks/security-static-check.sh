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
#     ruff with --isolated, so the repo's own config cannot switch them off; findings on
#     only INTRODUCED findings block: a rule + line-text pair the staged blob has more of
#     than HEAD's blob (a new file, or a renamed one, has no HEAD blob: all count). Line
#     numbers are not used, so an added `shell=True` inside an unchanged multi-line call
#     is caught. Covers shell=True calls, the dynamic-code builtins, SQL string building
#     and unsafe binary deserialisation (D12; S102 keeps exec() covered).
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

# ruff_keys <source> — one TSV row per Ruff finding: row, rule, trimmed text of that line, message.
# Exit 1 when ruff errors (rc 2+) or its JSON cannot be read: never an empty "clean" answer.
ruff_keys() {
    local out rc=0
    # why: stderr dropped — a failure is reported by the caller's notice
    out=$("$ruff" 2>/dev/null check --isolated --ignore-noqa --select "$RUFF_RULES" \
        --output-format json --stdin-filename "$file" - <<< "$1") || rc=$?
    [ "$rc" -le 1 ] || return 1
    # why: jq's parse error becomes the caller's notice
    jq 2>/dev/null -r --arg src "$1" '($src | split("\n")) as $lines | .[] | select(.code != null)
        | [.location.row, .code, ($lines[.location.row - 1] // "" | gsub("^\\s+|\\s+$"; "") | gsub("\t"; " ")),
           (.message | gsub("[\t\n]"; " "))] | @tsv' <<< "$out"
}

findings=()

while IFS= read -r file; do
    [ -z "$file" ] && continue
    diff_content=$(git diff --cached -U0 -- "$file" 2>/dev/null || true)
    [ -z "$diff_content" ] && continue

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
    # why: rc 1 means findings, which the loop below reads; rc 2+ is ruff failing, reported as a notice
    # Staged findings not matched by one of HEAD's (same rule, same line text) are introduced.
    # shellcheck disable=SC2310  # why: ruff_keys answers by explicit return codes; set -e is not relied on inside it
    new_keys=$(ruff_keys "$(git show ":${file}")") || {
        fail_open_notice "security-static-check" "ruff failed on ${file}; its Ruff S checks were skipped"
        continue
    }
    old_keys=$'\n'
    # why: no HEAD blob (new or renamed file) means nothing pre-existed
    if git cat-file -e "HEAD:${file}" 2>/dev/null; then
        # shellcheck disable=SC2310  # why: ruff_keys answers by explicit return codes; set -e is not relied on inside it
        old_rows=$(ruff_keys "$(git show "HEAD:${file}")") || {
            fail_open_notice "security-static-check" "ruff failed on HEAD:${file}; its Ruff S checks were skipped"
            continue
        }
        old_keys+=$(cut -f2,3 <<< "$old_rows")$'\n'   # rule<TAB>text, the lookup key
    fi
    while IFS=$'\t' read -r row code text msg; do
        [ -n "${code:-}" ] || continue
        key="${code}"$'\t'"${text}"
        if [[ "$old_keys" == *$'\n'"$key"$'\n'* ]]; then
            old_keys="${old_keys/$'\n'"$key"$'\n'/$'\n'}"   # consume one pre-existing match
            continue
        fi
        findings+=("${file}:${row}: $(ruff_label "$code") [${code}] ${msg}")
    done <<< "$new_keys"
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
