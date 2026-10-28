"""Every `Skill(x)` an auto-loaded rule names resolves (code-conventions-impact M12.4).

A reference is on disk (`claude-code/skills/<x>/SKILL.md`) or declared-external
(`codemem.draw.surface_allowlist.EXTERNAL`); anything else is dangling, the only defect
(engineering-standards §1, three-valued references). Parsing and classification are the
plugin-surface extractor's, so this test and the golden surface cannot disagree.
"""

from __future__ import annotations

from pathlib import Path

from codemem.draw.plugin_surface import RefClass, extract

REPO_ROOT = Path(__file__).resolve().parents[1]

# The routing table in coding-standards.md; a route removed or added must be deliberate.
CODING_STANDARDS_ROUTES = {
    "logging-and-comments",
    "python-quality-gates",
    "bash-defensive-patterns",
    "language-conventions",
    "secops",
    "secrets-management",
    "llm-output-safety",
    "impact-analysis",
    "writing-for-agents",
}


def rule_skill_refs(repo_root: Path) -> dict[str, dict[str, RefClass]]:
    """``{rule: {skill: class}}`` for every Skill() edge out of ``claude-code/rules``."""
    refs: dict[str, dict[str, RefClass]] = {}
    for e in extract(repo_root).edges:
        if e.src.startswith("rule:") and e.kind == "skill":
            refs.setdefault(e.src, {})[e.dst.split(":", 1)[1]] = e.ref_class
    return refs


def test_coding_standards_routes_to_its_skills() -> None:
    routes = rule_skill_refs(REPO_ROOT)["rule:coding-standards"]
    assert set(routes) == CODING_STANDARDS_ROUTES


def test_no_rule_has_a_dangling_skill_reference() -> None:
    dangling = {
        (rule, skill)
        for rule, skills in rule_skill_refs(REPO_ROOT).items()
        for skill, cls in skills.items()
        if cls is RefClass.DANGLING
    }
    assert dangling == set()


def test_dangling_is_found_in_any_form(tmp_path: Path) -> None:
    (tmp_path / "claude-code" / "skills" / "secops").mkdir(parents=True)
    (tmp_path / "claude-code" / "skills" / "secops" / "SKILL.md").write_text("x\n")
    (tmp_path / "claude-code" / "rules").mkdir()
    (tmp_path / "claude-code" / "rules" / "r.md").write_text(
        'Use Skill(secops), Skill("no-such-skill") and Skill( also-missing ).\n'
    )
    assert rule_skill_refs(tmp_path)["rule:r"] == {
        "secops": RefClass.ON_DISK,
        "no-such-skill": RefClass.DANGLING,
        "also-missing": RefClass.DANGLING,
    }
