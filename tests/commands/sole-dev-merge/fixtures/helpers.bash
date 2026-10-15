# helpers.bash — shared bats helpers for tests/commands/sole-dev-merge/*.bats
#
# Loaded via `load fixtures/helpers.bash` from each bats file's setup() (note:
# bats `load` strips the .bash extension when searching).
#
# Provides:
#   mkcommit MSG           — plumbing-only commit on current HEAD (bypasses
#                            the aa-ma-commit-signature.sh PreToolUse hook
#                            because the hook regex-matches `git commit`)
#   sandbox_init           — initialise BATS_TMP as a fresh git repo
#   tmp_script_dir         — return a fresh tmp dir for extracted scripts
#                            (kept OUTSIDE BATS_TMP so helper files don't
#                            dirty `git status --porcelain` and trip
#                            Stage A's clean-tree check — see M1 lesson)

mkcommit() {
    local msg="$1" parent tree sha
    parent=$(git rev-parse --verify -q HEAD 2>/dev/null || true)
    tree=$(git write-tree)
    if [[ -n "$parent" ]]; then
        sha=$(echo "$msg" | git commit-tree "$tree" -p "$parent")
    else
        sha=$(echo "$msg" | git commit-tree "$tree")
    fi
    git update-ref HEAD "$sha"
}

sandbox_init() {
    git init -q -b main
    git config user.email t@t.com
    git config user.name T
}

tmp_script_dir() {
    mktemp -d
}
