#!/usr/bin/env bash
# aa-ma-chart-guard.sh — enforcing checks for /aa-ma-chart maps (ADR-0013).
#
#   aa-ma-chart-guard.sh fog      <map>                        exit 0 fog present · 1 "no map needed"
#   aa-ma-chart-guard.sh claim    <map> <ticket-N|N>           exit 0 CLAIMED · 1 refused (reason + frontier)
#   aa-ma-chart-guard.sh reclaim  <map> <ticket-N|N>           CLAIMED → OPEN (+ Reclaimed: ts) → CLAIMED
#   aa-ma-chart-guard.sh from-map <map>                        exit 0 clear · 1 lists OPEN/CLAIMED + fog
#   aa-ma-chart-guard.sh import   <map> <task> <provenance>    git mv|mv+add → .claude/dev/active/<task>/<task>-map.md
#
# Exit 2 = usage (unknown check, unreadable map, missing argument). Every git
# failure is exit 1 with its reason on stdout. AA_MA_HOOKS_DISABLE=1 → exit 0.
#
# A `hooks/lib/` helper, not a registered hook: invoked from the command bodies
# (aa-ma-chart.md, aa-ma-plan.md --from-map) through the `_cand` resolution
# and symlinked by install.sh (L-005 — helpers are never auto-linked). Sources
# its sibling aa-ma-parse.sh via readlink -f so the installed symlink and the
# repo path both find it.
#
# Map grammar read here (docs/templates/map-template.md): one block per
# `### Ticket N: Title`, carrying `- Type:` `- Status:` `- Blocked-by:` lines
# that must precede `#### Question` (any `#`-heading ends the field run); fog = `- ` bullets under
# `## Not yet specified`. Invariant enforced by `claim`: at most ONE non-research
# ticket CLAIMED at a time (OV5) — research tickets are AFK and run in parallel.
#
# ponytail: awk over markdown, no Python. The map is small and the questions are
# few; if the grammar grows (nested tickets, multi-map efforts) move the reader to
# src/aa_ma/ beside gate.py and keep this file a launcher, as aa-ma-parse.sh did.

set -u

# shellcheck source=/dev/null
. "$(dirname "$(readlink -f "$0")")/aa-ma-parse.sh"
aa_ma_is_disabled && exit 0

usage() {
    sed -n '2,10p' "$0" >&2
    exit 2
}

CHECK="${1:-}"; MAP="${2:-}"
[ -n "$CHECK" ] && [ -n "$MAP" ] && [ -r "$MAP" ] || usage

ts() { date +%Y-%m-%dT%H:%M; }

# tickets <map> → TSV: N \t title \t type \t status \t blocked-by
tickets() {
    awk '
        /^### Ticket [0-9]+:/ {
            flush(); inb = 1
            n = $0; sub(/^### Ticket /, "", n); sub(/:.*/, "", n)
            t = $0; sub(/^### Ticket [0-9]+:[[:blank:]]*/, "", t)
            type = "grilling"; status = "OPEN"; blocked = "—"; next
        }
        /^##/ { flush(); inb = 0; next }
        inb && /^- Type:/     { v = $0; sub(/^- Type:[[:blank:]]*/, "", v); type = v }
        inb && /^- Status:/   { v = $0; sub(/^- Status:[[:blank:]]*/, "", v); status = v }
        inb && /^- Blocked-by:/ { v = $0; sub(/^- Blocked-by:[[:blank:]]*/, "", v); blocked = v }
        function flush() { if (inb) printf "%s\t%s\t%s\t%s\t%s\n", n, t, type, status, blocked }
        END { flush() }
    ' "$1"
}

# fog_bullets <map> → the `- ` lines under ## Not yet specified
fog_bullets() {
    awk '/^## Not yet specified/{f=1; next} /^## /{f=0} f && /^- /' "$1"
}

ticket_num() {  # ticket-N | N → N
    local n="${1#ticket-}"
    [[ "$n" =~ ^[0-9]+$ ]] || usage
    printf '%s\n' "$n"
}

# status_of <rows> <N>
status_of() { awk -F'\t' -v n="$2" '$1 == n { print $4 }' <<< "$1"; }

# unblocked <rows> <blocked-by field> → 0 iff every named ticket is RESOLVED|RULED_OUT
unblocked() {
    local rows="$1" field="$2" dep st
    [ "$field" = "—" ] || [ "$field" = "-" ] || [ -z "$field" ] && return 0
    for dep in ${field//,/ }; do
        st="$(status_of "$rows" "$dep")"
        [ "$st" = "RESOLVED" ] || [ "$st" = "RULED_OUT" ] || return 1
    done
    return 0
}

# frontier <rows> → "Ticket N: title" for every OPEN, unblocked ticket
frontier() {
    local rows="$1" n t type st bl
    while IFS=$'\t' read -r n t type st bl; do
        [ "$st" = "OPEN" ] && unblocked "$rows" "$bl" && printf '  - Ticket %s: %s (%s)\n' "$n" "$t" "$type"
    done <<< "$rows"
}

# set_status <map> <N> <status> [claimed-at-ts] [reclaimed-ts]
#   Rewrites one ticket block: Status line replaced, any Claimed-at dropped,
#   Claimed-at re-added iff a ts is given, Reclaimed appended iff a ts is given.
set_status() {
    local map="$1" tmp
    tmp="$(mktemp "${map}.XXXXXX")"
    awk -v n="$2" -v status="$3" -v cat="${4:-}" -v rts="${5:-}" '
        /^### Ticket [0-9]+:/ { inb = ($0 ~ "^### Ticket " n ":") }
        /^##/ && !/^### Ticket [0-9]+:/ { inb = 0 }
        inb && /^- Claimed-at:/ { next }
        inb && /^- Status:/ {
            print "- Status: " status
            if (cat != "") print "- Claimed-at: " cat
            if (rts != "") print "- Reclaimed: " rts
            next
        }
        { print }
    ' "$map" > "$tmp" && mv -f "$tmp" "$map"
}

do_claim() {  # <map> <N>
    local map="$1" n="$2" rows row type st bl t cn ct ctype cst
    rows="$(tickets "$map")"
    row="$(awk -F'\t' -v n="$n" '$1 == n' <<< "$rows")"
    if [ -z "$row" ]; then
        echo "refused: Ticket $n not found in $map"; return 1
    fi
    IFS=$'\t' read -r _ t type st bl <<< "$row"
    if [ "$st" != "OPEN" ]; then
        echo "refused: Ticket $n: $t is $st, not OPEN"
        [ "$st" = "CLAIMED" ] && echo "  (a dead session? re-take it with: reclaim <map> ticket-$n)"
        echo "frontier:"; frontier "$rows"; return 1
    fi
    # The session-wide invariant is asked before the ticket's own edges: "is a
    # session already busy?" is the same answer whichever ticket was named, and
    # the prototype run showed a blocked ticket otherwise hides that reason.
    if [ "$type" != "research" ]; then
        while IFS=$'\t' read -r cn ct ctype cst _; do
            if [ "$cst" = "CLAIMED" ] && [ "$ctype" != "research" ] && [ "$cn" != "$n" ]; then
                echo "refused: Ticket $cn: $ct is CLAIMED — at most one non-research ticket at a time"
                echo "  resolve it, or re-take it with: reclaim <map> ticket-$cn"
                echo "frontier:"; frontier "$rows"; return 1
            fi
        done <<< "$rows"
    fi
    if ! unblocked "$rows" "$bl"; then
        echo "refused: Ticket $n: $t is blocked by: $bl"
        echo "frontier:"; frontier "$rows"; return 1
    fi
    set_status "$map" "$n" CLAIMED "$(ts)"
    echo "claimed: Ticket $n: $t ($type)"
}

do_reclaim() {  # <map> <N>
    local map="$1" n="$2" st
    st="$(status_of "$(tickets "$map")" "$n")"
    if [ "$st" != "CLAIMED" ]; then
        echo "refused: Ticket $n is ${st:-not found}, not CLAIMED — nothing to reclaim"; return 1
    fi
    set_status "$map" "$n" OPEN "" "$(ts)"
    do_claim "$map" "$n"
}

do_from_map() {  # <map> → prints what blocks the handoff, or the counts
    local map="$1" rows open fog n_all n_res n_out
    rows="$(tickets "$map")"
    open="$(awk -F'\t' '$4 == "OPEN" || $4 == "CLAIMED" { printf "  - Ticket %s: %s (%s)\n", $1, $2, $4 }' <<< "$rows")"
    fog="$(fog_bullets "$map")"
    if [ -n "$open" ] || [ -n "$fog" ]; then
        echo "refused: the way is not clear"
        [ -n "$open" ] && { echo "unresolved tickets:"; printf '%s\n' "$open"; }
        [ -n "$fog" ] && { echo "fog (Not yet specified):"; printf '%s\n' "$fog" | sed 's/^/  /'; }
        return 1
    fi
    n_all="$(awk -F'\t' 'NF==5' <<< "$rows" | grep -c .)"
    n_res="$(awk -F'\t' '$4 == "RESOLVED"' <<< "$rows" | grep -c .)"
    n_out="$(awk -F'\t' '$4 == "RULED_OUT"' <<< "$rows" | grep -c .)"
    echo "clear: tickets=$n_all resolved=$n_res ruled_out=$n_out"
}

do_import() {  # <map> <task> <provenance>
    local map task="$2" prov="$3" top effort n dest
    map="$(readlink -f "$1")"; prov="$(readlink -f "$prov")"
    [ -n "$task" ] && [ -n "$prov" ] || usage
    do_from_map "$map" > /dev/null || { do_from_map "$map"; return 1; }
    if ! top="$(git rev-parse --show-toplevel 2>/dev/null)"; then
        echo "refused: import needs a git repository (cwd is not inside one)"; return 1
    fi
    cd "$top" || { echo "refused: cannot cd to $top"; return 1; }
    effort="$(sed -n '1s/^# Charting:[[:blank:]]*//p' "$map")"
    n="$(tickets "$map" | grep -c .)"
    dest=".claude/dev/active/${task}/${task}-map.md"
    mkdir -p "$(dirname "$dest")" || { echo "refused: cannot create $(dirname "$dest")"; return 1; }
    if git ls-files --error-unmatch -- "$map" > /dev/null 2>&1; then
        git mv -- "$map" "$dest" || { echo "refused: git mv failed"; return 1; }
    else
        if ! mv -- "$map" "$dest" || ! git add -- "$dest"; then
            echo "refused: mv + git add failed"; return 1
        fi
    fi
    printf '[%s] MAP_IMPORTED effort=%s tickets=%s\n' "$(date -Iseconds)" "${effort:-unknown}" "$n" >> "$prov" \
        || { echo "refused: cannot append to $prov"; return 1; }
    echo "imported: $dest (effort=${effort:-unknown} tickets=$n)"
}

case "$CHECK" in
    fog)
        if [ -z "$(fog_bullets "$MAP")" ]; then
            echo "no map needed — run /aa-ma-plan"; exit 1
        fi ;;
    claim)    do_claim   "$MAP" "$(ticket_num "${3:-}")" ;;
    reclaim)  do_reclaim "$MAP" "$(ticket_num "${3:-}")" ;;
    from-map) do_from_map "$MAP" ;;
    import)   [ -n "${3:-}" ] && [ -n "${4:-}" ] || usage; do_import "$MAP" "$3" "$4" ;;
    *)        usage ;;
esac
