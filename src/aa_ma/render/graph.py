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

__all__ = ["GraphHandle", "GraphStatus", "call_edges", "file_langs", "import_edges", "open_graph"]

MIN_SCHEMA_VERSION = 3  # file_edges arrived in codemem schema v3
_REMEDY = "run `codemem build`"
_MAX_SHOWN = 3  # stale paths quoted in a reason


class GraphStatus(StrEnum):
    OK = "ok"
    MISSING = "missing"
    SCHEMA_TOO_OLD = "schema_too_old"
    STALE = "stale"  # readable, but behind the working tree


@dataclass(frozen=True)
class GraphHandle:
    status: GraphStatus
    reason: str | None
    conn: sqlite3.Connection | None  # read-only; the caller owns it and closes it


def open_graph(repo_root: Path) -> GraphHandle:
    """Open ``<repo_root>/.codemem/index.db`` read-only and classify it."""
    db = conn = None
    try:
        db = Path(repo_root) / ".codemem" / "index.db"
        if not db.is_file():
            return GraphHandle(GraphStatus.MISSING, f"no codemem index at {db}; {_REMEDY}", None)
        conn = sqlite3.connect(f"{db.resolve().as_uri()}?mode=ro", uri=True)
        conn.execute("PRAGMA trusted_schema = OFF")  # the file is data, not code
        version = conn.execute("PRAGMA user_version").fetchone()[0]
        if version < MIN_SCHEMA_VERSION:
            conn.close()
            return GraphHandle(
                GraphStatus.SCHEMA_TOO_OLD,
                f"codemem index is schema v{version}, need v{MIN_SCHEMA_VERSION}; {_REMEDY}",
                None,
            )
        stale = _stale_paths(conn, Path(repo_root))
    except Exception as exc:  # noqa: BLE001 — "never raises" is the contract (ADR-0014)
        if conn is not None:
            conn.close()
        return GraphHandle(
            GraphStatus.MISSING, f"codemem index at {db} is unreadable ({exc}); {_REMEDY}", None
        )
    if stale:
        shown = ", ".join(_printable(p) for p in stale[:_MAX_SHOWN]) + (", ..." if len(stale) > _MAX_SHOWN else "")
        return GraphHandle(
            GraphStatus.STALE,
            f"{len(stale)} file(s) changed since indexing ({shown}); {_REMEDY}",
            conn,
        )
    return GraphHandle(GraphStatus.OK, None, conn)


def _stale_paths(conn: sqlite3.Connection, repo_root: Path) -> list[str]:
    """Indexed paths that are newer on disk than recorded, gone, or unusable.

    Paths come from the DB, which is data, not trusted input: a NULL, absolute
    or ``..`` path is stale without touching the filesystem; a symlink leaving
    the tree is stale and never stat'd. Any OSError or non-integer mtime is
    stale too.
    """
    # ponytail: one stat per indexed file; cache per handle if M13 measures it hot.
    root = repo_root.resolve()
    stale: list[str] = []
    for path, mtime in conn.execute("SELECT path, mtime FROM files ORDER BY path"):
        try:
            rel = Path(path)
            if rel.is_absolute() or ".." in rel.parts:
                raise ValueError("outside repo")
            target = (root / rel).resolve()
            if not target.is_relative_to(root):
                raise ValueError("symlink leaves repo")
            if mtime is not None and int(target.stat().st_mtime) > int(mtime):
                stale.append(path)
        except (OSError, RuntimeError, TypeError, ValueError):
            stale.append(str(path))
    return stale


def _printable(path: str) -> str:
    """DB-sourced text is quoted into a human-facing reason; strip control chars."""
    return "".join(c if c.isprintable() else "?" for c in path)


def file_langs(h: GraphHandle) -> dict[str, str]:
    """``path -> lang`` for every indexed file (a file is a graph node iff it is here)."""
    if h.conn is None:
        return {}
    return dict(h.conn.execute("SELECT path, lang FROM files"))


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
