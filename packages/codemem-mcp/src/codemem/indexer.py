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
import logging
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from . import resolver as _resolver
from .draw.plugin_surface import extract as _extract_plugin_surface
from .journal import wal as _wal
from .parser import ast_grep, python_ast
from .parser.python_ast import ParseResult
from .safety import GIT_TIMEOUT_S, SAFE_GIT, UnsafeDbPath, check_db_path
from .storage import db


logger = logging.getLogger(__name__)

__all__ = [
    "GIT_TIMEOUT_S",
    "SAFE_GIT",
    "BuildStats",
    "UnsafeDbPath",
    "build_index",
    "check_db_path",
    "discover_files",
    "parse_files",
    "plugin_edge_rows",
    "replace_plugin_edges",
    "tree_signature",
    "write_sidecar",
]


# Extensions we recognise. Files with any other extension are skipped —
# not indexed, not inserted. The indexer is source-code aware; docs and
# assets aren't in scope for v1.
_INDEXABLE_EXTENSIONS: frozenset[str] = frozenset(
    {".py"} | {ext for exts in ast_grep.SUPPORTED_LANGUAGES.values() for ext in exts}
)


@dataclass
class BuildStats:
    """Counters and timing reported by a full index build."""

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
    tracked = _ls_files(repo_root)
    if tracked is not None:
        # Filter by name before resolve(): resolve() is ~40 µs a file and runs
        # on every MCP query's freshness check (M15 §6.6: 52 ms → ~13 ms here).
        candidates = [
            (repo_root / rel).resolve()
            for rel in tracked
            if Path(rel).suffix.lower() in _INDEXABLE_EXTENSIONS
        ]
    else:
        candidates = [p for p in repo_root.rglob("*") if p.is_file()]

    return [
        p
        for p in candidates
        if p.suffix.lower() in _INDEXABLE_EXTENSIONS and p.is_file()
    ]


def git_tracked_files(repo_root: Path) -> list[Path] | None:
    """Return git-tracked files (absolute paths), or ``None`` if not a git repo."""
    tracked = _ls_files(repo_root)
    if tracked is None:
        return None
    return [(repo_root / rel).resolve() for rel in tracked]


def _ls_files(repo_root: Path) -> list[str] | None:
    """Repo-relative tracked paths from ``git ls-files -z``, or None without git/repo."""
    try:
        result = subprocess.run(  # noqa: S603  # why: fixed `git` argv, no shell
            [*SAFE_GIT, "-C", str(repo_root), "ls-files", "-z"],
            capture_output=True,
            check=False,
        )
    except FileNotFoundError:
        return None
    if result.returncode != 0:
        return None
    return [os.fsdecode(raw) for raw in result.stdout.split(b"\0") if raw]


def tree_signature(files: list[Path]) -> str:
    """Hash of every indexed file's path, mtime and size.

    Equal signatures mean no indexed file was added, removed or touched.
    Stat-only on purpose: ``git status`` would run the repo's fsmonitor and
    clean filters.
    """
    h = hashlib.sha256()
    for p in sorted(files):
        try:
            st = p.stat()
        except OSError:
            continue  # vanished since discovery: its absence changes the hash
        h.update(os.fsencode(p) + f"\0{st.st_mtime_ns}\0{st.st_size}\n".encode())
    return h.hexdigest()


def _discard_untrusted(db_path: Path) -> None:
    """Delete an existing DB (and its WAL files) that codemem did not build here."""
    if db_path.exists() and not db.index_trusted(db_path):
        db.remove_db_files(db_path)


def _write_build_sidecars(repo_root: Path, db_dir: Path, signature: str) -> None:
    try:
        result = subprocess.run(  # noqa: S603  # why: fixed `git` argv, no shell
            [*SAFE_GIT, "-C", str(repo_root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
            timeout=GIT_TIMEOUT_S,
        )
    except FileNotFoundError:
        return  # no git: the next refresh full-rebuilds
    except subprocess.TimeoutExpired:
        logger.warning(
            "git rev-parse timed out after %gs; last_sha/tree_sig not written",
            GIT_TIMEOUT_S,
        )
        return
    if result.returncode == 0:
        write_sidecar(db_dir / "last_sha", result.stdout.strip() + "\n")
        write_sidecar(db_dir / "tree_sig", signature + "\n")


def write_sidecar(path: Path, text: str) -> None:
    """Replace ``path`` atomically; a planted symlink is replaced, never followed.

    The index dir is repo-controlled when ``CODEMEM_DB`` points into a repo:
    a clone can commit ``last_sha -> ~/.bashrc`` there.
    """
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp.unlink(missing_ok=True)
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.replace(tmp, path)


# ---------------------------------------------------------------------
# Parse dispatch
# ---------------------------------------------------------------------


@dataclass
class _FileParse:
    path: Path  # absolute
    rel_to_repo: str  # posix string relative to repo_root
    lang: str
    result: ParseResult
    content_hash: str
    mtime: int
    size: int


def parse_files(  # noqa: C901  # why: pre-existing; refactor tracked in TODOS.md (M8.2 D8 pay-down, no logic change in a security milestone)
    files: list[Path],
    *,
    repo_root: Path,
    package: str,
) -> tuple[list[_FileParse], int]:
    """Parse each file with the appropriate parser.

    Python uses the stdlib parser one file at a time; other languages batch
    via ast-grep. A file ast-grep could not parse is absent from ``parses``
    (not an empty parse).

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
        pr = python_ast.extract_python_signatures(source, package=package, file_rel=rel)
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
            pr = sg_results.get(p)
            if pr is None:
                # Not parsed (no ast-grep, or a failed scan — already logged).
                # Skipping it, rather than storing an empty parse, keeps the
                # file's indexed symbols and its old content_hash, so an
                # incremental refresh re-parses it once ast-grep is back.
                continue
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


def _bulk_insert_symbols(
    conn, parses: list[_FileParse], path_to_fid: dict[str, int]
) -> int:
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
    """Insert edges after symbol IDs are known.

    Unresolved edges (dst None) are persisted via ``dst_unresolved`` column;
    Task 1.6 fills in later.
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


# ---------------------------------------------------------------------
# Plugin surface (M10.3)
# ---------------------------------------------------------------------

PluginEdgeRow = tuple[str, str, str, str]  # (src, dst, kind, ref_class)


def plugin_edge_rows(repo_root: Path) -> set[PluginEdgeRow]:
    """Every classified plugin-surface reference under ``repo_root``, as table rows.

    Empty, with one debug line, when the repo has no ``claude-code/`` tree.
    """
    if not (repo_root / "claude-code").is_dir():
        logger.debug("no claude-code/ under %s: plugin_edges left empty", repo_root)
        return set()
    surface = _extract_plugin_surface(repo_root)
    if surface.errors:
        # why debug: the same errors are reported by `codemem draw --check` and the
        # plugin-surface golden; the index still takes every edge that did parse.
        logger.debug(
            "plugin surface: %d extraction errors (first: %s)",
            len(surface.errors),
            surface.errors[0],
        )
    return {(e.src, e.dst, e.kind.value, e.ref_class.value) for e in surface.edges}


def replace_plugin_edges(conn, rows: set[PluginEdgeRow]) -> bool:
    """Make ``plugin_edges`` hold exactly ``rows``; True when anything changed.

    The table is small (hundreds of rows), so it is rebuilt whole rather than
    diffed. Unchanged rows write nothing, so a no-op refresh leaves the DB alone.
    The caller owns the transaction.
    """
    current = set(conn.execute("SELECT src, dst, kind, ref_class FROM plugin_edges"))
    if current == rows:
        return False
    conn.execute("DELETE FROM plugin_edges")
    conn.executemany(
        "INSERT INTO plugin_edges (src, dst, kind, ref_class) VALUES (?, ?, ?, ?)",
        sorted(rows),
    )
    return True


def build_index(
    repo_root: Path,
    db_path: Path,
    *,
    package: str = ".",
    wal_path: Path | None = None,
    write_sidecars: bool = True,
) -> BuildStats:
    """Full build pipeline: discover → parse → bulk insert.

    Idempotent: re-running against the same source state leaves the DB
    in the same shape (INSERT ON CONFLICT updates in place). With
    ``write_sidecars=False`` the caller records ``last_sha``/``tree_sig``
    itself: a DB built aside must not claim HEAD before it is swapped in.
    (So two writers record the sidecars: this one for a standalone build,
    ``refresh_index`` after its swap. One shared writer is a TODOS item.)
    Raises :class:`UnsafeDbPath` per :func:`codemem.safety.check_db_path`. An
    existing DB codemem did not build here is deleted first, not reused: its
    git-mining tables survive a build, so none of its rows may.
    """
    t0 = time.monotonic()
    repo_root = repo_root.resolve()
    # Never resolve db_path: following a planted link is the attack.
    db_path = db_path.absolute()
    check_db_path(db_path)
    _discard_untrusted(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    _pending_wal_acks: list[str] = []

    files = discover_files(repo_root)
    # Taken before parsing: a file edited mid-build changes the signature.
    signature = tree_signature(files)
    parses, py_errors = parse_files(files, repo_root=repo_root, package=package)
    plugin_rows = plugin_edge_rows(repo_root)

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
            # A full build replaces the whole graph. Children are cleared
            # EXPLICITLY: FK enforcement is OFF here, so `ON DELETE CASCADE`
            # does not fire — deleting only `files` left symbols/edges orphaned,
            # and the next insert re-attached them to whatever path reused the
            # freed file id (diagram-generation M3 §3.5). Clearing every graph
            # row (not just paths in this parse) also drops files deleted from
            # disk and heals an index corrupted by the old behaviour. The
            # git-mining tables are keyed by path and are left alone.
            for table in ("edges", "file_edges", "symbols", "files"):
                conn.execute(f"DELETE FROM {table}")  # noqa: S608  # why: table names come from the literal tuple above

            path_to_fid = _upsert_files(conn, parses)
            symbols_inserted = _bulk_insert_symbols(conn, parses, path_to_fid)
            _resolve_parent_ids(conn, parses)
            edges_inserted = _bulk_insert_edges(conn, parses)
            resolver_stats = _resolver.resolve_cross_file_edges(conn, parses=parses)
            replace_plugin_edges(conn, plugin_rows)

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
    if write_sidecars:
        _write_build_sidecars(repo_root, db_path.parent, signature)

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
