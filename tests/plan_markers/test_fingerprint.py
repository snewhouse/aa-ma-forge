"""Tests for aa_ma.plan_markers.fingerprint — transcript-derived correlation.

Reference: docs/spec/plan-marker-grammar.md §Fingerprint Correlation
Status: failing (Task 1.4). Implementation pending in Task 1.5.

The fingerprint matcher reads tool_use entries from the Claude Code
transcript JSONL and verifies that each phase marker's DONE claim is
backed by actual tool calls. SKIPPED markers (with reason) override
the fingerprint check for that phase.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

# These imports will fail until Task 1.5 implements the fingerprint matcher.
from aa_ma.plan_markers.fingerprint import ToolCall, correlate, load_tool_calls
from aa_ma.plan_markers.parser import Marker


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _marker(phase: str, status: str = "DONE", **payload: str) -> Marker:
    return Marker(
        timestamp=datetime(2026, 5, 11, 12, 0, 0, tzinfo=timezone.utc),
        phase_id=phase,
        status=status,  # type: ignore[arg-type]
        payload=payload,
    )


def _tc(name: str, **input_kwargs: object) -> ToolCall:
    return ToolCall(name=name, input=dict(input_kwargs))


# ---------------------------------------------------------------------------
# load_tool_calls from JSONL transcript
# ---------------------------------------------------------------------------


class TestLoadToolCalls:
    def test_loads_tool_use_entries(self, tmp_path):
        transcript = tmp_path / "transcript.jsonl"
        transcript.write_text(
            '{"type": "tool_use", "name": "Bash", "input": {"command": "ls"}}\n'
            '{"type": "text", "text": "hello"}\n'
            '{"type": "tool_use", "name": "Skill", "input": {"skill": "brainstorming"}}\n'
        )
        calls = load_tool_calls(transcript)
        assert len(calls) == 2
        assert calls[0].name == "Bash"
        assert calls[0].input == {"command": "ls"}
        assert calls[1].name == "Skill"
        assert calls[1].input == {"skill": "brainstorming"}

    def test_handles_nested_message_content(self, tmp_path):
        """Real Claude Code transcripts wrap tool_use inside message.content."""
        transcript = tmp_path / "transcript.jsonl"
        transcript.write_text(
            '{"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "Read", "input": {"file_path": "x"}}]}}\n'
        )
        calls = load_tool_calls(transcript)
        assert len(calls) == 1
        assert calls[0].name == "Read"

    def test_missing_transcript_returns_empty_list(self, tmp_path):
        """Hook should degrade gracefully if transcript_path doesn't exist."""
        calls = load_tool_calls(tmp_path / "nonexistent.jsonl")
        assert calls == []

    def test_malformed_jsonl_lines_skipped(self, tmp_path):
        transcript = tmp_path / "transcript.jsonl"
        transcript.write_text(
            '{"type": "tool_use", "name": "Bash", "input": {}}\n'
            "this is not json\n"
            '{"type": "tool_use", "name": "Read", "input": {}}\n'
        )
        calls = load_tool_calls(transcript)
        assert [c.name for c in calls] == ["Bash", "Read"]


# ---------------------------------------------------------------------------
# correlate — per-phase fingerprint checks
# ---------------------------------------------------------------------------


class TestPhase1Fingerprint:
    def test_satisfied_by_agent_explore(self):
        markers = [_marker("1")]
        calls = [_tc("Agent", subagent_type="Explore", prompt="explore X")]
        results = correlate(markers, calls)
        r = next(r for r in results if r.phase_id == "1")
        assert r.evidence_found == "present"

    def test_satisfied_by_general_purpose_agent(self):
        markers = [_marker("1")]
        calls = [_tc("Agent", subagent_type="general-purpose", prompt="x")]
        results = correlate(markers, calls)
        assert next(r for r in results if r.phase_id == "1").evidence_found == "present"

    def test_satisfied_by_src_read(self):
        markers = [_marker("1")]
        calls = [_tc("Read", file_path="src/aa_ma/__init__.py")]
        assert (
            next(
                r for r in correlate(markers, calls) if r.phase_id == "1"
            ).evidence_found
            == "present"
        )

    def test_missing_when_no_evidence(self):
        markers = [_marker("1")]
        calls = [_tc("Bash", command="ls")]
        assert (
            next(
                r for r in correlate(markers, calls) if r.phase_id == "1"
            ).evidence_found
            == "absent"
        )


class TestPhase1_3Fingerprint:
    def test_satisfied_by_three_askuserquestion(self):
        markers = [_marker("1.3")]
        calls = [_tc("AskUserQuestion") for _ in range(3)]
        assert (
            next(
                r for r in correlate(markers, calls) if r.phase_id == "1.3"
            ).evidence_found
            == "present"
        )

    def test_two_askuserquestion_insufficient(self):
        markers = [_marker("1.3")]
        calls = [_tc("AskUserQuestion"), _tc("AskUserQuestion")]
        assert (
            next(
                r for r in correlate(markers, calls) if r.phase_id == "1.3"
            ).evidence_found
            == "absent"
        )

    def test_satisfied_by_grill_me_skill(self):
        markers = [_marker("1.3")]
        calls = [_tc("Skill", skill="grill-me")]
        assert (
            next(
                r for r in correlate(markers, calls) if r.phase_id == "1.3"
            ).evidence_found
            == "present"
        )

    def test_satisfied_by_grill_with_docs(self):
        markers = [_marker("1.3")]
        calls = [_tc("Skill", skill="grill-with-docs")]
        assert (
            next(
                r for r in correlate(markers, calls) if r.phase_id == "1.3"
            ).evidence_found
            == "present"
        )


class TestPhase1_5Fingerprint:
    def test_satisfied_by_lessons_read(self):
        markers = [_marker("1.5")]
        calls = [_tc("Read", file_path="docs/lessons.md")]
        assert (
            next(
                r for r in correlate(markers, calls) if r.phase_id == "1.5"
            ).evidence_found
            == "present"
        )

    def test_satisfied_by_git_log_grep(self):
        markers = [_marker("1.5")]
        calls = [_tc("Bash", command='git log --grep="fix" --oneline')]
        assert (
            next(
                r for r in correlate(markers, calls) if r.phase_id == "1.5"
            ).evidence_found
            == "present"
        )


class TestPhase2Fingerprint:
    def test_satisfied_by_brainstorming_skill(self):
        markers = [_marker("2")]
        calls = [_tc("Skill", skill="superpowers:brainstorming")]
        assert (
            next(
                r for r in correlate(markers, calls) if r.phase_id == "2"
            ).evidence_found
            == "present"
        )


class TestPhase3Fingerprint:
    @pytest.mark.parametrize(
        "tc",
        [
            _tc("WebFetch", url="https://example.com"),
            _tc("WebSearch", query="x"),
            _tc("mcp__plugin_context7_context7__resolve-library-id", library="x"),
            _tc("Agent", subagent_type="Explore", prompt="x"),
        ],
    )
    def test_satisfied_by_any_research_tool(self, tc):
        markers = [_marker("3")]
        assert (
            next(
                r for r in correlate(markers, [tc]) if r.phase_id == "3"
            ).evidence_found
            == "present"
        )


class TestPhase4Fingerprint:
    def test_satisfied_by_complexity_router(self):
        markers = [_marker("4")]
        calls = [_tc("Skill", skill="complexity-router")]
        assert (
            next(
                r for r in correlate(markers, calls) if r.phase_id == "4"
            ).evidence_found
            == "present"
        )


class TestPhase4_2Fingerprint:
    @pytest.mark.parametrize(
        "skill",
        ["plan-ceo-review", "plan-eng-review", "plan-design-review"],
    )
    def test_satisfied_by_any_review_skill(self, skill):
        markers = [_marker("4.2")]
        calls = [_tc("Skill", skill=skill)]
        assert (
            next(
                r for r in correlate(markers, calls) if r.phase_id == "4.2"
            ).evidence_found
            == "present"
        )


class TestPhase4_5Fingerprint:
    def test_satisfied_by_plan_verification(self):
        markers = [_marker("4.5")]
        calls = [_tc("Skill", skill="plan-verification")]
        assert (
            next(
                r for r in correlate(markers, calls) if r.phase_id == "4.5"
            ).evidence_found
            == "present"
        )

    def test_satisfied_by_verification_agent(self):
        markers = [_marker("4.5")]
        calls = [
            _tc(
                "Agent",
                subagent_type="general-purpose",
                prompt="run 6 angles of adversarial verification on the plan",
            )
        ]
        assert (
            next(
                r for r in correlate(markers, calls) if r.phase_id == "4.5"
            ).evidence_found
            == "present"
        )


class TestPhase5Fingerprint:
    def test_requires_both_scribe_and_validator(self):
        markers = [_marker("5")]
        calls = [
            _tc("Agent", subagent_type="aa-ma-scribe", prompt="x"),
            _tc("Agent", subagent_type="aa-ma-validator", prompt="x"),
        ]
        assert (
            next(
                r for r in correlate(markers, calls) if r.phase_id == "5"
            ).evidence_found
            == "present"
        )

    def test_scribe_alone_insufficient(self):
        markers = [_marker("5")]
        calls = [_tc("Agent", subagent_type="aa-ma-scribe", prompt="x")]
        assert (
            next(
                r for r in correlate(markers, calls) if r.phase_id == "5"
            ).evidence_found
            == "absent"
        )


# ---------------------------------------------------------------------------
# SKIPPED override + MISSING markers
# ---------------------------------------------------------------------------


class TestSkippedOverride:
    def test_skipped_with_reason_bypasses_fingerprint(self):
        markers = [_marker("4.5", status="SKIPPED", reason="user_choice")]
        calls: list[ToolCall] = []  # no plan-verification evidence
        r = next(r for r in correlate(markers, calls) if r.phase_id == "4.5")
        assert r.evidence_found == "skipped_with_reason"
        assert r.marker_status == "SKIPPED"
        assert r.warning is None

    def test_skipped_without_reason_is_not_an_override(self):
        """SKIPPED without reason already warned at parser level. Here it
        should still be flagged as a problem in correlation output."""
        markers = [_marker("4.5", status="SKIPPED")]  # no reason
        calls: list[ToolCall] = []
        r = next(r for r in correlate(markers, calls) if r.phase_id == "4.5")
        assert r.warning is not None


class TestMissingMarkers:
    def test_phase_with_no_marker_and_no_evidence(self):
        markers: list[Marker] = []
        calls: list[ToolCall] = []
        results = correlate(markers, calls)
        # Each of the 9 required phases should appear in results
        phases = {r.phase_id for r in results}
        assert {"1", "1.3", "1.5", "2", "3", "4", "4.2", "4.5", "5"}.issubset(phases)
        for r in results:
            if r.phase_id in {"1", "1.3", "1.5", "2", "3", "4", "4.2", "4.5", "5"}:
                assert r.marker_status == "MISSING"

    def test_phase_with_marker_but_no_evidence(self):
        markers = [_marker("1.3")]
        calls: list[ToolCall] = []  # no askuserquestion, no grill skill
        r = next(r for r in correlate(markers, calls) if r.phase_id == "1.3")
        assert r.marker_status == "DONE"
        assert r.evidence_found == "absent"
        assert r.warning is not None


# ---------------------------------------------------------------------------
# CorrelationResult dataclass contract
# ---------------------------------------------------------------------------


class TestCorrelationResult:
    def test_has_required_fields(self):
        markers = [_marker("1")]
        calls = [_tc("Read", file_path="src/aa_ma/__init__.py")]
        r = correlate(markers, calls)[0]
        for attr in ("phase_id", "marker_status", "evidence_found", "warning"):
            assert hasattr(r, attr)
