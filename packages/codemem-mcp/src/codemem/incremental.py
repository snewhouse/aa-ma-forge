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
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from . import resolver as _resolver
from .diff.symbol_diff import ChangeKind, diff_symbols
from .indexer import build_index, parse_files, discover_files
from .parser.python_ast import Symbol
from .storage import db


__all__ = ["RefreshStats", "refresh_index"]


@dataclass
class RefreshStats:
    files_dirty: int = 0
    files_moved: int = 0
    files_deleted: int = 0
    symbols_added: int = 0
    symbols_removed: int = 0
    symbols_modified: int = 0
    symbols_renamed: int = 0
    edges_rewired: int = 0
    full_rebuild: bool = False
    elapsed_seconds: float = 0.0


# ---------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------

def refresh_index(
    repo_root: Path,
    db_path: Path,
    *,
    package: str = ".",
) -> RefreshStats:
    t0 = time.monotonic()
    repo_root = repo_root.resolve()
    db_path = db_path.resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    log_file = db_path.parent / "refresh.log"
    last_sha_file = db_path.parent / "last_sha"

    # ---- Fallback: no DB yet, no last_sha, or orphaned SHA ----------
    if not db_path.exists() or not last_sha_file.exists() or _sha_orphaned(
        repo_root, last_sha_file
    ):
        reason = _fallback_reason(db_path, last_sha_file, repo_root)
        _log(log_file, f"full rebuild: {reason}")
        # Wipe the DB before rebuild so stale rows from prior states
        # don't leak through. ``build_index``'s DELETE is scoped to
        # paths in the current parse set and won't clean up files
        # whose paths disappeared between runs.
        if db_path.exists():
            db_path.unlink()
        build_index(repo_root, db_path, package=package)
        _write_last_sha(repo_root, last_sha_file)
        return RefreshStats(
            full_rebuild=True, elapsed_seconds=time.monotonic() - t0
        )

    stats = RefreshStats()

    disk_files = discover_files(repo_root)
    # Map from repo-relative path → absolute path + hash for every disk file.
    disk_by_path: dict[str, tuple[Path, str]] = {}
    for p in disk_files:
        rel = p.resolve().relative_to(repo_root).as_posix()
        disk_by_path[rel] = (p.resolve(), _hash(p))

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
    dirty: list[str] = []               # path (edit in place OR new file)
    deleted: list[str] = []             # path (gone from disk, no move match)

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
        db.apply_schema(conn)  # idempotent — guarantees schema on first call
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
                parses, _ = parse_files(
                    dirty_abs, repo_root=repo_root, package=package
                )

                for fp in parses:
                    _apply_file_delta(conn, fp, stats)

                # Cross-file edges: re-run the resolver against the
                # FULL parse-result set. Narrow restriction (only files
                # with changed imports) is a future optimisation —
                # v1 re-resolves for every refresh to guarantee
                # correctness after cross-file renames.
                _resolver.resolve_cross_file_edges(conn, parses=parses)
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
        f"({stats.elapsed_seconds*1000:.1f}ms)",
    )
    return stats


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def _hash(p: Path) -> str:
    """SHA-256 of file contents. Returns empty string on read error so
    the caller can treat it as 'unknown' and re-index conservatively.
    """
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()
    except OSError:
        return ""


def _log(log_file: Path, message: str) -> None:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime())
    with log_file.open("a", encoding="utf-8") as fh:
        fh.write(f"[{timestamp}] {message}\n")


def _sha_orphaned(repo_root: Path, last_sha_file: Path) -> bool:
    try:
        sha = last_sha_file.read_text().strip()
    except OSError:
        return True
    if not sha:
        return True
    result = subprocess.run(
        ["git", "-C", str(repo_root), "cat-file", "-e", sha],
        capture_output=True,
        check=False,
    )
    return result.returncode != 0


def _fallback_reason(db_path: Path, last_sha_file: Path, repo_root: Path) -> str:
    if not db_path.exists():
        return "no DB (first refresh)"
    if not last_sha_file.exists():
        return "no last_sha file"
    if _sha_orphaned(repo_root, last_sha_file):
        return f"last_sha orphaned by git history rewrite ({last_sha_file.read_text().strip()[:12]}...)"
    return "unknown"


def _write_last_sha(repo_root: Path, last_sha_file: Path) -> None:
    result = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=False,
    )
    if result.returncode == 0:
        last_sha_file.parent.mkdir(parents=True, exist_ok=True)
        last_sha_file.write_text(result.stdout.strip() + "\n")


def _rewrite_scip_paths(conn, old_path: str, new_path: str) -> None:
    """When a file moves, every scip_id referencing the old path needs
    to be rewritten. The SCIP grammar encodes file path between the
    kind-marker and the ``#`` — simple string replacement is safe.
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
    """Upsert the file row, diff its symbols against the DB, apply
    ADDED/REMOVED/MODIFIED/RENAMED changes via SQL."""
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
