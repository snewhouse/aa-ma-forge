"""understand-codebase v1 upgrades (codebase-analysis-skills M5): the skill text pins the new steps.

AC3 and AC6 are text contracts; the code behind them (ground, changed-since, validate, run) is
tested in tests/analysis.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = ROOT / "claude-code/skills/understand-codebase"
SKILL = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
DIMENSIONS = (SKILL_DIR / "references/DIMENSIONS.md").read_text(encoding="utf-8")
AGENTS_TEMPLATE = (SKILL_DIR / "references/AGENTS-MD-TEMPLATE.md").read_text(encoding="utf-8")
ONBOARDING_TEMPLATE = (SKILL_DIR / "references/ONBOARDING-TEMPLATE.md").read_text(encoding="utf-8")
RUNBOOK = (ROOT / "claude-code/agents/codebase-onboarding-runbook.md").read_text(encoding="utf-8")
HEALTH = (ROOT / "claude-code/agents/codebase-onboarding-health.md").read_text(encoding="utf-8")

CODEMEM_TOOLS = ("hot_spots", "co_changes", "owners", "layers")
AGENTS_HEADINGS = {"Commands", "Gotchas", "Rules pointers"}  # AC3: pinned set
STATUSES = ("verified", "failed", "timeout", "not_run", "refused")
SKIPPED_WITHOUT_CLI = ("grounding", "onboarding.json", "currency check", "incremental regeneration")


def _section(text: str, heading: str) -> str:
    """From `heading` up to the next heading of the same or a higher level."""
    level = len(heading) - len(heading.lstrip("#"))
    start = text.index(heading)
    nxt = re.compile(rf"^#{{1,{level}}} ", re.M)
    m = nxt.search(text, start + len(heading))
    return text[start : m.start() if m else len(text)]


TIERS = {
    "Quick": _section(SKILL, "### Quick"),
    "Standard": _section(SKILL, "### Standard"),
    "Deep": _section(SKILL, "### Deep"),
}


# --- AC3 -------------------------------------------------------------------------------------


def test_runbook_never_runs_a_build_test_or_lint_command() -> None:
    line = next(ln for ln in RUNBOOK.splitlines() if ln.startswith("- **Read-only on the target.**"))
    assert "never run a build, test or lint command" in line
    assert "main thread" in line and "aa-ma-analysis run" in line
    assert "If you do try a command" not in RUNBOOK


def test_claim_check_samples_10_in_standard_and_20_in_deep() -> None:
    assert "10 sampled claims" in TIERS["Standard"]
    assert "~20 sampled claims" in TIERS["Deep"]


@pytest.mark.parametrize("dim", ["## 4 — Directory map & structure", "## 13 — Repo health snapshot"])
def test_dims_4_and_13_read_all_four_codemem_tools(dim: str) -> None:
    body = _section(DIMENSIONS, dim)
    assert "codemem query" in body
    assert all(f"`{tool}`" in body for tool in CODEMEM_TOOLS), body


def test_health_agent_reads_codemem_instead_of_rederiving() -> None:
    assert "codemem query" in HEALTH
    assert all(f"`{tool}`" in HEALTH for tool in ("hot_spots", "co_changes", "owners"))


def test_agents_template_keeps_only_what_code_cannot_tell() -> None:
    template = _section(AGENTS_TEMPLATE, "## TEMPLATE")
    fence = template[template.index("```markdown") : template.rindex("```")]
    headings = set(re.findall(r"^## (.+?)\s*$", fence, re.M))
    assert headings == AGENTS_HEADINGS


# --- the other v1 steps ----------------------------------------------------------------------


@pytest.mark.parametrize("tier", list(TIERS))
def test_every_tier_grounds_and_keeps_a_ledger(tier: str) -> None:
    body = TIERS[tier]
    assert "aa-ma-analysis ground" in body
    assert "coverage ledger" in body


def test_ground_failures_are_re_asked_once_then_dropped() -> None:
    assert "re-ask once" in SKILL and "drop the claim" in SKILL


def test_currency_check_is_the_main_threads_job() -> None:
    assert "aa-ma-analysis run" in SKILL
    assert "main thread" in SKILL and "asks once" in SKILL
    for text in (SKILL, ONBOARDING_TEMPLATE):
        assert all(s in text for s in STATUSES)


def test_onboarding_json_is_written_and_validated() -> None:
    assert ".claude/onboarding/onboarding.json" in SKILL
    assert "aa-ma-analysis validate onboarding" in SKILL
    assert "aa-ma-analysis ground --cited" in SKILL  # the section map comes from citations


def test_a_rerun_regenerates_only_the_changed_sections() -> None:
    assert "aa-ma-analysis changed-since" in SKILL
    assert "regenerate only" in SKILL


def test_without_the_cli_every_skip_is_named_in_provenance() -> None:
    rule = next(p for p in SKILL.split("\n\n") if "CLI is unavailable" in p)
    assert "Provenance" in rule
    assert all(s in rule for s in SKIPPED_WITHOUT_CLI), rule
