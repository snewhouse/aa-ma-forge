"""Tests for aa_ma.tui.__main__ CLI dispatch (M2 T2.5).

Created in aa-ma-tui-tracker M2 (2026-05-18).

Covers:
    - --snapshot / --snapshot=tree / --snapshot=summary / --json dispatch
    - --task NAME (exit 0 if found, 2 if not)
    - --include-completed flag extends discovery roots
    - no tasks discovered → exit 3
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest


def _populate(root: Path, fixture_dir: Path) -> None:
    """Copy one fixture task into `root` so discover_tasks finds it."""
    root.mkdir(parents=True, exist_ok=True)
    shutil.copytree(fixture_dir, root / fixture_dir.name)


# =============================================================================
# T2.5: __main__ dispatch + exit codes
# =============================================================================


def test_main_dispatch_board_default(
    tmp_path: Path, fixtures_dir: Path, capsys: pytest.CaptureFixture
) -> None:
    """`--snapshot` (no value) defaults to board; exits 0 with kanban output."""
    from aa_ma.tui.__main__ import main

    _populate(tmp_path, fixtures_dir / "playwright-skill")

    code = main(["--snapshot", "--root", str(tmp_path)])
    captured = capsys.readouterr()

    assert code == 0
    assert "PENDING" in captured.out
    assert "COMPLETE" in captured.out
    assert "playwright-skill" in captured.out


def test_main_dispatch_tree_requires_task(
    tmp_path: Path, fixtures_dir: Path, capsys: pytest.CaptureFixture
) -> None:
    """`--snapshot=tree --task NAME` renders tree for the named task."""
    from aa_ma.tui.__main__ import main

    _populate(tmp_path, fixtures_dir / "playwright-skill")

    code = main(
        [
            "--snapshot=tree",
            "--task",
            "playwright-skill",
            "--root",
            str(tmp_path),
        ]
    )
    captured = capsys.readouterr()

    assert code == 0
    assert "playwright-skill" in captured.out
    # Tree always shows at least one milestone heading
    assert "M1:" in captured.out


def test_main_dispatch_summary(
    tmp_path: Path, fixtures_dir: Path, capsys: pytest.CaptureFixture
) -> None:
    """`--snapshot=summary` prints one line per discovered task."""
    from aa_ma.tui.__main__ import main

    _populate(tmp_path, fixtures_dir / "playwright-skill")

    code = main(["--snapshot=summary", "--root", str(tmp_path)])
    captured = capsys.readouterr()

    assert code == 0
    assert "playwright-skill" in captured.out


def test_main_dispatch_json(
    tmp_path: Path, fixtures_dir: Path, capsys: pytest.CaptureFixture
) -> None:
    """`--json` emits parseable JSON envelope."""
    from aa_ma.tui.__main__ import main

    _populate(tmp_path, fixtures_dir / "playwright-skill")

    code = main(["--json", "--root", str(tmp_path)])
    captured = capsys.readouterr()

    assert code == 0
    parsed = json.loads(captured.out)
    assert parsed["schema_version"] == 1
    names = [t["name"] for t in parsed["tasks"]]
    assert "playwright-skill" in names


def test_main_exit_code_no_tasks(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
    """Empty root + --snapshot → exit code 3."""
    from aa_ma.tui.__main__ import main

    empty = tmp_path / "empty"
    empty.mkdir()

    code = main(["--snapshot", "--root", str(empty)])
    assert code == 3


def test_main_exit_code_task_not_found(tmp_path: Path, fixtures_dir: Path) -> None:
    """--task NAME with non-existent NAME → exit code 2."""
    from aa_ma.tui.__main__ import main

    _populate(tmp_path, fixtures_dir / "playwright-skill")

    code = main(
        [
            "--snapshot=tree",
            "--task",
            "does-not-exist",
            "--root",
            str(tmp_path),
        ]
    )
    assert code == 2


def test_main_include_completed_flag(
    tmp_path: Path, fixtures_dir: Path, capsys: pytest.CaptureFixture
) -> None:
    """--include-completed extends discovery to the completed/ subdir."""
    from aa_ma.tui.__main__ import main

    # Simulate ~/.claude layout: active/ empty, completed/ has one task
    claude_root = tmp_path / ".claude"
    (claude_root / "dev" / "active").mkdir(parents=True)
    completed_dir = claude_root / "dev" / "completed"
    completed_dir.mkdir(parents=True)
    shutil.copytree(
        fixtures_dir / "playwright-skill",
        completed_dir / "playwright-skill",
    )

    # Without --include-completed, the active/ dir is empty → exit 3
    code = main(["--snapshot", "--root", str(claude_root)])
    assert code == 3

    # With --include-completed, the completed task is discovered → exit 0
    code = main(["--snapshot", "--include-completed", "--root", str(claude_root)])
    captured = capsys.readouterr()
    assert code == 0
    assert "playwright-skill" in captured.out


def test_main_no_flags_launches_textual_app(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No --snapshot / --json → constructs + runs AAMAApp (M3 Step 3.10)."""
    from aa_ma.tui import app as app_module
    from aa_ma.tui.__main__ import main

    launched: list[app_module.AAMAApp] = []
    # Replace run() so the test doesn't actually start a Textual loop.
    monkeypatch.setattr(
        app_module.AAMAApp, "run", lambda self, *a, **kw: launched.append(self)
    )

    code = main([])
    assert code == 0
    assert len(launched) == 1
    assert isinstance(launched[0], app_module.AAMAApp)
