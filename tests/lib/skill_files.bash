# shellcheck shell=bash
# skill_files <path> — print <path>, then its sibling references/*.md when <path> is a
# SKILL.md, one per line. A skill split into SKILL.md + references/ (code-conventions-
# impact M5) is one document: a check that reads SKILL.md alone stops covering every line
# that moved (L-047). Bash twin of tests/skills/_helpers.py:skill_files.
skill_files() {
    local path="$1" ref
    printf '%s\n' "$path"
    [[ "$(basename "$path")" == SKILL.md ]] || return 0
    for ref in "$(dirname "$path")"/references/*.md; do
        if [[ -f "$ref" ]]; then printf '%s\n' "$ref"; fi
    done
}
