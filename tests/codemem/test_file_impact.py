"""Tests for codemem.mcp_tools.file_impact (M10.2)."""

from __future__ import annotations

from pathlib import Path

import pytest

from codemem.storage import apply_schema, connect, migrate, transaction

_SWEEP_FILLERS = [f"s{i}.md" for i in range(10)]


def _file(conn, path: str) -> int:
    conn.execute(
        "INSERT INTO files (path, lang, last_indexed) VALUES (?, 'python', 0)", (path,)
    )
    return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def _sym(conn, file_id: int, name: str, line: int = 1) -> int:
    conn.execute(
        "INSERT INTO symbols (file_id, scip_id, name, kind, line) "
        "VALUES (?, ?, ?, 'function', ?)",
        (file_id, f"scip-{file_id}-{name}", name, line),
    )
    return conn.execute("SELECT last_insert_rowid()").fetchone()[0]


def _call(conn, src: int, dst: int) -> None:
    conn.execute(
        "INSERT INTO edges (src_symbol_id, dst_symbol_id, kind) VALUES (?, ?, 'call')",
        (src, dst),
    )


def _commit(conn, sha: str, files: list[str], at: int) -> None:
    conn.execute(
        "INSERT INTO commits (sha, author_email, author_time, message) "
        "VALUES (?, 'dev@x.y', ?, 'msg')",
        (sha, at),
    )
    for fp in files:
        conn.execute(
            "INSERT INTO commit_files (commit_sha, file_path) VALUES (?, ?)", (sha, fp)
        )


@pytest.fixture
def impact_db(tmp_path: Path) -> Path:
    """``src/core.py`` defines ``api`` and ``_helper``.

    Callers: ``src/user.py::use_api`` → api, ``src/other.py::x`` → _helper,
    ``tests/test_core.py::test_api`` → api; ``api`` → ``_helper`` is internal.
    History: core.py + notes.md change together in 3 small commits;
    core.py + sweep.md + 10 fillers change together in 3 sweep commits.
    """
    db_path = tmp_path / "impact.db"
    conn = connect(db_path)
    apply_schema(conn)
    migrate(conn)
    with transaction(conn):
        core = _file(conn, "src/core.py")
        api = _sym(conn, core, "api", 1)
        helper = _sym(conn, core, "_helper", 5)
        _call(conn, api, helper)
        _call(conn, _sym(conn, _file(conn, "src/user.py"), "use_api"), api)
        _call(conn, _sym(conn, _file(conn, "src/other.py"), "x"), helper)
        _call(conn, _sym(conn, _file(conn, "tests/test_core.py"), "test_api"), api)
        for i in range(3):
            _commit(conn, f"small{i}", ["src/core.py", "notes.md"], 1700000000 + i)
            _commit(
                conn,
                f"sweep{i}",
                ["src/core.py", "sweep.md", *_SWEEP_FILLERS],
                1700000100 + i,
            )
    conn.close()
    return db_path


class TestFileImpact:
    def test_external_callers_exclude_own_file_and_tests(self, impact_db: Path) -> None:
        from codemem.mcp_tools import file_impact

        result = file_impact(impact_db, "src/core.py")
        assert result["error"] is None
        assert result["file"] == "src/core.py"
        assert result["external_callers"] == [
            {"file": "src/other.py", "name": "x"},
            {"file": "src/user.py", "name": "use_api"},
        ]

    def test_test_callers_are_split_out(self, impact_db: Path) -> None:
        from codemem.mcp_tools import file_impact

        result = file_impact(impact_db, "src/core.py")
        assert result["test_callers"] == [
            {"file": "tests/test_core.py", "name": "test_api"}
        ]

    def test_co_changes_drop_sweep_commits(self, impact_db: Path) -> None:
        from codemem.mcp_tools import file_impact

        co = file_impact(impact_db, "src/core.py")["co_changes"]
        assert co == [{"path": "notes.md", "count": 3, "ratio": 1.0}]

    def test_bad_path_is_error_dict(self, impact_db: Path) -> None:
        from codemem.mcp_tools import file_impact

        result = file_impact(impact_db, "../etc/passwd")
        assert result["error"]
        assert result["external_callers"] == []
        assert result["test_callers"] == []
        assert result["co_changes"] == []

    def test_unindexed_file_is_empty_not_error(self, impact_db: Path) -> None:
        from codemem.mcp_tools import file_impact

        result = file_impact(impact_db, "docs/nothing.md")
        assert result["error"] is None
        assert result["external_callers"] == result["test_callers"] == []

    def test_tiny_budget_truncates(self, impact_db: Path) -> None:
        from codemem.mcp_tools import file_impact

        result = file_impact(impact_db, "src/core.py", budget=1)
        assert result["truncated"] is True
