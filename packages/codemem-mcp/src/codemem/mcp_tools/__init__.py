"""codemem MCP tools — 6 ported from /index, public surface for the MCP server.

Each tool is a plain Python function returning a JSON-serialisable dict
so the MCP server layer (Task 1.10) can register them via FastMCP with
no extra glue. Every tool validates its args via
:mod:`~codemem.mcp_tools.sanitizers` BEFORE any SQL runs — adversarial
inputs return structured ``{"error": "..."}`` dicts, not exceptions.

Tools:
    who_calls         — upstream callers (BFS via canonical CTE)
    blast_radius      — downstream callees (transitive)
    dead_code         — symbols with zero incoming call edges
    dependency_chain  — shortest path from source to target
    search_symbols    — substring name search
    file_summary      — per-file symbol listing
"""

from __future__ import annotations

import json
import re
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..storage import db
from .queries import BLAST_RADIUS_CTE, WHO_CALLS_CTE
from .sanitizers import ValidationError, sanitize_path_arg, sanitize_symbol_arg


__all__ = [
    "aa_ma_context",
    "blast_radius",
    "co_changes",
    "dead_code",
    "dependency_chain",
    "file_summary",
    "hot_spots",
    "layers",
    "owners",
    "search_symbols",
    "symbol_history",
    "who_calls",
]

_DEFAULT_CO_CHANGES_EXCLUDE: tuple[str, ...] = ("CHANGELOG.md", "README.md")


_DEFAULT_BUDGET = 8_000
# Conservative char-per-token heuristic. 1 token ≈ 4 chars for English+code.
_CHARS_PER_TOKEN = 4


# ---------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------

def _budget_chars(budget_tokens: int) -> int:
    return max(budget_tokens, 1) * _CHARS_PER_TOKEN


def _exceeds_budget(payload: Any, budget_tokens: int) -> bool:
    return len(json.dumps(payload, default=str)) > _budget_chars(budget_tokens)


def _open_ro(db_path: Path) -> sqlite3.Connection:
    conn = db.connect(db_path, read_only=True)
    conn.row_factory = sqlite3.Row
    return conn


def _resolve_symbol_ids_by_name(
    conn: sqlite3.Connection, name: str
) -> list[int]:
    """Return ALL symbol IDs for symbols with this unqualified name."""
    rows = conn.execute("SELECT id FROM symbols WHERE name = ?", (name,)).fetchall()
    return [r["id"] for r in rows]


def _symbol_info_row(row: sqlite3.Row) -> dict:
    return {
        "scip_id": row["scip_id"],
        "name": row["name"],
        "kind": row["kind"],
        "file": row["path"],
        "line": row["line"],
    }


# ---------------------------------------------------------------------
# who_calls
# ---------------------------------------------------------------------

def who_calls(
    db_path: Path,
    name: str,
    *,
    max_depth: int = 3,
    budget: int = _DEFAULT_BUDGET,
) -> dict:
    """Return upstream callers of ``name`` (by unqualified symbol name)."""
    try:
        clean = sanitize_symbol_arg(name)
    except ValidationError as exc:
        return {"error": str(exc), "target": name, "callers": []}

    with _open_ro(db_path) as conn:
        target_ids = _resolve_symbol_ids_by_name(conn, clean)
        if not target_ids:
            return {"target": clean, "callers": [], "truncated": False, "error": None}

        caller_ids: set[int] = set()
        for tid in target_ids:
            rows = conn.execute(
                WHO_CALLS_CTE, {"target": tid, "max_depth": max_depth}
            ).fetchall()
            caller_ids.update(r["sid"] for r in rows)

        callers: list[dict] = []
        for cid in caller_ids:
            row = conn.execute(
                """
                SELECT s.scip_id, s.name, s.kind, s.line, f.path
                FROM symbols s JOIN files f ON s.file_id = f.id
                WHERE s.id = ?
                """,
                (cid,),
            ).fetchone()
            if row:
                callers.append(_symbol_info_row(row))

    callers.sort(key=lambda c: (c["file"], c["line"], c["name"]))
    return _truncate(
        {"target": clean, "callers": callers, "error": None},
        list_key="callers",
        budget=budget,
    )


# ---------------------------------------------------------------------
# blast_radius
# ---------------------------------------------------------------------

def blast_radius(
    db_path: Path,
    name: str,
    *,
    max_depth: int = 3,
    budget: int = _DEFAULT_BUDGET,
) -> dict:
    """Return downstream callees of ``name`` transitively."""
    try:
        clean = sanitize_symbol_arg(name)
    except ValidationError as exc:
        return {"error": str(exc), "target": name, "downstream": []}

    with _open_ro(db_path) as conn:
        target_ids = _resolve_symbol_ids_by_name(conn, clean)
        if not target_ids:
            return {"target": clean, "downstream": [], "truncated": False, "error": None}

        dst_ids: set[int] = set()
        for tid in target_ids:
            rows = conn.execute(
                BLAST_RADIUS_CTE, {"target": tid, "max_depth": max_depth}
            ).fetchall()
            dst_ids.update(r["sid"] for r in rows)

        downstream: list[dict] = []
        for did in dst_ids:
            row = conn.execute(
                """
                SELECT s.scip_id, s.name, s.kind, s.line, f.path
                FROM symbols s JOIN files f ON s.file_id = f.id
                WHERE s.id = ?
                """,
                (did,),
            ).fetchone()
            if row:
                downstream.append(_symbol_info_row(row))

    downstream.sort(key=lambda d: (d["file"], d["line"], d["name"]))
    return _truncate(
        {"target": clean, "downstream": downstream, "error": None},
        list_key="downstream",
        budget=budget,
    )


# ---------------------------------------------------------------------
# dead_code
# ---------------------------------------------------------------------

def dead_code(
    db_path: Path,
    *,
    budget: int = _DEFAULT_BUDGET,
) -> dict:
    """Return function/method symbols with zero incoming call edges."""
    with _open_ro(db_path) as conn:
        rows = conn.execute(
            """
            SELECT s.scip_id, s.name, s.kind, s.line, f.path
            FROM symbols s
            JOIN files f ON s.file_id = f.id
            LEFT JOIN edges e ON e.dst_symbol_id = s.id AND e.kind = 'call'
            WHERE s.kind IN ('function', 'method', 'async_function', 'async_method')
              AND e.dst_symbol_id IS NULL
            ORDER BY f.path, s.line
            """
        ).fetchall()
    symbols = [_symbol_info_row(r) for r in rows]
    return _truncate(
        {"symbols": symbols, "error": None}, list_key="symbols", budget=budget
    )


# ---------------------------------------------------------------------
# dependency_chain
# ---------------------------------------------------------------------

_CHAIN_CTE = """
WITH RECURSIVE chain(sid, depth, path) AS (
    SELECT id, 0, CAST(id AS TEXT)
    FROM symbols WHERE id = :source
    UNION
    SELECT e.dst_symbol_id, c.depth + 1, c.path || '->' || e.dst_symbol_id
    FROM edges e
    JOIN chain c ON e.src_symbol_id = c.sid
    WHERE c.depth < :max_depth
      AND e.kind = 'call'
      AND e.dst_symbol_id IS NOT NULL
      AND c.path NOT LIKE '%->' || e.dst_symbol_id
      AND c.path NOT LIKE '%->' || e.dst_symbol_id || '->%'
      AND CAST(e.dst_symbol_id AS TEXT) != c.path
)
SELECT path, depth FROM chain WHERE sid = :target ORDER BY depth LIMIT 1
"""


def dependency_chain(
    db_path: Path,
    source: str,
    target: str,
    *,
    max_depth: int = 5,
    budget: int = _DEFAULT_BUDGET,
) -> dict:
    """Shortest call-graph path from ``source`` to ``target``."""
    try:
        src_clean = sanitize_symbol_arg(source)
        tgt_clean = sanitize_symbol_arg(target)
    except ValidationError as exc:
        return {"error": str(exc), "chain": None}

    with _open_ro(db_path) as conn:
        src_ids = _resolve_symbol_ids_by_name(conn, src_clean)
        tgt_ids = _resolve_symbol_ids_by_name(conn, tgt_clean)
        if not src_ids or not tgt_ids:
            return {"chain": None, "error": None}

        best_chain: list[int] | None = None
        for sid in src_ids:
            for tid in tgt_ids:
                row = conn.execute(
                    _CHAIN_CTE,
                    {"source": sid, "target": tid, "max_depth": max_depth},
                ).fetchone()
                if row:
                    ids = [int(x) for x in row["path"].split("->")]
                    if best_chain is None or len(ids) < len(best_chain):
                        best_chain = ids

        if best_chain is None:
            return {"chain": None, "error": None}

        placeholders = ",".join("?" for _ in best_chain)
        rows = conn.execute(
            f"""
            SELECT s.id, s.scip_id, s.name, s.kind, s.line, f.path
            FROM symbols s JOIN files f ON s.file_id = f.id
            WHERE s.id IN ({placeholders})
            """,
            best_chain,
        ).fetchall()
        by_id = {r["id"]: r for r in rows}
        chain_rows = [_symbol_info_row(by_id[i]) for i in best_chain if i in by_id]

    return _truncate(
        {"chain": chain_rows, "error": None}, list_key="chain", budget=budget
    )


# ---------------------------------------------------------------------
# search_symbols
# ---------------------------------------------------------------------

def search_symbols(
    db_path: Path,
    query: str,
    *,
    budget: int = _DEFAULT_BUDGET,
) -> dict:
    """Substring match on symbols.name. Orders by exact > prefix > contains."""
    try:
        clean = sanitize_symbol_arg(query)
    except ValidationError as exc:
        return {"error": str(exc), "matches": []}

    with _open_ro(db_path) as conn:
        like = f"%{clean}%"
        rows = conn.execute(
            """
            SELECT s.scip_id, s.name, s.kind, s.line, f.path
            FROM symbols s JOIN files f ON s.file_id = f.id
            WHERE s.name LIKE ?
            ORDER BY
                CASE
                    WHEN s.name = ?       THEN 0
                    WHEN s.name LIKE ?    THEN 1
                    ELSE 2
                END,
                s.name, f.path, s.line
            """,
            (like, clean, f"{clean}%"),
        ).fetchall()
    matches = [_symbol_info_row(r) for r in rows]
    return _truncate(
        {"matches": matches, "error": None}, list_key="matches", budget=budget
    )


# ---------------------------------------------------------------------
# file_summary
# ---------------------------------------------------------------------

def file_summary(
    db_path: Path,
    path: str,
    *,
    budget: int = _DEFAULT_BUDGET,
    repo_root: Path | None = None,
) -> dict:
    """List symbols in ``path`` ordered by source line."""
    try:
        sanitize_symbol_arg(path)
        if repo_root is not None:
            sanitize_path_arg(path, repo_root)
    except ValidationError as exc:
        return {"error": str(exc), "symbols": []}

    with _open_ro(db_path) as conn:
        rows = conn.execute(
            """
            SELECT s.scip_id, s.name, s.kind, s.line, s.signature, f.path
            FROM symbols s JOIN files f ON s.file_id = f.id
            WHERE f.path = ?
            ORDER BY s.line
            """,
            (path,),
        ).fetchall()
    symbols: list[dict] = []
    for r in rows:
        info = _symbol_info_row(r)
        info["signature"] = r["signature"]
        symbols.append(info)
    return _truncate(
        {"symbols": symbols, "error": None}, list_key="symbols", budget=budget
    )


# ---------------------------------------------------------------------
# hot_spots (M3 Task 3.2)
# ---------------------------------------------------------------------

def hot_spots(
    db_path: Path,
    *,
    window_days: int = 90,
    top_n: int = 10,
    budget: int = _DEFAULT_BUDGET,
    now: float | None = None,
) -> dict:
    """Return top-N files ranked by (commits in window) × (function_count).

    Score breakdown is included per file (``commits_in_window``,
    ``function_count``, ``score``). Only files with ≥1 of each appear.

    ``now`` defaults to ``time.time()``; tests inject a fixed value.
    """
    cutoff = int((now if now is not None else time.time()) - window_days * 86400)
    query = """
        WITH fn_counts AS (
            SELECT f.path AS path, COUNT(s.id) AS function_count
              FROM files f
              JOIN symbols s ON s.file_id = f.id
             WHERE s.kind IN ('function','method','async_function','async_method')
             GROUP BY f.path
        ),
        commit_counts AS (
            SELECT cf.file_path AS path,
                   COUNT(DISTINCT cf.commit_sha) AS commits_in_window
              FROM commit_files cf
              JOIN commits c ON c.sha = cf.commit_sha
             WHERE c.author_time >= ?
             GROUP BY cf.file_path
        )
        SELECT fn.path AS path,
               cc.commits_in_window,
               fn.function_count,
               cc.commits_in_window * fn.function_count AS score
          FROM fn_counts fn
          JOIN commit_counts cc ON cc.path = fn.path
         WHERE fn.function_count >= 1
           AND cc.commits_in_window >= 1
         ORDER BY score DESC, fn.path ASC
         LIMIT ?
    """
    with _open_ro(db_path) as conn:
        rows = conn.execute(query, (cutoff, top_n)).fetchall()

    files = [
        {
            "path": r["path"],
            "commits_in_window": r["commits_in_window"],
            "function_count": r["function_count"],
            "score": r["score"],
        }
        for r in rows
    ]
    return _truncate(
        {"files": files, "window_days": window_days, "top_n": top_n, "error": None},
        list_key="files",
        budget=budget,
    )


# ---------------------------------------------------------------------
# co_changes (M3 Task 3.3)
# ---------------------------------------------------------------------

def co_changes(
    db_path: Path,
    file_path: str,
    *,
    threshold: int = 3,
    exclude: tuple[str, ...] | None = None,
    top_n: int = 50,
    budget: int = _DEFAULT_BUDGET,
) -> dict:
    """Return files co-changing with ``file_path`` that lack an import edge.

    Two filters on top of commit-co-occurrence:

    1. Must share at least ``threshold`` commits with ``file_path``.
    2. Must NOT be linked by an import/call edge in either direction — the
       whole point of this tool is to surface *implicit* coupling that the
       AST misses.

    ``exclude`` defaults to :data:`_DEFAULT_CO_CHANGES_EXCLUDE`
    (``("CHANGELOG.md", "README.md")``) which users routinely touch alongside
    everything else; pass an empty tuple to disable.

    Result order: ``count`` DESC, ``path`` ASC for deterministic tie-break.
    """
    try:
        clean = sanitize_symbol_arg(file_path)
    except ValidationError as exc:
        return {"error": str(exc), "target": file_path, "files": []}

    excludes = (
        _DEFAULT_CO_CHANGES_EXCLUDE if exclude is None else tuple(exclude)
    )

    # Parameterised `NOT IN (?, ?, ...)` — build conditionally so empty
    # excludes produces NO clause at all (a bare `NOT IN (NULL)` evaluates
    # to NULL/unknown and filters out everything, SQL three-valued-logic gotcha).
    exclude_clause = ""
    if excludes:
        exclude_clause = (
            "AND co.path NOT IN ("
            + ",".join("?" for _ in excludes)
            + ")"
        )
    query = f"""
        WITH target_commits AS (
            SELECT commit_sha FROM commit_files WHERE file_path = ?
        ),
        co_counts AS (
            SELECT cf.file_path AS path,
                   COUNT(DISTINCT cf.commit_sha) AS c
              FROM commit_files cf
             WHERE cf.commit_sha IN (SELECT commit_sha FROM target_commits)
               AND cf.file_path != ?
             GROUP BY cf.file_path
            HAVING COUNT(DISTINCT cf.commit_sha) >= ?
        ),
        linked AS (
            SELECT f2.path AS path
              FROM edges e
              JOIN symbols s1 ON s1.id = e.src_symbol_id
              JOIN symbols s2 ON s2.id = e.dst_symbol_id
              JOIN files   f1 ON f1.id = s1.file_id
              JOIN files   f2 ON f2.id = s2.file_id
             WHERE f1.path = ? AND f2.path != ?
            UNION
            SELECT f1.path AS path
              FROM edges e
              JOIN symbols s1 ON s1.id = e.src_symbol_id
              JOIN symbols s2 ON s2.id = e.dst_symbol_id
              JOIN files   f1 ON f1.id = s1.file_id
              JOIN files   f2 ON f2.id = s2.file_id
             WHERE f2.path = ? AND f1.path != ?
        )
        SELECT co.path AS path, co.c AS count
          FROM co_counts co
         WHERE co.path NOT IN (SELECT path FROM linked)
           {exclude_clause}
         ORDER BY co.c DESC, co.path ASC
         LIMIT ?
    """
    params: list[object] = [clean, clean, threshold, clean, clean, clean, clean]
    if excludes:
        params.extend(excludes)
    params.append(top_n)

    with _open_ro(db_path) as conn:
        rows = conn.execute(query, params).fetchall()

    files = [{"path": r["path"], "count": r["count"]} for r in rows]
    return _truncate(
        {
            "files": files,
            "target": clean,
            "threshold": threshold,
            "error": None,
        },
        list_key="files",
        budget=budget,
    )


# ---------------------------------------------------------------------
# owners (M3 Task 3.4)
# ---------------------------------------------------------------------

def owners(
    db_path: Path,
    path: str,
    *,
    repo_root: Path | None = None,
    refresh: bool = False,
    skip: bool = False,
    budget: int = _DEFAULT_BUDGET,
) -> dict:
    """Return per-author line-count percentages for a file or directory.

    Mode:
    * ``skip=True`` — honours the ``--no-owners`` flag; returns ``{"skipped": True, "authors": []}``.
    * Path ends with ``/`` or matches multiple rows in the ``ownership`` table
      prefix-wise — aggregated as a directory.
    * Otherwise — single-file lookup.

    Cache policy: reads from the ``ownership`` table unless ``refresh=True``,
    in which case ``GitMiner.get_blame`` is invoked (per-file 2s timeout) and
    the results persisted. When the cache is empty AND no ``repo_root`` is
    provided, returns an empty ``authors`` list rather than erroring — there
    is no way to compute ownership without git.

    Output:
        {"authors": [{"email","line_count","percentage"}, ...],
         "path", "from_cache": bool, "skipped": bool, "error", "truncated"}
    """
    if skip:
        return {
            "skipped": True,
            "authors": [],
            "path": path,
            "error": None,
        }

    try:
        clean = sanitize_symbol_arg(path)
    except ValidationError as exc:
        return {"error": str(exc), "path": path, "authors": [], "skipped": False}

    with _open_ro(db_path) as conn:
        # If ``refresh`` is requested and repo_root is provided, refresh first
        # then fall through to the normal cache read.
        if refresh and repo_root is not None:
            _refresh_ownership_cache(db_path, clean, repo_root=repo_root)

        # Directory-style query when path ends in '/' or when there are no
        # exact-match rows but prefix rows exist.
        is_directory = clean.endswith("/")
        if is_directory:
            rows = conn.execute(
                "SELECT author_email, SUM(line_count) AS line_count "
                "FROM ownership WHERE file_path LIKE ? || '%' "
                "GROUP BY author_email",
                (clean,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT author_email, line_count FROM ownership WHERE file_path = ?",
                (clean,),
            ).fetchall()

    if not rows:
        return {
            "authors": [],
            "path": clean,
            "from_cache": False,
            "skipped": False,
            "error": None,
            "truncated": False,
        }

    total = sum(r["line_count"] for r in rows)
    authors = [
        {
            "email": r["author_email"],
            "line_count": r["line_count"],
            "percentage": (r["line_count"] / total * 100.0) if total else 0.0,
        }
        for r in rows
    ]
    # Deterministic tie-break: percentage DESC, email ASC.
    authors.sort(key=lambda a: (-a["percentage"], a["email"]))

    return _truncate(
        {
            "authors": authors,
            "path": clean,
            "from_cache": True,
            "skipped": False,
            "error": None,
        },
        list_key="authors",
        budget=budget,
    )


def _refresh_ownership_cache(
    db_path: Path, path: str, *, repo_root: Path
) -> None:
    """Call ``GitMiner.get_blame`` for ``path`` (or the files under it when path
    is a directory) and write results to the ``ownership`` table.

    Per-file 2 second timeout matches the AC. Silently skips files that
    blame refuses (binary, not-in-HEAD, deleted) — they just don't get
    cache entries.
    """
    # Local import avoids circular dep if someone stubs mcp_tools before
    # analysis in some future toplevel layout.
    from codemem.analysis.git_mining import GitMiner

    miner = GitMiner(repo_root=repo_root)

    # Resolve the set of files to blame.
    targets: list[str]
    if path.endswith("/"):
        conn = db.connect(db_path)
        try:
            rows = conn.execute(
                "SELECT path FROM files WHERE path LIKE ? || '%'",
                (path,),
            ).fetchall()
            targets = [r[0] for r in rows]
        finally:
            conn.close()
    else:
        targets = [path]

    if not targets:
        return

    now = int(time.time())
    conn = db.connect(db_path)
    try:
        with db.transaction(conn):
            for t in targets:
                try:
                    result = miner.get_blame(t)
                except Exception:
                    continue
                if not result:
                    continue
                # Replace any stale rows for this file.
                conn.execute(
                    "DELETE FROM ownership WHERE file_path = ?", (t,)
                )
                for email, (line_count, pct) in result.items():
                    conn.execute(
                        "INSERT INTO ownership "
                        "(file_path, author_email, line_count, percentage, computed_at) "
                        "VALUES (?, ?, ?, ?, ?)",
                        (t, email, line_count, pct, now),
                    )
    finally:
        conn.close()


# ---------------------------------------------------------------------
# symbol_history (M3 Task 3.5)
# ---------------------------------------------------------------------

_SYMHIST_PRETTY = "%H\x1f%at\x1f%ae\x1f%s\x1e"


def symbol_history(
    db_path: Path,
    name: str,
    *,
    file_path: str | None = None,
    repo_root: Path | None = None,
    budget: int = _DEFAULT_BUDGET,
) -> dict:
    """Return ``git log -L:<name>:<file>`` summary per file containing ``name``.

    If ``file_path`` is given, only that file is queried. Otherwise every file
    that contains a symbol with unqualified name == ``name`` is queried. Each
    per-file entry carries: first/last commit sha+message+timestamp, change
    count, and list of distinct author emails.
    """
    try:
        clean_name = sanitize_symbol_arg(name)
    except ValidationError as exc:
        return {"error": str(exc), "target": name, "files": []}

    if repo_root is None:
        return {
            "error": "repo_root is required for symbol_history",
            "target": clean_name,
            "files": [],
        }

    # Resolve target files.
    with _open_ro(db_path) as conn:
        if file_path is not None:
            try:
                clean_file = sanitize_symbol_arg(file_path)
            except ValidationError as exc:
                return {"error": str(exc), "target": clean_name, "files": []}
            rows = conn.execute(
                "SELECT f.path FROM files f JOIN symbols s ON s.file_id=f.id "
                "WHERE s.name = ? AND f.path = ?",
                (clean_name, clean_file),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT DISTINCT f.path FROM files f JOIN symbols s ON s.file_id=f.id "
                "WHERE s.name = ?",
                (clean_name,),
            ).fetchall()

    target_files = [r["path"] for r in rows]
    if not target_files:
        return {
            "target": clean_name,
            "files": [],
            "error": None,
            "truncated": False,
        }

    # Import locally to avoid a hard top-level dep on analysis subpackage.
    from codemem.analysis.git_mining import GitMiner

    miner = GitMiner(repo_root=repo_root)
    file_histories: list[dict] = []
    for fp in target_files:
        entries = _git_log_L(miner, name=clean_name, file_path=fp)
        if not entries:
            continue
        # Entries sorted desc by author_time in git log output; we want asc.
        entries.sort(key=lambda e: e["author_time"])
        first, last = entries[0], entries[-1]
        authors = sorted({e["author_email"] for e in entries})
        file_histories.append(
            {
                "file": fp,
                "change_count": len(entries),
                "first_commit": first["sha"],
                "first_commit_message": first["message"],
                "first_commit_time": first["author_time"],
                "last_commit": last["sha"],
                "last_commit_message": last["message"],
                "last_commit_time": last["author_time"],
                "authors": authors,
            }
        )

    # Deterministic ordering across files.
    file_histories.sort(key=lambda fh: fh["file"])

    return _truncate(
        {
            "target": clean_name,
            "files": file_histories,
            "error": None,
        },
        list_key="files",
        budget=budget,
    )


def _git_log_L(miner, *, name: str, file_path: str) -> list[dict]:
    """Run ``git log -L:<name>:<file> --pretty=format:... -s`` and parse.

    ``-s`` suppresses the diff body; we only want the header per commit.
    Returns a list of ``{sha, author_time, author_email, message}`` dicts.
    """
    # git's -L:ident:file syntax rejects shell metachars itself, but we've
    # already sanitized via sanitize_symbol_arg so this is belt+braces.
    proc = miner._git(
        [
            "log",
            "-s",
            f"-L:{name}:{file_path}",
            f"--pretty=format:{_SYMHIST_PRETTY}",
            "--",
        ],
        check=False,
        timeout=10.0,
    )
    if proc.returncode != 0:
        return []
    out: list[dict] = []
    for block in proc.stdout.split("\x1e"):
        block = block.strip()
        if not block:
            continue
        parts = block.split("\x1f")
        if len(parts) != 4:
            continue
        sha, at, ae, subject = parts
        try:
            author_time = int(at)
        except ValueError:
            continue
        out.append(
            {
                "sha": sha,
                "author_time": author_time,
                "author_email": ae,
                "message": subject,
            }
        )
    return out


# ---------------------------------------------------------------------
# layers (M3 Task 3.6)
# ---------------------------------------------------------------------

_LAYER_MAX_COLS = 80          # AC: fits 80-col terminal without wrap
_LAYER_MAX_CHARS = 2_000      # AC: ≤ 500 tokens × 4 chars/token heuristic


def layers(
    db_path: Path,
    *,
    budget: int = _DEFAULT_BUDGET,
) -> dict:
    """Bucket files into core/middle/periphery by in-degree and render onion.

    In-degree here = count of incoming call edges targeting any symbol in
    the file. A file only appears in a bucket if it has ≥1 indexed symbol;
    files with zero in-degree still appear in the periphery.

    Buckets use tertile cutoffs (top 1/3 by in-degree = core, middle 1/3 =
    middle, bottom 1/3 = periphery) so the layering is stable even for tiny
    repos. Equal scores tie-break lexicographically on path.
    """
    query = """
        WITH file_in_degrees AS (
            SELECT f.path AS path,
                   COALESCE(SUM(CASE WHEN e.src_symbol_id IS NOT NULL THEN 1 ELSE 0 END), 0) AS in_degree
              FROM files f
              LEFT JOIN symbols s ON s.file_id = f.id
              LEFT JOIN edges   e ON e.dst_symbol_id = s.id
                                  AND e.src_symbol_id NOT IN (
                                      SELECT id FROM symbols WHERE file_id = f.id
                                  )
             GROUP BY f.path
        )
        SELECT path, in_degree FROM file_in_degrees ORDER BY in_degree DESC, path ASC
    """
    with _open_ro(db_path) as conn:
        rows = conn.execute(query).fetchall()

    files = [(r["path"], r["in_degree"]) for r in rows]
    if not files:
        return {
            "layers": {"core": [], "middle": [], "periphery": []},
            "ascii": "(no files indexed)",
            "error": None,
            "truncated": False,
        }

    # Tertile buckets. For n files, top ceil(n/3) = core, bottom ceil(n/3) = periphery,
    # remainder = middle. For n=1 we want everything in periphery (zero signal).
    n = len(files)
    if n == 1:
        core_count = 0
        peri_count = 1
    else:
        core_count = max(1, n // 3)
        peri_count = max(1, n // 3)
    core = [p for p, _ in files[:core_count]]
    periphery = [p for p, _ in files[n - peri_count:]]
    middle = [p for p, _ in files[core_count : n - peri_count]]

    ascii_art = _render_layers_onion(core, middle, periphery)
    payload = {
        "layers": {"core": core, "middle": middle, "periphery": periphery},
        "ascii": ascii_art,
        "error": None,
    }
    # No list_key truncation (layers dict is not a single list); rely on the
    # ASCII cap enforced inside the renderer plus the normal budget check.
    if len(json.dumps(payload, default=str)) > _budget_chars(budget):
        payload["truncated"] = True
    else:
        payload["truncated"] = False
    return payload


def _render_layers_onion(
    core: list[str], middle: list[str], periphery: list[str]
) -> str:
    """Render a tight 3-ring ASCII onion. Always ≤ 80 cols and ≤ 2000 chars.

    Shape:
        ┌─ core ────────────────────────────────────────────────────────┐
          core/file/a.py, core/file/b.py
        ├─ middle ──────────────────────────────────────────────────────┤
          middle/file/c.py, middle/file/d.py
        ├─ periphery ──────────────────────────────────────────────────┤
          edge/e.py
        └───────────────────────────────────────────────────────────────┘
    """
    lines: list[str] = []

    def _wrap_files(files: list[str], prefix: str = "  ") -> list[str]:
        """Wrap a comma-joined file list into ≤80-col lines."""
        out: list[str] = []
        current = prefix
        for i, f in enumerate(files):
            token = f + (", " if i < len(files) - 1 else "")
            if len(current) + len(token) > _LAYER_MAX_COLS:
                out.append(current.rstrip())
                current = prefix + token
            else:
                current += token
        if current.strip():
            out.append(current.rstrip())
        return out or [prefix + "(empty)"]

    def _section_header(label: str) -> str:
        raw = f"+ {label} "
        pad = (_LAYER_MAX_COLS - len(raw) - 1) * "-"
        return f"{raw}{pad}+"

    lines.append(_section_header("core"))
    lines.extend(_wrap_files(core))
    lines.append(_section_header("middle"))
    lines.extend(_wrap_files(middle))
    lines.append(_section_header("periphery"))
    lines.extend(_wrap_files(periphery))
    lines.append("+" + "-" * (_LAYER_MAX_COLS - 2) + "+")

    text = "\n".join(lines)
    # Hard truncate if somehow overbudget; append an ellipsis marker.
    if len(text) > _LAYER_MAX_CHARS:
        text = text[: _LAYER_MAX_CHARS - 4] + "\n..."
    return text


# ---------------------------------------------------------------------
# aa_ma_context (M3 Task 3.7 — the moat)
# ---------------------------------------------------------------------

# Extraction rules (verbatim contract from codemem-reference.md).
_FILE_MENTION_RE = re.compile(r"`([a-zA-Z0-9_\-./]+\.[a-zA-Z0-9]{1,5})`")
_SYMBOL_MENTION_RE = re.compile(r"`([a-zA-Z_][a-zA-Z0-9_.]{0,63})`")


def aa_ma_context(
    db_path: Path,
    task_name: str,
    *,
    repo_root: Path | None = None,
    write: bool = False,
    budget: int = _DEFAULT_BUDGET,
) -> dict:
    """Validate an AA-MA task and assemble a code-intel context pack.

    Walks ``<repo_root>/.claude/dev/active/<task_name>/<task_name>-{tasks,reference}.md``,
    extracts file + symbol mentions per the pinned extraction rules, then
    enriches via :func:`owners` for files and :func:`blast_radius` for symbols.

    With ``write=True`` the same content is appended to the task's
    reference.md as an ``## aa_ma_context snapshot [<ISO>]`` section.
    """
    try:
        clean = sanitize_symbol_arg(task_name)
    except ValidationError as exc:
        return {"error": str(exc), "task": task_name}

    if repo_root is None:
        return {"error": "repo_root is required for aa_ma_context", "task": clean}

    task_dir = Path(repo_root) / ".claude" / "dev" / "active" / clean
    if not task_dir.is_dir():
        return {
            "error": f"task not found: {clean} (expected at {task_dir})",
            "task": clean,
        }

    tasks_md = task_dir / f"{clean}-tasks.md"
    ref_md = task_dir / f"{clean}-reference.md"
    text_blobs: list[str] = []
    for p in (tasks_md, ref_md):
        if p.is_file():
            text_blobs.append(p.read_text(encoding="utf-8"))
    corpus = "\n".join(text_blobs)

    files = _extract_file_mentions(corpus, repo_root=Path(repo_root))
    symbols = _extract_symbol_mentions(corpus, db_path=db_path)

    # Owners per file (cache-only — don't trigger git subprocess here; the
    # tool is read-only and fast by contract).
    owners_by_file: dict[str, dict] = {}
    for fp in files:
        owners_by_file[fp] = owners(db_path, fp)

    # Blast radius per symbol.
    blast_by_symbol: dict[str, dict] = {}
    for sym in symbols:
        blast_by_symbol[sym] = blast_radius(db_path, sym)

    # hot_spots filtered to just the mentioned files (intersection, preserving
    # hot_spots' own ranking order).
    hs = hot_spots(db_path)
    mentioned_set = set(files)
    hs_filtered = [f for f in hs.get("files", []) if f["path"] in mentioned_set]

    markdown = _render_context_markdown(
        task=clean,
        files=files,
        symbols=symbols,
        owners_by_file=owners_by_file,
        blast_by_symbol=blast_by_symbol,
        hot_spots_filtered=hs_filtered,
    )

    if write:
        _append_snapshot_to_reference(ref_md, markdown)

    payload: dict[str, Any] = {
        "task": clean,
        "files": files,
        "symbols": symbols,
        "owners_by_file": owners_by_file,
        "blast_radius_by_symbol": blast_by_symbol,
        "hot_spots": hs_filtered,
        "markdown": markdown,
        "error": None,
        "truncated": False,
    }
    if len(json.dumps(payload, default=str)) > _budget_chars(budget):
        payload["truncated"] = True
    return payload


def _extract_file_mentions(corpus: str, *, repo_root: Path) -> list[str]:
    """Backticked path tokens that also exist on disk under repo_root.

    Deduplicates and preserves first-appearance order.
    """
    seen: dict[str, None] = {}
    for match in _FILE_MENTION_RE.findall(corpus):
        if match in seen:
            continue
        candidate = repo_root / match
        if candidate.is_file():
            seen[match] = None
    return list(seen.keys())


def _extract_symbol_mentions(corpus: str, *, db_path: Path) -> list[str]:
    """Backticked identifiers that also appear in the ``symbols.name`` column.

    Filters out anything matching a file-mention (those are files, not
    symbols). Deduplicates and preserves first-appearance order.
    """
    file_hits = set(_FILE_MENTION_RE.findall(corpus))
    candidates: list[str] = []
    for m in _SYMBOL_MENTION_RE.findall(corpus):
        if m in file_hits:
            continue
        if m not in candidates:
            candidates.append(m)
    if not candidates:
        return []
    placeholders = ",".join("?" for _ in candidates)
    with _open_ro(db_path) as conn:
        rows = conn.execute(
            f"SELECT DISTINCT name FROM symbols WHERE name IN ({placeholders})",
            candidates,
        ).fetchall()
    found = {r["name"] for r in rows}
    return [c for c in candidates if c in found]


def _render_context_markdown(
    *,
    task: str,
    files: list[str],
    symbols: list[str],
    owners_by_file: dict[str, dict],
    blast_by_symbol: dict[str, dict],
    hot_spots_filtered: list[dict],
) -> str:
    """Assemble the pastable Markdown fragment."""
    parts: list[str] = [f"# codemem aa_ma_context — {task}", ""]
    parts.append("## Files mentioned")
    if files:
        for fp in files:
            top_owner = ""
            ownres = owners_by_file.get(fp, {})
            authors = ownres.get("authors", [])
            if authors:
                top = authors[0]
                top_owner = f" — {top['email']} ({top['percentage']:.1f}%)"
            parts.append(f"- `{fp}`{top_owner}")
    else:
        parts.append("- (none)")
    parts.append("")
    parts.append("## Symbols mentioned")
    if symbols:
        for sym in symbols:
            blast = blast_by_symbol.get(sym, {})
            callees = blast.get("callees", [])
            parts.append(f"- `{sym}` (blast-radius: {len(callees)} downstream)")
    else:
        parts.append("- (none)")
    parts.append("")
    parts.append("## Hot spots (filtered to mentioned files)")
    if hot_spots_filtered:
        for hs in hot_spots_filtered:
            parts.append(
                f"- `{hs['path']}` — score {hs['score']} "
                f"({hs['commits_in_window']} commits × {hs['function_count']} fns)"
            )
    else:
        parts.append("- (none)")
    return "\n".join(parts) + "\n"


def _append_snapshot_to_reference(ref_md: Path, markdown: str) -> None:
    """Append ``## aa_ma_context snapshot [<ISO>]`` + content to reference.md."""
    ts = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    block = f"\n\n## aa_ma_context snapshot [{ts}]\n\n{markdown}"
    if ref_md.exists():
        ref_md.write_text(ref_md.read_text(encoding="utf-8") + block, encoding="utf-8")
    else:
        ref_md.write_text(block, encoding="utf-8")


# ---------------------------------------------------------------------
# Token-budget enforcement
# ---------------------------------------------------------------------

def _truncate(payload: dict, *, list_key: str, budget: int) -> dict:
    """Trim ``payload[list_key]`` until JSON size fits the budget.

    Adds a ``truncated: bool`` field to the payload either way so
    callers can detect whether results were capped.
    """
    items = payload.get(list_key, [])
    if not _exceeds_budget(payload, budget):
        return {**payload, "truncated": False}

    lo, hi = 0, len(items)
    # Binary-search the largest prefix that fits the budget.
    while lo < hi:
        mid = (lo + hi + 1) // 2
        candidate = {**payload, list_key: items[:mid], "truncated": True}
        if _exceeds_budget(candidate, budget):
            hi = mid - 1
        else:
            lo = mid
    return {**payload, list_key: items[:lo], "truncated": True}
