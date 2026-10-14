"""codemem's rules for repo-controlled inputs (M15 §6.8).

``.codemem/`` is repo-controllable. A clone can commit it, or any entry in it,
as a link to a user file: one refresh would overwrite the target with SQLite,
and even a read-only open of a WAL-mode target creates ``-wal``/``-shm`` beside
it. :func:`check_db_path` refuses such a dir. A clone (or a zip) can also ship a
whole index whose rows do not match the code. Detecting that through git was
bypassed four ways, so codemem trusts only an index it built itself: a DB file
codemem creates is stamped with this user's nonce for its directory, kept
outside the repo (:func:`trust_record`), and :func:`is_trusted` compares the
two. ``storage.db.connect`` applies both rules for every reader and writer;
``aa_ma.render.graph`` carries a twin (aa_ma never imports codemem), pinned by
``tests/codemem/test_safety_parity.py``.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import sqlite3
from pathlib import Path

__all__ = [
    "GIT_TIMEOUT_S",
    "SAFE_GIT",
    "TRUST_KEY",
    "UnsafeDbPath",
    "UntrustedIndex",
    "check_db_path",
    "is_trusted",
    "stamp",
    "trust_record",
]

# Every git call on the index path. Command-scope config outranks the repo's
# own .git/config, which can name commands git runs: `git ls-files` and
# `git status` both run core.fsmonitor (measured 2026-10-14).
SAFE_GIT = ("git", "-c", "core.fsmonitor=false", "-c", "core.hooksPath=/dev/null")

# Per git call on the query path. A healthy local rev-parse / ls-files takes
# ms; past 1 s git is wedged (a stuck index.lock, a hung mount) and the answer
# is "unknown". Same budget as the session-start Code-intel line.
GIT_TIMEOUT_S = 1.0


# The ``meta`` row holding a DB's stamp.
TRUST_KEY = "trust_nonce"


class UnsafeDbPath(OSError):
    """The DB dir is a symlink, holds one, cannot be listed, or its index is untrusted."""


class UntrustedIndex(UnsafeDbPath):
    """The index carries no stamp for this user and directory: codemem did not build it here."""


def check_db_path(db_path: Path) -> None:
    """Raise :class:`UnsafeDbPath` if ``db_path``'s dir is, holds or hides a symlink.

    Refused when the dir, or ANY entry in it, is a symlink (a list of names
    goes stale: SQLite alone adds ``-journal``), or when it cannot be listed
    (e.g. a regular file named ``.codemem``). A missing dir is fine (the
    caller creates it). The message names only the dir, never a repo-chosen
    entry. Point ``CODEMEM_DB`` at a dedicated dir.
    """
    db_dir = Path(db_path).parent
    if db_dir.is_symlink():
        raise UnsafeDbPath(f"{db_dir} is a symlink; codemem refuses it")
    try:
        linked = any(p.is_symlink() for p in db_dir.iterdir())
    except FileNotFoundError:
        return
    except OSError as exc:
        raise UnsafeDbPath(
            f"{db_dir} cannot be listed ({type(exc).__name__}); codemem refuses it"
        ) from exc
    if linked:
        raise UnsafeDbPath(f"{db_dir} holds a symlink; codemem refuses it")


def trust_record(db_dir: Path) -> Path:
    """This user's nonce file for ``db_dir``: outside every repo, keyed by its real path."""
    state = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    key = hashlib.sha256(os.fsencode(os.path.realpath(db_dir))).hexdigest()
    return Path(state) / "codemem" / "trust" / key


def _nonce(db_dir: Path, *, create: bool) -> str | None:
    rec = trust_record(db_dir)
    try:
        return rec.read_text().strip() or None
    except FileNotFoundError:
        if not create:
            return None
    except OSError:
        return None
    rec.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        fd = os.open(rec, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return _nonce(db_dir, create=False)  # a concurrent build created it first
    with os.fdopen(fd, "w") as fh:
        fh.write(secrets.token_hex(16) + "\n")
    return _nonce(db_dir, create=False)


def stamp(conn: sqlite3.Connection, db_dir: Path) -> None:
    """Mark a DB codemem has just created in ``db_dir`` as built here."""
    nonce = _nonce(db_dir, create=True)
    if nonce is None:
        raise UnsafeDbPath(
            f"cannot record trust for {db_dir} in {trust_record(db_dir).parent}"
        )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)"
    )
    conn.execute(
        "INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)", (TRUST_KEY, nonce)
    )
    conn.commit()


def is_trusted(conn: sqlite3.Connection, db_dir: Path) -> bool:
    """Whether the open DB carries this user's nonce for ``db_dir``."""
    nonce = _nonce(db_dir, create=False)
    if nonce is None:
        return False
    try:
        row = conn.execute(
            "SELECT value FROM meta WHERE key = ?", (TRUST_KEY,)
        ).fetchone()
    except sqlite3.Error:
        return False
    return row is not None and hmac.compare_digest(str(row[0]), nonce)
