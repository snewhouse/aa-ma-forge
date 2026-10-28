"""Every `Skill(x)` an auto-loaded rule names resolves (code-conventions-impact M12.4).

A reference is on disk (`claude-code/skills/<x>/SKILL.md`) or declared-external
(`codemem.draw.surface_allowlist.EXTERNAL`); anything else is dangling, the only defect
(engineering-standards §1, three-valued references).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from codemem.draw.surface_allowlist import EXTERNAL

REPO_ROOT = Path(__file__).resolve().parents[1]
RULES = REPO_ROOT / "claude-code" / "rules"
SKILLS = REPO_ROOT / "claude-code" / "skills"
SKILL_REF_RE = re.compile(
    r"Skill\(([A-Za-z0-9_:-]+)\)"
)  # the plugin-surface extractor's form


def dangling(text: str) -> list[str]:
    """Skill names referenced in ``text`` that are neither on disk nor declared-external."""
    return sorted(
        {
            name
            for name in SKILL_REF_RE.findall(text)
            if not (SKILLS / name / "SKILL.md").is_file()
            and name not in EXTERNAL["skill"]
        }
    )


def test_coding_standards_routes_to_skills() -> None:
    text = (RULES / "coding-standards.md").read_text(encoding="utf-8")
    assert len(SKILL_REF_RE.findall(text)) >= 5


@pytest.mark.parametrize("rule", sorted(RULES.glob("*.md")), ids=lambda p: p.name)
def test_rule_has_no_dangling_skill_reference(rule: Path) -> None:
    assert dangling(rule.read_text(encoding="utf-8")) == []


def test_dangling_is_found() -> None:
    text = (
        "Use Skill(secops), Skill(first-principles-framework) and Skill(no-such-skill)."
    )
    assert dangling(text) == ["no-such-skill"]
