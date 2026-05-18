"""Tests for aa_ma.tui.snapshot — Rich rendering modes.

Created in aa-ma-tui-tracker M2 (T2.1-T2.3, 2026-05-18).

Golden-file convention:
    - First run with missing golden file: writes the golden + fails with
      a clear "regenerate" message. Re-run passes.
    - Subsequent runs: byte-exact equality check.
    - Renderers MUST pin Console(width=120, record=True) for determinism.
"""

from __future__ import annotations

from pathlib import Path

import pytest


def _check_or_bootstrap_golden(actual: str, golden_path: Path) -> None:
    """Compare actual to golden file; bootstrap if missing.

    Raises pytest.fail on bootstrap so the test fails first run, passes
    second run — preserves TDD discipline without bouncing renderer code.
    """
    if not golden_path.exists():
        golden_path.parent.mkdir(parents=True, exist_ok=True)
        golden_path.write_text(actual, encoding="utf-8")
        pytest.fail(
            f"BOOTSTRAPPED golden file at {golden_path}; re-run test to verify."
        )
    expected = golden_path.read_text(encoding="utf-8")
    assert actual == expected, (
        f"Golden mismatch at {golden_path}. To regenerate, delete the file "
        f"and re-run. Actual ({len(actual)} chars) != expected ({len(expected)} chars)."
    )


# =============================================================================
# T2.1: render_board (4-column Rich kanban)
# =============================================================================


def test_render_board_matches_golden(static_tasks: list, snapshots_dir: Path) -> None:
    """render_board(tasks) emits stable 4-column kanban (PENDING/IN_PROGRESS/BLOCKED/COMPLETE)."""
    from aa_ma.tui.snapshot import render_board

    output = render_board(static_tasks)
    _check_or_bootstrap_golden(output, snapshots_dir / "board.txt")


def test_render_board_groups_by_aggregate_status(
    static_tasks: list,
) -> None:
    """Each task name appears under its aggregate-status column."""
    from aa_ma.tui.snapshot import render_board

    output = render_board(static_tasks)
    # alpha=COMPLETE, beta=IN_PROGRESS, gamma=BLOCKED → all three names present
    assert "alpha-task" in output
    assert "beta-task" in output
    assert "gamma-task" in output
    # No PENDING column tasks in fixture, but column header still rendered
    assert "PENDING" in output
    assert "IN_PROGRESS" in output
    assert "BLOCKED" in output
    assert "COMPLETE" in output


def test_render_board_empty_list_renders_4_columns() -> None:
    """Empty task list still renders all 4 column headers (no tasks listed)."""
    from aa_ma.tui.snapshot import render_board

    output = render_board([])
    assert "PENDING" in output
    assert "IN_PROGRESS" in output
    assert "BLOCKED" in output
    assert "COMPLETE" in output


def test_render_board_reuses_parser_discover_tasks() -> None:
    """Snapshot module imports the SAME discover_tasks as the parser module (L-052)."""
    import aa_ma.tui.parser as parser
    import aa_ma.tui.snapshot as snapshot

    # snapshot.discover_tasks is the same function object as parser.discover_tasks
    assert snapshot.discover_tasks is parser.discover_tasks


# =============================================================================
# T2.2: render_tree (single-task Rich Tree of milestones + steps)
# =============================================================================


def test_render_tree_matches_golden(static_tasks: list, snapshots_dir: Path) -> None:
    """render_tree(task) emits stable milestones-and-steps tree."""
    from aa_ma.tui.snapshot import render_tree

    # Use beta (IN_PROGRESS, 2 milestones, 5 steps — most varied)
    beta = next(t for t in static_tasks if t.name == "beta-task")
    output = render_tree(beta)
    _check_or_bootstrap_golden(output, snapshots_dir / "tree.txt")


def test_render_tree_includes_milestone_titles(static_tasks: list) -> None:
    """Tree includes every milestone title from the task."""
    from aa_ma.tui.snapshot import render_tree

    beta = next(t for t in static_tasks if t.name == "beta-task")
    output = render_tree(beta)
    for m in beta.milestones:
        assert m.title in output


def test_render_tree_includes_step_numbers(static_tasks: list) -> None:
    """Tree includes every step number (e.g. "2.2") from the task."""
    from aa_ma.tui.snapshot import render_tree

    beta = next(t for t in static_tasks if t.name == "beta-task")
    output = render_tree(beta)
    for m in beta.milestones:
        for s in m.steps:
            assert s.number in output


def test_render_tree_truncates_result_log_to_60_chars(static_tasks: list) -> None:
    """Per plan: tree shows first 60 chars of each Result Log."""
    from aa_ma.tui.model import (
        Gate,
        Milestone,
        MilestoneStatus,
        Mode,
        Step,
        StepStatus,
        Task,
    )
    from aa_ma.tui.snapshot import render_tree

    long_text = "x" * 100
    task = Task(
        name="long",
        root=Path("/tmp/long"),
        milestones=[
            Milestone(
                number=1,
                title="m",
                status=MilestoneStatus.IN_PROGRESS,
                gate=Gate.SOFT,
                mode=Mode.AFK,
                steps=[
                    Step(
                        number="1.1",
                        title="s",
                        status=StepStatus.IN_PROGRESS,
                        result_log=long_text,
                    )
                ],
            )
        ],
    )
    output = render_tree(task)
    # First 60 chars present
    assert "x" * 60 in output
    # 100-char form absent (would prove no truncation)
    assert "x" * 100 not in output


# =============================================================================
# T2.3: render_summary (one line per task)
# =============================================================================


def test_render_summary_matches_golden(static_tasks: list, snapshots_dir: Path) -> None:
    """render_summary(tasks) emits one line per task in stable format."""
    from aa_ma.tui.snapshot import render_summary

    output = render_summary(static_tasks)
    _check_or_bootstrap_golden(output, snapshots_dir / "summary.txt")


def test_render_summary_one_line_per_task(static_tasks: list) -> None:
    """Exactly N non-empty lines for N tasks (excluding ANSI codes)."""
    from aa_ma.tui.snapshot import render_summary

    output = render_summary(static_tasks)
    # Strip blank/whitespace-only lines
    lines = [ln for ln in output.splitlines() if ln.strip()]
    assert len(lines) == len(static_tasks), (
        f"Expected {len(static_tasks)} lines, got {len(lines)}: {lines}"
    )


def test_render_summary_contains_task_metadata(static_tasks: list) -> None:
    """Each line has name + status + steps progress + milestone progress."""
    from aa_ma.tui.snapshot import render_summary

    output = render_summary(static_tasks)
    # alpha: 4/4 steps, 2/2 ms, COMPLETE
    assert "alpha-task" in output
    assert "4/4 steps" in output
    assert "2/2 ms" in output
    # beta: 3/5 steps, IN_PROGRESS
    assert "beta-task" in output
    assert "3/5 steps" in output
    # gamma: 2/3 steps, BLOCKED
    assert "gamma-task" in output
    assert "2/3 steps" in output
