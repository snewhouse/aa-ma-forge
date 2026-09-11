"""Strict, fail-closed field reads for AA-MA gate enforcement.

`tui/parser.py` reads the same fields tolerantly and *defaults* on anything it
cannot read — `Gate: TYPO` becomes SOFT, `Mode: TYPO` becomes AFK, an
annotated `Status: COMPLETE (…)` becomes PENDING. Correct for a dashboard,
catastrophic for a gate: every default is a decision the gate then enforces.
This module is the other half of that contract: a read either yields a
canonical value or says, quoting the line, that it could not.

Contract: `.claude/dev/active/milestone-grammar-ssot/…-reference.md`
"M5 enforcement contract" — module layout, signatures, per-field absence
semantics, the 18-row form table. `plan_parsers.py` established the
`(value, is_valid, error)` shape; this module keeps it and adds `present`,
because absence means different things per field (a milestone with no
`Status:` is unreadable; one with no `Gate:` is SOFT) and only the caller
knows which.

Normalisation happens in exactly one place, for every enforced field: leading
whitespace-delimited token, bold markers stripped, case-folded to upper, then
canonical membership when a set is given. Reading *intent* is this module's
job; enforcing that plans are *written* canonically is the M2 linter's
(`grammar.find_non_canonical`). Conflating the two is what made `- Gate: hard`
a HARD gate in bash and a SOFT gate in Python.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from aa_ma.grammar import sanitize

MILESTONE_STATUSES: frozenset[str] = frozenset(
    {"PENDING", "ACTIVE", "IN_PROGRESS", "COMPLETE", "BLOCKED"}
)
"""Mirrors `tui.model.MilestoneStatus`; pinned by `tests/test_enforce.py`."""

STEP_STATUSES: frozenset[str] = frozenset(
    {"PENDING", "IN_PROGRESS", "COMPLETE", "BLOCKED", "SKIPPED", "DEFERRED"}
)
"""No `ACTIVE` — steps are IN_PROGRESS. `SKIPPED` is what the HITL gate in
`/execute-aa-ma-milestone` §5.2 writes and `DEFERRED` is in the corpus (3
lines); refusing the command's own output would be a false BLOCK."""

GATES: frozenset[str] = frozenset({"SOFT", "HARD"})
MODES: frozenset[str] = frozenset({"HITL", "AFK"})
PROTOTYPE_REQUIRED: frozenset[str] = frozenset({"YES", "NO"})


@dataclass(frozen=True)
class FieldRead:
    """One field read. `is_valid=False` means the caller MUST refuse."""

    value: str | None  # normalised; None only when absent
    present: bool  # field found at all
    is_valid: bool  # False => refuse; never a default
    error: str | None  # quotes the offending text


def _candidate_re(field: str) -> re.Pattern[str]:
    # Anything that *looks like* the field at line start is a candidate, including
    # bullets and whitespace we will go on to refuse — a refused line must be
    # found first, or it reads as "absent", which is the fail-open shape.
    # `[^\S\n]` is Unicode whitespace incl. NBSP; the bullet class is deliberately
    # wider than the one canonical bullet.
    return re.compile(
        rf"^(?P<lead>[^\S\n]*(?:[-*+•][^\S\n]*)?)"
        rf"\*{{0,2}}{re.escape(field)}\*{{0,2}}:\*{{0,2}}(?P<raw>[^\n]*)$",
        re.MULTILINE,
    )


_CANONICAL_LEAD_RE = re.compile(r"^[ \t]*(?:-[ \t]+)?$")


def read_enforced_field(
    block: str, field: str, canonical: frozenset[str] | None
) -> FieldRead:
    """Read `field` from `block` strictly. First occurrence wins.

    Fenced code and HTML comments are not markup and are not read. A line is a
    candidate only when the field name (bold or plain) is the first thing on
    it after an optional bullet — prose *mentioning* `Status:` mid-line is not.
    """
    match = _candidate_re(field).search(sanitize(block))
    if match is None:
        return FieldRead(None, False, True, None)
    line = match.group(0).strip()
    if not _CANONICAL_LEAD_RE.match(match.group("lead")):
        return FieldRead(
            None,
            True,
            False,
            f"{field}: non-canonical bullet or whitespace in {line!r}",
        )
    tokens = match.group("raw").split()
    if not tokens:
        return FieldRead(None, True, False, f"{field}: empty value in {line!r}")
    value = tokens[0].strip("*").upper()
    if not value:
        return FieldRead(None, True, False, f"{field}: empty value in {line!r}")
    if canonical is None:
        return FieldRead(value, True, True, None)
    by_upper = {c.upper(): c for c in canonical}
    if value in by_upper:
        return FieldRead(by_upper[value], True, True, None)
    return FieldRead(
        value,
        True,
        False,
        f"{field}: non-canonical value {tokens[0]!r} in {line!r}. "
        f"Canonical: {' | '.join(sorted(canonical))}",
    )


def read_milestone_status(own_block: str) -> FieldRead:
    """`Status:` of a milestone. Pass the milestone's *own* text (before its
    first `###`) so a sub-step's status cannot stand in for the milestone's."""
    return read_enforced_field(own_block, "Status", MILESTONE_STATUSES)


def read_step_status(step_block: str) -> FieldRead:
    """`Status:` of a step. Separate from the milestone read: `StepStatus` has no
    `ACTIVE`, so one parser cannot serve both."""
    return read_enforced_field(step_block, "Status", STEP_STATUSES)
