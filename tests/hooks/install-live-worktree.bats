#!/usr/bin/env bats
# install-live-worktree.bats — scripts/install.sh links ~/.claude into the live worktree
# (code-conventions-impact 10.0, ADR-0025 amending D7).
#
# The live worktree is the one ~/.local/share/codemem-plugin links to: a detached worktree
# of the forge kept on main by install.sh. With it in place, every ~/.claude link (and the
# --wire-git-hook path) resolves into it, so a branch checked out in the forge checkout is
# never live. Without it, install.sh links into the checkout it runs from, as before.
# Same throwaway-forge fixture as install-codemem-plugin.bats.

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
    ! grep -qF "${FORGE}/" "${HOME}/.claude/settings.json"
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
    ! grep -qF "${FORGE}/claude-code" "$hook"
}

@test "a dirty live worktree is still the link target (refresh skipped, warned)" {
    printf 'local edit\n' >> "${WORK}/wt/scripts/install.sh"
    ln -sfn "${WORK}/wt" "$LINK"
    run "${FORGE}/scripts/install.sh"
    [ "$status" -eq 0 ]
    [[ "$output" == *"uncommitted changes"* ]]
    [ -z "$(links | grep -v "^${WORK}/wt/")" ]
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
