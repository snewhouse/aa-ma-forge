import os
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


def test_a_sigil_free_plan_reports_zero_sigil_edges(capsys):
    """diagram-generation M11 AC1/AC8: edges=0 is the §6.7 HARD item's opt-out."""
    assert lint_main([str(FIX / "plan_ok.md"), "--repo-root", str(REPO)]) == 0
    assert "\nsigils: edges=0 phantom=0 unknown=0 index-unknown=0\nrender: " in "\n" + capsys.readouterr().out


def test_an_unread_section_13_is_sigils_unknown_never_zero(tmp_path, capsys):
    """L-012: an unterminated fence hides §13 — its sigil count is unknown, not 0 (not an opt-out)."""
    plan = tmp_path / "u-plan.md"
    plan.write_text('## 13. Architecture View\n\n### Component view\n\n```mermaid\ngraph TD\n  A -->|"@import"| B\n')
    assert lint_main([str(plan), "--repo-root", str(REPO)]) == 1
    out = capsys.readouterr().out
    assert "sigils: UNKNOWN" in out and "sigils: edges=" not in out


@pytest.mark.parametrize("argv", [[], ["/nonexistent.md"], [str(FIX)]])  # missing / not a file / dir
def test_usage_exit_2(argv, capsys):
    assert lint_main(argv) == 2
    assert "usage" in capsys.readouterr().err.lower()


def test_tasks_flag(tmp_path, capsys):
    plan = tmp_path / "foo.md"
    plan.write_text((FIX / "plan_flow_required.md").read_text().split("### Milestone 1")[0])
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


def test_render_duplicate_stems_refused(tmp_path, capsys):
    (tmp_path / "a").mkdir()
    (tmp_path / "b").mkdir()
    for d in ("a", "b"):
        (tmp_path / d / "plan.md").write_text("# x\n")
    out = tmp_path / "out"
    argv = [
        str(tmp_path / "a" / "plan.md"),
        str(tmp_path / "b" / "plan.md"),
        "--out",
        str(out),
    ]
    assert render_main(argv) == 2  # never silently clobber a/plan.md with b/plan.md
    assert "plan.html" in capsys.readouterr().err and not out.exists()


@pytest.mark.skipif(os.geteuid() == 0, reason="chmod 0 does not stop root")
def test_render_unreadable_source_exit_2_writes_nothing(tmp_path, capsys):
    src = tmp_path / "locked.md"
    src.write_text("# x\n")
    src.chmod(0)
    out = tmp_path / "out"
    try:
        assert render_main([str(FIX / "plan_ok.md"), str(src), "--out", str(out)]) == 2
    finally:
        src.chmod(0o644)
    assert "locked.md" in capsys.readouterr().err and not out.exists()  # all-or-nothing


def test_render_out_is_a_file_exit_2(tmp_path, capsys):
    out = tmp_path / "not-a-dir"
    out.write_text("")
    assert render_main([str(FIX / "plan_ok.md"), "--out", str(out)]) == 2
    assert "not-a-dir" in capsys.readouterr().err
