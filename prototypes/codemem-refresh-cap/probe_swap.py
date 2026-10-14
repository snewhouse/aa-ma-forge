"""Prototype probe: full rebuild into a temp DB, then os.replace, under reader load."""
import collections, os, shutil, sqlite3, sys, tempfile, threading
from pathlib import Path
from codemem.indexer import build_index
from codemem import mcp_tools
forge = Path(sys.argv[1])
with tempfile.TemporaryDirectory() as t:
    repo = Path(t) / "forge"
    shutil.copytree(forge, repo, ignore=shutil.ignore_patterns(".venv", ".codemem", "graphify-out"), symlinks=True)
    db = repo / ".codemem" / "index.db"
    build_index(repo, db)
    seen, stop = collections.Counter(), threading.Event()
    def reader():
        while not stop.is_set():
            try:
                r = mcp_tools.search_symbols(db, "refresh", budget=8000)
                seen["ok n=%d" % len(r["matches"]) if r.get("error") is None else "error-dict " + str(r["error"])[:50]] += 1
            except Exception as e:
                seen[f"raise {type(e).__name__}: {str(e)[:50]}"] += 1
    th = threading.Thread(target=reader); th.start()
    for i in range(5):
        tmp = db.with_name(f"index.db.tmp-{os.getpid()}")
        build_index(repo, tmp)
        c = sqlite3.connect(tmp); c.execute("PRAGMA wal_checkpoint(TRUNCATE)"); c.close()
        for side in ("-wal", "-shm"):
            Path(str(tmp) + side).unlink(missing_ok=True)
        os.replace(tmp, db)
    stop.set(); th.join()
    c = sqlite3.connect(db); print("integrity after 5 swaps:", c.execute("PRAGMA integrity_check").fetchone()[0], "symbols:", c.execute("select count(*) from symbols").fetchone()[0]); c.close()
    print("sidecar files:", sorted(p.name for p in db.parent.iterdir()))
    for k, v in seen.most_common():
        print(f"  {v:6d}  {k}")
