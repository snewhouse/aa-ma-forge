"""Tests for codemem.mcp_tools.owners (M3 Task 3.4).

AC: per-file or per-directory author percentages via `git blame --line-porcelain`;
cached in `ownership` table; 2s per-file timeout; `--no-owners` skip flag.
"""

from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

import pytest

from codemem.storage import apply_schema, connect, migrate, transaction


def _commit(root: Path, message: str, at: int, author: str | None = None) -> None:
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
        ["git", "-C", str(root), "commit", "-qm", message],
        check=True,
        env=env,
    )


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """Tiny git repo with a file mostly owned by one author."""
    root = tmp_path / "r"
    root.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
    subprocess.run(
        ["git", "-C", str(root), "config", "user.email", "owner@codemem.local"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(root), "config", "user.name", "owner"],
        check=True,
    )
    # 10 lines from owner@codemem.local
    (root / "a.py").write_text("".join(f"line{i}\n" for i in range(10)))
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    _commit(root, "seed", 1700000001)
    # 1 line added by second author (so owner has 10/11 ≈ 90.9%)
    (root / "a.py").write_text("".join(f"line{i}\n" for i in range(10)) + "newline\n")
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    _commit(root, "add one line", 1700000002, author="other@example.com")
    return root


@pytest.fixture
def db_with_cache(tmp_path: Path) -> Path:
    """v2 DB pre-populated with cached ownership for a test file."""
    db_path = tmp_path / "cache.db"
    conn = connect(db_path)
    apply_schema(conn)
    migrate(conn)
    with transaction(conn):
        conn.execute(
            "INSERT INTO ownership (file_path, author_email, line_count, percentage, computed_at) "
            "VALUES ('cached.py', 'alice@example.com', 80, 80.0, 1700000000)"
        )
        conn.execute(
            "INSERT INTO ownership (file_path, author_email, line_count, percentage, computed_at) "
            "VALUES ('cached.py', 'bob@example.com', 20, 20.0, 1700000000)"
        )
    conn.close()
    return db_path


class TestFunctionSurface:
    def test_owners_importable(self) -> None:
        from codemem.mcp_tools import owners  # noqa: F401

    def test_owners_callable(self) -> None:
        from codemem.mcp_tools import owners

        assert callable(owners)


class TestSkipFlag:
    def test_skip_returns_empty(self, db_with_cache: Path) -> None:
        from codemem.mcp_tools import owners

        result = owners(db_with_cache, "cached.py", skip=True)
        assert result["skipped"] is True
        assert result["authors"] == []


class TestCacheRead:
    def test_reads_from_cache_when_available(self, db_with_cache: Path) -> None:
        from codemem.mcp_tools import owners

        result = owners(db_with_cache, "cached.py")
        emails = {a["email"]: a for a in result["authors"]}
        assert "alice@example.com" in emails
        assert "bob@example.com" in emails
        assert emails["alice@example.com"]["percentage"] == 80.0
        assert emails["alice@example.com"]["line_count"] == 80

    def test_cache_result_sorted_desc_by_percentage(self, db_with_cache: Path) -> None:
        from codemem.mcp_tools import owners

        result = owners(db_with_cache, "cached.py")
        pcts = [a["percentage"] for a in result["authors"]]
        assert pcts == sorted(pcts, reverse=True)

    def test_cache_result_ties_break_by_email(self, tmp_path: Path) -> None:
        """Two authors with identical percentage — stable email ASC."""
        from codemem.mcp_tools import owners

        db_path = tmp_path / "tie.db"
        conn = connect(db_path)
        apply_schema(conn)
        migrate(conn)
        with transaction(conn):
            for email in ["zed@x", "alpha@x"]:
                conn.execute(
                    "INSERT INTO ownership (file_path, author_email, line_count, percentage, computed_at) "
                    "VALUES ('t.py', ?, 10, 50.0, 1)",
                    (email,),
                )
        conn.close()
        result = owners(db_path, "t.py")
        assert [a["email"] for a in result["authors"]] == ["alpha@x", "zed@x"]


class TestLiveRefresh:
    def test_refresh_populates_cache_from_git(
        self, tmp_path: Path, git_repo: Path
    ) -> None:
        """With refresh=True and repo_root, must call git blame, cache results."""
        from codemem.mcp_tools import owners

        db_path = tmp_path / "live.db"
        conn = connect(db_path)
        apply_schema(conn)
        migrate(conn)
        # Register the file in the files table so it's indexed.
        conn.execute(
            "INSERT INTO files (path, lang, last_indexed) VALUES ('a.py', 'python', 0)"
        )
        conn.commit()
        conn.close()

        result = owners(db_path, "a.py", refresh=True, repo_root=git_repo)
        emails = {a["email"]: a for a in result["authors"]}
        # owner has 10 lines, other has 1 line → ~90.9%
        assert "owner@codemem.local" in emails
        assert emails["owner@codemem.local"]["percentage"] > 90.0

        # Verify cache populated
        conn = connect(db_path)
        rows = conn.execute(
            "SELECT author_email, line_count FROM ownership WHERE file_path='a.py'"
        ).fetchall()
        conn.close()
        assert len(rows) >= 1
        by_email = dict(rows)
        assert by_email["owner@codemem.local"] >= 10

    def test_missing_cache_and_no_repo_returns_error(self, tmp_path: Path) -> None:
        """Asking for owners on a file with no cache AND no repo_root ⇒ error."""
        from codemem.mcp_tools import owners

        db_path = tmp_path / "empty.db"
        conn = connect(db_path)
        apply_schema(conn)
        migrate(conn)
        conn.close()
        result = owners(db_path, "nowhere.py")
        # No cache AND no repo_root means we have no data and no way to fetch
        assert result["authors"] == []
        assert result.get("from_cache") is False


class TestDirectoryPath:
    def test_directory_aggregates_across_files(self, tmp_path: Path) -> None:
        """When path is a directory prefix, aggregate line counts across all
        cached files under that prefix."""
        from codemem.mcp_tools import owners

        db_path = tmp_path / "dir.db"
        conn = connect(db_path)
        apply_schema(conn)
        migrate(conn)
        with transaction(conn):
            # alice: 90 lines across 2 files under src/aa_ma/
            conn.execute(
                "INSERT INTO ownership VALUES ('src/aa_ma/a.py', 'alice@x', 45, 90.0, 1)"
            )
            conn.execute(
                "INSERT INTO ownership VALUES ('src/aa_ma/b.py', 'alice@x', 45, 90.0, 1)"
            )
            # bob: 10 lines total across same 2 files
            conn.execute(
                "INSERT INTO ownership VALUES ('src/aa_ma/a.py', 'bob@x', 5, 10.0, 1)"
            )
            conn.execute(
                "INSERT INTO ownership VALUES ('src/aa_ma/b.py', 'bob@x', 5, 10.0, 1)"
            )
            # Unrelated file that shouldn't be included
            conn.execute(
                "INSERT INTO ownership VALUES ('other.py', 'carol@x', 100, 100.0, 1)"
            )
        conn.close()

        result = owners(db_path, "src/aa_ma/")
        emails = {a["email"]: a for a in result["authors"]}
        assert "carol@x" not in emails
        # alice: 90/100 = 90%, bob: 10/100 = 10%
        assert emails["alice@x"]["line_count"] == 90
        assert emails["alice@x"]["percentage"] == pytest.approx(90.0, abs=0.01)
        assert emails["bob@x"]["percentage"] == pytest.approx(10.0, abs=0.01)


class TestSanitization:
    def test_injection_returns_error(self, tmp_path: Path) -> None:
        from codemem.mcp_tools import owners

        db_path = tmp_path / "s.db"
        conn = connect(db_path)
        apply_schema(conn)
        migrate(conn)
        conn.close()
        result = owners(db_path, "$(rm -rf /tmp)")
        assert result["error"] is not None
        assert result["authors"] == []


class TestConcurrentRefresh:
    """Sub-step 2.9: the ownership refresh blames files concurrently, but the
    rows it writes are exactly what a serial refresh would write."""

    N_FILES = 10
    BLAME_SLEEP_S = 0.2

    @staticmethod
    def _fake_blame_result(path: str) -> dict[str, tuple[int, float]]:
        idx = int(path.split("_")[1].split(".")[0])
        counts = {"alice@x": 10 + idx, f"dev{idx % 3}@x": 5, "bob@x": idx % 4}
        counts = {e: c for e, c in counts.items() if c}
        total = sum(counts.values())
        return {e: (c, c / total * 100.0) for e, c in counts.items()}

    @pytest.fixture
    def indexed_db(self, tmp_path: Path) -> Path:
        db_path = tmp_path / "conc.db"
        conn = connect(db_path)
        apply_schema(conn)
        migrate(conn)
        with transaction(conn):
            for i in range(self.N_FILES):
                conn.execute(
                    "INSERT INTO files (path, lang, last_indexed) VALUES (?, 'python', 0)",
                    (f"pkg/f_{i}.py",),
                )
            for name in ("boom", "empty"):
                conn.execute(
                    "INSERT INTO files (path, lang, last_indexed) VALUES (?, 'python', 0)",
                    (f"pkg/{name}.py",),
                )
            # Stale rows for the two files whose blame fails: today's
            # semantics leave them untouched.
            conn.execute(
                "INSERT INTO ownership VALUES ('pkg/boom.py', 'stale@x', 7, 100.0, 1)"
            )
            conn.execute(
                "INSERT INTO ownership VALUES ('pkg/empty.py', 'stale@x', 3, 100.0, 1)"
            )
        conn.close()
        return db_path

    @pytest.fixture
    def slow_fake_blame(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import codemem.mcp_tools as mcp_tools
        from codemem.analysis.git_mining import GitMiner

        sleep_s = self.BLAME_SLEEP_S
        fake_result = self._fake_blame_result

        def fake_get_blame(self, file_path: str, *, timeout: float = 2.0):
            time.sleep(sleep_s)
            if file_path.endswith("boom.py"):
                raise subprocess.TimeoutExpired(cmd="git blame", timeout=timeout)
            if file_path.endswith("empty.py"):
                return {}
            return fake_result(file_path)

        monkeypatch.setattr(GitMiner, "get_blame", fake_get_blame)
        # Pin the pool size so the timing bound does not depend on the host's
        # CPU count.
        monkeypatch.setattr(
            mcp_tools, "_BLAME_MAX_WORKERS", self.N_FILES + 2, raising=False
        )

    def test_refresh_blames_files_concurrently(
        self, indexed_db: Path, slow_fake_blame: None, tmp_path: Path
    ) -> None:
        from codemem.mcp_tools import owners

        start = time.perf_counter()
        owners(indexed_db, "pkg/", refresh=True, repo_root=tmp_path)
        elapsed = time.perf_counter() - start
        serial = (self.N_FILES + 2) * self.BLAME_SLEEP_S
        assert elapsed < 1.0, (
            f"refresh took {elapsed:.2f}s; serial blame would take {serial:.1f}s"
        )

    def test_refresh_rows_match_serial_computation(
        self, indexed_db: Path, slow_fake_blame: None, tmp_path: Path
    ) -> None:
        from codemem.mcp_tools import owners

        result = owners(indexed_db, "pkg/", refresh=True, repo_root=tmp_path)

        # Serial reference: blame each file one after another.
        expected_rows: set[tuple[str, str, int, float]] = {
            ("pkg/boom.py", "stale@x", 7, 100.0),
            ("pkg/empty.py", "stale@x", 3, 100.0),
        }
        totals: dict[str, int] = {"stale@x": 7 + 3}
        for i in range(self.N_FILES):
            path = f"pkg/f_{i}.py"
            for email, (lc, pct) in self._fake_blame_result(path).items():
                expected_rows.add((path, email, lc, pct))
                totals[email] = totals.get(email, 0) + lc

        conn = connect(indexed_db)
        rows = conn.execute(
            "SELECT file_path, author_email, line_count, percentage FROM ownership"
        ).fetchall()
        stamps = conn.execute(
            "SELECT DISTINCT computed_at FROM ownership WHERE author_email != 'stale@x'"
        ).fetchall()
        conn.close()
        assert {tuple(r) for r in rows} == expected_rows
        assert len(stamps) == 1  # one refresh, one timestamp

        grand = sum(totals.values())
        expected_authors = sorted(
            (
                {"email": e, "line_count": c, "percentage": c / grand * 100.0}
                for e, c in totals.items()
            ),
            key=lambda a: (-a["percentage"], a["email"]),
        )
        assert result["authors"] == expected_authors


def test_a_directory_query_matches_its_prefix_literally(tmp_path: Path) -> None:
    """`_` and `%` in a directory name were LIKE wildcards: `a_c/` also matched `abc/`."""
    from codemem import mcp_tools

    db_path = tmp_path / "o.db"
    conn = connect(db_path)
    apply_schema(conn)
    migrate(conn)
    with transaction(conn):
        for path, who in (
            ("a_c/x.py", "one@example.com"),
            ("abc/y.py", "two@example.com"),
        ):
            conn.execute(
                "INSERT INTO ownership (file_path, author_email, line_count, percentage, "
                "computed_at) VALUES (?, ?, 10, 100.0, 1700000000)",
                (path, who),
            )
    conn.close()
    got = mcp_tools.owners(db_path, "a_c/")
    assert len(got["authors"]) == 1
