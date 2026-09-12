"""Angle 6 must name the v0.12.0 structural checks; text drift here silently disables them (L-010)."""

from pathlib import Path

SKILL = Path(__file__).resolve().parents[2] / "claude-code" / "skills" / "plan-verification" / "SKILL.md"


def test_angle6_names_architecture_view_check() -> None:
    text = SKILL.read_text(encoding="utf-8")
    assert "6. **Architecture View present or validly waived" in text
    assert "7. **Contract block per code milestone" in text
    assert "2026-09-11" in text  # literal cutover date, not "the v0.12.0 release date"


def test_angle6_lists_waiver_values() -> None:
    # At M2.7 this test is upgraded to import CANONICAL_DIAGRAM_WAIVERS (precedent:
    # test_enum_matches_engineering_standards_table) so prose and code cannot drift.
    text = SKILL.read_text(encoding="utf-8")
    for v in ("none", "docs-only", "config-only", "single-file"):
        assert f"`{v}`" in text
