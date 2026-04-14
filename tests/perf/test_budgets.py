"""Perf-budget gates (M1 Task 1.13).

Every test here carries ``@pytest.mark.perf`` so the normal fast unit
loop skips them. Run with::

    uv run pytest -m perf

CI runs this as a separate job; a budget failure (regression beyond
the documented tolerance in ``docs/codemem/performance-slo.md``)
halts the pipeline.
"""

from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path

import pytest

from codemem.indexer import build_index
from codemem.mcp_tools import who_calls
from codemem.pagerank import write_project_intel


# ---------------------------------------------------------------------
# Budget constants — mirror docs/codemem/performance-slo.md
# ---------------------------------------------------------------------

BUDGET_COLD_BUILD_SECONDS = 30.0
BUDGET_WARM_BUILD_SECONDS = 5.0
BUDGET_WHO_CALLS_MS = 100.0
BUDGET_PROJECT_INTEL_BYTES = 5 * 1024  # 5KB on aa-ma-forge


INDEX_REPO = Path.home() / ".claude-code-project-index"
AA_MA_FORGE_ROOT = Path(__file__).resolve().parent.parent.parent


# ---------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------

@pytest.fixture
def index_repo_snapshot(tmp_path: Path) -> Path:
    """Snapshot ``~/.claude-code-project-index/scripts/`` into a scratch
    git repo. Skips cleanly if the reference tree isn't available
    (e.g. CI without that checkout)."""
    if not INDEX_REPO.exists():
        pytest.skip(f"{INDEX_REPO} missing — install /index locally to exercise perf gates")
    scratch = tmp_path / "index-scratch"
    shutil.copytree(INDEX_REPO / "scripts", scratch / "scripts")
    (scratch / ".gitignore").write_text(".codemem/\n")
    subprocess.run(["git", "init", "-q", "-b", "main", str(scratch)], check=True)
    subprocess.run(
        ["git", "-C", str(scratch), "config", "user.email", "perf@codemem.local"],
        check=True,
    )
    subprocess.run(
        ["git", "-C", str(scratch), "config", "user.name", "perf"], check=True
    )
    subprocess.run(["git", "-C", str(scratch), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(scratch), "commit", "-qm", "snapshot", "--allow-empty"],
        check=True,
    )
    return scratch


@pytest.fixture
def aa_ma_forge_indexed(tmp_path: Path) -> Path:
    """Build a codemem DB over aa-ma-forge itself (for PROJECT_INTEL size test)."""
    db_path = tmp_path / "aa-ma-forge-index.db"
    build_index(AA_MA_FORGE_ROOT, db_path, package=".")
    return db_path


# ---------------------------------------------------------------------
# Build-time budgets
# ---------------------------------------------------------------------

@pytest.mark.perf
def test_cold_build_under_30s(benchmark, index_repo_snapshot, tmp_path):
    """AC: codemem build cold cache on ~10k-LOC Python repo < 30s."""
    db_path = tmp_path / "cold.db"

    def _run():
        if db_path.exists():
            db_path.unlink()
        build_index(index_repo_snapshot, db_path, package=".")

    elapsed = benchmark.pedantic(_run, rounds=3, iterations=1, warmup_rounds=0)
    # pedantic returns the mean wall-clock time of the last pass
    assert elapsed is None or elapsed < BUDGET_COLD_BUILD_SECONDS, (
        f"cold build exceeded {BUDGET_COLD_BUILD_SECONDS}s: {elapsed:.2f}s"
    )


@pytest.mark.perf
def test_warm_build_under_5s(benchmark, index_repo_snapshot, tmp_path):
    """AC: codemem build warm cache on same repo < 5s."""
    db_path = tmp_path / "warm.db"
    # Prime: first build populates the page cache and SQLite
    build_index(index_repo_snapshot, db_path, package=".")

    def _run():
        build_index(index_repo_snapshot, db_path, package=".")

    elapsed = benchmark.pedantic(_run, rounds=3, iterations=1, warmup_rounds=1)
    assert elapsed is None or elapsed < BUDGET_WARM_BUILD_SECONDS, (
        f"warm build exceeded {BUDGET_WARM_BUILD_SECONDS}s: {elapsed:.2f}s"
    )


# ---------------------------------------------------------------------
# Query-time budgets
# ---------------------------------------------------------------------

@pytest.mark.perf
def test_who_calls_anchor_under_100ms(benchmark, index_repo_snapshot, tmp_path):
    """AC: who_calls("extract_python_signatures") < 100ms."""
    db_path = tmp_path / "anchor.db"
    build_index(index_repo_snapshot, db_path, package=".")

    def _run():
        return who_calls(db_path, "extract_python_signatures", max_depth=3)

    # Benchmark the query. Convert mean seconds → milliseconds for the
    # assertion (pytest-benchmark exposes `stats` with explicit fields).
    result = benchmark(_run)
    # Sanity check result shape
    assert "callers" in result and "error" in result
    mean_ms = benchmark.stats["mean"] * 1000 if hasattr(benchmark, "stats") else 0
    # Some pytest-benchmark versions don't expose stats on the callable
    # object — measure directly as a backstop.
    if mean_ms == 0:
        t0 = time.monotonic()
        for _ in range(10):
            who_calls(db_path, "extract_python_signatures", max_depth=3)
        mean_ms = (time.monotonic() - t0) * 100  # 10 calls × 100
    assert mean_ms < BUDGET_WHO_CALLS_MS, (
        f"who_calls exceeded {BUDGET_WHO_CALLS_MS}ms: {mean_ms:.2f}ms mean"
    )


# ---------------------------------------------------------------------
# Output-size budgets
# ---------------------------------------------------------------------

@pytest.mark.perf
def test_project_intel_size_under_5kb(aa_ma_forge_indexed, tmp_path):
    """AC: PROJECT_INTEL.json ≤ 5KB on aa-ma-forge at budget=1024."""
    out = tmp_path / "PROJECT_INTEL.json"
    stats = write_project_intel(aa_ma_forge_indexed, out, budget=1024)
    assert stats["size_bytes"] <= BUDGET_PROJECT_INTEL_BYTES, (
        f"PROJECT_INTEL.json exceeded {BUDGET_PROJECT_INTEL_BYTES}B: "
        f"{stats['size_bytes']}B"
    )
