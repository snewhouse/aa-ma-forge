"""The forge ships no commands (code-conventions-impact M3, ADR-0020).

A stem that is both a command and a skill gives `/name` two entry points that drift
apart; with no commands at all, no stem can collide.
"""

from __future__ import annotations

from ._helpers import REPO_ROOT

COMMANDS = REPO_ROOT / "claude-code" / "commands"


def test_the_forge_ships_no_commands() -> None:
    assert not COMMANDS.exists() or not any(COMMANDS.iterdir())
