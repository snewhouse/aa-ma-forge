"""Tests for codemem.mcp_tools.symbol_history (M3 Task 3.5).

AC: ``git log -L:symbol:file`` returns first-seen, last-touched,
change count, authors; per-file when symbol exists in multiple files.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

from codemem.storage import apply_schema, connect, migrate


def _commit(root: Path, msg: str, at: int, author: str | None = None) -> None:
    env = {
        **os.environ,
        "GIT_AUTHOR_DATE": f"@{at} +0000",
        "GIT_COMMITTER_DATE": f"@{at} +0000",
    }
    if author:
        env["GIT_AUTHOR_NAME"] = author.split("@")[0]
        env["GIT_AUTHOR_EMAIL"] = author
        env["GIT_COMMITTER_NAME"] = author.split("@")[0]
        env["GIT_COMMITTER_EMAIL"] = author
    subprocess.run(
        ["git", "-C", str(root), "commit", "-qm", msg],
        check=True, env=env,
    )


@pytest.fixture
def git_repo(tmp_path: Path) -> tuple[Path, Path]:
    """Repo with function foo in a.py evolved across 3 commits, also defined in b.py."""
    root = tmp_path / "r"
    root.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
    subprocess.run(
        ["git", "-C", str(root), "config", "user.email", "dev@codemem.local"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(root), "config", "user.name", "dev"], check=True
    )
    # v1 of foo in a.py (introducing commit)
    (root / "a.py").write_text("def foo():\n    return 1\n")
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    _commit(root, "introduce foo in a.py", 1700000001)
    # v2 — second author touches foo
    (root / "a.py").write_text("def foo():\n    return 2  # bumped\n")
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    _commit(root, "bump foo return to 2", 1700000002, author="other@codemem.local")
    # v3 — original author touches foo again
    (root / "a.py").write_text("def foo():\n    return 42\n")
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    _commit(root, "set foo to 42", 1700000003)
    # Introduce foo in b.py too (separate file)
    (root / "b.py").write_text("def foo():\n    return 'b'\n")
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    _commit(root, "add foo in b.py", 1700000004)

    db_path = tmp_path / "hist.db"
    conn = connect(db_path)
    apply_schema(conn)
    migrate(conn)
    # Register files + symbols so symbol_history can find target files by name.
    conn.execute(
        "INSERT INTO files (path, lang, last_indexed) VALUES ('a.py', 'python', 0)"
    )
    conn.execute(
        "INSERT INTO files (path, lang, last_indexed) VALUES ('b.py', 'python', 0)"
    )
    conn.execute(
        "INSERT INTO symbols (file_id, scip_id, name, kind, line) "
        "VALUES (1, 'scip-a-foo', 'foo', 'function', 1)"
    )
    conn.execute(
        "INSERT INTO symbols (file_id, scip_id, name, kind, line) "
        "VALUES (2, 'scip-b-foo', 'foo', 'function', 1)"
    )
    conn.commit()
    conn.close()
    return db_path, root


class TestFunctionSurface:
    def test_importable(self) -> None:
        from codemem.mcp_tools import symbol_history  # noqa: F401

    def test_callable(self) -> None:
        from codemem.mcp_tools import symbol_history

        assert callable(symbol_history)


class TestBasic:
    def test_single_file_history(self, git_repo) -> None:
        from codemem.mcp_tools import symbol_history

        db_path, repo_root = git_repo
        result = symbol_history(db_path, "foo", file_path="a.py", repo_root=repo_root)
        assert result["error"] is None
        assert len(result["files"]) == 1
        fh = result["files"][0]
        assert fh["file"] == "a.py"
        # 3 commits touched foo in a.py (introduce + bump + set-42)
        assert fh["change_count"] == 3
        assert fh["first_commit_message"] == "introduce foo in a.py"
        assert fh["last_commit_message"] == "set foo to 42"
        # Two authors: original + other
        emails = set(fh["authors"])
        assert {"dev@codemem.local", "other@codemem.local"} <= emails

    def test_multi_file_per_file_history(self, git_repo) -> None:
        """Without file_path, symbol exists in two files → per-file history."""
        from codemem.mcp_tools import symbol_history

        db_path, repo_root = git_repo
        result = symbol_history(db_path, "foo", repo_root=repo_root)
        files_seen = {fh["file"] for fh in result["files"]}
        assert files_seen == {"a.py", "b.py"}
        # a.py: 3 touches; b.py: 1 touch
        counts = {fh["file"]: fh["change_count"] for fh in result["files"]}
        assert counts == {"a.py": 3, "b.py": 1}

    def test_no_matching_symbol_returns_empty(self, git_repo) -> None:
        from codemem.mcp_tools import symbol_history

        db_path, repo_root = git_repo
        result = symbol_history(db_path, "not_a_symbol", repo_root=repo_root)
        assert result["files"] == []
        assert result["error"] is None


class TestSanitization:
    def test_injection_rejected(self, tmp_path: Path) -> None:
        from codemem.mcp_tools import symbol_history

        db_path = tmp_path / "e.db"
        conn = connect(db_path)
        apply_schema(conn)
        migrate(conn)
        conn.close()
        result = symbol_history(db_path, "$(rm -rf /tmp)", repo_root=tmp_path)
        assert result["error"] is not None
        assert result["files"] == []


class TestMissingRepoRoot:
    def test_no_repo_root_returns_error(self, git_repo) -> None:
        from codemem.mcp_tools import symbol_history

        db_path, _ = git_repo
        result = symbol_history(db_path, "foo")  # no repo_root
        assert result["error"] is not None
        assert "repo_root" in result["error"]
