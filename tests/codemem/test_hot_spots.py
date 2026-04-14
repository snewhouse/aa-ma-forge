"""Tests for codemem.mcp_tools.hot_spots (M3 Task 3.2).

AC: top-N files ranked by (commits in window) × (function_count).
Includes score breakdown. ≥1 commit in window × ≥1 function is the floor.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from codemem.storage import apply_schema, connect, migrate, transaction


@pytest.fixture
def populated_db(tmp_path: Path) -> Path:
    """Create a v2 DB with deterministic fixture data.

    Scenario:
      - a.py: 3 functions, 5 commits in window
      - b.py: 2 functions, 3 commits in window
      - c.py: 1 function, 1 commit in window
      - d.py: 0 functions, 10 commits in window (excluded — no functions)
      - e.py: 4 functions, 0 commits in window (excluded — no commits)
    """
    db_path = tmp_path / "test.db"
    conn = connect(db_path)
    apply_schema(conn)
    migrate(conn)
    cutoff_now = 1_800_000_000  # 2027-01-15 — "now" for tests
    in_window = cutoff_now - 10 * 86400  # 10 days ago, within 90-day default
    out_of_window = cutoff_now - 120 * 86400  # 120 days ago, stale

    with transaction(conn):
        # Files + symbols (function counts)
        for (path, fns) in [
            ("a.py", 3), ("b.py", 2), ("c.py", 1),
            ("d.py", 0), ("e.py", 4),
        ]:
            conn.execute(
                "INSERT INTO files (path, lang, last_indexed) VALUES (?, 'python', 0)",
                (path,),
            )
            file_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
            for i in range(fns):
                conn.execute(
                    "INSERT INTO symbols (file_id, scip_id, name, kind, line) "
                    "VALUES (?, ?, ?, 'function', ?)",
                    (file_id, f"scip-{path}-{i}", f"f{i}", i + 1),
                )

        # Commits + commit_files — 5 for a.py, 3 for b.py, 1 for c.py, 10 for d.py in window
        counter = 0
        for (path, commits_in, commits_out) in [
            ("a.py", 5, 0), ("b.py", 3, 0), ("c.py", 1, 0),
            ("d.py", 10, 0), ("e.py", 0, 4),  # e.py only has out-of-window commits
        ]:
            for i in range(commits_in):
                sha = f"inw{counter:04x}"
                counter += 1
                conn.execute(
                    "INSERT INTO commits (sha, author_email, author_time, message) "
                    "VALUES (?, 'dev@x.y', ?, 'msg')",
                    (sha, in_window + i),
                )
                conn.execute(
                    "INSERT INTO commit_files (commit_sha, file_path) VALUES (?, ?)",
                    (sha, path),
                )
            for i in range(commits_out):
                sha = f"out{counter:04x}"
                counter += 1
                conn.execute(
                    "INSERT INTO commits (sha, author_email, author_time, message) "
                    "VALUES (?, 'dev@x.y', ?, 'msg')",
                    (sha, out_of_window + i),
                )
                conn.execute(
                    "INSERT INTO commit_files (commit_sha, file_path) VALUES (?, ?)",
                    (sha, path),
                )
    conn.close()
    return db_path


class TestFunctionSurface:
    def test_hot_spots_importable(self) -> None:
        from codemem.mcp_tools import hot_spots  # noqa: F401

    def test_hot_spots_is_callable(self) -> None:
        from codemem.mcp_tools import hot_spots

        assert callable(hot_spots)


class TestRanking:
    def test_returns_files_with_commits_and_functions(self, populated_db: Path) -> None:
        from codemem.mcp_tools import hot_spots

        result = hot_spots(populated_db, now=1_800_000_000)
        assert result["error"] is None
        paths = [f["path"] for f in result["files"]]
        # a.py (3×5=15), b.py (2×3=6), c.py (1×1=1) — in score order
        assert paths == ["a.py", "b.py", "c.py"]
        assert "d.py" not in paths   # zero functions
        assert "e.py" not in paths   # zero commits in window

    def test_score_breakdown_included(self, populated_db: Path) -> None:
        from codemem.mcp_tools import hot_spots

        result = hot_spots(populated_db, now=1_800_000_000)
        top = result["files"][0]
        assert top["path"] == "a.py"
        assert top["commits_in_window"] == 5
        assert top["function_count"] == 3
        assert top["score"] == 15

    def test_top_n_truncates_list(self, populated_db: Path) -> None:
        from codemem.mcp_tools import hot_spots

        result = hot_spots(populated_db, top_n=2, now=1_800_000_000)
        assert len(result["files"]) == 2
        assert [f["path"] for f in result["files"]] == ["a.py", "b.py"]

    def test_window_days_custom(self, populated_db: Path) -> None:
        """With window=5 days, only the in-window commits in the last 5 days count."""
        from codemem.mcp_tools import hot_spots

        # The in-window commits we inserted span 10 days back → (in_window, in_window+N-1)
        # "now" minus 5 days as cutoff keeps only the commits closer to now.
        result = hot_spots(populated_db, window_days=1, now=1_800_000_000)
        # In 1-day window we still capture commits >= (now-1*86400)
        # Our in-window anchor was 10 days before "now", so nothing in 1-day window.
        assert result["files"] == []


class TestBudgetAndEmptyCases:
    def test_empty_db_returns_empty(self, tmp_path: Path) -> None:
        from codemem.mcp_tools import hot_spots

        db_path = tmp_path / "empty.db"
        conn = connect(db_path)
        apply_schema(conn)
        migrate(conn)
        conn.close()
        result = hot_spots(db_path, now=1_800_000_000)
        assert result["files"] == []
        assert result["error"] is None

    def test_truncated_flag_on_budget_overflow(self, populated_db: Path) -> None:
        from codemem.mcp_tools import hot_spots

        # Tight budget forces truncation
        result = hot_spots(populated_db, budget=10, now=1_800_000_000)
        assert result["truncated"] is True

    def test_default_window_is_90_days(self, populated_db: Path) -> None:
        """AC bullet: 'commits in last 90 days' — default must be 90."""
        from codemem.mcp_tools import hot_spots
        import inspect

        sig = inspect.signature(hot_spots)
        assert sig.parameters["window_days"].default == 90


class TestDeterminism:
    def test_tiebreak_by_path(self, tmp_path: Path) -> None:
        """Equal scores must tie-break by path ASC for reproducibility."""
        from codemem.mcp_tools import hot_spots

        db_path = tmp_path / "tie.db"
        conn = connect(db_path)
        apply_schema(conn)
        migrate(conn)
        cutoff_now = 1_800_000_000
        in_window = cutoff_now - 10 * 86400
        with transaction(conn):
            # Two files, both with score 2 (1 fn × 2 commits each).
            # Insert in reverse alpha to ensure ORDER BY path ASC actually ran.
            for path in ["z.py", "a.py"]:
                conn.execute(
                    "INSERT INTO files (path, lang, last_indexed) VALUES (?, 'python', 0)",
                    (path,),
                )
                fid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                conn.execute(
                    "INSERT INTO symbols (file_id, scip_id, name, kind, line) "
                    "VALUES (?, ?, 'f', 'function', 1)",
                    (fid, f"s-{path}"),
                )
            for i in range(2):
                for path in ["z.py", "a.py"]:
                    sha = f"{path}-{i}"
                    conn.execute(
                        "INSERT INTO commits (sha, author_email, author_time, message) "
                        "VALUES (?, 'x@y.z', ?, '')",
                        (sha, in_window + i),
                    )
                    conn.execute(
                        "INSERT INTO commit_files (commit_sha, file_path) VALUES (?, ?)",
                        (sha, path),
                    )
        conn.close()
        result = hot_spots(db_path, now=cutoff_now)
        assert [f["path"] for f in result["files"]] == ["a.py", "z.py"]
