#!/usr/bin/env bats
# codemem-post-commit.bats — claude-code/codemem/hooks/post-commit.sh (M15.4, report 03 T4).
#
# Our own post-commit step: `codemem refresh` + `graphify update .` in a
# detached worker under flock; graphify-out/.built_sha gets the SHA captured
# at commit time, and only when graphify exits 0 (R03-D12). graphify is a
# stub here: it records start/end, can be held on a gate file, or fail.

setup() {
    FORGE="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)"
    HOOK="${FORGE}/claude-code/codemem/hooks/post-commit.sh"
    TMP="$(mktemp -d)"
    REPO="${TMP}/repo"
    STUBS="${TMP}/stubs"
    export STUB_LOG="${TMP}/stub.log"
    mkdir -p "$REPO" "$STUBS"
    cat > "${STUBS}/graphify" <<'EOF'
#!/usr/bin/env bash
echo "start $$" >> "$STUB_LOG"
if [[ -n "${STUB_GATE:-}" ]]; then
    while [[ -e "$STUB_GATE" ]]; do sleep 0.05; done
fi
[[ -n "${STUB_FAIL:-}" ]] && { echo "fail $$" >> "$STUB_LOG"; exit 3; }
mkdir -p graphify-out
git rev-parse HEAD > graphify-out/graph.json
echo "end $$" >> "$STUB_LOG"
EOF
    chmod +x "${STUBS}/graphify"
    export PATH="${STUBS}:/usr/local/bin:/usr/bin:/bin"
    cd "$REPO" || return 1
    git init -q -b main
    git config user.email t@example.invalid
    git config user.name t
    git config commit.gpgsign false
    printf '.codemem/\ngraphify-out/\n' > .gitignore
    printf 'def a():\n    return 1\n' > a.py
    git add -A
    git commit -qm seed
    mkdir -p .git/hooks
    printf '#!/usr/bin/env bash\n"%s" || true\n' "$HOOK" > .git/hooks/post-commit
    chmod +x .git/hooks/post-commit
}

teardown() {
    pkill -f "post-commit.sh --worker [0-9a-f]* ${REPO}" 2>/dev/null || true  # why: a gated test worker must not outlive its repo
    [[ -n "${TMP:-}" ]] && rm -rf "$TMP"
}

commit_change() {
    printf 'def a():\n    return %s\n' "$1" > a.py
    git add a.py
    git commit -qm "c$1"
}

# Wait (≤ 30 s) until no worker for this repo is running.
drain() {
    local i
    for ((i = 0; i < 300; i++)); do
        pgrep -f "post-commit.sh --worker [0-9a-f]* ${REPO}" > /dev/null || return 0
        sleep 0.1
    done
    return 1
}

@test "after a commit both sidecars equal HEAD" {
    commit_change 2
    drain
    head=$(git rev-parse HEAD)
    [ "$(cat .codemem/last_sha)" = "$head" ]
    [ "$(cat graphify-out/.built_sha)" = "$head" ]
}

@test "the hook returns at once while the worker is held" {
    touch "${TMP}/gate"
    start=$(date +%s%N)
    STUB_GATE="${TMP}/gate" commit_change 2
    elapsed_ms=$(( ($(date +%s%N) - start) / 1000000 ))
    [ "$elapsed_ms" -lt 2000 ]
    rm -f "${TMP}/gate"
    drain
}

@test "graphify failing keeps the previous .built_sha and logs one line" {
    commit_change 2
    drain
    old=$(cat graphify-out/.built_sha)
    STUB_FAIL=1 commit_change 3
    drain
    [ "$(cat graphify-out/.built_sha)" = "$old" ]
    [ "$(grep -c 'graphify update failed' .codemem/refresh.log)" -eq 1 ]
}

@test "a killed graphify run keeps the previous .built_sha" {
    commit_change 2
    drain
    old=$(cat graphify-out/.built_sha)
    touch "${TMP}/gate"
    STUB_GATE="${TMP}/gate" commit_change 3
    for ((i = 0; i < 50; i++)); do grep -q start "$STUB_LOG" && [ "$(grep -c start "$STUB_LOG")" -ge 2 ] && break; sleep 0.1; done
    pkill -9 -f "post-commit.sh --worker [0-9a-f]* ${REPO}"
    pkill -9 -f "${STUBS}/graphify"
    rm -f "${TMP}/gate"
    [ "$(cat graphify-out/.built_sha)" = "$old" ]
}

@test "race: two workers, A released last → .built_sha == A (flock + start SHA)" {
    commit_change 2
    sha_a=$(git rev-parse HEAD)
    commit_change 3
    sha_b=$(git rev-parse HEAD)
    drain
    : > "$STUB_LOG"
    touch "${TMP}/gate"
    STUB_GATE="${TMP}/gate" bash "$HOOK" --worker "$sha_b" "$REPO" &
    for ((i = 0; i < 100; i++)); do grep -q start "$STUB_LOG" && break; sleep 0.05; done
    bash "$HOOK" --worker "$sha_a" "$REPO" &
    sleep 0.5
    # A is queued on the lock: graphify ran once (B, held), nothing finished.
    [ "$(grep -c start "$STUB_LOG")" -eq 1 ]
    rm -f "${TMP}/gate"
    wait
    [ "$(cat graphify-out/.built_sha)" = "$sha_a" ]
    # Serialised: no start between a start and its end.
    run awk '/^start/ { if (open) bad = 1; open = 1 } /^end/ { open = 0 } END { exit bad }' "$STUB_LOG"
    [ "$status" -eq 0 ]
}

@test "graphify absent → one notice, codemem still refreshed, exit 0" {
    rm -f "${STUBS}/graphify"
    commit_change 2
    drain
    [ "$(cat .codemem/last_sha)" = "$(git rev-parse HEAD)" ]
    [ ! -e graphify-out/.built_sha ]
    [ "$(grep -c 'graphify not found' .codemem/refresh.log)" -eq 1 ]
}

@test "a relative PATH entry cannot run a repo-planted graphify" {
    printf '#!/bin/sh\ntouch "%s/planted-ran"\n' "$TMP" > graphify
    chmod +x graphify
    rm -f "${STUBS}/graphify"
    PATH=".:${PATH}" commit_change 2
    drain
    [ ! -e "${TMP}/planted-ran" ]
}

@test "a symlinked .built_sha is replaced, never followed" {
    mkdir -p graphify-out
    printf 'original\n' > "${TMP}/victim"
    ln -s "${TMP}/victim" graphify-out/.built_sha
    commit_change 2
    drain
    [ "$(cat "${TMP}/victim")" = "original" ]
    [ ! -L graphify-out/.built_sha ]
    [ "$(cat graphify-out/.built_sha)" = "$(git rev-parse HEAD)" ]
}

@test "a symlinked refresh.log is never appended to" {
    mkdir -p .codemem
    printf 'original\n' > "${TMP}/victim"
    ln -s "${TMP}/victim" .codemem/refresh.log
    STUB_FAIL=1 commit_change 2
    drain
    [ "$(cat "${TMP}/victim")" = "original" ]
}

@test "a worker refuses a SHA that is not 40-hex" {
    run bash "$HOOK" --worker "--output=/tmp/x" "$REPO"
    [ "$status" -eq 0 ]
    [ ! -e graphify-out/.built_sha ]
    [ ! -s "$STUB_LOG" ]
}

@test "rebase / cherry-pick / merge commits spawn no worker" {
    GIT_REFLOG_ACTION=rebase run bash "$HOOK"
    [ "$status" -eq 0 ]
    sleep 0.3
    [ ! -s "$STUB_LOG" ]
}

@test "the hook never fails a commit (exit 0 outside a repo)" {
    cd "$TMP"
    run bash "$HOOK"
    [ "$status" -eq 0 ]
}

@test "§6.6: no flock (stock macOS) still refreshes codemem; only the graph step is skipped" {
    nf="${TMP}/noflock-bin"
    mkdir -p "$nf"
    for d in /usr/local/bin /usr/bin /bin; do
        for f in "$d"/*; do
            b="${f##*/}"
            [[ "$b" == flock || -e "${nf}/${b}" ]] || ln -s "$f" "${nf}/${b}"
        done
    done
    PATH="${STUBS}:${nf}" commit_change 2
    drain
    [ "$(cat .codemem/last_sha)" = "$(git rev-parse HEAD)" ]
    [ ! -e graphify-out/.built_sha ]
    grep -q 'flock not found' .codemem/refresh.log
}

@test "§6.6: a .built_sha write that fails is logged" {
    commit_change 2
    drain
    chmod 555 graphify-out
    commit_change 3
    drain
    chmod 755 graphify-out
    grep -q 'post-commit: .*built_sha' .codemem/refresh.log
}

# --- §6.8 (M15): repo-controlled dirs, SHA-256, and bounded steps -----------

@test "§6.8: a symlinked graphify-out is never written through" {
    mkdir -p "${TMP}/victim-dir"
    ln -s "${TMP}/victim-dir" graphify-out
    commit_change 2
    drain
    [ -z "$(ls -A "${TMP}/victim-dir")" ]
    grep -q 'graphify-out is a symlink' .codemem/refresh.log
}

@test "§6.8: a symlinked .codemem/ is never refreshed through" {
    mkdir -p "${TMP}/victim-dir"
    printf 'keep\n' > "${TMP}/victim-dir/index.db"
    ln -s "${TMP}/victim-dir" .codemem
    commit_change 2
    drain
    [ "$(ls -A "${TMP}/victim-dir")" = "index.db" ]
    [ "$(cat "${TMP}/victim-dir/index.db")" = "keep" ]
}

@test "§6.8: a worker accepts a 64-hex (SHA-256) SHA" {
    sha=$(printf 'a%.0s' {1..64})
    run bash "$HOOK" --worker "$sha" "$REPO"
    [ "$status" -eq 0 ]
    [ "$(cat graphify-out/.built_sha)" = "$sha" ]
}

@test "§6.8: each step runs under timeout and the queue waits with flock -w" {
    real_flock=$(command -v flock)
    printf '#!/usr/bin/env bash\necho "timeout $*" >> "$STUB_LOG"\nshift\nexec "$@"\n' > "${STUBS}/timeout"
    printf '#!/usr/bin/env bash\necho "flock $*" >> "$STUB_LOG"\nexec %s "$@"\n' "$real_flock" > "${STUBS}/flock"
    chmod +x "${STUBS}/timeout" "${STUBS}/flock"
    commit_change 2
    drain
    grep -qE '^timeout [0-9]+ .*/graphify update \.$' "$STUB_LOG"
    grep -qE '^timeout [0-9]+ .*codemem refresh$' "$STUB_LOG"
    grep -qE '^timeout [0-9]+ .*codemem refresh-commits$' "$STUB_LOG"
    grep -qE '^flock -w [0-9]+ 9$' "$STUB_LOG"
    [ "$(cat graphify-out/.built_sha)" = "$(git rev-parse HEAD)" ]
}

@test "§6.8: a timed-out graphify (rc 124) keeps .built_sha and says so" {
    printf '#!/usr/bin/env bash\nexit 124\n' > "${STUBS}/graphify"
    commit_change 2
    drain
    [ ! -e graphify-out/.built_sha ]
    grep -q 'graphify update timed out after [0-9]*s' .codemem/refresh.log
}
