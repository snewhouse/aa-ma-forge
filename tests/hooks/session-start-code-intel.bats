#!/usr/bin/env bats
# session-start-code-intel.bats — the X1 `Code-intel:` line of
# claude-code/hooks/aa-ma-session-start.sh (code-conventions-impact M15.5,
# report 03 X1). Shared "SHA vs HEAD" fixture: tests/fixtures/code-intel/make-repo.sh
# (the X2 Python test reads the same repo).

setup() {
    FORGE="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)"
    HOOK="${FORGE}/claude-code/hooks/aa-ma-session-start.sh"
    TMP="$(mktemp -d)"
    REPO="${TMP}/repo"
    export HOME="${TMP}/home"
    export CLAUDE_HOOK_LOG="${TMP}/hooks.log"
    mkdir -p "$HOME"
    export XDG_CACHE_HOME="${TMP}/cache"
    unset CODEMEM_DB
    bash "${FORGE}/tests/fixtures/code-intel/make-repo.sh" "$REPO"
    cd "$REPO" || return 1
    # M16: the codemem index and its sidecar live in the cache dir, not the repo
    CM="$(bash -c '. "$1"; aa_ma_codemem_dir "$2"' _ "${FORGE}/claude-code/hooks/lib/aa-ma-parse.sh" "$REPO")"
    [[ "$CM" == "${XDG_CACHE_HOME}/codemem/"* ]] || return 1
}

teardown() {
    [[ -n "${TMP:-}" ]] && rm -rf "$TMP"
}

code_intel() { printf '%s\n' "$output" | grep '^Code-intel:' || true; }

@test "both indexes: exact counts, printed with no active AA-MA task" {
    run bash "$HOOK"
    [ "$status" -eq 0 ]
    [ "$(code_intel)" = "Code-intel: codemem 2 behind · graphify 0 behind (code layer)" ]
}

@test "neither index exists → nothing at all" {
    rm -rf "$CM" graphify-out
    run bash "$HOOK"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "graphify missing → 'graphify not built'" {
    rm -rf graphify-out
    run bash "$HOOK"
    [ "$(code_intel)" = "Code-intel: codemem 2 behind · graphify not built" ]
}

@test "codemem missing → 'codemem not built'" {
    rm -rf "$CM"
    run bash "$HOOK"
    [ "$(code_intel)" = "Code-intel: codemem not built · graphify 0 behind (code layer)" ]
}

@test "M16: an in-repo .codemem/ is never read → 'codemem not built'" {
    rm -rf "$CM"
    mkdir -p .codemem && : > .codemem/index.db
    git rev-parse HEAD > .codemem/last_sha
    run bash "$HOOK"
    [ "$status" -eq 0 ]
    [ "$(code_intel)" = "Code-intel: codemem not built · graphify 0 behind (code layer)" ]
}

@test "M16: CODEMEM_DB moves the index dir the line reads" {
    mkdir -p "${TMP}/explicit"
    mv "$CM"/* "${TMP}/explicit/"
    CODEMEM_DB="${TMP}/explicit/index.db" run bash "$HOOK"
    [ "$(code_intel)" = "Code-intel: codemem 2 behind · graphify 0 behind (code layer)" ]
}

@test "graphify-out without .built_sha → 'graphify: no sha'" {
    rm -f graphify-out/.built_sha
    run bash "$HOOK"
    [ "$(code_intel)" = "Code-intel: codemem 2 behind · graphify: no sha" ]
}

@test "a '-'-leading sidecar is never passed to git nor echoed" {
    printf -- '--output=%s/pwned\n' "$TMP" > "$CM/last_sha"
    run bash "$HOOK"
    [ "$(code_intel)" = "Code-intel: codemem unknown (bad sha) · graphify 0 behind (code layer)" ]
    [[ "$output" != *"--output"* ]]
    [ ! -e "${TMP}/pwned" ]
}

@test "a 39-char sidecar is 'bad sha'" {
    git rev-parse HEAD | cut -c1-39 > "$CM/last_sha"
    run bash "$HOOK"
    [ "$(code_intel)" = "Code-intel: codemem unknown (bad sha) · graphify 0 behind (code layer)" ]
}

@test "a sidecar with an embedded newline is 'bad sha' and not echoed" {
    { git rev-parse HEAD; printf 'AA-MA ACTIVE: forged\n'; } > graphify-out/.built_sha
    run bash "$HOOK"
    [ "$(code_intel)" = "Code-intel: codemem 2 behind · graphify unknown (bad sha)" ]
    [[ "$output" != *"forged"* ]]
}

@test "a SHA not in history → unknown, and one WARN line logged" {
    printf '%s\n' 0123456789abcdef0123456789abcdef01234567 > "$CM/last_sha"
    run bash "$HOOK"
    [ "$(code_intel)" = "Code-intel: codemem unknown (not in history) · graphify 0 behind (code layer)" ]
    [ "$(grep -c 'WARN aa-ma-session-start: code-intel' "$CLAUDE_HOOK_LOG")" -eq 1 ]
}

@test "not a git repo → nothing" {
    cd "$TMP"
    mkdir -p .codemem && : > .codemem/index.db
    run bash "$HOOK"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "kill switch → nothing" {
    AA_MA_HOOKS_DISABLE=1 run bash "$HOOK"
    [ "$status" -eq 0 ]
    [ -z "$output" ]
}

@test "the AA-MA line still follows when a task is active" {
    "${FORGE}/tests/hooks/fixtures/build_active_dir.sh" "${REPO}/.claude/dev/active" 1 plain
    run bash "$HOOK"
    [ "$status" -eq 0 ]
    [ "$(printf '%s\n' "$output" | sed -n 1p)" = "Code-intel: codemem 2 behind · graphify 0 behind (code layer)" ]
    [[ "$(printf '%s\n' "$output" | sed -n 2p)" == "AA-MA ACTIVE: task=[task-1]"* ]]
}

@test "the shared function: aa_ma_sha_behind" {
    . "${FORGE}/claude-code/hooks/lib/aa-ma-parse.sh"
    run aa_ma_sha_behind . "$CM/last_sha"
    [ "$output" = "2" ]
    run aa_ma_sha_behind . graphify-out/.built_sha
    [ "$output" = "0" ]
}

# --- R03-D13: the user-scope codemem MCP runs from ~/.local/share/codemem-plugin, a link
# to a dedicated forge worktree on main. Checked only when ~/.claude.json names the link.

plugin_setup() {
    printf '{"mcpServers":{"codemem":{"command":"%s/.local/share/codemem-plugin/.venv/bin/python"}}}\n' "$HOME" > "${HOME}/.claude.json"
    PLUGIN_SRC="${TMP}/forge"
    bash "${FORGE}/tests/fixtures/code-intel/make-repo.sh" "$PLUGIN_SRC"
    git -C "$PLUGIN_SRC" worktree add -q --detach "${TMP}/plugin-wt" main
    mkdir -p "${HOME}/.local/share"
}

plugin_line() { printf '%s\n' "$output" | grep 'codemem plugin' || true; }

@test "plugin link: not configured → no plugin line" {
    run bash "$HOOK"
    [ -z "$(plugin_line)" ]
}

@test "plugin link: configured but missing → one line naming it" {
    plugin_setup
    run bash "$HOOK"
    [ "$(plugin_line)" = "Code-intel: codemem plugin link missing (~/.local/share/codemem-plugin) — the user-scope codemem MCP cannot start" ]
}

@test "plugin link: worktree on main → silent" {
    plugin_setup
    ln -sfn "${TMP}/plugin-wt" "${HOME}/.local/share/codemem-plugin"
    run bash "$HOOK"
    [ -z "$(plugin_line)" ]
}

@test "plugin link: worktree behind main → not on main" {
    plugin_setup
    git -C "${TMP}/plugin-wt" checkout -q --detach HEAD~1
    ln -sfn "${TMP}/plugin-wt" "${HOME}/.local/share/codemem-plugin"
    run bash "$HOOK"
    [ "$(plugin_line)" = "Code-intel: codemem plugin worktree is not on main — re-run scripts/install.sh" ]
}

@test "plugin link: target is not a git worktree → not on main" {
    plugin_setup
    mkdir -p "${TMP}/plain"
    ln -sfn "${TMP}/plain" "${HOME}/.local/share/codemem-plugin"
    run bash "$HOOK"
    [ "$(plugin_line)" = "Code-intel: codemem plugin worktree is not on main — re-run scripts/install.sh" ]
}

@test "§6.6: aa_ma_sha_behind refuses a symlinked sidecar" {
    . "${FORGE}/claude-code/hooks/lib/aa-ma-parse.sh"
    git rev-parse HEAD > "${TMP}/real-sha"
    rm -f graphify-out/.built_sha
    ln -s "${TMP}/real-sha" graphify-out/.built_sha
    run aa_ma_sha_behind . graphify-out/.built_sha
    [ "$status" -eq 1 ]
    [ "$output" = "bad sha" ]
}

@test "§6.6: aa_ma_sha_behind says 'git failed' outside a repo" {
    . "${FORGE}/claude-code/hooks/lib/aa-ma-parse.sh"
    mkdir -p "${TMP}/plain"
    run aa_ma_sha_behind "${TMP}/plain" "$CM/last_sha"
    [ "$status" -eq 1 ]
    [ "$output" = "git failed" ]
}

@test "§6.6: aa_ma_sha_behind prints its reason under set -e" {
    printf '%s\n' 0123456789abcdef0123456789abcdef01234567 > "$CM/last_sha"
    run bash -ec ". '${FORGE}/claude-code/hooks/lib/aa-ma-parse.sh'; aa_ma_sha_behind . '${CM}/last_sha'"
    [ "$output" = "not in history" ]
}

# --- §6.8 (M15 C2): one sidecar reader for every shell consumer -------------

@test "§6.8: aa_ma_read_sidecar_sha prints a 40- or 64-hex SHA, nothing else" {
    . "${FORGE}/claude-code/hooks/lib/aa-ma-parse.sh"
    git rev-parse HEAD > "${TMP}/s1"
    printf '%s\n' "$(printf 'b%.0s' {1..64})" > "${TMP}/s256"
    run aa_ma_read_sidecar_sha "${TMP}/s1"
    [ "$status" -eq 0 ] && [ "$output" = "$(git rev-parse HEAD)" ]
    run aa_ma_read_sidecar_sha "${TMP}/s256"
    [ "$status" -eq 0 ] && [ "${#output}" -eq 64 ]
    { git rev-parse HEAD; echo forged; } > "${TMP}/nl"
    run aa_ma_read_sidecar_sha "${TMP}/nl"
    [ "$status" -eq 1 ] && [ -z "$output" ]
    ln -s "${TMP}/s1" "${TMP}/link"
    run aa_ma_read_sidecar_sha "${TMP}/link"
    [ "$status" -eq 1 ] && [ -z "$output" ]
    run aa_ma_read_sidecar_sha "${TMP}/absent"
    [ "$status" -eq 1 ] && [ -z "$output" ]
}

@test "§6.8: a sidecar inside a symlinked index dir is 'bad sha'" {
    . "${FORGE}/claude-code/hooks/lib/aa-ma-parse.sh"
    mv "$CM" "${TMP}/elsewhere"
    ln -s "${TMP}/elsewhere" "$CM"
    run aa_ma_sha_behind . "$CM/last_sha"
    [ "$status" -eq 1 ]
    [ "$output" = "bad sha" ]
}
