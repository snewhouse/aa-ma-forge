#!/usr/bin/env bats
# predicted-vs-actual.bats — claude-code/skills/execute-aa-ma-milestone/scripts/predicted-vs-actual.sh
# (code-conventions-impact 10.7; §6.3 of /execute-aa-ma-milestone, advisory in M10).
#
# changed   = git diff merge-base(main)..HEAD ∪ staged ∪ unstaged ∪ untracked-not-ignored
# predicted = the ACTIVE milestone's Contract paths ∪ their codemem co_changes partners
#             (threshold 5 shared commits, min-ratio 0.5)
# One `UNPREDICTED <path>` line per changed, unpredicted file; exit 0; exit 2 only when it
# cannot run (bad task name, missing plan/tasks, no milestone, no default branch).

bats_require_minimum_version 1.5.0

setup() {
    FORGE="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)"
    PVA="${FORGE}/claude-code/skills/execute-aa-ma-milestone/scripts/predicted-vs-actual.sh"
    WORK="$(mktemp -d "${BATS_TMPDIR}/pva.XXXXXX")"
    WORK="$(cd "$WORK" && pwd -P)"
    R="$WORK/r"
    T="$R/.claude/dev/active/t"
    export XDG_CACHE_HOME="$WORK/cache"
    unset CODEMEM_DB CODEMEM_BIN
    export FORGE PVA WORK R T
    _mkrepo
}

teardown() {
    rm -rf "$WORK"
}

_git() { git -C "$R" -c user.name=t -c user.email=t@t -c commit.gpgsign=false -c core.autocrlf=false "$@"; }

# Milestone 2 (ACTIVE) predicts a.py, tests/test_a.py and everything under lib/.
_mkrepo() {
    mkdir -p "$T" "$R/lib" "$R/tests"
    cp "${FORGE}/tests/hooks/fixtures/gate-scans/one-active-tasks.md" "$T/t-tasks.md"
    cat > "$T/t-plan.md" <<'EOF'
# Plan

### Milestone 1 — Done already
#### Contract
```
  Modify  old.py
```

### Milestone 2 — The one being gated
#### Contract
```
Files:
  Modify  a.py   # main change
  Modify  lib/
  Test    tests/test_a.py
```
EOF
    printf 'ignored.txt\n' > "$R/.gitignore"
    for f in a.py b.py old.py lib/x.py tests/test_a.py gone.py; do printf 'x\n' > "$R/$f"; done
    git init -q -b main "$R"
    _git add -A && _git commit -qm init
    _git checkout -q -b feat
}

# Point codemem at a stub that records its argv and prints $WORK/cm.json.
_stub_codemem() {
    mkdir -p "$WORK/cm"
    : > "$WORK/cm/index.db"
    export CODEMEM_DB="$WORK/cm/index.db"
    cat > "$WORK/codemem" <<'EOF'
#!/usr/bin/env bash
printf '%s\n' "$@" > "${WORK}/codemem.args"
cat "${WORK}/cm.json"
EOF
    chmod +x "$WORK/codemem"
    export CODEMEM_BIN="$WORK/codemem"
}

_run() { run bash -c 'cd "$R" && bash "$PVA" "$@"' _ "$@"; }

_unpredicted() { printf '%s\n' "$output" | sed -n 's/^UNPREDICTED //p'; }

@test "usage: no task name or an unsafe one exits 2" {
    _run
    [ "$status" -eq 2 ]
    _run '../x'
    [ "$status" -eq 2 ]
}

@test "missing plan exits 2 and names it" {
    rm "$T/t-plan.md"
    _run t
    [ "$status" -eq 2 ]
    [[ "$output" == *"t-plan.md"* ]]
}

@test "no default branch to take the merge-base from exits 2" {
    _git branch -q -m main trunk
    _run t
    [ "$status" -eq 2 ]
    [[ "$output" == *"merge-base"* ]]
}

@test "committed, staged, unstaged, untracked and deleted changes; Contract rows predict" {
    printf 'y\n' >> "$R/a.py"; printf 'y\n' >> "$R/b.py"; printf 'y\n' >> "$R/lib/x.py"
    printf 'y\n' >> "$R/tests/test_a.py"
    _git add -A && _git commit -qm work
    printf 'y\n' >> "$R/old.py" && _git add old.py          # staged
    printf 'n\n' > "$R/lib/new.py"                          # untracked, under a predicted dir
    printf 'n\n' > "$R/c.txt"                               # untracked
    printf 'n\n' > "$R/ignored.txt"                         # ignored: not a change
    rm "$R/gone.py"                                         # deleted, unstaged
    printf 'p\n' >> "$T/t-tasks.md"                         # .claude/dev/** is never unpredicted
    _run t
    [ "$status" -eq 0 ]
    [ "$(_unpredicted)" = "$(printf '%s\n' b.py c.txt gone.py old.py)" ]
    [[ "$output" == *"co_changes skipped"* ]]   # no codemem index: said, not silent
    [[ "$output" == *"changed=8 predicted=3 cochange=0 unpredicted=4"* ]]
}

@test "co_changes partners of Contract files are predicted; T7 constants passed" {
    _stub_codemem
    cat > "$WORK/cm.json" <<'EOF'
{"a.py": {"files": [{"path": "b.py", "count": 6, "ratio": 0.8}], "target": "a.py", "error": null},
 "lib/": {"files": [], "target": "lib/", "error": null},
 "tests/test_a.py": {"files": [], "target": "tests/test_a.py", "error": null}}
EOF
    printf 'y\n' >> "$R/a.py"; printf 'y\n' >> "$R/b.py"; printf 'y\n' >> "$R/old.py"
    _git add -A && _git commit -qm work
    _run t
    [ "$status" -eq 0 ]
    [ "$(_unpredicted)" = "old.py" ]
    [[ "$output" == *"cochange=1"* ]]
    run cat "$WORK/codemem.args"
    [ "${lines[0]}" = query ] && [ "${lines[1]}" = co_changes ]
    [[ "$output" == *$'--threshold\n5\n--min-ratio\n0.5'* ]]
    [[ "$output" == *$'--\na.py\nlib/\ntests/test_a.py'* ]]
}

@test "a single-path co_changes object (not keyed by path) is read too" {
    _stub_codemem
    cat > "$T/t-plan.md" <<'EOF'
### Milestone 2 — The one being gated
#### Contract
```
  Modify  a.py
```
EOF
    printf '{"files": [{"path": "b.py", "count": 5, "ratio": 0.5}], "target": "a.py", "error": null}\n' > "$WORK/cm.json"
    printf 'y\n' >> "$R/a.py"; printf 'y\n' >> "$R/b.py"
    _git add -A && _git commit -qm work
    _run t
    [ "$status" -eq 0 ]
    [ -z "$(_unpredicted)" ]
}

@test "codemem failing is a NOTE, never a silent empty partner set" {
    _stub_codemem
    printf 'not json\n' > "$WORK/cm.json"
    printf 'y\n' >> "$R/b.py" && _git add -A && _git commit -qm work
    _run t
    [ "$status" -eq 0 ]
    [ "$(_unpredicted)" = "b.py" ]
    [[ "$output" == *"NOTE: co_changes skipped"* ]]
}

@test "no Contract rows for the milestone: one NOTE, no UNPREDICTED lines, exit 0" {
    printf '### Milestone 2 — The one being gated\nNo contract here.\n' > "$T/t-plan.md"
    printf 'y\n' >> "$R/b.py" && _git add -A && _git commit -qm work
    _run t
    [ "$status" -eq 0 ]
    [ -z "$(_unpredicted)" ]
    [[ "$output" == *"no Contract rows for Milestone 2"* ]]
}

@test "a control character in a changed path is neutralised in the line" {
    printf 'n\n' > "$R/"$'evil\033[2Jname.txt'
    _run t
    [ "$status" -eq 0 ]
    [ "$(_unpredicted)" = "evil?[2Jname.txt" ]
}

@test "real codemem: a 5-commit co-change partner is predicted (keys contract)" {
    local cm="${FORGE}/.venv/bin/codemem"
    [ -x "$cm" ] || skip "no ${cm} — run uv sync"
    _git checkout -q main
    for i in 1 2 3 4 5; do
        printf '%s\n' "$i" >> "$R/a.py"; printf '%s\n' "$i" >> "$R/b.py"
        _git add -A && _git commit -qm "pair $i"
    done
    _git checkout -q -B feat
    "$cm" build --repo-root "$R" >/dev/null 2>&1   # why: setup noise; the assert below fails if it did not build
    "$cm" refresh-commits --repo-root "$R" >/dev/null 2>&1   # why: as above
    printf 'y\n' >> "$R/a.py"; printf 'y\n' >> "$R/b.py"; printf 'y\n' >> "$R/old.py"
    CODEMEM_BIN="$cm" _run t
    [ "$status" -eq 0 ]
    [ "$(_unpredicted)" = "old.py" ]
    [[ "$output" == *"cochange=1"* ]]
}
