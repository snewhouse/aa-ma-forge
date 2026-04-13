"""Canonical SQL queries for MCP tools (M1 Task 1.7).

Every call-graph walk uses one of the two recursive CTEs defined here.
Both are cycle-safe via a ``path`` column that records already-visited
symbol IDs as ``|id|`` tokens and rejects re-entry via ``NOT LIKE``.

Binding names (all queries):
    :target     — symbol ID anchor for upstream or downstream walk
    :max_depth  — depth cap (exclusive); 3 is a reasonable default

The WHO_CALLS_CTE is pinned verbatim in ``codemem-reference.md``.
``EXPLAIN QUERY PLAN`` on it MUST use ``idx_edges_dst`` (covering
(dst, kind, src)) — no bare SCAN TABLE allowed. The test harness
verifies this at :class:`~tests.codemem.test_mcp_tools.TestCanonicalCTEExplainPlan`.
"""

from __future__ import annotations


__all__ = ["WHO_CALLS_CTE", "BLAST_RADIUS_CTE"]


# Upstream: who calls the target? Walks edges.dst → edges.src.
# Uses idx_edges_dst(dst_symbol_id, kind, src_symbol_id) — a covering
# index — so the plan never has to touch the edges row body.
WHO_CALLS_CTE = """
WITH RECURSIVE callers(sid, depth, path) AS (
    SELECT src_symbol_id, 1, '|' || src_symbol_id || '|'
    FROM edges
    WHERE dst_symbol_id = :target AND kind = 'call'
    UNION
    SELECT e.src_symbol_id, c.depth + 1, c.path || e.src_symbol_id || '|'
    FROM edges e
    JOIN callers c ON e.dst_symbol_id = c.sid
    WHERE c.depth < :max_depth
      AND e.kind = 'call'
      AND c.path NOT LIKE '%|' || e.src_symbol_id || '|%'
)
SELECT DISTINCT sid FROM callers
"""


# Downstream: what does the target call (transitively)? Walks
# edges.src → edges.dst. Uses idx_edges_src for the reverse direction.
BLAST_RADIUS_CTE = """
WITH RECURSIVE descendants(sid, depth, path) AS (
    SELECT dst_symbol_id, 1, '|' || dst_symbol_id || '|'
    FROM edges
    WHERE src_symbol_id = :target
      AND kind = 'call'
      AND dst_symbol_id IS NOT NULL
    UNION
    SELECT e.dst_symbol_id, d.depth + 1, d.path || e.dst_symbol_id || '|'
    FROM edges e
    JOIN descendants d ON e.src_symbol_id = d.sid
    WHERE d.depth < :max_depth
      AND e.kind = 'call'
      AND e.dst_symbol_id IS NOT NULL
      AND d.path NOT LIKE '%|' || e.dst_symbol_id || '|%'
)
SELECT DISTINCT sid FROM descendants
"""
