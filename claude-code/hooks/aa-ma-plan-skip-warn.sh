#!/usr/bin/env bash
# PreToolUse(ExitPlanMode) + SessionEnd hook — advisory warn about skipped
# or missing /aa-ma-plan phase markers in the active runtime log.
#
# Reads stdin JSON from Claude Code:
#   { session_id, transcript_path, cwd, hook_event_name, ... }
#
# Behaviour:
#   1. Honour AA_MA_HOOKS_DISABLE=1 (master kill switch).
#   2. Find newest ~/.claude/runtime/aa-ma-plan-*.log; bail silently if none
#      (we're not in a plan-mode run).
#   3. Check each of the 9 required phase markers (1, 1.3, 1.5, 2, 3, 4,
#      4.2, 4.5, 5):
#        - missing                          → warn
#        - SKIPPED without reason=<token>   → warn
#        - INIT/DONE/SKIPPED-with-reason    → silent
#   4. Always exit 0 (advisory). Warnings are emitted to stderr.
#
# Future enhancement: transcript_path is read but not yet correlated against
# tool_use entries here — the Python aa_ma.plan_markers.fingerprint module
# is the canonical correlator; this bash hook does the cheaper marker-only
# check. Both stay aligned via docs/spec/plan-marker-grammar.md.

set -Eeuo pipefail

# -----------------------------------------------------------------------------
# 1. Kill switch.
# -----------------------------------------------------------------------------
if [ "${AA_MA_HOOKS_DISABLE:-0}" = "1" ]; then
    [ "${AA_MA_PLAN_MARKER_DEBUG:-0}" = "1" ] && printf 'aa-ma-plan-skip-warn: AA_MA_HOOKS_DISABLE=1, skipping\n' >&2
    exit 0
fi

# -----------------------------------------------------------------------------
# 2. Consume stdin JSON defensively. We do not require any specific fields —
#    transcript_path is optional for the marker-only check. Malformed JSON
#    is tolerated (the hook is advisory; never block on infra issues).
# -----------------------------------------------------------------------------
STDIN_JSON="$(cat 2>/dev/null || printf '{}')"

# Validate JSON shape, but never fail on it.
if command -v jq >/dev/null 2>&1; then
    if ! printf '%s' "$STDIN_JSON" | jq empty 2>/dev/null; then
        [ "${AA_MA_PLAN_MARKER_DEBUG:-0}" = "1" ] && printf 'aa-ma-plan-skip-warn: stdin not valid JSON, continuing with empty context\n' >&2
        STDIN_JSON='{}'
    fi
fi

# -----------------------------------------------------------------------------
# 3. Locate newest runtime log.
# -----------------------------------------------------------------------------
RUNTIME_DIR="${HOME:-/tmp}/.claude/runtime"

if [ ! -d "$RUNTIME_DIR" ]; then
    [ "${AA_MA_PLAN_MARKER_DEBUG:-0}" = "1" ] && printf 'aa-ma-plan-skip-warn: %s does not exist, not in a plan\n' "$RUNTIME_DIR" >&2
    exit 0
fi

# Newest aa-ma-plan-*.log by mtime. Use find + sort for portability.
LATEST_LOG="$(
    find "$RUNTIME_DIR" -maxdepth 1 -type f -name 'aa-ma-plan-*.log' -printf '%T@\t%p\n' 2>/dev/null \
        | sort -nr \
        | head -1 \
        | cut -f2-
)"

if [ -z "${LATEST_LOG:-}" ] || [ ! -f "$LATEST_LOG" ]; then
    [ "${AA_MA_PLAN_MARKER_DEBUG:-0}" = "1" ] && printf 'aa-ma-plan-skip-warn: no runtime log found, not in a plan\n' >&2
    exit 0
fi

[ "${AA_MA_PLAN_MARKER_DEBUG:-0}" = "1" ] && printf 'aa-ma-plan-skip-warn: inspecting %s\n' "$LATEST_LOG" >&2

# -----------------------------------------------------------------------------
# 4. Validate the 9 required phase markers.
#    For each: check presence; if SKIPPED, check for reason=<token>.
# -----------------------------------------------------------------------------

# Required phases per docs/spec/plan-marker-grammar.md §9 Required Markers.
REQUIRED_PHASES=(1 1.3 1.5 2 3 4 4.2 4.5 5)

WARNINGS=()

for phase in "${REQUIRED_PHASES[@]}"; do
    # Escape dot for regex.
    re_phase="${phase//./\\.}"
    # Find the marker line for this phase.
    line="$(grep -E "^\[[^]]+\][[:space:]]+PHASE_${re_phase}[[:space:]]+(INIT|DONE|SKIPPED)([[:space:]]|$)" "$LATEST_LOG" 2>/dev/null | head -1 || true)"

    if [ -z "$line" ]; then
        WARNINGS+=("PHASE_${phase}: marker missing from runtime log")
        continue
    fi

    # If SKIPPED, require reason=<token>.
    if printf '%s' "$line" | grep -qE '[[:space:]]+SKIPPED([[:space:]]|$)'; then
        if ! printf '%s' "$line" | grep -qE 'reason=[^[:space:]]+'; then
            WARNINGS+=("PHASE_${phase}: SKIPPED but missing required reason=<token> payload")
        fi
    fi
done

# -----------------------------------------------------------------------------
# 5. Emit warnings to stderr. Always exit 0 (advisory).
# -----------------------------------------------------------------------------
if [ "${#WARNINGS[@]}" -gt 0 ]; then
    {
        printf 'aa-ma-plan: %d phase marker issue(s) detected in %s\n' "${#WARNINGS[@]}" "$LATEST_LOG"
        for w in "${WARNINGS[@]}"; do
            printf '  - %s\n' "$w"
        done
        printf '  (advisory only — bypass with AA_MA_HOOKS_DISABLE=1)\n'
    } >&2
fi

exit 0
