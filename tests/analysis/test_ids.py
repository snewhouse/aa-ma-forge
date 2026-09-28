"""M1 AC3 + prototype refinements R-1 (redact before hashing) and R-2 (twin occurrence suffix)."""

from __future__ import annotations

import hashlib
import inspect
import re

import pytest

from aa_ma.analysis import ids

BASE = ("security", "security.sql_injection", "src/db.py", 'cur.execute("SELECT * FROM users WHERE id=" + uid)')


def _aws() -> str:
    return "AKIA" + "Q7ZXM3PL" + "K9WRT2VB"


def test_format_and_parity_with_the_prototype() -> None:
    """JS prototype on prototype/cas-analysis-schemas computed F-8eee32c533b2 for this tuple."""
    fid = ids.finding_id("security", "security.secret", "src/db.py", "aws-access-token")
    assert fid == "F-8eee32c533b2"
    assert re.fullmatch(r"F-[0-9a-f]{12}", ids.finding_id(*BASE))


def test_matches_the_documented_formula() -> None:
    expected = "F-" + hashlib.sha256("\x1f".join(BASE).encode()).hexdigest()[:12]
    assert ids.finding_id(*BASE) == expected


def test_line_number_is_not_an_input() -> None:
    """Same anchor at line 10 and line 15 → same ID: the anchor is text, never a position."""
    assert list(inspect.signature(ids.finding_id).parameters) == ["dimension", "rule", "path", "anchor"]
    assert ids.assign_ids([BASE]) == ids.assign_ids([BASE])


@pytest.mark.parametrize("i", range(4))
def test_any_part_changing_changes_the_id(i: int) -> None:
    changed: list[str] = list(BASE)
    changed[i] = changed[i] + "x"
    assert ids.finding_id(*changed) != ids.finding_id(*BASE)


def test_twins_get_distinct_ids_by_order_of_appearance() -> None:
    first, second, third = ids.assign_ids([BASE, BASE, BASE])
    assert len({first, second, third}) == 3
    assert first == ids.finding_id(*BASE)
    assert second == ids.finding_id(*BASE[:3], BASE[3] + "#2")
    assert third == ids.finding_id(*BASE[:3], BASE[3] + "#3")


def test_occurrence_counts_per_tuple_not_globally() -> None:
    other = ("maintainability", "maint.todo", "src/app.py", "# TODO: retries")
    got = ids.assign_ids([BASE, other, BASE, other])
    assert got[1] == ids.finding_id(*other)
    assert got[3] == ids.finding_id(*other[:3], other[3] + "#2")


def test_anchor_for_collapses_whitespace() -> None:
    assert ids.anchor_for("    #   TODO:\thandle   retries   ") == "# TODO: handle retries"


def test_anchor_for_redacts_before_hashing() -> None:
    """R-1: the stored and the hashed anchor are the same redacted text; no secret in either."""
    line = f'    AWS_KEY = "{_aws()}"'
    anchor = ids.anchor_for(line)
    assert _aws() not in anchor
    assert "[REDACTED:" in anchor
    assert ids.anchor_for(line) == anchor  # deterministic → stable ID across runs


def test_compare_vocabulary() -> None:
    prev = ["F-000000000001", "F-000000000002"]
    cur = ["F-000000000002", "F-000000000003"]
    assert ids.compare(prev, cur) == {
        "F-000000000001": "fixed",
        "F-000000000002": "persisting",
        "F-000000000003": "new",
    }


def test_compare_empty_previous_is_all_new() -> None:
    assert ids.compare([], ["F-000000000009"]) == {"F-000000000009": "new"}
