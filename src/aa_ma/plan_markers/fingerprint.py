"""Fingerprint matcher — verify phase markers against transcript tool calls.

Reads tool_use entries from a Claude Code JSONL transcript and verifies that
each DONE phase marker is backed by actual tool-call evidence.

Reference: docs/spec/plan-marker-grammar.md §Fingerprint Correlation
"""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from aa_ma.plan_markers.parser import Marker

logger = logging.getLogger(__name__)

# Phases the spec mandates evidence for.
REQUIRED_PHASES: tuple[str, ...] = ("1", "1.3", "1.5", "2", "3", "4", "4.2", "4.5", "5")

MarkerStatus = Literal["INIT", "DONE", "SKIPPED", "MISSING"]
EvidenceState = Literal["present", "absent", "skipped_with_reason", "not_required"]


@dataclass(frozen=True)
class ToolCall:
    """A tool_use entry from the Claude Code transcript."""

    name: str
    input: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CorrelationResult:
    """Outcome of correlating one phase marker against the transcript."""

    phase_id: str
    marker_status: MarkerStatus
    evidence_found: EvidenceState
    warning: str | None = None


# ---------------------------------------------------------------------------
# Transcript loading
# ---------------------------------------------------------------------------


def _yield_tool_uses(obj: Any) -> Iterable[dict[str, Any]]:
    """Recursively yield tool_use dicts from an arbitrary JSON structure.

    Real CC transcripts nest tool_use entries inside message.content arrays.
    Test fixtures may use the simpler top-level form. This handler covers
    both — and is defensive about future format changes.
    """
    if isinstance(obj, dict):
        if obj.get("type") == "tool_use" and "name" in obj:
            yield obj
        for v in obj.values():
            yield from _yield_tool_uses(v)
    elif isinstance(obj, list):
        for item in obj:
            yield from _yield_tool_uses(item)


def load_tool_calls(transcript_path: Path) -> list[ToolCall]:
    """Load tool_use entries from a JSONL transcript at `transcript_path`.

    Returns an empty list if the file doesn't exist. Malformed JSONL lines
    are warned and skipped. Hook callers should degrade gracefully.
    """
    if not transcript_path.exists():
        logger.warning("transcript path does not exist: %s", transcript_path)
        return []

    calls: list[ToolCall] = []
    with transcript_path.open() as fh:
        for lineno, raw in enumerate(fh, start=1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                turn = json.loads(raw)
            except json.JSONDecodeError as e:
                logger.warning("transcript line %d malformed JSON: %s", lineno, e)
                continue
            for tu in _yield_tool_uses(turn):
                calls.append(
                    ToolCall(
                        name=str(tu.get("name", "")),
                        input=dict(tu.get("input", {}))
                        if isinstance(tu.get("input"), dict)
                        else {},
                    )
                )
    return calls


# ---------------------------------------------------------------------------
# Per-phase fingerprint predicates
# ---------------------------------------------------------------------------


def _has(tcs: list[ToolCall], name: str, **input_match: str) -> bool:
    """Any tool call matching `name` AND all `input_match` regex patterns."""
    name_re = re.compile(name) if name.startswith("^") else None
    for tc in tcs:
        if name_re is not None:
            if not name_re.match(tc.name):
                continue
        else:
            if tc.name != name:
                continue
        ok = True
        for k, pattern in input_match.items():
            v = tc.input.get(k, "")
            if not isinstance(v, str):
                ok = False
                break
            if not re.search(pattern, v):
                ok = False
                break
        if ok:
            return True
    return False


def _count(tcs: list[ToolCall], name: str) -> int:
    return sum(1 for tc in tcs if tc.name == name)


def _phase_1(tcs: list[ToolCall]) -> bool:
    return _has(tcs, "Agent", subagent_type=r"^(Explore|general-purpose)$") or _has(
        tcs, "Read", file_path=r"^src/"
    )


def _phase_1_3(tcs: list[ToolCall]) -> bool:
    return _count(tcs, "AskUserQuestion") >= 3 or _has(
        tcs, "Skill", skill=r"grill-(me|with-docs)"
    )


def _phase_1_5(tcs: list[ToolCall]) -> bool:
    return _has(tcs, "Read", file_path=r"lessons\.md$") or _has(
        tcs, "Bash", command=r"git log .*--grep"
    )


def _phase_2(tcs: list[ToolCall]) -> bool:
    return _has(tcs, "Skill", skill=r"brainstorming")


def _phase_3(tcs: list[ToolCall]) -> bool:
    return (
        _has(tcs, "WebFetch")
        or _has(tcs, "WebSearch")
        or _has(tcs, "^mcp__.*context7.*")
        or _has(tcs, "Agent", subagent_type=r"^Explore$")
    )


def _phase_4(tcs: list[ToolCall]) -> bool:
    return _has(tcs, "Skill", skill=r"complexity-router")


def _phase_4_2(tcs: list[ToolCall]) -> bool:
    return _has(tcs, "Skill", skill=r"plan-(ceo|eng|design)-review")


def _phase_4_5(tcs: list[ToolCall]) -> bool:
    return _has(tcs, "Skill", skill=r"plan-verification") or _has(
        tcs, "Agent", prompt=r"verification|adversarial|6 angles"
    )


def _phase_5(tcs: list[ToolCall]) -> bool:
    return _has(tcs, "Agent", subagent_type=r"^aa-ma-scribe$") and _has(
        tcs, "Agent", subagent_type=r"^aa-ma-validator$"
    )


_PREDICATES: dict[str, Callable[[list[ToolCall]], bool]] = {
    "1": _phase_1,
    "1.3": _phase_1_3,
    "1.5": _phase_1_5,
    "2": _phase_2,
    "3": _phase_3,
    "4": _phase_4,
    "4.2": _phase_4_2,
    "4.5": _phase_4_5,
    "5": _phase_5,
}


# ---------------------------------------------------------------------------
# Correlation
# ---------------------------------------------------------------------------


def correlate(
    markers: list[Marker], tool_calls: list[ToolCall]
) -> list[CorrelationResult]:
    """Correlate phase markers against tool-call evidence.

    For each REQUIRED_PHASE:
    - If a SKIPPED marker (with `reason=...`) exists: bypass the fingerprint
      check; the skip is its own evidence.
    - If a SKIPPED marker exists WITHOUT `reason=...`: flag a warning.
    - If a DONE marker exists: check the per-phase predicate against
      tool_calls. Present → ok. Absent → warning.
    - If no marker exists: MISSING + warning.

    Unknown phase IDs (forward-compat) are passed through as MISSING with
    a note; the spec allows but does not require them.
    """
    by_phase: dict[str, Marker] = {m.phase_id: m for m in markers}
    results: list[CorrelationResult] = []

    for phase_id in REQUIRED_PHASES:
        marker = by_phase.get(phase_id)

        if marker is None:
            results.append(
                CorrelationResult(
                    phase_id=phase_id,
                    marker_status="MISSING",
                    evidence_found="absent",
                    warning=f"PHASE_{phase_id} marker missing from runtime log",
                )
            )
            continue

        if marker.status == "SKIPPED":
            if "reason" in marker.payload:
                results.append(
                    CorrelationResult(
                        phase_id=phase_id,
                        marker_status="SKIPPED",
                        evidence_found="skipped_with_reason",
                        warning=None,
                    )
                )
            else:
                results.append(
                    CorrelationResult(
                        phase_id=phase_id,
                        marker_status="SKIPPED",
                        evidence_found="absent",
                        warning=f"PHASE_{phase_id} SKIPPED but missing required reason=<token> payload",
                    )
                )
            continue

        # DONE (or INIT — only PHASE_0 should ever be INIT, but be defensive)
        predicate = _PREDICATES.get(phase_id)
        if predicate is None:
            # Forward-compat: unknown phase ID with a marker. Mark as ok.
            results.append(
                CorrelationResult(
                    phase_id=phase_id,
                    marker_status=marker.status,  # type: ignore[arg-type]
                    evidence_found="not_required",
                    warning=None,
                )
            )
            continue

        if predicate(tool_calls):
            results.append(
                CorrelationResult(
                    phase_id=phase_id,
                    marker_status=marker.status,  # type: ignore[arg-type]
                    evidence_found="present",
                    warning=None,
                )
            )
        else:
            results.append(
                CorrelationResult(
                    phase_id=phase_id,
                    marker_status=marker.status,  # type: ignore[arg-type]
                    evidence_found="absent",
                    warning=(
                        f"PHASE_{phase_id} marker claims DONE but no matching "
                        "tool-call evidence in transcript"
                    ),
                )
            )

    return results
