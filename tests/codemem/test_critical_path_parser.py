"""Tests for aa_ma.plan_parsers.parse_critical_path and CANONICAL_CRITICAL_PATHS.

`Critical-Path:` was the only one of the three canonical-enum fields with no
constant in code. `Skill(plan-verification)` Angle 6 check #2 claims to reject
novel values; with nothing to check against it was manual-only, so a typo or an
invented value passed silently and the §6.7 gate then demanded provenance
evidence for a value no rule recognised.

Two things are pinned here that a happy-path test would miss:

* the enum matches `claude-code/rules/engineering-standards.md`, which is the
  documented source of truth — drift between the two is the whole failure mode;
* the **bold** form is parsed, because that is what the §6.7 gate greps for
  (`^- \\*\\*Critical-Path:\\*\\* \\S`). A parser that only read the plain form
  would report a value the gate cannot see.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from aa_ma.grammar import split_milestones
from aa_ma.plan_parsers import CANONICAL_CRITICAL_PATHS, parse_critical_path

REPO_ROOT = Path(__file__).resolve().parents[2]
ENG_STANDARDS = REPO_ROOT / "claude-code" / "rules" / "engineering-standards.md"


def test_canonical_set_is_exactly_the_six_documented_values() -> None:
    assert CANONICAL_CRITICAL_PATHS == frozenset(
        {
            "auth-flow",
            "data-xform",
            "external-api",
            "version-pipeline",
            "doc-count-drift",
            "hook-modification",
        }
    )


def test_enum_matches_engineering_standards_table() -> None:
    """The rule file is the source of truth; the constant must not drift from it.

    Adding a value to one and not the other is the exact silent-divergence this
    milestone exists to close, one layer up.
    """
    text = ENG_STANDARDS.read_text(encoding="utf-8")
    # Rows look like: | `auth-flow`        | Authentication, ... |
    documented = set(re.findall(r"^\|\s*`([a-z-]+)`\s*\|", text, re.MULTILINE))
    # The table is the only place backticked kebab tokens appear in a leading
    # table cell, but intersect defensively rather than asserting equality on a
    # set scraped from prose.
    assert CANONICAL_CRITICAL_PATHS <= documented, (
        f"in code but not documented in engineering-standards.md: "
        f"{sorted(CANONICAL_CRITICAL_PATHS - documented)}"
    )


def test_scrape_is_not_vacuous() -> None:
    """Guard the guard: if the scrape returned nothing, the test above passes."""
    text = ENG_STANDARDS.read_text(encoding="utf-8")
    documented = set(re.findall(r"^\|\s*`([a-z-]+)`\s*\|", text, re.MULTILINE))
    assert len(documented) >= 6


@pytest.mark.parametrize("value", sorted(CANONICAL_CRITICAL_PATHS))
def test_bold_form_parses_for_every_canonical_value(value: str) -> None:
    block = f"## Milestone 1: X\n\n- Status: PENDING\n- **Critical-Path:** {value}\n"
    assert parse_critical_path(block) == (value, True, None)


def test_plain_form_also_parses() -> None:
    block = "## Milestone 1: X\n- Critical-Path: data-xform\n"
    value, is_valid, error = parse_critical_path(block)
    assert (value, is_valid, error) == ("data-xform", True, None)


def test_absent_field_is_valid_absent_field_semantic() -> None:
    """Absence is valid — §6.7 skips the check entirely when the field is absent."""
    block = "## Milestone 1: X\n- Status: PENDING\n"
    assert parse_critical_path(block) == (None, True, None)


def test_novel_value_is_rejected() -> None:
    block = "## Milestone 1: X\n- **Critical-Path:** database-migration\n"
    value, is_valid, error = parse_critical_path(block)
    assert value == "database-migration"
    assert is_valid is False
    assert error is not None


def test_case_variants_are_rejected() -> None:
    """Matches the Audit-Profile/TDD-Waiver precedent: exact lower-case only."""
    block = "## Milestone 1: X\n- **Critical-Path:** Data-Xform\n"
    _, is_valid, _ = parse_critical_path(block)
    assert is_valid is False


def test_backticked_value_is_rejected_like_the_other_enums() -> None:
    """A backticked value is what silently broke this plan's own artifacts."""
    block = "## Milestone 1: X\n- **Critical-Path:** `data-xform`\n"
    _, is_valid, _ = parse_critical_path(block)
    assert is_valid is False


def test_this_plans_own_milestones_all_parse() -> None:
    """Dogfood: every Critical-Path in the active plan must be canonical."""
    tasks = (
        REPO_ROOT
        / ".claude"
        / "dev"
        / "active"
        / "milestone-grammar-ssot"
        / "milestone-grammar-ssot-tasks.md"
    )
    if not tasks.exists():  # archived after completion
        pytest.skip("plan archived")
    blocks = split_milestones(tasks.read_text(encoding="utf-8"))
    assert blocks, "no milestones parsed — the assertion below would be vacuous"
    for block in blocks:
        _, is_valid, error = parse_critical_path(block.text)
        assert is_valid, f"Milestone {block.number}: {error}"
