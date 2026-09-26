"""Markdown → one self-contained HTML file. markdown-it-py + SRI-pinned mermaid UMD bundle behind a CSP; no other assets."""

from __future__ import annotations

import base64
import functools
import hashlib
import html as _html

from markdown_it import MarkdownIt

# Bumping this: re-check codemem draw's assumptions — MAX_EDGES (mermaid default
# maxEdges 500) and the quoted `-->|"@kind"|` sigil (bare `|@kind|` fails on 11.17.2).
MERMAID_VERSION = "11.17.2"  # latest 11.x at the 4.1 prototype (2026-09-12); single constant, bump deliberately
# codemem's io view needs flowchart edge ids (`n1 e0@--> n2` + `class e0 bare`), verified at 11.17.
# SRI of dist/mermaid.min.js at that version (single-file UMD, so the hash covers every byte that runs —
# the ESM entry lazy-imports chunks SRI cannot reach). Bump together with MERMAID_VERSION:
#   curl -sL https://cdn.jsdelivr.net/npm/mermaid@<V>/dist/mermaid.min.js | openssl dgst -sha384 -binary | openssl base64 -A
MERMAID_SRI = "sha384-EOXBFmc3gx5mb+vn0vPvvGqACToJD24hhacX5Yx+8NUUQrHIle/Qi5Bg9o3zKwW2"
_INIT_JS = (
    'mermaid.initialize({ startOnLoad: true, theme: matchMedia("(prefers-color-scheme: dark)").matches'
    ' ? "dark" : "default", securityLevel: "strict" });'
)


def sha256_b64(script: str) -> str:
    """The CSP source value for one inline script: base64 of its UTF-8 sha256."""
    return base64.b64encode(hashlib.sha256(script.encode()).digest()).decode()


def csp(*script_hashes: str) -> str:
    """The page CSP, admitting the mermaid CDN plus exactly these inline-script hashes.
    Defence in depth behind mermaid's DOMPurify; style-src must stay inline for mermaid's <style>."""
    hashes = " ".join(f"'sha256-{h}'" for h in script_hashes)
    return (
        f"default-src 'none'; script-src https://cdn.jsdelivr.net {hashes}; "
        "style-src 'unsafe-inline'; img-src data: https:; font-src data:"
    )


_INIT_SHA = sha256_b64(_INIT_JS)
_CSP = csp(_INIT_SHA)
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


_OPEN, _CLOSE = "<!--", "-->"


def _strip_comments(s: str) -> str:
    """Drop every `<!-- … -->` span; an unterminated `<!--` eats the rest, as a browser would.
    str.find, not a lazy regex: `<!--.*?-->` re-scans to EOF per opener on hostile input."""
    out, i = [], 0
    while (j := s.find(_OPEN, i)) != -1:
        out.append(s[i:j])
        if (k := s.find(_CLOSE, j + len(_OPEN))) == -1:
            return "".join(out)
        i = k + len(_CLOSE)
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
        f'<meta http-equiv="Content-Security-Policy" content="{_CSP}">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        f"<title>{_html.escape(title)}</title>\n<style>{_CSS}</style>\n</head>\n<body>\n<main>\n{body}</main>\n"
        f'<script src="https://cdn.jsdelivr.net/npm/mermaid@{MERMAID_VERSION}/dist/mermaid.min.js" '
        f'integrity="{MERMAID_SRI}" crossorigin="anonymous"></script>\n'
        f"<script>{_INIT_JS}</script>\n</body>\n</html>\n"
    )
