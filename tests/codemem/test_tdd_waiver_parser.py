"""Tests for aa_ma.plan_parsers.parse_tdd_waiver.

Contract:
- Extracts the `TDD-Waiver:` value from a milestone block.
- Returns (value, is_valid, error) tuple.
- value: str | None — raw value (lower-cased, stripped) or None if field absent.
- is_valid: bool — True iff value is one of CANONICAL_TDD_WAIVERS or value is None.
- error: str | None — human-readable error when is_valid is False.

Canonical values (from ADR-0005):
    refactor | docs-only | prototype | hotfix-emergency | tooling-config

Novel values rejected — must be added via plan + ADR.
"""
from __future__ import annotations

import pytest

from aa_ma.plan_parsers import (
    CANONICAL_TDD_WAIVERS,
    parse_tdd_waiver,
)


class TestCanonicalWaivers:
    """Each canonical value should parse and validate."""

    @pytest.mark.parametrize(
        "waiver",
        ["refactor", "docs-only", "prototype", "hotfix-emergency", "tooling-config"],
    )
    def test_canonical_value_is_valid(self, waiver: str) -> None:
        block = f"""## Milestone 4: Refactor module X
- Status: PENDING
- TDD-Waiver: {waiver}
- Gate: HARD
"""
        value, is_valid, error = parse_tdd_waiver(block)
        assert value == waiver
        assert is_valid is True
        assert error is None

    def test_canonical_set_size(self) -> None:
        assert CANONICAL_TDD_WAIVERS == frozenset(
            {"refactor", "docs-only", "prototype", "hotfix-emergency", "tooling-config"}
        )


class TestAbsentField:
    """Missing TDD-Waiver field returns (None, True, None) — most milestones have no waiver."""

    def test_missing_field_returns_none(self) -> None:
        block = """## Milestone 1: New feature
- Status: PENDING
- Gate: HARD
"""
        value, is_valid, error = parse_tdd_waiver(block)
        assert value is None
        assert is_valid is True
        assert error is None

    def test_empty_block(self) -> None:
        value, is_valid, error = parse_tdd_waiver("")
        assert value is None
        assert is_valid is True


class TestNonCanonicalValues:
    """Novel waiver values are rejected."""

    @pytest.mark.parametrize(
        "bad_value",
        ["idk", "later", "skip-tests", "no-tests", "WIP", "exempt", "lazy"],
    )
    def test_non_canonical_value_is_rejected(self, bad_value: str) -> None:
        block = f"""## Milestone 1: Test
- TDD-Waiver: {bad_value}
"""
        value, is_valid, error = parse_tdd_waiver(block)
        assert is_valid is False
        assert error is not None


class TestEdgeCases:
    """Whitespace, bold formatting, HTML comments."""

    def test_extra_whitespace_tolerated(self) -> None:
        block = """## Milestone 1: Test
- TDD-Waiver:    refactor
"""
        value, is_valid, _ = parse_tdd_waiver(block)
        assert value == "refactor"
        assert is_valid is True

    def test_bold_field_name_tolerated(self) -> None:
        block = """## Milestone 1: Test
- **TDD-Waiver:** prototype
"""
        value, is_valid, _ = parse_tdd_waiver(block)
        assert value == "prototype"
        assert is_valid is True

    def test_field_inside_html_comment_ignored(self) -> None:
        block = """## Milestone 1: Test
<!-- Example: TDD-Waiver: refactor -->
- Status: PENDING
"""
        value, is_valid, _ = parse_tdd_waiver(block)
        assert value is None
        assert is_valid is True

    def test_canonical_waiver_with_trailing_comment(self) -> None:
        """Allow trailing prose after the canonical value."""
        block = """## Milestone 1: Test
- TDD-Waiver: hotfix-emergency  (production outage 2026-05-11)
"""
        value, is_valid, _ = parse_tdd_waiver(block)
        # Parser should extract the canonical token; prose is metadata
        assert value == "hotfix-emergency"
        assert is_valid is True
