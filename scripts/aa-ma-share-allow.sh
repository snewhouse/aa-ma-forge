#!/usr/bin/env bash
# Allowlist for /aa-ma-share. Exit 0 = may publish, 1 = refuse. Pattern has no leading
# separator so relative (docs/adr/x.md), ./-prefixed and absolute paths all match.
# The command calls this script; no instruction in a conversation overrides it.
set -euo pipefail
case "${1:-}" in
  *../*|*/..) echo "refused: parent-directory segments are not allowed" >&2; exit 1 ;;
  *-plan.md|*docs/adr/*.md|*docs/spec/*.md) exit 0 ;;
  *) echo "refused: only *-plan.md, docs/adr/*.md, docs/spec/*.md may be shared" >&2; exit 1 ;;
esac
