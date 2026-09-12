"""Contract for aa_ma.render.html (plan-architecture-views M4)."""

from pathlib import Path

from aa_ma.render.html import MERMAID_SRI, MERMAID_VERSION, render_markdown

FIX = Path(__file__).parent / "fixtures" / "plan_ok.md"
GOLDEN = Path(__file__).resolve().parents[1] / "golden" / "render_plan_ok.html"


def test_mermaid_fence_becomes_pre_mermaid():
    out = render_markdown("```mermaid\nflowchart LR\n  A --> B\n```\n", title="t")
    assert '<pre class="mermaid">flowchart LR\n  A --&gt; B\n</pre>' in out


def test_tables_are_enabled():
    assert "<table>" in render_markdown("| a | b |\n|---|---|\n| 1 | 2 |\n", title="t")


def test_self_contained_and_pinned():
    out = render_markdown("# x\n", title="t")
    assert (
        f'src="https://cdn.jsdelivr.net/npm/mermaid@{MERMAID_VERSION}/dist/mermaid.min.js"'
        in out
    )
    assert MERMAID_VERSION.startswith(
        "11."
    )  # plan rule: latest 11.x; the dist path may move at 12
    assert '<link rel="stylesheet"' not in out
    assert "<title>t</title>" in out and "prefers-color-scheme" in out


def test_cdn_script_is_integrity_pinned_and_csp_locked():
    """§6.8 M4 security WARNING (A08): the single-file UMD bundle carries SRI, so the hash covers
    every byte that runs; a CSP meta confines scripts to that host + the hashed inline init."""
    out = render_markdown("# x\n", title="t")
    assert f'integrity="{MERMAID_SRI}" crossorigin="anonymous"' in out
    assert MERMAID_SRI.startswith("sha384-") and len(MERMAID_SRI) == len("sha384-") + 64
    csp = out.split('http-equiv="Content-Security-Policy" content="')[1].split('"')[0]
    assert (
        "default-src 'none'" in csp
        and "script-src https://cdn.jsdelivr.net 'sha256-" in csp
    )
    assert (
        "'unsafe-inline'" not in csp.split("style-src")[0]
    )  # scripts are never unsafe-inline


def test_html_comments_outside_fences_are_dropped():
    assert "hidden" not in render_markdown("<!-- hidden -->\ntext\n", title="t")


def test_html_comments_inside_fences_are_kept():
    out = render_markdown("```markdown\n<!-- keep -->\n```\n", title="t")
    assert "&lt;!-- keep --&gt;" in out


def test_raw_html_is_escaped_not_passed_through():
    out = render_markdown("<script>alert(1)</script>\n\ntext <b>x</b>\n", title="t")
    main = out.split("<main>")[1].split("</main>")[0]  # the skeleton's own init <script> sits outside
    assert "<script>" not in main and "&lt;script&gt;" in main and "&lt;b&gt;" in main


def test_golden():
    assert render_markdown(FIX.read_text(), title="plan_ok") == GOLDEN.read_text()


def test_html_after_a_comment_on_the_same_block_survives_escaped():
    out = render_markdown("<!-- c --> <div>keep</div>\ntext\n", title="t")
    assert (
        "&lt;div&gt;keep&lt;/div&gt;" in out and "<!--" not in out and " c " not in out
    )


def test_unterminated_comment_swallows_the_block_like_a_browser():
    assert "gone" not in render_markdown("<!-- gone\n<b>gone</b>\n", title="t")
