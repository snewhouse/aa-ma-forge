"""Frontmatter + companion-file assertions for the vendored ``understand-codebase`` skill.

Acceptance criteria (understand-codebase-skill M2.1):
  - ``SKILL.md`` parses as a valid markdown-with-yaml-frontmatter file
  - frontmatter ``name`` == ``"understand-codebase"`` (matches the dir name + ``Skill()`` invocation)
  - frontmatter ``description`` is a substantive string naming the onboarding deliverables
  - frontmatter ``allowed-tools`` is a non-empty list including the essentials it uses
  - every ``references/<X>.md`` and ``templates/<X>.md`` path named in ``SKILL.md`` exists on
    disk and is substantive (> 1 KB), and the references/ + templates/ inventory is pinned

Vendored into aa-ma-forge v0.9.0 — see docs/adr/0006-understand-codebase-adoption.md.
"""

from __future__ import annotations

import re

from ._helpers import SKILLS_DIR, split_frontmatter  # pyright: ignore[reportMissingImports]

SKILL_DIR_NAME = "understand-codebase"
SKILL_DIR = SKILLS_DIR / SKILL_DIR_NAME
SKILL_MD = SKILL_DIR / "SKILL.md"

EXPECTED_REFERENCES = [
    "AGENTS-MD-TEMPLATE.md",
    "DEEPDIVE-TEMPLATES.md",
    "DIMENSIONS.md",
    "ONBOARDING-TEMPLATE.md",
    "PLAYBOOK-ADD-FEATURE.md",
    "PLAYBOOK-CONTRIBUTE.md",
    "PROS-CONS-RUBRIC.md",
    "REUSE-MAP.md",
    "RULES-FILES.md",
]


def test_understand_codebase_skill_md_exists() -> None:
    assert SKILL_MD.exists(), f"SKILL.md not found at {SKILL_MD}"


def test_understand_codebase_frontmatter() -> None:
    """name == dir name; description is substantive and names the deliverables; allowed-tools is a non-empty list."""
    _, fm = split_frontmatter(SKILL_MD.read_text(encoding="utf-8"))

    assert fm.get("name") == SKILL_DIR_NAME, (
        f"Expected name={SKILL_DIR_NAME!r}, got {fm.get('name')!r} — must match the directory name"
    )

    description = fm.get("description")
    assert isinstance(description, str) and len(description.strip()) >= 50, (
        "description must be a substantive string explaining when/why to invoke the skill"
    )
    assert any(token in description for token in ("onboard", "ONBOARDING.md", "AGENTS.md")), (
        "description should mention the onboarding deliverables (ONBOARDING.md / AGENTS.md)"
    )

    allowed_tools = fm.get("allowed-tools")
    assert isinstance(allowed_tools, list) and allowed_tools, "allowed-tools must be a non-empty list"
    for tool in ("Read", "Write", "Agent"):
        assert tool in allowed_tools, f"expected {tool!r} in allowed-tools (the skill composes agents and writes files)"


def test_referenced_companion_files_exist_and_are_substantive() -> None:
    """Every references/<X>.md and templates/<X>.md path named in SKILL.md is on disk and > 1 KB."""
    text = SKILL_MD.read_text(encoding="utf-8")
    referenced = set(re.findall(r"\b((?:references|templates)/[A-Za-z0-9_.-]+\.md)\b", text))
    assert referenced, "expected SKILL.md to reference its references/ and templates/ companion files"
    for rel in sorted(referenced):
        path = SKILL_DIR / rel
        assert path.exists(), f"SKILL.md references {rel!r} but {path} is missing"
        assert path.stat().st_size > 1024, f"{rel} is suspiciously small (< 1 KB) — likely a stub, not the real file"


def test_companion_inventory_is_pinned() -> None:
    """Pin the exact references/ + templates/ inventory so an accidental add/delete fails loudly."""
    refs = sorted(p.name for p in (SKILL_DIR / "references").glob("*.md"))
    assert refs == EXPECTED_REFERENCES, f"references/ inventory drifted: {refs}"
    tmpls = sorted(p.name for p in (SKILL_DIR / "templates").glob("*"))
    assert tmpls == ["onboarding-team.md"], f"templates/ inventory drifted: {tmpls}"
