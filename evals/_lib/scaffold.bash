#!/usr/bin/env bash
# Shared scaffold: copy evals/_fixtures/<name>/ into the run's empty workspace and make it
# a git repo with no remote. Called by evals/_lib/<name>.sh, which each case links to.
set -euo pipefail
name="${1:?fixture name}"
src="$(cd "$(dirname "${BASH_SOURCE[0]}")/../_fixtures/${name}" && pwd)"
cp -R "${src}/." .
git init -q .
git add -A
git -c user.name=eval -c user.email=eval@example.invalid commit -q -m "fixture: ${name}"
