# Versioning Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add semantic versioning with commitizen + python-semantic-release, baseline tag v0.1.0, initial CHANGELOG, and VERSION single-source-of-truth.

**Architecture:** VERSION file as single source. pyproject.toml reads it dynamically via hatchling. __init__.py reads it at runtime. Commitizen validates commits. python-semantic-release automates bump + changelog + tag.

**Tech Stack:** commitizen (already installed globally), python-semantic-release (add as dev dep), hatchling (already build backend)

---

### Task 1: Create VERSION file and wire up dynamic versioning

**Files:**
- Create: `VERSION`
- Modify: `pyproject.toml`
- Modify: `src/aa_ma/__init__.py`

**Step 1: Create VERSION file**

Create `VERSION` at repo root with a single line:

```
0.1.0
```

No trailing newline beyond what the editor adds.

**Step 2: Update pyproject.toml for dynamic versioning**

Replace the static `version = "0.1.0"` with dynamic version reading from VERSION file. Change build system to use hatch-vcs or a simple file-read approach.

Replace:
```toml
[project]
name = "aa-ma"
version = "0.1.0"
```

With:
```toml
[project]
name = "aa-ma"
dynamic = ["version"]
```

Add after `[build-system]`:
```toml
[tool.hatch.version]
path = "VERSION"
pattern = "(?P<version>.+)"
```

**Step 3: Update __init__.py to read VERSION at runtime**

Replace:
```python
"""Advanced Agentic Memory Architecture (AA-MA)."""

__version__ = "0.1.0"
```

With:
```python
"""Advanced Agentic Memory Architecture (AA-MA)."""

from importlib.metadata import version

__version__ = version("aa-ma")
```

**Step 4: Verify it still works**

Run: `uv run python -c "import aa_ma; print(aa_ma.__version__)"`
Expected: `0.1.0`

**Step 5: Commit**

```bash
git add VERSION pyproject.toml src/aa_ma/__init__.py
git commit -m "build: add VERSION file as single source of truth for versioning"
```

---

### Task 2: Add commitizen and python-semantic-release config

**Files:**
- Modify: `pyproject.toml`

**Step 1: Add dev dependencies**

Add `python-semantic-release` to the uv dev-dependencies in pyproject.toml:

```toml
[tool.uv]
dev-dependencies = [
    "pytest>=8.0",
    "ruff>=0.4",
    "python-semantic-release>=9.0",
]
```

Note: commitizen 4.13.9 is already installed globally, no need to add as project dep.

**Step 2: Add commitizen config**

Add to pyproject.toml:

```toml
[tool.commitizen]
name = "cz_conventional_commits"
version_provider = "pep621"
tag_format = "v$version"
update_changelog_on_bump = true
version_files = [
    "VERSION",
]
```

**Step 3: Add python-semantic-release config**

Add to pyproject.toml:

```toml
[tool.semantic_release]
version_toml = ["pyproject.toml:project.version"]
version_variables = ["VERSION:__version__"]
major_on_zero = false
tag_format = "v{version}"
commit_message = "chore(release): v{version}"

[tool.semantic_release.changelog]
changelog_file = "CHANGELOG.md"

[tool.semantic_release.branches.main]
match = "main"
```

**Step 4: Install the new dependency**

Run: `uv sync`

**Step 5: Verify commitizen works**

Run: `uv run cz check --commit-msg-file <(echo "feat: test message")`
Expected: exit 0 (valid conventional commit)

**Step 6: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "build: add commitizen and python-semantic-release configuration"
```

---

### Task 3: Write initial CHANGELOG.md

**Files:**
- Create: `CHANGELOG.md`

**Step 1: Write the initial changelog**

This covers all work done in v0.1.0 (the 14 original commits + versioning setup). Written as a human-authored baseline. Future entries will be auto-generated.

```markdown
# Changelog

All notable changes to this project will be documented in this file.

This project adheres to [Semantic Versioning](https://semver.org/).

## v0.1.0 (2026-04-05)

Initial release of AA-MA Forge.

### Added

- AA-MA specification v2.1 (canonical spec, quick reference, team guide)
- Claude Code foundations reference (built-in vs AA-MA layer mapping)
- 6 AA-MA commands: execute-full, execute-milestone, execute-step, archive, ultraplan, verify-plan
- AA-MA execution skill (1,187 lines)
- 2 specialised agents: aa-ma-scribe (plan to artifacts), aa-ma-validator (read-only validation)
- Operational rules (aa-ma.md) and compaction hook (pre-compact-aa-ma.sh)
- Origin story narrative: how-we-got-here.md
- Python package skeleton (aa_ma) with validators, schemas, and CLI placeholders
- Install/uninstall scripts with symlink deployment and backup-first strategy
- Example completed task artifacts (aa-ma-team-guide)
- Apache-2.0 licence
```

**Step 2: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs: add initial CHANGELOG.md for v0.1.0 baseline"
```

---

### Task 4: Create v0.1.0 baseline tag

**Step 1: Create annotated tag**

```bash
git tag -a v0.1.0 -m "v0.1.0: Initial release of AA-MA Forge"
```

**Step 2: Verify tag**

Run: `git tag -l "v*"`
Expected: `v0.1.0`

Run: `git show v0.1.0 --quiet`
Expected: Shows tag metadata and points to current commit

**Step 3: Push tag**

```bash
git push origin main --follow-tags
```

---

### Task 5: Add narrative link to README + final push

**Files:**
- Modify: `README.md`

**Step 1: Add link to origin story in Credits section**

After the Helix.ml paragraph in the "Credits and inspirations" section, add:

```markdown
The full story is in [how we got here](docs/narrative/how-we-got-here.md).
```

**Step 2: Commit and push**

```bash
git add README.md
git commit -m "docs: add link to origin story narrative in README"
git push origin main
```

---

### Task 6: Verify everything works end-to-end

**Step 1: Check version reads correctly**

```bash
uv run python -c "import aa_ma; print(aa_ma.__version__)"
# Expected: 0.1.0
```

**Step 2: Check commitizen validates commits**

```bash
echo "not a valid commit" | uv run cz check --commit-msg-file /dev/stdin
# Expected: exit 1 (invalid)

echo "feat: valid commit message" | uv run cz check --commit-msg-file /dev/stdin
# Expected: exit 0 (valid)
```

**Step 3: Check tag exists on remote**

```bash
git ls-remote --tags origin
# Expected: shows v0.1.0
```

**Step 4: Check CHANGELOG exists and is correct**

```bash
head -5 CHANGELOG.md
# Expected: shows header and v0.1.0
```

**Step 5: Verify git is clean and pushed**

```bash
git status
git log --oneline origin/main..HEAD
# Expected: clean, 0 commits ahead
```
