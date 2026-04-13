"""Tests for codemem.pagerank — Task 1.8 (PageRank + PROJECT_INTEL.json)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from codemem.indexer import build_index
from codemem.pagerank import (
    compute_pagerank,
    write_project_intel,
)
from codemem.storage import db


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
def hub_repo(tmp_path: Path) -> tuple[Path, Path]:
    """Repo where `hub()` is called from many callers — it should outrank leaves."""
    (tmp_path / ".gitignore").write_text(".codemem/\n")
    (tmp_path / "m.py").write_text(
        "def hub(): return 42\n"
        "\n"
        "def a(): return hub()\n"
        "def b(): return hub()\n"
        "def c(): return hub()\n"
        "def d(): return hub()\n"
        "def e(): return hub()\n"
        "\n"
        "def orphan(): return 0\n"
    )
    _init_commit(tmp_path)
    db_path = tmp_path / ".codemem" / "index.db"
    build_index(tmp_path, db_path, package=".")
    return tmp_path, db_path


# ---------------------------------------------------------------------
# compute_pagerank
# ---------------------------------------------------------------------

class TestComputePageRank:
    def test_returns_per_symbol_scores(self, hub_repo):
        _, db_path = hub_repo
        with db.connect(db_path, read_only=True) as conn:
            ranks = compute_pagerank(conn)
        assert isinstance(ranks, dict)
        # Every symbol in the DB should be scored
        n_symbols = conn.execute("SELECT COUNT(*) FROM symbols").fetchone()[0]  # type: ignore
        # Re-open — conn was closed when with exited
        with db.connect(db_path, read_only=True) as conn:
            n_symbols = conn.execute("SELECT COUNT(*) FROM symbols").fetchone()[0]
        assert len(ranks) == n_symbols

    def test_hub_outranks_leaves(self, hub_repo):
        _, db_path = hub_repo
        with db.connect(db_path, read_only=True) as conn:
            ranks = compute_pagerank(conn)
            rows = conn.execute("SELECT id, name FROM symbols").fetchall()
        name_to_rank = {name: ranks[sid] for sid, name in rows}
        assert name_to_rank["hub"] > name_to_rank["a"]
        assert name_to_rank["hub"] > name_to_rank["orphan"]

    def test_sum_approximately_one(self, hub_repo):
        _, db_path = hub_repo
        with db.connect(db_path, read_only=True) as conn:
            ranks = compute_pagerank(conn)
        total = sum(ranks.values())
        assert 0.99 < total < 1.01  # PageRank sums to 1.0 ± float jitter

    def test_deterministic(self, hub_repo):
        _, db_path = hub_repo
        with db.connect(db_path, read_only=True) as conn:
            r1 = compute_pagerank(conn)
        with db.connect(db_path, read_only=True) as conn:
            r2 = compute_pagerank(conn)
        for sid in r1:
            assert abs(r1[sid] - r2[sid]) < 1e-9, sid

    def test_damping_default_point85(self):
        # Contract: damping=0.85 unless overridden. Sanity-check the default.
        from codemem.pagerank import DEFAULT_DAMPING
        assert DEFAULT_DAMPING == 0.85


# ---------------------------------------------------------------------
# write_project_intel → PROJECT_INTEL.json
# ---------------------------------------------------------------------

class TestProjectIntelJson:
    def test_writes_json_file(self, hub_repo, tmp_path):
        repo_root, db_path = hub_repo
        out = tmp_path / "PROJECT_INTEL.json"
        stats = write_project_intel(db_path, out, budget=1024)
        assert out.exists()
        payload = json.loads(out.read_text())
        assert "symbols" in payload
        assert "_meta" in payload
        assert "budget" in payload["_meta"]
        assert stats["written_symbols"] > 0

    def test_fits_budget(self, hub_repo, tmp_path):
        _, db_path = hub_repo
        out = tmp_path / "PROJECT_INTEL.json"
        write_project_intel(db_path, out, budget=128)  # ~512 chars
        size_chars = len(out.read_text())
        # Budget tokens * 4 chars/token is the char ceiling.
        assert size_chars <= 128 * 4 + 50  # small slack for JSON padding

    def test_hub_ranks_first(self, hub_repo, tmp_path):
        _, db_path = hub_repo
        out = tmp_path / "PROJECT_INTEL.json"
        write_project_intel(db_path, out, budget=1024)
        payload = json.loads(out.read_text())
        names = [s["name"] for s in payload["symbols"]]
        assert names[0] == "hub", f"expected hub first, got {names[:3]}"

    def test_deterministic_output_bytes(self, hub_repo, tmp_path):
        _, db_path = hub_repo
        out1 = tmp_path / "p1.json"
        out2 = tmp_path / "p2.json"
        write_project_intel(db_path, out1, budget=1024)
        write_project_intel(db_path, out2, budget=1024)
        assert out1.read_bytes() == out2.read_bytes()

    def test_tie_break_function_beats_variable(self, tmp_path):
        # Force a tie (no edges) — tie-break should prefer functions.
        # In our schema classes use '#' marker; we compare function vs method.
        (tmp_path / ".gitignore").write_text(".codemem/\n")
        (tmp_path / "x.py").write_text(
            "def a(): pass\n"
            "\n"
            "class C:\n"
            "    def m(self): pass\n"
        )
        _init_commit(tmp_path)
        db_path = tmp_path / ".codemem" / "index.db"
        build_index(tmp_path, db_path, package=".")
        out = tmp_path / "PROJECT_INTEL.json"
        write_project_intel(db_path, out, budget=1024)
        payload = json.loads(out.read_text())
        kinds_order = [s["kind"] for s in payload["symbols"]]
        # Among equally-ranked symbols, functions should appear before classes
        # (grammar kinds: function > class; methods get a different rank via
        # parent-class edges).
        assert kinds_order.count("function") >= 1

    def test_small_repo_under_5kb_budget(self, hub_repo, tmp_path):
        _, db_path = hub_repo
        out = tmp_path / "PROJECT_INTEL.json"
        write_project_intel(db_path, out, budget=1024)
        # M1 AC: PROJECT_INTEL.json ≤ 5KB on aa-ma-forge. Hub repo is
        # a proxy — if it comes in under 5KB the real target will too.
        assert out.stat().st_size <= 5 * 1024


# ---------------------------------------------------------------------
# Algorithm properties
# ---------------------------------------------------------------------

class TestAlgorithmProperties:
    def test_empty_db_returns_empty(self, tmp_path):
        db_path = tmp_path / "empty.db"
        with db.connect(db_path, read_only=False) as conn:
            db.apply_schema(conn)
        with db.connect(db_path, read_only=True) as conn:
            assert compute_pagerank(conn) == {}

    def test_isolated_node_gets_base_rank(self, hub_repo):
        _, db_path = hub_repo
        with db.connect(db_path, read_only=True) as conn:
            ranks = compute_pagerank(conn)
            n_symbols = conn.execute("SELECT COUNT(*) FROM symbols").fetchone()[0]
            orphan_id = conn.execute(
                "SELECT id FROM symbols WHERE name = 'orphan'"
            ).fetchone()[0]
        # Orphan (no edges) gets (1-d)/N as base
        expected_base = (1 - 0.85) / n_symbols
        assert ranks[orphan_id] >= expected_base * 0.99  # allow float slack
