"""Diagram-Waiver: plan-level, planning-time field; same fail-closed contract as TDD-Waiver (L-011)."""

import pytest

from aa_ma.plan_parsers import CANONICAL_DIAGRAM_WAIVERS, parse_diagram_waiver


class TestCanonical:
    @pytest.mark.parametrize("v", sorted(CANONICAL_DIAGRAM_WAIVERS))
    def test_plain_form(self, v: str) -> None:
        assert parse_diagram_waiver(f"# Plan\n**Created:** 2026-09-11\nDiagram-Waiver: {v}\n") == (v, True, None)

    @pytest.mark.parametrize("v", sorted(CANONICAL_DIAGRAM_WAIVERS))
    def test_bold_pair_form(self, v: str) -> None:
        assert parse_diagram_waiver(f"**Diagram-Waiver:** {v}\n") == (v, True, None)


class TestRejection:
    @pytest.mark.parametrize("bad", ["NONE", "docs only", "waived", "single_file", "**none**"])
    def test_non_canonical(self, bad: str) -> None:
        value, ok, err = parse_diagram_waiver(f"Diagram-Waiver: {bad}\n")
        assert ok is False and err

    def test_absent_is_none_and_valid(self) -> None:
        assert parse_diagram_waiver("# Plan\n") == (None, True, None)

    def test_backtick_wrapped_is_not_seen(self) -> None:
        # L-011: backtick-wrapped fields are invisible to the grammar (verified: _extract_field rejects them).
        assert parse_diagram_waiver("`Diagram-Waiver: none`\n")[0] is None
