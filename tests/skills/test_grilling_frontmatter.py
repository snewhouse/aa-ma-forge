"""Frontmatter assertions for the forked grilling skill (M2.1).

Provenance: forked from https://github.com/mattpocock/skills/skills/productivity/grilling
@ c55ee46 (aa-ma-forge v0.13.0). See ADR-0002 amendment.
"""

from __future__ import annotations

from ._helpers import assert_skill_frontmatter  # pyright: ignore[reportMissingImports]

SKILL_DIR_NAME = "grilling"
UPSTREAM_PATH = "mattpocock/skills/skills/productivity/grilling"


def test_grilling_frontmatter() -> None:
    """SKILL.md frontmatter is well-formed, model-invocable, and names upstream."""
    _, fm = assert_skill_frontmatter(SKILL_DIR_NAME, UPSTREAM_PATH)
    assert "disable-model-invocation" not in fm, (
        "grilling must stay model-invocable — grill-with-docs delegates to it via Skill()"
    )
