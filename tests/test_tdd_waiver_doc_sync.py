"""The TDD bullet in engineering-standards.md §2 is generated from plan_parsers.TDD_WAIVER_RULES.

`CANONICAL_TDD_WAIVERS` is what the tdd-sequence-auditor accepts; the rule text used to name a
different, stale set ("docs-only, config-only, or infrastructure-only"). The bullet now sits
between markers and must equal the text rendered here, so a waiver cannot be added, renamed or
reworded in one place only (code-conventions-impact M9.2).

Regenerate with ``scripts/regen-generated.sh``, which runs this file as a script.
"""

from __future__ import annotations

import sys
from pathlib import Path

from aa_ma.plan_parsers import CANONICAL_TDD_WAIVERS, TDD_WAIVER_RULES

REPO = Path(__file__).resolve().parents[1]
RULE = REPO / "claude-code" / "rules" / "engineering-standards.md"
BEGIN = (
    "<!-- BEGIN GENERATED tdd-waivers: from src/aa_ma/plan_parsers.py TDD_WAIVER_RULES;"
    " regenerate with scripts/regen-generated.sh -->"
)
END = "<!-- END GENERATED tdd-waivers -->"


def render() -> str:
    """The §2 TDD bullet, waivers sorted so the output is stable."""
    lines = [
        BEGIN,
        "- **TDD** — write failing tests before implementation; cover happy path, edge",
        "  cases, regressions. A milestone skips the test-first sequence only with a",
        "  canonical `TDD-Waiver:` value:",
    ]
    lines += [
        f"  - `{name}` — {TDD_WAIVER_RULES[name]}" for name in sorted(TDD_WAIVER_RULES)
    ]
    lines.append(END)
    return "\n".join(lines) + "\n"


def block(text: str) -> str:
    """The marker-delimited block in `text`, markers included."""
    start = text.index(BEGIN)
    stop = text.index(END, start) + len(END) + 1
    return text[start:stop]


def test_rule_block_equals_the_regenerated_text() -> None:
    assert block(RULE.read_text()) == render(), "run scripts/regen-generated.sh"


def test_markers_appear_exactly_once() -> None:
    text = RULE.read_text()
    assert text.count(BEGIN) == 1
    assert text.count(END) == 1


def test_every_canonical_waiver_has_a_rule_and_nothing_else_does() -> None:
    assert set(TDD_WAIVER_RULES) == CANONICAL_TDD_WAIVERS


def test_the_rules_say_what_m9_requires() -> None:
    text = render()
    assert "infrastructure-only" not in text
    assert "`tooling-config`" in text
    assert "existing tests" in TDD_WAIVER_RULES["refactor"]
    assert "green" in TDD_WAIVER_RULES["refactor"]
    assert "follow-up test task" in TDD_WAIVER_RULES["hotfix-emergency"]


def test_no_skill_restates_the_retired_skip_list() -> None:
    """Skills point at §2 instead of copying an old skip list ("infrastructure-only" is not a waiver)."""
    hits = [
        f"{path.relative_to(REPO)}:{n}"
        for root in ("claude-code", "docs/spec")
        for path in (REPO / root).rglob("*.md")
        for n, line in enumerate(path.read_text().splitlines(), 1)
        if "infrastructure-only" in line
    ]
    assert hits == [], f"point these at engineering-standards.md §2: {hits}"


def regenerate() -> None:
    """Rewrite the marker-delimited block in place (called by scripts/regen-generated.sh)."""
    text = RULE.read_text()
    RULE.write_text(text.replace(block(text), render()))


if __name__ == "__main__":
    regenerate()
    sys.exit(0)
