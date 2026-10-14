"""M15.1 prototype: bounded codemem refresh — thread vs subprocess, kill safety.

Throwaway. Run from the forge worktree: `uv run --no-sync python proto.py <forge_root>`.
Prints one line per experiment; exit 0 even when a check fails (it is evidence).
"""

import os
import shutil
import signal
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

from codemem.incremental import refresh_index
from codemem.indexer import build_index
from codemem.journal.lock import acquire_writer_lock
from codemem import mcp_tools

HERE = Path(__file__).resolve().parent
SLOW = HERE / "slow_refresh.py"
PY = sys.executable
N_FILES = 60


def git(repo, *args):
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


def make_repo(root: Path, variant: int) -> None:
    pkg = root / "pkg"
    pkg.mkdir(parents=True, exist_ok=True)
    for i in range(N_FILES):
        nxt = (i + 1) % N_FILES
        (pkg / f"m{i}.py").write_text(
            f"from pkg.m{nxt} import f{nxt}_0\n\n"
            + "".join(
                f"def f{i}_{j}(x):\n    return f{nxt}_0(x) + {variant}\n\n"
                for j in range(4 + variant)
            )
        )
    (pkg / "__init__.py").write_text("")


def counts(db: Path) -> tuple:
    c = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        return (
            c.execute("SELECT count(*) FROM files").fetchone()[0],
            c.execute("SELECT count(*) FROM symbols").fetchone()[0],
            c.execute("SELECT count(*) FROM (SELECT DISTINCT * FROM edges)").fetchone()[
                0
            ],
        )
    finally:
        c.close()


def integrity(db: Path) -> str:
    c = sqlite3.connect(str(db))
    try:
        return c.execute("PRAGMA integrity_check").fetchone()[0]
    finally:
        c.close()


def lock_free(lock: Path) -> bool:
    # Separate process: lockf is per-process, an in-process probe would always pass.
    code = (
        "import sys; from pathlib import Path; from codemem.journal.lock import acquire_writer_lock\n"
        "with acquire_writer_lock(Path(sys.argv[1])) as a: print(a)"
    )
    r = subprocess.run([PY, "-c", code, str(lock)], capture_output=True, text=True)
    return r.stdout.strip() == "True"


def kill_mid(repo: Path, db: Path, delay: float, after: float) -> str:
    p = subprocess.Popen(
        [PY, str(SLOW), str(repo), str(db), str(delay)],
        stdout=subprocess.PIPE,
        text=True,
    )
    assert p.stdout.readline().strip() == "READY"
    time.sleep(after)
    if p.poll() is not None:
        return "finished-before-kill"
    os.kill(p.pid, signal.SIGKILL)
    p.wait()
    return "killed"


def fixture(tmp: Path) -> tuple[Path, Path, str]:
    repo = tmp / "repo"
    make_repo(repo, 0)
    git(repo, "init", "-q")
    git(repo, "add", "-A")
    git(repo, "-c", "user.email=p@x", "-c", "user.name=p", "commit", "-qm", "v0")
    db = repo / ".codemem" / "index.db"
    build_index(repo, db)
    old = git(repo, "rev-parse", "HEAD")
    make_repo(repo, 1)
    git(repo, "add", "-A")
    git(repo, "-c", "user.email=p@x", "-c", "user.name=p", "commit", "-qm", "v1")
    return repo, db, old


def cold_counts(repo: Path, tmp: Path) -> tuple:
    ref = tmp / "ref.db"
    build_index(repo, ref)
    return counts(ref)


def experiment_kill(name: str, prep) -> None:
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        repo, db, old = fixture(tmp)
        prep(repo, db)
        outcome = kill_mid(repo, db, delay=0.1, after=1.0)
        lsf = db.parent / "last_sha"
        last = lsf.read_text().strip() if lsf.exists() else "absent"
        ok_lock = lock_free(db.parent / "db.lock")
        integ = integrity(db) if db.exists() else "no-db"
        stats = refresh_index(repo, db)
        after_counts, ref = counts(db), cold_counts(repo, tmp)
        print(
            f"{name}: kill={outcome} lock_free={ok_lock} integrity={integ} "
            f"last_sha_after_kill={'old' if last == old else last[:8]} "
            f"next_refresh(full={stats.full_rebuild}, dirty={stats.files_dirty}) "
            f"counts={after_counts} cold={ref} match={after_counts == ref}"
        )


def experiment_thread_lock() -> None:
    with tempfile.TemporaryDirectory() as t:
        lock = Path(t) / "db.lock"
        got = []
        barrier = threading.Barrier(2)

        def hold():
            with acquire_writer_lock(lock) as a:
                got.append(a)
                barrier.wait()
                barrier.wait()

        th = [threading.Thread(target=hold) for _ in range(2)]
        for x in th:
            x.start()
        for x in th:
            x.join()
        print(
            f"thread-lock: two threads, one process, both acquired={got} "
            f"(True,True = lockf does not exclude threads)"
        )


def time_query(repo: Path, db: Path) -> float:
    t0 = time.perf_counter()
    mcp_tools.search_symbols(db, "refresh", budget=2000)
    return (time.perf_counter() - t0) * 1000


def experiment_latency(forge: Path) -> None:
    with tempfile.TemporaryDirectory() as t:
        repo = Path(t) / "forge"
        shutil.copytree(
            forge,
            repo,
            ignore=shutil.ignore_patterns(
                ".venv", ".codemem", "node_modules", "graphify-out"
            ),
            symlinks=True,
        )
        db = repo / ".codemem" / "index.db"
        build_index(repo, db)
        base = sorted(time_query(repo, db) for _ in range(20))[10]
        # In-process no-op refresh (fresh index) vs subprocess no-op refresh.
        t0 = time.perf_counter()
        refresh_index(repo, db)
        inproc_noop = (time.perf_counter() - t0) * 1000
        t0 = time.perf_counter()
        subprocess.run(
            [
                PY,
                "-c",
                "import sys;from pathlib import Path;from codemem.incremental import refresh_index;"
                "refresh_index(Path(sys.argv[1]),Path(sys.argv[2]))",
                str(repo),
                str(db),
            ],
            check=True,
        )
        sub_noop = (time.perf_counter() - t0) * 1000
        # Force a full rebuild and query while it runs: thread arm.
        (db.parent / "last_sha").unlink()
        th = threading.Thread(target=refresh_index, args=(repo, db), daemon=True)
        t0 = time.perf_counter()
        th.start()
        lat_thread = []
        while th.is_alive():
            if db.exists():
                try:
                    lat_thread.append(time_query(repo, db))
                except Exception as e:  # prototype: record, keep going
                    lat_thread.append(f"ERR {type(e).__name__}")
        thread_total = (time.perf_counter() - t0) * 1000
        # Subprocess arm: same forced rebuild.
        (db.parent / "last_sha").unlink()
        t0 = time.perf_counter()
        p = subprocess.Popen(
            [
                PY,
                "-c",
                "import sys;from pathlib import Path;from codemem.incremental import refresh_index;"
                "refresh_index(Path(sys.argv[1]),Path(sys.argv[2]))",
                str(repo),
                str(db),
            ]
        )
        lat_sub = []
        while p.poll() is None:
            if db.exists():
                try:
                    lat_sub.append(time_query(repo, db))
                except Exception as e:
                    lat_sub.append(f"ERR {type(e).__name__}")
        sub_total = (time.perf_counter() - t0) * 1000

        def summ(xs):
            nums = sorted(x for x in xs if isinstance(x, float))
            errs = [x for x in xs if not isinstance(x, float)]
            if not nums:
                return f"n=0 errs={len(errs)} {sorted(set(errs))}"
            return f"n={len(nums)} p50={nums[len(nums) // 2]:.1f}ms max={nums[-1]:.1f}ms errs={len(errs)} {sorted(set(errs))[:3]}"

        print(
            f"latency(forge copy): query baseline p50={base:.1f}ms; no-op refresh in-process={inproc_noop:.0f}ms "
            f"subprocess={sub_noop:.0f}ms"
        )
        print(
            f"  during full rebuild — thread arm total={thread_total:.0f}ms queries {summ(lat_thread)}"
        )
        print(
            f"  during full rebuild — subprocess arm total={sub_total:.0f}ms queries {summ(lat_sub)}"
        )


def experiment_cap() -> None:
    """Subprocess left running past the 5 s cap finishes and the next query is fresh."""
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        repo, db, old = fixture(tmp)
        head = git(repo, "rev-parse", "HEAD")
        p = subprocess.Popen(
            [PY, str(SLOW), str(repo), str(db), "0.12"],
            stdout=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        t0 = time.perf_counter()
        try:
            p.wait(timeout=5)
            capped = False
        except subprocess.TimeoutExpired:
            capped = True
        waited = time.perf_counter() - t0
        lsf = db.parent / "last_sha"
        mid = lsf.read_text().strip()
        p.wait()
        end = lsf.read_text().strip()
        print(
            f"cap: returned after {waited:.2f}s timed_out={capped}; last_sha at cap={'old' if mid == old else 'HEAD' if mid == head else mid[:8]} "
            f"after background finish={'HEAD' if end == head else end[:8]} counts={counts(db)} cold={cold_counts(repo, tmp)}"
        )


def main() -> None:
    forge = Path(sys.argv[1])
    experiment_thread_lock()
    experiment_kill("kill-incremental (mid-txn)", lambda r, d: None)
    experiment_kill(
        "kill-full-rebuild (last_sha removed)",
        lambda r, d: (d.parent / "last_sha").unlink(),
    )
    experiment_kill(
        "kill-full-rebuild (DB removed, last_sha valid)", lambda r, d: d.unlink()
    )
    experiment_cap()
    experiment_latency(forge)


if __name__ == "__main__":
    main()
