# codemem — Performance SLOs

**Status**: M1 baseline. Enforced by `tests/perf/test_budgets.py` (pytest-benchmark). CI fails on any budget regression exceeding the documented tolerance.

These budgets are the *floor* agent UX needs. Breaking them means the tool is slow enough that agents stop using it — a worse outcome than smaller symbol coverage.

---

## M1-enforced budgets

| SLO | Budget | Tolerance | Harness |
|-----|--------|-----------|---------|
| `codemem build` cold cache on `~10k-LOC Python` repo | < 30s | ±10% | `test_cold_build` |
| `codemem build` warm cache (same repo) | < 5s | ±10% | `test_warm_build` |
| `who_calls("extract_python_signatures")` on `~/.claude-code-project-index/scripts/index_utils.py` | < 100ms | ±10% | `test_who_calls_anchor` |
| `PROJECT_INTEL.json` size at `--budget=1024` on aa-ma-forge | ≤ 5KB | absolute | `test_project_intel_size` |

### How the budgets are enforced

```python
# tests/perf/test_budgets.py excerpt
import pytest

@pytest.mark.perf
def test_cold_build(benchmark, index_repo):
    def _run():
        build_index(index_repo, index_repo / ".codemem" / "index.db", package=".")

    result = benchmark.pedantic(_run, rounds=3, iterations=1, warmup_rounds=0)
    assert result < 30.0, f"cold build exceeded 30s budget: {result:.2f}s"
```

`pytest-benchmark` writes results to `.benchmarks/` (git-ignored). Budget regressions are caught at CI time; first-time runs establish the baseline.

**Marker discipline**: every perf test carries `@pytest.mark.perf` so the fast unit loop skips them. CI runs two jobs — `test` (unmarked) and `perf` (`-m perf`). A budget failure fails the perf job and halts the pipeline.

---

## M2–M4 budgets (scheduled for future milestone gates)

| SLO | Budget | Milestone gate |
|-----|--------|----------------|
| `codemem refresh` after a 10-line edit | < 500ms | M2 |
| `codemem refresh` median on medium repo | < 800ms | M4 |
| Each M3 git-mining tool on aa-ma-forge | < 1s | M3 |
| `hot_spots()` on 50k-file synthetic fixture | < 5s | M3 |
| `codemem build` wall-clock ≤ 1.5× `/index` on each reference repo | ratio | M4 |

These aren't enforced in M1 tests — the subjects haven't shipped yet. The M3 and M4 tasks ship their own perf tests + harness extensions.

---

## Measurement methodology

* **Hardware assumption**: developer-class hardware (WSL / macOS / Linux laptop with SSD). CI runs on GitHub Actions Linux runners.
* **Cold cache**: fresh clone, `.codemem/` absent, system page cache NOT warmed. Simulated in tests by deleting the DB + walking the file tree fresh.
* **Warm cache**: second consecutive run after a cold build. System page cache contains the source files; SQLite PRAGMA mmap_size (256MB) is already populated.
* **Anchor symbol**: `extract_python_signatures` at `~/.claude-code-project-index/scripts/index_utils.py#extract_python_signatures`. This is the ported function; the anchor verifies the full pipeline — parser emits the symbol, indexer persists it, `who_calls` finds it via the canonical CTE.

---

## Budget rationale

* **30s cold build**: `/index` takes about 20s on the same 10k-LOC Python codebase. We allow 1.5× for the symbol-level PageRank + SQLite round-trips. Going above this means the architectural-kill criterion in plan §12 triggers.
* **5s warm build**: content-hash based short-circuit lands in M2 Task 2.2; M1's baseline is "everything reindexed" but SQLite WAL + mmap makes this sub-5s on most machines. Tighter budget arrives at M2 where we get credit for not re-parsing unchanged files.
* **100ms `who_calls`**: the canonical CTE uses the covering index `idx_edges_dst`. At expected graph density (N ≈ 1k symbols, avg degree ~3), this completes in <10ms on cached data; the 100ms budget includes the SQLite open + optional cold-index warm-up.
* **1024-token / 5KB `PROJECT_INTEL.json`**: agents paste this into prompts. 1024 tokens is a generous default (fits in every reasonable context budget); 5KB is the wire-format ceiling on aa-ma-forge — a small repo, so it's a real floor.

---

## Reproducibility

```bash
# Run only the perf suite
uv run pytest -m perf

# Run a single budget test with verbose benchmark output
uv run pytest -m perf -k "cold_build" --benchmark-histogram

# Regenerate the .benchmarks/ baseline (e.g. after an intentional perf
# change)
uv run pytest -m perf --benchmark-save=baseline
```

Results land in `.benchmarks/Linux-CPython-*/0001_baseline.json` (git-ignored).

Cross-tool comparisons (codemem vs `/index` vs Aider) live at `docs/benchmarks/codemem-vs-*.md` — those are M4 deliverables (Tasks 4.1 + 4.2).
