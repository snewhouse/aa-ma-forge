#!/usr/bin/env bash
# Regenerate every generated artifact that a CI drift check compares (ADR-0016):
#   docs/architecture/                 codemem draw --write     (architecture-drift job)
#   tests/golden/plugin-surface.json   plugin-surface golden    (codemem-smoke job)
# Run after any change to imports/calls, claude-code/ references, scripts/install.sh
# hook wiring, or docs/architecture.captions.json. Review `git diff` — the diff IS the
# architecture change. The index is rebuilt first: a stale one disagrees with CI (L-024).
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
# The index reads `git ls-files`, so an untracked source file is invisible to it and to
# CI: the docs would describe a tree nobody committed (diagram-generation M9, L-026).
mapfile -t exts < <(uv run --quiet python -c \
  'from codemem.indexer import _INDEXABLE_EXTENSIONS as e; print("\n".join("*" + x for x in sorted(e)))')
untracked=$(git ls-files --others --exclude-standard -- "${exts[@]}")
if [[ -n "${untracked}" ]]; then
  printf 'regen-generated: untracked source files are not indexed; git add them first:\n%s\n' "${untracked}" >&2
  exit 1
fi
uv run codemem build
uv run codemem draw --write
uv run python tests/codemem/test_plugin_surface.py
uv run codemem draw --check
git status --short -- docs/architecture tests/golden/plugin-surface.json
