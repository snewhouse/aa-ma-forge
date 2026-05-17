"""Tests for aa_ma.tui.model — Pydantic v2 models + enums.

Created in aa-ma-tui-tracker M1 T1.1 (2026-05-17).

Per L-065: every enum value has a documented justification in the source
module. These tests assert structural completeness (right values exist)
and basic round-trippability via Pydantic.
"""

from __future__ import annotations

import pytest


def test_milestone_status_enum_set() -> None:
    """MilestoneStatus has exactly {PENDING, ACTIVE, IN_PROGRESS, COMPLETE, BLOCKED}."""
    from aa_ma.tui.model import MilestoneStatus

    values = {m.value for m in MilestoneStatus}
    assert values == {"PENDING", "ACTIVE", "IN_PROGRESS", "COMPLETE", "BLOCKED"}


def test_step_status_enum_set() -> None:
    """StepStatus has exactly {PENDING, IN_PROGRESS, COMPLETE, BLOCKED}.

    Note: per spec, steps do not have an ACTIVE state — only milestones do.
    Real-world `Status: ACTIVE` on a step is coerced to IN_PROGRESS by the
    parser (semantic equivalence; see plan_parsers.py L-052 precedent).
    """
    from aa_ma.tui.model import StepStatus

    values = {s.value for s in StepStatus}
    assert values == {"PENDING", "IN_PROGRESS", "COMPLETE", "BLOCKED"}


def test_mode_enum_set() -> None:
    """Mode = {HITL, AFK}."""
    from aa_ma.tui.model import Mode

    values = {m.value for m in Mode}
    assert values == {"HITL", "AFK"}


def test_gate_enum_set() -> None:
    """Gate = {SOFT, HARD}."""
    from aa_ma.tui.model import Gate

    values = {g.value for g in Gate}
    assert values == {"SOFT", "HARD"}


def test_aggregate_status_enum_set() -> None:
    """AggregateStatus = {PENDING, IN_PROGRESS, BLOCKED, COMPLETE, ERROR} per L-065."""
    from aa_ma.tui.model import AggregateStatus

    values = {a.value for a in AggregateStatus}
    assert values == {"PENDING", "IN_PROGRESS", "BLOCKED", "COMPLETE", "ERROR"}


def test_step_model_construction() -> None:
    """Step has number, title, status, result_log fields."""
    from aa_ma.tui.model import Step, StepStatus

    step = Step(number="1.1", title="First step", status=StepStatus.PENDING)
    assert step.number == "1.1"
    assert step.title == "First step"
    assert step.status == StepStatus.PENDING
    assert step.result_log is None


def test_milestone_model_construction_with_defaults() -> None:
    """Milestone defaults: Gate.SOFT, Mode.AFK, no complexity/deps/criteria, empty steps."""
    from aa_ma.tui.model import Gate, Milestone, MilestoneStatus, Mode

    m = Milestone(number=1, title="Test", status=MilestoneStatus.PENDING)
    assert m.gate == Gate.SOFT
    assert m.mode == Mode.AFK
    assert m.complexity is None
    assert m.dependencies is None
    assert m.acceptance_criteria is None
    assert m.steps == []


def test_task_model_construction() -> None:
    """Task carries name, root, milestones, aggregate_status, last_modified, provenance_tail."""
    from pathlib import Path

    from aa_ma.tui.model import AggregateStatus, Task

    t = Task(
        name="demo",
        root=Path("/tmp/demo"),
        milestones=[],
        aggregate_status=AggregateStatus.PENDING,
    )
    assert t.name == "demo"
    assert t.root == Path("/tmp/demo")
    assert t.milestones == []
    assert t.aggregate_status == AggregateStatus.PENDING
    assert t.last_modified is None
    assert t.provenance_tail == []
    assert t.parse_error is None


def test_parse_error_is_raisable() -> None:
    """ParseError must be importable and raisable as a regular Exception."""
    from aa_ma.tui.model import ParseError

    with pytest.raises(ParseError):
        raise ParseError("test error")
