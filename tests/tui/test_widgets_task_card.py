"""Tests for src/aa_ma/tui/widgets/task_card.py — M3 Step 3.2.

TaskCard is a Static-subclass widget rendering one Task as a card:
  - bold task name on top line
  - aggregate_status badge
  - X/Y steps · M/N ms progress line
"""

from __future__ import annotations

import pytest

from aa_ma.tui.widgets.task_card import TaskCard


@pytest.fixture
def card_alpha(static_tasks):
    return TaskCard(static_tasks[0])  # alpha COMPLETE, 4 steps / 2 ms


@pytest.fixture
def card_beta(static_tasks):
    return TaskCard(static_tasks[1])  # beta IN_PROGRESS, 3/5 steps, 1/2 ms


@pytest.fixture
def card_gamma(static_tasks):
    return TaskCard(static_tasks[2])  # gamma BLOCKED, 2/3 steps, 1/2 ms


# -----------------------------------------------------------------------------
# Construction
# -----------------------------------------------------------------------------


def test_task_card_stores_task(card_alpha, static_tasks) -> None:
    assert card_alpha.task_data is static_tasks[0]


def test_task_card_is_static_subclass() -> None:
    from textual.widgets import Static

    assert issubclass(TaskCard, Static)


# -----------------------------------------------------------------------------
# Rendered text content (format method — pure)
# -----------------------------------------------------------------------------


def test_task_card_format_includes_name(card_alpha) -> None:
    text = card_alpha.format()
    assert "alpha-task" in text


def test_task_card_format_includes_aggregate_status(card_alpha, card_beta, card_gamma) -> None:
    assert "COMPLETE" in card_alpha.format()
    assert "IN_PROGRESS" in card_beta.format()
    assert "BLOCKED" in card_gamma.format()


def test_task_card_format_shows_step_progress(card_alpha, card_beta, card_gamma) -> None:
    # alpha: 4 steps, all COMPLETE → 4/4
    assert "4/4 steps" in card_alpha.format()
    # beta: 5 steps total, 3 COMPLETE (M1.1, M1.2, M2.1) → 3/5
    assert "3/5 steps" in card_beta.format()
    # gamma: 3 steps total, 2 COMPLETE (M1.1, M2.1) → 2/3
    assert "2/3 steps" in card_gamma.format()


def test_task_card_format_shows_milestone_progress(card_alpha, card_beta, card_gamma) -> None:
    # alpha: 2 ms, both COMPLETE → 2/2 ms
    assert "2/2 ms" in card_alpha.format()
    # beta: 2 ms, 1 COMPLETE → 1/2 ms
    assert "1/2 ms" in card_beta.format()
    # gamma: 2 ms, 1 COMPLETE → 1/2 ms
    assert "1/2 ms" in card_gamma.format()


# -----------------------------------------------------------------------------
# Reuse: counting comes from Task model (DRY — single source of truth)
# -----------------------------------------------------------------------------


def test_task_step_progress_method_exists(static_tasks) -> None:
    """Task model owns step_progress() so widgets and snapshot can share."""
    alpha, beta, gamma = static_tasks
    assert alpha.step_progress() == (4, 4)
    assert beta.step_progress() == (3, 5)
    assert gamma.step_progress() == (2, 3)


def test_task_milestone_progress_method_exists(static_tasks) -> None:
    """Task model owns milestone_progress() — same DRY rationale."""
    alpha, beta, gamma = static_tasks
    assert alpha.milestone_progress() == (2, 2)
    assert beta.milestone_progress() == (1, 2)
    assert gamma.milestone_progress() == (1, 2)


def test_task_progress_methods_handle_empty_milestones() -> None:
    """A Task with no milestones returns (0, 0) for both — not a division error."""
    from pathlib import Path

    from aa_ma.tui.model import Task

    t = Task(name="empty", root=Path("/tmp/empty"))
    assert t.step_progress() == (0, 0)
    assert t.milestone_progress() == (0, 0)


# Mount-via-Pilot test deferred to Step 3.10 (pytest-textual-snapshot smoke).
# Step 3.2 keeps scope narrow: format() and counting-method correctness.
