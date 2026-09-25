#!/usr/bin/env bash
# Regenerate the IO_DENSE_BAND line for <repo> at <sha> (diagram-generation M9, AC6).
#
# Builds a throwaway codemem index from `git archive <sha>`, never from the worktree,
# so the count is a function of the sha alone. Read-only on the measured repo.
set -euo pipefail

if [[ $# -ne 2 ]]; then
  echo "usage: $0 <repo> <sha>" >&2
  exit 2
fi
repo=$(cd "$1" && pwd)
sha=$(git -C "${repo}" rev-parse --verify "$2^{commit}")
tmp=$(mktemp -d)
trap 'rm -rf -- "${tmp}"' EXIT

mkdir "${tmp}/src"
git -C "${repo}" archive "${sha}" | tar -x -C "${tmp}/src"
uv run --quiet codemem --db "${tmp}/index.db" build --repo-root "${tmp}/src" >/dev/null
uv run --quiet python -m codemem.draw.io_sinks band "${tmp}/index.db" "$(basename "${repo}")" "${sha}"
