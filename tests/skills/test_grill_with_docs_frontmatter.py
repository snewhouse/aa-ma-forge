"""Frontmatter assertions for the forked grill-with-docs skill.

Acceptance criteria (M1.7):
  - SKILL.md parses as a valid markdown-with-yaml-frontmatter file
  - frontmatter `name` field == "grill-with-docs" (matches plugin Skill() invocation)
  - frontmatter `description` field is non-empty (required by Skill registry)
  - the upstream provenance comment is present and references mattpocock/skills

Provenance: forked from https://github.com/mattpocock/skills/skills/engineering/grill-with-docs
on 2026-05-10 (aa-ma-forge v0.6.0). See ADR-0002.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_PATH = REPO_ROOT / "claude-code" / "skills" / "grill-with-docs" / "SKILL.md"


def _split_frontmatter(text: str) -> tuple[str, dict]:
    """Return (provenance_lines, frontmatter_dict). Strict — raises on malformed input."""
    lines = text.splitlines()
    # Skip optional HTML-comment provenance lines at the top
    i = 0
    provenance: list[str] = []
    while i < len(lines) and lines[i].startswith("<!--"):
        provenance.append(lines[i])
        i += 1
    # Frontmatter delimiter
    if i >= len(lines) or lines[i].strip() != "---":
        raise ValueError(
            f"Expected '---' frontmatter opener at line {i + 1}, got: {lines[i] if i < len(lines) else '<EOF>'}"
        )
    i += 1
    body_start = i
    while i < len(lines) and lines[i].strip() != "---":
        i += 1
    if i >= len(lines):
        raise ValueError("Unterminated frontmatter — no closing '---' found")
    fm_text = "\n".join(lines[body_start:i])
    fm = yaml.safe_load(fm_text)
    if not isinstance(fm, dict):
        raise ValueError(f"Frontmatter is not a mapping; got {type(fm).__name__}")
    return "\n".join(provenance), fm


@pytest.fixture(scope="module")
def skill_content() -> str:
    assert SKILL_PATH.exists(), f"SKILL.md not found at {SKILL_PATH}"
    return SKILL_PATH.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def parsed(skill_content: str) -> tuple[str, dict]:
    return _split_frontmatter(skill_content)


def test_frontmatter_name_matches_skill_directory(parsed: tuple[str, dict]) -> None:
    """`name` must match the directory name so Skill('grill-with-docs') resolves."""
    _, fm = parsed
    assert fm.get("name") == "grill-with-docs", (
        f"Expected name='grill-with-docs', got name={fm.get('name')!r}. "
        f"This must match the directory name {SKILL_PATH.parent.name!r}."
    )


def test_frontmatter_description_non_empty(parsed: tuple[str, dict]) -> None:
    """`description` is required by the Claude Code Skill registry and must be substantive."""
    _, fm = parsed
    description = fm.get("description")
    assert description is not None, "Missing 'description' field in frontmatter"
    assert isinstance(description, str), (
        f"'description' must be str, got {type(description).__name__}"
    )
    assert len(description.strip()) >= 50, (
        f"'description' is too short ({len(description.strip())} chars); "
        "Skill descriptions should explain when/why to invoke (>= 50 chars)."
    )


def test_provenance_comment_references_upstream(parsed: tuple[str, dict]) -> None:
    """First line should be an HTML-comment crediting the mattpocock/skills upstream."""
    provenance, _ = parsed
    assert "mattpocock/skills" in provenance, (
        "Forked-from provenance comment is missing or does not reference "
        "the canonical upstream (mattpocock/skills). See ADR-0002."
    )
    assert "grill-with-docs" in provenance, (
        "Provenance comment should name the upstream skill path"
    )


def test_skill_directory_has_companion_format_files() -> None:
    """SKILL.md links to CONTEXT-FORMAT.md and ADR-FORMAT.md; both must exist."""
    skill_dir = SKILL_PATH.parent
    for companion in ("CONTEXT-FORMAT.md", "ADR-FORMAT.md"):
        assert (skill_dir / companion).exists(), (
            f"Missing companion doc {companion!r} in {skill_dir} — "
            "SKILL.md cross-references it"
        )
