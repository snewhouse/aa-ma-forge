"""Frontmatter assertions for the forked write-a-skill skill.

Acceptance criteria (M2.8):
  - SKILL.md parses as valid markdown-with-yaml-frontmatter
  - frontmatter `name` == "write-a-skill"
  - frontmatter `description` is non-empty
  - provenance comment references mattpocock/skills/skills/productivity/write-a-skill

Provenance: forked from https://github.com/mattpocock/skills/skills/productivity/write-a-skill
on 2026-05-10 (aa-ma-forge v0.6.0). See ADR-0004.
"""

from __future__ import annotations

from ._helpers import SKILLS_DIR, assert_skill_frontmatter  # pyright: ignore[reportMissingImports]

SKILL_DIR_NAME = "write-a-skill"
UPSTREAM_PATH = "mattpocock/skills/skills/productivity/write-a-skill"


def test_write_a_skill_frontmatter() -> None:
    """SKILL.md frontmatter matches plugin conventions and references upstream."""
    assert_skill_frontmatter(SKILL_DIR_NAME, UPSTREAM_PATH)


def test_write_a_skill_is_single_file() -> None:
    """Upstream ships write-a-skill as a single SKILL.md (no companion files).

    The skill itself counsels splitting only when SKILL.md exceeds 100 lines;
    upstream is 117 lines and remains single-file. Sanity-check that we haven't
    added incidental companion files during the fork.
    """
    skill_dir = SKILLS_DIR / SKILL_DIR_NAME
    files = sorted(p.name for p in skill_dir.iterdir() if p.is_file())
    assert files == ["SKILL.md"], (
        f"Expected only SKILL.md in {skill_dir}; found {files!r}. "
        "Upstream ships write-a-skill as a single-file skill."
    )
