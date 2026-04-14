# codemem vs `/index` — Performance Benchmark

Comparative wall-clock benchmarks for the codemem indexer against
[`claude-code-project-index`](https://github.com/ericbuess/claude-code-project-index)
(`/index`), which codemem's M1 tools are a superset of.

**Methodology.** `scripts/bench_codemem.py` runs 5 trials per measurement
and reports the MEDIAN wall-clock time (including subprocess startup).
Times are real time from `time.perf_counter()`; the script is the single
source of truth for reproducibility.

**Acceptance target** (M4 AC, from `codemem-tasks.md` §M4):
`codemem build` cold wall-clock **≤ 1.5×** `/index generate` cold on every
reference repo.

---

## Reference Repos

| Size | Repo | Status |
|---|---|---|
| Small | `aa-ma-forge` (this repo) | **Measured** — see below |
| Medium | `repowise` | Pending — user must specify local path |
| Large | 50k-LOC OSS Python project | Pending — user must specify local path |

Runs against medium + large reference repos require the user to have them
checked out locally; invoke the bench script with the repo path once they
are available:

```bash
python scripts/bench_codemem.py /path/to/repowise \
    --label "repowise (medium)" \
    --anchor <known-symbol-in-repowise>

python scripts/bench_codemem.py /path/to/50k-oss-project \
    --label "50k-LOC OSS (large)" \
    --anchor <known-symbol-in-that-repo>
```

Append the output block directly under this file's "Measurements" section.

---

## Measurements

### aa-ma-forge (small)

_Measured 2026-04-14 — `expt/code_mem_store_what` branch, post-M3 state._

| measurement | median (s) | ratio vs /index |
|---|---:|---:|
| codemem build cold | 0.172 | **0.73×** |
| codemem build warm | 0.180 | — |
| /index generate cold | 0.235 | 1.00× |
| codemem who_calls(refresh_commits_cache) | 0.048 | — |
| /index who-calls refresh_commits_cache | 0.026 | — |

**Build verdict:** PASS (0.73× ≤ 1.5× ceiling — codemem is 27 % faster
than `/index` on this repo; 67 files / 654 symbols / 1376 edges).

**Query note:** `codemem who_calls` via the CLI is 22 ms slower than
`/index who-calls`. Both times are dominated by subprocess startup and
stdlib imports (codemem: Python import-chain + sqlite open; /index: Python
import-chain + JSON parse). The same query via a warm in-process MCP
connection is sub-ms (enforced by `tests/perf/test_budgets.py`
`test_who_calls_query`, which measures < 100 ms budget with massive
headroom: empirical < 1 ms). This benchmark reflects cold-start CLI cost,
not steady-state MCP-server latency — agents that hold the MCP connection
open pay neither overhead.

### repowise (medium)

_Pending — run:_

```bash
python scripts/bench_codemem.py /path/to/repowise --label "repowise (medium)"
```

### 50k-LOC OSS (large)

_Pending — run:_

```bash
python scripts/bench_codemem.py /path/to/50k-oss-project --label "50k-LOC OSS (large)"
```

---

## Reproducibility notes

- Script: `scripts/bench_codemem.py` (checked in at this commit).
- Trials: 5 per measurement; median reported. `python3 -c "import statistics"` used for median — no external deps.
- Environment: WSL2 Ubuntu 24.04 / Linux 6.6.87.2; Python 3.13.5; `uv run codemem` against the codemem-mcp workspace package.
- `/index` invoked directly: `python3 ~/.claude-code-project-index/scripts/project_index.py` (build) and `.../cli.py query who-calls <anchor>` (query).
- Cold build: `.codemem/` / `PROJECT_INDEX.json` deleted before each trial. Warm: left in place.
- Anchor symbol varies per repo (must exist in both tools' indexes). For aa-ma-forge, `refresh_commits_cache` was chosen — it's a fresh M3 Task 3.1 symbol with known cross-file edges.
- Results are **not** time-normalised across machines. The ratio-to-`/index` figure is what matters, not the absolute seconds.

---

## Kill-criterion tie-in

Per `docs/codemem/kill-criteria.md` (plan §12), if `codemem build` wall-clock
exceeds **1.5×** `/index` on ANY reference repo at M1 exit, the SQLite-canonical
bet has not paid off and we fold back into `/index`. The small-repo result
(0.73×) preserves this bet; medium + large verdicts pending.
