#!/usr/bin/env bash
# Scaffold for tests/fixtures/evals/py-review/ (see scaffold.bash).
# A case links here; resolve the link so scaffold.bash is found beside the real file.
set -euo pipefail
real="$(readlink -f "${BASH_SOURCE[0]}")"
dir="$(dirname "${real}")"
exec bash "${dir}/scaffold.bash" py-review
