#!/usr/bin/env bats
# install-codemem-plugin.bats — scripts/install.sh keeps the user-scope codemem plugin
# worktree on main (code-conventions-impact M15.8, report 03 R03-D13).
#
# ~/.local/share/codemem-plugin is a link to a dedicated, detached worktree of the forge.
# install.sh re-points it to main's tip and runs `uv sync` there — but only when the link
# targets a linked worktree of the forge being installed; anything else is left alone.
# The forge is a throwaway copy (scripts/, claude-code/, docs/spec/) in its own repo so
# the test owns `main` and its worktree list. uv is a stub that records its argv.

setup() {
    REAL="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)"
    WORK="$(mktemp -d "${BATS_TMPDIR}/install-codemem-plugin.XXXXXX")"
    FORGE="${WORK}/forge"
    mkdir -p "${FORGE}/docs"
    cp -a "${REAL}/scripts" "${REAL}/claude-code" "${FORGE}/"
    cp -a "${REAL}/docs/spec" "${FORGE}/docs/"
    git -C "$FORGE" init -q -b main
    git -C "$FORGE" -c user.name=t -c user.email=t@t -c commit.gpgsign=false add -A
    git -C "$FORGE" -c user.name=t -c user.email=t@t -c commit.gpgsign=false commit -q -m one
    git -C "$FORGE" -c user.name=t -c user.email=t@t -c commit.gpgsign=false commit -q --allow-empty -m two
    git -C "$FORGE" worktree add -q --detach "${WORK}/wt" HEAD~1
    export HOME="${WORK}/home"
    mkdir -p "${HOME}/.claude"/{skills,agents,rules,hooks/lib,docs} "${HOME}/.local/share"
    printf '{}\n' > "${HOME}/.claude/settings.json"
    STUBS="${WORK}/stubs"
    mkdir -p "$STUBS"
    printf '#!/usr/bin/env bash\nprintf "%%s|%%s\\n" "$PWD" "$*" >> "%s/uv.log"\n' "$WORK" > "${STUBS}/uv"
    chmod +x "${STUBS}/uv"
    export PATH="${STUBS}:${PATH}"
    LINK="${HOME}/.local/share/codemem-plugin"
}

teardown() { rm -rf "$WORK"; }

@test "a link to a forge worktree is re-pointed to main and uv-synced" {
    ln -sfn "${WORK}/wt" "$LINK"
    run "${FORGE}/scripts/install.sh"
    [ "$status" -eq 0 ]
    [ "$(git -C "${WORK}/wt" rev-parse HEAD)" = "$(git -C "$FORGE" rev-parse main)" ]
    grep -qx "${WORK}/wt|sync --locked --quiet" "${WORK}/uv.log"
}

@test "--dry-run says what it would do and changes nothing" {
    ln -sfn "${WORK}/wt" "$LINK"
    before=$(git -C "${WORK}/wt" rev-parse HEAD)
    run "${FORGE}/scripts/install.sh" --dry-run
    [ "$status" -eq 0 ]
    [[ "$output" == *"Would refresh codemem plugin worktree ${WORK}/wt to main"* ]]
    [ "$(git -C "${WORK}/wt" rev-parse HEAD)" = "$before" ]
    [ ! -e "${WORK}/uv.log" ]
}

@test "a link to something that is not this forge's worktree is left alone" {
    mkdir -p "${WORK}/other"
    git -C "${WORK}/other" init -q
    ln -sfn "${WORK}/other" "$LINK"
    run "${FORGE}/scripts/install.sh"
    [ "$status" -eq 0 ]
    [[ "$output" == *"codemem plugin link"*"not a worktree of this forge"* ]]
    [ ! -e "${WORK}/uv.log" ]
}

@test "the forge checkout itself is never re-pointed" {
    ln -sfn "$FORGE" "$LINK"
    run "${FORGE}/scripts/install.sh"
    [ "$status" -eq 0 ]
    [[ "$output" == *"not a worktree of this forge"* ]]
    [ "$(git -C "$FORGE" symbolic-ref --short HEAD)" = "main" ]
}

@test "a dirty plugin worktree is warned about, not clobbered, and install still succeeds" {
    printf 'local edit\n' >> "${WORK}/wt/scripts/install.sh"
    ln -sfn "${WORK}/wt" "$LINK"
    run "${FORGE}/scripts/install.sh"
    [ "$status" -eq 0 ]
    [[ "$output" == *"codemem plugin worktree"*"uncommitted changes"* ]]
    grep -q 'local edit' "${WORK}/wt/scripts/install.sh"
}

@test "no link → nothing about the codemem plugin" {
    run "${FORGE}/scripts/install.sh"
    [ "$status" -eq 0 ]
    [[ "$output" != *"codemem plugin"* ]]
}

@test "§6.6: a forge that is not a git checkout does not abort install at step 8" {
    rm -rf "${FORGE}/.git"
    ln -sfn "${WORK}/wt" "$LINK"
    run "${FORGE}/scripts/install.sh"
    [ "$status" -eq 0 ]
    [[ "$output" == *"not a worktree of this forge"* ]]
}
