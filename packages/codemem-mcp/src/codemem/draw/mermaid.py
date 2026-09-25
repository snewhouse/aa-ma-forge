"""Cut -> mermaid flowchart text (diagram-generation M3).

Text only (ADR-0010): rendering to SVG/PNG goes through the existing ``MMDC_BIN``
seam in ``aa_ma.render.mermaid_lint``. Edges carry the QUOTED kind sigil
``-->|"@import"|`` — the bare ``-->|@import|`` form is a mermaid 11 parse error
(``@`` lexes as an edge id), and M5's PHANTOM_EDGE check reads the quoted form.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .captions import start_ids
from .cut import MAX_EDGES, Cut, Level, node_id

if TYPE_CHECKING:  # the renderer stays free of io_sinks' yaml/sqlite imports (§6.8)
    from .io_sinks import IoEdge

__all__ = ["CATEGORY_LABEL", "START_STYLE", "TIER_STYLE", "escape_label", "io_to_mermaid", "to_mermaid"]

START_STYLE = "stroke-width:4px"  # the @start highlight; M12's explorer reuses it
# I/O tiers (M9 AC4): mermaid has no `:::class` on edges, so edges get ids and
# `class e0,e3 qualified` lines. Space-separated dasharray: a comma would split the style.
TIER_STYLE = {"qualified": "stroke-width:2px,stroke-dasharray:0", "bare": "stroke-dasharray:4 4"}
CATEGORY_LABEL = {  # keys are io_sinks.CATEGORIES (pinned by a test)
    "db": "database", "http": "HTTP", "fs": "filesystem", "subprocess": "subprocess",
    "env": "environment", "queue": "queue / cache",
}

# '#' first: the other replacements introduce '#...;' entities that must survive.
# '%', '{', '}' stop a file name smuggling a `%%{init}%%` directive (it could
# restyle the diagram and beacon via themeCSS); '`' blocks markdown-string mode.
_ENTITIES = (
    ("#", "#35;"), ('"', "#quot;"), ("<", "#lt;"), (">", "#gt;"),
    ("%", "#37;"), ("{", "#123;"), ("}", "#125;"), ("`", "#96;"),
)


def escape_label(text: str) -> str:
    """Make a node label safe inside ``["..."]``; control characters become ``?``."""
    for raw, entity in _ENTITIES:
        text = text.replace(raw, entity)
    return "".join(c if c.isprintable() else "?" for c in text)


def to_mermaid(c: Cut, *, captions: dict[str, str] | None = None) -> str:
    """Deterministic ``flowchart LR``: nodes by label, then edges by (src, dst, kind) label.

    ``captions`` contributes only the ``@start`` highlight; caption prose stays outside the
    fence (``captions.for_cut``), so rewording a caption never changes this text.
    """
    lines = ["flowchart LR"]
    if c.dropped:
        lines.append(f"%% {c.dropped} edges not shown: over mermaid maxEdges {MAX_EDGES}")
    for nid, label in sorted(c.nodes.items(), key=lambda kv: kv[1]):
        lines.append(f'  {nid}["{escape_label(label)}"]')
    for a, b, kind in sorted(c.edges, key=lambda e: (c.nodes[e[0]], c.nodes[e[1]], e[2])):
        lines.append(f'  {a} -->|"@{kind}"| {b}')
    if start := start_ids(c, captions):
        lines.append(f"  classDef start {START_STYLE}")
        lines.append(f"  class {','.join(start)} start")
    return "\n".join(lines) + "\n"


def io_to_mermaid(edges: list[IoEdge], level: Level) -> str:
    """The I/O view: languages as subgraphs of sink categories, one numbered edge per arrow.

    Edge labels are ``IoEdge.calls``; edge ids ``e0..`` follow the sorted edge order, so
    the text is deterministic. Always exactly two ``classDef`` lines (M9 AC1).
    """
    edges = sorted(edges)
    kept = edges[:MAX_EDGES]
    lines = ["flowchart LR"]
    if len(edges) > len(kept):
        lines.append(f"%% {len(edges) - len(kept)} edges not shown: over mermaid maxEdges {MAX_EDGES}")
    for lang in sorted({e.lang for e in kept}):
        lines.append(f'  subgraph io_{lang}["{lang}"]')
        for category in sorted({e.category for e in kept if e.lang == lang}):
            lines.append(f'    io_{lang}_{category}[("{CATEGORY_LABEL[category]}")]')
        lines.append("  end")
    for src in sorted({e.src for e in kept}):
        lines.append(f'  {node_id(src, level)}["{escape_label(src)}"]')
    tiers: dict[str, list[str]] = {t: [] for t in TIER_STYLE}
    for i, e in enumerate(kept):
        lines.append(f'  {node_id(e.src, level)} e{i}@-->|"{e.calls}"| io_{e.lang}_{e.category}')
        tiers[e.tier].append(f"e{i}")
    lines += [f"  classDef {t} {style}" for t, style in TIER_STYLE.items()]
    lines += [f"  class {','.join(ids)} {t}" for t, ids in tiers.items() if ids]
    return "\n".join(lines) + "\n"
