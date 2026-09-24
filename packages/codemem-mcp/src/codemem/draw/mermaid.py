"""Cut -> mermaid flowchart text (diagram-generation M3).

Text only (ADR-0010): rendering to SVG/PNG goes through the existing ``MMDC_BIN``
seam in ``aa_ma.render.mermaid_lint``. Edges carry the QUOTED kind sigil
``-->|"@import"|`` — the bare ``-->|@import|`` form is a mermaid 11 parse error
(``@`` lexes as an edge id), and M5's PHANTOM_EDGE check reads the quoted form.
"""

from __future__ import annotations

from .cut import MAX_EDGES, Cut

__all__ = ["escape_label", "to_mermaid"]

# '#' first: the other replacements introduce '#...;' entities that must survive.
_ENTITIES = (("#", "#35;"), ('"', "#quot;"), ("<", "#lt;"), (">", "#gt;"))


def escape_label(text: str) -> str:
    """Make a node label safe inside ``["..."]``; control characters become ``?``."""
    for raw, entity in _ENTITIES:
        text = text.replace(raw, entity)
    return "".join(c if c.isprintable() else "?" for c in text)


def to_mermaid(c: Cut) -> str:
    """Deterministic ``flowchart LR``: nodes by label, then edges by (src, dst, kind) label."""
    lines = ["flowchart LR"]
    if c.dropped:
        lines.append(f"%% {c.dropped} edges not shown: over mermaid maxEdges {MAX_EDGES}")
    for nid, label in sorted(c.nodes.items(), key=lambda kv: kv[1]):
        lines.append(f'  {nid}["{escape_label(label)}"]')
    for a, b, kind in sorted(c.edges, key=lambda e: (c.nodes[e[0]], c.nodes[e[1]], e[2])):
        lines.append(f'  {a} -->|"@{kind}"| {b}')
    return "\n".join(lines) + "\n"
