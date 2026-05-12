"""Frontmatter + cross-reference assertions for the 4 ``codebase-onboarding-*`` worker agents.

These agents power the Deep tier of the ``understand-codebase`` skill (and are reusable
standalone). Vendored into aa-ma-forge v0.9.0 — see docs/adr/0006-understand-codebase-adoption.md.

Acceptance criteria (understand-codebase-skill M2.2):
  - each agent ``.md`` exists under ``claude-code/agents/``
  - each has well-formed YAML frontmatter with ``name`` (== filename stem), ``description``,
    and ``tools`` (a non-empty comma-separated string — the aa-ma-forge agent convention)
  - ``SKILL.md`` (Deep-tier workflow) and ``templates/onboarding-team.md`` (the TeamCreate
    composition) reference all 4 worker agents by ``subagent_type``
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENTS_DIR = REPO_ROOT / "claude-code" / "agents"
SKILL_DIR = REPO_ROOT / "claude-code" / "skills" / "understand-codebase"

AGENT_NAMES = [
    "codebase-onboarding-conventions",
    "codebase-onboarding-health",
    "codebase-onboarding-runbook",
    "codebase-onboarding-synthesizer",
]


def _frontmatter(path: Path) -> dict:
    lines = path.read_text(encoding="utf-8").splitlines()
    assert lines and lines[0].strip() == "---", f"{path.name}: missing '---' frontmatter opener"
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    assert end is not None, f"{path.name}: unterminated frontmatter"
    fm = yaml.safe_load("\n".join(lines[1:end]))
    assert isinstance(fm, dict), f"{path.name}: frontmatter is not a mapping"
    return fm


@pytest.mark.parametrize("agent", AGENT_NAMES)
def test_agent_file_exists(agent: str) -> None:
    assert (AGENTS_DIR / f"{agent}.md").exists(), f"missing agent file: claude-code/agents/{agent}.md"


@pytest.mark.parametrize("agent", AGENT_NAMES)
def test_agent_frontmatter(agent: str) -> None:
    fm = _frontmatter(AGENTS_DIR / f"{agent}.md")
    assert fm.get("name") == agent, f"{agent}.md: name={fm.get('name')!r} must match the filename stem"

    description = fm.get("description")
    assert isinstance(description, str) and description.strip(), f"{agent}.md: missing/empty 'description'"

    tools = fm.get("tools")
    assert isinstance(tools, str) and tools.strip(), (
        f"{agent}.md: 'tools' must be a non-empty comma-separated string (aa-ma-forge agent convention)"
    )
    tool_set = {t.strip() for t in tools.split(",") if t.strip()}
    assert {"Read", "Write"} <= tool_set, f"{agent}.md: expected at least Read + Write in 'tools', got {sorted(tool_set)}"


def test_skill_workflow_references_all_workers() -> None:
    """SKILL.md's Deep-tier workflow names all 4 worker agents."""
    skill_text = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
    for agent in AGENT_NAMES:
        assert agent in skill_text, f"SKILL.md does not reference worker agent {agent!r}"


def test_team_template_references_all_workers() -> None:
    """The Deep-tier TeamCreate composition (templates/onboarding-team.md) names all 4 worker agents."""
    team_text = (SKILL_DIR / "templates" / "onboarding-team.md").read_text(encoding="utf-8")
    for agent in AGENT_NAMES:
        assert agent in team_text, f"templates/onboarding-team.md does not reference worker agent {agent!r}"
