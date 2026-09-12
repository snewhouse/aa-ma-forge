"""Angle 6 must name the v0.12.0 structural checks; text drift here silently disables them (L-010).

The enum tests import the constants (precedent: test_enum_matches_engineering_standards_table)
so prose and code cannot drift — a value added to one side without the other fails here.
"""

import re
from pathlib import Path

from aa_ma.plan_parsers import CANONICAL_DIAGRAM_WAIVERS
from aa_ma.render.mermaid_lint import CODE_AUDIT_PROFILES

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / "claude-code" / "skills" / "plan-verification" / "SKILL.md"
ENG_STANDARDS = ROOT / "claude-code" / "rules" / "engineering-standards.md"

# Every live prose site that inlines the "code Audit-Profile" set (M1 §6.8 finding).
CODE_PROFILE_SITES = (
    "claude-code/rules/aa-ma.md",
    "claude-code/rules/engineering-standards.md",
    "claude-code/skills/plan-verification/SKILL.md",
    "docs/spec/aa-ma-specification.md",
    "docs/templates/plan-template.md",
)


def test_angle6_names_architecture_view_check() -> None:
    text = SKILL.read_text(encoding="utf-8")
    assert "6. **Architecture View present or validly waived" in text
    assert "7. **Contract block per code milestone" in text
    assert "2026-09-11" in text  # literal cutover date, not "the v0.12.0 release date"


def test_angle6_runs_the_lint_not_a_grep() -> None:
    text = SKILL.read_text(encoding="utf-8")
    assert "aa-ma-lint-views" in text
    assert "parse_diagram_waiver" in text
    assert "grep -nE '^\\*\\*Diagram-Waiver" not in text  # the M1 stopgap is gone


def test_angle6_lists_every_canonical_waiver_value() -> None:
    text = SKILL.read_text(encoding="utf-8")
    for v in CANONICAL_DIAGRAM_WAIVERS:
        assert f"`{v}`" in text, v


def test_engineering_standards_table_matches_waiver_enum() -> None:
    text = ENG_STANDARDS.read_text(encoding="utf-8")
    table = text.split("**Diagram-Waiver canonical values**", 1)[1].split("###", 1)[0]
    documented = set(re.findall(r"^\|\s*`([a-z-]+)`\s*\|", table, re.MULTILINE))
    assert documented == CANONICAL_DIAGRAM_WAIVERS


def test_prose_code_profile_sets_match_the_constant() -> None:
    """Each `Audit-Profile ∈ {a, b, c}` in live prose must equal CODE_AUDIT_PROFILES."""
    pattern = re.compile(r"Audit-Profile`? ?∈ ?\{([^}]*)\}")
    seen = 0
    for rel in CODE_PROFILE_SITES:
        for m in pattern.finditer((ROOT / rel).read_text(encoding="utf-8")):
            seen += 1
            values = {v.strip().strip("`") for v in m.group(1).split(",")}
            assert values == CODE_AUDIT_PROFILES, f"{rel}: {m.group(0)}"
    assert seen >= 5, f"expected the inline set at several sites, found {seen}"
