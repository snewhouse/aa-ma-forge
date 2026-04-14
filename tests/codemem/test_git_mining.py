"""Tests for codemem.analysis.git_mining (M3 Task 3.1).

Covers acceptance criteria:
- subprocess uses shell=False with `--` separator
- Wrappers for `git log` (commit cache) and `git blame` (ownership)
- Caches last 500 commits in `commits` table
- Incremental refresh via `git log <last_sha>..HEAD`
- All file path args validated against repo root
- Subprocess injection safety
- Populates `commit_files` junction
"""

from __future__ import annotations

import os
import subprocess
import sqlite3
from pathlib import Path

import pytest

from codemem.storage import apply_schema, connect, migrate


def _commit(root: Path, message: str, author_time: int) -> None:
    """Commit with a pinned author+committer date so tests are deterministic
    independent of wall-clock. This side-steps timestamp ties that would
    otherwise make 'newest by author_time' ambiguous under SQLite's
    undefined tie-break."""
    env = {
        **os.environ,
        "GIT_AUTHOR_DATE": f"@{author_time} +0000",
        "GIT_COMMITTER_DATE": f"@{author_time} +0000",
    }
    subprocess.run(
        ["git", "-C", str(root), "commit", "-qm", message],
        check=True,
        env=env,
    )


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """Create a tmp git repo with a small history. Returns repo root."""
    root = tmp_path / "repo"
    root.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
    subprocess.run(
        ["git", "-C", str(root), "config", "user.email", "miner@codemem.local"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(root), "config", "user.name", "miner"], check=True
    )
    # Seed commit — author_time pinned so each subsequent commit is strictly newer.
    (root / "a.py").write_text("def foo(): pass\n")
    (root / "b.py").write_text("def bar(): pass\n")
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    _commit(root, "seed: two files", 1700000001)
    # Second commit touching both files
    (root / "a.py").write_text("def foo(): return 1\n")
    (root / "b.py").write_text("def bar(): return 2\n")
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    _commit(root, "feat: flesh out", 1700000002)
    # Third commit touching only a.py
    (root / "a.py").write_text("def foo(): return 42\n")
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    _commit(root, "refactor: 42", 1700000003)
    return root


@pytest.fixture
def db(tmp_path: Path) -> sqlite3.Connection:
    """Fresh DB migrated to v2 (has commits + commit_files tables)."""
    conn = connect(tmp_path / "test.db")
    apply_schema(conn)
    migrate(conn)
    yield conn
    conn.close()


# ---------------------------------------------------------------------------
# Module shape
# ---------------------------------------------------------------------------


class TestModuleSurface:
    def test_git_mining_module_importable(self) -> None:
        from codemem.analysis import git_mining  # noqa: F401

    def test_git_miner_class_available(self) -> None:
        from codemem.analysis.git_mining import GitMiner

        assert callable(GitMiner)


# ---------------------------------------------------------------------------
# Commit cache population
# ---------------------------------------------------------------------------


class TestRefreshCommitsCache:
    def test_populates_commits_table_from_git_log(
        self, db: sqlite3.Connection, git_repo: Path
    ) -> None:
        from codemem.analysis.git_mining import GitMiner

        miner = GitMiner(repo_root=git_repo)
        n = miner.refresh_commits_cache(db, limit=500)
        assert n == 3  # seed + feat + refactor
        cur = db.execute("SELECT COUNT(*) FROM commits")
        assert cur.fetchone()[0] == 3

    def test_commits_have_correct_fields(
        self, db: sqlite3.Connection, git_repo: Path
    ) -> None:
        from codemem.analysis.git_mining import GitMiner

        GitMiner(repo_root=git_repo).refresh_commits_cache(db)
        cur = db.execute(
            "SELECT author_email, message FROM commits ORDER BY author_time ASC"
        )
        rows = cur.fetchall()
        assert rows[0] == ("miner@codemem.local", "seed: two files")
        assert rows[1] == ("miner@codemem.local", "feat: flesh out")
        assert rows[2] == ("miner@codemem.local", "refactor: 42")

    def test_populates_commit_files_junction(
        self, db: sqlite3.Connection, git_repo: Path
    ) -> None:
        from codemem.analysis.git_mining import GitMiner

        GitMiner(repo_root=git_repo).refresh_commits_cache(db)
        # Seed commit touched a.py and b.py; feat commit touched both; refactor touched only a.py.
        cur = db.execute(
            "SELECT file_path, COUNT(*) FROM commit_files GROUP BY file_path ORDER BY file_path"
        )
        rows = cur.fetchall()
        # a.py appears in 3 commits, b.py in 2.
        assert rows == [("a.py", 3), ("b.py", 2)]

    def test_idempotent(self, db: sqlite3.Connection, git_repo: Path) -> None:
        """Running refresh twice on an unchanged repo must not duplicate rows."""
        from codemem.analysis.git_mining import GitMiner

        miner = GitMiner(repo_root=git_repo)
        miner.refresh_commits_cache(db)
        miner.refresh_commits_cache(db)
        cur = db.execute("SELECT COUNT(*) FROM commits")
        assert cur.fetchone()[0] == 3
        cur = db.execute("SELECT COUNT(*) FROM commit_files")
        assert cur.fetchone()[0] == 5  # 2 + 2 + 1


class TestIncrementalRefresh:
    def test_only_new_commits_fetched_on_second_refresh(
        self, db: sqlite3.Connection, git_repo: Path
    ) -> None:
        """After initial cache, adding a new commit and refreshing must
        add exactly one row, not re-process existing history."""
        from codemem.analysis.git_mining import GitMiner

        miner = GitMiner(repo_root=git_repo)
        n_initial = miner.refresh_commits_cache(db)
        assert n_initial == 3

        # Add a fourth commit
        (git_repo / "c.py").write_text("def baz(): pass\n")
        subprocess.run(["git", "-C", str(git_repo), "add", "-A"], check=True)
        subprocess.run(
            ["git", "-C", str(git_repo), "commit", "-qm", "add c.py"],
            check=True,
        )

        n_new = miner.refresh_commits_cache(db)
        assert n_new == 1
        cur = db.execute("SELECT COUNT(*) FROM commits")
        assert cur.fetchone()[0] == 4


class TestLimitEnforcement:
    def test_commit_cap_trims_oldest(
        self, db: sqlite3.Connection, git_repo: Path
    ) -> None:
        """With limit=2 after seeding 3 commits, only 2 most-recent must remain."""
        from codemem.analysis.git_mining import GitMiner

        miner = GitMiner(repo_root=git_repo)
        miner.refresh_commits_cache(db, limit=2)
        cur = db.execute("SELECT COUNT(*) FROM commits")
        assert cur.fetchone()[0] == 2
        # The remaining ones must be the two newest (feat + refactor), ordered desc.
        cur = db.execute(
            "SELECT message FROM commits ORDER BY author_time DESC"
        )
        msgs = [r[0] for r in cur.fetchall()]
        assert msgs == ["refactor: 42", "feat: flesh out"]

    def test_cap_cascades_to_commit_files(
        self, db: sqlite3.Connection, git_repo: Path
    ) -> None:
        """When a commit is evicted for cap, its commit_files must cascade out."""
        from codemem.analysis.git_mining import GitMiner

        miner = GitMiner(repo_root=git_repo)
        miner.refresh_commits_cache(db, limit=1)
        # Only the newest commit (refactor: 42) remains — it touched a.py only.
        cur = db.execute("SELECT file_path FROM commit_files")
        rows = [r[0] for r in cur.fetchall()]
        assert rows == ["a.py"]


# ---------------------------------------------------------------------------
# Subprocess discipline + injection defense
# ---------------------------------------------------------------------------


class TestSanitization:
    def test_repo_root_rejects_outside_path(self, tmp_path: Path) -> None:
        """GitMiner constructor must reject a non-git directory."""
        from codemem.analysis.git_mining import GitMiner

        non_git = tmp_path / "not-a-repo"
        non_git.mkdir()
        with pytest.raises(Exception):  # OSError or CalledProcessError — any git-side reject
            GitMiner(repo_root=non_git).refresh_commits_cache(
                connect(tmp_path / "x.db")
            )

    def test_file_path_injection_rejected(self, git_repo: Path) -> None:
        """File-path args containing shell metachars must raise ValidationError
        before any subprocess runs."""
        from codemem.analysis.git_mining import GitMiner
        from codemem.mcp_tools.sanitizers import ValidationError

        miner = GitMiner(repo_root=git_repo)
        with pytest.raises(ValidationError):
            miner.get_blame("$(rm -rf /tmp)")
        with pytest.raises(ValidationError):
            miner.get_blame("a.py; rm -rf /")
        with pytest.raises(ValidationError):
            miner.get_blame("../../etc/passwd")

    def test_path_outside_repo_rejected(
        self, git_repo: Path, tmp_path: Path
    ) -> None:
        """A path that would canonicalise outside repo_root must be rejected."""
        from codemem.analysis.git_mining import GitMiner
        from codemem.mcp_tools.sanitizers import ValidationError

        miner = GitMiner(repo_root=git_repo)
        with pytest.raises(ValidationError):
            miner.get_blame("../../../some/other/place.py")


# ---------------------------------------------------------------------------
# Blame / ownership
# ---------------------------------------------------------------------------


class TestGetBlame:
    def test_blame_returns_author_percentages(
        self, git_repo: Path
    ) -> None:
        """With a single author, blame must attribute 100.0% to that email."""
        from codemem.analysis.git_mining import GitMiner

        miner = GitMiner(repo_root=git_repo)
        result = miner.get_blame("a.py")
        assert isinstance(result, dict)
        assert "miner@codemem.local" in result
        line_count, pct = result["miner@codemem.local"]
        assert line_count >= 1
        assert pct == pytest.approx(100.0, abs=0.001)

    def test_blame_returns_empty_for_missing_file(self, git_repo: Path) -> None:
        """Blame on a non-existent file returns an empty dict (not a crash)."""
        from codemem.analysis.git_mining import GitMiner

        miner = GitMiner(repo_root=git_repo)
        assert miner.get_blame("does-not-exist.py") == {}


class TestShellFalseDiscipline:
    def test_no_shell_true_in_module(self) -> None:
        """Static guarantee: git_mining.py uses shell=False everywhere."""
        src = (
            Path(__file__).resolve().parent.parent.parent
            / "packages"
            / "codemem-mcp"
            / "src"
            / "codemem"
            / "analysis"
            / "git_mining.py"
        ).read_text()
        # shell=True is banned. shell=False is either explicit or (correctly) the
        # default — so we just need to ensure the True form never appears.
        assert "shell=True" not in src
