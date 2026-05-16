"""Unit tests for aa_ma.goal_synthesis.

Backs the synthesis-algorithm spec in
`claude-code/skills/goal-condition-synthesis/SKILL.md`. Drives B1 (test
coverage) and I8 (hashing contract) from PR #1 review.
"""

from __future__ import annotations

import hashlib

import pytest

from aa_ma.goal_synthesis import (
    BANNED_VAGUE_TERMS,
    CONDITION_HASH_LEN,
    CONDITION_LENGTH_LIMIT,
    MIN_OBSERVABLE_ARTIFACTS,
    OBSERVABLE_ARTIFACT_PATTERNS,
    TURN_CAP_CEILING,
    TURN_CAP_FLOOR,
    ValidationError,
    ValidationOk,
    condition_hash,
    count_observable_artifacts,
    turn_cap,
    validate_condition,
)

# ---------------------------------------------------------------------------
# turn_cap — formula incl. floor/ceiling
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("pending", "expected"),
    [
        (0, TURN_CAP_FLOOR),    # 0 → floor (caller separately handles nothing_to_do)
        (1, 4),                 # ceil(1.5)=2 → floor
        (2, 4),                 # ceil(3)=3 → floor
        (3, 5),                 # ceil(4.5)=5
        (4, 6),                 # ceil(6)=6
        (5, 8),                 # ceil(7.5)=8
        (20, TURN_CAP_CEILING), # ceil(30)=30
        (25, TURN_CAP_CEILING), # min(37.5, 30)=30
        (100, TURN_CAP_CEILING),
    ],
)
def test_turn_cap_formula(pending: int, expected: int) -> None:
    assert turn_cap(pending) == expected


def test_turn_cap_floor_applies_to_single_milestone() -> None:
    """Single-milestone plans must clear finalisation overhead (~4 turns)."""
    assert turn_cap(1) >= TURN_CAP_FLOOR


def test_turn_cap_ceiling_applies_to_huge_plans() -> None:
    assert turn_cap(10_000) == TURN_CAP_CEILING


def test_turn_cap_rejects_negative_pending() -> None:
    with pytest.raises(ValueError):
        turn_cap(-1)


# ---------------------------------------------------------------------------
# count_observable_artifacts — canonical-table coverage
# ---------------------------------------------------------------------------


def test_count_observable_artifacts_full_template_matches_four() -> None:
    """The canonical full-execute template references ≥ 4 distinct artefacts."""
    condition = (
        "All remaining milestones in add-jwt-auth/tasks.md have Status: COMPLETE; "
        "add-jwt-auth-provenance.log contains a 'MILESTONE COMPLETE' line for each; "
        "git tag add-jwt-auth-complete exists; "
        "`make ci` exits 0; "
        "or stop after 5 turns."
    )
    matched = count_observable_artifacts(condition)
    assert {"tasks_md_status", "provenance_log", "git_tag", "test_exit_code"} <= matched


def test_count_observable_artifacts_verify_iterate_template() -> None:
    """The canonical verify-iterate template references verification.md."""
    condition = (
        "<task>-verification.md latest '## Verdict' block shows GREEN with "
        "0 Criticals AND every Critical from the previous Verdict block has a "
        "'Resolution:' line in this block; or stop after 3 iterations."
    )
    matched = count_observable_artifacts(condition)
    assert "verification_md" in matched


def test_count_observable_artifacts_returns_empty_for_vague() -> None:
    assert count_observable_artifacts("the feature is done and working") == frozenset()


@pytest.mark.parametrize(
    ("snippet", "artifact_id"),
    [
        ("see provenance.log entry", "provenance_log"),
        ("tasks.md Status: PENDING", "tasks_md_status"),
        ("git tag mything-complete exists", "git_tag"),
        ("make ci exits 0", "test_exit_code"),
        ("pytest passes", "test_exit_code"),
        ("trailing [AA-MA Plan] signature", "commit_footer"),
        ("foo-verification.md latest Verdict block", "verification_md"),
    ],
)
def test_count_observable_artifacts_per_row(snippet: str, artifact_id: str) -> None:
    assert artifact_id in count_observable_artifacts(snippet)


# ---------------------------------------------------------------------------
# condition_hash — deterministic, 12 hex chars, normalisation-stable
# ---------------------------------------------------------------------------


def test_condition_hash_length_and_charset() -> None:
    h = condition_hash("foo")
    assert len(h) == CONDITION_HASH_LEN
    assert all(c in "0123456789abcdef" for c in h)


def test_condition_hash_matches_shell_equivalent() -> None:
    """The hash must equal the documented shell equivalent: sha256 of LF-normalised bytes, first 12 hex."""
    condition = "line one\nline two\n"  # trailing newline gets stripped
    expected = hashlib.sha256(b"line one\nline two").hexdigest()[:CONDITION_HASH_LEN]
    assert condition_hash(condition) == expected


def test_condition_hash_normalises_crlf() -> None:
    assert condition_hash("a\r\nb") == condition_hash("a\nb")


def test_condition_hash_normalises_cr_only() -> None:
    assert condition_hash("a\rb") == condition_hash("a\nb")


def test_condition_hash_strips_trailing_whitespace_per_line() -> None:
    assert condition_hash("foo   \nbar\t") == condition_hash("foo\nbar")


def test_condition_hash_strips_trailing_blank_lines() -> None:
    assert condition_hash("foo\nbar\n\n\n") == condition_hash("foo\nbar")


def test_condition_hash_is_deterministic_across_calls() -> None:
    """Two sessions hashing the same byte sequence must produce identical digests."""
    sample = "All milestones in foo/tasks.md have Status: COMPLETE; or stop after 5 turns."
    assert condition_hash(sample) == condition_hash(sample)


def test_condition_hash_differs_on_byte_change() -> None:
    assert condition_hash("foo") != condition_hash("foo!")


# ---------------------------------------------------------------------------
# validate_condition — happy + every failure mode
# ---------------------------------------------------------------------------


_GOOD_CONDITION = (
    "All remaining milestones in foo/tasks.md have Status: COMPLETE; "
    "foo-provenance.log contains a 'MILESTONE COMPLETE' line for each; "
    "git tag foo-complete exists; "
    "`make ci` exits 0; "
    "or stop after 5 turns."
)


def test_validate_condition_happy_path() -> None:
    result = validate_condition(_GOOD_CONDITION, turn_cap_value=5)
    assert isinstance(result, ValidationOk)
    assert len(result.artifacts) >= MIN_OBSERVABLE_ARTIFACTS


@pytest.mark.parametrize("bad_cap", [0, -1, 31, 9999, TURN_CAP_CEILING + 1])
def test_validate_condition_rejects_turn_cap_out_of_range(bad_cap: int) -> None:
    result = validate_condition(_GOOD_CONDITION, turn_cap_value=bad_cap)
    assert isinstance(result, ValidationError)
    assert result.reason == "turn_cap_out_of_range"


def test_validate_condition_rejects_non_int_turn_cap() -> None:
    result = validate_condition(_GOOD_CONDITION, turn_cap_value=True)  # bool ⊂ int but rejected
    assert isinstance(result, ValidationError)
    assert result.reason == "turn_cap_out_of_range"


def test_validate_condition_rejects_oversize() -> None:
    huge = _GOOD_CONDITION + ("\n# padding " + "x" * 4_000)
    result = validate_condition(huge, turn_cap_value=5)
    assert isinstance(result, ValidationError)
    assert result.reason == "condition_too_long"


@pytest.mark.parametrize("vague_term", sorted(BANNED_VAGUE_TERMS))
def test_validate_condition_rejects_each_vague_term(vague_term: str) -> None:
    """Each canonical banned term must be rejected as a whole word."""
    # Embed the term in an otherwise-valid condition so only the vagueness fails.
    condition = (
        f"feature is {vague_term}; tasks.md says complete; provenance.log written; git tag set; "
        "make ci exits 0; or stop after 5 turns."
    )
    result = validate_condition(condition, turn_cap_value=5)
    assert isinstance(result, ValidationError)
    assert result.reason == "condition_too_vague"
    assert vague_term in result.detail


def test_validate_condition_does_not_match_vague_term_as_substring() -> None:
    """`done` should NOT match inside `doneness` (whole-word required)."""
    # We expect the condition to still be rejected (insufficient artefacts)
    # but NOT for vagueness — the whole-word boundary must prevent that.
    condition = "the system reaches doneness (no artefacts referenced)."
    result = validate_condition(condition, turn_cap_value=5)
    assert isinstance(result, ValidationError)
    assert result.reason == "observable_artifacts_insufficient"


def test_validate_condition_rejects_too_few_artifacts() -> None:
    condition = "git tag foo exists; or stop after 5 turns."  # only 1 artefact
    result = validate_condition(condition, turn_cap_value=5)
    assert isinstance(result, ValidationError)
    assert result.reason == "observable_artifacts_insufficient"


def test_validate_condition_accepts_minimum_two_artifacts() -> None:
    condition = (
        "tasks.md Status: COMPLETE; provenance.log shows MILESTONE COMPLETE; or stop after 5 turns."
    )
    result = validate_condition(condition, turn_cap_value=5)
    assert isinstance(result, ValidationOk)
    assert len(result.artifacts) >= MIN_OBSERVABLE_ARTIFACTS


# ---------------------------------------------------------------------------
# Canonical constants sanity — guard against silent drift
# ---------------------------------------------------------------------------


def test_canonical_constants_are_stable() -> None:
    """If this test fails, the SKILL.md spec MUST be updated in the same commit."""
    assert BANNED_VAGUE_TERMS == frozenset({"done", "working", "correct", "good", "ready"})
    assert TURN_CAP_FLOOR == 4
    assert TURN_CAP_CEILING == 30
    assert CONDITION_LENGTH_LIMIT == 4_000
    assert MIN_OBSERVABLE_ARTIFACTS == 2
    assert CONDITION_HASH_LEN == 12
    assert set(OBSERVABLE_ARTIFACT_PATTERNS.keys()) == {
        "provenance_log",
        "tasks_md_status",
        "git_tag",
        "test_exit_code",
        "commit_footer",
        "verification_md",
    }
