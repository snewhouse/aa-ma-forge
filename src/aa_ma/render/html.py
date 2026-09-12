"""Markdown → one self-contained HTML file. markdown-it-py + pinned mermaid ESM; no other assets."""

from __future__ import annotations

import functools
import html as _html

from markdown_it import MarkdownIt

MERMAID_VERSION = "11.17.2"  # latest 11.x at the 4.1 prototype (2026-09-12); single constant, bump deliberately
_CSS = """
:root{color-scheme:light dark;--fg:#1a1a1a;--bg:#fff;--muted:#f4f4f4;--line:#ddd}
@media(prefers-color-scheme:dark){:root{--fg:#e6e6e6;--bg:#151515;--muted:#222;--line:#333}}
body{margin:0;padding:1.5rem 1rem;background:var(--bg);color:var(--fg);font:15px/1.55 system-ui,sans-serif;max-width:56rem;margin-inline:auto}
pre{background:var(--muted);padding:.8rem;overflow-x:auto;border:1px solid var(--line)}
pre.mermaid{background:transparent;border:0;text-align:center}
table{border-collapse:collapse;display:block;overflow-x:auto}td,th{border:1px solid var(--line);padding:.3rem .6rem}
@media print{pre.mermaid{break-inside:avoid}a[href]::after{content:" (" attr(href) ")"}}
"""


def _fence(self, tokens, idx, options, env):  # noqa: ANN001 — markdown-it-py renderer-rule signature
    tok = tokens[idx]
    if tok.info.strip() == "mermaid":
        return f'<pre class="mermaid">{_html.escape(tok.content, quote=False)}</pre>\n'
    return self.fence(tokens, idx, options, env)


def _strip_comments(s: str) -> str:
    """Drop every `<!-- … -->` span; an unterminated `<!--` eats the rest, as a browser would.
    str.find, not a lazy regex: `<!--.*?-->` re-scans to EOF per opener on hostile input."""
    out, i = [], 0
    while (j := s.find("<!--", i)) != -1:
        out.append(s[i:j])
        if (k := s.find("-->", j + 4)) == -1:
            return "".join(out)
        i = k + 3
    out.append(s[i:])
    return "".join(out)


def _raw_html(self, tokens, idx, options, env):  # noqa: ANN001
    """Comments vanish; every other raw-HTML token is rendered as escaped text. Never passthrough."""
    return _html.escape(_strip_comments(tokens[idx].content))


@functools.cache  # one parser per process; rules carry no per-render state
def _md() -> MarkdownIt:
    md = MarkdownIt("commonmark", {"html": True}).enable(["table", "strikethrough"])
    md.add_render_rule("fence", _fence)
    md.add_render_rule("html_block", _raw_html)
    md.add_render_rule("html_inline", _raw_html)
    return md


def render_markdown(text: str, *, title: str) -> str:
    body = _md().render(text)
    return (
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        f"<title>{_html.escape(title)}</title>\n<style>{_CSS}</style>\n</head>\n<body>\n<main>\n{body}</main>\n"
        '<script type="module">\n'
        f'import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@{MERMAID_VERSION}/dist/mermaid.esm.min.mjs";\n'
        'const dark = matchMedia("(prefers-color-scheme: dark)").matches;\n'
        'mermaid.initialize({ startOnLoad: true, theme: dark ? "dark" : "default", securityLevel: "strict" });\n'
        "</script>\n</body>\n</html>\n"
    )
