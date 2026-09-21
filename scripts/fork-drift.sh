#!/usr/bin/env bash
# fork-drift.sh — Drift/Orphan detector for every fork in claude-code/skills/FORKS.json.
#
# Fetches each manifest file from mattpocock/skills at <ref> via `gh api`, then
# feeds `skill<TAB>file<TAB>md5|null` rows to the pure classifier
# (`python -m aa_ma.forks classify-all`). This script is the ONLY place that
# fetches (eng-review 3A / OV2 — never the plugin cache). The manifest is read
# by `aa_ma.forks` alone, so a malformed manifest fails closed with a named key.
#
# Usage: scripts/fork-drift.sh [--sha <ref>] [--manifest <path>]
# Exit:  0 ok · 1 gh missing / network / auth / bad manifest / empty content · 2 usage
#
# Only HTTP 404 on a FILE becomes `null` → ORPHAN. 403/auth/network exit 1, and
# the repo itself is checked first (GitHub answers 404, not 403, for a repo the
# caller cannot see) — a fork is never reported ORPHAN because the fetch was refused.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
SHA="main"
MANIFEST="${REPO_ROOT}/claude-code/skills/FORKS.json"
read -r -a GH <<< "${GH:-gh}"   # env seam so bats can stub it (release.sh precedent)

while [[ $# -gt 0 ]]; do
  case "$1" in
    --sha)      SHA="${2:?--sha needs a ref}"; shift 2 ;;
    --manifest) MANIFEST="${2:?--manifest needs a path}"; shift 2 ;;
    -h|--help)  awk 'NR==1{next} /^#/{print; next} {exit}' "$0"; exit 0 ;;
    *)          echo "usage: $0 [--sha <ref>] [--manifest <path>]" >&2; exit 2 ;;
  esac
done

command -v "${GH[0]}" >/dev/null 2>&1 || { echo "fork-drift: gh CLI not found (${GH[0]}) — install/authenticate gh, or set GH=" >&2; exit 1; }
[[ -f "$MANIFEST" ]] || { echo "fork-drift: manifest not found: $MANIFEST" >&2; exit 2; }

forks() { uv run --quiet --project "$REPO_ROOT" python -m aa_ma.forks "$@" --manifest "$MANIFEST"; }

rows="$(forks files)"   # validates the manifest before any fetch; ValueError → exit 1 under set -e

"${GH[@]}" api "repos/mattpocock/skills" --jq .full_name >/dev/null \
  || { echo "fork-drift: repos/mattpocock/skills unreachable — not classifying (a hidden repo must not look like missing files)" >&2; exit 1; }

err="$(mktemp)"; trap 'rm -f "$err"' EXIT

# Fetch everything first; classify only a complete fetch (a mid-loop failure must not
# leave the classifier holding partial rows, where every unfetched file reads as ORPHAN).
fetch_all() {
  while IFS=$'\t' read -r skill upstream file; do
    if body=$("${GH[@]}" api "repos/mattpocock/skills/contents/${upstream}/${file}?ref=${SHA}" --jq .content 2>"$err"); then
      [[ -n "$body" ]] || { echo "fork-drift: empty content for ${upstream}/${file} (file >1 MB?) — refusing" >&2; return 1; }
      printf '%s\t%s\t%s\n' "$skill" "$file" "$(printf '%s' "$body" | base64 -d | md5sum | cut -d' ' -f1)"
    elif grep -q 'HTTP 404' "$err"; then
      printf '%s\t%s\tnull\n' "$skill" "$file"                # ONLY a file-level 404 → ORPHAN
    else
      cat "$err" >&2; return 1                                # 403/auth/network → never ORPHAN
    fi
  done <<< "$rows"
}
fetched="$(fetch_all)"
forks classify-all <<< "$fetched"
