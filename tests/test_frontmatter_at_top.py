"""Every shipped skill, command and agent must open with its YAML frontmatter on line 1.

Claude Code only recognises frontmatter that starts at the top of the file. A line-1 HTML
comment silently dropped `name`/`description` (and `allowed-tools`) from six skills, which
then showed the comment as their description. Fork provenance now lives on line 2 as a
YAML `#` comment (ADR-0011 amendment, 2026-10-05). Each skill's `name` must also equal its
directory, since `name` sets the `/` command and callers use the directory slug.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
PLUGIN = REPO_ROOT / "claude-code"

# (glob, keys that must be non-empty strings). 2 of 14 commands carry no `name`, so
# commands only require `description`.
SURFACES = {
    "skills/*/SKILL.md": ("name", "description"),
    "commands/*.md": ("description",),
    "agents/*.md": ("name", "description"),
}

CASES = [
    pytest.param(path, keys, id=str(path.relative_to(PLUGIN)))
    for pattern, keys in SURFACES.items()
    for path in sorted(PLUGIN.glob(pattern))
]


def test_surfaces_are_not_empty() -> None:
    """Guard the guard: a moved directory must not turn this file into zero tests."""
    for pattern in SURFACES:
        assert list(PLUGIN.glob(pattern)), f"no files match claude-code/{pattern}"


def _frontmatter(path: Path) -> dict:
    lines = path.read_text(encoding="utf-8").split("\n")
    assert lines[0] == "---", f"line 1 must be '---', got: {lines[0][:80]!r}"
    assert "---" in lines[1:], "unterminated frontmatter: no closing '---'"
    close = lines.index("---", 1)
    fm = yaml.safe_load("\n".join(lines[1:close]))
    assert isinstance(fm, dict), f"frontmatter is not a mapping: {type(fm).__name__}"
    return fm


@pytest.mark.parametrize(("path", "keys"), CASES)
def test_frontmatter_starts_on_line_1(path: Path, keys: tuple[str, ...]) -> None:
    fm = _frontmatter(path)
    for key in keys:
        value = fm.get(key)
        assert isinstance(value, str) and value.strip(), f"missing or empty {key!r}"


@pytest.mark.parametrize(
    "path",
    [
        pytest.param(p, id=p.parent.name)
        for p in sorted(PLUGIN.glob("skills/*/SKILL.md"))
    ],
)
def test_skill_name_matches_directory(path: Path) -> None:
    """`name` sets the skill's `/` command; callers invoke skills by their directory slug."""
    name = _frontmatter(path).get("name")
    assert name == path.parent.name, (
        f"name {name!r} must match the directory {path.parent.name!r}"
    )
