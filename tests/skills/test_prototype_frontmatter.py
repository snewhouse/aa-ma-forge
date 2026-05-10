"""Frontmatter assertions for the forked prototype skill.

Acceptance criteria (M2.8):
  - SKILL.md parses as valid markdown-with-yaml-frontmatter
  - frontmatter `name` == "prototype"
  - frontmatter `description` is non-empty
  - provenance comment references mattpocock/skills/skills/engineering/prototype
  - companion files (LOGIC.md, UI.md) exist (referenced from SKILL.md)

Provenance: forked from https://github.com/mattpocock/skills/skills/engineering/prototype
on 2026-05-10 (aa-ma-forge v0.6.0). See ADR-0003.
"""

from __future__ import annotations

from ._helpers import SKILLS_DIR, assert_skill_frontmatter  # pyright: ignore[reportMissingImports]

SKILL_DIR_NAME = "prototype"
UPSTREAM_PATH = "mattpocock/skills/skills/engineering/prototype"


def test_prototype_frontmatter() -> None:
    """SKILL.md frontmatter matches plugin conventions and references upstream."""
    assert_skill_frontmatter(SKILL_DIR_NAME, UPSTREAM_PATH)


def test_prototype_has_logic_and_ui_branch_files() -> None:
    """SKILL.md routes between LOGIC.md (terminal TUI) and UI.md (web variants); both must exist."""
    skill_dir = SKILLS_DIR / SKILL_DIR_NAME
    for branch in ("LOGIC.md", "UI.md"):
        path = skill_dir / branch
        assert path.exists(), (
            f"Missing branch file {branch!r} in {skill_dir} — "
            "SKILL.md cross-references it as a routing target"
        )
        assert path.stat().st_size > 1000, (
            f"{branch} is suspiciously small ({path.stat().st_size} bytes); "
            "expected substantive prototype guidance (canonical files are 5-7 KB)"
        )
