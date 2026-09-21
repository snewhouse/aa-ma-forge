"""Shared helpers for agent-file tests (mirrors ``tests/skills/_helpers``)."""

from __future__ import annotations

from pathlib import Path

import yaml


def split_frontmatter(path: Path) -> tuple[dict, str]:
    """Return ``(frontmatter, body)`` for a ``---``-fenced agent file."""
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines and lines[0].strip() == "---", f"{path.name}: missing '---' frontmatter opener"
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    assert end is not None, f"{path.name}: unterminated frontmatter"
    fm = yaml.safe_load("\n".join(lines[1:end]))
    assert isinstance(fm, dict), f"{path.name}: frontmatter is not a mapping"
    return fm, "\n".join(lines[end + 1 :])
