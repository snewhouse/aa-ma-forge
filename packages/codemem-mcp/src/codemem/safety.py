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

import errno
import hashlib
import hmac
import os
import secrets
import sqlite3
import stat
import tempfile
from pathlib import Path

__all__ = [
    "GIT_TIMEOUT_S",
    "SAFE_GIT",
    "NONCE_BYTES",
    "TRUST_KEY",
    "TrustStoreError",
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

# 128-bit nonce: unguessable by a repo that cannot read the user's state dir.
NONCE_BYTES = 16
# A record is one hex nonce line; reading more than this means it is not one.
_RECORD_MAX_BYTES = 256
# os.link errnos meaning "this filesystem has no hard links" (FUSE, SMB, exFAT).
_NO_HARD_LINKS = {errno.EPERM, errno.ENOTSUP, errno.EOPNOTSUPP, errno.EXDEV}


class UnsafeDbPath(OSError):
    """The DB dir is a symlink, holds one, cannot be listed, or its index is untrusted."""


class UntrustedIndex(UnsafeDbPath):
    """The index carries no stamp for this user and directory: codemem did not build it here."""


class TrustStoreError(OSError):
    """This user's trust store cannot be read or written: a local fault, not a repo's."""


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


def _check_store_dir(store: Path) -> None:
    """Raise :class:`TrustStoreError` unless ``store`` is this user's private directory.

    A shared ``XDG_STATE_HOME`` (another user created ``codemem/trust`` first,
    or made it writable) would let them plant a nonce they know.
    """
    try:
        st = store.lstat()
    except FileNotFoundError:
        return
    except OSError as exc:
        raise TrustStoreError(
            f"trust store {store} unreadable ({type(exc).__name__})"
        ) from exc
    private = (
        stat.S_ISDIR(st.st_mode) and st.st_uid == os.getuid() and not st.st_mode & 0o022
    )
    if not private:
        raise TrustStoreError(
            f"trust store {store} is not a private directory of this user"
        )


def _read_record(rec: Path) -> str | None:
    """The nonce in ``rec``; None if the record is absent or empty."""
    _check_store_dir(rec.parent)
    try:
        fd = os.open(rec, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        with os.fdopen(fd, "rb") as fh:
            data = fh.read(_RECORD_MAX_BYTES)
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise TrustStoreError(
            f"trust store {rec.parent} unreadable ({type(exc).__name__})"
        ) from exc
    try:
        return data.decode("ascii").strip() or None
    except UnicodeDecodeError as exc:
        raise TrustStoreError(f"trust record {rec} does not hold a nonce") from exc


def _publish(tmp: Path, rec: Path) -> None:
    """Make ``tmp`` the record: whole or not at all, and never over another's."""
    try:
        os.link(tmp, rec)
    except FileExistsError:
        return  # a concurrent build created it first; use theirs
    except OSError as exc:
        if exc.errno not in _NO_HARD_LINKS:
            raise
        # No hard links on this filesystem: create it directly (a reader may briefly see it empty).
        try:
            fd = os.open(
                rec,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
                0o600,
            )
        except FileExistsError:
            return
        with os.fdopen(fd, "w") as fh:
            fh.write(tmp.read_text())
            fh.flush()
            os.fsync(fh.fileno())


def _nonce(db_dir: Path, *, create: bool) -> str | None:
    """This user's nonce for ``db_dir``; None if there is none and ``create`` is off.

    Raises :class:`TrustStoreError` when the store itself cannot be used, so a
    broken state dir is never mistaken for a hostile index. An empty record
    (a crash before its data reached disk) stamps nothing, so creating
    replaces it.
    """
    rec = trust_record(db_dir)
    nonce = _read_record(rec)
    if nonce is not None or not create:
        return nonce
    try:
        # why: only the leaf dir gets 0700 from mkdir; _check_store_dir rejects a shared one
        rec.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        _check_store_dir(rec.parent)
        fd, name = tempfile.mkstemp(
            dir=rec.parent, prefix=f".{rec.name}.", suffix=".tmp"
        )
        tmp = Path(name)
        try:
            with os.fdopen(fd, "w") as fh:
                fh.write(secrets.token_hex(NONCE_BYTES) + "\n")
                fh.flush()
                os.fsync(
                    fh.fileno()
                )  # the record must never appear empty after a crash
            if rec.exists():
                os.replace(tmp, rec)  # it was empty: nothing was stamped with it
            else:
                _publish(tmp, rec)
        finally:
            tmp.unlink(missing_ok=True)
    except TrustStoreError:
        raise
    except OSError as exc:
        raise TrustStoreError(
            f"trust store {rec.parent} unwritable ({type(exc).__name__})"
        ) from exc
    nonce = _read_record(rec)
    if nonce is None:
        raise TrustStoreError(f"trust record {rec} is empty after writing it")
    return nonce


def stamp(conn: sqlite3.Connection, db_dir: Path) -> None:
    """Mark a DB codemem has just created in ``db_dir`` as built here.

    Raises :class:`TrustStoreError` when the trust store cannot be used.
    """
    nonce = _nonce(db_dir, create=True)
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
    if row is None:
        return False
    # bytes: compare_digest raises TypeError on a non-ASCII str
    stored = str(row[0]).encode("utf-8", "surrogatepass")
    return hmac.compare_digest(stored, nonce.encode())
