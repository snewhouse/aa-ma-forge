"""Layered cuts L0–L3 over the codemem graph (diagram-generation M3).

Ported from the Ticket 3 prototype (branch ``prototype/diagram-generation-3``,
``Scope`` module) and pinned against its frozen data in
``tests/fixtures/draw-prototype-graph.json``:

* L0 — directories at depth 1      * L2 — files
* L1 — directories at depth 2      * L3 — symbols (``path::Class.method``), calls only

L0–L2 carry ``import`` and ``call`` edges, each labelled with its kind. A
``scope`` restricts any level to the hop-limited neighbourhood of the paths it
prefixes, walked before directories are collapsed. ``tests/`` is excluded at
every level unless ``include_tests``.

Reads the index directly, so it issues ``SELECT DISTINCT`` itself: codemem's
v1 ``edges`` table stores every call row twice (ADR-0014).
"""

from __future__ import annotations

import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from enum import IntEnum

__all__ = [
    "DIRECTIONS", "KINDS", "MAX_EDGES", "MIN_SCHEMA_VERSION",
    "Cut", "Level", "cut", "from_edges", "is_test_path", "node_id",
]

MAX_EDGES = 500  # mermaid's default maxEdges — the one hard ceiling (Ticket 3)
MIN_SCHEMA_VERSION = 3  # the first schema with file_edges — not CURRENT_SCHEMA_VERSION
DIRECTIONS = ("up", "down", "both")
KINDS = ("import", "call", "both")
_COLLAPSE_DEPTH = {0: 1, 1: 2}


class Level(IntEnum):
    L0 = 0
    L1 = 1
    L2 = 2
    L3 = 3


@dataclass(frozen=True)
class Cut:
    nodes: dict[str, str]  # node_id -> label
    edges: set[tuple[str, str, str]]  # (src_id, dst_id, kind)
    dropped: int  # edges beyond MAX_EDGES, not emitted


def node_id(name: str, level: Level) -> str:
    """Mermaid-safe id for ``name`` at ``level``; pinned by ``draw-node-ids.json``.

    The prototype's ``nid`` hash over ``L<level>:<name>``: seed 7, ``h*31 + c``,
    uint32, base36. ``c`` is JS ``charCodeAt(0)`` of each code point, i.e. the high
    surrogate for a non-BMP character — kept, because M12's JS must match byte-for-byte.
    """
    h = 7
    for ch in f"L{int(level)}:{name}":
        cp = ord(ch)
        unit = 0xD800 + ((cp - 0x10000) >> 10) if cp > 0xFFFF else cp
        h = (h * 31 + unit) & 0xFFFFFFFF
    return "n" + _base36(h)


def _base36(n: int) -> str:
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    out = ""
    while True:
        n, r = divmod(n, 36)
        out = digits[r] + out
        if n == 0:
            return out


def is_test_path(path: str) -> bool:
    """True when any directory component is ``tests``."""
    return "tests" in path.split("/")[:-1]


def cut(
    conn: sqlite3.Connection,
    level: Level,
    *,
    scope: str | None = None,
    hops: int = 1,
    include_tests: bool = False,
    direction: str = "both",
    kind: str = "both",
) -> Cut:
    if direction not in DIRECTIONS:
        raise ValueError(f"direction must be one of {DIRECTIONS}, got {direction!r}")
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {KINDS}, got {kind!r}")
    if hops < 0:
        raise ValueError(f"hops must be >= 0, got {hops}")
    level = Level(level)
    if level is Level.L3 and kind == "import":
        raise ValueError("L3 is symbol-level calls only; use --kind call or both")

    def keep(path: str) -> bool:
        return include_tests or not is_test_path(path)

    if level is Level.L3:
        # Recursive calls stay as self-loops here: at symbol level they are information.
        edges = {
            (f"{sf}::{sp}", f"{df}::{dp}", "call")
            for sf, sp, df, dp in _symbol_calls(conn)
            if keep(sf) and keep(df)
        }
    else:
        edges = {e for e in _file_edges(conn, kind) if keep(e[0]) and keep(e[1])}

    if scope:
        edges = _neighbourhood(edges, scope, hops, direction)
    if level in _COLLAPSE_DEPTH:
        depth = _COLLAPSE_DEPTH[level]
        edges = {
            (_dir(a, depth), _dir(b, depth), k)
            for a, b, k in edges
            if _dir(a, depth) != _dir(b, depth)
        }

    return from_edges(edges, level)


def from_edges(edges: set[tuple[str, str, str]], level: Level) -> Cut:
    """Named ``(src, dst, kind)`` edges -> ``Cut``: sorted, capped at ``MAX_EDGES``, ids checked unique."""
    ordered = sorted(edges)
    kept = ordered[:MAX_EDGES]
    names = {n for a, b, _ in kept for n in (a, b)}
    nodes = {node_id(n, level): n for n in names}
    if len(nodes) != len(names):
        raise ValueError(f"node_id collision at {level.name}; ids are not unique for this graph")
    return Cut(
        nodes=nodes,
        edges={(node_id(a, level), node_id(b, level), k) for a, b, k in kept},
        dropped=len(ordered) - len(kept),
    )


def _dir(path: str, depth: int) -> str:
    """Directory of ``path`` truncated to ``depth`` segments; top-level files stay themselves."""
    return "/".join(path.split("/")[:-1][:depth]) or path


def _file_edges(conn: sqlite3.Connection, kind: str) -> set[tuple[str, str, str]]:
    edges: set[tuple[str, str, str]] = set()
    if kind in ("call", "both"):
        # One call query for every level: L0-L2 project L3's symbol calls onto files.
        edges |= {(sf, df, "call") for sf, _, df, _ in _symbol_calls(conn) if sf != df}
    if kind in ("import", "both"):
        edges |= {
            (a, b, "import")
            for a, b in conn.execute(
                """
                SELECT DISTINCT s.path, d.path
                FROM file_edges fe
                JOIN files s ON s.id = fe.src_file_id
                JOIN files d ON d.id = fe.dst_file_id
                WHERE fe.kind = 'import' AND s.id <> d.id
                """
            )
        }
    return edges


def _symbol_calls(conn: sqlite3.Connection) -> set[tuple[str, str, str, str]]:
    rows = conn.execute(
        """
        SELECT DISTINCT sf.path, s.scip_id, df.path, d.scip_id
        FROM edges e
        JOIN symbols s ON s.id = e.src_symbol_id
        JOIN symbols d ON d.id = e.dst_symbol_id
        JOIN files sf ON sf.id = s.file_id
        JOIN files df ON df.id = d.file_id
        WHERE e.kind = 'call'
        """
    )
    return {(sf, _symbol_path(ss), df, _symbol_path(ds)) for sf, ss, df, ds in rows}


def _symbol_path(scip_id: str) -> str:
    """``codemem . /src/x.py#Cls.meth`` -> ``Cls.meth`` (symbol-id-grammar v1)."""
    return scip_id.rsplit("#", 1)[-1]


def _neighbourhood(
    edges: set[tuple[str, str, str]], scope: str, hops: int, direction: str
) -> set[tuple[str, str, str]]:
    """Edges reached within ``hops`` from every node whose name starts with ``scope``."""
    down: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    up: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    for e in edges:
        down[e[0]].append(e)
        up[e[1]].append(e)
    frontier = {n for n in (*down, *up) if n.startswith(scope)}
    seen = set(frontier)
    reached: set[tuple[str, str, str]] = set()
    for _ in range(hops):
        nxt: set[str] = set()
        for n in frontier:
            if direction != "up":
                for e in down.get(n, ()):
                    reached.add(e)
                    if e[1] not in seen:
                        nxt.add(e[1])
            if direction != "down":
                for e in up.get(n, ()):
                    reached.add(e)
                    if e[0] not in seen:
                        nxt.add(e[0])
        seen |= nxt
        frontier = nxt
    return reached
