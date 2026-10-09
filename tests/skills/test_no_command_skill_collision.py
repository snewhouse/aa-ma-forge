"""A slash name is a skill or a command, never both (code-conventions-impact M3, ADR-0020).

When a stem is both, `/name` reaches the command and the skill is reachable only by the
model — two copies of one entry point that drift apart.
"""

from __future__ import annotations

from pathlib import Path

CC = Path(__file__).resolve().parents[2] / "claude-code"


def test_no_stem_is_both_a_command_and_a_skill() -> None:
    commands = {p.stem for p in (CC / "commands").glob("*.md")}
    skills = {p.parent.name for p in (CC / "skills").glob("*/SKILL.md")}
    assert commands & skills == set()
