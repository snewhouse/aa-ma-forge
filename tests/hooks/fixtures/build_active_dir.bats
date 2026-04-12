#!/usr/bin/env bats
# build_active_dir.bats — self-test for the fixture builder.
#
# Exercises each documented behaviour of tests/hooks/fixtures/build_active_dir.sh
# so the fixture has its own red-green cycle rather than being exercised only
# indirectly through downstream consumer tests (M1.4/M2/M3/M4/M5).

setup() {
    FIXTURE_BIN="${BATS_TEST_DIRNAME}/build_active_dir.sh"
    BATS_TMP_FIXTURE="$(mktemp -d)"
    export BATS_TMP_FIXTURE
}

teardown() {
    [ -n "${BATS_TMP_FIXTURE:-}" ] && rm -rf "$BATS_TMP_FIXTURE"
}

@test "task_count=3 produces exactly 3 directories, each with 5 files" {
    run "$FIXTURE_BIN" "$BATS_TMP_FIXTURE/a" 3 plain
    [ "$status" -eq 0 ]

    dir_count=$(find "$BATS_TMP_FIXTURE/a" -mindepth 1 -maxdepth 1 -type d | wc -l)
    [ "$dir_count" -eq 3 ]

    for i in 1 2 3; do
        file_count=$(find "$BATS_TMP_FIXTURE/a/task-$i" -maxdepth 1 -type f | wc -l)
        [ "$file_count" -eq 5 ]
    done
}

@test "status_format variants emit expected markup" {
    run "$FIXTURE_BIN" "$BATS_TMP_FIXTURE/plain" 1 plain
    [ "$status" -eq 0 ]
    grep -Fxq -e '- Status: ACTIVE' "$BATS_TMP_FIXTURE/plain/task-1/task-1-tasks.md"
    run grep -Fxq -e '- **Status:** ACTIVE' "$BATS_TMP_FIXTURE/plain/task-1/task-1-tasks.md"
    [ "$status" -ne 0 ]

    run "$FIXTURE_BIN" "$BATS_TMP_FIXTURE/bold" 1 bold
    [ "$status" -eq 0 ]
    grep -Fxq -e '- **Status:** ACTIVE' "$BATS_TMP_FIXTURE/bold/task-1/task-1-tasks.md"

    run "$FIXTURE_BIN" "$BATS_TMP_FIXTURE/mixed" 2 mixed
    [ "$status" -eq 0 ]
    grep -Fxq -e '- **Status:** ACTIVE' "$BATS_TMP_FIXTURE/mixed/task-1/task-1-tasks.md"
    grep -Fxq -e '- Status: ACTIVE' "$BATS_TMP_FIXTURE/mixed/task-2/task-2-tasks.md"
}

@test "mtime_offsets applied verifiable via stat within 1s tolerance" {
    run "$FIXTURE_BIN" "$BATS_TMP_FIXTURE/m" 3 plain "-100,-50,0"
    [ "$status" -eq 0 ]

    now=$(date +%s)
    t1=$(stat -c %Y "$BATS_TMP_FIXTURE/m/task-1/task-1-tasks.md")
    t2=$(stat -c %Y "$BATS_TMP_FIXTURE/m/task-2/task-2-tasks.md")
    t3=$(stat -c %Y "$BATS_TMP_FIXTURE/m/task-3/task-3-tasks.md")

    d1=$((t1 - now))
    d2=$((t2 - now))
    d3=$((t3 - now))

    # Each within 1s of target offset
    [ "$d1" -ge -101 ] && [ "$d1" -le -99 ]
    [ "$d2" -ge -51 ] && [ "$d2" -le -49 ]
    [ "$d3" -ge -1 ] && [ "$d3" -le 1 ]
}

@test "--with-git creates an initialized repo with exactly one commit" {
    run "$FIXTURE_BIN" "$BATS_TMP_FIXTURE/g" 2 --with-git
    [ "$status" -eq 0 ]

    [ -d "$BATS_TMP_FIXTURE/g/.git" ]

    commit_count=$(git -C "$BATS_TMP_FIXTURE/g" rev-list --count HEAD)
    [ "$commit_count" -eq 1 ]
}

@test "bad task_count is rejected with a clear message" {
    run "$FIXTURE_BIN" "$BATS_TMP_FIXTURE/bad" abc
    [ "$status" -ne 0 ]
    [[ "$output" == *"task_count must be"* ]]
}

@test "unknown status_format is rejected" {
    run "$FIXTURE_BIN" "$BATS_TMP_FIXTURE/bad" 1 weird
    [ "$status" -ne 0 ]
    [[ "$output" == *"status_format must be"* ]]
}
