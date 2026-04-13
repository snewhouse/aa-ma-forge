"""PageRank-ranked PROJECT_INTEL.json projection (M1 Task 1.8).

Pure-Python power iteration over the call graph — no scipy, no
networkx. Aider-style: compute weighted in-degree centrality over
`symbols` linked by `edges`, then sort with stable tie-breakers and
binary-search the prefix that fits a token budget.

The output `PROJECT_INTEL.json` is the single dense artifact an agent
loads first — the index *itself* lives in SQLite, but this JSON
projection is what you paste into a prompt.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path


__all__ = [
    "DEFAULT_DAMPING",
    "DEFAULT_ITERATIONS",
    "DEFAULT_BUDGET_TOKENS",
    "compute_pagerank",
    "write_project_intel",
]


DEFAULT_DAMPING = 0.85
DEFAULT_ITERATIONS = 50
DEFAULT_EPS = 1e-6
DEFAULT_BUDGET_TOKENS = 1024
_CHARS_PER_TOKEN = 4

# Kind → sort priority for tie-break (lower = ranked first).
_KIND_PRIORITY: dict[str, int] = {
    "function":       0,
    "async_function": 0,
    "method":         1,
    "async_method":   1,
    "class":          2,
    "struct":         2,
    "interface":      2,
    "type_alias":     3,
}


# ---------------------------------------------------------------------
# Algorithm
# ---------------------------------------------------------------------

def compute_pagerank(
    conn: sqlite3.Connection,
    *,
    damping: float = DEFAULT_DAMPING,
    max_iterations: int = DEFAULT_ITERATIONS,
    eps: float = DEFAULT_EPS,
) -> dict[int, float]:
    """Compute PageRank over symbols with call edges as the graph.

    Returns ``{symbol_id: rank}`` summing to 1.0. Deterministic — same
    DB in, same floats out.
    """
    ids = [row[0] for row in conn.execute("SELECT id FROM symbols ORDER BY id")]
    n = len(ids)
    if n == 0:
        return {}

    # Build adjacency: for each node, the set of destinations it links to
    # (edges.src → edges.dst, kind='call', resolved only).
    out_edges: dict[int, list[int]] = {sid: [] for sid in ids}
    for src, dst in conn.execute(
        """
        SELECT src_symbol_id, dst_symbol_id
        FROM edges
        WHERE kind = 'call' AND dst_symbol_id IS NOT NULL
        """
    ):
        if src in out_edges and dst in out_edges:
            out_edges[src].append(dst)

    out_degree = {sid: max(len(tgts), 1) for sid, tgts in out_edges.items()}

    base = (1.0 - damping) / n
    rank = {sid: 1.0 / n for sid in ids}

    for _ in range(max_iterations):
        contributions: dict[int, float] = {sid: 0.0 for sid in ids}
        dangling_mass = 0.0
        for src in ids:
            dests = out_edges[src]
            if not dests:
                dangling_mass += rank[src]
                continue
            share = rank[src] / out_degree[src]
            for dst in dests:
                contributions[dst] += share

        # Dangling (no outbound edges) distributes rank uniformly per PageRank
        # random-surfer formulation — otherwise sum drifts below 1.0.
        dangling_spread = damping * dangling_mass / n

        new_rank = {
            sid: base + dangling_spread + damping * contributions[sid]
            for sid in ids
        }

        delta = sum(abs(new_rank[sid] - rank[sid]) for sid in ids)
        rank = new_rank
        if delta < eps:
            break

    # Final normalization — float error over many iters can leave sum != 1.
    total = sum(rank.values()) or 1.0
    return {sid: r / total for sid, r in rank.items()}


# ---------------------------------------------------------------------
# PROJECT_INTEL.json writer
# ---------------------------------------------------------------------

def _sort_key(entry: dict) -> tuple:
    """Stable sort key for tied ranks: kind priority, then file, then line, then name."""
    return (
        _KIND_PRIORITY.get(entry["kind"], 10),
        entry["file"],
        entry["line"] or 0,
        entry["name"],
    )


def _budget_chars(budget_tokens: int) -> int:
    return max(budget_tokens, 1) * _CHARS_PER_TOKEN


def _fits(payload: dict, budget_tokens: int) -> bool:
    return len(json.dumps(payload, separators=(",", ":"), sort_keys=True)) <= _budget_chars(budget_tokens)


def write_project_intel(
    db_path: Path,
    out_path: Path,
    *,
    budget: int = DEFAULT_BUDGET_TOKENS,
    damping: float = DEFAULT_DAMPING,
) -> dict:
    """Compute PageRank, rank symbols, binary-search-fit the budget,
    write ``out_path`` as deterministic JSON. Returns stats dict.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    from .storage import db as _db

    with _db.connect(db_path, read_only=True) as conn:
        conn.row_factory = sqlite3.Row
        ranks = compute_pagerank(conn, damping=damping)

        rows = conn.execute(
            """
            SELECT s.id, s.scip_id, s.name, s.kind, s.line, f.path
            FROM symbols s JOIN files f ON s.file_id = f.id
            """
        ).fetchall()

    symbols = [
        {
            "scip_id": r["scip_id"],
            "name": r["name"],
            "kind": r["kind"],
            "file": r["path"],
            "line": r["line"],
            "rank": ranks.get(r["id"], 0.0),
        }
        for r in rows
    ]

    # Primary sort: descending rank. Secondary: stable tie-break.
    symbols.sort(key=lambda s: (-s["rank"], _sort_key(s)))

    meta = {
        "schema": "codemem/project-intel@1",
        "budget": budget,
        "damping": damping,
        "total_symbols": len(symbols),
    }

    # Binary-search the longest prefix that fits the budget.
    lo, hi = 0, len(symbols)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        trial = {"_meta": {**meta, "written_symbols": mid}, "symbols": symbols[:mid]}
        if _fits(trial, budget):
            lo = mid
        else:
            hi = mid - 1

    final_symbols = symbols[:lo]
    payload = {
        "_meta": {**meta, "written_symbols": len(final_symbols)},
        "symbols": final_symbols,
    }

    out_path.write_text(
        json.dumps(payload, separators=(",", ":"), sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {"written_symbols": len(final_symbols), "size_bytes": out_path.stat().st_size}
