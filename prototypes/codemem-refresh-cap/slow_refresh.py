"""Prototype runner: `refresh_index` with an injected per-write delay.

Usage: slow_refresh.py <repo> <db> <delay_s>

The delay lands inside the write transaction (incremental: per file delta;
full rebuild: before the edge insert), so a SIGKILL during the sleep kills
the writer mid-transaction. Prints one JSON line of RefreshStats on exit.
"""

import dataclasses
import json
import sys
import time
from pathlib import Path

import codemem.incremental as inc
import codemem.indexer as idx

repo, dbp, delay = Path(sys.argv[1]), Path(sys.argv[2]), float(sys.argv[3])

_orig_delta = inc._apply_file_delta
_orig_edges = idx._bulk_insert_edges


def slow_delta(*a, **k):
    time.sleep(delay)
    return _orig_delta(*a, **k)


def slow_edges(*a, **k):
    time.sleep(delay * 20)
    return _orig_edges(*a, **k)


inc._apply_file_delta = slow_delta
idx._bulk_insert_edges = slow_edges
print("READY", flush=True)
stats = inc.refresh_index(repo, dbp)
print(json.dumps(dataclasses.asdict(stats)), flush=True)
