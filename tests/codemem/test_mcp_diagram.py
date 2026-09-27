"""codemem.mcp_tools.diagram — the MCP door onto ``codemem draw`` (diagram-generation M13).

Budget policy, decided by the 13.1 prototype on medical-research-skills (Ste, 2026-09-26):
reuse codemem's token budget; on overflow collapse to the next coarser level only while
that level still has edges, otherwise truncate the current level to the largest sorted
edge prefix that fits and count the rest in ``dropped``. Default level L2.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path

import pytest

from codemem import mcp_tools
from codemem.storage.db import connect, ensure_schema

KEYS = {"mermaid", "level", "nodes", "edges", "dropped", "collapsed_from", "truncated", "error"}


def _db(tmp_path: Path, imports: Sequence[tuple[str, str]]) -> Path:
    path = tmp_path / "idx.db"
    conn = connect(path)
    ensure_schema(conn)
    fid = {}
    for p in sorted({p for e in imports for p in e}):
        fid[p] = conn.execute(
            "INSERT INTO files(path, lang, last_indexed) VALUES (?, 'python', 0)", (p,)
        ).lastrowid
    conn.executemany(
        "INSERT INTO file_edges(src_file_id, dst_file_id, kind) VALUES (?, ?, 'import')",
        [(fid[a], fid[b]) for a, b in imports],
    )
    conn.commit()
    conn.close()
    return path


def _size(payload: dict) -> int:
    return len(json.dumps(payload, default=str))


N = 40  # edges per fixture graph


# Two sub-directories, 40 file edges between them: L2 = 40 edges, L1 = L0 = 1 edge.
TWO_DIRS = [(f"a/x/f{i:02}.py", f"b/y/g{i:02}.py") for i in range(N)]
# One directory at depth 2: L2 = 40 edges, L1 and L0 are empty (a monorepo's shape).
ONE_DIR = [(f"m/p/f{i:02}.py", f"m/p/g{i:02}.py") for i in range(N)]
# 40 top-level directories: L0 itself carries 40 edges.
MANY_TOPS = [(f"d{i:02}/f.py", f"e{i:02}/g.py") for i in range(N)]
SMALL = 300  # tokens: a few L2 edges fit, N do not
LIMIT = mcp_tools._budget_chars(SMALL)


def test_default_level_is_l2_and_every_key_is_present(tmp_path: Path) -> None:
    p = mcp_tools.diagram(_db(tmp_path, TWO_DIRS))
    assert set(p) == KEYS
    assert p["error"] is None
    assert (p["level"], p["nodes"], p["edges"], p["dropped"], p["collapsed_from"]) == ("L2", 2 * N, N, 0, None)
    assert p["mermaid"].startswith("flowchart LR\n")
    assert p["mermaid"].count('-->|"@import"|') == N


def test_over_budget_l2_collapses_to_l1(tmp_path: Path) -> None:  # AC2
    p = mcp_tools.diagram(_db(tmp_path, TWO_DIRS), level="L2", budget=SMALL)
    assert (p["level"], p["collapsed_from"], p["nodes"], p["edges"], p["dropped"]) == ("L1", "L2", 2, 1, 0)
    assert _size(p) <= LIMIT


def test_collapse_never_lands_on_an_empty_level(tmp_path: Path) -> None:
    """13.1: a one-directory graph has no L1 edges, so collapsing would answer with nothing."""
    p = mcp_tools.diagram(_db(tmp_path, ONE_DIR), level="L2", budget=SMALL)
    assert p["level"] == "L2" and p["collapsed_from"] is None
    assert 0 < p["edges"] < N
    assert p["edges"] + p["dropped"] == N
    assert _size(p) <= LIMIT


def test_l0_still_over_budget_truncates_at_l0(tmp_path: Path) -> None:
    p = mcp_tools.diagram(_db(tmp_path, MANY_TOPS), level="L2", budget=SMALL)
    assert (p["level"], p["collapsed_from"]) == ("L0", "L2")
    assert 0 < p["edges"] < N and p["edges"] + p["dropped"] == N
    assert _size(p) <= LIMIT


def test_truncation_keeps_the_sorted_prefix(tmp_path: Path) -> None:
    """Deterministic: the kept edges are the first ones in (src, dst, kind) order."""
    db = _db(tmp_path, ONE_DIR)
    a = mcp_tools.diagram(db, budget=SMALL)
    assert a == mcp_tools.diagram(db, budget=SMALL)
    assert '"m/p/f00.py"' in a["mermaid"] and f'"m/p/f{N - 1:02}.py"' not in a["mermaid"]


# Edges each graph holds per level: kept + dropped must add up to it.
TOTALS = {"two": {"L2": N, "L1": 1, "L0": 1}, "one": {"L2": N}, "tops": {"L2": N, "L1": N, "L0": N}}


@pytest.mark.parametrize("budget", [SMALL, mcp_tools._DEFAULT_BUDGET])
@pytest.mark.parametrize("name, graph", [("two", TWO_DIRS), ("one", ONE_DIR), ("tops", MANY_TOPS)])
def test_counts_match_the_mermaid_over_and_under_budget(tmp_path: Path, name, graph, budget) -> None:  # AC3
    p = mcp_tools.diagram(_db(tmp_path, graph), budget=budget)
    assert set(p) == KEYS
    assert p["mermaid"].count("-->|") == p["edges"]
    assert p["mermaid"].count('["') == p["nodes"]
    assert p["edges"] + p["dropped"] == TOTALS[name][p["level"]]


def test_scope_and_hops_reach_the_cut(tmp_path: Path) -> None:
    p = mcp_tools.diagram(_db(tmp_path, TWO_DIRS), scope="a/x/f00.py", hops=1)
    assert (p["nodes"], p["edges"]) == (2, 1)


def test_l3_is_symbol_calls(tmp_path: Path) -> None:
    p = mcp_tools.diagram(_db(tmp_path, TWO_DIRS), level="L3")
    assert p["error"] is None and p["level"] == "L3" and p["edges"] == 0  # imports only: no calls


@pytest.mark.parametrize("kwargs, needle", [
    ({"level": "L9"}, "level"),
    ({"level": "2"}, "level"),
    ({"hops": -1}, "hops"),
    ({"hops": 11}, "hops"),  # §6.8: _neighbourhood loops `hops` times — an agent could hang the server
    ({"hops": 10**12}, "hops"),
    ({"scope": "a" * 1025}, "scope"),
    ({"scope": "a/\x00"}, "scope"),
])
def test_bad_arguments_are_error_dicts(tmp_path: Path, kwargs, needle) -> None:
    p = mcp_tools.diagram(_db(tmp_path, TWO_DIRS), **kwargs)
    assert set(p) == KEYS and needle in p["error"] and p["edges"] == 0


def test_pre_v3_index_is_an_error_naming_codemem_build(tmp_path: Path) -> None:
    db = _db(tmp_path, TWO_DIRS)
    conn = connect(db)
    conn.execute("PRAGMA user_version = 2")
    conn.commit()
    conn.close()
    p = mcp_tools.diagram(db)
    assert set(p) == KEYS and "codemem build" in p["error"]


def test_hops_ten_is_allowed(tmp_path: Path) -> None:
    assert mcp_tools.diagram(_db(tmp_path, TWO_DIRS), scope="a/x/f00.py", hops=10)["error"] is None


def test_scope_with_spaces_is_allowed(tmp_path: Path) -> None:
    """Real directory names carry spaces; scope is matched in Python only, never SQL."""
    p = mcp_tools.diagram(_db(tmp_path, [("a b/x.py", "c/y.py")]), scope="a b/")
    assert p["error"] is None and p["edges"] == 1


@pytest.mark.parametrize("name, graph, budget", [("one", ONE_DIR, SMALL), ("tops", MANY_TOPS, SMALL),
                                                 ("two", TWO_DIRS, SMALL), ("two", TWO_DIRS, 10**6)])
def test_truncated_flag_and_note_say_what_the_counts_say(tmp_path: Path, name, graph, budget) -> None:
    """Like every other codemem tool, `truncated` says the answer is partial; pasted mermaid says so too."""
    p = mcp_tools.diagram(_db(tmp_path, graph), budget=budget)
    assert p["truncated"] is (p["dropped"] > 0 or p["collapsed_from"] is not None)
    assert (f"%% {p['dropped']} edges not shown" in p["mermaid"]) is (p["dropped"] > 0)
