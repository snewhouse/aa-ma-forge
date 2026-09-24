"""aa_ma.render.graph — the read-only seam from aa_ma onto a codemem index
(diagram-generation M2, ADR-0014).

Fixture DBs are built with stdlib ``sqlite3`` ONLY. Importing codemem here to
build test data would make the suite break the very contract this milestone
adds (``aa-ma-never-imports-codemem``). The schema below is the minimum subset
the seam reads; it mirrors codemem's column names, not its full DDL.
"""

from __future__ import annotations

import configparser
import os
import sqlite3
from pathlib import Path

import pytest

from aa_ma.render.graph import GraphStatus, call_edges, import_edges, open_graph

ROOT = Path(__file__).resolve().parents[2]

_DDL = """
CREATE TABLE files (id INTEGER PRIMARY KEY, path TEXT UNIQUE, mtime INTEGER);  -- no NOT NULL: a hostile DB need not honour it
CREATE TABLE symbols (id INTEGER PRIMARY KEY, file_id INTEGER NOT NULL, name TEXT);
CREATE TABLE edges (src_symbol_id INTEGER, dst_symbol_id INTEGER,
                    dst_unresolved TEXT, kind TEXT);
"""
_DDL_V3 = """
CREATE TABLE file_edges (src_file_id INTEGER NOT NULL, dst_file_id INTEGER,
                         dst_unresolved TEXT, kind TEXT NOT NULL, line INTEGER);
"""


def _repo(tmp_path: Path, *, version: int = 3) -> Path:
    """Repo with a.py, b.py, c.py and an index at ``user_version = version``.

    a imports b (resolved) and os (unresolved); a.caller calls b.helper twice
    (a duplicate row, as the v1 edges table really stores) and a.local
    (same-file); b.helper calls c.other.
    """
    for name in ("a", "b", "c"):
        (tmp_path / f"{name}.py").write_text(f"# {name}\n")
    db = tmp_path / ".codemem" / "index.db"
    db.parent.mkdir()
    conn = sqlite3.connect(db)
    conn.executescript(_DDL + (_DDL_V3 if version >= 3 else ""))
    for fid, name in enumerate(("a", "b", "c"), start=1):
        mtime = int((tmp_path / f"{name}.py").stat().st_mtime)
        conn.execute("INSERT INTO files VALUES (?, ?, ?)", (fid, f"{name}.py", mtime))
    conn.executemany(
        "INSERT INTO symbols VALUES (?, ?, ?)",
        [(1, 1, "caller"), (2, 1, "local"), (3, 2, "helper"), (4, 3, "other")],
    )
    conn.executemany(
        "INSERT INTO edges VALUES (?, ?, ?, 'call')",
        [(1, 3, None), (1, 3, None), (1, 2, None), (3, 4, None), (1, None, "os.getcwd")],
    )
    if version >= 3:
        conn.executemany(
            "INSERT INTO file_edges VALUES (?, ?, ?, 'import', NULL)",
            [(1, 2, None), (1, None, "os")],
        )
    conn.execute(f"PRAGMA user_version = {version}")
    conn.commit()
    conn.close()
    return tmp_path


def _add_file_row(root: Path, path: str | None, mtime: int = 0) -> None:
    conn = sqlite3.connect(root / ".codemem" / "index.db")
    conn.execute("INSERT INTO files(path, mtime) VALUES (?, ?)", (path, mtime))
    conn.commit()
    conn.close()


def _touch_forward(path: Path, seconds: int = 10) -> None:
    st = path.stat()
    os.utime(path, (st.st_atime, st.st_mtime + seconds))


# ---------------------------------------------------------------------
# open_graph statuses
# ---------------------------------------------------------------------

class TestOpenGraph:
    def test_ok(self, tmp_path: Path) -> None:
        h = open_graph(_repo(tmp_path))
        assert h.status is GraphStatus.OK
        assert h.reason is None
        assert h.conn is not None

    def test_missing_names_codemem_build(self, tmp_path: Path) -> None:
        h = open_graph(tmp_path)
        assert h.status is GraphStatus.MISSING
        assert "codemem build" in h.reason
        assert h.conn is None

    def test_schema_too_old(self, tmp_path: Path) -> None:
        h = open_graph(_repo(tmp_path, version=2))
        assert h.status is GraphStatus.SCHEMA_TOO_OLD
        assert "codemem build" in h.reason
        assert h.conn is None

    def test_stale_after_touch(self, tmp_path: Path) -> None:
        root = _repo(tmp_path)
        _touch_forward(root / "b.py")
        h = open_graph(root)
        assert h.status is GraphStatus.STALE
        assert "b.py" in h.reason

    def test_stale_after_delete(self, tmp_path: Path) -> None:
        root = _repo(tmp_path)
        (root / "c.py").unlink()
        h = open_graph(root)
        assert h.status is GraphStatus.STALE
        assert "c.py" in h.reason

    def test_unreadable_db_never_raises(self, tmp_path: Path) -> None:
        db = tmp_path / ".codemem" / "index.db"
        db.parent.mkdir()
        db.write_bytes(b"not a sqlite database" * 64)
        h = open_graph(tmp_path)
        assert h.status is GraphStatus.MISSING
        assert h.reason
        assert h.conn is None

    def test_directory_replaced_by_file_is_stale_not_raised(self, tmp_path: Path) -> None:
        """NotADirectoryError (and any OSError) must become STALE, never escape."""
        root = _repo(tmp_path)
        _add_file_row(root, "pkg/x.py")
        (root / "pkg").write_text("now a file\n")
        h = open_graph(root)
        assert h.status is GraphStatus.STALE
        assert "pkg/x.py" in h.reason

    @pytest.mark.parametrize("hostile", ["/etc/passwd", "../outside.py", "a/../../outside.py"])
    def test_paths_outside_repo_are_stale_not_statted(
        self, tmp_path: Path, hostile: str
    ) -> None:
        root = tmp_path / "repo"
        root.mkdir()
        (tmp_path / "outside.py").write_text("# exists, but not in the repo\n")
        _repo(root)
        # Far-future mtime: if the path were stat'd it would look fresh, so
        # only confinement can make this STALE (L-023: no pass-for-wrong-reason).
        _add_file_row(root, hostile, mtime=2**40)
        h = open_graph(root)
        assert h.status is GraphStatus.STALE
        assert hostile in h.reason

    def test_null_path_is_stale_not_raised(self, tmp_path: Path) -> None:
        root = _repo(tmp_path)
        _add_file_row(root, None)
        h = open_graph(root)
        assert h.status is GraphStatus.STALE

    def test_connection_is_read_only(self, tmp_path: Path) -> None:
        h = open_graph(_repo(tmp_path))
        with pytest.raises(sqlite3.OperationalError):
            h.conn.execute("DELETE FROM files")

    def test_open_does_not_create_db(self, tmp_path: Path) -> None:
        open_graph(tmp_path)
        assert not (tmp_path / ".codemem").exists()


# ---------------------------------------------------------------------
# Readers
# ---------------------------------------------------------------------

class TestReaders:
    def test_import_edges_resolved_only(self, tmp_path: Path) -> None:
        h = open_graph(_repo(tmp_path))
        assert import_edges(h) == {("a.py", "b.py")}

    def test_call_edges_projected_to_files(self, tmp_path: Path) -> None:
        """Duplicate rows collapse; same-file and unresolved calls drop out."""
        h = open_graph(_repo(tmp_path))
        assert call_edges(h) == {("a.py", "b.py"), ("b.py", "c.py")}

    @pytest.mark.parametrize("version", [2])
    def test_readers_empty_on_non_ok_handle(self, tmp_path: Path, version: int) -> None:
        h = open_graph(_repo(tmp_path, version=version))
        assert import_edges(h) == set()
        assert call_edges(h) == set()

    def test_readers_work_on_stale_handle(self, tmp_path: Path) -> None:
        """STALE is advisory — the graph is still readable, just behind disk."""
        root = _repo(tmp_path)
        _touch_forward(root / "a.py")
        h = open_graph(root)
        assert h.status is GraphStatus.STALE
        assert import_edges(h) == {("a.py", "b.py")}


# ---------------------------------------------------------------------
# Import contract (AC4) — asserted by NAME, never by total
# ---------------------------------------------------------------------

def test_never_imports_codemem_contract_declared() -> None:
    cfg = configparser.ConfigParser()
    cfg.read(ROOT / ".importlinter")
    c = cfg["importlinter:contract:aa-ma-never-imports-codemem"]
    assert c["name"] == "aa_ma never imports codemem"
    assert c["type"] == "forbidden"
    assert c["source_modules"].split() == ["aa_ma"]
    assert c["forbidden_modules"].split() == ["codemem"]
