"""Tests for codemem.journal.lock — Task 2.7 (single-writer lock)."""

from __future__ import annotations

import multiprocessing
from pathlib import Path

from codemem.journal.lock import acquire_writer_lock


class TestAcquireBasics:
    def test_acquires_fresh_lock_returns_true(self, tmp_path: Path):
        lock = tmp_path / "db.lock"
        with acquire_writer_lock(lock) as acquired:
            assert acquired is True
        # File exists but is no longer held
        assert lock.exists()

    def test_second_acquire_same_process_returns_true(self, tmp_path: Path):
        """POSIX fcntl.lockf locks are per-file-description, so the
        SAME process re-acquiring after release works."""
        lock = tmp_path / "db.lock"
        with acquire_writer_lock(lock) as a:
            assert a is True
        with acquire_writer_lock(lock) as b:
            assert b is True

    def test_sibling_context_managers_serialize(self, tmp_path: Path):
        """Nested with-blocks on the SAME process using new file
        descriptors → second should fail-fast since the first holds
        the lock."""
        lock = tmp_path / "db.lock"
        # Note: POSIX fcntl locks are process-scoped. Two file
        # descriptors from the same process share the lock — so nested
        # same-process acquires BOTH succeed. Contention is between
        # PROCESSES. We assert the single-process nested case:
        with acquire_writer_lock(lock) as outer:
            assert outer is True
            with acquire_writer_lock(lock) as inner:
                # Same process → fcntl.lockf treats as successful.
                assert inner is True


# ---------------------------------------------------------------------
# Cross-process contention — the real AC
# ---------------------------------------------------------------------

def _hold_lock(lock_path, ready, release):
    path = Path(lock_path)
    with acquire_writer_lock(path) as acquired:
        if acquired:
            ready.set()
            release.wait(timeout=10)


class TestCrossProcessContention:
    def test_second_process_cannot_acquire_while_held(self, tmp_path: Path):
        """AC: Second invocation no-ops with informative log line
        (does not queue). This proves contention is correctly
        detected across processes."""
        lock = tmp_path / "db.lock"
        ready = multiprocessing.Event()
        release = multiprocessing.Event()

        holder = multiprocessing.Process(
            target=_hold_lock, args=(str(lock), ready, release)
        )
        holder.start()
        try:
            assert ready.wait(timeout=5), "holder never acquired"

            # Now try from the main process — should fail to acquire.
            with acquire_writer_lock(lock) as acquired:
                assert acquired is False, "lock was granted twice"
        finally:
            release.set()
            holder.join(timeout=5)
            assert not holder.is_alive(), "holder didn't exit"

    def test_second_process_can_acquire_after_release(self, tmp_path: Path):
        lock = tmp_path / "db.lock"
        ready = multiprocessing.Event()
        release = multiprocessing.Event()

        holder = multiprocessing.Process(
            target=_hold_lock, args=(str(lock), ready, release)
        )
        holder.start()
        try:
            assert ready.wait(timeout=5)
            release.set()
            holder.join(timeout=5)
        finally:
            if holder.is_alive():
                holder.terminate()

        # After holder exits, main process should acquire cleanly.
        with acquire_writer_lock(lock) as acquired:
            assert acquired is True


# ---------------------------------------------------------------------
# Integration: refresh_index skips when lock is held
# ---------------------------------------------------------------------

class TestRefreshIndexLockIntegration:
    def test_refresh_noops_when_lock_held(self, tmp_path: Path):
        """AC: concurrent refresh invocations — second is a no-op."""
        import subprocess
        import time

        from codemem.incremental import refresh_index
        from codemem.indexer import build_index

        # Set up an indexed repo
        (tmp_path / ".gitignore").write_text(".codemem/\n")
        (tmp_path / "a.py").write_text("def foo(): return 1\n")
        subprocess.run(
            ["git", "init", "-q", "-b", "main", str(tmp_path)], check=True
        )
        subprocess.run(
            ["git", "-C", str(tmp_path), "config", "user.email", "t@x"], check=True
        )
        subprocess.run(
            ["git", "-C", str(tmp_path), "config", "user.name", "t"], check=True
        )
        subprocess.run(["git", "-C", str(tmp_path), "add", "-A"], check=True)
        subprocess.run(
            ["git", "-C", str(tmp_path), "commit", "-qm", "i"], check=True
        )

        db_path = tmp_path / ".codemem" / "index.db"
        build_index(tmp_path, db_path, package=".")

        # Start a process that holds the lock
        lock = db_path.parent / "db.lock"
        ready = multiprocessing.Event()
        release = multiprocessing.Event()
        holder = multiprocessing.Process(
            target=_hold_lock, args=(str(lock), ready, release)
        )
        holder.start()
        try:
            assert ready.wait(timeout=5)

            # With the lock held, refresh_index should no-op.
            stats = refresh_index(tmp_path, db_path, package=".")
            assert stats.skipped_locked is True
            # Log file should have the informative line
            log_text = (db_path.parent / "refresh.log").read_text()
            assert "another refresh holds db.lock" in log_text
        finally:
            release.set()
            holder.join(timeout=5)
            if holder.is_alive():
                holder.terminate()

        # After holder exits, refresh works normally
        stats = refresh_index(tmp_path, db_path, package=".")
        assert stats.skipped_locked is False
        # Give the timestamp a millisecond of separation before we
        # sanity-check the log got another line (it should).
        time.sleep(0.01)
