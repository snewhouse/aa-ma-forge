"""Tests for codemem schema v3 ``file_edges`` (diagram-generation M1).

Covers: v2 -> v3 migration, the downgrade guard (a v3 DB opened by
v2-era code keeps user_version 3), partial-unique-index de-duplication,
ON DELETE CASCADE, import-edge persistence through ``build_index``, and
row-set idempotency through the INCREMENTAL path (``refresh_index``) —
the path where the ``files`` row survives an edit, so CASCADE never fires.
"""

from __future__ import annotations

import sqlite3
import subprocess
from pathlib import Path

import pytest

from codemem.incremental import refresh_index
from codemem.indexer import build_index
from codemem.storage import db
from codemem.storage.db import apply_schema, connect, ensure_schema, migrate


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(root), *args], check=True)


def _init_commit(root: Path) -> None:
    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
    _git(root, "config", "user.email", "t@x")
    _git(root, "config", "user.name", "T")
    _commit(root)


def _commit(root: Path) -> None:
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "c", "--allow-empty")


def _user_version(conn: sqlite3.Connection) -> int:
    return conn.execute("PRAGMA user_version").fetchone()[0]


def _file_edge_rows(db_path: Path) -> list[tuple]:
    with db.connect(db_path, read_only=True) as conn:
        return sorted(
            conn.execute(
                "SELECT s.path, d.path, fe.dst_unresolved, fe.kind "
                "FROM file_edges fe "
                "JOIN files s ON s.id = fe.src_file_id "
                "LEFT JOIN files d ON d.id = fe.dst_file_id"
            ).fetchall(),
            key=repr,
        )


@pytest.fixture
def v3_db(tmp_path: Path):
    conn = connect(tmp_path / "t.db")
    ensure_schema(conn)
    yield conn
    conn.close()


def _insert_file(conn: sqlite3.Connection, path: str) -> int:
    cur = conn.execute(
        "INSERT INTO files(path, lang, last_indexed) VALUES (?, 'python', 0)",
        (path,),
    )
    return cur.lastrowid


# ---------------------------------------------------------------------
# Schema version
# ---------------------------------------------------------------------

class TestVersion:
    def test_current_schema_version_is_3(self) -> None:
        assert db.CURRENT_SCHEMA_VERSION == 3

    def test_apply_schema_alone_still_v1(self, tmp_path: Path) -> None:
        conn = connect(tmp_path / "t.db")
        apply_schema(conn)
        assert _user_version(conn) == 1
        conn.close()

    def test_v2_db_migrates_forward_to_v3(self, tmp_path: Path) -> None:
        conn = connect(tmp_path / "t.db")
        apply_schema(conn)
        # Stop at v2: run only the v2 migration, as v2-era code did.
        for target, sql in db.MIGRATIONS:
            if target == 2:
                with conn:
                    conn.executescript(sql)
                    conn.execute(f"PRAGMA user_version = {target}")
        assert _user_version(conn) == 2
        assert migrate(conn) == db.CURRENT_SCHEMA_VERSION
        assert _user_version(conn) == db.CURRENT_SCHEMA_VERSION
        conn.close()

    def test_ensure_schema_fresh_lands_at_v3(self, v3_db) -> None:
        assert _user_version(v3_db) == db.CURRENT_SCHEMA_VERSION
        assert v3_db.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='file_edges'"
        ).fetchone()

    def test_file_edges_absent_before_migrate(self, tmp_path: Path) -> None:
        conn = connect(tmp_path / "t.db")
        apply_schema(conn)
        assert not conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='file_edges'"
        ).fetchone()
        conn.close()


class TestDowngradeGuard:
    def test_v3_db_opened_by_v2_code_keeps_v3(
        self, v3_db, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """AC6 — v2-era code (CURRENT_SCHEMA_VERSION 2, MIGRATIONS up to v2)
        calling ensure_schema() must not walk a v3 DB back to 2."""
        f = _insert_file(v3_db, "a.py")
        v3_db.execute(
            "INSERT INTO file_edges(src_file_id, dst_unresolved, kind) "
            "VALUES (?, 'os', 'import')",
            (f,),
        )
        v3_db.commit()
        newer = db.CURRENT_SCHEMA_VERSION
        monkeypatch.setattr(db, "CURRENT_SCHEMA_VERSION", 2)
        monkeypatch.setattr(db, "MIGRATIONS", [m for m in db.MIGRATIONS if m[0] <= 2])
        assert ensure_schema(v3_db) == newer
        assert _user_version(v3_db) == newer
        assert v3_db.execute("SELECT count(*) FROM file_edges").fetchone()[0] == 1

    def test_apply_schema_on_v3_db_keeps_v3(self, v3_db) -> None:
        apply_schema(v3_db)
        assert _user_version(v3_db) == db.CURRENT_SCHEMA_VERSION


# ---------------------------------------------------------------------
# Table constraints
# ---------------------------------------------------------------------

class TestConstraints:
    def test_resolved_edge_deduplicated(self, v3_db) -> None:
        a, b = _insert_file(v3_db, "a.py"), _insert_file(v3_db, "b.py")
        for _ in range(3):
            v3_db.execute(
                "INSERT OR IGNORE INTO file_edges(src_file_id, dst_file_id, kind) "
                "VALUES (?, ?, 'import')",
                (a, b),
            )
        assert v3_db.execute("SELECT count(*) FROM file_edges").fetchone()[0] == 1

    def test_unresolved_edge_deduplicated(self, v3_db) -> None:
        a = _insert_file(v3_db, "a.py")
        for _ in range(3):
            v3_db.execute(
                "INSERT OR IGNORE INTO file_edges(src_file_id, dst_unresolved, kind) "
                "VALUES (?, 'os', 'import')",
                (a,),
            )
        assert v3_db.execute("SELECT count(*) FROM file_edges").fetchone()[0] == 1

    def test_both_dst_null_rejected(self, v3_db) -> None:
        a = _insert_file(v3_db, "a.py")
        with pytest.raises(sqlite3.IntegrityError):
            v3_db.execute(
                "INSERT INTO file_edges(src_file_id, kind) VALUES (?, 'import')", (a,)
            )

    def test_foreign_keys_on_and_cascade(self, v3_db) -> None:
        """AC7 — deleting a files row removes its file_edges (src AND dst)."""
        assert v3_db.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        a, b = _insert_file(v3_db, "a.py"), _insert_file(v3_db, "b.py")
        v3_db.execute(
            "INSERT INTO file_edges(src_file_id, dst_file_id, kind) VALUES (?, ?, 'import')",
            (a, b),
        )
        v3_db.execute(
            "INSERT INTO file_edges(src_file_id, dst_file_id, kind) VALUES (?, ?, 'import')",
            (b, a),
        )
        v3_db.execute("DELETE FROM files WHERE id = ?", (b,))
        assert v3_db.execute("SELECT count(*) FROM file_edges").fetchone()[0] == 0


# ---------------------------------------------------------------------
# Persistence through the indexer + incremental refresh
# ---------------------------------------------------------------------

@pytest.fixture
def import_repo(tmp_path: Path) -> tuple[Path, Path]:
    (tmp_path / ".gitignore").write_text(".codemem/\n")
    (tmp_path / "a.py").write_text(
        "import os\nfrom b import helper\n\ndef caller():\n    return helper()\n"
    )
    (tmp_path / "b.py").write_text("def helper():\n    return 1\n")
    (tmp_path / "c.py").write_text("def other():\n    return 2\n")
    _init_commit(tmp_path)
    db_path = tmp_path / ".codemem" / "index.db"
    build_index(tmp_path, db_path, package=".")
    return tmp_path, db_path


class TestPersistence:
    def test_build_persists_import_edges(self, import_repo) -> None:
        _, db_path = import_repo
        assert _file_edge_rows(db_path) == sorted(
            [("a.py", "b.py", None, "import"), ("a.py", None, "os", "import")],
            key=repr,
        )
        with db.connect(db_path, read_only=True) as conn:
            assert _user_version(conn) == db.CURRENT_SCHEMA_VERSION

    def test_refresh_edit_in_place_is_idempotent(self, import_repo) -> None:
        """AC5 — edit a file (files row survives), refresh twice: row SET
        equals a clean build of the same content, and no stale rows."""
        root, db_path = import_repo
        refresh_index(root, db_path, package=".")  # establish last_sha
        (root / "a.py").write_text(
            "import os\nfrom b import helper\nfrom c import other\n\n"
            "def caller():\n    return helper() + other()\n"
        )
        _commit(root)
        stats = refresh_index(root, db_path, package=".")
        assert not stats.full_rebuild
        after = _file_edge_rows(db_path)
        refresh_index(root, db_path, package=".")
        assert _file_edge_rows(db_path) == after
        assert after == sorted(
            [
                ("a.py", "b.py", None, "import"),
                ("a.py", "c.py", None, "import"),
                ("a.py", None, "os", "import"),
            ],
            key=repr,
        )

    def test_refresh_shrinks_when_import_removed(self, import_repo) -> None:
        """AC5b — removing an import removes its edge; set shrinks."""
        root, db_path = import_repo
        refresh_index(root, db_path, package=".")
        before = _file_edge_rows(db_path)
        (root / "a.py").write_text("def caller():\n    return 1\n")
        _commit(root)
        stats = refresh_index(root, db_path, package=".")
        assert not stats.full_rebuild
        after = _file_edge_rows(db_path)
        assert set(after) < set(before)
        assert after == []


class TestRenderSeamOnRealIndex:
    """aa_ma.render.graph reads codemem's REAL schema (ADR-0014). The seam's own
    tests use hand-built fixtures; this pins it to what codemem actually writes,
    so a table/column rename fails here, not at lint time. (codemem tests may
    import aa_ma — the contract forbids only the reverse.)"""

    def test_readers_on_built_index(self, import_repo) -> None:
        from aa_ma.render.graph import GraphStatus, call_edges, import_edges, open_graph

        root, _ = import_repo
        h = open_graph(root)
        assert h.status is GraphStatus.OK, h.reason
        assert import_edges(h) == {("a.py", "b.py")}
        assert call_edges(h) == {("a.py", "b.py")}
        h.conn.close()
