#!/usr/bin/env bats
# code-intel-refresh.bats — execute-aa-ma-milestone §6.0, scripts/code-intel-refresh.sh
# (code-conventions-impact M15.6, report 03 T6 / P0 #3).
#
# At the milestone boundary: refresh codemem (refresh + refresh-commits) and the
# graphify code graph through the 15.4 post-commit worker, then record
#   CODE_INTEL_REFRESH — <heading> — codemem=<sha|skipped(no index)> graphify=<sha|WARN reason>
# naming the PRE-commit HEAD. graphify never blocks; a codemem index that exists
# and fails to refresh is BLOCKED. graphify is a stub; codemem is the forge's.

bats_require_minimum_version 1.5.0

setup() {
    FORGE="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)"
    SCRIPT="${FORGE}/claude-code/skills/execute-aa-ma-milestone/scripts/code-intel-refresh.sh"
    WORK="$(mktemp -d)"
    # codemem keeps trust records under XDG_STATE_HOME (M15 §6.8): never the user's.
    export XDG_STATE_HOME="${WORK}/state"
    # ... and its default index under XDG_CACHE_HOME (M16)
    export XDG_CACHE_HOME="${WORK}/cache"
    unset CODEMEM_DB
    R="${WORK}/r"
    T="${R}/.claude/dev/active/t"
    PROV="${T}/t-provenance.log"
    HEADING="Milestone 2: The one being gated"
    STUBS="${WORK}/stubs"
    export STUB_LOG="${WORK}/stub.log"
    mkdir -p "$T" "$STUBS"
    cat > "${STUBS}/graphify" <<'EOF'
#!/usr/bin/env bash
echo "start" >> "$STUB_LOG"
[[ -n "${STUB_FAIL:-}" ]] && exit 3
mkdir -p graphify-out
git rev-parse HEAD > graphify-out/graph.json
EOF
    chmod +x "${STUBS}/graphify"
    # aa-ma-gate needs uv; link only uv, so a real graphify beside it stays off PATH.
    ln -s "$(command -v uv)" "${STUBS}/uv"
    export PATH="${STUBS}:/usr/local/bin:/usr/bin:/bin"
    cp "${BATS_TEST_DIRNAME}/fixtures/gate-scans/one-active-tasks.md" "${T}/t-tasks.md"
    : > "$PROV"
    printf '.codemem/\ngraphify-out/\n' > "${R}/.gitignore"
    printf 'def a():\n    return 1\n' > "${R}/a.py"
    git -C "$R" init -q -b main
    git -C "$R" -c user.name=t -c user.email=t@t -c commit.gpgsign=false add -A
    git -C "$R" -c user.name=t -c user.email=t@t -c commit.gpgsign=false commit -q -m init
    cd "$R" || return 1
    CM="$(bash -c '. "$1"; aa_ma_codemem_dir "$2"' _ "${FORGE}/claude-code/hooks/lib/aa-ma-parse.sh" "$R")"
    [[ "$CM" == "${XDG_CACHE_HOME}/codemem/"* ]] || return 1
    "${FORGE}/.venv/bin/codemem" build > /dev/null
}

teardown() {
    [[ -n "${WORK:-}" ]] && rm -rf "$WORK"
}

line_count() { grep -c 'CODE_INTEL_REFRESH' "$PROV" || true; }

@test "appends one line naming the pre-commit HEAD; both indexes at HEAD" {
    printf 'def a():\n    return 2\n' > a.py   # uncommitted milestone work
    head=$(git rev-parse HEAD)
    run bash "$SCRIPT" t
    [ "$status" -eq 0 ]
    [ "$(line_count)" -eq 1 ]
    grep -qE "^\[[^]]+\] CODE_INTEL_REFRESH — ${HEADING} — codemem=${head} graphify=${head}$" "$PROV"
    [ "$(cat "${CM}/last_sha")" = "$head" ]
    [ "$(cat graphify-out/.built_sha)" = "$head" ]
}

@test "--dry-run refreshes and prints the line, provenance untouched" {
    head=$(git rev-parse HEAD)
    run bash "$SCRIPT" t --dry-run
    [ "$status" -eq 0 ]
    [[ "$output" == *"CODE_INTEL_REFRESH — ${HEADING} — codemem=${head} graphify=${head}"* ]]
    [ "$(line_count)" -eq 0 ]
}

@test "graphify failing WARNs and never blocks" {
    head=$(git rev-parse HEAD)
    STUB_FAIL=1 run bash "$SCRIPT" t
    [ "$status" -eq 0 ]
    grep -qE "— codemem=${head} graphify=WARN " "$PROV"
}

@test "graphify absent WARNs 'graphify not found'" {
    rm -f "${STUBS}/graphify"
    run bash "$SCRIPT" t
    [ "$status" -eq 0 ]
    grep -qE "graphify=WARN graphify not found$" "$PROV"
}

@test "an existing codemem index that fails to refresh is BLOCKED, nothing appended" {
    # A refresh error on an index built here (a garbage file is untrusted and rebuilt, §6.8).
    "${FORGE}/.venv/bin/python" -I -c 'import sqlite3, sys; c = sqlite3.connect(sys.argv[1]); c.execute("DROP TABLE files"); c.commit()' "${CM}/index.db"
    git -c user.name=t -c user.email=t@t -c commit.gpgsign=false commit -q --allow-empty -m next
    run bash "$SCRIPT" t
    [ "$status" -eq 1 ]
    [[ "$output" == *"BLOCKED"*"codemem"* ]]
    [ "$(line_count)" -eq 0 ]
}

@test "no codemem index and no codemem → codemem=skipped(no index)" {
    rm -rf "$CM"
    head=$(git rev-parse HEAD)
    CODEMEM_BIN=/nonexistent run bash "$SCRIPT" t
    [ "$status" -eq 0 ]
    grep -qE "— codemem=skipped\(no index\) graphify=${head}$" "$PROV"
}

@test "a symlinked provenance log is refused" {
    printf 'original\n' > "${WORK}/victim"
    rm -f "$PROV"
    ln -s "${WORK}/victim" "$PROV"
    run bash "$SCRIPT" t
    [ "$status" -eq 1 ]
    [ "$(cat "${WORK}/victim")" = "original" ]
}

@test "a task name that is not a plain slug is refused" {
    run bash "$SCRIPT" "../t"
    [ "$status" -eq 1 ]
    [[ "$output" == *"BLOCKED"* ]]
}

@test "SKILL.md points at §6.0 and stays within the 500-line cap" {
    skill="${FORGE}/claude-code/skills/execute-aa-ma-milestone/SKILL.md"
    grep -q 'code-intel-refresh' "$skill"
    [ "$(wc -l < "$skill")" -le 500 ]
    grep -q 'scripts/code-intel-refresh.sh' "${FORGE}/claude-code/skills/execute-aa-ma-milestone/references/boundary-checks.md"
}

@test "a repo-planted claude-code/hooks/lib/aa-ma-parse.sh is never sourced" {
    mkdir -p claude-code/hooks/lib
    printf 'touch "%s/planted-ran"\n' "$WORK" > claude-code/hooks/lib/aa-ma-parse.sh
    run bash "$SCRIPT" t --dry-run
    [ "$status" -eq 0 ]
    [ ! -e "${WORK}/planted-ran" ]
}

@test "the §6.0 fence runs the installed copy only, never the repo's" {
    doc="${FORGE}/claude-code/skills/execute-aa-ma-milestone/references/boundary-checks.md"
    fence=$(awk '/^### 6.0/{f=1} f && /^```bash/{b=1; next} b && /^```/{exit} b' "$doc")
    [[ "$fence" == *'CLAUDE_HOME'* ]]
    [[ "$fence" != *'show-toplevel'* ]]
}

# --- §6.8 (M15 C2): the gate trusts no linked sidecar or index dir ----------

@test "§6.8: a symlinked last_sha naming HEAD is BLOCKED" {
    git rev-parse HEAD > "${WORK}/fake-sha"
    rm -f "${CM}/last_sha"
    ln -s "${WORK}/fake-sha" "${CM}/last_sha"
    run bash "$SCRIPT" t
    [ "$status" -eq 1 ]
    [[ "$output" == *"BLOCKED"* ]]
    [ "$(line_count)" -eq 0 ]
}

@test "§6.8: a symlinked .built_sha naming HEAD is a WARN, not a graphify SHA" {
    mkdir -p graphify-out
    git rev-parse HEAD > "${WORK}/fake-sha"
    ln -s "${WORK}/fake-sha" graphify-out/.built_sha
    STUB_FAIL=1 run bash "$SCRIPT" t
    [ "$status" -eq 0 ]
    grep -qE "graphify=WARN " "$PROV"
}

@test "§6.8: a symlinked index dir is BLOCKED and named" {
    mv "$CM" "${WORK}/elsewhere"
    ln -s "${WORK}/elsewhere" "$CM"
    run bash "$SCRIPT" t
    [ "$status" -eq 1 ]
    [[ "$output" == *"BLOCKED"*"index dir"*"symlink"* ]]
    [ "$(line_count)" -eq 0 ]
}

@test "§6.8 re-run: a link inside the index dir is BLOCKED and named" {
    printf 'x\n' > "${WORK}/victim"
    rm -f "${CM}/index.db"
    ln -s "${WORK}/victim" "${CM}/index.db"
    run bash "$SCRIPT" t
    [ "$status" -eq 1 ]
    [[ "$output" == *"BLOCKED"*"index dir"*"symlink"* ]]
    [ "$(line_count)" -eq 0 ]
}

@test "§6.8 re-run: a dangling index.db link is BLOCKED, not skipped(no index)" {
    rm -f "${CM}/index.db"
    ln -s "${WORK}/nowhere" "${CM}/index.db"
    run bash "$SCRIPT" t
    [ "$status" -eq 1 ]
    [ "$(line_count)" -eq 0 ]
}

@test "§6.8 trust: an index not built here is rebuilt, and §6.0 records HEAD" {
    printf 'garbage%.0s' {1..64} > "${CM}/index.db"
    head=$(git rev-parse HEAD)
    run bash "$SCRIPT" t
    [ "$status" -eq 0 ]
    grep -qE "— codemem=${head} graphify=" "$PROV"
}
