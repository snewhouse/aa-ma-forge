# Versioning Design: Commitizen + python-semantic-release

**Date:** 2026-04-05
**Author:** Stephen J Newhouse
**Status:** Approved

## Context

The repo has 14 commits, no tags, no changelog, and version strings in two places (pyproject.toml + __init__.py) with no synchronisation mechanism. Need proper semantic versioning that's automated and signposted.

## Two independent version tracks

| Track | Current | Location | Bumped by |
|-------|---------|----------|-----------|
| Spec version | v2.1 | `docs/spec/aa-ma-specification.md` header | Manual edit when spec changes |
| Package version | 0.1.0 | `VERSION` file (single source of truth) | `semantic-release` from commit history |

## What gets added

1. **VERSION file** at repo root — single line, single source of truth
2. **CHANGELOG.md** — initial manual entry for v0.1.0, auto-generated thereafter
3. **Commitizen config** in `pyproject.toml` — commit message validation
4. **python-semantic-release config** in `pyproject.toml` — version bump automation
5. **Dynamic version reading** — `pyproject.toml` and `__init__.py` read from VERSION file
6. **Git tag v0.1.0** on current commit as baseline
7. **Pre-commit hook** — commitizen validates commit format (optional, we already follow conventional commits)

## Release workflow

```bash
uv run semantic-release version     # bump, changelog, tag, commit
git push --follow-tags origin main  # push everything
```

## Baseline strategy

Tag current state as v0.1.0 with a manually written initial CHANGELOG. All future releases are automated from this baseline.

## Not in scope

- GitHub releases (can add later)
- CI/CD automation (sporadic maintenance, manual releases are fine)
- PyPI publishing (not distributing yet)
