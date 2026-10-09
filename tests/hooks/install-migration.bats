#!/usr/bin/env bats
# install-migration.bats — scripts/install.sh / uninstall.sh against a fake HOME seeded
# like a machine that predates code-conventions-impact M2: the 5 doctrine skills and
# hooks/lib/ruff-format.sh are real files, and settings.json already registers the hook.

MIGRATED=(logging-and-comments python-quality-gates llm-output-safety secrets-management bash-defensive-patterns)

setup() {
    REPO_ROOT="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)"
    WORK="$(mktemp -d "${BATS_TMPDIR}/install-migration.XXXXXX")"
    export HOME="${WORK}/home"
    CH="${HOME}/.claude"
    mkdir -p "${CH}"/{commands,skills,agents,rules,hooks/lib,docs}
    for s in "${MIGRATED[@]}"; do
        mkdir -p "${CH}/skills/${s}"
        printf 'old %s\n' "$s" > "${CH}/skills/${s}/SKILL.md"
    done
    printf '#!/usr/bin/env bash\n# old hook\n' > "${CH}/hooks/lib/ruff-format.sh"
    # Same command string the live settings.json carries (bash <CLAUDE_HOME>/hooks/lib/…).
    jq -n --arg cmd "bash ${CH}/hooks/lib/ruff-format.sh" '{hooks: {PostToolUse: [
        {matcher: "Edit|Write", hooks: [{type: "command", command: $cmd, timeout: 10}]}]}}' \
        > "${CH}/settings.json"
}

teardown() { rm -rf "$WORK"; }

ruff_count() {
    jq '[..|.command?|select(. != null and test("ruff-format"))]|length' "${CH}/settings.json"
}

@test "--dry-run lists the 5 skill links, the hook link and their backups" {
    run "${REPO_ROOT}/scripts/install.sh" --dry-run
    [ "$status" -eq 0 ]
    for s in "${MIGRATED[@]}"; do
        [[ "$output" == *"Would symlink: ${CH}/skills/${s} -> ${REPO_ROOT}/claude-code/skills/${s}"* ]]
        [[ "$output" == *"Would backup: ${CH}/skills/${s} -> "* ]]
    done
    [[ "$output" == *"Would symlink: ${CH}/hooks/lib/ruff-format.sh -> ${REPO_ROOT}/claude-code/hooks/ruff-format.sh"* ]]
    [[ "$output" == *"Would backup: ${CH}/hooks/lib/ruff-format.sh -> "* ]]
    [ -d "${CH}/skills/logging-and-comments" ] && [ ! -L "${CH}/skills/logging-and-comments" ]
}

@test "install: 5 skills + hook link into the repo; old real files are backed up; one ruff-format entry" {
    run "${REPO_ROOT}/scripts/install.sh"
    [ "$status" -eq 0 ]
    for s in "${MIGRATED[@]}"; do
        [ "$(readlink -f "${CH}/skills/${s}")" = "${REPO_ROOT}/claude-code/skills/${s}" ]
        grep -qx "old ${s}" "${CH}"/backups/aa-ma-forge-*/skills/"${s}"/SKILL.md
    done
    [ "$(readlink -f "${CH}/hooks/lib/ruff-format.sh")" = "${REPO_ROOT}/claude-code/hooks/ruff-format.sh" ]
    grep -q "old hook" "${CH}"/backups/aa-ma-forge-*/hooks/lib/ruff-format.sh
    [ "$(ruff_count)" -eq 1 ]
}

@test "fresh settings: ruff-format registered once as PostToolUse Edit|Write; a re-run adds nothing" {
    echo '{}' > "${CH}/settings.json"
    run "${REPO_ROOT}/scripts/install.sh"
    [ "$status" -eq 0 ]
    [ "$(ruff_count)" -eq 1 ]
    run jq -r '.hooks.PostToolUse[] | select(.hooks[].command | test("ruff-format")) | .matcher' "${CH}/settings.json"
    [ "$output" = "Edit|Write" ]
    run "${REPO_ROOT}/scripts/install.sh"
    [ "$status" -eq 0 ]
    [ "$(ruff_count)" -eq 1 ]
}

@test "settings.json is backed up to a timestamped file, not settings.json.bak" {
    echo '{}' > "${CH}/settings.json"
    run "${REPO_ROOT}/scripts/install.sh"
    [ "$status" -eq 0 ]
    [ ! -e "${CH}/settings.json.bak" ]
    run jq -c . "${CH}"/backups/settings-aa-ma-forge-*.json
    [ "$output" = "{}" ]
}

@test "a later settings-only backup never hides the real-file backup from uninstall --restore" {
    "${REPO_ROOT}/scripts/install.sh" >/dev/null
    sleep 1   # why: backup names have 1 s resolution; a second run must sort after the first
    # Drop the ruff registration so the next install mutates (and backs up) settings.json only.
    jq 'del(.hooks.PostToolUse[] | select(.hooks[].command | test("ruff-format")))' \
        "${CH}/settings.json" > "${WORK}/s.json" && mv "${WORK}/s.json" "${CH}/settings.json"
    "${REPO_ROOT}/scripts/install.sh" >/dev/null
    run "${REPO_ROOT}/scripts/uninstall.sh" --restore
    [ "$status" -eq 0 ]
    grep -qx "old secrets-management" "${CH}/skills/secrets-management/SKILL.md"
}

@test "--force still backs up a real directory before replacing it" {
    run "${REPO_ROOT}/scripts/install.sh" --force
    [ "$status" -eq 0 ]
    [ -L "${CH}/skills/secrets-management" ]
    grep -qx "old secrets-management" "${CH}"/backups/aa-ma-forge-*/skills/secrets-management/SKILL.md
}

@test "--force says it skips file backups even when it backs up a real directory" {
    run "${REPO_ROOT}/scripts/install.sh" --force
    [ "$status" -eq 0 ]
    [[ "$output" == *"Skipping file backups (--force flag set)"* ]]
}

@test "--restore takes each backed-up target whole from its newest backup (no per-file merge)" {
    mkdir -p "${CH}/backups/aa-ma-forge-20260101-000000/skills/x" "${CH}/backups/aa-ma-forge-20260102-000000/skills/x"
    printf 'old\n' > "${CH}/backups/aa-ma-forge-20260101-000000/skills/x/SKILL.md"
    printf 'stale\n' > "${CH}/backups/aa-ma-forge-20260101-000000/skills/x/gone.md"
    printf 'new\n' > "${CH}/backups/aa-ma-forge-20260102-000000/skills/x/SKILL.md"
    run "${REPO_ROOT}/scripts/uninstall.sh" --restore
    [ "$status" -eq 0 ]
    [ "$(cat "${CH}/skills/x/SKILL.md")" = "new" ]
    [ ! -e "${CH}/skills/x/gone.md" ]
}

@test "uninstall removes the skill links and the ruff-format registration" {
    "${REPO_ROOT}/scripts/install.sh" >/dev/null
    run "${REPO_ROOT}/scripts/uninstall.sh"
    [ "$status" -eq 0 ]
    for s in "${MIGRATED[@]}"; do [ ! -e "${CH}/skills/${s}" ]; done
    [ ! -e "${CH}/hooks/lib/ruff-format.sh" ]
    [ "$(ruff_count)" -eq 0 ]
}
