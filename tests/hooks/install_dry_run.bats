#!/usr/bin/env bats
# install_dry_run.bats — verifies scripts/install.sh --dry-run output for new skills.
#
# Acceptance criteria (M1.7):
#   - bash scripts/install.sh --dry-run announces the grill-with-docs symlink
#   - the operation is non-destructive (no real symlinks created)
#
# Install hygiene (code-conventions-impact M3.2): a command link left dangling into
# this repo is swept; a foreign symlink is recorded before it is replaced and put
# back by `uninstall.sh --restore`; uninstall deregisters every AA_MA_HOOKS row.

setup() {
    REPO_ROOT="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)"
    INSTALLER="${REPO_ROOT}/scripts/install.sh"
    [ -x "${INSTALLER}" ] || { echo "Installer not executable: ${INSTALLER}" >&2; return 1; }

    # Isolated HOME so the test is hermetic (no real ~/.claude mutations even on dry-run paths)
    BATS_FAKE_HOME="$(mktemp -d)"
    mkdir -p "${BATS_FAKE_HOME}/.claude"/{commands,skills,agents,rules,hooks/lib,docs,backups}
    export BATS_FAKE_HOME
}

teardown() {
    [ -n "${BATS_FAKE_HOME:-}" ] && rm -rf "${BATS_FAKE_HOME}"
    [ -n "${FAKE_REPO:-}" ] && rm -rf "${FAKE_REPO}"
    true  # why: a test that made no FAKE_REPO must not fail in teardown
}

# A throwaway copy of the parts of this repo install/uninstall read, for tests that
# corrupt the hook table or add a .worktrees/ checkout.
_fake_repo() {
    FAKE_REPO="$(mktemp -d)"
    cp -r "${REPO_ROOT}/scripts" "${REPO_ROOT}/claude-code" "${FAKE_REPO}/"
    mkdir -p "${FAKE_REPO}/docs" && cp -r "${REPO_ROOT}/docs/spec" "${FAKE_REPO}/docs/"
}

@test "install.sh --dry-run announces grill-with-docs symlink" {
    run env HOME="${BATS_FAKE_HOME}" bash "${INSTALLER}" --dry-run
    [ "${status}" -eq 0 ]
    [[ "${output}" == *"Would symlink:"*"skills/grill-with-docs"*"claude-code/skills/grill-with-docs"* ]]
}

@test "install.sh --dry-run target path is under the isolated HOME" {
    run env HOME="${BATS_FAKE_HOME}" bash "${INSTALLER}" --dry-run
    [ "${status}" -eq 0 ]
    [[ "${output}" == *"${BATS_FAKE_HOME}/.claude/skills/grill-with-docs"* ]]
}

@test "install.sh --dry-run creates no real symlinks under the isolated HOME" {
    run env HOME="${BATS_FAKE_HOME}" bash "${INSTALLER}" --dry-run
    [ "${status}" -eq 0 ]
    [ ! -L "${BATS_FAKE_HOME}/.claude/skills/grill-with-docs" ]
    [ ! -e "${BATS_FAKE_HOME}/.claude/skills/grill-with-docs" ]
}

@test "install.sh --dry-run announces all plugin skills (current disk count)" {
    run env HOME="${BATS_FAKE_HOME}" bash "${INSTALLER}" --dry-run
    [ "${status}" -eq 0 ]
    # Count "Would symlink: ... .claude/skills/<name> -> ... claude-code/skills/<name>" lines.
    # Compare to actual disk count rather than hardcoding — survives future
    # skill additions without doc-count-drift maintenance burden.
    skill_lines=$(echo "${output}" | grep -E "Would symlink: .+\.claude/skills/[^ ]+ -> .+/claude-code/skills/[^ ]+$" | wc -l)
    disk_count=$(ls -d "${REPO_ROOT}/claude-code/skills/"*/ | wc -l)
    [ "${skill_lines}" -eq "${disk_count}" ]
}

@test "install.sh --dry-run announces the hooks/lib/aa-ma-chart-guard.sh symlink (M5, L-005 pattern)" {
    run env HOME="${BATS_FAKE_HOME}" bash "${INSTALLER}" --dry-run
    [ "${status}" -eq 0 ]
    [[ "${output}" == *"Would symlink:"*".claude/hooks/lib/aa-ma-chart-guard.sh"*"claude-code/hooks/lib/aa-ma-chart-guard.sh"* ]]
}

# --- M3.2 install hygiene (real installs into the isolated HOME) -------------

_settings() { printf '{}\n' > "${BATS_FAKE_HOME}/.claude/settings.json"; }
# why: 2>/dev/null — the glob matches nothing when no manifest was written, which is "no rows"
_manifest_rows() { cat "${BATS_FAKE_HOME}"/.claude/backups/aa-ma-forge-*/foreign-symlinks.tsv 2>/dev/null; }

@test "install removes a command link that dangles into this repo, and leaves a foreign dangling one" {
    _settings
    ln -s "${REPO_ROOT}/claude-code/commands/gone-command.md" "${BATS_FAKE_HOME}/.claude/commands/gone-command.md"
    ln -s "${BATS_FAKE_HOME}/nowhere.md" "${BATS_FAKE_HOME}/.claude/commands/theirs.md"
    run env HOME="${BATS_FAKE_HOME}" bash "${INSTALLER}"
    [ "${status}" -eq 0 ]
    [ ! -L "${BATS_FAKE_HOME}/.claude/commands/gone-command.md" ]
    [ -L "${BATS_FAKE_HOME}/.claude/commands/theirs.md" ]
}

@test "install records a foreign symlink's destination before replacing it" {
    _settings
    mkdir -p "${BATS_FAKE_HOME}/elsewhere/grill-with-docs"
    ln -s "${BATS_FAKE_HOME}/elsewhere/grill-with-docs" "${BATS_FAKE_HOME}/.claude/skills/grill-with-docs"
    run env HOME="${BATS_FAKE_HOME}" bash "${INSTALLER}"
    [ "${status}" -eq 0 ]
    [ "$(_manifest_rows)" = "$(printf '%s\t%s' "${BATS_FAKE_HOME}/.claude/skills/grill-with-docs" "${BATS_FAKE_HOME}/elsewhere/grill-with-docs")" ]
    [ "$(readlink "${BATS_FAKE_HOME}/.claude/skills/grill-with-docs")" = "${REPO_ROOT}/claude-code/skills/grill-with-docs" ]
}

@test "--force still records a foreign symlink before replacing it" {
    _settings
    mkdir -p "${BATS_FAKE_HOME}/elsewhere/grill-with-docs"
    ln -s "${BATS_FAKE_HOME}/elsewhere/grill-with-docs" "${BATS_FAKE_HOME}/.claude/skills/grill-with-docs"
    run env HOME="${BATS_FAKE_HOME}" bash "${INSTALLER}" --force
    [ "${status}" -eq 0 ]
    [[ "$(_manifest_rows)" == *"${BATS_FAKE_HOME}/elsewhere/grill-with-docs" ]]
}

@test "--dry-run announces a foreign symlink and records nothing" {
    ln -s "${BATS_FAKE_HOME}/elsewhere" "${BATS_FAKE_HOME}/.claude/skills/grill-with-docs"
    run env HOME="${BATS_FAKE_HOME}" bash "${INSTALLER}" --dry-run
    [ "${status}" -eq 0 ]
    [[ "${output}" == *"Would record foreign symlink: ${BATS_FAKE_HOME}/.claude/skills/grill-with-docs"* ]]
    [ -z "$(_manifest_rows)" ]
}

@test "uninstall --restore puts a recorded foreign symlink back" {
    _settings
    mkdir -p "${BATS_FAKE_HOME}/elsewhere/grill-with-docs"
    ln -s "${BATS_FAKE_HOME}/elsewhere/grill-with-docs" "${BATS_FAKE_HOME}/.claude/skills/grill-with-docs"
    env HOME="${BATS_FAKE_HOME}" bash "${INSTALLER}" >/dev/null
    run env HOME="${BATS_FAKE_HOME}" bash "${REPO_ROOT}/scripts/uninstall.sh" --restore
    [ "${status}" -eq 0 ]
    [ "$(readlink "${BATS_FAKE_HOME}/.claude/skills/grill-with-docs")" = "${BATS_FAKE_HOME}/elsewhere/grill-with-docs" ]
}

# Every hook script install.sh registers, from the one table both scripts source.
_installed_hook_scripts() {
    # shellcheck source=/dev/null
    ( . "${REPO_ROOT}/scripts/lib/aa-ma-install-lib.sh" && printf '%s\n' "${AA_MA_HOOKS[@]}" ) \
        | grep -oE '[A-Za-z0-9_.-]+\.sh' | sort -u
}
# why: || true — grep -c prints 0 but exits 1 when nothing matches, and 0 is the answer
_registered() { jq -r '[..|.command?|select(. != null)]|.[]' "${HOME_UNDER_TEST:-${BATS_FAKE_HOME}}/.claude/settings.json" | grep -cF "/hooks/lib/$1" || true; }

@test "uninstall deregisters every hook install.sh registers (derived from AA_MA_HOOKS)" {
    _settings
    env HOME="${BATS_FAKE_HOME}" bash "${INSTALLER}" >/dev/null
    [ "$(_installed_hook_scripts | wc -l)" -ge 1 ]  # the loops below must not pass vacuously
    for h in $(_installed_hook_scripts); do [ "$(_registered "$h")" -ge 1 ]; done
    run env HOME="${BATS_FAKE_HOME}" bash "${REPO_ROOT}/scripts/uninstall.sh"
    [ "${status}" -eq 0 ]
    for h in $(_installed_hook_scripts); do [ "$(_registered "$h")" -eq 0 ] || { echo "still registered: $h"; return 1; }; done
}

@test "uninstall --restore also deregisters every AA_MA_HOOKS row" {
    _settings
    env HOME="${BATS_FAKE_HOME}" bash "${INSTALLER}" >/dev/null
    run env HOME="${BATS_FAKE_HOME}" bash "${REPO_ROOT}/scripts/uninstall.sh" --restore
    [ "${status}" -eq 0 ]
    [ -n "$(_installed_hook_scripts)" ]
    for h in $(_installed_hook_scripts); do [ "$(_registered "$h")" -eq 0 ] || { echo "still registered: $h"; return 1; }; done
}

@test "uninstall removes a link into this repo whose source directory is gone" {
    ln -s "${REPO_ROOT}/claude-code/no-such-dir/x.md" "${BATS_FAKE_HOME}/.claude/commands/x.md"
    run env HOME="${BATS_FAKE_HOME}" bash "${REPO_ROOT}/scripts/uninstall.sh"
    [ "${status}" -eq 0 ]
    [ ! -L "${BATS_FAKE_HOME}/.claude/commands/x.md" ]
}

@test "uninstall refuses a malformed hook table before removing anything" {
    _fake_repo
    sed -i 's/^AA_MA_HOOKS=($/AA_MA_HOOKS=(\n    "not a row"/' "${FAKE_REPO}/scripts/lib/aa-ma-install-lib.sh"
    ln -s "${FAKE_REPO}/claude-code/skills/grill-with-docs" "${BATS_FAKE_HOME}/.claude/skills/grill-with-docs"
    run env HOME="${BATS_FAKE_HOME}" bash "${FAKE_REPO}/scripts/uninstall.sh"
    [ "${status}" -eq 1 ]
    [[ "${output}" == *"not a row"* ]]
    [ -L "${BATS_FAKE_HOME}/.claude/skills/grill-with-docs" ]
}

@test "uninstall --restore recreates a foreign link whose parent directory is gone" {
    mkdir -p "${BATS_FAKE_HOME}/.claude/backups/aa-ma-forge-20260101-000000"
    printf '%s\t%s\n' "${BATS_FAKE_HOME}/.claude/commands/x.md" "${BATS_FAKE_HOME}/elsewhere.md" \
        > "${BATS_FAKE_HOME}/.claude/backups/aa-ma-forge-20260101-000000/foreign-symlinks.tsv"
    rmdir "${BATS_FAKE_HOME}/.claude/commands"
    run env HOME="${BATS_FAKE_HOME}" bash "${REPO_ROOT}/scripts/uninstall.sh" --restore
    [ "${status}" -eq 0 ]
    [ "$(readlink "${BATS_FAKE_HOME}/.claude/commands/x.md")" = "${BATS_FAKE_HOME}/elsewhere.md" ]
}

@test "uninstall --restore --dry-run says it would restore a foreign link our link now occupies" {
    _settings
    mkdir -p "${BATS_FAKE_HOME}/elsewhere/grill-with-docs"
    ln -s "${BATS_FAKE_HOME}/elsewhere/grill-with-docs" "${BATS_FAKE_HOME}/.claude/skills/grill-with-docs"
    env HOME="${BATS_FAKE_HOME}" bash "${INSTALLER}" >/dev/null
    run env HOME="${BATS_FAKE_HOME}" bash "${REPO_ROOT}/scripts/uninstall.sh" --restore --dry-run
    [ "${status}" -eq 0 ]
    [[ "${output}" == *"Would restore foreign symlink: ${BATS_FAKE_HOME}/.claude/skills/grill-with-docs"* ]]
}

@test "uninstall --restore logs and skips a manifest row outside ~/.claude" {
    mkdir -p "${BATS_FAKE_HOME}/.claude/backups/aa-ma-forge-20260101-000000"
    printf '%s\t%s\n' "${BATS_FAKE_HOME}/outside" "${BATS_FAKE_HOME}/x" \
        > "${BATS_FAKE_HOME}/.claude/backups/aa-ma-forge-20260101-000000/foreign-symlinks.tsv"
    run env HOME="${BATS_FAKE_HOME}" bash "${REPO_ROOT}/scripts/uninstall.sh" --restore
    [ "${status}" -eq 0 ]
    [[ "${output}" == *"Skipping manifest row"*"${BATS_FAKE_HOME}/outside"* ]]
    [ ! -e "${BATS_FAKE_HOME}/outside" ] && [ ! -L "${BATS_FAKE_HOME}/outside" ]
}

@test "uninstall deregisters hooks when HOME holds regex metacharacters" {
    HOME_UNDER_TEST="${BATS_FAKE_HOME}/h+(x"
    mkdir -p "${HOME_UNDER_TEST}/.claude"/{skills,agents,rules,hooks/lib,docs}
    printf '{}\n' > "${HOME_UNDER_TEST}/.claude/settings.json"
    env HOME="${HOME_UNDER_TEST}" bash "${INSTALLER}" >/dev/null
    [ "$(_registered aa-ma-session-start.sh)" -ge 1 ]
    run env HOME="${HOME_UNDER_TEST}" bash "${REPO_ROOT}/scripts/uninstall.sh"
    [ "${status}" -eq 0 ]
    [ -n "$(_installed_hook_scripts)" ]
    for h in $(_installed_hook_scripts); do [ "$(_registered "$h")" -eq 0 ] || { echo "still registered: $h"; return 1; }; done
}

@test "install treats a relative link into this repo as ours, not foreign" {
    _settings
    ln -s "$(realpath --relative-to="${BATS_FAKE_HOME}/.claude/skills" "${REPO_ROOT}/claude-code/skills/grill-with-docs")" \
        "${BATS_FAKE_HOME}/.claude/skills/grill-with-docs"
    run env HOME="${BATS_FAKE_HOME}" bash "${INSTALLER}"
    [ "${status}" -eq 0 ]
    [ -z "$(_manifest_rows)" ]
}

@test "install records a link into another checkout under .worktrees/ as foreign" {
    _settings
    _fake_repo
    mkdir -p "${FAKE_REPO}/.worktrees/other/claude-code/skills/grill-with-docs"
    ln -s "${FAKE_REPO}/.worktrees/other/claude-code/skills/grill-with-docs" "${BATS_FAKE_HOME}/.claude/skills/grill-with-docs"
    run env HOME="${BATS_FAKE_HOME}" bash "${FAKE_REPO}/scripts/install.sh"
    [ "${status}" -eq 0 ]
    [[ "$(_manifest_rows)" == *"/.worktrees/other/claude-code/skills/grill-with-docs" ]]
}

@test "install runs when ~/.claude/commands does not exist" {
    _settings
    rmdir "${BATS_FAKE_HOME}/.claude/commands"
    run env HOME="${BATS_FAKE_HOME}" bash "${INSTALLER}"
    [ "${status}" -eq 0 ]
}

@test "uninstall --restore refuses a manifest row that climbs out of ~/.claude with .." {
    mkdir -p "${BATS_FAKE_HOME}/.claude/backups/aa-ma-forge-20260101-000000"
    printf '%s\t%s\n' "${BATS_FAKE_HOME}/.claude/../evil/link" "${BATS_FAKE_HOME}/x" \
        > "${BATS_FAKE_HOME}/.claude/backups/aa-ma-forge-20260101-000000/foreign-symlinks.tsv"
    run env HOME="${BATS_FAKE_HOME}" bash "${REPO_ROOT}/scripts/uninstall.sh" --restore
    [ "${status}" -eq 0 ]
    [[ "${output}" == *"Skipping manifest row"* ]]
    [ ! -e "${BATS_FAKE_HOME}/evil" ]
}

@test "uninstall warns and carries on when it cannot rewrite settings.json" {
    _settings
    env HOME="${BATS_FAKE_HOME}" bash "${INSTALLER}" >/dev/null
    chmod a-w "${BATS_FAKE_HOME}/.claude"   # the temp file beside settings.json cannot be created
    run env HOME="${BATS_FAKE_HOME}" bash "${REPO_ROOT}/scripts/uninstall.sh"
    chmod u+w "${BATS_FAKE_HOME}/.claude"
    [ "${status}" -eq 0 ]
    [[ "${output}" == *"Could not update"* ]]
    [[ "${output}" == *"Uninstall Summary"* ]]
}

@test "install and uninstall keep settings.json's file mode" {
    _settings
    chmod 600 "${BATS_FAKE_HOME}/.claude/settings.json"
    env HOME="${BATS_FAKE_HOME}" bash "${INSTALLER}" >/dev/null
    [ "$(stat -c %a "${BATS_FAKE_HOME}/.claude/settings.json")" = 600 ]
    env HOME="${BATS_FAKE_HOME}" bash "${REPO_ROOT}/scripts/uninstall.sh" >/dev/null
    [ "$(stat -c %a "${BATS_FAKE_HOME}/.claude/settings.json")" = 600 ]
}

@test "install and uninstall work when invoked through a symlink" {
    _settings
    mkdir -p "${BATS_FAKE_HOME}/bin"
    ln -s "${REPO_ROOT}/scripts/install.sh" "${BATS_FAKE_HOME}/bin/aa-install"
    ln -s "${REPO_ROOT}/scripts/uninstall.sh" "${BATS_FAKE_HOME}/bin/aa-uninstall"
    run env HOME="${BATS_FAKE_HOME}" bash "${BATS_FAKE_HOME}/bin/aa-install"
    [ "${status}" -eq 0 ]
    [ "$(readlink "${BATS_FAKE_HOME}/.claude/skills/aa-ma-plan")" = "${REPO_ROOT}/claude-code/skills/aa-ma-plan" ]
    run env HOME="${BATS_FAKE_HOME}" bash "${BATS_FAKE_HOME}/bin/aa-uninstall"
    [ "${status}" -eq 0 ]
    [ ! -e "${BATS_FAKE_HOME}/.claude/skills/aa-ma-plan" ]
}

# A chmod that, like BSD/macOS chmod, has no --reference option.
_bsd_chmod_on_path() {
    mkdir -p "${BATS_FAKE_HOME}/shim"
    printf '#!/usr/bin/env bash\nfor a in "$@"; do [[ "$a" == --reference* ]] && { echo "chmod: illegal option -- -" >&2; exit 1; }; done\nexec /bin/chmod "$@"\n' \
        > "${BATS_FAKE_HOME}/shim/chmod"
    /bin/chmod +x "${BATS_FAKE_HOME}/shim/chmod"
    SHIM_PATH="${BATS_FAKE_HOME}/shim:${PATH}"
}

@test "install and uninstall work with a BSD chmod (no --reference) and keep a 0600 settings.json" {
    _settings
    chmod 600 "${BATS_FAKE_HOME}/.claude/settings.json"
    _bsd_chmod_on_path
    run env PATH="${SHIM_PATH}" HOME="${BATS_FAKE_HOME}" bash "${INSTALLER}"
    [ "${status}" -eq 0 ]
    [ "$(_registered aa-ma-session-start.sh)" -ge 1 ]
    [ "$(stat -c %a "${BATS_FAKE_HOME}/.claude/settings.json")" = 600 ]
    run env PATH="${SHIM_PATH}" HOME="${BATS_FAKE_HOME}" bash "${REPO_ROOT}/scripts/uninstall.sh"
    [ "${status}" -eq 0 ]
    for h in $(_installed_hook_scripts); do [ "$(_registered "$h")" -eq 0 ] || { echo "still registered: $h"; return 1; }; done
    [ "$(stat -c %a "${BATS_FAKE_HOME}/.claude/settings.json")" = 600 ]
    ! ls "${BATS_FAKE_HOME}/.claude/"settings.json.tmp.* 2>/dev/null
}

@test "uninstall needs bash 4 only under --restore (no declare -A on the default path)" {
    # stock macOS bash is 3.2: associative arrays must stay inside the --restore branch
    [ "$(grep -cE '^[[:space:]]*declare -A' "${REPO_ROOT}/scripts/uninstall.sh")" -eq 1 ]
    grep -n 'declare -A RESTORED' "${REPO_ROOT}/scripts/uninstall.sh"
}

@test "a second install registers nothing new when HOME holds regex metacharacters" {
    HOME_UNDER_TEST="${BATS_FAKE_HOME}/h+(x"
    mkdir -p "${HOME_UNDER_TEST}/.claude"/{skills,agents,rules,hooks/lib,docs}
    printf '{}\n' > "${HOME_UNDER_TEST}/.claude/settings.json"
    env HOME="${HOME_UNDER_TEST}" bash "${INSTALLER}" >/dev/null
    first=$(jq '[..|.command?|select(. != null)]|length' "${HOME_UNDER_TEST}/.claude/settings.json")
    env HOME="${HOME_UNDER_TEST}" bash "${INSTALLER}" >/dev/null
    second=$(jq '[..|.command?|select(. != null)]|length' "${HOME_UNDER_TEST}/.claude/settings.json")
    [ "${first}" -ge 1 ] && [ "${first}" -eq "${second}" ]
}

@test "uninstall deregisters even when settings.json has a hook group without a hooks array" {
    _settings
    env HOME="${BATS_FAKE_HOME}" bash "${INSTALLER}" >/dev/null
    jq '.hooks.SessionStart += [{"matcher": "x"}]' "${BATS_FAKE_HOME}/.claude/settings.json" > "${BATS_FAKE_HOME}/s.json"
    mv "${BATS_FAKE_HOME}/s.json" "${BATS_FAKE_HOME}/.claude/settings.json"
    run env HOME="${BATS_FAKE_HOME}" bash "${REPO_ROOT}/scripts/uninstall.sh"
    [ "${status}" -eq 0 ]
    [ "$(_registered aa-ma-session-start.sh)" -eq 0 ]
}
