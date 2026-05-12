"""Frontmatter + body assertions for the ``/understand-codebase`` command.

A thin wrapper that invokes ``Skill(understand-codebase)``. Vendored into aa-ma-forge
v0.9.0 — see docs/adr/0006-understand-codebase-adoption.md.

Acceptance criteria (understand-codebase-skill M2.3):
  - the command ``.md`` exists under ``claude-code/commands/``
  - frontmatter ``name`` == ``"understand-codebase"`` with a non-empty ``description``
  - the body invokes ``Skill(understand-codebase)`` (it is a thin wrapper, not a re-implementation)
  - the body documents the tier flags ``--quick`` / ``--standard`` / ``--deep``
"""

from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
COMMAND_MD = REPO_ROOT / "claude-code" / "commands" / "understand-codebase.md"


def _frontmatter(path: Path) -> dict:
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines and lines[0].strip() == "---", "missing '---' frontmatter opener"
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    assert end is not None, "unterminated frontmatter"
    fm = yaml.safe_load("\n".join(lines[1:end]))
    assert isinstance(fm, dict), "frontmatter is not a mapping"
    return fm


def test_command_file_exists() -> None:
    assert COMMAND_MD.exists(), f"missing command file: {COMMAND_MD}"


def test_command_frontmatter() -> None:
    fm = _frontmatter(COMMAND_MD)
    assert fm.get("name") == "understand-codebase", f"name={fm.get('name')!r}"
    description = fm.get("description")
    assert isinstance(description, str) and description.strip(), "missing/empty 'description'"


def test_command_delegates_to_skill() -> None:
    body = COMMAND_MD.read_text(encoding="utf-8")
    assert "Skill(understand-codebase)" in body, (
        "command body must invoke Skill(understand-codebase) — it is a thin wrapper around the skill"
    )


def test_command_documents_tier_flags() -> None:
    body = COMMAND_MD.read_text(encoding="utf-8")
    for flag in ("--quick", "--standard", "--deep"):
        assert flag in body, f"command should document the {flag} tier flag"
