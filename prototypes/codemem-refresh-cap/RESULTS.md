# M15.1 prototype — bounded codemem refresh (2026-10-14)

Question: how do we cap `refresh_index` (synchronous, no timeout) at 5 s, and is a kill mid-run safe?

| Experiment | Result |
|---|---|
| Two threads, one process, `acquire_writer_lock` on one path | both acquired (`fcntl.lockf` is per-process) — a thread arm needs its own in-process guard |
| SIGKILL mid incremental transaction | lock free, integrity ok, `last_sha` unchanged; next refresh dirty=60, counts == cold build |
| SIGKILL mid full rebuild (`last_sha` removed) | lock free, integrity ok; next refresh full rebuild, counts == cold build |
| SIGKILL mid full rebuild (DB removed, `last_sha` valid) | lock free, integrity ok; next refresh incremental dirty=61, counts == cold build |
| Subprocess past the 5 s cap, left running (`start_new_session`) | caller returns at 5.00 s with `last_sha` old; background run finishes, `last_sha` == HEAD, counts == cold |
| No-op refresh on aa-ma-forge copy | in-process 68 ms, subprocess 125 ms; `git rev-parse HEAD` 3.8 ms, `git status --porcelain -uno` 6.4 ms |
| Readers during an in-place full rebuild (today's fallback unlinks `index.db`) | ~23k polls raised `unable to open database file` / `no such table` / `disk I/O error`; 856 OK — **both arms** |
| Full rebuild into `index.db.tmp-<pid>`, checkpoint, `os.replace` (×5) under a looping reader | 1802/1802 reads OK, 0 errors, integrity ok |

Verdict: **subprocess** (B). Spawn only when an in-process pre-check (last_sha vs HEAD, porcelain) says stale;
wait ≤ 5 s; on timeout leave it running detached and serve `stale=true, reason=timeout`. Kill-safety holds today.
**Plan change:** the full-rebuild fallback must build to a temp DB and `os.replace` it (atomic for readers);
risk to test in 15.2: a long-lived reader holding the old `index.db-wal` across the swap.

Run: `uv run --no-sync python prototypes/codemem-refresh-cap/proto.py "$PWD"` (also `probe_readers.py`, `probe_swap.py`).
