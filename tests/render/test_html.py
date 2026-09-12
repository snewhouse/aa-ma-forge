"""Contract for aa_ma.render.html (plan-architecture-views M4)."""

from pathlib import Path

from aa_ma.render.html import MERMAID_VERSION, render_markdown

FIX = Path(__file__).parent / "fixtures" / "plan_ok.md"
GOLDEN = Path(__file__).resolve().parents[1] / "golden" / "render_plan_ok.html"


def test_mermaid_fence_becomes_pre_mermaid():
    out = render_markdown("```mermaid\nflowchart LR\n  A --> B\n```\n", title="t")
    assert '<pre class="mermaid">flowchart LR\n  A --&gt; B\n</pre>' in out


def test_tables_are_enabled():
    assert "<table>" in render_markdown("| a | b |\n|---|---|\n| 1 | 2 |\n", title="t")


def test_self_contained_and_pinned():
    out = render_markdown("# x\n", title="t")
    assert f"mermaid@{MERMAID_VERSION}/dist/mermaid.esm.min.mjs" in out
    assert '<link rel="stylesheet"' not in out
    assert "<title>t</title>" in out and "prefers-color-scheme" in out


def test_html_comments_outside_fences_are_dropped():
    assert "hidden" not in render_markdown("<!-- hidden -->\ntext\n", title="t")


def test_html_comments_inside_fences_are_kept():
    out = render_markdown("```markdown\n<!-- keep -->\n```\n", title="t")
    assert "&lt;!-- keep --&gt;" in out


def test_raw_html_is_escaped_not_passed_through():
    out = render_markdown("<script>alert(1)</script>\n\ntext <b>x</b>\n", title="t")
    assert "<script>" not in out and "&lt;script&gt;" in out and "&lt;b&gt;" in out


def test_golden():
    assert render_markdown(FIX.read_text(), title="plan_ok") == GOLDEN.read_text()
