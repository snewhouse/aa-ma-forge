"""Tests for SQLite WAL hygiene (M2 Task 2.6).

AC: `PRAGMA wal_checkpoint(TRUNCATE)` is invoked after large indexer
batches; WAL file size stays bounded under repeated refreshes.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from codemem.incremental import refresh_index
from codemem.indexer import build_index


def _init_commit(root: Path) -> None:
    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
    subprocess.run(
        ["git", "-C", str(root), "config", "user.email", "t@x"], check=True
    )
    subprocess.run(["git", "-C", str(root), "config", "user.name", "T"], check=True)
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(root), "commit", "-qm", "i", "--allow-empty"], check=True
    )


@pytest.fixture
def active_repo(tmp_path: Path) -> tuple[Path, Path]:
    (tmp_path / ".gitignore").write_text(".codemem/\n")
    (tmp_path / "a.py").write_text(
        "\n".join(f"def f_{i}():\n    return {i}\n" for i in range(50))
    )
    _init_commit(tmp_path)
    db_path = tmp_path / ".codemem" / "index.db"
    build_index(tmp_path, db_path, package=".")
    return tmp_path, db_path


class TestWALCheckpoint:
    def test_wal_file_small_after_build(self, active_repo):
        _, db_path = active_repo
        wal_file = Path(str(db_path) + "-wal")
        if not wal_file.exists():
            # Checkpoint truncated the WAL so the file is gone — that's ideal.
            return
        # Post-TRUNCATE checkpoint the -wal should be empty or tiny.
        assert wal_file.stat().st_size < 4096, (
            f"WAL file not truncated: {wal_file.stat().st_size} bytes"
        )

    def test_wal_size_bounded_under_repeated_refresh(self, active_repo):
        """Run 10 refreshes with content edits between each; WAL
        size at the end must stay under a small cap."""
        root, db_path = active_repo
        wal_file = Path(str(db_path) + "-wal")

        for i in range(10):
            (root / "a.py").write_text(
                "\n".join(f"def f_{j}():\n    return {j + i}\n" for j in range(50))
            )
            refresh_index(root, db_path, package=".")

        # After 10 refreshes with truncate-checkpoints, the -wal file
        # should still be tiny (or absent).
        if wal_file.exists():
            assert wal_file.stat().st_size < 32 * 1024, (
                f"WAL unbounded: {wal_file.stat().st_size} bytes"
            )

    def test_main_db_file_grew_not_wal(self, active_repo):
        """Sanity: after a build, the primary .db file has size;
        the .db-wal file does not (checkpoint merged writes)."""
        _, db_path = active_repo
        assert db_path.stat().st_size > 0
        wal_file = Path(str(db_path) + "-wal")
        if wal_file.exists():
            assert wal_file.stat().st_size <= db_path.stat().st_size
