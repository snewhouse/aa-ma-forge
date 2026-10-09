"""Frontmatter + body-verbatim assertions for the Derived `aa-ma-research` skill (M4.1).

Provenance: derived from https://github.com/mattpocock/skills/skills/engineering/research
@ c55ee46 (aa-ma-forge v0.13.0); renamed so `~/.claude/skills/research` (a real
dir) is never shadowed (OV1). See ADR-0012.
"""

from __future__ import annotations

from ._helpers import (  # pyright: ignore[reportMissingImports]
    LOCAL_SECTION,
    SKILLS_DIR,
    assert_skill_frontmatter,
    upstream_body_md5,
)

SKILL_DIR_NAME = "aa-ma-research"
UPSTREAM_PATH = "mattpocock/skills/skills/engineering/research"
# Whole-file md5 of skills/engineering/research/SKILL.md @ c55ee46 (reference.md "Upstream").
UPSTREAM_MD5 = "e1dd6af372a9e1d134eff7d8362fe3f7"


def _upstream_body_md5(text: str) -> str:
    """sed '2d;/^## In this repo/,$d' SKILL.md | sed 's/^name: aa-ma-research$/name: research/' | md5sum"""
    return upstream_body_md5(
        text, rename={"name: aa-ma-research\n": "name: research\n"}
    )


def test_aa_ma_research_frontmatter() -> None:
    """SKILL.md is Derived, renamed, model-invocable, and names upstream."""
    provenance, fm = assert_skill_frontmatter(SKILL_DIR_NAME, UPSTREAM_PATH)
    assert provenance.startswith("# Derived from"), (
        "aa-ma-research is a Derived fork (renamed)"
    )
    assert "disable-model-invocation" not in fm, (
        "aa-ma-research must stay model-invocable — charting (M5) dispatches it via Skill()"
    )


def test_aa_ma_research_body_is_upstream_verbatim() -> None:
    """Everything between the provenance line and `## In this repo` is upstream @ c55ee46."""
    text = (SKILLS_DIR / SKILL_DIR_NAME / "SKILL.md").read_text(encoding="utf-8")
    assert LOCAL_SECTION in text, f"missing the appended `{LOCAL_SECTION}` section"
    assert _upstream_body_md5(text) == UPSTREAM_MD5


def test_aa_ma_research_in_this_repo_lines() -> None:
    """The three AA-MA dispatch rules from the M4 Contract are present."""
    text = (SKILLS_DIR / SKILL_DIR_NAME / "SKILL.md").read_text(encoding="utf-8")
    local = text.split(LOCAL_SECTION, 1)[1]
    for needle in (
        "subagent_type: aa-ma-researcher",
        "## Not pursued",
        "docs/research/<plan-slug>-<topic>.md",
    ):
        assert needle in local, f"`{LOCAL_SECTION}` lacks {needle!r}"
