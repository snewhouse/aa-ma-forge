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
import sqlite3
import time
from pathlib import Path
from typing import Any

from ..storage import db
from .queries import BLAST_RADIUS_CTE, WHO_CALLS_CTE
from .sanitizers import ValidationError, sanitize_path_arg, sanitize_symbol_arg


__all__ = [
    "blast_radius",
    "co_changes",
    "dead_code",
    "dependency_chain",
    "file_summary",
    "hot_spots",
    "owners",
    "search_symbols",
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
