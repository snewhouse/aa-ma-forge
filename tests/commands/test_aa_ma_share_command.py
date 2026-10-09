"""Frontmatter + body assertions for the ``/aa-ma-share`` command (plan-architecture-views M3).

- frontmatter ``name`` == ``"aa-ma-share"`` with a non-empty ``description``
- the body resolves the checkout via ``readlink -f`` on its own installed symlink
- the body calls the tested allowlist script rather than describing an allowlist in prose
- the body never routes through ``aa-ma-render`` (the Artifact tool wraps and renders markdown)
- the command count sites agree with the number of command files on disk (doc-count-drift)
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
COMMAND_MD = REPO_ROOT / "claude-code" / "skills" / "aa-ma-share" / "SKILL.md"


def _frontmatter(path: Path) -> dict:
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines and lines[0].strip() == "---", "missing '---' frontmatter opener"
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    assert end is not None, "unterminated frontmatter"
    fm = yaml.safe_load("\n".join(lines[1:end]))
    assert isinstance(fm, dict), "frontmatter is not a mapping"
    return fm


def test_command_frontmatter() -> None:
    fm = _frontmatter(COMMAND_MD)
    assert fm.get("name") == "aa-ma-share"
    assert isinstance(fm.get("description"), str) and fm["description"].strip()


def test_command_body_contract() -> None:
    body = COMMAND_MD.read_text(encoding="utf-8")
    assert "readlink -f" in body
    assert "scripts/aa-ma-share-allow.sh" in body
    assert "aa-ma-render" not in body


def _count(sub: str, pattern: str) -> int:
    return len(
        [
            q
            for q in (REPO_ROOT / "claude-code" / sub).glob(pattern)
            if q.name != "README.md"
        ]
    )


def test_readme_slash_names_are_shipped_skills() -> None:
    """README's slash-name list names skills on disk (the forge's commands became skills, ADR-0020)."""
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    section = readme.split("### All slash commands", 1)[1].split("\n### ", 1)[0]
    names = set(re.findall(r"^- `/([a-z0-9-]+)`", section, re.MULTILINE))
    skills = {
        p.parent.name for p in (REPO_ROOT / "claude-code" / "skills").glob("*/SKILL.md")
    }
    assert len(names) >= 13 and names <= skills, sorted(names - skills)


def test_security_md_asset_lists_match_disk() -> None:
    """SECURITY.md enumerates every shipped command/skill/agent/hook by name and count."""
    text = (REPO_ROOT / "SECURITY.md").read_text(encoding="utf-8")
    expected = {
        "skills directories": (
            {
                d.name
                for d in (REPO_ROOT / "claude-code" / "skills").iterdir()
                if d.is_dir()
            },
            None,
        ),
        "agent files": (
            {p.stem for p in (REPO_ROOT / "claude-code" / "agents").glob("*.md")},
            None,
        ),
    }
    for label, (names, _) in expected.items():
        m = re.search(rf"- (\d+) {re.escape(label)}: `[^`]+` \(([^)]*)\)", text)
        assert m, f"SECURITY.md: no '{label}' line"
        listed = {x.strip() for x in m.group(2).split(",")}
        assert int(m.group(1)) == len(names), (
            f"{label}: says {m.group(1)}, disk {len(names)}"
        )
        assert listed == names, f"{label}: {sorted(listed ^ names)}"


def test_foundations_count_headings_match_disk() -> None:
    """docs/spec/claude-code-foundations.md `### Skills (N)` / `### Agents (N)` track disk.

    SECURITY.md is covered by test_security_md_asset_lists_match_disk; CLAUDE.md is gitignored.
    """
    text = (REPO_ROOT / "docs" / "spec" / "claude-code-foundations.md").read_text(
        encoding="utf-8"
    )
    on_disk = {
        "Skills": len(
            [d for d in (REPO_ROOT / "claude-code" / "skills").iterdir() if d.is_dir()]
        ),
        "Agents": len(list((REPO_ROOT / "claude-code" / "agents").glob("*.md"))),
    }
    for label, n in on_disk.items():
        m = re.search(rf"^### {label} \((\d+)\)$", text, re.MULTILINE)
        assert m, f"foundations: no '### {label} (N)' heading"
        assert int(m.group(1)) == n, (
            f"foundations: {label} heading says {m.group(1)}, disk has {n}"
        )
