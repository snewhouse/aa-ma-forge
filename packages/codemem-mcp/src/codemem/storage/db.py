"""
SQLite connection + schema management for codemem.

Single entry point: `connect(path, read_only=False)` returns a configured
connection with per-connection PRAGMAs applied (WAL + busy_timeout +
cache + mmap + foreign_keys). Schema creation and migrations are handled
by `apply_schema()` / `migrate()`.

Design notes (per Task 1.0 + Task 1.2):
- Read-only MCP connections use `mode=ro` URI and get the same per-conn
  PRAGMAs (foreign_keys is a no-op on read paths but harmless).
- Migration is forward-only via `PRAGMA user_version`.
- `application_id=0xC0DE3E33` marks codemem DBs (detectable via `sqlite3
  file cmd` or `PRAGMA application_id`).
- `dst_symbol_id OR dst_unresolved` CHECK lets unresolved imports be
  persisted; M1 Step 1.6 (cross-file edge resolution) can retry them.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from importlib.resources import files as _pkg_files
from pathlib import Path
from typing import Iterator

__all__ = [
    "APPLICATION_ID",
    "CURRENT_SCHEMA_VERSION",
    "MIGRATIONS",
    "apply_schema",
    "connect",
    "migrate",
]

APPLICATION_ID = 0x434D454D  # 'CMEM' ASCII = 1129209165 (within signed int32, per SQLite application_id spec)
CURRENT_SCHEMA_VERSION = 1  # M1 baseline; bumps to 2 in M3 Task 3.8

# Forward-only migrations. Each entry: (target_version, SQL_script_string).
# The initial schema (v1) is provided by schema.sql; migrations here start at v2.
MIGRATIONS: list[tuple[int, str]] = [
    # M3 Task 3.8 will append:
    # (2, """
    #   CREATE TABLE commits (...);
    #   CREATE TABLE ownership (...);
    #   CREATE TABLE co_change_pairs (...);
    # """)
]


def _apply_per_connection_pragmas(conn: sqlite3.Connection, *, read_only: bool) -> None:
    """Apply PRAGMAs that are per-connection (not persisted).

    busy_timeout, cache_size, mmap_size, foreign_keys, temp_store must be
    re-issued on every new connection. journal_mode, user_version,
    application_id are persisted at DB level and do NOT need re-issue.
    """
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.execute("PRAGMA cache_size = -65536")       # 64 MB per conn
    conn.execute("PRAGMA mmap_size = 268435456")     # 256 MB; up to DB size
    conn.execute("PRAGMA temp_store = MEMORY")
    if not read_only:
        # FK constraints only enforced on write paths; mode=ro ignores them.
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA synchronous = NORMAL")


def connect(path: str | Path, *, read_only: bool = False) -> sqlite3.Connection:
    """Open a codemem SQLite connection with PRAGMAs applied.

    Parameters
    ----------
    path : str | Path
        Path to the DB file (created if absent and not read_only).
    read_only : bool
        If True, open via `file:...?mode=ro` URI.
    """
    path = Path(path)
    if read_only:
        uri = f"file:{path}?mode=ro"
        conn = sqlite3.connect(uri, uri=True, timeout=5.0)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(path, timeout=5.0)
    _apply_per_connection_pragmas(conn, read_only=read_only)
    return conn


def _load_initial_schema_sql() -> str:
    """Return the contents of storage/schema.sql as a string.

    Uses importlib.resources so this works both in-source and from an
    installed wheel.
    """
    return (_pkg_files("codemem.storage") / "schema.sql").read_text(encoding="utf-8")


def apply_schema(conn: sqlite3.Connection) -> None:
    """Apply the initial schema (v1) to a fresh DB.

    Idempotent thanks to `CREATE TABLE IF NOT EXISTS` in schema.sql.
    Does NOT overwrite a DB with a higher user_version — callers should
    branch between apply_schema (fresh) and migrate (existing).
    """
    conn.executescript(_load_initial_schema_sql())


def _current_user_version(conn: sqlite3.Connection) -> int:
    cur = conn.execute("PRAGMA user_version")
    row = cur.fetchone()
    return int(row[0]) if row else 0


def migrate(conn: sqlite3.Connection) -> int:
    """Apply any pending MIGRATIONS. Returns the new user_version.

    Called after `connect()`. If DB is fresh (user_version = 0) the
    caller is expected to run `apply_schema()` first to reach v1; this
    function takes over from v1 upward.

    Each migration runs in its own transaction. If a migration fails,
    the transaction is rolled back and the user_version is unchanged.
    """
    current = _current_user_version(conn)
    for target, sql in MIGRATIONS:
        if target > current:
            with conn:  # auto-commit/rollback
                conn.executescript(sql)
                conn.execute(f"PRAGMA user_version = {target}")
            current = target
    return current


@contextmanager
def transaction(conn: sqlite3.Connection) -> Iterator[sqlite3.Connection]:
    """Context manager that wraps writes in a transaction.

    `with transaction(conn): ... executemany(...) ...` — on exception,
    rolls back. On normal exit, commits. Slightly clearer than the
    auto-commit `with conn:` form when mixing executemany + DDL.
    """
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise


def is_codemem_db(conn: sqlite3.Connection) -> bool:
    """True if the connected DB was initialized by codemem (application_id matches)."""
    cur = conn.execute("PRAGMA application_id")
    row = cur.fetchone()
    return int(row[0]) == APPLICATION_ID if row else False
