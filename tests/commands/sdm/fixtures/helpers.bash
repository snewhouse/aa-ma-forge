# helpers.bash — shared setup for tests/commands/sdm/*.bats (sdm.sh).
#
# Every test runs in its own sandbox under $BATS_TEST_TMPDIR:
#   forge/test/repo.git   a bare repo standing in for GitHub
#   work/                 the clone the test runs sdm.sh in (branch `feature`, 1 commit ahead of main)
# Safety (L-058): sdm_setup exports a GIT_CONFIG_* rewrite of every https://github.com/ URL to
# forge/, so no git call in a test can reach GitHub; gh is the PATH stub in fixtures/bin.
# sdm.sh reads origin's configured URL (no insteadOf expansion), so it still sees github.com.

# SDM_UNDER_TEST: run the suite against another copy (the RED log ran it against the 1.0 prototype)
SDM="${SDM_UNDER_TEST:-$(cd "${BATS_TEST_DIRNAME}/../../.." && pwd)/claude-code/skills/sole-dev-merge/scripts/sdm.sh}"
export SDM
export STUB_PR_NUM=42   # the PR number the gh stub reports; assert against this, never a literal

mkcommit() {   # plumbing commit: the commit-signature hook only sees `git commit`
    local parent sha
    parent=$(git rev-parse --verify -q HEAD || true)   # why: no HEAD yet is the first commit
    sha=$(echo "$1" | git commit-tree "$(git write-tree)" ${parent:+-p "$parent"})
    git update-ref HEAD "$sha"
}

sdm_setup() {
    export PATH="${BATS_TEST_DIRNAME}/fixtures/bin:$PATH"
    export CLI_LOG="$BATS_TEST_TMPDIR/cli.log" GIT_TERMINAL_PROMPT=0
    export GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0="url.$BATS_TEST_TMPDIR/forge/.insteadOf" GIT_CONFIG_VALUE_0="https://github.com/"
    export CI_APPEAR_INTERVAL_S=1 CI_APPEAR_TIMEOUT_S=2 CI_POLL_TIMEOUT=5s AA_MA_FOOTER_HELPER=/nonexistent
    export CLAUDE_HOME="$BATS_TEST_TMPDIR/claude-home"   # why: an empty home, so the real ~/.claude footer link is never used
    mkdir -p "$CLAUDE_HOME"
    : > "$CLI_LOG"
    mkdir -p "$BATS_TEST_TMPDIR/forge/test"
    git init -q --bare -b main "$BATS_TEST_TMPDIR/forge/test/repo.git"
    WORK="$BATS_TEST_TMPDIR/work"
    git init -q -b main "$WORK"
    cd "$WORK" || return
    git config user.email t@t.com; git config user.name T
    git remote add origin https://github.com/test/repo.git
    echo init > a.txt; git add a.txt; mkcommit init
    git push -q origin main
    git remote set-head origin main
    git checkout -q -b feature
    echo change > b.txt; git add b.txt; mkcommit "feat: change"
}

gh_calls() { grep -c "^gh $1" "$CLI_LOG" || true; }   # why: grep -c exits 1 on 0 matches
