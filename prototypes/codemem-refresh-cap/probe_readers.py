"""Prototype probe: what a reader sees while a full rebuild runs in place."""
import collections, shutil, subprocess, sys, tempfile, time
from pathlib import Path
from codemem.indexer import build_index
from codemem import mcp_tools
forge = Path(sys.argv[1])
with tempfile.TemporaryDirectory() as t:
    repo = Path(t) / "forge"
    shutil.copytree(forge, repo, ignore=shutil.ignore_patterns(".venv", ".codemem", "graphify-out"), symlinks=True)
    db = repo / ".codemem" / "index.db"
    build_index(repo, db)
    full = len(mcp_tools.search_symbols(db, "refresh", budget=8000).get("results", mcp_tools.search_symbols(db, "refresh", budget=8000)))
    (db.parent / "last_sha").unlink()
    p = subprocess.Popen([sys.executable, "-c", "import sys;from pathlib import Path;from codemem.incremental import refresh_index;refresh_index(Path(sys.argv[1]),Path(sys.argv[2]))", str(repo), str(db)])
    seen = collections.Counter()
    while p.poll() is None:
        try:
            r = mcp_tools.search_symbols(db, "refresh", budget=8000)
            n = len(r.get("results", [])) if isinstance(r, dict) else -1
            seen["error-dict: " + str(r["error"])[:60] if isinstance(r, dict) and "error" in r else ("full" if n == full else f"partial/empty n={n}")] += 1
        except Exception as e:
            seen[f"raise {type(e).__name__}: {str(e)[:50]}"] += 1
    print("baseline results:", full)
    for k, v in seen.most_common():
        print(f"  {v:5d}  {k}")
    for cmd in (["git", "rev-parse", "HEAD"], ["git", "status", "--porcelain", "-uno"], ["git", "status", "--porcelain"]):
        ts = []
        for _ in range(10):
            t0 = time.perf_counter(); subprocess.run(["git", "-C", str(forge), *cmd[1:]], capture_output=True); ts.append((time.perf_counter() - t0) * 1000)
        print(f"{' '.join(cmd)} p50={sorted(ts)[5]:.1f}ms (forge)")
