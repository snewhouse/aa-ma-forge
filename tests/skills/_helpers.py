"""Shared helpers for SKILL.md frontmatter tests across the plugin's forked skills.

Used by test_grill_with_docs_frontmatter.py (M1.7), test_prototype_frontmatter.py
(M2.8), and test_write_a_skill_frontmatter.py (M2.8).
"""

from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = REPO_ROOT / "claude-code" / "skills"


def split_frontmatter(text: str) -> tuple[str, dict]:
    """Return (provenance_lines, frontmatter_dict). Strict — raises on malformed input.

    Skips optional HTML-comment provenance lines at the top, then parses the
    standard `---` YAML frontmatter block.
    """
    lines = text.splitlines()
    i = 0
    provenance: list[str] = []
    while i < len(lines) and lines[i].startswith("<!--"):
        provenance.append(lines[i])
        i += 1
    if i >= len(lines) or lines[i].strip() != "---":
        raise ValueError(
            f"Expected '---' frontmatter opener at line {i + 1}, "
            f"got: {lines[i] if i < len(lines) else '<EOF>'}"
        )
    i += 1
    body_start = i
    while i < len(lines) and lines[i].strip() != "---":
        i += 1
    if i >= len(lines):
        raise ValueError("Unterminated frontmatter — no closing '---' found")
    fm_text = "\n".join(lines[body_start:i])
    fm = yaml.safe_load(fm_text)
    if not isinstance(fm, dict):
        raise ValueError(f"Frontmatter is not a mapping; got {type(fm).__name__}")
    return "\n".join(provenance), fm


def assert_skill_frontmatter(
    skill_dir_name: str,
    expected_upstream_path: str,
    min_description_length: int = 50,
) -> tuple[str, dict]:
    """Common assertion bundle for forked-skill SKILL.md files.

    Verifies:
      - SKILL.md exists at claude-code/skills/<skill_dir_name>/SKILL.md
      - frontmatter `name` matches `skill_dir_name`
      - frontmatter `description` is a non-empty string of >= min_description_length chars
      - provenance comment references mattpocock/skills and the expected upstream path

    Returns (provenance_lines, frontmatter_dict) for further assertions.
    """
    skill_path = SKILLS_DIR / skill_dir_name / "SKILL.md"
    assert skill_path.exists(), f"SKILL.md not found at {skill_path}"

    text = skill_path.read_text(encoding="utf-8")
    provenance, fm = split_frontmatter(text)

    assert fm.get("name") == skill_dir_name, (
        f"Expected name={skill_dir_name!r}, got name={fm.get('name')!r}. "
        f"Must match the directory name."
    )

    description = fm.get("description")
    assert description is not None, "Missing 'description' field in frontmatter"
    assert isinstance(description, str), (
        f"'description' must be str, got {type(description).__name__}"
    )
    assert len(description.strip()) >= min_description_length, (
        f"'description' is too short ({len(description.strip())} chars); "
        f"Skill descriptions should explain when/why to invoke "
        f"(>= {min_description_length} chars)."
    )

    assert "mattpocock/skills" in provenance, (
        "Forked-from provenance comment is missing or does not reference "
        "the canonical upstream (mattpocock/skills)."
    )
    assert expected_upstream_path in provenance, (
        f"Provenance comment should name the upstream skill path "
        f"({expected_upstream_path!r})"
    )

    return provenance, fm
