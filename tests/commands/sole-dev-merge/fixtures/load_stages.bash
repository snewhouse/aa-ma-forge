#!/usr/bin/env bash
# load_stages.bash — extracts every ```bash ... ``` block from the
# /sole-dev-merge command markdown and emits them concatenated to stdout, so a
# bats test (or one-shot harness) can `source <(load_stages)` and call the
# stage functions directly.
#
# The command markdown is the single source of truth for the workflow logic
# (per plan §1.1: "All workflow logic lives inline in the command markdown as
# named bash blocks — no skill/lib scaffolding"). This extractor preserves
# that invariant for tests — no duplication, no drift.
#
# Usage:
#   source "$BATS_TEST_DIRNAME/fixtures/load_stages.bash"
#   load_stages | source /dev/stdin
#   stage_a_preflight && echo OK
#
# Or:
#   eval "$(load_stages)"
#
# Implementation notes:
# - Markdown fences must be exactly ```bash on opening and ``` on closing.
# - Only fenced bash blocks are extracted; inline `code` and other languages
#   are ignored.
# - The function returns 0 on success, 1 if the command file is not found.

load_stages() {
  local md_file="${SOLE_DEV_MERGE_MD:-}"

  if [ -z "$md_file" ]; then
    # Default: locate the command relative to this fixture's location
    local fixture_dir
    fixture_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    # fixture_dir = .../tests/commands/sole-dev-merge/fixtures
    # repo root   = fixture_dir/../../../..
    md_file="${fixture_dir}/../../../../claude-code/commands/sole-dev-merge.md"
  fi

  if [ ! -f "$md_file" ]; then
    echo "load_stages: command markdown not found: $md_file" >&2
    return 1
  fi

  awk '
    /^```bash$/ { in_block=1; next }
    /^```$/     { in_block=0; next }
    in_block    { print }
  ' "$md_file"
}
