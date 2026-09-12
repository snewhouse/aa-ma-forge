#!/usr/bin/env bash
# release.sh — cut a release deterministically: no amend, no retag, no CHANGELOG surgery.
#
#   scripts/release.sh <major|minor|patch> --headline "<one-line theme>" [--dry-run] [--no-push]
#
# The script edits CHANGELOG.md (`## Unreleased` → `## vX.Y.Z (date)`) and the README
# "Current version" line FIRST; commitizen's bump commit is `git commit -a`, so those edits
# ride in cz's own commit next to VERSION/pyproject.toml, and `annotated_tag = true` tags
# it. `update_changelog_on_bump = false` keeps cz away from the curated notes (L-006).
# Then push with tags and publish a GitHub Release whose notes are the new section.
#
# Exit: 0 ok · 1 preflight refusal (reason on stderr) · 2 usage.
# Env seams (tests stub them): CZ (default "uv run cz"), GH (default "gh").
set -euo pipefail

usage() { echo "usage: scripts/release.sh <major|minor|patch> --headline \"<text>\" [--dry-run] [--no-push]" >&2; exit 2; }
refuse() { echo "release: refused — $*" >&2; exit 1; }

INC="${1:-}"; [[ -n "$INC" ]] || usage; shift
HEADLINE=""; DRY=0; NOPUSH=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --headline) HEADLINE="${2:-}"; shift 2 ;;
    --dry-run) DRY=1; shift ;;
    --no-push) NOPUSH=1; shift ;;
    *) usage ;;
  esac
done
read -r -a CZ <<< "${CZ:-uv run cz}"   # may carry args ("uv run cz"); tests point it at a stub
read -r -a GH <<< "${GH:-gh}"

# --- preflight ---------------------------------------------------------------------------
case "$INC" in major|minor|patch) ;; *) refuse "increment must be major|minor|patch (got '$INC')" ;; esac
[[ -n "$HEADLINE" ]] || refuse "--headline is required (the README 'Current version' line needs a theme)"
[[ "$(git branch --show-current)" == "main" ]] || refuse "must run on main"
[[ -z "$(git status --porcelain)" ]] || refuse "working tree must be clean (cz commits with -a)"
git fetch -q origin main
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]] || refuse "HEAD must equal origin/main (push or pull first)"
[[ "$(grep -c '^## Unreleased$' CHANGELOG.md)" -eq 1 ]] || refuse "CHANGELOG.md needs exactly one '## Unreleased' heading"
# ≥1 bullet between `## Unreleased` and the next `## ` heading — an empty section is not a release.
[[ "$(awk '/^## Unreleased$/{f=1;next} /^## /{f=0} f && /^- /' CHANGELOG.md | wc -l)" -ge 1 ]] \
  || refuse "'## Unreleased' has no bullets — curate the notes first"
README_RE='^\*\*Current version:\*\* v[0-9]+\.[0-9]+\.[0-9]+ — '
[[ "$(grep -cE "$README_RE" README.md)" -eq 1 ]] || refuse "README.md needs exactly one '**Current version:** vX.Y.Z — ' line"
NEW="$("${CZ[@]}" bump --get-next --increment "${INC^^}" 2>/dev/null | tail -1)"
[[ "$NEW" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || refuse "could not read the next version from cz (got '$NEW')"
[[ -z "$(git tag -l "v$NEW")" ]] || refuse "tag v$NEW already exists"
if [[ $DRY -eq 0 && $NOPUSH -eq 0 ]]; then "${GH[@]}" auth status >/dev/null 2>&1 || refuse "gh is not authenticated (or pass --no-push)"; fi

HEADING="## v$NEW ($(date +%F))"
README_LINE="**Current version:** v$NEW — $HEADLINE"
if [[ $DRY -eq 1 ]]; then
  echo "dry-run: would cut v$NEW"
  echo "  CHANGELOG.md: '## Unreleased' → '$HEADING'"
  echo "  README.md:    '$README_LINE'"
  "${CZ[@]}" bump --dry-run --increment "${INC^^}" 2>/dev/null || true
  exit 0
fi

# --- edit, then let cz commit + tag -------------------------------------------------------
sed -i "s/^## Unreleased$/$HEADING/" CHANGELOG.md
[[ "$(grep -c "^$HEADING$" CHANGELOG.md)" -eq 1 ]] || refuse "CHANGELOG heading rename did not apply"
sed -i -E "s|${README_RE}.*|$(printf '%s' "$README_LINE" | sed 's/[&|]/\\&/g')|" README.md
[[ "$(grep -cF "$README_LINE" README.md)" -eq 1 ]] || refuse "README 'Current version' line replacement did not apply"
"${CZ[@]}" bump --increment "${INC^^}" --yes
[[ "$(git cat-file -t "v$NEW" 2>/dev/null)" == "tag" ]] || refuse "cz did not create an annotated tag v$NEW (set annotated_tag = true)"
[[ -z "$(git status --porcelain)" ]] || refuse "tree dirty after cz bump — inspect before pushing"
# uv.lock must carry the new version in the tagged tree (pre_bump_hooks = ["uv lock"]).
if [[ -f uv.lock ]]; then
  awk '/^name = "aa-ma"$/{f=1;next} f&&/^version = /{print;exit}' uv.lock | grep -qF "\"$NEW\"" \
    || refuse "uv.lock still records the old version — is pre_bump_hooks = [\"uv lock\"] set in [tool.commitizen]?"
fi
echo "released v$NEW locally: $(git log --format='%h %s' -1)"
[[ $NOPUSH -eq 0 ]] || { echo "--no-push: not pushed; rollback = git tag -d v$NEW && git reset --hard origin/main"; exit 0; }

# --- publish ----------------------------------------------------------------------------
git push --follow-tags origin main
NOTES="$(mktemp)"; trap 'rm -f "$NOTES"' EXIT
awk -v h="$HEADING" '$0==h{f=1;next} /^## /{f=0} f' CHANGELOG.md > "$NOTES"
"${GH[@]}" release create "v$NEW" --title "v$NEW" --notes-file "$NOTES"
echo "published v$NEW"
