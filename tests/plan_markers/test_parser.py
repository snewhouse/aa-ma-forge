"""Tests for aa_ma.plan_markers.parser — marker grammar contract.

Reference: docs/spec/plan-marker-grammar.md
Status: failing (Task 1.2). Implementation pending in Task 1.3.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

# This import will fail until Task 1.3 implements the parser.
# That's intentional — the failing-import is what makes Task 1.2 red.
from aa_ma.plan_markers.parser import Marker, parse_log  # noqa: E402


# ---------------------------------------------------------------------------
# Well-formed markers
# ---------------------------------------------------------------------------


class TestWellFormedSingleLine:
    def test_phase_0_init(self):
        line = "[2026-05-11T12:30:15+01:00] PHASE_0 INIT — slug=harden-aa-ma-plan-20260511123015"
        markers = parse_log(line)
        assert len(markers) == 1
        m = markers[0]
        assert m.phase_id == "0"
        assert m.status == "INIT"
        assert m.payload == {"slug": "harden-aa-ma-plan-20260511123015"}
        assert m.timestamp == datetime(
            2026, 5, 11, 12, 30, 15, tzinfo=timezone(timedelta(hours=1))
        )

    def test_phase_done_with_payload(self):
        line = "[2026-05-11T12:31:00+01:00] PHASE_1 DONE — context_gathering=complete"
        markers = parse_log(line)
        assert len(markers) == 1
        assert markers[0].phase_id == "1"
        assert markers[0].status == "DONE"
        assert markers[0].payload == {"context_gathering": "complete"}

    def test_phase_skipped_with_reason(self):
        line = "[2026-05-11T12:43:15+01:00] PHASE_4.2 SKIPPED — reason=user_passed"
        markers = parse_log(line)
        assert len(markers) == 1
        assert markers[0].phase_id == "4.2"
        assert markers[0].status == "SKIPPED"
        assert markers[0].payload == {"reason": "user_passed"}

    def test_sub_phase_id_with_dot(self):
        line = "[2026-05-11T12:32:10+01:00] PHASE_1.3 DONE — grill_mode=with-docs branches_resolved=7 questions_asked=12"
        markers = parse_log(line)
        assert len(markers) == 1
        assert markers[0].phase_id == "1.3"
        assert markers[0].payload == {
            "grill_mode": "with-docs",
            "branches_resolved": "7",
            "questions_asked": "12",
        }

    def test_phase_4_with_percent_in_value(self):
        line = "[2026-05-11T12:42:00+01:00] PHASE_4 DONE — complexity_score=42% plan_elements=12/12"
        markers = parse_log(line)
        assert markers[0].payload == {
            "complexity_score": "42%",
            "plan_elements": "12/12",
        }

    def test_phase_5_with_path_value(self):
        line = "[2026-05-11T12:50:30+01:00] PHASE_5 DONE — artifacts=5 task_dir=.claude/dev/active/harden-aa-ma-plan"
        markers = parse_log(line)
        assert markers[0].payload["artifacts"] == "5"
        assert markers[0].payload["task_dir"] == ".claude/dev/active/harden-aa-ma-plan"


# ---------------------------------------------------------------------------
# Multi-line log
# ---------------------------------------------------------------------------


class TestMultiLineLog:
    def test_full_run_log(self):
        log = """
[2026-05-11T12:30:15+01:00] PHASE_0 INIT — slug=t-20260511123015
[2026-05-11T12:31:00+01:00] PHASE_1 DONE — context_gathering=complete
[2026-05-11T12:32:10+01:00] PHASE_1.3 DONE — grill_mode=with-docs branches_resolved=7
[2026-05-11T12:33:05+01:00] PHASE_1.5 SKIPPED — reason=flag_--skip-lessons
[2026-05-11T12:50:30+01:00] PHASE_5 DONE — artifacts=5 task_dir=/tmp/x
""".strip()
        markers = parse_log(log)
        assert len(markers) == 5
        phase_ids = [m.phase_id for m in markers]
        assert phase_ids == ["0", "1", "1.3", "1.5", "5"]
        # Order-preserving.
        assert markers[3].status == "SKIPPED"
        assert markers[3].payload == {"reason": "flag_--skip-lessons"}

    def test_empty_lines_are_skipped(self):
        log = """
[2026-05-11T12:30:15+01:00] PHASE_0 INIT — slug=x


[2026-05-11T12:31:00+01:00] PHASE_1 DONE — context_gathering=complete
"""
        markers = parse_log(log)
        assert len(markers) == 2

    def test_empty_log_returns_empty_list(self):
        assert parse_log("") == []
        assert parse_log("\n\n  \n") == []


# ---------------------------------------------------------------------------
# Malformed markers — must be tolerant per spec rule 5
# ---------------------------------------------------------------------------


class TestMalformedMarkers:
    def test_skipped_without_reason_emits_warning_and_keeps_marker(self, caplog):
        """Per spec: SKIPPED MUST include reason=... — but the parser is
        tolerant (rule 5: malformed lines warn, not error). The marker is
        parsed but flagged via warning, so downstream code can detect."""
        line = "[2026-05-11T12:43:15+01:00] PHASE_4.2 SKIPPED — note=oops"
        markers = parse_log(line)
        # Tolerant parse — still produces a marker
        assert len(markers) == 1
        assert markers[0].status == "SKIPPED"
        # ...but a warning must surface
        assert any("reason" in r.message.lower() for r in caplog.records), (
            "expected a warning about missing reason=... on SKIPPED marker"
        )

    def test_malformed_timestamp_is_ignored(self, caplog):
        line = "[not-a-timestamp] PHASE_1 DONE — context_gathering=complete"
        markers = parse_log(line)
        assert markers == []
        assert any("timestamp" in r.message.lower() for r in caplog.records)

    def test_unknown_status_is_ignored(self, caplog):
        line = "[2026-05-11T12:30:15+01:00] PHASE_1 MAYBE — context_gathering=partial"
        markers = parse_log(line)
        assert markers == []
        assert any("status" in r.message.lower() for r in caplog.records)

    def test_unknown_phase_id_is_kept_with_warning(self, caplog):
        """Forward-compatibility (spec rule 6): unknown phase IDs warn, not error."""
        line = "[2026-05-11T12:30:15+01:00] PHASE_99.7 DONE — exotic=true"
        markers = parse_log(line)
        assert len(markers) == 1
        assert markers[0].phase_id == "99.7"
        assert any("unknown phase" in r.message.lower() for r in caplog.records)

    def test_garbage_line_is_ignored(self, caplog):
        line = "This is not a marker at all."
        markers = parse_log(line)
        assert markers == []

    def test_missing_separator_is_ignored(self, caplog):
        # Real em-dash (U+2014) required, not regular hyphen
        line = "[2026-05-11T12:30:15+01:00] PHASE_1 DONE - context_gathering=complete"
        markers = parse_log(line)
        assert markers == []


# ---------------------------------------------------------------------------
# Marker dataclass contract
# ---------------------------------------------------------------------------


class TestMarkerDataclass:
    def test_marker_is_immutable(self):
        line = "[2026-05-11T12:30:15+01:00] PHASE_1 DONE — k=v"
        m = parse_log(line)[0]
        with pytest.raises((AttributeError, Exception)):  # frozen dataclass or similar
            m.phase_id = "tampered"  # type: ignore[misc]

    def test_marker_has_required_fields(self):
        line = "[2026-05-11T12:30:15+01:00] PHASE_1 DONE — k=v"
        m = parse_log(line)[0]
        assert hasattr(m, "timestamp")
        assert hasattr(m, "phase_id")
        assert hasattr(m, "status")
        assert hasattr(m, "payload")

    def test_marker_payload_is_dict_of_strings(self):
        line = "[2026-05-11T12:30:15+01:00] PHASE_4 DONE — complexity_score=42% plan_elements=12/12"
        m = parse_log(line)[0]
        assert isinstance(m.payload, dict)
        assert all(isinstance(k, str) and isinstance(v, str) for k, v in m.payload.items())
