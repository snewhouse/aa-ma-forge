"""Indexer driver — file discovery + parse + bulk insert (M1 Task 1.5).

Entry points:

* :func:`discover_files` — uses ``git ls-files`` when the target is a git
  repo (so ``.gitignore`` is respected for free); falls back to a plain
  directory walk otherwise.
* :func:`build_index` — end-to-end pipeline:
  discover → dispatch-per-language parse → bulk insert into SQLite.

Bulk-insert strategy (per AC):
    ``PRAGMA foreign_keys = OFF`` toggled around the executemany batch,
    then ``PRAGMA foreign_keys = ON`` + ``PRAGMA foreign_key_check``
    verifies no orphaned references slipped in. This avoids per-row FK
    validation cost during bulk load without sacrificing correctness.
"""

from __future__ import annotations

import hashlib
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from . import resolver as _resolver
from .journal import wal as _wal
from .parser import ast_grep, python_ast
from .parser.python_ast import ParseResult
from .storage import db


__all__ = ["BuildStats", "build_index", "discover_files", "parse_files"]


# Extensions we recognise. Files with any other extension are skipped —
# not indexed, not inserted. The indexer is source-code aware; docs and
# assets aren't in scope for v1.
_INDEXABLE_EXTENSIONS: frozenset[str] = frozenset(
    {".py"}
    | {ext for exts in ast_grep.SUPPORTED_LANGUAGES.values() for ext in exts}
)


@dataclass
class BuildStats:
    files_indexed: int = 0
    symbols_inserted: int = 0
    edges_inserted: int = 0
    cross_file_resolved: int = 0
    cross_file_unresolved: int = 0
    elapsed_seconds: float = 0.0
    python_parse_errors: int = 0


# ---------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------

def discover_files(repo_root: Path) -> list[Path]:
    """Return absolute paths to indexable files under ``repo_root``.

    Uses ``git ls-files`` when available so ``.gitignore`` is honoured
    for free. Falls back to ``Path.rglob`` when the target isn't a git
    repo or ``git`` isn't on PATH.

    Files that git tracks but are missing from the working tree
    (e.g. user deleted without ``git rm``) are filtered out — we
    can't index what we can't read.
    """
    repo_root = repo_root.resolve()
    tracked = _git_tracked_files(repo_root)
    if tracked is not None:
        candidates = tracked
    else:
        candidates = [p for p in repo_root.rglob("*") if p.is_file()]

    return [
        p for p in candidates
        if p.suffix.lower() in _INDEXABLE_EXTENSIONS and p.is_file()
    ]


def _git_tracked_files(repo_root: Path) -> list[Path] | None:
    """Return git-tracked files (absolute paths), or ``None`` if not a git repo."""
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "ls-files"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return None
    if result.returncode != 0:
        return None
    return [
        (repo_root / line).resolve()
        for line in result.stdout.splitlines()
        if line.strip()
    ]


# ---------------------------------------------------------------------
# Parse dispatch
# ---------------------------------------------------------------------

@dataclass
class _FileParse:
    path: Path              # absolute
    rel_to_repo: str        # posix string relative to repo_root
    lang: str
    result: ParseResult
    content_hash: str
    mtime: int
    size: int


def parse_files(
    files: list[Path],
    *,
    repo_root: Path,
    package: str,
) -> tuple[list[_FileParse], int]:
    """Parse each file with the appropriate parser. Python uses the stdlib
    parser one file at a time; other languages batch via ast-grep.

    Returns ``(parses, python_parse_errors)`` — second value counts files
    whose Python parse returned an empty ParseResult (caller metric).
    """
    repo_root = repo_root.resolve()
    py_files: list[Path] = []
    sg_files: list[Path] = []
    for f in files:
        if f.suffix == ".py":
            py_files.append(f)
        elif ast_grep.language_from_path(f) is not None:
            sg_files.append(f)

    parses: list[_FileParse] = []
    python_parse_errors = 0

    # --- Python (stdlib ast) -------------------------------------------
    for p in py_files:
        try:
            source = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        rel = p.resolve().relative_to(repo_root).as_posix()
        pr = python_ast.extract_python_signatures(
            source, package=package, file_rel=rel
        )
        if not pr.symbols and source.strip():
            python_parse_errors += 1  # file had content but we got nothing
        parses.append(
            _FileParse(
                path=p.resolve(),
                rel_to_repo=rel,
                lang="python",
                result=pr,
                content_hash=hashlib.sha256(source.encode("utf-8")).hexdigest(),
                mtime=int(p.stat().st_mtime),
                size=len(source.encode("utf-8")),
            )
        )

    # --- ast-grep batched ---------------------------------------------
    if sg_files:
        sg_results = ast_grep.extract_with_ast_grep(
            sg_files, package=package, repo_root=repo_root
        )
        for p in sg_files:
            pr = sg_results.get(p, ParseResult(symbols=[], edges=[]))
            try:
                source = p.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            rel = p.resolve().relative_to(repo_root).as_posix()
            lang = (ast_grep.language_from_path(p) or "unknown").lower()
            parses.append(
                _FileParse(
                    path=p.resolve(),
                    rel_to_repo=rel,
                    lang=lang,
                    result=pr,
                    content_hash=hashlib.sha256(source.encode("utf-8")).hexdigest(),
                    mtime=int(p.stat().st_mtime),
                    size=len(source.encode("utf-8")),
                )
            )

    return parses, python_parse_errors


# ---------------------------------------------------------------------
# Bulk insert
# ---------------------------------------------------------------------

def _upsert_files(conn, parses: list[_FileParse]) -> dict[str, int]:
    """Insert/update a row per file; return path → file_id map."""
    now = int(time.time())
    for fp in parses:
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
    rows = conn.execute("SELECT path, id FROM files").fetchall()
    return {path: fid for path, fid in rows}


def _bulk_insert_symbols(conn, parses: list[_FileParse], path_to_fid: dict[str, int]) -> int:
    """Insert symbols for every parse; return total rows inserted.

    Uses ``INSERT OR REPLACE`` keyed on ``(file_id, scip_id)`` so a
    re-index of the same file replaces in place (idempotent rebuild).
    parent_id starts NULL; resolved in a second pass.
    """
    rows: list[tuple] = []
    for fp in parses:
        fid = path_to_fid.get(fp.rel_to_repo)
        if fid is None:
            continue
        for s in fp.result.symbols:
            rows.append(
                (
                    fid,
                    s.scip_id,
                    s.name,
                    s.kind,
                    s.line,
                    s.signature,
                    s.signature_hash,
                    s.docstring,
                )
            )
    if not rows:
        return 0
    conn.executemany(
        """
        INSERT INTO symbols
            (file_id, scip_id, name, kind, line, signature, signature_hash, docstring, parent_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL)
        ON CONFLICT(file_id, scip_id) DO UPDATE SET
            name            = excluded.name,
            kind            = excluded.kind,
            line            = excluded.line,
            signature       = excluded.signature,
            signature_hash  = excluded.signature_hash,
            docstring       = excluded.docstring
        """,
        rows,
    )
    return len(rows)


def _resolve_parent_ids(conn, parses: list[_FileParse]) -> None:
    """Second-pass UPDATE that fills in parent_id via scip_id → id lookup."""
    rows = conn.execute("SELECT scip_id, id FROM symbols").fetchall()
    scip_to_id = {scip: sid for scip, sid in rows}

    updates: list[tuple[int, str]] = []
    for fp in parses:
        for s in fp.result.symbols:
            if s.parent_scip_id is None:
                continue
            parent_id = scip_to_id.get(s.parent_scip_id)
            if parent_id is not None:
                updates.append((parent_id, s.scip_id))
    if updates:
        conn.executemany(
            "UPDATE symbols SET parent_id = ? WHERE scip_id = ?",
            updates,
        )


def _bulk_insert_edges(conn, parses: list[_FileParse]) -> int:
    """Insert edges after symbol IDs are known. Unresolved edges (dst None)
    are persisted via ``dst_unresolved`` column; Task 1.6 fills in later.
    """
    rows = conn.execute("SELECT scip_id, id FROM symbols").fetchall()
    scip_to_id = {scip: sid for scip, sid in rows}

    edge_rows: list[tuple[int, int | None, str | None, str]] = []
    for fp in parses:
        for e in fp.result.edges:
            src_id = scip_to_id.get(e.src_scip_id)
            if src_id is None:
                continue  # src not persisted (shouldn't happen but defensive)
            dst_id = scip_to_id.get(e.dst_scip_id) if e.dst_scip_id else None
            dst_unresolved = e.dst_unresolved
            if dst_id is None and dst_unresolved is None and e.dst_scip_id:
                # Have a scip target but it wasn't persisted — leave as string
                dst_unresolved = e.dst_scip_id
            if dst_id is None and dst_unresolved is None:
                continue  # schema CHECK would reject
            edge_rows.append((src_id, dst_id, dst_unresolved, e.kind))
    if not edge_rows:
        return 0
    conn.executemany(
        """
        INSERT OR IGNORE INTO edges
            (src_symbol_id, dst_symbol_id, dst_unresolved, kind)
        VALUES (?, ?, ?, ?)
        """,
        edge_rows,
    )
    return len(edge_rows)


# ---------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------

def _parse_result_to_wal_args(fp) -> dict:
    """Serialise a file parse for persistence as a WAL entry payload."""
    return {
        "path": fp.rel_to_repo,
        "lang": fp.lang,
        "mtime": fp.mtime,
        "size": fp.size,
        "content_hash_before": None,
        "content_hash_after": fp.content_hash,
        "parse_result": {
            "symbols": [
                {
                    "scip_id": s.scip_id,
                    "name": s.name,
                    "kind": s.kind,
                    "line": s.line,
                    "signature": s.signature,
                    "signature_hash": s.signature_hash,
                    "docstring": s.docstring,
                    "parent_scip_id": s.parent_scip_id,
                }
                for s in fp.result.symbols
            ],
            "edges": [
                {
                    "src_scip_id": e.src_scip_id,
                    "dst_scip_id": e.dst_scip_id,
                    "dst_unresolved": e.dst_unresolved,
                    "kind": e.kind,
                }
                for e in fp.result.edges
            ],
            "imports": list(fp.result.imports),
        },
    }


def build_index(
    repo_root: Path,
    db_path: Path,
    *,
    package: str = ".",
    wal_path: Path | None = None,
) -> BuildStats:
    """Full build pipeline: discover → parse → bulk insert.

    Idempotent: re-running against the same source state leaves the DB
    in the same shape (INSERT ON CONFLICT updates in place).
    """
    t0 = time.monotonic()
    repo_root = repo_root.resolve()
    db_path = db_path.resolve()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    _pending_wal_acks: list[str] = []

    files = discover_files(repo_root)
    parses, py_errors = parse_files(files, repo_root=repo_root, package=package)

    conn = db.connect(db_path, read_only=False)
    try:
        # ensure_schema = apply_schema + migrate. Production writers MUST
        # run migrations so a fresh DB lands at CURRENT_SCHEMA_VERSION and
        # M3 tables (commits/commit_files/ownership/co_change_pairs) exist
        # for the first MCP query that needs them (L-253).
        db.ensure_schema(conn)

        # Drop FK enforcement for bulk load. PRAGMA foreign_keys must be set
        # OUTSIDE any transaction per SQLite docs — toggle before begin.
        conn.execute("PRAGMA foreign_keys = OFF")

        with db.transaction(conn):
            # Strategy: delete stale rows for files we're re-indexing so the
            # "ON CONFLICT DO UPDATE" semantics don't leave orphaned symbols
            # from a previous build. We key on path, not full row compare —
            # Task 2.2's mtime+size+hash-based dirty detection replaces this.
            if parses:
                placeholders = ",".join("?" for _ in parses)
                paths = [fp.rel_to_repo for fp in parses]
                conn.execute(
                    f"DELETE FROM files WHERE path IN ({placeholders})", paths
                )
                # symbols + edges cascade-deleted via FK ON DELETE CASCADE

            path_to_fid = _upsert_files(conn, parses)
            symbols_inserted = _bulk_insert_symbols(conn, parses, path_to_fid)
            _resolve_parent_ids(conn, parses)
            edges_inserted = _bulk_insert_edges(conn, parses)
            resolver_stats = _resolver.resolve_cross_file_edges(
                conn, parses=parses
            )

            # Append WAL entries for every file we just indexed — these
            # serve as the bootstrap record for `codemem replay --from-wal`.
            # Intent + ack are written in one pair each since the SQLite
            # commit is happening immediately below (we're inside the
            # transaction context).
            if wal_path is not None:
                for fp in parses:
                    args = _parse_result_to_wal_args(fp)
                    entry_id = _wal.append_intent(
                        wal_path,
                        op="file_upsert",
                        args=args,
                        # Tag with the schema version the DB is at RIGHT NOW
                        # (post ensure_schema). Hardcoding v1 here would make
                        # every WAL entry replay-incompatible with the v2 DB
                        # that just wrote it — L-253.
                        prev_user_version=db.CURRENT_SCHEMA_VERSION,
                        content_sha=args["content_hash_after"] or "",
                    )
                    # Track the id so we can ack after the transaction
                    # commits; collect into a closure-side list.
                    _pending_wal_acks.append(entry_id)

        # Re-enable FK enforcement and verify nothing slipped past.
        conn.execute("PRAGMA foreign_keys = ON")
        fk_violations = conn.execute("PRAGMA foreign_key_check").fetchall()
        if fk_violations:
            raise RuntimeError(
                f"codemem bulk load violated foreign keys: {fk_violations[:5]}"
            )
        integrity = conn.execute("PRAGMA integrity_check").fetchall()
        if integrity != [("ok",)]:
            raise RuntimeError(f"codemem SQLite integrity check failed: {integrity}")

        # M2 Task 2.6: truncate the SQLite WAL after a large batch so
        # -wal file size stays bounded. TRUNCATE is the strictest
        # checkpoint mode — forces a full WAL→db merge and resets the
        # wal file to zero bytes. Harmless no-op on an already-empty WAL.
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    finally:
        conn.close()

    # Emit WAL acks AFTER the transaction has committed. The intent
    # lines were written inside the transaction context above; acking
    # here means a crash between commit and ack-append produces the
    # branch-2 "already applied, needs ack" state — which replay_wal
    # handles idempotently.
    if wal_path is not None and _pending_wal_acks:
        for entry_id in _pending_wal_acks:
            _wal.append_ack(wal_path, entry_id)
        # M2 Task 2.8: rotate once per batch if the live WAL has grown
        # past the threshold. Cheap size-check, no-op on small logs.
        _wal.rotate_if_needed(wal_path)

    # Write last_sha so the NEXT refresh can take the incremental path
    # instead of falling back to a full rebuild. If the repo isn't a
    # git repo (rglob fallback in discover_files), `git rev-parse HEAD`
    # fails and we skip — next refresh will still do a full rebuild,
    # which is acceptable for non-git trees.
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=False,
        )
        if result.returncode == 0:
            last_sha_file = db_path.parent / "last_sha"
            last_sha_file.write_text(result.stdout.strip() + "\n")
    except FileNotFoundError:
        pass  # git not on PATH — first refresh will full-rebuild too

    return BuildStats(
        files_indexed=len(parses),
        symbols_inserted=symbols_inserted,
        edges_inserted=edges_inserted
        + resolver_stats["resolved"]
        + resolver_stats["unresolved"],
        cross_file_resolved=resolver_stats["resolved"],
        cross_file_unresolved=resolver_stats["unresolved"],
        elapsed_seconds=time.monotonic() - t0,
        python_parse_errors=py_errors,
    )
