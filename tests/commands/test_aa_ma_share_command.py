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
COMMANDS = REPO_ROOT / "claude-code" / "commands"
COMMAND_MD = COMMANDS / "aa-ma-share.md"


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


def test_command_count_sites_match_disk() -> None:
    n = len(list(COMMANDS.glob("*.md")))
    sites = {
        "CLAUDE.md": r"commands/\s+(\d+) slash commands",
        "SECURITY.md": r"- (\d+) command files:",
    }
    for rel, pat in sites.items():
        m = re.search(pat, (REPO_ROOT / rel).read_text(encoding="utf-8"))
        assert m, f"{rel}: count line not found"
        assert int(m.group(1)) == n, f"{rel} says {m.group(1)} commands, disk has {n}"
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    table = readme.split("### All commands", 1)[1].split("\n\n", 2)[1]
    rows = {m.group(1) for m in re.finditer(r"^\| `/([a-z0-9-]+)`", table, re.MULTILINE)}
    assert rows == {p.stem for p in COMMANDS.glob("*.md")}, rows ^ {p.stem for p in COMMANDS.glob("*.md")}
