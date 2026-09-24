"""codemem.draw.mermaid — Cut -> mermaid flowchart text (diagram-generation M3).

Render evidence: ``render_check`` is asserted NEVER ``FAIL`` (a definitive parse
error). In CI there is no browser, so it is ``UNKNOWN`` — honest, never counted as
PASS (L-012). Where a renderer works (locally since 2026-09-24) it is ``PASS``, and
that verdict is recorded in provenance as an observation, not inferred from here.
"""

from __future__ import annotations

from aa_ma.render.mermaid_lint import render_check

from codemem.draw.cut import MAX_EDGES, Cut, Level, node_id
from codemem.draw.mermaid import escape_label, to_mermaid


def _cut(names: list[tuple[str, str, str]], level: Level = Level.L2, dropped: int = 0) -> Cut:
    ids = {n: node_id(n, level) for a, b, _ in names for n in (a, b)}
    return Cut(
        nodes={i: n for n, i in ids.items()},
        edges={(ids[a], ids[b], k) for a, b, k in names},
        dropped=dropped,
    )


SAMPLE = [
    ("src/a.py", "src/b.py", "import"),
    ("src/a.py", "src/b.py", "call"),
    ("src/b.py", "lib/c (d)-e.py", "call"),
]


def test_header_nodes_and_quoted_sigil_edges() -> None:
    text = to_mermaid(_cut(SAMPLE))
    lines = text.splitlines()
    assert lines[0] == "flowchart LR"
    a, b = node_id("src/a.py", Level.L2), node_id("src/b.py", Level.L2)
    assert f'  {a}["src/a.py"]' in lines
    assert f'  {a} -->|"@import"| {b}' in lines
    assert f'  {a} -->|"@call"| {b}' in lines
    assert "-->|@" not in text  # bare sigil is a mermaid 11 parse error


def test_deterministic() -> None:
    assert to_mermaid(_cut(SAMPLE)) == to_mermaid(_cut(list(reversed(SAMPLE))))


def test_parens_and_hyphen_survive_inside_quotes() -> None:
    assert '["lib/c (d)-e.py"]' in to_mermaid(_cut(SAMPLE))


def test_escape_label() -> None:
    assert escape_label('x"y') == "x#quot;y"
    assert escape_label("a#b") == "a#35;b"
    assert escape_label("<b>") == "#lt;b#gt;"
    assert escape_label("evil\x1b[31m") == "evil?[31m"
    assert escape_label("a (b)-c") == "a (b)-c"


def test_escape_hash_first() -> None:
    """'#' is escaped before the entities it introduces, never double-escaped."""
    assert escape_label('"') == "#quot;"


def test_dropped_is_reported_as_comment() -> None:
    text = to_mermaid(_cut(SAMPLE, dropped=7))
    assert f"%% 7 edges not shown: over mermaid maxEdges {MAX_EDGES}" in text


def test_empty_cut_is_valid_header_only() -> None:
    assert to_mermaid(Cut(nodes={}, edges=set(), dropped=0)) == "flowchart LR\n"


def test_render_never_fails_on_hostile_labels() -> None:
    hostile = SAMPLE + [("x\"y#z<w>.py", "é/😀.py", "import")]
    text = to_mermaid(_cut(hostile))
    assert render_check([text]) != "FAIL", text
