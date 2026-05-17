"""Hypothesis round-trip property test for aa_ma.tui.parser.

Created in aa-ma-tui-tracker M1 T1.7 (2026-05-17).

Property: given a randomly-generated valid tasks.md, the parser must
recover the same milestone statuses and step statuses as encoded in the
strategy. Catches regex regressions across the L-052 grammar tolerance
surface (plain vs bold-pair Status forms, plain vs bullet-prefixed lines).

Marked `@pytest.mark.slow` per pyproject.toml convention — runs only with
`uv run pytest -m slow`.
"""

from __future__ import annotations

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st


# Strategies -----------------------------------------------------------------


MILESTONE_STATUSES = ["PENDING", "ACTIVE", "IN_PROGRESS", "COMPLETE", "BLOCKED"]
STEP_STATUSES_RAW = ["PENDING", "IN_PROGRESS", "COMPLETE", "BLOCKED"]
GATES = ["SOFT", "HARD"]
MODES = ["HITL", "AFK"]


@st.composite
def _milestone_block(draw, number: int) -> tuple[str, dict]:
    """Generate one milestone block (text + expected fields dict).

    Randomly chooses between plain and bold-pair `Status:` form to
    exercise L-052 tolerance.
    """
    title = draw(
        st.text(
            alphabet=st.characters(min_codepoint=65, max_codepoint=90),
            min_size=3,
            max_size=15,
        )
    )
    m_status = draw(st.sampled_from(MILESTONE_STATUSES))
    gate = draw(st.sampled_from(GATES))
    mode = draw(st.sampled_from(MODES))
    complexity = draw(st.integers(min_value=0, max_value=100))
    use_bold = draw(st.booleans())

    if use_bold:
        status_line = f"- **Status:** {m_status}"
        gate_line = f"- **Gate:** {gate}"
        mode_line = f"- **Mode:** {mode}"
    else:
        status_line = f"- Status: {m_status}"
        gate_line = f"- Gate: {gate}"
        mode_line = f"- Mode: {mode}"

    n_steps = draw(st.integers(min_value=0, max_value=3))
    step_specs: list[tuple[str, str, str]] = []  # (number, status, result_log)
    step_lines: list[str] = []
    for s_idx in range(1, n_steps + 1):
        s_number = f"{number}.{s_idx}"
        s_title = draw(
            st.text(
                alphabet=st.characters(min_codepoint=97, max_codepoint=122),
                min_size=3,
                max_size=10,
            )
        )
        s_status = draw(st.sampled_from(STEP_STATUSES_RAW))
        s_result = draw(
            st.text(
                alphabet=st.characters(min_codepoint=33, max_codepoint=126),
                min_size=0,
                max_size=20,
            )
        ).strip()
        step_specs.append((s_number, s_status, s_result))
        s_status_line = (
            f"- **Status:** {s_status}"
            if draw(st.booleans())
            else f"- Status: {s_status}"
        )
        result_line = f"- Result Log: {s_result}" if s_result else "- Result Log:"
        step_lines.append(
            f"### Step {s_number}: {s_title}\n{s_status_line}\n{result_line}\n"
        )

    block = (
        f"## Milestone {number}: {title}\n"
        f"{status_line}\n"
        f"{mode_line}\n"
        f"{gate_line}\n"
        f"- Complexity: {complexity}\n\n" + "\n".join(step_lines)
    )

    expected = {
        "number": number,
        "title": title,
        "status": m_status,
        "gate": gate,
        "mode": mode,
        "complexity": complexity,
        "steps": step_specs,
    }
    return block, expected


@st.composite
def _tasks_md_content(draw) -> tuple[str, list[dict]]:
    """Generate a full tasks.md body (between 1 and 4 milestones)."""
    n = draw(st.integers(min_value=1, max_value=4))
    blocks: list[str] = []
    expectations: list[dict] = []
    for i in range(1, n + 1):
        block, expected = draw(_milestone_block(i))
        blocks.append(block)
        expectations.append(expected)
    return "# Tasks\n\n" + "\n".join(blocks), expectations


# Test -----------------------------------------------------------------------


@pytest.mark.slow
@given(content_and_expected=_tasks_md_content())
@settings(
    deadline=None,
    max_examples=50,
    suppress_health_check=[HealthCheck.function_scoped_fixture],
)
def test_parser_roundtrip_status_fields(
    tmp_path_factory: pytest.TempPathFactory,
    content_and_expected: tuple[str, list[dict]],
) -> None:
    """Round-trip property: parser recovers milestone & step statuses verbatim."""
    from aa_ma.tui.model import MilestoneStatus, StepStatus
    from aa_ma.tui.parser import parse_task_dir

    content, expected = content_and_expected

    base = tmp_path_factory.mktemp("hypo")
    task_dir = base / "hypo-task"
    task_dir.mkdir()
    (task_dir / "hypo-task-tasks.md").write_text(content, encoding="utf-8")

    task = parse_task_dir(task_dir)

    assert len(task.milestones) == len(expected)
    for parsed, exp in zip(task.milestones, expected, strict=True):
        assert parsed.number == exp["number"]
        # Status enum value comparison
        assert parsed.status == MilestoneStatus(exp["status"])
        assert parsed.gate.value == exp["gate"]
        assert parsed.mode.value == exp["mode"]
        assert parsed.complexity == exp["complexity"]
        # Steps
        assert len(parsed.steps) == len(exp["steps"])
        for p_step, (e_num, e_status, _e_result) in zip(
            parsed.steps, exp["steps"], strict=True
        ):
            assert p_step.number == e_num
            assert p_step.status == StepStatus(e_status)
