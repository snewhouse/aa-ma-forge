"""Tests for aa_ma.plan_parsers.CRITICAL_PATH_GLOBS and derive_critical_paths.

The globs turn a changed-file list into the `Critical-Path:` values it should
carry. They are checked three ways: every glob is valid and points at real
files; the hook-modification globs correspond to the engineering-standards
Critical-Path table cell by cell; and derive_critical_paths maps a mixed list
correctly. (Lives under tests/codemem/ because the plan names it there; that
conftest only puts scripts/ on sys.path, so an aa_ma-only test is unaffected.)
"""

from __future__ import annotations

import fnmatch
import re
from pathlib import Path

import pytest

from aa_ma.gitutil import git, split_z
from aa_ma.plan_parsers import (
    CANONICAL_CRITICAL_PATHS,
    CRITICAL_PATH_GLOBS,
    derive_critical_paths,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ENG_STANDARDS = REPO_ROOT / "claude-code" / "rules" / "engineering-standards.md"
# Literal globs whose file does not exist yet: M11 creates src/aa_ma/impact.py.
# Any other missing literal path is a typo and fails.
NOT_YET_CREATED = {"src/aa_ma/impact.py"}
# The table names `claude-code/skills/**` only as "the gate/scan logic inside" it,
# so the code carries narrower per-skill globs instead of the whole tree.
QUALIFIED_IN_TABLE = "claude-code/skills/**"
# Code globs the table cell does not name: the plan (M10, 10.5) extends the row
# with files that change what every session enforces. Pinned so a change on either
# side is a visible decision, not drift; reported for the doctrine table.
PLAN_EXTENSIONS = {
    "src/aa_ma/impact.py",
    "src/aa_ma/gitutil.py",
    ".gitleaksignore",
    ".pre-commit-config.yaml",
    "scripts/check_conventions.py",
    "scripts/install.sh",
    "scripts/uninstall.sh",
    "scripts/lib/aa-ma-install-lib.sh",
    ".github/dependabot.yml",
}
_WILDCARDS = re.compile(r"[*?\[]")


def _all_globs() -> list[tuple[str, str]]:
    return [
        (value, glob) for value, globs in CRITICAL_PATH_GLOBS.items() for glob in globs
    ]


def _tracked() -> list[str]:
    return split_z(git(["ls-files", "-z"], REPO_ROOT))


def _table_cell(value: str) -> str:
    text = ENG_STANDARDS.read_text(encoding="utf-8")
    row = re.search(rf"^\|\s*`{re.escape(value)}`\s*\|(.*)\|\s*$", text, re.MULTILINE)
    assert row, f"no {value} row in {ENG_STANDARDS.name}"
    return row.group(1)


def _expand_braces(token: str) -> list[str]:
    m = re.search(r"\{([^{}]*)\}", token)
    if not m:
        return [token]
    return [
        expanded
        for alt in m.group(1).split(",")
        for expanded in _expand_braces(token[: m.start()] + alt + token[m.end() :])
    ]


def _table_globs(value: str) -> set[str]:
    """Backticked paths in the row, braces expanded; `lib/` is a qualifier, not a path."""
    tokens = re.findall(r"`([^`]+)`", _table_cell(value))
    return {
        g for t in tokens if "/" in t and not t.endswith("/") for g in _expand_braces(t)
    }


def test_keys_are_canonical() -> None:
    assert set(CRITICAL_PATH_GLOBS) <= CANONICAL_CRITICAL_PATHS


@pytest.mark.parametrize(("value", "glob"), _all_globs())
def test_glob_is_fnmatch_valid(value: str, glob: str) -> None:
    assert "{" not in glob and "}" not in glob, "fnmatch does not expand braces"
    assert not glob.startswith(("/", "./")), "globs are repo-relative POSIX paths"
    re.compile(fnmatch.translate(glob))


def test_one_glob_per_path_no_duplicates() -> None:
    for value, globs in CRITICAL_PATH_GLOBS.items():
        assert len(globs) == len(set(globs)), value


@pytest.mark.parametrize(("value", "glob"), _all_globs())
def test_every_glob_names_real_files(value: str, glob: str) -> None:
    """A literal glob is an existing file (bar NOT_YET_CREATED); a wildcard one matches a tracked file."""
    if _WILDCARDS.search(glob):
        assert any(fnmatch.fnmatchcase(p, glob) for p in _tracked()), glob
    elif glob in NOT_YET_CREATED:
        assert not (REPO_ROOT / glob).exists(), (
            f"{glob} exists now: drop it from NOT_YET_CREATED"
        )
    else:
        assert (REPO_ROOT / glob).is_file(), glob


def test_every_real_literal_file_derives_its_value() -> None:
    tracked = _tracked()
    derived = derive_critical_paths(tracked)
    for value, glob in _all_globs():
        if not _WILDCARDS.search(glob) and glob not in NOT_YET_CREATED:
            assert glob in derived.get(value, []), (value, glob)


def test_hook_modification_globs_correspond_to_the_table() -> None:
    table = _table_globs("hook-modification")
    code = set(CRITICAL_PATH_GLOBS["hook-modification"])
    assert QUALIFIED_IN_TABLE in table
    # 1. Every unqualified path the table names is a glob in code.
    assert table - {QUALIFIED_IN_TABLE} <= code, sorted(
        table - {QUALIFIED_IN_TABLE} - code
    )
    # 2. The qualified one is narrowed, never carried whole: each skill glob sits inside it.
    assert QUALIFIED_IN_TABLE not in code
    skill_globs = {g for g in code if g.startswith("claude-code/skills/")}
    assert skill_globs, "the table's gate/scan skills have no glob"
    assert all(fnmatch.fnmatchcase(g, QUALIFIED_IN_TABLE) for g in skill_globs)
    # 3. Everything else in code is the pinned plan extension set.
    assert code - table - skill_globs == PLAN_EXTENSIONS


def test_hook_glob_covers_hooks_lib() -> None:
    """The table says `claude-code/hooks/**` (incl. `lib/`); fnmatch `*` crosses `/`."""
    assert derive_critical_paths(["claude-code/hooks/lib/aa-ma-log.sh"]) == {
        "hook-modification": ["claude-code/hooks/lib/aa-ma-log.sh"]
    }


def test_version_pipeline_globs() -> None:
    assert _table_globs("version-pipeline") == set(), (
        "the table names no paths for this row"
    )
    assert set(CRITICAL_PATH_GLOBS["version-pipeline"]) == {
        "scripts/release.sh",
        "VERSION",
    }


def test_derive_critical_paths_mixed_list() -> None:
    paths = [
        "README.md",
        "src/aa_ma/gate.py",
        "claude-code/hooks/ruff-format.sh",
        "claude-code/skills/execute-aa-ma-milestone/SKILL.md",
        "claude-code/skills/impact-analysis/SKILL.md",
        ".github/workflows/security.yml",
        "VERSION",
        "scripts/release.sh",
        "src/aa_ma/gate.py",
        "src/aa_ma/tui/app.py",
    ]
    assert derive_critical_paths(paths) == {
        "hook-modification": [
            ".github/workflows/security.yml",
            "claude-code/hooks/ruff-format.sh",
            "claude-code/skills/execute-aa-ma-milestone/SKILL.md",
            "src/aa_ma/gate.py",
        ],
        "version-pipeline": ["VERSION", "scripts/release.sh"],
    }


def test_derive_critical_paths_no_hits_is_empty() -> None:
    assert derive_critical_paths(["README.md", "docs/x.md"]) == {}
    assert derive_critical_paths([]) == {}


def test_derive_is_case_sensitive() -> None:
    """fnmatchcase, not fnmatch: the answer must not depend on the host OS."""
    assert derive_critical_paths(["version"]) == {}
