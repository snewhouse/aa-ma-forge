"""Process-level single-writer lock (M2 Task 2.7).

Cross-platform: ``fcntl.lockf`` on POSIX, ``msvcrt.locking`` on
Windows. Exposed as a context manager ``acquire_writer_lock(path)`` —
when the lock is already held, yields ``False`` so the caller can
no-op (not queue) with an informative log line.

Usage::

    with acquire_writer_lock(Path(".codemem/db.lock")) as acquired:
        if not acquired:
            return  # another writer is active; we no-op

        # ... do the write ...

Separate from ``refresh.pid`` (Task 2.5 — the post-commit hook's
process-tracking file). ``db.lock`` is ABOUT THE DB; ``refresh.pid``
is ABOUT THE HOOK. Read MCP connections use ``mode=ro`` on the SQLite
URI and never touch either file.
"""

from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


__all__ = ["acquire_writer_lock"]


_IS_WINDOWS = sys.platform == "win32"


@contextmanager
def acquire_writer_lock(path: Path) -> Iterator[bool]:
    """Try to acquire an exclusive advisory lock on ``path``.

    Yields ``True`` if acquired (caller can proceed with writes),
    ``False`` if another process already holds it (caller should
    no-op). Either way, the lock is released on context exit.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    # O_CREAT so the lock file exists; O_WRONLY because we need a
    # write fd to lock on POSIX (shared-read fds can only take
    # shared-read locks).
    fd = os.open(path, os.O_CREAT | os.O_WRONLY, 0o644)

    try:
        acquired = _try_lock(fd)
        try:
            yield acquired
        finally:
            if acquired:
                _unlock(fd)
    finally:
        os.close(fd)


def _try_lock(fd: int) -> bool:
    """Return True if we got the exclusive lock, False if another
    process holds it. Never raises on contention (uses non-blocking)."""
    if _IS_WINDOWS:
        return _try_lock_windows(fd)
    return _try_lock_posix(fd)


def _unlock(fd: int) -> None:
    if _IS_WINDOWS:
        _unlock_windows(fd)
    else:
        _unlock_posix(fd)


# ---------------------------------------------------------------------
# POSIX implementation — fcntl.lockf with LOCK_EX | LOCK_NB
# ---------------------------------------------------------------------

def _try_lock_posix(fd: int) -> bool:
    import fcntl

    try:
        fcntl.lockf(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except (BlockingIOError, OSError):
        # EAGAIN / EACCES → held by another process
        return False


def _unlock_posix(fd: int) -> None:
    import fcntl

    try:
        fcntl.lockf(fd, fcntl.LOCK_UN)
    except OSError:
        pass  # unlock failures at shutdown are non-fatal


# ---------------------------------------------------------------------
# Windows implementation — msvcrt.locking
# ---------------------------------------------------------------------

def _try_lock_windows(fd: int) -> bool:  # pragma: no cover — POSIX CI
    import msvcrt

    try:
        msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        return True
    except OSError:
        return False


def _unlock_windows(fd: int) -> None:  # pragma: no cover — POSIX CI
    import msvcrt

    try:
        msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
    except OSError:
        pass
