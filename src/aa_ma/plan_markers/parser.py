"""Marker parser for /aa-ma-plan phase markers.

Implements the grammar defined in docs/spec/plan-marker-grammar.md.

Grammar:
    [<ISO8601-timestamp>] PHASE_<id> <STATUS> — <key>=<value> [<key>=<value> ...]

- <STATUS> ∈ {INIT, DONE, SKIPPED}
- INIT valid only on PHASE_0
- SKIPPED MUST include reason=<token>
- Separator is em-dash (U+2014) surrounded by single spaces
- Malformed lines warn (via logging) and are skipped
- Unknown phase IDs warn but are kept (forward-compat)
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

logger = logging.getLogger(__name__)

Status = Literal["INIT", "DONE", "SKIPPED"]

# Known phase IDs per spec §9 Required Markers. Unknown IDs warn (forward-compat).
KNOWN_PHASE_IDS: frozenset[str] = frozenset(
    {"0", "1", "1.3", "1.5", "2", "3", "4", "4.2", "4.5", "5"}
)
VALID_STATUSES: frozenset[str] = frozenset({"INIT", "DONE", "SKIPPED"})

# Em-dash separator (U+2014) with single spaces. Regular hyphens are rejected.
_EM_DASH = "—"

# Anchored marker pattern. Captures: timestamp, phase_id, status, payload-str.
# Phase ID accepts dotted form (e.g. 1.3, 4.5).
_MARKER_RE = re.compile(
    r"^\[(?P<ts>[^\]]+)\]\s+"
    r"PHASE_(?P<phase>[0-9]+(?:\.[0-9]+)?)\s+"
    r"(?P<status>[A-Z]+)\s+"
    rf"{_EM_DASH}\s+"
    r"(?P<payload>.+)$"
)

# Each key=value token. Values are shell-safe non-space tokens.
_KV_RE = re.compile(r"([a-z][a-z0-9_]*)=(\S+)")


@dataclass(frozen=True)
class Marker:
    """A single phase marker line from a /aa-ma-plan runtime log.

    Immutable by design — frozen dataclass. Mutation attempts raise
    FrozenInstanceError.
    """

    timestamp: datetime
    phase_id: str
    status: Status
    payload: dict[str, str] = field(default_factory=dict)


def _parse_payload(payload_str: str) -> dict[str, str]:
    """Parse `k1=v1 k2=v2 ...` token stream into a dict."""
    return dict(_KV_RE.findall(payload_str))


def _parse_line(line: str) -> Marker | None:
    """Parse a single line. Return None on malformed / unknown.

    Emits warnings via the module logger for tolerant cases (per spec rule 6).
    """
    stripped = line.strip()
    if not stripped:
        return None

    m = _MARKER_RE.match(stripped)
    if not m:
        logger.warning(
            "marker line did not match grammar (likely missing em-dash separator or malformed structure): %r",
            stripped,
        )
        return None

    ts_str = m.group("ts")
    phase_id = m.group("phase")
    status_str = m.group("status")
    payload_str = m.group("payload")

    # Validate timestamp.
    try:
        ts = datetime.fromisoformat(ts_str)
    except ValueError:
        logger.warning(
            "invalid timestamp %r — dropping marker line: %r", ts_str, stripped
        )
        return None

    # Validate status.
    if status_str not in VALID_STATUSES:
        logger.warning(
            "unknown status %r — must be one of %s — dropping marker line: %r",
            status_str,
            sorted(VALID_STATUSES),
            stripped,
        )
        return None

    # Parse payload.
    payload = _parse_payload(payload_str)

    # Warn (but keep) on unknown phase IDs — forward-compat per spec rule 7.
    if phase_id not in KNOWN_PHASE_IDS:
        logger.warning(
            "unknown phase ID %r — keeping marker for forward-compat: %r",
            phase_id,
            stripped,
        )

    # Warn on INIT misuse (only valid on PHASE_0) per spec rule 3.
    if status_str == "INIT" and phase_id != "0":
        logger.warning(
            "INIT status is only valid on PHASE_0; got PHASE_%s: %r", phase_id, stripped
        )

    # Warn on SKIPPED missing reason= per spec rule 1.
    if status_str == "SKIPPED" and "reason" not in payload:
        logger.warning(
            "SKIPPED marker missing required reason=<token> payload: %r", stripped
        )

    return Marker(
        timestamp=ts,
        phase_id=phase_id,
        status=status_str,  # type: ignore[arg-type]  # checked above
        payload=payload,
    )


def parse_log(text: str) -> list[Marker]:
    """Parse a runtime log into a list of markers.

    Tolerant: malformed lines are warned-and-skipped per the grammar spec
    (rules 6 & 7 — `docs/spec/plan-marker-grammar.md`). The parser never
    raises on parse errors; bad input simply yields fewer markers and
    surfaces warnings via the module logger.

    Args:
        text: the full text of a runtime log (multi-line).

    Returns:
        list of `Marker` in source order.
    """
    markers: list[Marker] = []
    for line in text.splitlines():
        marker = _parse_line(line)
        if marker is not None:
            markers.append(marker)
    return markers
