#!/usr/bin/env bash
# SessionStart hook: surface the most-recently-touched active AA-MA task.
#
# Behaviour:
#   - Scans project-local `.claude/dev/active/` first, then $HOME/.claude/dev/active/
#   - Picks the task whose `*-tasks.md` has the newest mtime (ties → alphabetical)
#   - Emits a single hidden-context line describing the top task + its absolute path
#   - Appends "(N other active tasks: a, b, c [and M more])" when there are 2+ active tasks
#
# Honours AA_MA_HOOKS_DISABLE=1 (master kill switch).
# Always exits 0 — never blocks session start.

set -euo pipefail

# Resolve helper across two layouts (project subdir OR installed sibling).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "${SCRIPT_DIR}/lib/aa-ma-parse.sh" ]; then
    HELPER="${SCRIPT_DIR}/lib/aa-ma-parse.sh"
elif [ -f "${SCRIPT_DIR}/aa-ma-parse.sh" ]; then
    HELPER="${SCRIPT_DIR}/aa-ma-parse.sh"
else
    printf 'aa-ma-session-start: cannot find aa-ma-parse.sh helper\n' >&2
    exit 0  # SessionStart must never block session start
fi
# shellcheck source=lib/aa-ma-parse.sh
# shellcheck disable=SC1090,SC1091
. "$HELPER"

# Master kill switch honoured.
if aa_ma_is_disabled; then
    exit 0
fi

# Collect active task dirs (mtime-sorted, project-first collision).
mapfile -t TASKS < <(aa_ma_list_active_tasks)

if [ "${#TASKS[@]}" -eq 0 ]; then
    exit 0
fi

# Normalise each path to remove any accidental "//" introduced by trailing-slash $HOME.
normalise_path() {
    # shellcheck disable=SC2001  # sed more portable than bash ${var//} here
    printf '%s' "$1" | sed 's|//*|/|g'
}

TOP_DIR="$(normalise_path "${TASKS[0]}")"
TOP_NAME="$(basename "$TOP_DIR")"
TOP_TASKS_FILE="${TOP_DIR}/${TOP_NAME}-tasks.md"

# Extract milestone + step from the top task's tasks.md (format-agnostic via helper).
active_milestone="unknown"
active_step="unknown"
if [ -f "$TOP_TASKS_FILE" ]; then
    m=$(aa_ma_extract_active_milestone "$TOP_TASKS_FILE")
    s=$(aa_ma_extract_active_step "$TOP_TASKS_FILE")
    [ -n "$m" ] && active_milestone="$m"
    [ -n "$s" ] && active_step="$s"
fi

# Build footer listing other active tasks (cap at 3 names, then "and M more").
FOOTER=""
OTHER_COUNT=$(( ${#TASKS[@]} - 1 ))
if [ "$OTHER_COUNT" -gt 0 ]; then
    declare -a OTHER_NAMES=()
    for ((i = 1; i < ${#TASKS[@]}; i++)); do
        OTHER_NAMES+=("$(basename "${TASKS[i]}")")
    done

    shown_count=${#OTHER_NAMES[@]}
    if [ "$shown_count" -gt 3 ]; then
        shown_count=3
    fi

    # Comma-join the shown names.
    joined=""
    for ((j = 0; j < shown_count; j++)); do
        if [ $j -eq 0 ]; then
            joined="${OTHER_NAMES[j]}"
        else
            joined="${joined}, ${OTHER_NAMES[j]}"
        fi
    done

    remaining=$(( ${#OTHER_NAMES[@]} - shown_count ))
    if [ "$remaining" -gt 0 ]; then
        FOOTER=" (${OTHER_COUNT} other active tasks: ${joined} and ${remaining} more)"
    else
        FOOTER=" (${OTHER_COUNT} other active tasks: ${joined})"
    fi
fi

# -----------------------------------------------------------------------------
# Untrusted input reaches this line from two independent sources: the milestone
# and step TITLES (content of a tasks.md in whatever repo the user cloned) and
# the task DIRECTORY NAME (a path component, equally attacker-chosen). The line
# is hidden system context emitted before the user types anything, so an
# unescaped value can close its own bracket and forge a second AA-MA directive.
# Reproduced end-to-end via both vectors.
#
# The two sources need DIFFERENT treatment, which is the mistake worth not
# repeating: an earlier fix ran the task name through the display sanitiser and
# then built the file path from the result, so a legal directory
# `fix-[urgent]-parser` produced `fix-(urgent)-parser-reference.md` — every
# session start citing a file that does not exist.
#
#   * display fields  -> rewrite (they are prose; corrupting them is harmless)
#   * the path        -> emit verbatim or not at all (rewriting it breaks it)
#
# Truncation uses bash substring, not `cut -c`: measured on this host, `cut -c`
# is byte-oriented and splits a multibyte character, emitting invalid UTF-8 into
# the transcript. The 120 cap clears the longest real heading in the corpus (112).
# -----------------------------------------------------------------------------
_aa_ma_display() {
    local v
    v=$(printf '%s' "$1" \
        | tr -d '\000-\037\177' \
        | sed -E 's/\[/(/g; s/]/)/g
                  s/[Aa][Aa][-_[:space:]]*[Mm][Aa][[:space:]]*[Aa][Cc][Tt][Ii][Vv][Ee]/AA-MA_ACTIVE/g
                  s/[Ll][Oo][Aa][Dd][[:space:]]+[Cc][Oo][Nn][Tt][Ee][Xx][Tt]:/load-context_/g')
    printf '%s' "${v:0:120}"
}

# The path is trusted to be correct or it is not emitted. A sanitised path is
# worse than no path: it sends the model to a file that does not exist.
case "${TOP_DIR}/${TOP_NAME}" in
    *[!A-Za-z0-9._/-]*)
        PATH_CLAUSE="Load context: open this task's directory manually — its path contains characters unsafe to inline here." ;;
    *)
        PATH_CLAUSE="Load context: Read ${TOP_DIR}/${TOP_NAME}-reference.md and ${TOP_NAME}-tasks.md before proceeding." ;;
esac

# Emit the hidden system-context line.
printf 'AA-MA ACTIVE: task=[%s] milestone=[%s] step=[%s]. %s%s' \
    "$(_aa_ma_display "$TOP_NAME")" \
    "$(_aa_ma_display "$active_milestone")" \
    "$(_aa_ma_display "$active_step")" \
    "$PATH_CLAUSE" \
    "$(_aa_ma_display "$FOOTER")"

exit 0
