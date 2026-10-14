#!/usr/bin/env bash
# Shared "SHA vs HEAD" fixture (M15.5; report 03 X1/X2 shared-logic test).
#
# Usage: make-repo.sh <dir>
# Creates <dir> as a git repo with three commits C1..C3 and both sidecars:
#   .codemem/index.db (empty) + .codemem/last_sha = C1   → codemem 2 behind
#   graphify-out/.built_sha = C3                         → graphify 0 behind
# Read by tests/hooks/session-start-code-intel.bats (shell) and
# tests/codemem/test_x2_envelope.py (Python) so both compute against one repo.
set -euo pipefail
dir="$1"
mkdir -p "$dir"
cd "$dir"
git init -q -b main
git config user.email t@example.invalid
git config user.name t
git config commit.gpgsign false
printf '.codemem/\ngraphify-out/\n' > .gitignore
for i in 1 2 3; do
    printf 'def f():\n    return %s\n' "$i" > a.py
    git add -A
    git commit -q -m "c$i"
done
mkdir -p .codemem graphify-out
: > .codemem/index.db
git rev-parse HEAD~2 > .codemem/last_sha
git rev-parse HEAD > graphify-out/.built_sha
