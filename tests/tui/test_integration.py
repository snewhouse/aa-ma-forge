"""End-to-end integration test — M4 Step 4.3.

Spawns `uv run aa-ma-tui` as a subprocess against a controlled temp dir
that mimics a `.claude` project layout. Validates the CLI contract end-to-end:
parser → model → discover → formatter (snapshot + JSON) without exercising
the interactive Textual app (kept out of subprocess scope; covered by
test_app_smoke.py via Pilot).

Closes part of the app.py coverage gap from M3 (live CLI launch path).
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _seed_fake_claude_root(tmp_path: Path, n_tasks: int = 2) -> Path:
    """Seed a `.claude/dev/active/` layout with N minimal AA-MA tasks.

    Returns the `.claude` directory itself (use as --root).
    """
    claude = tmp_path / ".claude"
    active = claude / "dev" / "active"
    active.mkdir(parents=True)

    for i in range(n_tasks):
        name = f"int-task-{i}"
        task_dir = active / name
        task_dir.mkdir()
        (task_dir / f"{name}-plan.md").write_text(f"# Plan for {name}\n")
        (task_dir / f"{name}-reference.md").write_text(f"# Reference for {name}\n")
        (task_dir / f"{name}-context-log.md").write_text(f"# Context for {name}\n")
        (task_dir / f"{name}-provenance.log").write_text(
            f"[2026-05-18T09:00:00] {name} initialised\n"
        )
        (task_dir / f"{name}-tasks.md").write_text(
            f"# {name}\n\n"
            "## Milestone 1: First milestone\n"
            "- Status: COMPLETE\n"
            "- Gate: SOFT\n\n"
            "### Step 1.1: A step\n"
            "- Status: COMPLETE\n"
            "- Result Log: done\n"
        )
    return claude


def _run_cli(*args: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Invoke the installed aa-ma-tui via uv run."""
    cmd = ["uv", "run", "aa-ma-tui", *args]
    return subprocess.run(
        cmd,
        cwd=cwd or REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


# -----------------------------------------------------------------------------
# Snapshot mode end-to-end
# -----------------------------------------------------------------------------


def test_cli_snapshot_summary_against_temp_root(tmp_path: Path) -> None:
    claude = _seed_fake_claude_root(tmp_path, n_tasks=2)
    result = _run_cli("--snapshot=summary", "--root", str(claude))
    assert result.returncode == 0, result.stderr
    assert "int-task-0" in result.stdout
    assert "int-task-1" in result.stdout
    assert "COMPLETE" in result.stdout


def test_cli_snapshot_board_against_temp_root(tmp_path: Path) -> None:
    claude = _seed_fake_claude_root(tmp_path, n_tasks=1)
    result = _run_cli("--snapshot=board", "--root", str(claude))
    assert result.returncode == 0, result.stderr
    # Board view groups by aggregate status
    assert "COMPLETE" in result.stdout


def test_cli_snapshot_tree_specific_task(tmp_path: Path) -> None:
    claude = _seed_fake_claude_root(tmp_path, n_tasks=1)
    result = _run_cli(
        "--snapshot=tree", "--task", "int-task-0", "--root", str(claude)
    )
    assert result.returncode == 0, result.stderr
    assert "int-task-0" in result.stdout
    assert "First milestone" in result.stdout


# -----------------------------------------------------------------------------
# JSON mode end-to-end
# -----------------------------------------------------------------------------


def test_cli_json_against_temp_root(tmp_path: Path) -> None:
    claude = _seed_fake_claude_root(tmp_path, n_tasks=3)
    result = _run_cli("--json", "--root", str(claude))
    assert result.returncode == 0, result.stderr
    envelope = json.loads(result.stdout)
    assert envelope["schema_version"] == 1
    assert isinstance(envelope["tasks"], list)
    assert len(envelope["tasks"]) == 3
    names = sorted(t["name"] for t in envelope["tasks"])
    assert names == ["int-task-0", "int-task-1", "int-task-2"]


def test_cli_json_envelope_well_formed(tmp_path: Path) -> None:
    """Per-task fields present and types as documented."""
    claude = _seed_fake_claude_root(tmp_path, n_tasks=1)
    result = _run_cli("--json", "--root", str(claude))
    envelope = json.loads(result.stdout)
    task = envelope["tasks"][0]
    assert task["name"] == "int-task-0"
    assert task["aggregate_status"] == "COMPLETE"
    assert isinstance(task["milestones"], list)
    assert len(task["milestones"]) == 1
    assert task["milestones"][0]["title"] == "First milestone"


# -----------------------------------------------------------------------------
# Exit codes
# -----------------------------------------------------------------------------


def test_cli_exit_3_when_no_tasks_discovered(tmp_path: Path) -> None:
    """EXIT_NO_TASKS = 3 when no tasks under any root."""
    empty_claude = tmp_path / ".claude"
    (empty_claude / "dev" / "active").mkdir(parents=True)
    result = _run_cli("--snapshot", "--root", str(empty_claude))
    assert result.returncode == 3, f"stdout={result.stdout!r} stderr={result.stderr!r}"


def test_cli_exit_2_when_task_not_found(tmp_path: Path) -> None:
    """EXIT_TASK_NOT_FOUND = 2 when --task NAME doesn't match any task."""
    claude = _seed_fake_claude_root(tmp_path, n_tasks=1)
    result = _run_cli(
        "--snapshot=tree", "--task", "nonexistent", "--root", str(claude)
    )
    assert result.returncode == 2


def test_cli_version_exits_0() -> None:
    result = _run_cli("--version")
    assert result.returncode == 0
    assert "aa-ma-tui" in result.stdout


# -----------------------------------------------------------------------------
# --include-completed
# -----------------------------------------------------------------------------


def test_cli_include_completed_extends_discovery(tmp_path: Path) -> None:
    """Tasks under .claude/dev/completed/ are discovered only with --include-completed."""
    claude = _seed_fake_claude_root(tmp_path, n_tasks=1)
    completed = claude / "dev" / "completed"
    completed.mkdir(parents=True)
    name = "old-task"
    task_dir = completed / name
    task_dir.mkdir()
    (task_dir / f"{name}-tasks.md").write_text(
        "## Milestone 1: archived\n- Status: COMPLETE\n\n### Step 1.1: x\n- Status: COMPLETE\n- Result Log: y\n"
    )
    for suf in ("plan", "reference", "context-log"):
        (task_dir / f"{name}-{suf}.md").write_text("")
    (task_dir / f"{name}-provenance.log").write_text("")

    # Without flag: only int-task-0 (1 task)
    r1 = _run_cli("--json", "--root", str(claude))
    e1 = json.loads(r1.stdout)
    assert len(e1["tasks"]) == 1
    assert {t["name"] for t in e1["tasks"]} == {"int-task-0"}

    # With flag: both
    r2 = _run_cli("--json", "--include-completed", "--root", str(claude))
    e2 = json.loads(r2.stdout)
    assert len(e2["tasks"]) == 2
    assert {t["name"] for t in e2["tasks"]} == {"int-task-0", "old-task"}
