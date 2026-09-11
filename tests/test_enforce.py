"""Contract tests for `aa_ma.enforce` — strict, fail-closed field reads.

Every row here is taken from the reference.md "M5 enforcement contract" form
table (rows 1-14 are field-level; rows 15-18 are block-structure rows and
live in `tests/test_grammar.py` / `tests/test_gate.py`). Verdicts are the
contract's, not invented at test-writing time.
"""

from __future__ import annotations

import pytest

from aa_ma.enforce import (
    MILESTONE_STATUSES,
    STEP_STATUSES,
    FieldRead,
    read_enforced_field,
    read_milestone_status,
    read_step_status,
)
from aa_ma.tui.model import MilestoneStatus, StepStatus

NBSP = " "

# (row, input line, expected FieldRead) for `Status` read as a milestone field.
STATUS_ROWS = [
    (1, "- Status: ACTIVE", "ACTIVE"),
    (2, "  - Status: ACTIVE", "ACTIVE"),
    (3, "\t- Status: ACTIVE", "ACTIVE"),
    (4, "- **Status:** ACTIVE", "ACTIVE"),
    (5, "- **Status**: ACTIVE", "ACTIVE"),
    (6, "- Status: **ACTIVE**", "ACTIVE"),
    (7, "- Status: ACTIVE (resumed after compaction)", "ACTIVE"),
    (8, "- Status: COMPLETE (2026-05-09, commit abc1234)", "COMPLETE"),
    (14, "- Status: ACTIVE\r", "ACTIVE"),
]


@pytest.mark.parametrize(("row", "line", "expected"), STATUS_ROWS)
def test_status_rows_read_their_decided_verdict(
    row: int, line: str, expected: str
) -> None:
    got = read_milestone_status(f"## Milestone 1: T\n{line}\n")
    assert got == FieldRead(value=expected, present=True, is_valid=True, error=None), (
        f"row {row}"
    )


@pytest.mark.parametrize(
    ("row", "line"),
    [
        (9, "* Status: ACTIVE"),
        (10, f"-{NBSP}Status: ACTIVE"),
        (10, f"{NBSP}- Status: ACTIVE"),
    ],
)
def test_non_canonical_bullets_are_refused_not_absent(row: int, line: str) -> None:
    """Rows 9-10: refuse. A silent 'absent' here is the fail-open shape."""
    got = read_milestone_status(f"## Milestone 1: T\n{line}\n")
    assert got.present is True
    assert got.is_valid is False
    assert got.error is not None and "Status" in got.error
    # The offending text is quoted via repr, so an invisible NBSP shows as \xa0.
    assert repr(line.strip()) in got.error, f"row {row}"


def test_gate_case_folds_and_rejects_typo() -> None:
    hard = read_enforced_field("- Gate: hard\n", "Gate", frozenset({"SOFT", "HARD"}))
    assert hard == FieldRead("HARD", True, True, None)  # row 11
    typo = read_enforced_field("- Gate: TYPO\n", "Gate", frozenset({"SOFT", "HARD"}))
    assert typo.present and not typo.is_valid and "TYPO" in (typo.error or "")  # row 12


def test_mode_typo_is_refused_never_afk() -> None:
    """Row 13: `Mode: TYPO` must never resolve to AFK (auto-dispatch without asking)."""
    got = read_enforced_field("- Mode: TYPO\n", "Mode", frozenset({"HITL", "AFK"}))
    assert got.value != "AFK"
    assert not got.is_valid


def test_absent_field_is_present_false_and_valid() -> None:
    """Absence semantics are the caller's decision, per field — the read only reports it."""
    assert read_enforced_field("- Gate: SOFT\n", "Mode", None) == FieldRead(
        None, False, True, None
    )


def test_empty_value_is_refused() -> None:
    got = read_enforced_field("- Status:\n", "Status", None)
    assert got.present and not got.is_valid


def test_canonical_membership_is_case_insensitive_and_returns_canonical_spelling() -> (
    None
):
    cp = frozenset({"data-xform", "hook-modification"})
    assert (
        read_enforced_field(
            "- **Critical-Path:** Data-Xform\n", "Critical-Path", cp
        ).value
        == "data-xform"
    )
    bad = read_enforced_field("- **Critical-Path:** novel-value\n", "Critical-Path", cp)
    assert not bad.is_valid and "novel-value" in (bad.error or "")


def test_no_canonical_set_means_upper_cased_leading_token() -> None:
    assert read_enforced_field("- Foo: bar baz\n", "Foo", None).value == "BAR"


def test_first_occurrence_wins_and_prose_mentions_are_not_candidates() -> None:
    block = "## Milestone 1: T\nThe Status: PENDING mention here is prose.\n- Status: ACTIVE\n- Status: COMPLETE\n"
    assert read_milestone_status(block).value == "ACTIVE"


def test_html_comments_and_fences_are_not_read() -> None:
    block = (
        "<!-- - Status: COMPLETE -->\n```\n- Status: BLOCKED\n```\n- Status: ACTIVE\n"
    )
    assert read_milestone_status(block).value == "ACTIVE"


def test_step_status_has_no_active_but_accepts_shipped_vocabulary() -> None:
    """Milestone and step Status are separate reads because the enums differ.

    SKIPPED is what /execute-aa-ma-milestone §5.2 writes at a HITL skip and
    DEFERRED appears 3 times in the corpus; refusing the command's own output
    would be a self-inflicted false BLOCK, so both are canonical for steps.
    """
    assert read_step_status("- Status: ACTIVE\n").is_valid is False
    assert read_milestone_status("- Status: ACTIVE\n").is_valid is True
    assert (
        read_step_status("- Status: SKIPPED — User skipped at HITL gate\n").value
        == "SKIPPED"
    )
    assert read_step_status("- Status: DEFERRED — see M5\n").value == "DEFERRED"


def test_canonical_sets_do_not_drift_from_the_tui_enums() -> None:
    assert {m.value for m in MilestoneStatus} == MILESTONE_STATUSES
    assert {s.value for s in StepStatus} <= STEP_STATUSES


def test_every_invalid_read_quotes_the_offending_text() -> None:
    for line in ("- Gate: TYPO", "* Status: ACTIVE", "- Status:"):
        got = read_enforced_field(
            line + "\n",
            line.split()[1].rstrip(":"),
            frozenset({"HARD", "SOFT", "ACTIVE"}),
        )
        assert not got.is_valid
        assert got.error and line.strip() in got.error, line


def test_field_read_is_frozen() -> None:
    fr = FieldRead("X", True, True, None)
    with pytest.raises(Exception):
        fr.value = "Y"  # type: ignore[misc]
