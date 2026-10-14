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
    diagram           — mermaid cut of the graph, sized to the budget (M13)
"""

from __future__ import annotations

import json
import logging
import os
import re
import sqlite3
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

from ..storage import db
from .queries import BLAST_RADIUS_CTE, WHO_CALLS_CTE
from .sanitizers import ValidationError, sanitize_path_arg, sanitize_symbol_arg

if TYPE_CHECKING:
    from ..incremental import Freshness

logger = logging.getLogger(__name__)


__all__ = [
    "aa_ma_context",
    "blast_radius",
    "co_changes",
    "dead_code",
    "dependency_chain",
    "diagram",
    "REFRESH_CAP_S",
    "ensure_built",
    "ensure_fresh",
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
_MAX_HOPS = (
    10  # diagram(): a neighbourhood this wide is the whole graph on any real repo
)
_MAX_SCOPE = 1024  # diagram(): a path prefix, matched in Python only (never SQL)
# Conservative char-per-token heuristic. 1 token ≈ 4 chars for English+code.
_CHARS_PER_TOKEN = 4


# ---------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------


# The refresh step of a query is capped at this: the aa-ma-forge cold-build
# SLO (report 03 R03-D6). Past it, results are served with stale=true and the
# refresh keeps running in the background. A missing index is cold-built
# unbounded (nothing to serve without it); see ensure_fresh.
REFRESH_CAP_S = 5.0


def ensure_built(db_path: Path, repo_root: Path) -> dict | None:
    """Make the index servable: build it if missing, refresh it if stale.

    Returns ``None`` when there is a DB to serve (fresh or, past the cap,
    stale), or a structured ``{"error": ...}`` dict when there is none.
    Never raises. :func:`ensure_fresh` returns the freshness fields too.
    """
    result = ensure_fresh(db_path, repo_root)
    return {"error": result["error"]} if "error" in result else None


def ensure_fresh(db_path: Path, repo_root: Path, *, cap: float = REFRESH_CAP_S) -> dict:
    """Build if missing, then refresh if stale with the refresh capped at ``cap`` s.

    Returns the X2 fields ``index_sha``, ``head_sha``, ``stale`` and
    ``stale_reason``; with no DB to serve, an ``error`` too. ``stale`` is
    True, False or ``"unknown"``, as it stands AFTER the refresh attempt (D6).
    ``stale_reason`` is None when fresh, else one of:

    - ``locked`` / ``error`` / ``timeout``: the refresh did not finish (the
      pre-check cause, behind or dirty, goes in the refresh.log line);
    - ``behind`` / ``dirty`` / ``no_index_sha``: still stale after a
      refresh that finished (the tree moved meanwhile);
    - ``no_git`` / ``no_head``: ``stale`` is ``"unknown"``;
    - ``no_index``: the build failed, nothing to serve;
    - ``unsafe_db_path``: refused per ``codemem.safety.check_db_path``
      (repo-controlled ``.codemem/``; M15 §6.8). Nothing is served or written;
    - ``untrusted``: an index codemem did not build here (``codemem.safety``)
      whose rebuild did not finish within ``cap``. Nothing is served.

    A missing DB is cold-built in-process and unbounded (nothing can be
    served without it); only the wait for another process's build is capped.
    The refresh runs as a ``codemem refresh`` subprocess (M15.1 verdict): the
    writer lock is per-process, a thread cannot be stopped, and a subprocess
    that outlives the cap keeps running on its own.
    """
    from ..safety import TrustStoreError, UnsafeDbPath, check_db_path

    try:
        check_db_path(db_path)
    except UnsafeDbPath as exc:
        return {"error": str(exc), **_unknown_freshness("unsafe_db_path")}
    err = _build_if_missing(db_path, repo_root, cap)
    if err is not None:
        return {**err, **_unknown_freshness("no_index")}
    try:
        from ..incremental import check_freshness, log_refresh

        before = check_freshness(repo_root, db_path)
        if before.stale is not True:
            return _freshness_fields(before)
        outcome = _capped_refresh(db_path, repo_root, cap)
        after = check_freshness(repo_root, db_path) if outcome == "ok" else before
        fields = _freshness_fields(after)
        if after.reason == "untrusted":
            # Never serve an index codemem did not build here (M15 §6.8).
            log_refresh(
                db_path.parent,
                f"ensure_fresh: not served (untrusted); rebuild {outcome}",
            )
            return {
                "error": _UNTRUSTED_ERROR.get(outcome, _UNTRUSTED_ERROR["error"]),
                **fields,
            }
        if outcome != "ok":
            log_refresh(
                db_path.parent,
                f"ensure_fresh: serving a stale index ({before.reason}); refresh {outcome}",
            )
            fields["stale_reason"] = outcome
        return fields
    except TrustStoreError as exc:
        logger.warning("ensure_fresh: %s", exc)
        return {
            "error": f"codemem trust store unusable: {exc}",
            **_unknown_freshness("error"),
        }
    except Exception as exc:  # noqa: BLE001  # why: tool-surface contract — never raise, return fields
        logger.warning("ensure_fresh: freshness check failed: %s", type(exc).__name__)
        return _unknown_freshness("error")


# Why nothing is served for an untrusted index, by rebuild outcome: a caller
# should retry while it runs, and stop retrying when it failed.
_UNTRUSTED_ERROR = {
    "timeout": "the index was not built by codemem here; its rebuild is still running, retry shortly",
    "locked": "the index was not built by codemem here; another refresh holds the lock, retry shortly",
    "ok": "the index was not built by codemem here and its rebuild did not take; run `codemem build`",
    "error": "the index was not built by codemem here and its rebuild failed; see .codemem/refresh.log, then run `codemem build`",
}


def _unknown_freshness(reason: str) -> dict:
    return {
        "index_sha": None,
        "head_sha": None,
        "stale": "unknown",
        "stale_reason": reason,
    }


def _freshness_fields(f: Freshness) -> dict:
    return {
        "index_sha": f.index_sha,
        "head_sha": f.head_sha,
        "stale": "unknown" if f.stale is None else f.stale,
        "stale_reason": f.reason,
    }


def _capped_refresh(db_path: Path, repo_root: Path, cap: float) -> str:
    """Run ``codemem refresh``; return ok, locked, error or timeout within ``cap``."""
    from ..incremental import EXIT_LOCKED

    # -I: `-m` would otherwise put the cwd first on sys.path, and a repo
    # that ships its own codemem/cli.py would run inside the refresh.
    proc = subprocess.Popen(  # noqa: S603  # why: fixed argv (this interpreter + codemem.cli), no shell
        [
            sys.executable,
            "-I",
            "-m",
            "codemem.cli",
            "--db",
            str(db_path),
            "refresh",
            "--repo-root",
            str(repo_root),
        ],
        cwd=db_path.parent,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    try:
        rc = proc.wait(timeout=cap)
    except subprocess.TimeoutExpired:
        # ponytail: left running, detached; it holds db.lock, so queries
        # until it ends see "locked". Kill-safe either way (M15.1).
        return "timeout"
    return {0: "ok", EXIT_LOCKED: "locked"}.get(rc, "error")


def _build_if_missing(db_path: Path, repo_root: Path, cap: float) -> dict | None:
    """Cold-build a missing DB, or wait up to ``cap`` for another process's build.

    The build goes through ``refresh_index``: the same writer lock (beside
    the DB, so ``CODEMEM_DB`` elsewhere is still one lock), a DB built aside
    and swapped in whole (a poller never sees a half-built file), and
    ``last_sha`` + ``tree_sig`` recorded. Lives in :mod:`codemem.mcp_tools`
    so the plugin server never imports the indexer or journal itself.
    """
    if db_path.exists():
        return None
    if not repo_root.is_dir():
        return {"error": f"build failed: repo root is not a directory: {repo_root}"}
    try:
        # Lazy import: keep mcp_tools' cold-start cheap when the DB exists.
        from ..incremental import refresh_index

        if not refresh_index(repo_root, db_path).skipped_locked:
            return None
        deadline = time.monotonic() + cap
        while time.monotonic() < deadline:
            time.sleep(0.1)
            if db_path.exists():
                return None
        return {
            "error": f"build in progress by another process; timed out after {cap:g}s"
        }
    except Exception as exc:  # noqa: BLE001  # why: tool-surface contract — an error dict, never a raise
        return {"error": f"build failed: {exc.__class__.__name__}: {exc}"}


def _budget_chars(budget_tokens: int) -> int:
    return max(budget_tokens, 1) * _CHARS_PER_TOKEN


def _exceeds_budget(payload: Any, budget_tokens: int) -> bool:
    return len(json.dumps(payload, default=str)) > _budget_chars(budget_tokens)


def _open_ro(db_path: Path) -> sqlite3.Connection:
    conn = db.connect(db_path, read_only=True)
    conn.row_factory = sqlite3.Row
    return conn


def _resolve_symbol_ids_by_name(conn: sqlite3.Connection, name: str) -> list[int]:
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
            return {
                "target": clean,
                "downstream": [],
                "truncated": False,
                "error": None,
            }

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
            """,  # noqa: S608  # why: only `?` placeholders are interpolated; values are bound
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

    excludes = _DEFAULT_CO_CHANGES_EXCLUDE if exclude is None else tuple(exclude)

    # Parameterised `NOT IN (?, ?, ...)` — build conditionally so empty
    # excludes produces NO clause at all (a bare `NOT IN (NULL)` evaluates
    # to NULL/unknown and filters out everything, SQL three-valued-logic gotcha).
    exclude_clause = ""
    if excludes:
        exclude_clause = "AND co.path NOT IN (" + ",".join("?" for _ in excludes) + ")"
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
    """  # noqa: S608  # why: exclude_clause is literals + `?` placeholders; values are bound
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
                "FROM ownership WHERE substr(file_path, 1, length(?1)) = ?1 "
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


# Each blame is a ``git`` subprocess, so threads overlap the waiting.
_BLAME_MAX_WORKERS = min(8, os.cpu_count() or 1)


def _refresh_ownership_cache(db_path: Path, path: str, *, repo_root: Path) -> None:
    """Blame ``path`` and write the results to the ``ownership`` table.

    Calls ``GitMiner.get_blame`` for ``path`` (or the files under it when
    path is a directory).

    Per-file 2 second timeout matches the AC. Files that blame refuses
    (binary, not-in-HEAD, deleted) get no cache entries; a blame that raises
    (e.g. the timeout) is logged as one warning and skipped. Blames run concurrently on a bounded thread pool; only
    the calling thread writes, in sorted file-path order.
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
                "SELECT path FROM files WHERE substr(path, 1, length(?1)) = ?1",
                (path,),
            ).fetchall()
            targets = [r[0] for r in rows]
        finally:
            conn.close()
    else:
        targets = [path]

    if not targets:
        return

    def _blame(target: str) -> dict[str, tuple[int, float]]:
        try:
            return miner.get_blame(target)
        except Exception as exc:  # noqa: BLE001  # why: one unblameable file must not sink the owners report
            logger.warning(
                "owners: blame failed for %s (%s); skipped", target, type(exc).__name__
            )
            return {}

    targets = sorted(targets)
    with ThreadPoolExecutor(max_workers=_BLAME_MAX_WORKERS) as pool:
        results = list(pool.map(_blame, targets))

    now = int(time.time())
    conn = db.connect(db_path)
    try:
        with db.transaction(conn):
            for t, result in zip(targets, results):
                if not result:
                    continue
                # Replace any stale rows for this file.
                conn.execute("DELETE FROM ownership WHERE file_path = ?", (t,))
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

_LAYER_MAX_COLS = 80  # AC: fits 80-col terminal without wrap
_LAYER_MAX_CHARS = 2_000  # AC: ≤ 500 tokens × 4 chars/token heuristic


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
    periphery = [p for p, _ in files[n - peri_count :]]
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


def diagram(  # noqa: C901  # why: pre-existing; refactor tracked in TODOS.md (M8.2 D8 pay-down, no logic change in a security milestone)
    db_path: Path,
    *,
    level: str = "L2",
    scope: str | None = None,
    hops: int = 1,
    budget: int = _DEFAULT_BUDGET,
) -> dict:
    """``codemem draw`` as a budgeted tool (diagram-generation M13).

    Over budget, collapse to the next coarser level only while that level still has
    edges; otherwise keep the current level and truncate it to the largest sorted edge
    prefix that fits. Measured on a one-top-level-dir monorepo (13.1): unguarded
    collapse answered a 482-edge L3 question with an empty L2. ``dropped`` counts every
    edge not drawn (mermaid's ``maxEdges`` cap and budget truncation alike); the mermaid
    says so in a ``%%`` line, and ``truncated`` is true whenever the answer is partial.
    """
    from ..draw.cut import MIN_SCHEMA_VERSION, Level, cut, from_edges
    from ..draw.mermaid import to_mermaid

    def out(c, lv, *, frm=None, dropped=0, error=None) -> dict:
        text = to_mermaid(c) if c else ""
        if (
            c and dropped > c.dropped
        ):  # budget truncation: to_mermaid only notes its own maxEdges cap
            text = text.replace(
                "flowchart LR\n",
                f"flowchart LR\n%% {dropped} edges not shown: over the {budget}-token budget\n",
                1,
            )
        return {
            "mermaid": text,
            "level": lv,
            "nodes": len(c.nodes) if c else 0,
            "edges": len(c.edges) if c else 0,
            "dropped": dropped,
            "collapsed_from": frm,
            "truncated": dropped > 0 or frm is not None,
            "error": error,
        }

    if level not in Level.__members__:
        return out(
            None,
            level,
            error=f"level must be one of {list(Level.__members__)}, got {level!r}",
        )
    if not 0 <= hops <= _MAX_HOPS:  # the neighbourhood walk loops `hops` times
        return out(None, level, error=f"hops must be 0..{_MAX_HOPS}, got {hops}")
    if scope is not None and not (len(scope) <= _MAX_SCOPE and scope.isprintable()):
        return out(
            None,
            level,
            error=f"scope must be at most {_MAX_SCOPE} printable characters",
        )
    try:
        with _open_ro(db_path) as conn:
            version = conn.execute("PRAGMA user_version").fetchone()[0]
            if version < MIN_SCHEMA_VERSION:
                return out(
                    None,
                    level,
                    error=f"index is schema v{version}, need v{MIN_SCHEMA_VERSION}; run `codemem build`",
                )
            requested = lv = Level[level]
            c = cut(conn, lv, scope=scope, hops=hops)
            while lv > Level.L0 and _exceeds_budget(
                out(c, lv.name, dropped=c.dropped), budget
            ):
                coarser = cut(conn, Level(lv - 1), scope=scope, hops=hops)
                if not coarser.edges:
                    break
                lv, c = Level(lv - 1), coarser
    except (ValueError, sqlite3.Error) as exc:
        return out(None, level, error=str(exc))

    frm = requested.name if lv is not requested else None
    if not _exceeds_budget(out(c, lv.name, frm=frm, dropped=c.dropped), budget):
        return out(c, lv.name, frm=frm, dropped=c.dropped)
    named = sorted((c.nodes[a], c.nodes[b], k) for a, b, k in c.edges)

    def fitted(k: int) -> dict:
        return out(
            from_edges(set(named[:k]), lv),
            lv.name,
            frm=frm,
            dropped=c.dropped + len(named) - k,
        )

    return fitted(
        _largest_prefix(len(named), lambda k: not _exceeds_budget(fitted(k), budget))
    )


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
    tasks_md = task_dir / f"{clean}-tasks.md"
    ref_md = task_dir / f"{clean}-reference.md"
    problem = _task_path_problem(task_dir, tasks_md, ref_md)
    if problem is not None:
        return {"error": problem, "task": clean}

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

    Deduplicates and preserves first-appearance order. The corpus is repo
    text: an absolute or ``..`` token, or one whose link leaves the repo, is
    never probed (M15 §6.8 background review).
    """
    root = repo_root.resolve()
    seen: dict[str, None] = {}
    for match in _FILE_MENTION_RE.findall(corpus):
        rel = Path(match)
        if match in seen or rel.is_absolute() or ".." in rel.parts:
            continue
        candidate = (root / rel).resolve()
        if candidate.is_relative_to(root) and candidate.is_file():
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
            f"SELECT DISTINCT name FROM symbols WHERE name IN ({placeholders})",  # noqa: S608  # why: only `?` placeholders are interpolated; values are bound
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


def _task_path_problem(task_dir: Path, *files: Path) -> str | None:
    """Why the task path cannot be used, or None.

    The task path is repo-controlled: a committed link at ``.claude``,
    ``dev``, ``active``, the task dir or ``files`` would make
    ``aa_ma_context(write=True)`` append repo-chosen text to any user file
    (M15 §6.8 re-run 1).
    """
    chain = [task_dir.parents[2], task_dir.parents[1], task_dir.parent, task_dir]
    if any(p.is_symlink() for p in [*chain, *files]):
        return f"task path for {task_dir.name} contains a symlink; refusing to read or write it"
    if not task_dir.is_dir():
        return f"task not found: {task_dir.name} (expected at {task_dir})"
    return None


def _append_snapshot_to_reference(ref_md: Path, markdown: str) -> None:
    """Append ``## aa_ma_context snapshot [<ISO>]`` + content to reference.md."""
    ts = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    block = f"\n\n## aa_ma_context snapshot [{ts}]\n\n{markdown}"
    # O_NOFOLLOW: a link planted after aa_ma_context's check is still refused.
    flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    with os.fdopen(os.open(ref_md, flags, 0o644), "a", encoding="utf-8") as fh:
        fh.write(block)


# ---------------------------------------------------------------------
# Token-budget enforcement
# ---------------------------------------------------------------------


def _largest_prefix(n: int, fits: Callable[[int], bool]) -> int:
    """Largest ``k <= n`` with ``fits(k)``, by binary search; ``fits`` must be monotone."""
    lo, hi = 0, n
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if fits(mid):
            lo = mid
        else:
            hi = mid - 1
    return lo


def _truncate(payload: dict, *, list_key: str, budget: int) -> dict:
    """Trim ``payload[list_key]`` until JSON size fits the budget.

    Adds a ``truncated: bool`` field to the payload either way so
    callers can detect whether results were capped.
    """
    items = payload.get(list_key, [])
    if not _exceeds_budget(payload, budget):
        return {**payload, "truncated": False}
    keep = _largest_prefix(
        len(items),
        lambda k: (
            not _exceeds_budget(
                {**payload, list_key: items[:k], "truncated": True}, budget
            )
        ),
    )
    return {**payload, list_key: items[:keep], "truncated": True}
