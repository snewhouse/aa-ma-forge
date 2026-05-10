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

from ._helpers import SKILLS_DIR, assert_skill_frontmatter  # pyright: ignore[reportMissingImports]

SKILL_DIR_NAME = "grill-with-docs"
UPSTREAM_PATH = "mattpocock/skills/skills/engineering/grill-with-docs"


def test_grill_with_docs_frontmatter() -> None:
    """SKILL.md frontmatter is well-formed and matches plugin conventions."""
    assert_skill_frontmatter(SKILL_DIR_NAME, UPSTREAM_PATH)


def test_skill_directory_has_companion_format_files() -> None:
    """SKILL.md cross-references CONTEXT-FORMAT.md and ADR-FORMAT.md; both must exist."""
    skill_dir = SKILLS_DIR / SKILL_DIR_NAME
    for companion in ("CONTEXT-FORMAT.md", "ADR-FORMAT.md"):
        assert (skill_dir / companion).exists(), (
            f"Missing companion doc {companion!r} in {skill_dir} — "
            "SKILL.md cross-references it"
        )
