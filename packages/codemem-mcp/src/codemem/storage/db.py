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
- `application_id=0x434D454D` ('CMEM' ASCII) marks codemem DBs (detectable
  via `sqlite3 file cmd` or `PRAGMA application_id`). The plan-draft value
  `0xC0DE3E33` was corrected during Task 1.2 implementation — that form
  overflows SQLite's signed-int32 application_id column and silently
  stored 0.
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
CURRENT_SCHEMA_VERSION = 2  # M3 Task 3.8: git-mining tables (commits/ownership/co_change_pairs + commit_files junction)

# Forward-only migrations. Each entry: (target_version, SQL_script_string).
# The initial schema (v1) is provided by schema.sql; migrations here start at v2.
# Migration scripts MUST be idempotent-safe via `IF NOT EXISTS` so a crash
# between `executescript` and `PRAGMA user_version` does not wedge the DB.
_MIGRATION_V2_GIT_MINING = """
-- M3 Task 3.8: git intelligence tables.
-- Adds commits, commit_files (junction), ownership, co_change_pairs.
-- M2 introduced no schema changes — this is the first migration past v1.

-- Commits cache (last 500 by Task 3.1 policy; table has no size limit,
-- writer is responsible for eviction).
CREATE TABLE IF NOT EXISTS commits (
    sha           TEXT    PRIMARY KEY,
    author_email  TEXT    NOT NULL,
    author_time   INTEGER NOT NULL,   -- unix epoch, from `git log --pretty=%at`
    message       TEXT    NOT NULL    -- subject line only, from `%s`
);

CREATE INDEX IF NOT EXISTS idx_commits_author_time ON commits(author_time);

-- Junction: which files each cached commit touched.
-- Not listed in the plan's 3-table summary but required by hot_spots,
-- co_changes, symbol_history to avoid per-query git subprocess calls.
-- ON DELETE CASCADE so evicting a commit purges its file attribution.
CREATE TABLE IF NOT EXISTS commit_files (
    commit_sha  TEXT NOT NULL REFERENCES commits(sha) ON DELETE CASCADE,
    file_path   TEXT NOT NULL,              -- repo-relative; file may have been deleted since
    PRIMARY KEY (commit_sha, file_path)
);

CREATE INDEX IF NOT EXISTS idx_commit_files_path ON commit_files(file_path);

-- Per-file author percentages from `git blame --line-porcelain`.
-- Cache; Task 3.4 recomputes on demand or via `codemem refresh --owners`.
CREATE TABLE IF NOT EXISTS ownership (
    file_path    TEXT    NOT NULL,
    author_email TEXT    NOT NULL,
    line_count   INTEGER NOT NULL,
    percentage   REAL    NOT NULL,          -- 0.0 .. 100.0
    computed_at  INTEGER NOT NULL,          -- unix epoch — cache freshness key
    PRIMARY KEY (file_path, author_email)
);

CREATE INDEX IF NOT EXISTS idx_ownership_file ON ownership(file_path);

-- Pre-materialised co-change counts. Populated as a side-effect of commits
-- cache refresh; query-time co_changes() reads this directly. The CHECK
-- canonicalises ordering so (a,b) and (b,a) cannot both be stored.
CREATE TABLE IF NOT EXISTS co_change_pairs (
    file_a       TEXT    NOT NULL,
    file_b       TEXT    NOT NULL,
    count        INTEGER NOT NULL,
    last_commit  TEXT    REFERENCES commits(sha) ON DELETE SET NULL,
    PRIMARY KEY (file_a, file_b),
    CHECK (file_a < file_b)
);

CREATE INDEX IF NOT EXISTS idx_co_change_pairs_a ON co_change_pairs(file_a);
CREATE INDEX IF NOT EXISTS idx_co_change_pairs_b ON co_change_pairs(file_b);
"""

MIGRATIONS: list[tuple[int, str]] = [
    (2, _MIGRATION_V2_GIT_MINING),
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
