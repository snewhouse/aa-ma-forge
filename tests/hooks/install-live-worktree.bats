#!/usr/bin/env bats
# install-live-worktree.bats — scripts/install.sh links ~/.claude into the live worktree
# (code-conventions-impact 10.0, ADR-0025 amending D7).
#
# The live worktree is the one ~/.local/share/codemem-plugin links to: a detached worktree
# of the forge kept on main by install.sh. With it in place, every ~/.claude link (and the
# --wire-git-hook path) resolves into it, so a branch checked out in the forge checkout is
# never live. Without it, install.sh links into the checkout it runs from, as before.
# Same throwaway-forge fixture as install-codemem-plugin.bats.

bats_require_minimum_version 1.5.0

setup() {
    REAL="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)"
    WORK="$(mktemp -d "${BATS_TMPDIR}/install-live-wt.XXXXXX")"
    WORK="$(cd "$WORK" && pwd -P)"
    FORGE="${WORK}/forge"
    mkdir -p "${FORGE}/docs"
    cp -a "${REAL}/scripts" "${REAL}/claude-code" "${FORGE}/"
    cp -a "${REAL}/docs/spec" "${FORGE}/docs/"
    git -C "$FORGE" init -q -b main
    git -C "$FORGE" -c user.name=t -c user.email=t@t -c commit.gpgsign=false add -A
    git -C "$FORGE" -c user.name=t -c user.email=t@t -c commit.gpgsign=false commit -q -m one
    git -C "$FORGE" worktree add -q --detach "${WORK}/wt" main
    export HOME="${WORK}/home"
    mkdir -p "${HOME}/.claude"/{skills,agents,rules,hooks/lib,docs} "${HOME}/.local/share"
    printf '{}\n' > "${HOME}/.claude/settings.json"
    STUBS="${WORK}/stubs"
    mkdir -p "$STUBS"
    printf '#!/usr/bin/env bash\nexit 0\n' > "${STUBS}/uv"
    chmod +x "${STUBS}/uv"
    export PATH="${STUBS}:${PATH}"
    LINK="${HOME}/.local/share/codemem-plugin"
}

teardown() { rm -rf "$WORK"; }

# every ~/.claude link the installer made, resolved
links() { find "${HOME}/.claude" -type l -exec readlink -f {} \; ; }

@test "with a live worktree, every ~/.claude link resolves into it" {
    ln -sfn "${WORK}/wt" "$LINK"
    run "${FORGE}/scripts/install.sh"
    [ "$status" -eq 0 ]
    [ -n "$(links)" ]
    [ -z "$(links | grep -v "^${WORK}/wt/")" ]
}

@test "with a live worktree, settings.json hook commands name no path in the checkout" {
    ln -sfn "${WORK}/wt" "$LINK"
    run "${FORGE}/scripts/install.sh"
    [ "$status" -eq 0 ]
    run ! grep -qF "${FORGE}/" "${HOME}/.claude/settings.json"
}

@test "re-pointing links from the checkout to the live worktree records nothing as foreign" {
    run "${FORGE}/scripts/install.sh"
    [ "$status" -eq 0 ]
    [ -n "$(links | grep "^${FORGE}/")" ]
    ln -sfn "${WORK}/wt" "$LINK"
    run "${FORGE}/scripts/install.sh"
    [ "$status" -eq 0 ]
    [[ "$output" != *"Replacing foreign symlink"* ]]
    [ -z "$(find "${HOME}/.claude/backups" -name foreign-symlinks.tsv -size +0 2>/dev/null)" ]
    [ -z "$(links | grep -v "^${WORK}/wt/")" ]
}

@test "--wire-git-hook runs the live worktree's post-commit, not the checkout's" {
    ln -sfn "${WORK}/wt" "$LINK"
    run "${FORGE}/scripts/install.sh" --wire-git-hook
    [ "$status" -eq 0 ]
    hook="$(git -C "$FORGE" rev-parse --path-format=absolute --git-common-dir)/hooks/post-commit"
    grep -qF "${WORK}/wt/claude-code/codemem/hooks/post-commit.sh" "$hook"
    run ! grep -qF "${FORGE}/claude-code" "$hook"
}

@test "a dirty live worktree aborts the install before any link changes (fail closed)" {
    printf 'local edit\n' >> "${WORK}/wt/scripts/install.sh"
    ln -sfn "${WORK}/wt" "$LINK"
    run "${FORGE}/scripts/install.sh"
    [ "$status" -eq 1 ]
    [[ "$output" == *"uncommitted changes"* ]]
    [ -z "$(links)" ]
}

@test "a failed live-worktree refresh aborts the install before any link changes" {
    printf '#!/usr/bin/env bash\nexit 1\n' > "${STUBS}/uv"
    ln -sfn "${WORK}/wt" "$LINK"
    run "${FORGE}/scripts/install.sh"
    [ "$status" -eq 1 ]
    [[ "$output" == *"refresh failed"* ]]
    [ -z "$(links)" ]
}

@test "no jq → the install stops before the checkout-link sweep; existing links survive" {
    run "${FORGE}/scripts/install.sh"
    [ "$status" -eq 0 ]
    before="$(links | sort)"
    [ -n "$(printf '%s\n' "$before" | grep '/hooks/')" ]
    nojq="${WORK}/nojq"
    mkdir -p "$nojq"
    for f in /usr/bin/* /bin/*; do
        [ "$(basename "$f")" = jq ] || ln -sfn "$f" "${nojq}/$(basename "$f")"
    done
    ln -sfn "${WORK}/wt" "$LINK"
    PATH="${STUBS}:${nojq}" run "${FORGE}/scripts/install.sh"
    [ "$status" -eq 1 ]
    [[ "$output" == *"jq is required"* ]]
    [ "$(links | sort)" = "$before" ]
}

@test "a link into the checkout with no counterpart in the live worktree is removed" {
    git -C "$FORGE" checkout -q -b feat
    mkdir -p "${FORGE}/claude-code/skills/branch-only" "${FORGE}/claude-code/agents"
    printf -- '---\nname: branch-only\n---\n' > "${FORGE}/claude-code/skills/branch-only/SKILL.md"
    printf -- '---\nname: branch-agent\n---\n' > "${FORGE}/claude-code/agents/branch-agent.md"
    run "${FORGE}/scripts/install.sh"
    [ "$status" -eq 0 ]
    [ -L "${HOME}/.claude/skills/branch-only" ]
    [ -L "${HOME}/.claude/agents/branch-agent.md" ]
    ln -sfn "${WORK}/wt" "$LINK"
    run "${FORGE}/scripts/install.sh"
    [ "$status" -eq 0 ]
    [ ! -L "${HOME}/.claude/skills/branch-only" ]
    [ ! -L "${HOME}/.claude/agents/branch-agent.md" ]
    [ -z "$(links | grep -v "^${WORK}/wt/")" ]
}

@test "aa_ma_live_worktree: a link whose parent directory is gone is not a live worktree" {
    ln -sfn "${WORK}/gone/wt" "$LINK"
    cd "$FORGE"
    REPO_ROOT="$FORGE"
    # shellcheck source=/dev/null
    . "${FORGE}/scripts/lib/aa-ma-install-lib.sh"
    run aa_ma_live_worktree
    [ "$status" -ne 0 ]
    [ -z "$output" ]
}

@test "no live worktree → links resolve into the checkout, as before" {
    run "${FORGE}/scripts/install.sh"
    [ "$status" -eq 0 ]
    [ -z "$(links | grep -v "^${FORGE}/")" ]
}

@test "a link to something that is not this forge's worktree → links into the checkout" {
    mkdir -p "${WORK}/other"
    git -C "${WORK}/other" init -q
    ln -sfn "${WORK}/other" "$LINK"
    run "${FORGE}/scripts/install.sh"
    [ "$status" -eq 0 ]
    [ -z "$(links | grep -v "^${FORGE}/")" ]
}

@test "uninstall.sh removes links that resolve into the live worktree" {
    ln -sfn "${WORK}/wt" "$LINK"
    "${FORGE}/scripts/install.sh" >/dev/null
    [ -n "$(links | grep "^${WORK}/wt/")" ]
    run "${FORGE}/scripts/uninstall.sh"
    [ "$status" -eq 0 ]
    [ -z "$(links | grep "^${WORK}/wt/")" ]
}

@test "impact-preedit (10.6): registered exactly once after two installs; hooks/lib linked; uninstall removes it" {
    count='[.. | .command? | select(. != null and test("impact-preedit"))] | length'
    "${FORGE}/scripts/install.sh" >/dev/null
    run "${FORGE}/scripts/install.sh"
    [ "$status" -eq 0 ]
    [ "$(jq "$count" "${HOME}/.claude/settings.json")" -eq 1 ]
    [ "$(jq -r '.hooks.PreToolUse[] | select(any(.hooks[]; .command | test("impact-preedit"))) | .matcher' "${HOME}/.claude/settings.json")" = "Edit|Write" ]
    [ -L "${HOME}/.claude/hooks/lib/aa-ma-impact-preedit.sh" ]
    [ -e "${HOME}/.claude/hooks/lib/aa-ma-parse.sh" ]
    "${FORGE}/scripts/uninstall.sh" >/dev/null
    [ "$(jq "$count" "${HOME}/.claude/settings.json")" -eq 0 ]
}
