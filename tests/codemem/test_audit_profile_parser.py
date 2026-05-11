"""Tests for aa_ma.plan_parsers.parse_audit_profile.

Contract:
- Extracts the `Audit-Profile:` value from a milestone block in tasks.md.
- Returns (value, is_valid, error) tuple.
- value: str | None — the raw value (lower-cased, stripped) or None if field absent.
- is_valid: bool — True iff value is one of CANONICAL_AUDIT_PROFILES or value is None.
- error: str | None — human-readable error when is_valid is False.

Canonical values (from ADR-0005, mirrors Critical-Path enum pattern):
    full | code-only | docs-only | infra | custom

Novel values are rejected — must be added via plan + ADR.
"""
from __future__ import annotations

import pytest

from aa_ma.plan_parsers import (
    CANONICAL_AUDIT_PROFILES,
    parse_audit_profile,
)


class TestCanonicalProfiles:
    """Each canonical value should parse and validate."""

    @pytest.mark.parametrize("profile", ["full", "code-only", "docs-only", "infra", "custom"])
    def test_canonical_value_is_valid(self, profile: str) -> None:
        block = f"""## Milestone 1: Test
- Status: PENDING
- Audit-Profile: {profile}
- Gate: HARD
"""
        value, is_valid, error = parse_audit_profile(block)
        assert value == profile
        assert is_valid is True
        assert error is None

    def test_canonical_set_size(self) -> None:
        assert CANONICAL_AUDIT_PROFILES == frozenset({"full", "code-only", "docs-only", "infra", "custom"})


class TestAbsentField:
    """Missing Audit-Profile field returns (None, True, None) — grandfathered handling is elsewhere."""

    def test_missing_field_returns_none(self) -> None:
        block = """## Milestone 1: Test
- Status: PENDING
- Gate: HARD
"""
        value, is_valid, error = parse_audit_profile(block)
        assert value is None
        assert is_valid is True
        assert error is None

    def test_empty_block(self) -> None:
        value, is_valid, error = parse_audit_profile("")
        assert value is None
        assert is_valid is True


class TestNonCanonicalValues:
    """Novel values are rejected with helpful error."""

    @pytest.mark.parametrize(
        "bad_value",
        ["FULL", "Full", "all", "comprehensive", "lite", "heavy", "minimal", "nope"],
    )
    def test_non_canonical_value_is_rejected(self, bad_value: str) -> None:
        block = f"""## Milestone 1: Test
- Audit-Profile: {bad_value}
"""
        value, is_valid, error = parse_audit_profile(block)
        # value may be normalized to lower-case; the rejection happens because
        # the lower-cased form is also not in the canonical set.
        # For variants like "FULL" / "Full" — these SHOULD be rejected
        # (we want exact canonical lower-case match to avoid ambiguity).
        if bad_value.lower() == "full":
            # "FULL" / "Full" are NOT canonical (canonical is "full" exact)
            # The parser may or may not normalize case; treat as rejection.
            assert is_valid is False
            assert error is not None
        else:
            assert is_valid is False
            assert error is not None
            assert bad_value.lower() in error.lower() or "canonical" in error.lower()


class TestEdgeCases:
    """Whitespace, trailing chars, alternate formatting."""

    def test_extra_whitespace_tolerated(self) -> None:
        block = """## Milestone 1: Test
- Audit-Profile:    full
"""
        value, is_valid, _ = parse_audit_profile(block)
        assert value == "full"
        assert is_valid is True

    def test_bold_field_name_tolerated(self) -> None:
        """Mirror Status format: both `- Status:` and `- **Status:**` exist in real plans."""
        block = """## Milestone 1: Test
- **Audit-Profile:** code-only
"""
        value, is_valid, _ = parse_audit_profile(block)
        assert value == "code-only"
        assert is_valid is True

    def test_field_inside_html_comment_ignored(self) -> None:
        """HTML-comment instructions in templates shouldn't be parsed as values."""
        block = """## Milestone 1: Test
<!-- Example: Audit-Profile: full -->
- Status: PENDING
"""
        value, is_valid, _ = parse_audit_profile(block)
        # The HTML-comment line should be stripped; result is "no field"
        assert value is None
        assert is_valid is True

    def test_first_value_wins_when_duplicated(self) -> None:
        """If the field appears twice (shouldn't happen but defend), first occurrence wins."""
        block = """## Milestone 1: Test
- Audit-Profile: full
- Audit-Profile: docs-only
"""
        value, is_valid, _ = parse_audit_profile(block)
        assert value == "full"
        assert is_valid is True
