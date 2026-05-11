"""Parsers for canonical AA-MA milestone fields.

These parsers extract and validate canonical enum fields from milestone
blocks in `[task]-tasks.md` files. They are consumed by:

- `Skill(plan-verification)` Angle 6 structural check
- `/execute-aa-ma-milestone` Phase 6.8 trigger logic

Canonical enums follow the `Critical-Path:` precedent established in
ADR-0001 (engineering-standards-architecture): the value set is fixed,
and adding a new value requires a plan + ADR rather than ad-hoc
extension. Both `Audit-Profile` and `TDD-Waiver` were introduced in
ADR-0005 (post-impl-adversarial-review) for the v0.8.0 release.

Each parser returns a 3-tuple `(value, is_valid, error)`:
    value:    str | None — extracted value (lower-cased, trimmed) or None if absent
    is_valid: bool       — True iff value is None OR a canonical member
    error:    str | None — human-readable error when is_valid is False

Field-absence is treated as valid (None) because most milestones have no
waiver, and grandfathering by `Created:` date is handled outside these
parsers (in the plan-verification Angle 6 structural check).
"""
from __future__ import annotations

import re

# -----------------------------------------------------------------------------
# Canonical enums (mirror Critical-Path enum in engineering-standards.md §1)
# -----------------------------------------------------------------------------

CANONICAL_AUDIT_PROFILES: frozenset[str] = frozenset(
    {"full", "code-only", "docs-only", "infra", "custom"}
)
"""Canonical `Audit-Profile:` values per milestone.

- `full`: All 5 audit agents dispatch (code-reviewer, security-auditor,
  tdd-sequence-auditor, context7-evidence-auditor, future-proofing-auditor)
- `code-only`: All agents except docs-specific lints
- `docs-only`: Only future-proofing-auditor (counts/versions/magic numbers)
- `infra`: code-reviewer + security-auditor + future-proofing-auditor;
  skips TDD-sequence-auditor and context7-evidence-auditor
- `custom`: per-milestone explicit lists via `Audit-Run:` / `Audit-Skip:`
"""

CANONICAL_TDD_WAIVERS: frozenset[str] = frozenset(
    {"refactor", "docs-only", "prototype", "hotfix-emergency", "tooling-config"}
)
"""Canonical `TDD-Waiver:` values per milestone.

When present, the tdd-sequence-auditor returns WAIVED instead of PASS/FAIL.
Reasons:
- `refactor`: Behaviour-preserving change; existing tests cover the surface
- `docs-only`: No `src/` touched (auto-detected too)
- `prototype`: `Prototype-Required: YES` already set; `Skill(prototype)` governs
- `hotfix-emergency`: Production incident; tests added in follow-up
- `tooling-config`: `pyproject.toml` / CI config / Dockerfile only
"""

# -----------------------------------------------------------------------------
# Internal helpers
# -----------------------------------------------------------------------------

_HTML_COMMENT_RE = re.compile(r"<!--[\s\S]*?-->")


def _strip_html_comments(text: str) -> str:
    """Remove HTML-comment blocks so commented-out examples don't trip the parser.

    Matches the behavior of `_aa_ma_strip_html_comments` in `aa-ma-parse.sh` —
    intentionally tolerant of multi-line comments.
    """
    return _HTML_COMMENT_RE.sub("", text)


def _extract_field(text: str, field_name: str) -> str | None:
    """Extract the first occurrence of the field's value as a verbatim token.

    Tolerates:
      - Plain form: `Audit-Profile: full`
      - Bold-pair form: `**Audit-Profile:** full`
      - Split-bold form: `**Audit-Profile**: full` (less common)
      - Leading `- ` list-item bullet
      - Variable whitespace around the colon and value
      - HTML-comment blocks (stripped before scan)

    The returned value is **case-preserving** — canonical-enum validation is
    strict on exact case (matches the `Critical-Path:` precedent). Plan
    authors must use the documented lower-case form; `FULL` or `Full` are
    rejected as non-canonical.

    Returns:
        The first token after the colon (whitespace-delimited), verbatim.
        None if the field is not present.
    """
    cleaned = _strip_html_comments(text)
    # Pattern allows `**` before the field name, after the field name (i.e.
    # before the colon), AND after the colon — covers all three bold styles.
    pattern = re.compile(
        rf"^[ \t]*-?[ \t]*\*{{0,2}}{re.escape(field_name)}\*{{0,2}}:\*{{0,2}}[ \t]+(\S+)",
        re.MULTILINE,
    )
    match = pattern.search(cleaned)
    if match is None:
        return None
    return match.group(1).strip()


def _parse_canonical_field(
    text: str, field_name: str, canonical: frozenset[str]
) -> tuple[str | None, bool, str | None]:
    """Generic canonical-enum field parser used by parse_audit_profile and parse_tdd_waiver.

    Returns:
        (value, is_valid, error) where:
          - value: str | None — extracted token (lower-cased) or None if absent
          - is_valid: True iff value is None OR in `canonical`
          - error: str | None — populated when is_valid is False
    """
    value = _extract_field(text, field_name)
    if value is None:
        return (None, True, None)
    if value in canonical:
        return (value, True, None)
    canonical_list = " | ".join(sorted(canonical))
    error = (
        f"Non-canonical {field_name} value: {value!r}. "
        f"Canonical values: {canonical_list}. "
        f"Adding a new value requires a plan + ADR (per ADR-0005)."
    )
    return (value, False, error)


# -----------------------------------------------------------------------------
# Public API
# -----------------------------------------------------------------------------


def parse_audit_profile(text: str) -> tuple[str | None, bool, str | None]:
    """Parse `Audit-Profile:` from a milestone block.

    Args:
        text: The full text of a milestone block from `[task]-tasks.md`.

    Returns:
        (value, is_valid, error). See module docstring for semantics.

    Example:
        >>> block = "## Milestone 1\\n- Audit-Profile: full\\n"
        >>> parse_audit_profile(block)
        ('full', True, None)
    """
    return _parse_canonical_field(text, "Audit-Profile", CANONICAL_AUDIT_PROFILES)


def parse_tdd_waiver(text: str) -> tuple[str | None, bool, str | None]:
    """Parse `TDD-Waiver:` from a milestone block.

    Args:
        text: The full text of a milestone block from `[task]-tasks.md`.

    Returns:
        (value, is_valid, error). See module docstring for semantics.

    Example:
        >>> block = "## Milestone 4\\n- TDD-Waiver: refactor\\n"
        >>> parse_tdd_waiver(block)
        ('refactor', True, None)
    """
    return _parse_canonical_field(text, "TDD-Waiver", CANONICAL_TDD_WAIVERS)
