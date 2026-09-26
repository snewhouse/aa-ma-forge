#!/usr/bin/env bash
# Regenerate the MRS_BUDGET lines for <repo> at <sha> (diagram-generation M13, AC1).
#
# One line per level, the whole-repo cut `codemem draw` emits (tests excluded):
#   MRS_BUDGET L<n> nodes=<int> edges=<int> chars=<int>
# `chars` counts the mermaid text in characters. Builds a throwaway index from
# `git archive <sha>`, never the worktree, so the lines are a function of the sha
# alone. Read-only on the measured repo.
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: $0 <repo> <sha>" >&2
  exit 2
fi
root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)  # this checkout's codemem, from any cwd
repo=$(cd "$1" && pwd)
sha=$(git -C "${repo}" rev-parse --verify "$2^{commit}")
tmp=$(mktemp -d)
trap 'rm -rf -- "${tmp}"' EXIT

mkdir "${tmp}/src"
git -C "${repo}" archive "${sha}" | tar -x -C "${tmp}/src"
uv run --quiet --project "${root}" codemem --db "${tmp}/index.db" build --repo-root "${tmp}/src" >/dev/null 2>&1
for level in L0 L1 L2 L3; do
  uv run --quiet --project "${root}" codemem --db "${tmp}/index.db" draw --level "${level}" \
    >"${tmp}/out.mmd" 2>"${tmp}/err"
  # stderr: `codemem draw: L2 69 nodes / 97 edges[ (+N dropped …)]`
  read -r _ _ _ nodes _ _ edges _ <"${tmp}/err"
  printf 'MRS_BUDGET %s nodes=%s edges=%s chars=%s\n' "${level}" "${nodes}" "${edges}" \
    "$(LC_ALL=C.UTF-8 wc -m <"${tmp}/out.mmd" | tr -d ' ')"
done
