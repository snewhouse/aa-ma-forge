"""Reference implementation of the goal-condition-synthesis algorithm.

Canonical algorithmic spec for `Skill(goal-condition-synthesis)`. Unit-tested in
`tests/test_goal_synthesis.py`. The SKILL.md document is the operator-facing
protocol; this module is the executable contract that protects the algorithm
from drift.

Public surface:

- ``BANNED_VAGUE_TERMS``
- ``OBSERVABLE_ARTIFACT_PATTERNS``
- ``TURN_CAP_FLOOR``, ``TURN_CAP_CEILING``, ``CONDITION_LENGTH_LIMIT``
- ``turn_cap(pending_milestones)``
- ``count_observable_artifacts(condition)``
- ``condition_hash(condition)``
- ``validate_condition(condition, turn_cap_value)``
- ``ValidationOk``, ``ValidationError``
"""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Constants — canonical values referenced from goal-condition-synthesis/SKILL.md
# ---------------------------------------------------------------------------

#: Banned vague terms (case-insensitive whole-word match).
BANNED_VAGUE_TERMS: frozenset[str] = frozenset(
    {"done", "working", "correct", "good", "ready"}
)

#: Regex patterns identifying each row of the canonical observable-artifact
#: table from goal-condition-synthesis/SKILL.md. A condition references an
#: artifact iff at least one regex from its row matches.
OBSERVABLE_ARTIFACT_PATTERNS: dict[str, tuple[re.Pattern[str], ...]] = {
    "provenance_log": (re.compile(r"provenance\.log", re.IGNORECASE),),
    "tasks_md_status": (
        re.compile(r"tasks\.md", re.IGNORECASE),
        re.compile(r"\bStatus:\s*(COMPLETE|PENDING|ACTIVE)\b"),
    ),
    "git_tag": (re.compile(r"\bgit\s+tag\b", re.IGNORECASE),),
    "test_exit_code": (
        re.compile(r"\bmake\s+ci\b", re.IGNORECASE),
        re.compile(r"\bpytest\b", re.IGNORECASE),
        re.compile(r"\bexit(?:s|ed)?\s+0\b", re.IGNORECASE),
    ),
    "commit_footer": (
        re.compile(r"\[AA-MA Plan\]"),
        re.compile(r"\bcommit\s+footer", re.IGNORECASE),
    ),
    "verification_md": (re.compile(r"verification\.md", re.IGNORECASE),),
}

TURN_CAP_FLOOR: int = 4
TURN_CAP_CEILING: int = 30
CONDITION_LENGTH_LIMIT: int = 4_000
MIN_OBSERVABLE_ARTIFACTS: int = 2
CONDITION_HASH_LEN: int = 12


# ---------------------------------------------------------------------------
# Validation result types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ValidationOk:
    """Condition validates. ``artifacts`` is the set of artefact ids matched."""

    artifacts: frozenset[str]


@dataclass(frozen=True)
class ValidationError:
    """Condition does not validate. ``reason`` is one of the canonical tokens."""

    reason: str  # one of: condition_too_long | condition_too_vague |
    # observable_artifacts_insufficient | turn_cap_out_of_range
    detail: str = ""


ValidationResult = ValidationOk | ValidationError


# ---------------------------------------------------------------------------
# Turn-cap formula
# ---------------------------------------------------------------------------


def turn_cap(pending_milestones: int) -> int:
    """Return the canonical turn cap for the full-execute mode.

    Formula: ``max(TURN_CAP_FLOOR, ceil(min(pending * 1.5, TURN_CAP_CEILING)))``.

    Floor of 4 prevents single-milestone plans from being capped below the
    finalisation overhead (milestone commit + verify-plan + finalize). Ceiling
    of 30 is the cost ceiling for AFK runs.
    """
    if pending_milestones < 0:
        raise ValueError(f"pending_milestones must be non-negative, got {pending_milestones}")
    raw = min(pending_milestones * 1.5, TURN_CAP_CEILING)
    return max(TURN_CAP_FLOOR, math.ceil(raw))


# ---------------------------------------------------------------------------
# Observable-artifact counting
# ---------------------------------------------------------------------------


def count_observable_artifacts(condition: str) -> frozenset[str]:
    """Return the set of canonical artifact ids referenced by ``condition``.

    An artifact is "referenced" iff at least one of its regex patterns matches.
    """
    matched: set[str] = set()
    for artifact_id, patterns in OBSERVABLE_ARTIFACT_PATTERNS.items():
        for pattern in patterns:
            if pattern.search(condition):
                matched.add(artifact_id)
                break
    return frozenset(matched)


# ---------------------------------------------------------------------------
# Condition hashing — deterministic, byte-stable across sessions
# ---------------------------------------------------------------------------


def _normalise_for_hash(condition: str) -> bytes:
    """Return LF-normalised, right-stripped, UTF-8 encoded bytes."""
    # Normalise CR/CRLF → LF, strip trailing whitespace per line, drop trailing newlines.
    normalised = condition.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in normalised.split("\n")]
    # Strip trailing empty lines.
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines).encode("utf-8")


def condition_hash(condition: str) -> str:
    """Return the canonical 12-hex-character SHA-256 prefix of ``condition``.

    Equivalent shell:
        printf '%s' "$CONDITION_LF_NORMALISED" | sha256sum | cut -c1-12
    """
    digest = hashlib.sha256(_normalise_for_hash(condition)).hexdigest()
    return digest[:CONDITION_HASH_LEN]


# ---------------------------------------------------------------------------
# Vague-term detection
# ---------------------------------------------------------------------------


# Whole-word, case-insensitive match.
_BANNED_TERM_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(t) for t in sorted(BANNED_VAGUE_TERMS)) + r")\b",
    re.IGNORECASE,
)


def _has_vague_term(condition: str) -> str | None:
    """Return the first banned term matched (lowercased) or None."""
    match = _BANNED_TERM_PATTERN.search(condition)
    return match.group(1).lower() if match else None


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_condition(condition: str, turn_cap_value: int) -> ValidationResult:
    """Validate a synthesised condition against all 4 checks.

    Returns ``ValidationOk`` with the matched artifact set, or ``ValidationError``
    whose ``reason`` is one of the canonical tokens.
    """
    if not isinstance(turn_cap_value, int) or isinstance(turn_cap_value, bool):
        return ValidationError("turn_cap_out_of_range", f"expected int, got {type(turn_cap_value).__name__}")
    if turn_cap_value < 1 or turn_cap_value > TURN_CAP_CEILING:
        return ValidationError(
            "turn_cap_out_of_range",
            f"turn_cap={turn_cap_value} outside [1, {TURN_CAP_CEILING}]",
        )

    if len(condition) > CONDITION_LENGTH_LIMIT:
        return ValidationError(
            "condition_too_long",
            f"length={len(condition)} > {CONDITION_LENGTH_LIMIT}",
        )

    vague = _has_vague_term(condition)
    if vague is not None:
        return ValidationError("condition_too_vague", f"banned term: {vague!r}")

    artifacts = count_observable_artifacts(condition)
    if len(artifacts) < MIN_OBSERVABLE_ARTIFACTS:
        return ValidationError(
            "observable_artifacts_insufficient",
            f"matched {len(artifacts)} of canonical {len(OBSERVABLE_ARTIFACT_PATTERNS)}, "
            f"need ≥ {MIN_OBSERVABLE_ARTIFACTS}",
        )

    return ValidationOk(artifacts=artifacts)
