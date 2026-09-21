#!/usr/bin/env bats
# aa-ma-chart-guard.bats — the charting guard's refusal, reclaim and import legs.
#
# mattpocock-trio-adoption M5 (ADR-0013). The guard is a `hooks/lib/` helper
# invoked from the /aa-ma-chart and /aa-ma-plan command bodies, never a
# registered hook event. Every enforcing answer a charting session relies on
# — "may I claim this?", "is the way clear?", "where did the map go?" — comes
# from here, so each one has a test that fails if the logic breaks.
#
# Run against the repo path (as a fresh clone does) AND through a fake
# CLAUDE_HOME symlink (as an installed machine does): the guard sources its
# sibling aa-ma-parse.sh via readlink -f, and both routes must land on it.

bats_require_minimum_version 1.5.0

setup() {
    REPO_ROOT="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)"
    GUARD="${REPO_ROOT}/claude-code/hooks/lib/aa-ma-chart-guard.sh"
    HELPER="${REPO_ROOT}/claude-code/hooks/lib/aa-ma-parse.sh"
    FIXDIR="${BATS_TEST_DIRNAME}/fixtures/charting"
    WORK="$(mktemp -d "${BATS_TMPDIR}/chart-guard.XXXXXX")"
    CLAUDE_HOME="${WORK}/claude-home"
    mkdir -p "${CLAUDE_HOME}/hooks/lib"
    ln -s "${HELPER}" "${CLAUDE_HOME}/hooks/lib/aa-ma-parse.sh"
    [ -f "${GUARD}" ] && ln -s "${GUARD}" "${CLAUDE_HOME}/hooks/lib/aa-ma-chart-guard.sh"
    export REPO_ROOT GUARD HELPER FIXDIR WORK CLAUDE_HOME
    unset AA_MA_HOOKS_DISABLE
}

teardown() {
    rm -rf "${WORK}"
}

# Copy a fixture into the work dir so mutating checks never touch the repo.
_map() {  # <fixture-stem>
    cp "${FIXDIR}/$1-map.md" "${WORK}/$1-map.md"
    printf '%s\n' "${WORK}/$1-map.md"
}

# Lines of one ticket block, for field assertions.
_block() {  # <map> <N>
    awk -v n="$2" '/^### Ticket /{f=($0 ~ "^### Ticket " n ":")} /^## /{f=0} f' "$1"
}

# --- (a) fog -----------------------------------------------------------------

@test "fog: zero fog → 'no map needed — run /aa-ma-plan', exit 1, nothing created" {
    map="$(_map fogless)"
    before="$(md5sum < "$map")"
    run bash "$GUARD" fog "$map"
    [ "$status" -eq 1 ]
    [[ "$output" == *"no map needed — run /aa-ma-plan"* ]]
    [ "$(md5sum < "$map")" = "$before" ]
    [ ! -e "${WORK}/.claude" ]
}

@test "fog: at least one bullet under Not yet specified → exit 0" {
    run bash "$GUARD" fog "$(_map open)"
    [ "$status" -eq 0 ]
}

# --- (b) claim ---------------------------------------------------------------

@test "claim: a non-research ticket while another non-research ticket is CLAIMED → exit 1 + frontier" {
    map="$(_map claimed)"
    before="$(md5sum < "$map")"
    run bash "$GUARD" claim "$map" ticket-3
    [ "$status" -eq 1 ]
    [[ "$output" == *"Ticket 1: Which storage shape?"*"CLAIMED"* ]]
    [[ "$output" == *"frontier"* ]]
    [[ "$output" == *"Ticket 2: Does the API paginate?"* ]]
    [[ "$output" == *"Ticket 3: Which name?"* ]]
    [[ "$output" != *"Ticket 4:"* ]]        # blocked by 1 → not on the frontier
    [ "$(md5sum < "$map")" = "$before" ]    # a refusal never writes
}

@test "claim: the one-at-a-time refusal wins over blocked-by (prototype-run finding)" {
    map="$(_map claimed)"
    run bash "$GUARD" claim "$map" ticket-4        # blocked by 1 AND 1 is CLAIMED
    [ "$status" -eq 1 ]
    [[ "$output" == *"at most one non-research ticket"* ]]
    [[ "$output" != *"is blocked by"* ]]
}

@test "claim: a research ticket while a grilling ticket is CLAIMED → exit 0 (research runs in parallel)" {
    map="$(_map claimed)"
    run bash "$GUARD" claim "$map" ticket-2
    [ "$status" -eq 0 ]
    _block "$map" 2 | grep -q '^- Status: CLAIMED$'
    _block "$map" 2 | grep -Eq '^- Claimed-at: [0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}$'
    _block "$map" 1 | grep -q '^- Claimed-at: 2026-09-21T09:00$'   # other block untouched
}

@test "claim: a ticket whose Blocked-by is not yet RESOLVED/RULED_OUT → exit 1" {
    map="$(_map open)"
    run bash "$GUARD" claim "$map" ticket-3
    [ "$status" -eq 1 ]
    [[ "$output" == *"blocked"* ]]
    _block "$map" 3 | grep -q '^- Status: OPEN$'
}

@test "claim: an OPEN, unblocked ticket → CLAIMED + Claimed-at, exit 0; bare N accepted" {
    map="$(_map open)"
    run bash "$GUARD" claim "$map" 1
    [ "$status" -eq 0 ]
    [[ "$output" == *"Ticket 1: Which storage shape?"* ]]
    _block "$map" 1 | grep -q '^- Status: CLAIMED$'
    [ "$(_block "$map" 1 | grep -c '^- Claimed-at: ')" -eq 1 ]
}

@test "claim: a RESOLVED ticket or an unknown ticket → exit 1" {
    map="$(_map open)"
    run bash "$GUARD" claim "$map" ticket-2
    [ "$status" -eq 1 ]
    run bash "$GUARD" claim "$map" ticket-9
    [ "$status" -eq 1 ]
    [[ "$output" == *"not found"* ]]
}

# --- (c) from-map ------------------------------------------------------------

@test "from-map: OPEN tickets or fog → exit 1 listing them" {
    run bash "$GUARD" from-map "$(_map open)"
    [ "$status" -eq 1 ]
    [[ "$output" == *"Ticket 1: Which storage shape?"* ]]
    [[ "$output" == *"Ticket 3: Which query API shape feels right?"* ]]
    [[ "$output" != *"Ticket 2:"* ]]
    [[ "$output" == *"migration of existing data"* ]]
}

@test "from-map: a CLAIMED ticket is listed too" {
    run bash "$GUARD" from-map "$(_map claimed)"
    [ "$status" -eq 1 ]
    [[ "$output" == *"Ticket 1: Which storage shape?"*"CLAIMED"* ]]
}

@test "from-map: every ticket RESOLVED|RULED_OUT and no fog → exit 0 with the ticket count" {
    run bash "$GUARD" from-map "$(_map clear)"
    [ "$status" -eq 0 ]
    [[ "$output" == *"tickets=3"* ]]
}

# --- (d) reclaim -------------------------------------------------------------

@test "reclaim: CLAIMED → OPEN + '- Reclaimed: <ts>' → CLAIMED again with a fresh Claimed-at" {
    map="$(_map claimed)"
    run bash "$GUARD" reclaim "$map" ticket-1
    [ "$status" -eq 0 ]
    _block "$map" 1 | grep -q '^- Status: CLAIMED$'
    [ "$(_block "$map" 1 | grep -c '^- Claimed-at: ')" -eq 1 ]
    ! _block "$map" 1 | grep -q '^- Claimed-at: 2026-09-21T09:00$'
    _block "$map" 1 | grep -Eq '^- Reclaimed: [0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}$'
    _block "$map" 3 | grep -q '^- Status: OPEN$'
}

@test "reclaim: a ticket that is not CLAIMED → exit 1, map unchanged" {
    map="$(_map open)"
    before="$(md5sum < "$map")"
    run bash "$GUARD" reclaim "$map" ticket-1
    [ "$status" -eq 1 ]
    [ "$(md5sum < "$map")" = "$before" ]
}

# --- (e) import --------------------------------------------------------------

_repo() {  # prints a fresh git repo holding the clear map at the charting path
    local r="${WORK}/repo-$RANDOM"
    mkdir -p "$r/.claude/dev/charting/demo-effort" "$r/.claude/dev/active/demo-task"
    git -C "$r" init -q
    git -C "$r" config user.email t@example.com
    git -C "$r" config user.name t
    cp "${FIXDIR}/clear-map.md" "$r/.claude/dev/charting/demo-effort/demo-effort-map.md"
    : > "$r/.claude/dev/active/demo-task/demo-task-provenance.log"
    printf '%s\n' "$r"
}

@test "import: tracked map → git mv into .claude/dev/active/<task>/<task>-map.md + MAP_IMPORTED line" {
    r="$(_repo)"
    git -C "$r" add -A && git -C "$r" commit -qm init
    run bash -c "cd '$r' && bash '$GUARD' import .claude/dev/charting/demo-effort/demo-effort-map.md demo-task .claude/dev/active/demo-task/demo-task-provenance.log"
    [ "$status" -eq 0 ]
    [ -f "$r/.claude/dev/active/demo-task/demo-task-map.md" ]
    [ ! -e "$r/.claude/dev/charting/demo-effort/demo-effort-map.md" ]
    grep -Eq '^\[[^]]+\] MAP_IMPORTED effort=demo-effort tickets=3$' "$r/.claude/dev/active/demo-task/demo-task-provenance.log"
    git -C "$r" status --porcelain | grep -q '^R.*demo-task-map.md'
}

@test "import: untracked map → mv + git add, same destination and provenance line" {
    r="$(_repo)"
    run bash -c "cd '$r' && bash '$GUARD' import .claude/dev/charting/demo-effort/demo-effort-map.md demo-task .claude/dev/active/demo-task/demo-task-provenance.log"
    [ "$status" -eq 0 ]
    [ -f "$r/.claude/dev/active/demo-task/demo-task-map.md" ]
    [ ! -e "$r/.claude/dev/charting/demo-effort/demo-effort-map.md" ]
    grep -q 'MAP_IMPORTED effort=demo-effort tickets=3' "$r/.claude/dev/active/demo-task/demo-task-provenance.log"
    git -C "$r" status --porcelain | grep -q '^A.*demo-task-map.md'
}

@test "import: refuses a map that is not clear (from-map would fail)" {
    r="$(_repo)"
    cp "${FIXDIR}/open-map.md" "$r/.claude/dev/charting/demo-effort/demo-effort-map.md"
    run bash -c "cd '$r' && bash '$GUARD' import .claude/dev/charting/demo-effort/demo-effort-map.md demo-task .claude/dev/active/demo-task/demo-task-provenance.log"
    [ "$status" -eq 1 ]
    [ -e "$r/.claude/dev/charting/demo-effort/demo-effort-map.md" ]
}

@test "import: a cwd that is not a git repo → exit 1 with a reason" {
    mkdir -p "${WORK}/norepo" && cp "${FIXDIR}/clear-map.md" "${WORK}/norepo/m.md"
    run bash -c "cd '${WORK}/norepo' && bash '$GUARD' import m.md demo-task prov.log"
    [ "$status" -eq 1 ]
    [ -n "$output" ]
    [ -e "${WORK}/norepo/m.md" ]
}

# --- plumbing ----------------------------------------------------------------

@test "usage: unknown check or missing map → exit 2" {
    run bash "$GUARD" bogus "$(_map open)"
    [ "$status" -eq 2 ]
    run bash "$GUARD" claim "${WORK}/does-not-exist.md" ticket-1
    [ "$status" -eq 2 ]
    run bash "$GUARD"
    [ "$status" -eq 2 ]
}

@test "AA_MA_HOOKS_DISABLE=1: every check is a no-op exit 0 and writes nothing" {
    map="$(_map claimed)"
    before="$(md5sum < "$map")"
    AA_MA_HOOKS_DISABLE=1 run bash "$GUARD" claim "$map" ticket-3
    [ "$status" -eq 0 ]
    [ "$(md5sum < "$map")" = "$before" ]
}

@test "installed route: the fake CLAUDE_HOME symlink resolves the sibling aa-ma-parse.sh" {
    [ -L "${CLAUDE_HOME}/hooks/lib/aa-ma-chart-guard.sh" ]
    run bash "${CLAUDE_HOME}/hooks/lib/aa-ma-chart-guard.sh" from-map "$(_map clear)"
    [ "$status" -eq 0 ]
}

# --- §6.8 M5 pins (security CRITICAL + WARNINGs) --------------------------------

@test "slug: import refuses a <task> that is not [a-z0-9-]+ (exit 2, nothing moved)" {
    r="$(_repo)"
    run bash -c "cd '$r' && bash '$GUARD' import .claude/dev/charting/demo-effort/demo-effort-map.md '../../x' .claude/dev/active/demo-task/demo-task-provenance.log"
    [ "$status" -eq 2 ]
    [ -e "$r/.claude/dev/charting/demo-effort/demo-effort-map.md" ]
    [ ! -e "$r/.claude/dev/x-map.md" ] && [ ! -e "$r/x-map.md" ]
}

@test "slug: fog and import refuse a map whose '# Charting:' header is not a slug (exit 2)" {
    map="$(_map badheader)"
    run bash "$GUARD" fog "$map"
    [ "$status" -eq 2 ]
    r="$(_repo)"; cp "${FIXDIR}/badheader-map.md" "$r/.claude/dev/charting/demo-effort/demo-effort-map.md"
    run bash -c "cd '$r' && bash '$GUARD' import .claude/dev/charting/demo-effort/demo-effort-map.md demo-task .claude/dev/active/demo-task/demo-task-provenance.log"
    [ "$status" -eq 2 ]
    [ -e "$r/.claude/dev/charting/demo-effort/demo-effort-map.md" ]
}

@test "claim: a ticket block with no Status line → exit 1 'could not write', map unchanged" {
    map="$(_map nostatus)"
    before="$(md5sum < "$map")"
    run bash "$GUARD" claim "$map" ticket-1
    [ "$status" -eq 1 ]
    [[ "$output" == *"could not write"* ]]
    [ "$(md5sum < "$map")" = "$before" ]
}

@test "import: refuses to clobber an existing <task>-map.md (untracked path)" {
    r="$(_repo)"
    printf 'existing\n' > "$r/.claude/dev/active/demo-task/demo-task-map.md"
    run bash -c "cd '$r' && bash '$GUARD' import .claude/dev/charting/demo-effort/demo-effort-map.md demo-task .claude/dev/active/demo-task/demo-task-provenance.log"
    [ "$status" -eq 1 ]
    [[ "$output" == *"already exists"* ]]
    [ "$(cat "$r/.claude/dev/active/demo-task/demo-task-map.md")" = "existing" ]
    [ -e "$r/.claude/dev/charting/demo-effort/demo-effort-map.md" ]
}

@test "AA_MA_HOOKS_DISABLE=1 disables enforcement only: import still moves the map and writes MAP_IMPORTED" {
    r="$(_repo)"
    cp "${FIXDIR}/open-map.md" "$r/.claude/dev/charting/demo-effort/demo-effort-map.md"   # not clear
    run bash -c "cd '$r' && AA_MA_HOOKS_DISABLE=1 bash '$GUARD' import .claude/dev/charting/demo-effort/demo-effort-map.md demo-task .claude/dev/active/demo-task/demo-task-provenance.log"
    [ "$status" -eq 0 ]
    [ -f "$r/.claude/dev/active/demo-task/demo-task-map.md" ]
    grep -q 'MAP_IMPORTED effort=open-effort tickets=3' "$r/.claude/dev/active/demo-task/demo-task-provenance.log"
}

@test "usage: the usage text names every check (not tied to header line numbers)" {
    run bash "$GUARD"
    [ "$status" -eq 2 ]
    for c in fog claim reclaim from-map import; do [[ "$output" == *"$c"* ]]; done
}

# The /aa-ma-chart fences, executed as shipped (aa-ma-gate-python.bats pattern):
# the guard-resolution fence (with <effort> substituted) followed by the fog-test fence.
_chart_fences() {  # <effort>
    local cmd="${REPO_ROOT}/claude-code/commands/aa-ma-chart.md"
    { awk '/^## Guard resolution/{f=1} f && /^```bash$/{g=1; next} g && /^```$/{exit} g' "$cmd" | sed "s|^EFFORT=\"<effort>\"|EFFORT=\"$1\"|"
      awk '/^3\. \*\*Fog test/{f=1} f && /^ *```bash$/{g=1; next} g && /^ *```$/{exit} g' "$cmd"; }
}

@test "chart fence: an effort outside [a-z0-9-]+ exits 2 before any rm can run" {
    mkdir -p "${WORK}/proj/.claude/dev/charting/other" && printf 'keep\n' > "${WORK}/proj/.claude/dev/charting/other/other-map.md"
    git -C "${WORK}/proj" init -q
    _chart_fences '../other' > "${WORK}/fence.sh"
    run bash -c "cd '${WORK}/proj' && bash '${WORK}/fence.sh'"
    [ "$status" -eq 2 ]
    [ -f "${WORK}/proj/.claude/dev/charting/other/other-map.md" ]
    _chart_fences '' > "${WORK}/fence0.sh"
    run bash -c "cd '${WORK}/proj' && bash '${WORK}/fence0.sh'"
    [ "$status" -eq 2 ]
    [ -f "${WORK}/proj/.claude/dev/charting/other/other-map.md" ]
}

@test "chart fence: a fogless draft removes only its own map + empty dir, exit 1; siblings untouched" {
    mkdir -p "${WORK}/proj/.claude/dev/charting/other" "${WORK}/proj/.claude/dev/charting/fogless-effort"
    printf 'keep\n' > "${WORK}/proj/.claude/dev/charting/other/other-map.md"
    cp "${FIXDIR}/fogless-map.md" "${WORK}/proj/.claude/dev/charting/fogless-effort/fogless-effort-map.md"
    git -C "${WORK}/proj" init -q
    _chart_fences 'fogless-effort' > "${WORK}/fence.sh"
    run bash -c "cd '${WORK}/proj' && bash '${WORK}/fence.sh'"
    [ "$status" -eq 1 ]
    [[ "$output" == *"no map needed"* ]]
    [ ! -e "${WORK}/proj/.claude/dev/charting/fogless-effort" ]
    [ -f "${WORK}/proj/.claude/dev/charting/other/other-map.md" ]
}
