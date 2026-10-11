#!/usr/bin/env bats
# hook-headers.bats — every claude-code/hooks/*.sh states its contract in its header (M7.3):
#   # Event: <registered event(s)>, or "none" for a helper that is not a registered hook
#   # Mode: Blocking | Advisory
#   # Exit: <codes and meanings>
#   # Fail-open: <what happens when the hook cannot do its job>
# and the header agrees with the AA_MA_HOOKS registration table.

bats_require_minimum_version 1.5.0

setup() {
    ROOT="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)"
    TABLE="$ROOT/scripts/lib/aa-ma-install-lib.sh"
}

# header_field <file> <field> — the value of "# <field>: …" within the first 20 lines.
header_field() {
    head -n 20 "$1" | sed -n "s/^# $2: //p" | head -n 1
}

# registered_events <hook basename> — the events the AA_MA_HOOKS table registers it for.
registered_events() {
    sed -n '/^AA_MA_HOOKS=(/,/^)/p' "$TABLE" | grep -F "|$1|" | sed 's/^ *"//; s/|.*//' | sort -u
}

@test "every hook declares Event, Mode, Exit and Fail-open in its header" {
    for f in "$ROOT"/claude-code/hooks/*.sh; do
        for field in Event Mode Exit Fail-open; do
            [ -n "$(header_field "$f" "$field")" ] || { echo "${f##*/}: no '# ${field}:' header"; return 1; }
        done
        [[ "$(header_field "$f" Mode)" =~ ^(Blocking|Advisory)([^A-Za-z]|$) ]] || { echo "${f##*/}: Mode must be Blocking or Advisory"; return 1; }
    done
}

@test "each Event header names every event the hook is registered for" {
    for f in "$ROOT"/claude-code/hooks/*.sh; do
        name="${f##*/}"
        event="$(header_field "$f" Event)"
        events="$(registered_events "$name")"
        if [ -z "$events" ]; then
            [[ "$event" == none* ]] || { echo "$name: not registered, so its Event must start with 'none'"; return 1; }
            continue
        fi
        while IFS= read -r e; do
            [[ "$event" == *"$e"* ]] || { echo "$name: Event '$event' misses registered $e"; return 1; }
        done <<< "$events"
    done
}

@test "an Advisory hook never exits 2, and no hook exits 1 as a policy decision" {
    for f in "$ROOT"/claude-code/hooks/*.sh; do
        name="${f##*/}"
        mode="$(header_field "$f" Mode)"
        event="$(header_field "$f" Event)"
        if [[ "$mode" == Advisory* && "$event" != none* ]]; then
            run ! grep -nE '^[^#]*\bexit 2\b' "$f"
        fi
        # exit 1 is allowed only for hook-infrastructure errors, which the Exit header must say
        if grep -qE '^[^#]*\bexit 1\b' "$f"; then   # code only: comments may say "exit 1 means …"
            [[ "$(header_field "$f" Exit)" == *"1 "*infra* ]] || { echo "$name: exits 1 but its Exit header does not mark 1 as an infra error"; return 1; }
        fi
    done
}
