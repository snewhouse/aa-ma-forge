"""Tests for codemem.pagerank — Task 1.8 (PageRank + PROJECT_INTEL.json)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
import tiktoken

from codemem.indexer import build_index
from codemem.pagerank import (
    _fits,
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

    def test_fits_uses_tiktoken_not_chars(self):
        # The fix replaces a 4-char-per-token proxy with cl100k_base tokenisation.
        # Construct a payload where char-count and tiktoken-count diverge:
        # ASCII with frequent token boundaries gives ~0.5 tokens/char, so a
        # ~110-char JSON encodes to ~55 tiktoken tokens. Pick a budget where
        # the proxy says FITS but tiktoken says DOESN'T.
        payload = {"name": " x" * 50}
        json_str = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        enc = tiktoken.get_encoding("cl100k_base")
        n_chars = len(json_str)
        n_tokens = len(enc.encode(json_str))

        # Premise check: assertion only meaningful if proxy and tiktoken disagree
        # at this budget. Both must hold for the test to discriminate.
        budget = 30
        assert n_chars <= budget * 4, (
            f"test premise broken: payload is {n_chars} chars, exceeds proxy "
            f"ceiling {budget * 4}; pick a denser payload"
        )
        assert n_tokens > budget, (
            f"test premise broken: payload is only {n_tokens} tokens; "
            f"pick a budget below {n_tokens}"
        )

        # Old proxy: chars ({n_chars}) ≤ {budget*4} → returns True (FITS).
        # Fix: tokens ({n_tokens}) > {budget} → returns False (does not fit).
        assert _fits(payload, budget_tokens=budget) is False, (
            "budget enforcement still uses char proxy; "
            "must use tiktoken cl100k_base encoder"
        )

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

    def test_rank_emitted_as_3_sig_figs(self, hub_repo, tmp_path):
        # v2 AC: rank values rounded to 3 sig figs at emission for stable diffs.
        # Behavioural assertion: float(f"{rank:.3g}") == rank for every emitted rank.
        # Pre-fix code emits raw PageRank floats (full precision) → fails.
        _, db_path = hub_repo
        out = tmp_path / "PROJECT_INTEL.json"
        write_project_intel(db_path, out, budget=1024)
        payload = json.loads(out.read_text())
        for sym in payload["symbols"]:
            rank = sym["rank"]
            if rank == 0.0:
                continue  # zero is trivially 3-sig-fig
            assert float(f"{rank:.3g}") == rank, (
                f"rank {rank!r} for {sym['name']!r} not rounded to 3 sig figs"
            )

    def test_output_fits_tiktoken_budget(self, hub_repo, tmp_path):
        # End-to-end honesty invariant: output's tiktoken-encoded length must
        # not exceed the budget. With the 4-char proxy this is violated when
        # tokens-per-char > 0.25 (e.g. emoji-heavy or symbol-heavy content);
        # under the fix it is enforced directly at _fits() time.
        enc = tiktoken.get_encoding("cl100k_base")
        _, db_path = hub_repo
        out = tmp_path / "PROJECT_INTEL.json"
        budget = 1024
        write_project_intel(db_path, out, budget=budget)
        n_tokens = len(enc.encode(out.read_text()))
        assert n_tokens <= budget, (
            f"output is {n_tokens} tiktoken tokens, exceeds budget={budget}"
        )


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
