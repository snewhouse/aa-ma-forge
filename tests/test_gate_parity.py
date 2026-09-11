"""Behavioural no-second-parser guard (M5 5.3 acceptance).

For every contract row, drive `aa_ma.gate` AND the primitive it is supposed to
be built on over the same input, and assert identical readings. A grep for
`re.compile` is satisfiable by `re.match`; this is not.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from aa_ma import enforce, plan_parsers
from aa_ma.gate import EXIT_OK, EXIT_UNREADABLE, answer
from aa_ma.grammar import split_milestones

NBSP = " "

FIELD_ROWS = [
    (1, "Status", "- Status: ACTIVE"),
    (2, "Status", "  - Status: ACTIVE"),
    (3, "Status", "\t- Status: ACTIVE"),
    (4, "Status", "- **Status:** ACTIVE"),
    (5, "Status", "- **Status**: ACTIVE"),
    (6, "Status", "- Status: **ACTIVE**"),
    (7, "Status", "- Status: ACTIVE (resumed after compaction)"),
    (8, "Status", "- Status: COMPLETE (2026-05-09, commit abc1234)"),
    (9, "Status", "* Status: ACTIVE"),
    (10, "Status", f"-{NBSP}Status: ACTIVE"),
    (11, "Gate", "- Gate: hard"),
    (12, "Gate", "- Gate: TYPO"),
    (13, "Mode", "- Mode: TYPO"),
    (14, "Status", "- Status: ACTIVE\r"),
]


@pytest.mark.parametrize(("row", "field", "line"), FIELD_ROWS)
def test_gate_reads_each_field_row_exactly_as_enforce_does(
    tmp_path: Path, row: int, field: str, line: str
) -> None:
    status_line = "" if field == "Status" else "- Status: ACTIVE\n"
    body = f"## Milestone 1: T\n{status_line}{line}\n"
    p = tmp_path / "t-tasks.md"
    p.write_bytes(body.encode())
    canonical = {
        "Status": enforce.MILESTONE_STATUSES,
        "Gate": enforce.GATES,
        "Mode": enforce.MODES,
    }[field]
    primitive = enforce.read_enforced_field(body.replace("\r", ""), field, canonical)
    got = answer(p)
    if primitive.is_valid:
        assert got.exit_code in (EXIT_OK, 1), f"row {row}: {got.errors}"
        if field == "Status":
            assert (got.milestone is not None) == (primitive.value == "ACTIVE")
            if got.milestone:
                assert got.milestone.status == primitive.value
        elif field == "Gate":
            assert got.milestone is not None and got.milestone.gate == primitive.value
    else:
        assert got.exit_code == EXIT_UNREADABLE, f"row {row}"
        assert any(primitive.error in e for e in got.errors), f"row {row}: {got.errors}"


def test_gate_block_choice_is_grammar_split_milestones() -> None:
    """Rows 15-18: the gate never segments text itself."""
    for name in ("styles", "one-active", "two-active", "no-active"):
        p = Path(f"tests/hooks/fixtures/gate-scans/{name}-tasks.md")
        blocks = split_milestones(p.read_text())
        for b in blocks:
            got = answer(p, number=b.number)
            if got.milestone is not None:
                assert got.milestone.title == b.title
                assert (
                    got.milestone.heading
                    == b.text.split("\n", 1)[0].lstrip("#").strip()
                )


@pytest.mark.parametrize("value", sorted(plan_parsers.CANONICAL_AUDIT_PROFILES))
def test_audit_profile_agrees_with_plan_parsers_on_canonical_input(
    tmp_path: Path, value: str
) -> None:
    body = f"## Milestone 1: T\n- Status: ACTIVE\n- Audit-Profile: {value}\n"
    p = tmp_path / "t-tasks.md"
    p.write_text(body)
    v, ok, _ = plan_parsers.parse_audit_profile(body)
    assert ok and answer(p).milestone.audit_profile == v


def test_audit_profile_bold_value_is_the_one_deliberate_divergence(
    tmp_path: Path,
) -> None:
    """plan_parsers rejects `**infra**` (it enforces canonical *writing*); the
    gate reads *intent* and strips the bold. Documented in reference.md
    'Why normalise rather than reject'; asserted so the divergence stays known."""
    body = "## Milestone 1: T\n- Status: ACTIVE\n- Audit-Profile: **infra**\n"
    p = tmp_path / "t-tasks.md"
    p.write_text(body)
    assert plan_parsers.parse_audit_profile(body)[1] is False
    assert answer(p).milestone.audit_profile == "infra"


def test_parity_is_not_vacuous() -> None:
    assert len(FIELD_ROWS) == 14
    assert sum(1 for _, f, _ in FIELD_ROWS if f == "Status") == 11
