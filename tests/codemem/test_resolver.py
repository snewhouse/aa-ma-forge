"""Tests for codemem.resolver — Task 1.6 (cross-file edge resolution)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from codemem.indexer import build_index
from codemem.resolver import build_import_map
from codemem.storage import db


# ---------------------------------------------------------------------
# build_import_map — dotted-path construction
# ---------------------------------------------------------------------

class TestBuildImportMap:
    def test_plain_module(self):
        m = build_import_map(["src/utils/helpers.py"])
        assert m["src.utils.helpers"] == "src/utils/helpers.py"

    def test_init_py_also_registers_package_name(self):
        m = build_import_map(["src/pkg/__init__.py"])
        assert m["src.pkg.__init__"] == "src/pkg/__init__.py"
        assert m["src.pkg"] == "src/pkg/__init__.py"

    def test_ignores_non_python(self):
        m = build_import_map(["src/app.ts", "src/main.py", "README.md"])
        assert "src.app" not in m  # .ts is resolver-scoped to python
        assert m["src.main"] == "src/main.py"

    def test_top_level_init_no_package_name(self):
        m = build_import_map(["__init__.py"])
        # dotted = '__init__'; pkg = '' after removesuffix → skipped
        assert m["__init__"] == "__init__.py"
        assert "" not in m


# ---------------------------------------------------------------------
# 4-strategy resolution via end-to-end build_index run
# ---------------------------------------------------------------------

def _init_commit(root: Path) -> None:
    subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
    subprocess.run(
        ["git", "-C", str(root), "config", "user.email", "t@x"], check=True
    )
    subprocess.run(
        ["git", "-C", str(root), "config", "user.name", "T"], check=True
    )
    subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(root), "commit", "-qm", "init", "--allow-empty"], check=True
    )


@pytest.fixture
def cross_file_repo(tmp_path: Path) -> Path:
    """Two-file Python repo where a.py imports b.py and calls b.helper()."""
    (tmp_path / ".gitignore").write_text(".codemem/\n")
    (tmp_path / "a.py").write_text(
        "from b import helper\n"
        "\n"
        "def caller():\n"
        "    return helper()\n"
    )
    (tmp_path / "b.py").write_text(
        "def helper():\n"
        "    return 42\n"
    )
    _init_commit(tmp_path)
    return tmp_path


@pytest.fixture
def unresolvable_repo(tmp_path: Path) -> Path:
    """Repo with a call to an external library — dst_unresolved should stay."""
    (tmp_path / ".gitignore").write_text(".codemem/\n")
    (tmp_path / "app.py").write_text(
        "import requests\n"
        "\n"
        "def fetch():\n"
        "    return requests.get('https://x')\n"
    )
    _init_commit(tmp_path)
    return tmp_path


class TestCrossFileResolution:
    def test_resolved_edge_materialized_in_db(self, cross_file_repo, tmp_path):
        db_path = tmp_path / "out" / "index.db"
        build_index(cross_file_repo, db_path, package=".")
        with db.connect(db_path, read_only=True) as conn:
            rows = conn.execute(
                "SELECT src.name, dst.name "
                "FROM edges e "
                "JOIN symbols src ON src.id = e.src_symbol_id "
                "JOIN symbols dst ON dst.id = e.dst_symbol_id "
                "WHERE e.kind = 'call'"
            ).fetchall()
            assert ("caller", "helper") in rows

    def test_cross_file_edge_has_null_dst_unresolved(self, cross_file_repo, tmp_path):
        db_path = tmp_path / "out" / "index.db"
        build_index(cross_file_repo, db_path, package=".")
        with db.connect(db_path, read_only=True) as conn:
            row = conn.execute(
                "SELECT e.dst_unresolved "
                "FROM edges e "
                "JOIN symbols src ON src.id = e.src_symbol_id "
                "WHERE src.name = 'caller' AND e.kind = 'call'"
            ).fetchone()
            assert row is not None
            assert row[0] is None  # fully resolved

    def test_external_import_leaves_unresolved_edge(self, unresolvable_repo, tmp_path):
        db_path = tmp_path / "out" / "index.db"
        build_index(unresolvable_repo, db_path, package=".")
        with db.connect(db_path, read_only=True) as conn:
            rows = conn.execute(
                "SELECT e.dst_symbol_id, e.dst_unresolved "
                "FROM edges e "
                "JOIN symbols src ON src.id = e.src_symbol_id "
                "WHERE src.name = 'fetch' AND e.kind = 'call'"
            ).fetchall()
            assert rows, "no call edges emitted for fetch()"
            # `requests.get()` → attribute call → `get` is the callee name.
            # Not resolvable (requests not indexed) → dst_unresolved populated.
            has_unresolved_get = any(
                dst_id is None and dst_unresolved == "get"
                for dst_id, dst_unresolved in rows
            )
            assert has_unresolved_get, rows

    def test_relative_import_strategy(self, tmp_path):
        # Strategy 2: source dir + imp
        (tmp_path / ".gitignore").write_text(".codemem/\n")
        (tmp_path / "pkg").mkdir()
        (tmp_path / "pkg" / "a.py").write_text(
            "from b import helper\n"
            "def caller(): return helper()\n"
        )
        (tmp_path / "pkg" / "b.py").write_text(
            "def helper(): return 1\n"
        )
        _init_commit(tmp_path)
        db_path = tmp_path / "out" / "index.db"
        build_index(tmp_path, db_path, package=".")
        with db.connect(db_path, read_only=True) as conn:
            rows = conn.execute(
                "SELECT src.name, dst.name "
                "FROM edges e "
                "JOIN symbols src ON src.id = e.src_symbol_id "
                "JOIN symbols dst ON dst.id = e.dst_symbol_id "
                "WHERE e.kind = 'call'"
            ).fetchall()
            assert ("caller", "helper") in rows

    def test_suffix_match_strategy(self, tmp_path):
        # Strategy 4: deeply-nested module, caller imports by shortname
        (tmp_path / ".gitignore").write_text(".codemem/\n")
        (tmp_path / "deep").mkdir()
        (tmp_path / "deep" / "nested").mkdir()
        (tmp_path / "deep" / "nested" / "utils.py").write_text(
            "def deep_helper(): return 9\n"
        )
        (tmp_path / "caller.py").write_text(
            "from utils import deep_helper\n"
            "def run(): return deep_helper()\n"
        )
        _init_commit(tmp_path)
        db_path = tmp_path / "out" / "index.db"
        build_index(tmp_path, db_path, package=".")
        with db.connect(db_path, read_only=True) as conn:
            rows = conn.execute(
                "SELECT src.name, dst.name "
                "FROM edges e "
                "JOIN symbols src ON src.id = e.src_symbol_id "
                "JOIN symbols dst ON dst.id = e.dst_symbol_id "
                "WHERE e.kind = 'call'"
            ).fetchall()
            assert ("run", "deep_helper") in rows


# ---------------------------------------------------------------------
# Parser contract — python_ast populates imports + unresolved_edges
# ---------------------------------------------------------------------

class TestPythonParserExposesImports:
    def test_import_statement_captured(self):
        from codemem.parser.python_ast import extract_python_signatures
        pr = extract_python_signatures(
            "import os\nimport a.b\nfrom c.d import e\n",
            package=".", file_rel="x.py",
        )
        assert "os" in pr.imports
        assert "a.b" in pr.imports
        assert "c.d" in pr.imports

    def test_external_call_emits_unresolved_edge(self):
        from codemem.parser.python_ast import extract_python_signatures
        pr = extract_python_signatures(
            "def f():\n    return requests.get('x')\n",
            package=".", file_rel="x.py",
        )
        # Was 0 before Task 1.6; now we emit the unresolved candidate.
        assert pr.edges == []  # intra-file still empty
        names = {e.dst_unresolved for e in pr.unresolved_edges}
        assert "get" in names
