# Runbook: cutting a release

`scripts/release.sh` is the only supported way to cut a release. It exists because every
release from v0.7.0 to v0.11.0 was cut by hand-restoring the CHANGELOG after `cz bump`
overwrote it, then amending and re-tagging (lessons L-006 / L-008). The script does the
whole cut in one deterministic pass: no amend, no retag, no CHANGELOG surgery.

The global `/release-prep` command (Makefile targets `make ci` / `make version-bump` …)
does **not** apply to this repo — there is no Makefile. Use this runbook.

## What the script does

```
scripts/release.sh <major|minor|patch> --headline "<one-line theme>" [--dry-run] [--no-push]
```

1. **Preflight** (any failure → exit 1, nothing touched): on `main`; clean tree; `HEAD == origin/main`;
   `CHANGELOG.md` has exactly one `## Unreleased` with ≥ 1 bullet; `README.md` has exactly one
   `**Current version:** vX.Y.Z — …` line; next version from `cz bump --get-next`; tag absent;
   `gh auth status` (unless `--no-push`/`--dry-run`).
2. `## Unreleased` → `## vX.Y.Z (YYYY-MM-DD)`; README line → `**Current version:** vX.Y.Z — <headline>`.
3. `uv run cz bump --increment <INC> --yes` — commitizen updates `pyproject.toml` + `VERSION`,
   commits **everything** (`git commit -a`, message `bump: version A → B` + `[ad-hoc]`) and creates an
   **annotated** tag. `update_changelog_on_bump = false`, so cz never touches the CHANGELOG.
4. `git push --follow-tags origin main`, then `gh release create vX.Y.Z --notes-file <the new section>`.

## Procedure

```bash
# 0. The curated notes are the release notes. Make sure `## Unreleased` says what shipped.
sed -n '/^## Unreleased/,/^## v/p' CHANGELOG.md

# 1. Everything merged, pushed, green.
git status -sb            # ## main...origin/main, clean
uv run pytest -q && uv run lint-imports && bats tests/hooks tests/commands

# 2. Rehearse — prints the plan, changes nothing.
scripts/release.sh minor --headline "one line on what this release is about" --dry-run

# 3. Cut it.
scripts/release.sh minor --headline "one line on what this release is about"

# 4. Verify.
git tag -n1 vX.Y.Z                    # annotated message present
git describe --tags                   # vX.Y.Z
uv sync && uv run python -c "import importlib.metadata as m; print(m.version('aa-ma'))"
gh release view vX.Y.Z
scripts/install.sh                    # spec docs are copied, not symlinked
```

`## Unreleased` is **not** re-created by the script — an empty permanent stub would hide the
doc-drift Tier 2 "feat/fix commits with no changelog entry" check. The first milestone of the
next plan re-creates it (plan-architecture-views Sub-step 1.8 is the precedent).

## Rollback

| When | Do |
|---|---|
| Preflight refused / `--no-push` / cz failed | `git tag -d vX.Y.Z; git reset --hard origin/main` — the tree was clean by preflight, nothing else is lost |
| Already pushed | `gh release delete vX.Y.Z --yes; git push --delete origin vX.Y.Z; git revert <bump-sha> && git push`. **Never re-point a pushed tag** — cut the next patch instead |

## Rehearsing the script itself (after editing it)

`bats tests/commands/release.bats` (13 cases, stub `cz`/`gh`, bare temp origin). For an end-to-end
rehearsal with the real commitizen, never push from a `file://` clone of the live repo — use a
throwaway bare origin:

```bash
S=$(mktemp -d); git clone -q --bare . "$S/origin.git"; git clone -q "$S/origin.git" "$S/work"
cd "$S/work" && uv sync -q && GH=true scripts/release.sh minor --headline "rehearsal"
git log -1 --stat; git tag -n1; git ls-remote --tags origin
```
