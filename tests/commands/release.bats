#!/usr/bin/env bats
# scripts/release.sh — deterministic release: the script edits CHANGELOG/README first,
# then `cz bump` (git commit -a + annotated tag) sweeps them into its own commit.
# No amend, no retag (the L-006 anti-pattern). Runs against a temp clone of a bare
# origin with stub `cz` and `gh` on PATH, so nothing here touches a real remote.

bats_require_minimum_version 1.5.0

setup() {
  REPO_ROOT="$(cd "${BATS_TEST_DIRNAME}/../.." && pwd)"
  RELEASE="${REPO_ROOT}/scripts/release.sh"
  WORK="$(mktemp -d "${BATS_TMPDIR}/release.XXXXXX")"
  export REPO_ROOT RELEASE WORK
  export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t
  export HOME="$WORK/home"; mkdir -p "$HOME"   # no user git config / hooks
  _make_origin_and_clone
  _stub_tools
  cd "$WORK/work"
}

teardown() { rm -rf "$WORK"; }

_make_origin_and_clone() {
  git init -q --bare -b main "$WORK/origin.git"
  git clone -q "$WORK/origin.git" "$WORK/work" 2>/dev/null
  cd "$WORK/work"
  git checkout -q -b main
  printf '# Changelog\n\n## Unreleased\n\n### Added\n\n- thing one\n- thing two\n\n## v0.11.0 (2026-09-12)\n\n- old\n' > CHANGELOG.md
  printf '# aa-ma-forge\n\n**Current version:** v0.11.0 — old headline here.\n\nbody\n' > README.md
  printf '__version__ = "0.11.0"\n' > VERSION
  printf '[project]\nname = "aa-ma"\nversion = "0.11.0"\n' > pyproject.toml
  git add -A && git commit -q -m "init" && git tag v0.11.0 && git push -q -u origin main --tags
}

# Stub cz: --get-next prints the next version; bump edits version files, commits -a with
# the real bump message shape and creates an annotated tag — the commitizen 4.x behaviour
# the script relies on. Stub gh: records argv.
_stub_tools() {
  mkdir -p "$WORK/bin"
  cat > "$WORK/bin/cz" <<'EOF'
#!/usr/bin/env bash
set -e
if [[ "$*" == *"--get-next"* ]]; then echo "0.12.0"; exit 0; fi
if [[ "$*" == *"--dry-run"* ]]; then echo "bump: version 0.11.0 → 0.12.0"; echo "tag to create: v0.12.0"; exit 0; fi
if [[ "$1" == "bump" ]]; then
  sed -i 's/0\.11\.0/0.12.0/' VERSION pyproject.toml
  git commit -q -a -m "bump: version 0.11.0 → 0.12.0" -m "[ad-hoc]"
  git tag -a v0.12.0 -m "v0.12.0"
  exit 0
fi
echo "stub cz: unexpected args $*" >&2; exit 99
EOF
  cat > "$WORK/bin/gh" <<'EOF'
#!/usr/bin/env bash
echo "$*" >> "${GH_LOG:?}"
exit 0
EOF
  chmod +x "$WORK/bin/cz" "$WORK/bin/gh"
  export CZ="$WORK/bin/cz" GH="$WORK/bin/gh" GH_LOG="$WORK/gh.log"
}

@test "usage: no increment → exit 2" {
  run "$RELEASE"; [ "$status" -eq 2 ]; [[ "$output" == *usage* ]]
}

@test "refuses a bad increment" {
  run "$RELEASE" huge --headline h; [ "$status" -eq 1 ]; [[ "$output" == *increment* ]]
}

@test "refuses a missing --headline" {
  run "$RELEASE" minor; [ "$status" -eq 1 ]; [[ "$output" == *headline* ]]
}

@test "refuses when not on main" {
  git checkout -q -b feature
  run "$RELEASE" minor --headline h; [ "$status" -eq 1 ]; [[ "$output" == *main* ]]
}

@test "refuses a dirty tree" {
  echo x >> README.md
  run "$RELEASE" minor --headline h; [ "$status" -eq 1 ]; [[ "$output" == *clean* ]]
}

@test "refuses when HEAD is not origin/main" {
  git commit -q --allow-empty -m "local only"
  run "$RELEASE" minor --headline h; [ "$status" -eq 1 ]; [[ "$output" == *origin/main* ]]
}

@test "refuses when CHANGELOG has no ## Unreleased" {
  sed -i 's/^## Unreleased$/## Soon/' CHANGELOG.md && git commit -q -am x && git push -q
  run "$RELEASE" minor --headline h; [ "$status" -eq 1 ]; [[ "$output" == *Unreleased* ]]
}

@test "refuses an empty ## Unreleased" {
  printf '# Changelog\n\n## Unreleased\n\n## v0.11.0 (2026-09-12)\n\n- old\n' > CHANGELOG.md
  git commit -q -am x && git push -q
  run "$RELEASE" minor --headline h; [ "$status" -eq 1 ]; [[ "$output" == *Unreleased* ]]
}

@test "refuses when the tag already exists" {
  git tag v0.12.0
  run "$RELEASE" minor --headline h; [ "$status" -eq 1 ]; [[ "$output" == *v0.12.0* ]]
}

@test "--dry-run prints the plan and changes nothing" {
  run "$RELEASE" minor --headline "new headline" --dry-run
  [ "$status" -eq 0 ]
  [[ "$output" == *"0.12.0"* ]] && [[ "$output" == *"new headline"* ]]
  [ -z "$(git status --porcelain)" ]
  grep -q '^## Unreleased$' CHANGELOG.md
  [ -z "$(git tag -l v0.12.0)" ]
}

@test "--no-push: one commit with CHANGELOG+README+VERSION, heading renamed, annotated tag, clean tree" {
  run "$RELEASE" minor --headline "new headline" --no-push
  [ "$status" -eq 0 ]
  ! grep -q 'Unreleased' CHANGELOG.md
  grep -q "^## v0.12.0 ($(date +%F))$" CHANGELOG.md
  grep -q '^- thing one$' CHANGELOG.md                                  # curated notes survive
  [ "$(grep -c '^\*\*Current version:\*\* v0.12.0 — new headline$' README.md)" -eq 1 ]
  ! grep -q 'old headline' README.md
  [ "$(git log --format=%s -1)" = "bump: version 0.11.0 → 0.12.0" ]
  git show --stat --format= HEAD | grep -q CHANGELOG.md
  git show --stat --format= HEAD | grep -q README.md
  git show --stat --format= HEAD | grep -q VERSION
  [ "$(git cat-file -t v0.12.0)" = "tag" ]                              # annotated, not lightweight
  [ -z "$(git status --porcelain)" ]
  [ -z "$(git ls-remote --tags origin v0.12.0)" ]                       # nothing pushed
}

@test "push path: origin receives main + tag and gh release is created from the section" {
  run "$RELEASE" minor --headline "new headline"
  [ "$status" -eq 0 ]
  [ "$(git ls-remote --tags origin v0.12.0 | wc -l)" -ge 1 ]
  [ "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)" ]
  grep -q '^release create v0.12.0' "$GH_LOG"
  grep -q -- '--notes-file' "$GH_LOG"
}

@test "refuses when README lacks exactly one Current version line" {
  sed -i '/Current version/d' README.md && git commit -q -am x && git push -q
  run "$RELEASE" minor --headline h; [ "$status" -eq 1 ]; [[ "$output" == *"Current version"* ]]
}
