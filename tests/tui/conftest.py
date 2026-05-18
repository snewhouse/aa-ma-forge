"""Shared pytest fixtures for tests/tui/.

Created in aa-ma-tui-tracker M1 (2026-05-17), extended in M2.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest


@pytest.fixture
def fixtures_dir() -> Path:
    """Absolute path to the tests/tui/fixtures/tasks/ directory.

    Use via:
        def test_x(fixtures_dir: Path) -> None:
            playwright = fixtures_dir / "playwright-skill"
            ...
    """
    return Path(__file__).parent / "fixtures" / "tasks"


@pytest.fixture
def snapshots_dir() -> Path:
    """Absolute path to tests/tui/snapshots/ (golden text + JSON files)."""
    return Path(__file__).parent / "snapshots"


@pytest.fixture
def static_tasks() -> list:
    """Three deterministic Task objects for golden-file rendering tests.

    Built programmatically (not parsed) to keep golden output stable
    across filesystem mtimes and run timing.

    Layout:
        alpha-task   — COMPLETE (all 2 milestones done; 4 steps total)
        beta-task    — IN_PROGRESS (M1 done, M2 mid-flight; 5 steps total)
        gamma-task   — BLOCKED (M1 done, M2 blocked; 3 steps total)
    """
    from aa_ma.tui.model import (
        Gate,
        Milestone,
        MilestoneStatus,
        Mode,
        Step,
        StepStatus,
        Task,
    )

    fixed_dt = datetime(2026, 5, 1, 12, 0, 0, tzinfo=timezone.utc)

    alpha = Task(
        name="alpha-task",
        root=Path("/tmp/fixtures/alpha-task"),
        last_modified=fixed_dt,
        provenance_tail=[
            "[2026-05-01T11:00] alpha M1 COMPLETE",
            "[2026-05-01T11:55] alpha M2 COMPLETE",
            "[2026-05-01T12:00] alpha SHIPPED",
        ],
        milestones=[
            Milestone(
                number=1,
                title="Setup",
                status=MilestoneStatus.COMPLETE,
                gate=Gate.SOFT,
                mode=Mode.AFK,
                complexity=20,
                steps=[
                    Step(
                        number="1.1",
                        title="install deps",
                        status=StepStatus.COMPLETE,
                        result_log="installed",
                    ),
                    Step(
                        number="1.2",
                        title="scaffold",
                        status=StepStatus.COMPLETE,
                        result_log="ok",
                    ),
                ],
            ),
            Milestone(
                number=2,
                title="Ship",
                status=MilestoneStatus.COMPLETE,
                gate=Gate.HARD,
                mode=Mode.AFK,
                complexity=45,
                steps=[
                    Step(
                        number="2.1",
                        title="run tests",
                        status=StepStatus.COMPLETE,
                        result_log="all green",
                    ),
                    Step(
                        number="2.2",
                        title="release",
                        status=StepStatus.COMPLETE,
                        result_log="v1.0 shipped",
                    ),
                ],
            ),
        ],
    )

    beta = Task(
        name="beta-task",
        root=Path("/tmp/fixtures/beta-task"),
        last_modified=fixed_dt,
        provenance_tail=["[2026-05-01T11:30] beta M1 COMPLETE"],
        milestones=[
            Milestone(
                number=1,
                title="Foundations",
                status=MilestoneStatus.COMPLETE,
                gate=Gate.SOFT,
                mode=Mode.AFK,
                complexity=30,
                steps=[
                    Step(
                        number="1.1",
                        title="design",
                        status=StepStatus.COMPLETE,
                        result_log="approved",
                    ),
                    Step(
                        number="1.2",
                        title="prototype",
                        status=StepStatus.COMPLETE,
                        result_log="working",
                    ),
                ],
            ),
            Milestone(
                number=2,
                title="Implementation",
                status=MilestoneStatus.IN_PROGRESS,
                gate=Gate.HARD,
                mode=Mode.AFK,
                complexity=70,
                steps=[
                    Step(
                        number="2.1",
                        title="code",
                        status=StepStatus.COMPLETE,
                        result_log="merged",
                    ),
                    Step(
                        number="2.2",
                        title="test",
                        status=StepStatus.IN_PROGRESS,
                        result_log="writing",
                    ),
                    Step(number="2.3", title="docs", status=StepStatus.PENDING),
                ],
            ),
        ],
    )

    gamma = Task(
        name="gamma-task",
        root=Path("/tmp/fixtures/gamma-task"),
        last_modified=fixed_dt,
        provenance_tail=["[2026-05-01T10:00] gamma BLOCKED on upstream API"],
        milestones=[
            Milestone(
                number=1,
                title="Research",
                status=MilestoneStatus.COMPLETE,
                gate=Gate.SOFT,
                mode=Mode.AFK,
                complexity=15,
                steps=[
                    Step(
                        number="1.1",
                        title="literature review",
                        status=StepStatus.COMPLETE,
                        result_log="20 papers found",
                    ),
                ],
            ),
            Milestone(
                number=2,
                title="Validate",
                status=MilestoneStatus.BLOCKED,
                gate=Gate.HARD,
                mode=Mode.HITL,
                complexity=80,
                steps=[
                    Step(
                        number="2.1",
                        title="prototype",
                        status=StepStatus.COMPLETE,
                        result_log="working",
                    ),
                    Step(
                        number="2.2",
                        title="upstream-validation",
                        status=StepStatus.BLOCKED,
                        result_log="vendor API down since 2026-04-30",
                    ),
                ],
            ),
        ],
    )

    return [alpha, beta, gamma]
