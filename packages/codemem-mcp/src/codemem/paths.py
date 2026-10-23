"""Where codemem keeps a repo's index by default (code-conventions-impact M16).

Not in the repo: ``.codemem/`` was repo-controlled, and a clone could commit a
WAL, a rollback journal or a stamped index beside the real one for SQLite to
replay (M15 §6.8 re-run 3). The index is derived data, so it goes to the XDG
cache, one dir per checkout: ``$XDG_CACHE_HOME/codemem/<sha256(realpath root)>/``.

Twins (same formula, pinned by tests/codemem/test_safety_parity.py):
``aa_ma.render.graph._default_db_path`` and ``aa_ma_codemem_dir`` in
``claude-code/hooks/lib/aa-ma-parse.sh``.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path


def cache_home() -> Path:
    """``$XDG_CACHE_HOME``, or ``~/.cache`` when it is unset or relative (XDG spec)."""
    env = os.environ.get("XDG_CACHE_HOME", "")
    return Path(env) if os.path.isabs(env) else Path.home() / ".cache"


def default_db_path(repo_root: Path) -> Path:
    """The index file codemem uses for ``repo_root`` when ``--db``/``CODEMEM_DB`` is unset."""
    key = hashlib.sha256(os.fsencode(os.path.realpath(repo_root))).hexdigest()
    return cache_home() / "codemem" / key / "index.db"


def resolve_db_path(repo_root: Path, db: str | os.PathLike | None = None) -> Path:
    """``db``, else ``$CODEMEM_DB``, else the default; always absolute.

    Absolute because the capped refresh runs with cwd = the DB dir, where a
    relative path names another file (M15 pre-merge MEDIUM).
    """
    chosen = db or os.environ.get("CODEMEM_DB") or default_db_path(repo_root)
    return Path(chosen).absolute()
