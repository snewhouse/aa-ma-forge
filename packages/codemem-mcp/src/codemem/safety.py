"""codemem's one rule for repo-controlled inputs (M15 §6.8).

``.codemem/`` is repo-controllable: a clone can commit it, or any entry in it,
as a link to a user file (one refresh would overwrite the target with SQLite,
and even a read-only open of a WAL-mode target creates ``-wal``/``-shm`` beside
it), or commit a whole index whose rows do not match the code and have it
served as fresh. Every reader (``storage.db.connect``) and every writer
(``indexer.build_index``, ``incremental.refresh_index``, ``mcp_tools.ensure_fresh``)
applies :func:`check_db_path`, so readers refuse exactly what writers refuse.
``aa_ma.render.graph`` carries a twin (aa_ma never imports codemem).
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

__all__ = ["GIT_TIMEOUT_S", "SAFE_GIT", "UnsafeDbPath", "check_db_path"]

# Every git call on the index path. Command-scope config outranks the repo's
# own .git/config, which can name commands git runs: `git ls-files` and
# `git status` both run core.fsmonitor (measured 2026-10-14).
SAFE_GIT = ("git", "-c", "core.fsmonitor=false", "-c", "core.hooksPath=/dev/null")

# Per git call on the query path. A healthy local rev-parse / ls-files takes
# ms; past 1 s git is wedged (a stuck index.lock, a hung mount) and the answer
# is "unknown". Same budget as the session-start Code-intel line.
GIT_TIMEOUT_S = 1.0


class UnsafeDbPath(OSError):
    """The DB dir is a symlink, holds one, is tracked by git, or cannot be checked."""


def check_db_path(db_path: Path) -> None:
    """Raise :class:`UnsafeDbPath` unless ``db_path``'s dir is codemem's own.

    Refused when the dir, or ANY entry in it, is a symlink (a list of names
    goes stale: SQLite alone adds ``-journal``), when git tracks anything in
    it, or when it cannot be listed or git cannot answer. A missing dir is
    fine (the caller creates it). The message names only the dir, never a
    repo-chosen entry. Point ``CODEMEM_DB`` at a dedicated dir.
    """
    db_dir = Path(db_path).parent
    unsafe = UnsafeDbPath(
        f"{db_dir} is a symlink, holds one, or is tracked by git; codemem refuses it"
    )
    if db_dir.is_symlink():
        raise unsafe
    try:
        linked = any(p.is_symlink() for p in db_dir.iterdir())
    except FileNotFoundError:
        return
    except OSError as exc:  # a regular file named .codemem, or unreadable
        raise UnsafeDbPath(
            f"{db_dir} cannot be listed ({type(exc).__name__}); codemem refuses it"
        ) from exc
    if linked:
        raise unsafe
    try:
        tracked = subprocess.run(  # noqa: S603  # why: fixed `git` argv, no shell
            [*SAFE_GIT, "-C", str(db_dir), "ls-files", "-z", "--", "."],
            capture_output=True,
            timeout=GIT_TIMEOUT_S,
            check=False,
            env={
                **os.environ,
                "LC_ALL": "C",
            },  # stable message text for the check below
        )
    except FileNotFoundError:
        # ponytail: with no git installed a tracked index cannot be detected;
        # every freshness answer is then stale "unknown" (no_git), leads only.
        return
    except subprocess.TimeoutExpired as exc:
        raise UnsafeDbPath(
            f"{db_dir}: git did not answer in {GIT_TIMEOUT_S:g}s; codemem refuses it"
        ) from exc
    if tracked.returncode == 0:
        if tracked.stdout:
            raise unsafe
    elif b"not a git repository" not in tracked.stderr:
        # Fail closed: e.g. "dubious ownership" is a repo git refused to read.
        raise UnsafeDbPath(
            f"{db_dir}: git could not list it (rc {tracked.returncode}); codemem refuses it"
        )
