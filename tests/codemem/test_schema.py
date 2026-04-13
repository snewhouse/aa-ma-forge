"""Tests for codemem.storage schema + migrations (M1 Task 1.2).

Covers acceptance criteria from codemem-plan.md Step 1.2:
- Schema applies to fresh DB
- FK constraints enforced (INSERT on orphaned FK → IntegrityError)
- Integrity check passes
- user_version progression
- application_id marker round-trip
- PRAGMAs take effect per-connection
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from codemem.storage import (
    APPLICATION_ID,
    CURRENT_SCHEMA_VERSION,
    apply_schema,
    connect,
    is_codemem_db,
    migrate,
    transaction,
)


@pytest.fixture
def fresh_db(tmp_path: Path):
    """Create a fresh codemem DB at tmp_path/test.db and apply schema."""
    db_path = tmp_path / "test.db"
    conn = connect(db_path)
    apply_schema(conn)
    yield conn
    conn.close()


class TestSchemaApply:
    def test_application_id_set(self, fresh_db: sqlite3.Connection) -> None:
        """application_id marker identifies codemem DBs."""
        assert is_codemem_db(fresh_db)
        cur = fresh_db.execute("PRAGMA application_id")
        assert cur.fetchone()[0] == APPLICATION_ID

    def test_user_version_is_v1(self, fresh_db: sqlite3.Connection) -> None:
        """Fresh DB after apply_schema is at v1 (M1 baseline)."""
        cur = fresh_db.execute("PRAGMA user_version")
        assert cur.fetchone()[0] == CURRENT_SCHEMA_VERSION == 1

    def test_journal_mode_is_wal(self, fresh_db: sqlite3.Connection) -> None:
        cur = fresh_db.execute("PRAGMA journal_mode")
        assert cur.fetchone()[0].lower() == "wal"

    def test_tables_present(self, fresh_db: sqlite3.Connection) -> None:
        cur = fresh_db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        )
        names = {r[0] for r in cur.fetchall()}
        assert {"files", "symbols", "edges"}.issubset(names)

    def test_indexes_present(self, fresh_db: sqlite3.Connection) -> None:
        cur = fresh_db.execute(
            "SELECT name FROM sqlite_master WHERE type='index' ORDER BY name"
        )
        names = {r[0] for r in cur.fetchall()}
        for required in (
            "idx_edges_dst",
            "idx_edges_src",
            "idx_symbols_file_kind_name",
            "idx_symbols_name",
            "idx_files_lang",
        ):
            assert required in names, f"missing index: {required}"

    def test_integrity_check_passes(self, fresh_db: sqlite3.Connection) -> None:
        cur = fresh_db.execute("PRAGMA integrity_check")
        assert cur.fetchone()[0] == "ok"

    def test_apply_schema_is_idempotent(self, fresh_db: sqlite3.Connection) -> None:
        # Second apply must not error or duplicate objects.
        apply_schema(fresh_db)
        cur = fresh_db.execute("PRAGMA integrity_check")
        assert cur.fetchone()[0] == "ok"


class TestForeignKeys:
    def test_pragma_foreign_keys_enabled(self, fresh_db: sqlite3.Connection) -> None:
        cur = fresh_db.execute("PRAGMA foreign_keys")
        assert cur.fetchone()[0] == 1

    def test_orphaned_symbol_insert_raises(self, fresh_db: sqlite3.Connection) -> None:
        """Inserting a symbol with a non-existent file_id must fail on FK."""
        with pytest.raises(sqlite3.IntegrityError):
            fresh_db.execute(
                "INSERT INTO symbols (file_id, scip_id, name, kind, line) "
                "VALUES (999, 'x', 'x', 'function', 1)"
            )

    def test_file_delete_cascades_to_symbols(self, fresh_db: sqlite3.Connection) -> None:
        with transaction(fresh_db):
            fresh_db.execute(
                "INSERT INTO files (path, lang, last_indexed) VALUES ('a.py', 'python', 0)"
            )
            fresh_db.execute(
                "INSERT INTO symbols (file_id, scip_id, name, kind, line) "
                "VALUES (1, 'id1', 'foo', 'function', 1)"
            )
        cur = fresh_db.execute("SELECT COUNT(*) FROM symbols")
        assert cur.fetchone()[0] == 1
        with transaction(fresh_db):
            fresh_db.execute("DELETE FROM files WHERE id = 1")
        cur = fresh_db.execute("SELECT COUNT(*) FROM symbols")
        assert cur.fetchone()[0] == 0, "ON DELETE CASCADE failed"

    def test_symbol_delete_cascades_to_edges(self, fresh_db: sqlite3.Connection) -> None:
        with transaction(fresh_db):
            fresh_db.execute(
                "INSERT INTO files (path, lang, last_indexed) VALUES ('a.py', 'python', 0)"
            )
            fresh_db.execute(
                "INSERT INTO symbols (file_id, scip_id, name, kind, line) "
                "VALUES (1, 's1', 'a', 'function', 1), "
                "       (1, 's2', 'b', 'function', 2)"
            )
            fresh_db.execute(
                "INSERT INTO edges (src_symbol_id, dst_symbol_id, kind) VALUES (1, 2, 'call')"
            )
        cur = fresh_db.execute("SELECT COUNT(*) FROM edges")
        assert cur.fetchone()[0] == 1
        with transaction(fresh_db):
            fresh_db.execute("DELETE FROM symbols WHERE id = 2")
        cur = fresh_db.execute("SELECT COUNT(*) FROM edges")
        assert cur.fetchone()[0] == 0


class TestEdgesCheck:
    def test_edges_require_dst_or_unresolved(self, fresh_db: sqlite3.Connection) -> None:
        """CHECK constraint: edge must have either dst_symbol_id OR dst_unresolved."""
        with transaction(fresh_db):
            fresh_db.execute(
                "INSERT INTO files (path, lang, last_indexed) VALUES ('a.py', 'python', 0)"
            )
            fresh_db.execute(
                "INSERT INTO symbols (file_id, scip_id, name, kind, line) "
                "VALUES (1, 's1', 'a', 'function', 1)"
            )
        with pytest.raises(sqlite3.IntegrityError):
            fresh_db.execute(
                "INSERT INTO edges (src_symbol_id, kind) VALUES (1, 'call')"
            )

    def test_unresolved_edge_persists(self, fresh_db: sqlite3.Connection) -> None:
        """An edge to an un-indexed symbol (e.g. stdlib import) must round-trip."""
        with transaction(fresh_db):
            fresh_db.execute(
                "INSERT INTO files (path, lang, last_indexed) VALUES ('a.py', 'python', 0)"
            )
            fresh_db.execute(
                "INSERT INTO symbols (file_id, scip_id, name, kind, line) "
                "VALUES (1, 's1', 'a', 'function', 1)"
            )
            fresh_db.execute(
                "INSERT INTO edges (src_symbol_id, dst_symbol_id, dst_unresolved, kind) "
                "VALUES (1, NULL, 'requests.get', 'call')"
            )
        cur = fresh_db.execute(
            "SELECT dst_unresolved FROM edges WHERE src_symbol_id = 1"
        )
        assert cur.fetchone()[0] == "requests.get"


class TestMigrate:
    def test_migrate_noop_at_current_version(self, fresh_db: sqlite3.Connection) -> None:
        """With no migrations defined past v1, migrate() is a no-op."""
        version = migrate(fresh_db)
        assert version == CURRENT_SCHEMA_VERSION


class TestCanonicalCTEExplainPlan:
    """Verify canonical who_calls CTE uses indexes (no table scan).

    Acceptance criterion from plan Step 1.2 and §M1: explain-plan on
    canonical CTE must use indexes only.
    """

    def test_who_calls_cte_uses_idx_edges_dst(self, fresh_db: sqlite3.Connection) -> None:
        query = """
        WITH RECURSIVE callers(sid, depth, path) AS (
            SELECT src_symbol_id, 1, '|' || src_symbol_id || '|'
              FROM edges WHERE dst_symbol_id = ? AND kind='call'
            UNION
            SELECT e.src_symbol_id, c.depth+1, c.path || e.src_symbol_id || '|'
              FROM edges e JOIN callers c ON e.dst_symbol_id = c.sid
             WHERE c.depth < ?
               AND c.path NOT LIKE '%|' || e.src_symbol_id || '|%'
        )
        SELECT DISTINCT sid FROM callers;
        """
        cur = fresh_db.execute(f"EXPLAIN QUERY PLAN {query}", (1, 3))
        plan = "\n".join(row[3] for row in cur.fetchall())
        # Must reference our covering index on edges(dst_symbol_id, ...)
        assert "idx_edges_dst" in plan, f"CTE not using idx_edges_dst:\n{plan}"


class TestReadOnlyConnection:
    def test_read_only_connect_cannot_write(self, tmp_path: Path) -> None:
        # Create & populate with a writable conn first
        db_path = tmp_path / "ro.db"
        w = connect(db_path)
        apply_schema(w)
        w.execute(
            "INSERT INTO files (path, lang, last_indexed) VALUES ('a.py', 'python', 0)"
        )
        w.commit()
        w.close()

        r = connect(db_path, read_only=True)
        try:
            with pytest.raises(sqlite3.OperationalError):
                r.execute(
                    "INSERT INTO files (path, lang, last_indexed) VALUES ('b.py', 'python', 0)"
                )
        finally:
            r.close()
