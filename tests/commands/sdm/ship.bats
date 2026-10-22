#!/usr/bin/env bats
# ship.bats — `sdm.sh ship [--notes FILE]` (sole-dev-merge-simplify 1.1; spec: the plan's sdm.sh test spec).
#
# Ported from tests/commands/sole-dev-merge/ (stages E, E3, F, G1, G2), re-targeted to "$SDM" ship:
# no state files, no REMOTE_CHOICE, no glab. Old `PR_NUM=`/`PR_URL=` exports are now printed lines.
# Each test names its origin as "<old file>:<line>"; tests new to sdm.sh are prefixed "new:".
#
# The gh stub (fixtures/bin/gh) logs argv to $CLI_LOG and keeps the PR body (PATCHed or
# `pr create --body-file`) at $CLI_LOG.body. Pushes land in the local bare forge (helpers.bash).

bats_require_minimum_version 1.5.0

load fixtures/helpers

setup() {
    sdm_setup
    FORGE="$BATS_TEST_TMPDIR/forge/test/repo.git"
    BODY_STORE="$CLI_LOG.body"
    PR_URL_EXPECTED="https://github.com/test/repo/pull/${STUB_PR_NUM}"
}

ship() { run --separate-stderr "$SDM" ship "$@"; }

forge_feature() { git --git-dir="$FORGE" rev-parse -q --verify refs/heads/feature || true; }   # why: no ref = empty, not a failure

count() { grep -c -- "$1" "$CLI_LOG" || true; }      # why: grep -c exits 1 on 0 matches
count_f() { grep -cF -- "$1" "$CLI_LOG" || true; }   # why: as above

non_watch_checks() { grep '^gh pr checks' "$CLI_LOG" | grep -vc -- '--watch' || true; }   # why: as above

five_commit_branch() {   # sdm_setup made "feat: change"; four more → 5 commits ahead of main
    local n
    for n in 2 3 4 5; do
        echo "$n" > "f${n}.txt"; git add "f${n}.txt"; mkcommit "feat: change number $n"
    done
}

assert_no_push() { [ -z "$(forge_feature)" ]; }

# ---------------------------------------------------------------------------
# origin is github.com: pass/abort (test_stage_e_remote.bats)
# ---------------------------------------------------------------------------

@test "e_remote:52 — github.com https origin passes: pushed, PR created, rc 0" {
    ship
    [ "$status" -eq 0 ]
    [[ "$output" != *ABORT* ]]
    [ "$(forge_feature)" = "$(git rev-parse HEAD)" ]
    [ "$(gh_calls 'pr create')" -eq 1 ]
}

@test "e_remote:139 — the single github remote (scp form git@github.com:) → proceeds" {
    # why: a second insteadOf so the scp URL also lands in the local forge, never on GitHub (L-058)
    export GIT_CONFIG_COUNT=2 GIT_CONFIG_KEY_1="url.$BATS_TEST_TMPDIR/forge/.insteadOf" GIT_CONFIG_VALUE_1="git@github.com:"
    git remote set-url origin git@github.com:test/repo.git
    ship
    [ "$status" -eq 0 ]
    [[ "$output" != *ABORT* ]]
    [ "$(forge_feature)" = "$(git rev-parse HEAD)" ]
    [ "$(count_f 'pr create -R test/repo')" -eq 1 ]
}

@test "e_remote:164 — no github remote → ABORT: ship: origin is on <host>, no push, no gh pr call" {
    git remote set-url origin https://bitbucket.org.invalid/x/y.git   # why: reserved host, never resolves (L-058)
    ship
    [ "$status" -eq 1 ]
    [ "${lines[0]}" = "ABORT: ship: origin is on bitbucket.org.invalid, not github.com" ]
    assert_no_push
    [ "$(gh_calls 'pr')" -eq 0 ]
}

# ---------------------------------------------------------------------------
# PR body (test_stage_e3_body.bats) — read from the stub's body store
# ---------------------------------------------------------------------------

@test "e3_body:55 — 5-commit branch → one '- <subject>' bullet per commit" {
    five_commit_branch
    ship
    [ "$status" -eq 0 ]
    [ -f "$BODY_STORE" ]
    grep -qx -- '- feat: change' "$BODY_STORE"
    local n
    for n in 2 3 4 5; do grep -qx -- "- feat: change number $n" "$BODY_STORE"; done
    [ "$(grep -cE '^[-*] ' "$BODY_STORE")" -ge 5 ]
}

@test "e3_body:65 — '## Test plan' heading present" {
    five_commit_branch
    ship
    [ "$status" -eq 0 ]
    grep -q '^## Test plan$' "$BODY_STORE"
}

@test "e3_body:72 — AA-MA plan active → 'Plan context: …' line" {
    five_commit_branch
    export AA_MA_PLAN_DIR="$BATS_TEST_TMPDIR/.claude/dev/active/some-task"
    mkdir -p "$AA_MA_PLAN_DIR"
    ship
    [ "$status" -eq 0 ]
    grep -qE '^Plan context: /.+/\.claude/dev/active/.+/?$' "$BODY_STORE"
}

@test "e3_body:84 — no AA-MA plan → no 'Plan context:' line" {
    five_commit_branch
    unset AA_MA_PLAN_DIR
    ship
    [ "$status" -eq 0 ]
    [ -f "$BODY_STORE" ]
    run ! grep -q '^Plan context:' "$BODY_STORE"
}

@test "e3_body:152 — AA_MA_PLAN_DIR with a newline, CR and tab → one 'Plan context:' line, control chars stripped" {
    five_commit_branch
    export AA_MA_PLAN_DIR=$'/p/.claude/dev/active/x\n## Injected\r\tz'
    ship
    [ "$status" -eq 0 ]
    grep -qxF 'Plan context: /p/.claude/dev/active/x## Injectedz' "$BODY_STORE"
    run ! grep -q '^## Injected' "$BODY_STORE"
}

@test "e3_body:93 — required headings: Summary, Changes by area, Reviewer notes" {
    five_commit_branch
    ship
    [ "$status" -eq 0 ]
    grep -q '^## Summary$' "$BODY_STORE"
    grep -q '^## Changes by area$' "$BODY_STORE"
    grep -q '^## Reviewer notes$' "$BODY_STORE"
}

@test "e3_body:102 — traceability footer is the last line" {
    five_commit_branch
    ship
    [ "$status" -eq 0 ]
    grep -q '<!-- Generated by /sole-dev-merge -->' "$BODY_STORE"
    [ "$(tail -n 1 "$BODY_STORE")" = "<!-- Generated by /sole-dev-merge -->" ]
}

@test "e3_body:118 — --notes FILE content appears under '## Reviewer notes', no '(none)'" {
    five_commit_branch
    local notes="$BATS_TEST_TMPDIR/notes.md"
    cat > "$notes" <<'NOTES'
[LOW] B101 assert_used Use of assert detected — example/path.py:5
[LOW] B311 random Standard pseudo-random generators are not suitable — other.py:12
NOTES
    ship --notes "$notes"
    [ "$status" -eq 0 ]
    grep -qF '[LOW] B101 assert_used Use of assert detected — example/path.py:5' "$BODY_STORE"
    grep -qF '[LOW] B311 random Standard pseudo-random generators are not suitable — other.py:12' "$BODY_STORE"
    # the notes follow the heading, not another section
    [ "$(grep -n '^## Reviewer notes$' "$BODY_STORE" | cut -d: -f1)" -lt "$(grep -n 'B101 assert_used' "$BODY_STORE" | cut -d: -f1)" ]
    run ! grep -q '^(none)$' "$BODY_STORE"
}

@test "e3_body:139 — no --notes (or an empty notes file) → '(none)' under '## Reviewer notes'" {
    five_commit_branch
    ship
    [ "$status" -eq 0 ]
    grep -q '^## Reviewer notes$' "$BODY_STORE"
    grep -q '^(none)$' "$BODY_STORE"
    : > "$BATS_TEST_TMPDIR/empty.md"; rm -f "$BODY_STORE"
    ship --notes "$BATS_TEST_TMPDIR/empty.md"
    [ "$status" -eq 0 ]
    grep -q '^(none)$' "$BODY_STORE"
}

# ---------------------------------------------------------------------------
# auth, push, PR create/update (test_stage_f_idempotent.bats)
# ---------------------------------------------------------------------------

@test "f:73 — gh auth status non-zero → STATUS: AUTH_REQUIRED, rc 0 within 5s, nothing pushed" {
    export GH_AUTH_OK=0
    run --separate-stderr timeout 5s "$SDM" ship
    [ "$status" -eq 0 ]
    [ "${lines[0]}" = "STATUS: AUTH_REQUIRED — run gh auth login" ]
    assert_no_push
    [ "$(gh_calls 'pr')" -eq 0 ]
}

@test "f:94 — gh auth OK → no AUTH_REQUIRED" {
    ship
    [ "$status" -eq 0 ]
    [[ "$output" != *AUTH_REQUIRED* ]]
}

@test "f:107 — existing PR → one REST PATCH + one read-back, never gh pr edit or create" {
    export GH_PR_EXISTS=1
    ship
    [ "$status" -eq 0 ]
    [ "$(count 'pr create')" -eq 0 ]
    [ "$(count 'pr edit')" -eq 0 ]
    [ "$(count "^gh api -X PATCH repos/test/repo/pulls/${STUB_PR_NUM} -F body=@")" -eq 1 ]
    [ "$(count_f "gh api repos/test/repo/pulls/${STUB_PR_NUM} --jq .body")" -eq 1 ]
    local n_view n_patch
    n_view=$(grep -n '^gh pr view' "$CLI_LOG" | head -1 | cut -d: -f1)
    n_patch=$(grep -n -- '-X PATCH' "$CLI_LOG" | head -1 | cut -d: -f1)
    [ -n "$n_view" ] && [ -n "$n_patch" ]
    [ "$n_view" -lt "$n_patch" ]
}

@test "f:128 — existing PR, read-back matches → body stored verbatim, no STATUS line, PR_NUM printed" {
    export GH_PR_EXISTS=1
    local notes="$BATS_TEST_TMPDIR/notes.md"
    printf -- '- `code`, {owner} {repo}, → ✓\n' > "$notes"
    ship --notes "$notes"
    [ "$status" -eq 0 ]
    grep -qxF -- '- `code`, {owner} {repo}, → ✓' "$BODY_STORE"
    [[ "$output" != *PR_BODY_NOT_UPDATED* ]]
    [ "${lines[0]}" = "PR_NUM=${STUB_PR_NUM}" ]
}

@test "f:142 — read-back mismatch → STATUS: PR_BODY_NOT_UPDATED reason=readback-differs, rc 0, ship goes on" {
    export GH_PR_EXISTS=1 GH_PR_BODY_READBACK="an older body"
    ship
    [ "$status" -eq 0 ]
    [ "${lines[0]}" = "STATUS: PR_BODY_NOT_UPDATED — PR #${STUB_PR_NUM} reason=readback-differs" ]
    [ "${lines[1]}" = "PR_NUM=${STUB_PR_NUM}" ]
    [ "${lines[2]}" = "PR_URL=${PR_URL_EXPECTED}" ]
    [ "${lines[3]}" = "CI_STATE=green" ]
}

@test "f:153 — a failing PATCH → STATUS: PR_BODY_NOT_UPDATED reason=patch-failed, rc 0 (never a set -e exit)" {
    export GH_PR_EXISTS=1 GH_API_PATCH_RC=1
    ship
    [ "$status" -eq 0 ]
    [ "${lines[0]}" = "STATUS: PR_BODY_NOT_UPDATED — PR #${STUB_PR_NUM} reason=patch-failed" ]
    [[ "$output" == *"PR_NUM=${STUB_PR_NUM}"* ]]
}

@test "f:163 — existing PR from a fork (isCrossRepository) → no PATCH, reason=not-this-branch, ship stops, no PR_NUM" {
    export GH_PR_EXISTS=1 GH_PR_CROSS_REPO=true
    ship
    [ "$status" -eq 0 ]
    [ "$(count '-X PATCH')" -eq 0 ]
    [ "${lines[0]}" = "STATUS: PR_BODY_NOT_UPDATED — PR #${STUB_PR_NUM} reason=not-this-branch" ]
    [[ "$output" != *"PR_NUM="* ]]
    [ "$(gh_calls 'pr create')" -eq 0 ]
    [ "$(gh_calls 'pr checks')" -eq 0 ]
}

@test "f:179 — existing PR whose head is another branch → no PATCH, reason=not-this-branch" {
    export GH_PR_EXISTS=1 GH_PR_HEAD_REF=other
    ship
    [ "$status" -eq 0 ]
    [ "$(count '-X PATCH')" -eq 0 ]
    [[ "$output" == *"reason=not-this-branch"* ]]
    [[ "$output" != *"PR_NUM="* ]]
}

@test "f:191 — the PR is looked up once, by branch with -R, all fields in one call" {
    export GH_PR_EXISTS=1
    ship
    [ "$status" -eq 0 ]
    [ "$(gh_calls 'pr view')" -eq 1 ]
    [ "$(count_f 'gh pr view feature -R test/repo --json number,url,isCrossRepository,headRefName,state,headRefOid')" -eq 1 ]
    [[ "$output" == *"PR_URL=${PR_URL_EXPECTED}"* ]]
}

@test "f:202 — create path: PR_NUM comes from create's own URL (-R slug --head branch), no second by-branch lookup" {
    # why: the old re-lookup after create could pick a fork's same-named PR; sdm.sh makes one lookup only
    export GH_PR_EXISTS=0 GH_PR_CROSS_REPO=true
    ship
    [ "$status" -eq 0 ]
    [ "$(gh_calls 'pr view')" -eq 1 ]
    [ "$(gh_calls 'pr create')" -eq 1 ]
    grep '^gh pr create' "$CLI_LOG" | grep -qF -- '-R test/repo'
    grep '^gh pr create' "$CLI_LOG" | grep -qF -- '--head feature'
    grep '^gh pr create' "$CLI_LOG" | grep -qF -- '--base main'
    [ "${lines[0]}" = "PR_NUM=${STUB_PR_NUM}" ]
}

@test "f:215 — the branch's only PR is MERGED → a new PR is created, the old one is not PATCHed" {
    export GH_PR_EXISTS=1 GH_PR_LOOKUP_STATE=MERGED
    ship
    [ "$status" -eq 0 ]
    [ "$(gh_calls 'pr create')" -eq 1 ]
    [ "$(count '-X PATCH')" -eq 0 ]
    [ "${lines[0]}" = "PR_NUM=${STUB_PR_NUM}" ]
}

@test "f:275 — origin on gitlab → ABORT before any push or gh call" {
    git remote set-url origin https://gitlab.com.invalid/x/y.git   # why: reserved host, never resolves (L-058)
    ship
    [ "$status" -eq 1 ]
    [ "${lines[0]}" = "ABORT: ship: origin is on gitlab.com.invalid, not github.com" ]
    [ "$(grep -c '^gh ' "$CLI_LOG" || true)" -eq 0 ]   # why: grep -c exits 1 on 0 matches
    assert_no_push
}

@test "f:304 — no existing PR → create path: no PATCH, no read-back, no PR_BODY_NOT_UPDATED" {
    ship
    [ "$status" -eq 0 ]
    [ "$(gh_calls 'pr create')" -eq 1 ]
    [ "$(count '-X PATCH')" -eq 0 ]
    [ "$(count '--jq .body')" -eq 0 ]
    [[ "$output" != *PR_BODY_NOT_UPDATED* ]]
}

@test "f:317 — sdm.sh never calls gh pr edit" {
    [ -f "$SDM" ]
    run grep -c 'pr edit' "$SDM"
    [ "$output" = 0 ]
}

@test "f:322 — no existing PR → gh pr create with --body-file, never edit" {
    ship
    [ "$status" -eq 0 ]
    [ "$(count 'pr edit')" -eq 0 ]
    [ "$(gh_calls 'pr create')" -eq 1 ]
    [ "$(count '--body-file')" -eq 1 ]
}

@test "f:360 — title is the HEAD subject cut to 70 chars" {
    local long_subject
    long_subject="feat: $(printf 'x%.0s' {1..100})"   # 106 chars
    echo more > c.txt; git add c.txt; mkcommit "$long_subject"
    ship
    [ "$status" -eq 0 ]
    [ "$(count_f "--title ${long_subject:0:70}")" -eq 1 ]
    [ "$(count_f "--title ${long_subject:0:71}")" -eq 0 ]
}

@test "f:388 — git push -u origin HEAD lands the branch in the forge before PR ops" {
    ship
    [ "$status" -eq 0 ]
    [ "$(forge_feature)" = "$(git rev-parse HEAD)" ]
    [ "$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}')" = origin/feature ]
}

@test "f:410 — prints PR_NUM and PR_URL, in that order, first on stdout" {
    ship
    [ "$status" -eq 0 ]
    [ "${lines[0]}" = "PR_NUM=${STUB_PR_NUM}" ]
    [ "${lines[1]}" = "PR_URL=${PR_URL_EXPECTED}" ]
    [ "$(gh_calls 'pr view')" -eq 1 ]
}

# ---------------------------------------------------------------------------
# CI wait (test_stage_g_poll.bats)
# ---------------------------------------------------------------------------

@test "g_poll:59 — CI green → stdout is exactly PR_NUM, PR_URL, CI_STATE=green" {
    export GH_WATCH_HANG=0 GH_CHECKS_RC=0
    ship
    [ "$status" -eq 0 ]
    [ "${#lines[@]}" -eq 3 ]
    [ "${lines[0]}" = "PR_NUM=${STUB_PR_NUM}" ]
    [ "${lines[1]}" = "PR_URL=${PR_URL_EXPECTED}" ]
    [ "${lines[2]}" = "CI_STATE=green" ]
}

@test "g_poll:69 — never-returning watch → STATUS: CI_TIMEOUT + recovery hint + CI_STATE=timeout" {
    export GH_WATCH_HANG=1 CI_POLL_TIMEOUT=2s
    run --separate-stderr timeout 20s "$SDM" ship
    [ "$status" -eq 0 ]
    [[ "$output" == *"STATUS: CI_TIMEOUT — see ${PR_URL_EXPECTED}"* ]]
    [[ "$output" == *"recovery: sdm.sh finish ${STUB_PR_NUM} once CI completes"* ]]
    [ "${lines[${#lines[@]}-1]}" = "CI_STATE=timeout" ]
}

@test "g_poll:83 — CI failed (rc 1) → STATUS: CI_FAILED + PR URL + diagnostic + CI_STATE=failed" {
    export GH_WATCH_HANG=0 GH_CHECKS_RC=1
    ship
    [ "$status" -eq 0 ]
    [[ "$output" == *"STATUS: CI_FAILED — see ${PR_URL_EXPECTED}"* ]]
    [[ "$output" == *$'\n'"  diagnostic: gh pr checks ${STUB_PR_NUM}"* ]]
    [ "${lines[${#lines[@]}-1]}" = "CI_STATE=failed" ]
}

@test "g_poll:96 — checks not registered yet → waits for them, then CI_STATE=green" {
    export GH_CHECKS_RC=0 GH_CHECKS_NONE_CALLS=2 CI_APPEAR_INTERVAL_S=1
    ship
    [ "$status" -eq 0 ]
    [[ "$output" == *"CI_STATE=green"* ]]
    [ "$(gh_calls 'pr checks')" -ge 3 ]
}

@test "g_poll:105 — no check ever registers → says so on stderr, then CI_STATE=failed" {
    export GH_CHECKS_RC=0 GH_CHECKS_NONE_CALLS=99 CI_APPEAR_TIMEOUT_S=0 CI_APPEAR_INTERVAL_S=1
    ship
    [ "$status" -eq 0 ]
    [[ "$stderr" == *"ship: no checks registered after 0s"* ]]
    [[ "$output" == *"CI_STATE=failed"* ]]
}

@test "g_poll:114 — a real wait counts its seconds and gives up at the cap" {
    export GH_CHECKS_RC=0 GH_CHECKS_NONE_CALLS=99 CI_APPEAR_TIMEOUT_S=2 CI_APPEAR_INTERVAL_S=1
    ship
    [ "$status" -eq 0 ]
    [[ "$stderr" == *"ship: no checks registered after 2s"* ]]
    [ "$(gh_calls 'pr checks')" -ge 3 ]
}

@test "g_poll:134 — an interval of 0 is ignored (the wait would never advance)" {
    export GH_CHECKS_RC=0 GH_CHECKS_NONE_CALLS=99 CI_APPEAR_TIMEOUT_S=0 CI_APPEAR_INTERVAL_S=0
    run --separate-stderr timeout 30s "$SDM" ship
    [ "$status" -eq 0 ]
    [[ "$stderr" == *"ship: ignoring CI_APPEAR_INTERVAL_S"* ]]
}

@test "g_poll:142 — the watch is gh pr checks <n> -R slug --watch --interval 30 --fail-fast" {
    export GH_CHECKS_RC=0
    ship
    [ "$status" -eq 0 ]
    grep -q "^gh pr checks ${STUB_PR_NUM} -R test/repo .*--watch" "$CLI_LOG"
    grep '^gh pr checks' "$CLI_LOG" | grep -- '--watch' | grep -q -- '--interval 30'
    grep '^gh pr checks' "$CLI_LOG" | grep -- '--watch' | grep -q -- '--fail-fast'
}

# ---------------------------------------------------------------------------
# G1 strategy inside ship (test_stage_g_merge.bats)
# ---------------------------------------------------------------------------

@test "g_merge:82 — rebase allowed (default) → stderr 'ship: strategy=rebase'" {
    export GH_ALLOW_REBASE=true
    ship
    [ "$status" -eq 0 ]
    [[ "$stderr" == *"ship: strategy=rebase"* ]]
    [ "$(count_f 'gh api repos/test/repo --jq .allow_rebase_merge')" -eq 1 ]
}

@test "g_merge:91 — rebase disabled → stderr 'ship: strategy=merge'" {
    export GH_ALLOW_REBASE=false
    ship
    [ "$status" -eq 0 ]
    [[ "$stderr" == *"ship: strategy=merge"* ]]
    [[ "$stderr" != *"strategy=rebase"* ]]
}

# ---------------------------------------------------------------------------
# new tests
# ---------------------------------------------------------------------------

@test "new: 1 — watch rc 0 but a check row is 'cancel' → STATUS: CI_FAILED, CI_STATE=failed" {
    export GH_CHECKS_RC=0 GH_CHECKS_ROWS=$'build\tpass\t1m\thttps://x/1\nlint\tcancel\t0\thttps://x/2'
    ship
    [ "$status" -eq 0 ]
    [[ "$output" == *"STATUS: CI_FAILED — see ${PR_URL_EXPECTED}"* ]]
    [ "${lines[${#lines[@]}-1]}" = "CI_STATE=failed" ]
}

@test "new: 1 — watch rc 0 but a check row is 'fail' → STATUS: CI_FAILED, CI_STATE=failed" {
    export GH_CHECKS_RC=0 GH_CHECKS_ROWS=$'build\tfail\t1m\thttps://x/1'
    ship
    [ "$status" -eq 0 ]
    [[ "$output" == *"STATUS: CI_FAILED — see ${PR_URL_EXPECTED}"* ]]
    [ "${lines[${#lines[@]}-1]}" = "CI_STATE=failed" ]
}

@test "new: 4 — CI_TIMEOUT hint is exactly '  recovery: sdm.sh finish <n> once CI completes', never --auto" {
    export GH_WATCH_HANG=1 CI_POLL_TIMEOUT=2s
    run --separate-stderr timeout 20s "$SDM" ship
    [ "$status" -eq 0 ]
    [[ "$output" == *"STATUS: CI_TIMEOUT — see ${PR_URL_EXPECTED}"$'\n'"  recovery: sdm.sh finish ${STUB_PR_NUM} once CI completes"$'\n'* ]]
    [[ "$output" != *--auto* ]]
    [[ "$stderr" != *--auto* ]]
}

@test "new: 5 — G1 API failure → ABORT: ship: cannot read allow_rebase_merge, rc 1, never rebase" {
    export GH_API_REPO_RC=1
    ship
    [ "$status" -eq 1 ]
    [[ "$output" == *"ABORT: ship: cannot read allow_rebase_merge"* ]]
    [[ "$output$stderr" != *"strategy=rebase"* ]]
    [ "${lines[0]}" = "PR_NUM=$STUB_PR_NUM" ]   # the PR exists by now: its number comes before the ABORT
    [ "${lines[1]}" = "PR_URL=$PR_URL_EXPECTED" ]
    [ "$(gh_calls 'pr checks')" -eq 0 ]
}

@test "new: 5 — allow_rebase_merge null → ABORT: ship: allow_rebase_merge is 'null', not true or false" {
    export GH_ALLOW_REBASE=null
    ship
    [ "$status" -eq 1 ]
    [[ "$output" == *"ABORT: ship: allow_rebase_merge is 'null', not true or false"* ]]
    [[ "$output$stderr" != *"strategy=rebase"* ]]
    [ "${lines[0]}" = "PR_NUM=$STUB_PR_NUM" ]
}

@test "new: 16 — ship sees github.com through the insteadOf rewrite; push lands in the forge; gh gets -R test/repo" {
    [ "$(git config --get remote.origin.url)" = "https://github.com/test/repo.git" ]
    ship
    [ "$status" -eq 0 ]
    [ "$(forge_feature)" = "$(git rev-parse HEAD)" ]
    [ "$(gh_calls 'pr')" -ge 1 ]
    # every gh pr call names the repo explicitly
    [ "$(grep '^gh pr ' "$CLI_LOG" | grep -vc -- ' -R test/repo' || true)" -eq 0 ]   # why: grep -c exits 1 on 0 matches
}

@test "new: non-github scp origin (git@gitlab.com.invalid:x/y.git) → ABORT, no push, no gh call" {
    git remote set-url origin git@gitlab.com.invalid:x/y.git   # why: reserved host, never resolves (L-058)
    ship
    [ "$status" -eq 1 ]
    [ "${lines[0]}" = "ABORT: ship: origin is on gitlab.com.invalid, not github.com" ]
    assert_no_push
    [ "$(grep -c '^gh ' "$CLI_LOG" || true)" -eq 0 ]   # why: grep -c exits 1 on 0 matches
}

@test "new: a URL whose path contains github.com is not github → ABORT names the real host" {
    git remote set-url origin https://gitlab.com.invalid/org/github.com-tools.git
    ship
    [ "$status" -eq 1 ]
    [ "${lines[0]}" = "ABORT: ship: origin is on gitlab.com.invalid, not github.com" ]
    assert_no_push
    [ "$(grep -c '^gh ' "$CLI_LOG" || true)" -eq 0 ]   # why: grep -c exits 1 on 0 matches
}

@test "new: the ABORT never prints the origin URL (a token in it stays hidden)" {
    git remote set-url origin https://tok123@gitlab.com.invalid/x/y.git
    ship
    [ "$status" -eq 1 ]
    [ "${lines[0]}" = "ABORT: ship: origin is on gitlab.com.invalid, not github.com" ]
    [[ "$output" != *tok123* ]]
    [[ "$stderr" != *tok123* ]]
    assert_no_push
}

@test "new: origin pushurl wins over url → ABORT names the pushurl's host" {
    git config remote.origin.pushurl https://gitlab.com.invalid/x/y.git
    ship
    [ "$status" -eq 1 ]
    [ "${lines[0]}" = "ABORT: ship: origin is on gitlab.com.invalid, not github.com" ]
    assert_no_push
    [ "$(grep -c '^gh ' "$CLI_LOG" || true)" -eq 0 ]   # why: grep -c exits 1 on 0 matches
}

@test "new: a local-path origin → ABORT: ship: origin is not a github.com remote" {
    git remote set-url origin "$FORGE"
    ship
    [ "$status" -eq 1 ]
    [ "${lines[0]}" = "ABORT: ship: origin is not a github.com remote" ]
    assert_no_push
    [ "$(grep -c '^gh ' "$CLI_LOG" || true)" -eq 0 ]   # why: grep -c exits 1 on 0 matches
}

@test "new: CI_APPEAR_TIMEOUT_S=02 waits the decimal 2s worth of looks" {
    export GH_CHECKS_NONE_CALLS=99 CI_APPEAR_INTERVAL_S=1 CI_APPEAR_TIMEOUT_S=02
    ship
    [ "$status" -eq 0 ]
    [[ "$stderr" =~ ship:\ no\ checks\ registered\ after\ ([0-9]+)s ]]
    [ "${BASH_REMATCH[1]}" -ge 2 ]
    [ "$(non_watch_checks)" -ge 3 ]
    [[ "$stderr" != *"ignoring CI_APPEAR_TIMEOUT_S"* ]]
}

@test "new: CI_APPEAR_TIMEOUT_S=09 is decimal 9 — never an arithmetic error, never ignored" {
    export GH_CHECKS_NONE_CALLS=2 CI_APPEAR_INTERVAL_S=1 CI_APPEAR_TIMEOUT_S=09
    ship
    [ "$status" -eq 0 ]
    [[ "$output" == *"CI_STATE=green"* ]]
    [[ "$stderr" != *"value too great"* ]]
    [[ "$stderr" != *"syntax error"* ]]
    [[ "$stderr" != *"ignoring CI_APPEAR_TIMEOUT_S"* ]]
    [ "$(non_watch_checks)" -ge 3 ]
}

@test "new: CI_APPEAR_TIMEOUT_S=010 is decimal 10, not octal 8 (~10s)" {
    export GH_CHECKS_NONE_CALLS=99 CI_APPEAR_INTERVAL_S=1 CI_APPEAR_TIMEOUT_S=010
    run --separate-stderr timeout 60s "$SDM" ship
    [ "$status" -eq 0 ]
    [[ "$stderr" =~ ship:\ no\ checks\ registered\ after\ ([0-9]+)s ]]
    [ "${BASH_REMATCH[1]}" -ge 10 ]
    [ "$(non_watch_checks)" -ge 11 ]
}

@test "new: existing OPEN PR whose head never reaches the push → re-read, then reason=head-not-updated, no PATCH, no PR_NUM, rc 0" {
    export GH_PR_EXISTS=1 GH_PR_HEAD_OID=0000000000000000000000000000000000000000
    ship
    [ "$status" -eq 0 ]
    [ "${lines[0]}" = "STATUS: PR_BODY_NOT_UPDATED — PR #${STUB_PR_NUM} reason=head-not-updated" ]
    [ "$(count '-X PATCH')" -eq 0 ]
    [[ "$output" != *"PR_NUM="* ]]
    [ "$(count '^gh pr view feature')" -ge 2 ]   # why: it re-read before giving up (bounded by CI_APPEAR_TIMEOUT_S)
}

@test "new (live, PR #55): GitHub's head lags the push once → ship re-reads, updates the body and waits for CI" {
    # why: right after a re-push GitHub still reported the old headRefOid; ship called its own PR not-this-branch
    export GH_PR_EXISTS=1 GH_PR_STALE_OID_CALLS=1
    ship
    [ "$status" -eq 0 ]
    [[ "$output" != *PR_BODY_NOT_UPDATED* ]]
    [ "$(count '-X PATCH')" -eq 1 ]
    [ "${lines[0]}" = "PR_NUM=$STUB_PR_NUM" ]
    [ "${lines[-1]}" = "CI_STATE=green" ]
    [ "$(count '^gh pr view feature')" -eq 2 ]
}

@test "new: a fork's PR or another head branch is refused at once, never re-read (reason=not-this-branch)" {
    export GH_PR_EXISTS=1 GH_PR_CROSS_REPO=true
    ship
    [ "$status" -eq 0 ]
    [ "${lines[0]}" = "STATUS: PR_BODY_NOT_UPDATED — PR #${STUB_PR_NUM} reason=not-this-branch" ]
    [ "$(count '^gh pr view feature')" -eq 1 ]
}

@test "new: the body temp file is removed after ship (success and ABORT paths)" {
    local tmp="$BATS_TEST_TMPDIR/ship-tmp"
    mkdir -p "$tmp"
    run env TMPDIR="$tmp" "$SDM" ship
    [ "$status" -eq 0 ]
    [ -s "$BODY_STORE" ]   # a body was written, so a temp file existed
    [ -z "$(ls -A "$tmp")" ]
    rm -f "$BODY_STORE"
    run env TMPDIR="$tmp" GH_API_REPO_RC=1 "$SDM" ship   # ABORT after the body was made
    [ "$status" -eq 1 ]
    [ -s "$BODY_STORE" ]
    [ -z "$(ls -A "$tmp")" ]
}

# ---------------------------------------------------------------------------
# fix/sdm-failure-lines (TODOS "sdm.sh M1 §6.8 review notes", "sdm.sh M1 PR review")
# ---------------------------------------------------------------------------

@test "fix: the forge rejects the push → ABORT: ship: git push failed (rc=1), no gh pr call" {
    printf '#!/bin/sh\necho "rejected by test hook" >&2\nexit 1\n' > "$FORGE/hooks/pre-receive"
    chmod +x "$FORGE/hooks/pre-receive"
    ship
    [ "$status" -eq 1 ]
    [ "${lines[-1]}" = "ABORT: ship: git push failed (rc=1)" ]
    assert_no_push
    [ "$(count '^gh pr ')" -eq 0 ]
}

@test "fix: the PR is closed during the head wait → reason=not-open, no PATCH, no PR_NUM, rc 0" {
    # first lookup: OPEN at the old head; the re-read: CLOSED at the pushed head
    export GH_PR_EXISTS=1 GH_PR_STALE_OID_CALLS=1 GH_PR_CLOSED_AFTER_CALLS=1
    ship
    [ "$status" -eq 0 ]
    [ "${lines[0]}" = "STATUS: PR_BODY_NOT_UPDATED — PR #${STUB_PR_NUM} reason=not-open" ]
    [ "$(count '-X PATCH')" -eq 0 ]
    [[ "$output" != *"PR_NUM="* ]]
}

@test "fix: --notes with a missing file → ABORT before any push" {
    ship --notes "$BATS_TEST_TMPDIR/no-such-notes.md"
    [ "$status" -eq 1 ]
    [ "${lines[-1]}" = "ABORT: ship: notes file '$BATS_TEST_TMPDIR/no-such-notes.md' is not a readable file" ]
    assert_no_push
}

@test "fix: --notes with no FILE → ABORT before any push" {
    ship --notes
    [ "$status" -eq 1 ]
    [ "${lines[-1]}" = "ABORT: ship: --notes needs a FILE" ]
    assert_no_push
}

@test "fix: a relative --notes path from a subdirectory is read from there, not from the toplevel" {
    mkdir -p sub && echo "[LOW] from sub" > sub/n.md
    cd sub
    ship --notes n.md
    [ "$status" -eq 0 ]
    grep -qxF '[LOW] from sub' "$BODY_STORE"
}

@test "fix: watch rc 0 but the checks re-read fails → never green: STATUS: CI_FAILED, stderr says why" {
    export GH_CHECKS_RC=0 GH_CHECKS_REREAD_RC=1
    ship
    [ "$status" -eq 0 ]
    [[ "$output" == *"STATUS: CI_FAILED — see ${PR_URL_EXPECTED}"* ]]
    [ "${lines[-1]}" = "CI_STATE=failed" ]
    [[ "$stderr" == *"ship: could not re-read the checks (rc=1)"* ]]
}

@test "fix: CI_POLL_TIMEOUT=0 (no timeout at all) is ignored with a stderr line" {
    export CI_POLL_TIMEOUT=0
    ship
    [ "$status" -eq 0 ]
    [[ "$stderr" == *"ship: ignoring CI_POLL_TIMEOUT='0'"* ]]
    [ "${lines[-1]}" = "CI_STATE=green" ]
}

@test "fix: CI_POLL_TIMEOUT=abc is ignored with a stderr line, never a failed watch" {
    export CI_POLL_TIMEOUT=abc
    ship
    [ "$status" -eq 0 ]
    [[ "$stderr" == *"ship: ignoring CI_POLL_TIMEOUT='abc'"* ]]
    [ "${lines[-1]}" = "CI_STATE=green" ]
}

@test "fix: a raw '@' in the URL password → host read after the last '@', slug test/repo" {
    git config remote.origin.url 'https://u:p@ss@github.com/test/repo.git'
    run bash -c 'source "$SDM"; sdm_slug ship; echo "$SLUG"'
    [ "$status" -eq 0 ]
    [ "$output" = test/repo ]
}

@test "fix: a raw '@' in the URL password never shows in the ABORT (non-github host)" {
    git config remote.origin.url 'https://u:p@ss@gitlab.com.invalid/x/y.git'
    ship
    [ "$status" -eq 1 ]
    [ "${lines[-1]}" = "ABORT: ship: origin is on gitlab.com.invalid, not github.com" ]
    assert_no_push
}

@test "fix: every PR lookup by branch runs under timeout 30" {
    # why: a logging wrapper in front of the real timeout shows each call's argv
    local real; real=$(command -v timeout)
    mkdir -p "$BATS_TEST_TMPDIR/tbin"
    printf '#!/usr/bin/env bash\n{ printf timeout; printf " %%s" "$@"; echo; } >> "$CLI_LOG"\nexec %q "$@"\n' "$real" \
        > "$BATS_TEST_TMPDIR/tbin/timeout"
    chmod +x "$BATS_TEST_TMPDIR/tbin/timeout"
    export PATH="$BATS_TEST_TMPDIR/tbin:$PATH" GH_PR_EXISTS=1 GH_PR_STALE_OID_CALLS=1
    ship
    [ "$status" -eq 0 ]
    [ "$(count '^gh pr view feature')" -eq 2 ]
    [ "$(count '^timeout 30 gh pr view feature')" -eq 2 ]
}
