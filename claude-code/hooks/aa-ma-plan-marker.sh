#!/usr/bin/env bash
# aa-ma-plan-marker.sh — append a well-formed phase marker to the active
# /aa-ma-plan runtime log.
#
# Usage:
#   aa-ma-plan-marker.sh <slug> <phase_id> <status> [key=value ...]
#
# Where:
#   <slug>     plan-run slug (e.g., harden-aa-ma-plan-20260511130000)
#   <phase_id> one of: 0, 1, 1.3, 1.5, 2, 3, 4, 4.2, 4.5, 5
#   <status>   INIT | DONE | SKIPPED   (case-sensitive; INIT only on PHASE_0)
#   key=value  zero or more payload tokens. Values may NOT contain spaces.
#
# Behaviour:
#   - Creates ~/.claude/runtime/ if it does not exist.
#   - Appends a single line in the canonical grammar:
#       [<ISO8601-ts>] PHASE_<id> <STATUS> — <key>=<value> [<key>=<value> ...]
#   - Validates SKIPPED has reason=; warns to stderr otherwise (still appends).
#   - Idempotent on directory creation; concurrent writes use append-only I/O.
#   - Exits 0 on successful append; non-zero only on argument errors.
#
# Reference grammar: docs/spec/plan-marker-grammar.md

set -Eeuo pipefail

if [ "$#" -lt 3 ]; then
    printf 'aa-ma-plan-marker: usage: %s <slug> <phase_id> <status> [key=value ...]\n' "$(basename "$0")" >&2
    exit 2
fi

SLUG="$1"
PHASE_ID="$2"
STATUS="$3"
shift 3

# Validate status.
case "$STATUS" in
    INIT|DONE|SKIPPED) ;;
    *)
        printf 'aa-ma-plan-marker: invalid status %q (must be INIT, DONE, or SKIPPED)\n' "$STATUS" >&2
        exit 2
        ;;
esac

# Validate slug (alphanumeric + hyphens).
if ! printf '%s' "$SLUG" | grep -qE '^[a-z0-9]([a-z0-9-]*[a-z0-9])?$'; then
    printf 'aa-ma-plan-marker: invalid slug %q (must be lowercase [a-z0-9-])\n' "$SLUG" >&2
    exit 2
fi

# Validate phase ID shape.
if ! printf '%s' "$PHASE_ID" | grep -qE '^[0-9]+(\.[0-9]+)?$'; then
    printf 'aa-ma-plan-marker: invalid phase_id %q (must be digits, optionally one dot)\n' "$PHASE_ID" >&2
    exit 2
fi

# Validate INIT-only-on-PHASE_0 invariant (warn but proceed).
if [ "$STATUS" = "INIT" ] && [ "$PHASE_ID" != "0" ]; then
    printf 'aa-ma-plan-marker: WARNING: INIT status is only valid on PHASE_0; got PHASE_%s\n' "$PHASE_ID" >&2
fi

# Build payload from remaining key=value args. Reject values containing spaces.
PAYLOAD=""
for kv in "$@"; do
    if ! printf '%s' "$kv" | grep -qE '^[a-z][a-z0-9_]*=[^[:space:]]+$'; then
        printf 'aa-ma-plan-marker: invalid key=value %q (key must be lowercase, value must be space-free)\n' "$kv" >&2
        exit 2
    fi
    if [ -z "$PAYLOAD" ]; then
        PAYLOAD="$kv"
    else
        PAYLOAD="$PAYLOAD $kv"
    fi
done

# Warn (but accept) SKIPPED without reason=.
if [ "$STATUS" = "SKIPPED" ] && ! printf '%s' "$PAYLOAD" | grep -qE '(^| )reason='; then
    printf 'aa-ma-plan-marker: WARNING: SKIPPED markers should include reason=<token>\n' >&2
fi

# Resolve runtime log path.
RUNTIME_DIR="${HOME:-/tmp}/.claude/runtime"
mkdir -p "$RUNTIME_DIR"
LOGFILE="${RUNTIME_DIR}/aa-ma-plan-${SLUG}.log"

# Compose marker. Em-dash (U+2014).
TS="$(date -u +"%Y-%m-%dT%H:%M:%S%z" | sed 's/\(..\)$/:\1/')"  # RFC3339 with colon in offset
if [ -n "$PAYLOAD" ]; then
    LINE="[${TS}] PHASE_${PHASE_ID} ${STATUS} — ${PAYLOAD}"
else
    LINE="[${TS}] PHASE_${PHASE_ID} ${STATUS} —"
fi

printf '%s\n' "$LINE" >> "$LOGFILE"
