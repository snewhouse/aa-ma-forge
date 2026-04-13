"""Tests for codemem.mcp_tools — Task 1.7 (6 MCP tools + sanitization + CTE)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from codemem.indexer import build_index
from codemem.mcp_tools import (
    blast_radius,
    dead_code,
    dependency_chain,
    file_summary,
    search_symbols,
    who_calls,
)
from codemem.mcp_tools.sanitizers import (
    ValidationError,
    sanitize_path_arg,
    sanitize_symbol_arg,
)
from codemem.storage import db


# ---------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------

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
def indexed_repo(tmp_path: Path) -> tuple[Path, Path]:
    """Indexed repo with a linear call chain: a → b → c → d."""
    (tmp_path / ".gitignore").write_text(".codemem/\n")
    (tmp_path / "chain.py").write_text(
        "def d():\n"
        "    return 1\n"
        "\n"
        "def c():\n"
        "    return d()\n"
        "\n"
        "def b():\n"
        "    return c()\n"
        "\n"
        "def a():\n"
        "    return b()\n"
        "\n"
        "def orphan():\n"
        "    return 99\n"
    )
    (tmp_path / "cls.py").write_text(
        "class MyClass:\n"
        "    def run(self):\n"
        "        return 1\n"
    )
    _init_commit(tmp_path)
    db_path = tmp_path / ".codemem" / "index.db"
    build_index(tmp_path, db_path, package=".")
    return tmp_path, db_path


# ---------------------------------------------------------------------
# Sanitizers — AC-required adversarial inputs
# ---------------------------------------------------------------------

class TestSanitizers:
    def test_normal_symbol_name_accepted(self):
        assert sanitize_symbol_arg("extract_python_signatures") == "extract_python_signatures"

    def test_normal_path_accepted(self, tmp_path):
        (tmp_path / "a.py").write_text("x = 1\n")
        p = sanitize_path_arg("a.py", tmp_path)
        assert p == (tmp_path / "a.py").resolve()

    def test_parent_traversal_rejected(self):
        with pytest.raises(ValidationError):
            sanitize_symbol_arg("../../etc/passwd")

    def test_absolute_path_rejected(self, tmp_path):
        with pytest.raises(ValidationError):
            sanitize_path_arg("/etc/passwd", tmp_path)

    def test_nested_traversal_rejected(self):
        with pytest.raises(ValidationError):
            sanitize_symbol_arg("foo/../../bar")

    def test_long_unicode_rejected(self):
        with pytest.raises(ValidationError):
            sanitize_symbol_arg("\u4e00" * 10_000)  # 10K Chinese chars

    def test_sql_injection_rejected(self):
        with pytest.raises(ValidationError):
            sanitize_symbol_arg("'; DROP TABLE symbols;--")

    def test_regex_metachars_rejected(self):
        # Regex metachars like ( ) { } * + ? | [ ] ^ $ \ should not pass
        for bad in ["foo(bar)", "foo.*", "foo|bar", "foo[0]", "foo{2}", r"foo\bar"]:
            with pytest.raises(ValidationError):
                sanitize_symbol_arg(bad)

    def test_non_string_rejected(self):
        with pytest.raises(ValidationError):
            sanitize_symbol_arg(123)  # type: ignore[arg-type]

    def test_empty_string_rejected(self):
        with pytest.raises(ValidationError):
            sanitize_symbol_arg("")

    def test_path_escape_after_resolution_rejected(self, tmp_path):
        # Path.resolve() normalizes ../ — verify we catch canonicalized escapes
        sub = tmp_path / "sub"
        sub.mkdir()
        (tmp_path / "outside.py").write_text("x=1\n")
        with pytest.raises(ValidationError):
            sanitize_path_arg("../outside.py", sub)


# ---------------------------------------------------------------------
# who_calls
# ---------------------------------------------------------------------

class TestWhoCalls:
    def test_returns_upstream_callers(self, indexed_repo):
        _, db_path = indexed_repo
        result = who_calls(db_path, "d")
        assert "error" not in result or result["error"] is None
        caller_names = {c["name"] for c in result["callers"]}
        # d is called by c (depth 1); c called by b (depth 2); b called by a (depth 3)
        # max_depth default = 3 so a, b, c should all appear
        assert {"a", "b", "c"}.issubset(caller_names)

    def test_respects_max_depth(self, indexed_repo):
        _, db_path = indexed_repo
        # depth=1 should return only immediate caller (c)
        result = who_calls(db_path, "d", max_depth=1)
        caller_names = {c["name"] for c in result["callers"]}
        assert caller_names == {"c"}

    def test_orphan_has_no_callers(self, indexed_repo):
        _, db_path = indexed_repo
        result = who_calls(db_path, "orphan")
        assert result["callers"] == []

    def test_unknown_symbol_returns_empty(self, indexed_repo):
        _, db_path = indexed_repo
        result = who_calls(db_path, "nonexistent_symbol_xyz")
        assert result["callers"] == []

    def test_malicious_input_returns_error_no_crash(self, indexed_repo):
        _, db_path = indexed_repo
        result = who_calls(db_path, "../../etc/passwd")
        assert "error" in result
        assert result["error"] is not None
        assert "callers" not in result or result["callers"] == []

    def test_sql_injection_does_not_execute(self, indexed_repo):
        _, db_path = indexed_repo
        # Try injection — should be rejected by sanitizer
        result = who_calls(db_path, "'; DROP TABLE symbols;--")
        assert "error" in result and result["error"] is not None
        # Table still exists
        with db.connect(db_path, read_only=True) as conn:
            cnt = conn.execute("SELECT COUNT(*) FROM symbols").fetchone()[0]
            assert cnt > 0


# ---------------------------------------------------------------------
# blast_radius
# ---------------------------------------------------------------------

class TestBlastRadius:
    def test_returns_downstream_callees(self, indexed_repo):
        _, db_path = indexed_repo
        result = blast_radius(db_path, "a")
        downstream_names = {d["name"] for d in result["downstream"]}
        # a → b → c → d
        assert {"b", "c", "d"}.issubset(downstream_names)

    def test_terminal_symbol_has_no_downstream(self, indexed_repo):
        _, db_path = indexed_repo
        result = blast_radius(db_path, "d")
        assert result["downstream"] == []

    def test_malicious_input_returns_error(self, indexed_repo):
        _, db_path = indexed_repo
        result = blast_radius(db_path, "foo/../../bar")
        assert result["error"] is not None


# ---------------------------------------------------------------------
# dead_code
# ---------------------------------------------------------------------

class TestDeadCode:
    def test_finds_orphan_functions(self, indexed_repo):
        _, db_path = indexed_repo
        result = dead_code(db_path)
        dead_names = {s["name"] for s in result["symbols"]}
        assert "orphan" in dead_names
        # 'a' has no callers (top of chain) — also dead per zero-inbound-edge rule
        assert "a" in dead_names
        # 'd' has a caller (c) — not dead
        assert "d" not in dead_names


# ---------------------------------------------------------------------
# dependency_chain
# ---------------------------------------------------------------------

class TestDependencyChain:
    def test_finds_path_from_source_to_target(self, indexed_repo):
        _, db_path = indexed_repo
        result = dependency_chain(db_path, "a", "d")
        assert result["chain"] is not None
        chain_names = [step["name"] for step in result["chain"]]
        assert chain_names == ["a", "b", "c", "d"]

    def test_no_path_returns_none(self, indexed_repo):
        _, db_path = indexed_repo
        result = dependency_chain(db_path, "orphan", "d")
        assert result["chain"] is None

    def test_malicious_input_returns_error(self, indexed_repo):
        _, db_path = indexed_repo
        result = dependency_chain(db_path, "../../etc", "d")
        assert result["error"] is not None


# ---------------------------------------------------------------------
# search_symbols
# ---------------------------------------------------------------------

class TestSearchSymbols:
    def test_matches_by_substring(self, indexed_repo):
        _, db_path = indexed_repo
        result = search_symbols(db_path, "run")
        names = {m["name"] for m in result["matches"]}
        assert "run" in names  # MyClass.run

    def test_matches_class_names(self, indexed_repo):
        _, db_path = indexed_repo
        result = search_symbols(db_path, "MyClass")
        names = {m["name"] for m in result["matches"]}
        assert "MyClass" in names

    def test_empty_query_returns_error(self, indexed_repo):
        _, db_path = indexed_repo
        result = search_symbols(db_path, "")
        assert result["error"] is not None


# ---------------------------------------------------------------------
# file_summary
# ---------------------------------------------------------------------

class TestFileSummary:
    def test_lists_symbols_in_file(self, indexed_repo):
        _, db_path = indexed_repo
        result = file_summary(db_path, "chain.py")
        names = [s["name"] for s in result["symbols"]]
        assert "a" in names and "b" in names and "c" in names
        # Sorted by line
        lines = [s["line"] for s in result["symbols"]]
        assert lines == sorted(lines)

    def test_malicious_path_rejected(self, indexed_repo):
        _, db_path = indexed_repo
        result = file_summary(db_path, "../../etc/passwd")
        assert result["error"] is not None

    def test_unknown_path_returns_empty(self, indexed_repo):
        _, db_path = indexed_repo
        result = file_summary(db_path, "no_such_file.py")
        assert result["symbols"] == []


# ---------------------------------------------------------------------
# Token budget enforcement
# ---------------------------------------------------------------------

class TestBudget:
    def test_budget_truncates_results(self, tmp_path):
        # Many symbols → exceed tiny budget
        (tmp_path / ".gitignore").write_text(".codemem/\n")
        src = "\n".join(f"def sym_{i}(): return {i}" for i in range(200))
        (tmp_path / "big.py").write_text(src)
        _init_commit(tmp_path)
        db_path = tmp_path / ".codemem" / "index.db"
        build_index(tmp_path, db_path, package=".")

        result = search_symbols(db_path, "sym", budget=200)  # extremely tiny
        assert result["truncated"] is True
        assert len(result["matches"]) < 200

    def test_ample_budget_returns_all(self, tmp_path):
        (tmp_path / ".gitignore").write_text(".codemem/\n")
        src = "\n".join(f"def sym_{i}(): return {i}" for i in range(10))
        (tmp_path / "small.py").write_text(src)
        _init_commit(tmp_path)
        db_path = tmp_path / ".codemem" / "index.db"
        build_index(tmp_path, db_path, package=".")

        result = search_symbols(db_path, "sym", budget=8000)
        assert result["truncated"] is False
        assert len(result["matches"]) == 10


# ---------------------------------------------------------------------
# Canonical CTE explain-plan — AC gate
# ---------------------------------------------------------------------

class TestCanonicalCTEExplainPlan:
    def test_who_calls_cte_uses_indexes_only(self, indexed_repo):
        """AC: explain-plan on the canonical CTE uses indexes only (no table scan)."""
        from codemem.mcp_tools.queries import WHO_CALLS_CTE

        _, db_path = indexed_repo
        with db.connect(db_path, read_only=True) as conn:
            # Resolve 'd' to its symbol id for binding
            sid = conn.execute(
                "SELECT id FROM symbols WHERE name = 'd'"
            ).fetchone()[0]
            plan = conn.execute(
                "EXPLAIN QUERY PLAN " + WHO_CALLS_CTE,
                {"target": sid, "max_depth": 3},
            ).fetchall()

        # Every line of the plan referencing 'edges' must use an index.
        for row in plan:
            detail = row[-1] if isinstance(row, tuple) else row["detail"]
            if "edges" in detail.lower():
                # Must be a SEARCH against an index, never a SCAN
                assert "SCAN" not in detail.upper() or "USING INDEX" in detail.upper(), (
                    f"bare SCAN on edges detected: {detail}"
                )
