#!/usr/bin/env bats
# test_stage_b_scope.bats — verifies Stage B (scope-aware CI checks) and the
# L-007 guard that reverts out-of-scope drift.
#
# Plan §4 1.3 acceptance contract:
#   Given an in-scope `*.py` file with a lint error AND `tests/codemem/foo.py`
#   untouched by the branch (but dirty in the working tree), after Stage B
#   runs: `git diff tests/codemem/foo.py` produces zero bytes AND the in-scope
#   file passes `ruff check`.

setup() {
  # Repo root = three levels up from this test file
  REPO_ROOT="$(cd "$BATS_TEST_DIRNAME/../../.." && pwd)"
  # ruff lives in the project's .venv
  export PATH="$REPO_ROOT/.venv/bin:$PATH"

  TMPDIR="$(mktemp -d)"
  cd "$TMPDIR" || return 1
  git init -b main -q
  git config user.email "test@test.com"
  git config user.name "test"
  git config commit.gpgsign false
  mkdir -p tests/codemem src
  printf 'def foo():\n    return "foo"\n' > tests/codemem/foo.py
  git add tests/codemem/foo.py
  git commit -q -m "baseline"
  git checkout -b feat -q

  # Source stage functions from the canonical markdown (single source of truth)
  # shellcheck source=fixtures/load_stages.bash
  source "$REPO_ROOT/tests/commands/sole-dev-merge/fixtures/load_stages.bash"
  eval "$(SOLE_DEV_MERGE_MD=$REPO_ROOT/claude-code/commands/sole-dev-merge.md load_stages)"
}

teardown() {
  cd /
  rm -rf "$TMPDIR"
}

@test "Stage B: L-007 guard reverts out-of-scope drift, in-scope ruff fix lands" {
  # In-scope: src/x.py with lint errors (unused imports + bad spacing)
  printf 'import os\nimport sys\ndef hi():\n    return    "hi"\n' > src/x.py
  git add src/x.py
  git commit -q -m "feat"

  # Plant out-of-scope drift: modify tests/codemem/foo.py in working tree
  printf 'def foo():\n    return "MODIFIED OUT OF SCOPE"\n' > tests/codemem/foo.py

  run stage_b_scope
  [ "$status" -eq 0 ]

  # Acceptance #1: out-of-scope file fully reverted (L-007 guard worked)
  out_of_scope_diff_bytes=$(git diff tests/codemem/foo.py | wc -c)
  [ "$out_of_scope_diff_bytes" -eq 0 ]

  # Acceptance #2: in-scope file passes ruff check (auto-fix applied)
  run ruff check src/x.py
  [ "$status" -eq 0 ]
}

@test "Stage B: empty changeset is a no-op (Stage B does not error)" {
  # No commits ahead of main — Stage A normally catches this, but Stage B
  # itself should still be safe to invoke (changed_files empty → all steps
  # skip, L-007 guard reverts nothing).
  run stage_b_scope
  [ "$status" -eq 0 ]
  [[ "$output" == *"Stage B OK"* ]]
}

@test "Stage B: in-scope shell file is detected in scope set" {
  printf '#!/usr/bin/env bash\necho hi\n' > src/script.sh
  git add src/script.sh
  git commit -q -m "feat-sh"

  run stage_b_scope
  [ "$status" -eq 0 ]
  [[ "$output" == *"sh=1"* ]]
  [[ "$output" == *"py=0"* ]]
}

@test "Stage B: in-scope formatter changes survive (not reverted by L-007 guard)" {
  # Commit an in-scope file that ruff will reformat, then verify the file
  # IS dirty after Stage B (the L-007 guard must not touch in-scope files).
  printf 'def hi():\n    return    "hi"\n' > src/y.py
  git add src/y.py
  git commit -q -m "feat-y"

  run stage_b_scope
  [ "$status" -eq 0 ]

  # src/y.py is in scope → its ruff-format change should be in the working tree
  run git diff --name-only HEAD
  [[ "$output" == *"src/y.py"* ]]
}

@test "Stage B: pytest exit-5 (no tests collected) does NOT abort" {
  # Plant a `tests/` directory with no test files at all. Stage B's pytest
  # invocation should exit 5 (no tests collected) which we now treat as skip.
  # This is the canonical "tests/ holds only fixtures, no test_*.py" case
  # caught during M1.3 empirical run.
  mkdir -p tests/extra
  printf 'def helper(): return 1\n' > tests/extra/helpers.py
  printf 'def hi():\n    return "hi"\n' > src/z.py
  git add src/z.py tests/extra/helpers.py
  git commit -q -m "feat-no-collected-tests"

  run stage_b_scope
  [ "$status" -eq 0 ]
  [[ "$output" != *"ABORT: pytest"* ]]
}
