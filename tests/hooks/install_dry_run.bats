#!/usr/bin/env bats
# install_dry_run.bats — verifies scripts/install.sh --dry-run output for new skills.
#
# Acceptance criteria (M1.7):
#   - bash scripts/install.sh --dry-run announces the grill-with-docs symlink
#   - the operation is non-destructive (no real symlinks created)
#
# Pattern can be extended in M2 for prototype + write-a-skill.

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

@test "install.sh --dry-run announces all 14 plugin skills (M1 post-fork count)" {
    run env HOME="${BATS_FAKE_HOME}" bash "${INSTALLER}" --dry-run
    [ "${status}" -eq 0 ]
    # Count "Would symlink: ... .claude/skills/<name> -> ... claude-code/skills/<name>" lines.
    skill_lines=$(echo "${output}" | grep -E "Would symlink: .+\.claude/skills/[^ ]+ -> .+/claude-code/skills/[^ ]+$" | wc -l)
    [ "${skill_lines}" -eq 14 ]
}
