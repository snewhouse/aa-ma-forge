"""Tests for codemem v1 → v2 schema migration (M3 Task 3.8).

Covers acceptance criteria from codemem-tasks.md Task 3.8:
- `schema.sql` + migration framework adds tables `commits`, `ownership`,
  `co_change_pairs` via `PRAGMA user_version` bump to 2.
- M2 introduces no schema changes; user_version stays at 1 through M2 —
  i.e. a fresh apply_schema() still yields v1.
- FKs and cascades per M1 contract.
- Migration from v1 → v2 tested round-trip (apply v1 → migrate → verify).

Scope note: adding a supporting `commit_files` junction table alongside
the 3 tables named in the plan, because `hot_spots()`, `co_changes()`,
and `symbol_history()` all need to know which files each commit touched,
and storing that as a proper junction table is idiomatic SQL (vs. a
denormalized JSON blob on `commits`). The 3 named tables (commits,
ownership, co_change_pairs) remain the public v2 surface.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from codemem.storage import apply_schema, connect, migrate, transaction


@pytest.fixture
def v1_db(tmp_path: Path):
    """Fresh DB at v1 (apply_schema, no migrate call)."""
    db_path = tmp_path / "test.db"
    conn = connect(db_path)
    apply_schema(conn)
    yield conn
    conn.close()


@pytest.fixture
def v2_db(tmp_path: Path):
    """DB migrated to v2 (apply_schema → migrate)."""
    db_path = tmp_path / "test.db"
    conn = connect(db_path)
    apply_schema(conn)
    migrate(conn)
    yield conn
    conn.close()


# ---------------------------------------------------------------------------
# Schema version progression
# ---------------------------------------------------------------------------


class TestVersionProgression:
    def test_fresh_apply_schema_stays_at_v1(self, v1_db: sqlite3.Connection) -> None:
        """apply_schema alone must leave user_version=1 (M1/M2 baseline)."""
        cur = v1_db.execute("PRAGMA user_version")
        assert cur.fetchone()[0] == 1

    def test_migrate_bumps_to_v2(self, v2_db: sqlite3.Connection) -> None:
        """migrate() must advance user_version to 2."""
        cur = v2_db.execute("PRAGMA user_version")
        assert cur.fetchone()[0] == 2

    def test_migrate_idempotent_at_v2(self, v2_db: sqlite3.Connection) -> None:
        """Re-running migrate on already-v2 DB is a no-op."""
        version = migrate(v2_db)
        assert version == 2
        cur = v2_db.execute("PRAGMA user_version")
        assert cur.fetchone()[0] == 2


# ---------------------------------------------------------------------------
# V2 tables present
# ---------------------------------------------------------------------------


class TestV2Tables:
    def test_commits_table_exists(self, v2_db: sqlite3.Connection) -> None:
        cur = v2_db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='commits'"
        )
        assert cur.fetchone() is not None

    def test_ownership_table_exists(self, v2_db: sqlite3.Connection) -> None:
        cur = v2_db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='ownership'"
        )
        assert cur.fetchone() is not None

    def test_co_change_pairs_table_exists(self, v2_db: sqlite3.Connection) -> None:
        cur = v2_db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name='co_change_pairs'"
        )
        assert cur.fetchone() is not None

    def test_commit_files_junction_exists(self, v2_db: sqlite3.Connection) -> None:
        """Supporting junction table for commit↔file many-to-many."""
        cur = v2_db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='commit_files'"
        )
        assert cur.fetchone() is not None

    def test_v2_tables_absent_from_v1(self, v1_db: sqlite3.Connection) -> None:
        """M2 ends at v1 — these tables MUST NOT exist before migrate()."""
        cur = v1_db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name IN ('commits','ownership','co_change_pairs','commit_files')"
        )
        assert cur.fetchall() == []


# ---------------------------------------------------------------------------
# Commits table shape + constraints
# ---------------------------------------------------------------------------


class TestCommitsSchema:
    def test_commits_columns(self, v2_db: sqlite3.Connection) -> None:
        cur = v2_db.execute("PRAGMA table_info(commits)")
        cols = {row[1]: row for row in cur.fetchall()}
        # Expected columns per Task 3.1 AC: sha (PK), author_email, author_time, message
        assert "sha" in cols
        assert "author_email" in cols
        assert "author_time" in cols
        assert "message" in cols
        # sha is primary key
        assert cols["sha"][5] == 1  # pk flag

    def test_commits_insert_and_readback(self, v2_db: sqlite3.Connection) -> None:
        with transaction(v2_db):
            v2_db.execute(
                "INSERT INTO commits (sha, author_email, author_time, message) "
                "VALUES (?, ?, ?, ?)",
                ("abc123", "stephen.j.newhouse@gmail.com", 1700000000, "feat: test"),
            )
        cur = v2_db.execute("SELECT author_email, author_time, message FROM commits WHERE sha=?", ("abc123",))
        row = cur.fetchone()
        assert row == ("stephen.j.newhouse@gmail.com", 1700000000, "feat: test")

    def test_commits_sha_is_unique(self, v2_db: sqlite3.Connection) -> None:
        v2_db.execute(
            "INSERT INTO commits (sha, author_email, author_time, message) "
            "VALUES (?, ?, ?, ?)",
            ("dup", "a@b.c", 1, "first"),
        )
        with pytest.raises(sqlite3.IntegrityError):
            v2_db.execute(
                "INSERT INTO commits (sha, author_email, author_time, message) "
                "VALUES (?, ?, ?, ?)",
                ("dup", "a@b.c", 2, "second"),
            )

    def test_idx_commits_author_time_exists(self, v2_db: sqlite3.Connection) -> None:
        """Index for time-range queries (hot_spots 90-day window)."""
        cur = v2_db.execute(
            "SELECT name FROM sqlite_master WHERE type='index' "
            "AND name='idx_commits_author_time'"
        )
        assert cur.fetchone() is not None


# ---------------------------------------------------------------------------
# commit_files junction + cascade
# ---------------------------------------------------------------------------


class TestCommitFilesSchema:
    def test_commit_files_columns(self, v2_db: sqlite3.Connection) -> None:
        cur = v2_db.execute("PRAGMA table_info(commit_files)")
        cols = {row[1] for row in cur.fetchall()}
        assert {"commit_sha", "file_path"}.issubset(cols)

    def test_commit_files_cascade_on_commit_delete(self, v2_db: sqlite3.Connection) -> None:
        """Deleting a commit must cascade-delete its commit_files rows."""
        with transaction(v2_db):
            v2_db.execute(
                "INSERT INTO commits (sha, author_email, author_time, message) "
                "VALUES ('c1', 'a@b.c', 1, 'msg')"
            )
            v2_db.execute(
                "INSERT INTO commit_files (commit_sha, file_path) VALUES ('c1', 'a.py')"
            )
            v2_db.execute(
                "INSERT INTO commit_files (commit_sha, file_path) VALUES ('c1', 'b.py')"
            )
        cur = v2_db.execute("SELECT COUNT(*) FROM commit_files")
        assert cur.fetchone()[0] == 2
        with transaction(v2_db):
            v2_db.execute("DELETE FROM commits WHERE sha='c1'")
        cur = v2_db.execute("SELECT COUNT(*) FROM commit_files")
        assert cur.fetchone()[0] == 0

    def test_commit_files_pk_prevents_duplicates(self, v2_db: sqlite3.Connection) -> None:
        with transaction(v2_db):
            v2_db.execute(
                "INSERT INTO commits (sha, author_email, author_time, message) "
                "VALUES ('c1', 'a@b.c', 1, 'msg')"
            )
            v2_db.execute(
                "INSERT INTO commit_files (commit_sha, file_path) VALUES ('c1', 'a.py')"
            )
        with pytest.raises(sqlite3.IntegrityError):
            v2_db.execute(
                "INSERT INTO commit_files (commit_sha, file_path) VALUES ('c1', 'a.py')"
            )

    def test_idx_commit_files_path_exists(self, v2_db: sqlite3.Connection) -> None:
        """Index for reverse lookup: all commits touching a given file."""
        cur = v2_db.execute(
            "SELECT name FROM sqlite_master WHERE type='index' "
            "AND name='idx_commit_files_path'"
        )
        assert cur.fetchone() is not None


# ---------------------------------------------------------------------------
# Ownership table
# ---------------------------------------------------------------------------


class TestOwnershipSchema:
    def test_ownership_columns(self, v2_db: sqlite3.Connection) -> None:
        cur = v2_db.execute("PRAGMA table_info(ownership)")
        cols = {row[1] for row in cur.fetchall()}
        assert {
            "file_path",
            "author_email",
            "line_count",
            "percentage",
            "computed_at",
        }.issubset(cols)

    def test_ownership_insert_and_readback(self, v2_db: sqlite3.Connection) -> None:
        v2_db.execute(
            "INSERT INTO ownership (file_path, author_email, line_count, percentage, computed_at) "
            "VALUES (?, ?, ?, ?, ?)",
            ("src/aa_ma/__init__.py", "stephen.j.newhouse@gmail.com", 95, 95.0, 1700000000),
        )
        cur = v2_db.execute(
            "SELECT line_count, percentage FROM ownership "
            "WHERE file_path=? AND author_email=?",
            ("src/aa_ma/__init__.py", "stephen.j.newhouse@gmail.com"),
        )
        assert cur.fetchone() == (95, 95.0)

    def test_ownership_pk_prevents_same_author_twice(self, v2_db: sqlite3.Connection) -> None:
        v2_db.execute(
            "INSERT INTO ownership (file_path, author_email, line_count, percentage, computed_at) "
            "VALUES ('a.py', 'a@b.c', 10, 50.0, 1)"
        )
        with pytest.raises(sqlite3.IntegrityError):
            v2_db.execute(
                "INSERT INTO ownership (file_path, author_email, line_count, percentage, computed_at) "
                "VALUES ('a.py', 'a@b.c', 20, 75.0, 2)"
            )


# ---------------------------------------------------------------------------
# Co-change pairs
# ---------------------------------------------------------------------------


class TestCoChangePairsSchema:
    def test_co_change_pairs_columns(self, v2_db: sqlite3.Connection) -> None:
        cur = v2_db.execute("PRAGMA table_info(co_change_pairs)")
        cols = {row[1] for row in cur.fetchall()}
        assert {"file_a", "file_b", "count"}.issubset(cols)

    def test_co_change_pairs_enforces_a_lt_b(self, v2_db: sqlite3.Connection) -> None:
        """CHECK (file_a < file_b) prevents storing both (x,y) and (y,x)."""
        # Valid insert (a < b lex)
        v2_db.execute(
            "INSERT INTO co_change_pairs (file_a, file_b, count) VALUES ('a.py', 'b.py', 3)"
        )
        # Invalid: b > a violates CHECK
        with pytest.raises(sqlite3.IntegrityError):
            v2_db.execute(
                "INSERT INTO co_change_pairs (file_a, file_b, count) "
                "VALUES ('z.py', 'a.py', 5)"
            )
        # Invalid: equal files also violate
        with pytest.raises(sqlite3.IntegrityError):
            v2_db.execute(
                "INSERT INTO co_change_pairs (file_a, file_b, count) "
                "VALUES ('same.py', 'same.py', 1)"
            )

    def test_co_change_pairs_pk_prevents_duplicates(self, v2_db: sqlite3.Connection) -> None:
        v2_db.execute(
            "INSERT INTO co_change_pairs (file_a, file_b, count) VALUES ('a.py', 'b.py', 3)"
        )
        with pytest.raises(sqlite3.IntegrityError):
            v2_db.execute(
                "INSERT INTO co_change_pairs (file_a, file_b, count) VALUES ('a.py', 'b.py', 5)"
            )

    def test_co_change_pairs_last_commit_fk_set_null_on_delete(
        self, v2_db: sqlite3.Connection
    ) -> None:
        """When a cached commit is evicted, pair's last_commit becomes NULL (not cascade-delete)."""
        with transaction(v2_db):
            v2_db.execute(
                "INSERT INTO commits (sha, author_email, author_time, message) "
                "VALUES ('c1', 'a@b.c', 1, 'msg')"
            )
            v2_db.execute(
                "INSERT INTO co_change_pairs (file_a, file_b, count, last_commit) "
                "VALUES ('a.py', 'b.py', 3, 'c1')"
            )
        with transaction(v2_db):
            v2_db.execute("DELETE FROM commits WHERE sha='c1'")
        cur = v2_db.execute("SELECT last_commit, count FROM co_change_pairs")
        row = cur.fetchone()
        assert row[0] is None       # FK ON DELETE SET NULL
        assert row[1] == 3          # pair itself preserved


# ---------------------------------------------------------------------------
# V1 data preservation across migration
# ---------------------------------------------------------------------------


class TestRoundTripMigration:
    def test_v1_data_survives_v2_migration(self, tmp_path: Path) -> None:
        """Insert v1 rows → migrate to v2 → v1 rows still present with same values."""
        db_path = tmp_path / "roundtrip.db"
        conn = connect(db_path)
        try:
            apply_schema(conn)
            # Populate v1 tables
            with transaction(conn):
                conn.execute(
                    "INSERT INTO files (path, lang, last_indexed) "
                    "VALUES ('src/a.py', 'python', 1700000000)"
                )
                conn.execute(
                    "INSERT INTO symbols (file_id, scip_id, name, kind, line) "
                    "VALUES (1, 'scip-1', 'foo', 'function', 10)"
                )
                conn.execute(
                    "INSERT INTO symbols (file_id, scip_id, name, kind, line) "
                    "VALUES (1, 'scip-2', 'bar', 'function', 20)"
                )
                conn.execute(
                    "INSERT INTO edges (src_symbol_id, dst_symbol_id, kind) "
                    "VALUES (1, 2, 'call')"
                )
            # Migrate to v2
            version = migrate(conn)
            assert version == 2

            # V1 rows must still be intact
            cur = conn.execute("SELECT path, lang FROM files")
            assert cur.fetchone() == ("src/a.py", "python")
            cur = conn.execute("SELECT COUNT(*) FROM symbols")
            assert cur.fetchone()[0] == 2
            cur = conn.execute(
                "SELECT src_symbol_id, dst_symbol_id, kind FROM edges"
            )
            assert cur.fetchone() == (1, 2, "call")
        finally:
            conn.close()

    def test_integrity_check_after_migration(self, v2_db: sqlite3.Connection) -> None:
        cur = v2_db.execute("PRAGMA integrity_check")
        assert cur.fetchone()[0] == "ok"

    def test_foreign_key_check_after_migration(self, v2_db: sqlite3.Connection) -> None:
        cur = v2_db.execute("PRAGMA foreign_key_check")
        assert cur.fetchall() == []

    def test_current_schema_version_constant_is_2(self) -> None:
        """Python-side constant must track SQL user_version bump."""
        from codemem.storage import CURRENT_SCHEMA_VERSION

        assert CURRENT_SCHEMA_VERSION == 2
