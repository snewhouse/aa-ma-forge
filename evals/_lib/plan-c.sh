#!/usr/bin/env bash
# Scaffold for tests/fixtures/evals/plan-c/ (see scaffold.bash).
# A case links here; resolve the link so scaffold.bash is found beside the real file.
exec bash "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")/scaffold.bash" plan-c
