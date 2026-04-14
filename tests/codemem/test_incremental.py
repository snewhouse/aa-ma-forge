"""Tests for codemem.incremental — Task 2.2 (incremental refresh driver)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from codemem.incremental import RefreshStats, refresh_index
from codemem.indexer import build_index
from codemem.storage import db


def _init_commit(root: Path) -> str:
    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
    subprocess.run(
        ["git", "-C", str(root), "config", "user.email", "t@x"], check=True
    )
    subprocess.run(["git", "-C", str(root), "config", "user.name", "T"], check=True)
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(root), "commit", "-qm", "i", "--allow-empty"], check=True
    )
    return subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()


def _commit(root: Path, msg: str = "edit") -> str:
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(root), "commit", "-qm", msg, "--allow-empty"], check=True
    )
    return subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()


@pytest.fixture
def base_repo(tmp_path: Path) -> tuple[Path, Path]:
    """Git repo with 2 files, initially indexed."""
    (tmp_path / ".gitignore").write_text(".codemem/\n")
    (tmp_path / "a.py").write_text(
        "def helper():\n    return 1\n"
    )
    (tmp_path / "b.py").write_text(
        "def caller():\n    return 2\n"
    )
    _init_commit(tmp_path)
    db_path = tmp_path / ".codemem" / "index.db"
    build_index(tmp_path, db_path, package=".")
    return tmp_path, db_path


# ---------------------------------------------------------------------
# Stats & basic invariants
# ---------------------------------------------------------------------

class TestRefreshStatsShape:
    def test_refresh_returns_stats(self, base_repo):
        root, db_path = base_repo
        stats = refresh_index(root, db_path, package=".")
        assert isinstance(stats, RefreshStats)

    def test_no_changes_zero_dirty(self, base_repo):
        root, db_path = base_repo
        stats = refresh_index(root, db_path, package=".")
        assert stats.files_dirty == 0
        assert stats.symbols_added == 0
        assert stats.symbols_removed == 0
        assert stats.symbols_modified == 0


# ---------------------------------------------------------------------
# Common case: content edit
# ---------------------------------------------------------------------

class TestContentEdit:
    def test_edit_detected_and_reflected(self, base_repo):
        root, db_path = base_repo
        # Add a new function to a.py
        (root / "a.py").write_text(
            "def helper():\n    return 1\n"
            "def second():\n    return 2\n"
        )
        stats = refresh_index(root, db_path, package=".")
        assert stats.files_dirty == 1
        # New symbol is in the DB
        with db.connect(db_path, read_only=True) as conn:
            names = {n for (n,) in conn.execute("SELECT name FROM symbols")}
            assert "second" in names

    def test_removed_function_gone_from_db(self, base_repo):
        root, db_path = base_repo
        # Replace a.py — delete helper
        (root / "a.py").write_text("# nothing\n")
        refresh_index(root, db_path, package=".")
        with db.connect(db_path, read_only=True) as conn:
            names = {n for (n,) in conn.execute(
                "SELECT name FROM symbols WHERE name = 'helper'"
            )}
            assert names == set(), "helper should have been removed"


# ---------------------------------------------------------------------
# Git mv — symbol moved, not add+remove
# ---------------------------------------------------------------------

class TestGitMv:
    def test_rename_keeps_symbols_intact(self, base_repo):
        root, db_path = base_repo
        with db.connect(db_path, read_only=True) as conn:
            a_symbols_before = sorted(
                n for (n,) in conn.execute(
                    "SELECT name FROM symbols s JOIN files f ON s.file_id = f.id "
                    "WHERE f.path = 'a.py'"
                )
            )
        assert "helper" in a_symbols_before

        # git mv a.py → moved/a.py
        (root / "moved").mkdir()
        subprocess.run(
            ["git", "-C", str(root), "mv", "a.py", "moved/a.py"], check=True
        )
        refresh_index(root, db_path, package=".")

        with db.connect(db_path, read_only=True) as conn:
            # helper still exists, now under moved/a.py
            row = conn.execute(
                "SELECT f.path FROM symbols s JOIN files f ON s.file_id = f.id "
                "WHERE s.name = 'helper'"
            ).fetchone()
            assert row is not None
            assert row[0] == "moved/a.py"
            # Only ONE helper row — not added + removed separately
            count = conn.execute(
                "SELECT COUNT(*) FROM symbols WHERE name = 'helper'"
            ).fetchone()[0]
            assert count == 1


# ---------------------------------------------------------------------
# File deletion
# ---------------------------------------------------------------------

class TestFileDeletion:
    def test_deleted_file_removed_from_db(self, base_repo):
        root, db_path = base_repo
        (root / "b.py").unlink()
        refresh_index(root, db_path, package=".")
        with db.connect(db_path, read_only=True) as conn:
            paths = {p for (p,) in conn.execute("SELECT path FROM files")}
            assert "b.py" not in paths
            # caller() symbol should be gone via CASCADE
            names = {n for (n,) in conn.execute(
                "SELECT name FROM symbols WHERE name = 'caller'"
            )}
            assert names == set()


# ---------------------------------------------------------------------
# Git history rewrite — fallback to full rebuild
# ---------------------------------------------------------------------

class TestGitHistoryRewrite:
    def test_orphaned_last_sha_triggers_full_rebuild(self, base_repo):
        root, db_path = base_repo
        # Corrupt the stored last_sha to a non-existent commit
        last_sha_file = db_path.parent / "last_sha"
        last_sha_file.write_text("0000000000000000000000000000000000000000\n")

        # Add a new file so we can verify the rebuild picked it up
        (root / "c.py").write_text("def third(): return 3\n")
        _commit(root, "add c.py")

        stats = refresh_index(root, db_path, package=".")
        assert stats.full_rebuild is True
        with db.connect(db_path, read_only=True) as conn:
            names = {n for (n,) in conn.execute("SELECT name FROM symbols")}
            assert {"helper", "caller", "third"}.issubset(names)

    def test_missing_last_sha_triggers_full_rebuild(self, base_repo):
        root, db_path = base_repo
        last_sha_file = db_path.parent / "last_sha"
        if last_sha_file.exists():
            last_sha_file.unlink()

        stats = refresh_index(root, db_path, package=".")
        # Missing last_sha is the first-time-refresh case — full rebuild
        assert stats.full_rebuild is True


# ---------------------------------------------------------------------
# last_sha bookkeeping
# ---------------------------------------------------------------------

class TestLastShaBookkeeping:
    def test_last_sha_written_after_refresh(self, base_repo):
        root, db_path = base_repo
        refresh_index(root, db_path, package=".")
        last_sha_file = db_path.parent / "last_sha"
        assert last_sha_file.exists()
        current_head = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        assert last_sha_file.read_text().strip() == current_head


# ---------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------

class TestIdempotency:
    def test_repeat_refresh_no_change(self, base_repo):
        root, db_path = base_repo
        refresh_index(root, db_path, package=".")
        s2 = refresh_index(root, db_path, package=".")
        # Second refresh should be a clean no-op
        assert s2.files_dirty == 0
        assert s2.symbols_added == 0
        assert s2.symbols_removed == 0
        assert s2.symbols_modified == 0
