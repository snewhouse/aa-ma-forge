"""Tests for codemem.mcp_tools.co_changes (M3 Task 3.3).

AC: files co-changing with input AND lacking import-graph edge to it;
threshold ≥3 commits; CHANGELOG.md/README.md excluded by default.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from codemem.storage import apply_schema, connect, migrate, transaction


def _add_commit_touching(conn, sha: str, files: list[str], at: int = 1700000000) -> None:
    conn.execute(
        "INSERT INTO commits (sha, author_email, author_time, message) "
        "VALUES (?, 'dev@x.y', ?, 'msg')",
        (sha, at),
    )
    for fp in files:
        conn.execute(
            "INSERT INTO commit_files (commit_sha, file_path) VALUES (?, ?)",
            (sha, fp),
        )


def _add_file_with_symbol(conn, path: str) -> int:
    """Add a file + one dummy function symbol. Return file_id."""
    conn.execute(
        "INSERT INTO files (path, lang, last_indexed) VALUES (?, 'python', 0)",
        (path,),
    )
    fid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.execute(
        "INSERT INTO symbols (file_id, scip_id, name, kind, line) "
        "VALUES (?, ?, 'fn', 'function', 1)",
        (fid, f"scip-{path}"),
    )
    return fid


@pytest.fixture
def populated_db(tmp_path: Path) -> Path:
    """Build a v2 DB where file X co-changes with Y (≥3 commits, no import)
    AND with Z (≥3 commits, but Z imports X so should be filtered)
    AND with CHANGELOG.md (≥3 commits, default-excluded).
    """
    db_path = tmp_path / "coch.db"
    conn = connect(db_path)
    apply_schema(conn)
    migrate(conn)
    with transaction(conn):
        _add_file_with_symbol(conn, "X.md")
        _add_file_with_symbol(conn, "Y.md")
        _add_file_with_symbol(conn, "Z.py")
        _add_file_with_symbol(conn, "CHANGELOG.md")
        _add_file_with_symbol(conn, "W.md")  # co-changes once only

        # Add import edge Z → X (so Z is linked, should be filtered)
        # symbols table: Z's symbol (id?) → X's symbol
        # We just inserted one symbol per file; rowids are 1..5 in order.
        # Look them up by scip_id to be safe.
        x_sym = conn.execute(
            "SELECT id FROM symbols WHERE scip_id = ?", ("scip-X.md",)
        ).fetchone()[0]
        z_sym = conn.execute(
            "SELECT id FROM symbols WHERE scip_id = ?", ("scip-Z.py",)
        ).fetchone()[0]
        conn.execute(
            "INSERT INTO edges (src_symbol_id, dst_symbol_id, kind) "
            "VALUES (?, ?, 'call')",
            (z_sym, x_sym),
        )

        # 3 commits: (X, Y, Z)
        _add_commit_touching(conn, "c1", ["X.md", "Y.md", "Z.py"], 1700000001)
        _add_commit_touching(conn, "c2", ["X.md", "Y.md", "Z.py"], 1700000002)
        _add_commit_touching(conn, "c3", ["X.md", "Y.md", "Z.py"], 1700000003)
        # 3 commits: (X, CHANGELOG)
        _add_commit_touching(conn, "c4", ["X.md", "CHANGELOG.md"], 1700000004)
        _add_commit_touching(conn, "c5", ["X.md", "CHANGELOG.md"], 1700000005)
        _add_commit_touching(conn, "c6", ["X.md", "CHANGELOG.md"], 1700000006)
        # 1 commit: (X, W) — below threshold
        _add_commit_touching(conn, "c7", ["X.md", "W.md"], 1700000007)

    conn.close()
    return db_path


class TestFunctionSurface:
    def test_importable(self) -> None:
        from codemem.mcp_tools import co_changes  # noqa: F401

    def test_callable(self) -> None:
        from codemem.mcp_tools import co_changes

        assert callable(co_changes)


class TestCoChangeLogic:
    def test_returns_coupled_file_y(self, populated_db: Path) -> None:
        """Y co-changes with X 3 times, no import edge → must appear."""
        from codemem.mcp_tools import co_changes

        result = co_changes(populated_db, "X.md")
        paths = [f["path"] for f in result["files"]]
        assert "Y.md" in paths
        y = next(f for f in result["files"] if f["path"] == "Y.md")
        assert y["count"] == 3

    def test_filters_linked_file_z(self, populated_db: Path) -> None:
        """Z co-changes 3 times but imports X → must be filtered."""
        from codemem.mcp_tools import co_changes

        result = co_changes(populated_db, "X.md")
        assert "Z.py" not in [f["path"] for f in result["files"]]

    def test_default_excludes_changelog(self, populated_db: Path) -> None:
        """CHANGELOG.md co-changes 3 times but is default-excluded."""
        from codemem.mcp_tools import co_changes

        result = co_changes(populated_db, "X.md")
        assert "CHANGELOG.md" not in [f["path"] for f in result["files"]]

    def test_below_threshold_omitted(self, populated_db: Path) -> None:
        """W co-changes only 1 time (default threshold 3) → omitted."""
        from codemem.mcp_tools import co_changes

        result = co_changes(populated_db, "X.md")
        assert "W.md" not in [f["path"] for f in result["files"]]

    def test_custom_threshold_surfaces_low_count_neighbours(
        self, populated_db: Path
    ) -> None:
        from codemem.mcp_tools import co_changes

        result = co_changes(populated_db, "X.md", threshold=1)
        # W.md is at 1 commit — now it should appear. Z still filtered (import).
        paths = [f["path"] for f in result["files"]]
        assert "W.md" in paths
        assert "Z.py" not in paths

    def test_custom_exclude_overrides_default(self, populated_db: Path) -> None:
        """Passing explicit ``exclude=()`` disables the default set so CHANGELOG
        becomes visible again (with import-graph filter still applied)."""
        from codemem.mcp_tools import co_changes

        result = co_changes(populated_db, "X.md", exclude=())
        assert "CHANGELOG.md" in [f["path"] for f in result["files"]]

    def test_ordering_desc_by_count_then_path(self, populated_db: Path) -> None:
        from codemem.mcp_tools import co_changes

        result = co_changes(populated_db, "X.md", threshold=1, exclude=())
        # Expected order:
        # - CHANGELOG (3), Y (3) — tied at 3, path ASC: CHANGELOG.md < Y.md
        # - W (1)
        paths = [f["path"] for f in result["files"]]
        assert paths == ["CHANGELOG.md", "Y.md", "W.md"]


class TestInvariants:
    def test_empty_db_empty_result(self, tmp_path: Path) -> None:
        from codemem.mcp_tools import co_changes

        db_path = tmp_path / "empty.db"
        conn = connect(db_path)
        apply_schema(conn)
        migrate(conn)
        conn.close()
        result = co_changes(db_path, "anything.md")
        assert result["files"] == []
        assert result["error"] is None

    def test_sanitization_rejects_injection(self, tmp_path: Path) -> None:
        """Adversarial input returns a structured error, not an exception."""
        from codemem.mcp_tools import co_changes

        db_path = tmp_path / "e.db"
        conn = connect(db_path)
        apply_schema(conn)
        migrate(conn)
        conn.close()
        result = co_changes(db_path, "$(rm -rf /tmp)")
        assert result["error"] is not None
        assert result["files"] == []

    def test_input_file_not_returned(self, populated_db: Path) -> None:
        """The input file must not appear in its own co-change list."""
        from codemem.mcp_tools import co_changes

        result = co_changes(populated_db, "X.md")
        assert "X.md" not in [f["path"] for f in result["files"]]
