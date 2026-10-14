"""Bounded refresh + stale semantics (code-conventions-impact M15.2, report 03 P0 #1).

Covers report 03 P0 #1 AC (a)-(e) and its edge cases (no git, detached HEAD,
shallow clone / orphaned SHA, dirty tree, missing index), the kill-mid-refresh
recovery, the 15.1 atomic full-rebuild swap, and the real ``codemem refresh``.
"""

from __future__ import annotations

import os
import signal
import sqlite3
import subprocess
import sys
import textwrap
import time
from pathlib import Path

import pytest

from codemem import mcp_tools
from codemem.incremental import check_freshness, refresh_index
from codemem.indexer import build_index

CLI_SRC = (
    Path(__file__).resolve().parents[2] / "packages/codemem-mcp/src/codemem/cli.py"
)


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=True
    ).stdout.strip()


def _commit(root: Path, msg: str = "edit") -> str:
    _git(root, "add", "-A")
    _git(root, "-c", "user.email=t@x", "-c", "user.name=T", "commit", "-qm", msg)
    return _git(root, "rev-parse", "HEAD")


@pytest.fixture
def repo(tmp_path: Path) -> tuple[Path, Path]:
    """Committed git repo with two files and a fresh index."""
    root = tmp_path / "r"
    root.mkdir()
    (root / ".gitignore").write_text(".codemem/\n")
    (root / "a.py").write_text("def helper():\n    return 1\n")
    (root / "b.py").write_text(
        "from a import helper\n\ndef caller():\n    return helper()\n"
    )
    _git(root, "init", "-q", "-b", "main")
    _commit(root, "init")
    db_path = root / ".codemem" / "index.db"
    build_index(root, db_path)
    return root, db_path


def _symbols(db_path: Path) -> set[str]:
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        return {r[0] for r in conn.execute("SELECT name FROM symbols")}
    finally:
        conn.close()


def _log_lines(db_path: Path, prefix: str) -> list[str]:
    log = db_path.parent / "refresh.log"
    if not log.exists():
        return []
    return [ln for ln in log.read_text().splitlines() if prefix in ln]


def _hold_lock_in_child(lock: Path) -> subprocess.Popen:
    """Hold the writer lock from another process (lockf is per-process)."""
    code = textwrap.dedent(
        """
        import sys, time
        from pathlib import Path
        from codemem.journal.lock import acquire_writer_lock
        with acquire_writer_lock(Path(sys.argv[1])) as got:
            print("HELD" if got else "BUSY", flush=True)
            time.sleep(30)
        """
    )
    p = subprocess.Popen(
        [sys.executable, "-c", code, str(lock)], stdout=subprocess.PIPE, text=True
    )
    assert p.stdout is not None
    assert p.stdout.readline().strip() == "HELD"
    return p


def _forbid_refresh_spawn(monkeypatch) -> None:
    """Fail if anything spawns ``codemem.cli`` (git calls still run)."""
    real = subprocess.Popen

    def guarded(argv, *a, **k):
        if "codemem.cli" in list(argv):
            raise AssertionError(f"a refresh was spawned: {argv}")
        return real(argv, *a, **k)

    monkeypatch.setattr(subprocess, "Popen", guarded)


# ---------------------------------------------------------------------
# check_freshness: the cheap in-process pre-check
# ---------------------------------------------------------------------


class TestCheckFreshness:
    def test_fresh_after_build(self, repo):
        root, db_path = repo
        f = check_freshness(root, db_path)
        assert f.stale is False
        assert f.reason is None
        assert f.index_sha == f.head_sha == _git(root, "rev-parse", "HEAD")

    def test_behind_after_commit(self, repo):
        root, db_path = repo
        (root / "c.py").write_text("def new():\n    pass\n")
        head = _commit(root)
        f = check_freshness(root, db_path)
        assert (f.stale, f.reason, f.head_sha) == (True, "behind", head)
        assert f.index_sha != head

    def test_dirty_tree_is_stale_until_refreshed(self, repo):
        root, db_path = repo
        (root / "a.py").write_text("def helper2():\n    return 2\n")
        f = check_freshness(root, db_path)
        assert (f.stale, f.reason) == (True, "dirty")
        refresh_index(root, db_path)
        assert check_freshness(root, db_path).stale is False

    def test_no_git_is_unknown(self, tmp_path):
        (tmp_path / "a.py").write_text("x = 1\n")
        db_path = tmp_path / ".codemem" / "index.db"
        build_index(tmp_path, db_path)
        f = check_freshness(tmp_path, db_path)
        assert (f.stale, f.reason, f.head_sha) == (None, "no_git", None)

    def test_missing_last_sha_is_stale(self, repo):
        root, db_path = repo
        (db_path.parent / "last_sha").unlink()
        f = check_freshness(root, db_path)
        assert (f.stale, f.reason, f.index_sha) == (True, "no_index_sha", None)

    def test_detached_head_compares_sha(self, repo):
        root, db_path = repo
        _git(root, "checkout", "-q", "--detach")
        assert check_freshness(root, db_path).stale is False
        (root / "c.py").write_text("def d():\n    pass\n")
        head = _commit(root)
        f = check_freshness(root, db_path)
        assert (f.stale, f.reason, f.head_sha) == (True, "behind", head)

    def test_malformed_last_sha_is_not_trusted(self, repo):
        root, db_path = repo
        (db_path.parent / "last_sha").write_text("--output=/tmp/x\n")
        f = check_freshness(root, db_path)
        assert (f.stale, f.reason, f.index_sha) == (True, "no_index_sha", None)


# ---------------------------------------------------------------------
# refresh_index: orphaned SHA, atomic full rebuild, kill recovery
# ---------------------------------------------------------------------


class TestRefreshIndex:
    def test_orphaned_last_sha_full_rebuild(self, repo):
        """Shallow clone / force-push: last_sha is not in history → full rebuild."""
        root, db_path = repo
        (db_path.parent / "last_sha").write_text("0" * 40 + "\n")
        (root / "c.py").write_text("def orphan_case():\n    pass\n")
        _commit(root)
        stats = refresh_index(root, db_path)
        assert stats.full_rebuild is True
        assert "orphan_case" in _symbols(db_path)
        assert check_freshness(root, db_path).stale is False

    def test_option_shaped_last_sha_never_reaches_git(self, repo, monkeypatch):
        """last_sha is repo-controlled: only 40-hex is passed to git; anything else rebuilds."""
        root, db_path = repo
        import codemem.incremental as inc

        argvs: list[list[str]] = []
        real_run = inc.subprocess.run

        def spy(argv, *a, **k):
            argvs.append(list(argv))
            return real_run(argv, *a, **k)

        monkeypatch.setattr(inc.subprocess, "run", spy)
        (db_path.parent / "last_sha").write_text("--output=/tmp/pwned\n")
        stats = refresh_index(root, db_path)
        assert stats.full_rebuild is True
        assert not any("--output=/tmp/pwned" in a for argv in argvs for a in argv)

    def test_full_rebuild_never_unlinks_the_live_db(self, repo, monkeypatch):
        """15.1: readers keep a whole DB while a full rebuild runs (temp DB + os.replace)."""
        root, db_path = repo
        import codemem.incremental as inc

        seen: list[tuple[Path, bool]] = []
        real_build = inc.build_index

        def spy(repo_root, target, **kw):
            seen.append((Path(target), db_path.exists()))
            assert "helper" in _symbols(db_path)  # the live DB is still readable
            return real_build(repo_root, target, **kw)

        monkeypatch.setattr(inc, "build_index", spy)
        (db_path.parent / "last_sha").unlink()
        (root / "c.py").write_text("def rebuilt():\n    pass\n")
        _commit(root)  # discover_files indexes tracked files only
        refresh_index(root, db_path)
        assert seen and seen[0][0] != db_path and seen[0][1] is True
        assert "rebuilt" in _symbols(db_path)
        leftovers = sorted(
            p.name for p in db_path.parent.iterdir() if "rebuild" in p.name
        )
        assert leftovers == []

    def test_long_lived_reader_across_swap(self, repo):
        """The old DB's WAL frames never bleed into the swapped-in DB.

        A reader holding a snapshot pins the old -wal; a writer then commits
        frames there. Kept across the swap, that -wal/-shm pair makes new
        readers of the NEW file see the OLD data (measured 2026-10-14).
        """
        root, db_path = repo
        old = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        old.execute("BEGIN")
        assert old.execute("SELECT count(*) FROM symbols").fetchone()[0] > 0
        writer = sqlite3.connect(db_path)
        writer.execute("PRAGMA wal_autocheckpoint=0")
        writer.execute("CREATE TABLE stale_wal_marker(x)")
        writer.commit()
        assert (db_path.parent / "index.db-wal").stat().st_size > 0
        (db_path.parent / "last_sha").unlink()
        (root / "c.py").write_text("def after_swap():\n    pass\n")
        _commit(root)  # discover_files indexes tracked files only
        refresh_index(root, db_path)
        assert "after_swap" in _symbols(db_path)
        old.execute("SELECT count(*) FROM symbols").fetchone()
        old.close()
        writer.close()
        conn = sqlite3.connect(db_path)
        try:
            assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master")}
            assert "stale_wal_marker" not in tables
        finally:
            conn.close()
        assert "after_swap" in _symbols(db_path)

    @pytest.mark.parametrize("prep", ["incremental", "full_rebuild"])
    def test_killed_refresh_next_refresh_recovers(self, repo, prep):
        root, db_path = repo
        for i in range(6):
            (root / f"m{i}.py").write_text(f"def f{i}():\n    return {i}\n")
        _commit(root)
        if prep == "full_rebuild":
            (db_path.parent / "last_sha").unlink()
        slow = textwrap.dedent(
            """
            import sys, time
            from pathlib import Path
            import codemem.incremental as inc, codemem.indexer as idx
            d, e = inc._apply_file_delta, idx._bulk_insert_edges
            inc._apply_file_delta = lambda *a, **k: (time.sleep(0.2), d(*a, **k))[1]
            idx._bulk_insert_edges = lambda *a, **k: (time.sleep(3), e(*a, **k))[1]
            print("READY", flush=True)
            inc.refresh_index(Path(sys.argv[1]), Path(sys.argv[2]))
            print("DONE", flush=True)
            """
        )
        p = subprocess.Popen(
            [sys.executable, "-c", slow, str(root), str(db_path)],
            stdout=subprocess.PIPE,
            text=True,
        )
        assert p.stdout is not None and p.stdout.readline().strip() == "READY"
        time.sleep(0.6)
        assert p.poll() is None, "refresh finished before the kill"
        os.kill(p.pid, signal.SIGKILL)
        p.wait()
        refresh_index(root, db_path)
        assert {f"f{i}" for i in range(6)} <= _symbols(db_path)
        conn = sqlite3.connect(db_path)
        try:
            assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        finally:
            conn.close()
        assert check_freshness(root, db_path).stale is False


# ---------------------------------------------------------------------
# ensure_fresh / ensure_built: the bounded refresh behind every MCP query
# ---------------------------------------------------------------------


class TestEnsureFresh:
    def test_cap_is_the_cold_build_slo(self):
        assert mcp_tools.REFRESH_CAP_S == 5.0

    def test_a_fresh_index_spawns_nothing(self, repo, monkeypatch):
        root, db_path = repo
        _forbid_refresh_spawn(monkeypatch)
        r = mcp_tools.ensure_fresh(db_path, root)
        assert r["stale"] is False and r["stale_reason"] is None
        assert r["index_sha"] == r["head_sha"]

    def test_b_behind_head_refreshes_and_serves_fresh(self, repo):
        root, db_path = repo
        (root / "c.py").write_text("def fresh_now():\n    pass\n")
        head = _commit(root)
        r = mcp_tools.ensure_fresh(db_path, root)
        assert (r["stale"], r["stale_reason"], r["index_sha"], r["head_sha"]) == (
            False,
            None,
            head,
            head,
        )
        assert "fresh_now" in _symbols(db_path)

    def test_c_lock_held_returns_within_cap_stale_locked(self, repo):
        root, db_path = repo
        (root / "c.py").write_text("def x():\n    pass\n")
        _commit(root)
        holder = _hold_lock_in_child(db_path.parent / "db.lock")
        try:
            t0 = time.monotonic()
            r = mcp_tools.ensure_fresh(db_path, root)
            assert time.monotonic() - t0 < mcp_tools.REFRESH_CAP_S
        finally:
            holder.kill()
            holder.wait()
        assert (r["stale"], r["stale_reason"]) == (True, "locked")
        assert len(_log_lines(db_path, "ensure_fresh:")) == 1

    def test_d_refresh_error_is_stale_error_and_logged(self, repo):
        root, db_path = repo
        (root / "c.py").write_text("def x():\n    pass\n")
        _commit(root)
        db_path.write_bytes(b"not a sqlite database at all" * 10)
        r = mcp_tools.ensure_fresh(db_path, root)
        assert (r["stale"], r["stale_reason"]) == (True, "error")
        assert len(_log_lines(db_path, "ensure_fresh:")) == 1
        assert _log_lines(db_path, "refresh: error")

    def test_timeout_is_stale_then_background_finishes(self, repo):
        root, db_path = repo
        (root / "c.py").write_text("def late():\n    pass\n")
        head = _commit(root)
        r = mcp_tools.ensure_fresh(db_path, root, cap=0.01)
        assert (r["stale"], r["stale_reason"]) == (True, "timeout")
        assert len(_log_lines(db_path, "ensure_fresh:")) == 1
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if check_freshness(root, db_path).stale is False:
                break
            time.sleep(0.1)
        r2 = mcp_tools.ensure_fresh(db_path, root)
        assert (r2["stale"], r2["index_sha"]) == (False, head)

    def test_dirty_tree_refreshes_to_fresh(self, repo):
        root, db_path = repo
        (root / "a.py").write_text("def edited_live():\n    return 3\n")
        r = mcp_tools.ensure_fresh(db_path, root)
        assert (r["stale"], r["stale_reason"]) == (False, None)
        assert "edited_live" in _symbols(db_path)

    def test_e_cold_build_writes_last_sha(self, repo):
        root, db_path = repo
        for p in db_path.parent.iterdir():
            p.unlink()
        r = mcp_tools.ensure_fresh(db_path, root)
        head = _git(root, "rev-parse", "HEAD")
        assert (db_path.parent / "last_sha").read_text().strip() == head
        assert (r["stale"], r["index_sha"]) == (False, head)

    def test_no_git_is_unknown_and_spawns_nothing(self, tmp_path, monkeypatch):
        (tmp_path / "a.py").write_text("x = 1\n")
        db_path = tmp_path / ".codemem" / "index.db"
        _forbid_refresh_spawn(monkeypatch)
        r = mcp_tools.ensure_fresh(db_path, tmp_path)
        assert (r["stale"], r["stale_reason"], r["head_sha"]) == (
            "unknown",
            "no_git",
            None,
        )
        assert db_path.exists()

    def test_other_process_build_wait_is_capped(self, repo):
        root, db_path = repo
        for p in db_path.parent.iterdir():
            if p.name != "db.lock":
                p.unlink()
        holder = _hold_lock_in_child(db_path.parent / "db.lock")
        try:
            t0 = time.monotonic()
            r = mcp_tools.ensure_fresh(db_path, root, cap=0.3)
            waited = time.monotonic() - t0
        finally:
            holder.kill()
            holder.wait()
        assert "error" in r and "0.3" in r["error"]
        assert waited < 2.0

    def test_ensure_built_keeps_its_none_or_error_contract(self, repo):
        root, db_path = repo
        (root / "c.py").write_text("def y():\n    pass\n")
        _commit(root)
        assert mcp_tools.ensure_built(db_path, root) is None
        assert check_freshness(root, db_path).stale is False


# ---------------------------------------------------------------------
# codemem refresh: the real driver
# ---------------------------------------------------------------------


def _cli(root: Path, db_path: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "codemem.cli", "--db", str(db_path), "refresh", *args],
        capture_output=True,
        text=True,
        cwd=root,
    )


class TestRefreshCli:
    def test_refresh_runs_the_driver(self, repo):
        root, db_path = repo
        (root / "c.py").write_text("def via_cli():\n    pass\n")
        head = _commit(root)
        r = _cli(root, db_path)
        assert r.returncode == 0, r.stderr
        assert "placeholder" not in (r.stdout + r.stderr).lower()
        assert "via_cli" in _symbols(db_path)
        assert (db_path.parent / "last_sha").read_text().strip() == head

    def test_refresh_locked_exits_75(self, repo):
        root, db_path = repo
        holder = _hold_lock_in_child(db_path.parent / "db.lock")
        try:
            r = _cli(root, db_path)
        finally:
            holder.kill()
            holder.wait()
        assert r.returncode == 75

    def test_refresh_error_exits_1_and_logs(self, repo):
        root, db_path = repo
        (root / "c.py").write_text("def z():\n    pass\n")
        _commit(root)
        db_path.write_bytes(b"garbage" * 50)
        r = _cli(root, db_path)
        assert r.returncode == 1
        assert _log_lines(db_path, "refresh: error")

    def test_no_placeholder_text_left_in_cli(self):
        assert "placeholder" not in CLI_SRC.read_text().lower()


class TestRefreshLogHardening:
    """refresh.log sits in a repo-controllable dir (L-049: probe the hostile inputs)."""

    def test_symlinked_log_is_not_followed(self, repo, tmp_path):
        root, db_path = repo
        target = tmp_path / "victim-rc"
        target.write_text("original\n")
        log = db_path.parent / "refresh.log"
        log.unlink(missing_ok=True)
        log.symlink_to(target)
        from codemem.incremental import log_refresh

        log_refresh(db_path.parent, "ensure_fresh: probe")
        assert target.read_text() == "original\n"

    def test_one_line_per_message(self, repo):
        root, db_path = repo
        from codemem.incremental import log_refresh

        log_refresh(db_path.parent, "refresh: error X: a\nforged [2026] line\r")
        lines = (db_path.parent / "refresh.log").read_text().splitlines()
        assert len([ln for ln in lines if "forged" in ln]) == 1
        assert not any(ln.startswith("forged") for ln in lines)


class TestRepoControlledInputs:
    """A cloned repo controls its tree and can commit .codemem/ (security review, 2026-10-14)."""

    def test_repo_cannot_shadow_the_codemem_package(self, repo, tmp_path):
        root, db_path = repo
        marker = tmp_path / "pwned"
        (root / "codemem").mkdir()
        (root / "codemem" / "__init__.py").write_text("")
        (root / "codemem" / "cli.py").write_text(
            f"from pathlib import Path\nPath({str(marker)!r}).write_text('ran')\n"
        )
        (root / "c.py").write_text("def x():\n    pass\n")
        _commit(root)
        r = mcp_tools.ensure_fresh(db_path, root)
        assert not marker.exists(), "repo code ran inside the refresh"
        assert r["stale"] is False

    @pytest.mark.parametrize("name", ["tree_sig", "last_sha"])
    def test_sidecar_symlink_is_replaced_not_followed(self, repo, tmp_path, name):
        root, db_path = repo
        victim = tmp_path / "victim-rc"
        victim.write_text("original\n")
        side = db_path.parent / name
        side.unlink(missing_ok=True)
        side.symlink_to(victim)
        (root / "c.py").write_text("def y():\n    pass\n")
        _commit(root)
        refresh_index(root, db_path)
        assert victim.read_text() == "original\n"
        assert not side.is_symlink()

    def test_repo_git_config_runs_nothing(self, repo, tmp_path):
        """`git ls-files` / `status` run a repo's core.fsmonitor (measured 2026-10-14)."""
        root, db_path = repo
        marker = tmp_path / "ran"
        hook = tmp_path / "hook.sh"
        hook.write_text(f"#!/bin/sh\necho ran >> {marker}\ncat\n")
        hook.chmod(0o755)
        _git(root, "config", "core.fsmonitor", str(hook))
        _git(root, "config", "filter.evil.clean", str(hook))
        (root / ".gitattributes").write_text("*.py filter=evil\n")
        (root / "a.py").write_text("def edited():\n    return 9\n")
        check_freshness(root, db_path)
        refresh_index(root, db_path)
        (db_path.parent / "last_sha").unlink()
        refresh_index(root, db_path)  # full rebuild path
        mcp_tools.ensure_fresh(db_path, root)
        assert not marker.exists(), marker.read_text()
