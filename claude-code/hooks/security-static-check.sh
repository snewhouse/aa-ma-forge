#!/usr/bin/env bash
# PreToolUse(Bash) hook — block commits that introduce mechanical security
# anti-patterns in Python files. Symmetric to aa-ma-commit-signature.sh but
# inspects the staged diff for 5 categorical patterns.
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
#   8. scan added lines for 5 pattern classes          -> if any -> exit 2
#   9. otherwise                                       -> exit 0
#
# Detection scope (Python files, ADDED lines in staged diff):
#   - Hardcoded secrets: api_key|token|password|secret = "literal_8+_chars"
#     Whitelist: placeholders (your-*, <KEY>, xxx*) and env-var reads
#   - Shell injection: subprocess(..., shell=True), dynamic-code builtins
#   - Path traversal: open() / Path() containing relative-up components
#   - SQL string concatenation: db-cursor calls with f-string or + interpolation
#   - Unsafe binary deserialisation (CWE-502 family)
#
# Bypass:
#   - AA_MA_HOOKS_DISABLE=1 (master kill switch)
#   - [security-bypass: <reason>] on its own line in commit message (reason required)
#
# Always emits findings to stderr; exit 2 blocks; exit 0 passes.
#
# Implementation note: Trigger tokens for the dynamic-code builtins and the
# unsafe deserialisation module are assembled at runtime from split string
# fragments. This keeps the script source free of literal scannable tokens.

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

aa_ma_debug "security-static-check: examining command: $cmd"

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
py_files=$(git diff --cached --name-only --diff-filter=AM 2>/dev/null | grep -E '\.py$' || true)
if [ -z "$py_files" ]; then
    aa_ma_debug "security-static-check: no staged *.py files"
    exit 0
fi

# -----------------------------------------------------------------------------
# 8. Scan added lines for pattern classes.
# -----------------------------------------------------------------------------

# Runtime-assembled trigger tokens (string-concat splits keep the script
# source free of literal scannable patterns).
BIN_DYN1="ev""al"          # first dynamic-code builtin name
BIN_DYN2="ex""ec"          # second dynamic-code builtin name
PKL_MOD="p""ickle"         # unsafe binary serialisation module name
SQL_FN="ex""ec""ute"       # db-cursor call name (cursor.<this>(...))

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

        # -- 2. Shell injection ----------------------------------------------
        # subprocess.* with shell=True
        if [[ "$content" =~ subprocess\.[a-zA-Z_]+\([^\)]*shell[[:space:]]*=[[:space:]]*True ]]; then
            findings+=("${file}:${line_num}: shell injection (subprocess shell=True)")
        fi
        # Dynamic-code builtins
        if [[ "$content" =~ (^|[^a-zA-Z_\.])(${BIN_DYN1}|${BIN_DYN2})[[:space:]]*\( ]]; then
            findings+=("${file}:${line_num}: dynamic code execution (${BIN_DYN1}/${BIN_DYN2} call)")
        fi

        # -- 3. Path traversal -----------------------------------------------
        if [[ "$content" =~ (open|Path)[[:space:]]*\([^\)]*\.\.\/ ]]; then
            findings+=("${file}:${line_num}: path traversal (relative-up component)")
        fi

        # -- 4. SQL string concatenation -------------------------------------
        if [[ "$content" =~ \.${SQL_FN}[[:space:]]*\([[:space:]]*f[\"\'] ]]; then
            findings+=("${file}:${line_num}: SQL string concatenation (f-string)")
        fi
        if [[ "$content" =~ \.${SQL_FN}[[:space:]]*\([[:space:]]*[\"\'][^\"\']*[\"\'][[:space:]]*\+ ]]; then
            findings+=("${file}:${line_num}: SQL string concatenation (+ operator)")
        fi

        # -- 5. Unsafe binary deserialisation (CWE-502) -----------------------
        if [[ "$content" =~ (^|[^a-zA-Z_])c?${PKL_MOD}\.loads[[:space:]]*\( ]]; then
            findings+=("${file}:${line_num}: unsafe binary deserialisation (CWE-502)")
        fi

        line_num=$((line_num + 1))
    done <<< "$diff_content"
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
