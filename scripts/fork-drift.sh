#!/usr/bin/env bash
# fork-drift.sh — Drift/Orphan detector for every fork in claude-code/skills/FORKS.json.
#
# Fetches each manifest file from mattpocock/skills at <ref> via `gh api`, then
# feeds {file: md5|null} to the pure classifier (`python -m aa_ma.forks classify`).
# This script is the ONLY place that fetches (eng-review 3A / OV2 — never the
# plugin cache).
#
# Usage: scripts/fork-drift.sh [--sha <ref>] [--manifest <path>]
# Exit:  0 ok · 1 gh missing / network / auth / empty content · 2 usage
#
# Only HTTP 404 becomes `null` → ORPHAN. 403/auth/network exit 1 — a fork is
# never reported ORPHAN because the fetch was refused.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
SHA="main"
MANIFEST="${REPO_ROOT}/claude-code/skills/FORKS.json"
read -r -a GH <<< "${GH:-gh}"   # env seam so bats can stub it (release.sh precedent)

while [[ $# -gt 0 ]]; do
  case "$1" in
    --sha)      SHA="${2:?--sha needs a ref}"; shift 2 ;;
    --manifest) MANIFEST="${2:?--manifest needs a path}"; shift 2 ;;
    -h|--help)  sed -n '2,13p' "$0"; exit 0 ;;
    *)          echo "usage: $0 [--sha <ref>] [--manifest <path>]" >&2; exit 2 ;;
  esac
done

command -v "${GH[0]}" >/dev/null 2>&1 || { echo "fork-drift: gh CLI not found (${GH[0]}) — install/authenticate gh, or set GH=" >&2; exit 1; }
[[ -f "$MANIFEST" ]] || { echo "fork-drift: manifest not found: $MANIFEST" >&2; exit 2; }

err="$(mktemp)"; trap 'rm -f "$err"' EXIT

# One row per (skill, file): "<skill>\t<upstream>\t<file>"
while IFS=$'\t' read -r skill upstream file; do
  if body=$("${GH[@]}" api "repos/mattpocock/skills/contents/${upstream}/${file}?ref=${SHA}" --jq .content 2>"$err"); then
    [[ -n "$body" ]] || { echo "fork-drift: empty content for ${upstream}/${file} (file >1 MB?) — refusing" >&2; exit 1; }
    md5=$(printf '%s' "$body" | base64 -d | md5sum | cut -d' ' -f1)
    printf '%s\t%s\t%s\n' "$skill" "$file" "$md5"
  elif grep -q 'HTTP 404' "$err"; then
    printf '%s\t%s\t%s\n' "$skill" "$file" "null"          # ONLY 404 → ORPHAN
  else
    cat "$err" >&2; exit 1                                  # 403/auth/network → never ORPHAN
  fi
done < <(python3 -c '
import json, sys
for name, row in json.load(open(sys.argv[1])).items():
    for f in row["files"]:
        print(name, row["upstream"], f, sep="\t")
' "$MANIFEST") | python3 -c '
import json, sys, collections
by = collections.defaultdict(dict)
for line in sys.stdin:
    skill, f, md5 = line.rstrip("\n").split("\t")
    by[skill][f] = None if md5 == "null" else md5
json.dump(by, sys.stdout)
' > "${err}.json"

while IFS=$'\t' read -r skill fetched; do
  uv run --quiet --project "$REPO_ROOT" python -m aa_ma.forks classify "$skill" "$fetched" --manifest "$MANIFEST"
done < <(python3 -c '
import json, sys
for skill, fetched in json.load(open(sys.argv[1])).items():
    print(skill, json.dumps(fetched), sep="\t")
' "${err}.json")
rm -f "${err}.json"
