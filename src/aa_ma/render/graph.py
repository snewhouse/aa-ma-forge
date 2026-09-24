"""Read-only seam from aa_ma onto a codemem index (ADR-0014).

aa_ma reads codemem's SQLite file with stdlib ``sqlite3`` and never imports
codemem — the ``aa-ma-never-imports-codemem`` import-linter contract pins that,
so the coupling is the on-disk schema (``PRAGMA user_version >= 3``), not a
Python API. ``open_graph`` never raises: every failure is a ``GraphStatus``
plus a reason naming the remedy.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

__all__ = ["GraphHandle", "GraphStatus", "call_edges", "import_edges", "open_graph"]

MIN_SCHEMA_VERSION = 3  # file_edges arrived in codemem schema v3
_REMEDY = "run `codemem build`"


class GraphStatus(StrEnum):
    OK = "ok"
    MISSING = "missing"
    SCHEMA_TOO_OLD = "schema_too_old"
    STALE = "stale"  # readable, but behind the working tree


@dataclass(frozen=True)
class GraphHandle:
    status: GraphStatus
    reason: str | None
    conn: sqlite3.Connection | None


def open_graph(repo_root: Path) -> GraphHandle:
    """Open ``<repo_root>/.codemem/index.db`` read-only and classify it."""
    db = Path(repo_root) / ".codemem" / "index.db"
    if not db.is_file():
        return GraphHandle(GraphStatus.MISSING, f"no codemem index at {db}; {_REMEDY}", None)
    conn = None
    try:
        conn = sqlite3.connect(f"{db.resolve().as_uri()}?mode=ro", uri=True)
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        if version < MIN_SCHEMA_VERSION:
            conn.close()
            return GraphHandle(
                GraphStatus.SCHEMA_TOO_OLD,
                f"codemem index is schema v{version}, need v{MIN_SCHEMA_VERSION}; {_REMEDY}",
                None,
            )
        stale = _stale_paths(conn, Path(repo_root))
    except sqlite3.Error as exc:
        if conn is not None:
            conn.close()
        return GraphHandle(
            GraphStatus.MISSING, f"codemem index at {db} is unreadable ({exc}); {_REMEDY}", None
        )
    if stale:
        shown = ", ".join(stale[:3]) + (", ..." if len(stale) > 3 else "")
        return GraphHandle(
            GraphStatus.STALE,
            f"{len(stale)} file(s) changed since indexing ({shown}); {_REMEDY}",
            conn,
        )
    return GraphHandle(GraphStatus.OK, None, conn)


def _stale_paths(conn: sqlite3.Connection, repo_root: Path) -> list[str]:
    """Indexed paths whose on-disk mtime is newer than recorded, or that are gone."""
    # ponytail: one stat per indexed file; cache per handle if M13 measures it hot.
    stale: list[str] = []
    for path, mtime in conn.execute("SELECT path, mtime FROM files ORDER BY path"):
        try:
            disk = int((repo_root / path).stat().st_mtime)
        except FileNotFoundError:
            stale.append(path)
            continue
        if mtime is not None and disk > mtime:
            stale.append(path)
    return stale


def import_edges(h: GraphHandle) -> set[tuple[str, str]]:
    """Resolved file->file import edges as ``(src_path, dst_path)``."""
    if h.conn is None:
        return set()
    return set(
        h.conn.execute(
            """
            SELECT DISTINCT s.path, d.path
            FROM file_edges fe
            JOIN files s ON s.id = fe.src_file_id
            JOIN files d ON d.id = fe.dst_file_id
            WHERE fe.kind = 'import'
            """
        )
    )


def call_edges(h: GraphHandle) -> set[tuple[str, str]]:
    """Resolved symbol->symbol calls projected to ``(src_path, dst_path)``.

    DISTINCT is load-bearing, not cosmetic: codemem's v1 ``edges`` table
    stores exact duplicate rows (its composite PK never matches — see
    ADR-0014). Same-file calls are dropped; a file graph has no self-loops.
    """
    if h.conn is None:
        return set()
    return set(
        h.conn.execute(
            """
            SELECT DISTINCT sf.path, df.path
            FROM edges e
            JOIN symbols ss ON ss.id = e.src_symbol_id
            JOIN symbols ds ON ds.id = e.dst_symbol_id
            JOIN files sf ON sf.id = ss.file_id
            JOIN files df ON df.id = ds.file_id
            WHERE e.kind = 'call' AND sf.id <> df.id
            """
        )
    )
