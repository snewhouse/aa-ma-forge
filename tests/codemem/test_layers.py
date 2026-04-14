"""Tests for codemem.mcp_tools.layers (M3 Task 3.6).

AC: in-degree bucketing of edges → 3-layer ASCII onion (core/middle/periphery).
Output ≤500 tokens, fits 80-col terminal, golden file tracked for regression.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from codemem.storage import apply_schema, connect, migrate, transaction


def _add_file_with_symbols(conn, path: str, n_symbols: int, starting_scip: int) -> list[int]:
    """Add a file + n_symbols placeholder functions. Returns inserted symbol ids."""
    conn.execute(
        "INSERT INTO files (path, lang, last_indexed) VALUES (?, 'python', 0)",
        (path,),
    )
    fid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    ids: list[int] = []
    for i in range(n_symbols):
        conn.execute(
            "INSERT INTO symbols (file_id, scip_id, name, kind, line) "
            "VALUES (?, ?, ?, 'function', ?)",
            (fid, f"scip-{starting_scip + i}", f"s{starting_scip + i}", i + 1),
        )
        ids.append(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
    return ids


@pytest.fixture
def populated_db(tmp_path: Path) -> Path:
    """3-tier topology: core.py (high in-degree), mid.py (med), edge.py (low)."""
    db_path = tmp_path / "l.db"
    conn = connect(db_path)
    apply_schema(conn)
    migrate(conn)
    with transaction(conn):
        # core.py: 1 symbol, will be called by 5 symbols from other files
        core_ids = _add_file_with_symbols(conn, "core.py", 1, 1)
        # middle.py: 2 symbols, each called by 2 from edge.py
        middle_ids = _add_file_with_symbols(conn, "middle.py", 2, 10)
        # edge.py: 3 symbols; they are callers, not callees
        edge_ids = _add_file_with_symbols(conn, "edge.py", 3, 20)

        # edge.py symbols call middle.py symbols (creates middle.py in-degree 3)
        for src in edge_ids[:3]:
            conn.execute(
                "INSERT INTO edges (src_symbol_id, dst_symbol_id, kind) VALUES (?, ?, 'call')",
                (src, middle_ids[0]),
            )
        # middle.py symbols call core.py (creates core.py in-degree 2)
        for src in middle_ids:
            conn.execute(
                "INSERT INTO edges (src_symbol_id, dst_symbol_id, kind) VALUES (?, ?, 'call')",
                (src, core_ids[0]),
            )
        # edge.py also calls core (bumps core's in-degree higher)
        for src in edge_ids:
            conn.execute(
                "INSERT INTO edges (src_symbol_id, dst_symbol_id, kind) VALUES (?, ?, 'call')",
                (src, core_ids[0]),
            )
        # Final in-degrees:
        # core.py: 2 (from middle) + 3 (from edge) = 5
        # middle.py: 3 (from edge)
        # edge.py: 0
    conn.close()
    return db_path


class TestFunctionSurface:
    def test_importable(self) -> None:
        from codemem.mcp_tools import layers  # noqa: F401

    def test_callable(self) -> None:
        from codemem.mcp_tools import layers

        assert callable(layers)


class TestBucketing:
    def test_three_layer_buckets(self, populated_db: Path) -> None:
        from codemem.mcp_tools import layers

        result = layers(populated_db)
        assert result["error"] is None
        assert set(result["layers"].keys()) == {"core", "middle", "periphery"}

    def test_highest_in_degree_in_core(self, populated_db: Path) -> None:
        from codemem.mcp_tools import layers

        result = layers(populated_db)
        assert "core.py" in result["layers"]["core"]

    def test_lowest_in_degree_in_periphery(self, populated_db: Path) -> None:
        from codemem.mcp_tools import layers

        result = layers(populated_db)
        assert "edge.py" in result["layers"]["periphery"]

    def test_middle_in_middle(self, populated_db: Path) -> None:
        from codemem.mcp_tools import layers

        result = layers(populated_db)
        assert "middle.py" in result["layers"]["middle"]


class TestAsciiOutput:
    def test_ascii_output_present(self, populated_db: Path) -> None:
        from codemem.mcp_tools import layers

        result = layers(populated_db)
        assert isinstance(result["ascii"], str)
        assert len(result["ascii"]) > 0
        # Labels appear in the output
        assert "core" in result["ascii"].lower()
        assert "middle" in result["ascii"].lower()
        assert "periphery" in result["ascii"].lower()

    def test_ascii_lines_fit_80_columns(self, populated_db: Path) -> None:
        from codemem.mcp_tools import layers

        result = layers(populated_db)
        for line in result["ascii"].splitlines():
            assert len(line) <= 80, f"line exceeds 80 cols: {len(line)} — {line!r}"

    def test_ascii_token_budget(self, populated_db: Path) -> None:
        """≤ 500 tokens ≈ ≤ 2000 chars (1:4 heuristic per reference.md)."""
        from codemem.mcp_tools import layers

        result = layers(populated_db)
        assert len(result["ascii"]) <= 2000


class TestEmptyAndSanitization:
    def test_empty_db_empty_layers(self, tmp_path: Path) -> None:
        from codemem.mcp_tools import layers

        db_path = tmp_path / "empty.db"
        conn = connect(db_path)
        apply_schema(conn)
        migrate(conn)
        conn.close()
        result = layers(db_path)
        assert result["layers"] == {"core": [], "middle": [], "periphery": []}
        assert result["error"] is None
