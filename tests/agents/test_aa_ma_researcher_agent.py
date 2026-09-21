"""Frontmatter + prompt assertions for the ``aa-ma-researcher`` agent (M4.2).

The agent is the non-nesting worker behind ``Skill(aa-ma-research)`` (ADR-0012, D7).
Upstream ``research`` has documented self-nesting (mattpocock/skills#530); our fix is
structural — the agent has no ``Agent`` tool — with a prompt prohibition on ``claude``
as the fallback. These tests pin both.
"""

from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENT_PATH = REPO_ROOT / "claude-code" / "agents" / "aa-ma-researcher.md"

EXPECTED_TOOLS = {"Read", "Glob", "Grep", "Bash", "WebSearch", "WebFetch", "Write"}
REQUIRED_PROMPT_PHRASES = (
    "exactly one file",
    "cite",
    "Not pursued",
    "never run `claude`",
)


def _split(path: Path) -> tuple[dict, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines and lines[0].strip() == "---", (
        f"{path.name}: missing '---' frontmatter opener"
    )
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    assert end is not None, f"{path.name}: unterminated frontmatter"
    fm = yaml.safe_load("\n".join(lines[1:end]))
    assert isinstance(fm, dict), f"{path.name}: frontmatter is not a mapping"
    return fm, "\n".join(lines[end + 1 :])


def test_agent_file_exists() -> None:
    assert AGENT_PATH.exists(), (
        "missing agent file: claude-code/agents/aa-ma-researcher.md"
    )


def test_agent_frontmatter_tools_exact() -> None:
    fm, _ = _split(AGENT_PATH)
    assert fm.get("name") == "aa-ma-researcher"
    assert isinstance(fm.get("description"), str) and fm["description"].strip()
    tools = fm.get("tools")
    assert isinstance(tools, str), (
        "'tools' must be a comma-separated string (agent convention)"
    )
    tool_set = {t.strip() for t in tools.split(",") if t.strip()}
    assert tool_set == EXPECTED_TOOLS, (
        f"tools drifted from the M4 Contract: {tool_set ^ EXPECTED_TOOLS}"
    )
    assert "Agent" not in tool_set, (
        "aa-ma-researcher must not be able to re-delegate (no Agent tool)"
    )


def test_agent_prompt_carries_the_contract() -> None:
    _, prompt = _split(AGENT_PATH)
    for phrase in REQUIRED_PROMPT_PHRASES:
        assert phrase in prompt, f"prompt lacks {phrase!r}"
