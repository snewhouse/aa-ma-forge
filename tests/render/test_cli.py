from pathlib import Path

import pytest

from aa_ma.render.cli import lint_main, render_main

REPO = Path(__file__).resolve().parents[2]
FIX = Path(__file__).parent / "fixtures"


def test_clean_plan_exit_0(capsys):
    assert lint_main([str(FIX / "plan_ok.md"), "--repo-root", str(REPO)]) == 0
    assert "render: UNKNOWN" in capsys.readouterr().out


def test_findings_exit_1(capsys):
    assert lint_main([str(FIX / "plan_stale_path.md"), "--repo-root", str(REPO)]) == 1
    assert "STALE_PATH" in capsys.readouterr().out


@pytest.mark.parametrize(
    "argv", [[], ["/nonexistent.md"], [str(FIX)]]
)  # missing / not a file / dir
def test_usage_exit_2(argv, capsys):
    assert lint_main(argv) == 2
    assert "usage" in capsys.readouterr().err.lower()


def test_tasks_flag(tmp_path, capsys):
    plan = tmp_path / "foo.md"
    plan.write_text(
        (FIX / "plan_flow_required.md").read_text().split("### Milestone 1")[0]
    )
    tasks = tmp_path / "t.md"
    tasks.write_text("## Milestone 1: X\n- **Critical-Path:** data-xform\n")
    assert lint_main([str(plan), "--repo-root", str(REPO), "--tasks", str(tasks)]) == 1
    assert "NO_FLOW_VIEW" in capsys.readouterr().out


def test_render_writes_html(tmp_path, capsys):
    assert render_main([str(FIX / "plan_ok.md"), "--out", str(tmp_path)]) == 0
    out = tmp_path / "plan_ok.html"
    assert out.exists() and '<pre class="mermaid">' in out.read_text()
    assert capsys.readouterr().out.strip() == str(out)  # prints each written path


@pytest.mark.parametrize(
    "argv", [[], ["/nonexistent.md"], [str(FIX)]]
)  # none / not a file / dir
def test_render_usage_exit_2(argv, capsys):
    assert render_main(argv) == 2
    assert "usage" in capsys.readouterr().err.lower()
