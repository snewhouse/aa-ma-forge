#!/usr/bin/env bash
# Regenerate every generated artifact that a CI drift check compares (ADR-0016):
#   docs/architecture/                 codemem draw --write     (architecture-drift job)
#   tests/golden/plugin-surface.json   plugin-surface golden    (codemem-smoke job)
# Run after any change to imports/calls, claude-code/ references, scripts/install.sh
# hook wiring, or docs/architecture.captions.json. Review `git diff` — the diff IS the
# architecture change. The index is rebuilt first: a stale one disagrees with CI (L-024).
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
uv run codemem build
uv run codemem draw --write
uv run python tests/codemem/test_plugin_surface.py
uv run codemem draw --check
git status --short -- docs/architecture tests/golden/plugin-surface.json
