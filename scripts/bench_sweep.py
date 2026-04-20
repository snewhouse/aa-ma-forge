#!/usr/bin/env python3
"""M3 budget-sweep orchestrator for the bench harness.

Runs scripts/bench_codemem_vs_aider.py N times per budget and aggregates
medians per (tool, budget) cell. Honors AD-006 (3-run median) without
modifying the single-run harness shape (M2 Task 2.6 contract preserved).

Usage:
    uv run python scripts/bench_sweep.py \\
        --repo /tmp/bench-fastapi \\
        --budgets 512,1024,2048,4096 \\
        --runs 3 \\
        --pinned-sha 708606c982cf35718cb2214c0bb9261cf548f042 \\
        --out /tmp/bench-fastapi.json
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path


def _median_int(values: list[int]) -> int:
    """Median of a list of ints, coerced back to int. Empty → 0."""
    nums = [v for v in values if isinstance(v, int)]
    if not nums:
        return 0
    return int(statistics.median(nums))


def aggregate(runs: list[dict]) -> dict:
    """Aggregate N per-budget harness runs into per-tool medians.

    Status precedence (worst first): error > skipped > ok. One failed run
    drags the cell to error so downstream consumers can flag it.
    """
    if not runs:
        return {}
    tool_names = list(runs[0]["tools"].keys())
    out: dict = {}
    for tool in tool_names:
        statuses = [r["tools"][tool].get("status", "error") for r in runs]
        if "error" in statuses:
            status = "error"
        elif "skipped" in statuses:
            status = "skipped"
        else:
            status = "ok"
        out[tool] = {
            "status": status,
            "raw_bytes": _median_int(
                [r["tools"][tool].get("raw_bytes", 0) for r in runs]
            ),
            "tiktoken_tokens": _median_int(
                [r["tools"][tool].get("tiktoken_tokens", 0) for r in runs]
            ),
            "symbol_count": _median_int(
                [r["tools"][tool].get("symbol_count", 0) for r in runs]
            ),
            "runs_included": len(runs),
        }
    return out


def _run_harness_once(
    project_root: Path, repo: Path, budget: int
) -> dict | None:
    """Invoke the single-run harness, return parsed JSON or None on failure."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        out = Path(f.name)
    try:
        r = subprocess.run(
            [
                "uv", "run", "python",
                "scripts/bench_codemem_vs_aider.py",
                "--repo", str(repo),
                "--requested-budget", str(budget),
                "--out", str(out),
            ],
            cwd=project_root,
            capture_output=True, text=True, timeout=600,
        )
        if r.returncode != 0:
            print(f"  harness exit {r.returncode}: "
                  f"{r.stderr.strip()[-200:]}", file=sys.stderr)
            return None
        return json.loads(out.read_text())
    except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        print(f"  harness error: {type(e).__name__}: {e}", file=sys.stderr)
        return None
    finally:
        out.unlink(missing_ok=True)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", type=Path, required=True,
                   help="Target repository root")
    p.add_argument("--budgets", default="512,1024,2048,4096",
                   help="Comma-separated budget list")
    p.add_argument("--runs", type=int, default=3,
                   help="Runs per cell (AD-006 default)")
    p.add_argument("--out", type=Path, required=True,
                   help="Output JSON path")
    p.add_argument("--pinned-sha", default="",
                   help="Target repo SHA for provenance")
    p.add_argument("--project-root", type=Path,
                   default=Path(__file__).resolve().parents[1],
                   help="aa-ma-forge root (where bench_codemem_vs_aider lives)")
    args = p.parse_args(argv)

    budgets = [int(b.strip()) for b in args.budgets.split(",")]
    result: dict = {
        "repo": str(args.repo.resolve()),
        "pinned_sha": args.pinned_sha,
        "runs_per_cell": args.runs,
        "budgets": budgets,
        "tokenizer": "cl100k_base",
        "measurements": {},
        "overlap": {},
    }

    for budget in budgets:
        print(f"--- budget={budget}, {args.runs} run(s) ---",
              file=sys.stderr)
        runs: list[dict] = []
        for i in range(args.runs):
            run_json = _run_harness_once(args.project_root, args.repo, budget)
            if run_json is not None:
                runs.append(run_json)
                cm = run_json["tools"]["codemem"]
                ai = run_json["tools"]["aider"]
                print(f"  run {i + 1}/{args.runs}: "
                      f"cm={cm['status']}({cm['symbol_count']}sym) "
                      f"ai={ai['status']}({ai['symbol_count']}sym)",
                      file=sys.stderr)
        if runs:
            result["measurements"][f"budget_{budget}"] = aggregate(runs)
            # Overlap sets are deterministic given fixed inputs, so the first
            # successful run's overlap is representative.
            result["overlap"][f"budget_{budget}"] = runs[0]["overlap"]
        else:
            print(f"  budget={budget}: ALL {args.runs} RUNS FAILED",
                  file=sys.stderr)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(f"wrote {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
