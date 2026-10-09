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

# Every hook script install.sh registers, read from its AA_MA_HOOKS table.
_installed_hook_scripts() {
    sed -n '/^AA_MA_HOOKS=(/,/^)/p' "${INSTALLER}" | grep -oE '[A-Za-z0-9_.-]+\.sh' | sort -u
}
_registered() { jq -r '[..|.command?|select(. != null)]|.[]' "${BATS_FAKE_HOME}/.claude/settings.json" | grep -c "/hooks/lib/$1" || true; }

@test "uninstall deregisters every hook install.sh registers (derived from AA_MA_HOOKS)" {
    _settings
    env HOME="${BATS_FAKE_HOME}" bash "${INSTALLER}" >/dev/null
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
    for h in $(_installed_hook_scripts); do [ "$(_registered "$h")" -eq 0 ] || { echo "still registered: $h"; return 1; }; done
}
