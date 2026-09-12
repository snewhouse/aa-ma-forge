"""The planning-standard element count is stated as an integer in several live prose
sites. Spec §XI is the source of truth; every other site must agree with it, so the
next element bump cannot leave a stale "13" behind (proactive Tier 6 — L-010 class).
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _spec_count() -> int:
    text = (ROOT / "docs/spec/aa-ma-specification.md").read_text(encoding="utf-8")
    section = text.split("### Required Outputs (Every Plan)", 1)[1].split("### Format & Mapping", 1)[0]
    return len(re.findall(r"^\d+\. \*\*", section, re.MULTILINE))


def _ints(path: str, pattern: str) -> list[int]:
    text = (ROOT / path).read_text(encoding="utf-8")
    found = [int(m) for m in re.findall(pattern, text)]
    assert found, f"{path}: pattern {pattern!r} matched nothing — site moved or was reworded"
    return found


SITES = {
    "claude-code/rules/aa-ma.md": r"these (\d+) outputs:",
    "README.md": r"\*\*(\d+) mandatory outputs\*\*",
    "docs/spec/claude-code-foundations.md": r"(\d+) mandatory outputs",
    "docs/templates/plan-template.md": r"(?:all|ALL) (\d+) (?:mandatory planning|AA-MA planning) elements",
    "claude-code/agents/aa-ma-validator.md": r"\((\d+) AA-MA Elements\)|/(\d+) elements present",
    "claude-code/commands/aa-ma-plan.md": r"(?:ALL|all) (\d+) (?:required )?elements",
    "claude-code/skills/aa-ma-plan-workflow/references/PHASE_4_PLAN_GENERATION.md": r"(?:ALL|all) (\d+) (?:required |AA-MA )?elements",
    "claude-code/agents/aa-ma-scribe.md": r"all (\d+) AA-MA elements",
}


def test_spec_lists_thirteen_or_more_elements() -> None:
    assert _spec_count() >= 13


def test_every_prose_site_matches_spec_count() -> None:
    expected = _spec_count()
    drift = {}
    for path, pattern in SITES.items():
        text = (ROOT / path).read_text(encoding="utf-8")
        found = [int(g) for m in re.findall(pattern, text) for g in (m if isinstance(m, tuple) else (m,)) if g]
        assert found, f"{path}: pattern matched nothing — site moved or was reworded"
        if any(n != expected for n in found):
            drift[path] = found
    assert not drift, f"element count is {expected} in spec §XI but these sites disagree: {drift}"


def test_readme_list_length_matches_its_own_heading() -> None:
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    n = int(re.search(r"\*\*(\d+) mandatory outputs\*\*", text).group(1))
    block = text.split("mandatory outputs**:", 1)[1].split("\n\n", 2)[1]
    assert len(re.findall(r"^\d+\. ", block, re.MULTILINE)) == n
