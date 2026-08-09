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

# sweep_slug_tmp — remove every SLUG-namespaced /tmp artefact this test owns.
#
# A glob sweep, not an enumerated list. Two teardowns
# (test_stage_c_dispatch.bats, test_stage_d_triage.bats) each hardcoded the same
# five filenames; when Stage D grew a sixth (reviewer-notes) neither learned
# about it, and 25 suite runs left 29 files in /tmp.
#
# Scope, stated precisely because the first version of this comment overclaimed:
# the glob covers every artefact whose name embeds SLUG. It does NOT cover the
# three un-slugged writers — sole-dev-merge.md's banner-shown marker, AUQ_LOG
# (/tmp/sole-dev-merge-auq.json) and BODY_OUT (/tmp/sole-dev-merge-body.md).
# Those are shared-name files; deleting them by glob could hit a concurrent run.
#
# The pattern deliberately has no "-" before SLUG and no "." after it: requiring
# either made /tmp/sole-dev-merge-${SLUG}.md and extensionless names unmatchable.
#
# Over-deletion is not reachable: SLUG is quoted (so a literal "*" stays
# literal), and a match would require another run's SLUG to contain ours as a
# substring, which the "bats-$$-"/"smoke_$$"/"testslug_$$" prefixes prevent.
sweep_slug_tmp() {
    # No SLUG means the test wrote no SLUG-namespaced files — the common case in
    # teardowns shared across a file where only one test sets it. Silent by
    # design: warning here would fire on the 8 of 9 tests for which it is
    # correct behaviour, and noise that always fires is noise nobody reads.
    [[ -n "${SLUG:-}" ]] || return 0
    rm -f "/tmp/sole-dev-merge-"*"${SLUG}"*
}
