"""Incremental refresh driver (M2 Task 2.2).

Turns cold-build `build_index` into a fast warm-path `refresh_index`
that only re-parses and re-persists dirty files, respecting git
metadata to handle moves and history rewrites correctly.

Dirty-detection order of precedence:

1. If ``.codemem/last_sha`` is absent OR
   ``git cat-file -e <last_sha>`` fails (history rewrite orphaned it),
   fall back to a FULL REBUILD via :func:`codemem.indexer.build_index`.
   A warning is written to ``.codemem/refresh.log``.
2. Otherwise, content-hash every currently-tracked file and compare
   against the DB's ``files`` table.
3. Files with a hash matching a DB row at a **different path** are
   treated as moves (``git mv``) — the existing file row's ``path``
   is rewritten, preserving all dependent symbols + edges. The AC
   explicitly requires moves NOT be emitted as add+remove.
4. Files with changed hash at the same path → re-parse, diff against
   old DB symbols, apply ADDED/REMOVED/MODIFIED deltas (RENAMED from
   :mod:`codemem.diff.symbol_diff` becomes an in-place UPDATE of
   ``symbols.name`` + ``scip_id``).
5. New files on disk → full parse + insert.
6. DB rows whose path vanished from disk and whose hash didn't match
   any moved candidate → delete (CASCADE cleans dependent rows).

Cross-file resolver is re-run only for files whose ``imports``
actually changed (cheap import-set-diff check).
"""

from __future__ import annotations

import hashlib
import logging
import os
import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from . import resolver as _resolver
from .diff.symbol_diff import ChangeKind, diff_symbols
from .indexer import (
    GIT_TIMEOUT_S,
    SAFE_GIT,
    UnsafeDbPath,
    build_index,
    check_db_path,
    discover_files,
    parse_files,
    tree_signature,
    write_sidecar,
)
from .journal.lock import acquire_writer_lock
from .parser.python_ast import Symbol
from .storage import db


__all__ = [
    "EXIT_LOCKED",
    "Freshness",
    "RefreshStats",
    "UnsafeDbPath",
    "check_freshness",
    "log_refresh",
    "refresh_index",
]

# `codemem refresh` exit code when another refresh holds db.lock: EX_TEMPFAIL
# (sysexits.h), "try again later". Read by mcp_tools.ensure_fresh.
EXIT_LOCKED = 75

logger = logging.getLogger(__name__)

# `.codemem/last_sha` and `tree_sig` are repo-controlled (a clone can commit
# them): only a full SHA-1 (40-hex) or SHA-256 (64-hex) is ever passed to git.
_SHA_RE = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")


@dataclass
class RefreshStats:
    """Counters and timing reported by :func:`refresh_index`."""

    files_dirty: int = 0
    files_moved: int = 0
    files_deleted: int = 0
    symbols_added: int = 0
    symbols_removed: int = 0
    symbols_modified: int = 0
    symbols_renamed: int = 0
    edges_rewired: int = 0
    full_rebuild: bool = False
    # M2 Task 2.7: set when a concurrent refresh held the writer lock;
    # this refresh no-opped rather than queued.
    skipped_locked: bool = False
    elapsed_seconds: float = 0.0


@dataclass(frozen=True)
class Freshness:
    """How the index at a DB path relates to the working tree (report 03 X2).

    ``stale`` is True, False, or None when it cannot be known (no git).
    ``reason`` names why it is stale or unknown: ``behind``, ``dirty``,
    ``no_index_sha``, ``no_git`` or ``no_head``.
    """

    index_sha: str | None
    head_sha: str | None
    stale: bool | None
    reason: str | None


def check_freshness(repo_root: Path, db_path: Path) -> Freshness:
    """Cheap in-process staleness check (~15 ms on aa-ma-forge when fresh, M15 §6.6).

    First, an index codemem did not build here is stale ``untrusted`` whatever
    its sidecars say (M15 §6.8). Then compares ``last_sha`` with HEAD, then the
    working tree's signature with the one the last refresh recorded. Runs no
    refresh itself.
    """
    head = _git(repo_root, "rev-parse", "--verify", "-q", "HEAD")
    if not db.index_trusted(db_path):
        return Freshness(None, head, True, "untrusted")
    index_sha = _read_sha(db_path.parent / "last_sha")
    if head is None:
        inside = _git(repo_root, "rev-parse", "--git-dir") is not None
        return Freshness(index_sha, None, None, "no_head" if inside else "no_git")
    if index_sha is None:
        return Freshness(None, head, True, "no_index_sha")
    if index_sha != head:
        return Freshness(index_sha, head, True, "behind")
    stored = _read_text(db_path.parent / "tree_sig")
    if stored is None or tree_signature(discover_files(repo_root)) != stored:
        return Freshness(index_sha, head, True, "dirty")
    return Freshness(index_sha, head, False, None)


def log_refresh(db_dir: Path, message: str) -> None:
    """Append one timestamped line to ``<db_dir>/refresh.log``."""
    _log(db_dir / "refresh.log", message)


# ---------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------


def refresh_index(
    repo_root: Path,
    db_path: Path,
    *,
    package: str = ".",
) -> RefreshStats:
    """Refresh the index at ``db_path`` to match the working tree under ``repo_root``.

    Holds the single-writer lock; if another refresh holds it, returns at once
    with ``skipped_locked`` set. Raises :class:`UnsafeDbPath` per
    :func:`codemem.safety.check_db_path`. An index codemem did not build here
    is rebuilt in full.

    Args:
        repo_root: Root of the repository to index.
        db_path: Path to the SQLite index; its parent also holds the log,
            ``last_sha`` and lock files.
        package: Package name used when building SCIP ids.

    Returns:
        A :class:`RefreshStats` describing what changed.
    """
    t0 = time.monotonic()
    repo_root = repo_root.resolve()
    # Never resolve db_path: following a planted link is the attack.
    db_path = db_path.absolute()
    check_db_path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    log_file = db_path.parent / "refresh.log"
    lock_file = db_path.parent / "db.lock"

    # M2 Task 2.7: single-writer lock. If another refresh holds it,
    # no-op (don't queue) — the currently-running refresh will pick
    # up our changes since it re-scans disk state.
    with acquire_writer_lock(lock_file) as acquired:
        if not acquired:
            _log(log_file, "refresh: skipped (another refresh holds db.lock)")
            return RefreshStats(
                skipped_locked=True, elapsed_seconds=time.monotonic() - t0
            )
        # Taken before reading the tree: an edit made during the refresh
        # leaves the stored signature behind, so the next check re-runs.
        disk_files = discover_files(repo_root)
        sig = tree_signature(disk_files)
        stats = _refresh_locked(
            repo_root,
            db_path,
            package=package,
            t0=t0,
            disk_files=disk_files,
        )
        write_sidecar(db_path.parent / "tree_sig", sig + "\n")
        return stats


def _refresh_locked(  # noqa: C901  # why: pre-existing; refactor tracked in TODOS.md (M8.2 D8 pay-down, no logic change in a security milestone)
    repo_root: Path,
    db_path: Path,
    *,
    package: str,
    t0: float,
    disk_files: list[Path],
) -> RefreshStats:
    log_file = db_path.parent / "refresh.log"
    last_sha_file = db_path.parent / "last_sha"
    # ---- Fallback: no DB yet, no last_sha, or orphaned SHA ----------
    if (
        not db_path.exists()
        or not db.index_trusted(db_path)
        or not last_sha_file.exists()
        or _sha_orphaned(repo_root, last_sha_file)
    ):
        reason = _fallback_reason(db_path, last_sha_file, repo_root)
        _log(log_file, f"full rebuild: {reason}")
        # Build from empty so stale rows from prior states don't leak
        # through (``build_index``'s DELETE is scoped to the current parse
        # set). Never in place: readers keep the old DB until the swap.
        _rebuild_and_swap(repo_root, db_path, package=package)
        _write_last_sha(repo_root, last_sha_file)
        return RefreshStats(full_rebuild=True, elapsed_seconds=time.monotonic() - t0)

    stats = RefreshStats()

    # Map from repo-relative path → absolute path + hash for every disk file
    # (discover_files already returns resolved paths).
    disk_by_path: dict[str, tuple[Path, str]] = {}
    for p in disk_files:
        rel = p.relative_to(repo_root).as_posix()
        disk_by_path[rel] = (p, _hash(p))

    # Map from DB-stored path → (id, content_hash) so we can diff.
    with db.connect(db_path, read_only=True) as conn:
        db_rows = {
            path: (fid, chash)
            for path, fid, chash in conn.execute(
                "SELECT path, id, content_hash FROM files"
            )
        }

    # --- Classify changes ---------------------------------------------
    moved: list[tuple[str, str]] = []  # (old_path, new_path)
    dirty: list[str] = []  # path (edit in place OR new file)
    deleted: list[str] = []  # path (gone from disk, no move match)

    disk_hashes: dict[str, str] = {rel: h for rel, (_, h) in disk_by_path.items()}
    db_hashes: dict[str, str] = {
        path: h for path, (_, h) in db_rows.items() if h is not None
    }

    # Detect moves by hash FIRST so we don't misclassify as delete+add.
    unchanged_disk_paths: set[str] = set()
    matched_db_paths: set[str] = set()
    for disk_path, disk_hash in disk_hashes.items():
        if disk_path in db_rows:
            if db_rows[disk_path][1] == disk_hash:
                unchanged_disk_paths.add(disk_path)
            else:
                dirty.append(disk_path)
            matched_db_paths.add(disk_path)

    for disk_path, disk_hash in disk_hashes.items():
        if disk_path in matched_db_paths:
            continue
        # Unmatched disk path — maybe a move from a DB path with same hash
        moved_from = next(
            (
                db_path_
                for db_path_, db_hash in db_hashes.items()
                if db_hash == disk_hash
                and db_path_ not in matched_db_paths
                and db_path_ not in disk_hashes
            ),
            None,
        )
        if moved_from is not None:
            moved.append((moved_from, disk_path))
            matched_db_paths.add(moved_from)
        else:
            dirty.append(disk_path)  # brand-new file

    for db_path_ in db_rows:
        if db_path_ not in matched_db_paths:
            deleted.append(db_path_)

    stats.files_dirty = len(dirty)
    stats.files_moved = len(moved)
    stats.files_deleted = len(deleted)

    if not (dirty or moved or deleted):
        _write_last_sha(repo_root, last_sha_file)
        stats.elapsed_seconds = time.monotonic() - t0
        return stats

    # ---- Apply mutations ---------------------------------------------
    conn = db.connect(db_path, read_only=False)
    try:
        # apply_schema + migrate — see L-253 and db.ensure_schema docstring.
        db.ensure_schema(conn)
        with db.transaction(conn):
            for old_path, new_path in moved:
                conn.execute(
                    "UPDATE files SET path = ? WHERE path = ?",
                    (new_path, old_path),
                )
                # Symbols on a moved file keep their rows; scip_ids encode
                # file paths, so we have to rewrite them too.
                _rewrite_scip_paths(conn, old_path, new_path)

            for path in deleted:
                conn.execute("DELETE FROM files WHERE path = ?", (path,))
                # CASCADE handles dependent symbols + edges

            if dirty:
                dirty_abs = [disk_by_path[p][0] for p in dirty]
                parses, _ = parse_files(dirty_abs, repo_root=repo_root, package=package)

                for fp in parses:
                    _apply_file_delta(conn, fp, stats)

                # Cross-file edges: re-run the resolver against the
                # FULL parse-result set. Narrow restriction (only files
                # with changed imports) is a future optimisation —
                # v1 re-resolves for every refresh to guarantee
                # correctness after cross-file renames.
                _resolver.resolve_cross_file_edges(conn, parses=parses)

        # M2 Task 2.6: checkpoint SQLite WAL after a meaningful batch
        # so -wal file size doesn't grow unbounded across many
        # refreshes. Executed outside the transaction since
        # wal_checkpoint is a PRAGMA.
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    finally:
        conn.close()

    _write_last_sha(repo_root, last_sha_file)
    stats.elapsed_seconds = time.monotonic() - t0
    _log(
        log_file,
        f"refresh: dirty={stats.files_dirty} moved={stats.files_moved} "
        f"deleted={stats.files_deleted} added={stats.symbols_added} "
        f"removed={stats.symbols_removed} modified={stats.symbols_modified} "
        f"renamed={stats.symbols_renamed} "
        f"({stats.elapsed_seconds * 1000:.1f}ms)",
    )
    return stats


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------


def _hash(p: Path) -> str:
    """SHA-256 of file contents.

    Returns empty string on read error so the caller can treat it as
    'unknown' and re-index conservatively.
    """
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    except OSError:
        return ""


def _log(log_file: Path, message: str) -> None:
    """Append one line to ``log_file``; never through a symlink; never raises.

    ``.codemem/`` is repo-controllable (a clone can commit
    ``refresh.log -> ~/.bashrc``, or ``.codemem`` itself as a link), and
    messages can carry repo-controlled text such as file names in exception
    messages: newlines are folded so one call is one line, and a symlinked
    log or log directory is refused.
    """
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime())
    line = " ".join(message.splitlines())
    flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    try:
        if log_file.parent.is_symlink():
            raise OSError(f"{log_file.parent.name} is a symlink")
        log_file.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(log_file, flags, 0o644)
    except OSError as exc:
        logger.warning("refresh.log not written (%s): %s", type(exc).__name__, log_file)
        return
    with os.fdopen(fd, "a", encoding="utf-8") as fh:
        fh.write(f"[{timestamp}] {line}\n")


def _rebuild_and_swap(repo_root: Path, db_path: Path, *, package: str) -> None:
    """Full build into a sibling file, then ``os.replace`` it over the live DB.

    The caller holds db.lock. An in-place unlink made every concurrent
    reader raise for the whole rebuild (M15.1: ~23k errors on aa-ma-forge);
    the swap is atomic for readers. The old DB's ``-wal``/``-shm`` are
    unlinked first: a reader still holding them keeps its own (now
    nameless) copies, and new readers of the new DB start clean instead
    of replaying the old DB's WAL frames into it.
    """
    tmp = db_path.with_name(db_path.name + ".rebuild")
    for leftover in _db_files(tmp):  # a rebuild killed mid-run
        leftover.unlink(missing_ok=True)
    build_index(repo_root, tmp, package=package, write_sidecars=False)
    for side in _db_files(tmp)[1:] + _db_files(db_path)[1:]:
        side.unlink(missing_ok=True)
    os.replace(tmp, db_path)


def _db_files(path: Path) -> list[Path]:
    """The SQLite file and its WAL-mode sidecars, main file first."""
    return [
        path,
        path.with_name(path.name + "-wal"),
        path.with_name(path.name + "-shm"),
    ]


def _git(repo_root: Path, *args: str) -> str | None:
    """Stdout of a git command, or None when git fails or is missing."""
    try:
        result = subprocess.run(  # noqa: S603  # why: fixed `git` argv, no shell
            [*SAFE_GIT, "-C", str(repo_root), *args],
            capture_output=True,
            text=True,
            check=False,
            timeout=GIT_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired:
        logger.warning(
            "git %s timed out after %gs; freshness unknown", args[0], GIT_TIMEOUT_S
        )
        return None
    except OSError:
        return None
    return result.stdout.strip() if result.returncode == 0 else None


# A sidecar is one SHA or signature line; bounds the read of a planted huge file.
_SIDECAR_MAX_BYTES = 128


def _read_text(path: Path) -> str | None:
    """A sidecar's one line; None if absent, unreadable, empty or a symlink.

    Python twin of the shell's ``aa_ma_read_sidecar_sha`` (aa-ma-parse.sh):
    same byte bound, only trailing newlines dropped. The DB dir itself is
    checked by ``indexer.check_db_path`` before any refresh.
    """
    if path.is_symlink():
        return None
    try:
        with path.open("rb") as fh:
            text = fh.read(_SIDECAR_MAX_BYTES).decode("ascii")
    except (OSError, UnicodeDecodeError):
        return None
    return text.rstrip("\n") or None


def _read_sha(path: Path) -> str | None:
    """A 40- or 64-hex SHA from ``path``, or None for anything else (repo-controlled file)."""
    text = _read_text(path)
    return text if text is not None and _SHA_RE.fullmatch(text) else None


def _sha_orphaned(repo_root: Path, last_sha_file: Path) -> bool:
    sha = _read_sha(last_sha_file)
    return sha is None or _git(repo_root, "cat-file", "-e", sha) is None


def _fallback_reason(db_path: Path, last_sha_file: Path, repo_root: Path) -> str:
    if not db_path.exists():
        return "no DB (first refresh)"
    if not db.index_trusted(db_path):
        return "index not built by codemem here (untrusted)"
    if not last_sha_file.exists():
        return "no last_sha file"
    sha = _read_sha(last_sha_file)
    if sha is None:
        return "last_sha malformed (not a 40/64-hex SHA)"  # never echo repo-controlled text
    if _sha_orphaned(repo_root, last_sha_file):
        return f"last_sha orphaned by git history rewrite ({sha[:12]}...)"
    return "unknown"


def _write_last_sha(repo_root: Path, last_sha_file: Path) -> None:
    head = _git(repo_root, "rev-parse", "HEAD")
    if head is not None:
        last_sha_file.parent.mkdir(parents=True, exist_ok=True)
        write_sidecar(last_sha_file, head + "\n")


def _rewrite_scip_paths(conn, old_path: str, new_path: str) -> None:
    """Rewrite every scip_id that references a moved file's old path.

    The SCIP grammar encodes file path between the kind-marker and the
    ``#`` — simple string replacement is safe.
    """
    # Build the SCIP ID prefix: ``codemem <package> <marker><file>#`` —
    # the file portion is what changes. Update every row that references
    # the moved file (they all share file_id after the UPDATE above).
    file_id = conn.execute(
        "SELECT id FROM files WHERE path = ?", (new_path,)
    ).fetchone()
    if not file_id:
        return
    rows = conn.execute(
        "SELECT id, scip_id FROM symbols WHERE file_id = ?", (file_id[0],)
    ).fetchall()
    for sid, old_scip in rows:
        new_scip = old_scip.replace(old_path, new_path)
        if new_scip != old_scip:
            conn.execute(
                "UPDATE symbols SET scip_id = ? WHERE id = ?",
                (new_scip, sid),
            )


def _apply_file_delta(conn, fp, stats: RefreshStats) -> None:
    """Upsert the file row, diff its symbols against the DB, and apply the changes.

    ADDED/REMOVED/MODIFIED/RENAMED changes are applied via SQL.
    """
    now = int(time.time())
    conn.execute(
        """
        INSERT INTO files (path, lang, mtime, size, content_hash, last_indexed)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(path) DO UPDATE SET
            lang         = excluded.lang,
            mtime        = excluded.mtime,
            size         = excluded.size,
            content_hash = excluded.content_hash,
            last_indexed = excluded.last_indexed
        """,
        (fp.rel_to_repo, fp.lang, fp.mtime, fp.size, fp.content_hash, now),
    )
    fid = conn.execute(
        "SELECT id FROM files WHERE path = ?", (fp.rel_to_repo,)
    ).fetchone()[0]

    # Load existing symbols for this file as Symbol records so the
    # Task 2.1 diff can compare like-for-like.
    existing: list[Symbol] = []
    for row in conn.execute(
        """
        SELECT scip_id, name, kind, line, signature, signature_hash,
               docstring, parent_id
        FROM symbols WHERE file_id = ?
        """,
        (fid,),
    ):
        existing.append(
            Symbol(
                scip_id=row[0],
                name=row[1],
                kind=row[2],
                line=row[3] or 0,
                signature=row[4],
                signature_hash=row[5],
                docstring=row[6],
                parent_scip_id=None,  # parent_id is int, diff keys on scip_id
            )
        )

    diff = diff_symbols(existing, fp.result.symbols)

    for change in diff.changes:
        if change.kind == ChangeKind.ADDED:
            _insert_symbol(conn, fid, change.new)
            stats.symbols_added += 1
        elif change.kind == ChangeKind.REMOVED:
            conn.execute(
                "DELETE FROM symbols WHERE file_id = ? AND scip_id = ?",
                (fid, change.old.scip_id),
            )
            stats.symbols_removed += 1
        elif change.kind == ChangeKind.MODIFIED:
            conn.execute(
                """
                UPDATE symbols SET
                    line = ?, signature = ?, signature_hash = ?, docstring = ?
                WHERE file_id = ? AND scip_id = ?
                """,
                (
                    change.new.line,
                    change.new.signature,
                    change.new.signature_hash,
                    change.new.docstring,
                    fid,
                    change.old.scip_id,
                ),
            )
            stats.symbols_modified += 1
        elif change.kind == ChangeKind.RENAMED:
            # Update name + scip_id in place — incoming edges (pointing
            # to this symbol id) survive unharmed.
            conn.execute(
                """
                UPDATE symbols SET
                    scip_id = ?, name = ?, line = ?, signature = ?,
                    signature_hash = ?, docstring = ?
                WHERE file_id = ? AND scip_id = ?
                """,
                (
                    change.new.scip_id,
                    change.new.name,
                    change.new.line,
                    change.new.signature,
                    change.new.signature_hash,
                    change.new.docstring,
                    fid,
                    change.old.scip_id,
                ),
            )
            stats.symbols_renamed += 1
        # UNCHANGED is a no-op.


def _insert_symbol(conn, file_id: int, sym: Symbol) -> None:
    conn.execute(
        """
        INSERT INTO symbols
            (file_id, scip_id, name, kind, line, signature, signature_hash,
             docstring, parent_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL)
        ON CONFLICT(file_id, scip_id) DO NOTHING
        """,
        (
            file_id,
            sym.scip_id,
            sym.name,
            sym.kind,
            sym.line,
            sym.signature,
            sym.signature_hash,
            sym.docstring,
        ),
    )
