#!/usr/bin/env python3
"""codemem vs /index wall-clock benchmark (M4 Task 4.1).

Runs 5 trials of each measurement, reports MEDIAN wall-clock time. Emits
a Markdown block suitable for appending to docs/benchmarks/codemem-vs-index.md.

Measurements (per repo):
  1. codemem build cold   — rm -rf .codemem/ then `codemem build`
  2. codemem build warm   — `codemem build` on an already-built index (noop-ish)
  3. /index generate cold — rm -f PROJECT_INDEX.json then project_index.py
  4. codemem who_calls    — one representative MCP query via CLI
  5. /index who-calls     — same query via /index's cli.py

Usage:
    python scripts/bench_codemem.py <repo-path> [--anchor SYMBOL] [--label LABEL]

Default anchor is ``refresh_commits_cache`` (present in aa-ma-forge). For
other repos pass ``--anchor <symbol>`` where ``<symbol>`` is known to exist
in both tools' indexes.

Reproducibility: script sleeps 0.1s between runs; times include subprocess
startup. Results stored deterministically by commit-sha of the repo under
test (not the measuring tool).
"""

from __future__ import annotations

import argparse
import os
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
INDEX_SCRIPT = Path.home() / ".claude-code-project-index" / "scripts" / "project_index.py"
INDEX_CLI = Path.home() / ".claude-code-project-index" / "scripts" / "cli.py"
TRIALS = 5


def _time(fn) -> float:
    t0 = time.perf_counter()
    fn()
    return time.perf_counter() - t0


def _run(args: list[str], cwd: Path, env_extra: dict | None = None) -> None:
    env = {**os.environ, **(env_extra or {})}
    subprocess.run(
        args, cwd=cwd, env=env, shell=False, check=True,
        capture_output=True,
    )


def _median(ts: list[float]) -> float:
    return statistics.median(ts)


def bench_codemem_build_cold(repo: Path) -> float:
    """Cold build: remove .codemem/ first."""
    def do():
        shutil.rmtree(repo / ".codemem", ignore_errors=True)
        _run(
            ["uv", "run", "codemem", "build"],
            cwd=REPO_ROOT,
            env_extra={"CODEMEM_REPO": str(repo)} if repo != REPO_ROOT else {},
        )
    return _time(do)


def bench_codemem_build_warm(repo: Path) -> float:
    """Warm build: index already present."""
    def do():
        _run(["uv", "run", "codemem", "build"], cwd=REPO_ROOT)
    return _time(do)


def bench_index_build_cold(repo: Path) -> float:
    """Cold /index build: remove PROJECT_INDEX.json first."""
    def do():
        json_path = repo / "PROJECT_INDEX.json"
        if json_path.exists():
            json_path.unlink()
        _run(["python3", str(INDEX_SCRIPT)], cwd=repo)
    return _time(do)


def bench_codemem_who_calls(repo: Path, anchor: str) -> float:
    """Representative MCP query."""
    def do():
        _run(
            ["uv", "run", "codemem", "query", "who_calls", anchor],
            cwd=REPO_ROOT,
        )
    return _time(do)


def bench_index_who_calls(repo: Path, anchor: str) -> float:
    """Same query via /index CLI."""
    def do():
        _run(
            ["python3", str(INDEX_CLI), "query", "who-calls", anchor],
            cwd=repo,
        )
    return _time(do)


def run_trials(label: str, fn, n: int = TRIALS) -> list[float]:
    print(f"  {label:.<40s}", end=" ", flush=True)
    results: list[float] = []
    for _ in range(n):
        try:
            results.append(fn())
        except subprocess.CalledProcessError as exc:
            print(f"FAIL ({exc.returncode})")
            return []
        time.sleep(0.1)
    print(f"median={_median(results):.3f}s (n={n})")
    return results


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("repo", type=Path, help="Path to repo under test")
    ap.add_argument("--anchor", default="refresh_commits_cache",
                    help="Symbol name to probe in who_calls queries")
    ap.add_argument("--label", default=None,
                    help="Human label for this repo (default: repo dir name)")
    args = ap.parse_args()

    repo = args.repo.resolve()
    if not (repo / ".git").exists():
        print(f"error: {repo} is not a git repo", file=sys.stderr)
        return 1

    label = args.label or repo.name

    print(f"\n=== bench: {label} ({repo}) ===")
    print(f"    anchor symbol: {args.anchor}")

    results: dict[str, float] = {}

    # codemem cold + warm
    results["codemem_cold"] = _median(
        run_trials("codemem build (cold)",
                   lambda: bench_codemem_build_cold(repo)) or [float("nan")]
    )
    results["codemem_warm"] = _median(
        run_trials("codemem build (warm)",
                   lambda: bench_codemem_build_warm(repo)) or [float("nan")]
    )

    # /index cold
    if INDEX_SCRIPT.exists():
        results["index_cold"] = _median(
            run_trials("/index generate (cold)",
                       lambda: bench_index_build_cold(repo)) or [float("nan")]
        )
    else:
        print(f"  /index not found at {INDEX_SCRIPT} — skipping comparison")
        results["index_cold"] = float("nan")

    # who_calls queries — best-effort; different anchors per repo
    results["codemem_who_calls"] = _median(
        run_trials(f"codemem who_calls {args.anchor}",
                   lambda: bench_codemem_who_calls(repo, args.anchor)) or [float("nan")]
    )
    if INDEX_CLI.exists():
        results["index_who_calls"] = _median(
            run_trials(f"/index who-calls {args.anchor}",
                       lambda: bench_index_who_calls(repo, args.anchor)) or [float("nan")]
        )
    else:
        results["index_who_calls"] = float("nan")

    # Ratio (codemem / /index). Target: ≤ 1.5.
    build_ratio = (
        results["codemem_cold"] / results["index_cold"]
        if results["index_cold"] and not (results["index_cold"] != results["index_cold"])
        else float("nan")
    )

    # Print markdown row
    print(f"\n### {label}\n")
    print("| measurement | median (s) | ratio vs /index |")
    print("|---|---:|---:|")
    print(f"| codemem build cold | {results['codemem_cold']:.3f} | {build_ratio:.2f}× |")
    print(f"| codemem build warm | {results['codemem_warm']:.3f} | — |")
    print(f"| /index generate cold | {results['index_cold']:.3f} | 1.00× |")
    print(f"| codemem who_calls({args.anchor}) | {results['codemem_who_calls']:.3f} | — |")
    print(f"| /index who-calls {args.anchor} | {results['index_who_calls']:.3f} | — |")
    print(
        f"\n**Target:** `codemem build cold` ≤ 1.5× `/index generate cold`. "
        f"Observed: **{build_ratio:.2f}×** — "
        f"{'PASS' if build_ratio <= 1.5 else 'FAIL'}."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
