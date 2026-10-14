"""Read-only seam from aa_ma onto a codemem index (ADR-0014).

aa_ma reads codemem's SQLite file with stdlib ``sqlite3`` and never imports
codemem — the ``aa-ma-never-imports-codemem`` import-linter contract pins that,
so the coupling is the on-disk schema (``PRAGMA user_version >= 3``), not a
Python API. ``open_graph`` never raises: every failure is a ``GraphStatus``
plus a reason naming the remedy.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import sqlite3
import stat
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

__all__ = [
    "GraphHandle",
    "GraphStatus",
    "call_edges",
    "file_langs",
    "import_edges",
    "open_graph",
    "printable",
]

MIN_SCHEMA_VERSION = 3  # file_edges arrived in codemem schema v3
_REMEDY = "run `codemem build`"
_MAX_SHOWN = 3  # stale paths quoted in a reason


class GraphStatus(StrEnum):
    """Whether a codemem index can answer: usable, absent, too old or stale."""

    OK = "ok"
    MISSING = "missing"
    SCHEMA_TOO_OLD = "schema_too_old"
    STALE = "stale"  # readable, but behind the working tree


@dataclass(frozen=True)
class GraphHandle:
    """The result of :func:`open_graph`: a status, its reason, and the connection if any."""

    status: GraphStatus
    reason: str | None
    conn: sqlite3.Connection | None  # read-only; the caller owns it and closes it


def _unsafe_reason(db_dir: Path) -> str | None:
    """Why ``db_dir`` must not be opened, or None: twin of ``codemem.safety.check_db_path``.

    Repo-controlled (M15 §6.8): a linked target opened read-only still gets
    -wal/-shm beside it. aa_ma never imports codemem (ADR-0014), so the rule
    is repeated here; ``tests/codemem/test_safety_parity.py`` keeps the two
    in step.
    """
    if db_dir.is_symlink():
        return "is a symlink"
    try:
        linked = any(p.is_symlink() for p in db_dir.iterdir())
    except FileNotFoundError:
        return None  # absent: open_graph reports MISSING with the build remedy
    except OSError:
        return "cannot be listed"
    return "holds a symlink" if linked else None


def _trust_problem(conn: sqlite3.Connection, db_dir: Path) -> str | None:
    """Why the index must not be read, or None: twin of ``codemem.safety.is_trusted``.

    A committed or copied index would otherwise let DIAGRAM_VERIFIED vouch for
    a graph that is not the code's (M15 §6.8 re-run 2). A broken trust store
    (unreadable, not a private dir of this user, a record that is not a
    nonce) is named as such, never as "not built here" (SECURITY.md).
    ``tests/codemem/test_safety_parity.py`` keeps the two in step.
    """
    not_built = f"was not built by codemem here; {_REMEDY}"
    state = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    key = hashlib.sha256(os.fsencode(os.path.realpath(db_dir))).hexdigest()
    rec = Path(state) / "codemem" / "trust" / key
    try:
        st = rec.parent.lstat()
        private = (
            stat.S_ISDIR(st.st_mode)
            and st.st_uid == os.getuid()
            and not st.st_mode & 0o022
        )
        if not private:
            return f"cannot be checked: trust store {rec.parent} is not a private directory of this user"
        fd = os.open(rec, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        with os.fdopen(fd, "rb") as fh:
            nonce = fh.read(256).decode("ascii").strip()
    except FileNotFoundError:
        return not_built
    except (OSError, UnicodeDecodeError) as exc:
        return f"cannot be checked: trust store {rec.parent} unreadable ({type(exc).__name__})"
    try:
        row = conn.execute(
            "SELECT value FROM meta WHERE key = 'trust_nonce'"
        ).fetchone()
    except sqlite3.Error:
        return not_built
    if not nonce or row is None:
        return not_built
    # bytes: compare_digest raises TypeError on a non-ASCII str
    stored = str(row[0]).encode("utf-8", "surrogatepass")
    return None if hmac.compare_digest(stored, nonce.encode()) else not_built


def open_graph(repo_root: Path) -> GraphHandle:
    """Open ``<repo_root>/.codemem/index.db`` read-only and classify it."""
    db = conn = None
    try:
        db = Path(repo_root) / ".codemem" / "index.db"
        unsafe = _unsafe_reason(db.parent)
        if unsafe is not None:
            return GraphHandle(
                GraphStatus.MISSING, f"{db.parent} {unsafe}; refusing to open it", None
            )
        if not db.is_file():
            return GraphHandle(
                GraphStatus.MISSING, f"no codemem index at {db}; {_REMEDY}", None
            )
        conn = sqlite3.connect(f"{db.absolute().as_uri()}?mode=ro", uri=True)
        conn.execute("PRAGMA trusted_schema = OFF")  # the file is data, not code
        problem = _trust_problem(conn, db.parent)
        if problem is not None:
            conn.close()
            return GraphHandle(
                GraphStatus.MISSING, f"codemem index at {db} {problem}", None
            )
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
            GraphStatus.MISSING,
            f"codemem index at {db} is unreadable ({printable(str(exc))}); {_REMEDY}",
            None,
        )
    if stale:
        shown = ", ".join(printable(p) for p in stale[:_MAX_SHOWN]) + (
            ", ..." if len(stale) > _MAX_SHOWN else ""
        )
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


def printable(path: str) -> str:
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
