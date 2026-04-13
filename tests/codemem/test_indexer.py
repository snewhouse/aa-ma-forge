"""Tests for codemem.indexer — Task 1.5 (file discovery + indexer driver)."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from codemem.indexer import (
    BuildStats,
    build_index,
    discover_files,
)
from codemem.storage import db


def _init_git_repo(root: Path) -> None:
    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
    subprocess.run(
        ["git", "-C", str(root), "config", "user.email", "test@codemem.local"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(root), "config", "user.name", "Tester"], check=True
    )


def _git_add_commit(root: Path, msg: str = "add") -> None:
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(root), "commit", "-qm", msg, "--allow-empty"], check=True
    )


@pytest.fixture
def tiny_repo(tmp_path: Path) -> Path:
    """Git repo with a mix of tracked + ignored Python and TypeScript files."""
    _init_git_repo(tmp_path)
    (tmp_path / ".gitignore").write_text(".codemem/\n*.pyc\nignored_dir/\n")
    (tmp_path / "app.py").write_text(
        "def greet(name):\n"
        "    return f'hi {name}'\n"
        "\n"
        "def main():\n"
        "    return greet('world')\n"
    )
    (tmp_path / "lib.ts").write_text(
        "export function double(n: number): number {\n"
        "    return n * 2;\n"
        "}\n"
        "\n"
        "export class Counter {\n"
        "    inc() { return 1; }\n"
        "}\n"
    )
    (tmp_path / "README.md").write_text("# tiny\n")
    # Gitignored:
    (tmp_path / "ignored_dir").mkdir()
    (tmp_path / "ignored_dir" / "secret.py").write_text("def secret(): return 1\n")
    (tmp_path / "build.pyc").write_text("binary garbage")
    _git_add_commit(tmp_path)
    return tmp_path


# ---------------------------------------------------------------------
# discover_files
# ---------------------------------------------------------------------

class TestDiscoverFiles:
    def test_returns_tracked_indexable_files(self, tiny_repo):
        # discover_files returns only files with parseable extensions —
        # .py and ast-grep-supported langs. Markdown is tracked but not
        # indexable.
        files = discover_files(tiny_repo)
        names = sorted(f.name for f in files)
        assert "app.py" in names
        assert "lib.ts" in names
        assert "README.md" not in names

    def test_respects_gitignore(self, tiny_repo):
        files = discover_files(tiny_repo)
        paths = [f.as_posix() for f in files]
        assert not any("ignored_dir" in p for p in paths), paths
        assert not any(p.endswith(".pyc") for p in paths), paths

    def test_returns_absolute_paths(self, tiny_repo):
        files = discover_files(tiny_repo)
        assert all(f.is_absolute() for f in files), files

    def test_non_git_directory_falls_back_to_walk(self, tmp_path):
        # No git init. Should still discover files via walk.
        (tmp_path / "a.py").write_text("def x(): pass\n")
        (tmp_path / "b.ts").write_text("function y() {}\n")
        files = discover_files(tmp_path)
        names = {f.name for f in files}
        assert {"a.py", "b.ts"}.issubset(names)


# ---------------------------------------------------------------------
# build_index — end-to-end
# ---------------------------------------------------------------------

class TestBuildIndex:
    def test_stats_shape(self, tiny_repo, tmp_path):
        db_path = tmp_path / ".codemem" / "index.db"
        stats = build_index(tiny_repo, db_path, package=".")
        assert isinstance(stats, BuildStats)
        assert stats.files_indexed >= 2  # app.py + lib.ts at minimum

    def test_creates_db_and_applies_schema(self, tiny_repo, tmp_path):
        db_path = tmp_path / ".codemem" / "index.db"
        build_index(tiny_repo, db_path, package=".")
        assert db_path.exists()
        with db.connect(db_path, read_only=True) as conn:
            assert db.is_codemem_db(conn)
            # user_version should be at baseline
            assert conn.execute("PRAGMA user_version").fetchone()[0] == 1

    def test_inserts_files_rows(self, tiny_repo, tmp_path):
        db_path = tmp_path / ".codemem" / "index.db"
        build_index(tiny_repo, db_path, package=".")
        with db.connect(db_path, read_only=True) as conn:
            langs = {row[0] for row in conn.execute("SELECT lang FROM files")}
            assert "python" in langs
            assert "typescript" in langs
            # Gitignored files absent
            paths = [row[0] for row in conn.execute("SELECT path FROM files")]
            assert not any("ignored_dir" in p for p in paths)

    def test_inserts_python_symbols(self, tiny_repo, tmp_path):
        db_path = tmp_path / ".codemem" / "index.db"
        build_index(tiny_repo, db_path, package=".")
        with db.connect(db_path, read_only=True) as conn:
            names = {row[0] for row in conn.execute(
                "SELECT name FROM symbols WHERE kind IN ('function','method','class')"
            )}
            assert {"greet", "main"}.issubset(names)

    def test_inserts_typescript_symbols(self, tiny_repo, tmp_path):
        # skip if sg binary unavailable
        if shutil.which("sg") is None:
            pytest.skip("ast-grep not on PATH")
        db_path = tmp_path / ".codemem" / "index.db"
        build_index(tiny_repo, db_path, package=".")
        with db.connect(db_path, read_only=True) as conn:
            names = {row[0] for row in conn.execute("SELECT name FROM symbols")}
            assert {"double", "Counter", "inc"}.issubset(names)

    def test_parent_id_resolved_for_methods(self, tiny_repo, tmp_path):
        if shutil.which("sg") is None:
            pytest.skip("ast-grep not on PATH")
        db_path = tmp_path / ".codemem" / "index.db"
        build_index(tiny_repo, db_path, package=".")
        with db.connect(db_path, read_only=True) as conn:
            row = conn.execute(
                "SELECT s.parent_id, p.name "
                "FROM symbols s JOIN symbols p ON p.id = s.parent_id "
                "WHERE s.kind = 'method' AND s.name = 'inc'"
            ).fetchone()
            assert row is not None
            assert row[1] == "Counter"  # parent is the class

    def test_integrity_check_passes_after_build(self, tiny_repo, tmp_path):
        db_path = tmp_path / ".codemem" / "index.db"
        build_index(tiny_repo, db_path, package=".")
        with db.connect(db_path, read_only=True) as conn:
            result = conn.execute("PRAGMA integrity_check").fetchall()
            assert result == [("ok",)]

    def test_fk_check_passes(self, tiny_repo, tmp_path):
        # AC: "integrity check post-insert" — using foreign_key_check as
        # the more specific form for FK validation.
        db_path = tmp_path / ".codemem" / "index.db"
        build_index(tiny_repo, db_path, package=".")
        with db.connect(db_path, read_only=False) as conn:
            violations = conn.execute("PRAGMA foreign_key_check").fetchall()
            assert violations == [], violations

    def test_intra_file_edges_persisted(self, tiny_repo, tmp_path):
        db_path = tmp_path / ".codemem" / "index.db"
        build_index(tiny_repo, db_path, package=".")
        with db.connect(db_path, read_only=True) as conn:
            # main() calls greet() — should persist as a call edge
            rows = conn.execute(
                "SELECT src.name, dst.name "
                "FROM edges e "
                "JOIN symbols src ON src.id = e.src_symbol_id "
                "JOIN symbols dst ON dst.id = e.dst_symbol_id "
                "WHERE e.kind = 'call'"
            ).fetchall()
            assert ("main", "greet") in rows

    def test_idempotent_rebuild(self, tiny_repo, tmp_path):
        db_path = tmp_path / ".codemem" / "index.db"
        build_index(tiny_repo, db_path, package=".")
        with db.connect(db_path, read_only=True) as conn:
            before_files = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
            before_syms = conn.execute("SELECT COUNT(*) FROM symbols").fetchone()[0]

        build_index(tiny_repo, db_path, package=".")
        with db.connect(db_path, read_only=True) as conn:
            after_files = conn.execute("SELECT COUNT(*) FROM files").fetchone()[0]
            after_syms = conn.execute("SELECT COUNT(*) FROM symbols").fetchone()[0]

        # Same content → same counts (idempotent — no duplicates).
        assert after_files == before_files
        assert after_syms == before_syms

    def test_unparseable_source_does_not_crash(self, tmp_path):
        _init_git_repo(tmp_path)
        (tmp_path / ".gitignore").write_text(".codemem/\n")
        (tmp_path / "broken.py").write_text("def ::: broken\n")
        _git_add_commit(tmp_path)
        db_path = tmp_path / ".codemem" / "index.db"
        # Should not raise — empty ParseResult is tolerated.
        stats = build_index(tmp_path, db_path, package=".")
        assert stats.files_indexed >= 1
        with db.connect(db_path, read_only=True) as conn:
            # file row exists, just no symbols for it
            paths = [r[0] for r in conn.execute("SELECT path FROM files")]
            assert any("broken.py" in p for p in paths)
