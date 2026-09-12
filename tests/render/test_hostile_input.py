"""Untrusted plan.md must not cost super-linear time or leak host facts (§6.8 M2 security audit;
same class as L-013's 17-second regex). Budgets are generous wall-clock ceilings: the quadratic
forms measured 14-20 s at 200 KB, the linear forms well under a second."""

import time
from pathlib import Path

from aa_ma.render.html import render_markdown
from aa_ma.render.mermaid_lint import lint_text

FIX = Path(__file__).parent / "fixtures"
REPO = Path(__file__).resolve().parents[2]
BUDGET_S = 2.0


def _plan_with_component(body: str) -> str:
    return (
        "# P\n**Created:** 2026-09-11\n**Diagram-Waiver:** none\n\n"
        "## 13. Architecture View\n### Component view\n" + body
    )


def _timed(text: str) -> float:
    t0 = time.perf_counter()
    lint_text(text, REPO)
    return time.perf_counter() - t0


def test_bracket_flood_is_linear() -> None:
    body = "```mermaid\nflowchart LR\n  " + "[" * 200_000 + "\n```\n"
    assert _timed(_plan_with_component(body)) < BUDGET_S


def test_slash_flood_is_linear() -> None:
    body = "```mermaid\nflowchart LR\n  A[" + "a/" * 100_000 + "]\n```\n"
    assert _timed(_plan_with_component(body)) < BUDGET_S


def test_fence_flood_is_linear() -> None:
    body = "```mermaid\nflowchart LR\n  A --> B\n```\n" * 6_000
    assert _timed(_plan_with_component(body)) < BUDGET_S


def test_unclosed_opener_flood_is_linear() -> None:
    body = "```mermaid\n" * 18_000
    assert _timed(_plan_with_component(body)) < BUDGET_S


def test_paths_outside_repo_root_are_never_probed_as_present(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (tmp_path / "secret.json").write_text("{}")  # exists, but outside repo_root
    body = (
        "```mermaid\nflowchart LR\n"
        f'  A["{tmp_path / "secret.json"}"] --> B[../secret.json] --> C[docs/x.md]\n```\n'
    )
    rep = lint_text(_plan_with_component(body), repo)
    stale = [f.message for f in rep.findings if f.code == "STALE_PATH"]
    assert len(stale) == 3, rep.findings  # absolute, parent-escape and plain-missing all reported


def test_unknown_type_message_never_carries_raw_control_chars() -> None:
    body = "```mermaid\n\x1b[2J\x1b]0;pwned\x07evil TD\n  A --> B\n```\n"
    rep = lint_text(_plan_with_component(body), REPO)
    msgs = [f.message for f in rep.findings if f.code == "UNKNOWN_TYPE"]
    assert msgs and "\x1b" not in msgs[0] and "\\x1b" in msgs[0]


def test_render_unterminated_comment_flood_is_linear() -> None:
    body = (
        "<!--\n" * 50_000
    )  # one html_block, 50k openers, no closer (M4 comment stripper)
    t0 = time.perf_counter()
    render_markdown(body, title="t")
    assert time.perf_counter() - t0 < BUDGET_S
