"""Tests for aa_ma.tui.parser — directory-to-Task parsing.

Created in aa-ma-tui-tracker M1 (T1.2 onwards, 2026-05-17).
"""

from __future__ import annotations

from pathlib import Path


# =============================================================================
# T1.2: parse_task_dir happy path
# =============================================================================


def test_parse_complete_task(fixtures_dir: Path) -> None:
    """Parse a real completed task: playwright-skill.

    Falsifiable assertions (per L-059): exact counts and exact first-step
    Result Log value, drawn from the on-disk fixture.
    """
    from aa_ma.tui.model import MilestoneStatus, StepStatus
    from aa_ma.tui.parser import parse_task_dir

    task = parse_task_dir(fixtures_dir / "playwright-skill")

    assert task.name == "playwright-skill"
    assert len(task.milestones) >= 1, "playwright-skill has at least one milestone"

    m1 = task.milestones[0]
    assert m1.number == 1
    assert m1.title == "Core Skill File (SKILL.md)"
    assert m1.status == MilestoneStatus.COMPLETE
    assert m1.complexity == 45

    # First step assertions
    assert len(m1.steps) >= 3
    s1 = m1.steps[0]
    assert s1.number == "1.1"
    assert s1.title == "Create skill directory structure"
    assert s1.status == StepStatus.COMPLETE
    assert s1.result_log is not None
    assert "playwright-testing" in s1.result_log


# =============================================================================
# T1.3: parser tolerance for **Status:** bold-pair variant (L-052)
# =============================================================================


def test_parse_tolerates_bold_status(fixtures_dir: Path) -> None:
    """`**Status:** COMPLETE` must parse identically to `- Status: COMPLETE`."""
    from aa_ma.tui.model import MilestoneStatus, StepStatus
    from aa_ma.tui.parser import parse_task_dir

    task = parse_task_dir(fixtures_dir / "edge-bold-status")

    assert len(task.milestones) == 1
    m1 = task.milestones[0]
    assert m1.status == MilestoneStatus.COMPLETE

    # Step 1.1 has **Status:** COMPLETE
    s1 = m1.steps[0]
    assert s1.status == StepStatus.COMPLETE
    assert s1.result_log == "bold style worked"

    # Step 1.2 has **Status:** PENDING and an empty Result Log
    s2 = m1.steps[1]
    assert s2.status == StepStatus.PENDING
    assert s2.result_log is None  # blank → None per spec


def test_parse_defaults_when_status_absent(fixtures_dir: Path) -> None:
    """Missing Status field → PENDING (default)."""
    from aa_ma.tui.model import MilestoneStatus, StepStatus
    from aa_ma.tui.parser import parse_task_dir

    task = parse_task_dir(fixtures_dir / "edge-no-status")

    assert len(task.milestones) == 1
    m1 = task.milestones[0]
    assert m1.status == MilestoneStatus.PENDING

    s1 = m1.steps[0]
    assert s1.status == StepStatus.PENDING
    # Step has Result Log: did some work — should parse
    assert s1.result_log == "did some work"


def test_parse_blank_result_log_returns_none(fixtures_dir: Path) -> None:
    """`Result Log:` with blank value OR absent field → None."""
    from aa_ma.tui.parser import parse_task_dir

    task = parse_task_dir(fixtures_dir / "edge-blank-result")
    m1 = task.milestones[0]
    # Step 1.1 has `- Result Log:` (blank)
    assert m1.steps[0].result_log is None
    # Step 1.2 has no Result Log line at all
    assert m1.steps[1].result_log is None


# =============================================================================
# T1.4: discover_tasks merges multiple roots
# =============================================================================


def test_discover_tasks_merges_roots(tmp_path: Path, fixtures_dir: Path) -> None:
    """discover_tasks([rootA, rootB]) merges tasks from both root dirs."""
    import shutil

    from aa_ma.tui.parser import discover_tasks

    root_a = tmp_path / "rootA"
    root_b = tmp_path / "rootB"
    root_a.mkdir()
    root_b.mkdir()
    shutil.copytree(fixtures_dir / "playwright-skill", root_a / "playwright-skill")
    shutil.copytree(fixtures_dir / "edge-bold-status", root_b / "edge-bold-status")

    tasks = discover_tasks([root_a, root_b])

    names = sorted(t.name for t in tasks)
    assert names == ["edge-bold-status", "playwright-skill"]


def test_discover_tasks_empty_roots_returns_empty_list(tmp_path: Path) -> None:
    """discover_tasks on an empty root dir returns []."""
    from aa_ma.tui.parser import discover_tasks

    empty = tmp_path / "empty"
    empty.mkdir()
    assert discover_tasks([empty]) == []


def test_discover_tasks_skips_nonexistent_root(tmp_path: Path) -> None:
    """Non-existent root dirs are silently skipped, not raised."""
    from aa_ma.tui.parser import discover_tasks

    nonexistent = tmp_path / "does-not-exist"
    assert discover_tasks([nonexistent]) == []


# =============================================================================
# T1.5: discover_tasks survives per-task parse errors
# =============================================================================


def test_discover_tasks_survives_malformed(tmp_path: Path, fixtures_dir: Path) -> None:
    """When one task dir fails to parse, others still parse; failing dir
    becomes a Task with aggregate_status=ERROR + parse_error populated."""
    import shutil

    from aa_ma.tui.model import AggregateStatus
    from aa_ma.tui.parser import discover_tasks

    root = tmp_path / "root"
    root.mkdir()
    shutil.copytree(fixtures_dir / "playwright-skill", root / "playwright-skill")
    shutil.copytree(fixtures_dir / "edge-malformed", root / "edge-malformed")

    tasks = discover_tasks([root])
    by_name = {t.name: t for t in tasks}

    # Good task parses normally
    good = by_name["playwright-skill"]
    assert good.parse_error is None
    assert len(good.milestones) >= 1

    # Bad task gets ERROR badge with parse_error
    bad = by_name["edge-malformed"]
    assert bad.aggregate_status == AggregateStatus.ERROR
    assert bad.parse_error is not None
    assert "Milestone" in bad.parse_error  # mentions the missing milestone headers


def test_discover_tasks_survives_missing_tasks_file(tmp_path: Path) -> None:
    """A directory with no `{name}-tasks.md` is treated as ERROR, not skipped."""
    from aa_ma.tui.model import AggregateStatus
    from aa_ma.tui.parser import discover_tasks

    root = tmp_path / "root"
    root.mkdir()
    empty_task = root / "no-tasks-file"
    empty_task.mkdir()

    tasks = discover_tasks([root])
    assert len(tasks) == 1
    assert tasks[0].name == "no-tasks-file"
    assert tasks[0].aggregate_status == AggregateStatus.ERROR
    assert tasks[0].parse_error is not None
    assert "missing tasks file" in tasks[0].parse_error


# =============================================================================
# T1.6: aggregate_status derivation (5 tests, one per state per L-065)
# =============================================================================


def _make_task(milestones, parse_error=None):
    """Helper: build a Task from a list of (status, [step_statuses]) tuples."""
    from aa_ma.tui.model import (
        Milestone,
        Step,
        Task,
    )

    ms = []
    for i, (m_status, step_statuses) in enumerate(milestones, start=1):
        steps = [
            Step(number=f"{i}.{j}", title=f"step {j}", status=s)
            for j, s in enumerate(step_statuses, start=1)
        ]
        ms.append(Milestone(number=i, title=f"m{i}", status=m_status, steps=steps))
    return Task(
        name="t",
        root=Path("/tmp/t"),
        milestones=ms,
        parse_error=parse_error,
    )


def test_aggregate_status_pending_when_no_step_started() -> None:
    """All milestones PENDING + all steps PENDING → aggregate PENDING."""
    from aa_ma.tui.model import AggregateStatus, MilestoneStatus, StepStatus

    t = _make_task(
        [
            (MilestoneStatus.PENDING, [StepStatus.PENDING, StepStatus.PENDING]),
            (MilestoneStatus.PENDING, [StepStatus.PENDING]),
        ]
    )
    assert t.aggregate_status == AggregateStatus.PENDING


def test_aggregate_status_in_progress_when_some_step_started() -> None:
    """One step IN_PROGRESS → aggregate IN_PROGRESS."""
    from aa_ma.tui.model import AggregateStatus, MilestoneStatus, StepStatus

    t = _make_task(
        [
            (MilestoneStatus.ACTIVE, [StepStatus.IN_PROGRESS, StepStatus.PENDING]),
            (MilestoneStatus.PENDING, [StepStatus.PENDING]),
        ]
    )
    assert t.aggregate_status == AggregateStatus.IN_PROGRESS


def test_aggregate_status_blocked_when_any_step_blocked() -> None:
    """Any step BLOCKED → aggregate BLOCKED (overrides IN_PROGRESS / COMPLETE)."""
    from aa_ma.tui.model import AggregateStatus, MilestoneStatus, StepStatus

    t = _make_task(
        [
            (MilestoneStatus.COMPLETE, [StepStatus.COMPLETE, StepStatus.COMPLETE]),
            (MilestoneStatus.IN_PROGRESS, [StepStatus.BLOCKED]),
        ]
    )
    assert t.aggregate_status == AggregateStatus.BLOCKED


def test_aggregate_status_complete_when_all_milestones_complete() -> None:
    """All milestones COMPLETE → aggregate COMPLETE (terminal)."""
    from aa_ma.tui.model import AggregateStatus, MilestoneStatus, StepStatus

    t = _make_task(
        [
            (MilestoneStatus.COMPLETE, [StepStatus.COMPLETE]),
            (MilestoneStatus.COMPLETE, [StepStatus.COMPLETE, StepStatus.COMPLETE]),
        ]
    )
    assert t.aggregate_status == AggregateStatus.COMPLETE


def test_aggregate_status_error_when_parse_error_set() -> None:
    """parse_error populated → aggregate ERROR (terminal); ignores milestone state."""
    from aa_ma.tui.model import AggregateStatus, MilestoneStatus, StepStatus

    t = _make_task(
        [(MilestoneStatus.COMPLETE, [StepStatus.COMPLETE])],
        parse_error="bad data",
    )
    assert t.aggregate_status == AggregateStatus.ERROR


def test_aggregate_status_real_completed_fixture(fixtures_dir: Path) -> None:
    """End-to-end: a real fully-completed fixture → COMPLETE."""
    from aa_ma.tui.model import AggregateStatus
    from aa_ma.tui.parser import parse_task_dir

    t = parse_task_dir(fixtures_dir / "playwright-skill")
    assert t.aggregate_status == AggregateStatus.COMPLETE


# =============================================================================
# T1.8: provenance_tail returns last N lines (default 5)
# =============================================================================


def test_provenance_tail_returns_last_5_nonblank_lines(fixtures_dir: Path) -> None:
    """parse_task_dir populates task.provenance_tail with last 5 non-blank lines."""
    from aa_ma.tui.parser import parse_task_dir

    t = parse_task_dir(fixtures_dir / "playwright-skill")
    assert len(t.provenance_tail) == 5
    # Last line of the real fixture is the PLAN COMPLETE marker
    assert "PLAN COMPLETE" in t.provenance_tail[-1]
    # Lines are stripped (no trailing newline)
    for line in t.provenance_tail:
        assert not line.endswith("\n")
        assert line.strip() != ""


def test_provenance_tail_empty_when_log_missing(tmp_path: Path) -> None:
    """If no `{name}-provenance.log` file, provenance_tail is []."""
    from aa_ma.tui.parser import parse_task_dir

    task_dir = tmp_path / "no-prov"
    task_dir.mkdir()
    (task_dir / "no-prov-tasks.md").write_text(
        "# x\n\n## Milestone 1: only\n- Status: PENDING\n", encoding="utf-8"
    )
    t = parse_task_dir(task_dir)
    assert t.provenance_tail == []


def test_provenance_tail_handles_short_log(tmp_path: Path) -> None:
    """If log has fewer than 5 non-blank lines, return all of them."""
    from aa_ma.tui.parser import parse_task_dir

    task_dir = tmp_path / "short-prov"
    task_dir.mkdir()
    (task_dir / "short-prov-tasks.md").write_text(
        "# x\n\n## Milestone 1: only\n- Status: PENDING\n", encoding="utf-8"
    )
    (task_dir / "short-prov-provenance.log").write_text(
        "line one\n\nline two\n", encoding="utf-8"
    )
    t = parse_task_dir(task_dir)
    assert t.provenance_tail == ["line one", "line two"]


# =============================================================================
# T1.9: last_modified = max(file mtimes)
# =============================================================================


def test_last_modified_is_most_recent_file_mtime(tmp_path: Path) -> None:
    """last_modified = max mtime across the 5 standard AA-MA files."""
    import os
    import time

    from aa_ma.tui.parser import parse_task_dir

    task_dir = tmp_path / "lm"
    task_dir.mkdir()
    files = [
        "lm-tasks.md",
        "lm-plan.md",
        "lm-reference.md",
        "lm-context-log.md",
        "lm-provenance.log",
    ]
    for f in files:
        (task_dir / f).write_text(
            "# x\n\n## Milestone 1: only\n- Status: PENDING\n", encoding="utf-8"
        )

    # Set explicit mtimes: provenance.log is newest by 2 seconds
    base = time.time()
    for i, f in enumerate(files):
        os.utime(task_dir / f, (base + i, base + i))

    t = parse_task_dir(task_dir)
    assert t.last_modified is not None
    # Newest file mtime should match the last file we touched
    assert abs(t.last_modified.timestamp() - (base + len(files) - 1)) < 1


def test_last_modified_only_tasks_file(tmp_path: Path) -> None:
    """Even with just tasks.md present, last_modified equals its mtime."""
    from aa_ma.tui.parser import parse_task_dir

    task_dir = tmp_path / "solo"
    task_dir.mkdir()
    tasks_file = task_dir / "solo-tasks.md"
    tasks_file.write_text(
        "# x\n\n## Milestone 1: only\n- Status: PENDING\n", encoding="utf-8"
    )

    t = parse_task_dir(task_dir)
    assert t.last_modified is not None
    assert abs(t.last_modified.timestamp() - tasks_file.stat().st_mtime) < 1
