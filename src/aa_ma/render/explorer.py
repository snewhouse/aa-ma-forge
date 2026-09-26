"""`aa-ma-render --explorer`: the whole codemem graph in one clickable HTML page.

diagram-generation M12 (map Ticket 11, ADR-0010/0014). The graph is read through the
stdlib-sqlite3 seam (``graph.py``) and embedded as JSON; ``explorer.js`` derives each
level in the browser and drills on click through ONE delegated listener, so mermaid
keeps ``securityLevel: "strict"`` and no ``click`` line is ever emitted. Security is
html.py's: the same pinned CDN bundle and SRI, and a CSP composed by ``html.csp`` from
this page's own inline-script hash. Output lives in ``build/`` only (gitignored).
"""

from __future__ import annotations

import html as _html
import json
from pathlib import Path

from aa_ma.render.graph import GraphStatus, call_edges, import_edges, open_graph
from aa_ma.render.html import _CSS, MERMAID_SRI, MERMAID_VERSION, csp, sha256_b64

__all__ = ["MAX_EDGES", "build_explorer"]

# mermaid's default maxEdges. codemem.draw.cut.MAX_EDGES holds the same value; aa_ma may not
# import codemem (import contract), so tests/render/test_explorer_fixture.py pins the two.
MAX_EDGES = 500
_JS = (Path(__file__).with_name("explorer.js")).read_text(encoding="utf-8")
if "<script" in _JS.lower() or "</script" in _JS.lower():  # it is inlined verbatim: this would end it
    raise RuntimeError("explorer.js must not contain a script tag")
_PAGE_CSS = """
#bar{display:flex;gap:.5rem;align-items:center;flex-wrap:wrap;margin-bottom:1rem}
#stale{background:#fff3cd;color:#664d03;padding:.5rem .8rem;border:1px solid #ffe69c}
#out{overflow:auto}#out g.node{cursor:pointer}
"""


def _island(obj: object) -> str:
    """JSON safe inside ``<script type="application/json">``: no ``< > &`` survive, so a
    file named ``</script>`` cannot end the island (codemem.draw.captions.json_island's rule;
    aa_ma may not import it)."""
    return (
        json.dumps(obj, ensure_ascii=False, sort_keys=True)
        .replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    )


def build_explorer(repo_root: Path) -> tuple[str, str | None]:
    """(page, stale reason or None). Raises ``ValueError`` naming ``codemem build`` when the
    index is missing, too old or unreadable — an explorer of no graph is not a page."""
    h = open_graph(repo_root)
    try:
        if h.status not in (GraphStatus.OK, GraphStatus.STALE):
            raise ValueError(h.reason or h.status.value)
        edges = sorted(
            {(s, d, "import") for s, d in import_edges(h)} | {(s, d, "call") for s, d in call_edges(h)}
        )
    finally:
        if h.conn is not None:
            h.conn.close()
    stale = h.reason if h.status is GraphStatus.STALE else None
    graph = {"edges": [list(e) for e in edges], "maxEdges": MAX_EDGES, "stale": stale}
    page = (
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        f'<meta http-equiv="Content-Security-Policy" content="{csp(sha256_b64(_JS))}">\n'
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        f"<title>{_html.escape(repo_root.resolve().name)} — explorer</title>\n"
        f"<style>{_CSS}{_PAGE_CSS}</style>\n</head>\n<body>\n<main>\n"
        '<p id="stale" hidden></p>\n'
        '<div id="bar"><button id="top">top</button><button id="up">up</button>'
        '<label><input type="checkbox" id="tests"> tests</label> <code id="where"></code></div>\n'
        '<div id="out"></div>\n</main>\n'
        f'<script type="application/json" id="graph">{_island(graph)}</script>\n'
        f'<script src="https://cdn.jsdelivr.net/npm/mermaid@{MERMAID_VERSION}/dist/mermaid.min.js" '
        f'integrity="{MERMAID_SRI}" crossorigin="anonymous"></script>\n'
        f"<script>{_JS}</script>\n</body>\n</html>\n"
    )
    return page, stale
