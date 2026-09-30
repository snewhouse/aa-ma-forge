"""Incremental regeneration: which onboarding sections does a commit range make stale?

Map (5.1 prototype, Ste PASS): a section is stale when a changed path is one it cites, lies under a
directory it cites (`dir/`, any depth), or matches its fixed globs; any add, delete or rename makes
the structure section stale; a stamp sha that is no longer a commit makes every section stale.
"""

from __future__ import annotations

import fnmatch
import re
from pathlib import Path
from typing import NamedTuple

from . import stamp
from .models import HEX12, Onboarding

SHA12 = re.compile(rf"[0-9a-f]{{{HEX12}}}")
STRUCTURE = "03-structure.md"  # sections are keyed by deep-dive file name
# Truth nobody cites line by line.
SECTION_GLOBS = {
    "01-stack.md": (
        "pyproject.toml",
        "*.lock",
        "package.json",
        ".python-version",
        ".tool-versions",
    ),
    "05-tests-ci.md": (".github/workflows/*", "tests/*", "pytest.ini", "conftest.py"),
}


class Change(NamedTuple):
    status: str  # git's first letter: A, C, D, M, R, T
    path: str


def changed_since(repo: Path, sha12: str) -> list[Change] | None:
    """Committed changes from `sha12` to HEAD, or None — every section is stale — when `sha12` is
    not a commit here or the tree has tracked changes the diff cannot see."""
    if not SHA12.fullmatch(sha12):
        raise ValueError(f"not a {HEX12}-hex-digit sha: {sha12!r}")
    _, dirty, _ = stamp.head_stamp(
        repo
    )  # a repo with a commit and a safe config, or it raises
    if dirty:
        return None
    if stamp.run_git(
        repo, "cat-file", "-e", "--end-of-options", f"{sha12}^{{commit}}"
    ).returncode:
        return None
    diff = stamp.run_git(
        repo, "diff", "--name-status", "-z", "-M", "--end-of-options", sha12, "HEAD"
    )
    if diff.returncode:
        raise stamp.UnsafeRepo(f"{repo}: git diff failed: {diff.stderr.strip()}")
    fields, out = diff.stdout.split("\0"), []
    i = 0
    while i < len(fields) and fields[i]:
        status = fields[i][0]
        paths = 2 if status in "RC" else 1
        out += [Change(status, p) for p in fields[i + 1 : i + 1 + paths]]
        i += 1 + paths
    return out


def _matches(path: str, entries: list[str], globs: tuple[str, ...]) -> bool:
    return (
        path in entries
        or any(e.endswith("/") and path.startswith(e) for e in entries)
        or any(fnmatch.fnmatch(path, g) for g in globs)
    )


def sections_to_regenerate(
    onboarding: Onboarding, changed: list[Change] | None
) -> list[str]:
    if changed is None:
        return sorted(onboarding.sections)
    stale = {
        section
        for section, entries in onboarding.sections.items()
        for c in changed
        if _matches(c.path, entries, SECTION_GLOBS.get(section, ()))
    }
    if STRUCTURE in onboarding.sections and any(c.status in "ADRC" for c in changed):
        stale.add(STRUCTURE)
    return sorted(stale)
