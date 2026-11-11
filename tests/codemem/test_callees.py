"""Tests for codemem.mcp_tools.callees and the deprecated blast_radius alias (M10.2)."""

from __future__ import annotations

from pathlib import Path

import pytest

from codemem.storage import apply_schema, connect, migrate, transaction


@pytest.fixture
def chain_db(tmp_path: Path) -> Path:
    """``top`` calls ``mid``, ``mid`` calls ``leaf``; ``leaf`` calls nothing."""
    db_path = tmp_path / "callees.db"
    conn = connect(db_path)
    apply_schema(conn)
    migrate(conn)
    with transaction(conn):
        conn.execute(
            "INSERT INTO files (path, lang, last_indexed) VALUES ('m.py', 'python', 0)"
        )
        for line, name in enumerate(("top", "mid", "leaf"), start=1):
            conn.execute(
                "INSERT INTO symbols (file_id, scip_id, name, kind, line) "
                "VALUES (1, ?, ?, 'function', ?)",
                (f"scip-{name}", name, line),
            )
        conn.execute(
            "INSERT INTO edges (src_symbol_id, dst_symbol_id, kind) VALUES (1, 2, 'call')"
        )
        conn.execute(
            "INSERT INTO edges (src_symbol_id, dst_symbol_id, kind) VALUES (2, 3, 'call')"
        )
    conn.close()
    return db_path


class TestCallees:
    def test_returns_transitive_callees(self, chain_db: Path) -> None:
        from codemem.mcp_tools import callees

        result = callees(chain_db, "top")
        assert result["error"] is None
        assert result["target"] == "top"
        assert [c["name"] for c in result["callees"]] == ["mid", "leaf"]
        assert result["truncated"] is False

    def test_max_depth_one_stops_at_direct_callees(self, chain_db: Path) -> None:
        from codemem.mcp_tools import callees

        result = callees(chain_db, "top", max_depth=1)
        assert [c["name"] for c in result["callees"]] == ["mid"]

    def test_leaf_has_no_callees(self, chain_db: Path) -> None:
        from codemem.mcp_tools import callees

        assert callees(chain_db, "leaf")["callees"] == []

    def test_unknown_symbol_is_empty_not_error(self, chain_db: Path) -> None:
        from codemem.mcp_tools import callees

        result = callees(chain_db, "nope")
        assert result["callees"] == []
        assert result["error"] is None

    def test_bad_name_is_error_dict(self, chain_db: Path) -> None:
        from codemem.mcp_tools import callees

        result = callees(chain_db, "x; DROP TABLE symbols")
        assert result["error"]
        assert result["callees"] == []


class TestBlastRadiusAlias:
    def test_downstream_equals_callees(self, chain_db: Path) -> None:
        from codemem.mcp_tools import blast_radius, callees

        alias = blast_radius(chain_db, "top")
        assert (
            alias["downstream"]
            == alias["callees"]
            == callees(chain_db, "top")["callees"]
        )

    def test_carries_deprecation_notice(self, chain_db: Path) -> None:
        from codemem.mcp_tools import blast_radius

        assert (
            blast_radius(chain_db, "top")["deprecated"]
            == "use callees; removed after v0.18.x"
        )

    def test_error_path_keeps_both_keys(self, chain_db: Path) -> None:
        from codemem.mcp_tools import blast_radius

        result = blast_radius(chain_db, "$(rm)")
        assert result["error"]
        assert result["downstream"] == result["callees"] == []
