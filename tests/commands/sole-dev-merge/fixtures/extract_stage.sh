#!/usr/bin/env bash
# extract_stage.sh — pull a named stage's bash from sole-dev-merge.md
#
# Usage:
#   extract_stage.sh <stage-marker> <command-md-path>
#
# Example:
#   extract_stage.sh stage-a-preflight claude-code/skills/sole-dev-merge/SKILL.md
#
# Looks for fenced markers:
#   # === <stage-marker> (BEGIN) ===
#   ...
#   # === <stage-marker> (END) ===
#
# Emits the bash between (exclusive of the markers themselves), prefixed
# with a shebang so the output is directly executable.
#
# A SKILL.md is read with its references/*.md: stages moved there when the
# skill was split (code-conventions-impact M5). A marker must occur exactly
# once across those files.
#
# Exit codes:
#   0 — extraction succeeded (non-empty body)
#   1 — markers not found, found more than once, OR body empty

set -euo pipefail

STAGE="${1:?usage: extract_stage.sh <stage-marker> <command-md-path>}"
FILE="${2:?usage: extract_stage.sh <stage-marker> <command-md-path>}"

BEGIN_MARK="=== ${STAGE} (BEGIN) ==="
END_MARK="=== ${STAGE} (END) ==="

# shellcheck source=tests/lib/skill_files.bash disable=SC1091  # why: path built from BASH_SOURCE; scanners without -x cannot follow it
. "$(dirname "${BASH_SOURCE[0]}")/../../../lib/skill_files.bash"
mapfile -t FILES < <(skill_files "$FILE")

# Fixed-string match via index() to avoid regex escaping pitfalls with ().
for mark in "$BEGIN_MARK" "$END_MARK"; do
    n=$(awk -v m="$mark" 'index($0, m) { n++ } END { print n + 0 }' "${FILES[@]}")
    if [[ "$n" -gt 1 ]]; then
        echo "extract_stage.sh: '$mark' found $n times in ${FILES[*]}" >&2
        exit 1
    fi
done
# FNR == 1: a BEGIN left open in one file never runs on into the next.
BODY=$(awk -v b="$BEGIN_MARK" -v e="$END_MARK" '
    FNR == 1 { inside = 0 }
    index($0, b) { inside = 1; next }
    index($0, e) { inside = 0; next }
    inside { print }
' "${FILES[@]}")

if [[ -z "$BODY" ]]; then
    echo "extract_stage.sh: no body found for marker '$STAGE' in $FILE" >&2
    exit 1
fi

printf '#!/usr/bin/env bash\n%s\n' "$BODY"
